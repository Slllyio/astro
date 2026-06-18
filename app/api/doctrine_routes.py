"""Doctrine Validator API — empirical population-scale testing of classical rules.

Turns the `app.medini.analysis.doctrine_validator` core into HTTP endpoints over
the DuckDB catalog:

  GET /medini/doctrine/outcomes              list the testable outcome flags
  GET /medini/doctrine/validate?yoga=&outcome=          one rule's lift + p-value
  GET /medini/doctrine/validate?attr_root=&attr_field=&outcome=
  GET /medini/doctrine/validate?strong_graha=&outcome=
  GET /medini/doctrine/scan?outcome=         every yoga vs one outcome, by lift

The catalog connection is provided via the ``get_con`` dependency so tests can
inject a synthetic in-memory DuckDB. If the catalog is absent the endpoints return
503 rather than 500.
"""
from __future__ import annotations

from typing import Iterator

import duckdb
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.medini.analysis import doctrine_validator as dv

doctrine_router = APIRouter(prefix="/medini/doctrine", tags=["Doctrine Validator"])


def get_con() -> Iterator[duckdb.DuckDBPyConnection]:
    """Open the catalog read-only for one request. Overridable in tests."""
    if not dv.DEFAULT_CATALOG.exists():
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"DuckDB catalog not built at {dv.DEFAULT_CATALOG}. "
                   f"Run: python -m app.medini.etl.build_duckdb_catalog",
        )
    con = dv.open_catalog()
    try:
        yield con
    finally:
        con.close()


@doctrine_router.get("/outcomes")
async def outcomes() -> dict:
    """The binary outcome flags that can be tested (from person_labels)."""
    return {"outcomes": list(dv.OUTCOMES)}


@doctrine_router.get("/validate")
async def validate(
    outcome: str = Query(..., description="An outcome flag; see /outcomes"),
    yoga: str | None = Query(None, description="Condition: chart carries this yoga"),
    attr_root: str | None = Query(None, description="Condition: person_attributes root"),
    attr_field: str | None = Query(None, description="…with this field"),
    strong_graha: str | None = Query(None, description="Condition: this graha is Shadbala-strongest"),
    con: duckdb.DuckDBPyConnection = Depends(get_con),
) -> dict:
    """Validate one rule: outcome-rate in the condition cohort vs baseline + p-value."""
    try:
        if yoga:
            res = dv.validate_yoga(con, yoga, outcome)
        elif attr_root and attr_field:
            res = dv.validate_attribute(con, attr_root, attr_field, outcome)
        elif strong_graha:
            res = dv.validate_strong_graha(con, strong_graha, outcome)
        else:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="provide one condition: yoga, (attr_root+attr_field), or strong_graha",
            )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return res.to_dict()


@doctrine_router.get("/scan")
async def scan(
    outcome: str = Query(..., description="An outcome flag; see /outcomes"),
    con: duckdb.DuckDBPyConnection = Depends(get_con),
) -> dict:
    """Validate every yoga against one outcome, ranked by lift."""
    try:
        results = dv.scan_yogas(con, outcome)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return {"outcome": outcome, "results": [r.to_dict() for r in results]}


@doctrine_router.get("/event-classes")
async def event_classes(con: duckdb.DuckDBPyConnection = Depends(get_con)) -> dict:
    """Event classes available for timing analysis (with counts)."""
    rows = con.execute(
        "SELECT event_class, COUNT(*) n FROM events_with_dasha "
        "WHERE md_lord_at_event IS NOT NULL GROUP BY 1 ORDER BY 2 DESC"
    ).fetchall()
    return {"event_classes": [{"event_class": c, "n": int(n)} for c, n in rows]}


@doctrine_router.get("/dasha-timing")
async def dasha_timing(
    event_class: str = Query(..., description="see /event-classes"),
    level: str = Query("md", description="'md' or 'ad'"),
    con: duckdb.DuckDBPyConnection = Depends(get_con),
) -> dict:
    """Does an event class cluster under particular dasha lords (vs each lord's
    natural Vimshottari share of life)?"""
    try:
        results = dv.validate_dasha_timing(con, event_class, level)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return {"event_class": event_class, "level": level,
            "results": [r.__dict__ for r in results]}


@doctrine_router.get("/age-shift")
async def age_shift(
    event_class: str = Query(..., description="see /event-classes"),
    yoga: str | None = Query(None),
    attr_root: str | None = Query(None),
    attr_field: str | None = Query(None),
    strong_graha: str | None = Query(None),
    con: duckdb.DuckDBPyConnection = Depends(get_con),
) -> dict:
    """Does a chart condition shift the age at which an event class strikes?"""
    try:
        attr = (attr_root, attr_field) if attr_root and attr_field else None
        res = dv.validate_age_shift(con, event_class, yoga=yoga, attr=attr,
                                    strong_graha=strong_graha)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return res.__dict__


@doctrine_router.get("/maraka")
async def maraka(
    event_class: str = Query("death_cause_unspecified", description="see /event-classes"),
    level: str = Query("md", description="'md' or 'ad'"),
    definition: str = Query("full", description="'lords' | 'lords_occupants' | 'full' (lords+occupants+Saturn)"),
    con: duckdb.DuckDBPyConnection = Depends(get_con),
) -> dict:
    """Maraka doctrine: do events run under a maraka-planet dasha more than the
    dasha-length-weighted, per-ascendant baseline? Includes MD&AD confluence and a
    per-ascendant breakdown (the marakas differ by Lagna)."""
    try:
        res = dv.validate_maraka(con, event_class, level, definition)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return res.__dict__


@doctrine_router.get("/death-significators")
async def death_significators(
    event_class: str = Query("death_cause_unspecified", description="see /event-classes"),
    level: str = Query("md", description="'md' or 'ad'"),
    con: duckdb.DuckDBPyConnection = Depends(get_con),
) -> dict:
    """Test all classical death-timing significators head-to-head (maraka, 8th/3rd
    lord, badhakesa, 22nd drekkana lord, 64th navamsa lord), ranked by lift."""
    try:
        results = dv.death_significators_report(con, event_class, level)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return {"event_class": event_class, "level": level,
            "results": [r.__dict__ for r in results]}


@doctrine_router.get("/transit")
async def transit(
    planet: str = Query("Saturn", description="transiting graha"),
    houses: str = Query("6,8,12", description="comma-separated natal houses"),
    event_class: str = Query("death_cause_unspecified", description="see /event-classes"),
    con: duckdb.DuckDBPyConnection = Depends(get_con),
) -> dict:
    """Is a planet transiting one of `houses` (from natal Lagna) at the event more
    than the uniform-house baseline?"""
    try:
        hs = tuple(int(h) for h in houses.split(",") if h.strip())
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="houses must be comma-separated integers") from exc
    return dv.validate_transit_house(con, planet, hs, event_class).__dict__
