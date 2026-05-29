"""Gochara (transit) engine with double-transit detection — Phase 7.

The temporal-trigger layer. Phase 6 produces the static bhava promise;
Phase 7 says *when* that promise activates. Together they form the
prediction stack: promise + activation + trigger.

## What "double transit" means

BPHS Ch.31 — Saturn and Jupiter together carry the largest temporal
weight (because they're slowest and stay in a sign longest). A bhava's
affairs activate when:

1. Saturn AND Jupiter both transit the **bhava sign** itself, OR
2. Saturn AND Jupiter both transit the **bhava lord's sign**, OR
3. Saturn AND Jupiter both transit the **bhava karaka's sign**.

"Both" need not be exact same moment — within a year of each other
counts in the classical reading. Here we report the discrete state:
both currently present, partially present, neither.

## Sthira Vedha — transit cancellation from Moon

BPHS Ch.31 gives the *Sthira Vedha* (fixed obstruction) table per
planet. Saturn's transits from Moon are cancelled if Sun is in the
Vedha (3rd from the target house). The classical table is:

| Transit Planet | Result-house from Moon | Vedha planet | Vedha house |
|----------------|------------------------|--------------|-------------|
| Sun            | 1, 6, 11               | Saturn       | 4, 12, 5    |
| Moon           | (multiple per BPHS)    | (varies)     | (varies)    |
| Mars           | 3, 6, 11               | Mercury      | 12, 9, 5    |
| Mercury        | 2, 4, 6, 8, 10, 11     | Saturn       | (varies)    |
| Jupiter        | 2, 5, 7, 9, 11         | Venus        | 12, 4, 3, 10, 8 |
| Venus          | 1, 2, 3, 4, 5, 8, 9, 11, 12 | Rahu/Ketu | (varies)    |
| Saturn         | 3, 6, 11               | Mars         | 12, 9, 5    |

We implement the most-used Saturn-from-Moon variant for Sade-Sati
detection.

## Output

``GocharaVerdict`` carries: for each bhava, the active-transit set,
the double-transit flag, and Sthira-Vedha cancellations.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.core.bhava_judge import _BHAVA_KARAKAS, _NATURAL_BENEFICS, _NATURAL_MALEFICS
from app.core.chart_model import Chart
from app.core.drishti_argala import aspects_from_planet
from app.core.functional_roles import functional_roles


@dataclass(frozen=True)
class TransitState:
    """Per-bhava transit state at a target moment."""
    bhava: int
    transit_planets_in_bhava: tuple[str, ...]
    transit_planets_aspecting_bhava: tuple[str, ...]
    saturn_present: bool          # in bhava OR aspecting
    jupiter_present: bool          # in bhava OR aspecting
    rahu_present: bool
    is_double_transit_bhava: bool   # Saturn + Jupiter both touching this bhava
    is_double_transit_lord: bool    # Saturn + Jupiter both touching lord's sign
    is_double_transit_karaka: bool  # Saturn + Jupiter both touching karaka sign
    sthira_vedha_cancelled: bool
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class GocharaVerdict:
    """Whole-chart gochara verdict at one target_jd."""
    per_bhava: Mapping[int, TransitState]
    active_double_transit_bhavas: tuple[int, ...]
    sade_sati_active: bool          # Saturn in 12/1/2 from natal Moon
    saturn_vedha_cancelled: bool    # Saturn's transit benefit cancelled (chart-level)
    saturn_from_moon: int           # Saturn's current position from natal Moon


def _transit_sign_to_natal_house(transit_sign: int, asc_sign: int) -> int:
    """Whole-sign natal house for a transiting planet.

    Validates inputs are 1..12 — silently accepting 0 or 13 would yield
    a phantom house number (the audit caught this exact fragility).
    """
    if not (1 <= transit_sign <= 12 and 1 <= asc_sign <= 12):
        raise ValueError(
            f"transit_sign and asc_sign must both be 1..12; "
            f"got transit_sign={transit_sign}, asc_sign={asc_sign}"
        )
    return ((transit_sign - asc_sign) % 12) + 1


def _planet_touches_house(
    planet: str, planet_transit_house: int | None, target_house: int,
) -> bool:
    """A planet 'touches' a house if it sits IN it OR aspects it.

    Returns False when ``planet_transit_house`` is None (planet missing
    from the transit dict). Prior to the audit fix this silently fell
    back to house 0, generating phantom aspects via ``_step(0, …)``.
    """
    if planet_transit_house is None:
        return False
    if planet_transit_house == target_house:
        return True
    aspects = aspects_from_planet(planet, planet_transit_house)
    return target_house in aspects


def _bhava_for_planet_in_natal(
    planet: str, transit_signs: Mapping[str, int], asc_sign: int,
) -> int | None:
    """Which natal house does a transiting planet currently occupy?"""
    s = transit_signs.get(planet)
    if s is None:
        return None
    return _transit_sign_to_natal_house(s, asc_sign)


def _check_sade_sati(transit_signs: Mapping[str, int], moon_sign: int) -> bool:
    """Saturn in 12th, 1st, or 2nd from natal Moon → Sade Sati active."""
    sat_sign = transit_signs.get("Saturn")
    if sat_sign is None:
        return False
    distance = ((sat_sign - moon_sign) % 12) + 1
    return distance in {12, 1, 2}


def _check_sthira_vedha_saturn_chart_level(
    transit_signs: Mapping[str, int], moon_sign: int,
) -> tuple[bool, int]:
    """Chart-level Saturn vedha (BPHS Ch.31).

    Saturn's auspicious results in 3rd / 6th / 11th from Moon are
    cancelled if Mars is in 12th / 9th / 5th from Moon respectively.

    Returns:
        (cancelled: bool, saturn_from_moon: int)
    """
    sat_sign = transit_signs.get("Saturn")
    if sat_sign is None:
        return False, 0
    sat_from_moon = ((sat_sign - moon_sign) % 12) + 1
    if sat_from_moon not in {3, 6, 11}:
        return False, sat_from_moon
    mars_sign = transit_signs.get("Mars")
    if mars_sign is None:
        return False, sat_from_moon
    mars_from_moon = ((mars_sign - moon_sign) % 12) + 1
    vedha_pairs = {3: 12, 6: 9, 11: 5}
    return mars_from_moon == vedha_pairs[sat_from_moon], sat_from_moon


def compute_gochara(
    chart: Chart, transit_signs: Mapping[str, int],
) -> GocharaVerdict:
    """Build the gochara verdict for one chart at one target moment.

    Args:
        chart: The natal Chart.
        transit_signs: planet → current transit sign (1..12).
    """
    moon_sign = chart.sign_of("Moon") or 1
    asc_sign = chart.asc_sign

    # Transit houses (whole-sign from Lagna)
    transit_houses: dict[str, int] = {}
    for p, ts in transit_signs.items():
        transit_houses[p] = _transit_sign_to_natal_house(ts, asc_sign)

    roles = functional_roles(asc_sign)

    per_bhava: dict[int, TransitState] = {}
    for b in range(1, 13):
        # Planets sitting in the bhava
        in_bhava = tuple(sorted(p for p, h in transit_houses.items() if h == b))
        # Planets aspecting the bhava (excluding occupants from aspect list)
        aspecting = []
        for p, h in transit_houses.items():
            if h == b:
                continue
            if b in aspects_from_planet(p, h):
                aspecting.append(p)
        aspecting_t = tuple(sorted(aspecting))

        saturn_present = (
            "Saturn" in in_bhava or "Saturn" in aspecting_t
        )
        jupiter_present = (
            "Jupiter" in in_bhava or "Jupiter" in aspecting_t
        )
        rahu_present = "Rahu" in in_bhava or "Rahu" in aspecting_t

        # Double-transit checks: bhava itself, lord's sign, karaka's sign.
        # For "bhava sign": did Saturn AND Jupiter both touch this bhava?
        dt_bhava = saturn_present and jupiter_present

        # Lord — use ``is not None`` (not truthy) because house 0 would
        # be falsy, and silent fallback to .get(planet, 0) used to inject
        # phantom positions for missing transit planets. The audit fix is
        # to pass None and short-circuit inside _planet_touches_house.
        lord = next(
            (p for p, r in roles.items() if b in r.houses_ruled), None,
        )
        lord_natal_sign = chart.sign_of(lord) if lord else None
        lord_natal_house: int | None = None
        if lord_natal_sign is not None:
            lord_natal_house = _transit_sign_to_natal_house(
                lord_natal_sign, asc_sign,
            )
        dt_lord = False
        if lord_natal_house is not None:
            sat_touches_lord = _planet_touches_house(
                "Saturn", transit_houses.get("Saturn"), lord_natal_house,
            )
            jup_touches_lord = _planet_touches_house(
                "Jupiter", transit_houses.get("Jupiter"), lord_natal_house,
            )
            dt_lord = sat_touches_lord and jup_touches_lord

        # Karaka (first natural karaka for this bhava)
        karakas = _BHAVA_KARAKAS.get(b, ())
        dt_karaka = False
        for k in karakas:
            k_natal_sign = chart.sign_of(k)
            if k_natal_sign is None:
                continue
            k_natal_house = _transit_sign_to_natal_house(
                k_natal_sign, asc_sign,
            )
            sat_touches_k = _planet_touches_house(
                "Saturn", transit_houses.get("Saturn"), k_natal_house,
            )
            jup_touches_k = _planet_touches_house(
                "Jupiter", transit_houses.get("Jupiter"), k_natal_house,
            )
            if sat_touches_k and jup_touches_k:
                dt_karaka = True
                break

        per_bhava[b] = TransitState(
            bhava=b,
            transit_planets_in_bhava=in_bhava,
            transit_planets_aspecting_bhava=aspecting_t,
            saturn_present=saturn_present,
            jupiter_present=jupiter_present,
            rahu_present=rahu_present,
            is_double_transit_bhava=dt_bhava,
            is_double_transit_lord=dt_lord,
            is_double_transit_karaka=dt_karaka,
            sthira_vedha_cancelled=False,  # chart-level — see verdict
            notes=(),
        )

    active_dt = tuple(
        b for b, ts in per_bhava.items()
        if (ts.is_double_transit_bhava or ts.is_double_transit_lord
            or ts.is_double_transit_karaka)
    )
    vedha_cancelled, sat_from_moon = _check_sthira_vedha_saturn_chart_level(
        transit_signs, moon_sign,
    )

    return GocharaVerdict(
        per_bhava=per_bhava,
        active_double_transit_bhavas=active_dt,
        sade_sati_active=_check_sade_sati(transit_signs, moon_sign),
        saturn_vedha_cancelled=vedha_cancelled,
        saturn_from_moon=sat_from_moon,
    )


def is_triggered(verdict: GocharaVerdict, bhava: int) -> bool:
    """Convenience: is the bhava under an active double-transit?

    Note: chart-level ``saturn_vedha_cancelled`` is intentionally NOT
    applied here — Phase 6 / Phase 9 can decide whether to discount the
    triggers when Saturn's auspicious vedha is dead.
    """
    ts = verdict.per_bhava.get(bhava)
    if ts is None:
        return False
    return (
        ts.is_double_transit_bhava
        or ts.is_double_transit_lord
        or ts.is_double_transit_karaka
    )
