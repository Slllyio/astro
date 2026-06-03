"""Sparse Track-B charts (missing Moon / lords) must not crash the Phase-1b
primitives — they should return safe defaults via the guard clauses. The judge
goldens inject `stated_positions` that may omit planets, so every primitive that
references the Moon or a specific lord has to tolerate its absence."""
from __future__ import annotations

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives import balarishta, bhangas, maraka


def _sparse(lons: dict[str, float]) -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()},
        asc_lon=0.0, ayanamsa="raman")


def test_kemadruma_false_when_moon_absent():
    """No Moon -> kemadruma / kemadruma-bhanga return False, never KeyError."""
    assert bhangas.kemadruma(_sparse({"Sun": 5.0, "Jupiter": 20.0})) is False
    assert bhangas.kemadruma_bhanga(_sparse({"Sun": 5.0})) is False


def test_neecha_bhanga_no_crash_when_moon_and_dispositor_absent():
    """Sun debilitated in Libra with no Moon/Venus present -> evaluates, no crash."""
    result = bhangas.neecha_bhanga("Sun", _sparse({"Sun": 190.0}))
    assert isinstance(result, bool)


def test_maraka_points_falls_back_to_lagna_when_moon_absent():
    """64th-navamsa is reckoned from the Moon; absent Moon -> falls back to the
    Lagna without raising, and both death-point lords are valid sign-lords."""
    mp = maraka.maraka_points(_sparse({"Sun": 5.0}))
    assert mp.navamsa64_lord in SIGN_LORDS.values()
    assert mp.drekkana22_lord in SIGN_LORDS.values()


def test_balarishta_inert_when_moon_absent():
    """No Moon -> the gate cannot apply (Raman's yogas are all Moon-anchored)."""
    st = balarishta.balarishta(_sparse({"Sun": 5.0, "Jupiter": 20.0}))
    assert st.applies is False and st.cancelled is False and st.reasons == ()
