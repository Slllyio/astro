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
