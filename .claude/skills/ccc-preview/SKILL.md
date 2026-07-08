---
name: ccc-preview
description: >
  Render a Corn & Culture Club draft.md into a styled, email-safe edition.html.
  Use when asked to "preview the edition", "render the newsletter", "make the
  HTML", or see how an edition looks. Applies the Iowa design system (warm
  palette, corn dividers, FREE badges, single 600px column). Output:
  data/editions/<start>/edition.html.
---

# ccc-preview — render the edition

Turns a written `draft.md` into a good-looking HTML edition you can open in a
browser (and that degrades gracefully in email). This is the last step before
handing off to the newsletter platform.

## Run it

```bash
uv run python scripts/render_preview.py --start <YYYY-MM-DD>
# or: uv run python scripts/render_preview.py data/editions/<start>/draft.md
```

Writes `data/editions/<start>/edition.html`. The renderer:
- reads the `draft.md` YAML frontmatter (`subject`, `preheader`, `critter`,
  `edition_start`) and the markdown body,
- converts markdown → HTML (line breaks preserved so each event card keeps its
  name / time / blurb / link on separate lines),
- applies `style/design-system.md`: masthead, barn-red section headers, gold
  `FREE` badges, event cards with a corn-gold left border, emoji dividers, a
  hidden preheader span, and a footer.

## Verify it actually looks right (don't skip)
Screenshot it — reading the HTML source is not enough:

```bash
uv run --with playwright python - <<'PY'
from playwright.sync_api import sync_playwright
import pathlib
url = pathlib.Path("data/editions/<start>/edition.html").resolve().as_uri()
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/opt/pw-browsers/chromium")
    pg = b.new_page(viewport={"width":640,"height":1400}, device_scale_factor=2)
    pg.goto(url); pg.screenshot(path="/tmp/edition.png", full_page=True); b.close()
PY
```
Then look at `/tmp/edition.png`. Check: masthead reads right, cards are clean
(one line each for name/time/blurb), FREE badges pop, dividers are centered, no
text collapsed together, mobile width holds.

## Design system knobs
All colors + layout live in `scripts/render_preview.py` (palette `C`) and
`style/design-system.md`. To restyle, change those — keep it email-safe:
single column ≤600px, inline-ish styles, system fonts, no external assets.

## Handing off to the platform (Phase 4)
`edition.html` is the paste-ready artifact. In beehiiv you paste the body / use
it as the design reference, then schedule. When beehiiv API automation is added,
`ccc-publish` will push this HTML directly.

## Notes
- Email clients vary; beehiiv does final CSS inlining at send. This file is the
  faithful browser preview + a solid starting HTML.
- `FREE` renders as a gold badge (it's written as `` `FREE` `` in the draft).
  Cost markers `$`/`$$` in backticks render as green badges.
- Emoji-only lines (e.g. `🌽 🌽 🌽`) become styled dividers automatically.
