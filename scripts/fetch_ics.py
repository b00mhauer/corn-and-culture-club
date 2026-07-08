"""Fetch + parse ICS calendar feeds listed in data/sources.yaml.

Coverage-floor gathering only. Emits normalized Event dicts within a date window.
Run standalone to smoke-test a single source:

    uv run python scripts/fetch_ics.py --source iowa-childrens-museum --days 14
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime

import requests
from icalendar import Calendar

from ccc_core import (
    BROWSER_UA,
    USER_AGENT,
    Event,
    clean,
    enrich,
    parse_window,
    sources_by,
)


def _fetch(url: str) -> bytes:
    """GET a feed, retrying with a browser UA if the origin bot-blocks us."""
    for ua in (USER_AGENT, BROWSER_UA):
        resp = requests.get(url, headers={"User-Agent": ua}, timeout=30)
        if resp.status_code == 200:
            return resp.content
        if resp.status_code not in (403, 406, 429):
            resp.raise_for_status()
    resp.raise_for_status()
    return b""


def _as_date(value) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return None


def _iso(value) -> tuple[str, bool]:
    """Return (iso_string, all_day)."""
    if isinstance(value, datetime):
        return value.isoformat(), False
    if isinstance(value, date):
        return value.isoformat(), True
    return "", False


def fetch_source(source: dict, d0: date, d1: date) -> list[Event]:
    raw = _fetch(source["feed"])
    cal = Calendar.from_ical(raw)
    events: list[Event] = []

    for comp in cal.walk("VEVENT"):
        dtstart = comp.get("DTSTART")
        if dtstart is None:
            continue
        start_val = dtstart.dt
        sday = _as_date(start_val)
        if sday is None or not (d0 <= sday <= d1):
            continue

        start_iso, all_day = _iso(start_val)
        end_iso = None
        if comp.get("DTEND") is not None:
            end_iso, _ = _iso(comp.get("DTEND").dt)

        ev = Event(
            title=clean(str(comp.get("SUMMARY", ""))),
            start=start_iso,
            end=end_iso,
            all_day=all_day,
            source=source["id"],
            source_name=source["name"],
            venue=clean(str(comp.get("LOCATION", ""))) or None,
            town=source.get("town") if source.get("town") not in ("county", "regional") else None,
            url=str(comp.get("URL", "")) or source["url"],
            description=clean(str(comp.get("DESCRIPTION", "")))[:1500],
        )
        events.append(enrich(ev, source.get("audience", "general")))

    return events


def fetch_all(d0: date, d1: date, only: str | None = None) -> tuple[list[Event], list[dict]]:
    """Return (events, per_source_report)."""
    events: list[Event] = []
    report: list[dict] = []
    for src in sources_by(method="ics"):
        if only and src["id"] != only:
            continue
        if not src.get("feed"):
            report.append({"source": src["id"], "status": "skipped_no_feed"})
            continue
        try:
            got = fetch_source(src, d0, d1)
            events.extend(got)
            report.append({"source": src["id"], "status": "ok", "count": len(got)})
        except Exception as exc:  # noqa: BLE001 — one bad feed shouldn't kill the run
            report.append({"source": src["id"], "status": "error", "error": str(exc)[:200]})
    return events, report


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch ICS event feeds into normalized JSON.")
    ap.add_argument("--start", help="YYYY-MM-DD (default: today)")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--source", help="only this source id")
    args = ap.parse_args()

    d0, d1 = parse_window(args.start, args.days)
    events, report = fetch_all(d0, d1, only=args.source)
    print(json.dumps({
        "window": {"start": d0.isoformat(), "end": d1.isoformat()},
        "report": report,
        "count": len(events),
        "events": [e.to_dict() for e in events],
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
