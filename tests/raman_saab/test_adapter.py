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


def test_adapter_populates_combust_fraction():
    """Adapter must compute combust_fraction via the primitives module (not stub 0.0)."""
    from app.raman_saab.primitives.combustion import combust_fraction
    chart = cast_chart(BANGALORE, ayanamsa="raman")
    # All planets must have a float in [0, 1].
    for p in chart.planets.values():
        assert 0.0 <= p.combust_fraction <= 1.0
    # Values must match what the combustion primitive would compute independently.
    for name, p in chart.planets.items():
        assert p.combust_fraction == combust_fraction(name, chart)


def test_adapter_populates_pure_special_fields():
    """Task 7: karakamsa, arudha_lagna, maraka_points, balarishta are filled by cast_chart."""
    from app.raman_saab.primitives.special_points import atmakaraka
    chart = cast_chart(BANGALORE, ayanamsa="raman")
    assert chart.karakamsa is not None and chart.karakamsa.name == "Karakamsa"
    assert chart.karakamsa.sign == chart.planets[atmakaraka(chart)].navamsa_sign
    assert chart.arudha_lagna is not None and chart.arudha_lagna.name == "ArudhaLagna"
    assert chart.maraka_points is not None and len(chart.maraka_points.units) >= 1
    assert chart.balarishta is not None and isinstance(chart.balarishta.applies, bool)


def test_adapter_populates_upagrahas():
    """Task 8: upagrahas dict with Gulika and Mandi are filled by cast_chart."""
    chart = cast_chart(BANGALORE, ayanamsa="raman")
    assert chart.upagrahas is not None
    assert set(chart.upagrahas) == {"Gulika", "Mandi"}
    assert 1 <= chart.upagrahas["Gulika"].sign <= 12


def test_adapter_fills_shadbala_for_ephemeris_chart():
    """Task 2: cast_chart attaches a ShadbalaBreakdown + ishta/kashta to all 7 grahas."""
    from app.raman_saab.chart.model import ShadbalaBreakdown
    chart = cast_chart(BANGALORE, ayanamsa="raman")
    for name in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        p = chart.planets[name]
        assert isinstance(p.shadbala_rupas, ShadbalaBreakdown)
        rupas = p.shadbala_rupas.total / 60.0
        assert 0.0 < rupas < 12.0, f"{name} total/60 = {rupas} out of band"
        assert p.ishta is not None and 0.0 <= p.ishta <= 60.0
        assert p.kashta is not None and 0.0 <= p.kashta <= 60.0
    # Nodes carry no Shadbala (they are never in SWE_PLANETS).
    assert chart.planets["Rahu"].shadbala_rupas is None
    assert chart.planets["Ketu"].shadbala_rupas is None


def test_from_stated_positions_leaves_shadbala_none():
    """Track-B charts have no ephemeris context → shadbala_rupas stays None."""
    from app.raman_saab.chart.model import RamanChart
    chart = RamanChart.from_stated_positions(
        {"Sun": {"lon": 100.0, "bhava": 1}, "Moon": {"lon": 200.0, "bhava": 7}},
        asc_lon=0.0, ayanamsa="raman")
    for p in chart.planets.values():
        assert p.shadbala_rupas is None
        assert p.ishta is None and p.kashta is None
