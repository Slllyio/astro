"""Tests for the portal Person repository.

Uses the shared `db_engine` / `db_session` fixtures from tests/conftest.py
(in-memory aiosqlite + StaticPool). Importing `app.portal.models` at module
load time registers Person with the shared DeclarativeBase BEFORE the
fixture's `Base.metadata.create_all` runs, so the persons table is created.
"""
from __future__ import annotations

import datetime as dt

import pytest

# Module-level import is load-bearing: registers Person with Base.metadata
# before the db_engine fixture calls create_all.
from app.portal import repository
from app.portal.models import Person

pytestmark = pytest.mark.asyncio


# --- canonical-baseline fixture values ----------------------------------------
# Bangalore 1990-07-15 12:00 IST per project CLAUDE.md.
_BANGALORE = dict(
    name="Test Mother",
    relationship="mother",
    dob=dt.date(1990, 7, 15),
    time_of_birth=dt.time(12, 0, 0),
    tz="+05:30",
    lat=12.97,
    lon=77.59,
    place_name="Bangalore, India",
    notes="Canonical project baseline.",
)


async def test_create_and_get_by_id_roundtrip(db_session):
    """create() -> get_by_id() returns the same row with a UUID pk."""
    person = await repository.create(db_session, **_BANGALORE)

    # UUID-shaped 36-char primary key.
    assert isinstance(person.id, str)
    assert len(person.id) == 36
    assert person.id.count("-") == 4

    # Audit timestamps populated by defaults.
    assert person.created_at is not None
    assert person.updated_at is not None
    assert person.is_deleted is False
    assert person.deleted_at is None

    fetched = await repository.get_by_id(db_session, person.id)
    assert fetched is not None
    assert fetched.id == person.id
    assert fetched.name == "Test Mother"
    assert fetched.relationship == "mother"
    assert fetched.dob == dt.date(1990, 7, 15)
    assert fetched.time_of_birth == dt.time(12, 0, 0)
    assert fetched.tz == "+05:30"
    assert fetched.lat == pytest.approx(12.97)
    assert fetched.lon == pytest.approx(77.59)
    assert fetched.place_name == "Bangalore, India"
    assert fetched.notes == "Canonical project baseline."


async def test_get_by_id_unknown_returns_none(db_session):
    """Unknown id is None (not an exception) — keeps the repo composable."""
    result = await repository.get_by_id(db_session, "00000000-0000-0000-0000-000000000000")
    assert result is None


async def test_list_all_returns_inserted_person(db_session):
    """A freshly-created person shows up in list_all() with one row."""
    created = await repository.create(db_session, **_BANGALORE)

    rows = await repository.list_all(db_session)
    assert len(rows) == 1
    assert rows[0].id == created.id
    assert rows[0].name == "Test Mother"


async def test_list_all_orders_by_relationship_then_name(db_session):
    """Order is relationship ASC, name ASC — predictable list view."""
    await repository.create(
        db_session,
        name="Beta",
        relationship="father",
        dob=dt.date(1960, 1, 1),
        time_of_birth=None,
        tz="+05:30",
        lat=12.97,
        lon=77.59,
    )
    await repository.create(
        db_session,
        name="Alpha",
        relationship="father",
        dob=dt.date(1960, 1, 1),
        time_of_birth=None,
        tz="+05:30",
        lat=12.97,
        lon=77.59,
    )
    await repository.create(
        db_session,
        name="Gamma",
        relationship="mother",
        dob=dt.date(1960, 1, 1),
        time_of_birth=None,
        tz="+05:30",
        lat=12.97,
        lon=77.59,
    )

    rows = await repository.list_all(db_session)
    assert [r.name for r in rows] == ["Alpha", "Beta", "Gamma"]
    assert [r.relationship for r in rows] == ["father", "father", "mother"]


async def test_list_all_excludes_soft_deleted_by_default(db_session):
    """Soft-deleted rows are hidden from list_all() without include_deleted=True."""
    keeper = await repository.create(db_session, **_BANGALORE)
    deleted = await repository.create(
        db_session,
        name="Goner",
        relationship="other",
        dob=dt.date(1970, 6, 1),
        time_of_birth=None,
        tz="+00:00",
        lat=0.0,
        lon=0.0,
    )

    ok = await repository.soft_delete(db_session, deleted.id)
    assert ok is True

    # Default: live rows only.
    live = await repository.list_all(db_session)
    assert len(live) == 1
    assert live[0].id == keeper.id

    # Opt-in: includes the tombstoned row too.
    all_rows = await repository.list_all(db_session, include_deleted=True)
    assert len(all_rows) == 2
    ids = {r.id for r in all_rows}
    assert keeper.id in ids
    assert deleted.id in ids


async def test_list_all_filters_by_relationship(db_session):
    """list_all(relationship=...) narrows to that group."""
    await repository.create(db_session, **_BANGALORE)  # mother
    await repository.create(
        db_session,
        name="Dad",
        relationship="father",
        dob=dt.date(1960, 1, 1),
        time_of_birth=None,
        tz="+05:30",
        lat=12.97,
        lon=77.59,
    )

    mothers = await repository.list_all(db_session, relationship="mother")
    assert len(mothers) == 1
    assert mothers[0].name == "Test Mother"

    fathers = await repository.list_all(db_session, relationship="father")
    assert len(fathers) == 1
    assert fathers[0].name == "Dad"


async def test_update_changes_fields(db_session):
    """update() sets whitelisted fields and refreshes the instance."""
    person = await repository.create(db_session, **_BANGALORE)
    original_id = person.id
    original_created = person.created_at

    updated = await repository.update(
        db_session,
        person.id,
        name="Renamed Mother",
        notes="Updated notes",
        lat=13.0,
    )
    assert updated is not None
    assert updated.id == original_id  # id preserved
    assert updated.name == "Renamed Mother"
    assert updated.notes == "Updated notes"
    assert updated.lat == pytest.approx(13.0)
    # Untouched fields remain.
    assert updated.relationship == "mother"
    assert updated.lon == pytest.approx(77.59)
    # created_at never changes.
    assert updated.created_at == original_created


async def test_update_ignores_non_whitelisted_fields(db_session):
    """id / is_deleted / created_at can NOT be mutated through update()."""
    person = await repository.create(db_session, **_BANGALORE)
    original_id = person.id
    original_created = person.created_at

    # Try to overwrite forbidden fields.
    forged_id = "deadbeef-dead-beef-dead-beefdeadbeef"
    updated = await repository.update(
        db_session,
        person.id,
        id=forged_id,
        is_deleted=True,
        created_at=dt.datetime(1900, 1, 1, tzinfo=dt.timezone.utc),
        name="Allowed Change",
    )
    assert updated is not None
    assert updated.id == original_id  # forged id rejected
    assert updated.is_deleted is False  # cannot bypass soft_delete
    assert updated.created_at == original_created
    assert updated.name == "Allowed Change"  # the legitimate field landed


async def test_update_unknown_id_returns_none(db_session):
    """Updating an unknown id returns None instead of raising."""
    result = await repository.update(
        db_session,
        "00000000-0000-0000-0000-000000000000",
        name="ghost",
    )
    assert result is None


async def test_soft_delete_marks_row_without_physical_delete(db_session):
    """soft_delete() sets is_deleted + deleted_at but keeps the row."""
    person = await repository.create(db_session, **_BANGALORE)
    pid = person.id

    ok = await repository.soft_delete(db_session, pid)
    assert ok is True

    # Default get returns None (filtered out).
    assert await repository.get_by_id(db_session, pid) is None

    # But the row is still physically there with the tombstone fields set.
    raw = await db_session.get(Person, pid)
    assert raw is not None
    assert raw.is_deleted is True
    assert raw.deleted_at is not None
    assert raw.deleted_at.tzinfo is not None  # tz-aware

    # include_deleted=True surfaces it through the repository too.
    via_repo = await repository.get_by_id(db_session, pid, include_deleted=True)
    assert via_repo is not None
    assert via_repo.id == pid
    assert via_repo.is_deleted is True


async def test_soft_delete_unknown_returns_false(db_session):
    """Deleting an unknown id returns False (idempotent no-op-False)."""
    ok = await repository.soft_delete(db_session, "00000000-0000-0000-0000-000000000000")
    assert ok is False


async def test_soft_delete_twice_returns_false_second_time(db_session):
    """Once tombstoned, repeating delete is a safe False (not an exception)."""
    person = await repository.create(db_session, **_BANGALORE)
    assert await repository.soft_delete(db_session, person.id) is True
    # Second call: get_by_id filters out the deleted row, so soft_delete -> False.
    assert await repository.soft_delete(db_session, person.id) is False
