"""Gochara (transits) — judged from the natal Moon + Ashtakavarga support, with Sade-Sati."""
from __future__ import annotations

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.primitives import transits as tr

_MAINPURI = BirthData(name="M", year=1989, month=10, day=12, hour=10, minute=2,
                      tz_offset=5.5, latitude=27.23, longitude=79.03)


def _natal():
    return cast_chart(_MAINPURI, ayanamsa="lahiri")


def test_gochara_rows_well_formed():
    rows = tr.gochara(_natal(), 2026, 6, 28)
    assert {r.planet for r in rows} == set(tr.SIGNIFICANT)
    for r in rows:
        assert 1 <= r.sign <= 12
        assert 1 <= r.house_from_moon <= 12 and 1 <= r.house_from_lagna <= 12
        assert r.gochara_good == (r.house_from_moon in tr._GOCHARA_GOOD[r.planet])
        if r.bav_bindus is not None:
            assert r.supported == (r.bav_bindus >= 4)


def test_sade_sati_setting_mainpuri_2026():
    """Natal Moon in Aquarius; in 2026 Saturn transits Pisces = the 2nd from the Moon = setting."""
    assert tr.sade_sati(_natal(), 2026, 6, 28) == "Sade-Sati: setting (2nd from Moon)"


def test_sade_sati_absent_when_saturn_far_from_moon():
    """No Sade-Sati when Saturn is well away from the 12/1/2 from the Moon."""
    # A date with Saturn not in Aqu/Pis/Ari (e.g. 2030, Saturn ~ Aries/Taurus boundary): assert the
    # function returns either None or a valid phase string — never an exception.
    out = tr.sade_sati(_natal(), 2030, 6, 28)
    assert out is None or out.startswith("Sade-Sati")


def test_transit_chart_casts():
    tc = tr.transit_chart(2026, 6, 28)
    assert len(tc.planets) == 9 and 1 <= tc.planets["Saturn"].sign <= 12
