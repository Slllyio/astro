"""Async repository functions for the Person table.

Module-level coroutines (no Repository class) — matches the project's
existing style of using `AsyncSession` directly from route handlers.

All read methods filter `is_deleted=False` by default. Hard delete is
intentionally NOT exposed by v1; the portal route layer only calls
`soft_delete`.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import utc_now
from app.portal.models import Person

# Columns the caller is allowed to update via `update()`. Anything not in this
# set is silently ignored — protects id / is_deleted / created_at / deleted_at
# from being clobbered by a blind dict-merge.
_UPDATABLE_FIELDS: frozenset[str] = frozenset(
    {
        "name",
        "relationship",
        "dob",
        "time_of_birth",
        "tz",
        "lat",
        "lon",
        "place_name",
        "notes",
    }
)


async def create(
    session: AsyncSession,
    *,
    name: str,
    relationship: str,
    dob: dt.date,
    time_of_birth: dt.time | None,
    tz: str,
    lat: float,
    lon: float,
    place_name: str | None = None,
    notes: str | None = None,
) -> Person:
    """Insert a new Person; id auto-assigned via uuid4 default.

    Validation of `relationship` enum + `tz` format happens upstream in the
    Pydantic form schema, not here. This function commits and refreshes so the
    caller gets back a fully-populated instance ready to template.
    """
    person = Person(
        name=name,
        relationship=relationship,
        dob=dob,
        time_of_birth=time_of_birth,
        tz=tz,
        lat=lat,
        lon=lon,
        place_name=place_name,
        notes=notes,
    )
    session.add(person)
    await session.commit()
    await session.refresh(person)
    return person


async def get_by_id(
    session: AsyncSession,
    person_id: str,
    *,
    include_deleted: bool = False,
) -> Person | None:
    """Fetch a single Person by primary key.

    Returns None when the row is missing OR (by default) is soft-deleted.
    Set `include_deleted=True` to bypass the soft-delete filter — required
    when implementing a restore endpoint.
    """
    person = await session.get(Person, person_id)
    if person is None:
        return None
    if person.is_deleted and not include_deleted:
        return None
    return person


async def list_all(
    session: AsyncSession,
    *,
    include_deleted: bool = False,
    relationship: str | None = None,
) -> list[Person]:
    """Return all live Persons, ordered by relationship then name.

    Cheap O(N) scan — the portal expects O(10..100) saved relatives. If
    `relationship` is given, narrows to that group. `include_deleted=True`
    surfaces tombstoned rows for an admin/restore view.
    """
    stmt = select(Person)
    if not include_deleted:
        stmt = stmt.where(Person.is_deleted.is_(False))
    if relationship is not None:
        stmt = stmt.where(Person.relationship == relationship)
    stmt = stmt.order_by(Person.relationship, Person.name)
    result = await session.scalars(stmt)
    return list(result.all())


async def update(
    session: AsyncSession,
    person_id: str,
    **fields: Any,
) -> Person | None:
    """Whitelist-update a Person's user-editable fields.

    Returns the refreshed Person, or None if the id is unknown / soft-deleted.
    Fields outside `_UPDATABLE_FIELDS` are silently dropped, so id /
    is_deleted / created_at / deleted_at can never be mutated through this
    path. `updated_at` is auto-bumped via the column's `onupdate=utc_now`.
    """
    person = await get_by_id(session, person_id)
    if person is None:
        return None
    for key, value in fields.items():
        if key in _UPDATABLE_FIELDS:
            setattr(person, key, value)
    await session.commit()
    await session.refresh(person)
    return person


async def soft_delete(session: AsyncSession, person_id: str) -> bool:
    """Mark the Person as deleted; row is retained for audit/restore.

    Returns True on success, False if the id is unknown or already deleted
    (so re-calling delete is a safe no-op-False, not an exception).
    """
    person = await get_by_id(session, person_id)
    if person is None:
        return False
    person.is_deleted = True
    person.deleted_at = utc_now()
    await session.commit()
    return True


# Alias kept for caller-side flexibility (portal_routes uses `get`).
get = get_by_id

