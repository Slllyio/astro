"""Full-kundali derivation for timed births — the maraka-rule inputs.

With a real birth time (Rodden-rated, from Astro-Databank) we can cast the
lagna and whole-sign houses, which unlocks the house-based part of B. V.
Raman's death-timing doctrine that the birth-time-free Wikidata corpus could
not test:

- **Maraka lords** — the lords of the 2nd and 7th signs from the lagna;
  their dasha periods are the classical death-inflicting windows.
- **8th lord** (ayus lord) and 8th-house occupants.
- Natal placements (Saturn/Mars/Rahu/Ketu in the 8th) for longevity-band
  tests.

Everything reuses the production engine (`app.core.ephemeris_engine`):
Lahiri sidereal, whole-sign houses, and the same D1 pipeline the app serves.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.core.ephemeris_engine import calculate_all_charts

# Sign rulerships (1 Aries .. 12 Pisces) — matches survival_analysis.SIGN_RULER
# and feature_engineering.SIGN_RULERS.
SIGN_RULER: dict[int, str] = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon",
    5: "Sun", 6: "Mercury", 7: "Venus", 8: "Mars",
    9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}

_GRAHAS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
           "Saturn", "Rahu", "Ketu")


def _nth_sign(lagna_sign: int, n: int) -> int:
    """Sign of the n-th house from lagna (whole-sign; n=1 is the lagna sign)."""
    return ((lagna_sign - 1 + (n - 1)) % 12) + 1


@dataclass(frozen=True)
class Kundali:
    """The subset of a chart the maraka validation needs."""
    lagna_sign: int
    moon_longitude: float           # sidereal, degrees
    birth_jd: float                 # UT julian day
    planet_house: dict[str, int]    # graha -> whole-sign house 1..12
    maraka_lords: frozenset[str]    # lords of 2H and 7H from lagna
    lord_8: str                     # lord of 8H from lagna
    lord_2: str
    lord_7: str

    def occupants(self, house: int) -> frozenset[str]:
        return frozenset(g for g, h in self.planet_house.items() if h == house)


def cast_kundali(
    year: int, month: int, day: int, hour: int, minute: int,
    tz_offset: float, lat: float, lon: float,
) -> Kundali | None:
    """Cast the natal chart via the production engine; None on failure.

    Validates inputs explicitly — Swiss Ephemeris is lenient (month 13 rolls
    over, |lat| > 90 may not raise), and scraped data contains junk that must
    not silently become a wrong chart.
    """
    if not (1 <= month <= 12 and 1 <= day <= 31 and 0 <= hour < 24
            and 0 <= minute < 60 and -90.0 <= lat <= 90.0
            and -180.0 <= lon <= 180.0 and abs(tz_offset) <= 14.0
            and 1000 <= year <= 2100):
        return None
    try:
        chart = calculate_all_charts(
            year, month, day, hour, minute, tz_offset,
            latitude=lat, longitude=lon,
        )
    except Exception:  # noqa: BLE001 — bad coords/dates in scraped data
        return None
    asc = chart.get("ascendant")
    if not asc:
        return None
    lagna_sign = int(asc["sign"])
    d1 = chart["d1"]
    planet_house = {}
    for g in _GRAHAS:
        pos = d1.get(g)
        if pos is None or "house" not in pos:
            return None
        planet_house[g] = int(pos["house"])
    lord_2 = SIGN_RULER[_nth_sign(lagna_sign, 2)]
    lord_7 = SIGN_RULER[_nth_sign(lagna_sign, 7)]
    lord_8 = SIGN_RULER[_nth_sign(lagna_sign, 8)]
    # jd: the engine computed it internally; recompute from mahadasha anchor —
    # simplest is to expose via moon block. calculate_all_charts returns
    # 'mahadasha' computed at jd; but we need birth_jd + moon lon for the
    # dasha timeline. d1 Moon longitude is sidereal; jd we recompute:
    from app.core.ephemeris_engine import calculate_jd, to_decimal_hours
    birth_jd = calculate_jd(year, month, day,
                            to_decimal_hours(hour, minute), tz_offset)
    return Kundali(
        lagna_sign=lagna_sign,
        moon_longitude=float(d1["Moon"]["longitude"]),
        birth_jd=birth_jd,
        planet_house=planet_house,
        maraka_lords=frozenset({lord_2, lord_7}),
        lord_8=lord_8,
        lord_2=lord_2,
        lord_7=lord_7,
    )
