"""Phase 2 harness: the ayanamsa patch really changes the sidereal frame, and nothing else."""
from __future__ import annotations

import swisseph as swe

from tools.validation import reliability as rel

ROW = dict(person_id="x", birth_date="1990-07-15", birth_time="12:00", tz_offset=5.5,
           latitude=12.97, longitude=77.59)   # canonical Bangalore baseline


def _moon(label: str) -> float:
    from app.parashara.chart.cast import cast
    minutes, sidm = rel.CONDITIONS[label]
    rel._TARGET[0] = None if sidm == swe.SIDM_LAHIRI else sidm
    try:
        return cast(year=1990, month=7, day=15, hour=12, minute=0, tz_offset=5.5 - minutes / 60,
                    latitude=12.97, longitude=77.59).longitudes["Moon"]
    finally:
        rel._TARGET[0] = None


class TestAyanamsaPatch:
    def test_raman_ayanamsa_shifts_moon_by_ayanamsa_difference(self):
        """Lahiri minus Raman ayanamsa (~1.4 deg in 1990) is exactly the shift in sidereal Moon."""
        orig = swe.set_sid_mode
        rel.install_ayanamsa_patch()
        try:
            jd = swe.julday(1990, 7, 15, 6.5)
            rel._ORIG_SET_SID(swe.SIDM_LAHIRI); lahiri = swe.get_ayanamsa_ut(jd)
            rel._ORIG_SET_SID(swe.SIDM_RAMAN); raman = swe.get_ayanamsa_ut(jd)
            shift = (_moon("raman_ayanamsa") - _moon("base")) % 360
            assert 1.0 < lahiri - raman < 2.0
            assert abs(shift - (lahiri - raman)) < 0.01
        finally:
            swe.set_sid_mode = orig

    def test_plus_60_minutes_moves_moon_half_a_degree(self):
        """The Moon moves ~0.5 deg per hour: the tz shift really moves the birth moment +1h."""
        orig = swe.set_sid_mode
        rel.install_ayanamsa_patch()
        try:
            d = (_moon("+60m") - _moon("base")) % 360
            assert 0.4 < d < 0.7
        finally:
            swe.set_sid_mode = orig


class TestKappa:
    def test_identical_constant_series_is_perfectly_reliable(self):
        """A constant instrument that never changes counts as kappa 1, not undefined."""
        assert rel._kappa([True] * 5, [True] * 5) == 1.0
