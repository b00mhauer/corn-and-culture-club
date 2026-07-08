# Facebook events — WIRED via Scrape Creators

Facebook is the biggest source of local happenings, and the good news: Scrape Creators has
a **Facebook Events API** that returns *structured* events (name, date, place, url) — much
cleaner than Instagram captions. This is wired and working.

## How it works
`scripts/fetch_facebook.py` reads `method: facebook` sources from `sources.yaml`. Two kinds:
- `fb_query: "<text>"` → `GET /v1/facebook/events/search?query=<text>` — keyword/location search.
- `fb_url: "<page url>"` → `GET /v1/facebook/events?url=<page url>` — one page's events.

```bash
uv run python scripts/fetch_facebook.py --start <YYYY-MM-DD> --days 7 \
  > data/editions/<start>/facebook.json
```

The fetcher: drops past + online-only events, keeps only events in the date window whose
place/title looks like our county, normalizes to the standard Event schema (with
`when_text` = Facebook's human date string, which is authoritative for the time), tags
age/cost coarsely, and de-dupes. Needs `SCRAPE_CREATORS_API_KEY`. ~1 credit per query/page.

## What's verified
- `events/search?query=` works well with **simple location queries** ("Iowa City",
  "Coralville Iowa", "North Liberty Iowa"). Over-specific queries ("...kids family")
  return nothing — keep queries broad and let the fetcher's county+window filter narrow.
- Live run confirmed **North Liberty Blues & BBQ (Sat, Jul 11, 10 AM)** with the band
  lineup — corroborated a web-search find and pinned the exact time.
- `events?url=` (page pull) can 500 on a bad/short slug (e.g. `/englert`). Verify the real
  page URL before adding an `fb_url` source; the fetcher logs the error and continues.

## Your job in Discovery (turning results into edition events)
1. Most FB search hits are **further out than this week** — that's fine, they seed *future*
   editions and the Deep Dive "coming up" section. Note the good ones.
2. **Dedupe against calendar candidates.** The same event often appears on a venue calendar
   AND Facebook. Keep the richer record; prefer FB's `when_text` for the exact time.
3. FB gives a real date/time, so most items need **no** `needs_confirm` — but sanity-check
   anything that looks like a personal/party listing or an out-of-area bleed-through.
4. Add curated venue pages via `fb_url` (Englert, Hancher, Gabe's, the fairgrounds, farms)
   once you confirm each page's URL.

## Cost & safety
- Off by default; runs only when the skill invokes it during Discovery.
- Key lives in `.env` (gitignored). Never print or commit it.
- Bound spend with `--max-calls`; the script prints `credits_remaining` each run.
- Keep the query/page list curated — every entry is a credit and a bit of noise.
