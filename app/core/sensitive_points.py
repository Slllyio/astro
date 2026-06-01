"""Sensitive points + Upagrahas (sub-planets) — Gap E.

Classical Vedic astrology uses ~15 named calculated points beyond the
9 grahas. These are computed from planetary longitudes via specific
formulae and function as silent karmic-trigger markers. The most-used
are:

## Sensitive Points

- **Bhrigu Bindu** — midpoint of Rahu and Moon longitudes. The
  "karmic midpoint" where Rahu's accumulated load meets Moon's
  emotional/public-mind surface. Transits over Bhrigu Bindu trigger
  major life events. (Nadi tradition — first systematized by Bhrigu
  Samhita; modern usage popularized by R. Santhanam, K.N. Rao.)

- **Pranapada** — life-energy point derived from Sun's longitude +
  ascendant calculation. BPHS Ch.91. Three different formulae exist
  per BPHS depending on whether Sun is in Chara/Sthira/Dwiswabhava
  sign at birth. Used for: vitality, longevity-cusp, near-death events.

- **Bhāva Madhya** — exact degree of bhava center; used for cuspal
  analysis (Sripati / Krishneeya chalit bhava system).

## Upagrahas (5 main, derived from Sun's longitude)

Per BPHS Ch.84-88, five "sub-planets" arise from Sun's longitude
via fixed degree-offsets. Each functions as a silent afflictor:

- **Dhuma** ("smoke") = Sun + 4°13'20" (133°20')
- **Vyatipata** ("crisis") = 360° − Dhuma (i.e., 226°40' arc back)
- **Parivesha** ("halo") = Vyatipata + 180°
- **Indrachapa** ("rainbow") = 360° − Parivesha
- **Upaketu** ("flag/tail") = Indrachapa + 16°40' (Sun + 30°)

When Upagrahas conjoin or aspect planets/bhavas they ADD a layer of
silent affliction. Vyatipata + Lagna = mortality risk; Dhuma + 8H =
slow chronic illness; Upaketu + 6H = sudden hidden enemies.

## Maandi / Gulika

The "son of Saturn" — most-malefic calculated point per BPHS Ch.7.
Computed from the time of birth divided into 8 parts of the day or
night. The Maandi position depends on:
1. Day-of-week of birth
2. Is the birth diurnal or nocturnal
3. The specific part of the day/night (per BPHS table)

Maandi conjoined with a planet poisons that planet's significations.
In 8H = severe Maraka; in 6H = chronic disease; with Lagna lord =
self-undermining.

## Beeja Sphuta + Kshetra Sphuta — Fertility points

- **Beeja Sphuta** (male potency) = Sun_lon + Jupiter_lon + Venus_lon
  → reduced to a sign. Male native's procreative capacity.

- **Kshetra Sphuta** (female potency) = Moon_lon + Jupiter_lon + Mars_lon
  → reduced to a sign. Female native's procreative capacity.

Strong dignity (own/exalted sign, no malefic aspect) = good fertility;
debilitated/afflicted = challenged fertility (modern reading: lower
sperm count / ovarian reserve issues / IVF requirements).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.core.chart_model import Chart
from app.core.dignity import (
    is_debilitated, is_exalted, is_own_sign,
)


@dataclass(frozen=True)
class SensitivePoint:
    """One calculated sensitive point with its sign + house + interpretation hint."""
    name: str                  # "Bhrigu Bindu", "Pranapada", etc.
    longitude: float           # 0-360°, sidereal
    sign: int                  # 1..12
    natal_house: int           # 1..12 (from chart's asc_sign)
    degree_in_sign: float      # 0-30°
    interpretation_hint: str   # short doctrine phrase


@dataclass(frozen=True)
class FertilitySphuta:
    """Beeja or Kshetra Sphuta with dignity classification."""
    name: str
    longitude: float
    sign: int
    sign_lord: str
    dignity: str               # "exalted" | "own" | "neutral" | "debilitated"
    fertility_grade: str       # "STRONG" | "AVERAGE" | "WEAK"


# Sign-lord lookup
_SIGN_LORDS: Final[Mapping[int, str]] = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
    7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}


# Upagraha offsets from Sun's longitude in degrees per BPHS Ch.84-88
_UPAGRAHA_OFFSETS_FROM_SUN: Final[Mapping[str, float]] = {
    # Dhuma is Sun + 4°13'20" — but actually classical: Sun_lon + 133°20'
    # to find Dhuma, NOT a small offset. The 4°13'20" is the offset of
    # day-degree-arithmetic. Let me use the standard formulation:
    "Dhuma":      133.0 + 20.0 / 60.0,           # Sun + 133°20'
    "Vyatipata":  360.0 - (133.0 + 20.0 / 60.0), # 226°40' from Sun
    "Parivesha":  360.0 - (133.0 + 20.0 / 60.0) + 180.0,
    "Indrachapa": 360.0 - (360.0 - (133.0 + 20.0 / 60.0) + 180.0),
    "Upaketu":    30.0,                          # Sun + 30°
}


def bhrigu_bindu(chart: Chart) -> SensitivePoint:
    """Midpoint of Rahu and Moon longitudes — "karmic midpoint".

    Formula: ((Rahu_lon + Moon_lon) / 2) mod 360.
    Uses the SHORTER arc midpoint — if Rahu and Moon are more than 180°
    apart, we go the other way around to find the true midpoint.

    Per Nadi tradition / R. Santhanam's compendium. Transits over
    Bhrigu Bindu reliably trigger life-pivot events.
    """
    rahu = chart.planet_lons.get("Rahu")
    moon = chart.planet_lons.get("Moon")
    if rahu is None or moon is None:
        raise ValueError(
            "bhrigu_bindu requires Rahu and Moon longitudes in chart"
        )
    diff = abs(rahu - moon)
    if diff > 180:
        # Take midpoint on the other side
        mid = ((rahu + moon) / 2 + 180) % 360
    else:
        mid = (rahu + moon) / 2
    sign = int(mid // 30) + 1
    natal_house = ((sign - chart.asc_sign) % 12) + 1
    return SensitivePoint(
        name="Bhrigu Bindu",
        longitude=mid, sign=sign, natal_house=natal_house,
        degree_in_sign=mid - (sign - 1) * 30,
        interpretation_hint=(
            "Karmic midpoint of Rahu (accumulated load) and Moon (mind/public). "
            "Transits here trigger major karmic-pivot life events."
        ),
    )


def pranapada(chart: Chart) -> SensitivePoint:
    """Life-energy point — BPHS Ch.91.

    Simplified formula (most-cited variant): Pranapada longitude =
    (Sun_lon + 3 * (ascendant_arc_from_Aries)) mod 360, divided to
    find the resulting sign.

    The full BPHS formulation has Chara/Sthira/Dwiswabhava variants;
    we implement the universal version here. The point indicates
    life-vitality location and near-death-event windows when crossed.
    """
    sun_lon = chart.planet_lons.get("Sun")
    if sun_lon is None:
        raise ValueError("pranapada requires Sun longitude in chart")
    asc_arc = chart.asc_lon
    # Sun longitude in 'vighatika' (1/3600 of a day) — simplified
    pp_lon = (sun_lon + 3 * asc_arc) % 360
    sign = int(pp_lon // 30) + 1
    natal_house = ((sign - chart.asc_sign) % 12) + 1
    return SensitivePoint(
        name="Pranapada",
        longitude=pp_lon, sign=sign, natal_house=natal_house,
        degree_in_sign=pp_lon - (sign - 1) * 30,
        interpretation_hint=(
            "Life-energy point per BPHS Ch.91. Transits here mark "
            "vitality-cusp + significant-event timing."
        ),
    )


def upagrahas(chart: Chart) -> dict[str, SensitivePoint]:
    """The 5 Upagrahas (sub-planets) derived from Sun's longitude.

    Per BPHS Ch.84-88. Each functions as a silent malefic when
    conjoined with planets or bhavas — Vyatipata especially is the
    classical "danger marker".
    """
    sun_lon = chart.planet_lons.get("Sun")
    if sun_lon is None:
        raise ValueError("upagrahas require Sun longitude in chart")
    out: dict[str, SensitivePoint] = {}
    interpretation = {
        "Dhuma":      "Smoke — slow chronic afflictions when conjoined",
        "Vyatipata":  "Crisis — most-dangerous unseen point; mortality marker",
        "Parivesha":  "Halo — confusing/illusory afflictions",
        "Indrachapa": "Rainbow — false promises, mirage-like results",
        "Upaketu":    "Tail — sudden disturbances, comet-like reversal",
    }
    for name, offset in _UPAGRAHA_OFFSETS_FROM_SUN.items():
        lon = (sun_lon + offset) % 360
        sign = int(lon // 30) + 1
        natal_house = ((sign - chart.asc_sign) % 12) + 1
        out[name] = SensitivePoint(
            name=name, longitude=lon, sign=sign,
            natal_house=natal_house,
            degree_in_sign=lon - (sign - 1) * 30,
            interpretation_hint=interpretation[name],
        )
    return out


# Maandi / Gulika table per BPHS Ch.7
# Index = day of week (0=Sunday, 1=Monday, ..., 6=Saturday)
# Inner index = part-of-day (0..7 = 8 equal parts of the day or night)
# Value = the part-of-day Maandi occupies (Saturn's son rules)
# Source: BPHS Ch.7.34-37 + Phaladeepika Ch.4
_MAANDI_DAY_PART: Final[tuple[int, ...]] = (
    # Sunday  Monday  Tuesday  Wednesday  Thursday  Friday  Saturday
    6,       5,      4,       3,         2,        1,      0,
)
_MAANDI_NIGHT_PART: Final[tuple[int, ...]] = (
    2, 1, 0, 6, 5, 4, 3,
)


def maandi(
    chart: Chart, day_of_week: int, is_day_birth: bool,
    sunrise_lon_offset: float = 0.0,
) -> SensitivePoint:
    """Maandi/Gulika — son of Saturn, the most-malefic calculated point.

    Per BPHS Ch.7.34-37. Calculated by dividing the day (sunrise to
    sunset) or night (sunset to sunrise) into 8 equal parts; Saturn's
    son rules one specific part determined by day-of-week.

    Args:
        chart: natal Chart.
        day_of_week: 0=Sunday, 1=Monday, ..., 6=Saturday.
        is_day_birth: True if birth was between sunrise and sunset.
        sunrise_lon_offset: degrees of arc Sun travels per equal-part
            (typically computed externally; default 0.0 uses the natal
            Sun longitude as proxy, less precise).

    Returns:
        SensitivePoint at the calculated Maandi longitude.
    """
    if not 0 <= day_of_week <= 6:
        raise ValueError(f"day_of_week must be 0..6, got {day_of_week}")
    sun_lon = chart.planet_lons.get("Sun")
    if sun_lon is None:
        raise ValueError("maandi requires Sun longitude in chart")
    table = _MAANDI_DAY_PART if is_day_birth else _MAANDI_NIGHT_PART
    part_index = table[day_of_week]
    # Simplified: place Maandi at Sun_lon + (part_index * 22.5°) — each
    # of the 8 parts is 1/8 of a half-day, conventionally treated as
    # 22.5° solar arc.
    maandi_lon = (sun_lon + part_index * 22.5 + sunrise_lon_offset) % 360
    sign = int(maandi_lon // 30) + 1
    natal_house = ((sign - chart.asc_sign) % 12) + 1
    return SensitivePoint(
        name="Maandi (Gulika)",
        longitude=maandi_lon, sign=sign, natal_house=natal_house,
        degree_in_sign=maandi_lon - (sign - 1) * 30,
        interpretation_hint=(
            f"Saturn's son — most-malefic calculated point. Birth-day "
            f"part {part_index + 1}/8 ({'day' if is_day_birth else 'night'}). "
            "Conjoined planets/bhavas: their significations are poisoned."
        ),
    )


def _classify_fertility(sphuta_sign: int, sphuta_planet: str) -> tuple[str, str]:
    """Return (dignity_label, fertility_grade) for a Sphuta point."""
    if is_exalted(sphuta_planet, sphuta_sign):
        return "exalted", "STRONG"
    if is_own_sign(sphuta_planet, sphuta_sign):
        return "own", "STRONG"
    if is_debilitated(sphuta_planet, sphuta_sign):
        return "debilitated", "WEAK"
    return "neutral", "AVERAGE"


def beeja_sphuta(chart: Chart) -> FertilitySphuta:
    """Male potency point = Sun_lon + Jupiter_lon + Venus_lon (mod 360).

    Dignity of sign-lord at result longitude grades male fertility.
    Per Mansagari + later commentaries. Modern reading: lower sperm
    count / hormone issues when sphuta-lord debilitated.
    """
    sun = chart.planet_lons.get("Sun")
    jup = chart.planet_lons.get("Jupiter")
    ven = chart.planet_lons.get("Venus")
    if None in (sun, jup, ven):
        raise ValueError(
            "beeja_sphuta requires Sun, Jupiter, Venus longitudes"
        )
    lon = (sun + jup + ven) % 360
    sign = int(lon // 30) + 1
    lord = _SIGN_LORDS[sign]
    dignity, grade = _classify_fertility(sign, lord)
    return FertilitySphuta(
        name="Beeja Sphuta", longitude=lon, sign=sign,
        sign_lord=lord, dignity=dignity, fertility_grade=grade,
    )


def kshetra_sphuta(chart: Chart) -> FertilitySphuta:
    """Female potency point = Moon_lon + Jupiter_lon + Mars_lon (mod 360).

    Dignity of sign-lord grades female fertility. Modern reading:
    ovarian reserve / menstrual regularity / pregnancy success when
    sphuta-lord debilitated.
    """
    moon = chart.planet_lons.get("Moon")
    jup = chart.planet_lons.get("Jupiter")
    mars = chart.planet_lons.get("Mars")
    if None in (moon, jup, mars):
        raise ValueError(
            "kshetra_sphuta requires Moon, Jupiter, Mars longitudes"
        )
    lon = (moon + jup + mars) % 360
    sign = int(lon // 30) + 1
    lord = _SIGN_LORDS[sign]
    dignity, grade = _classify_fertility(sign, lord)
    return FertilitySphuta(
        name="Kshetra Sphuta", longitude=lon, sign=sign,
        sign_lord=lord, dignity=dignity, fertility_grade=grade,
    )


@dataclass(frozen=True)
class SensitivePointsReport:
    """Aggregate report of all sensitive points for a chart."""
    bhrigu_bindu: SensitivePoint
    pranapada: SensitivePoint
    upagrahas: Mapping[str, SensitivePoint]
    beeja_sphuta: FertilitySphuta
    kshetra_sphuta: FertilitySphuta
    maandi: SensitivePoint | None = None  # Requires day-of-week + is_day_birth


def compute_all(
    chart: Chart, day_of_week: int | None = None,
    is_day_birth: bool | None = None,
) -> SensitivePointsReport:
    """Compute the full sensitive-points report for a chart.

    Maandi is included only when both day_of_week and is_day_birth are
    provided (it requires birth-time + day-of-week metadata not in the
    pure-chart input).
    """
    m: SensitivePoint | None = None
    if day_of_week is not None and is_day_birth is not None:
        m = maandi(chart, day_of_week, is_day_birth)
    return SensitivePointsReport(
        bhrigu_bindu=bhrigu_bindu(chart),
        pranapada=pranapada(chart),
        upagrahas=upagrahas(chart),
        beeja_sphuta=beeja_sphuta(chart),
        kshetra_sphuta=kshetra_sphuta(chart),
        maandi=m,
    )
