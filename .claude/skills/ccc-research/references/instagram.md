# Instagram discovery (Scrape Creators)

Wired and working. This is the Tier-B automation from the Catskill Crew video, adapted.

## How it works
`scripts/fetch_instagram.py` calls Scrape Creators' `/v1/instagram/user/posts` for every
`method: instagram` handle in `sources.yaml`, keeps posts newer than `--days`, and emits
**signals** (not finished events): caption, post date, permalink, image URL, location.

```bash
uv run python scripts/fetch_instagram.py --days 21 --max-handles 6 \
  > data/editions/<start>/instagram.json
```

Needs `SCRAPE_CREATORS_API_KEY` in `.env`. **~1 credit per handle per run.** The script
prints `credits_remaining` and caps spend with `--max-handles`.

## Turning signals into events (your job in Discovery)
1. **Read every caption.** Many are literal dated event lists ("July 2: Fanfare & Flight
   @ NL Amphitheater…"). Split them into individual events.
2. **Image-only flyers:** when `caption` is empty and it's not a video, open `image_url`
   and read the flyer with vision — dates/times/venues live in the graphic.
3. Emit each as an event object: `source: "discovery:ig:<handle>"`, include the post URL,
   and set `needs_confirm: true` unless the caption states date/time unambiguously.
4. Cross-check against the calendar candidates so you don't double-list (the Python
   dedupe doesn't see IG signals).

## Curating handles
Quality over quantity — every handle costs a credit and adds noise. Keep the list to
orgs that actually post dated local events. Prune handles that return 0 recent posts
(wrong/inactive handle) or only lifestyle content.
- Verified active on first run: `thinkiowacity`, `littlevillagemag`, `summerofthearts`.
- Returned 0 (fix or drop): `theicm`, `northlibertyiowa` — confirm the real handle.
- Add over time: local farms/orchards, breweries with family hours, the fairgrounds,
  library/rec accounts, downtown districts.

## Facebook
Same pattern will apply if/when a Facebook scraper endpoint is added — see
`facebook.md`. Instagram is the higher-signal, lower-friction start.

## Cost & safety
- Off by default; only runs when the skill invokes it during Discovery.
- The key lives in `.env` (gitignored). Never print it or commit it.
- If credits run low, the fetcher still returns what it got; `--max-handles` bounds spend.
