"""M4 — Three-pillar bhava synthesis.

Raman's foundational method (*How to Judge a Horoscope I*) and BPHS
Adhyayas 11-22: every bhava is read as a fused verdict over THREE pillars:

    1. The bhava itself (sign + occupants)
    2. The bhava-LORD (where it sits, what it rules, its strength)
    3. The bhava-KARAKA (natural significator of the house)

Track A and Track B both compute these three values per bhava, but
emit them as separate atoms. This module fuses them into one
`ThreePillarBhava` per house and assembles a `ThreePillarReading` for
all 12.

Karaka table (natural significators per BPHS):
- 1H: Sun       7H:  Venus     (10H + 1H)
- 2H: Jupiter   8H:  Saturn
- 3H: Mars      9H:  Jupiter   (1H + 9H + 10H)
- 4H: Moon     10H:  Sun + Mercury + Jupiter + Saturn (primary: Sun)
- 5H: Jupiter  11H:  Jupiter   (gains)
- 6H: Mars     12H:  Saturn

Public surface
--------------
- ``build_three_pillar_reading(reading)`` -> ``ThreePillarReading``
- ``ThreePillarBhava`` — per-house fused verdict
"""

from __future__ import annotations

from typing import Any, Mapping

from pydantic import BaseModel, ConfigDict, Field

from app.integration.md_lord_dossier import (
    _conjunctions,
    _dignity_for,
    _houses_aspected,
    _SIGN_LORDS,
    _SIGN_NAMES,
    _track_b_functional_roles,
)


# Primary karaka per house. (For multi-karaka houses we pick the primary
# per BPHS — e.g. 10H has 4 karakas but Sun is primary.)
_BHAVA_KARAKAS: dict[int, str] = {
    1: "Sun",      # vitality, body
    2: "Jupiter",  # wealth, family, speech
    3: "Mars",     # courage, siblings, effort
    4: "Moon",     # mother, home, comforts
    5: "Jupiter", # children, intellect, poorvapunya
    6: "Mars",     # enemies, debt, illness
    7: "Venus",    # spouse, partnerships
    8: "Saturn",   # longevity, occult, inheritance
    9: "Jupiter", # dharma, father, fortune
    10: "Sun",     # career, status, action
    11: "Jupiter", # gains, elder siblings, fulfillment
    12: "Saturn",  # losses, foreign, moksha
}

# Friendly + reasonable enemy table for dignity scoring.
_DIGNITY_SCORE: dict[str, int] = {
    "exalted": 2, "own": 2, "friendly": 1,
    "neutral": 0, "debilitated": -2,
}

_FUNCTIONAL_SCORE: dict[str, int] = {
    "yogakaraka": 2, "lagna_lord": 1, "benefic": 1,
    "neutral": 0, "maraka": -1, "badhakesh": -2, "malefic": -1,
}


class ThreePillarBhava(BaseModel):
    """One house's fused three-pillar verdict."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    bhava: int = Field(ge=1, le=12)
    bhava_sign: int = Field(ge=1, le=12)
    bhava_sign_name: str

    # Pillar 1: house occupants + aspects to house
    occupants: tuple[str, ...]
    planets_aspecting_house: tuple[str, ...]

    # Pillar 2: bhava lord
    lord_planet: str
    lord_house: int = Field(ge=1, le=12)
    lord_sign_name: str
    lord_dignity: str
    lord_functional_role: str
    lord_is_retrograde: bool

    # Pillar 3: karaka
    karaka_planet: str
    karaka_house: int = Field(ge=1, le=12)
    karaka_sign_name: str
    karaka_dignity: str

    # Synthesis
    composite_score: float = Field(ge=-6.0, le=6.0)
    composite_label: str  # very_strong / strong / mixed / weak / afflicted
    synthesis_lines: tuple[str, ...]


class ThreePillarReading(BaseModel):
    """All 12 houses fused via the three-pillar method."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    lagna_sign: int = Field(ge=1, le=12)
    lagna_sign_name: str
    per_bhava: dict[int, ThreePillarBhava]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _label_for_score(score: float) -> str:
    if score >= 4: return "very_strong"
    if score >= 2: return "strong"
    if score >= -1: return "mixed"
    if score >= -3: return "weak"
    return "afflicted"


def _bhava_sign(lagna_sign: int, bhava: int) -> int:
    """Sign of the Nth house given lagna sign (whole-sign system)."""
    return ((lagna_sign - 1 + bhava - 1) % 12) + 1


def _occupants_of_house(planets: dict, house: int) -> tuple[str, ...]:
    """All planets whose .house == house."""
    out: list[str] = []
    for name, body in planets.items():
        if isinstance(body, dict) and int(body.get("house", 0)) == house:
            out.append(name)
    return tuple(sorted(out))


def _planets_aspecting_house(planets: dict, target_house: int) -> tuple[str, ...]:
    """Planets whose Parashari aspects reach target_house."""
    out: list[str] = []
    for name, body in planets.items():
        if not isinstance(body, dict):
            continue
        planet_house = int(body.get("house", 0))
        if planet_house == 0:
            continue
        aspects = _houses_aspected(name, planet_house)
        if target_house in aspects:
            out.append(name)
    return tuple(sorted(out))


def _compose_synthesis_lines(
    bhava: int, bhava_sign_name: str,
    occupants: tuple[str, ...], aspecting: tuple[str, ...],
    lord_planet: str, lord_house: int, lord_sign_name: str,
    lord_dignity: str, lord_functional_role: str,
    karaka_planet: str, karaka_house: int, karaka_sign_name: str,
    karaka_dignity: str,
) -> tuple[str, ...]:
    """Build 3 readable lines: house pillar, lord pillar, karaka pillar."""
    # Line 1: house pillar
    if occupants:
        occ_str = ", ".join(occupants)
        l1 = f"H{bhava} {bhava_sign_name}: occupied by {occ_str}"
    else:
        l1 = f"H{bhava} {bhava_sign_name}: empty"
    if aspecting:
        asp = ", ".join(p for p in aspecting if p not in occupants)
        if asp:
            l1 += f"; aspected by {asp}"

    # Line 2: lord pillar
    role_str = f" [{lord_functional_role}]" if lord_functional_role != "neutral" else ""
    dig_str = f" ({lord_dignity})" if lord_dignity not in ("neutral",) else ""
    l2 = (
        f"LORD {lord_planet} in {lord_house}H {lord_sign_name}{dig_str}{role_str}"
    )

    # Line 3: karaka pillar
    same = " (same planet)" if karaka_planet == lord_planet else ""
    k_dig_str = f" ({karaka_dignity})" if karaka_dignity not in ("neutral",) else ""
    l3 = f"KARAKA {karaka_planet}{same} in {karaka_house}H {karaka_sign_name}{k_dig_str}"

    return (l1, l2, l3)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_three_pillar_reading(
    reading: Mapping[str, Any],
) -> ThreePillarReading:
    """Compose a 12-house three-pillar reading for the chart."""
    chart = reading.get("chart") or {}
    planets = chart.get("planets") or {}
    asc_sign = int((chart.get("cusps") or {}).get("sign", 1))

    roles = {}
    try:
        roles = _track_b_functional_roles(asc_sign)
    except Exception:
        pass

    per_bhava: dict[int, ThreePillarBhava] = {}

    for bhava in range(1, 13):
        bhava_sign = _bhava_sign(asc_sign, bhava)
        bhava_sign_name = _SIGN_NAMES[bhava_sign]

        # Pillar 1: occupants + aspects
        occupants = _occupants_of_house(planets, bhava)
        aspecting = _planets_aspecting_house(planets, bhava)

        # Pillar 2: bhava lord
        lord_planet = _SIGN_LORDS[bhava_sign]
        lord_body = planets.get(lord_planet) or {}
        lord_house = int(lord_body.get("house", 0))
        lord_sign = int(lord_body.get("sign", 0))
        lord_sign_name = _SIGN_NAMES[lord_sign] if 1 <= lord_sign <= 12 else "?"
        lord_dignity = _dignity_for(lord_planet, lord_sign) if lord_sign else "neutral"
        lord_is_retrograde = bool(lord_body.get("is_retrograde", False))

        # Functional role of lord per current lagna
        lord_func = "neutral"
        lord_role_obj = roles.get(lord_planet)
        if lord_role_obj is not None:
            if getattr(lord_role_obj, "is_yogakaraka", False):
                lord_func = "yogakaraka"
            elif getattr(lord_role_obj, "is_badhakesh", False):
                lord_func = "badhakesh"
            elif getattr(lord_role_obj, "is_maraka", False):
                lord_func = "maraka"
            elif getattr(lord_role_obj, "is_functional_benefic", False):
                lord_func = "benefic"
            elif getattr(lord_role_obj, "is_functional_malefic", False):
                lord_func = "malefic"
            elif getattr(lord_role_obj, "is_lagna_lord", False):
                lord_func = "lagna_lord"

        # Pillar 3: karaka
        karaka_planet = _BHAVA_KARAKAS[bhava]
        karaka_body = planets.get(karaka_planet) or {}
        karaka_house = int(karaka_body.get("house", 0))
        karaka_sign = int(karaka_body.get("sign", 0))
        karaka_sign_name = _SIGN_NAMES[karaka_sign] if 1 <= karaka_sign <= 12 else "?"
        karaka_dignity = (
            _dignity_for(karaka_planet, karaka_sign) if karaka_sign else "neutral"
        )

        # Composite score: sum of 3 pillar scores in [-6, +6]
        score = 0.0
        # Pillar 1: occupant impact — benefics +, malefics −
        benefics = {"Jupiter", "Venus", "Mercury", "Moon"}
        malefics = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
        for occ in occupants:
            if occ in benefics:
                score += 0.5
            elif occ in malefics:
                score -= 0.5
        # Pillar 2: lord dignity + functional role
        score += _DIGNITY_SCORE.get(lord_dignity, 0)
        score += _FUNCTIONAL_SCORE.get(lord_func, 0)
        # Pillar 3: karaka dignity
        score += _DIGNITY_SCORE.get(karaka_dignity, 0) * 0.5
        # Clamp
        score = max(-6.0, min(6.0, score))

        label = _label_for_score(score)
        lines = _compose_synthesis_lines(
            bhava, bhava_sign_name, occupants, aspecting,
            lord_planet, lord_house, lord_sign_name,
            lord_dignity, lord_func,
            karaka_planet, karaka_house, karaka_sign_name, karaka_dignity,
        )

        per_bhava[bhava] = ThreePillarBhava(
            bhava=bhava,
            bhava_sign=bhava_sign,
            bhava_sign_name=bhava_sign_name,
            occupants=occupants,
            planets_aspecting_house=aspecting,
            lord_planet=lord_planet,
            lord_house=lord_house,
            lord_sign_name=lord_sign_name,
            lord_dignity=lord_dignity,
            lord_functional_role=lord_func,
            lord_is_retrograde=lord_is_retrograde,
            karaka_planet=karaka_planet,
            karaka_house=karaka_house,
            karaka_sign_name=karaka_sign_name,
            karaka_dignity=karaka_dignity,
            composite_score=score,
            composite_label=label,
            synthesis_lines=lines,
        )

    return ThreePillarReading(
        lagna_sign=asc_sign,
        lagna_sign_name=_SIGN_NAMES[asc_sign],
        per_bhava=per_bhava,
    )
