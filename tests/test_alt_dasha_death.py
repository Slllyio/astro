"""Tests for the doctrine-mining battery (alternate dashas + significator probe).

Pure-logic tests on the helpers + a tiny synthetic catalog so the dasha/significator
tests run without the full corpus. Also locks in the new validated `maraka_from_sun`
significator.
"""
from __future__ import annotations

import duckdb
import pytest

from app.medini.analysis import alt_dasha_death as ad
from app.medini.analysis import doctrine_validator as dv


def test_share_maps_sum_to_one() -> None:
    assert sum(ad._ASH_SHARE.values()) == pytest.approx(1.0)
    assert sum(ad._YOG_SHARE.values()) == pytest.approx(1.0)
    assert sum(ad._VIM_SHARE.values()) == pytest.approx(1.0)


def test_lord_from_and_sun_sign() -> None:
    # 2nd from Aries (1) is Taurus (2) ruled by Venus
    assert ad._lord_from(1, 2) == "Venus"
    # Sun in 1st house of an Aries lagna → sun_sign = Aries
    assert ad._sun_sign({"asc": 1, "gh": {"Sun": 1}}) == 1
    # Sun in 5th house of Aries → sun_sign = Leo (5)
    assert ad._sun_sign({"asc": 1, "gh": {"Sun": 5}}) == 5


def test_maraka_from_sun_significator_registered() -> None:
    assert "maraka_from_sun" in dv._SIGNIFICATORS
    # Aries lagna, Sun in 1st (sun_sign=Aries): 2nd-from-Sun=Taurus→Venus,
    # 7th-from-Sun=Libra→Venus, +Saturn.
    s = dv._SIGNIFICATORS["maraka_from_sun"](1, 5.0, {"Sun": 1})
    assert s == {"Venus", "Saturn"}


def _battery_con() -> duckdb.DuckDBPyConnection:
    """Aries natives, all dying under a Saturn Vimshottari MD, born so Yogini/Ashtottari
    are well-defined. Saturn is always in maraka_full (natural maraka), so the maraka
    significator must hit ~100%."""
    con = duckdb.connect()
    house_cols = ", ".join(f"{g.lower()}_house INT" for g in dv._MARAKA_GRAHAS)
    lon_cols = ", ".join(f"{g.lower()}_lon DOUBLE" for g in dv._MARAKA_GRAHAS)
    con.execute(f"CREATE TABLE charts (person_id TEXT, asc_sign INT, asc_lon DOUBLE, "
                f"birth_jd_used DOUBLE, moon_nakshatra INT, "
                f"{house_cols}, {lon_cols})")
    con.execute("CREATE TABLE events_with_dasha (person_id TEXT, event_class TEXT, "
                "md_lord_at_event TEXT, event_jd DOUBLE, md_seq INT, ad_seq INT)")
    con.execute("CREATE TABLE jaimini_karakas (person_id TEXT, karaka TEXT, planet TEXT)")
    ng = len(dv._MARAKA_GRAHAS)
    for i in range(150):
        bjd = 2_430_000.0 + i
        con.execute("INSERT INTO charts VALUES (?,?,?,?,?," +
                    ",".join("?" * (2 * ng)) + ")",
                    [f"P:{i}", 1, 5.0, bjd, i % 27, *([1] * ng), *([5.0] * ng)])
        con.execute("INSERT INTO events_with_dasha VALUES (?,?,?,?,?,?)",
                    [f"P:{i}", "death_cause_unspecified", "Saturn", bjd + 50 * 365.2425, 4, 0])
        con.execute("INSERT INTO jaimini_karakas VALUES (?,?,?)",
                    [f"P:{i}", "AK_Atmakaraka", "Jupiter"])
    return con


def test_significator_battery_runs_and_flags_maraka() -> None:
    con = _battery_con()
    res = {r.name: r for r in ad.probe_significators(con)}
    # Saturn MD is always a maraka_full member → ~100% hit, strong support
    assert res["maraka from Lagna (baseline)"].observed == pytest.approx(1.0, abs=0.01)
    assert res["maraka from Lagna (baseline)"].lift > 1.0
    con.close()


def test_dasha_battery_runs() -> None:
    con = _battery_con()
    res = ad.run(con)
    names = {r.name for r in res}
    assert any("Ashtottari" in n for n in names) and any("Yogini" in n for n in names)
    for r in res:
        assert r.n >= 0 and r.expected >= 0.0
    con.close()
