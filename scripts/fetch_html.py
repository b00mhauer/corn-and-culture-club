"""Fetch events from web sources that aren't plain ICS feeds.

Two pluggable parsers, chosen per source via the `parser` field in sources.yaml:

  parser: localist  -> Localist JSON API ({feed}/api/2/events). Used by University
                       of Iowa calendars (calendar.uiowa.edu, hancher.uiowa.edu).
  parser: jsonld    -> schema.org Event data embedded as <script ld+json>. Works
                       for venue sites that expose it server-side.

NOTE on this environment: many local calendars are JavaScript-rendered SPAs whose
events never appear in server HTML, and headless rendering is blocked here. Those
sources are covered instead through Facebook events (fetch_facebook.py) and the
research skill's web-search discovery. This module handles the sources that DO
serve structured data over plain HTTP.

    uv run python scripts/fetch_html.py --start 2026-07-09 --days 7
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date

import requests

from ccc_core import (
    BROWSER_UA,
    USER_AGENT,
    Event,
    clean,
    dedupe,
    enrich,
    parse_window,
    sources_by,
    to_central,
)


def _get(url: str, params: dict | None = None) -> requests.Response:
    for ua in (USER_AGENT, BROWSER_UA):
        r = requests.get(url, params=params, headers={"User-Agent": ua}, timeout=30)
        if r.status_code == 200:
            return r
        if r.status_code not in (403, 406, 429):
            r.raise_for_status()
    r.raise_for_status()
    return r


# --- Localist -----------------------------------------------------------------

def parse_localist(src: dict, d0: date, d1: date) -> list[Event]:
    base = src["feed"].rstrip("/")
    days = (d1 - d0).days + 1
    body = _get(f"{base}/api/2/events", {"days": days, "start": d0.isoformat(), "pp": 100}).json()
    out: list[Event] = []
    for wrap in body.get("events", []):
        ev = wrap.get("event", wrap)
        insts = ev.get("event_instances") or []
        start = ""
        if insts:
            start = to_central(iso=insts[0].get("event_instance", {}).get("start", "") or None)
        sday = start[:10]
        if not (d0.isoformat() <= sday <= d1.isoformat()):
            continue
        e = Event(
            title=clean(ev.get("title", "")),
            start=start,
            source=src["id"],
            source_name=src["name"],
            venue=clean(ev.get("location_name") or ev.get("venue_name") or "") or None,
            town=src.get("town") if src.get("town") not in ("county", "regional") else None,
            url=ev.get("localist_url") or ev.get("url"),
            description=clean(ev.get("description_text") or "")[:1500],
            cost="free" if ev.get("free") else "unknown",
            is_free=True if ev.get("free") else None,
        )
        out.append(enrich(e, src.get("audience", "general")))
    return out


# --- schema.org JSON-LD -------------------------------------------------------

_LD = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', re.S | re.I)
_EVENT_TYPES = {"Event", "Festival", "MusicEvent", "TheaterEvent", "SocialEvent",
                "ChildrensEvent", "EducationEvent", "ExhibitionEvent", "ComedyEvent"}


def _walk_ld(node, found: list[dict]) -> None:
    if isinstance(node, list):
        for n in node:
            _walk_ld(n, found)
    elif isinstance(node, dict):
        if "@graph" in node:
            _walk_ld(node["@graph"], found)
        t = node.get("@type", "")
        types = {t} if isinstance(t, str) else set(t or [])
        if types & _EVENT_TYPES:
            found.append(node)


def _ld_to_event(ev: dict, src: dict, d0: date, d1: date) -> Event | None:
    """Convert one schema.org Event object to our Event (windowed)."""
    start = to_central(iso=str(ev.get("startDate", "")) or None)
    sday = start[:10]
    if not sday or not (d0.isoformat() <= sday <= d1.isoformat()):
        return None
    loc = ev.get("location") or {}
    if isinstance(loc, list):
        loc = loc[0] if loc else {}
    venue = loc.get("name") if isinstance(loc, dict) else None
    offers = ev.get("offers") or {}
    if isinstance(offers, list):
        offers = offers[0] if offers else {}
    price = offers.get("price") if isinstance(offers, dict) else None
    is_free = (str(price) in ("0", "0.0", "0.00")) if price is not None else None
    e = Event(
        title=clean(ev.get("name", "")),
        start=start,
        source=src["id"],
        source_name=src["name"],
        venue=clean(venue or "") or None,
        town=src.get("town") if src.get("town") not in ("county", "regional") else None,
        url=ev.get("url") or src["url"],
        description=clean(str(ev.get("description", "")))[:1500],
        cost="free" if is_free else ("paid" if price else "unknown"),
        is_free=is_free,
    )
    return enrich(e, src.get("audience", "general"))


def _extract_ld_events(html: str) -> list[dict]:
    found: list[dict] = []
    for block in _LD.findall(html):
        try:
            _walk_ld(json.loads(block), found)
        except (json.JSONDecodeError, TypeError):
            continue
    return found


def parse_jsonld(src: dict, d0: date, d1: date) -> list[Event]:
    events = (_ld_to_event(ev, src, d0, d1) for ev in _extract_ld_events(_get(src["url"]).text))
    return [e for e in events if e]


# --- WhoFi (North Liberty & Solon libraries) ---------------------------------
# ICS export is disabled; the featured list links to event pages that each carry
# schema.org JSON-LD. Fetch the list, then each event page (capped).

def parse_whofi(src: dict, d0: date, d1: date, cap: int = 40) -> list[Event]:
    listing = _get(src["feed"]).text
    host = src["feed"].split("/calendar")[0]
    ids: list[str] = []
    for m in re.findall(r"/calendar/event/(\d+)", listing):
        if m not in ids:
            ids.append(m)
    out: list[Event] = []
    for eid in ids[:cap]:
        event_url = f"{host}/calendar/event/{eid}"
        try:
            html = _get(event_url).text
        except requests.RequestException:
            continue
        for ev in _extract_ld_events(html):
            e = _ld_to_event(ev, src, d0, d1)
            if e:
                e.url = event_url  # link to the event's own page, not the generic list
                out.append(e)
    return out


# --- ICPL (Iowa City Public Library) custom vbapi ----------------------------

_ICPL_AGE = {
    "babies": "0-4", "toddlers": "0-4", "preschool": "0-4", "preschoolers": "0-4",
    "kids": "5-11", "children": "5-11", "school age": "5-11",
    "tweens": "12-18", "teens": "12-18", "young adults": "12-18",
    "families": "all", "all ages": "all", "everyone": "all",
}


def parse_icpl_vbapi(src: dict, d0: date, d1: date) -> list[Event]:
    body = _get(src["feed"], {"start": d0.isoformat(), "end": d1.isoformat()}).json()
    out: list[Event] = []
    for ev in body.get("events", []):
        if str(ev.get("visible_to_public")) not in ("1", "True", "true"):
            continue
        title = clean(ev.get("title", ""))
        start = str(ev.get("start", ""))
        if not title or not start[:10]:
            continue
        if not (d0.isoformat() <= start[:10] <= d1.isoformat()):
            continue
        bands: list[str] = []
        age = ev.get("age")
        labels = age.values() if isinstance(age, dict) else (age if isinstance(age, list) else [])
        for lbl in labels:
            b = _ICPL_AGE.get(str(lbl).strip().lower())
            if b and b not in bands:
                bands.append(b)
        locs = ev.get("locations")
        venue = "Iowa City Public Library"
        if isinstance(locs, dict) and locs:
            venue = str(next(iter(locs.values())))
        elif isinstance(locs, list) and locs:
            first = locs[0]
            venue = first.get("name") if isinstance(first, dict) else str(first)
        path = ev.get("path") or ""
        e = Event(
            title=title,
            start=start,
            end=str(ev.get("end")) or None,
            source=src["id"],
            source_name=src["name"],
            venue=clean(venue),
            town="Iowa City",
            url=("https://www.icpl.org" + path) if path.startswith("/") else (path or src["url"]),
            description=clean(str(ev.get("description", "")))[:1500],
            age_bands=bands,
        )
        out.append(enrich(e, src.get("audience", "family")))
    return out


# --- SceneThink (Little Village) ---------------------------------------------

def _local_signal(*parts: str) -> bool:
    """True if any county-town name appears (SceneThink/aggregators bleed regional)."""
    from ccc_core import TOWNS

    hay = " ".join(p.lower() for p in parts if p)
    if any(a.strip() in hay for al in TOWNS.values() for a in al):
        return True
    return "iowa city" in hay or "johnson county" in hay


def parse_scenethink(src: dict, d0: date, d1: date) -> list[Event]:
    body = _get(src["feed"], {"limit": 300}).json()
    out: list[Event] = []
    for wrap in body.get("events", []):
        s = wrap.get("_source", {})
        start = to_central(iso=str(s.get("starttime", "")) or None)
        sday = start[:10]
        if not sday or not (d0.isoformat() <= sday <= d1.isoformat()):
            continue
        venue = s.get("venue") or {}
        vname = venue.get("name") if isinstance(venue, dict) else None
        vcity = venue.get("city") if isinstance(venue, dict) else None
        title = clean(s.get("name", ""))
        if not _local_signal(vname or "", vcity or "", title):
            continue  # drop regional bleed (Des Moines, etc.)
        eid = s.get("id")
        e = Event(
            title=title,
            start=start,
            source=src["id"],
            source_name=src["name"],
            venue=clean(vname or "") or None,
            town=vcity if vcity else None,
            url=(f"https://little-village.scenethink.com/little-village/calendars/all-events/{eid}"
                 if eid else src["url"]),
            description=clean(s.get("summary") or s.get("description") or "")[:1500],
        )
        out.append(enrich(e, src.get("audience", "general")))
    return out


# --- CivicPlus event RSS (Coralville) ----------------------------------------

_EVENT_DATE = re.compile(r"Event date:\s*</strong>\s*([A-Za-z]+ \d{1,2},? \d{4})", re.I)
_EVENT_TIME = re.compile(r"Event Time:\s*</strong>\s*(\d{1,2}:\d{2}\s*[AP]M)", re.I)


def parse_civicplus_rss(src: dict, d0: date, d1: date) -> list[Event]:
    import xml.etree.ElementTree as ET
    from datetime import datetime as _dt

    xml = _get(src["feed"]).content
    root = ET.fromstring(xml)
    out: list[Event] = []
    for item in root.findall(".//item"):
        title = clean(item.findtext("title") or "")
        desc = item.findtext("description") or ""
        link = (item.findtext("link") or src["url"]).strip()
        # The event date lives in the description, NOT in pubDate (that's the post date).
        md = _EVENT_DATE.search(desc)
        if not md:
            continue
        try:
            day = _dt.strptime(md.group(1).replace(",", ""), "%B %d %Y").date()
        except ValueError:
            continue
        if not (d0 <= day <= d1):
            continue
        mt = _EVENT_TIME.search(desc)
        start = f"{day.isoformat()}T{_dt.strptime(mt.group(1).strip(), '%I:%M %p').strftime('%H:%M:%S')}" \
            if mt else day.isoformat()
        e = Event(
            title=title,
            start=start,
            source=src["id"],
            source_name=src["name"],
            town=src.get("town"),
            url=link,
            description=clean(desc)[:1500],
        )
        out.append(enrich(e, src.get("audience", "general")))
    return out


PARSERS = {
    "localist": parse_localist,
    "jsonld": parse_jsonld,
    "scenethink": parse_scenethink,
    "civicplus_rss": parse_civicplus_rss,
    "whofi": parse_whofi,
    "icpl_vbapi": parse_icpl_vbapi,
}


def fetch_all(d0: date, d1: date, only: str | None = None) -> tuple[list[Event], list[dict]]:
    events: list[Event] = []
    report: list[dict] = []
    for src in sources_by(method="html"):
        parser = src.get("parser")
        if only and src["id"] != only:
            continue
        if parser not in PARSERS:
            report.append({"source": src["id"], "status": "skipped_no_parser"})
            continue
        try:
            got = PARSERS[parser](src, d0, d1)
            events.extend(got)
            report.append({"source": src["id"], "status": "ok", "parser": parser, "count": len(got)})
        except Exception as exc:  # noqa: BLE001
            report.append({"source": src["id"], "status": "error", "parser": parser, "error": str(exc)[:160]})
    return dedupe(events), report


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch events from HTML/API sources.")
    ap.add_argument("--start")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--source")
    args = ap.parse_args()
    d0, d1 = parse_window(args.start, args.days)
    events, report = fetch_all(d0, d1, only=args.source)
    print(json.dumps({
        "window": {"start": d0.isoformat(), "end": d1.isoformat()},
        "report": report,
        "count": len(events),
        "events": [e.to_dict() for e in events],
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
