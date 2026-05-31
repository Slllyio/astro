"""Varshaphala / Tajik — annual progression + Sahams (S-4).

Vimshottari MD/AD/PD gives chart-level dasha precision to about a year.
For TIGHTER predictions ("what will happen in THIS year"), classical
Jyotisha uses **Tajik / Varshaphala**: a separate annual chart cast at
the moment Sun returns to its exact natal longitude (the "solar
return"), plus a set of progressing sensitive points (Muntha + Sahams)
that activate specific life domains for the year.

This module computes a SIMPLIFIED Varshaphala that doesn't require a
full ephemeris call (no solar-return chart cast):

  * **Muntha**     — progressing sensitive point that starts in natal
                     Lagna and advances 1 sign per year. At age 0 → 1H,
                     age 1 → 2H, age 11 → 12H, age 12 → 1H again.
  * **Munthesha**  — sign-lord of the sign Muntha currently occupies.
                     Primary planet of the year.
  * **Sahams**     — natal-frame sensitive midpoints. Each computed by a
                     classical formula like "Punya = Asc + Moon - Sun".
                     Their HOUSE from Lagna shows which life domain
                     each saham primes for activation.

## Sahams covered

This module covers the 8 most-cited Sahams (per Phaladeepika Ch.16 +
Pancha Pakshi commentaries). The full Tajik canon has 50+; the
remaining are domain-specialized (e.g. for muhurta) and would be added
on demand.

| Saham   | Formula (longitudes)                | Domain               |
|---------|-------------------------------------|----------------------|
| Punya   | Asc + Moon - Sun                    | merit / virtue / luck |
| Vidya   | Asc + Mercury - Jupiter             | learning / knowledge  |
| Karma   | Asc + Mars - Mercury                | action / career       |
| Yasas   | Asc + Jupiter - Mercury             | fame / reputation     |
| Putra   | Asc + Jupiter - Saturn              | children / progeny    |
| Vivaha  | Asc + Venus - Saturn (unisex form)  | marriage              |
| Mrityu  | Asc + 8H_cusp - Moon                | death-risk / longevity|
| Bhratru | Asc + Jupiter - Mars                | siblings              |

## What this is NOT

This is not a full Varshaphala. A complete implementation would cast
the actual solar-return chart at the JD when Sun reaches natal-Sun
longitude, then read the entire chart through the Varshaphala lens
(Sahams referenced to the annual Asc, not natal). For the bulk
pipeline where birth_jd may be imprecise (44% date-only in our corpus),
the natal-frame Sahams + Muntha are the doctrinally-justifiable subset
we can deliver without misleading precision.

## References

  * Phaladeepika Ch.16 — Sahams + Muntha
  * V. Subrahmanya Sastri's *Tajik Neelakanthi* — full Tajik canon
  * BV Raman *Hindu Predictive Astrology* — Muntha delineation
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping


# ─── Sign-lord (duplicated to avoid import cycle) ───────────────────


_SIGN_LORDS: Final[Mapping[int, str]] = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
    7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}


# ─── Muntha ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Muntha:
    """Progressing sensitive point at age N."""
    sign: int                    # 1..12
    house_from_lagna: int        # 1..12 (always = sign-asc_sign+1 mod 12+1)
    munthesha: str               # planet ruling the muntha sign
    age_years: float             # age input used
    domain_focus: str            # which life domain this year primes


# Doctrinal reading of Muntha-in-bhava (Phaladeepika Ch.16.4)
_MUNTHA_HOUSE_DOMAIN: Final[Mapping[int, str]] = {
    1: "self / body / new ventures focus",
    2: "wealth / family / speech focus",
    3: "siblings / courage / short journeys",
    4: "mother / home / property focus",
    5: "children / education / creativity",
    6: "service / health / debt / litigation",
    7: "spouse / partnerships / public dealings",
    8: "longevity-test / occult / sudden changes",
    9: "father / dharma / long-journey / fortune",
    10: "career / status / authority focus",
    11: "gains / network / aspirations",
    12: "expenses / loss / moksha / foreign-residence",
}


def compute_muntha(asc_sign: int, age_years: float) -> Muntha:
    """Compute Muntha at the given age.

    Muntha starts in the natal Lagna at age 0 and advances 1 sign per
    completed year. The year-month math:

      muntha_sign = ((asc_sign - 1 + int(age_years)) % 12) + 1

    Returns Muntha aggregate with sign + house + munthesha + domain hint.
    """
    if age_years < 0:
        raise ValueError(f"age_years must be >= 0, got {age_years}")
    years_completed = int(age_years)
    muntha_sign = ((asc_sign - 1 + years_completed) % 12) + 1
    house = ((muntha_sign - asc_sign) % 12) + 1
    lord = _SIGN_LORDS[muntha_sign]
    return Muntha(
        sign=muntha_sign, house_from_lagna=house, munthesha=lord,
        age_years=float(age_years),
        domain_focus=_MUNTHA_HOUSE_DOMAIN.get(house, "general focus"),
    )


# ─── Sahams ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Saham:
    """One sensitive point with its domain reading."""
    name: str
    formula: str                 # human-readable formula
    longitude: float             # 0..360
    sign: int                    # 1..12
    house_from_lagna: int        # 1..12
    domain: str                  # what life area this saham primes
    is_well_placed: bool         # True if in kendra/trikona, False if in dushtana


_KENDRAS: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_TRIKONAS: Final[frozenset[int]] = frozenset({5, 9})
_DUSHTANAS: Final[frozenset[int]] = frozenset({6, 8, 12})


def _saham_position(
    asc_lon: float, plus_lon: float, minus_lon: float,
) -> tuple[float, int]:
    """Generic saham formula: Asc + X - Y, mod 360.

    Returns (longitude, sign).
    """
    lon = (asc_lon + plus_lon - minus_lon) % 360.0
    sign = int(lon // 30.0) + 1
    return (lon, sign)


def _house_from_lagna(saham_sign: int, asc_sign: int) -> int:
    return ((saham_sign - asc_sign) % 12) + 1


def _is_well_placed(house: int) -> bool:
    return house in _KENDRAS or house in _TRIKONAS


def compute_sahams(
    asc_sign: int, asc_lon: float,
    planet_lons: Mapping[str, float],
) -> tuple[Saham, ...]:
    """Compute the 8 core natal-frame Sahams.

    Args:
        asc_sign: 1..12 — natal Lagna sign.
        asc_lon: 0..360 — natal Lagna longitude.
        planet_lons: {planet: longitude} from chart.planet_lons.

    Returns:
        Tuple of 8 Saham reports.
    """
    def _need(planet: str) -> float | None:
        return planet_lons.get(planet)

    sahams: list[Saham] = []

    def _add(name: str, plus_planet: str, minus_planet: str,
             formula: str, domain: str) -> None:
        plus_lon = _need(plus_planet)
        minus_lon = _need(minus_planet)
        if plus_lon is None or minus_lon is None:
            return
        lon, sign = _saham_position(asc_lon, plus_lon, minus_lon)
        house = _house_from_lagna(sign, asc_sign)
        sahams.append(Saham(
            name=name, formula=formula,
            longitude=round(lon, 3), sign=sign,
            house_from_lagna=house, domain=domain,
            is_well_placed=_is_well_placed(house),
        ))

    _add("Punya", "Moon", "Sun",
         "Asc + Moon - Sun", "merit / virtue / luck")
    _add("Vidya", "Mercury", "Jupiter",
         "Asc + Mercury - Jupiter", "learning / knowledge")
    _add("Karma", "Mars", "Mercury",
         "Asc + Mars - Mercury", "action / career")
    _add("Yasas", "Jupiter", "Mercury",
         "Asc + Jupiter - Mercury", "fame / reputation")
    _add("Putra", "Jupiter", "Saturn",
         "Asc + Jupiter - Saturn", "children / progeny")
    _add("Vivaha", "Venus", "Saturn",
         "Asc + Venus - Saturn (unisex)", "marriage")
    # Mrityu uses 8H cusp longitude (asc_lon + 210° approx for whole-sign)
    # Simplified: use cusp of 8th sign from Lagna
    eighth_cusp = (asc_lon + 7 * 30.0) % 360.0
    moon_lon = _need("Moon")
    if moon_lon is not None:
        lon = (asc_lon + eighth_cusp - moon_lon) % 360.0
        sign = int(lon // 30.0) + 1
        house = _house_from_lagna(sign, asc_sign)
        sahams.append(Saham(
            name="Mrityu",
            formula="Asc + 8H-cusp - Moon",
            longitude=round(lon, 3), sign=sign,
            house_from_lagna=house, domain="death-risk / longevity-test",
            is_well_placed=_is_well_placed(house),
        ))
    _add("Bhratru", "Jupiter", "Mars",
         "Asc + Jupiter - Mars", "siblings")

    return tuple(sahams)


# ─── Aggregate ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class VarshaphalaReport:
    """Year-progression sensitive points for a chart at a given age.

    SIMPLIFIED — does not include the actual annual-chart cast. Carries
    Muntha + Sahams that don't require a solar-return ephemeris call.
    """
    muntha: Muntha
    sahams: tuple[Saham, ...]


def compute_varshaphala(
    asc_sign: int, asc_lon: float,
    planet_lons: Mapping[str, float],
    age_years: float,
) -> VarshaphalaReport:
    """Aggregate Varshaphala progression for a chart at the given age."""
    return VarshaphalaReport(
        muntha=compute_muntha(asc_sign, age_years),
        sahams=compute_sahams(asc_sign, asc_lon, planet_lons),
    )


def format_varshaphala(r: VarshaphalaReport) -> str:
    """Render Varshaphala report as text."""
    lines = ["=== VARSHAPHALA / TAJIK PROGRESSION ==="]
    lines.append(
        f"  Muntha       : sign {r.muntha.sign} "
        f"(house {r.muntha.house_from_lagna} from Lagna)  "
        f"munthesha = {r.muntha.munthesha}"
    )
    lines.append(f"               focus: {r.muntha.domain_focus}")
    lines.append("  Sahams:")
    for s in r.sahams:
        flag = "OK " if s.is_well_placed else "!! "
        lines.append(
            f"    {flag}{s.name:<8}  sign {s.sign:>2} "
            f"(house {s.house_from_lagna:>2})  -- {s.domain}"
        )
    return "\n".join(lines)
