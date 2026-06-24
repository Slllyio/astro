"""Classical severity scoring for mundane forecast events.

Returns a 1-10 score per event so the consumer-facing forecast can sort
"big" events (Saturn ingress, eclipse) above "small" ones (Mercury station,
Mercury-Venus near-miss conjunction).

The scoring is **deterministic**, based on classical weighting principles
from Phaladeepika (mundane chapters) and BPHS:

* SLOW PLANETS DOMINATE: Saturn > Rahu/Ketu > Jupiter > Mars dominate
  mundane forecasts because their effects span weeks-to-years. Mercury and
  Moon shift too often to be a "mundane-week" headline.
* LUMINARIES > LESSER GRAHAS for eclipses + lunations (the entire sky
  pivots on the Sun-Moon axis).
* RARE BEATS COMMON: ingresses and stations are rarer than conjunctions
  for the slow planets — Saturn ingresses once every 2.5 yrs, Jupiter once
  every ~1 yr. Anything that rare deserves a top score.
* CONJUNCTION SEVERITY scales with rarity (jupiter-saturn = high, mars-
  mercury = low) AND with tightness (a 0.3° orb is louder than 1.9°).

The score is intentionally banded (1-10 integer) rather than continuous
so the UI can color-code with a small palette (green/yellow/orange/red).
"""
from __future__ import annotations

from typing import Any

# Planet weights — relative importance in mundane affairs. Slow movers
# higher because their ingresses set the "mood" of a generation/year/season.
_PLANET_WEIGHT: dict[str, int] = {
    "Saturn":  10,
    "Rahu":     9, "Ketu": 9,
    "Jupiter":  9,
    "Mars":     7,
    "Sun":      6,   # mostly via eclipses; daily ingress is fast
    "Venus":    5,
    "Mercury":  4,
    "Moon":     4,   # mostly via lunations; daily nakshatra change is fast
}

# Base scores per event type, before per-planet adjustment.
_BASE_TYPE_SCORE: dict[str, int] = {
    "ECLIPSE":     10,
    "INGRESS":      6,
    "STATION":      5,
    "FULL_MOON":    5,
    "NEW_MOON":     5,
    "CONJUNCTION":  4,
}

# Conjunction-pair classical weighting. A "great conjunction" (Jupiter-Saturn)
# is mundane-political "era marker" — every ~20 yrs and historically tied to
# regime-change predictions in Western mundane astrology too. A
# Mercury-Venus near-miss is mostly cosmetic.
_CONJUNCTION_PAIR_BONUS: dict[frozenset[str], int] = {
    frozenset({"Jupiter", "Saturn"}): 4,
    frozenset({"Saturn", "Mars"}):    3,  # bellicose, frequently cited
    frozenset({"Saturn", "Rahu"}):    3,
    frozenset({"Saturn", "Ketu"}):    3,
    frozenset({"Jupiter", "Rahu"}):   2,  # "guru-chandala" yoga signal
    frozenset({"Jupiter", "Ketu"}):   2,
    frozenset({"Mars", "Rahu"}):      2,  # "angaraka" — violence/accident
    frozenset({"Mars", "Saturn"}):    3,  # same energy as Saturn-Mars
    frozenset({"Jupiter", "Mars"}):   2,
    frozenset({"Venus", "Saturn"}):   1,
    frozenset({"Mercury", "Saturn"}): 1,
}


def _conjunction_orb_modifier(orb_degrees: float) -> int:
    """Tighter conjunctions are louder; ≤0.5° gets +2, ≤1.0° gets +1."""
    if orb_degrees <= 0.5:
        return 2
    if orb_degrees <= 1.0:
        return 1
    return 0


def score_event(event: dict[str, Any]) -> int:
    """Return a 1-10 severity score for a mundane forecast event.

    Clamped to [1, 10] so the UI can rely on a fixed band. The exact
    weights are tunable in the module-level constants without changing
    callers.
    """
    event_type = event.get("type")
    base = _BASE_TYPE_SCORE.get(event_type, 3)

    if event_type in {"INGRESS", "STATION"}:
        planet = event.get("planet", "")
        # Bonus = planet weight, scaled so Saturn (10) bumps a STATION
        # from 5 -> 9, Mercury (4) keeps it at ~5.
        bonus = (_PLANET_WEIGHT.get(planet, 4) - 5) // 2
        return max(1, min(10, base + bonus + 1))

    if event_type == "CONJUNCTION":
        a = event.get("planet_a", "")
        b = event.get("planet_b", "")
        pair_bonus = _CONJUNCTION_PAIR_BONUS.get(frozenset({a, b}), 0)
        avg_planet_weight = (_PLANET_WEIGHT.get(a, 4) + _PLANET_WEIGHT.get(b, 4)) // 2
        planet_bonus = (avg_planet_weight - 5) // 2
        orb = event.get("orb_degrees", 2.0)
        return max(1, min(10, base + pair_bonus + planet_bonus
                          + _conjunction_orb_modifier(orb)))

    if event_type in {"NEW_MOON", "FULL_MOON"}:
        # Lunation severity is constant per event type; the *page* can
        # boost a lunation if it falls in a sensitive nakshatra later.
        return base

    if event_type == "ECLIPSE":
        # Solar > Lunar in mundane terms (totality affects vast geography).
        # Subtype tunes within family.
        family = event.get("family", "")
        subtype = event.get("subtype", "")
        if family == "SOLAR":
            if subtype == "TOTAL":
                return 10
            if subtype in {"ANNULAR", "HYBRID"}:
                return 9
            return 8  # partial solar
        if family == "LUNAR":
            if subtype == "TOTAL":
                return 9
            if subtype == "PARTIAL":
                return 8
            return 7  # penumbral
        return base

    return max(1, min(10, base))


def severity_band(score: int) -> str:
    """Map a 1-10 score to a UI color band name.

    The page CSS uses these to color-code event cards: green/yellow/orange/red.
    Keeps colour decisions in CSS, not Python.
    """
    if score >= 9:
        return "red"     # major / era-defining
    if score >= 7:
        return "orange"  # significant
    if score >= 5:
        return "yellow"  # notable
    return "green"       # minor / background


def annotate_events(events: list[dict]) -> list[dict]:
    """Tag each event in-place-by-copy with severity score + band.

    Returns a NEW list of NEW dicts (per immutability convention) so callers
    can compose this with other annotators without mutation.
    """
    return [
        {**e, "severity": score_event(e), "severity_band": severity_band(score_event(e))}
        for e in events
    ]
