"""Candidate-generation tests — equivalence classes are real (invariant inside, distinct
across boundaries), bisection localises boundaries, and the Tier-L light chart agrees
with the full cast on every field the event-scoring path reads.
"""
from __future__ import annotations

import pytest
import swisseph as swe

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.primitives import vimshottari as vim
from app.raman_saab.rectification import candidates as C

_BIRTH_KW = dict(year=1989, month=10, day=12, latitude=27.23, longitude=79.03,
                 tz_offset=5.5)
_MARRIAGE_JD = vim.date_to_jd(2017, 12, 4)


@pytest.fixture(scope="module")
def cands() -> tuple[C.CandidateChart, ...]:
    return C.generate_candidates(
        **_BIRTH_KW, window_local_hours=(9.5, 10.5),
        ayanamsas=("raman", "lahiri"), event_jds=(_MARRIAGE_JD,))


class TestEquivalenceClasses:
    def test_probe_key_is_invariant_inside_a_class(self, cands) -> None:
        """Two instants strictly inside one class carry the identical feature key."""
        cand = max(cands, key=lambda c: c.birth_jd)  # any class; use its interior
        span = 20.0 / 86400.0
        a = C._probe(cand.birth_jd - span, 27.23, 79.03, cand.ayanamsa, (_MARRIAGE_JD,))
        b = C._probe(cand.birth_jd + span, 27.23, 79.03, cand.ayanamsa, (_MARRIAGE_JD,))
        # 40 s straddling the representative of a multi-minute class stays in-class.
        assert a.key == b.key == cand.class_id

    def test_adjacent_classes_differ_and_tile_the_window(self, cands) -> None:
        """Per ayanamsa: classes are contiguous over the window and adjacent ones differ."""
        for ay in ("raman", "lahiri"):
            row = sorted((c for c in cands if c.ayanamsa == ay), key=lambda c: c.birth_jd)
            assert row, f"no candidates for {ay}"
            for a, b in zip(row, row[1:]):
                assert a.interval_local[1] == b.interval_local[0]
                assert a.class_id != b.class_id
                assert b.boundaries  # every non-first class opens with a labelled boundary

    def test_ayanamsas_disagree_on_the_marriage_dasha_chain(self, cands) -> None:
        """The rect_case_01 discriminator: at ~10:02 the raman chain at the marriage date
        is Sa/Sun/... while lahiri's is Sa/Venus/... — captured in period_triples."""
        def at_1002(ay):
            return min((c for c in cands if c.ayanamsa == ay),
                       key=lambda c: abs(c.birth_jd - swe.julday(1989, 10, 12,
                                                                 10.0333 - 5.5,
                                                                 swe.GREG_CAL)))
        raman, lahiri = at_1002("raman"), at_1002("lahiri")
        assert raman.period_triples[0][:2] == ("Saturn", "Sun")
        assert lahiri.period_triples[0][:2] == ("Saturn", "Venus")

    def test_class_intervals_are_narrower_than_the_window(self, cands) -> None:
        """A 1-hour window with a marriage-date dasha registered splits into >1 class
        (the claimable resolution is the class interval, not the window)."""
        for ay in ("raman", "lahiri"):
            assert sum(1 for c in cands if c.ayanamsa == ay) > 1


class TestLightChartEquivalence:
    def test_light_chart_matches_full_cast_on_scoring_fields(self) -> None:
        """Tier-L agrees with cast_chart on every field event scoring reads: asc, planet
        longitudes/signs/rasi-houses, nakshatras, and the (MD, AD, PD) resolution."""
        birth = BirthData(name="x", year=1989, month=10, day=12, hour=10, minute=2,
                          tz_offset=5.5, latitude=27.23, longitude=79.03)
        full = cast_chart(birth, ayanamsa="raman")
        light = C.light_chart(full.jd_ut, 27.23, 79.03, "raman")
        assert light.asc_sign == full.asc_sign
        assert light.asc_lon == pytest.approx(full.asc_lon, abs=1e-9)
        for name, fp in full.planets.items():
            lp = light.planets[name]
            assert lp.lon == pytest.approx(fp.lon, abs=1e-9)
            assert (lp.sign, lp.rasi_house, lp.nakshatra) == (
                fp.sign, fp.rasi_house, fp.nakshatra)
        pd_l = vim.pratyantar_on(light, _MARRIAGE_JD)
        pd_f = vim.pratyantar_on(full, _MARRIAGE_JD)
        assert (pd_l.maha, pd_l.antar, pd_l.pratyantar) == (
            pd_f.maha, pd_f.antar, pd_f.pratyantar)

    def test_light_chart_has_no_shadbala(self) -> None:
        """The tier contract: Tier-L must be visibly strength-less so the fact-scorer
        guard can refuse it."""
        light = C.light_chart(swe.julday(1989, 10, 12, 4.5333, swe.GREG_CAL),
                              27.23, 79.03, "raman")
        assert all(p.shadbala_rupas is None for p in light.planets.values())


class TestChartCache:
    def test_cache_returns_same_object_per_tier(self, cands) -> None:
        """light()/full() memoise per (class_id, tier) — at most one cast per candidate."""
        cache = C.ChartCache()
        c0 = next(c for c in cands if c.ayanamsa == "raman")
        assert cache.light(c0) is cache.light(c0)
        full_a = cache.full(c0)
        assert full_a is cache.full(c0)
        assert full_a.planets["Sun"].shadbala_rupas is not None
