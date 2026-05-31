"""Cross-engine yoga-detection comparator.

Track A (``app.reading.computations.yogas_extended.*``) and Track B
(``app.core.yoga_library``) independently detect classical yogas
(Lakshmi, Gajakesari, Mangal Dosha, etc.). They use different detection
implementations and slightly different yoga sets.

This comparator does a symmetric-difference diff between the two yoga
sets for the same chart and surfaces:
- Yogas BOTH engines detect (agreement)
- Yogas only Track A detects (Track B miss)
- Yogas only Track B detects (Track A miss)

Naming normalisation
--------------------
Track A uses lowercase-underscored rule IDs like
``yogas_extended.lakshmi`` or ``foundation.gajakesari``; Track B uses
TitleCase names like ``Lakshmi`` or ``Gajakesari``. The comparator
normalises both to a common ``lowercase-stripped-of-prefixes`` form
before diffing.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.chart_model import Chart
from app.core.yoga_library import active_yogas
from app.integration.gap_annotator import chart_from_reading
from app.integration.yoga_aliases import alias_canonical


class YogaSetDiff(BaseModel):
    """Per-yoga agreement record."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    canonical_name: str
    track_a_names: list[str] = Field(
        default_factory=list,
        description="Original Track-A rule IDs that mapped to this canonical name",
    )
    track_b_name: str | None = None
    track_b_intensity: float | None = None
    detected_by: str  # "both" | "track_a_only" | "track_b_only"


class YogaComparisonReport(BaseModel):
    """Aggregate report from ``compare_yoga_detection``."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    track_a_engine: str = "app.reading (yogas_extended + foundation)"
    track_b_engine: str = "app.core.yoga_library"

    track_a_yoga_count: int
    track_b_yoga_count: int
    intersection_count: int
    track_a_only: list[str]
    track_b_only: list[str]
    both: list[str]
    per_yoga: list[YogaSetDiff]

    verdict_summary: str


def _normalise(name: str) -> str:
    """Canonicalise a yoga name for cross-engine matching.

    Pipeline:
    1. lower-case
    2. strip module prefixes ("yogas_extended.", "foundation.", etc.)
    3. replace underscores with spaces
    4. strip trailing " yoga" / " dosha" (Track A keeps these, Track B sometimes does)
    5. apply alias map — yogas with known cross-engine variants
       (e.g. "neech_bhanga" / "neecha bhanga raja") fold to one canonical name
    """
    n = name.lower()
    # Drop namespace prefix
    if "." in n:
        n = n.rsplit(".", 1)[-1]
    # Normalise separators
    n = n.replace("_", " ").strip()
    # Strip trailing classifiers
    for suffix in (" yoga", " dosha"):
        if n.endswith(suffix):
            n = n[: -len(suffix)].strip()
    # Apply alias map — known cross-engine equivalences
    return alias_canonical(n)


def _collect_track_a_yogas(reading: dict[str, Any]) -> dict[str, list[str]]:
    """Walk the reading dict for ``classification == "yoga"`` findings.

    Returns a dict {canonical_name → [original_rule_ids]} so the
    deduplication is visible to the consumer (some yogas surface from
    multiple rule paths in Track A)."""
    results: dict[str, list[str]] = {}

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            if (
                node.get("classification") == "yoga"
                and node.get("rule")
                and isinstance(node["rule"], str)
            ):
                canonical = _normalise(node["rule"])
                if canonical:
                    results.setdefault(canonical, []).append(node["rule"])
            for v in node.values():
                _walk(v)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(reading)
    return results


def _collect_track_b_yogas(chart: Chart) -> dict[str, tuple[str, float]]:
    """Run Track B's ``active_yogas`` and return {canonical → (name, intensity)}."""
    out: dict[str, tuple[str, float]] = {}
    for yoga in active_yogas(chart):
        if not getattr(yoga, "active", False):
            continue
        canonical = _normalise(yoga.name)
        if canonical:
            out[canonical] = (yoga.name, float(getattr(yoga, "intensity", 0.0)))
    return out


def compare_yoga_detection(
    reading: dict[str, Any],
) -> YogaComparisonReport:
    """Diff Track A's detected yogas (from a reading) against Track B's
    ``active_yogas(chart)``.

    Track B's Chart is constructed from the reading via
    ``app.integration.gap_annotator.chart_from_reading``. Comparison is
    pure-Python (no LLM, no swisseph, no IO).
    """
    a_yogas = _collect_track_a_yogas(reading)
    chart = chart_from_reading(reading)
    b_yogas = _collect_track_b_yogas(chart)

    all_canonical = sorted(set(a_yogas) | set(b_yogas))
    per_yoga: list[YogaSetDiff] = []
    a_only: list[str] = []
    b_only: list[str] = []
    both: list[str] = []

    for canonical in all_canonical:
        in_a = canonical in a_yogas
        in_b = canonical in b_yogas
        a_names = a_yogas.get(canonical, [])
        b_pair = b_yogas.get(canonical)
        if in_a and in_b:
            detected_by = "both"
            both.append(canonical)
        elif in_a:
            detected_by = "track_a_only"
            a_only.append(canonical)
        else:
            detected_by = "track_b_only"
            b_only.append(canonical)
        per_yoga.append(YogaSetDiff(
            canonical_name=canonical,
            track_a_names=a_names,
            track_b_name=b_pair[0] if b_pair else None,
            track_b_intensity=b_pair[1] if b_pair else None,
            detected_by=detected_by,
        ))

    summary = (
        f"both={len(both)}, track_a_only={len(a_only)}, track_b_only={len(b_only)}"
    )

    return YogaComparisonReport(
        track_a_yoga_count=len(a_yogas),
        track_b_yoga_count=len(b_yogas),
        intersection_count=len(both),
        track_a_only=a_only,
        track_b_only=b_only,
        both=both,
        per_yoga=per_yoga,
        verdict_summary=summary,
    )
