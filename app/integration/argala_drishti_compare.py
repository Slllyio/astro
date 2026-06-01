"""Cross-engine Argala + Drishti comparator.

Track A (``app.reading.computations.argala`` + ``jaimini_drishti``) and
Track B (``app.core.drishti_argala``) independently compute Jaimini
argala (intervention/blocking aspects) and rasi drishti (sign aspects)
per house and per planet.

Two diff axes:

1. **Drishti**: which signs aspect which other signs. Both engines
   should encode the same Jaimini rule (each sign aspects 5 specific
   other signs based on its category).

2. **Argala**: which houses cause argala on which bhavas. Track B
   reports ``ArgalaSource(focal_bhava, argala_house, distance, kind,
   causing_planets)`` per bhava; Track A emits per-bhava Findings whose
   evidence contains the relevant argala-causing planets.

The comparator anchors on the per-bhava CAUSING-PLANET SET — for each
bhava 1..12, does the SAME set of planets cause argala under both
engines? Disagreement implies a doctrine drift in argala rules.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.drishti_argala import argala_report

# Planet names to scan for in Track A's evidence text.
_PLANETS = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter",
    "Venus", "Saturn", "Rahu", "Ketu",
)


class ArgalaPerBhavaDiff(BaseModel):
    """Per-bhava argala-source comparison."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    bhava: int = Field(ge=1, le=12)
    track_a_causing_planets: list[str]
    track_b_causing_planets: list[str]
    intersection: list[str]
    only_in_a: list[str]
    only_in_b: list[str]
    agrees: bool


class ArgalaDrishtiComparisonReport(BaseModel):
    """Aggregate Argala+Drishti comparator output."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    track_a_engine: str = "app.reading.computations.argala + jaimini_drishti"
    track_b_engine: str = "app.core.drishti_argala"

    per_bhava: list[ArgalaPerBhavaDiff]
    full_agreement: bool
    agreement_count: int
    disagreement_count: int
    verdict_summary: str


def _extract_planets_from_evidence(evidence: list[str]) -> set[str]:
    """Scan a Finding's evidence strings for canonical planet names."""
    text = " ".join(evidence)
    return {p for p in _PLANETS if re.search(rf"\b{re.escape(p)}\b", text)}


def _track_a_per_bhava_planets(reading: dict[str, Any]) -> dict[int, set[str]]:
    """Walk reading for argala-classified findings and extract per-bhava
    causing-planet sets from each Finding's evidence."""
    out: dict[int, set[str]] = {b: set() for b in range(1, 13)}

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            rule = node.get("rule", "") or ""
            if isinstance(rule, str) and "argala" in rule.lower():
                # Try to extract bhava number from rule or id
                bhava_match = re.search(r"(?:bhava|house|h)[._]?(\d{1,2})", rule.lower())
                if not bhava_match:
                    # Look in id
                    id_val = node.get("id", "") or ""
                    if isinstance(id_val, str):
                        bhava_match = re.search(r"(\d{1,2})", id_val)
                if bhava_match:
                    bhava = int(bhava_match.group(1))
                    if 1 <= bhava <= 12:
                        ev = node.get("evidence") or []
                        if isinstance(ev, list):
                            out[bhava].update(
                                _extract_planets_from_evidence([str(x) for x in ev])
                            )
            for v in node.values():
                _walk(v)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(reading)
    return out


def compare_argala_drishti(reading: dict[str, Any]) -> ArgalaDrishtiComparisonReport:
    """Diff per-bhava argala causing-planet sets between Track A and Track B.

    Track A is read out of the reading (no re-computation needed). Track B
    is invoked fresh via ``argala_report(planet_houses)``.
    """
    planets_block = (reading.get("chart") or {}).get("planets") or {}
    planet_houses: dict[str, int] = {
        name: int(body["house"])
        for name, body in planets_block.items()
        if isinstance(body, dict) and "house" in body
    }

    a_per_bhava = _track_a_per_bhava_planets(reading)

    b_report = argala_report(planet_houses)
    b_per_bhava: dict[int, set[str]] = {b: set() for b in range(1, 13)}
    for bhava, sources in b_report.items():
        for source in sources:
            b_per_bhava[int(bhava)].update(source.causing_planets)

    per_bhava: list[ArgalaPerBhavaDiff] = []
    agreement_count = 0
    disagreement_count = 0

    for bhava in range(1, 13):
        a_set = a_per_bhava.get(bhava, set())
        b_set = b_per_bhava.get(bhava, set())
        intersection = sorted(a_set & b_set)
        only_a = sorted(a_set - b_set)
        only_b = sorted(b_set - a_set)
        agrees = a_set == b_set
        if agrees:
            agreement_count += 1
        else:
            disagreement_count += 1
        per_bhava.append(ArgalaPerBhavaDiff(
            bhava=bhava,
            track_a_causing_planets=sorted(a_set),
            track_b_causing_planets=sorted(b_set),
            intersection=intersection,
            only_in_a=only_a,
            only_in_b=only_b,
            agrees=agrees,
        ))

    full_agreement = disagreement_count == 0

    summary = (
        f"FULL AGREEMENT on argala across all 12 bhavas"
        if full_agreement
        else f"agreements={agreement_count}/12 bhavas, disagreements={disagreement_count}"
    )

    return ArgalaDrishtiComparisonReport(
        per_bhava=per_bhava,
        full_agreement=full_agreement,
        agreement_count=agreement_count,
        disagreement_count=disagreement_count,
        verdict_summary=summary,
    )
