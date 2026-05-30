"""Tier-3 enrichment: surface lockfile-documented doctrine disagreements.

For each Finding whose rule appears in a known-dispute table, attach a
``Dispute`` carrying:

* ``rule``               — the disputed rule name
* ``sources_for``        — classical texts/citations supporting the engine's
                           **locked** side (from ``docs/doctrine-decisions.md``)
* ``sources_against``    — classical texts/citations supporting the
                           alternative variant
* ``canonical_example``  — optional named-doctrine reference

The module ships a STATIC dispute table for v1 — comprehensive
doctrine-variant detection from the RAG corpus is intentionally out of
scope. Dispute table entries correspond to lockfile decisions D-3, D-10,
D-11, D-12 in ``docs/doctrine-decisions.md``.

Methodology:
    Type: descriptive
    Inputs to retrieval/scoring: ``finding.rule`` (string match against
        a static lockfile-driven dispute table). NEVER
        ``finding.verdict`` free-text.
    Explicitly NOT used: ``Finding.verdict`` free-text. The verdict
        could carry biographical contamination; matching disputes by
        verdict would conflate two different sources of failure.
    Thresholds & their source: none — this is a pure lookup against
        the static lockfile-driven dispute table; the table itself is
        sourced from ``docs/doctrine-decisions.md`` (D-3 Vimsopaka, D-10
        Karaka Triangulation, D-11 Neech Bhanga, D-12 Kala Sarpa).
    Famous-chart anti-contamination: not applicable here — the dispute
        table is hardcoded from classical sources, not retrieved from
        the RAG corpus, so there is no biographical-passage filtering
        step needed at this layer.
    Null-baseline test required: N/A — pure lookup.
    Prediction-trap declaration: "This module does NOT predict outcomes.
        It surfaces pre-existing lockfile-documented disagreements
        between classical sources. No fitting against any chart corpus
        with outcome labels."

Doctrine source:
    * D-3 (Vimsopaka scheme): ``docs/doctrine-decisions.md``
    * D-10 (Karaka triangulation): ``docs/doctrine-decisions.md``
    * D-11 (Neech Bhanga primary rule): ``docs/doctrine-decisions.md``
    * D-12 (Kala Sarpa primary definition): ``docs/doctrine-decisions.md``

Anti-preference design (Section 14 commitment):
    The emitted ``Dispute`` schema carries no ``is_correct`` /
    ``recommended_side`` / ``engine_preferred`` field — by intent. The
    engine documents which side it locked but never claims it is the
    "right" side; downstream consumers (UI, narrator) display BOTH
    sides and let users make the call.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from app.reading.schema import Dispute, Finding

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _DisputeEntry:
    """One row in the static dispute table.

    ``match_substring`` is lowercased and compared against
    ``finding.rule.lower()`` for membership. Multiple Finding rules can
    map to the same DisputeEntry (e.g. all neech-bhanga findings share
    the D-11 dispute).
    """

    rule_label: str
    sources_for: tuple[str, ...]
    sources_against: tuple[str, ...]
    canonical_example: str | None = None


# Lockfile-driven dispute table. Keys are the lowercased substring that
# must appear in ``finding.rule.lower()`` for the dispute to fire. Values
# carry the citations from both sides.
#
# Lockfile reference is in the docstring above. Any addition / removal
# here MUST be accompanied by a parallel lockfile amendment so the
# engine's emitted disputes stay traceable to a documented decision.
_DISPUTE_TABLE: dict[str, _DisputeEntry] = {
    # D-10
    "karaka triangulation": _DisputeEntry(
        rule_label="Karaka Triangulation",
        sources_for=(
            "Sanjay-Rath, Crux of Vedic Astrology — triple-AND formulation",
        ),
        sources_against=(
            "BPHS Vol.I Ch.11 — uses Arudha Lagna as second pivot in some cases",
        ),
        canonical_example="D-10 (docs/doctrine-decisions.md)",
    ),
    # D-11
    "neech bhanga": _DisputeEntry(
        rule_label="Neech Bhanga (debilitation cancellation)",
        sources_for=(
            "BPHS Vol.I Ch.39 v.10 — exalted lord of debilitation-sign "
            "in kendra from Lagna or Moon (primary rule)",
        ),
        sources_against=(
            "BPHS Vol.I Ch.39 v.11 — depositor in own or exaltation sign",
            "BPHS Vol.I Ch.39 v.12 — dispositor + exalted planet conjunction",
            "BPHS Vol.I Ch.39 v.13 — mutual exchange between debilitation- "
            "and exaltation-lords",
        ),
        canonical_example="D-11 (docs/doctrine-decisions.md)",
    ),
    # D-3
    "vimsopaka": _DisputeEntry(
        rule_label="Vimsopaka strength scheme",
        sources_for=(
            "BPHS Ch.7 vv.21-25 — Shodashavarga 16-varga scheme (sum=20.0)",
        ),
        sources_against=(
            "BPHS Ch.7 — Saptavarga 7-varga scheme (simpler classical variant)",
            "BPHS Ch.7 — Dashavarga 10-varga scheme (mid-detail variant)",
        ),
        canonical_example="D-3 (docs/doctrine-decisions.md)",
    ),
    # D-12
    "kala sarpa": _DisputeEntry(
        rule_label="Kala Sarpa (primary definition)",
        sources_for=(
            "K.N. Rao / PVR Narasimha Rao — strict 180-degree Rahu-leading",
        ),
        sources_against=(
            "Loose definition — any concentration of planets between the nodes",
            "Bidirectional — Rahu-leading or Ketu-leading both count",
        ),
        canonical_example="D-12 (docs/doctrine-decisions.md)",
    ),
}


# --------------------------------------------------------------------------- #
# Helpers                                                                      #
# --------------------------------------------------------------------------- #


def _lookup_dispute(rule_name: str) -> _DisputeEntry | None:
    """Return the dispute entry matching ``rule_name``, or None.

    Substring-matched (lowercased) against the table keys. The first hit
    wins; the table is ordered by lockfile decision number.
    """
    if not rule_name:
        return None
    lower = rule_name.lower()
    for key, entry in _DISPUTE_TABLE.items():
        if key in lower:
            return entry
    return None


# --------------------------------------------------------------------------- #
# Public API                                                                   #
# --------------------------------------------------------------------------- #


def surface_disputes(findings: list[Finding]) -> list[Finding]:
    """Return a new list of findings with ``dispute`` populated when applicable.

    Findings whose ``rule`` matches an entry in ``_DISPUTE_TABLE`` get a
    ``Dispute`` attached describing both sides of the classical
    disagreement. Findings whose rule is undisputed are returned
    unchanged.
    """
    out: list[Finding] = []
    for finding in findings:
        entry = _lookup_dispute(finding.rule)
        if entry is None:
            out.append(finding)
            continue
        dispute = Dispute(
            rule=entry.rule_label,
            sources_for=list(entry.sources_for),
            sources_against=list(entry.sources_against),
            canonical_example=entry.canonical_example,
        )
        out.append(finding.model_copy(update={"dispute": dispute}))
    return out
