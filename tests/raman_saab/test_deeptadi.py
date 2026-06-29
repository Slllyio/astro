"""Deeptadi avasthas — Raman's ten planetary result-states (HPA Ch.7). Computed from dignity +
combustion + retrogression + position; additive/reported (verdict-invariant)."""
from __future__ import annotations

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData, RamanChart
from app.raman_saab.primitives import deeptadi

_MAINPURI = BirthData(name="M", year=1989, month=10, day=12, hour=10, minute=2,
                      tz_offset=5.5, latitude=27.23, longitude=79.03)


def test_mainpuri_states():
    """Mercury exalted in Virgo -> Deeptha; Mars combust -> Vikala."""
    ch = cast_chart(_MAINPURI, ayanamsa="raman")
    states = deeptadi.chart_states(ch)
    assert states["Mercury"][0] == "Deeptha"
    assert states["Mars"][0] == "Vikala"
    assert all(s in deeptadi.RESULTS for s, _ in states.values())


def test_polarity_matches_results_table():
    ch = cast_chart(_MAINPURI, ayanamsa="raman")
    for planet in ("Sun", "Mercury", "Jupiter"):
        assert deeptadi.polarity(planet, ch) == deeptadi.RESULTS[deeptadi.state(planet, ch)][0]


def test_exalted_is_deeptha_debil_is_khala():
    exalt = RamanChart.from_stated_positions({"Saturn": {"lon": 200.0, "bhava": 1}},  # Libra (exalt)
                                             asc_lon=200.0, ayanamsa="raman")
    debil = RamanChart.from_stated_positions({"Saturn": {"lon": 5.0, "bhava": 1}},    # Aries (debil)
                                             asc_lon=5.0, ayanamsa="raman")
    assert deeptadi.state("Saturn", exalt) == "Deeptha"
    assert deeptadi.state("Saturn", debil) == "Khala"


def test_ten_states_all_have_a_result_and_polarity():
    assert len(deeptadi.RESULTS) == 10
    assert all(pol in (1, -1) for pol, _ in deeptadi.RESULTS.values())
