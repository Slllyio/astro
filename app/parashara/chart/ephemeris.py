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

_FLAGS: Final[int] = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED


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
