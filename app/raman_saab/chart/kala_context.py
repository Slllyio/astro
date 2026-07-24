"""Build a real-chart :class:`KalaContext` from a birth (the ephemeris/date piece).

The Kala Bala *formulae* live in ``app/raman_saab/primitives/shadbala/kala.py`` and
are pure — they take an injected :class:`KalaContext` of temporal facts that Raman
derives outside the longitudes.  This module derives those facts from a real birth:

  * ``birth_degrees``  — (local-time-from-midnight hours) × 15            (pure, from BirthData)
  * ``weekday_lord``   — civil weekday → planetary lord                    (from jd_ut)
  * ``is_day`` / ``day_third`` — sunrise/sunset partition                  (swe.rise_trans)
  * ``hora_lord``      — Chaldean descending order seeded at the weekday    (GBB-5:606-627)
                         lord at sunrise, advanced by horas elapsed
  * ``ayanamsa``       — passed through (degrees) for the Ayana sub-component

CARRY-OVER (Phase 1c-3) — ``year_lord`` (Abda) / ``month_lord`` (Masa):
  These require the **Ahargana since creation** (Kali-epoch day count, GBB-5:343-423)
  to index the 60-year Samvatsara / 12-month lord cycles.  That is genuinely involved
  (epoch constants, intercalary-month handling) and shipping a *guessed* Ahargana would
  silently corrupt Kala for every real chart (a wrong year/month lord shifts 15+30 Sh
  onto the wrong planet).  We therefore emit a documented sentinel ``UNKNOWN`` rather
  than fake it; the formulae in ``kala.py`` award 0 Sh when the lord does not match any
  real planet, so the only effect is a (correctly) under-counted Kala until 1c-3.

The ``swe.rise_trans`` call mirrors the verified-live pattern in ``chart/upagrahas.py``
(rsmi before geopos; ``rise_trans(tjd_ut, body, rsmi, geopos, atpress, attemp, flags)``).

Usage::

    from app.raman_saab.chart.adapter import cast_chart
    from app.raman_saab.chart.model import BirthData
    from app.raman_saab.chart.kala_context import kala_context

    b = BirthData("X", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)
    chart = cast_chart(b, ayanamsa="raman")
    ctx = kala_context(b, chart, ayanamsa=22.28)   # ayanamsa in degrees
"""
from __future__ import annotations

import logging
from typing import Final

import swisseph as swe

from app.raman_saab.chart.ayanamsa import sidereal_mode
from app.raman_saab.chart.model import BirthData, RamanChart
from app.raman_saab.primitives.shadbala.kala import KalaContext

logger = logging.getLogger(__name__)

# Civil weekday → planetary lord, index 0=Sunday .. 6=Saturday.
# Calibrated so 1990-07-15 (a Sunday) → "Sun" via ``int((jd + 1.5) % 7)``,
# the same calibration the Gulika/Mandi code in chart/upagrahas.py relies on.
_WEEKDAY_LORDS: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
)

# Chaldean (geocentric, slowest→fastest) descending order for hora rulership.
# The 1st hora of any day is ruled by that day's weekday lord; successive horas
# step through this cycle (GBB-5:606-627).
_CHALDEAN_ORDER: Final[tuple[str, ...]] = (
    "Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon",
)

# Sentinel for the Ahargana-dependent lords we deliberately do not fake (1c-3 carry-over).
_AHARGANA_UNKNOWN: Final[str] = "UNKNOWN"


def _jd_ut(b: BirthData) -> float:
    """Julian Day (UT) of the birth moment — identical to the chart adapter."""
    utc_hour = (b.hour + b.minute / 60.0) - b.tz_offset
    return swe.julday(b.year, b.month, b.day, utc_hour, swe.GREG_CAL)


def _local_midnight_jd(b: BirthData) -> float:
    """JD (UT) for 00:00 *local civil* time on the birth date."""
    return swe.julday(b.year, b.month, b.day, 0.0 - b.tz_offset, swe.GREG_CAL)


def _weekday_index(jd_ut: float) -> int:
    """Civil weekday 0=Sunday .. 6=Saturday for a UT Julian Day.

    Uses ``int((jd + 1.5) % 7)`` — calibrated against the Bangalore baseline:
    JD 2448087.77 (1990-07-15, a confirmed Sunday) → 0.  This matches the
    convention already pinned in ``chart/upagrahas.py`` and is preferred over
    ``swe.day_of_week`` (which returns 0=Monday .. 6=Sunday — a different base).
    """
    return int((jd_ut + 1.5) % 7)


def _birth_degrees(b: BirthData) -> float:
    """(Local-time-from-midnight in hours) × 15 — the raw Nathonnatha angle.

    The kala formula folds values > 180 itself, so we pass the raw value.
    """
    hours_from_midnight = b.hour + b.minute / 60.0
    return hours_from_midnight * 15.0


def _sunrise_sunset(b: BirthData, ayanamsa: str) -> tuple[float, float]:
    """Return (sunrise_jd, sunset_jd) bracketing the birth date (disc-centre).

    Mirrors the verified-live ``swe.rise_trans`` pattern from chart/upagrahas.py:
    rsmi flags come BEFORE geopos; both positional.  Sunrise is searched from local
    civil midnight (so we get *this* date's sunrise); sunset from that sunrise.
    """
    geopos: tuple[float, float, float] = (b.longitude, b.latitude, 0.0)
    jd_midnight = _local_midnight_jd(b)
    try:
        with sidereal_mode(ayanamsa):
            _ret_r, tret_r = swe.rise_trans(
                jd_midnight, swe.SUN,
                swe.CALC_RISE | swe.BIT_DISC_CENTER,
                geopos, 0.0, 0.0, swe.FLG_SWIEPH,
            )
            sunrise = float(tret_r[0])
            _ret_s, tret_s = swe.rise_trans(
                sunrise, swe.SUN,
                swe.CALC_SET | swe.BIT_DISC_CENTER,
                geopos, 0.0, 0.0, swe.FLG_SWIEPH,
            )
            sunset = float(tret_s[0])
    except swe.Error as exc:
        # No ordinary sunrise/sunset — polar day/night at extreme latitude (rise_trans returns no
        # event / the search runs off the Moshier range). Kala Bala is genuinely undefined there;
        # fail with a CLEAN domain error instead of leaking the low-level swisseph.Error.
        raise ValueError(
            f"sunrise/sunset undefined at latitude {b.latitude} on "
            f"{b.year:04d}-{b.month:02d}-{b.day:02d}: Kala Bala requires a real day/night span; "
            f"extreme-latitude (polar day/night) charts are out of scope ({exc})") from exc
    return sunrise, sunset


def _day_partition(jd_ut: float, sunrise: float, sunset: float) -> tuple[bool, int]:
    """Return (is_day, day_third) for the birth within the day or night span.

    Day birth: ``sunrise <= jd < sunset``; the span is split into 3 equal parts
    (Tribhaga), ``day_third`` ∈ {0, 1, 2}.  Night birth: the relevant
    sunset→next-sunrise (or prev-sunset→sunrise) span is partitioned the same way.
    """
    is_day = sunrise <= jd_ut < sunset
    if is_day:
        span0, span1 = sunrise, sunset
    else:
        # Night: the span is whichever sunset→sunrise window brackets the birth.
        # For a same-date night birth before sunrise we lack the prior sunset here,
        # so approximate the night span as a full day's complement; day_third is
        # still well-defined as a third of that span.
        span_len = sunset - sunrise
        if jd_ut >= sunset:
            span0, span1 = sunset, sunset + (1.0 - span_len)
        else:  # jd < sunrise: previous night
            span0, span1 = sunrise - (1.0 - span_len), sunrise
    span = span1 - span0
    if span <= 0.0:
        return is_day, 0
    frac = (jd_ut - span0) / span
    third = min(int(frac * 3.0), 2)
    third = max(third, 0)
    return is_day, third


def _hora_lord(
    jd_ut: float, sunrise: float, sunset: float, weekday_lord: str,
) -> str:
    """Hora lord at birth (GBB-5:606-627).

    The 1st hora after sunrise is ruled by the weekday lord; successive (≈1-hour)
    horas step through the Chaldean descending order.  Day horas span sunrise→sunset
    in 12 equal parts; night horas span sunset→sunrise in 12 equal parts — the
    classical 24-hora-per-nychthemeron scheme seeded at the weekday lord.
    """
    is_day = sunrise <= jd_ut < sunset
    if is_day:
        span0, span1 = sunrise, sunset
    elif jd_ut >= sunset:
        span_len = sunset - sunrise
        span0, span1 = sunset, sunset + (1.0 - span_len)
    else:
        span_len = sunset - sunrise
        span0, span1 = sunrise - (1.0 - span_len), sunrise

    hora_len = (span1 - span0) / 12.0
    if hora_len <= 0.0:
        horas_elapsed = 0
    else:
        horas_elapsed = int((jd_ut - span0) / hora_len)

    # Day horas start at the weekday lord; night continues the unbroken cycle
    # (12 day horas already consumed before the first night hora).
    seed = _CHALDEAN_ORDER.index(weekday_lord)
    offset = horas_elapsed if is_day else (12 + horas_elapsed)
    return _CHALDEAN_ORDER[(seed + offset) % 7]


def kala_context(
    birth: BirthData,
    chart: RamanChart,
    *,
    ayanamsa: float,
) -> KalaContext:
    """Build a :class:`KalaContext` from a real birth + cast chart.

    Computed fields: ``birth_degrees``, ``weekday_lord``, ``is_day``, ``day_third``,
    ``hora_lord``, and ``ayanamsa`` (passed through, in degrees).

    Flagged fields (Phase 1c-3 carry-over): ``year_lord`` / ``month_lord`` are set to
    the sentinel ``"UNKNOWN"`` because they require the Ahargana since creation
    (GBB-5:343-423); see the module docstring.  The pure formulae award 0 Sh when a
    lord matches no real planet, so a sentinel under-counts (never mis-counts) Kala.

    Args:
        birth: the birth data (for time-of-day, location).
        chart: the cast chart — used only for ``jd_ut`` (must not be ``None``).
        ayanamsa: ayanamsa in degrees for the Ayana sub-component (caller-supplied).

    Raises:
        ValueError: if the chart carries no ``jd_ut`` (Track-B stated-positions chart).
    """
    if chart.jd_ut is None:
        raise ValueError(
            "kala_context requires a real (ephemeris) chart with jd_ut set; "
            "a from_stated_positions chart has no birth moment."
        )

    jd_ut = chart.jd_ut
    weekday_lord = _WEEKDAY_LORDS[_weekday_index(jd_ut)]
    sunrise, sunset = _sunrise_sunset(birth, chart.ayanamsa)
    is_day, day_third = _day_partition(jd_ut, sunrise, sunset)
    hora_lord = _hora_lord(jd_ut, sunrise, sunset, weekday_lord)

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "kala_context: wd_lord=%s is_day=%s third=%d hora=%s "
            "sunrise=%.5f sunset=%.5f",
            weekday_lord, is_day, day_third, hora_lord, sunrise, sunset,
        )

    return KalaContext(
        birth_degrees=_birth_degrees(birth),
        is_day=is_day,
        day_third=day_third,
        year_lord=_AHARGANA_UNKNOWN,    # Phase 1c-3: needs Ahargana (GBB-5:343-423)
        month_lord=_AHARGANA_UNKNOWN,   # Phase 1c-3: needs Ahargana (GBB-5:343-423)
        weekday_lord=weekday_lord,
        hora_lord=hora_lord,
        ayanamsa=float(ayanamsa),
    )
