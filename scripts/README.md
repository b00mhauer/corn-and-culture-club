# scripts/

Python (uv-managed) fetch + normalize utilities. Built in Phase 1.

Planned:
- `fetch_ics.py`     — pull + parse ICS feeds from data/sources.yaml
- `fetch_html.py`    — HTML scrapers (firecrawl / requests+bs4) per source
- `fetch_weather.py` — NWS api.weather.gov (free, no key) for Iowa City
- `normalize.py`     — → common event schema, dedupe, age/cost tagging
- `build_edition.py` — assemble research.json for a given week

Run everything through uv:  `uv run python scripts/<name>.py`
