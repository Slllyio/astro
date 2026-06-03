"""Kala Bala — temporal strength component of Shadbala (9 sub-components).

Usage:
    from app.raman_saab.primitives.shadbala import kala
    ctx = kala.KalaContext(birth_degrees=146.5, is_day=True, day_third=2,
                           year_lord="Saturn", month_lord="Mercury",
                           weekday_lord="Mercury", hora_lord="Moon",
                           ayanamsa=21 + 16/60)
    sh = kala.kala_bala("Sun", chart, ctx)   # -> Shashtiamsas (float)

Reference: B.V. Raman, *Graha & Bhava Balas* (GBB-5), §3.
All sub-functions return **Shashtiamsas**. Sun/Moon/Nodes get 0 for Yuddha.

Sub-components (GBB-5):
  Nathonnatha (§115-147)   — day/night arc converted to diurnal/nocturnal strength.
  Paksha     (§215-223)    — waxing/waning fraction; Moon doubled.
  Tribhaga   (§253-320)    — ruler of the birth-third of day/night; Jupiter always 60.
  Abda       (§563-596)    — 15 to the year lord.
  Masa       (§563-596)    — 30 to the month lord.
  Vara       (§563-596)    — 45 to the weekday lord.
  Hora       (§563-596)    — 60 to the hora lord.
  Ayana      (§936-957)    — declination-based; Sun doubled.
  Yuddha     (§1001-1043)  — planetary war adjustment (signed).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.raman_saab.chart.model import RamanChart

# ── Planet sets ────────────────────────────────────────────────────────────────

_DIVA: Final[frozenset[str]] = frozenset({"Sun", "Jupiter", "Venus"})
_RATRI: Final[frozenset[str]] = frozenset({"Moon", "Mars", "Saturn"})
_KALA_PLANETS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"
)

# ── KalaContext ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class KalaContext:
    """Temporal facts Raman derives outside the longitudes, injected so the Kala
    formulae are testable Track-B (no ephemeris).  Built from a real chart by
    ``chart/kala_context.py`` (Task 4).
    """

    birth_degrees: float   # time-from-midnight in degrees (Nathonnatha)
    is_day: bool           # day vs night birth (Tribhaga)
    day_third: int         # 0, 1, 2 — which third of the day/night (Tribhaga)
    year_lord: str         # Abda lord  (15 Sh)
    month_lord: str        # Masa lord  (30 Sh)
    weekday_lord: str      # Vara lord  (45 Sh)
    hora_lord: str         # Hora lord  (60 Sh)
    ayanamsa: float        # degrees; Sayana = nirayana + ayanamsa


# ══════════════════════════════════════════════════════════════════════════════
# Task 1 — 4 longitude/time sub-components
# ══════════════════════════════════════════════════════════════════════════════


def nathonnatha_bala(planet: str, birth_degrees: float) -> float:
    """Diurnal/nocturnal arc strength (GBB-5:115-147).

    ``birth_degrees`` = (time-from-midnight hours) × 15.
    Fold to [0, 180]; Diva planets score bd/3, Ratri (180-bd)/3, Mercury always 60.
    """
    if planet not in _KALA_PLANETS:
        return 0.0
    bd = birth_degrees % 360.0
    if bd > 180.0:
        bd = 360.0 - bd
    if planet == "Mercury":
        return 60.0
    return round(bd / 3.0 if planet in _DIVA else (180.0 - bd) / 3.0, 3)


def paksha_bala(planet: str, chart: RamanChart) -> float:
    """Waxing/waning strength (GBB-5:215-223).

    s = (Moon − Sun) % 360; fold to [0, 180]; shubha = s/3.
    Benefics (Jup, Ven, Merc) and waxing Moon get shubha; malefics get 60 − shubha.
    Moon is DOUBLED.
    """
    if planet not in _KALA_PLANETS:
        return 0.0
    if "Moon" not in chart.planets or "Sun" not in chart.planets:
        return 0.0
    s = (chart.planets["Moon"].lon - chart.planets["Sun"].lon) % 360.0
    if s > 180.0:
        s = 360.0 - s
    shubha = s / 3.0
    if planet == "Moon":
        return round(shubha * 2.0, 3)                         # Moon doubled
    benefic = planet in ("Jupiter", "Venus", "Mercury")
    return round(shubha if benefic else 60.0 - shubha, 3)


# Ayana declination table (arc-minutes).
# Cumulative at 0°, 15°, 30°, …, 90° and per-15° increments (GBB-5:936-957).
_CUM: Final[tuple[float, ...]] = (0, 362, 703, 1002, 1238, 1388, 1440)
_INC: Final[tuple[float, ...]] = (362, 341, 299, 236, 150, 52)

# Planets where NORTH declination adds strength (Sun, Mars, Jupiter, Venus).
_AYANA_ADD_NORTH: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Jupiter", "Venus"})


def _declination(sayana_lon: float) -> tuple[float, bool]:
    """Return (declination_degrees, is_north) from a sayana longitude."""
    lon = sayana_lon % 360.0
    if lon <= 90.0:
        bhuja, north = lon, True
    elif lon <= 180.0:
        bhuja, north = 180.0 - lon, True
    elif lon <= 270.0:
        bhuja, north = lon - 180.0, False
    else:
        bhuja, north = 360.0 - lon, False
    q = min(int(bhuja // 15), 5)
    decl_min = _CUM[q] + _INC[q] * (bhuja - 15.0 * q) / 15.0
    return decl_min / 60.0, north


def ayana_bala(planet: str, chart: RamanChart, ayanamsa: float) -> float:
    """Declination-based strength (GBB-5:936-957).

    Sayana = nirayana + ayanamsa.  Declination via the 6×15° table.
    Sign rule: Sun/Mars/Jup/Ven N+, S−; Moon/Saturn S+, N−; Mercury always +.
    Formula: ((24 + signed_decl) / 48) × 60.  Sun DOUBLED.
    """
    if planet not in _KALA_PLANETS or planet not in chart.planets:
        return 0.0
    decl, north = _declination(chart.planets[planet].lon + ayanamsa)
    if planet == "Mercury":
        signed = decl
    elif planet in _AYANA_ADD_NORTH:
        signed = decl if north else -decl
    else:                                       # Moon, Saturn: S additive, N subtractive
        signed = -decl if north else decl
    val = ((24.0 + signed) / 48.0) * 60.0
    return round(val * 2.0 if planet == "Sun" else val, 3)


# Disc diameters in arc-seconds (GBB-5:1001-1043).
_DISC: Final[dict[str, float]] = {
    "Mars": 9.4, "Mercury": 6.6, "Jupiter": 190.4, "Venus": 16.6, "Saturn": 158.0,
}


def yuddha_bala(
    planet: str,
    chart: RamanChart,
    prior_bala: Mapping[str, float],
) -> float:
    """Planetary-war adjustment (GBB-5:1001-1043).

    Only Mars/Mercury/Jupiter/Venus/Saturn can be at war (within 1° of each other).
    Lesser longitude = victor; adjustment = |ΔBala| / |Δdisc-diameter|.
    Returns the signed adjustment (positive = victor, negative = loser, 0 = no war).
    ``prior_bala`` = running (Sthana+Dik+Kala-so-far) aggregate; pass {} pre-assembly.
    """
    if planet not in _DISC or planet not in chart.planets:
        return 0.0
    for other, other_pos in chart.planets.items():
        if other == planet or other not in _DISC:
            continue
        sep = abs(chart.planets[planet].lon - other_pos.lon) % 360.0
        sep = min(sep, 360.0 - sep)
        if sep < 1.0 and prior_bala:
            diff = prior_bala.get(planet, 0.0) - prior_bala.get(other, 0.0)
            disc_diff = abs(_DISC[planet] - _DISC[other])
            yuddha = abs(diff) / disc_diff if disc_diff else 0.0
            winner = planet if chart.planets[planet].lon < other_pos.lon else other
            return round(yuddha if winner == planet else -yuddha, 3)
    return 0.0


# ══════════════════════════════════════════════════════════════════════════════
# Task 2 — 5 lord/third sub-components
# ══════════════════════════════════════════════════════════════════════════════

# Tribhaga rulers by third (GBB-5:264-273).
_DAY_THIRDS: Final[tuple[str, ...]] = ("Mercury", "Sun", "Saturn")
_NIGHT_THIRDS: Final[tuple[str, ...]] = ("Moon", "Venus", "Mars")


def tribhaga_bala(planet: str, *, is_day: bool, day_third: int) -> float:
    """Ruler of the birth-third of day/night gets 60; Jupiter always 60 (GBB-5:253-320)."""
    if planet == "Jupiter":
        return 60.0                                             # Jupiter always
    ruler = (_DAY_THIRDS if is_day else _NIGHT_THIRDS)[day_third]
    return 60.0 if planet == ruler else 0.0


def abda_bala(planet: str, year_lord: str) -> float:
    """Year lord (Abda) receives 15 Shashtiamsas (GBB-5:563-596)."""
    return 15.0 if planet == year_lord else 0.0


def masa_bala(planet: str, month_lord: str) -> float:
    """Month lord (Masa) receives 30 Shashtiamsas (GBB-5:563-596)."""
    return 30.0 if planet == month_lord else 0.0


def vara_bala(planet: str, weekday_lord: str) -> float:
    """Weekday lord (Vara) receives 45 Shashtiamsas (GBB-5:563-596)."""
    return 45.0 if planet == weekday_lord else 0.0


def hora_bala(planet: str, hora_lord: str) -> float:
    """Hora lord receives 60 Shashtiamsas (GBB-5:563-596)."""
    return 60.0 if planet == hora_lord else 0.0


# ══════════════════════════════════════════════════════════════════════════════
# Task 3 — kala_bala assembly
# ══════════════════════════════════════════════════════════════════════════════


def kala_bala(
    planet: str,
    chart: RamanChart,
    ctx: KalaContext,
    prior_bala: Mapping[str, float] | None = None,
) -> float:
    """Total Kala Bala (Shashtiamsas) = Σ of the 9 sub-components (GBB-5).

    ``prior_bala`` = each planet's (Sthana+Dik+Kala-so-far) aggregate needed by
    Yuddha.  Pass ``{}`` or ``None`` pre-assembly (Yuddha returns 0).
    """
    if planet not in _KALA_PLANETS:
        return 0.0
    total = (
        nathonnatha_bala(planet, ctx.birth_degrees)
        + paksha_bala(planet, chart)
        + tribhaga_bala(planet, is_day=ctx.is_day, day_third=ctx.day_third)
        + abda_bala(planet, ctx.year_lord)
        + masa_bala(planet, ctx.month_lord)
        + vara_bala(planet, ctx.weekday_lord)
        + hora_bala(planet, ctx.hora_lord)
        + ayana_bala(planet, chart, ctx.ayanamsa)
        + yuddha_bala(planet, chart, prior_bala or {})
    )
    return round(total, 3)
