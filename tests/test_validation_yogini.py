"""Phase 3Y: the Yogini periods are the Parashara engine's own, and the exposure reads them correctly."""
from __future__ import annotations

import dataclasses
from itertools import groupby

import numpy as np
import pytest

from app.parashara.chart.cast import cast
from app.parashara.primitives import yogini_dasha as yog
from app.parashara.primitives.nakshatra_dasha import bhukti_timeline
from app.parashara.reading import _birth_balance, _dashas
from app.parashara.synthesis.chart_facts import house_sign, planet_signs
from app.parashara.primitives.relationships import SIGN_LORDS
from tools.validation import riskset_timing as rt
from tools.validation.activation_store import influence
from tools.validation.yogini_timing import life_share, process, tier_rows, yogini_ads

ROW = dict(person_id="x", birth_date="1990-07-15", birth_time="12:00", tz_offset=5.5,
           latitude=12.97, longitude=77.59)   # canonical Bangalore baseline


@pytest.fixture(scope="module")
def chart():
    return cast(year=1990, month=7, day=15, hour=12, minute=0, tz_offset=5.5, latitude=12.97, longitude=77.59)


def _mds(ads):
    """Collapse consecutive ADs into (MD lord, start, end, [ADs])."""
    out = []
    for _, g in groupby(enumerate(ads), key=lambda t: (t[1][0], _md_no(ads, t[0]))):
        g = [x for _, x in g]
        out.append((g[0][0], g[0][2], g[-1][3], g))
    return out


def _md_no(ads, i):
    """MD counter: increments whenever an AD's lord equals its MD lord (each MD opens with its own AD)."""
    return sum(1 for a in ads[: i + 1] if a[0] == a[1])


class TestYoginiPeriods:
    def test_first_cycle_equals_engine_reading(self, chart):
        """The first 8 MDs match the engine's own Yogini timeline in reading._dashas (lord and end age)."""
        eng = next(d for d in _dashas(chart) if d.system == "yogini").timeline
        mine = _mds(yogini_ads(chart, chart.janma_nakshatra))[:8]
        assert [m[0] for m in mine] == [p.lord for p in eng]
        assert np.allclose([m[2] for m in mine], [p.end_year for p in eng])
        assert np.allclose([m[1] for m in mine[1:]], [p.start_year for p in eng[1:]])

    def test_antardashas_are_engine_bhuktis_anchored_at_true_md_start(self, chart):
        """Birth MD's ADs = bhukti_timeline from (-elapsed x years); later MDs' ADs = bhukti_timeline exactly."""
        el = _birth_balance(chart)
        idx = {lord: i for i, (lord, _) in enumerate(yog.CYCLE)}
        mds = _mds(yogini_ads(chart, chart.janma_nakshatra))
        first_lord, years = mds[0][0], yog.CYCLE[idx[mds[0][0]]][1]
        full = [b for b in bhukti_timeline(yog.CYCLE, idx[first_lord], mahadasha_start_year=-el * years)
                if b.end_year > 0]
        assert [(a[1], a[3]) for a in mds[0][3]] == pytest.approx([(b.lord, b.end_year) for b in full])
        lord, start, _, ads = mds[3]
        ref = bhukti_timeline(yog.CYCLE, idx[lord], mahadasha_start_year=start)
        assert [a[1] for a in ads] == [b.lord for b in ref]
        assert np.allclose([a[3] for a in ads], [b.end_year for b in ref])

    def test_contiguous_and_cycle_repeats_to_horizon(self, chart):
        """Periods tile 0..>=95 with no gap; MD i+8 has MD i's lord and full length (the 36-year cycle repeats)."""
        ads = yogini_ads(chart, chart.janma_nakshatra)
        assert ads[0][2] == 0.0 and ads[-1][3] >= 95
        assert all(abs(a[3] - b[2]) < 1e-9 for a, b in zip(ads, ads[1:]))
        mds = _mds(ads)
        yrs = dict(yog.CYCLE)
        for i in range(1, len(mds) - 9):
            assert mds[i + 8][0] == mds[i][0]
            assert mds[i + 8][2] - mds[i + 8][1] == pytest.approx(yrs[mds[i][0]])

    def test_mrigasira_worked_example_starts_with_sankata_rahu(self, chart):
        """BPHS-46:199: Mrigasira (5) + 3 = 8, remainder 0 -> the 8th Yogini, Sankata, ruled by Rahu."""
        assert (yog.seed(5).yogini, yog.seed(5).lord) == ("Sankata", "Rahu")
        mriga = dataclasses.replace(chart, janma_nakshatra=5)
        assert yogini_ads(mriga, 5)[0][0] == "Rahu"     # MD at birth (its own AD may already be spent)

    def test_placebo_is_seeded_one_nakshatra_ahead(self, chart):
        """The placebo sequence is the engine's Yogini for janma nakshatra + 1, on the same chart."""
        _, res = process(ROW)
        nak = chart.janma_nakshatra
        assert np.array_equal(res["real"][2], tier_rows(chart, nak)[2])
        assert np.array_equal(res["placebo"][2], tier_rows(chart, nak % 27 + 1)[2])
        assert yogini_ads(chart, nak % 27 + 1)[0][0] == yog.seed(nak % 27 + 1).lord


class TestRahuAndExposure:
    def test_rahu_influences_only_by_occupying_or_conjoining_the_lord(self, chart):
        """Rahu owns no sign and casts no drishti here, so it bears on H only by occupation or lord-conjunction."""
        signs = planet_signs(chart)
        for h in range(1, 13):
            hs = house_sign(chart.asc_sign, h)
            expect = signs["Rahu"] == hs or signs["Rahu"] == signs[SIGN_LORDS[hs]]
            assert influence("Rahu", h, chart, signs) == expect

    def test_life_share_is_exact_time_share(self, chart):
        """The lifetime share equals the exposure averaged over a fine age grid 15..75."""
        st = rt.Store.__new__(rt.Store)
        st.data = {"x": {"real": tier_rows(chart, chart.janma_nakshatra)}}
        for houses, level in (((7,), "AD"), ((2, 11), "MD"), (rt.MARAKA, "AD")):
            share = life_share(st, "x", houses, level, "real")
            grid = np.linspace(15, 75, 60001)[:-1]
            approx = np.mean([rt.exposed(st.tier("x", g, houses), level) for g in grid[::20]])
            assert 0.0 <= share <= 1.0
            assert share == pytest.approx(approx, abs=0.01)
