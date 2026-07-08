# 🌽 Corn & Culture Club — Build Plan

A weekly newsletter + website for parents of kids (newborn through high school) in Johnson
County, Iowa — Iowa City, Coralville, North Liberty, Solon, Tiffin, University Heights,
Hills, Swisher, Oxford, Lone Tree.

**The promise:** you're too busy to track fifteen calendars. We do it for you. One email a
week that tells you what's worth doing with your kids, what's free, what deadline you're
about to miss, and one cool local thing you didn't know about.

Modeled on [Catskill Crew](https://catskillcrew.com/) (beehiiv-based, ~40k subscribers,
built largely with Claude Code — see [the video](https://www.youtube.com/watch?v=GnhNNeUsFdE)),
but adapted for a family audience in a college-town county. Priorities: **helpful, fun,
interesting** — monetization later, if ever.

---

## 1. What we borrow from Catskill Crew, and what we change

| Catskill Crew | Corn & Culture Club |
|---|---|
| Events skew nightlife/arts/outdoors for adults & weekenders | Events filtered for families, tagged by **age band** and **cost** |
| Sources are heavily Instagram (venues, promoters) | Sources are mostly **institutional calendars with ICS/RSS feeds** (libraries, parks & rec, museums, schools) — easier and free to scrape |
| Weather/conditions section (hiking, foliage) | Weather framed for parents: pool/splash-pad weather, sledding, "indoor backup plan" days |
| Real estate spun into separate newsletter | **School notes** section instead — no-school days, registration windows, conference weeks |
| Animal emoji dividers (🦅 🐻 🦉), rustic design | Iowa iconography: 🌽 🚜 🦅 🐷 🎪 — county-fair-meets-college-town design |
| Weekly, voice of a well-connected neighbor | Same voice, but a well-connected *parent*: "we found the good stuff so you don't have to" |

The core architecture is the same one from the video: **Claude Code skills** (research →
write → preview → publish) so a new edition is created by conversation, not by hand.

## 2. Content buckets (v1 edition template)

1. **👋 The Huddle** — 2–4 sentence greeting. Warm, direct, one seasonal observation, zero fluff.
2. **🌤️ The Forecast** — weekend weather in parent terms ("Saturday is a pool day; Sunday
   bring the rain boots to the farmers market"). Sunrise/sunset near solstices, first-freeze
   and snow-day chatter in season.
3. **🌽 The Week Ahead** — the heart of it. Events by day, each with:
   - name, time, venue, town, link to source
   - age tags: `👶 0–4` · `🎒 5–11` · `🎧 12–18` · `👨‍👩‍👧 all ages`
   - cost tag: `FREE` gets visual emphasis
   - one punchy sentence of why-it's-worth-it
4. **🆓 Free & Cheap Five** — the five best free/under-$10 things this week, pulled to the top
   for skimmers. (Likely the most-loved section — Johnson County has an unusual amount of free
   programming.)
5. **🏫 School Notes** — rotating, short: ICCSD / Clear Creek Amana / Solon / Regina no-school
   days coming up, registration deadlines (summer camps, youth sports, preschool lotteries),
   conference weeks. This is the "you're about to miss the signup" alarm — a section busy
   parents will forward to each other.
6. **🚜 The Deep Dive** — one short feature per week: a park/playground review, a new business
   with a play corner, a hidden gem (e.g., the Devonian Fossil Gorge, Wilson's Orchard in
   the off-season), an interview with a local (librarian, coach, camp director).
7. **📌 The Bulletin** — community shorts: new openings/closings, calls for volunteers, reader
   shout-outs, "send us your event" link. (Sponsor slots can live here someday; for now it's
   pure community.)
8. **✌️ Sign-off** — one line, consistent catchphrase (to be workshopped — e.g., "See you at
   the ped mall. 🌽").

Standing-events reference (weekly storytimes, open gyms, tot time at the rec centers) lives
as an **evergreen page on the website**, not repeated in every email — link to it instead.

## 3. Source map (research targets)

### Tier 1 — structured calendars, scrape every week (most have ICS/RSS)
- **Libraries:** Iowa City Public Library ([icpl.org/calendar](https://www.icpl.org/calendar) — storytimes, family, teen categories), Coralville PL, North Liberty Library, Solon PL, Tiffin PL
- **Parks & Rec:** Iowa City, Coralville, North Liberty (Second Saturdays, Beat the Bitter, Blues & BBQ), Tiffin, Solon
- **Aggregators:** [Think Iowa City](https://thinkiowacity.com/events/) (CVB — covers the whole county), [Little Village calendar](https://littlevillage.scenethink.com/), [Johnson County events](https://johnsoncountyiowa.gov/events), Johnson County Conservation (Kent Park programs, Wings & Wild Things)
- **Venues:** Iowa Children's Museum ([theicm.org](https://theicm.org)), Englert Theatre, Hancher Auditorium, FilmScene (family screenings), Riverside Theatre, Coralville Center for the Performing Arts, Xtream Arena, Iowa City Downtown District (Block Party, Northside Oktoberfest kids' hours)

### Tier 2 — school & seasonal
- District calendars: **ICCSD**, **Clear Creek Amana**, **Solon CSD**, Regina Catholic, Willowwind/Preucil/Montessori
- University of Iowa: athletics family events (Kids' Day at Kinnick, gymnastics/wrestling meets = cheap kid entertainment), Museum of Natural History, Stanley Museum of Art family days, Pentacrest events
- Seasonal heavy-hitters: Wilson's Orchard & Farm, Colony Pumpkin Patch, Iowa City Farmers Market, Coralville Farmers Market, Johnson County Fair (late July!), Party in the Park series, Jazz Fest / Arts Fest / Soul Fest, Rec Center pools & splash pads

### Tier 3 — social & long tail (add later, costs money or scraping effort)
- Instagram/Facebook: @thinkiowacity, @icgov, @northlibertyiowa, @theicm, @icpubliclibrary, school PTO pages, local parent Facebook groups (manual skim at first)
- Eventbrite within ~20 miles of Iowa City; AllEvents; Macaroni KID (competitor scan — note what they miss)
- Instagram automation via Scrape Creators API + image analysis, exactly as in the video — **deferred until Tier 1/2 pipelines are solid**, because unlike the Catskills, most family events here are on real websites first.

All sources live in `data/sources.yaml` with per-source scrape method (`ics` / `html` /
`api` / `manual`), so adding a source never means writing new orchestration.

## 4. Technical architecture

```
corn-and-culture-club/
├── .claude/
│   └── skills/
│       ├── ccc-research/    # SKILL.md + scraper workflows per source type
│       ├── ccc-writer/      # SKILL.md + style guide + per-section templates
│       ├── ccc-preview/     # SKILL.md + HTML email/web template
│       └── ccc-publish/     # SKILL.md + beehiiv (or Buttondown) workflow
├── scripts/                 # Python, uv-managed
│   ├── fetch_ics.py         # pull + parse ICS feeds from sources.yaml
│   ├── fetch_html.py        # firecrawl/requests+readability scrapers per source
│   ├── fetch_weather.py     # NWS api.weather.gov (free, no key) for Iowa City
│   ├── normalize.py         # → common event schema, dedupe, age/cost tagging
│   └── build_edition.py     # assemble research JSON for a given week
├── data/
│   ├── sources.yaml         # the source map above, one entry per source
│   ├── evergreen.yaml       # standing weekly events (storytimes, open gyms)
│   └── editions/2026-07-16/ # research.json, draft.md, edition.html per edition
├── style/
│   ├── voice.md             # writing style guide
│   └── design-system.md     # colors, fonts, dividers, layout tokens
└── PLAN.md
```

**Event schema** (JSON): `title, start, end, venue, town, url, source, description,
age_bands[], cost, is_free, indoor_outdoor, tags[], confidence`. Dedupe on
fuzzy(title)+date+venue since Think Iowa City and Little Village will overlap heavily
with primary sources.

**Skills, not a monolith script.** Same philosophy as the video: each skill is a properly
formatted Claude skill (SKILL.md with frontmatter) so a future session can do the whole
thing conversationally:

> "Research next week's edition" → `ccc-research` fans out scrapers, writes `research.json`
> "Write it" → `ccc-writer` produces `draft.md` in house voice
> "Preview it" → `ccc-preview` renders `edition.html`
> "Ship it" → `ccc-publish` pushes to the newsletter platform

**Age tagging** is the special sauce and mostly LLM work, not code: the research skill
classifies each event into age bands from its description (with a `confidence` field;
low-confidence tags get flagged for your 30-second human review).

**Weather:** NWS `api.weather.gov` is free, keyless, and excellent for Iowa — no scraping
needed at all.

## 5. Publishing platform

**Recommendation: beehiiv** (what Catskill Crew uses).
- Free "Launch" tier: up to 2,500 subscribers, includes a hosted website + archive +
  signup page — your website and newsletter in one, zero extra work.
- Custom domain (`cornandcultureclub.com`) supported.
- **Caveat:** beehiiv's API (for fully-automated post creation) requires a paid plan. Plan
  for a **5-minute human step** at first: `ccc-publish` generates final HTML, you paste it
  into beehiiv and hit schedule. That human touch is a feature early on anyway — you're the
  editor. If/when you outgrow it, either upgrade beehiiv or switch the pipeline to
  Buttondown (API on cheap tiers) — the skills architecture makes the last mile swappable.

## 6. Voice & design (seed — to be refined against real drafts)

**Voice:** A well-connected Johnson County parent. Warm, direct ("you"), enthusiastic but
never breathless, short punchy sentences for listings, casually insider ("the ped mall,"
"the Coral Ridge carousel," "Kinnick," "CCA side of the county"). Never corporate, never
"fun for the whole family!" clichés. Honest about duds and rain plans. A little funny, in
a dry Midwest way.

**Design:** mimic Catskill Crew's bones — single column, big friendly section headers,
emoji dividers, generous whitespace — with an Iowa skin: corn-gold + barn-red + prairie-green
palette, 🌽 as the primary divider, rotating supporting cast (🚜 🐷 🦅 🎪 🧺). The preview
skill encodes all of this in one HTML template used for both email and web.

## 7. Build phases

### Phase 0 — Scaffold (first session)
Repo layout above, `uv` project, `data/sources.yaml` seeded from the source map, `.gitignore`
(secrets, scratch), `style/voice.md` v1.

### Phase 1 — Research pipeline
`fetch_ics.py` + `fetch_html.py` against **Tier 1 sources only** (start with ~8: ICPL,
Coralville PL, North Liberty Library, Think Iowa City, Little Village, ICM, JC Conservation,
North Liberty rec). Normalizer + dedupe + age tagging. `ccc-research` skill wrapping it all.
**Milestone: one command produces a clean `research.json` for a real week.**

### Phase 2 — Writer
`style/voice.md` fleshed out (steal structure from Catskill Crew editions, rewrite the soul
for Iowa parents). Per-section templates in `ccc-writer`.
**Milestone: a full draft edition you'd actually send to a friend.**

### Phase 3 — Preview
HTML template + `ccc-preview` skill. Look at real Catskill Crew editions for layout patterns,
apply the Iowa design system.
**Milestone: `edition.html` that looks like a real newsletter in a browser and in Gmail.**

### Phase 4 — Publish & launch
beehiiv account, domain, signup page. Dry-run 2–3 editions sent only to yourself/family.
Then a soft launch: share with your own parent network, school group chats, a note to the
libraries ("we link to your programs every week").
**Milestone: Edition #1 to real subscribers. Thursday morning send** (parents plan the
weekend Thursday; school-notes deadlines land before Friday-folder chaos).

### Phase 5 — Automate the cadence
- A **Claude Code Routine / scheduled session** (or GitHub Action) every Wednesday: runs
  research, writes the draft, renders the preview, and emails/pings you the draft for a
  10-minute edit + paste into beehiiv.
- Add Tier 2 sources (schools, UI, seasonal) and the school-deadline tracker.
- Only now consider Tier 3 (Instagram/Scrape Creators + image analysis, per the video).

### Later / maybe
Event-submission form (beehiiv supports embeds), reader polls, "best playground bracket"
type interactive fun, sponsorships from kid-adjacent local businesses — all deferred by
design.

## 8. Risks & principles

- **Accuracy over volume.** Every event links to its source; include a gentle "double-check
  before you load the minivan" norm. Never publish an event the pipeline can't source-link.
- **Scraping etiquette:** prefer ICS/RSS/APIs; respect robots.txt; cache aggressively; these
  institutions *want* their events promoted — when in doubt, email them (also great for
  relationship-building and future submissions).
- **Seasonality:** summer is a firehose, January is thin. The Deep Dive and School Notes
  buckets keep thin weeks worth opening.
- **Competitor check:** Macaroni KID and Facebook groups exist; the edge is curation, voice,
  age tags, and the deadline alarm — not raw listings.
- **Keys & costs:** NWS is free; firecrawl has a free tier; Scrape Creators only when Tier 3
  starts. All keys in `.env`, gitignored from day one.
