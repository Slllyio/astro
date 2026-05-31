"""Integration layer bridging the two parallel reading engines.

This package adapts between two independently-developed reading engines that
both live in this repo but were built in isolation:

- **Track A** — ``app.reading.*`` — deterministic kundli engine with strict
  schema discipline (1763 tests, 18 doctrine commitments, JSON envelope
  versioned 1.2.0). Public entry: ``app.reading.proforma.compute(...)``.
- **Track B** — ``app.core.reading_composer`` + ``app.core.dkp_*`` +
  ``app.core.functional_roles`` + 8 Gap modules — the "astrologer's-lens"
  framework with DKP modulation, Doctrine Translation Engine (27 records
  spanning ancient shloka → modern manifestation), and three-pillar bhava
  judgement. Public entry: ``app.core.reading_composer.compose_reading(...)``.

Neither engine is modified by this package. Adapters here are READ-ONLY
over both APIs and produce a NEW envelope (``IntegratedReadingOutput``)
that wraps Track A's output and decorates it with Track B's doctrine
translations and modulation context.

Public surface:

- ``enhance(reading_dict)`` — annotate a Track-A reading with DKP translations.
- ``compare_chara_dasha(chart_input, target_iso=None)`` — diff both Chara
  Dasha implementations for the same chart.
- ``IntegratedReadingOutput`` — Pydantic envelope wrapping enhanced output.
"""

from __future__ import annotations

from app.integration.dkp_enhancer import (
    IntegratedReadingOutput,
    enhance,
)
from app.integration.chara_compare import (
    CharaComparisonReport,
    compare_chara_dasha,
)
from app.integration.functional_compare import (
    FunctionalComparisonReport,
    compare_functional_roles,
)
from app.integration.dkp_modulator_adapter import (
    DkpModulatedReading,
    ModulatedDomainReading,
    build_dkp_context_from_reading,
    modulate_all_domains,
    modulate_domain,
)
from app.integration.gap_annotator import (
    GapAnnotatedReading,
    GapModuleEntry,
    annotate_with_gap_modules,
    chart_from_reading,
)
# v0.4.0 comparator suite
from app.integration.vimshottari_compare import (
    VimshottariCurrentMDReport,
    compare_vimshottari_current_md,
)
from app.integration.yoga_compare import (
    YogaComparisonReport,
    compare_yoga_detection,
)
from app.integration.shadbala_compare import (
    ShadbalaComparisonReport,
    compare_shadbala,
)
from app.integration.d9_compare import (
    D9ComparisonReport,
    compare_d9_signs,
)
from app.integration.argala_drishti_compare import (
    ArgalaDrishtiComparisonReport,
    compare_argala_drishti,
)
# v0.5.0 LLM narrative + adversarial verification
from app.integration.narrative import (
    DomainNarrative,
    NarrativeOutput,
    CriticReview,
    CriticVerdict,
    VerifiedClaim,
    VerifiedNarrative,
    compose_narrative,
    run_critics,
    narrate_and_verify,
)
# v0.6.0 + v0.7.0 — benchmark + corpus RAG
from app.integration.benchmark import (
    BenchmarkReport,
    CHART_REGISTRY,
    EventOutcome,
    FAMOUS_EVENTS,
    FamousChart,
    FamousEvent,
    PerChartSummary,
    PerDomainSummary,
    run_benchmark,
    score_event,
)
from app.integration.corpus_rag_enhancer import (
    CorpusCitation,
    CorpusRAGEnhancedReading,
    enhance_with_corpus_rag,
)

__all__ = [
    # DKP enhancer (v0.1.0)
    "IntegratedReadingOutput",
    "enhance",
    # Chara Dasha comparator (v0.1.0)
    "CharaComparisonReport",
    "compare_chara_dasha",
    # Functional benefic/malefic comparator (v0.2.0)
    "FunctionalComparisonReport",
    "compare_functional_roles",
    # DKP modulator adapter (v0.2.0)
    "DkpModulatedReading",
    "ModulatedDomainReading",
    "build_dkp_context_from_reading",
    "modulate_all_domains",
    "modulate_domain",
    # Gap-module annotator (v0.3.0)
    "GapAnnotatedReading",
    "GapModuleEntry",
    "annotate_with_gap_modules",
    "chart_from_reading",
    # v0.4.0 comparator suite
    "VimshottariCurrentMDReport",
    "compare_vimshottari_current_md",
    "YogaComparisonReport",
    "compare_yoga_detection",
    "ShadbalaComparisonReport",
    "compare_shadbala",
    "D9ComparisonReport",
    "compare_d9_signs",
    "ArgalaDrishtiComparisonReport",
    "compare_argala_drishti",
    # v0.5.0 narrative + critics
    "DomainNarrative",
    "NarrativeOutput",
    "CriticReview",
    "CriticVerdict",
    "VerifiedClaim",
    "VerifiedNarrative",
    "compose_narrative",
    "run_critics",
    "narrate_and_verify",
    # v0.6.0 benchmark
    "BenchmarkReport",
    "CHART_REGISTRY",
    "EventOutcome",
    "FAMOUS_EVENTS",
    "FamousChart",
    "FamousEvent",
    "PerChartSummary",
    "PerDomainSummary",
    "run_benchmark",
    "score_event",
    # v0.7.0 corpus RAG
    "CorpusCitation",
    "CorpusRAGEnhancedReading",
    "enhance_with_corpus_rag",
]
