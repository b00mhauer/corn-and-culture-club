"""Render a draft.md edition into a styled, email-safe edition.html.

Applies the Corn & Culture Club design system (style/design-system.md): warm
Iowa palette, corn dividers, FREE badges, single 600px column. Output works in a
browser and degrades gracefully in email clients (beehiiv handles final inlining
at send time).

    uv run python scripts/render_preview.py --start 2026-07-09
    uv run python scripts/render_preview.py data/editions/2026-07-09/draft.md
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import markdown as md
import yaml

from ccc_core import DATA

# --- palette (from design-system.md) -----------------------------------------
C = {
    "gold": "#F2B705",
    "red": "#A62B1F",
    "green": "#3E6B3A",
    "sky": "#5B8FB0",
    "cream": "#FBF7EC",
    "ink": "#2A2622",
    "stone": "#6E655B",
    "card": "#FFFFFF",
}


def split_front_matter(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return {}, text
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


def _week_label(start: str) -> str:
    try:
        d0 = datetime.strptime(start, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        d0 = date.today()
    d1 = d0 + timedelta(days=6)
    same_month = d0.month == d1.month
    left = d0.strftime("%B %-d")
    right = d1.strftime("%-d" if same_month else "%B %-d")
    return f"Week of {left}–{right}, {d1.year}"


def _style_dividers(html: str, critter: str) -> str:
    """Turn emoji-only paragraphs (e.g. '🌽 🌽 🌽') into styled dividers."""
    def repl(m: re.Match) -> str:
        inner = m.group(1).strip()
        # only-emoji / whitespace, no letters or digits
        if inner and not re.search(r"[A-Za-z0-9]", inner):
            return (
                f'<div style="text-align:center;font-size:20px;letter-spacing:10px;'
                f'margin:34px 0 30px;line-height:1;">{inner}</div>'
            )
        return m.group(0)

    return re.sub(r"<p>(.*?)</p>", repl, html, flags=re.S)


def _decorate(html: str) -> str:
    # FREE / cost badges (they come through as <code>…</code>)
    def badge(m: re.Match) -> str:
        txt = m.group(1)
        bg = C["gold"] if txt.upper() == "FREE" else C["green"]
        fg = C["ink"] if txt.upper() == "FREE" else "#FFFFFF"
        return (
            f'<span style="background:{bg};color:{fg};font-weight:700;font-size:11px;'
            f'letter-spacing:.5px;padding:2px 8px;border-radius:999px;'
            f'white-space:nowrap;">{txt}</span>'
        )

    html = re.sub(r"<code>(.*?)</code>", badge, html)

    # Section headers
    html = html.replace(
        "<h2>",
        f'<h2 style="font-family:Georgia,serif;color:{C["red"]};font-size:21px;'
        f'margin:34px 0 12px;line-height:1.25;">',
    )
    # Deep-dive etc. h3 if any
    html = html.replace(
        "<h3>",
        f'<h3 style="font-family:Georgia,serif;color:{C["ink"]};font-size:17px;'
        f'margin:22px 0 8px;">',
    )
    # Event cards (blockquotes)
    html = html.replace(
        "<blockquote>",
        f'<blockquote style="margin:0 0 14px;padding:14px 16px;background:{C["card"]};'
        f'border-left:4px solid {C["gold"]};border-radius:8px;'
        f'box-shadow:0 1px 3px rgba(42,38,34,.08);">',
    )
    # Links
    html = re.sub(
        r"<a ",
        f'<a style="color:{C["red"]};text-decoration:underline;" ',
        html,
    )
    # Paragraphs + list items → readable body
    html = html.replace(
        "<p>", f'<p style="margin:0 0 12px;color:{C["ink"]};font-size:16px;line-height:1.55;">'
    )
    html = html.replace(
        "<li>", f'<li style="margin:0 0 8px;color:{C["ink"]};font-size:16px;line-height:1.5;">'
    )
    # Blockquote inner paragraphs: tighten
    html = html.replace(
        f'<blockquote style="margin:0 0 14px;padding:14px 16px;background:{C["card"]};'
        f'border-left:4px solid {C["gold"]};border-radius:8px;'
        f'box-shadow:0 1px 3px rgba(42,38,34,.08);"><p style="margin:0 0 12px;'
        f'color:{C["ink"]};font-size:16px;line-height:1.55;">',
        f'<blockquote style="margin:0 0 14px;padding:14px 16px;background:{C["card"]};'
        f'border-left:4px solid {C["gold"]};border-radius:8px;'
        f'box-shadow:0 1px 3px rgba(42,38,34,.08);"><p style="margin:0 0 4px;'
        f'color:{C["ink"]};font-size:15px;line-height:1.5;">',
    )
    return html


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{subject}</title>
<style>
  body {{ margin:0; padding:0; background:{cream}; }}
  a {{ color:{red}; }}
  @media (max-width:620px) {{ .wrap {{ width:100% !important; }} .pad {{ padding:20px !important; }} }}
</style>
</head>
<body style="margin:0;padding:0;background:{cream};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
<span style="display:none!important;visibility:hidden;opacity:0;height:0;width:0;overflow:hidden;">{preheader}</span>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{cream};">
<tr><td align="center" style="padding:24px 12px;">
  <table role="presentation" class="wrap" width="600" cellpadding="0" cellspacing="0" style="width:600px;max-width:600px;background:{cream};">
    <!-- masthead -->
    <tr><td style="text-align:center;padding:8px 0 18px;">
      <div style="font-size:30px;">🌽</div>
      <div style="font-family:Georgia,serif;font-size:30px;font-weight:700;color:{red};letter-spacing:.5px;">Corn &amp; Culture Club</div>
      <div style="color:{stone};font-size:13px;margin-top:4px;">Johnson County, Iowa &nbsp;·&nbsp; {week}</div>
      <div style="height:3px;background:{gold};width:80px;margin:14px auto 0;border-radius:2px;"></div>
    </td></tr>
    <!-- body -->
    <tr><td class="pad" style="padding:6px 8px 8px;">
      {body}
    </td></tr>
    <!-- footer -->
    <tr><td style="padding:26px 12px 10px;text-align:center;color:{stone};font-size:12px;line-height:1.6;">
      <div style="font-size:16px;margin-bottom:8px;">🌽</div>
      You're getting this because you love this corner of Iowa.<br>
      Corn &amp; Culture Club · Johnson County, IA<br>
      <span style="color:{stone};">Reply with a tip · Forward to a fellow parent</span>
    </td></tr>
  </table>
</td></tr>
</table>
</body>
</html>
"""


def render(draft_path: Path) -> tuple[str, dict]:
    fm, body_md = split_front_matter(draft_path.read_text())
    critter = fm.get("critter", "🌽")
    # nl2br keeps each line of an event card (name / time / blurb / link) on its
    # own line instead of collapsing them into one run of text.
    body_html = md.markdown(body_md, extensions=["extra", "sane_lists", "nl2br"])
    body_html = _style_dividers(body_html, critter)
    body_html = _decorate(body_html)

    html = TEMPLATE.format(
        subject=fm.get("subject", "Corn & Culture Club"),
        preheader=fm.get("preheader", ""),
        week=_week_label(fm.get("edition_start", "")),
        body=body_html,
        **C,
    )
    return html, fm


def main() -> int:
    ap = argparse.ArgumentParser(description="Render draft.md into styled edition.html.")
    ap.add_argument("draft", nargs="?", help="path to draft.md")
    ap.add_argument("--start", help="edition start date (finds data/editions/<start>/draft.md)")
    args = ap.parse_args()

    if args.draft:
        draft_path = Path(args.draft)
    elif args.start:
        draft_path = DATA / "editions" / args.start / "draft.md"
    else:
        ap.error("provide a draft path or --start")

    if not draft_path.exists():
        ap.error(f"no draft at {draft_path}")

    html, fm = render(draft_path)
    out = draft_path.parent / "edition.html"
    out.write_text(html)
    print(f"Wrote {out}  ({len(html):,} bytes)")
    print(f"Subject:   {fm.get('subject','')}")
    print(f"Preheader: {fm.get('preheader','')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
