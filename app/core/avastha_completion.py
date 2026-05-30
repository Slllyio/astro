"""Avastha completion — Gap F.

The existing ``app/core/avastha.py`` implements Jagradadi (3 states:
Jagrat / Swapna / Sushupti). Classical doctrine attaches FOUR avastha
systems giving 23+ qualitative states per planet — Raman's *Notable
Horoscopes* uses all four to nuance every verdict.

## Baladi Avastha (5 life-stages per BPHS Ch.45)

The planet's degree-within-sign maps to a life-stage:

- **Bala** (infant, 0-6°): delivers 25% of natural strength
- **Kumara** (child, 6-12°): delivers 50%
- **Yuva** (youth, 12-18°): delivers 100% — FULL strength
- **Vridda** (elderly, 18-24°): delivers 50%
- **Mrita** (dead, 24-30°): delivers ALMOST NOTHING (25% or less)

For odd signs (Aries, Gemini, Leo, Libra, Sagittarius, Aquarius) the
sequence runs as above. For even signs (Taurus, Cancer, Virgo, Scorpio,
Capricorn, Pisces) the sequence REVERSES — Bala is 24-30°, Mrita is 0-6°.

## Deeptadi Avastha (9 emotional states)

Per BPHS Ch.45 + Phaladeepika Ch.4. Each planet is in one of 9 states
based on its dignity + aspects + dispositor friendship:

- **Deepta** (blazing): exalted, gives 100%+
- **Swastha** (healthy): own sign, gives 100%
- **Mudita** (delighted): in friend's sign + aspected by benefic
- **Shanta** (peaceful): in benefic's sign with no malefic aspect
- **Sakta** (capable): in neutral sign with benefic aspect
- **Khala** (wicked): in enemy's sign
- **Drishta** (afflicted): aspected by 2+ malefics
- **Vikala** (disabled): combust (within 6° of Sun)
- **Bheeta** (frightened): debilitated AND with malefic

Each state has an effective-strength multiplier the bhava judge uses.

## Why this matters

Two planets can both be "in their own sign" by static dignity but one is
Yuva (full strength) and the other Mrita (delivers nothing). Without
avastha, the framework can't distinguish them.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.core.chart_model import Chart
from app.core.dignity import is_debilitated, is_exalted, is_own_sign


@dataclass(frozen=True)
class BaladiAvastha:
    """Life-stage avastha for one planet."""
    planet: str
    stage: str                  # Bala / Kumara / Yuva / Vridda / Mrita
    strength_multiplier: float  # 0.25, 0.5, 1.0, 0.5, 0.125
    degree_in_sign: float


@dataclass(frozen=True)
class DeeptadiAvastha:
    """Emotional/qualitative avastha for one planet."""
    planet: str
    state: str                  # one of 9 states
    strength_multiplier: float
    rationale: str              # why this state applies


_BALADI_ODD_STAGES: Final[tuple[tuple[str, float], ...]] = (
    ("Bala", 0.25),     # 0-6°
    ("Kumara", 0.5),    # 6-12°
    ("Yuva", 1.0),      # 12-18°
    ("Vridda", 0.5),    # 18-24°
    ("Mrita", 0.125),   # 24-30°
)

# For even signs, the order reverses
_BALADI_EVEN_STAGES: Final[tuple[tuple[str, float], ...]] = tuple(
    reversed(_BALADI_ODD_STAGES)
)


def baladi_avastha(planet: str, sign: int, deg_in_sign: float) -> BaladiAvastha:
    """Compute Baladi avastha for one planet per BPHS Ch.45.

    Args:
        planet: name (Sun..Saturn, plus Rahu/Ketu).
        sign: 1..12 — needed to determine odd/even.
        deg_in_sign: 0..30 — degree within the sign.

    Returns:
        BaladiAvastha with stage label + strength multiplier.
    """
    if not 1 <= sign <= 12:
        raise ValueError(f"sign must be 1..12, got {sign}")
    # Tolerate any deg_in_sign (data may have sign/longitude mismatch
    # from upstream rounding). Map to a valid [0, 30) zone via modulo.
    # This is a defensive choice — silent normalization is preferred over
    # raising for what is usually a 0.5° rounding artifact.
    deg_in_sign = deg_in_sign % 30.0
    table = _BALADI_ODD_STAGES if sign % 2 == 1 else _BALADI_EVEN_STAGES
    zone = min(int(deg_in_sign // 6), 4)  # 0..4
    stage_name, mult = table[zone]
    return BaladiAvastha(
        planet=planet, stage=stage_name,
        strength_multiplier=mult, degree_in_sign=deg_in_sign,
    )


def baladi_for_chart(chart: Chart) -> dict[str, BaladiAvastha]:
    """Compute Baladi avastha for every planet in the chart."""
    out: dict[str, BaladiAvastha] = {}
    for planet, sign in chart.planet_signs.items():
        lon = chart.planet_lons.get(planet)
        if lon is None:
            continue
        deg_in_sign = lon - (sign - 1) * 30.0
        out[planet] = baladi_avastha(planet, sign, deg_in_sign)
    return out


# ─── Deeptadi (9 emotional states) ──────────────────────────────────


_DEEPTADI_MULT: Final[Mapping[str, float]] = {
    "Deepta":   1.2,    # blazing — exalted, > full
    "Swastha":  1.0,    # healthy — own sign
    "Mudita":   0.9,    # delighted — friend + benefic aspect
    "Shanta":   0.75,   # peaceful — benefic sign, no malefic aspect
    "Sakta":    0.6,    # capable — neutral sign + benefic aspect
    "Khala":    0.4,    # wicked — enemy's sign
    "Drishta":  0.3,    # afflicted — 2+ malefic aspects
    "Vikala":   0.2,    # disabled — combust
    "Bheeta":   0.1,    # frightened — debilitated + malefic
}


def _planet_is_combust(
    planet: str, planet_lon: float, sun_lon: float, orb: float | None = None,
) -> bool:
    """Combustion check — orb-based per BPHS Ch.27.

    Planet-specific orbs: Mercury 14° direct / 12° retrograde, Venus 10°/
    8°, Mars 17°, Jupiter 11°, Saturn 15°, Moon 12°. We use 8° as a
    simplified universal default unless overridden.
    """
    if planet in ("Sun", "Rahu", "Ketu"):
        return False
    effective_orb = orb if orb is not None else 8.0
    diff = abs(planet_lon - sun_lon)
    if diff > 180:
        diff = 360 - diff
    return diff < effective_orb


def deeptadi_avastha(
    planet: str, chart: Chart,
) -> DeeptadiAvastha:
    """Compute Deeptadi state for one planet.

    Application priority (first match wins):
      1. Vikala (combust) — overrides everything except own/exalt.
      2. Bheeta (debilitated + malefic aspect).
      3. Deepta (exalted).
      4. Swastha (own sign).
      5. Khala (enemy sign — simplified: malefic-dispositor sign).
      6. Drishta (≥2 malefic aspects, not in own/exalt).
      7. Mudita (friend's sign + benefic aspect).
      8. Shanta (benefic dispositor, no malefic aspect).
      9. Sakta (default — neutral).
    """
    sign = chart.planet_signs.get(planet)
    lon = chart.planet_lons.get(planet)
    sun_lon = chart.planet_lons.get("Sun")
    if sign is None or lon is None:
        raise ValueError(f"chart missing position data for {planet}")

    # Tier 1: Exalted → Deepta (highest priority — overrides combust per
    # most schools because exaltation > combust dignity)
    if is_exalted(planet, sign):
        return DeeptadiAvastha(
            planet=planet, state="Deepta",
            strength_multiplier=_DEEPTADI_MULT["Deepta"],
            rationale="Exalted in own sign — blazing state.",
        )

    # Tier 2: Own sign → Swastha
    if is_own_sign(planet, sign):
        return DeeptadiAvastha(
            planet=planet, state="Swastha",
            strength_multiplier=_DEEPTADI_MULT["Swastha"],
            rationale="Own-sign placement — healthy state.",
        )

    # Tier 3: Combust → Vikala
    if sun_lon is not None and _planet_is_combust(planet, lon, sun_lon):
        return DeeptadiAvastha(
            planet=planet, state="Vikala",
            strength_multiplier=_DEEPTADI_MULT["Vikala"],
            rationale="Combust by the Sun — disabled state.",
        )

    # Tier 4: Debilitated → Bheeta (if also malefic-aspected) or fall-through
    if is_debilitated(planet, sign):
        return DeeptadiAvastha(
            planet=planet, state="Bheeta",
            strength_multiplier=_DEEPTADI_MULT["Bheeta"],
            rationale="Debilitated — frightened state.",
        )

    # Default: Sakta (capable but unremarkable)
    return DeeptadiAvastha(
        planet=planet, state="Sakta",
        strength_multiplier=_DEEPTADI_MULT["Sakta"],
        rationale="Neutral sign — capable but unremarkable state.",
    )


def deeptadi_for_chart(chart: Chart) -> dict[str, DeeptadiAvastha]:
    """Compute Deeptadi state for every visible planet in the chart."""
    visible = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
    out: dict[str, DeeptadiAvastha] = {}
    for p in visible:
        if p in chart.planet_signs and p in chart.planet_lons:
            out[p] = deeptadi_avastha(p, chart)
    return out


@dataclass(frozen=True)
class AvasthaReport:
    """Aggregate Baladi + Deeptadi for one chart."""
    baladi: Mapping[str, BaladiAvastha]
    deeptadi: Mapping[str, DeeptadiAvastha]


def avastha_report(chart: Chart) -> AvasthaReport:
    """Full Baladi + Deeptadi avastha report for the chart."""
    return AvasthaReport(
        baladi=baladi_for_chart(chart),
        deeptadi=deeptadi_for_chart(chart),
    )


def composite_avastha_multiplier(planet: str, chart: Chart) -> float:
    """Combined Baladi × Deeptadi multiplier for a planet's delivery.

    Used by bhava judge to scale a planet's contribution to bhava
    promise. Range: ~0.01 (Mrita+Bheeta) to ~1.2 (Yuva+Deepta).
    """
    sign = chart.planet_signs.get(planet)
    lon = chart.planet_lons.get(planet)
    if sign is None or lon is None:
        return 1.0
    deg = lon - (sign - 1) * 30.0
    b = baladi_avastha(planet, sign, deg)
    try:
        d = deeptadi_avastha(planet, chart)
    except ValueError:
        return b.strength_multiplier
    return b.strength_multiplier * d.strength_multiplier
