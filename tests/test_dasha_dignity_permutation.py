"""Tests for the chart-shuffle permutation control.

Pin the null mechanics on two synthetic corpora: one where the chart
genuinely predicts valence (real ≫ null) and one where it cannot
(real indistinguishable from null).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.medini.ml.dasha_dignity_permutation import precompute_quality, run_permutation

# signs: Saturn exalted in Libra(7) for Taurus(2) lagna -> strong;
# Saturn debilitated in Aries(1) for Cancer(4) lagna -> weak.
LIBRA, ARIES, TAURUS, CANCER = 7, 1, 2, 4


def _charts(n_strong: int, n_weak: int) -> pd.DataFrame:
    rows = []
    cols = {f"{l}_sign": LIBRA for l in
            ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu")}
    for i in range(n_strong):
        r = {"person_id": f"S{i}", "asc_sign": TAURUS, **cols}
        rows.append(r)
    weak_cols = {**cols, "saturn_sign": ARIES}
    for i in range(n_weak):
        r = {"person_id": f"W{i}", "asc_sign": CANCER, **weak_cols}
        rows.append(r)
    return pd.DataFrame(rows)


def test_precompute_quality_shape_and_values() -> None:
    charts = _charts(2, 2)
    persons, q = precompute_quality(charts)
    assert q.shape == (4, 9)
    # Saturn column: strong people (idx 0,1) score higher than weak (2,3).
    sat = 6  # _LORDS index of Saturn
    assert q[0, sat] > q[2, sat]


def test_real_gradient_beats_null_when_chart_predicts_valence() -> None:
    # Strong-Saturn people: beneficial prime events. Weak: adverse. Saturn
    # runs as both MD and AD so the pair score tracks the chart.
    charts = _charts(40, 40)
    rows = []
    for i in range(40):
        rows.append({"person_id": f"S{i}", "event_class": "marriage",
                     "event_subtype": "Beneficial", "md_lord_at_event": "Saturn",
                     "ad_lord_at_event": "Saturn", "age_at_event_years": 33.0})
    for i in range(40):
        rows.append({"person_id": f"W{i}", "event_class": "death",
                     "event_subtype": "Adverse", "md_lord_at_event": "Saturn",
                     "ad_lord_at_event": "Saturn", "age_at_event_years": 33.0})
    events = pd.DataFrame(rows)
    r = run_permutation(events, charts, k=200, seed=0)
    assert r["real_gradient"] > 0.5
    assert r["z_score"] > 2.0
    assert r["empirical_p"] <= 0.05
    assert r["exceed_real"] == 0


def test_no_signal_when_valence_independent_of_chart() -> None:
    # Same charts, but valence assigned at random w.r.t. chart quality.
    charts = _charts(40, 40)
    rng = np.random.default_rng(0)
    rows = []
    for grp in ("S", "W"):
        for i in range(40):
            ben = bool(rng.integers(0, 2))
            rows.append({"person_id": f"{grp}{i}",
                         "event_class": "x",
                         "event_subtype": "Beneficial" if ben else "Adverse",
                         "md_lord_at_event": "Saturn", "ad_lord_at_event": "Saturn",
                         "age_at_event_years": 33.0})
    events = pd.DataFrame(rows)
    r = run_permutation(events, charts, k=200, seed=1)
    # Real should sit inside the null cloud, not in the tail.
    assert r["empirical_p"] > 0.05
