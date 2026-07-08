# Corn & Culture Club — Design System (v1)

> Seed values. The `ccc-preview` skill (Phase 3) will encode these into one HTML
> template used for both email and web. Refine against real Catskill Crew editions
> and real Gmail rendering before locking anything.

## Feel

County-fair-meets-college-town. Warm, tactile, a little handmade — not a slick
SaaS newsletter. Single column, big friendly section headers, emoji dividers,
generous whitespace. Steal Catskill Crew's *bones* (layout, rhythm, scannability),
give it an Iowa *skin* (palette, icons, references).

## Palette

| Token | Hex | Use |
|---|---|---|
| `corn-gold` | `#F2B705` | primary accent, dividers, FREE badge |
| `barn-red` | `#A62B1F` | headers, links, emphasis |
| `prairie-green` | `#3E6B3A` | secondary accent, age tags |
| `sky` | `#5B8FB0` | tertiary / cold-weather forecast accents |
| `cream` | `#FBF7EC` | page/background |
| `ink` | `#2A2622` | body text |
| `stone` | `#6E655B` | captions, metadata, "double-check" notes |

Keep contrast AA-legible on `cream`. FREE badge = `corn-gold` bg + `ink` text so
it pops in the skim.

## Type

- Headers: a warm slab or friendly display face (web-safe fallback: Georgia /
  serif). Confirm what renders in email — for the email build, prefer a system
  serif stack over a webfont that Gmail may strip.
- Body: readable sans (system stack: -apple-system, Segoe UI, Roboto, sans-serif).
- Listings: same body font, bold event name, regular blurb.

## Dividers (the Catskill Crew move, Iowa-fied)

Emoji rule between sections. Primary: 🌽. Rotating supporting cast so editions
feel alive: 🚜 🐷 🦅 🎪 🧺 🌾. One divider style per edition (pick a "critter of
the week") is a fun, low-effort signature — mirrors Catskill Crew's animal emoji
in the subject line (🦅 🐻 🦉).

## Section header pattern

Each bucket gets: emoji + short ALL-ish-CAPS or title-case label, e.g.

```
🌽  THE WEEK AHEAD
🆓  FREE & CHEAP FIVE
🏫  SCHOOL NOTES
```

## Event listing block (the atom)

```
[Bold Event Name]                          [FREE]  [👶 0–4]
Sat · 10:30am · Iowa Children's Museum, Coralville
One punchy sentence on why it's worth your Saturday. ↗ source
```

- Age band chips: `👶 0–4` · `🎒 5–11` · `🎧 12–18` · `👨‍👩‍👧 all`
- Cost chip: `FREE` (gold) / `$` / `$$`. FREE always visually loudest.
- Every block ends with a source link — non-negotiable (accuracy = trust).

## Layout tokens

- Max content width ~600px (email-safe).
- Section spacing generous; dividers give breathing room.
- Mobile-first: everything single-column, tap targets comfortable, no side-by-side.
- Images: optional per event; if used, keep small and lazy — email clients are
  finicky. Alt text always.

## Email-vs-web notes

- Email: inline CSS, table-based layout, no external fonts, test in Gmail +
  Apple Mail. beehiiv handles a lot of this if we publish there.
- Web (archive page): same template, can be a touch richer (webfonts, the
  evergreen standing-events page, an event-submission link).
