"""The extra astronomy Shadbala needs — planetary speeds and the ayanamsa — via swisseph.

The base caster (`cast`) gets positions/ascendant/nakshatra from `app.core.ephemeris_engine`, which
does not return speeds or the ayanamsa. Cheshta bala needs each planet's longitudinal SPEED, and
Ayana bala needs the AYANAMSA (to convert nirayana -> sayana for declination). Both are pure
astronomy, computed here with swisseph directly (Lahiri sidereal, matching the platform).
"""
from __future__ import annotations

from typing import Final

import swisseph as swe

from app.core.ephemeris_engine import PLANETS, calculate_jd, to_decimal_hours
from app.parashara.primitives.shadbala.kala import KalaContext

_FLAGS: Final[int] = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED

#: Weekday number (0=Sunday..6=Saturday) -> its ruling graha.
_WEEKDAY_LORD: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
#: Planetary-hour order (BPHS-27:446): first hora = weekday lord, then this cycle.
_HORA_ORDER: Final[tuple[str, ...]] = (
    "Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars")
#: Creation Ahargana (days since Creation) as on 1 Jan 1860 — Burgess, per BPHS-27:379.
_AHARGANA_1860: Final[int] = 714404108573
_JD_1860: Final[float] = swe.julday(1860, 1, 1, 0.0, swe.GREG_CAL)


def _birth_jd(*, year: int, month: int, day: int, hour: int, minute: int, tz_offset: float) -> float:
    return calculate_jd(year, month, day, to_decimal_hours(hour, minute), tz_offset)


def speeds_and_ayanamsa(*, year: int, month: int, day: int, hour: int, minute: int,
                        tz_offset: float) -> tuple[dict[str, float], float]:
    """(longitudinal speed deg/day per graha, ayanamsa deg) for the birth moment.

    Speed < 0 is retrograde. Ketu's speed mirrors Rahu's (they are 180 deg apart, same rate).
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    jd = _birth_jd(year=year, month=month, day=day, hour=hour, minute=minute, tz_offset=tz_offset)
    speeds: dict[str, float] = {}
    for name, pid in PLANETS.items():
        xx, _ = swe.calc_ut(jd, pid, _FLAGS)
        speeds[name] = xx[3]                 # deg/day; negative = retrograde
    speeds["Ketu"] = speeds.get("Rahu", 0.0)  # Ketu shares Rahu's rate
    ayanamsa = swe.get_ayanamsa_ut(jd)
    return speeds, ayanamsa


def _sunrise(jd: float, geopos: tuple[float, float, float], rise: bool) -> float:
    rsmi = (swe.CALC_RISE if rise else swe.CALC_SET) | swe.BIT_DISC_CENTER
    _, tret = swe.rise_trans(jd, swe.SUN, rsmi, geopos)
    return tret[0]


def _weekday(jd_sunrise: float) -> int:
    """0=Sunday..6=Saturday for the astrological day beginning at `jd_sunrise`."""
    return (int(jd_sunrise + 1.5)) % 7      # JDN+1.5 floor mod 7, 0=Sunday (calibrated in tests)


def _ahargana(jd_midnight: float) -> int:
    return _AHARGANA_1860 + int(round(jd_midnight - _JD_1860))


def kala_context(*, year: int, month: int, day: int, hour: int, minute: int,
                 tz_offset: float, latitude: float, longitude: float) -> KalaContext:
    """Resolve the Kala-bala time inputs for a birth (BPHS ch.27: Nathonnata, Tribhaga, Vara, Hora,
    Masa, Varsha)."""
    jd = calculate_jd(year, month, day, to_decimal_hours(hour, minute), tz_offset)
    geopos = (longitude, latitude, 0.0)

    sunrise = _sunrise(jd - 1.0, geopos, rise=True)
    if sunrise > jd:                         # birth is before this day's sunrise -> use previous
        sunrise = _sunrise(jd - 2.0, geopos, rise=True)
    sunset = _sunrise(sunrise, geopos, rise=False)
    next_sunrise = _sunrise(sunset, geopos, rise=True)
    is_day = sunrise <= jd < sunset

    # Tribhaga: which third of the day (or night) of birth.
    if is_day:
        frac = (jd - sunrise) / (sunset - sunrise)
    else:
        start = sunset if jd >= sunset else _sunrise(sunrise - 1.0, geopos, rise=False)
        end = next_sunrise if jd >= sunset else sunrise
        frac = (jd - start) / (end - start)
    day_third = min(int(frac * 3) + 1, 3)

    # Nathonnata: 0 at local apparent midnight -> 1 at noon (uses clock hour as local solar approx).
    t = to_decimal_hours(hour, minute)
    unnata_fraction = 1.0 - abs(t - 12.0) / 12.0

    weekday = _weekday(sunrise)
    weekday_lord = _WEEKDAY_LORD[weekday]

    # Hora: 24 equal horas from sunrise; 1st = weekday lord, then the hora cycle.
    hora_len = (next_sunrise - sunrise) / 24.0
    hora_index = max(0, min(int((jd - sunrise) / hora_len), 23))
    start_idx = _HORA_ORDER.index(weekday_lord)
    hora_lord = _HORA_ORDER[(start_idx + hora_index) % 7]

    # Varsha (year) + Masa (month) lords via the Ahargana (BPHS-27:379-410; /360 and /30).
    aharg = _ahargana(int(jd) + 0.5 if jd - int(jd) >= 0.5 else int(jd) - 0.5)
    varsha_lord = _WEEKDAY_LORD[((aharg // 360) * 3 + 1) % 7 - 1]
    masa_lord = _WEEKDAY_LORD[((aharg // 30) * 2 + 1) % 7 - 1]
    return KalaContext(is_day=is_day, day_third=day_third, unnata_fraction=unnata_fraction,
                       weekday_lord=weekday_lord, hora_lord=hora_lord,
                       varsha_lord=varsha_lord, masa_lord=masa_lord)


def transit_signs(*, year: int, month: int, day: int, hour: int = 12, minute: int = 0,
                  tz_offset: float = 0.0) -> dict[str, int]:
    """The sidereal sign (1..12) of each graha on a transit date — the input gochara needs.

    Lahiri sidereal, matching the platform; noon by default (a transit sign rarely turns within a
    day for the slow grahas). Ketu mirrors Rahu (180 deg opposite -> the 7th sign)."""
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    jd = calculate_jd(year, month, day, to_decimal_hours(hour, minute), tz_offset)
    out: dict[str, int] = {}
    for name, pid in PLANETS.items():
        xx, _ = swe.calc_ut(jd, pid, _FLAGS)
        out[name] = int(xx[0] % 360.0 // 30) + 1
    if "Rahu" in out:
        out["Ketu"] = ((out["Rahu"] - 1 + 6) % 12) + 1
    return out


def special_lagnas(*, year: int, month: int, day: int, hour: int, minute: int,
                   tz_offset: float, latitude: float, longitude: float) -> dict[str, float]:
    """Bhava / Hora / Ghatika Lagna longitudes (BPHS ch.5) — the Sun's sunrise longitude advanced
    by the ghatis elapsed since sunrise (1 day = 60 ghatis). Pure formula in
    `doctrine.special_lagnas`; this supplies the two ephemeris inputs."""
    from app.parashara.doctrine.special_lagnas import special_lagna_longitudes
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    jd = calculate_jd(year, month, day, to_decimal_hours(hour, minute), tz_offset)
    geopos = (longitude, latitude, 0.0)
    sunrise = _sunrise(jd - 1.0, geopos, rise=True)
    if sunrise > jd:
        sunrise = _sunrise(jd - 2.0, geopos, rise=True)
    sun_at_sunrise = swe.calc_ut(sunrise, swe.SUN, _FLAGS)[0][0] % 360.0
    ghatis = (jd - sunrise) * 60.0                       # 1 day = 60 ghatis
    return special_lagna_longitudes(sun_at_sunrise, ghatis)


def gulika_longitude(*, year: int, month: int, day: int, hour: int, minute: int,
                     tz_offset: float, latitude: float, longitude: float) -> float:
    """Gulika's (Mandi's) sidereal longitude — the ascendant rising at the start of SATURN's eighth
    of the day (night: the eighth counted from the 5th weekday lord). BPHS ch.3:1303-1325.

    The day (sunrise->sunset) or night (sunset->next sunrise) is split into 8 equal parts; the 1st is
    the weekday lord (night: the 5th weekday lord), then in weekday order; Saturn's part is Gulika.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    jd = calculate_jd(year, month, day, to_decimal_hours(hour, minute), tz_offset)
    geopos = (longitude, latitude, 0.0)
    sunrise = _sunrise(jd - 1.0, geopos, rise=True)
    if sunrise > jd:
        sunrise = _sunrise(jd - 2.0, geopos, rise=True)
    sunset = _sunrise(sunrise, geopos, rise=False)
    is_day = sunrise <= jd < sunset

    weekday = _weekday(sunrise)                          # 0=Sun..6=Saturn (Saturn's index = 6)
    if is_day:
        span_start, span_end, start_lord = sunrise, sunset, weekday
    else:
        span_start = sunset if jd >= sunset else _sunrise(sunrise - 1.0, geopos, rise=False)
        span_end = _sunrise(sunset, geopos, rise=True) if jd >= sunset else sunrise
        start_lord = (weekday + 4) % 7                   # the 5th weekday lord (night)
    part = (span_end - span_start) / 8.0
    saturn_k = (6 - start_lord) % 7                      # which eighth Saturn rules (Saturn index 6)
    gulika_jd = span_start + saturn_k * part
    _, ascmc = swe.houses_ex(gulika_jd, latitude, longitude, b"P", swe.FLG_SIDEREAL)
    return ascmc[0] % 360.0
