from __future__ import annotations
from app.raman_saab.primitives import nakshatra as nk
from app.raman_saab.chart.model import RamanChart


def test_nakshatra_lords_cycle():
    assert nk.nakshatra_lord(1) == "Ketu"      # Ashwini
    assert nk.nakshatra_lord(2) == "Venus"     # Bharani
    assert nk.nakshatra_lord(10) == "Ketu"     # Magha (cycle repeats every 9)
    assert nk.nakshatra_lord(27) == "Mercury"  # Revati


def test_tara_position_from_janma():
    # Moon at 0° (Ashwini=1). A planet also in Ashwini = tara 1 (janma); 3rd star = vipat (3).
    chart = RamanChart.from_stated_positions(
        {"Moon": {"lon": 0.0, "bhava": 1}, "Mars": {"lon": 2 * (360 / 27), "bhava": 1}},
        asc_lon=0.0, ayanamsa="raman")
    assert nk.tara_position("Mars", chart) == 3
    assert nk.tara_of("Mars", chart) == "vipat"
