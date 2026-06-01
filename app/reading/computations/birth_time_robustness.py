"""Tier-3 enrichment: birth-time sensitivity scoring.

For each Finding in a base ``ReadingOutput``-shaped dict, re-run the
deterministic core pipeline (``_run_core_pipeline``) at ±5min and
±10min birth-time perturbations and compute the fraction of nudges
that flipped the Finding's ``direction`` enum. The result is attached
as a ``RobustnessScore`` on the Finding.

Critical recursion-safety discipline:
    This module imports the PRIVATE ``_run_core_pipeline`` directly
    from ``app.reading.proforma`` rather than calling the public
    ``compute(..., enrich=True)``. Calling ``compute`` from inside a
    Tier-3 enrichment would re-enter ``_apply_tier3_enrichments``,
    which re-invokes ``score_robustness``, which re-invokes
    ``compute``, ad infinitum. The private entry-point is the only
    safe seam — any future maintainer who refactors this MUST
    preserve the direct ``_run_core_pipeline`` import.

The ``sensitive_to_birth_time`` boolean flag is currently marked
**EXPERIMENTAL** in the schema's Meta block until a published
methodology grounds the threshold choice (Section 14 mandate). The
raw ``flip_rate_at_5min`` / ``flip_rate_at_10min`` numerics are the
SHIP-stable outputs; the boolean is informational only.

Methodology:
    Type: descriptive — structural sensitivity measurement.
    Inputs to retrieval/scoring: the supplied ``ChartInput``
        (perturbed at ±5min and ±10min via the local
        ``_shift_chart_input`` helper) and the base
        ``ReadingOutput``-shaped dict's findings (matched by
        ``Finding.id``). NEVER ``finding.verdict`` free-text — only
        the ``direction`` enum participates in the flip check.
    Explicitly NOT used: ``Finding.verdict`` free-text — verdict is
        narrative and would silently change between runs in ways
        unrelated to structural sensitivity.
    Thresholds & their source: ``sensitive_to_birth_time`` is True
        when EITHER ``flip_rate_at_5min`` or ``flip_rate_at_10min``
        is strictly greater than 0.0 — i.e. ANY nudge in the four
        perturbations flipped the finding's direction. This is the
        most conservative possible threshold (one flip = sensitive)
        and is held EXPERIMENTAL pending a published methodology
        that grounds a less-conservative cut-off.

        NO threshold or weight in this module has been fit, tuned, or
        selected against any dataset of historical outcomes.
    Famous-chart anti-contamination: not applicable here — the
        scorer operates on structural ``direction`` enums emitted by
        deterministic pipeline runs, with no biographical-passage
        retrieval.
    Null-baseline test required: N/A — no fitted model.
    Prediction-trap declaration: "This module does NOT predict
        outcomes. It measures the STRUCTURAL sensitivity of
        previously-emitted findings to ±5min and ±10min birth-time
        perturbations. No fitting against any chart corpus with
        outcome labels."

Doctrine source:
    Spec Section 14, Tier-3 methodology commitments (raw numerics
    ship; threshold-derived boolean labelled EXPERIMENTAL) +
    Section 5 (private ``_run_core_pipeline`` as the only safe
    re-entry seam for Tier-3 robustness loops).

Anti-preference design (Section 14 commitment):
    The ``RobustnessScore`` carries the raw flip rates AND the
    boolean derived from the conservative threshold; downstream
    consumers can ignore the boolean and decide for themselves how
    to interpret the numerics.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

# Direct import of the PRIVATE entry-point — see module docstring for
# the recursion-safety reason. Module-bound so monkeypatching for tests
# affects every caller within the module.
from app.reading.proforma import _run_core_pipeline
from app.reading.schema import ChartInput, Finding, RobustnessScore

logger = logging.getLogger(__name__)


# Perturbation budget in minutes. Two pairs (±5min and ±10min) keep the
# total sub-runs to at most 4 — well within the bounded budget required
# by the recursion-safety test.
_PERTURBATIONS_5MIN: tuple[int, ...] = (-5, 5)
_PERTURBATIONS_10MIN: tuple[int, ...] = (-10, 10)


# ---------------------------------------------------------------------------
# Time-shift helper
# ---------------------------------------------------------------------------


def _shift_chart_input(ci: ChartInput, minutes: int) -> ChartInput:
    """Return a new ChartInput with ``time`` shifted by ``minutes``.

    Handles midnight crossover by re-emitting ``dob`` correctly. The
    Pydantic frozen + extra="forbid" guarantee on ChartInput means
    every other field is preserved by construction.
    """
    base_dt = datetime.fromisoformat(f"{ci.dob} {ci.time}:00")
    shifted = base_dt + timedelta(minutes=minutes)
    return ChartInput(
        dob=shifted.strftime("%Y-%m-%d"),
        time=shifted.strftime("%H:%M"),
        tz=ci.tz,
        lat=ci.lat,
        lon=ci.lon,
    )


# ---------------------------------------------------------------------------
# Finding extraction
# ---------------------------------------------------------------------------


def _collect_finding_dicts(reading_output: dict[str, Any]) -> list[dict[str, Any]]:
    """Walk a ReadingOutput-shaped dict and extract every finding dict.

    Returns the dicts directly (not Pydantic objects) because the
    nudge runs hand back ``model_dump()`` payloads and the comparison
    keys (``id``, ``direction``) are the only fields we need.
    """
    out: list[dict[str, Any]] = []

    # Test-convenience flat list.
    for f in reading_output.get("_all_findings", []) or []:
        if isinstance(f, dict):
            out.append(f)

    for block_name in ("primitives", "foundations", "practitioner"):
        block = reading_output.get(block_name) or {}
        for f in block.get("findings", []) or []:
            if isinstance(f, dict):
                out.append(f)

    sequences = reading_output.get("sequences") or {}
    for seq_name in ("amsha_bala_krama", "career_executive"):
        seq = sequences.get(seq_name)
        if seq is None:
            continue
        for f in (seq.get("steps") or {}).values():
            if isinstance(f, dict):
                out.append(f)
        ov = seq.get("overall_verdict")
        if isinstance(ov, dict):
            out.append(ov)
    for seq_list_name in ("md_judgments", "ad_judgments"):
        for seq in sequences.get(seq_list_name, []) or []:
            for f in (seq.get("checks") or {}).values():
                if isinstance(f, dict):
                    out.append(f)
            ov = seq.get("overall_verdict")
            if isinstance(ov, dict):
                out.append(ov)

    domains = reading_output.get("domains") or {}
    for _dname, domain in domains.items():
        if domain is None:
            continue
        for slot in ("promise", "overall_verdict"):
            f = domain.get(slot)
            if isinstance(f, dict):
                out.append(f)
        for list_slot in ("triggers", "afflictions", "cross_checks"):
            for f in domain.get(list_slot, []) or []:
                if isinstance(f, dict):
                    out.append(f)

    return out


def _build_direction_index(
    reading_output: dict[str, Any],
) -> dict[str, str]:
    """Return ``{finding_id: direction}`` for every finding in the dict."""
    index: dict[str, str] = {}
    for f in _collect_finding_dicts(reading_output):
        fid = f.get("id")
        direction = f.get("direction")
        if fid and direction:
            index[fid] = direction
    return index


def _finding_from_dict(d: dict[str, Any]) -> Finding | None:
    """Reconstruct a Pydantic Finding from a dict, returning None on failure."""
    try:
        return Finding.model_validate(d)
    except Exception:  # pragma: no cover - defensive; downstream tests pin shape
        logger.debug("Could not reconstruct Finding from dict id=%r", d.get("id"))
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def score_robustness(
    chart_input: ChartInput, base_output: dict[str, Any]
) -> list[Finding]:
    """Return a list of Findings enriched with ``RobustnessScore``.

    For each finding in ``base_output``, the scorer:

    1. Re-runs ``_run_core_pipeline`` at perturbations ``{-5, +5}min``
       (the ±5min pair) and ``{-10, +10}min`` (the ±10min pair).
    2. Reads each nudge's direction for the same finding ID.
    3. Computes ``flip_rate_at_5min`` and ``flip_rate_at_10min`` as
       the fraction of the 2 perturbations in each band where the
       direction differed from the base direction.
    4. Sets ``sensitive_to_birth_time`` True iff either flip rate is
       strictly greater than 0.0 (conservative, EXPERIMENTAL gate).

    Findings whose ID is absent from a nudge run's output are counted
    as "agreed" for that nudge (the structural shift was not enough
    to make the finding appear/disappear in a way the comparator
    could see); this conservative choice avoids inflating the
    flip rate with bookkeeping changes.
    """
    base_findings = _collect_finding_dicts(base_output)
    if not base_findings:
        return []

    # Run the 4 perturbation pipelines once each; build a direction
    # index per nudge so we can look up by finding ID below.
    nudge_indices_5: list[dict[str, str]] = []
    for offset in _PERTURBATIONS_5MIN:
        nudge_ci = _shift_chart_input(chart_input, offset)
        nudge_out = _run_core_pipeline(nudge_ci)
        nudge_indices_5.append(_build_direction_index(nudge_out))

    nudge_indices_10: list[dict[str, str]] = []
    for offset in _PERTURBATIONS_10MIN:
        nudge_ci = _shift_chart_input(chart_input, offset)
        nudge_out = _run_core_pipeline(nudge_ci)
        nudge_indices_10.append(_build_direction_index(nudge_out))

    out: list[Finding] = []
    for finding_dict in base_findings:
        finding = _finding_from_dict(finding_dict)
        if finding is None:
            continue
        base_direction = finding.direction
        # ±5min flip count
        flips_5 = sum(
            1
            for idx in nudge_indices_5
            if idx.get(finding.id, base_direction) != base_direction
        )
        # ±10min flip count
        flips_10 = sum(
            1
            for idx in nudge_indices_10
            if idx.get(finding.id, base_direction) != base_direction
        )
        flip_rate_5 = flips_5 / len(nudge_indices_5) if nudge_indices_5 else 0.0
        flip_rate_10 = flips_10 / len(nudge_indices_10) if nudge_indices_10 else 0.0
        sensitive = (flip_rate_5 > 0.0) or (flip_rate_10 > 0.0)

        robustness = RobustnessScore(
            sensitive_to_birth_time=sensitive,
            flip_rate_at_5min=flip_rate_5,
            flip_rate_at_10min=flip_rate_10,
            inputs_used=["direction"],
        )
        out.append(finding.model_copy(update={"robustness": robustness}))

    return out
