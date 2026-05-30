"""Tier-0 primitive: Deeptadi 9-state classification per planet.

This is the third Avastha lineage in the classical scheme, distinct
from the Baladi (degree-based, 5 states) and Jagradadi (drishti-based,
3 states) lineages already covered by ``app.core.avastha``. The
Deeptadi 9 states partition every planet into one of:

| # | State        | Direction | Trigger                                       |
|---|--------------|-----------|-----------------------------------------------|
| 1 | Deepta       | positive  | Planet in its exaltation sign.                |
| 2 | Shanta       | positive  | Planet in its Moolatrikona range.             |
| 3 | Susvastha    | positive  | Planet in its own sign (sva-rashi, non-MT).   |
| 4 | Pramudita    | positive  | Planet in a friend's sign.                    |
| 5 | Dukhita      | negative  | Planet in an enemy's sign.                    |
| 6 | Sudukhita    | negative  | Planet in its debilitation sign.              |
| 7 | Kshobita     | negative  | Planet within 1° of another non-luminary.     |
| 8 | Atra         | negative  | Planet combust by the Sun.                    |
| 9 | Khala        | negative  | Planet afflicted by a malefic aspect (default).|

The Deeptadi state of a planet is read once — that is, the priority
order above is followed strictly. Combust-with-the-Sun (Atra) and
Planetary-War (Kshobita) take precedence over the sign-based states
because both are overriding afflictions: the planet's intrinsic dignity
matters less when its light or motion is disrupted. In the rare case
where both apply, Kshobita wins (planetary war is the stronger
disturbance — the planet's *motion* itself is in conflict, not merely
its visibility).

Sources
=======

The Deeptadi catalog is reproduced in BPHS Ch.45 and Phaladeepika
Ch.16. The 9-state form here is the most widely cited modern reading
(PVR Narasimha Rao, Sanjay Rath); some early modern commentators count
only 7 or 8 states by collapsing Khala into Atra or Pramudita into
Susvastha. We keep all 9 distinct.

Public API
==========

    compute_deeptadi_avasthas(d1_chart) -> dict[str, Finding]

Usage
=====

    >>> from app.core.ephemeris_engine import calculate_all_charts
    >>> chart = calculate_all_charts(1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)
    >>> from app.reading.computations.avasthas import compute_deeptadi_avasthas
    >>> states = compute_deeptadi_avasthas(chart["d1"])
    >>> states["Jupiter"].verdict
    'Jupiter is ... ...'
"""
from __future__ import annotations

import logging
from typing import Final, Literal

from app.core.dignity import (
    DEBILITATION,
    EXALTATION,
    NAISARGIKA_FRIENDSHIP,
    OWN_SIGNS,
    SIGN_RULERS,
    is_moolatrikona,
)
from app.core.planet_state import angular_separation, is_combust
from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# 3-vote envelope.
_PRIMITIVE_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


DeeptadiState = Literal[
    "Deepta", "Susvastha", "Pramudita", "Shanta",
    "Dukhita", "Sudukhita", "Kshobita", "Atra", "Khala",
]


# Classical valence per CLAUDE.md ("benefics: Jupiter, Venus, Mercury,
# Moon; malefics: Sun, Mars, Saturn, Rahu, Ketu").
_MALEFICS: Final[frozenset[str]] = frozenset(
    {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
)

# Planets ineligible for planetary war (Graha Yuddha) per D-13 / BPHS
# Vol.I Ch.27 v.13: luminaries do not engage; nodes are non-physical
# and excluded by convention.
_GRAHA_YUDDHA_EXCLUDED: Final[frozenset[str]] = frozenset(
    {"Sun", "Moon", "Rahu", "Ketu"}
)

# Planetary-war orb in degrees (D-13 lock).
_PLANETARY_WAR_ORB: Final[float] = 1.0


# Direction polarity per state.
_POSITIVE_STATES: Final[frozenset[str]] = frozenset(
    {"Deepta", "Susvastha", "Pramudita", "Shanta"}
)
_NEGATIVE_STATES: Final[frozenset[str]] = frozenset(
    {"Dukhita", "Sudukhita", "Kshobita", "Atra", "Khala"}
)


# Human-readable reasons for each state.
_STATE_REASONS: Final[dict[DeeptadiState, str]] = {
    "Deepta":    "exalted",
    "Shanta":    "in Moolatrikona",
    "Susvastha": "in own sign",
    "Pramudita": "in friend's sign",
    "Dukhita":   "in enemy's sign",
    "Sudukhita": "debilitated",
    "Kshobita":  "in planetary war",
    "Atra":      "combust",
    "Khala":     "afflicted by malefic aspect",
}


def _is_friend(planet: str, ruler: str) -> bool:
    """True if ``planet`` views ``ruler`` as a naisargika friend."""
    if planet not in NAISARGIKA_FRIENDSHIP:
        return False
    return ruler in NAISARGIKA_FRIENDSHIP[planet]["friends"]


def _is_enemy(planet: str, ruler: str) -> bool:
    """True if ``planet`` views ``ruler`` as a naisargika enemy."""
    if planet not in NAISARGIKA_FRIENDSHIP:
        return False
    return ruler in NAISARGIKA_FRIENDSHIP[planet]["enemies"]


def _in_planetary_war(
    planet: str, d1_chart: dict
) -> tuple[bool, str | None]:
    """Return (is_in_war, opponent_name).

    Per D-13: planets within 1° of each other engage in war, excluding
    the two luminaries and (by convention) the nodes. Sun's involvement
    is reserved for combustion (Atra) rather than war (Kshobita).
    """
    if planet in _GRAHA_YUDDHA_EXCLUDED:
        return False, None
    try:
        my_lon = float(d1_chart[planet]["longitude"])
    except (KeyError, TypeError, ValueError):
        return False, None

    for other, entry in d1_chart.items():
        if other == planet or other in _GRAHA_YUDDHA_EXCLUDED:
            continue
        try:
            other_lon = float(entry["longitude"])
        except (KeyError, TypeError, ValueError):
            continue
        if angular_separation(my_lon, other_lon) <= _PLANETARY_WAR_ORB:
            return True, other
    return False, None


def _is_malefic_afflicted(planet: str, d1_chart: dict) -> bool:
    """True if any malefic is within 8° of this planet (conjunction).

    A pragmatic v1 reading of "afflicted by malefic aspect": any malefic
    within 8° (the standard close-conjunction orb) is treated as
    afflicting. We exclude the planet itself and treat the Sun's
    affliction via combustion as Atra (already handled upstream).
    """
    try:
        my_lon = float(d1_chart[planet]["longitude"])
    except (KeyError, TypeError, ValueError):
        return False

    for malefic in _MALEFICS:
        if malefic == planet:
            continue
        entry = d1_chart.get(malefic)
        if not entry:
            continue
        try:
            malefic_lon = float(entry["longitude"])
        except (KeyError, TypeError, ValueError):
            continue
        if angular_separation(my_lon, malefic_lon) <= 8.0:
            return True
    return False


def _deeptadi_state(planet: str, d1_chart: dict) -> tuple[DeeptadiState, str]:
    """Decide the Deeptadi state for one planet.

    Returns (state, human_readable_reason). Priority order:

        1. Kshobita (planetary war) — overriding affliction
        2. Atra (combust by Sun) — overriding affliction
        3. Deepta (exalted)
        4. Sudukhita (debilitated)
        5. Shanta (Moolatrikona)
        6. Susvastha (own sign, non-MT)
        7. Pramudita (friend's sign)
        8. Dukhita (enemy's sign)
        9. Khala (default — malefic aspect or otherwise)
    """
    entry = d1_chart[planet]
    sign = int(entry["sign"]) if isinstance(entry.get("sign"), int) else None
    longitude = float(entry["longitude"])

    # --- 1. Kshobita: planetary war (overrides everything) -------------- #
    in_war, opponent = _in_planetary_war(planet, d1_chart)
    if in_war:
        return "Kshobita", f"in planetary war with {opponent}"

    # --- 2. Atra: combust by Sun (overrides sign-based states) ---------- #
    sun_entry = d1_chart.get("Sun")
    if sun_entry is not None and planet != "Sun":
        try:
            sun_lon = float(sun_entry["longitude"])
            if is_combust(planet, longitude, sun_lon):
                return "Atra", "combust by Sun"
        except (KeyError, ValueError):
            # Combustion check rejects unknown planets (Sun/Rahu/Ketu);
            # safe to fall through.
            pass

    # --- 3. Deepta: exaltation ------------------------------------------ #
    if sign is not None and EXALTATION.get(planet) == sign:
        return "Deepta", "exalted"

    # --- 4. Sudukhita: debilitation ------------------------------------- #
    if sign is not None and DEBILITATION.get(planet) == sign:
        return "Sudukhita", "debilitated"

    # --- 5. Shanta: Moolatrikona ---------------------------------------- #
    if is_moolatrikona(planet, longitude):
        return "Shanta", "in Moolatrikona"

    # --- 6. Susvastha: own sign (non-MT) -------------------------------- #
    if sign is not None and sign in OWN_SIGNS.get(planet, set()):
        return "Susvastha", "in own sign"

    # --- 7/8. Pramudita / Dukhita: friend or enemy of sign ruler -------- #
    if sign is not None:
        ruler = SIGN_RULERS.get(sign)
        if ruler is not None and planet != ruler:
            if _is_friend(planet, ruler):
                return "Pramudita", f"in friend ({ruler})'s sign"
            if _is_enemy(planet, ruler):
                return "Dukhita", f"in enemy ({ruler})'s sign"

    # --- 9. Khala: default -- malefic affliction or unclassified -------- #
    if _is_malefic_afflicted(planet, d1_chart):
        return "Khala", "afflicted by malefic"
    return "Khala", "unclassified (default)"


def _avastha_finding(
    planet: str, state: DeeptadiState, reason: str, entry: dict
) -> Finding:
    """Build the Finding for one planet's Deeptadi state."""
    direction = "positive" if state in _POSITIVE_STATES else "negative"
    sign_name = entry.get("sign_name", "?")
    verdict = f"{planet} is {state} ({reason})"
    return Finding(
        id=f"primitive.avasthas.{planet.lower()}",
        rule="deeptadi_avasthas",
        source_sequence=None,
        classification="primitive",
        direction=direction,
        verdict=verdict,
        evidence=[
            f"planet={planet}",
            f"state={state}",
            f"reason={reason}",
            f"sign={sign_name}",
            f"longitude={float(entry['longitude']):.4f}",
        ],
        confidence=_PRIMITIVE_CONFIDENCE,
    )


def compute_deeptadi_avasthas(d1_chart: dict) -> dict[str, Finding]:
    """Compute Deeptadi 9-state classification per planet.

    Args:
        d1_chart: Mapping of planet-name -> position dict. Each position
            must carry ``longitude``, ``sign`` (1..12), and ideally
            ``sign_name`` for prettier verdicts.

    Returns:
        Dict keyed by planet name, each value a
        ``primitive.avasthas.<planet>`` Finding whose ``direction``
        partitions into positive (Deepta/Susvastha/Pramudita/Shanta)
        vs negative (Dukhita/Sudukhita/Kshobita/Atra/Khala).

    Raises:
        KeyError: if a planet entry lacks ``longitude``.
    """
    findings: dict[str, Finding] = {}
    for planet, entry in d1_chart.items():
        if "longitude" not in entry:
            raise KeyError(
                f"planet {planet!r} missing required 'longitude' field"
            )
        state, reason = _deeptadi_state(planet, d1_chart)
        findings[planet] = _avastha_finding(planet, state, reason, entry)
    return findings


__all__ = ["compute_deeptadi_avasthas", "DeeptadiState"]
