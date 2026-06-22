"""Light tests for the learned death-ranker helpers (no full-corpus XGBoost train)."""
from __future__ import annotations

import pandas as pd

from app.medini.ml import train_death_ranker as tdr


def test_per_lord_flags_shape_and_maraka() -> None:
    # Aries lagna, all planets in house 1, Karakamsa = Aries.
    gh = {g: 1 for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter",
                         "Venus", "Saturn", "Rahu", "Ketu")}
    rows = tdr._per_lord_flags(asc=1, asc_lon=5.0, gh=gh, ak_sign=1)
    assert len(rows) == 9                       # one per dāśā lord
    by_lord = {r[0]: r for r in rows}
    # Saturn is always in maraka_full → f_full flag set
    assert by_lord["Saturn"][1] == 1
    # score is f_full + f_third + f_nav (0..3)
    for r in rows:
        assert 0 <= r[6] <= 3


def test_capture_at_10_perfect_and_random() -> None:
    # Two persons, 10 windows each; the death window has the highest score → captured.
    recs = []
    for pid in ("A", "B"):
        for i in range(10):
            recs.append({"person_id": pid, "is_death": int(i == 0), "s": 10 - i})
    df = pd.DataFrame(recs)
    assert tdr._capture_at_10(df, "s") == 1.0     # death window always top-1
    # reverse: death window is lowest → never in top-10% (k=1)
    df["s2"] = df["is_death"]                       # death window lowest score (0 vs others 0)
    # make non-death strictly higher
    df["s3"] = df.apply(lambda r: 0.0 if r["is_death"] else 1.0, axis=1)
    assert tdr._capture_at_10(df, "s3") == 0.0


def test_features_list_is_stable() -> None:
    assert "mid_age" in tdr._FEATURES and "duration_days" in tdr._FEATURES
    assert "f_sun" in tdr._FEATURES and "f_km" in tdr._FEATURES
