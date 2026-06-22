"""Tests for the death-window predictor backtest.

The split helper is tested directly; the end-to-end backtest runs on a small
synthetic in-memory catalog with a *planted* signal (deaths always fall on a
maraka MD window), so the composite lever must show a realized lift > 1 and at
least match the duration-only capture.
"""
from __future__ import annotations

import duckdb
import pytest

from app.medini.analysis import death_backtest as bt
from app.medini.analysis import death_window_predictor as dwp
from app.medini.analysis.death_window_predictor import _role_count

_DPY = 365.2425


def test_in_test_split_stable_and_proportional() -> None:
    ids = [f"P:{i}" for i in range(4000)]
    a = {p for p in ids if bt._in_test(p, 0.25)}
    b = {p for p in ids if bt._in_test(p, 0.25)}
    assert a == b                                   # deterministic
    assert 0.20 < len(a) / len(ids) < 0.30          # ~25%
    # nested: a smaller frac is a subset region of the larger (same hash, lower cut)
    big = {p for p in ids if bt._in_test(p, 0.5)}
    assert a <= big


def _bt_con(n_persons: int = 120) -> duckdb.DuckDBPyConnection:
    """Synthetic catalog: Aries lagna; deaths planted on a Saturn (maraka_full) MD
    in the madhya bracket; control windows use lords in NO death-significator set."""
    asc, lon = 1, 5.0
    gh = {g: 0 for g in dwp._MARAKA_GRAHAS}          # no maraka occupants
    sig = dwp._DEATH_COMPOSITE
    death_lord = "Saturn"                            # always in maraka_full
    assert _role_count(death_lord, asc, lon, gh, sig)[0] >= 1
    # control lords that play none of the three roles for this chart
    controls = [g for g in ("Sun", "Moon", "Mars", "Jupiter", "Rahu", "Ketu")
                if _role_count(g, asc, lon, gh, sig)[0] == 0]
    assert len(controls) >= 4

    con = duckdb.connect()
    chart_cols = (", ".join(f"{g.lower()}_house INT" for g in dwp._MARAKA_GRAHAS) + ", "
                  + ", ".join(f"{g.lower()}_lon DOUBLE" for g in dwp._MARAKA_GRAHAS))
    con.execute("CREATE TABLE charts (person_id TEXT, asc_sign INT, asc_lon DOUBLE, "
                "birth_jd_used DOUBLE, " + chart_cols + ")")
    con.execute("CREATE TABLE dasha_windows (person_id TEXT, md_lord TEXT, ad_lord TEXT, "
                "md_seq INT, ad_seq INT, start_jd DOUBLE, end_jd DOUBLE, duration_days DOUBLE)")
    con.execute("CREATE TABLE events_with_dasha (person_id TEXT, event_class TEXT, "
                "md_lord_at_event TEXT, ad_lord_at_event TEXT, age_at_event_years DOUBLE, "
                "md_seq INT, ad_seq INT, event_jd DOUBLE)")

    ng = len(dwp._MARAKA_GRAHAS)
    cvals = [0] * ng + [0.0] * ng     # 9 house ints + 9 natal-lon doubles
    win_years = 10.0
    death_seq = 4                                    # mid-age 45 → madhya bracket
    for i in range(n_persons):
        bjd = 2_440_000.0 + i
        con.execute("INSERT INTO charts VALUES (?,?,?,?," +
                    ",".join("?" * len(cvals)) + ")",
                    [f"P:{i}", asc, lon, bjd, *cvals])
        for seq in range(6):
            lord = death_lord if seq == death_seq else controls[seq % len(controls)]
            sjd = bjd + seq * win_years * _DPY
            ejd = sjd + win_years * _DPY
            con.execute("INSERT INTO dasha_windows VALUES (?,?,?,?,?,?,?,?)",
                        [f"P:{i}", lord, lord, seq, 0, sjd, ejd, win_years * _DPY])
        d_jd = bjd + (death_seq + 0.5) * win_years * _DPY
        con.execute("INSERT INTO events_with_dasha VALUES (?,?,?,?,?,?,?,?)",
                    [f"P:{i}", "death_cause_unspecified", death_lord, death_lord,
                     45.0, death_seq, 0, d_jd])
    return con


def test_backtest_runs_and_detects_planted_signal() -> None:
    con = _bt_con()
    res = bt.backtest(con, test_frac=0.5)
    d = res.to_dict()

    assert d["n_test_deaths"] > 0 and d["n_train_deaths"] > 0
    # all metrics serializable + in sane ranges
    assert 0.0 <= d["top_decile_capture_m0"] <= 1.0
    assert 0.0 <= d["top_decile_capture_m2"] <= 1.0
    # planted: deaths sit on an above-average-confluence (maraka) window
    assert d["composite_realized_lift"] > 1.0
    # composite can only help (or tie) capture when the signal is planted
    assert d["top_decile_capture_m2"] >= d["top_decile_capture_m0"]
    # composite raised the per-death likelihood (M2 >= M1)
    assert d["loglik_m2"] >= d["loglik_m1"]
    con.close()


def test_backtest_no_planted_signal_is_neutral() -> None:
    # If every window shares one control lord, composite is constant → no lift.
    con = duckdb.connect()
    chart_cols = (", ".join(f"{g.lower()}_house INT" for g in dwp._MARAKA_GRAHAS) + ", "
                  + ", ".join(f"{g.lower()}_lon DOUBLE" for g in dwp._MARAKA_GRAHAS))
    con.execute("CREATE TABLE charts (person_id TEXT, asc_sign INT, asc_lon DOUBLE, "
                "birth_jd_used DOUBLE, " + chart_cols + ")")
    con.execute("CREATE TABLE dasha_windows (person_id TEXT, md_lord TEXT, ad_lord TEXT, "
                "md_seq INT, ad_seq INT, start_jd DOUBLE, end_jd DOUBLE, duration_days DOUBLE)")
    con.execute("CREATE TABLE events_with_dasha (person_id TEXT, event_class TEXT, "
                "md_lord_at_event TEXT, ad_lord_at_event TEXT, age_at_event_years DOUBLE, "
                "md_seq INT, ad_seq INT, event_jd DOUBLE)")
    ng = len(dwp._MARAKA_GRAHAS)
    cvals = [0] * ng + [0.0] * ng
    for i in range(80):
        bjd = 2_440_000.0 + i
        con.execute("INSERT INTO charts VALUES (?,?,?,?," + ",".join("?" * len(cvals)) + ")",
                    [f"P:{i}", 1, 5.0, bjd, *cvals])
        for seq in range(5):
            sjd = bjd + seq * 10 * _DPY
            con.execute("INSERT INTO dasha_windows VALUES (?,?,?,?,?,?,?,?)",
                        [f"P:{i}", "Sun", "Sun", seq, 0, sjd, sjd + 10 * _DPY, 10 * _DPY])
        con.execute("INSERT INTO events_with_dasha VALUES (?,?,?,?,?,?,?,?)",
                    [f"P:{i}", "death_cause_unspecified", "Sun", "Sun", 25.0, 2, 0, bjd + 25 * _DPY])
    res = bt.backtest(con, test_frac=0.5)
    # constant composite → realized lift ≈ 1.0 (no spurious signal)
    assert res.composite_realized_lift == pytest.approx(1.0, abs=1e-6)
    con.close()
