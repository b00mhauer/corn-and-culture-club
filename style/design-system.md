# Corn & Culture Club — Design System

Modern, clean, editorial. The reference points are local brands that already read
right here: **Big Grove Brewery**, **Wilson's Orchard & Farm**, **Field Day**, and
**Hawkeye black-and-gold**. That means: confident type, restrained natural palette,
lots of whitespace, hairline rules, and almost no ornament. Not rustic, not folksy,
not emoji-laden. The `ccc-preview` skill encodes this in one HTML template
(`scripts/render_preview.py`).

## Principles

- **Modern and quiet.** Whitespace and type do the work. If a divider, badge, or
  emoji isn't earning its place, cut it.
- **One accent, used with discipline.** Deep green primary, gold secondary. Not both
  loud at once.
- **Editorial, not decorative.** Uppercase eyebrow labels, a newspaper-style
  nameplate, flat cards. It should look like a well-made local magazine, not a
  scrapbook.
- **No emoji as structure.** No corn dividers, no emoji age icons. (A rare emoji in
  body copy is fine if it's genuinely useful, but the chrome stays clean.)

## Palette

| Token | Hex | Use |
|---|---|---|
| `bg` | `#F4F1EA` | warm bone background |
| `surface` | `#FFFFFF` | cards |
| `ink` | `#1B1A17` | near-black text, nameplate |
| `muted` | `#6E675B` | meta text, captions |
| `line` | `#E4DDCF` | hairline rules, card borders |
| `green` | `#2E5A3E` | primary accent (section labels, FREE, links) |
| `gold` | `#C0891F` | secondary accent (ampersand, day kickers, `$`) |

## Type

System sans only (email-safe, no webfonts): `-apple-system, Segoe UI, Roboto,
Helvetica, Arial`. The modern feel comes from *weight and spacing*, not a fancy face:
- **Nameplate:** uppercase, extra-bold, wide letter-spacing (~2px).
- **Section labels:** small uppercase green eyebrow, letter-spaced.
- **Day kickers:** small uppercase gold.
- **Card meta:** small uppercase muted (day / time / venue).
- **Body:** 16px, line-height ~1.6.

## Layout

- Single column, max 600px, generous padding.
- **Nameplate:** wordmark left, edition date right, a 2px ink rule under, then a small
  uppercase tagline. Newspaper masthead energy.
- **Sections:** a hairline rule, then the uppercase eyebrow label, then content.
  Whitespace separates sections. No emoji dividers.
- **Event card:** flat white, 1px `line` border, 10px radius, no drop shadow.
  - line 1: **bold name** + chips
  - line 2: uppercase muted meta (day · time · venue)
  - line 3: the one-line hook
  - line 4: the source link
- **Chips** (written as `` `TOKEN` `` in the draft):
  - `FREE` → filled green
  - `$` / `$$` → filled gold
  - `AGES 0-4`, `ALL AGES`, etc. → outlined, muted
- **Footer:** hairline, uppercase wordmark, one plain line, the tip line.

## Email vs. web

Inline-ish styles, table layout, system fonts, no external assets, ≤600px. Works in a
browser now; beehiiv does final CSS inlining at send. Test in Gmail before launch.
