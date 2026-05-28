"""Tier-1 foundation: Phase-1 Shadbala wrapper per BPHS Ch.27.

Doctrine source: BPHS Vol.II Ch.27 (Sphuta Bala Adhyaya), verses 27.32-38.

BPHS Ch.27 decomposes Shadbala into six components. Phase-0 (Sthana-bala)
is already implemented in ``app.core.shadbala.sthana_bala`` and consumed
by upstream primitives. This module wraps the remaining **five** Phase-1
components as Findings so they participate in the foundation tier:

  - **Dig-bala**         (BPHS 27.36): directional strength
    * Sun, Mars     -> 10th-house Dig (Madhya / midheaven)
    * Moon, Venus   -> 4th-house Dig  (Patala / IC)
    * Mercury, Jup. -> 1st-house Dig  (Lagna)
    * Saturn        -> 7th-house Dig  (Descendant)
  - **Kala-bala**        (BPHS 27.32-33, Phase-2 partial): paksha-bala
    sub-component is the only one filled at present. The other 7 Kala
    sub-components (Natonnata, Tribhaga, Abda, Masa, Vara, Hora, Ayana,
    Yuddha) remain Phase-2b work but the public API already accommodates
    them via the ``is_daytime`` arg (consumed inside core's
    ``shadbala_total`` when Phase-2b lands).
  - **Cheshta-bala**     (BPHS 27.36-37): motion strength. Retrograde
    star-planet = 60 virupa, direct = 30. Sun & Moon = 0 in Phase-2.
  - **Naisargika-bala**  (BPHS 27.34): innate constant per planet.
    Sun=60, Moon=51.43, Venus=42.86, Jupiter=34.29, Mercury=25.71,
    Mars=17.14, Saturn=8.57 (descending 60/7-step).
  - **Drik-bala**        (BPHS 27.38): net aspectual strength. Sum of
    benefic-aspect virupa minus malefic-aspect virupa, divided by 4.

The module is intentionally **a thin wrapper**: every numerical value is
computed by ``app.core.shadbala.shadbala_total`` and re-projected into
``Finding`` envelopes. No new astrological math lives here.

Public API
==========

  compute_shadbala_phase1(d1_chart, asc_sign, is_daytime) -> dict[str, Finding]

Returns a Finding per chart-planet keyed by planet name.

ID grammar: ``foundation.shadbala_phase1.<planet>``  (lower-cased planet).
Classification: ``primitive``.
Direction: ``positive`` when total >= 100, ``negative`` when total <= 30,
``neutral`` otherwise.

Verdict format::

    'Saturn Shadbala-phase1: dig=10.0 kala=15.0 cheshta=20.0 nai=8.6 drik=5.0 (total=58.6)'

Usage
=====

    >>> from app.core.ephemeris_engine import calculate_all_charts
    >>> charts = calculate_all_charts(
    ...     year=1990, month=7, day=15, hour=12, minute=0,
    ...     tz_offset=5.5, latitude=12.97, longitude=77.59,
    ... )
    >>> from app.reading.computations.shadbala_phase1 import (
    ...     compute_shadbala_phase1,
    ... )
    >>> findings = compute_shadbala_phase1(
    ...     charts["d1"], asc_sign=charts["ascendant"]["sign"],
    ...     is_daytime=True,
    ... )
    >>> findings["Sun"].direction in {"positive", "negative", "neutral"}
    True
"""
from __future__ import annotations

import logging
from typing import Final

from app.core.shadbala import shadbala_total
from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# Direction thresholds. These bracket the Phase-1 component sum
# (excluding Sthana) — the maximum theoretical Phase-1 total is roughly
# 60 (Dig) + 60 (Kala) + 60 (Cheshta) + 60 (Naisargika cap) + 60 (Drik)
# = 300 virupa, though Drik can be negative.
_POSITIVE_THRESHOLD: Final[float] = 100.0
_NEGATIVE_THRESHOLD: Final[float] = 30.0


_FOUNDATION_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _direction_for(total: float) -> str:
    """Map Phase-1 total -> Finding.direction enum value."""
    if total >= _POSITIVE_THRESHOLD:
        return "positive"
    if total <= _NEGATIVE_THRESHOLD:
        return "negative"
    return "neutral"


def _verdict_for(planet: str, dig: float, kala: float, cheshta: float,
                 nai: float, drik: float, total: float) -> str:
    """Human-readable one-line verdict for the Finding."""
    return (
        f"{planet} Shadbala-phase1: dig={dig:.1f} kala={kala:.1f} "
        f"cheshta={cheshta:.1f} nai={nai:.1f} drik={drik:.1f} "
        f"(total={total:.1f})"
    )


def _parse_component(finding: Finding, key: str) -> float:
    """Test-helper: pull a numeric component out of a Finding's evidence."""
    needle = f"{key}="
    for line in finding.evidence:
        if line.startswith(needle):
            return float(line[len(needle):])
    raise KeyError(f"component {key!r} not found in evidence")


def _planet_finding(
    planet: str,
    breakdown: dict,
) -> Finding:
    """Build the Finding for one planet's Phase-1 Shadbala bundle."""
    dig = float(breakdown.get("dig", 0.0))
    kala = float(breakdown.get("kala", 0.0))
    cheshta = float(breakdown.get("cheshta", 0.0))
    nai = float(breakdown.get("naisargika", 0.0))
    drik = float(breakdown.get("drik", 0.0))
    total = dig + kala + cheshta + nai + drik
    direction = _direction_for(total)
    return Finding(
        id=f"foundation.shadbala_phase1.{planet.lower()}",
        rule="shadbala_phase1",
        source_sequence=None,
        classification="primitive",
        direction=direction,
        verdict=_verdict_for(planet, dig, kala, cheshta, nai, drik, total),
        evidence=[
            f"planet={planet}",
            f"dig={dig:.4f}",
            f"kala={kala:.4f}",
            f"cheshta={cheshta:.4f}",
            f"nai={nai:.4f}",
            f"drik={drik:.4f}",
            f"total={total:.4f}",
            "doctrine=BPHS Ch.27 (Sphuta Bala vv.32-38)",
        ],
        confidence=_FOUNDATION_CONFIDENCE,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_shadbala_phase1(
    d1_chart: dict,
    asc_sign: int,
    is_daytime: bool,
) -> dict[str, Finding]:
    """Compute Phase-1 Shadbala components per chart planet.

    Args:
        d1_chart: Mapping of planet-name -> position dict. Each entry
            must carry ``sign`` (1..12), ``longitude``, and
            ``is_retrograde``. Optionally ``d9_sign``.
        asc_sign: Ascendant rashi (1..12).
        is_daytime: Reserved for Phase-2b Kala-bala sub-components
            (Vara/Hora/Ayana require day/night context). Currently
            forwarded but not consumed; the API is locked so adding
            Phase-2b later is non-breaking.

    Returns:
        Dict keyed by planet name, each value a Finding with
        ``id="foundation.shadbala_phase1.<planet>"``.

    Raises:
        ValueError: if ``asc_sign`` is not in ``1..12``.
    """
    if not 1 <= asc_sign <= 12:
        raise ValueError(
            f"asc_sign must be in [1, 12], got {asc_sign!r}"
        )
    # ``is_daytime`` is reserved; touch it so type-checkers see the binding.
    _ = bool(is_daytime)

    out: dict[str, Finding] = {}
    for planet, entry in d1_chart.items():
        sign = entry.get("sign")
        if not isinstance(sign, int) or not (1 <= sign <= 12):
            continue
        lon = entry.get("longitude")
        if not isinstance(lon, (int, float)):
            lon = (sign - 1) * 30.0 + 15.0
        d9 = entry.get("d9_sign", sign)
        house = ((sign - asc_sign) % 12) + 1
        breakdown = shadbala_total(
            planet,
            longitude=float(lon),
            d1_sign=sign,
            d9_sign=d9,
            house=house,
            chart=d1_chart,
        )
        out[planet] = _planet_finding(planet, breakdown)
    return out


__all__ = [
    "compute_shadbala_phase1",
]
