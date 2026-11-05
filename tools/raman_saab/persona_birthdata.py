"""Birth data for the persona study — fetched, quality-gated, and never guessed.

BUILD-TIME tool — lives OUTSIDE app/. Reads a public astrology database and turns one
person into a castable nativity, or refuses. Nothing here touches engine state.

Why a module of its own, with a committed fixture and its own tests: a birth-data scrape
is the one step in the study whose failures are SILENT. A wrong ascendant makes every
house-based answer noise, and nothing downstream ever complains — the run would finish and
produce a confident, meaningless result. Three specific traps, each met by a check here:

* **Page furniture reads like a nativity.** Every astrotheme page carries a live transits
  widget ("Fri. 28 Aug., 04:19 AM UT"). A regex for a time over the whole page finds the
  furniture on every person. The parser anchors on the `Born:` / `In:` pair instead.
* **"Rodden" on the page is a person, not a rating.** The contributor line reads
  "Contributor : Lois Rodden". The rating is the token immediately before "Reliability".
* **Pre-standard-time births carry a zone's LMT, not a place's.** `zoneinfo` answers a 1879
  Ulm birth with Europe/Berlin's local mean time (+00:53:28) when Ulm's own is +00:39:58 —
  fourteen minutes, about 3.5 degrees of ascendant, on a chart whose own rectification
  question turns on cusp proximity. `standard_time_offset` returns None rather than an
  approximation, which is what drops such births from the roster.

Usage:
    py -3.12 -m tools.raman_saab.persona_birthdata --slug Marilyn_Monroe
    py -3.12 -m tools.raman_saab.persona_birthdata --slug Frida_Kahlo --zone America/Mexico_City
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import re
import time
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from typing import Optional
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

_BASE = "https://www.astrotheme.com/astrology/"
_NOMINATIM = "https://nominatim.openstreetmap.org/search"
_UA = "astro-persona-study/1.0 (research; contact via repository)"

#: Rodden ratings this study accepts. AA is a birth certificate or civil record; A is from
#: the person, a parent, or the family. Everything below (B biography, C caution, DD
#: conflicting, X no time) is dropped — the study reports its rating split, so admitting a
#: weaker tier would blur the one axis that could explain a null.
ACCEPTED_RATINGS = ("AA", "A")

#: The rating token sits immediately before the word "Reliability" in the page's data card.
_RATING_RE = re.compile(r"\b(AA|A|B|C|DD|X|XX)\b\s*Reliability", re.I)
#: `Born: Friday, March 14 , 1879, 11:30 AM In: Ulm (Germany)` — the spacing around the day
#: is the page's own, not a typo, so the pattern tolerates it.
_BORN_RE = re.compile(
    r"Born:\s*(?:\w+\.?,?\s*)?"                       # optional weekday
    r"([A-Z][a-z]+)\s+(\d{1,2})\s*,\s*(\d{4})\s*,\s*"  # month day, year,
    r"(\d{1,2}):(\d{2})\s*([AP]M)"                     # 11:30 AM
    r".{0,40}?In:\s*([^<]{2,80}?)\s*(?:Sun:|$)", re.S)
_SOURCE_RE = re.compile(r"Source\s*:\s*</td>\s*<td[^>]*>([^<]{2,120})<", re.I)
_MONTHS = ("January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December")


@dataclass(frozen=True)
class BirthRecord:
    """One nativity, with the provenance that decides whether it may be used."""
    slug: str
    name: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
    place: str
    rodden: str
    source_note: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    zone: str = ""
    tz_offset: Optional[float] = None

    @property
    def usable(self) -> bool:
        """Castable AND admissible: coordinates, a real standard-time offset, and a rating
        this study accepts. Anything else is dropped and recorded, never patched."""
        return (self.rodden.upper() in ACCEPTED_RATINGS
                and self.latitude is not None and self.longitude is not None
                and self.tz_offset is not None)


def strip_tags(html: str) -> str:
    """Markup out, single-spaced text in — the form both anchors are written against."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


def parse_astrotheme(html: str, *, slug: str = "", name: str = "") -> Optional[BirthRecord]:
    """The nativity stated on one fetched page, or None if the page does not state one.

    Returns None rather than a partial record: a birth with no time, or a page that failed
    to load, must leave the roster rather than enter it with a plausible-looking default.
    """
    flat = strip_tags(html)
    born = _BORN_RE.search(flat)
    if born is None:
        logger.info("no birth line found for %s", slug or name)
        return None
    month_name, day, year, hour, minute, meridiem, place = born.groups()
    if month_name not in _MONTHS:
        logger.info("unrecognised month %r for %s", month_name, slug or name)
        return None
    h = int(hour) % 12 + (12 if meridiem.upper() == "PM" else 0)

    rating = _RATING_RE.search(flat)
    source = _SOURCE_RE.search(html)
    return BirthRecord(
        slug=slug, name=name or slug.replace("_", " "),
        year=int(year), month=_MONTHS.index(month_name) + 1, day=int(day),
        hour=h, minute=int(minute), place=place.strip(),
        rodden=(rating.group(1).upper() if rating else ""),
        source_note=(source.group(1).strip() if source else ""))


def standard_time_offset(zone: str, rec: BirthRecord) -> Optional[float]:
    """The civil UTC offset in hours at that instant, or None if it is not standard time.

    `zoneinfo` answers pre-standard-time dates with the ZONE's local mean time, which is
    the reference city's, not the birth city's — an error of minutes that lands directly on
    the ascendant. Standard offsets are whole quarter-hours, so a non-quarter answer is the
    tell, and the honest response is to refuse the record rather than round it.
    """
    try:
        off = dt.datetime(rec.year, rec.month, rec.day, rec.hour, rec.minute,
                          tzinfo=ZoneInfo(zone)).utcoffset()
    except Exception:                                    # noqa: BLE001 — unknown zone name
        logger.warning("unknown time zone %r", zone)
        return None
    if off is None:
        return None
    minutes = off.total_seconds() / 60.0
    if minutes % 15 != 0:
        logger.info("%s at %s is local mean time (%+.4fh), not a standard offset — dropped",
                    rec.place, rec.year, minutes / 60.0)
        return None
    return minutes / 60.0


def _get(url: str, *, timeout: int = 30) -> str:
    """Decoded with the charset the server declares, not a guess.

    astrotheme serves ISO-8859-1. Reading it as UTF-8 turns `Coyoacán` into `Coyoac?n`,
    which then fails to geocode — a birthplace silently lost to an encoding default.
    """
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:      # noqa: S310 — https only
        raw = resp.read()
        charset = resp.headers.get_content_charset() or "utf-8"
    return raw.decode(charset, "replace")


def fetch_page(slug: str, *, timeout: int = 30) -> str:
    """The raw page for one person. Kept separate from parsing so the parser is testable
    against a committed fixture and never needs the network."""
    return _get(_BASE + urllib.parse.quote(slug), timeout=timeout)


def geocode(place: str, *, timeout: int = 30, pause: float = 1.1) -> Optional[tuple]:
    """(latitude, longitude) for a place name, from OpenStreetMap.

    The pause honours Nominatim's one-request-per-second policy; this runs over a roster of
    a couple of dozen, so being slow is free and being rude is not.
    """
    time.sleep(pause)
    url = f"{_NOMINATIM}?{urllib.parse.urlencode({'q': place, 'format': 'json', 'limit': 1})}"
    try:
        hits = json.loads(_get(url, timeout=timeout))
    except Exception:                                    # noqa: BLE001 — network or JSON
        logger.warning("geocoding failed for %r", place)
        return None
    if not hits:
        logger.info("no coordinates for %r", place)
        return None
    return round(float(hits[0]["lat"]), 4), round(float(hits[0]["lon"]), 4)


def resolve(slug: str, *, zone: str = "", name: str = "") -> Optional[BirthRecord]:
    """Fetch, parse, geocode and time-zone one person. None whenever any step refuses."""
    rec = parse_astrotheme(fetch_page(slug), slug=slug, name=name)
    if rec is None:
        return None
    coords = geocode(rec.place)
    if coords is None:
        return rec
    lat, lon = coords
    rec = BirthRecord(**{**asdict(rec), "latitude": lat, "longitude": lon, "zone": zone})
    if not zone:
        return rec
    return BirthRecord(**{**asdict(rec), "tz_offset": standard_time_offset(zone, rec)})


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description="Resolve one persona's birth data.")
    ap.add_argument("--slug", required=True, help="astrotheme page slug, e.g. Marilyn_Monroe")
    ap.add_argument("--zone", default="", help="IANA zone for the birthplace")
    args = ap.parse_args(argv)

    rec = resolve(args.slug, zone=args.zone)
    if rec is None:
        print(f"[persona-birthdata] {args.slug}: no nativity stated — dropped")
        return 1
    print(f"[persona-birthdata] {rec.name}")
    print(f"  born   {rec.year:04d}-{rec.month:02d}-{rec.day:02d} "
          f"{rec.hour:02d}:{rec.minute:02d}  in {rec.place}")
    print(f"  rodden {rec.rodden or '(none stated)'}   source: {rec.source_note or '-'}")
    print(f"  coords {rec.latitude}, {rec.longitude}   zone {rec.zone or '-'} "
          f"offset {rec.tz_offset if rec.tz_offset is not None else '(not standard time)'}")
    print(f"  usable {rec.usable}")
    return 0 if rec.usable else 1


if __name__ == "__main__":
    raise SystemExit(main())
