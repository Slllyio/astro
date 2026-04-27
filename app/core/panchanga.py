"""Panchanga (five limbs of Vedic time) for a given Julian Day.

Computes the five anga of Vedic almanacs:

1. **Tithi**     -- lunar day (0..29), waxing/waning paksha derived from
   ``moon_lon - sun_lon``.
2. **Karana**    -- half-tithi (0..59), seven movable + four fixed names.
3. **Yoga**      -- panchanga's Sun+Moon harmonic (0..26). NOT to be
   confused with chart-based planetary yogas.
4. **Vara**      -- weekday derived directly from the Julian Day.
5. **Nakshatra** -- Moon's nakshatra at the moment (delegated to
   ``app.core.nakshatra`` when available, with an inline fallback).

All Sun and Moon longitudes are sidereal Lahiri, sourced from
``app.core.ephemeris_engine.calculate_d1_position`` so panchanga values
stay consistent with the rest of the engine's outputs.
"""
from __future__ import annotations

from typing import TypedDict

import swisseph as swe

from app.core.ephemeris_engine import calculate_d1_position


# ---------------------------------------------------------------------------
# Tithi (30 lunar days per synodic month; 12 deg of moon-sun separation each)
# ---------------------------------------------------------------------------

TITHI_NAMES: tuple[str, ...] = (
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi",
    # Index 14 within a paksha: Purnima (full moon) in Shukla,
    # Amavasya (new moon) in Krishna. Resolved at lookup time.
    "Purnima",
)

PAKSHA_SHUKLA = "Shukla"
PAKSHA_KRISHNA = "Krishna"


# ---------------------------------------------------------------------------
# Karana (60 half-tithis; 6 deg of moon-sun separation each)
# ---------------------------------------------------------------------------

# 7 movable (chara) karanas. They cycle 8 times across indices 1..56.
KARANA_MOVABLE: tuple[str, ...] = (
    "Bava", "Balava", "Kaulava", "Taitila",
    "Garaja", "Vanija", "Vishti",
)

# 4 fixed (sthira) karanas at known fixed slots.
KARANA_KIMSTUGHNA = "Kimstughna"   # index 0
KARANA_SHAKUNI = "Shakuni"         # index 57
KARANA_CHATUSHPADA = "Chatushpada"  # index 58
KARANA_NAGA = "Naga"               # index 59


# ---------------------------------------------------------------------------
# Yoga (27 panchanga yogas; (sun + moon) traversing 360 deg in 27 slots)
# ---------------------------------------------------------------------------

YOGA_NAMES: tuple[str, ...] = (
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarma", "Dhriti", "Shoola", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyana", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Indra", "Vaidhriti",
)


# ---------------------------------------------------------------------------
# Vara (weekday). Standard JD weekday formula: ``int(jd + 1.5) % 7``.
#
# Empirically verified against pinned baselines:
#   * 1990-07-15 12:00 IST (06:30 UTC) -> JD ~2448087.77 -> formula = 0
#     and that date was a Sunday.
#   * 2000-01-01 12:00 UTC -> JD 2451545.0 -> formula = 6
#     and that date was a Saturday.
# So the mapping for this formula is 0=Sunday..6=Saturday.
# ---------------------------------------------------------------------------

VARA_NAMES: tuple[str, ...] = (
    "Sunday", "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday",
)


# ---------------------------------------------------------------------------
# Nakshatra: prefer the canonical module; fall back to an inline lookup.
# ---------------------------------------------------------------------------

try:  # pragma: no cover - import behaviour depends on neighbour module
    from app.core.nakshatra import nakshatra_for_longitude as _nakshatra_lookup
    _HAS_NAKSHATRA_MODULE = True
except Exception:  # pragma: no cover - exercised only if module is missing
    _HAS_NAKSHATRA_MODULE = False

    _FALLBACK_NAKSHATRAS: tuple[str, ...] = (
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
        "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
        "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
        "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
        "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
        "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
    )

    def _nakshatra_lookup(longitude: float) -> dict:  # type: ignore[no-redef]
        """Inline fallback when ``app.core.nakshatra`` is unavailable.

        Matches the project's floor-division boundary convention: an exact
        boundary lands at the START of the next nakshatra.
        """
        lon = longitude % 360.0
        span = 360 / 27
        idx = int(lon // span)
        if idx > 26:
            idx = 26
        return {
            "index": idx,
            "name": _FALLBACK_NAKSHATRAS[idx],
            "longitude_in_nakshatra": lon - (idx * span),
        }


# ---------------------------------------------------------------------------
# Result schemas
# ---------------------------------------------------------------------------


class TithiInfo(TypedDict):
    index: int      # 0..29
    name: str       # "Pratipada"..."Purnima" (Shukla) / "Amavasya" (Krishna)
    paksha: str     # "Shukla" or "Krishna"


class KaranaInfo(TypedDict):
    index: int      # 0..59
    name: str


class YogaInfo(TypedDict):
    index: int      # 0..26
    name: str


class VaraInfo(TypedDict):
    index: int      # 0..6 (0=Monday ... 6=Sunday)
    name: str       # "Monday".."Sunday"


class PanchangaResult(TypedDict):
    tithi: TithiInfo
    karana: KaranaInfo
    yoga: YogaInfo       # panchanga's yoga, distinct from chart yogas
    vara: VaraInfo
    nakshatra: dict      # NakshatraInfo when available; minimal dict otherwise


# ---------------------------------------------------------------------------
# Pure helpers (operate on longitudes / JD; no ephemeris coupling)
# ---------------------------------------------------------------------------


def _tithi_info(sun_lon: float, moon_lon: float) -> TithiInfo:
    """Compute tithi from sidereal Sun/Moon longitudes.

    ``tithi_index = int(((moon - sun) % 360) / 12)``. Indices 0..14 are
    Shukla paksha; 15..29 are Krishna paksha. Within each paksha, the
    fifteenth tithi (index 14 from the paksha start) is named Purnima
    (full moon, end of Shukla) or Amavasya (new moon, end of Krishna).
    """
    delta = (moon_lon - sun_lon) % 360.0
    index = int(delta / 12.0)
    if index > 29:  # defensive against fp edge cases at exactly 360
        index = 29

    if index < 15:
        paksha = PAKSHA_SHUKLA
        within_paksha = index
        name = "Purnima" if within_paksha == 14 else TITHI_NAMES[within_paksha]
    else:
        paksha = PAKSHA_KRISHNA
        within_paksha = index - 15
        name = "Amavasya" if within_paksha == 14 else TITHI_NAMES[within_paksha]

    return TithiInfo(index=index, name=name, paksha=paksha)


def _karana_info(sun_lon: float, moon_lon: float) -> KaranaInfo:
    """Compute karana (half-tithi) from sidereal Sun/Moon longitudes.

    Layout:
      - index 0:        Kimstughna (fixed)
      - indices 1..56:  the 7 movable karanas, cycling 8 times.
                        Mapping: ``KARANA_MOVABLE[(index - 1) % 7]``
      - index 57:       Shakuni (fixed)
      - index 58:       Chatushpada (fixed)
      - index 59:       Naga (fixed)
    """
    delta = (moon_lon - sun_lon) % 360.0
    index = int(delta / 6.0)
    if index > 59:  # defensive against fp edge cases at exactly 360
        index = 59

    if index == 0:
        name = KARANA_KIMSTUGHNA
    elif index == 57:
        name = KARANA_SHAKUNI
    elif index == 58:
        name = KARANA_CHATUSHPADA
    elif index == 59:
        name = KARANA_NAGA
    else:
        name = KARANA_MOVABLE[(index - 1) % 7]

    return KaranaInfo(index=index, name=name)


def _yoga_info(sun_lon: float, moon_lon: float) -> YogaInfo:
    """Compute panchanga yoga from sidereal Sun/Moon longitudes.

    27 yogas span 360 deg of (sun + moon), so each is 360/27 deg wide.
    """
    span = 360.0 / 27
    total = (sun_lon + moon_lon) % 360.0
    index = int(total / span)
    if index > 26:
        index = 26
    return YogaInfo(index=index, name=YOGA_NAMES[index])


def _vara_info(jd: float) -> VaraInfo:
    """Compute vara (weekday) from Julian Day.

    ``int(jd + 1.5) % 7`` with mapping 0=Monday..6=Sunday. The +1.5 shift
    accounts for the JD epoch starting at noon UT on a Monday.
    """
    index = int(jd + 1.5) % 7
    return VaraInfo(index=index, name=VARA_NAMES[index])


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def compute_panchanga(jd: float) -> PanchangaResult:
    """Compute all five limbs of the panchanga at a given Julian Day.

    Internally fetches Sun and Moon longitudes via the ephemeris engine
    (sidereal Lahiri) so values match other engine outputs exactly.
    """
    sun = calculate_d1_position(jd, swe.SUN)
    moon = calculate_d1_position(jd, swe.MOON)
    sun_lon = sun["longitude"]
    moon_lon = moon["longitude"]

    return PanchangaResult(
        tithi=_tithi_info(sun_lon, moon_lon),
        karana=_karana_info(sun_lon, moon_lon),
        yoga=_yoga_info(sun_lon, moon_lon),
        vara=_vara_info(jd),
        nakshatra=dict(_nakshatra_lookup(moon_lon)),
    )
