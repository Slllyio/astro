"""Tier-0 primitive: Arudha padas (A1..A12), Upapada Lagna, and UL2.

Doctrine lock - D-2 (``docs/doctrine-decisions.md``)
====================================================

The Arudha (also "Arudha pada", "pada-sign") of a bhava is the sign that
results from mirroring the bhava's lord through the bhava. The classical
recipe (BPHS Vol.I Ch.29 vv.4-5):

    1. Count from the bhava B to the bhava's lord's house position L.
    2. Apply the same count forward from L. That sign is the raw pada.
    3. Exception (Sanjay Rath, Crux of Vedic Astrology): if the raw pada
       lands in the **1st or 7th sign from the bhava itself** (the bhava's
       own sign, or directly opposite), shift the pada to the **10th
       house from itself**. This dissolves the degenerate "lord in own
       sign" and "lord in 7th" cases that classical commentators flag as
       inert.

This module applies the D-2 exception **uniformly** to A1..A12 and to UL,
UL2. (Note: A1 is the same as the Arudha Lagna, AL.)

Closed-form formula for the raw pada (equivalent to the count-and-step
recipe modulo 12):

    raw_pada_sign = ((2 * L_sign - B_sign - 1) mod 12) + 1

where L_sign is the (1-indexed) sign occupied by the bhava lord and
B_sign is the (1-indexed) bhava sign (= (asc_sign + bhava_idx - 2) mod 12 + 1).

Public API
==========

    compute_arudha_padas(d1_chart, asc_sign) -> dict[str, Finding]

Returns a dict keyed by the canonical pada short-name (``"al"`` for A1,
``"a2"`` ... ``"a12"``, ``"ul"`` for Upapada Lagna, ``"ul2"`` for the
second Upapada). Each Finding's ``evidence`` includes ``pada_sign=<N>``
(1-indexed) so downstream sequences can read the sign machine-readably
without re-parsing the verdict string.

Usage
=====

    >>> from app.core.ephemeris_engine import calculate_all_charts
    >>> chart = calculate_all_charts(1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)
    >>> from app.reading.computations.arudha_upapada import compute_arudha_padas
    >>> padas = compute_arudha_padas(chart["d1"], chart["ascendant"]["sign"])
    >>> padas["al"].verdict
    'Arudha Lagna in Taurus'
"""
from __future__ import annotations

import logging
from typing import Final

from app.core.dignity import SIGN_RULERS
from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


# Sign names (1-indexed: index 0 unused, names[1] = Aries .. names[12] = Pisces).
_SIGN_NAMES: Final[tuple[str, ...]] = (
    "",  # 0-slot placeholder so 1-indexed lookup is direct
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


# Canonical pada keys: A1 is aliased to "al" for ergonomic API surface.
_PADA_KEYS: Final[tuple[str, ...]] = (
    "al",                          # A1 (Arudha Lagna)
    "a2", "a3", "a4", "a5", "a6", "a7", "a8", "a9", "a10", "a11", "a12",
    "ul",                          # Upapada Lagna (= pada of 12th house)
    "ul2",                         # Secondary Upapada (= pada of 12th from UL)
)


# Pretty labels used in verdict strings.
_PADA_LABELS: Final[dict[str, str]] = {
    "al":  "Arudha Lagna",
    "a2":  "A2 (Arudha pada of 2nd)",
    "a3":  "A3 (Arudha pada of 3rd)",
    "a4":  "A4 (Arudha pada of 4th)",
    "a5":  "A5 (Arudha pada of 5th)",
    "a6":  "A6 (Arudha pada of 6th)",
    "a7":  "A7 (Arudha pada of 7th)",
    "a8":  "A8 (Arudha pada of 8th)",
    "a9":  "A9 (Arudha pada of 9th)",
    "a10": "A10 (Arudha pada of 10th)",
    "a11": "A11 (Arudha pada of 11th)",
    "a12": "A12 (Arudha pada of 12th)",
    "ul":  "Upapada Lagna",
    "ul2": "UL2 (Secondary Upapada)",
}


# 3-vote envelope: same shape as karakas — Arudha computation is purely
# geometric, no doctrine vote, so the score stays at 0.0 / band
# "indicative_only" until downstream sequences vote.
_PRIMITIVE_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


def _bhava_sign(asc_sign: int, bhava_index: int) -> int:
    """Return the (1-indexed) sign of the ``bhava_index``-th bhava from the
    ``asc_sign``-th-sign Lagna. ``bhava_index`` is 1..12."""
    return ((asc_sign - 1) + (bhava_index - 1)) % 12 + 1


def _planet_sign(d1_chart: dict, planet: str) -> int:
    """Read the 1-indexed sign of a planet from the D1 chart."""
    entry = d1_chart.get(planet)
    if entry is None:
        raise KeyError(f"planet {planet!r} missing from D1 chart")
    sign = entry.get("sign")
    if not isinstance(sign, int) or not (1 <= sign <= 12):
        raise ValueError(
            f"planet {planet!r} D1 entry has invalid sign {sign!r}"
        )
    return sign


def _raw_pada(bhava_sign: int, lord_sign: int) -> int:
    """Compute the raw Arudha pada sign before the D-2 exception.

    Closed form: P = ((2 * L - B - 1) mod 12) + 1 (1-indexed signs).
    """
    return ((2 * lord_sign - bhava_sign - 1) % 12) + 1


def _apply_d2_exception(
    bhava_sign: int, raw_pada_sign: int
) -> tuple[int, bool]:
    """Apply the D-2 (Sanjay Rath / BPHS Ch.29 vv.4-5) exception rule.

    If ``raw_pada_sign`` is in the **1st or 7th** from ``bhava_sign``
    (i.e. same sign or opposite), shift the pada to the **10th from
    itself**. Returns the (final_pada_sign, exception_fired) tuple.
    """
    # Relative house from bhava: 1..12.
    rel = ((raw_pada_sign - bhava_sign) % 12) + 1
    if rel == 1 or rel == 7:
        # Shift to 10th from pada.
        shifted = ((raw_pada_sign - 1 + 9) % 12) + 1
        return shifted, True
    return raw_pada_sign, False


def _compute_one_pada(
    d1_chart: dict, bhava_sign_value: int
) -> tuple[int, int, int, bool, str]:
    """Compute the Arudha pada for a single bhava-sign.

    Returns ``(final_sign, raw_sign, lord_sign, exception_fired, lord_name)``.
    Helper so UL/UL2 (which use synthetic bhava signs rather than the
    asc-derived ones) share the logic.
    """
    lord_name = SIGN_RULERS[bhava_sign_value]
    lord_sign = _planet_sign(d1_chart, lord_name)
    raw = _raw_pada(bhava_sign_value, lord_sign)
    final, fired = _apply_d2_exception(bhava_sign_value, raw)
    return final, raw, lord_sign, fired, lord_name


def _build_finding(
    key: str,
    bhava_index_label: str,
    bhava_sign_value: int,
    final_sign: int,
    raw_sign: int,
    lord_name: str,
    lord_sign: int,
    exception_fired: bool,
) -> Finding:
    """Construct the Finding for one pada slot."""
    label = _PADA_LABELS[key]
    final_sign_name = _SIGN_NAMES[final_sign]
    raw_sign_name = _SIGN_NAMES[raw_sign]
    lord_sign_name = _SIGN_NAMES[lord_sign]
    verdict = f"{label} in {final_sign_name}"

    evidence = [
        f"pada_key={key}",
        f"pada_sign={final_sign}",
        f"pada_sign_name={final_sign_name}",
        f"bhava={bhava_index_label}",
        f"bhava_sign={bhava_sign_value}",
        f"bhava_sign_name={_SIGN_NAMES[bhava_sign_value]}",
        f"bhava_lord={lord_name}",
        f"bhava_lord_sign={lord_sign}",
        f"bhava_lord_sign_name={lord_sign_name}",
        f"raw_pada_sign={raw_sign}",
        f"raw_pada_sign_name={raw_sign_name}",
        f"d2_exception_fired={exception_fired}",
        "doctrine=D-2 (1_7_to_10)",
    ]

    return Finding(
        id=f"primitive.arudha.{key}",
        rule="arudha_upapada",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=evidence,
        confidence=_PRIMITIVE_CONFIDENCE,
    )


def compute_arudha_padas(d1_chart: dict, asc_sign: int) -> dict[str, Finding]:
    """Compute A1..A12, UL, and UL2 as Findings.

    Args:
        d1_chart: Natal D1 chart mapping ``planet_name -> position_dict``.
            Each position dict must carry a 1-indexed ``sign`` field.
            (``app.core.ephemeris_engine.calculate_all_charts`` produces
            the expected shape.)
        asc_sign: 1-indexed Ascendant sign (1 = Aries .. 12 = Pisces).

    Returns:
        Dict keyed by canonical pada short-name (``"al"``, ``"a2"`` ...
        ``"a12"``, ``"ul"``, ``"ul2"``). Each value is a Finding with
        ``id == "primitive.arudha.<key>"`` and ``pada_sign=<n>`` in
        ``evidence`` so downstream consumers can read the sign without
        parsing the verdict.

    Raises:
        ValueError: ``asc_sign`` out of 1..12 range.
        KeyError: a required bhava-lord planet missing from ``d1_chart``.
    """
    if not isinstance(asc_sign, int) or not (1 <= asc_sign <= 12):
        raise ValueError(
            f"asc_sign must be a 1-indexed sign in 1..12, got {asc_sign!r}"
        )

    findings: dict[str, Finding] = {}

    # A1..A12 (where A1 == AL).
    for bhava_index in range(1, 13):
        key = "al" if bhava_index == 1 else f"a{bhava_index}"
        bhava_sig = _bhava_sign(asc_sign, bhava_index)
        final, raw, lord_sign, fired, lord_name = _compute_one_pada(
            d1_chart, bhava_sig
        )
        findings[key] = _build_finding(
            key=key,
            bhava_index_label=str(bhava_index),
            bhava_sign_value=bhava_sig,
            final_sign=final,
            raw_sign=raw,
            lord_name=lord_name,
            lord_sign=lord_sign,
            exception_fired=fired,
        )

    # UL == A12 by definition (Pada of the 12th house). We re-emit it
    # under the "ul" key so downstream code that asks for UL specifically
    # finds it without alias hunting.
    a12 = findings["a12"]
    ul_pada_sign = int(
        next(line for line in a12.evidence if line.startswith("pada_sign="))
        .split("=", 1)[1]
    )
    ul_bhava_sign = int(
        next(line for line in a12.evidence if line.startswith("bhava_sign="))
        .split("=", 1)[1]
    )
    ul_lord = next(
        line for line in a12.evidence if line.startswith("bhava_lord=")
    ).split("=", 1)[1]
    ul_lord_sign = int(
        next(line for line in a12.evidence
             if line.startswith("bhava_lord_sign=")).split("=", 1)[1]
    )
    ul_raw = int(
        next(line for line in a12.evidence
             if line.startswith("raw_pada_sign=")).split("=", 1)[1]
    )
    ul_fired = (
        next(line for line in a12.evidence
             if line.startswith("d2_exception_fired=")).split("=", 1)[1]
        == "True"
    )
    findings["ul"] = _build_finding(
        key="ul",
        bhava_index_label="12 (Upapada)",
        bhava_sign_value=ul_bhava_sign,
        final_sign=ul_pada_sign,
        raw_sign=ul_raw,
        lord_name=ul_lord,
        lord_sign=ul_lord_sign,
        exception_fired=ul_fired,
    )

    # UL2 = the Arudha pada of the 12th-from-UL. Per Sanjay Rath, this is
    # the second-marriage indicator; it applies the standard Arudha
    # algorithm to a synthetic bhava whose sign is the 12th from UL.
    ul2_bhava_sign = ((ul_pada_sign - 1) + 11) % 12 + 1   # 12th from UL
    ul2_final, ul2_raw, ul2_lord_sign, ul2_fired, ul2_lord = _compute_one_pada(
        d1_chart, ul2_bhava_sign
    )
    findings["ul2"] = _build_finding(
        key="ul2",
        bhava_index_label="12 from UL (Secondary Upapada)",
        bhava_sign_value=ul2_bhava_sign,
        final_sign=ul2_final,
        raw_sign=ul2_raw,
        lord_name=ul2_lord,
        lord_sign=ul2_lord_sign,
        exception_fired=ul2_fired,
    )

    # Sanity: invariant ordering matches the public contract.
    if set(findings.keys()) != set(_PADA_KEYS):
        # Defensive — should be impossible by construction.
        missing = set(_PADA_KEYS) - set(findings.keys())
        extra = set(findings.keys()) - set(_PADA_KEYS)
        raise RuntimeError(
            f"arudha pada key mismatch: missing={missing!r} extra={extra!r}"
        )

    return findings


__all__ = ["compute_arudha_padas"]
