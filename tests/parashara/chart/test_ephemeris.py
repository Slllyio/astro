"""The Kala-bala time context resolved from a birth (BPHS ch.27 — sunrise + the Hindu calendar).

The doctrinal anchor is Parashara's OWN worked example (BPHS-27:412-424): the astrological year that
began on 1 June 1984 is ruled by Thursday's lord (Jupiter), and that month by Friday's lord (Venus).
Reproducing it pins the Ahargana arithmetic (/360 for Varsha, /30 for Masa) against the source, not
against engine self-output. The weekday calibration is pinned against ordinary civil facts.
"""
from __future__ import annotations

import swisseph as swe

from app.parashara.chart.ephemeris import _WEEKDAY_LORD, _ahargana, _weekday, kala_context


class TestAharganaWorkedExample:
    """BPHS-27:412-424 — the 1 June 1984 astrological year/month lords."""

    def _lords(self, year, month, day):
        jd = swe.julday(year, month, day, 12.0, swe.GREG_CAL)
        A = _ahargana(int(jd) + 0.5)
        varsha = _WEEKDAY_LORD[((A // 360) * 3 + 1) % 7 - 1]
        masa = _WEEKDAY_LORD[((A // 30) * 2 + 1) % 7 - 1]
        return varsha, masa

    def test_1984_varsha_is_jupiter_masa_is_venus(self):
        """Parashara's example: the year from 1 Jun 1984 -> Jupiter (Thu); its month -> Venus (Fri)."""
        varsha, masa = self._lords(1984, 6, 1)
        assert varsha == "Jupiter"
        assert masa == "Venus"


class TestWeekday:
    """_weekday(jd) = 0=Sunday..6=Saturday, calibrated against civil dates."""

    def test_known_weekdays(self):
        for (y, m, d, lord) in [(1990, 7, 15, "Sun"), (2000, 1, 1, "Saturn"),
                                (1984, 6, 1, "Venus")]:
            jd = swe.julday(y, m, d, 6.0, swe.GREG_CAL)  # ~sunrise
            assert _WEEKDAY_LORD[_weekday(jd)] == lord


class TestKalaContext:
    """The resolved context for the canonical Bangalore noon birth."""

    def test_canonical_noon(self):
        ctx = kala_context(year=1990, month=7, day=15, hour=12, minute=0,
                           tz_offset=5.5, latitude=12.97, longitude=77.59)
        assert ctx.is_day is True                     # a noon birth
        assert ctx.unnata_fraction == 1.0             # exactly noon
        assert ctx.weekday_lord == "Sun"              # 1990-07-15 was a Sunday
        assert ctx.day_third in (1, 2, 3)
        assert ctx.hora_lord in _WEEKDAY_LORD

    def test_midnight_is_night(self):
        ctx = kala_context(year=1990, month=7, day=15, hour=0, minute=30,
                           tz_offset=5.5, latitude=12.97, longitude=77.59)
        assert ctx.is_day is False
        assert ctx.unnata_fraction < 0.1              # near apparent midnight
