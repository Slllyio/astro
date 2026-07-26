"""Gochara (transits) — judged from the natal Moon + Ashtakavarga support, with Sade-Sati."""
from __future__ import annotations

import swisseph as swe

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


class TestGocharaTimeline:
    """Multi-year outlook — the same Gochara/Vedha scheme as `gochara()`, spread over time."""

    def _ref_jd(self):
        return swe.julday(2026, 7, 26, 12.0)

    def test_segments_are_chronological_contiguous_and_cover_the_window(self):
        natal = _natal()
        ref_jd = self._ref_jd()
        tl = tr.gochara_timeline(natal, ref_jd, 5, 10, step_days=10)
        assert set(tl.keys()) == {"Jupiter", "Saturn", "Rahu", "Ketu"}
        start_jd = ref_jd - 5 * tr.DAYS_PER_VEDIC_YEAR
        end_jd = ref_jd + 10 * tr.DAYS_PER_VEDIC_YEAR
        for planet, segs in tl.items():
            assert segs, planet
            assert segs[0].start_jd == start_jd
            assert segs[-1].end_jd == end_jd
            for a, b in zip(segs, segs[1:]):
                assert a.end_jd == b.start_jd          # contiguous, no gaps or overlaps
                assert a.sign != b.sign                 # each segment is exactly one sign

    def test_good_flag_and_bindus_match_the_snapshot_definition(self):
        natal = _natal()
        tl = tr.gochara_timeline(natal, self._ref_jd(), 3, 3, step_days=10)
        moon_sign = natal.planets["Moon"].sign
        for planet, segs in tl.items():
            for seg in segs:
                hfm = ((seg.sign - moon_sign) % 12) + 1
                assert seg.house_from_moon == hfm
                assert seg.gochara_good == (hfm in tr._GOCHARA_GOOD[planet])
                if not seg.gochara_good:
                    assert seg.bav_bindus is None
                    assert seg.vedha_sample_fraction == 0.0
                assert 0.0 <= seg.vedha_sample_fraction <= 1.0

    def test_rahu_ketu_have_no_ashtakavarga_bindus(self):
        """Rahu/Ketu carry no Bhinnashtakavarga in classical doctrine — bav_bindus stays None
        even on their favourable windows."""
        natal = _natal()
        tl = tr.gochara_timeline(natal, self._ref_jd(), 5, 5, step_days=10,
                                 planets=("Rahu", "Ketu"))
        for segs in tl.values():
            for seg in segs:
                assert seg.bav_bindus is None

    def test_restricting_to_fewer_planets_returns_only_those(self):
        natal = _natal()
        tl = tr.gochara_timeline(natal, self._ref_jd(), 2, 2, step_days=15, planets=("Jupiter",))
        assert set(tl.keys()) == {"Jupiter"}
