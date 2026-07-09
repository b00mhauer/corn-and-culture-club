# Status & Roadmap

Snapshot of where Corn & Culture Club stands, what's open, and where to contribute next.
Pairs with [README.md](README.md) (how it works) and [PLAN.md](PLAN.md) (why).

_Last updated: 2026-07-09._

## Phase status

| Phase | What | State |
|---|---|---|
| 0 | Scaffold (uv project, sources map, style seeds) | ✅ Done |
| 1 | Research pipeline (coverage + curation skill) | ✅ Done |
| 2 | Writer skill (`draft.md` in house voice) | ✅ Done |
| 3 | Preview skill (branded `edition.html`) | ✅ Done |
| — | Discovery: Instagram + Facebook (Scrape Creators) | ✅ Live |
| — | Brand kit integrated (logo, fonts, assets) | ✅ Done |
| 4 | Publishing (beehiiv hand-off) | ◻ Open |
| 5 | Weekly automation (scheduled run) | ◻ Open |

## What works today

- **Nine live event sources**, all wired in `data/sources.yaml`:
  Iowa Children's Museum (ICS), Iowa City Public Library (custom JSON API), Coralville
  (CivicPlus RSS), North Liberty + Solon libraries (WhoFi), Little Village (SceneThink
  JSON), plus Facebook events (10 town/venue queries, paginated) and Instagram signals.
  A full `--discover` sweep yields ~100 candidates for a week.
- **Times normalized to America/Chicago** at ingestion (fixes wrong-day/UTC bugs).
- **Curation → draft → render** produces a branded, on-voice edition. Event links resolve
  to real event pages, with a Google-search fallback (`ccc_core.search_url`).
- **Brand applied**: corn-emblem masthead, Zilla Slab / Work Sans / Newsreader, per-day
  weather strip, mode icons, "What's poppin'" popcorn on Free & Cheap.

## Open items (roughly prioritized)

1. **Phase 4 — beehiiv publishing.** Build `ccc-publish` + `scripts/publish_beehiiv.py`
   against the v2 API (`POST /v2/publications/{id}/posts`). Requires: owner completes
   beehiiv identity verification to mint `BEEHIIV_API_KEY`, and confirms the plan allows
   API posting. Host the `/style/assets` (header, favicon, OG) so email uses real URLs
   instead of the data-URI masthead.
2. **Phase 5 — weekly automation.** A scheduled run (Claude Code Routine or Action) that
   builds candidates → curates → writes → previews and pings a draft for review. The
   Scrape Creators key is already in the environment variables for this.
3. **Email-safe rendering.** The SVG icons + webfonts look great on web but Gmail strips
   both. Produce an email variant (hosted PNG icons / emoji fallback, system fonts).
4. **More calendars.** Wire the University of Iowa Localist calendar (coded, but this
   sandbox's proxy 502s the host — works on an open network) and Think Iowa City
   (`?ical=1`, currently Cloudflare-blocked from datacenter IPs). See `sources.yaml` notes.
5. **Voice tuning.** The owner finds it slightly plain; sharpen `style/voice.md` against
   real drafts.

## Known issues / caveats

- **Sandbox network limits:** some hosts (UI Localist, Think Iowa City) are blocked from
  this environment but work from a normal network. Parsers for them are written and correct.
- **WhoFi latency:** the library parser fetches each event page (N+1), so it's slow;
  capped at 40/source. Fine for a weekly run.
- **Facebook filter is strict on purpose** (requires a county-town signal) — FB search
  bleeds in global junk otherwise. Documented in `fetch_facebook.py`.
- **`needs_confirm`/discovery items:** state real times from the data; only genuinely
  variable details (e.g. a rotating concert park) get a note. Never invent a fact.

## Good first contributions

- Add a source: append to `data/sources.yaml` with a `parser` (`ics` / `localist` /
  `jsonld` / `scenethink` / `civicplus_rss` / `whofi` / `instagram` / `facebook`) and test
  with `uv run python scripts/fetch_html.py --source <id>`.
- Build the email-safe render variant (item 3).
- Wire a new venue's Facebook page as an `fb_url` source once its slug is confirmed.
- Improve the coarse tagging heuristics in `ccc_core.py` (age bands, mode, junk flags).

## Where the record lives

Design decisions and the running history are in the git log and the (now-merged) pull
request. The editorial thesis and phase plan are in PLAN.md.
