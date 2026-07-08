# Corn & Culture Club — Design System (v2)

> Drop-in replacement for `style/design-system.md` in the repo. This supersedes the v1
> seed. It matches the brand kit in `Brand & Style Guide.dc.html` and the exported
> `/assets`. The ccc-preview skill should encode the **email-safe** column of Type below;
> the web archive + signup page may use the brand webfonts.

## Positioning

A social club and weekly newsletter for people in their late thirties around **greater
Iowa City**. Going-out and culture first — date nights, nights out with friends — with a
kids-in-tow lane as one tagged facet, not the whole product. Voice: a well-connected
neighbor with a good memory and a spreadsheet. Curated, not aggregated.

**Tagline (primary):** Ears to the ground on the good stuff around town.
**Tagline (utility/descriptive):** The good stuff to do in greater Iowa City.

## Feel

Modern-editorial with vintage-Midwest warmth. Warm paper, dark ink, one bright kernel of
gold. Single column, big slab section headers, clean **line-icon dividers (no emoji)**,
generous whitespace. Confident but never breathless.

## Palette (tokens)

| Token | Hex | Use |
|---|---|---|
| `corn-gold` | `#D9A408` | primary accent, ampersand, dividers, FREE-adjacent |
| `prairie-green` | `#345E3B` | links, `FREE` badge fill |
| `brick` | `#A63A28` | alarm only (deadlines) — rare |
| `ink` | `#17150F` | body text + dark backgrounds |
| `paper` | `#F1ECDF` | page background |
| `gold-wash` | `#F7ECC9` | event-icon chip backgrounds |
| `stone` | `#6E6454` | meta, captions, "double-check" notes |
| `hairline` | `#E4DAC6` | borders, rules, card outlines |
| `card` | `#FFFFFF` | event card / panel background |

Gold is the star and stays rare. Links are green with a gold underline. Brick appears
maybe once per edition, on a deadline.

## Type

| Role | Web / brand assets | Email-safe (sent newsletter) |
|---|---|---|
| Display / masthead / headlines | **Zilla Slab** 600–700 | `Georgia, 'Times New Roman', serif` |
| Interface / labels / badges / meta | **Work Sans** 700–800, UPPERCASE + letter-spacing | system: `-apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif` |
| Reading prose (Huddle, Deep Dive) | **Newsreader** 400 | `Georgia, serif` |

Gmail/Apple Mail strip webfonts — the **email build uses the system stacks**. Zilla Slab /
Work Sans / Newsreader are for the web archive, signup page, and social images only.

## Logo system

Three marks, all in `/assets`:
- **Primary lockup** — corn-ear emblem + two-line Zilla Slab wordmark, gold ampersand.
- **Emblem** — stylized ear of corn: gold body, ink **kernel grid** (straight rows/cols,
  not a diagonal crosshatch), small prairie-green leaf husks at the base. Wide/blunt cob,
  not a narrow rounded one. Ring/seal variant for covers. Min size 28px; below that use the monogram.
- **Monogram** — ink `C&C` on a corn-gold rounded square. Primary favicon; avatars, merch.
- **Popcorn (playful register)** — a puffed-kernel cluster tied to the recurring
  **"What's poppin'"** device (subject lines, stickers, the Free & Cheap icon). Not the
  formal logo — the fun counterpart to the serious corn mark.

Rules: keep clear space ≈ the emblem's width; never recolor the corn off gold; never add
gradients/shadows; never set the wordmark in any face but Zilla Slab.

## Section header pattern

Hairline rule, then a **gold line-icon + uppercase Work Sans label**. The eight beats:
The Huddle · The Forecast · Date Night & Out · Community & Outdoors · With the Kids ·
Free & Cheap Five · The Deep Dive · The Bulletin.

## Event card (the atom)

```
[gold-wash icon chip]  Bold Event Name  [FREE]  [DATE NIGHT] [ALL AGES]
                       SAT 10:00AM · NORTH LIBERTY   (Work Sans, uppercase, stone)
                       One punchy sentence on why it's worth it.
                       details ↗  (green text, gold underline — always source-linked)
```

- Tags: cost (`FREE` = green fill; `$`/`$$` = hairline outline), mode/age (`DATE NIGHT`,
  `NIGHT OUT`, `ALL AGES`, `0–4`…). `FREE` is always the loudest.
- Every block ends with a source link — non-negotiable.

## Layout tokens

- Email max width 600px; card radius 12px; icon chip 38–44px, radius 10–11px.
- Section dividers: 1px `hairline` rule + 32px top margin.
- Mobile-first, single column, comfortable tap targets.
