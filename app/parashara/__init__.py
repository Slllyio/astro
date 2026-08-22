"""Parashara — a faithful BPHS (Brihat Parashara Hora Shastra) engine.

**Engine #2 of a multi-stream platform.** `app/raman_saab/` encodes Sri B. V. Raman's system and
is finished and frozen (textbook fidelity at its measured ceiling, guarded by the golden ratchet).
This package encodes **Parashara's own system** from BPHS and its allied classical texts.

## The root authority is the whole point

`raman_saab`'s directive is *"if Raman and another authority disagree, **Raman wins**"* — BPHS is
deliberately NOT natal-citable there (it is admitted only at `corroboration` tier: resolvable for
click-to-source, barred from natal citations by `test_natal_citations_are_raman_only`).

**This engine inverts that: Parashara is root.** Where BPHS and Raman differ, BPHS wins here.
Raman's books are, at most, corroboration for a BPHS reading. The two engines therefore cannot
share a verdict layer — that is precisely why this is a separate engine and not a mode of the
existing one.

## Hard isolation (tested both directions)

* `app/raman_saab/` imports NOTHING from `app/parashara/` — the Raman ratchet is untouchable by
  construction.
* `app/parashara/` imports NOTHING from `app/raman_saab/`'s doctrine or judging layers. It may use
  genuinely **stream-agnostic substrate** (ephemeris/varga arithmetic, ashtakavarga tables) — maths
  that belongs to no tradition — but never another stream's doctrine, verdicts, or rule corpus.
* Pinned by ``tests/parashara/test_engine_isolation.py``.

## What IS shared, deliberately

The **fidelity apparatus** — `Citation(work, line)` into real corpus lines, a source-lock freezing
each cited file's sha256, and an exhaustive citation enumeration. That machinery is stream-agnostic
and is the single most valuable thing the Raman engine built; re-deriving it per stream would be
waste. This package has its OWN registry (`doctrine.book_registry`) with its own root authority,
but the same shape.

## Layout

    doctrine/     book_registry (BPHS = root), sources (Citation/verify/passage)
    chart/        thin adapter over the shared caster
    primitives/   computed quantities BPHS defines (vimsopaka, avasthas, dashas, ...)
    judges/       verdict layer (Phase 2) — BPHS's own judging, NOT Raman's clause order

Corpus: `data/knowledge_library/sources/bphs/` — 91 of 97 chapters; see
`docs/parashara/BPHS_CORPUS_COVERAGE.md` for the honest per-chapter record.
"""
from __future__ import annotations
