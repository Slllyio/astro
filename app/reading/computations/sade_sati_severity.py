"""Tier-2 doctrine: Sade Sati severity scoring (SAV-modulated).

Doctrine source: Classical Parashari Sade Sati definition (Saturn
transiting 12th/1st/2nd from natal Moon) + Sarvashtakavarga modulation
per K.N. Rao's predictive school and Sanjay Rath's *Vedic Remedies in
Astrology* (Saturn-remedies chapter).

Sade Sati is the ~7.5-year period when transit Saturn occupies the 12th,
1st (PEAK), or 2nd from the natal Moon. The phase alone is a coarse
qualifier — practitioners use the Sarvashtakavarga (SAV) bindu count
on the rashi Saturn currently transits to refine severity:

  +------------------------------------------------+----------+
  | Condition                                      | Severity |
  +================================================+==========+
  | SAV >= 30 AND natal Saturn is benefic in       | mild     |
  | functional terms                               |          |
  +------------------------------------------------+----------+
  | SAV >= 30 AND natal Saturn NOT functional      | moderate |
  | benefic                                        |          |
  +------------------------------------------------+----------+
  | 25 <= SAV < 30 (any natal Saturn)              | moderate |
  +------------------------------------------------+----------+
  | SAV < 25 AND phase == PEAK                     | severe   |
  +------------------------------------------------+----------+
  | SAV < 25 AND phase != PEAK (Rising or Setting) | moderate |
  +------------------------------------------------+----------+

When not in Sade Sati at all: a single neutral Finding is emitted
("Sade Sati inactive — transit Saturn at ...") so the downstream
consumer always gets a deterministic shape.

Public API
==========

    compute_sade_sati_severity(d1_chart, asc_sign, transit_saturn_sign) -> Finding

Phase detection delegates to ``app.core.sade_sati.is_in_sade_sati``;
the SAV vector comes from ``app.core.ashtakavarga.compute_ashtakavarga``;
the functional-nature check uses ``app.reading.computations.functional_nature``.
"""
from __future__ import annotations

import logging
from typing import Final, Literal, Mapping

from app.core.ashtakavarga import compute_ashtakavarga
from app.core.sade_sati import SadeSatiPhase, is_in_sade_sati
from app.reading.computations.functional_nature import (
    compute_functional_nature,
)
from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


_SIGN_NAMES: Final[tuple[str, ...]] = (
    "",
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


# SAV thresholds (K.N. Rao predictive matrix).
_SAV_BENEFIC_FLOOR: Final[int] = 30
_SAV_MODERATE_FLOOR: Final[int] = 25


# Practitioner confidence envelope (single deterministic lookup).
_PRACTITIONER_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


def _severity(
    sav: int, phase: SadeSatiPhase, saturn_is_benefic: bool,
) -> Literal["mild", "moderate", "severe"]:
    """Apply the severity matrix."""
    if sav >= _SAV_BENEFIC_FLOOR:
        return "mild" if saturn_is_benefic else "moderate"
    if sav >= _SAV_MODERATE_FLOOR:
        return "moderate"
    # sav < 25
    if phase == SadeSatiPhase.PEAK:
        return "severe"
    return "moderate"


def _natal_saturn_is_benefic(asc_sign: int) -> bool:
    """True iff natal Saturn is a functional benefic / yogakaraka for the
    given ascendant (per D-7)."""
    natures = compute_functional_nature(asc_sign=asc_sign)
    saturn_nature_evidence = next(
        (e for e in natures["Saturn"].evidence if e.startswith("nature=")),
        None,
    )
    if saturn_nature_evidence is None:
        # Fallback: parse the verdict.
        verdict_lower = natures["Saturn"].verdict.lower()
        return ("yogakaraka" in verdict_lower) or ("benefic" in verdict_lower)
    nature_value = saturn_nature_evidence.split("=", 1)[1]
    return nature_value in {"yogakaraka", "functional_benefic"}


def _inactive_finding(
    transit_saturn_sign: int, natal_moon_sign: int,
) -> Finding:
    """The neutral 'not currently in Sade Sati' Finding."""
    sign_name = _SIGN_NAMES[transit_saturn_sign]
    moon_sign_name = _SIGN_NAMES[natal_moon_sign]
    verdict = (
        f"Sade Sati inactive — transit Saturn in {sign_name}, "
        f"natal Moon in {moon_sign_name}"
    )[:140]
    return Finding(
        id="practitioner.sade_sati.current",
        rule="sade_sati_severity",
        source_sequence=None,
        classification="trigger",
        direction="neutral",
        verdict=verdict,
        evidence=[
            "phase=none",
            f"transit_saturn_sign={transit_saturn_sign}",
            f"natal_moon_sign={natal_moon_sign}",
            "doctrine=Classical Parashari Sade Sati (whole-sign 12/1/2 from natal Moon)",
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def _active_finding(
    phase: SadeSatiPhase,
    sav: int,
    severity: str,
    transit_saturn_sign: int,
    natal_moon_sign: int,
    saturn_is_benefic: bool,
) -> Finding:
    """Active Sade Sati Finding."""
    phase_label = phase.value.title()  # "Rising"/"Peak"/"Setting"
    sign_name = _SIGN_NAMES[transit_saturn_sign]
    verdict = (
        f"Sade Sati {phase_label} phase in {sign_name}, SAV={sav}, "
        f"severity={severity}"
    )[:140]
    return Finding(
        id="practitioner.sade_sati.current",
        rule="sade_sati_severity",
        source_sequence=None,
        classification="trigger",
        direction="negative",
        verdict=verdict,
        evidence=[
            f"phase={phase.value}",
            f"sav_bindus={sav}",
            f"severity={severity}",
            f"natal_saturn_functional_benefic={saturn_is_benefic}",
            f"transit_saturn_sign={transit_saturn_sign}",
            f"natal_moon_sign={natal_moon_sign}",
            "doctrine=K.N. Rao SAV-modulated Sade Sati severity matrix",
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def compute_sade_sati_severity(
    d1_chart: Mapping[str, Mapping[str, object]],
    asc_sign: int,
    transit_saturn_sign: int,
) -> Finding:
    """Compute current Sade Sati state + severity for a chart.

    Args:
        d1_chart: Mapping {planet_name: planet_record}. Must contain at
            least the 7 BAV-contributing planets (Sun..Saturn) with
            ``sign`` fields, plus a ``Moon`` entry (which is among the
            7). Rahu/Ketu may be absent.
        asc_sign: 1..12 ascendant sign.
        transit_saturn_sign: 1..12 sign of transit Saturn at the
            evaluation moment.

    Returns:
        A single Finding with ``id="practitioner.sade_sati.current"``.
        - ``direction="neutral"`` and a benign verdict when Sade Sati is
          inactive.
        - ``direction="negative"`` with severity (mild/moderate/severe)
          recorded in both verdict and evidence when active.

    Raises:
        ValueError: if ``asc_sign`` or ``transit_saturn_sign`` is out of
            1..12, or if ``d1_chart`` is missing the natal Moon.
    """
    if not 1 <= asc_sign <= 12:
        raise ValueError(f"asc_sign must be in 1..12, got {asc_sign}")
    if not 1 <= transit_saturn_sign <= 12:
        raise ValueError(
            f"transit_saturn_sign must be in 1..12, got {transit_saturn_sign}"
        )

    moon_record = d1_chart.get("Moon")
    if moon_record is None:
        raise ValueError("d1_chart missing 'Moon' entry — cannot compute Sade Sati")
    natal_moon_sign = int(moon_record["sign"])  # type: ignore[arg-type]
    if not 1 <= natal_moon_sign <= 12:
        raise ValueError(
            f"natal Moon sign must be 1..12, got {natal_moon_sign}"
        )

    info = is_in_sade_sati(transit_saturn_sign, natal_moon_sign)
    if info is None:
        return _inactive_finding(transit_saturn_sign, natal_moon_sign)

    # Active branch: compute SAV at the transit-Saturn sign.
    # The transit_saturn_sign is 1-indexed; the SAV vector is 0-indexed.
    ashtakavarga = compute_ashtakavarga(
        d1_chart, {"sign": asc_sign},
    )
    sav_vector = ashtakavarga["sav"]
    sav_value = int(sav_vector[transit_saturn_sign - 1])

    saturn_is_benefic = _natal_saturn_is_benefic(asc_sign)
    severity = _severity(sav_value, info["phase"], saturn_is_benefic)

    return _active_finding(
        info["phase"], sav_value, severity,
        transit_saturn_sign, natal_moon_sign, saturn_is_benefic,
    )


__all__ = ["compute_sade_sati_severity"]
