"""Cross-engine Shadbala comparator.

Both Track A (``app.reading.computations.shadbala_phase1.compute_shadbala_phase1``)
and Track B (``app.core.shadbala_report.compute_shadbala``) compute the
six-fold strength of each planet (Sthana, Dig, Kala, Cheshta, Naisargika,
Drik). Their internal sub-calculations differ — Track A emits Findings
with strength bands ("strong"/"medium"/"weak"); Track B emits numeric
``total_virupa`` scores.

This comparator anchors on the strength CLASSIFICATION (whether a planet
is "sufficiently strong") because that's the load-bearing downstream
question — both engines have notions of strong/weak and both apply
classical thresholds.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.shadbala_report import compute_shadbala, is_sufficiently_strong
from app.integration.gap_annotator import chart_from_reading
from app.reading.computations.shadbala_phase1 import compute_shadbala_phase1


_CLASSICAL_7 = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")


class PlanetShadbalaDiff(BaseModel):
    """Per-planet Shadbala agreement record."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    planet: str
    track_a_strength_band: str | None
    track_a_direction: str | None
    track_b_total_virupa: float | None
    track_b_is_sufficiently_strong: bool | None
    track_b_above_minimum: dict[str, float] | None = None
    classification_aligns: bool | None  # whether "strong" verdict matches


class ShadbalaComparisonReport(BaseModel):
    """Aggregate Shadbala comparator output."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    track_a_engine: str = "app.reading.computations.shadbala_phase1"
    track_b_engine: str = "app.core.shadbala_report"

    per_planet: list[PlanetShadbalaDiff]
    track_a_strong_planets: list[str]
    track_b_strong_planets: list[str]
    classifications_in_agreement: int
    classifications_in_disagreement: int
    track_b_strongest: str | None
    track_b_weakest: str | None

    verdict_summary: str


def _extract_track_a_strength(finding: Any) -> tuple[str | None, str | None]:
    """Extract (band, direction) from a Track-A Finding dataclass or dict.

    Track A's Phase 1 emits Findings with verdict strings like
    "Sun has strong Shadbala (rupas: 6.8)" — we read the structured
    direction and the band from confidence.band if available."""
    if finding is None:
        return None, None
    direction = getattr(finding, "direction", None)
    if direction is None and isinstance(finding, dict):
        direction = finding.get("direction")
    confidence = getattr(finding, "confidence", None)
    if confidence is None and isinstance(finding, dict):
        confidence = finding.get("confidence")
    band = None
    if confidence is not None:
        band = getattr(confidence, "band", None)
        if band is None and isinstance(confidence, dict):
            band = confidence.get("band")
    return band, direction


def compare_shadbala(reading: dict[str, Any]) -> ShadbalaComparisonReport:
    """Diff Track A vs Track B Shadbala on the same reading.

    Track A's compute_shadbala_phase1 needs ``d1_chart`` shape (planet→
    position dict with sign/longitude/is_retrograde). The reading dict
    has ``chart.planets`` in the same shape.
    Track B's compute_shadbala needs a ``Chart`` object — we build it
    via ``chart_from_reading``."""
    chart_block = reading.get("chart") or {}
    planets = chart_block.get("planets") or {}
    asc_sign = (chart_block.get("cusps") or {}).get("sign")
    extras = chart_block.get("extras") or {}
    is_daytime = bool(extras.get("is_daytime", True))

    if asc_sign is None:
        raise ValueError("reading.chart.cusps.sign missing")

    a_findings = compute_shadbala_phase1(planets, int(asc_sign), is_daytime)

    chart_b = chart_from_reading(reading)
    b_report = compute_shadbala(chart_b)
    b_per_planet = dict(b_report.per_planet)

    per_planet: list[PlanetShadbalaDiff] = []
    a_strong: list[str] = []
    b_strong: list[str] = []
    aligned = 0
    misaligned = 0

    for planet in _CLASSICAL_7:
        a_finding = a_findings.get(planet)
        a_band, a_direction = _extract_track_a_strength(a_finding)
        b_record = b_per_planet.get(planet)
        b_strong_flag = is_sufficiently_strong(planet, chart_b) if b_record else None
        b_total = float(b_record.total_virupa) if b_record else None

        # Track A says strong when band in {"high", "very_strong"}
        # OR direction == "positive". We use direction as primary signal.
        a_strong_flag: bool | None
        if a_direction is None:
            a_strong_flag = None
        else:
            a_strong_flag = a_direction == "positive"

        if a_strong_flag:
            a_strong.append(planet)
        if b_strong_flag:
            b_strong.append(planet)

        aligns: bool | None
        if a_strong_flag is None or b_strong_flag is None:
            aligns = None
        else:
            aligns = a_strong_flag == b_strong_flag
            if aligns:
                aligned += 1
            else:
                misaligned += 1

        per_planet.append(PlanetShadbalaDiff(
            planet=planet,
            track_a_strength_band=a_band,
            track_a_direction=a_direction,
            track_b_total_virupa=b_total,
            track_b_is_sufficiently_strong=b_strong_flag,
            classification_aligns=aligns,
        ))

    summary = (
        f"aligned={aligned}/7 (mis={misaligned}); "
        f"B strongest={b_report.strongest}, B weakest={b_report.weakest}"
    )

    return ShadbalaComparisonReport(
        per_planet=per_planet,
        track_a_strong_planets=a_strong,
        track_b_strong_planets=b_strong,
        classifications_in_agreement=aligned,
        classifications_in_disagreement=misaligned,
        track_b_strongest=b_report.strongest,
        track_b_weakest=b_report.weakest,
        verdict_summary=summary,
    )
