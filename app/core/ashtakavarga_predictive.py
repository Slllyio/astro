"""Ashtakavarga predictive layer — Gap A.

BPHS Ch.66-69 + BV Raman's *A Manual of Hindu Astrology* establish four
predictive uses of Ashtakavarga that our framework has not exercised:

1. **Bhava strength via SAV** — Sarvashtakavarga points per BHAVA (not
   per sign): classify ≥30 STRONG, 25-29 AVERAGE, <25 WEAK. Bhava
   predictions inherit this strength as a multiplier.

2. **Transit modulation via BAV** — when a planet P transits a sign S
   with HIGH BAV[P][S], its results are AMPLIFIED; LOW BAV suppresses
   the same configuration's effects. Raman used 30 as the cutoff for
   "good transit", 25-30 average, ≤25 inhibitory.

3. **Sage's Sarvashtaka method** (BPHS Ch.66-69) — dasha bhukti results
   modulated by the SAV of the bhukti lord's natal sign + transit sign.
   Strong-strong = full delivery; weak-weak = severe inhibition.

4. **Kakshya analysis** — each sign has 8 sub-segments of 3°45' each;
   each kakshya is "owned" by a specific contributor. Transit through
   a kakshya whose owner is benefic-aspected delivers; through a malefic-
   owned kakshya delays.

## Why this matters

Round 11 ML found no signal in features like "planet sign" alone. The
AND-gate framework (Phases 1-9) added doctrine-faithful concurrence.
Ashtakavarga adds **quantitative strength-grading** on top — the
master's actual timing precision. Without it, our framework predicts
direction (which house activates) but not intensity (how strongly).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

from app.core.ashtakavarga import compute_ashtakavarga
from app.core.chart_model import Chart


# Per BPHS Ch.66 + Raman *Manual* — empirical thresholds widely used.
SAV_STRONG_THRESHOLD: Final[int] = 30
SAV_AVERAGE_THRESHOLD: Final[int] = 25
BAV_PER_PLANET_STRONG: Final[int] = 5   # bindu ≥5 in a sign = strong for that planet
BAV_PER_PLANET_AVERAGE: Final[int] = 4
BAV_MAX_PER_SIGN: Final[int] = 8         # max BAV value per planet per sign

_VISIBLE_PLANETS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
)


@dataclass(frozen=True)
class BhavaSAVReport:
    """SAV verdict for a single bhava."""
    bhava: int
    sav_points: int           # max theoretical 56, typical 22-35
    strength_label: str       # "strong" | "average" | "weak"
    multiplier: float         # 1.3 strong, 1.0 average, 0.7 weak — applied to bhava verdict


@dataclass(frozen=True)
class TransitBAVReport:
    """BAV verdict for a planet currently transiting a sign."""
    planet: str
    transit_sign: int
    bav_points: int           # max 8 per planet per sign
    strength_label: str       # "strong" | "average" | "weak"
    delivery_multiplier: float


@dataclass(frozen=True)
class AshtakavargaPredictive:
    """Whole-chart Ashtakavarga predictive report."""
    sav_per_bhava: Mapping[int, BhavaSAVReport]
    bav_per_planet_per_sign: Mapping[str, list[int]]   # ref data
    sav_per_sign: list[int]                              # ref data
    strongest_bhava: int
    weakest_bhava: int
    total_sav: int                                       # sum across 12 signs


def _chart_to_d1_dict(chart: Chart) -> dict[str, dict[str, object]]:
    """Convert Chart to the dict-shape compute_ashtakavarga expects."""
    return {
        p: {
            "sign": chart.planet_signs.get(p),
            "longitude": chart.planet_lons.get(p, 0.0),
        }
        for p in _VISIBLE_PLANETS
        if p in chart.planet_signs
    }


def _classify_sav(points: int) -> tuple[str, float]:
    """SAV strength label + bhava-verdict multiplier."""
    if points >= SAV_STRONG_THRESHOLD:
        return "strong", 1.3
    if points >= SAV_AVERAGE_THRESHOLD:
        return "average", 1.0
    return "weak", 0.7


def _classify_bav(points: int) -> tuple[str, float]:
    """BAV-per-planet-per-sign label + transit-delivery multiplier."""
    if points >= BAV_PER_PLANET_STRONG:
        return "strong", 1.3
    if points >= BAV_PER_PLANET_AVERAGE:
        return "average", 1.0
    return "weak", 0.7


def compute_predictive(chart: Chart) -> AshtakavargaPredictive:
    """Compute the full Ashtakavarga predictive report for one chart.

    The bhava judge (Phase 6) and gochara engine (Phase 7) can call this
    once per chart and apply the multipliers to their verdicts.
    """
    asc = {"sign": chart.asc_sign, "longitude": chart.asc_lon}
    matrix = compute_ashtakavarga(_chart_to_d1_dict(chart), asc)

    sav_per_sign: list[int] = list(matrix["sav"])
    bav_per_planet: dict[str, list[int]] = dict(matrix["bav_per_planet"])

    # Map sign-indexed SAV → bhava-indexed SAV
    sav_per_bhava: dict[int, BhavaSAVReport] = {}
    for bhava in range(1, 13):
        sign = ((bhava - 1 + chart.asc_sign - 1) % 12) + 1
        points = sav_per_sign[sign - 1]
        label, mult = _classify_sav(points)
        sav_per_bhava[bhava] = BhavaSAVReport(
            bhava=bhava, sav_points=points,
            strength_label=label, multiplier=mult,
        )

    by_strength = sorted(sav_per_bhava.values(), key=lambda r: r.sav_points)
    return AshtakavargaPredictive(
        sav_per_bhava=sav_per_bhava,
        bav_per_planet_per_sign=bav_per_planet,
        sav_per_sign=sav_per_sign,
        strongest_bhava=by_strength[-1].bhava,
        weakest_bhava=by_strength[0].bhava,
        total_sav=sum(sav_per_sign),
    )


def transit_bav_report(
    report: AshtakavargaPredictive, planet: str, transit_sign: int,
) -> TransitBAVReport:
    """For a planet currently transiting a sign, grade its BAV strength.

    Raman: when a planet transits a sign with ≥5 of its own bindus,
    results are strongly delivered; with ≤3, transit signal is muted
    even if double-transit or other doctrinal triggers fire.
    """
    if planet not in _VISIBLE_PLANETS:
        raise ValueError(f"planet must be visible (Sun..Saturn), got {planet}")
    if not 1 <= transit_sign <= 12:
        raise ValueError(f"transit_sign must be 1..12, got {transit_sign}")
    bav = report.bav_per_planet_per_sign.get(planet, [0]*12)
    points = bav[transit_sign - 1]
    label, mult = _classify_bav(points)
    return TransitBAVReport(
        planet=planet, transit_sign=transit_sign,
        bav_points=points, strength_label=label,
        delivery_multiplier=mult,
    )


def sage_dasha_bhukti_grade(
    report: AshtakavargaPredictive, bhukti_lord: str,
    bhukti_lord_natal_sign: int, current_transit_sign: int,
) -> dict[str, object]:
    """Sage's Sarvashtaka method (BPHS Ch.66-69).

    Grade dasha-bhukti delivery by COMBINING:
      (a) SAV of bhukti lord's natal sign (static promise)
      (b) BAV of bhukti lord in the sign it's currently transiting (dynamic activation)

    Returns a verdict dict with:
      - static_sav: int
      - transit_bav: int
      - composite_grade: "FULL" / "PARTIAL" / "MUTED"
      - delivery_multiplier: float
    """
    static_sav = report.sav_per_sign[bhukti_lord_natal_sign - 1]
    transit_bav = report.bav_per_planet_per_sign.get(bhukti_lord, [0]*12)[
        current_transit_sign - 1
    ]
    # Composite: both strong → FULL; one weak → PARTIAL; both weak → MUTED
    static_strong = static_sav >= SAV_STRONG_THRESHOLD
    transit_strong = transit_bav >= BAV_PER_PLANET_STRONG
    if static_strong and transit_strong:
        grade, mult = "FULL", 1.5
    elif static_strong or transit_strong:
        grade, mult = "PARTIAL", 1.0
    elif static_sav < SAV_AVERAGE_THRESHOLD and transit_bav < BAV_PER_PLANET_AVERAGE:
        grade, mult = "MUTED", 0.5
    else:
        grade, mult = "AVERAGE", 0.8
    return {
        "static_sav": static_sav,
        "transit_bav": transit_bav,
        "composite_grade": grade,
        "delivery_multiplier": mult,
    }


def kakshya_owner(sign: int, deg_in_sign: float) -> str:
    """Identify the kakshya-owner planet for a given longitude.

    Each sign has 8 kakshyas of 3°45' (= 225 arc-min). The owners cycle:
    Saturn, Jupiter, Mars, Sun, Venus, Mercury, Moon, Lagna — repeating.
    Per BPHS Ch.69. The first kakshya of each sign is owned by Saturn.
    """
    if not (1 <= sign <= 12):
        raise ValueError(f"sign must be 1..12, got {sign}")
    if not (0 <= deg_in_sign < 30):
        raise ValueError(f"deg_in_sign must be 0..30, got {deg_in_sign}")
    KAKSHYA_OWNERS = ("Saturn", "Jupiter", "Mars", "Sun",
                      "Venus", "Mercury", "Moon", "Lagna")
    kakshya_index = int(deg_in_sign // 3.75)  # 30/8 = 3.75°
    return KAKSHYA_OWNERS[kakshya_index]
