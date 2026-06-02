from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData

# Canonical pin: Bangalore 1990-07-15 12:00 IST (the repo baseline), but asserted in RAMAN ayanamsa.
BANGALORE = BirthData("Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)

def test_cast_chart_has_nine_grahas_and_lagna():
    chart = cast_chart(BANGALORE, ayanamsa="raman")
    assert set(chart.planets) == {"Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"}
    assert 1 <= chart.asc_sign <= 12
    assert len(chart.bhava_madhyas) == 12 and len(chart.bhava_sandhis) == 12

def test_ketu_opposes_rahu():
    chart = cast_chart(BANGALORE, ayanamsa="raman")
    diff = abs((chart.planets["Ketu"].lon - chart.planets["Rahu"].lon) % 360 - 180)
    assert diff < 1e-6

def test_every_planet_has_a_bhava_in_range():
    chart = cast_chart(BANGALORE, ayanamsa="raman")
    for p in chart.planets.values():
        assert 1 <= p.bhava <= 12 and 1 <= p.rasi_house <= 12
