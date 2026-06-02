import swisseph as swe
from app.raman_saab.chart.ayanamsa import sidereal_mode, AYANAMSA

def test_mode_is_restored_after_context():
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    before = swe.get_ayanamsa_ut(2451545.0)          # Lahiri value at J2000
    with sidereal_mode("raman"):
        inside = swe.get_ayanamsa_ut(2451545.0)
        assert abs(inside - before) > 0.1            # Raman differs from Lahiri (~0.9°)
    after = swe.get_ayanamsa_ut(2451545.0)
    assert abs(after - before) < 1e-9                # restored exactly

def test_unknown_ayanamsa_raises():
    import pytest
    with pytest.raises(ValueError):
        with sidereal_mode("nonsense"):
            pass
