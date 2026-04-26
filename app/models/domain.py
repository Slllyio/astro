"""SQLAlchemy 2.0 ORM models for users, natal charts, and transit alerts."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> dt.datetime:
    """Timezone-aware UTC now. Replaces deprecated datetime.utcnow() (Py 3.12+)."""
    return dt.datetime.now(dt.timezone.utc)


class Base(DeclarativeBase):
    pass


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)

    birth_year: Mapped[int] = mapped_column(Integer)
    birth_month: Mapped[int] = mapped_column(Integer)
    birth_day: Mapped[int] = mapped_column(Integer)
    birth_hour: Mapped[int] = mapped_column(Integer)
    birth_minute: Mapped[int] = mapped_column(Integer)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    tz_offset: Mapped[float] = mapped_column(Float)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    natal_chart: Mapped["NatalChart | None"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    transit_alerts: Mapped[list["TransitAlert"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class NatalChart(Base):
    __tablename__ = "natal_charts"
    __table_args__ = (UniqueConstraint("user_id", name="uq_natal_charts_user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"), index=True)

    # Anchors needed for forward Dasha math without re-running Swiss Ephemeris.
    birth_jd: Mapped[float] = mapped_column(Float)
    birth_moon_longitude: Mapped[float] = mapped_column(Float)

    # Sidereal Lahiri ascendant (Lagna). Required - lat/lon are required on
    # BirthDataInput, so every persisted natal chart has an ascendant.
    ascendant_lon: Mapped[float] = mapped_column(Float)
    ascendant_sign: Mapped[int] = mapped_column(Integer)

    # Sidereal D1 longitudes (0..360) and whole-sign indices (1..12) for each graha.
    # Sign columns are denormalized so the daemon can do whole-sign aspect checks
    # without recomputing int(lon // 30) every tick.
    sun_lon: Mapped[float] = mapped_column(Float)
    sun_sign: Mapped[int] = mapped_column(Integer)
    moon_lon: Mapped[float] = mapped_column(Float)
    moon_sign: Mapped[int] = mapped_column(Integer)
    mars_lon: Mapped[float] = mapped_column(Float)
    mars_sign: Mapped[int] = mapped_column(Integer)
    mercury_lon: Mapped[float] = mapped_column(Float)
    mercury_sign: Mapped[int] = mapped_column(Integer)
    jupiter_lon: Mapped[float] = mapped_column(Float)
    jupiter_sign: Mapped[int] = mapped_column(Integer)
    venus_lon: Mapped[float] = mapped_column(Float)
    venus_sign: Mapped[int] = mapped_column(Integer)
    saturn_lon: Mapped[float] = mapped_column(Float)
    saturn_sign: Mapped[int] = mapped_column(Integer)
    rahu_lon: Mapped[float] = mapped_column(Float)
    rahu_sign: Mapped[int] = mapped_column(Integer)
    ketu_lon: Mapped[float] = mapped_column(Float)
    ketu_sign: Mapped[int] = mapped_column(Integer)

    full_chart_json: Mapped[dict] = mapped_column(JSON)

    user: Mapped["UserProfile"] = relationship(back_populates="natal_chart")


class TransitAlert(Base):
    __tablename__ = "transit_alerts"
    __table_args__ = (
        Index("ix_transit_alerts_user_active_date", "user_id", "is_active", "exact_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_profiles.id"))

    alert_type: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)

    transit_planet: Mapped[str] = mapped_column(String)
    natal_planet: Mapped[str] = mapped_column(String)
    is_exact: Mapped[bool] = mapped_column(Boolean, default=False)

    exact_date: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["UserProfile"] = relationship(back_populates="transit_alerts")
