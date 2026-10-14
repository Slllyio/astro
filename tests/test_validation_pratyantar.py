"""Phase 3P: pratyantar periods are the engine's own, and the exposure flags read them correctly."""
from __future__ import annotations

import swisseph as swe

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.primitives import vimshottari as vd
from tools.validation.pratyantar_timing import pd_periods, worker

ROW = dict(person_id="x", birth_date="1990-07-15", birth_time="12:00", tz_offset=5.5,
           latitude=12.97, longitude=77.59)   # canonical Bangalore baseline
BJD = swe.julday(1990, 7, 15, 12.0, swe.GREG_CAL)


class TestPratyantar:
    def test_running_pd_matches_engine_pratyantar_on(self):
        """At age 30 the period found here is the engine's pratyantar_on() period."""
        ch = cast_chart(BirthData(name="x", year=1990, month=7, day=15, hour=12, minute=0, tz_offset=5.5,
                                  latitude=12.97, longitude=77.59))
        pds = pd_periods(ch, BJD, 0.0)
        age = 30.0
        mine = next(p for p in pds if p[0] <= age < p[1])
        eng = vd.pratyantar_on(ch, BJD + age * 365.2425)
        assert (mine[2], mine[3], mine[4]) == (eng.maha, eng.antar, eng.pratyantar)

    def test_triple_implies_pd_and_levels_consistent(self):
        """Triple convergence implies the PD lord activates, and the level count equals 3 then."""
        pid, res = worker((ROW, [(a / 2, "7") for a in range(20, 160)], ["7", "maraka"], "raman"))
        for v in res["real"]["q"].values():
            pd_act, tri, n = v
            assert (not tri) or (pd_act and n == 3)
        a, b = res["real"]["life"]["7"]
        assert 0.0 <= b <= a <= 1.0
