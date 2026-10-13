"""Phase 4.3 matching: scoring and tie-splitting are exact, and decoys stay within the registered window."""
from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import swisseph as swe

from tools.validation.blind_matching import decoy_jobs, score, tie_split_hit


class TestMatching:
    def test_score_counts_matches_minus_mismatches(self):
        """+1 for a matching pole, -1 for the opposite, 0 for mixed."""
        chart = {7: "afflicted", 5: "favourable", 9: "mixed"}
        assert score(chart, [(7, "afflicted"), (5, "afflicted"), (9, "afflicted")]) == 0
        assert score(chart, [(7, "afflicted"), (5, "favourable")]) == 2

    def test_tie_split(self):
        """A 3-way tie at the top gives 1/3 of a hit; the chance hit rate over random ties is 1/5."""
        assert tie_split_hit(2, [2, 2, 0, 0]) == (1 / 3, 2.0)
        assert tie_split_hit(0, [1, 0, 0, 0])[0] == 0.0
        assert tie_split_hit(0, [0, 0, 0, 0]) == (0.2, 3.0)

    def test_same_day_decoys_within_three_days(self):
        """Regime-S decoys fall within +/-3 days of the true birth date, at the same place."""
        row = SimpleNamespace(person_id="x", birth_date="2000-03-01", birth_time="10:30",
                              tz_offset=5.5, latitude=12.9, longitude=77.6)
        jobs = decoy_jobs(row, np.random.default_rng(0))
        jd0 = swe.julday(2000, 3, 1, 12.0)
        for j in jobs[1:6]:
            assert abs(swe.julday(j[2], j[3], j[4], 12.0) - jd0) <= 3
            assert j[6:] == (5.5, 12.9, 77.6)
        assert all(j[2] == 2000 for j in jobs[6:])
