# 🌽 Corn & Culture Club

A weekly, curated newsletter + website about the good stuff to do in **greater Iowa City**
(Johnson County, Iowa). Audience: connected local adults — date nights, nights out with
friends, community happenings, and family/kids activities as one tagged lane. Not an
aggregator; a curated pick, produced mostly automatically with Claude Code.

**Tagline:** *Ears to the ground on the good stuff around town.*

New here? Read this, then **[STATUS.md](STATUS.md)** for what's done / what's next, and
**[PLAN.md](PLAN.md)** for the full design rationale.

---

## How it works

An edition is produced by a four-step pipeline. Steps 1 and 4 are Python; the parts that
need taste (2 and 3) are Claude Code **skills** in `.claude/skills/`, so you make an
edition by conversation.

```
  gather (Python)          curate (skill)        write (skill)      render (Python)     publish
  ────────────────         ──────────────        ─────────────      ───────────────     ───────
  build_edition.py    →    ccc-research     →     ccc-writer    →    ccc-preview    →    ccc-publish
  candidates.json          research.json         draft.md           edition.html        (beehiiv)
```

1. **Coverage + discovery** — `scripts/build_edition.py` pulls structured calendars (ICS,
   library/city APIs), plus optional paid discovery (Facebook events, Instagram signals),
   normalizes + de-dupes them, adds the NWS weather, and writes a **candidate pool**.
2. **Curation** — the `ccc-research` skill (Claude) reads the pool, hunts the non-obvious,
   cuts junk, tags by mode (date-night / night-out / kids / community), and writes hooks →
   `research.json`.
3. **Writing** — the `ccc-writer` skill turns that into `draft.md` in the house voice.
4. **Preview** — `scripts/render_preview.py` renders `draft.md` into a branded
   `edition.html`. `ccc-publish` (planned) hands it to beehiiv.

The editorial thesis: **calendars are the floor, not the product.** The value is discovery
(the non-obvious) + curation (a point of view). See PLAN.md §2.5.

## Quickstart

```bash
uv sync                                  # install deps (Python 3.11, uv)
cp .env.example .env                     # then add keys (see below)

# Build the candidate pool for a week (free sources only):
uv run python scripts/build_edition.py --start 2026-07-16 --days 7

# Add paid discovery (Facebook events + Instagram signals):
uv run python scripts/build_edition.py --start 2026-07-16 --days 7 --discover

# Render an existing draft to HTML:
uv run python scripts/render_preview.py --start 2026-07-16
```

Then, in a Claude Code session on this repo, drive the skills: *"research next week's
edition"* → *"write it"* → *"preview it."*

### Keys (`.env`, gitignored)

| Var | Needed for | Notes |
|---|---|---|
| `SCRAPE_CREATORS_API_KEY` | Facebook events + Instagram | Paid, opt-in. Free ICS/HTML sources work without it. |
| `BEEHIIV_API_KEY` | Automated publishing (Phase 4) | Needs beehiiv identity verification + likely a paid tier. |
| `BEEHIIV_PUBLICATION_ID` | Publishing | Not secret; already set. |
| `NWS_USER_AGENT` | Weather | NWS is free/keyless; just identify the app. |

Never commit real keys. The gather scripts read `.env` via `ccc_core.load_env()`.

## Layout

```
scripts/          Python: fetchers, core, orchestrator, renderer (uv-run)
  ccc_core.py       schema, tagging, dedupe, tz normalize, .env, search_url
  fetch_ics.py      ICS feeds        fetch_html.py   library/city/aggregator APIs
  fetch_facebook.py Facebook events  fetch_instagram.py  IG caption/image signals
  fetch_weather.py  NWS forecast     build_edition.py    orchestrator → candidates.json
  render_preview.py draft.md → edition.html
.claude/skills/   ccc-research, ccc-writer, ccc-preview (+ ccc-publish planned)
data/sources.yaml the tiered source map (one entry per source; drives the fetchers)
data/editions/<start>/  per-edition artifacts (candidates.json, research.json, draft.md, edition.html)
style/            brand system: design-system.md (v2), voice.md, /assets, brand guides
PLAN.md           full plan + editorial thesis + roadmap
STATUS.md         current state, open items, good first contributions
```

## Conventions

- Run everything through `uv`. Lint with `uv run ruff check scripts/`.
- Secrets only in `.env`. Sources are added in `data/sources.yaml`, never in code.
- Voice (`style/voice.md`) and design (`style/design-system.md`) are the law for output;
  fix them there, then regenerate.
