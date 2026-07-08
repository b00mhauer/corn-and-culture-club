"""Fetch recent Instagram posts for curated handles via Scrape Creators.

These are DISCOVERY SIGNALS, not finished events. Many local orgs post dated
event round-ups in their captions (and image-only flyers); the ccc-research
skill reads this output and extracts real events — including analyzing the
images, per the Catskill Crew video.

Costs ~1 credit per handle per run, so it's opt-in and cost-capped. Needs
SCRAPE_CREATORS_API_KEY in .env.

    uv run python scripts/fetch_instagram.py --days 21 --max-handles 6
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone

import requests

from ccc_core import USER_AGENT, clean, load_sources, require_key

API = "https://api.scrapecreators.com/v1/instagram/user/posts"


def _caption(node: dict) -> str:
    edges = node.get("edge_media_to_caption", {}).get("edges", [])
    return clean(edges[0]["node"]["text"]) if edges else ""


def fetch_handle(handle: str, key: str, since_ts: float) -> tuple[list[dict], int | None, str]:
    """Return (recent_posts, credits_remaining, status)."""
    resp = requests.get(
        API,
        params={"handle": handle},
        headers={"x-api-key": key, "User-Agent": USER_AGENT},
        timeout=30,
    )
    if resp.status_code == 404:
        return [], None, "not_found"
    resp.raise_for_status()
    body = resp.json()
    credits = body.get("credits_remaining")

    posts: list[dict] = []
    for edge in body.get("posts", []):
        node = edge.get("node", edge)
        ts = node.get("taken_at_timestamp") or node.get("taken_at")
        if not ts or ts < since_ts:
            continue
        shortcode = node.get("shortcode") or node.get("code")
        posts.append({
            "handle": handle,
            "shortcode": shortcode,
            "url": node.get("url") or (f"https://www.instagram.com/p/{shortcode}/" if shortcode else None),
            "posted": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
            "caption": _caption(node),
            "image_url": node.get("display_url"),
            "is_video": node.get("is_video", False),
            "location": (node.get("location") or {}).get("name") if node.get("location") else None,
            "flagged_upcoming_event": node.get("has_upcoming_event", False),
            "likes": node.get("edge_media_preview_like", {}).get("count"),
        })
    return posts, credits, "ok"


def fetch_all(days: int, max_handles: int | None, only: str | None = None) -> dict:
    key = require_key("SCRAPE_CREATORS_API_KEY")
    since = (datetime.now(tz=timezone.utc) - timedelta(days=days)).timestamp()

    handles = [s for s in load_sources() if s.get("method") == "instagram" and s.get("handle")]
    if only:
        handles = [s for s in handles if s["id"] == only or s.get("handle") == only]
    if max_handles:
        handles = handles[:max_handles]

    results: list[dict] = []
    report: list[dict] = []
    credits_left: int | None = None
    for src in handles:
        try:
            posts, credits, status = fetch_handle(src["handle"], key, since)
            credits_left = credits if credits is not None else credits_left
            results.append({"source": src["id"], "handle": src["handle"], "posts": posts})
            report.append({"handle": src["handle"], "status": status, "recent_posts": len(posts)})
        except Exception as exc:  # noqa: BLE001 — one bad handle shouldn't kill the run
            report.append({"handle": src["handle"], "status": "error", "error": str(exc)[:160]})

    return {
        "window_days": days,
        "credits_remaining": credits_left,
        "report": report,
        "signals": results,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch Instagram discovery signals via Scrape Creators.")
    ap.add_argument("--days", type=int, default=21, help="only posts newer than this")
    ap.add_argument("--max-handles", type=int, default=None, help="cap credits spent this run")
    ap.add_argument("--handle", help="only this handle/source id")
    args = ap.parse_args()

    data = fetch_all(args.days, args.max_handles, only=args.handle)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
