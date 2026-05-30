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

__all__ = [
    "IntegratedReadingOutput",
    "enhance",
    "CharaComparisonReport",
    "compare_chara_dasha",
]
