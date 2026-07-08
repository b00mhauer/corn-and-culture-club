"""Corn & Culture Club — shared core.

Deterministic gathering + structuring only. This is the "coverage floor" from
the editorial thesis: it produces a clean *candidate pool*. All taste — deciding
what's actually worth a busy parent's time, cutting junk, finding the non-obvious
— happens later, in the ccc-research skill (Claude). Keep judgment out of here;
keep it coarse, transparent, and flagged.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path

import yaml
from rapidfuzz import fuzz

# --- constants ---------------------------------------------------------------

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data"

# Polite identifier for every outbound request. Institutions want their events
# promoted; we still identify ourselves and link back.
USER_AGENT = "corn-and-culture-club/0.1 (+https://cornandcultureclub.com; michael@480th.com)"

# Some origins bot-block the honest UA; keep a browser-ish fallback for those.
BROWSER_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)

AGE_BANDS = ("0-4", "5-11", "12-18", "all")

# Towns we cover, plus loose aliases seen in venue/description text.
TOWNS = {
    # NB: no bare "ic " alias — it false-matches "botaniC Garden", "musiC ", etc.
    "Iowa City": ["iowa city", "downtown ic", "ped mall", "pedestrian mall"],
    "Coralville": ["coralville", "coral ridge"],
    "North Liberty": ["north liberty"],
    "Solon": ["solon"],
    "Tiffin": ["tiffin"],
    "University Heights": ["university heights"],
    "Oxford": ["oxford"],
    "Hills": ["hills"],
    "Swisher": ["swisher"],
    "Lone Tree": ["lone tree"],
}

# --- keyword tables for the coarse first-pass tagging ------------------------

_AGE_KEYWORDS = {
    "0-4": [
        "baby", "babies", "infant", "toddler", "tot ", "tots", "lapsit", "lap sit",
        "storytime", "story time", "preschool", "pre-k", "prek", "little ones",
        "ages 0", "0-2", "2-5", "under 5", "mother goose", "wee ",
    ],
    "5-11": [
        "kids", "children", "elementary", "school age", "school-age", "ages 5",
        "ages 6", "6-10", "5-11", "grade school", "youth", "juniors", "cub",
    ],
    "12-18": [
        "teen", "teens", "tween", "tweens", "middle school", "high school",
        "ages 12", "young adult", "ya ", "grades 6", "grades 7", "grades 9",
    ],
    "all": [
        "all ages", "all-ages", "family", "families", "family-friendly",
        "community", "everyone welcome", "intergenerational",
    ],
}

_FREE_KEYWORDS = ["free", "no cost", "no charge", "free admission", "free event", "$0"]
_PAID_KEYWORDS = ["ticket", "$", "admission", "registration required", "register", "fee", "cost:"]

_OUTDOOR_KEYWORDS = [
    "park", "trail", "garden", "outdoor", "farm", "orchard", "plaza", "pavilion",
    "festival", "market", "field", "green", "lawn", "riverfront", "campground",
    "playground", "splash pad", "pool",
]
_INDOOR_KEYWORDS = [
    "library", "museum", "theatre", "theater", "center", "gym", "hall", "studio",
    "cinema", "arena", "auditorium", "gallery", "lounge", "cafe", "brewery",
]

# Words that push an event toward "probably kid-relevant."
_FAMILY_POSITIVE = [
    "kid", "child", "family", "families", "toddler", "baby", "storytime",
    "story time", "all ages", "youth", "teen", "tween", "preschool", "puppet",
    "craft", "lego", "stem", "petting", "pumpkin", "trick or treat", "santa",
    "egg hunt", "read", "playground", "splash", "carousel", "zoo", "animal",
]
# Community/social occasions that are family-friendly even without kid words.
# These are the *interesting* events (the whole point of the newsletter), and the
# kid-keyword list above scores them 0, which biases curation toward libraries.
# This signal keeps them in contention. NB: kept outdoor/community-flavored so it
# doesn't sweep in bar shows (those get caught by _ADULT_SIGNALS).
_SOCIAL_POSITIVE = [
    "festival", "fair", "parade", "farmers market", "market", "in the park",
    "party in the park", "block party", "bbq", "barbecue", "fireworks",
    "concert", "live music", "music in the park", "food truck", "celebration",
    "community", "beef days", "summer social", "art walk", "open house",
]
# Words that suggest adults-only unless "family" also present.
_ADULT_SIGNALS = [
    "21+", "21 and over", "wine", "cocktail", "beer tasting", "happy hour",
    "gala", "burlesque", "trivia night", "bar crawl", "networking", "singles",
    "nightclub", "after dark", "late night",
]


# --- event schema ------------------------------------------------------------

@dataclass
class Event:
    """One candidate event. Coarse auto-tags; the skill refines/overrides."""

    title: str
    start: str  # ISO 8601
    source: str  # source id
    source_name: str = ""
    end: str | None = None
    all_day: bool = False
    when_text: str = ""  # human-readable time as given by source (e.g. FB "Sat, Jul 11 at 1 PM")
    venue: str | None = None
    town: str | None = None
    url: str | None = None
    description: str = ""
    age_bands: list[str] = field(default_factory=list)
    cost: str = "unknown"  # free | low | paid | unknown
    is_free: bool | None = None
    indoor_outdoor: str = "unknown"  # indoor | outdoor | unknown
    tags: list[str] = field(default_factory=list)
    family_relevance: int = 0  # 0..3 coarse
    auto_flags: list[str] = field(default_factory=list)
    confidence: float = 0.5
    id: str = ""

    def __post_init__(self) -> None:
        if not self.id:
            basis = f"{self.source}|{self.title}|{self.start}".lower()
            self.id = f"{self.source}:{hashlib.sha1(basis.encode()).hexdigest()[:10]}"

    def to_dict(self) -> dict:
        return asdict(self)


# --- source config -----------------------------------------------------------

def load_env(path: Path | None = None) -> dict[str, str]:
    """Minimal .env reader (no extra dep). Values already in os.environ win."""
    import os

    path = path or (REPO / ".env")
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return dict(os.environ)


def require_key(name: str) -> str:
    """Fetch a secret from env/.env or fail with a clear, key-free message."""
    import os

    load_env()
    val = os.environ.get(name, "").strip()
    if not val:
        raise SystemExit(
            f"Missing {name}. Add it to .env (copy .env.example). "
            f"This source needs a paid API key; it's opt-in and off by default."
        )
    return val


def load_sources(path: Path | None = None) -> list[dict]:
    path = path or (DATA / "sources.yaml")
    with open(path) as fh:
        return yaml.safe_load(fh)["sources"]


def sources_by(method: str | None = None, tier: int | None = None) -> list[dict]:
    out = load_sources()
    if method is not None:
        out = [s for s in out if s.get("method") == method]
    if tier is not None:
        out = [s for s in out if s.get("tier") == tier]
    return out


# --- coarse tagging (first pass only) ----------------------------------------

def _haystack(*parts: str | None) -> str:
    return " ".join(p.lower() for p in parts if p)


def guess_age_bands(text: str) -> list[str]:
    hits = [band for band, kws in _AGE_KEYWORDS.items() if any(k in text for k in kws)]
    return hits or []  # empty = unknown; skill decides


def guess_cost(text: str) -> tuple[str, bool | None]:
    if any(k in text for k in _FREE_KEYWORDS):
        return "free", True
    if any(k in text for k in _PAID_KEYWORDS):
        return "paid", False
    return "unknown", None


def guess_indoor_outdoor(text: str) -> str:
    out = any(k in text for k in _OUTDOOR_KEYWORDS)
    ind = any(k in text for k in _INDOOR_KEYWORDS)
    if out and not ind:
        return "outdoor"
    if ind and not out:
        return "indoor"
    return "unknown"


def guess_town(text: str, default: str | None = None) -> str | None:
    for town, aliases in TOWNS.items():
        if any(a in text for a in aliases):
            return town
    return default


def score_family_relevance(text: str, source_audience: str) -> tuple[int, list[str]]:
    """Coarse 0..3. Flags uncertain calls for the skill/human to review.

    Rewards both explicit kid-programming AND community-social occasions, so a
    free concert-in-the-park isn't scored 0 next to a library storytime. A
    `social_event` flag marks the community picks so curation can feature them.
    """
    flags: list[str] = []
    pos = sum(1 for k in _FAMILY_POSITIVE if k in text)
    social = [k for k in _SOCIAL_POSITIVE if k in text]
    adult = [k for k in _ADULT_SIGNALS if k in text]
    has_family_word = any(k in text for k in ("family", "all ages", "kid", "child"))

    score = 0
    if source_audience == "family":
        score += 1  # source is a family venue → baseline lean
    score += min(pos, 2)  # up to +2 for kid words
    if social:
        score += 1  # a community/social occasion counts too
        flags.append("social_event")

    if adult and not has_family_word and not social:
        score = max(0, score - 2)
        flags.append(f"adult_signal:{adult[0]}")
    if score == 0:
        flags.append("family_relevance_uncertain")
    return min(score, 3), flags


# Titles that are usually NOT things to go do (closures, admin, filler). The
# skill makes the final cut; we just flag them so junk is easy to spot/drop.
_NON_EVENT_SIGNALS = [
    "closed", "cancelled", "canceled", "no school", "holiday - ", "postponed",
    "rescheduled", "sold out", "private event", "staff only", "members only meeting",
]


def flag_noise(ev: Event) -> list[str]:
    t = ev.title.lower()
    return ["likely_non_event"] if any(s in t for s in _NON_EVENT_SIGNALS) else []


def enrich(ev: Event, source_audience: str = "general") -> Event:
    """Run all coarse taggers over an event in place."""
    text = _haystack(ev.title, ev.description, ev.venue, ev.town)
    ev.age_bands = ev.age_bands or guess_age_bands(text)
    if ev.cost == "unknown":
        ev.cost, ev.is_free = guess_cost(text)
    if ev.indoor_outdoor == "unknown":
        ev.indoor_outdoor = guess_indoor_outdoor(text)
    ev.town = ev.town or guess_town(text)
    ev.family_relevance, flags = score_family_relevance(text, source_audience)
    ev.auto_flags = list(dict.fromkeys([*ev.auto_flags, *flags, *flag_noise(ev)]))
    if not ev.age_bands:
        ev.auto_flags.append("age_uncertain")
    return ev


# --- dedupe ------------------------------------------------------------------

def _day(iso: str) -> str:
    return iso[:10] if iso else ""


def dedupe(events: list[Event], threshold: int = 87) -> list[Event]:
    """Collapse the same event reported by multiple sources.

    Match = same calendar day AND fuzzy(title) >= threshold. Keeps the richer
    record (longer description) and records the merged sources in tags.
    """
    kept: list[Event] = []
    for ev in sorted(events, key=lambda e: (e.start or "", -len(e.description or ""))):
        dup = None
        for k in kept:
            if _day(k.start) == _day(ev.start) and fuzz.token_set_ratio(k.title, ev.title) >= threshold:
                dup = k
                break
        if dup is None:
            kept.append(ev)
        else:
            tag = f"also:{ev.source}"
            if tag not in dup.tags:
                dup.tags.append(tag)
            for band in ev.age_bands:
                if band not in dup.age_bands:
                    dup.age_bands.append(band)
    return kept


# --- misc helpers ------------------------------------------------------------

def parse_window(start: str | None, days: int) -> tuple[date, date]:
    """Return (start_date, end_date_inclusive). Default start = today."""
    if start:
        d0 = datetime.strptime(start, "%Y-%m-%d").date()
    else:
        d0 = date.today()
    from datetime import timedelta

    return d0, d0 + timedelta(days=days - 1)


def search_url(title: str, town: str | None = None, when: str | None = None) -> str:
    """A Google-search fallback link for when we have no real event page. A search
    that surfaces the event beats a homepage that buries it."""
    from urllib.parse import quote_plus

    q = f'"{title}"'
    if town:
        q += f" {town}"
    if when:
        q += f" {when}"
    return f"https://www.google.com/search?q={quote_plus(q)}"


def clean(text: str | None) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)  # strip stray HTML
    text = text.replace("&#039;", "'").replace("&amp;", "&").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", text).strip()
