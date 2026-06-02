"""Gulika & Mandi upagrahas — ephemeris layer.

Computation: the day (sunrise→sunset) and night (sunset→next sunrise) are each
divided into 8 equal parts; parts are ruled cyclically by the 7 weekday lords
starting from the weekday lord of the day (daytime) or 5th from it (night).
Gulika = ascendant at the START of Saturn's part; Mandi = ascendant at the END.

Traditions differ on start vs end for Gulika/Mandi — the convention here
(Gulika=start, Mandi=end) is pinned against an external reference; see
test_gulika_sign_matches_reference in the paired test.

Usage::

    from app.raman_saab.chart.model import BirthData
    from app.raman_saab.chart import upagrahas
    b = BirthData("X", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)
    g = upagrahas.gulika(b, ayanamsa="raman")
    m = upagrahas.mandi(b, ayanamsa="raman")
"""
from __future__ import annotations

import swisseph as swe

from app.raman_saab.chart.ayanamsa import sidereal_mode
from app.raman_saab.chart.model import BirthData, SpecialPoint
from app.raman_saab.chart import varga

# Weekday lord order: index 0=Sunday .. 6=Saturday.
# Each weekday's daytime is divided into 8 parts cycling through this order
# from the day's own lord; night starts from (weekday + 5) % 7.
_WEEKDAY_LORDS: tuple[str, ...] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"
)
_SAT_IDX: int = 6  # Saturn's position in _WEEKDAY_LORDS


def _jd_ut(b: BirthData) -> float:
    """Julian Day Number (UT) for the birth moment."""
    return swe.julday(
        b.year, b.month, b.day,
        (b.hour + b.minute / 60.0) - b.tz_offset,
        swe.GREG_CAL,
    )


def _weekday(jd: float) -> int:
    """Civil weekday 0=Sunday..6=Saturday from a Julian Day number.

    Calibrated so that 1990-07-15 (Bangalore baseline, confirmed Sunday via
    Python datetime) returns 0.  The formula ``int((jd + 1.5) % 7)`` passes
    this test: JD 2448087.77 → int(2448089.27 % 7) = int(0.27 + 7k) = 0.
    """
    return int((jd + 1.5) % 7)


def _local_midnight_jd(b: BirthData) -> float:
    """JD for 00:00 local civil time on the birth date (may be negative UTC hour)."""
    return swe.julday(b.year, b.month, b.day, 0.0 - b.tz_offset, swe.GREG_CAL)


def _calc_rise(start_jd: float, geopos: tuple[float, float, float]) -> float:
    """Next sunrise JD after start_jd (disc-centre).

    VERIFIED LIVE (pyswisseph 2.10.03): rise_trans signature is
      rise_trans(tjd_ut, body, rsmi, geopos, atpress=0.0, attemp=0.0, flags=...)
    rsmi comes BEFORE geopos (both positional); returns (retflag, tret) with tret[0]=JD.
    """
    _ret, tret = swe.rise_trans(
        start_jd, swe.SUN,
        swe.CALC_RISE | swe.BIT_DISC_CENTER,
        geopos, 0.0, 0.0, swe.FLG_SWIEPH,
    )
    return float(tret[0])


def _calc_set(start_jd: float, geopos: tuple[float, float, float]) -> float:
    """Next sunset JD after start_jd (disc-centre)."""
    _ret, tret = swe.rise_trans(
        start_jd, swe.SUN,
        swe.CALC_SET | swe.BIT_DISC_CENTER,
        geopos, 0.0, 0.0, swe.FLG_SWIEPH,
    )
    return float(tret[0])


def _ascendant(jd: float, b: BirthData) -> float:
    """Sidereal lagna longitude (0..360) at the given JD.

    Called inside an already-active sidereal_mode context.
    """
    _cusp, ascmc = swe.houses_ex(jd, b.latitude, b.longitude, b"O", swe.FLG_SIDEREAL)
    return float(ascmc[0]) % 360.0


def _saturn_part_bounds(b: BirthData, ayanamsa: str) -> tuple[float, float]:
    """Return (start_jd, end_jd) of Saturn's 1/8 part of the relevant span.

    Algorithm (HPA, Gulika computation):
    - Day birth: divide sunrise→sunset into 8 equal parts; part lords cycle
      from the weekday's own lord.
    - Night birth: divide preceding-sunset→sunrise (or sunset→next-sunrise)
      into 8 parts; parts start from the lord of (weekday + 5) % 7.
    Saturn's part index i satisfies (_WEEKDAY_LORDS[(seq_start + i) % 7] == "Saturn").
    """
    jd = _jd_ut(b)
    geopos: tuple[float, float, float] = (b.longitude, b.latitude, 0.0)

    with sidereal_mode(ayanamsa):
        # Sunrise: search from local civil midnight so we always get today's sunrise.
        jd_midnight = _local_midnight_jd(b)
        sunrise = _calc_rise(jd_midnight, geopos)

        # Sunset: search from sunrise so we get the same day's sunset.
        sunset = _calc_set(sunrise, geopos)

        is_day = sunrise <= jd < sunset
        wd = _weekday(jd)

        if is_day:
            span0, span1 = sunrise, sunset
            seq_start = wd  # day sequence starts from the weekday's own lord
        else:
            # Night: find the relevant sunset→sunrise span that brackets jd.
            if jd >= sunset:
                # Birth after today's sunset → tonight's span
                next_sunrise = _calc_rise(sunset, geopos)
                span0, span1 = sunset, next_sunrise
            else:
                # Birth before today's sunrise → last night's span
                prev_sunset = _calc_set(jd_midnight - 0.5, geopos)
                span0, span1 = prev_sunset, sunrise
            seq_start = (wd + 5) % 7  # night sequence starts 5 lords ahead

        part = (span1 - span0) / 8.0
        # Find index i such that the (seq_start + i)-th lord is Saturn
        i = (_SAT_IDX - seq_start) % 7
        return span0 + i * part, span0 + (i + 1) * part


def _point(name: str, jd: float, b: BirthData, ayanamsa: str) -> SpecialPoint:
    """Build a SpecialPoint from a Julian Day (lagna at that moment)."""
    with sidereal_mode(ayanamsa):
        lon = _ascendant(jd, b)
    sign = int(lon // 30) + 1
    return SpecialPoint(
        name=name,
        lon=lon,
        sign=sign,
        bhava=sign,  # upagraha bhava = its sign number (whole-sign)
        navamsa_sign=varga.navamsa_sign(lon),
    )


def gulika(birth: BirthData, *, ayanamsa: str = "raman") -> SpecialPoint:
    """Ascendant at the START of Saturn's eighth-part (Gulika Kala).

    Tradition: Gulika = start of Saturn's segment.  Pinned to the Bangalore
    baseline; see test_gulika_sign_matches_reference.
    """
    start, _end = _saturn_part_bounds(birth, ayanamsa)
    return _point("Gulika", start, birth, ayanamsa)


def mandi(birth: BirthData, *, ayanamsa: str = "raman") -> SpecialPoint:
    """Ascendant at the END of Saturn's eighth-part (Mandi).

    Convention (start vs end) must be verified against an external reference;
    some traditions treat Mandi as the same moment as Gulika or as the start
    of the NEXT part.  Here Mandi = end of Saturn's part.
    See test_gulika_sign_matches_reference for the external pin status.
    """
    _start, end = _saturn_part_bounds(birth, ayanamsa)
    return _point("Mandi", end, birth, ayanamsa)
