"""Tier-0 primitive: Karakamsha Lagna.

Karakamsha Lagna is the **D9 (Navamsha) sign occupied by the Atmakaraka**
(highest-degree planet per the Jaimini chara-karaka ranking). It serves
as the secondary reference Lagna for Jaimini-school readings: Bhrigu's
"karakamsha rajayoga", Sanjay Rath's KarakAmsa methodology, and Step 19
of the Mahadasha judgment proforma (repeat-from-Karakamsha-Lagna).

Doctrine
========

Depends on **D-1** (karakas, 8-karaka Jaimini scheme — locked) for AK
identification. There is no separate doctrine lock for the
"AK-D9-sign = KarakAmsa" identity itself — this is the classical
definition (BPHS Vol.I Ch.34; reaffirmed throughout post-Parashari
Jaimini literature).

Algorithm
=========

    1. Identify the Atmakaraka via ``compute_karakas(d1_chart)``.
       The AK is the planet with the highest effective degree-within-sign
       (with the D-1 retrograde / Rahu inversion rules applied).
    2. Read the AK's sign in the D9 chart.
    3. That sign IS the Karakamsha Lagna.

Public API
==========

    compute_karakamsha(d1_chart, d9_chart) -> Finding

The returned Finding's ``evidence`` carries ``ak_planet=<name>`` and
``karakamsha_sign=<n>`` (1-indexed) so downstream sequences (notably
Step 19 of MD judgments) can read the sign machine-readably without
parsing the verdict string.

Usage
=====

    >>> from app.core.ephemeris_engine import calculate_all_charts
    >>> chart = calculate_all_charts(1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)
    >>> from app.reading.computations.karakamsha import compute_karakamsha
    >>> finding = compute_karakamsha(chart["d1"], chart["d9"])
    >>> finding.verdict
    'Karakamsha Lagna in Gemini (AK Sun in Gemini of D9)'
"""
from __future__ import annotations

import logging
from typing import Final

from app.reading.computations.karakas import compute_karakas
from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


_SIGN_NAMES: Final[tuple[str, ...]] = (
    "",  # 0-slot placeholder so 1-indexed lookup is direct
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


_PRIMITIVE_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


def _extract_ak_planet(d1_chart: dict) -> str:
    """Identify the Atmakaraka planet from the D1 chart.

    Uses ``compute_karakas`` so the D-1 doctrine lock (8-karaka mode,
    Rahu inversion, Ketu exclusion, retrograde inversion) is applied
    uniformly with the rest of the pipeline.
    """
    karakas = compute_karakas(d1_chart)
    ak_finding = karakas["atmakaraka"]
    for line in ak_finding.evidence:
        if line.startswith("planet="):
            return line.split("=", 1)[1]
    raise RuntimeError(
        "compute_karakas atmakaraka evidence missing 'planet=' line"
    )


def compute_karakamsha(d1_chart: dict, d9_chart: dict) -> Finding:
    """Compute the Karakamsha Lagna for the given D1 + D9 charts.

    Args:
        d1_chart: Natal D1 chart (planet -> position-dict).
        d9_chart: Navamsha D9 chart (planet -> position-dict). Each
            position dict must carry a 1-indexed ``sign`` field.

    Returns:
        A single Finding with ``id == "primitive.karakamsha.lagna"``
        whose verdict identifies the Karakamsha Lagna and whose
        ``evidence`` carries ``ak_planet=<name>`` and
        ``karakamsha_sign=<n>``.

    Raises:
        KeyError: AK planet missing from D9 chart.
        ValueError: AK planet's D9 entry has an invalid sign field.
    """
    ak_planet = _extract_ak_planet(d1_chart)

    if ak_planet not in d9_chart:
        raise KeyError(
            f"Atmakaraka {ak_planet!r} missing from D9 chart"
        )
    d9_entry = d9_chart[ak_planet]
    ak_d9_sign = d9_entry.get("sign")
    if not isinstance(ak_d9_sign, int) or not (1 <= ak_d9_sign <= 12):
        raise ValueError(
            f"Atmakaraka {ak_planet!r} D9 entry has invalid sign "
            f"{ak_d9_sign!r}"
        )

    # AK's D1 sign (for the human-readable verdict; not strictly needed
    # for the doctrine output).
    d1_entry = d1_chart.get(ak_planet, {})
    ak_d1_sign = d1_entry.get("sign") if isinstance(d1_entry, dict) else None
    ak_d1_sign_name = (
        _SIGN_NAMES[ak_d1_sign] if isinstance(ak_d1_sign, int)
        and 1 <= ak_d1_sign <= 12 else "?"
    )

    sign_name = _SIGN_NAMES[ak_d9_sign]
    verdict = (
        f"Karakamsha Lagna in {sign_name} (AK {ak_planet} in {sign_name} of D9)"
    )

    evidence = [
        f"ak_planet={ak_planet}",
        f"ak_d1_sign={ak_d1_sign}",
        f"ak_d1_sign_name={ak_d1_sign_name}",
        f"ak_d9_sign={ak_d9_sign}",
        f"ak_d9_sign_name={sign_name}",
        f"karakamsha_sign={ak_d9_sign}",
        f"karakamsha_sign_name={sign_name}",
        "doctrine=D-1 (jaimini_8_karaka_pvr) - karakas dependency",
    ]

    return Finding(
        id="primitive.karakamsha.lagna",
        rule="karakamsha",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict=verdict,
        evidence=evidence,
        confidence=_PRIMITIVE_CONFIDENCE,
    )


__all__ = ["compute_karakamsha"]
