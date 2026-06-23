"""Tests for the manner-of-death stratified signal hunt.

Pure-logic tests on the label mapping + a tiny synthetic catalog so the stratified
report runs without the full corpus.
"""
from __future__ import annotations

import duckdb
import pytest

from app.medini.analysis import doctrine_validator as dv
from app.medini.analysis import manner_of_death as md


def test_manner_label_maps_and_skips_longevity() -> None:
    con = duckdb.connect()
    con.execute("CREATE TABLE person_attributes (person_id TEXT, root TEXT, field TEXT, "
                "detail TEXT, source TEXT)")
    rows = [
        ("A", "Suicide"), ("B", "Accidental"), ("C", "Illness/ Disease"),
        ("D", "Unusual"), ("E", "Other Death"),
        ("F", "Long life more than 80 yrs"),          # longevity tag → no manner
        ("G", "Other Death"), ("G", "Suicide"),       # concrete beats 'other'
    ]
    for pid, detail in rows:
        con.execute("INSERT INTO person_attributes VALUES (?,?,?,?,?)",
                    [pid, "Death", "Death", detail, "holos"])
    lab = md.manner_label(con)
    assert lab == {"A": "suicide", "B": "accidental", "C": "illness",
                   "D": "unusual", "E": "other", "G": "suicide"}
    assert "F" not in lab                              # longevity excluded
    con.close()


def test_excess_is_zero_minus_share() -> None:
    # MD-lord not in the killer set → excess = −share(set)
    r = {"md": "Sun", "asc": 1, "gh": {}}
    e = md._excess(r, lambda _r: {"Mars"})
    assert e == pytest.approx(-dv.LORD_SHARE["Mars"])
    # MD-lord in the set → excess = 1 − share(set)
    r2 = {"md": "Mars", "asc": 1, "gh": {}}
    e2 = md._excess(r2, lambda _r: {"Mars"})
    assert e2 == pytest.approx(1.0 - dv.LORD_SHARE["Mars"])
    # empty killer set → None (skipped)
    assert md._excess(r, lambda _r: set()) is None


def _manner_con() -> duckdb.DuckDBPyConnection:
    """Aries natives; unnatural deaths die under a Mars MD (a violent karaka), natural
    deaths under Jupiter (not a violent karaka) — so the contrast must point positive."""
    con = duckdb.connect()
    house_cols = ", ".join(f"{g.lower()}_house INT" for g in dv._MARAKA_GRAHAS)
    lon_cols = ", ".join(f"{g.lower()}_lon DOUBLE" for g in dv._MARAKA_GRAHAS)
    con.execute(f"CREATE TABLE charts (person_id TEXT, asc_sign INT, asc_lon DOUBLE, "
                f"{house_cols}, {lon_cols})")
    con.execute("CREATE TABLE events_with_dasha (person_id TEXT, event_class TEXT, "
                "md_lord_at_event TEXT, event_jd DOUBLE)")
    con.execute("CREATE TABLE jaimini_karakas (person_id TEXT, karaka TEXT, planet TEXT)")
    con.execute("CREATE TABLE person_attributes (person_id TEXT, root TEXT, field TEXT, "
                "detail TEXT, source TEXT)")
    ng = len(dv._MARAKA_GRAHAS)
    for i in range(120):
        pid = f"P:{i}"
        con.execute("INSERT INTO charts VALUES (?,?,?," + ",".join("?" * (2 * ng)) + ")",
                    [pid, 1, 5.0, *([1] * ng), *([5.0] * ng)])
        if i % 2 == 0:                                # unnatural, Mars MD
            md_lord, detail = "Mars", "Accidental"
        else:                                         # natural, Jupiter MD
            md_lord, detail = "Jupiter", "Illness/ Disease"
        con.execute("INSERT INTO events_with_dasha VALUES (?,?,?,?)",
                    [pid, "death_cause_unspecified", md_lord, 2_430_000.0 + i])
        con.execute("INSERT INTO jaimini_karakas VALUES (?,?,?)",
                    [pid, "AK_Atmakaraka", "Jupiter"])
        con.execute("INSERT INTO person_attributes VALUES (?,?,?,?,?)",
                    [pid, "Death", "Death", detail, "holos"])
    return con


def test_report_runs_and_contrast_positive() -> None:
    con = _manner_con()
    rep = md.manner_stratified_report(con)
    assert rep["counts"]["accidental"] == 60 and rep["counts"]["illness"] == 60
    assert "per_manner" in rep and "contrasts" in rep
    mars = next(c for c in rep["contrasts"] if c["name"] == "Mars (violence)")
    # unnatural deaths all under Mars MD → Mars clusters more for unnatural than natural
    assert mars["diff"] > 0
    assert set(rep["composite_perm"]) == {"diff", "n_perm", "p_perm"}
    con.close()
