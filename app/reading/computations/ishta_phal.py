"""Tier-0 primitive: Ishta Phal & Kashta Phal (BPHS Ch.47 v.3).

Doctrine lock - D-4 (``docs/doctrine-decisions.md``)
====================================================

Use the **BPHS Ch.47 v.3 formula**:

    Ishta_Phal  = sqrt(Cheshta_bala * Uchcha_bala)
    Kashta_Phal = 60 - Ishta_Phal

Both Cheshta_bala and Uchcha_bala are taken in their Shadbala "Rupa"
form (i.e. on the 60-point virupa scale). The Phaladeepika alternative
(substituting Saptavargaja_bala for Uchcha_bala) is computed in parallel
elsewhere (``computations/dispute_surfacing.py``) and surfaced as a
report-only dispute when the two formulas disagree by more than 10
virupa on a planet of interest. See D-4 lockfile entry for rationale.

Hard invariants
===============

    ishta + kashta = 60.0 (within float epsilon)
    ishta in [0, 60]
    kashta in [0, 60]

Graceful degradation
====================

The Cheshta-bala precursor lives in ``app.core.shadbala``; if a caller
hasn't computed it yet (or the chart's Sun/Moon entry naturally yields
Cheshta=0 by classical convention), this module still emits a Finding.
When Cheshta is **missing entirely** from the input dict (no 'cheshta'
key), the Finding is emitted with ``direction="neutral"`` and a verdict
that flags the pending precursor — never raises.

Public API
==========

    def compute_ishta_phal(
        d1_chart: dict,
        shadbala_components: dict[str, dict[str, float]],
    ) -> dict[str, Finding]

``shadbala_components`` is a dict keyed by planet name mapping to a
sub-dict carrying ``cheshta`` and ``uchcha`` Rupa values. Callers
typically build this from ``app.core.shadbala``:

    from app.core.shadbala import cheshta_bala, uchcha_bala
    comps = {
        p: {
            "cheshta": cheshta_bala(p, e.get("is_retrograde", False)),
            "uchcha":  uchcha_bala(p, e["longitude"]),
        }
        for p, e in d1_chart.items() if p != "Ketu"  # nodes optional
    }

Direction
=========

    ishta > 30                  -> direction = "positive" (favorable)
    kashta > 30                 -> direction = "negative" (unfavorable)
    otherwise (ishta == kashta == 30 boundary)  -> "neutral"
"""
from __future__ import annotations

import logging
import math
from typing import Final

from app.reading.schema import ConfidenceScore, Finding

logger = logging.getLogger(__name__)


_PRIMITIVE_CONFIDENCE: Final[ConfidenceScore] = ConfidenceScore(
    score=0.0,
    votes={"house": False, "lord": False, "karaka": False},
    band="indicative_only",
)


def _natal_planets_for_ishta(d1_chart: dict) -> list[str]:
    """Return the natal planet set we will score.

    Classical Ishta_Phal applies to the seven natural planets. Rahu/Ketu
    are included only if present in the input shadbala_components (most
    callers will omit them since classical Cheshta_bala for the nodes is
    nil).
    """
    candidates = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
    return [p for p in candidates if p in d1_chart]


def _make_finding(
    planet: str,
    ishta: float,
    kashta: float,
    cheshta: float | None,
    uchcha: float | None,
    pending_cheshta: bool,
) -> Finding:
    """Build the per-planet Finding."""
    if pending_cheshta:
        verdict = f"{planet} Ishta Phal pending Cheshta-bala (Shadbala Phase 1)"
        direction = "neutral"
    else:
        verdict = (
            f"{planet} Ishta={ishta:.2f}, Kashta={kashta:.2f} "
            f"({'favorable' if ishta > 30 else 'unfavorable' if kashta > 30 else 'balanced'})"
        )
        if ishta > 30.0:
            direction = "positive"
        elif kashta > 30.0:
            direction = "negative"
        else:
            direction = "neutral"

    evidence = [
        f"planet={planet}",
        f"ishta={ishta:.6f}",
        f"kashta={kashta:.6f}",
        f"cheshta={cheshta if cheshta is not None else 'missing'}",
        f"uchcha={uchcha if uchcha is not None else 'missing'}",
        f"pending_cheshta={pending_cheshta}",
        "doctrine=D-4 (bphs_47_3, ishta = sqrt(cheshta * uchcha))",
    ]

    return Finding(
        id=f"primitive.ishta_phal.{planet.lower()}",
        rule="ishta_phal",
        source_sequence=None,
        classification="primitive",
        direction=direction,
        verdict=verdict,
        evidence=evidence,
        confidence=_PRIMITIVE_CONFIDENCE,
    )


def compute_ishta_phal(
    d1_chart: dict,
    shadbala_components: dict,
) -> dict[str, Finding]:
    """Compute Ishta_Phal & Kashta_Phal per planet (BPHS Ch.47 v.3).

    Args:
        d1_chart: Natal D1 chart (planet -> position dict). Used to
            enumerate the natal planet set.
        shadbala_components: Dict keyed by planet name. Each value is a
            sub-dict expected to carry ``cheshta`` (float, 0..60) and
            ``uchcha`` (float, 0..60) Rupa values. If a planet's
            ``cheshta`` key is missing entirely, the Finding is emitted
            with ``direction="neutral"`` and a "pending Cheshta-bala"
            verdict per the D-4 graceful-degradation rule.

    Returns:
        Dict keyed by planet name. Each value is a Finding with
        ``id == "primitive.ishta_phal.<planet_lowercase>"`` and
        ``evidence`` carrying ``ishta=<float>``, ``kashta=<float>``,
        ``cheshta=<value>``, ``uchcha=<value>``,
        ``pending_cheshta=<bool>``.

    Raises:
        TypeError: if ``shadbala_components`` is not a dict.
    """
    if not isinstance(shadbala_components, dict):
        raise TypeError(
            f"shadbala_components must be a dict, got "
            f"{type(shadbala_components).__name__}"
        )

    findings: dict[str, Finding] = {}
    for planet in _natal_planets_for_ishta(d1_chart):
        comps = shadbala_components.get(planet)
        if not isinstance(comps, dict):
            comps = {}

        cheshta_raw = comps.get("cheshta")
        uchcha_raw = comps.get("uchcha")

        # Pending-Cheshta path: emit a neutral Finding without computing.
        # (We treat *missing* cheshta as pending; cheshta=0.0 explicitly
        # is a valid result for Sun/Moon and triggers the normal path.)
        if cheshta_raw is None:
            findings[planet] = _make_finding(
                planet=planet,
                ishta=0.0,
                kashta=60.0,
                cheshta=None,
                uchcha=uchcha_raw if isinstance(uchcha_raw, (int, float)) else None,
                pending_cheshta=True,
            )
            continue

        try:
            cheshta = float(cheshta_raw)
        except (TypeError, ValueError):
            logger.warning(
                "ishta_phal: %s has non-numeric cheshta=%r; treating as missing",
                planet, cheshta_raw,
            )
            findings[planet] = _make_finding(
                planet=planet,
                ishta=0.0,
                kashta=60.0,
                cheshta=None,
                uchcha=None,
                pending_cheshta=True,
            )
            continue

        try:
            uchcha = float(uchcha_raw) if uchcha_raw is not None else 0.0
        except (TypeError, ValueError):
            logger.warning(
                "ishta_phal: %s has non-numeric uchcha=%r; defaulting to 0.0",
                planet, uchcha_raw,
            )
            uchcha = 0.0

        # Defensive clamp: BPHS formula requires non-negative inputs.
        cheshta_clamped = max(0.0, cheshta)
        uchcha_clamped = max(0.0, uchcha)
        # Cap at 60 -- the maximum virupa for either component.
        cheshta_clamped = min(60.0, cheshta_clamped)
        uchcha_clamped = min(60.0, uchcha_clamped)

        ishta = math.sqrt(cheshta_clamped * uchcha_clamped)
        # Cap defensively to 60 (mathematically already true given the
        # clamps above, but keeps the invariant explicit in the code).
        ishta = max(0.0, min(60.0, ishta))
        kashta = 60.0 - ishta

        findings[planet] = _make_finding(
            planet=planet,
            ishta=ishta,
            kashta=kashta,
            cheshta=cheshta,
            uchcha=uchcha,
            pending_cheshta=False,
        )

    return findings


__all__ = ["compute_ishta_phal"]
