"""Render a draft.md edition into a styled, email-safe edition.html.

Applies the Corn & Culture Club design system (style/design-system.md): a modern,
clean, editorial look in the spirit of local brands like Big Grove, Wilson's, and
Hawkeye black-and-gold. Warm bone background, near-black ink, a disciplined
green/gold accent, tight uppercase wordmark, airy flat cards, hairline rules,
minimal ornament. Works in a browser; beehiiv handles final inlining at send.

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

# --- palette (modern, warm, restrained) --------------------------------------
C = {
    "bg": "#F4F1EA",       # warm bone
    "surface": "#FFFFFF",  # cards
    "ink": "#1B1A17",      # near-black
    "muted": "#6E675B",    # warm gray, meta text
    "line": "#E4DDCF",     # hairline
    "green": "#2E5A3E",    # deep earthy green — primary accent
    "gold": "#C0891F",     # modern gold — secondary accent (corn + Hawkeye nod)
}

# System font stacks (email-safe, no webfonts). Tight sans reads modern.
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"


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


def _strip_emoji_dividers(html: str) -> str:
    """Delete emoji-only / symbol-only paragraphs. Separation is a design job."""
    def repl(m: re.Match) -> str:
        inner = re.sub(r"<br\s*/?>", "", m.group(1)).strip()
        if inner and not re.search(r"[A-Za-z0-9]", inner):
            return ""
        return m.group(0)

    return re.sub(r"<p[^>]*>(.*?)</p>", repl, html, flags=re.S)


def _chip(txt: str) -> str:
    """Render a `backtick token` as a small modern chip."""
    t = txt.strip()
    up = t.upper()
    if up == "FREE":
        style = f"background:{C['green']};color:#FFFFFF;border:1px solid {C['green']};"
    elif t.startswith("$"):
        style = f"background:{C['gold']};color:#FFFFFF;border:1px solid {C['gold']};"
    else:  # ages / neutral chips: outlined, quiet
        style = f"background:transparent;color:{C['muted']};border:1px solid {C['line']};"
    return (
        f'<span style="display:inline-block;{style}font-size:10.5px;font-weight:700;'
        f"letter-spacing:.6px;text-transform:uppercase;padding:2px 8px;border-radius:4px;"
        f'vertical-align:middle;white-space:nowrap;margin:0 4px 4px 0;">{t}</span>'
    )


def _one_card(inner: str) -> str:
    """Render one event (the lines of a single <p>) as a flat card."""
    parts = [p.strip() for p in re.split(r"<br\s*/?>", inner) if p.strip()]
    if not parts:
        return ""
    link = parts.pop() if "<a " in parts[-1] else ""
    name = parts[0] if parts else ""
    meta = parts[1] if len(parts) > 1 else ""
    hook = " ".join(parts[2:]) if len(parts) > 2 else ""

    rows = [
        f'<div style="font-size:16px;font-weight:700;line-height:1.3;'
        f'color:{C["ink"]};margin-bottom:5px;">{name}</div>'
    ]
    if meta:
        rows.append(
            f'<div style="font-size:11px;font-weight:600;letter-spacing:.7px;'
            f'text-transform:uppercase;color:{C["muted"]};margin-bottom:8px;">{meta}</div>'
        )
    if hook:
        rows.append(
            f'<div style="font-size:15px;line-height:1.55;color:{C["ink"]};">{hook}</div>'
        )
    if link:
        rows.append(f'<div style="margin-top:9px;font-size:13px;">{link}</div>')
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="margin:0 0 10px;"><tr><td style="background:{C["surface"]};'
        f'border:1px solid {C["line"]};border-radius:10px;padding:15px 17px;">'
        f'{"".join(rows)}</td></tr></table>'
    )


def _style_cards(html: str) -> str:
    """Turn each blockquote into flat cards. Markdown merges adjacent blockquotes
    into one <blockquote> with several <p> — render one card per <p>."""
    def repl(m: re.Match) -> str:
        paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", m.group(1), flags=re.S)
        cards = "".join(_one_card(p) for p in paragraphs)
        return cards or m.group(0)

    return re.sub(r"<blockquote>(.*?)</blockquote>", repl, html, flags=re.S)


def _decorate(html: str) -> str:
    html = re.sub(r"<code>(.*?)</code>", lambda m: _chip(m.group(1)), html)
    html = _style_cards(html)

    # Section headers: editorial eyebrow — thin rule, green uppercase label.
    def h2(m: re.Match) -> str:
        return (
            f'<div style="border-top:1px solid {C["line"]};margin:34px 0 14px;"></div>'
            f'<h2 style="font-family:{SANS};color:{C["green"]};font-size:13px;'
            f"font-weight:800;letter-spacing:1.6px;text-transform:uppercase;"
            f'margin:0 0 14px;line-height:1.2;">{m.group(1)}</h2>'
        )

    html = re.sub(r"<h2>(.*?)</h2>", h2, html, flags=re.S)
    html = re.sub(
        r"<h3>(.*?)</h3>",
        lambda m: f'<h3 style="font-family:{SANS};color:{C["ink"]};font-size:18px;'
        f'font-weight:700;margin:22px 0 8px;line-height:1.3;">{m.group(1)}</h3>',
        html,
        flags=re.S,
    )

    # Day sub-headings in Week Ahead → small gold kicker.
    html = re.sub(
        r"<p[^>]*>\s*<strong>([^<]{3,40})</strong>\s*</p>",
        lambda m: f'<div style="font-size:11px;font-weight:800;text-transform:uppercase;'
        f'letter-spacing:1.4px;color:{C["gold"]};margin:18px 0 9px;">{m.group(1)}</div>',
        html,
    )

    html = re.sub(
        r"<a ", f'<a style="color:{C["green"]};font-weight:700;text-decoration:none;'
        f'border-bottom:1px solid {C["line"]};" ', html
    )
    html = re.sub(
        r"<p>", f'<p style="margin:0 0 14px;color:{C["ink"]};font-size:16px;'
        f'line-height:1.62;">', html
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
<style>
  body {{ margin:0; padding:0; background:{bg}; }}
  @media (max-width:620px) {{ .wrap {{ width:100% !important; }} .pad {{ padding:22px !important; }} }}
</style>
</head>
<body style="margin:0;padding:0;background:{bg};font-family:{sans};">
<span style="display:none!important;visibility:hidden;opacity:0;height:0;width:0;overflow:hidden;">{preheader}</span>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{bg};">
<tr><td align="center" style="padding:30px 12px;">
  <table role="presentation" class="wrap" width="600" cellpadding="0" cellspacing="0" style="width:600px;max-width:600px;">
    <!-- nameplate -->
    <tr><td style="padding:2px 4px 16px;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
        <td style="font-family:{sans};font-size:19px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:{ink};">Corn <span style="color:{gold};">&amp;</span> Culture Club</td>
        <td align="right" style="font-family:{sans};font-size:11px;font-weight:600;letter-spacing:.8px;text-transform:uppercase;color:{muted};">{week}</td>
      </tr></table>
      <div style="border-top:2px solid {ink};margin-top:10px;"></div>
      <div style="font-family:{sans};font-size:11px;font-weight:600;letter-spacing:1.4px;text-transform:uppercase;color:{muted};padding-top:8px;">The good stuff to do with your kids in Johnson County, Iowa</div>
    </td></tr>
    <!-- body -->
    <tr><td class="pad" style="padding:8px 4px 8px;">
      {body}
    </td></tr>
    <!-- footer -->
    <tr><td style="padding:34px 4px 10px;color:{muted};font-size:12px;line-height:1.7;">
      <div style="border-top:1px solid {line};margin-bottom:18px;"></div>
      <span style="font-weight:800;letter-spacing:1.2px;text-transform:uppercase;color:{ink};">Corn &amp; Culture Club</span><br>
      Johnson County, Iowa. Written for parents, by a local who did the legwork.<br>
      Reply with a tip. Forward to a fellow parent.
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
    body_html = _strip_emoji_dividers(body_html)
    body_html = _decorate(body_html)

    html = TEMPLATE.format(
        subject=fm.get("subject", "Corn & Culture Club"),
        preheader=fm.get("preheader", ""),
        week=_week_label(fm.get("edition_start", "")),
        body=body_html,
        sans=SANS,
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
