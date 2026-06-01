"""Family-charts portal — FastAPI routes mounted at ``/portal/*``.

Purely additive: this router CALLS the master-reading layer
(``app.integration.compose_master_reading`` / ``llm_polish_master_reading``)
and persists user-supplied birth data via the Phase 1 ``app.portal``
package. NO astro logic lives here.

Routes (see Phase 1 UI design):

    GET  /portal/                 list of saved relatives
    GET  /portal/new              new-person form
    POST /portal/new              create + redirect to /portal/{id}
    GET  /portal/{id}             full master reading view
    GET  /portal/{id}/edit        edit form pre-filled from DB
    POST /portal/{id}/edit        update + redirect to /portal/{id}
    POST /portal/{id}/delete      soft-delete + redirect to /portal/

Validation strategy mirrors ``reading_v15_routes``: a ``ValidationError``
from Pydantic re-renders ``form.html`` with the user-typed values and an
error banner. Only the public ``ChartInput`` validator is reused — the
portal layer adds its own ``PersonForm`` validator for the
portal-specific fields (name, relationship, place_name, notes).

Engine call (``compose_master_reading``) is sync + cpu-bound. We offload
to a worker thread via ``asyncio.to_thread`` so the async event loop
stays responsive — same convention as ``reading_v15_routes``.
"""
from __future__ import annotations

import asyncio
import datetime as dt
import logging
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.integration import compose_master_reading, llm_polish_master_reading
from app.portal import repository as person_repo
from app.portal.models import Person
from app.reading.proforma import compute as track_a_compute
from app.reading.schema import ChartInput

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/portal", tags=["portal"])

# Module-level template registry — same per-module pattern used in the
# v1.5 and integrated route modules.
_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


# ---------------------------------------------------------------------------
# Portal-side validation
# ---------------------------------------------------------------------------

# Closed-set list — mirrors the UI design and is validated upstream of
# the DB write. Adding a value here is the single source of truth.
_RELATIONSHIP_OPTIONS: tuple[str, ...] = (
    "self", "spouse", "mother", "father", "son", "daughter",
    "brother", "sister", "grandparent", "grandchild", "friend", "other",
)


class _PersonForm(BaseModel):
    """Pydantic envelope for the portal new/edit form.

    Layers on top of the locked Track-A ``ChartInput`` ranges by reusing
    the same lat/lon bounds; adds portal-only constraints (name length,
    relationship enum, optional notes). ``frozen=True`` + ``extra='forbid'``
    matches the project-wide discipline.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str = Field(min_length=1, max_length=80)
    relationship: Literal[
        "self", "spouse", "mother", "father", "son", "daughter",
        "brother", "sister", "grandparent", "grandchild", "friend", "other",
    ]
    dob: str = Field(description="ISO YYYY-MM-DD")
    time: str | None = Field(default=None, description="HH:MM (24-hour) or empty")
    tz: str = Field(min_length=1, description="Signed offset, e.g. +05:30")
    lat: float = Field(ge=-90.0, le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)
    place_name: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=2000)


# ---------------------------------------------------------------------------
# Form-rendering helpers
# ---------------------------------------------------------------------------

def _form_data_dict(
    *,
    name: str | None,
    relationship: str | None,
    dob: str | None,
    time: str | None,
    tz: str | None,
    lat: float | str | None,
    lon: float | str | None,
    place_name: str | None,
    notes: str | None,
) -> dict[str, Any]:
    """Repack form values for re-rendering after a validation error.

    Mirrors the ``_form_data`` helper in ``reading_v15_routes``. Values
    are stored as supplied so the user keeps what they typed.
    """
    return {
        "name": name,
        "relationship": relationship,
        "dob": dob,
        "time": time,
        "tz": tz,
        "lat": lat,
        "lon": lon,
        "place_name": place_name,
        "notes": notes,
    }


def _first_error_message(exc: ValidationError) -> str:
    """Extract a human-readable first-error message from a Pydantic error."""
    errors = exc.errors()
    if not errors:
        return "Invalid input."
    err = errors[0]
    loc = ".".join(str(x) for x in err.get("loc", ()))
    msg = err.get("msg", "invalid value")
    return f"{loc}: {msg}" if loc else msg


def _parse_dob(dob_str: str) -> dt.date:
    """Convert form 'YYYY-MM-DD' to a ``datetime.date``. Raises ValueError."""
    return dt.date.fromisoformat(dob_str)


def _parse_time(time_str: str | None) -> dt.time | None:
    """Convert form 'HH:MM' (or empty) to a ``datetime.time``. Empty -> None."""
    if not time_str:
        return None
    # Accept both 'HH:MM' and 'HH:MM:SS' just in case the browser includes seconds.
    return dt.time.fromisoformat(time_str)


def _person_to_form_data(person: Person) -> dict[str, Any]:
    """Pre-fill the edit form from a saved Person row."""
    return {
        "name": person.name,
        "relationship": person.relationship,
        "dob": person.dob.isoformat() if person.dob else None,
        "time": person.time_of_birth.strftime("%H:%M") if person.time_of_birth else None,
        "tz": person.tz,
        "lat": person.lat,
        "lon": person.lon,
        "place_name": person.place_name,
        "notes": person.notes,
    }


# ---------------------------------------------------------------------------
# Reading-engine wrapper
# ---------------------------------------------------------------------------

def _generate_reading_sync(person: Person, *, polish: bool) -> dict[str, Any]:
    """Synchronous helper run inside ``asyncio.to_thread``.

    Builds a ``ChartInput`` from a Person row, runs the Track-A engine, then
    composes the master reading. Optionally LLM-polishes it. Returns the
    serialised payload — the caller is responsible for handing it to Jinja.

    Falls back to the unpolished MasterReading dict when polish=True but
    no LLM backend is wired (the helper uses the stub client by default).
    """
    if person.time_of_birth is None:
        # Master reading needs a wall-clock; default to midday when unknown.
        # This is documented in the view template's "unknown-time" note.
        time_str = "12:00"
    else:
        time_str = person.time_of_birth.strftime("%H:%M")

    chart_input = ChartInput(
        dob=person.dob.isoformat(),
        time=time_str,
        tz=person.tz,
        lat=person.lat,
        lon=person.lon,
    )
    reading = track_a_compute(chart_input, enrich=False)
    master = compose_master_reading(reading)
    if polish:
        polished = llm_polish_master_reading(master)
        return polished.model_dump(mode="json")
    return master.model_dump(mode="json")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
@router.get("", response_class=HTMLResponse)
async def list_persons(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """List all (live) saved persons."""
    persons = await person_repo.list_all(db)
    return templates.TemplateResponse(
        request,
        "portal/index.html",
        {
            # B3's index.html iterates over `relatives`. Keep `persons` too
            # in case downstream consumers expect either key.
            "relatives": persons,
            "persons": persons,
        },
    )


@router.get("/new", response_class=HTMLResponse)
async def new_person_form(request: Request) -> HTMLResponse:
    """Render the empty new-person form."""
    return templates.TemplateResponse(
        request,
        "portal/form.html",
        {
            "mode": "new",
            "form_data": _form_data_dict(
                name=None, relationship=None, dob=None, time=None,
                tz=None, lat=None, lon=None, place_name=None, notes=None,
            ),
            "relationship_options": _RELATIONSHIP_OPTIONS,
            "post_action": "/portal/new",
            "cancel_href": "/portal/",
            "person_id": None,
            "error": None,
        },
    )


@router.post("/new")
async def create_person(
    request: Request,
    name: Annotated[str, Form()],
    relationship: Annotated[str, Form()],
    dob: Annotated[str, Form()],
    tz: Annotated[str, Form()],
    lat: Annotated[float, Form()],
    lon: Annotated[float, Form()],
    time: Annotated[str | None, Form()] = None,
    place_name: Annotated[str | None, Form()] = None,
    notes: Annotated[str | None, Form()] = None,
    db: AsyncSession = Depends(get_db),
):
    """Validate and persist a new person.

    On success: 303 redirect to ``/portal/{id}``. On validation error:
    re-render the form with an error banner + preserved user input.
    """
    try:
        form = _PersonForm(
            name=name,
            relationship=relationship,
            dob=dob,
            time=time or None,
            tz=tz,
            lat=lat,
            lon=lon,
            place_name=place_name or None,
            notes=notes or None,
        )
        dob_date = _parse_dob(form.dob)
        tob = _parse_time(form.time)
    except (ValidationError, ValueError) as exc:
        msg = (
            _first_error_message(exc)
            if isinstance(exc, ValidationError)
            else str(exc)
        )
        return templates.TemplateResponse(
            request,
            "portal/form.html",
            {
                "mode": "new",
                "form_data": _form_data_dict(
                    name=name, relationship=relationship, dob=dob,
                    time=time, tz=tz, lat=lat, lon=lon,
                    place_name=place_name, notes=notes,
                ),
                "relationship_options": _RELATIONSHIP_OPTIONS,
                "post_action": "/portal/new",
                "cancel_href": "/portal/",
                "person_id": None,
                "error": f"Invalid input — {msg}",
            },
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    person = await person_repo.create(
        db,
        name=form.name,
        relationship=form.relationship,
        dob=dob_date,
        time_of_birth=tob,
        tz=form.tz,
        lat=form.lat,
        lon=form.lon,
        place_name=form.place_name,
        notes=form.notes,
    )

    return RedirectResponse(
        url=f"/portal/{person.id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/{person_id}", response_class=HTMLResponse)
async def view_person(
    request: Request,
    person_id: str,
    polish: bool = False,
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """Render the full master reading for ``person_id``.

    Calls ``compose_master_reading`` on demand. With ``?polish=1`` also
    runs ``llm_polish_master_reading``. Returns 404 for missing /
    soft-deleted ids.
    """
    person = await person_repo.get(db, person_id)
    if person is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person {person_id!r} not found.",
        )

    reading_payload: dict[str, Any] | None = None
    reading_error: str | None = None
    try:
        reading_payload = await asyncio.to_thread(
            _generate_reading_sync, person, polish=polish
        )
    except Exception as exc:  # noqa: BLE001 — top of route; surface friendly
        logger.exception("reading engine failed for person=%s", person.id)
        reading_error = f"{type(exc).__name__}: {exc}"

    chart_basics = (reading_payload or {}).get("chart_basics") or {}

    return templates.TemplateResponse(
        request,
        "portal/person_detail.html",
        {
            "person": person,
            "reading": reading_payload,
            "reading_error": reading_error,
            "chart_basics": chart_basics,
            "polish": polish,
        },
    )


@router.get("/{person_id}/edit", response_class=HTMLResponse)
async def edit_person_form(
    request: Request,
    person_id: str,
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """Render the edit form pre-filled from the saved Person row."""
    person = await person_repo.get(db, person_id)
    if person is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person {person_id!r} not found.",
        )
    return templates.TemplateResponse(
        request,
        "portal/form.html",
        {
            "mode": "edit",
            "person": person,
            "form_data": _person_to_form_data(person),
            "relationship_options": _RELATIONSHIP_OPTIONS,
            "post_action": f"/portal/{person.id}/edit",
            "cancel_href": f"/portal/{person.id}",
            "person_id": person.id,
            "error": None,
        },
    )


@router.post("/{person_id}/edit")
async def update_person(
    request: Request,
    person_id: str,
    name: Annotated[str, Form()],
    relationship: Annotated[str, Form()],
    dob: Annotated[str, Form()],
    tz: Annotated[str, Form()],
    lat: Annotated[float, Form()],
    lon: Annotated[float, Form()],
    time: Annotated[str | None, Form()] = None,
    place_name: Annotated[str | None, Form()] = None,
    notes: Annotated[str | None, Form()] = None,
    db: AsyncSession = Depends(get_db),
):
    """Apply form updates to ``person_id`` and redirect to its view."""
    person = await person_repo.get(db, person_id)
    if person is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person {person_id!r} not found.",
        )

    try:
        form = _PersonForm(
            name=name,
            relationship=relationship,
            dob=dob,
            time=time or None,
            tz=tz,
            lat=lat,
            lon=lon,
            place_name=place_name or None,
            notes=notes or None,
        )
        dob_date = _parse_dob(form.dob)
        tob = _parse_time(form.time)
    except (ValidationError, ValueError) as exc:
        msg = (
            _first_error_message(exc)
            if isinstance(exc, ValidationError)
            else str(exc)
        )
        return templates.TemplateResponse(
            request,
            "portal/form.html",
            {
                "mode": "edit",
                "person": person,
                "form_data": _form_data_dict(
                    name=name, relationship=relationship, dob=dob,
                    time=time, tz=tz, lat=lat, lon=lon,
                    place_name=place_name, notes=notes,
                ),
                "relationship_options": _RELATIONSHIP_OPTIONS,
                "post_action": f"/portal/{person_id}/edit",
                "cancel_href": f"/portal/{person_id}",
                "person_id": person_id,
                "error": f"Invalid input — {msg}",
            },
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    await person_repo.update(
        db,
        person_id,
        name=form.name,
        relationship=form.relationship,
        dob=dob_date,
        time_of_birth=tob,
        tz=form.tz,
        lat=form.lat,
        lon=form.lon,
        place_name=form.place_name,
        notes=form.notes,
    )

    return RedirectResponse(
        url=f"/portal/{person_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/{person_id}/delete")
async def delete_person(
    request: Request,
    person_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete ``person_id`` and redirect back to the index."""
    deleted = await person_repo.soft_delete(db, person_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Person {person_id!r} not found.",
        )
    return RedirectResponse(
        url="/portal/",
        status_code=status.HTTP_303_SEE_OTHER,
    )
