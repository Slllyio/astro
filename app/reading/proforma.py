"""Main orchestrator for `app.reading`.

Two-function pattern per spec Section 5 (Data flow / Public-vs-private
orchestration):

- `_run_core_pipeline` — private, deterministic, Stages 1-7. No RAG. No
  recursion. Birth-time-robustness MUST import this directly (rather than
  `compute`) to avoid recursion through Tier-3 modules that re-invoke the
  engine on time perturbations.
- `compute` — public; runs the core pipeline and, when `enrich=True`,
  layers Tier-3 enrichments (citations, consensus, dispute, robustness,
  contradiction detection) via `_apply_tier3_enrichments`.

For Phase 1 the only goal is to ship the structural seam; both
`_run_core_pipeline` and `_apply_tier3_enrichments` are deliberately stubbed:

- `_run_core_pipeline` returns the minimal valid `ReadingOutput`-shaped
  dict (empty blocks for Stages 1-7) with a fully populated `Meta` that
  echoes the canonical doctrine locks (D-1..D-16 + open-Q5 thresholds).
- `_apply_tier3_enrichments` is identity (no Tier-3 modules ship until
  Task 6.x).

The real Stage-1..7 implementations land in Task 1.4 onward (computations,
foundations, practitioner, sequences, domains). Each sequence module appends
to the relevant `*Block` here without touching this orchestrator's public
shape.
"""
from __future__ import annotations

import logging
import sys
from datetime import UTC, datetime
from typing import Any

from app.reading.schema import (
    ChartBlock,
    ChartInput,
    DoctrineConfig,
    DomainsBlock,
    FoundationsBlock,
    Meta,
    PractitionerBlock,
    PrimitivesBlock,
    ReadingOutput,
    SequencesBlock,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Engine version sourcing
# ---------------------------------------------------------------------------

_ENGINE_VERSION_FALLBACK = "0.0.0+phase1"


def _engine_version() -> str:
    """Best-effort engine version string.

    Phase 1: returns a phase-tagged placeholder. Phase 6 wires this to the
    package metadata / git short-sha so every emitted reading is fully
    self-describing about which engine produced it.
    """
    return _ENGINE_VERSION_FALLBACK


def _swiss_ephemeris_version() -> str:
    """Swiss Ephemeris library version, or ``"unknown"`` if unavailable."""
    try:
        import swisseph as swe

        return str(swe.version)
    except Exception:  # pragma: no cover - swisseph is a hard dep in this repo
        logger.warning("swisseph version unavailable; defaulting to 'unknown'")
        return "unknown"


def _python_version() -> str:
    """Tuple-style Python version string, e.g. ``"3.12.10"``."""
    info = sys.version_info
    return f"{info.major}.{info.minor}.{info.micro}"


def _generated_at_iso() -> str:
    """Current UTC instant as ISO-8601 (timezone-aware)."""
    return datetime.now(UTC).isoformat()


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


def _run_core_pipeline(chart_input: ChartInput) -> dict[str, Any]:
    """Run Stages 1-7 of the kundli pipeline.

    Private. Deterministic. No RAG. No recursion. Birth-time-robustness
    (Task 6.5) calls this directly to evaluate flip-rates over time
    perturbations without triggering Tier-3 enrichment on each call.

    Phase 1 stub: returns a `ReadingOutput`-shaped dict with empty stage
    blocks and a fully populated `Meta` envelope (schema_version, stability,
    doctrine_config defaults, environment fingerprint).
    """
    logger.info(
        "Running core pipeline for dob=%s time=%s tz=%s lat=%s lon=%s",
        chart_input.dob,
        chart_input.time,
        chart_input.tz,
        chart_input.lat,
        chart_input.lon,
    )

    meta = Meta(
        engine_version=_engine_version(),
        swiss_ephemeris_version=_swiss_ephemeris_version(),
        python_version=_python_version(),
        generated_at=_generated_at_iso(),
        chart_input=chart_input,
        doctrines_used=[],
        doctrine_config=DoctrineConfig(),
        enrichment_enabled=False,
        robustness_enabled=False,
        stage_timings_ms={},
    )

    output = ReadingOutput(
        meta=meta,
        chart=ChartBlock(),
        primitives=PrimitivesBlock(),
        foundations=FoundationsBlock(),
        practitioner=PractitionerBlock(),
        sequences=SequencesBlock(),
        domains=DomainsBlock(),
        contradictions=[],
        warnings=[],
    )

    # Round-trip through Pydantic so the dict carries the model's coerced
    # / default-applied shape rather than whatever Python types the stage
    # functions hand back. This is the same payload `compute` would emit.
    return output.model_dump(mode="json")


def _apply_tier3_enrichments(
    base: dict[str, Any], chart_input: ChartInput
) -> dict[str, Any]:
    """Layer Tier-3 enrichments on top of the core pipeline output.

    Tier-3 = citations, consensus_scoring, dispute_surfacing, robustness,
    contradiction_detector. Each subsystem reads the bare `ReadingOutput`
    payload and returns an updated payload with `Finding.enrichment_level`
    bumped and the matching enrichment fields populated.

    Phase 1 stub: identity. Task 6.x wires the real Tier-3 chain.
    """
    logger.debug(
        "Tier-3 enrichment stub invoked (no-op) for dob=%s", chart_input.dob
    )
    return base


def compute(chart_input: ChartInput, enrich: bool = True) -> dict[str, Any]:
    """Run the full kundli pipeline and return a `ReadingOutput`-shaped dict.

    This is the public engine entry point. CLI, API routes, and downstream
    callers (LLM narrators, frontend, RAG layers) should call this rather
    than `_run_core_pipeline`. The only exception is birth-time-robustness,
    which calls `_run_core_pipeline` directly to avoid recursion.

    Args:
        chart_input: Validated user-supplied birth-data envelope.
        enrich: If True (default), layer Tier-3 enrichments after the core
            pipeline completes. If False, return the bare deterministic
            output. Per spec Section 5, `enrich=False` MUST return the
            exact same dict as `_run_core_pipeline` so robustness loops are
            byte-stable across runs.

    Returns:
        A dict matching the `ReadingOutput` Pydantic schema.
    """
    base = _run_core_pipeline(chart_input)
    if not enrich:
        return base
    return _apply_tier3_enrichments(base, chart_input)
