"""Tests for the Doctrine Validator core + API.

Builds a tiny synthetic DuckDB (person_labels + chart_yogas) with a *known*
association so the lift/p-value math is checkable, then exercises both the service
functions and the FastAPI router (mounted standalone — no app.main dependency).
"""
from __future__ import annotations

import duckdb
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.doctrine_routes import doctrine_router, get_con
from app.medini.analysis import doctrine_validator as dv


def _synthetic_con() -> duckdb.DuckDBPyConnection:
    """200 people: 100 with 'StrongYoga' (80% famous), 100 without (20% famous).
    Baseline = 0.50; condition cohort should show a large positive lift."""
    con = duckdb.connect(":memory:")
    con.execute("CREATE TABLE person_labels (person_id TEXT, is_famous BOOLEAN, has_award BOOLEAN)")
    con.execute("CREATE TABLE chart_yogas (person_id TEXT, yoga TEXT)")
    rows = []
    for i in range(100):  # cohort with yoga: 80 famous
        rows.append((f"y{i}", i < 80, False))
    for i in range(100):  # without yoga: 20 famous
        rows.append((f"n{i}", i < 20, False))
    con.executemany("INSERT INTO person_labels VALUES (?, ?, ?)", rows)
    con.executemany("INSERT INTO chart_yogas VALUES (?, ?)",
                    [(f"y{i}", "StrongYoga") for i in range(100)])
    return con


def test_validate_yoga_detects_strong_positive_effect() -> None:
    con = _synthetic_con()
    res = dv.validate_yoga(con, "StrongYoga", "is_famous")
    assert res.n_condition == 100
    assert res.condition_rate == pytest.approx(0.80)
    assert res.baseline_rate == pytest.approx(0.50)
    assert res.lift == pytest.approx(1.6, abs=0.01)
    assert res.p_value < 0.001          # highly significant
    assert res.verdict == "supports"


def test_null_effect_outcome() -> None:
    con = _synthetic_con()
    res = dv.validate_yoga(con, "StrongYoga", "has_award")  # nobody has awards
    assert res.condition_rate == 0.0
    assert res.verdict in ("no-effect", "insufficient-n")


def test_unknown_outcome_raises() -> None:
    con = _synthetic_con()
    with pytest.raises(ValueError):
        dv.validate_yoga(con, "StrongYoga", "not_a_column")


def test_scan_sorts_by_lift() -> None:
    con = _synthetic_con()
    results = dv.scan_yogas(con, "is_famous")
    assert results[0].condition == "yoga:StrongYoga"
    assert results == sorted(results, key=lambda r: r.lift, reverse=True)


# ------------------------------- API ------------------------------- #

def _timing_con() -> duckdb.DuckDBPyConnection:
    """events_with_dasha where deaths over-cluster under Saturn MD and the
    'StrongYoga' cohort dies ~10y later."""
    con = duckdb.connect(":memory:")
    con.execute("""CREATE TABLE events_with_dasha
        (event_id INT, person_id TEXT, event_class TEXT,
         md_lord_at_event TEXT, ad_lord_at_event TEXT, age_at_event_years DOUBLE)""")
    con.execute("CREATE TABLE chart_yogas (person_id TEXT, yoga TEXT)")
    rows, eid = [], 0
    # 300 Saturn-MD deaths (age ~80), 100 Venus-MD deaths (age ~70); jittered so
    # the within-cohort variance is non-zero (the t-test needs spread).
    for i in range(300):
        rows.append((eid := eid + 1, f"s{eid}", "death_cause_unspecified", "Saturn", "Sun", 80.0 + (i % 7) - 3))
    for i in range(100):
        rows.append((eid := eid + 1, f"v{eid}", "death_cause_unspecified", "Venus", "Sun", 70.0 + (i % 7) - 3))
    con.executemany("INSERT INTO events_with_dasha VALUES (?,?,?,?,?,?)", rows)
    # tag the Saturn cohort with a yoga (so age-shift sees later deaths)
    con.executemany("INSERT INTO chart_yogas VALUES (?, ?)",
                    [(r[1], "StrongYoga") for r in rows if r[3] == "Saturn"])
    return con


def test_dasha_timing_flags_overclustered_lord() -> None:
    con = _timing_con()
    res = dv.validate_dasha_timing(con, "death_cause_unspecified", "md")
    by_lord = {r.lord: r for r in res}
    # Saturn: observed 300/400 = 0.75 vs natural share 19/120 ~ 0.158 -> big lift, significant
    assert by_lord["Saturn"].lift > 3
    assert by_lord["Saturn"].p_value < 0.001
    assert by_lord["Saturn"].verdict == "supports"
    # results sorted by lift descending
    assert res == sorted(res, key=lambda r: r.lift, reverse=True)


def test_age_shift_detects_later_deaths() -> None:
    con = _timing_con()
    res = dv.validate_age_shift(con, "death_cause_unspecified", yoga="StrongYoga")
    assert res.mean_age_cohort == pytest.approx(80.0, abs=0.6)
    assert res.mean_age_rest == pytest.approx(70.0, abs=0.6)
    assert res.diff_years == pytest.approx(10.0, abs=0.6)
    assert res.p_value < 0.001
    assert res.verdict == "later"


def _maraka_con() -> duckdb.DuckDBPyConnection:
    """Leo-Lagna natives whose deaths all run under Saturn MD. For Leo, the 7th
    lord is Saturn (a maraka) -> the maraka-MD rate should be ~100%."""
    con = duckdb.connect(":memory:")
    con.execute("""CREATE TABLE events_with_dasha
        (event_id INT, person_id TEXT, event_class TEXT, md_lord_at_event TEXT, ad_lord_at_event TEXT)""")
    house_cols = ", ".join(f"{g}_house INT" for g in
                           ("sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"))
    con.execute(f"CREATE TABLE charts (person_id TEXT, asc_sign INT, {house_cols})")
    ew, ch = [], []
    for i in range(200):
        ew.append((i, f"p{i}", "death_cause_unspecified", "Saturn", "Mercury"))
        ch.append((f"p{i}", 5, *([1] * 9)))  # Leo ascendant; all grahas in house 1 (no 2/7 occupants)
    con.executemany("INSERT INTO events_with_dasha VALUES (?,?,?,?,?)", ew)
    con.executemany("INSERT INTO charts VALUES (?,?,?,?,?,?,?,?,?,?,?)", ch)
    return con


def test_maraka_detects_seventh_lord_dasha() -> None:
    con = _maraka_con()
    res = dv.validate_maraka(con, "death_cause_unspecified", "md")
    # Leo: 2nd lord Mercury, 7th lord Saturn -> all-Saturn deaths => 100% maraka
    assert res.observed_rate == pytest.approx(1.0)
    assert res.lift > 1.5
    assert res.verdict == "supports"
    # per-ascendant breakdown present for Leo (sign 5)
    leo = next(b for b in res.by_ascendant if b["asc_sign"] == 5)
    assert leo["seventh_lord"] == "Saturn"
    assert leo["maraka_rate"] == pytest.approx(1.0)


@pytest.mark.asyncio
async def test_maraka_endpoint() -> None:
    app = FastAPI()
    app.include_router(doctrine_router)
    con = _maraka_con()
    app.dependency_overrides[get_con] = lambda: con
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://t") as ac:
        r = await ac.get("/medini/doctrine/maraka",
                         params={"event_class": "death_cause_unspecified", "level": "md"})
        assert r.status_code == 200
        assert r.json()["verdict"] == "supports"
        assert any(b["asc_sign"] == 5 for b in r.json()["by_ascendant"])
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_validate_endpoint() -> None:
    app = FastAPI()
    app.include_router(doctrine_router)
    con = _synthetic_con()
    app.dependency_overrides[get_con] = lambda: con

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://t") as ac:
        r = await ac.get("/medini/doctrine/validate",
                         params={"yoga": "StrongYoga", "outcome": "is_famous"})
        assert r.status_code == 200
        body = r.json()
        assert body["lift"] == pytest.approx(1.6, abs=0.01)
        assert body["verdict"] == "supports"

        # missing condition -> 422
        r2 = await ac.get("/medini/doctrine/validate", params={"outcome": "is_famous"})
        assert r2.status_code == 422

        # outcomes list
        r3 = await ac.get("/medini/doctrine/outcomes")
        assert "is_famous" in r3.json()["outcomes"]
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_timing_endpoints() -> None:
    app = FastAPI()
    app.include_router(doctrine_router)
    con = _timing_con()
    app.dependency_overrides[get_con] = lambda: con

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://t") as ac:
        r = await ac.get("/medini/doctrine/dasha-timing",
                         params={"event_class": "death_cause_unspecified", "level": "md"})
        assert r.status_code == 200
        saturn = next(x for x in r.json()["results"] if x["lord"] == "Saturn")
        assert saturn["lift"] > 3 and saturn["verdict"] == "supports"

        r2 = await ac.get("/medini/doctrine/age-shift",
                          params={"event_class": "death_cause_unspecified", "yoga": "StrongYoga"})
        assert r2.status_code == 200
        assert r2.json()["verdict"] == "later"

        r3 = await ac.get("/medini/doctrine/dasha-timing",
                          params={"event_class": "death_cause_unspecified", "level": "bogus"})
        assert r3.status_code == 422
    app.dependency_overrides.clear()
