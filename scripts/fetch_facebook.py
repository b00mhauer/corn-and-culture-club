"""Fetch public Facebook events via Scrape Creators.

Facebook is the biggest source of local happenings, and — unlike Instagram —
the events endpoint returns STRUCTURED events (name, date, place, url), so these
come back close to finished. We still treat them as discovery: the ccc-research
skill dedupes them against calendar candidates and curates.

Two source types in sources.yaml (method: facebook):
  - fb_query: "<text>"   -> GET /v1/facebook/events/search?query=<text>
  - fb_url:   "<pageurl>" -> GET /v1/facebook/events?url=<pageurl>

~1 credit per query/page per run. Needs SCRAPE_CREATORS_API_KEY in .env.

    uv run python scripts/fetch_facebook.py --start 2026-07-09 --days 7
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date

import requests

from ccc_core import (
    TOWNS,
    USER_AGENT,
    Event,
    clean,
    dedupe,
    enrich,
    guess_town,
    parse_window,
    require_key,
    to_central,
)

SEARCH = "https://api.scrapecreators.com/v1/facebook/events/search"
PAGE = "https://api.scrapecreators.com/v1/facebook/events"


def _local_date(ts: int | None) -> str:
    # FB timestamps are UTC seconds; store as America/Chicago local (fixes the
    # day/time, e.g. an 8:30pm CDT show is 01:30 UTC the next day).
    return to_central(ts=ts) if ts else ""


def _in_county(place_name: str, title: str) -> bool:
    """True if PLACE or TITLE carries a clear county signal (a town name).

    We keep this STRICT (drop when false) for Facebook specifically. FB's search
    bleeds in global junk — a lenient 'keep and flag' pass was tested and let in
    Denmark, Idaho, and Ohio events, because those venues carry no local signal.
    Real local FB events reliably include their city in the place data, so
    'no county signal' almost always means 'not local'. Measured: strict drops
    ~0 legitimate local events. (Calendar sources, which lack reliable place
    data, use the softer keep-and-flag in build_edition's keep() instead.)
    """
    hay = f"{place_name} {title}".lower()
    if any(alias.strip() in hay for aliases in TOWNS.values() for alias in aliases):
        return True
    return "iowa city" in hay or "johnson county" in hay


def _to_event(raw: dict, source_id: str, d0: date, d1: date) -> Event | None:
    if raw.get("is_past") or raw.get("is_online"):
        return None
    ts = raw.get("start_timestamp")
    start_iso = _local_date(ts)
    if start_iso:
        sday = date.fromisoformat(start_iso[:10])  # Central date
        if not (d0 <= sday <= d1):
            return None

    place = (raw.get("event_place") or {}).get("contextual_name") or ""
    title = clean(raw.get("name", ""))
    if not _in_county(place, title):
        return None

    price = (raw.get("ticketing_context_row") or {}).get("price_range_text")
    ev = Event(
        title=title,
        start=start_iso,
        when_text=clean(raw.get("day_time_sentence", "")),
        source=source_id,
        source_name="Facebook Events",
        venue=place or None,
        town=guess_town(f"{place} {title}".lower()),
        url=raw.get("url") or raw.get("event_url"),
        description=clean(raw.get("day_time_sentence", "")),
        cost="paid" if price else "unknown",
        is_free=None,
    )
    if price:
        ev.tags.append(f"price:{price}")
    ev.tags.append("via:facebook")
    return enrich(ev, "general")


def _get(url: str, params: dict, key: str) -> dict:
    """GET with one retry on transient 5xx (the FB API 500s intermittently)."""
    headers = {"x-api-key": key, "User-Agent": USER_AGENT}
    last: Exception | None = None
    for attempt in range(2):
        resp = requests.get(url, params=params, headers=headers, timeout=40)
        if resp.status_code < 500:
            resp.raise_for_status()
            return resp.json()
        last = requests.HTTPError(f"{resp.status_code} {resp.reason}")
    raise last  # type: ignore[misc]


def _search_paged(query: str, key: str, pages: int) -> tuple[list[dict], int | None]:
    """Follow the cursor for up to `pages` pages. Each page is ~1 credit, so this
    trades credits for recall. Stops early when the cursor runs out."""
    raws: list[dict] = []
    credits: int | None = None
    params = {"query": query}
    for _ in range(max(1, pages)):
        body = _get(SEARCH, params, key)
        credits = body.get("credits_remaining", credits)
        batch = body.get("events", [])
        raws.extend(batch)
        cursor = body.get("cursor")
        if not cursor or not batch:
            break
        params = {"query": query, "cursor": cursor}
    return raws, credits


def fetch_all(d0: date, d1: date, max_calls: int | None, only: str | None = None,
              pages: int = 2) -> dict:
    from ccc_core import load_sources

    key = require_key("SCRAPE_CREATORS_API_KEY")
    srcs = [s for s in load_sources() if s.get("method") == "facebook"]
    if only:
        srcs = [s for s in srcs if s["id"] == only]
    if max_calls:
        srcs = srcs[:max_calls]

    events: list[Event] = []
    report: list[dict] = []
    credits: int | None = None
    for src in srcs:
        try:
            if src.get("fb_query"):
                raws, credits = _search_paged(src["fb_query"], key, pages)
            elif src.get("fb_url"):
                body = _get(PAGE, {"url": src["fb_url"]}, key)
                credits = body.get("credits_remaining", credits)
                raws = body.get("events", [])
            else:
                report.append({"source": src["id"], "status": "skipped_no_query"})
                continue
            got = [e for e in (_to_event(r, src["id"], d0, d1) for r in raws) if e]
            events.extend(got)
            report.append({"source": src["id"], "status": "ok", "raw": len(raws), "in_window_local": len(got)})
        except Exception as exc:  # noqa: BLE001
            report.append({"source": src["id"], "status": "error", "error": str(exc)[:160]})

    deduped = dedupe(events)
    return {
        "window": {"start": d0.isoformat(), "end": d1.isoformat()},
        "credits_remaining": credits,
        "report": report,
        "count": len(deduped),
        "events": [e.to_dict() for e in deduped],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch public Facebook events via Scrape Creators.")
    ap.add_argument("--start", help="YYYY-MM-DD (default: today)")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--max-calls", type=int, default=None, help="cap queries run this run")
    ap.add_argument("--pages", type=int, default=2, help="pages per query (~1 credit each)")
    ap.add_argument("--source", help="only this source id")
    args = ap.parse_args()

    d0, d1 = parse_window(args.start, args.days)
    data = fetch_all(d0, d1, args.max_calls, only=args.source, pages=args.pages)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
