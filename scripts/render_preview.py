"""Render a draft.md edition into a styled, visual edition.html.

Design: Morning Brew editorial energy, Iowa City themed, high-end-outdoors-brand
restraint. Hawkeye black-and-gold with a warm oat base and a pine-green accent,
an Old Capitol dome masthead, a per-day weather strip, and clean line-icons per
event mode. Optimized for the web/preview; beehiiv adapts the email at send.

    uv run python scripts/render_preview.py --start 2026-07-09
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import markdown as md
import yaml

from ccc_core import DATA

# --- palette (Hawkeye black + gold, warm oat, pine) --------------------------
C = {
    "bg": "#F1ECDF",       # warm oat
    "panel": "#FFFFFF",
    "ink": "#17150F",      # warm near-black (Hawkeye black)
    "muted": "#6E6454",
    "line": "#E4DAC6",
    "gold": "#D9A408",     # deep premium gold
    "goldsoft": "#F7ECC9", # soft gold fill
    "green": "#345E3B",    # prairie-green (links / free)
    "brick": "#A63A28",    # alarm only (deadlines) — rare
    "cream": "#F1ECDF",
}
# Brand type: webfonts for the web page, system stacks as email-safe fallback.
FONT_DISPLAY = "'Zilla Slab',Georgia,'Times New Roman',serif"   # masthead / headlines
FONT_LABEL = "'Work Sans',-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"  # labels / meta / chips
FONT_PROSE = "'Newsreader',Georgia,'Times New Roman',serif"     # reading prose
SANS = FONT_LABEL  # back-compat alias used throughout
FONTS_LINK = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?'
    'family=Zilla+Slab:wght@600;700&'
    'family=Work+Sans:wght@600;700;800&'
    'family=Newsreader:opsz,wght@6..72,400;6..72,500&display=swap" rel="stylesheet">'
)

REPO = Path(__file__).resolve().parent.parent

# --- inline SVG line icons (currentColor, stroke) ----------------------------
_ICONS = {
    # weather
    "sun": '<circle cx="12" cy="12" r="4.2"/><path d="M12 2v2M12 20v2M4.2 4.2l1.5 1.5M18.3 18.3l1.5 1.5M2 12h2M20 12h2M4.2 19.8l1.5-1.5M18.3 5.7l1.5-1.5"/>',
    "partly": '<circle cx="8.5" cy="8.5" r="3"/><path d="M8.5 1.8v1.6M2.3 8.5h1.6M4.1 4.1l1.1 1.1M13 4.1l-1.1 1.1"/><path d="M7 19h9a3.2 3.2 0 0 0 .3-6.4A4.5 4.5 0 0 0 8 12.5 3.3 3.3 0 0 0 7 19Z"/>',
    "cloud": '<path d="M7 18h10a3.5 3.5 0 0 0 .3-7A5 5 0 0 0 8 10.4 3.6 3.6 0 0 0 7 18Z"/>',
    "rain": '<path d="M7 15h10a3.5 3.5 0 0 0 .3-7A5 5 0 0 0 8 7.4 3.6 3.6 0 0 0 7 15Z"/><path d="M9 18l-1 2.5M13 18l-1 2.5M17 18l-1 2.5"/>',
    "storm": '<path d="M7 14h10a3.5 3.5 0 0 0 .3-7A5 5 0 0 0 8 6.4 3.6 3.6 0 0 0 7 14Z"/><path d="M12.5 13l-2.5 4h3l-2.5 4"/>',
    "snow": '<path d="M7 15h10a3.5 3.5 0 0 0 .3-7A5 5 0 0 0 8 7.4 3.6 3.6 0 0 0 7 15Z"/><path d="M9 19h.01M12 20.5h.01M15 19h.01"/>',
    # event modes
    "date": '<path d="M12 20.5S3.5 14.6 3.5 8.9A4.4 4.4 0 0 1 12 6.9a4.4 4.4 0 0 1 8.5 2c0 5.7-8.5 11.6-8.5 11.6Z"/>',
    "night": '<circle cx="7" cy="18" r="2.5"/><circle cx="17" cy="16" r="2.5"/><path d="M9.5 18V5l10-2v13"/>',
    "kids": '<circle cx="12" cy="8" r="5"/><path d="M12 13v5M10.5 20.5 12 18l1.5 2.5"/>',
    "community": '<circle cx="9" cy="8" r="3"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0M16 6.5a3 3 0 0 1 0 5.8M21.5 20a5.5 5.5 0 0 0-4-5.3"/>',
    "pin": '<path d="M12 21s7-5.7 7-11a7 7 0 1 0-14 0c0 5.3 7 11 7 11Z"/><circle cx="12" cy="10" r="2.5"/>',
    # brand: popcorn cluster ("What's poppin'" — Free & Cheap device)
    "popcorn": '<circle cx="9" cy="7" r="2.3"/><circle cx="14.5" cy="6.5" r="2.3"/><circle cx="12" cy="10" r="2.3"/><path d="M7.5 11.5 9 21h6l1.5-9.5"/>',
    "coffee": '<path d="M4 8h13v5a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5V8ZM17 9h2.2a2.3 2.3 0 0 1 0 4.6H17"/>',
    "school": '<path d="M12 3 2 8l10 5 10-5-10-5ZM6 10.5V16c0 1.3 2.7 3 6 3s6-1.7 6-3v-5.5"/>',
    "news": '<path d="M4 5h13v14H4zM17 8h3v9a2 2 0 0 1-2 2M8 9h5M8 12h5M8 15h3"/>',
}


def svg(name: str, size: int, color: str, sw: float = 1.7) -> str:
    inner = _ICONS.get(name, _ICONS["pin"])
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="{sw}" stroke-linecap="round" '
        f'stroke-linejoin="round" style="vertical-align:middle;">{inner}</svg>'
    )


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
    same = d0.month == d1.month
    return f"{d0.strftime('%b %-d')}–{d1.strftime('%-d' if same else '%b %-d')}, {d1.year}"


# --- weather strip -----------------------------------------------------------

def _wx_icon(short: str) -> str:
    s = short.lower()
    if "thunder" in s or "storm" in s:
        return "storm"
    if "snow" in s or "flurr" in s:
        return "snow"
    if "rain" in s or "shower" in s or "drizzle" in s:
        return "rain"
    if "partly" in s or "mostly sunny" in s or "mostly clear" in s:
        return "partly"
    if "sunny" in s or "clear" in s:
        return "sun"
    if "cloud" in s or "overcast" in s:
        return "cloud"
    return "partly"


def _day_label(name: str) -> str:
    first = name.split()[0]
    if first in ("This", "Today", "Tonight", "Overnight", "This"):
        return "Today"
    return first[:3]


def weather_strip(edition_dir: Path) -> str:
    cj = edition_dir / "candidates.json"
    if not cj.exists():
        return ""
    try:
        periods = json.loads(cj.read_text()).get("weather", {}).get("periods", [])
    except (json.JSONDecodeError, KeyError):
        return ""
    days = [p for p in periods if p.get("is_daytime")][:6]
    if not days:
        return ""
    cells = []
    for p in days:
        icon = _wx_icon(p.get("short", ""))
        cells.append(
            f'<td align="center" style="padding:6px 4px;">'
            f'<div style="font-size:10.5px;font-weight:800;letter-spacing:.8px;'
            f'text-transform:uppercase;color:{C["muted"]};">{_day_label(p["name"])}</div>'
            f'<div style="margin:6px 0 4px;">{svg(icon, 26, C["gold"])}</div>'
            f'<div style="font-size:15px;font-weight:800;color:{C["ink"]};">{p["temp"]}&deg;</div>'
            f"</td>"
        )
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="background:{C["panel"]};border:1px solid {C["line"]};border-radius:12px;'
        f'margin:0 0 6px;"><tr><td style="padding:12px 10px 4px;">'
        f'<div style="font-size:10.5px;font-weight:800;letter-spacing:1.4px;'
        f'text-transform:uppercase;color:{C["gold"]};text-align:center;padding-bottom:2px;">'
        f'This Week’s Forecast</div>'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
        f'{"".join(cells)}</tr></table>'
        f"</td></tr></table>"
    )


# --- chips + mode icon -------------------------------------------------------

def _chip(txt: str) -> str:
    t = txt.strip()
    up = t.upper()
    if up == "FREE":
        style = f"background:{C['green']};color:#FFFFFF;border:1px solid {C['green']};"
    elif t.startswith("$"):
        style = f"background:{C['gold']};color:{C['ink']};border:1px solid {C['gold']};"
    else:
        style = f"background:transparent;color:{C['muted']};border:1px solid {C['line']};"
    return (
        f'<span style="display:inline-block;{style}font-size:10px;font-weight:800;'
        f"letter-spacing:.6px;text-transform:uppercase;padding:2px 8px;border-radius:4px;"
        f'vertical-align:middle;white-space:nowrap;margin:0 4px 4px 0;">{t}</span>'
    )


def _mode_icon(name_line: str) -> str:
    s = name_line.upper()
    if "DATE NIGHT" in s:
        return "date"
    if "NIGHT OUT" in s:
        return "night"
    if "KIDS" in s:
        return "kids"
    if "ALL AGES" in s:
        return "community"
    return "pin"


# --- event cards -------------------------------------------------------------

def _one_card(inner: str) -> str:
    parts = [p.strip() for p in re.split(r"<br\s*/?>", inner) if p.strip()]
    if not parts:
        return ""
    link = parts.pop() if "<a " in parts[-1] else ""
    name = parts[0] if parts else ""
    meta = parts[1] if len(parts) > 1 else ""
    hook = " ".join(parts[2:]) if len(parts) > 2 else ""
    icon = _mode_icon(name)

    rows = [
        f'<div style="font-size:16px;font-weight:800;line-height:1.3;'
        f'color:{C["ink"]};margin-bottom:5px;">{name}</div>'
    ]
    if meta:
        rows.append(
            f'<div style="font-size:11px;font-weight:700;letter-spacing:.6px;'
            f'text-transform:uppercase;color:{C["muted"]};margin-bottom:7px;">{meta}</div>'
        )
    if hook:
        rows.append(f'<div style="font-size:15px;line-height:1.55;color:{C["ink"]};">{hook}</div>')
    if link:
        rows.append(f'<div style="margin-top:8px;font-size:13px;">{link}</div>')

    badge = (
        f'<div style="width:38px;height:38px;border-radius:10px;background:{C["goldsoft"]};'
        f'border:1px solid {C["line"]};text-align:center;line-height:38px;">'
        f'{svg(icon, 20, C["ink"])}</div>'
    )
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 10px;">'
        f'<tr><td style="background:{C["panel"]};border:1px solid {C["line"]};border-radius:12px;'
        f'padding:14px 16px;">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>'
        f'<td valign="top" width="50" style="padding-right:12px;">{badge}</td>'
        f'<td valign="top">{"".join(rows)}</td>'
        f"</tr></table></td></tr></table>"
    )


def _style_cards(html: str) -> str:
    def repl(m: re.Match) -> str:
        paras = re.findall(r"<p[^>]*>(.*?)</p>", m.group(1), flags=re.S)
        return "".join(_one_card(p) for p in paras) or m.group(0)

    return re.sub(r"<blockquote>(.*?)</blockquote>", repl, html, flags=re.S)


# section header icons by keyword
_SECTION_ICON = [
    ("date night", "date"), ("friends", "night"), ("community", "community"),
    ("outdoor", "community"), ("kids", "kids"), ("free", "popcorn"),
    ("cheap", "popcorn"), ("school", "school"), ("deep dive", "coffee"),
    ("bulletin", "news"), ("huddle", "sun"), ("forecast", "sun"),
]


def _section_icon(label: str) -> str:
    low = label.lower()
    for kw, name in _SECTION_ICON:
        if kw in low:
            return name
    return "pin"


def _decorate(html: str) -> str:
    html = re.sub(r"<code>(.*?)</code>", lambda m: _chip(m.group(1)), html)
    html = _style_cards(html)

    def h2(m: re.Match) -> str:
        label = m.group(1)
        icon = svg(_section_icon(label), 18, C["gold"])
        return (
            f'<div style="border-top:1px solid {C["line"]};margin:32px 0 0;"></div>'
            f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin:15px 0 13px;"><tr>'
            f'<td valign="middle" style="padding-right:8px;">{icon}</td>'
            f'<td valign="middle"><span style="font-family:{SANS};color:{C["ink"]};'
            f"font-size:13px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;"
            f'">{label}</span></td></tr></table>'
        )

    html = re.sub(r"<h2>(.*?)</h2>", h2, html, flags=re.S)
    html = re.sub(
        r"<h3>(.*?)</h3>",
        lambda m: f'<h3 style="font-family:{FONT_DISPLAY};color:{C["ink"]};font-size:19px;'
        f'font-weight:700;margin:22px 0 8px;line-height:1.3;">{m.group(1)}</h3>',
        html, flags=re.S,
    )
    html = re.sub(
        r"<a ", f'<a style="color:{C["green"]};font-weight:700;text-decoration:none;'
        f'border-bottom:1.5px solid {C["gold"]};" ', html,
    )
    # Reading prose (Huddle, Forecast, Deep Dive) in Newsreader; a touch larger.
    html = re.sub(
        r"<p>", f'<p style="margin:0 0 14px;color:{C["ink"]};font-family:{FONT_PROSE};'
        f'font-size:17px;line-height:1.6;">', html,
    )
    html = html.replace(
        "<li>", f'<li style="margin:0 0 9px;color:{C["ink"]};font-size:16px;line-height:1.55;">'
    )
    return html


TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{subject}</title>
{fonts}
<style>
  body {{ margin:0; padding:0; background:{bg}; }}
  @media (max-width:620px) {{ .wrap {{ width:100% !important; }} .pad {{ padding:20px !important; }} }}
</style>
</head>
<body style="margin:0;padding:0;background:{bg};font-family:{prose};">
<span style="display:none!important;visibility:hidden;opacity:0;height:0;width:0;overflow:hidden;">{preheader}</span>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{bg};">
<tr><td align="center" style="padding:24px 12px;">
  <table role="presentation" class="wrap" width="600" cellpadding="0" cellspacing="0" style="width:600px;max-width:600px;">

    <!-- masthead: brand header emblem + wordmark -->
    <tr><td style="padding:0;line-height:0;">
      <img src="{header_src}" width="600" alt="Corn &amp; Culture Club — the good stuff to do in greater Iowa City" style="display:block;width:100%;max-width:600px;border-radius:14px 14px 0 0;">
    </td></tr>
    <tr><td style="background:{ink};padding:0 20px 14px;text-align:center;">
      <div style="font-family:{label};font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#B9AE93;">{week}</div>
    </td></tr>

    <!-- headline + weather + body on panel -->
    <tr><td class="pad" style="background:{bg};padding:20px 6px 8px;">
      <div style="font-family:{display};font-size:26px;font-weight:700;line-height:1.22;color:{ink};margin:2px 4px 16px;">{headline}</div>
      {weather}
      {body}
    </td></tr>

    <!-- footer -->
    <tr><td style="padding:30px 8px 12px;color:{muted};font-size:12px;line-height:1.7;text-align:center;font-family:{label};">
      <div style="border-top:1px solid {line};margin-bottom:16px;"></div>
      <span style="font-weight:800;letter-spacing:1.4px;text-transform:uppercase;color:{ink};">Corn &amp; Culture Club</span><br>
      Ears to the ground on the good stuff around greater Iowa City.<br>
      Reply with a tip. Forward to a friend.
    </td></tr>
  </table>
</td></tr>
</table>
</body>
</html>
"""


def render(draft_path: Path) -> tuple[str, dict]:
    fm, body_md = split_front_matter(draft_path.read_text())
    body_html = md.markdown(body_md, extensions=["extra", "sane_lists", "nl2br"])
    # drop emoji-only paragraphs (legacy dividers)
    body_html = re.sub(
        r"<p[^>]*>([^A-Za-z0-9<]+)</p>", "", body_html)
    body_html = _decorate(body_html)

    headline = fm.get("subject", "This week in greater Iowa City")

    html = TEMPLATE.format(
        subject=fm.get("subject", "Corn & Culture Club"),
        preheader=fm.get("preheader", ""),
        week=_week_label(fm.get("edition_start", "")),
        headline=headline,
        weather=weather_strip(draft_path.parent),
        body=body_html,
        header_src=_masthead_src(),
        fonts=FONTS_LINK,
        display=FONT_DISPLAY,
        label=FONT_LABEL,
        prose=FONT_PROSE,
        sans=SANS,
        **C,
    )
    return html, fm


def _masthead_src() -> str:
    """The brand email-header asset, inlined as a data URI for the standalone
    preview. In production (beehiiv) this becomes a hosted URL."""
    import base64

    p = REPO / "style" / "assets" / "email-header-600x200.png"
    if p.exists():
        b64 = base64.b64encode(p.read_bytes()).decode()
        return f"data:image/png;base64,{b64}"
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Render draft.md into styled edition.html.")
    ap.add_argument("draft", nargs="?")
    ap.add_argument("--start")
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
    print(f"Subject: {fm.get('subject','')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
