"""Fetch the weekend forecast from NWS (api.weather.gov) — free, keyless.

Returns raw forecast periods for Iowa City. The parent-framing ("pool day",
"bring the rain boots", "indoor-backup day") is editorial and happens in the
ccc-writer skill, not here — this just delivers clean facts.

    uv run python scripts/fetch_weather.py --days 4
"""

from __future__ import annotations

import argparse
import json
import sys

import requests

from ccc_core import USER_AGENT

# Iowa City, roughly the center of the county we cover.
IOWA_CITY = (41.6611, -91.5302)


def _get(url: str) -> dict:
    resp = requests.get(url, headers={"User-Agent": USER_AGENT, "Accept": "application/geo+json"}, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_forecast(lat: float = IOWA_CITY[0], lon: float = IOWA_CITY[1], periods: int = 8) -> dict:
    points = _get(f"https://api.weather.gov/points/{lat},{lon}")
    props = points["properties"]
    forecast = _get(props["forecast"])["properties"]["periods"][:periods]

    slim = [
        {
            "name": p["name"],
            "start": p["startTime"],
            "is_daytime": p["isDaytime"],
            "temp": p["temperature"],
            "temp_unit": p["temperatureUnit"],
            "wind": p.get("windSpeed"),
            "short": p["shortForecast"],
            "detailed": p["detailedForecast"],
            "precip_pct": (p.get("probabilityOfPrecipitation") or {}).get("value"),
        }
        for p in forecast
    ]
    return {
        "location": {
            "city": props["relativeLocation"]["properties"]["city"],
            "state": props["relativeLocation"]["properties"]["state"],
            "grid": f'{props["gridId"]} {props["gridX"]},{props["gridY"]}',
        },
        "periods": slim,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch NWS forecast for Iowa City.")
    ap.add_argument("--days", type=int, default=4, help="~2 periods/day (day+night)")
    args = ap.parse_args()
    data = fetch_forecast(periods=args.days * 2)
    print(json.dumps(data, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
