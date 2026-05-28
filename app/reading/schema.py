"""Pydantic models for `app/reading` JSON output.

This module is the immutable contract between the kundli analysis engine and
every downstream consumer (CLI, future LLM narrators, frontend, RAG layers).
The schema is versioned (`Meta.schema_version`); breaking changes require a
major version bump per the changelog committed alongside the next minor
release.

Schema version: 1.0.0
Stability: experimental (until the first non-engine downstream consumer ships)

The shape of each model is dictated by:

- Spec Section 6 (Universal Finding model, ID grammar, named-dict sequence
  checks, the 4 enum tuples reproduced verbatim).
- Spec Section 15 (API-documenter refinements: `Meta.stability`,
  `Meta.doctrine_config`, dual JD+ISO-8601 dates, Pydantic Field constraints,
  `Finding.enrichment_level`, `Finding.contradicts_finding_ids`,
  `Finding.consensus_status`).
- Lockfile `docs/doctrine-decisions.md` (D-1..D-16): each decision is echoed
  by `DoctrineConfig` so every emitted reading is self-describing about which
  doctrine variants produced it.

Locks enforced at the model level:

- `model_config = ConfigDict(frozen=True, extra="forbid")` on every model
  (matches CLAUDE.md `extra="forbid"` discipline).
- Numeric ranges (`Field(ge=, le=)`) for every probabilistic / bounded score.
- `Literal[...]` enums for every closed-set categorical field
  (classification, direction, band, severity, ...).
- Named-dict validators on `*Judgment` models assert
  `set(checks.keys()) == set(<XYZ>_CHECK_KEYS)` so adding/dropping a check
  requires both a spec amendment AND a schema version bump.
"""
from __future__ import annotations

from typing import Any, Final, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# Input envelope
# ---------------------------------------------------------------------------


class ChartInput(BaseModel):
    """User-supplied birth-data envelope.

    Format conventions:
        - `dob` is ISO date `YYYY-MM-DD`
        - `time` is 24-hour `HH:MM`
        - `tz` is signed offset `±HH:MM` (the project does NOT accept tz-database names)
        - `lat`, `lon` in decimal degrees; negatives are South / West
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    dob: str
    time: str
    tz: str
    lat: float = Field(ge=-90.0, le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)


# ---------------------------------------------------------------------------
# Tier-3 enrichment sub-models (defined before Finding because Finding embeds them)
# ---------------------------------------------------------------------------


class Citation(BaseModel):
    """A single doctrine-source citation attached to a Finding by Tier-3 RAG."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source: str
    passage: str
    relevance: float = Field(ge=0.0, le=1.0)
    knowledge_doc_id: str


class ConsensusScore(BaseModel):
    """Cross-source agreement scored by `consensus_scoring.py` (Tier-3)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    score: float = Field(ge=0.0, le=1.0)
    sources_agreeing: int = Field(ge=0)
    sources_total: int = Field(ge=0)
    low_consensus_flag: bool


class Dispute(BaseModel):
    """Report-only doctrine variance surfaced by `dispute_surfacing.py`.

    By design carries NO `is_correct` / `recommended_side` / `engine_preferred`
    field (spec Section 14, Tier-3 methodology commitments).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    rule: str
    sources_for: list[str] = Field(default_factory=list)
    sources_against: list[str] = Field(default_factory=list)
    canonical_example: str | None = None


class RobustnessScore(BaseModel):
    """Output of `birth_time_robustness.py` (Tier-3).

    `sensitive_to_birth_time` is `EXPERIMENTAL` until the threshold
    methodology is published (Section 14).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    sensitive_to_birth_time: bool
    flip_rate_at_5min: float = Field(ge=0.0, le=1.0)
    flip_rate_at_10min: float = Field(ge=0.0, le=1.0)
    inputs_used: list[str] = Field(default_factory=list)


class ConfidenceScore(BaseModel):
    """3-vote rule confidence envelope.

    `votes` is a fixed-key dict {house, lord, karaka} -> bool indicating which
    of the three classical evidence pillars agree with the finding. `score`
    is a [0,1] aggregation; `band` is the human-readable bucket.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    score: float = Field(ge=0.0, le=1.0)
    votes: dict[str, bool]
    band: Literal["indicative_only", "low", "medium", "high", "very_strong"]


# ---------------------------------------------------------------------------
# Universal Finding model
# ---------------------------------------------------------------------------


class Finding(BaseModel):
    """The universal output unit emitted by every engine module.

    A Finding represents one judgment: a karaka identification, a yoga
    detection, an MD check-step result, a domain promise/trigger/affliction.
    Tier-3 enrichments (citations, consensus, dispute, robustness,
    contradicts_finding_ids) are inline so consumers never need a JOIN to
    top-level enrichment tables.

    ID grammar (stable across runs; enumeration-based IDs are forbidden):
        - `seq_<N>.<scope>.<rule_slug>`         e.g. `seq_5.md_3.step_05_rashi_depositor`
        - `primitive.<module>.<rule_slug>`      e.g. `primitive.karakas.atmakaraka`
        - `foundation.<module>.<rule_slug>`     e.g. `foundation.argala.7th_house_argala`
        - `practitioner.<module>.<rule_slug>`   e.g. `practitioner.mks.saturn_in_1`
        - `domain.<name>.<rule_slug>`           e.g. `domain.marriage.7l_dasha_window`
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    rule: str
    source_sequence: str | None
    classification: Literal["promise", "trigger", "affliction", "yoga", "primitive"]
    direction: Literal["positive", "negative", "neutral", "mixed"]
    verdict: str = Field(max_length=140)
    verdict_language: Literal["en"] = "en"
    evidence: list[str] = Field(default_factory=list)
    confidence: ConfidenceScore

    # Tier-3 enrichments (populated only when enrich=True). Defaults below
    # disambiguate "Tier-3 disabled" from "ran but no results."
    enrichment_level: Literal[0, 1, 2, 3] = 0
    citations: list[Citation] = Field(default_factory=list)
    consensus: ConsensusScore | None = None
    consensus_status: Literal["not_computed", "no_agreement", "computed"] = "not_computed"
    dispute: Dispute | None = None
    robustness: RobustnessScore | None = None
    contradicts_finding_ids: list[str] = Field(default_factory=list)
