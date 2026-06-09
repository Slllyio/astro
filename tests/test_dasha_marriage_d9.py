"""Tests for the D9 marriage-significator timing test."""
from __future__ import annotations

import pandas as pd

from app.medini.ml.dasha_marriage_d9 import (
    _sig_d1_7L_d9_disp, _sig_d1_7th_lord, _sig_venus_d9_disp, run_d9,
)
from app.medini.ml.dasha_significator_timing import _LORDS

ARIES, TAURUS, LIBRA, SCORPIO = 1, 2, 7, 8


def test_significator_planets() -> None:
    vi = {l: i for i, l in enumerate(_LORDS)}
    # Aries asc → 7th = Libra → Venus.
    row = pd.Series({"asc_sign": ARIES, "venus_d9_sign": LIBRA, "venus_d9_sign_dummy": 0})
    assert _sig_d1_7th_lord(row) == vi["Venus"]
    # Venus in Libra navamsa → dispositor Venus.
    assert _sig_venus_d9_disp(pd.Series({"venus_d9_sign": LIBRA})) == vi["Venus"]
    # D1 7th-lord (Venus) sits in Aries navamsa → dispositor Mars.
    row2 = pd.Series({"asc_sign": ARIES, "venus_d9_sign": ARIES})
    assert _sig_d1_7L_d9_disp(row2) == vi["Mars"]


def _corpus():
    # Two ascendants; marriages half-concentrated under each chart's D1 7th-lord.
    charts = pd.DataFrame([
        {"person_id": "p1", "asc_sign": ARIES},   # 7th lord Venus
        {"person_id": "p2", "asc_sign": TAURUS},  # 7th = Scorpio → Mars
    ])
    d9 = pd.DataFrame([
        {"person_id": "p1", "sun_d9_sign": 1, "moon_d9_sign": 1, "mars_d9_sign": 1,
         "mercury_d9_sign": 1, "jupiter_d9_sign": 1, "venus_d9_sign": LIBRA,
         "saturn_d9_sign": 1, "rahu_d9_sign": 1, "ketu_d9_sign": 1},
        {"person_id": "p2", "sun_d9_sign": 1, "moon_d9_sign": 1, "mars_d9_sign": SCORPIO,
         "mercury_d9_sign": 1, "jupiter_d9_sign": 1, "venus_d9_sign": 1,
         "saturn_d9_sign": 1, "rahu_d9_sign": 1, "ketu_d9_sign": 1},
    ])
    rows = []
    for pid, lord7 in (("p1", "Venus"), ("p2", "Mars")):
        for i in range(40):
            rows.append({"person_id": pid, "event_class": "marriage",
                         "md_lord_at_event": lord7 if i % 2 else "Sun",
                         "age_at_event_years": 30.0})
    return pd.DataFrame(rows), charts, d9


def test_run_d9_structure_and_baseline_signal() -> None:
    events, charts, d9 = _corpus()
    tab = run_d9(events, charts, d9, k=80, seed=0)
    assert set(tab["significator"]) == {
        "d1_7th_lord", "venus_d9_disp", "d1_7L_d9_disp", "d1_7L_or_venus_d9"}
    d1 = tab[tab.significator == "d1_7th_lord"].iloc[0]
    assert d1["obs"] > d1["null"]          # planted 7th-lord signal
    assert {"lift", "z", "p"} <= set(tab.columns)
