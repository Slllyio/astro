"""Cast a Parashara chart from birth data — the inputs this engine's primitives consume.

The primitives take a lightweight shape (sidereal longitudes + ascendant sign + Moon paksha + janma
nakshatra) rather than a heavy chart model, so this caster produces exactly that.

Positions come from the shared **pure-astronomy** ephemeris (`app.core.ephemeris_engine`), the
swisseph layer both engines already use — casting a longitude is astronomy, not any tradition's
doctrine. The isolation test allows this module only that astronomy substrate, nothing doctrinal.
Ayanamsa is the repo default (Lahiri sidereal), consistent across the platform.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Mapping

import app.core.ephemeris_engine as _eph   # pure-astronomy substrate (swisseph); named in full so
                                           # the isolation guard sees the exact module, not the pkg
from app.parashara.chart.ephemeris import kala_context, speeds_and_ayanamsa
from app.parashara.primitives.shadbala.kala import KalaContext

_NAK_SPAN: Final[float] = 360.0 / 27.0


@dataclass(frozen=True)
class ParasharaChart:
    """The minimal chart the Parashara primitives need."""
    longitudes: Mapping[str, float]     # graha -> sidereal longitude (deg)
    asc_sign: int                       # 1..12
    asc_longitude: float
    moon_waxing: bool                   # Shukla Paksha (Moon ahead of Sun by 0..180)
    janma_nakshatra: int                # 1..27 (Moon's nakshatra)
    speeds: Mapping[str, float]         # graha -> longitudinal speed (deg/day); <0 retrograde
    ayanamsa: float                     # Lahiri ayanamsa (deg) at birth — for Ayana bala
    kala: KalaContext                   # birth's time facts — for Kala bala's time sub-components


def _nakshatra_number(longitude: float) -> int:
    return int((longitude % 360.0) // _NAK_SPAN) + 1


def _moon_is_waxing(sun_lon: float, moon_lon: float) -> bool:
    """Shukla Paksha: the Moon is ahead of the Sun by 0..180 degrees (bright, waxing half)."""
    return 0.0 < (moon_lon - sun_lon) % 360.0 < 180.0


def cast(*, year: int, month: int, day: int, hour: int, minute: int,
         tz_offset: float, latitude: float, longitude: float) -> ParasharaChart:
    """Cast a Parashara chart for the given birth (Lahiri sidereal)."""
    charts = _eph.calculate_all_charts(year, month, day, hour, minute, tz_offset,
                                       latitude=latitude, longitude=longitude)
    d1 = charts["d1"]
    asc = charts["ascendant"]
    if asc is None:                                  # defensive: lat/lon were required above
        raise ValueError("ascendant could not be computed; latitude/longitude required")

    longitudes = {name: pos["longitude"] for name, pos in d1.items()}
    speeds, ayanamsa = speeds_and_ayanamsa(year=year, month=month, day=day, hour=hour,
                                           minute=minute, tz_offset=tz_offset)
    kala = kala_context(year=year, month=month, day=day, hour=hour, minute=minute,
                        tz_offset=tz_offset, latitude=latitude, longitude=longitude)
    return ParasharaChart(
        longitudes=longitudes,
        asc_sign=asc["sign"],
        asc_longitude=asc["longitude"],
        moon_waxing=_moon_is_waxing(longitudes["Sun"], longitudes["Moon"]),
        janma_nakshatra=_nakshatra_number(longitudes["Moon"]),
        speeds=speeds,
        ayanamsa=ayanamsa,
        kala=kala,
    )
