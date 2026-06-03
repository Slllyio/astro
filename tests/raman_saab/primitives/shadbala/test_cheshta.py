from app.raman_saab.primitives.shadbala import cheshta

# GBB Standard Horoscope: stated mean longitudes, seegrochchas, true longitudes (deg).
_TRUE = {"Mars": 229 + 49 / 60, "Mercury": 180 + 33 / 60, "Jupiter": 83 + 35 / 60, "Venus": 170 + 4 / 60, "Saturn": 124 + 51 / 60}
_MEAN = {"Mars": 266.34, "Mercury": 181.2275, "Jupiter": 66.91, "Venus": 181.2275, "Saturn": 111.23}
_SEEG = {"Mars": 181.2275, "Mercury": 174.49, "Jupiter": 181.2275, "Venus": 158.35, "Saturn": 181.2275}
_EXPECTED = {"Mars": 22.28, "Mercury": 2.13, "Jupiter": 35.33, "Venus": 5.76, "Saturn": 21.06}


def test_chesta_kendra_pins_ramans_worked_values():
    """Kuja CK should be 293.15 (reduced 66.85), matching GBB Ex.49 exactly."""
    ck = cheshta.chesta_kendra(_SEEG["Mars"], _MEAN["Mars"], _TRUE["Mars"])
    assert abs(ck - 293.15) < 0.2


def test_cheshta_bala_fixture_five_planets():
    """All 5 GBB Standard Horoscope ChestaBala values must reproduce to ±0.5 Shashtiamsas."""
    for p, exp in _EXPECTED.items():
        got = cheshta.cheshta_bala(_SEEG[p], _MEAN[p], _TRUE[p])
        assert abs(got - exp) < 0.5, f"{p}: got {got}, expected {exp}"


def test_sun_moon_have_no_cheshta_in_total():
    """PLANETS tuple must be exactly the 5 non-luminaries — Sun/Moon absent (GBB §6)."""
    assert cheshta.PLANETS == ("Mars", "Mercury", "Jupiter", "Venus", "Saturn")


def test_cheshta_end_to_end_on_ephemeris_chart():
    """Real chart: Cheshta computed from jd_ut via the epoch method stays in [0,60] for the
    5 planets, and the chart-level helper returns 0 for Sun/Moon/nodes."""
    from app.raman_saab.chart.adapter import cast_chart
    from app.raman_saab.chart.model import BirthData
    from app.raman_saab.chart import mean_longitudes as ml
    chart = cast_chart(BirthData("X", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59), ayanamsa="raman")
    mns = ml.mean_longitudes(chart.jd_ut, 1990)
    for p in cheshta.PLANETS:
        val = cheshta.cheshta_bala_for_chart(p, chart, mns["mean"], mns["seeg"])
        assert 0.0 <= val <= 60.0
    for absent in ("Sun", "Moon", "Rahu", "Ketu"):
        assert cheshta.cheshta_bala_for_chart(absent, chart, mns["mean"], mns["seeg"]) == 0.0
