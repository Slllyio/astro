"""Functional Benefic/Malefic assignment per Lagna (BPHS Ch.3).

Phase 1 of the astrologer's-lens framework. Every downstream phase
(yoga detector, bhava judge, gochara engine, DKP modulation) needs to
know whether a planet is a *friend* or *enemy* for THIS Lagna — which
is a per-chart question, not a per-planet property.

## The four functional roles

Every visible planet (Sun..Saturn) receives at most one of these labels
per Lagna; Rahu/Ketu are intentionally excluded (no sign rulership →
no functional role).

* **Yogakaraka (YK)** — rules **one Kendra (4/7/10) AND one Trikona (5/9)**.
  Classical BPHS auspicious-by-default. Five canonical assignments fall out:
  Mars for Cancer + Leo; Venus for Capricorn + Aquarius; Saturn for
  Taurus + Libra. The Yogakaraka's dasha is the chart's best fortune
  window absent affliction.

* **Maraka (MK)** — rules **2H or 7H**. The two death-inflicting houses
  per BPHS Ch.34. Maraka-MD is the classical mortality window —
  caveat: Maraka is statistical not deterministic, and Vipareeta Raja
  yogas can invert it.

* **Badhakesh (BD)** — the *obstruction-causing* lord, whose house
  depends on Lagna modality:
  * **Movable** (Aries/Cancer/Libra/Capricorn — signs 1/4/7/10) → **11L**
  * **Fixed** (Taurus/Leo/Scorpio/Aquarius — signs 2/5/8/11) → **9L**
  * **Dual** (Gemini/Virgo/Sagittarius/Pisces — signs 3/6/9/12) → **7L**

* **Functional Benefic (FB) / Functional Malefic (FM)** — derived from
  the lordship pattern. FB requires a Trikona/Kendra lordship without
  dominant Dusthana (6/8/12) involvement. FM rules a Dusthana without
  redeeming Trikona. *Both labels can co-exist with Yogakaraka/Maraka.*

## Why this is the gate

Without functional roles, a downstream "Saturn is malefic" claim is
*meaningless*: Saturn is the Yogakaraka for Taurus and Libra Lagna but
a functional malefic for Cancer and Leo Lagna. Same planet, opposite
disposition. Every yoga, every dasha interpretation, every gochara
verdict in this framework reads off this table first.

Reference: BPHS Ch.3 (sign rulerships), Ch.34 (Marakas), and the
Phaladeepika tradition for Badhakesh per modality.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

# The 7 visible planets get functional-role assignment. Rahu/Ketu have
# no sign rulership in BPHS Ch.3 — they bypass this engine.
_VISIBLE_PLANETS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
)

# Sign(s) owned by each planet — BPHS Ch.3.
_PLANET_OWNS: Final[Mapping[str, tuple[int, ...]]] = {
    "Sun":     (5,),         # Leo
    "Moon":    (4,),         # Cancer
    "Mars":    (1, 8),       # Aries + Scorpio
    "Mercury": (3, 6),       # Gemini + Virgo
    "Jupiter": (9, 12),      # Sagittarius + Pisces
    "Venus":   (2, 7),       # Taurus + Libra
    "Saturn":  (10, 11),     # Capricorn + Aquarius
}

# House-classification sets (1-indexed).
_KENDRAS:   Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_TRIKONAS:  Final[frozenset[int]] = frozenset({1, 5, 9})
_DUSTHANAS: Final[frozenset[int]] = frozenset({6, 8, 12})
_MARAKAS:   Final[frozenset[int]] = frozenset({2, 7})

# Lagna modality → Badhakesh house number.
# Movable (signs 1/4/7/10) → 11; Fixed (2/5/8/11) → 9; Dual (3/6/9/12) → 7.
_MOVABLE_LAGNAS: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_FIXED_LAGNAS:   Final[frozenset[int]] = frozenset({2, 5, 8, 11})
_DUAL_LAGNAS:    Final[frozenset[int]] = frozenset({3, 6, 9, 12})


@dataclass(frozen=True)
class FunctionalRoles:
    """Immutable per-planet role bundle for one Lagna.

    A single planet can carry multiple labels at once — e.g. for Leo
    Lagna, Mars is *both* Yogakaraka (rules 4H + 9H) AND a Maraka in
    contexts where it activates the 4H lord aspect. The boolean flags
    are independent.
    """
    planet: str
    houses_ruled: tuple[int, ...]
    is_lagna_lord: bool
    is_yogakaraka: bool
    is_maraka: bool
    is_badhakesh: bool
    is_functional_benefic: bool
    is_functional_malefic: bool


def houses_ruled_by(planet: str, lagna_sign: int) -> tuple[int, ...]:
    """Houses (1..12) a planet rules from the given Lagna.

    Vectorised version of `((sign - asc_sign) % 12) + 1` over the
    planet's owned signs, sorted ascending. Rahu/Ketu yield () — they
    don't rule signs in our doctrine lock.
    """
    if planet not in _PLANET_OWNS:
        return ()
    owned = _PLANET_OWNS[planet]
    return tuple(sorted(((s - lagna_sign) % 12) + 1 for s in owned))


def badhakesh_house(lagna_sign: int) -> int:
    """Which house's lord is the Badhakesh for this Lagna?"""
    if lagna_sign in _MOVABLE_LAGNAS:
        return 11
    if lagna_sign in _FIXED_LAGNAS:
        return 9
    if lagna_sign in _DUAL_LAGNAS:
        return 7
    raise ValueError(f"lagna_sign must be 1..12, got {lagna_sign}")


def _classify_planet(planet: str, lagna_sign: int, badhaka_h: int) -> FunctionalRoles:
    """Compute the role bundle for one (planet, Lagna) pair."""
    houses = houses_ruled_by(planet, lagna_sign)
    houses_set = set(houses)

    is_lagna_lord = 1 in houses_set

    # YK: rules at least one Kendra AND at least one Trikona, with at
    # least one of those being a distinct non-Lagna house. 1H counts
    # as either set but doesn't suffice alone.
    kendra_hits = houses_set & _KENDRAS
    trikona_hits = houses_set & _TRIKONAS
    distinct_kendra = bool(kendra_hits - {1})
    distinct_trikona = bool(trikona_hits - {1})
    is_yogakaraka = distinct_kendra and distinct_trikona

    is_maraka = bool(houses_set & _MARAKAS)
    is_badhakesh = badhaka_h in houses_set

    dusthana_hits = houses_set & _DUSTHANAS
    # FB: rules trikona + no dusthana presence (5L, 9L, or YK without dusthana).
    is_fb = bool(distinct_trikona or is_yogakaraka) and not dusthana_hits
    # FM: rules a dusthana without a redeeming trikona.
    is_fm = bool(dusthana_hits) and not distinct_trikona

    return FunctionalRoles(
        planet=planet,
        houses_ruled=houses,
        is_lagna_lord=is_lagna_lord,
        is_yogakaraka=is_yogakaraka,
        is_maraka=is_maraka,
        is_badhakesh=is_badhakesh,
        is_functional_benefic=is_fb,
        is_functional_malefic=is_fm,
    )


def functional_roles(lagna_sign: int) -> dict[str, FunctionalRoles]:
    """Build the 7-planet functional-role table for one Lagna.

    Returns:
        Mapping planet-name → FunctionalRoles. Rahu/Ketu are
        intentionally absent.
    """
    if not 1 <= lagna_sign <= 12:
        raise ValueError(f"lagna_sign must be 1..12, got {lagna_sign}")
    badhaka_h = badhakesh_house(lagna_sign)
    return {p: _classify_planet(p, lagna_sign, badhaka_h) for p in _VISIBLE_PLANETS}


def yogakaraka_planets(lagna_sign: int) -> tuple[str, ...]:
    """The classical Yogakaraka set for a given Lagna — usually 0 or 1.

    For most Lagnas this returns () or a singleton; the five canonical
    Yogakaraka Lagnas (Cancer, Leo, Taurus, Libra, Capricorn, Aquarius)
    each have exactly one.
    """
    roles = functional_roles(lagna_sign)
    return tuple(p for p, r in roles.items() if r.is_yogakaraka)


def maraka_planets(lagna_sign: int) -> tuple[str, ...]:
    """Planets ruling 2H or 7H — the classical death-inflictors."""
    roles = functional_roles(lagna_sign)
    return tuple(p for p, r in roles.items() if r.is_maraka)


def badhakesh_planet(lagna_sign: int) -> str:
    """The single planet ruling the Badhaka house for this Lagna.

    Always returns exactly one planet name — the doctrine maps each
    Lagna to one Badhaka house, and exactly one planet rules that house.
    """
    bh = badhakesh_house(lagna_sign)
    roles = functional_roles(lagna_sign)
    for p, r in roles.items():
        if bh in r.houses_ruled:
            return p
    raise RuntimeError(f"no planet rules house {bh} for Lagna {lagna_sign}")
