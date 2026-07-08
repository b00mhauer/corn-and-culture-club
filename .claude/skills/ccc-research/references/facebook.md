# Getting Facebook events (honestly)

Facebook is the biggest single source of local happenings — especially the informal,
social, one-off stuff we care most about. It is also the **hardest** to pull, on
purpose. Here's the real landscape and the practical path, cheapest first.

## Why it's hard

- Facebook **shut down the public Events API**. The old Graph API `/{page}/events`
  endpoint was deprecated years ago; you can't just pull a page's events with a token
  anymore unless you're an admin of that page. There is no free official firehose.
- Public event/page HTML is **login-walled and obfuscated** — brittle to scrape, and
  automated scraping violates Facebook's ToS. Don't build the newsletter's spine on it.

## The practical path (matches how the Catskill Crew guy handled Instagram)

### Tier A — free, works today (start here)
1. **Capture the cross-posts.** Most venues/organizers who make a FB event also put it
   on their **own website calendar** or a **ticketing platform** (Eventbrite, Do319,
   dice.fm). We scrape those directly and get a big chunk of "Facebook" events without
   touching Facebook. Every venue calendar we add shrinks the Facebook gap.
2. **Manual-assist extraction.** When you (Michael) or a reader spots a great FB event,
   drop the URL into the research chat. Claude `WebFetch`es the public event page and
   extracts title/date/venue/description into an event object. Semi-automated, zero cost,
   and you're curating anyway.
3. **Targeted web search.** Search surfaces many public FB events ("<venue> Iowa City
   facebook event <month>"); extract with WebFetch. Hit-or-miss but free.

### Tier B — paid API, when you want it automated (the Scrape Creators upgrade)
The video used **Scrape Creators** for Instagram; it (and alternatives) also cover
Facebook. When you're ready to automate a fixed set of pages/groups:
- **Scrape Creators** — same vendor as the video; check current Facebook endpoints.
- **Apify "Facebook Events Scraper"** actor — pay-per-run, returns structured events for
  a page or a location+date query. Cheapest to start; good for a weekly cron.
- **Bright Data** — heavier/pricier, more robust at scale.

Drop the key in `.env` (`SCRAPE_CREATORS_API_KEY` or an Apify token) and we add a
`scripts/fetch_facebook.py` that targets a curated list of pages — exactly mirroring the
ICS fetcher. This is the same "graduate Tier 3 to automation" step as Instagram; it costs
a little money, so it's opt-in and off by default.

## Recommendation
Run **Tier A now** (free, and the venue-calendar capture alone covers a lot). Add **Tier B**
only once the weekly rhythm is solid and you've decided a few specific FB pages/groups are
worth automating. Keep a curated allowlist of pages — don't try to boil the Facebook ocean;
that's where the junk lives.

## Curated FB pages/groups worth watching (seed — expand over time)
- Venue pages: Englert, Hancher, Gabe's, FilmScene, Iowa Children's Museum, city
  parks & rec pages.
- Community: local "Iowa City Moms" / "Johnson County Families" type groups (word-of-mouth),
  Downtown Iowa City, Think Iowa City.
> Verify each page is public and worth the slot before adding it to any automated pull.
