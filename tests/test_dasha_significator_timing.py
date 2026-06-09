"""Tests for the significator-timing test (chart-specific dasha timing)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.medini.ml.dasha_significator_timing import (
    _bhavas_for,
    _houselord_lookup,
    _houselord_match,
    measured_md_exposure_by_person,
    run_timing,
)

ARIES, TAURUS, LIBRA = 1, 2, 7


def test_houselord_lookup_known_cells() -> None:
    L = _houselord_lookup()
    from app.medini.ml.dasha_significator_timing import _LORDS
    idx = {l: i for i, l in enumerate(_LORDS)}
    # Aries asc: 7th house = Libra → Venus. 10th house = Capricorn → Saturn.
    assert L[ARIES - 1, 7 - 1] == idx["Venus"]
    assert L[ARIES - 1, 10 - 1] == idx["Saturn"]
    # Taurus asc: 1st house = Taurus → Venus.
    assert L[TAURUS - 1, 1 - 1] == idx["Venus"]


def test_bhavas_for_classes() -> None:
    assert _bhavas_for("marriage") == (7,)
    assert _bhavas_for("career") == (10,)
    assert _bhavas_for("death") == (8,)
    assert _bhavas_for(None) == (1,)
    assert _bhavas_for("nonsense") == (1,)


def test_measured_exposure_sums_to_one() -> None:
    windows = pd.DataFrame([
        {"person_id": "p1", "md_lord": "Venus", "duration_days": 20.0},
        {"person_id": "p1", "md_lord": "Saturn", "duration_days": 19.0},
        {"person_id": "p1", "md_lord": "Sun", "duration_days": 6.0},
    ])
    exp = measured_md_exposure_by_person(windows, "md_lord")
    assert abs(exp["p1"].sum() - 1.0) < 1e-9
    from app.medini.ml.dasha_significator_timing import _LORDS
    vi = _LORDS.index("Venus")
    assert exp["p1"][vi] == 20.0 / 45.0


def test_houselord_match_logic() -> None:
    from app.medini.ml.dasha_significator_timing import _LORDS
    idx = {l: i for i, l in enumerate(_LORDS)}
    L = _houselord_lookup()
    # one event: Aries-asc person, marriage (7th=Libra=Venus), MD=Venus → match.
    asc = np.array([ARIES])
    pe = np.array([0])
    bhavas = [(7,)]
    lord = np.array([idx["Venus"]])
    assert _houselord_match(asc, pe, bhavas, lord, L)[0]
    # MD=Mars → no match for Aries 7th.
    assert not _houselord_match(asc, pe, bhavas, np.array([idx["Mars"]]), L)[0]


def _corpus():
    # Two ascendants so house-lords differ across people.
    charts = pd.DataFrame([
        {"person_id": "p1", "asc_sign": ARIES},   # 7th lord = Venus
        {"person_id": "p2", "asc_sign": TAURUS},  # 7th lord = Mars
    ])
    rows, wins = [], []
    for pid, lord7 in (("p1", "Venus"), ("p2", "Mars")):
        for i in range(30):
            rows.append({"person_id": pid, "event_class": "marriage",
                         "event_subtype": "Beneficial",
                         # half the marriages under the true 7th lord
                         "md_lord_at_event": lord7 if i % 2 else "Sun",
                         "ad_lord_at_event": "Sun", "age_at_event_years": 30.0})
        for lord, dur in (("Venus", 20.0), ("Mars", 7.0), ("Sun", 6.0),
                          ("Saturn", 19.0)):
            wins.append({"person_id": pid, "md_lord": lord, "duration_days": dur})
    return pd.DataFrame(rows), charts, pd.DataFrame(wins)


def test_run_timing_shape_and_signal() -> None:
    events, charts, windows = _corpus()
    tab = run_timing(events, charts, windows, k=50, seed=0)
    assert "marriage" in tab["event_class"].values
    r = tab[tab.event_class == "marriage"].iloc[0]
    # constructed: 7th-lord match rate (~0.5) should exceed the chart-shuffle null
    assert r["houselord_md_obs"] > r["houselord_md_null"]
    assert {"houselord_md_z", "houselord_md_p", "karaka_md_lift"} <= set(tab.columns)
