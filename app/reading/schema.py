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


# ---------------------------------------------------------------------------
# Named-dict sequence check enums (spec Section 6 — verbatim)
# ---------------------------------------------------------------------------

# Source: notebook NotebookLM proforma — "How to Judge a Mahadasha" by Anil
# Kumar Jain. Schema validation refuses any judgment dict missing one of
# these keys. Order is fixed for stable iteration; output dicts preserve
# insertion order. Adding a key requires a spec amendment AND a schema
# minor-version bump per Section 15.
MD_CHECK_KEYS: Final[tuple[str, ...]] = (
    "bhaav_from_lagna",                    # 1.  Bhava the MD lord occupies from Lagna
    "commonality_significations",          # 2.  Overlap between planet karakas and bhava themes
    "residential_strength",                # 3.  Degree-distance from Bhaav Madhya
    "bhaavs_aspected_fully",               # 4.  Bhavas the MD lord fully aspects
    "rashi_depositor",                     # 5.  Placement of rashi depositor of MD lord
    "balaadi_avastha",                     # 6.  Baladi state of MD lord (Bala/Kumara/Yuva/Vriddha/Mrita)
    "conjunctions_within_15deg",           # 7.  Planets within 15° of MD lord (functionally activated)
    "full_aspects_on_md_lord",             # 8.  Planets giving full aspect to MD lord
    "trinal_planets",                      # 9.  Planets trinal to MD lord within 15°
    "proximity_to_exact_trine",            # 10. Closeness of trinal planets to exact 120°
    "md_lord_as_lagna_yogas",              # 11. Treat MD lord point as Lagna; overlay yogas
    "nakshatra_tara_from_moon",            # 12. Tara (2nd/9th best, 7th worst) of MD lord's nakshatra from natal Moon
    "nakshatra_depositor_dignity",         # 13. Functional nature + dignity of MD lord's nakshatra-depositor
    "navamsa_depositor",                   # 14. Navamsa depositor of MD lord; generic + functional
    "kartari_yoga",                        # 15. Shubha/Pap Kartari on MD lord (planets flanking)
    "planet_in_2nd_from_md_lord",          # 16. What "comes out" of the MD; dignity of 2nd-from-MD-lord planet
    "ishta_phal",                          # 17. Ishta Phal scores of rashi/nakshatra/navamsa depositors
    "repeat_from_arudha_lagna",            # 18. Repeat checks 1-17 treating Arudha Lagna as reference
    "repeat_from_karakamsha_lagna",        # 19. Repeat checks 1-17 treating Karakamsha Lagna as reference
)

# Source: notebook NotebookLM proforma — "How To Read Antardasha In Vedic Astrology"
AD_CHECK_KEYS: Final[tuple[str, ...]] = (
    "rulership_of_ad_lord",                # 1.  Houses owned by AD lord (what it activates)
    "house_placement_of_ad_lord",          # 2.  Bhava occupied by AD lord (where results play out)
    "strength_dignity_influence",          # 3.  Combust/exalted/debilitated/dignified state
    "rajyoga_formed",                      # 4.  Latent Rajyogas activated by AD lord
    "afflictions",                         # 5.  Pap Kartari, malefic aspects, suppression
    "divisional_chart_assessment",         # 6.  D3/D7/D9/D10 confirmation for AD lord
    "mutual_position_md_ad",               # 7.  6/8/12 friction vs trinal support between MD and AD lords
)

# Source: notebook NotebookLM proforma — "The Architecture of Fate: Shodasha Varga System"
AMSHA_BALA_KRAMA_KEYS: Final[tuple[str, ...]] = (
    "analyze_d1",                          # 1.  Primary promise and physical manifestation
    "consult_d9",                          # 2.  Inner strength, dharma, ultimate "fruit"
    "specific_varga_refinement",           # 3.  Domain-specific Varga (D10 career, D7 children, etc.)
    "dasha_transit_activation",            # 4.  When the conditionally active Varga potential fires
)

# Source: notebook NotebookLM proforma — "The Varga System Handbook: Blueprint for Professional Destiny"
CAREER_EXECUTIVE_KEYS: Final[tuple[str, ...]] = (
    "vargottama_amatya_karaka",            # 1.  Vargottama check + Amatya Karaka identification
    "gandanta_knots",                      # 2.  Scan dasha sequence for water-to-fire nakshatra junctions
    "vimsopaka_strength",                  # 3.  Verify dasha lord has Vimsopaka >10 (Shodashavarga scheme)
    "gulika_saturn_bottlenecks",           # 4.  Debilitated Saturn in D10-6H or Gulika in D10-10H
)


def _require_exact_keys(
    checks: dict[str, Finding], expected: tuple[str, ...], model_name: str
) -> dict[str, Finding]:
    """Validator helper: assert the dict's keys exactly match `expected`.

    The error is raised as ValueError so Pydantic re-wraps it into a
    ValidationError. We sort the diffs deterministically so the error
    message is stable across runs (per ID-stability discipline).
    """
    expected_set = set(expected)
    got_set = set(checks.keys())
    missing = sorted(expected_set - got_set)
    extra = sorted(got_set - expected_set)
    if missing or extra:
        raise ValueError(
            f"{model_name}.checks must contain exactly the keys in spec Section 6. "
            f"missing={missing!r} extra={extra!r}"
        )
    return checks


# ---------------------------------------------------------------------------
# Sequence-result models (one per named sequence)
# ---------------------------------------------------------------------------


class MDJudgment(BaseModel):
    """Sequence 5 — Vimshottari Mahadasha 19-check judgment.

    `start_date` / `end_date` are ISO-8601 strings; `start_jd` / `end_jd`
    retain Julian-Day precision (spec Section 15 — dual representation).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    md_lord: str
    start_jd: float
    end_jd: float
    start_date: str
    end_date: str
    age_at_start: float
    age_at_end: float
    is_current: bool
    is_past: bool
    is_future: bool
    checks: dict[str, Finding]
    overall_verdict: Finding

    @model_validator(mode="after")
    def _validate_check_keys(self):
        _require_exact_keys(self.checks, MD_CHECK_KEYS, "MDJudgment")
        return self


class ADJudgment(BaseModel):
    """Sequence 6 — Vimshottari Antardasha 7-check judgment."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    ad_lord: str
    md_lord: str
    start_jd: float
    end_jd: float
    start_date: str
    end_date: str
    age_at_start: float
    age_at_end: float
    is_current: bool
    is_past: bool
    is_future: bool
    checks: dict[str, Finding]
    overall_verdict: Finding

    @model_validator(mode="after")
    def _validate_check_keys(self):
        _require_exact_keys(self.checks, AD_CHECK_KEYS, "ADJudgment")
        return self


class AmshaBalaKramaResult(BaseModel):
    """Sequence 1 — BPHS layered Varga judgment (4 steps)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    steps: dict[str, Finding]
    overall_verdict: Finding

    @model_validator(mode="after")
    def _validate_step_keys(self):
        _require_exact_keys(self.steps, AMSHA_BALA_KRAMA_KEYS, "AmshaBalaKramaResult")
        return self


class CareerExecutiveResult(BaseModel):
    """Sequence 2 — Career Executive Consulting (4 steps)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    steps: dict[str, Finding]
    overall_verdict: Finding

    @model_validator(mode="after")
    def _validate_step_keys(self):
        _require_exact_keys(self.steps, CAREER_EXECUTIVE_KEYS, "CareerExecutiveResult")
        return self


# ---------------------------------------------------------------------------
# Cross-cutting models
# ---------------------------------------------------------------------------


class Contradiction(BaseModel):
    """Cross-finding disagreement detected by `contradiction_detector.py`.

    `severity` `"soft"` means the directions disagree but both findings stand;
    `"hard"` means at least one finding must yield. `suggested_arbitration`
    is descriptive only (spec Section 14: never picks a winner).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    finding_ids: list[str] = Field(min_length=2)
    domain: str
    description: str
    severity: Literal["soft", "hard"]
    suggested_arbitration: str | None = None


class TimingWindow(BaseModel):
    """A dated event-window in a `DomainReading`.

    Dates are ISO-8601. `event_type` classifies the window for downstream
    UI grouping; `triggering_finding_ids` cross-references the Findings whose
    activation drove the window.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    start_date: str
    end_date: str
    driving_period: str
    event_type: Literal[
        "marriage",
        "career_shift",
        "child_birth",
        "education_milestone",
        "health_event",
        "wealth_event",
        "spiritual_event",
        "general",
    ]
    confidence_band: Literal["indicative_only", "low", "medium", "high", "very_strong"]
    triggering_finding_ids: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Remedies + DomainReading
# ---------------------------------------------------------------------------


class RemedyRecommendation(BaseModel):
    """A doctrine-cited remedy attached to a DomainReading.

    `kind` enumerates the broad remedy category; the precise prescription
    lives in `description`. `source` carries the classical citation per
    Tier-3 citation discipline.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: Literal["mantra", "gemstone", "yantra", "donation", "ritual", "behavioural", "other"]
    description: str
    source: str | None = None


class DomainReading(BaseModel):
    """One of the 6 named domain syntheses (career, marriage, ...).

    Aggregates the promise (natal potential), triggers (firing conditions),
    timing_windows (dated activations), afflictions (limiters), cross_checks
    (sequence-corroboration findings), remedies, and an overall verdict +
    confidence score for the domain.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    domain: str
    promise: Finding
    triggers: list[Finding] = Field(default_factory=list)
    timing_windows: list[TimingWindow] = Field(default_factory=list)
    afflictions: list[Finding] = Field(default_factory=list)
    cross_checks: list[Finding] = Field(default_factory=list)
    remedies: list[RemedyRecommendation] = Field(default_factory=list)
    overall_verdict: Finding
    confidence: ConfidenceScore


# ---------------------------------------------------------------------------
# DoctrineConfig — echoes the 16 lockfile decisions (D-1..D-16)
# ---------------------------------------------------------------------------


class DoctrineConfig(BaseModel):
    """Records the doctrine variant chosen for THIS reading.

    Every default value mirrors the locked decision in
    `docs/doctrine-decisions.md` (D-1 through D-16). When a reading is
    emitted, this block lets downstream consumers verify exactly which
    doctrine variants produced it. Configurable per-chart but with these
    documented defaults.

    Defaults track lockfile revision 1 (2026-05-27).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    # D-1 — 8-karaka (PVR Narasimha Rao) matches jagannathahora.io pinning
    karaka_mode: Literal[7, 8] = 8

    # D-2 — 1/7 → 10 shift applied uniformly to A1..A12, UL, UL₂
    arudha_exception: Literal["1_7_to_10", "none"] = "1_7_to_10"

    # D-3 — Shodashavarga 16-varga (BPHS Ch.7 vv.21–25, sum = 20.0)
    vimsopaka_scheme: Literal["shodashavarga", "saptavarga", "dashavarga"] = "shodashavarga"

    # D-4 — BPHS Ch.47 v.3 formula
    ishta_formula: Literal["bphs_47_3", "phaladeepika_6"] = "bphs_47_3"

    # D-8 — Sripati cusps (BPHS Vol.II Ch.51); KP/Placidus excluded by scope
    bhava_chalit_system: Literal["sripati", "porphyry"] = "sripati"

    # D-10 — Sanjay-Rath triple-AND formulation
    karaka_triangulation_reading: Literal["sanjay_rath", "bphs_classical"] = "sanjay_rath"

    # D-11 — BPHS Vol.I Ch.39 v.10 primary rule
    neech_bhanga_rule: Literal["bphs_39_10", "alt_1", "alt_2", "alt_3"] = "bphs_39_10"

    # D-12 — Strict 180° Rahu-leading
    kala_sarpa_definition: Literal["strict_180_rahu_leading", "loose", "partial"] = "strict_180_rahu_leading"

    # D-13 — Northern-latitude winner (BPHS Ch.27 v.13)
    graha_yuddha_winner: Literal["northern_latitude", "size", "brightness"] = "northern_latitude"

    # Section 12 open-Q #5 resolution — locked defaults
    consensus_min_sources: int = Field(default=3, ge=0)
    consensus_agreement_threshold: float = Field(default=0.66, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Pipeline-stage block models (placeholders — populated by downstream tasks)
# ---------------------------------------------------------------------------
#
# Each block carries the outputs of one pipeline stage. The internal field
# set will fill in as Phase 1 -> Phase 5 modules ship. For now we provide
# minimum structural envelopes that satisfy ReadingOutput composition and
# enforce the frozen + extra="forbid" lock so future field additions are
# explicit (and gated by a schema version bump).


class ChartBlock(BaseModel):
    """Stage 1 — natal chart raw outputs (lagna, planets, cusps, ayanamsa)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    lagna_longitude: float | None = None
    ayanamsa: float | None = None
    planets: dict[str, Any] = Field(default_factory=dict)
    cusps: dict[str, Any] = Field(default_factory=dict)
    extras: dict[str, Any] = Field(default_factory=dict)


class PrimitivesBlock(BaseModel):
    """Stage 2 — Tier-0 outputs (karakas, arudha, dignities, ...)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    findings: list[Finding] = Field(default_factory=list)
    by_module: dict[str, list[Finding]] = Field(default_factory=dict)


class FoundationsBlock(BaseModel):
    """Stage 3 — Tier-1 outputs (functional nature, bhava chalit, ...)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    findings: list[Finding] = Field(default_factory=list)
    by_module: dict[str, list[Finding]] = Field(default_factory=dict)


class PractitionerBlock(BaseModel):
    """Stage 4 — Tier-2 doctrine layer (MKS, Kala Sarpa, Neech Bhanga, ...)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    findings: list[Finding] = Field(default_factory=list)
    by_module: dict[str, list[Finding]] = Field(default_factory=dict)


class SequencesBlock(BaseModel):
    """Stage 5 — the 4 named sequence-result models.

    Each sequence result is optional: not every reading exercises every
    sequence (e.g. a chart with no career judgment skips Sequence 2).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    amsha_bala_krama: AmshaBalaKramaResult | None = None
    career_executive: CareerExecutiveResult | None = None
    md_judgments: list[MDJudgment] = Field(default_factory=list)
    ad_judgments: list[ADJudgment] = Field(default_factory=list)


class DomainsBlock(BaseModel):
    """Stage 6 — the 6 named domain syntheses."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    career: DomainReading | None = None
    marriage: DomainReading | None = None
    children: DomainReading | None = None
    wealth: DomainReading | None = None
    health: DomainReading | None = None
    education: DomainReading | None = None


# ---------------------------------------------------------------------------
# Meta — schema/version/doctrine echo
# ---------------------------------------------------------------------------


class Meta(BaseModel):
    """Engine + chart-input metadata accompanying every reading.

    `schema_version` is the public stable lock; bump to 1.1.0 for additive
    fields, 2.0.0 for breaking changes. `stability` is `"experimental"`
    until the first non-engine downstream consumer ships, then `"beta"`,
    then `"stable"`.

    `doctrine_config` echoes the 16 lockfile decisions so every emitted
    reading is self-describing (per spec Section 6, design choices).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["1.0.0"] = "1.0.0"
    stability: Literal["experimental", "beta", "stable"] = "experimental"
    engine_version: str
    swiss_ephemeris_version: str
    python_version: str
    generated_at: str  # ISO-8601 UTC
    chart_input: ChartInput
    doctrines_used: list[str] = Field(default_factory=list)
    doctrine_config: DoctrineConfig
    enrichment_enabled: bool
    robustness_enabled: bool
    stage_timings_ms: dict[str, int] = Field(default_factory=dict)
    schema_changelog_url: str = "docs/reading/CHANGELOG.md"


# ---------------------------------------------------------------------------
# ReadingOutput — root
# ---------------------------------------------------------------------------


class ReadingOutput(BaseModel):
    """Top-level JSON contract.

    The 9-key shape mirrors the pipeline stages 1–8 (spec Section 6):

    - `meta`           — engine + chart envelope, doctrine echo
    - `chart`          — Stage 1 natal raw
    - `primitives`     — Stage 2 Tier-0 outputs
    - `foundations`    — Stage 3 Tier-1 outputs
    - `practitioner`   — Stage 4 Tier-2 outputs
    - `sequences`      — Stage 5 4 named sequence results
    - `domains`        — Stage 6 6 named domain readings
    - `contradictions` — Stage 8.3 cross-finding disagreements
    - `warnings`       — engine-level diagnostics (non-fatal)
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    meta: Meta
    chart: ChartBlock
    primitives: PrimitivesBlock
    foundations: FoundationsBlock
    practitioner: PractitionerBlock
    sequences: SequencesBlock
    domains: DomainsBlock
    contradictions: list[Contradiction] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
