import pytest
from app.core.ephemeris_engine import (
    calculate_jd,
    get_ayanamsa,
    calculate_d1_position,
    calculate_divisional_longitude
)
import swisseph as swe

def test_ayanamsa_shift():
    """
    Test 2: Verify Ayanamsa shift effect (Tropical vs. Sidereal difference).
    """
    # 2000-01-01 12:00:00 UTC
    jd = swe.julday(2000, 1, 1, 12.0, swe.GREG_CAL)
    
    # Calculate Tropical position (Sun)
    swe.set_sid_mode(0) # Standard tropical, ignore sidereal
    res_tropical, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)
    trop_long = res_tropical[0]
    
    # Calculate Sidereal position (Lahiri)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    res_sidereal, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
    sid_long = res_sidereal[0]
    
    # The difference should be roughly the Ayanamsa (~23 degrees 51 mins for 2000)
    ayanamsa = swe.get_ayanamsa_ut(jd)
    diff = (trop_long - sid_long) % 360
    
    assert abs(diff - ayanamsa) < 0.01, "Sidereal and Tropical difference should closely match Lahiri Ayanamsa"

def test_sign_boundary_no_overflow():
    """
    Test 1 & 3: Ensure boundary conditions don't overflow improperly.
    Verify that a planet at exactly 29.999 degrees doesn't round up to the next sign.
    """
    import math
    
    # Create a synthetic longitude exactly at the edge of Virgo (Sign 6, index 5)
    # Virgo is 150 to 180 degrees. 179.9999 is in Virgo.
    edge_longitude = 179.9999
    
    sign_index = int(edge_longitude // 30)
    assert sign_index == 5, f"Expected sign index 5 (Virgo), got {sign_index}"
    
    degree_in_sign = edge_longitude % 30
    assert math.isclose(degree_in_sign, 29.9999, rel_tol=1e-9), f"Expected 29.9999 degrees, got {degree_in_sign}"
    
    # Exactly on the boundary (180.0000) should be Libra (Sign 7, index 6)
    boundary_longitude = 180.0000
    sign_index_bound = int(boundary_longitude // 30)
    assert sign_index_bound == 6, f"Expected sign index 6 (Libra), got {sign_index_bound}"

def test_divisional_calculation_edge():
    """
    Test 3 extension: Verify Navamsa and Dasamsa accurately compute at boundary points.
    """
    # 29 deg 59 min in Aries = 29.9833 degrees
    # This is the 9th Navamsa of Aries (26.66 to 30.00)
    # 9th Navamsa of Aries is Sagittarius.
    long_aries_end = 29.9833
    d9_long = calculate_divisional_longitude(long_aries_end, 9)
    d9_sign_index = int(d9_long // 30)
    # Sagittarius is index 8
    assert d9_sign_index == 8, f"29.9833 Aries should be Sagittarius Navamsa, got index {d9_sign_index}"
    
    # This is the 10th Dasamsa of Aries (27.00 to 30.00)
    # Odd sign (Aries=0) starts at itself (Aries=0). 10th Dasamsa is 0 + 9 = 9 = Capricorn.
    d10_long = calculate_divisional_longitude(long_aries_end, 10)
    d10_sign_index = int(d10_long // 30)
    # Capricorn is index 9
    assert d10_sign_index == 9, f"29.9833 Aries should be Capricorn Dasamsa, got index {d10_sign_index}"
