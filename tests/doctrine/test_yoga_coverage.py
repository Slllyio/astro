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
    # coverage is computed on DISTINCT yogas (OCR duplicates deduped) with EXACT stem matching.
    # After increments 35+36 the engine covers ~42% of Raman's named yogas (up from ~24% pre-35).
    assert 38 <= o["coverage_pct"] < 60, o["coverage_pct"]
    assert o["covered"] >= 24, o["covered"]
    assert o["n_distinct_yogas"] >= 55, o["n_distinct_yogas"]
    # the increment-35 (occupancy) and increment-36 (lord-based) additions are present
    covered_lower = {n.lower() for n in o["covered_names"]}
    assert any("gajakesari" in n for n in covered_lower)
    for added in ("chatussagara", "dhurdhura", "sakata", "vasumathi", "chakra", "gola",
                  "parvata", "sankha", "sreenatha", "samudra", "chapa"):
        assert any(added in n for n in covered_lower), added


def test_increment_35_new_detectors_fire_on_defining_charts():
    """Each increment-35 yoga fires on a chart built to its Raman definition, and is silent
    otherwise — a faithfulness check on the 8 new detectors."""
    from app.core import yoga_library as YL
    from app.core.chart_model import Chart

    def chart(signs):
        houses = dict(signs)  # asc_sign=1 → house == sign
        lons = {p: (s - 1) * 30 + 15.0 for p, s in signs.items()}
        return Chart(planet_signs=signs, planet_houses=houses, planet_lons=lons,
                     asc_sign=1, asc_lon=5.0)

    def fires(c, name):
        return next(y for y in YL.detect_all(c) if y.name == name).active

    seven = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
    # Gola: all seven in one sign
    assert fires(chart({p: 5 for p in seven} | {"Rahu": 1, "Ketu": 7}), "Gola")
    # Chatussagara: kendras 1,4,7,10 occupied
    assert fires(chart({"Sun": 1, "Moon": 4, "Mars": 7, "Jupiter": 10, "Mercury": 2,
                        "Venus": 3, "Saturn": 5, "Rahu": 6, "Ketu": 12}), "Chatussagara")
    # Sakata: Moon in 6th from Jupiter (Jup=1 → Moon=6)
    assert fires(chart({"Jupiter": 1, "Moon": 6, "Sun": 2, "Mars": 3, "Mercury": 4,
                        "Venus": 5, "Saturn": 7, "Rahu": 8, "Ketu": 2}), "Sakata")
    # and a plain chart should not trip Gola/Chatussagara
    spread = {"Sun": 1, "Moon": 2, "Mars": 5, "Mercury": 3, "Jupiter": 8, "Venus": 11,
              "Saturn": 9, "Rahu": 6, "Ketu": 12}
    assert not fires(chart(spread), "Gola")


def test_increment_36_lord_based_detectors():
    """The lord-based increment-36 yogas fire on charts built to their definition."""
    from app.core import yoga_library as YL
    from app.core.chart_model import Chart

    def chart(signs, asc=1):
        return Chart(planet_signs=signs, planet_houses={p: ((s - asc) % 12) + 1 for p, s in signs.items()},
                     planet_lons={p: (s - 1) * 30 + 15.0 for p, s in signs.items()},
                     asc_sign=asc, asc_lon=(asc - 1) * 30 + 5.0)

    def fires(c, name):
        return next(y for y in YL.detect_all(c) if y.name == name).active

    # Samudra: all seven planets in even houses (asc=Aries → even signs)
    even = {"Sun": 2, "Moon": 4, "Mars": 6, "Mercury": 8, "Jupiter": 10, "Venus": 12,
            "Saturn": 2, "Rahu": 1, "Ketu": 7}
    assert fires(chart(even), "Samudra")

    # Kahala (Aries asc): L4=Moon, L9=Jupiter in mutual kendras; L1=Mars strong (own sign Aries)
    kahala = {"Mars": 1, "Moon": 1, "Jupiter": 4, "Sun": 5, "Mercury": 6,
              "Venus": 7, "Saturn": 8, "Rahu": 9, "Ketu": 3}
    assert fires(chart(kahala), "Kahala")
    # a chart with a debilitated/weak Lagna lord should not fire Kahala
    weak = dict(kahala, Mars=4)  # Mars now in Cancer (debilitated), not strong
    assert not fires(chart(weak), "Kahala")
