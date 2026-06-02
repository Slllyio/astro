from __future__ import annotations

from app.raman_saab.primitives import functional_nature as fn
from app.raman_saab.chart.model import RamanChart


def _chart(asc_lon: float) -> RamanChart:
    # one dummy planet so the chart is valid; functional_nature only needs asc_sign
    return RamanChart.from_stated_positions({"Sun": {"lon": 0.0, "bhava": 1}},
                                            asc_lon=asc_lon, ayanamsa="raman")


def test_printed_table_cells_verbatim():
    # Aries (asc_sign 1): Jupiter best benefic; Mercury worst malefic. HTJAH-I:525
    c = _chart(5.0)
    assert fn.functional_nature("Jupiter", c) == "benefic"
    assert fn.functional_nature("Mercury", c) == "malefic"
    # Libra (asc_sign 7): Mars is the printed NEUTRAL ("feeble benefic"). HTJAH-I:550
    # Libra is sign 7, longitude range 180-210, so start at 6*30+5 = 185.
    c7 = _chart(6 * 30 + 5.0)
    assert fn.functional_nature("Saturn", c7) == "yogakaraka"   # Saturn is Libra's YK (overlay)
    assert fn.functional_nature("Sun", c7) == "malefic"


def test_yoga_karakas_only_mars_saturn_venus():
    # owns a kendra (other than 1st) AND a trikona (other than 1st) from the Lagna.
    assert fn.is_yogakaraka("Mars", 4) and fn.is_yogakaraka("Mars", 5)       # Cancer, Leo
    assert fn.is_yogakaraka("Saturn", 7) and fn.is_yogakaraka("Saturn", 2)   # Libra, Taurus
    assert fn.is_yogakaraka("Venus", 10) and fn.is_yogakaraka("Venus", 11)   # Cap, Aqu
    assert not fn.is_yogakaraka("Jupiter", 1)
    assert not fn.is_yogakaraka("Mars", 1)


def test_kendradhipati_dosha_for_benefic_kendra_lords():
    # Jupiter for Gemini (asc 3) owns the 7th & 10th (both kendras) -> dosha.
    assert fn.kendradhipati_dosha("Jupiter", 3) is True
    # Mars for Aries (asc 1) is a natural malefic -> no kendradhipati dosha.
    assert fn.kendradhipati_dosha("Mars", 1) is False


def test_houses_owned_from_lagna():
    assert fn.houses_owned("Saturn", 11) == [1, 12]   # Aquarius lagna: Saturn owns 1 & 12
    assert fn.houses_owned("Sun", 5) == [1]           # Leo lagna: Sun owns the 1st only
