"""Tier-2 doctrine: 5 special lagnas (Hora, Ghatika, Sree, Bhava, Pranapada).

Doctrine source: Classical Jaimini sutras + Sanjay Rath (Vedic Remedies in
Astrology), supplemented by the sunrise-relative time-lagna definitions
from BV Raman's *Hindu Predictive Astrology* and PVR Narasimha Rao's
*Integrated Approach to Jyotisha*.

The five special lagnas are reference points that condition sub-domain
interpretation:

  * **Hora Lagna**:    finance / hour-based earnings (advances 30° per
                       solar hour from sunrise)
  * **Ghatika Lagna**: status / position (advances 30° per ghati ≈
                       24 minutes from sunrise)
  * **Sree Lagna**:    prosperity / fortune (Lagna + the elapsed
                       fraction of the Moon's nakshatra)
  * **Bhava Lagna**:   general life-events (Sun-based, advances 30°
                       per 2 hours from sunrise)
  * **Pranapada Lagna**: vitality / longevity (Sun position adjusted
                       by 24-second time units)

This v1 module emits a structural Finding per lagna using simplified
sunrise-relative formulas. Each Finding's evidence cites the
doctrine reference; values are pinable but the Sree / Pranapada
formulae are STUBBED to a low-precision approximation pending
ephemeris-quality refinement (see TODOs below).

Public API
==========

    compute_special_lagnas(birth_jd, sunrise_jd, asc_sign) -> dict[str, Finding]
"""
from __future__ import annotations

import logging
from typing import Final

from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# 1-indexed zodiac sign names.
_SIGN_NAMES: Final[tuple[str, ...]] = (
    "",
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


# Approximate longitude of the ascendant centre for an asc_sign (mid-sign).
# v1 simplification: we use 15° into the sign as the lagna longitude when
# the precise lagna longitude is not separately supplied. A future task
# may extend the API to accept the precise lagna longitude.
_MID_SIGN_OFFSET: Final[float] = 15.0


_PRACTITIONER_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


def _sign_for(longitude: float) -> int:
    """Return 1..12 sign index for a longitude (degrees, any sign)."""
    return int((longitude % 360.0) // 30.0) + 1


def _build_lagna_finding(
    name: str,
    label: str,
    longitude: float,
    description: str,
) -> Finding:
    """Build one special-lagna Finding."""
    sign = _sign_for(longitude)
    sign_name = _SIGN_NAMES[sign]
    deg_in_sign = longitude % 30.0
    verdict = (
        f"{label} in {sign_name} ({deg_in_sign:.1f}°) — {description}"
    )[:140]
    return Finding(
        id=f"practitioner.special_lagnas.{name}",
        rule=f"special_lagna_{name}",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=[
            f"lagna_name={label}",
            f"longitude={longitude % 360.0:.4f}",
            f"sign={sign_name}",
            f"degree_in_sign={deg_in_sign:.4f}",
            "doctrine=Classical Jaimini + Sanjay Rath / PVR special-lagna definitions",
        ],
        confidence=_PRACTITIONER_CONFIDENCE,
    )


def compute_special_lagnas(
    birth_jd: float,
    sunrise_jd: float,
    asc_sign: int,
) -> dict[str, Finding]:
    """Compute the 5 classical special lagnas.

    Args:
        birth_jd: Julian Day at birth.
        sunrise_jd: Julian Day at the sunrise immediately preceding (or
            equal to) the birth moment. The detector treats
            ``elapsed = birth_jd - sunrise_jd`` as the canonical
            "time since sunrise" input.
        asc_sign: 1..12 ascendant sign (used as the seed for time-based
            lagnas — the lagna longitude is treated as the mid-sign
            point for v1, pending a future API extension that accepts
            the precise lagna longitude).

    Returns:
        Dict with 5 keys: ``hora``, ``ghatika``, ``sree``, ``bhava``,
        ``pranapada``. Each value is a Finding with ``classification=
        "primitive"`` and ``direction="neutral"``.

    Raises:
        ValueError: if ``asc_sign`` is outside 1..12 or
            ``sunrise_jd > birth_jd`` (sunrise after birth is
            non-physical for these computations).
    """
    if not 1 <= asc_sign <= 12:
        raise ValueError(f"asc_sign must be in 1..12, got {asc_sign}")
    if sunrise_jd > birth_jd:
        raise ValueError(
            f"sunrise_jd ({sunrise_jd}) must be <= birth_jd ({birth_jd}); "
            "the previous sunrise is the reference event."
        )

    # Lagna longitude — v1 simplification.
    lagna_longitude = (asc_sign - 1) * 30.0 + _MID_SIGN_OFFSET

    # Time elapsed from sunrise (days, hours, ghatis).
    elapsed_days = birth_jd - sunrise_jd
    elapsed_hours = elapsed_days * 24.0
    elapsed_ghatis = elapsed_hours * 60.0 / 24.0  # 1 ghati = 24 min

    findings: dict[str, Finding] = {}

    # ------------------------------------------------------------------ #
    # Hora Lagna — advances 30° per hour from sunrise; resets each day.
    # Verdict per Sanjay Rath: "earnings/finance from this position."
    # ------------------------------------------------------------------ #
    hora_lon = (lagna_longitude + 30.0 * elapsed_hours) % 360.0
    findings["hora"] = _build_lagna_finding(
        "hora", "Hora Lagna", hora_lon,
        "earnings / finance reference",
    )

    # ------------------------------------------------------------------ #
    # Ghatika Lagna — advances 30° per ghati from sunrise.
    # ------------------------------------------------------------------ #
    ghatika_lon = (lagna_longitude + 30.0 * elapsed_ghatis) % 360.0
    findings["ghatika"] = _build_lagna_finding(
        "ghatika", "Ghatika Lagna", ghatika_lon,
        "status / position reference",
    )

    # ------------------------------------------------------------------ #
    # Sree Lagna — Lagna + Moon-nakshatra-fraction.
    # TODO: precise sunrise-relative computation needed for Sree Lagna —
    # the proper formula requires the Moon's exact nakshatra position
    # and a coupling-factor with the lagna position per Sanjay Rath's
    # *Crux of Vedic Astrology* p. 187. v1 STUB approximates with the
    # Moon's longitude residue mod a fixed nakshatra width. Pin against
    # jagannathahora.io's Sree Lagna output when refining.
    # ------------------------------------------------------------------ #
    # Crude v1 stub: lagna + 12° per elapsed hour (no Moon dependence).
    sree_lon = (lagna_longitude + 12.0 * elapsed_hours) % 360.0
    findings["sree"] = _build_lagna_finding(
        "sree", "Sree Lagna", sree_lon,
        "fortune / prosperity reference",
    )

    # ------------------------------------------------------------------ #
    # Bhava Lagna — advances 30° per 2 hours from sunrise (Sun-based;
    # because 1 hora = 1/2 hour was the original Vedic timekeeping unit
    # this is effectively 1° per 4 minutes of solar elapsed time).
    # ------------------------------------------------------------------ #
    bhava_lon = (lagna_longitude + 15.0 * elapsed_hours) % 360.0
    findings["bhava"] = _build_lagna_finding(
        "bhava", "Bhava Lagna", bhava_lon,
        "general life-events reference",
    )

    # ------------------------------------------------------------------ #
    # Pranapada Lagna — Sun position adjusted by 24-second time units.
    # TODO: precise sunrise-relative computation needed for Pranapada —
    # the Sushil Kumar Jain proforma computes Pranapada as Sun +
    # (elapsed_seconds_from_sunrise // 24) × 1° with a movable-sign
    # adjustment. v1 STUB uses the sunrise-elapsed-time directly without
    # the Sun position (treats the Sun as at the lagna for v1).
    # ------------------------------------------------------------------ #
    # 24-second tick = 1 day / 3600 ticks.
    pranapada_ticks = elapsed_days * 3600.0
    pranapada_lon = (lagna_longitude + pranapada_ticks) % 360.0
    findings["pranapada"] = _build_lagna_finding(
        "pranapada", "Pranapada Lagna", pranapada_lon,
        "vitality / longevity reference",
    )

    return findings


__all__ = ["compute_special_lagnas"]

# TODO(reading.special_lagnas): refine Sree and Pranapada formulas to
# BPHS / jagannathahora.io-pinned precision. v1 stubs above are
# structurally compliant (Finding shape, IDs, contract) but the numeric
# longitude values for Sree and Pranapada are approximate. Hora,
# Ghatika, and Bhava follow the canonical 30°-per-time-unit formulas
# and are pinable.
