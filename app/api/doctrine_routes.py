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

import datetime as _dt

from app.medini.analysis import death_window_predictor as dwp
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


@doctrine_router.get("/death-composite")
async def death_composite(
    event_class: str = Query("death_cause_unspecified", description="see /event-classes"),
    level: str = Query("md", description="'md' or 'ad'"),
    con: duckdb.DuckDBPyConnection = Depends(get_con),
) -> dict:
    """Composite death-risk: does the dasha lord playing more death-significator
    roles (maraka + 3rd lord + 64th navamsa) raise risk (dose-response)?"""
    try:
        res = dv.validate_composite_death_score(con, event_class, level)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return res.__dict__


@doctrine_router.get("/longevity-bracket")
async def longevity_bracket(
    significator: str = Query("maraka_full", description="a death significator"),
    event_class: str = Query("death_cause_unspecified", description="see /event-classes"),
    level: str = Query("md", description="'md' or 'ad'"),
    con: duckdb.DuckDBPyConnection = Depends(get_con),
) -> dict:
    """Does a significator's timing power concentrate in a longevity bracket
    (alpa / madhya / purna by age-at-event)?"""
    try:
        res = dv.validate_significator_by_bracket(con, significator, event_class, level)
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return res.__dict__


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


@doctrine_router.get("/death-window")
async def death_window(
    year: int = Query(..., description="birth year"),
    month: int = Query(..., ge=1, le=12),
    day: int = Query(..., ge=1, le=31),
    hour: int = Query(12, ge=0, le=23),
    minute: int = Query(0, ge=0, le=59),
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    tz_offset: float = Query(0.0, description="hours east of UTC"),
    as_of: str | None = Query(None, description="ISO date; default today (UTC)"),
    top_n: int | None = Query(10, description="return the N riskiest windows; null = all"),
    calibrate: bool = Query(False, description="re-derive risk factors live from the catalog"),
) -> dict:
    """Per-chart death-window predictor: rank a living person's future Vimśottarī
    MD×AD periods by composite death-significator confluence × longevity bracket.

    The risk factors default to this session's measured lifts; pass ``calibrate=true``
    to re-derive them live from the catalog (requires the DuckDB catalog to be built)."""
    try:
        as_of_date = _dt.date.fromisoformat(as_of) if as_of else None
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="as_of must be an ISO date (YYYY-MM-DD)") from exc

    composite_factor = bracket_factor = None
    if calibrate:
        if not dv.DEFAULT_CATALOG.exists():
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="calibration requested but DuckDB catalog is not built",
            )
        con = dv.open_catalog()
        try:
            composite_factor, bracket_factor = dwp.calibrate_factors(con)
        finally:
            con.close()

    try:
        return dwp.predict_death_windows(
            year=year, month=month, day=day, hour=hour, minute=minute,
            latitude=latitude, longitude=longitude, tz_offset=tz_offset,
            as_of=as_of_date, top_n=top_n,
            composite_factor=composite_factor, bracket_factor=bracket_factor,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
