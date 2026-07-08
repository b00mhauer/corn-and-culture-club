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
from datetime import date, datetime, timezone

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
)

SEARCH = "https://api.scrapecreators.com/v1/facebook/events/search"
PAGE = "https://api.scrapecreators.com/v1/facebook/events"


def _local_date(ts: int | None) -> str:
    if not ts:
        return ""
    # FB timestamps are UTC seconds; date-level is all we need for windowing.
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def _in_county(place_name: str, title: str, query: str) -> bool:
    """Keep events that look local. Lenient — curation makes the final call."""
    hay = f"{place_name} {title} {query}".lower()
    return any(alias.strip() in hay for aliases in TOWNS.values() for alias in aliases) or \
        "iowa city" in hay or "johnson county" in hay


def _to_event(raw: dict, source_id: str, query: str, d0: date, d1: date) -> Event | None:
    if raw.get("is_past") or raw.get("is_online"):
        return None
    ts = raw.get("start_timestamp")
    start_iso = _local_date(ts)
    if ts:
        sday = datetime.fromtimestamp(ts, tz=timezone.utc).date()
        if not (d0 <= sday <= d1):
            return None

    place = (raw.get("event_place") or {}).get("contextual_name") or ""
    title = clean(raw.get("name", ""))
    if not _in_county(place, title, query):
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
    resp = requests.get(url, params=params, headers={"x-api-key": key, "User-Agent": USER_AGENT}, timeout=40)
    resp.raise_for_status()
    return resp.json()


def fetch_all(d0: date, d1: date, max_calls: int | None, only: str | None = None) -> dict:
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
                body = _get(SEARCH, {"query": src["fb_query"]}, key)
                q = src["fb_query"]
            elif src.get("fb_url"):
                body = _get(PAGE, {"url": src["fb_url"]}, key)
                q = src["fb_url"]
            else:
                report.append({"source": src["id"], "status": "skipped_no_query"})
                continue
            credits = body.get("credits_remaining", credits)
            raws = body.get("events", [])
            got = [e for e in (_to_event(r, src["id"], q, d0, d1) for r in raws) if e]
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
    ap.add_argument("--max-calls", type=int, default=None, help="cap credits spent this run")
    ap.add_argument("--source", help="only this source id")
    args = ap.parse_args()

    d0, d1 = parse_window(args.start, args.days)
    data = fetch_all(d0, d1, args.max_calls, only=args.source)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
