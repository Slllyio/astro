"""Tier-3 enrichment: detect cross-sequence verdict-direction conflicts.

For each pair of Findings that share a domain context but emit **opposing
direction enums** (e.g. one positive, the other negative for the same
conceptual question), emit a top-level ``Contradiction`` describing the
disagreement.

The output ``Contradiction`` carries:

* ``finding_ids``           — the two (or more) conflicting Finding IDs
* ``domain``                — the shared domain context (e.g. ``career``,
                              ``marriage``); ``"general"`` when no domain
                              token is extractable
* ``description``           — descriptive summary of the disagreement
* ``severity``              — ``"soft"`` for directional disagreement,
                              ``"hard"`` for logical impossibility (yoga
                              detected + prerequisite missing)
* ``suggested_arbitration`` — DESCRIPTIVE ONLY (e.g. ``"Sequence 5 says
                              positive, Sequence 6 says negative"``). The
                              engine NEVER picks a winner.

Methodology:
    Type: descriptive
    Inputs to retrieval/scoring: ``finding.id`` (parsed for domain
        context token) + ``finding.direction`` enum. NEVER
        ``finding.verdict`` free-text — verdict carries narrative /
        biographical wording that would silently re-introduce
        confirmation bias into a cross-source diff.
    Explicitly NOT used: ``Finding.verdict`` free-text. Using verdict
        to "agree" or "disagree" would conflate narrative phrasing
        with classical doctrine direction; the entire point of
        ``direction`` as a closed enum is to give us a doctrine-stable
        comparand.
    Thresholds & their source: directional conflict is detected when
        the pair of directions is one of ``{(positive, negative),
        (negative, positive)}``. ``mixed`` is NOT contradicted (it
        already encodes ambivalence). ``neutral`` is NOT contradicted
        (no substantive claim being made). The set is hardcoded per
        spec Section 6's 4-value direction enum; no fitting against
        any historical-outcome dataset.
    Famous-chart anti-contamination: not applicable here — the
        detector operates on the structural ``direction`` enum, which
        has no biographical text to leak. If a downstream Finding's
        direction were itself derived from contaminated RAG, that bug
        belongs to the upstream module, not the detector.
    Null-baseline test required: N/A — pure structural comparison.
    Prediction-trap declaration: "This module does NOT predict outcomes.
        It detects PRE-EXISTING directional disagreements between
        Findings emitted by other modules. No fitting against any
        chart corpus with outcome labels."

Doctrine source:
    Spec Section 14, Tier-3 methodology commitments. The descriptive
    arbitration discipline ("never picks a winner") is the central
    anti-overreach safeguard: in the presence of cross-source
    disagreement, v1 surfaces BOTH sides and leaves arbitration to the
    human reader.

Anti-preference design (Section 14 commitment):
    The emitted ``Contradiction`` schema carries no ``winning_side`` /
    ``engine_preferred`` field — by intent. ``suggested_arbitration``
    is descriptive text only ("Finding A says X; Finding B says Y").
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.reading.schema import Contradiction, Finding

logger = logging.getLogger(__name__)


# Direction-pair set that constitutes a substantive disagreement.
# - (positive, negative) and (negative, positive) are the conflict pairs.
# - (neutral, anything): not a substantive claim being made.
# - (mixed, anything):   mixed already encodes ambivalence.
_CONFLICT_PAIRS: frozenset[frozenset[str]] = frozenset(
    [
        frozenset({"positive", "negative"}),
    ]
)

# Known domain context tokens that can appear as the second segment of
# a Finding ID. The detector parses ``domain.<X>.<rule>`` /
# ``seq_N.md_M.<X>_check`` / similar shapes and looks for one of these
# tokens to determine whether two Findings are addressing the same
# conceptual question.
_KNOWN_DOMAINS: frozenset[str] = frozenset(
    {
        "career",
        "marriage",
        "children",
        "wealth",
        "health",
        "education",
        "spiritual",
        "general",
    }
)


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #


def _extract_domain_token(finding_id: str) -> str | None:
    """Return a known domain token if one appears in the finding ID.

    Examples:
        ``"domain.career.10l_strong"`` -> ``"career"``
        ``"seq_5.md_3.career_check"``  -> ``"career"``
        ``"primitive.karakas.atmakaraka"`` -> None
    """
    if not finding_id:
        return None
    lower = finding_id.lower()
    for token in _KNOWN_DOMAINS:
        # We require word-boundary-ish match: token must appear as a
        # dot-segment or as a prefix/suffix of a dot-segment to avoid
        # accidentally matching ``career_executive`` against ``career``
        # when we don't want it to. For v1 we use simple ``in`` since
        # all current ID shapes embed the domain as a clean substring.
        if token in lower:
            return token
    return None


@dataclass(frozen=True)
class _FindingShim:
    """Lightweight extraction wrapper.

    Carries only the fields the detector needs from a Finding (or a
    dict shaped like one). Keeping it minimal means we can run on
    either pydantic objects or plain dicts coming out of
    ``ReadingOutput.model_dump()``.
    """

    id: str
    direction: str
    domain: str | None
    source: str  # "domain" | "sequence" | "other"


def _coerce_finding(item: Any) -> _FindingShim | None:
    """Best-effort coerce a Finding-like input into a _FindingShim."""
    if isinstance(item, Finding):
        fid = item.id
        direction = item.direction
    elif isinstance(item, dict):
        fid = item.get("id")
        direction = item.get("direction")
    else:
        return None
    if not fid or not direction:
        return None
    domain = _extract_domain_token(fid)
    source = "other"
    if fid.startswith("domain."):
        source = "domain"
    elif fid.startswith("seq_"):
        source = "sequence"
    return _FindingShim(id=fid, direction=direction, domain=domain, source=source)


def _collect_findings_from_output(reading_output: dict[str, Any]) -> list[_FindingShim]:
    """Pull every Finding-like object out of a ReadingOutput-shaped dict.

    Walks: ``primitives.findings``, ``foundations.findings``,
    ``practitioner.findings``, the four sequence result models'
    ``checks`` / ``steps`` / ``overall_verdict`` slots, and the six
    domain readings' ``promise`` / ``triggers`` / ``afflictions`` /
    ``cross_checks`` / ``overall_verdict``. For test convenience a
    flat ``_all_findings`` key is also honoured.
    """
    out: list[_FindingShim] = []

    # Test-convenience flat list.
    for f in reading_output.get("_all_findings", []) or []:
        shim = _coerce_finding(f)
        if shim is not None:
            out.append(shim)

    # Standard ReadingOutput blocks.
    for block_name in ("primitives", "foundations", "practitioner"):
        block = reading_output.get(block_name) or {}
        for f in block.get("findings", []) or []:
            shim = _coerce_finding(f)
            if shim is not None:
                out.append(shim)

    sequences = reading_output.get("sequences") or {}
    for seq_name in ("amsha_bala_krama", "career_executive"):
        seq = sequences.get(seq_name)
        if seq is None:
            continue
        for f in (seq.get("steps") or {}).values():
            shim = _coerce_finding(f)
            if shim is not None:
                out.append(shim)
        shim = _coerce_finding(seq.get("overall_verdict"))
        if shim is not None:
            out.append(shim)
    for seq_list_name in ("md_judgments", "ad_judgments"):
        for seq in sequences.get(seq_list_name, []) or []:
            for f in (seq.get("checks") or {}).values():
                shim = _coerce_finding(f)
                if shim is not None:
                    out.append(shim)
            shim = _coerce_finding(seq.get("overall_verdict"))
            if shim is not None:
                out.append(shim)

    domains = reading_output.get("domains") or {}
    for _dname, domain in domains.items():
        if domain is None:
            continue
        for slot in ("promise", "overall_verdict"):
            shim = _coerce_finding(domain.get(slot))
            if shim is not None:
                out.append(shim)
        for list_slot in ("triggers", "afflictions", "cross_checks"):
            for f in domain.get(list_slot, []) or []:
                shim = _coerce_finding(f)
                if shim is not None:
                    out.append(shim)

    return out


def _describe_direction_conflict(a: _FindingShim, b: _FindingShim) -> str:
    """Build a descriptive (never winner-picking) arbitration string."""
    label_a = a.source if a.source != "other" else "finding"
    label_b = b.source if b.source != "other" else "finding"
    return (
        f"{label_a} ({a.id}) says {a.direction}; "
        f"{label_b} ({b.id}) says {b.direction}. "
        "Both sides surfaced for human arbitration."
    )


# --------------------------------------------------------------------------- #
# Public API                                                                   #
# --------------------------------------------------------------------------- #


def detect_contradictions(reading_output: dict[str, Any]) -> list[Contradiction]:
    """Detect pairwise direction-conflicts in a ReadingOutput-shaped dict.

    Operation:
        1. Walk every Finding-bearing slot in the input and extract
           ``(id, direction, domain_token)`` shims.
        2. For every pair sharing a domain token, compare directions.
        3. If the direction pair is in ``_CONFLICT_PAIRS``, emit a
           ``Contradiction`` with severity ``"soft"`` (directional
           disagreement) and a descriptive ``suggested_arbitration``.

    Severity escalation to ``"hard"`` (logical impossibility) is
    reserved for future modules with explicit prerequisite-tracking
    metadata; v1 emits ``"soft"`` for all detected conflicts.
    """
    findings = _collect_findings_from_output(reading_output)
    out: list[Contradiction] = []
    seen_pairs: set[frozenset[str]] = set()

    for i, a in enumerate(findings):
        if a.domain is None:
            continue
        for b in findings[i + 1:]:
            if b.domain is None or a.domain != b.domain:
                continue
            if a.id == b.id:
                continue
            pair_key = frozenset({a.id, b.id})
            if pair_key in seen_pairs:
                continue
            if frozenset({a.direction, b.direction}) not in _CONFLICT_PAIRS:
                continue
            seen_pairs.add(pair_key)
            description = (
                f"Direction conflict in domain '{a.domain}': "
                f"{a.id} ({a.direction}) vs {b.id} ({b.direction})."
            )
            out.append(
                Contradiction(
                    finding_ids=[a.id, b.id],
                    domain=a.domain,
                    description=description,
                    severity="soft",
                    suggested_arbitration=_describe_direction_conflict(a, b),
                )
            )

    return out
