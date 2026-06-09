"""Tests for app.medini.ml.dasha_event_associations.

Pin the exposure baselines, the lift/binomial association maths, the
min-support gate, and the MD×AD pair table — these are the rules the
descriptive "which lord makes which event" finding rests on.
"""
from __future__ import annotations

import pandas as pd
import pytest

from app.medini.ml.dasha_event_associations import (
    compute_lord_associations,
    compute_pair_associations,
    measured_exposure,
    nominal_exposure,
    run,
)


# ---------- baselines ----------

def test_nominal_exposure_sums_to_one_and_weights_by_years() -> None:
    exp = nominal_exposure()
    assert abs(sum(exp.values()) - 1.0) < 1e-9
    # Venus (20 yr) must be the largest, Sun (6 yr) the smallest.
    assert max(exp, key=exp.get) == "Venus"
    assert min(exp, key=exp.get) == "Sun"
    assert exp["Venus"] == pytest.approx(20 / 120)
    assert exp["Sun"] == pytest.approx(6 / 120)


def test_measured_exposure_from_windows() -> None:
    windows = pd.DataFrame({
        "md_lord": ["Venus", "Venus", "Sun", "Mars"],
        "duration_days": [100.0, 100.0, 50.0, 50.0],
    })
    exp = measured_exposure(windows, "md_lord")
    assert exp["Venus"] == pytest.approx(200 / 300)
    assert exp["Sun"] == pytest.approx(50 / 300)
    assert abs(sum(exp.values()) - 1.0) < 1e-9


def test_measured_exposure_rejects_missing_columns() -> None:
    with pytest.raises(KeyError):
        measured_exposure(pd.DataFrame({"md_lord": ["Venus"]}), "md_lord")


# ---------- single-lord associations ----------

def _events(md: list[str], cls: list[str]) -> pd.DataFrame:
    return pd.DataFrame({
        "event_class": cls,
        "md_lord_at_event": md,
        "ad_lord_at_event": md,  # reuse for convenience
    })


def test_lift_above_one_for_injected_signal() -> None:
    """50 marriages all under Venus → Venus lift >> 1 vs its ~16.7% base."""
    ev = _events(["Venus"] * 50, ["marriage"] * 50)
    out = compute_lord_associations(
        ev, "md_lord_at_event", nominal_exposure(), min_support=5
    )
    venus = out[out["lord"] == "Venus"].iloc[0]
    assert venus["observed_share"] == 1.0
    assert venus["lift"] > 1.0
    # 100% observed vs 16.7% baseline over n=50 is wildly significant.
    assert venus["p_value"] < 1e-6


def test_lift_near_one_when_matching_baseline() -> None:
    """Events drawn in proportion to exposure → every lift ≈ 1, no
    cell significant."""
    exp = nominal_exposure()
    md, cls = [], []
    # 1200 events split exactly by nominal years (Venus 200, Sun 60, ...).
    for lord, years in [("Venus", 20), ("Sun", 6), ("Moon", 10),
                        ("Saturn", 19), ("Mercury", 17), ("Jupiter", 16),
                        ("Rahu", 18), ("Mars", 7), ("Ketu", 7)]:
        n = years * 10
        md += [lord] * n
        cls += ["mixed"] * n
    out = compute_lord_associations(
        _events(md, cls), "md_lord_at_event", exp, min_support=5
    )
    assert (out["lift"].sub(1.0).abs() < 0.01).all()
    assert (out["p_value"] > 0.05).all()


def test_min_support_drops_sparse_cells() -> None:
    ev = _events(["Venus"] * 50 + ["Sun"] * 3, ["x"] * 53)
    out = compute_lord_associations(
        ev, "md_lord_at_event", nominal_exposure(), min_support=5
    )
    assert "Venus" in set(out["lord"])
    assert "Sun" not in set(out["lord"])  # only 3 < 5


def test_observed_shares_sum_within_class() -> None:
    ev = _events(["Venus"] * 30 + ["Mars"] * 30, ["e"] * 60)
    out = compute_lord_associations(
        ev, "md_lord_at_event", nominal_exposure(), min_support=5
    )
    assert out["observed_share"].sum() == pytest.approx(1.0)


# ---------- pair associations ----------

def test_pair_association_lift_and_columns() -> None:
    ev = pd.DataFrame({
        "event_class": ["marriage"] * 20,
        "md_lord_at_event": ["Venus"] * 20,
        "ad_lord_at_event": ["Jupiter"] * 20,
    })
    exp = nominal_exposure()
    out = compute_pair_associations(ev, exp, exp, min_support=5)
    row = out.iloc[0]
    assert row["lord"] == "Venus/Jupiter"
    assert row["md_lord"] == "Venus" and row["ad_lord"] == "Jupiter"
    # base = P(Venus)*P(Jupiter); observed share = 1.0 → strong lift.
    assert row["lift"] > 1.0
    assert row["scope"] == "md_ad_pair"


# ---------- end-to-end ----------

def test_run_writes_outputs(tmp_path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    # Minimal events_with_dasha parquet: marriages skew to Venus.
    ev = pd.DataFrame({
        "event_class": ["marriage"] * 40 + ["death"] * 40,
        "md_lord_at_event": ["Venus"] * 40 + ["Saturn"] * 40,
        "ad_lord_at_event": ["Jupiter"] * 40 + ["Mars"] * 40,
    })
    ev.to_parquet(data_dir / "events_with_dasha.parquet", index=False)

    out_dir = tmp_path / "out"
    stats = run(data_dir, out_dir, baseline="nominal", min_support=5)

    assert stats["events"] == 80
    assert (out_dir / "dasha_event_associations.csv").exists()
    md = (out_dir / "dasha_event_associations.md").read_text(encoding="utf-8")
    assert "Dasha → event associations" in md
    assert "Venus" in md and "marriage" in md
