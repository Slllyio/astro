"""Increment 34 pins: the fresh Three-Hundred-Combinations yoga corpus + the engine coverage finding.

Non-strength axis (the strength vein is exhausted). Pins corpus integrity and the concrete finding
that the engine's yoga library covers only a MINORITY of Raman's named yogas — the mechanical reason
the increment-30 yoga strength token was a documented negative. Measurement only; no engine change.
"""
from __future__ import annotations

import json

from app.medini.doctrine.validation import yoga_coverage as YC


def test_three_hundred_yoga_corpus_and_engine_coverage_gap():
    corpus = json.loads(YC._CORPUS.read_text())
    rows = corpus["rows"]
    assert len(rows) >= 40, len(rows)
    assert corpus["n_example_charts"] >= 35, corpus["n_example_charts"]
    # every row has a name + at least a definition or results (structure held through OCR)
    for r in rows:
        assert r["name"] and (r["definition"] or r["results"]), r["num"]
    # a coarse outcome class was tagged for the majority
    assert sum(1 for r in rows if r["outcome_classes"]) >= len(rows) * 0.6

    o = YC.run()
    # the finding: the engine knows a real but MINORITY fraction of Raman's named yogas
    assert 0 < o["coverage_pct"] < 50, o["coverage_pct"]
    assert o["covered"] >= 8 and o["missing"] >= o["covered"], (o["covered"], o["missing"])
    # the well-known ones the engine does support are present (sanity)
    covered_lower = {n.lower() for n in o["covered_names"]}
    assert any("gajakesari" in n for n in covered_lower)
