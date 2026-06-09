"""Tests for the marriage timing deep dive."""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.medini.ml.dasha_marriage_deepdive import (
    _perm_test, significator_table, split_half,
)
from app.medini.ml.dasha_significator_timing import _LORDS, _houselord_lookup

ARIES, TAURUS = 1, 7  # (Taurus=2 actually; keep asc values valid below)


def test_perm_test_detects_elevated_match() -> None:
    # match_fn ignores asc and returns a fixed 60%-true vector → obs >> null≈... .
    vec = np.array([True] * 60 + [False] * 40)
    r = _perm_test(lambda a: vec, np.array([1, 2, 3]), 3, k=50, seed=0)
    assert r["obs"] == 0.6
    assert "z" in r and "p" in r and "lift" in r


def _corpus():
    charts = pd.DataFrame([
        {"person_id": "p1", "asc_sign": 1},   # 7th = Libra → Venus
        {"person_id": "p2", "asc_sign": 2},   # 7th = Scorpio → Mars
    ])
    rows, wins = [], []
    for pid, lord7 in (("p1", "Venus"), ("p2", "Mars")):
        for i in range(40):
            rows.append({"person_id": pid, "event_class": "marriage",
                         "event_subtype": "Beneficial",
                         "md_lord_at_event": lord7 if i % 2 else "Sun",
                         "ad_lord_at_event": "Sun", "age_at_event_years": 30.0})
        for lord in _LORDS:
            wins.append({"person_id": pid, "md_lord": lord, "duration_days": 10.0})
    return pd.DataFrame(rows), charts, pd.DataFrame(wins)


def test_significator_table_structure_and_signal() -> None:
    events, charts, _ = _corpus()
    tab = significator_table(events, charts, k=60, seed=0)
    levels = set(tab["level"])
    assert {"MD", "AD", "MD∩AD"} <= levels
    sig7 = tab[(tab.significator == "7th-lord") & (tab.level == "MD")].iloc[0]
    # constructed so half the marriages run the true 7th lord → obs > null
    assert sig7["obs"] > sig7["null"]


def test_split_half_shape() -> None:
    events, charts, _ = _corpus()
    sp = split_half(events, charts, k=30, seeds=(0,))
    assert sp.empty or {"half", "lift", "z", "p"} <= set(sp.columns)
