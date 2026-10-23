"""Phase 3J: the store's chara periods are the Parashara engine's own, and the exposure reads them correctly."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.parashara.chart.cast import cast
from app.parashara.primitives import chara_dasha as cd
from tools.validation import riskset_timing as rt
from tools.validation.jaimini_timing import death_keys, exposure_rows, house_sign, process
from tools.validation.yogini_timing import life_share

ROW = dict(person_id="x", birth_date="1990-07-15", birth_time="12:00", tz_offset=5.5,
           latitude=12.97, longitude=77.59)   # canonical Bangalore baseline


@pytest.fixture(scope="module")
def chart():
    return cast(year=1990, month=7, day=15, hour=12, minute=0, tz_offset=5.5, latitude=12.97, longitude=77.59)


class TestChara:
    def test_store_periods_equal_engine_timeline(self, chart):
        """Period boundaries in the store are exactly `chara_dasha.timeline` from the real Lagna."""
        sg = cd.chart_signs(chart)
        s, e, t, _ = exposure_rows(chart.asc_sign, sg, chart.asc_sign, (chart.asc_sign,))
        tl = cd.timeline(chart.asc_sign, sg, horizon=100.0)
        assert np.allclose(s, [p.start_year for p in tl]) and np.allclose(e, [p.end_year for p in tl])
        for row, p in zip(t, tl):        # exactly one house is the dasa sign from the Lagna
            assert row[:12].sum() == 1 and house_sign(chart.asc_sign, int(row[:12].argmax()) + 1) == p.sign

    def test_placebo_is_the_sequence_seeded_one_sign_ahead(self, chart):
        """Placebo periods are the engine's timeline from Lagna + 1, judged against the real Lagna."""
        _, res = process(ROW)
        sg = cd.chart_signs(chart)
        tl = cd.timeline(chart.asc_sign % 12 + 1, sg, horizon=100.0)
        assert np.allclose(res["placebo"][0], [p.start_year for p in tl])
        assert np.array_equal(res["real"][2], exposure_rows(chart.asc_sign, sg, chart.asc_sign, (chart.asc_sign,))[2])

    def test_wider_activation_contains_the_lagna_rule(self):
        """The Lagna/AK/Karakamsa arm is a superset of the Lagna-only exposure."""
        _, res = process(ROW)
        assert (res["lagna_ak_karakamsa"][2] >= res["real"][2]).all()

    def test_life_share_matches_a_grid(self):
        """The lifetime share is the exposed time-share over ages 15-75."""
        _, res = process(ROW)
        st = rt.Store.__new__(rt.Store)
        st.data = {"x": res}
        for houses in ((7,), (2, 11)):
            share = life_share(st, "x", houses, "MD", "real")
            grid = np.linspace(15, 75, 3001)[:-1]
            approx = np.mean([rt.exposed(st.tier("x", g, houses), "MD") for g in grid])
            assert share == pytest.approx(approx, abs=0.01)

    def test_death_events_are_keyed_for_exclusion(self):
        """Own and relatives' deaths are excluded; other events are kept."""
        ev = pd.DataFrame({"person_id": ["a", "a", "b"], "event_jd": [1.0, 2.0, 3.0],
                           "houses": [rt.MARAKA, (9,), (7,)],
                           "event_root": ["Death", "Death of Father", "Relationship"]})
        assert death_keys(ev) == {("a", 1.0, "maraka"), ("a", 2.0, "(9,)")}
