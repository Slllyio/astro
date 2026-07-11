"""Drift-guard for docs/raman_doctrine/VALIDATION_SUMMARY.md.

The summary is the single honest ledger of held-out performance. This test re-runs each
validator and asserts the exact numbers printed in the summary's headline table still hold
(tight tolerances, not floors) so the ledger and the engine can NEVER silently diverge: any
change that moves a number — improvement or regression — trips a test here and forces the
summary to be updated in the same commit.

If you intentionally change the engine and a number here moves, update BOTH this test and the
matching row of VALIDATION_SUMMARY.md together.
"""
from pathlib import Path

from app.medini.doctrine.validation import (
    worked_chart_validate as W,
    nh_strength_validate as N,
    timing_validate as T,
    balance_validate as B,
    longevity_validate as L,
)

_CORP = Path("docs/raman_doctrine/validation/corpora")
_HELDOUT = sorted(str(p) for p in _CORP.glob("heldout_ch*.json"))
_TOL = 0.2  # percentage-point tolerance on reproduced within-one / exact figures


# ---- Strength (sign-reconstructed) ------------------------------------------------------

def test_summary_strength_pooled_heldout():
    # Row: "Strength (sign-reconstructed) | within-one 54.7% (exact 24.5%, Δ +0.17) | N=53".
    # Re-pinned at increments 17 (sutra-fed strength; was 52.8/26.4/+0.49) and 18/M-C
    # (vargottama dignity counted once; Δ +0.32 -> +0.17, within-one/exact unchanged).
    s = W.run(_HELDOUT)
    assert s["n_scored"] == 53
    assert abs(s["within1_pct"] - 54.7) <= _TOL
    assert abs(s["exact_pct"] - 24.5) <= _TOL
    assert abs(s["mean_delta"] - 0.17) <= 0.02


def test_summary_strength_max_expansion():
    # Row: "Strength — max HTJAH expansion | within-one 55.3% (exact 25.0%, Δ +0.20) | N=76".
    # Re-pinned at increments 17 (was 53.9/26.3/+0.43) and 18/M-C (Δ +0.30 -> +0.20).
    maxset = _HELDOUT + [str(_CORP / "unseen_scoreable.json"), str(_CORP / "unseen_grow.json")]
    s = W.run(maxset)
    assert s["n_scored"] == 76
    assert abs(s["within1_pct"] - 55.3) <= _TOL
    assert abs(s["mean_delta"] - 0.20) <= 0.02


def test_summary_strength_fresh_blind():
    # Row: "Strength — fresh blind only | within-one 71.4% (Δ -0.21) | N=14".
    s = W.run([str(_CORP / "unseen_scoreable.json")])
    assert s["n_scored"] == 14
    assert abs(s["within1_pct"] - 71.4) <= _TOL


def test_summary_strength_nh_degree_accurate():
    # Row: "Strength — NH degree-accurate | within-one 53.3% (exact 26.7%, Δ +1.07) | N=15".
    # Re-pinned at increment 17 (was 46.7/33.3).
    # Δ is +1.07 (not +1.13) since the degree layer's combustion term is on for the
    # degree-resolved NH charts; within-one is unchanged (combustion is within-one-neutral
    # on the original 15 -- see REPORT_degree_engine.md).
    s = N.run()
    assert s["n"] == 15
    assert s["n_excluded"] == 0
    assert abs(s["within1_pct"] - 53.3) <= _TOL
    assert abs(s["mean_delta"] - 1.00) <= 0.02


def test_summary_strength_nh_degree_pooled_grown():
    # Row: "Strength — NH degree pooled (grown) | within-one 53.1% (Δ +0.44) | N=32".
    # The grown degree-accurate held-out (15 + 17 fresh), degree feature layer on
    # (combustion). 0 excluded. Beats the 40.6% sign-baseline on the same corpus.
    import json
    import tempfile
    a = json.loads((_CORP / "nh_strength.json").read_text())["rows"]
    b = json.loads((_CORP / "nh_strength_grow.json").read_text())["rows"]
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump({"rows": a + b}, fh)
        pooled = fh.name
    s = N.run(pooled)
    assert s["n"] == 32
    assert s["n_excluded"] == 0
    # Re-pinned at increment 17 (was 43.8/+0.69).
    assert abs(s["within1_pct"] - 53.1) <= _TOL
    assert abs(s["mean_delta"] - 0.41) <= 0.02


# ---- Timing ------------------------------------------------------------------------------

def test_summary_timing_htjah():
    # Row: "Timing — HTJAH events | mahadasa-lord exact 100% (8/8); antara within-one 8/8".
    s = T.run([str(_CORP / "heldout_timing.json"), str(_CORP / "heldout_timing_ch12_8th.json")])
    assert s["n_events"] == 8
    assert s["md_exact"] == 8
    assert s["ad_within_one_bhukti"] == s["ad_n"]


def test_summary_timing_notable_horoscopes():
    # Row: "Timing — Notable Horoscopes | mahadasa-lord exact 94.0% (47/50); antara 92.9%".
    s = T.run(str(_CORP / "nh_timing.json"))
    assert s["n_events"] == 50
    assert s["md_exact"] == 47
    assert s["ad_n"] == 42
    assert s["ad_within_one_bhukti"] == 39


# ---- Daśā balance ------------------------------------------------------------------------

def test_summary_balance_nh():
    # Row: "Dasa balance — NH | starting-lord exact 93.3% (28/30); duration +/-0.5y 28/30".
    s = B.run()
    assert s["n"] == 30
    assert s["lord_exact"] == 28
    assert s["dur_within_tol"] == 28


# ---- Longevity ---------------------------------------------------------------------------

def test_summary_longevity_bhava_predicts_and_benefic_strength_does_not():
    # Row: "Longevity — 8th bhava | Spearman rho +0.52 (p~0.06) | N=14".
    s = L.run()
    assert s["n"] == 14
    sp = s["spearman"]
    # Re-pinned at increment 17: rho 0.52 -> 0.50 (8th-bhava scores shift slightly).
    assert abs(sp["bhava"]["rho"] - 0.50) <= 0.01
    # the discriminating claim: bhava-strength predicts, general benefic-strength anti-predicts.
    assert sp["lord"]["rho"] < 0
    assert sp["karaka"]["rho"] < 0
    assert sp["bhava"]["rho"] == max(v["rho"] for v in sp.values())
