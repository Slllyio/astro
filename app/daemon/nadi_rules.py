"""
Nadi/Vedic transit aspect detection rules.

Pure functions with no IO, no Swiss Ephemeris, no DB. Unit-testable in isolation.
The transit worker imports from here; nothing in here imports from the worker.
"""
from __future__ import annotations

from dataclasses import dataclass

# House-distance from transit planet's sign to the natal planet's sign,
# 1-indexed Vedic whole-sign counting (same sign = 1, next forward sign = 2, ...).
#
# Saturn 3rd/10th, Jupiter 5th/9th, Mars 4th/8th are the classical "special drishti".
# Conjunction (1) and opposition (7) are universal.
#
# Rahu/Ketu use Jupiter-style 5th/9th — modern Sukra/Chandra Nadi convention.
# Alternative conventions (BV Raman: nodes have no drishti; KP: dispositor proxy)
# can be wired in by editing the two NODE_5TH/NODE_9TH rows below.
VEDIC_ASPECTS: dict[str, dict[int, str]] = {
    "Saturn":  {1: "CONJUNCTION", 7: "OPPOSITION", 3: "SATURN_3RD",   10: "SATURN_10TH"},
    "Jupiter": {1: "CONJUNCTION", 7: "OPPOSITION", 5: "JUPITER_5TH",   9: "JUPITER_9TH"},
    "Mars":    {1: "CONJUNCTION", 7: "OPPOSITION", 4: "MARS_4TH",      8: "MARS_8TH"},
    "Rahu":    {1: "CONJUNCTION", 7: "OPPOSITION", 5: "NODE_5TH",      9: "NODE_9TH"},
    "Ketu":    {1: "CONJUNCTION", 7: "OPPOSITION", 5: "NODE_5TH",      9: "NODE_9TH"},
}

# Planets the v1 daemon monitors. Inner planets (Sun/Moon/Mercury/Venus) move too
# fast to produce useful Nadi-cadence alerts; they're tracked in NatalChart but not
# used as transit sources.
TRANSIT_PLANETS: tuple[str, ...] = ("Saturn", "Jupiter", "Mars", "Rahu", "Ketu")

# Natal planets the daemon checks transits against. All 9 grahas are valid targets.
NATAL_PLANETS: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"
)


@dataclass(frozen=True)
class AspectResult:
    """Outcome of comparing one transit-planet position against one natal-planet position."""
    transit_planet: str
    natal_planet: str
    alert_type: str           # e.g. "CONJUNCTION", "SATURN_3RD"
    house_distance: int       # 1..12, Vedic whole-sign count
    is_exact: bool            # True if circular_distance(lons) <= orb_degrees
    transit_lon: float
    natal_lon: float


def circular_distance(lon1: float, lon2: float) -> float:
    """Shortest angular distance between two longitudes on the 360 deg circle.

    A naive abs(lon1 - lon2) fails at the 359/2 deg boundary (returns 357 instead
    of 3). This helper handles the Pisces/Aries cusp correctly. See Phase 2 plan
    constraint #1 and the cusp tests in test_nadi_rules.py.
    """
    diff = abs(lon1 - lon2) % 360.0
    return min(diff, 360.0 - diff)


def whole_sign_house_distance(from_sign: int, to_sign: int) -> int:
    """Vedic whole-sign house count from from_sign to to_sign (1-indexed; same = 1).

    Both signs are 1..12 (1 = Aries). Counting is forward-only and inclusive of start.
    """
    if not (1 <= from_sign <= 12 and 1 <= to_sign <= 12):
        raise ValueError(f"signs must be 1..12, got {from_sign}, {to_sign}")
    return ((to_sign - from_sign) % 12) + 1


def compute_vedic_aspect(
    transit_planet: str,
    transit_sign: int,
    transit_lon: float,
    natal_planet: str,
    natal_sign: int,
    natal_lon: float,
    orb_degrees: float,
) -> AspectResult | None:
    """Return an AspectResult if the transit makes a recognized Vedic aspect, else None.

    Whole-sign drishti fires regardless of degree (any planet in the same sign
    aspects every degree of that sign). The orb_degrees tolerance only governs
    whether a CONJUNCTION is flagged is_exact=True for prioritization.
    """
    rules = VEDIC_ASPECTS.get(transit_planet)
    if rules is None:
        return None

    house_distance = whole_sign_house_distance(transit_sign, natal_sign)
    alert_type = rules.get(house_distance)
    if alert_type is None:
        return None

    is_exact = (
        alert_type == "CONJUNCTION"
        and circular_distance(transit_lon, natal_lon) <= orb_degrees
    )

    return AspectResult(
        transit_planet=transit_planet,
        natal_planet=natal_planet,
        alert_type=alert_type,
        house_distance=house_distance,
        is_exact=is_exact,
        transit_lon=transit_lon,
        natal_lon=natal_lon,
    )


def describe_aspect(result: AspectResult) -> str:
    """Human-readable description for TransitAlert.description."""
    qualifier = " (exact)" if result.is_exact else ""
    return (
        f"Transit {result.transit_planet} forms {result.alert_type} "
        f"with natal {result.natal_planet}{qualifier}"
    )
