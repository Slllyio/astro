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
