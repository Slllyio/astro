from app.raman_saab.chart import varga

def test_navamsa_fire_sign_starts_aries():
    # 1° Aries -> first navamsa -> Aries (fire start). 100° (Cancer 10°) per element rule.
    assert varga.navamsa_sign(1.0) == 1

def test_nakshatra_pada_boundaries():
    # Each nakshatra = 13°20'. 0° -> Ashwini(1) pada 1; 13.5° -> Bharani(2) pada 1.
    assert varga.nakshatra_pada(0.0) == (1, 1)
    assert varga.nakshatra_pada(13.5)[0] == 2

def test_vargottama_helper():
    assert varga.is_vargottama(sign=1, navamsa=1) is True
    assert varga.is_vargottama(sign=1, navamsa=2) is False
