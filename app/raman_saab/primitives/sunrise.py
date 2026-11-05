"""Sunrise on the birth date (JD UT, disc centre).

Moved here from the removed ``app.raman_saab.rectification.arithmetic`` (2026-11-05) so
callers that only need sunrise (e.g. ``tools/raman_saab/build_holdout.py``) keep working.
Replicates the verified ``kala_context._sunrise_sunset`` swe.rise_trans pattern (rsmi
flags BEFORE geopos; search from local civil midnight so it is *this* date's sunrise).
"""
from __future__ import annotations

import swisseph as swe

from app.raman_saab.chart.ayanamsa import sidereal_mode
from app.raman_saab.chart.model import BirthData


def sunrise_jd(birth: BirthData, ayanamsa: str) -> float:
    """Sunrise (JD UT, disc-centre) on the birth date."""
    jd_midnight = swe.julday(birth.year, birth.month, birth.day,
                             -birth.tz_offset, swe.GREG_CAL)
    geopos = (birth.longitude, birth.latitude, 0.0)
    with sidereal_mode(ayanamsa):
        _ret, tret = swe.rise_trans(
            jd_midnight, swe.SUN,
            swe.CALC_RISE | swe.BIT_DISC_CENTER,
            geopos, 0.0, 0.0, swe.FLG_SWIEPH)
    return float(tret[0])


__all__ = ["sunrise_jd"]
