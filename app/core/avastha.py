"""
Avastha (planetary states) for Vedic astrology.

Pure functions, no IO, no DB, no Swiss Ephemeris call. Computes:
  * Baladi avastha (5 states by degree-in-sign; reversed for even signs)
  * Jagradadi avastha (3 states by drishti aspects from benefics/malefics)
  * compute_avasthas: per-planet AvasthaInfo dict over a D1 chart.

Imports `whole_sign_house_distance` from `app.daemon.nadi_rules`.

A note on drishti reuse: the existing `compute_vedic_aspect` in
`app.daemon.nadi_rules` shortcircuits to None for any transit planet
absent from `VEDIC_ASPECTS` (Sun, Moon, Mercury, Venus). Those four
benefics still cast 7th-house drishti, so this module re-derives the
per-planet drishti house-set locally and uses
`whole_sign_house_distance` directly. CONJUNCTION (house_distance == 1)
is intentionally excluded from drishti tally per the user spec
("drishti aspects" = glance-aspects, not co-residency).
"""
from __future__ import annotations

from typing import Literal, TypedDict

from app.daemon.nadi_rules import whole_sign_house_distance

# ---------------------------------------------------------------------------
# Type definitions
# ---------------------------------------------------------------------------

BaladiState = Literal["Bala", "Kumara", "Yuva", "Vriddha", "Mrita"]
JagradadiState = Literal["Jagrad", "Swapna", "Sushupti"]


class AvasthaInfo(TypedDict):
    baladi: BaladiState
    jagradadi: JagradadiState
    benefic_aspects: int
    malefic_aspects: int


# ---------------------------------------------------------------------------
# Module constants
# ---------------------------------------------------------------------------

BENEFICS: tuple[str, ...] = ("Jupiter", "Venus", "Mercury", "Moon")
MALEFICS: tuple[str, ...] = ("Saturn", "Mars", "Rahu", "Ketu", "Sun")
GRAHAS: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
    "Saturn", "Rahu", "Ketu",
)

# 30 deg/sign / 5 buckets = 6 deg per Baladi state. Exact.
BALADI_BUCKET_WIDTH: float = 6.0

# Odd-sign progression by ascending degree.
BALADI_ODD: tuple[BaladiState, ...] = (
    "Bala", "Kumara", "Yuva", "Vriddha", "Mrita",
)
# Even-sign progression: same buckets, REVERSED.
BALADI_EVEN: tuple[BaladiState, ...] = tuple(reversed(BALADI_ODD))

# Per-planet drishti house targets (1-indexed whole-sign house distance from
# the aspecting planet's sign to the target sign). All planets have a 7th
# (opposition) drishti; the special drishti houses come from classical
# Parashara conventions plus the project's nodal convention (5/9 for
# Rahu/Ketu, matching `nadi_rules.VEDIC_ASPECTS`).
#
# Conjunction (house_distance == 1) is NOT included here -- spec says
# "drishti aspects" are glance-aspects, distinct from co-residency.
_DRISHTI_HOUSES: dict[str, frozenset[int]] = {
    "Sun":     frozenset({7}),
    "Moon":    frozenset({7}),
    "Mars":    frozenset({4, 7, 8}),
    "Mercury": frozenset({7}),
    "Jupiter": frozenset({5, 7, 9}),
    "Venus":   frozenset({7}),
    "Saturn":  frozenset({3, 7, 10}),
    "Rahu":    frozenset({5, 7, 9}),
    "Ketu":    frozenset({5, 7, 9}),
}


# ---------------------------------------------------------------------------
# Baladi
# ---------------------------------------------------------------------------

def baladi_state(sign: int, degree_in_sign: float) -> BaladiState:
    """Classify Baladi avastha by degree-in-sign with parity-aware ordering.

    Args:
        sign: 1..12 (1 = Aries).
        degree_in_sign: [0, 30); a value of exactly 30.0 is normalized to 0.0.

    Returns:
        One of "Bala", "Kumara", "Yuva", "Vriddha", "Mrita".

    Cusp convention: degrees < cutoff fall in the lower bucket, equality goes
    to the upper bucket (e.g. exactly 6.0 -> "Kumara"). Matches the
    `int(lon // 30)` floor-division convention used elsewhere in the engine.

    Raises:
        ValueError: if `sign` is not in 1..12 or `degree_in_sign` is not in
            [0, 30].
    """
    if not (1 <= sign <= 12):
        raise ValueError(f"sign must be 1..12, got {sign}")
    if not (0.0 <= degree_in_sign <= 30.0):
        raise ValueError(
            f"degree_in_sign must be in [0, 30], got {degree_in_sign}"
        )

    # Normalize the degenerate 30.0 case (full sign) down to 0.0 so it lands
    # in the first bucket (which is "Bala" for odd signs, "Mrita" for even).
    deg = degree_in_sign % 30.0

    # Bucket index 0..4. Clamp defensively against floating-point drift.
    idx = int(deg // BALADI_BUCKET_WIDTH)
    if idx > 4:
        idx = 4
    elif idx < 0:
        idx = 0

    table = BALADI_ODD if (sign % 2 == 1) else BALADI_EVEN
    return table[idx]


# ---------------------------------------------------------------------------
# Jagradadi
# ---------------------------------------------------------------------------

def _drishti_hits(from_planet: str, from_sign: int, to_sign: int) -> bool:
    """True iff `from_planet` at `from_sign` casts drishti onto `to_sign`."""
    houses = _DRISHTI_HOUSES.get(from_planet)
    if houses is None:
        return False
    distance = whole_sign_house_distance(from_sign, to_sign)
    return distance in houses


def jagradadi_state(
    planet_name: str,
    planet_sign: int,
    chart: dict[str, dict],
) -> tuple[JagradadiState, int, int]:
    """Classify Jagradadi avastha for `planet_name` based on incoming drishti.

    Args:
        planet_name: the target graha (the one whose state we classify).
        planet_sign: target's whole-sign 1..12.
        chart: full D1 chart dict; each entry has at least a "sign" key.

    Returns:
        (state, benefic_aspect_count, malefic_aspect_count) where state is:
            * "Jagrad"   -> only benefics aspect (or no aspects at all)
            * "Swapna"   -> both benefics AND malefics aspect
            * "Sushupti" -> only malefics aspect

    Self-aspects and aspects from a planet missing from `chart` are skipped.
    Conjunction is not counted as drishti.
    """
    benefic_count = 0
    malefic_count = 0

    for other in BENEFICS + MALEFICS:
        if other == planet_name:
            continue
        other_entry = chart.get(other)
        if other_entry is None:
            continue
        other_sign = other_entry["sign"]
        if not _drishti_hits(other, other_sign, planet_sign):
            continue
        if other in BENEFICS:
            benefic_count += 1
        else:
            malefic_count += 1

    if malefic_count > 0 and benefic_count == 0:
        state: JagradadiState = "Sushupti"
    elif malefic_count > 0 and benefic_count > 0:
        state = "Swapna"
    else:
        # No aspects at all OR benefic-only -> Jagrad.
        state = "Jagrad"

    return state, benefic_count, malefic_count


# ---------------------------------------------------------------------------
# Aggregator
# ---------------------------------------------------------------------------

def compute_avasthas(d1_chart: dict[str, dict]) -> dict[str, AvasthaInfo]:
    """Compute Baladi + Jagradadi avastha for every graha in `d1_chart`.

    Args:
        d1_chart: dict keyed by graha name; each value must include "sign"
            (1..12) and "degree_in_sign" (float in [0, 30)).

    Returns:
        Dict keyed by graha name, mapping to AvasthaInfo.

    Raises:
        ValueError: if any of the 9 grahas are missing.
    """
    missing = [g for g in GRAHAS if g not in d1_chart]
    if missing:
        raise ValueError(f"d1_chart missing grahas: {missing}")

    out: dict[str, AvasthaInfo] = {}
    for graha in GRAHAS:
        entry = d1_chart[graha]
        sign = entry["sign"]
        deg = entry["degree_in_sign"]
        baladi = baladi_state(sign, deg)
        jagradadi, b_count, m_count = jagradadi_state(graha, sign, d1_chart)
        out[graha] = AvasthaInfo(
            baladi=baladi,
            jagradadi=jagradadi,
            benefic_aspects=b_count,
            malefic_aspects=m_count,
        )
    return out
