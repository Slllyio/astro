"""Real-chart KalaContext (Phase 1c-2b, Task 4) — ephemeris/date derivation.

Verifies the tractable fields (birth_degrees, weekday_lord, is_day, day_third,
hora_lord, ayanamsa) for the Bangalore baseline, and asserts the Ahargana-dependent
year/month lords are flagged ``UNKNOWN`` (not faked) — a documented 1c-3 carry-over.

Canonical baseline: Bangalore 1990-07-15 12:00 IST, lat 12.97, lon 77.59, tz +5.5.
1990-07-15 is a Sunday → weekday_lord must be "Sun".
"""
from __future__ import annotations

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.kala_context import kala_context
from app.raman_saab.chart.model import BirthData
from app.raman_saab.primitives.shadbala.kala import KalaContext

_BLR = BirthData("X", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)
_KALA_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")


def _ctx() -> KalaContext:
    chart = cast_chart(_BLR, ayanamsa="raman")
    return kala_context(_BLR, chart, ayanamsa=22.28)


def test_returns_kala_context_instance() -> None:
    """kala_context produces the frozen KalaContext the kala formulae consume."""
    assert isinstance(_ctx(), KalaContext)


def test_weekday_lord_is_sun_on_a_sunday() -> None:
    """1990-07-15 is a Sunday → the Vara (weekday) lord must be the Sun."""
    assert _ctx().weekday_lord == "Sun"


def test_is_day_true_for_noon_birth() -> None:
    """A noon birth falls between sunrise and sunset → is_day is a True bool."""
    ctx = _ctx()
    assert isinstance(ctx.is_day, bool)
    assert ctx.is_day is True


def test_day_third_in_valid_range() -> None:
    """The day/night third index must be one of {0, 1, 2} (Tribhaga)."""
    assert _ctx().day_third in {0, 1, 2}


def test_birth_degrees_is_180_at_noon() -> None:
    """Noon = 12h from midnight → 12 × 15 = 180° (raw Nathonnatha angle)."""
    assert abs(_ctx().birth_degrees - 180.0) < 1e-6


def test_hora_lord_is_a_real_planet() -> None:
    """The hora lord must be one of the seven classical grahas (Chaldean cycle)."""
    assert _ctx().hora_lord in _KALA_PLANETS


def test_ayanamsa_passed_through_as_degrees() -> None:
    """The caller-supplied ayanamsa is carried through unchanged (degrees)."""
    assert abs(_ctx().ayanamsa - 22.28) < 1e-6


def test_year_and_month_lords_flagged_unknown() -> None:
    """Abda/Masa lords need the Ahargana (GBB-5:343-423) — flagged, not faked (1c-3)."""
    ctx = _ctx()
    assert ctx.year_lord == "UNKNOWN"
    assert ctx.month_lord == "UNKNOWN"


def test_flagged_lords_award_zero_bala_not_wrong_bala() -> None:
    """A sentinel lord matches no real planet, so Abda/Masa award 0 Sh to every graha
    (under-counts, never mis-counts, until the Ahargana lands in 1c-3)."""
    from app.raman_saab.primitives.shadbala import kala

    ctx = _ctx()
    for planet in _KALA_PLANETS:
        assert kala.abda_bala(planet, ctx.year_lord) == 0.0
        assert kala.masa_bala(planet, ctx.month_lord) == 0.0


def test_rejects_stated_positions_chart_without_jd() -> None:
    """A Track-B from_stated_positions chart has no jd_ut → must raise, not guess."""
    import pytest

    from app.raman_saab.chart.model import RamanChart

    stated = {"Sun": {"lon": 100.0, "bhava": 1}, "Moon": {"lon": 200.0, "bhava": 1}}
    chart = RamanChart.from_stated_positions(stated, asc_lon=185.0, ayanamsa="raman")
    with pytest.raises(ValueError):
        kala_context(_BLR, chart, ayanamsa=22.28)
