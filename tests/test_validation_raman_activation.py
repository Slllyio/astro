"""Phase 3R store: it reproduces the Raman engine's own activation grading, period by period."""
from __future__ import annotations

import swisseph as swe

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.primitives import vimshottari as vd
from tools.validation.raman_activation_store import NAK, periods, timeline

BIRTH = BirthData(name="x", year=1990, month=7, day=15, hour=12, minute=0, tz_offset=5.5,
                  latitude=12.97, longitude=77.59)   # canonical Bangalore baseline
BJD = swe.julday(1990, 7, 15, 12.0, swe.GREG_CAL)


class TestRamanActivationStore:
    def test_unshifted_timeline_is_the_engines(self):
        """Shift 0 returns the engine's own mahadasha_timeline unchanged."""
        ch = cast_chart(BIRTH)
        assert [(p.maha, p.start_jd) for p in timeline(ch)] == [(p.maha, p.start_jd) for p in vd.mahadasha_timeline(ch)]

    def test_placebo_rebuild_matches_engine_at_zero_shift(self):
        """The placebo construction itself, run with a 360-degree shift, reproduces the engine timeline."""
        ch = cast_chart(BIRTH)
        eng = vd.mahadasha_timeline(ch)
        reb = timeline(ch, moon_shift=360.0)
        assert [p.maha for p in reb] == [p.maha for p in eng]
        assert all(abs(a.start_jd - b.start_jd) < 1e-6 for a, b in zip(reb, eng))

    def test_placebo_starts_one_lord_later(self):
        """One nakshatra ahead -> the birth MD is the next Vimshottari lord."""
        ch = cast_chart(BIRTH)
        seq = list(vd._sequence_from(vd.mahadasha_timeline(ch)[0].maha))
        assert timeline(ch, moon_shift=NAK)[0].maha == seq[1]

    def test_tiers_equal_engine_active_houses(self):
        """On a running period, houses graded >=3 here are exactly active_houses' par_excellence set."""
        ch = cast_chart(BIRTH)
        jd = BJD + 30 * 365.2425
        age = 30.0
        row = next(p for p in periods(ch, BJD, "primary") if p[2] <= age < p[3])
        both = {h for h in range(1, 13) if row[3 + h] >= 3}
        eng = {a.house for a in vd.active_houses(ch, jd) if a.grade == "par_excellence"}
        assert both == eng
