"""Tests for the house-lordship → event-class lift analysis."""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.medini.ml.dasha_houselord_class import (
    _ruled_lookup, _rules_house, run_analysis,
)
from app.medini.ml.dasha_significator_timing import _LORDS


def test_ruled_lookup_mars_aries_lagna() -> None:
    R = _ruled_lookup()
    mars = _LORDS.index("Mars")
    # Mars owns Aries(1) & Scorpio(8); from Aries lagna those are houses 1 and 8.
    mask = R[mars, 1 - 1]
    assert mask & (1 << 0)   # house 1
    assert mask & (1 << 7)   # house 8
    assert not mask & (1 << 6)  # house 7 not ruled by Mars for Aries asc


def test_rules_house_vector() -> None:
    R = _ruled_lookup()
    md = np.array([_LORDS.index("Venus")])   # Venus owns Taurus(2), Libra(7)
    asc = np.array([1])                       # Aries lagna → Libra is 7th
    assert _rules_house(md, asc, 7, R)[0]     # Venus rules the 7th
    assert not _rules_house(md, asc, 10, R)[0]


def _corpus():
    charts = pd.DataFrame([
        {"person_id": "p1", "asc_sign": 1},   # 7th lord = Venus
        {"person_id": "p2", "asc_sign": 2},   # 7th lord = Mars
    ])
    rows = []
    for pid, lord7 in (("p1", "Venus"), ("p2", "Mars")):
        # marriages concentrated under that chart's 7th lord; deaths under Saturn
        for i in range(60):
            rows.append({"person_id": pid, "event_class": "marriage",
                         "md_lord_at_event": lord7 if i % 2 else "Sun",
                         "age_at_event_years": 30.0})
        for i in range(60):
            rows.append({"person_id": pid, "event_class": "career",
                         "md_lord_at_event": "Mercury", "age_at_event_years": 35.0})
    return pd.DataFrame(rows), charts


def test_run_analysis_keys_and_marriage_cell() -> None:
    events, charts = _corpus()
    res = run_analysis(events, charts, k=80, seed=0)
    assert {"canonical_cells", "diagonal_lift", "z", "p"} <= set(res)
    mar = [c for c in res["canonical_cells"] if c["class"] == "marriage"]
    assert mar and mar[0]["obs"] >= 0
    # marriage obs share should exceed the chart-shuffle null (planted signal)
    assert mar[0]["lift"] is None or mar[0]["lift"] >= 1.0
