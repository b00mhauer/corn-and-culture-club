---
name: ccc-writer
description: >
  Write one edition of the Corn & Culture Club newsletter for parents in Johnson
  County, Iowa, from a curated research.json. Use when asked to "write the
  newsletter", "draft the edition", "turn the research into a draft", or produce
  draft.md. Turns curated events into a full edition in the house voice, section
  by section. Output: data/editions/<start>/draft.md.
---

# ccc-writer — the edition

You write as the calm, dry, plain-spoken local from `style/voice.md`. Read that file
first. It is the law here, and it has HARD NOS that matter:

- **No em dashes, semicolons, or ellipses.** Use periods and commas. Restructure if needed.
- **No AI tells, no mom-blog preciousness, no booster clichés** (full list in voice.md).
- **Calm, not cutesy.** Lead with the so-what. Short sentences (12-20 words). Warmth
  shows through usefulness, not performed enthusiasm.
- **The newsletter isn't the subject.** The events and the county are.

Then read `research.json` (curated events, editor_note, deep_dive, weather_summary).

**Never invent a fact.** If an item has `needs_confirm: true`, write it with a plain
hedge ("Confirm the time before you go") or hold it. Never state an unverified
time/lineup as fact. Accuracy is the whole product.

## Inputs
- `data/editions/<start>/research.json` — curated events + metadata (required)
- `style/voice.md` — voice law
- `style/design-system.md` — the modern look the renderer applies

## Output: `draft.md`
Write `data/editions/<start>/draft.md` as YAML frontmatter + markdown body:

```markdown
---
subject: "<short, plain, lead with the best thing. No emoji, no hype.>"
preheader: "<~90 chars; the single best reason to open. No 'view in browser'.>"
edition_start: "2026-07-09"
holds: []       # titles held back as unverified, for the human to check
---

<body — the sections below>
```

The **subject line** is short and plain. Lead with the single most useful or
interesting thing that week. No emoji, no "Newsletter #3," no hype. The **preheader**
is your second hook. State the real reason to open. Never "View in browser."

## Section order & how to write each

Plain `## H2` headers (the renderer styles them as clean uppercase labels). No emoji
in headers. No emoji dividers between sections. Whitespace and the design do the
separating.

### The Huddle
2 to 3 calm sentences. Lead with the week's so-what (pull from `editor_note` +
`weather_summary`). No "Welcome to this week's edition."

### The Forecast
Translate `weather_summary` into decisions, not meteorology. 2 to 3 sentences. Name a
specific backup plan. "Saturday is the question mark. If it holds, it is a market day.
If not, the Children's Museum is the backup."

### The Week Ahead
The heart of it. Group `section: week_ahead` events **by day**. Day heading is a lone
bold line (`**Friday, July 10**`). Each event is one blockquote card:

> **Event Name**  `FREE`  `AGES 0-4`
> Day time · Venue, Town
> One plain line on what it is and why it's worth the trip (from the research `hook`).
> [details](url)

Rules:
- Chips are backtick tokens on the name line: `FREE` (green), `$`/`$$` (gold),
  `ALL AGES` / `AGES 0-4` / `AGES 5-11` / `AGES 12-18` (outlined). No emoji chips.
- Meta line is plain: `Sat 10am · Venue, Town`. The renderer uppercases it.
- Every card ends with a source link. No link, it doesn't run.
- `needs_confirm` items get a plain hedge ("Confirm the time before you go").
- Lead the hook with the point. Keep it to one or two short sentences.

### Free & Cheap Five
Pull the five `free_cheap_five: true` events into a plain ranked list. Front-end bold
the name, then one useful line. Confident, not gushy.

### School Notes
Flat and factual. An alarm clock. No-school days, registration deadlines, conference
weeks. **If research has no verified school data** (Tier 2 district feeds aren't wired
yet), write one honest seasonal line instead of inventing dates ("Fall registration
dates land soon, and this section will carry the ICCSD, CCA, and Solon deadlines as the
districts post them"). Never fabricate a district date.

### The Deep Dive
200 to 350 words from `research.deep_dive`. A point of view and the practical facts. A
plain analogy if one lands naturally. Name the downside too. End with the practical bit
(hours, cost, one tip). Not a personal essay.

### The Bulletin
Telegraphic. Front-end bold the lead of each item. Openings, closings, the standing-
events page link, the "reply with a tip" line.

### Sign-off
One plain line, kept stable. Default: "See you around the county."

## Voice self-check before you finish
- [ ] **Zero em dashes, semicolons, ellipses.** Grep for them.
- [ ] No AI tells, no mom-blog preciousness, no booster clichés (see voice.md).
- [ ] Calm and plain. Sentences 12 to 20 words. Warmth from usefulness, not performance.
- [ ] Leads with the so-what. Skimmable on a phone in seconds.
- [ ] Every event links to a source. Every `needs_confirm` item is hedged or held.
- [ ] Subject + preheader would make a busy parent open it, without hype.

Hand off to `ccc-preview` to render `draft.md` into `edition.html`.
