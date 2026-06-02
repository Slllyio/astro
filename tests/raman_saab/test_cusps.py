from app.raman_saab.chart import cusps

def test_sandhis_are_midpoints_of_madhyas():
    madhyas = tuple(float(x) for x in range(0, 360, 30))  # 12 evenly-spaced madhyas
    s = cusps.sandhis_from_madhyas(madhyas)
    assert len(s) == 12
    assert abs(s[0] - 345.0) < 1e-9        # midpoint(330, 0) wrapping = 345

def test_bhava_of_uses_sandhi_brackets():
    madhyas = tuple(float(x) for x in range(0, 360, 30))   # madhya[i]=30*i
    s = cusps.sandhis_from_madhyas(madhyas)
    # a planet exactly on madhya[3]=90 is squarely in bhava 4 (1-indexed)
    assert cusps.bhava_of(90.0, s) == 4
    # near a sandhi -> flagged
    assert cusps.is_on_sandhi(s[3], s, orb=1.0) is True
