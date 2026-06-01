"""Tier-0 primitive: Vimsopaka Bala in the Shodashavarga (16-varga) scheme.

Doctrine lock - D-3 (``docs/doctrine-decisions.md``)
====================================================

Use the **Shodashavarga (16-varga) Vimsopaka scheme** with the canonical
BPHS Vol.I Ch.7 vv.21-25 weights. The weights sum to exactly **20.0**
by definition (Vimsopaka = "twenty-fold portion"). Any change to the
weights MUST be reflected by D-3 amendment in
``docs/doctrine-decisions.md``.

Canonical weights (D-3 revision 1)
==================================

    D1 (Rasi)            3.5    D24 (Chaturvimsamsa)  0.5
    D2 (Hora)            1.0    D27 (Saptavimsamsa)   0.5
    D3 (Drekkana)        1.0    D30 (Trimsamsa)       1.0
    D4 (Chaturthamsa)    0.5    D40 (Khavedamsa)      0.5
    D7 (Saptamsa)        0.5    D45 (Akshavedamsa)    0.5
    D9 (Navamsa)         3.0    D60 (Shastiamsa)      4.0
    D10 (Dasamsa)        0.5
    D12 (Dwadasamsa)     0.5
    D16 (Shodasamsa)     2.0
    D20 (Vimsamsa)       0.5
    Sum                 = 20.0

Algorithm
=========

For each planet (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn —
plus Rahu/Ketu if present in the chart), iterate over the 16 vargas.
In each varga determine the planet's **dignity coefficient** from its
sign placement:

    Exalted / Moolatrikona / Own sign  -> 1.0
    Friend's sign                       -> 0.5
    Neutral                             -> 0.25
    Enemy / Debilitated                 -> 0.0

Vimsopaka(planet) = sum over 16 vargas of weight * coefficient.

The score is in **[0.0, 20.0]** (assertable property).

Public API
==========

    VIMSOPAKA_WEIGHTS_SHODASHAVARGA: Final[dict[int, float]]
        Frozen at module-load time; sum-to-20.0 invariant asserted.

    compute_vimsopaka(d1_chart, all_varga_charts) -> dict[str, Finding]
        all_varga_charts is a dict keyed by **divisor** (int) mapping to
        the per-planet position dict for that varga. The caller is
        responsible for including divisor 1 -> d1_chart. Convenience:
        the function will fall back to ``d1_chart`` if divisor 1 is
        absent.

Usage
=====

    >>> from app.core.ephemeris_engine import calculate_all_charts
    >>> from app.core.shodashavarga import (
    ...     SHODASHAVARGA_NAMES, compute_divisional_charts,
    ... )
    >>> chart = calculate_all_charts(1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)
    >>> d1 = chart["d1"]
    >>> div_charts = compute_divisional_charts(d1)
    >>> varga_in = {1: d1}
    >>> for divisor, name in SHODASHAVARGA_NAMES.items():
    ...     if divisor != 1:
    ...         varga_in[divisor] = div_charts[name]
    >>> from app.reading.computations.vimsopaka import compute_vimsopaka
    >>> findings = compute_vimsopaka(d1, varga_in)
    >>> findings["Sun"].verdict   # doctest: +ELLIPSIS
    'Sun Vimsopaka ... (...)'
"""
from __future__ import annotations

import logging
from typing import Final

from app.core.dignity import (
    dignity_state,
    is_moolatrikona,
)
from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# D-3 doctrine constants
# --------------------------------------------------------------------------

# Canonical BPHS Ch.7 vv.21-25 per-Varga weights. Frozen at module load.
VIMSOPAKA_WEIGHTS_SHODASHAVARGA: Final[dict[int, float]] = {
    1: 3.5, 2: 1.0, 3: 1.0, 4: 0.5,
    7: 0.5, 9: 3.0, 10: 0.5, 12: 0.5,
    16: 2.0, 20: 0.5, 24: 0.5, 27: 0.5,
    30: 1.0, 40: 0.5, 45: 0.5, 60: 4.0,
}

# Arithmetic invariant per D-3 (Vimsopaka = "twenty-fold portion"). This
# check is REQUIRED at import time per the doctrine lockfile. If any
# future amendment alters the table, the assertion will catch a wrong
# total before the engine can produce misleading scores.
assert abs(sum(VIMSOPAKA_WEIGHTS_SHODASHAVARGA.values()) - 20.0) < 1e-9, (
    "D-3 invariant violation: VIMSOPAKA_WEIGHTS_SHODASHAVARGA must sum to 20.0"
)


# Dignity coefficient table per the Phase-1 spec for vimsopaka. The 5-tier
# breakdown collapses to 4 numeric levels (exalted/own/MT == 1.0, friendly
# == 0.5, neutral == 0.25, debilitated/inimical == 0.0).
_DIGNITY_COEFFICIENT: Final[dict[str, float]] = {
    "exalted":      1.0,
    "own":          1.0,
    "moolatrikona": 1.0,    # synthesized in _coefficient_for
    "friendly":     0.5,
    "neutral":      0.25,
    "inimical":     0.0,
    "debilitated":  0.0,
}


_PRIMITIVE_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


# Verdict-band thresholds for human-readable summary. The dispute / domain
# layer may apply different bands; these are documented in the verdict
# only.
def _band_for(score: float) -> str:
    if score >= 15.0:
        return "very strong"
    if score >= 12.0:
        return "strong"
    if score >= 8.0:
        return "moderate"
    if score >= 5.0:
        return "weak"
    return "very weak"


def _coefficient_for(planet: str, sign: int, longitude: float | None) -> float:
    """Return the per-varga dignity coefficient for a planet.

    The 1.0 tier is awarded for exaltation, own-sign, AND Moolatrikona.
    Since ``dignity_state`` returns ``"own"`` for Moolatrikona placements
    (Moolatrikona is a longitude-degree subset of own-sign), the
    classification already collapses cleanly. We additionally call
    ``is_moolatrikona`` for documentation purposes — both paths yield 1.0.

    Rahu/Ketu: classical dignity tables are silent. Per ``dignity.py``,
    they have no exaltation / own-sign / debilitation entries; only
    ``dignity_state`` fall-through to the naisargika ruler check applies.
    We delegate to ``dignity_state`` which will return ``"neutral"`` /
    ``"friendly"`` / ``"inimical"`` based on the sign-ruler relation
    encoded in ``NAISARGIKA_FRIENDSHIP``.
    """
    try:
        state = dignity_state(planet, sign)
    except (KeyError, ValueError):
        # Unknown planet (e.g. Rahu/Ketu in some configurations).
        # Conservative default: neutral (0.25).
        return _DIGNITY_COEFFICIENT["neutral"]

    coeff = _DIGNITY_COEFFICIENT.get(state)
    if coeff is None:
        # Defensive: dignity_state is a Literal, so this is unreachable
        # under normal operation, but a future enum-add must not crash
        # silently.
        return _DIGNITY_COEFFICIENT["neutral"]
    return coeff


def _planet_sign(chart: dict, planet: str) -> int | None:
    """Return the 1-indexed sign of ``planet`` in ``chart``, or None."""
    entry = chart.get(planet)
    if not isinstance(entry, dict):
        return None
    sign = entry.get("sign")
    if not isinstance(sign, int) or not (1 <= sign <= 12):
        return None
    return sign


def _planet_longitude(chart: dict, planet: str) -> float | None:
    """Return the longitude (deg) of ``planet`` in ``chart``, or None."""
    entry = chart.get(planet)
    if not isinstance(entry, dict):
        return None
    lon = entry.get("longitude")
    if isinstance(lon, (int, float)):
        return float(lon)
    return None


def _natal_planets(d1_chart: dict) -> list[str]:
    """Return the list of natal planets we will score.

    The seven Vedic naturals plus Rahu/Ketu, but ONLY those actually
    present in ``d1_chart``. (Custom charts may omit nodes.)
    """
    candidates = [
        "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
        "Rahu", "Ketu",
    ]
    return [p for p in candidates if p in d1_chart]


def compute_vimsopaka(
    d1_chart: dict, all_varga_charts: dict[int, dict]
) -> dict[str, Finding]:
    """Compute Vimsopaka Bala (Shodashavarga scheme) per planet.

    Args:
        d1_chart: Natal D1 chart (planet -> position dict). Required so
            we can enumerate the natal planet set.
        all_varga_charts: Dict keyed by divisor (int) mapping to the
            per-varga position dict for that planet set. MUST contain
            entries for every divisor in
            ``VIMSOPAKA_WEIGHTS_SHODASHAVARGA``. If divisor 1 is
            absent, ``d1_chart`` is used as the divisor-1 fallback.

    Returns:
        Dict keyed by planet name. Each value is a Finding with
        ``id == "primitive.vimsopaka.<planet_lowercase>"`` and
        ``evidence`` including ``score=<float>``,
        ``band=<string>``, and per-varga breakdown lines.

    Raises:
        ValueError: ``all_varga_charts`` missing a required divisor and
            no fallback is available.
    """
    if not isinstance(all_varga_charts, dict):
        raise TypeError(
            f"all_varga_charts must be a dict[int, dict], got "
            f"{type(all_varga_charts).__name__}"
        )

    # Build the divisor -> chart mapping with d1 fallback.
    resolved: dict[int, dict] = dict(all_varga_charts)
    if 1 not in resolved:
        resolved[1] = d1_chart

    missing = [
        d for d in VIMSOPAKA_WEIGHTS_SHODASHAVARGA
        if d not in resolved or not isinstance(resolved[d], dict)
    ]
    if missing:
        raise ValueError(
            f"all_varga_charts missing required divisors: {missing!r}"
        )

    findings: dict[str, Finding] = {}
    for planet in _natal_planets(d1_chart):
        score = 0.0
        breakdown: list[str] = []
        for divisor, weight in VIMSOPAKA_WEIGHTS_SHODASHAVARGA.items():
            varga_chart = resolved[divisor]
            sign = _planet_sign(varga_chart, planet)
            if sign is None:
                # Planet missing from this varga; treat as neutral (0.25
                # coefficient) so the score remains computable. Log so
                # operational issues surface.
                logger.warning(
                    "vimsopaka: planet %s missing from D%d; coefficient=0.25",
                    planet, divisor,
                )
                coeff = _DIGNITY_COEFFICIENT["neutral"]
                state = "missing"
            else:
                lon = _planet_longitude(varga_chart, planet)
                # Track Moolatrikona explicitly when the longitude is
                # available, so the band reflects the canonical tier.
                mt = bool(lon is not None and is_moolatrikona(planet, lon))
                if mt:
                    state = "moolatrikona"
                    coeff = _DIGNITY_COEFFICIENT["moolatrikona"]
                else:
                    state = dignity_state(planet, sign) if planet in (
                        "Sun", "Moon", "Mars", "Mercury",
                        "Jupiter", "Venus", "Saturn",
                    ) else "neutral"
                    coeff = _coefficient_for(planet, sign, lon)
            contribution = weight * coeff
            score += contribution
            breakdown.append(
                f"D{divisor}: w={weight} sign={sign} state={state} "
                f"coeff={coeff:.2f} contrib={contribution:.3f}"
            )

        # Pin to canonical bounds (defensive against float drift).
        if score < 0.0:
            score = 0.0
        if score > 20.0:
            score = 20.0

        band = _band_for(score)
        verdict = (
            f"{planet} Vimsopaka {score:.2f} ({band} across vargas)"
        )

        evidence = [
            f"planet={planet}",
            f"score={score:.6f}",
            f"band={band}",
            "doctrine=D-3 (shodashavarga, sum=20.0)",
        ]
        evidence.extend(breakdown)

        findings[planet] = Finding(
            id=f"primitive.vimsopaka.{planet.lower()}",
            rule="vimsopaka",
            source_sequence=None,
            classification="primitive",
            direction="neutral",
            verdict=verdict,
            evidence=evidence,
            confidence=_PRIMITIVE_CONFIDENCE,
        )

    return findings


__all__ = [
    "VIMSOPAKA_WEIGHTS_SHODASHAVARGA",
    "compute_vimsopaka",
]
