---
name: ccc-research
description: >
  Research one edition of the Corn & Culture Club newsletter for parents in
  Johnson County, Iowa. Use when asked to "research an edition", "find events for
  this week", "pull the newsletter research", or build research.json. Runs the
  coverage pipeline, then does the two jobs that need taste: DISCOVERY (hunt the
  non-obvious events that aren't on any calendar) and CURATION (score, cut junk,
  rank, write hooks). Output: data/editions/<start>/research.json.
---

# ccc-research — the editorial brain

Read `PLAN.md` §2.5 (editorial thesis) before you start. The one rule that governs
everything here:

> **The calendars are the floor, not the product.** A dump of library and parks
> feeds is sterile and misses the interesting stuff. People subscribe for "what's
> actually worth your time, including things you'd never have found." Coolness beats
> completeness. A calendar has no point of view — your job is to give it one.

You do three things, in ascending order of value: **Coverage → Discovery → Curation.**

---

## Step 1 — Coverage + structured discovery (one command)

```bash
uv run python scripts/build_edition.py --start <YYYY-MM-DD> --days 7 --discover
```

`--discover` pulls the paid sources (uses Scrape Creators credits); drop it for a
free ICS/HTML-only run. This writes `data/editions/<start>/candidates.json`:
- **candidates** — de-duped, tagged pool from ICS feeds (ICM), HTML/API sources
  (Localist where reachable), AND structured **Facebook events** (the biggest
  coverage source; town + venue queries across the county).
- **instagram_signals** — recent post captions/images to mine for the non-obvious.
- **weather** — NWS forecast.

Read `candidates.json`. Skim `dropped_for_review` (the junk filter can be wrong).
The pool is tuned for recall, so it includes some noise on purpose — your curation
is what makes it precise. **Do not stop here.**

## Step 2 — Discovery (hunt the non-obvious — this is why people subscribe)

Spend real effort here. Aim for **at least 2–3 genuinely interesting finds that were
NOT on any calendar.** Use web search + WebFetch. Hunt across:

- **Every venue calendar in town.** Music/arts/culture venues each publish their own
  and they're full of the good stuff: **Englert Theatre**, **Hancher Auditorium**,
  **Gabe's**, **FilmScene** (family matinees), **The Mill**, **Riverside Theatre**,
  **Coralville Center for the Performing Arts**, **Xtream Arena**, **Public Space One**,
  **Trumpet Blossom**. Filter for all-ages / family-appropriate.
- **Facebook events (automated — Scrape Creators is wired).** The single biggest source
  of local happenings, and it comes back STRUCTURED (name/date/place/url). Run:
  ```bash
  uv run python scripts/fetch_facebook.py --start <YYYY-MM-DD> --days 7 > data/editions/<start>/facebook.json
  ```
  It searches the town-scoped queries in `sources.yaml` (method: facebook), filters to
  our county + date window, and de-dupes. These are near-finished events — **dedupe them
  against the calendar candidates** (same event often appears in both; keep the richer
  record and prefer FB's `when_text` for the exact time). ~1 credit per query. Add venue
  `fb_url` pages as you confirm their slugs. See `references/facebook.md`.
- **Instagram (automated — Scrape Creators is wired).** Run:
  ```bash
  uv run python scripts/fetch_instagram.py --days 21 --max-handles 6 > data/editions/<start>/instagram.json
  ```
  This pulls recent post captions + images for the curated handles in
  `sources.yaml` (method: instagram). Local orgs routinely post **dated event
  round-ups in captions** (e.g. @thinkiowacity's weekly list, @summerofthearts).
  Read every caption; extract any event into an event object with
  `"source": "discovery:ig:<handle>"` and the post URL. For **image-only flyers**
  (`caption` empty, `is_video` false), fetch `image_url` and read the flyer text
  yourself — you have vision; that's the video's exact move. Costs ~1 credit/handle,
  so keep the handle list curated. See `references/instagram.md`.
- **Reddit** r/IowaCity and local **parent Facebook groups** — word-of-mouth, pop-ups,
  the informal social occasions that never hit a calendar.
- **New & seasonal firsts** — a new business opening a play corner, first pumpkin-patch
  weekend, splash pad opening day, first farmers market of the season. These are gold.
- **Little Village editorial** picks (not just their calendar) and any reader tips.

Record each discovery as an event object (same schema as candidates), with
`"source": "discovery:<where>"` and a note on how you found it so it's checkable.

## Step 3 — Curation (score, cut, rank, give it a POV)

Now be the editor. For every candidate AND discovery:

1. **Would a busy parent actually care?** If not, cut it. Be ruthless — better to send
   eight great things than forty rows. Cut duplicates, filler, closures, and
   `age_uncertain` items you can't resolve.
2. **Fix the auto-tags.** The Python guesses coarsely. Trust your read of the
   description over the heuristic for `age_bands`, `cost`/`is_free`, `town`.
3. **Score `interest_score` 1–5.** 5 = "rearrange your Saturday." 1 = "fine, filler."
4. **Assign a `section`:** `week_ahead` · `free_cheap_five` · `school_notes` ·
   `deep_dive` · `bulletin`.
5. **Write the `hook`** — one line in the house voice (`style/voice.md`): why it's worth
   it, lead with the appeal not the logistics. This is the writing seed the ccc-writer
   skill builds on.
6. **Pick ONE `deep_dive`** idea for the week (a park review, hidden gem, a local to
   feature). Note it even if it needs more research.
7. **Free & Cheap Five:** choose the five best free/under-$10 things and mark them.

## Output — research.json

Write `data/editions/<start>/research.json`:

```json
{
  "edition": {"start": "2026-07-16", "end": "2026-07-22", "days": 7},
  "weather": { "...": "carried from candidates.json (facts only)" },
  "editor_note": "1-2 sentences on the week's theme/feel for the writer.",
  "deep_dive": {"idea": "...", "why": "...", "needs": "what more to research"},
  "events": [
    {
      "title": "Art Play Sundays",
      "start": "2026-07-19T11:00:00",
      "venue": "Iowa Children's Museum",
      "town": "Coralville",
      "url": "https://theicm.org/event/...",
      "source": "iowa-childrens-museum",
      "age_bands": ["0-4", "5-11"],
      "cost": "low", "is_free": false,
      "indoor_outdoor": "indoor",
      "section": "week_ahead",
      "interest_score": 4,
      "free_cheap_five": false,
      "hook": "Open-ended art, zero cleanup for you — the good kind of tired-out."
    }
  ],
  "cut": [{"title": "...", "reason": "duplicate / not family / filler"}]
}
```

## Quality bar (self-check before you finish)

- [ ] At least 2–3 events came from Discovery, not calendars.
- [ ] Every kept event has a source URL (accuracy = trust; never publish an unlinkable event).
- [ ] Junk is actually cut, not just tagged. The `events` list is tight.
- [ ] Age bands and FREE flags are correct — parents filter on these.
- [ ] One Deep Dive chosen.
- [ ] Nothing reads like a calendar dump. It reads like a friend who did the legwork.
