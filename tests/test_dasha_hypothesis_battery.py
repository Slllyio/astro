"""Tests for the pre-registered hypothesis battery harness."""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.medini.ml.dasha_hypothesis_battery import (
    _bh_fdr, _rate, build_registry, run_battery,
)
from app.medini.ml.dasha_significator_timing import _LORDS, _houselord_lookup


def test_registry_is_large_and_well_formed() -> None:
    reg = build_registry()
    assert len(reg) >= 100                       # ~exhaustive
    assert len({h["id"] for h in reg}) == len(reg)  # unique ids
    assert {h["type"] for h in reg} == {"sig_md", "sig_ad", "karaka", "age", "d9"}
    assert all("label" in h and "event_class" in h for h in reg)


def test_bh_fdr_step_up() -> None:
    # three tiny p's + many large → the tiny ones pass, large ones fail.
    p = [0.001, 0.002, 0.003] + [0.6] * 17
    passed = _bh_fdr(p, alpha=0.05)
    assert passed[:3] == [True, True, True]
    assert not any(passed[3:])
    # all-null → none pass
    assert not any(_bh_fdr([0.5] * 10))


def test_rate_vectorised_matcher() -> None:
    L = _houselord_lookup()
    idx = {l: i for i, l in enumerate(_LORDS)}
    # Aries asc (1): 7th = Libra = Venus. Event MD = Venus → matches house 7.
    asc_pp = np.array([1])
    pe = np.array([0, 0])
    lord = np.array([idx["Venus"], idx["Mars"]])
    assert _rate(asc_pp, pe, 7, lord, L) == 0.5   # one of two matches


def _corpus():
    charts = pd.DataFrame([
        {"person_id": "p1", "asc_sign": 1},
        {"person_id": "p2", "asc_sign": 4},
    ])
    d9 = pd.DataFrame([{"person_id": p, **{f"{g}_d9_sign": 1 for g in (
        "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn",
        "rahu", "ketu")}} for p in ("p1", "p2")])
    rows, wins = [], []
    for pid in ("p1", "p2"):
        for cls in ("marriage", "career", "death", "relationship", "family",
                    "health", "education", "divorce", "personal"):
            for i in range(80):
                rows.append({"person_id": pid, "event_class": cls,
                             "md_lord_at_event": _LORDS[i % 9],
                             "ad_lord_at_event": _LORDS[(i + 1) % 9],
                             "age_at_event_years": 30.0 + i % 40})
        for lord in _LORDS:
            wins.append({"person_id": pid, "md_lord": lord, "duration_days": 13.3})
    return pd.DataFrame(rows), charts, d9, pd.DataFrame(wins)


def test_run_battery_end_to_end_smoke() -> None:
    events, charts, d9, windows = _corpus()
    df = run_battery(events, charts, d9, windows, k=30, seed=0)
    assert len(df) >= 100
    assert "fdr_pass" in df.columns
    assert df["p"].between(0, 1).all()
    # random md assignment → essentially no real signal; FDR survivors should be few
    assert int(df["fdr_pass"].sum()) <= 5
