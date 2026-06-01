"""SQLAlchemy 2.0 ORM model for portal-saved relatives (Person).

A `Person` is the persistence anchor for the family-charts portal. Each row
captures everything the master-reading pipeline needs (dob/time/tz/lat/lon)
plus display metadata (name, relationship, place_name, notes). Soft-delete
via `is_deleted` + `deleted_at` so accidental removals are recoverable.

This module reuses `app.models.domain.Base` (the shared DeclarativeBase)
so `init_db()` -> `Base.metadata.create_all` picks up the `persons` table
without a second metadata registry.
"""
from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import Boolean, Date, DateTime, Float, Index, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.models.domain import Base, utc_now


def _new_id() -> str:
    """UUID4 hex string PK. Stable, URL-safe, collision-free for same-named relatives."""
    return str(uuid.uuid4())


class Person(Base):
    """A saved relative whose master reading can be regenerated on demand.

    Identity uses a UUID4 hex string (`id`) so URLs at /portal/{id} are
    stable and avoid clashing when two relatives share a display name.
    """

    __tablename__ = "persons"
    __table_args__ = (
        # Alpha-sort on the list view.
        Index("ix_persons_name", "name"),
        # Group-by-relationship list view.
        Index("ix_persons_relationship", "relationship"),
        # Default "live persons, newest first" query — covers without a sort step.
        Index("ix_persons_is_deleted_created_at", "is_deleted", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)

    # Display + relationship metadata.
    name: Mapped[str] = mapped_column(String, nullable=False)
    relationship: Mapped[str] = mapped_column(String(32), nullable=False)

    # Birth data — required by the master-reading pipeline.
    dob: Mapped[dt.date] = mapped_column(Date, nullable=False)
    # NULL => unknown birth time; view layer must degrade gracefully (e.g.
    # solar/sunrise chart) rather than inventing a placeholder.
    time_of_birth: Mapped[dt.time | None] = mapped_column(Time, nullable=True)
    # IANA name ('Asia/Kolkata') OR signed offset literal ('+05:30'). Resolved
    # to a float offset in the service layer before calling ChartInput.
    tz: Mapped[str] = mapped_column(String(32), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)

    # Display-only free-text place. lat/lon are the source of truth for math.
    place_name: Mapped[str | None] = mapped_column(String, nullable=True)
    # Markdown free-form notes; rendered at view time, stored raw.
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Soft-delete: hide from default queries but retain row for audit/restore.
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deleted_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Audit timestamps; reuse the project-wide tz-aware utc_now helper.
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return (
            f"Person(id={self.id!r}, name={self.name!r}, "
            f"relationship={self.relationship!r}, is_deleted={self.is_deleted!r})"
        )
