"""ASP-15 transit-band elections over the canonical chart's own BAV tables."""
from __future__ import annotations

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.electional.asp_transit_elections import transit_election
from app.raman_saab.primitives.ashtakavarga import bhinnashtakavarga


@pytest.fixture(scope="module")
def chart():
    return cast_chart(BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59),
                      ayanamsa="raman")


class TestTransitElection:
    def test_sun_band_edges_follow_asp_15(self, chart):
        """ASP-15:21-30: 5-8 auspicious, 4 mixed, 1-3 poor, 0 absolutely forbidden — every
        sign's verdict must match its own BAV bindu band."""
        bav = bhinnashtakavarga(chart, "Sun")
        for sign in range(1, 13):
            te = transit_election(chart, "Sun", sign)
            b = bav[sign]
            expected = ("forbidden" if b == 0 else "poor" if b <= 3 else
                        "mixed" if b == 4 else "auspicious")
            assert te.verdict == expected, sign

    def test_moon_six_plus_is_auspicious_for_marriage(self, chart):
        """ASP-15:55-62: Moon 6-8 auspicious; 1-3 fruitless."""
        bav = bhinnashtakavarga(chart, "Moon")
        for sign in range(1, 13):
            te = transit_election(chart, "Moon", sign)
            if bav[sign] >= 6:
                assert te.verdict == "auspicious" and "marriage" in te.activities
            elif bav[sign] <= 3:
                assert te.verdict == "poor"

    def test_jupiter_max_bindu_sign_is_the_auspicious_one(self, chart):
        """ASP-15:116-128: Jupiter transiting his own max-bindu sign."""
        bav = bhinnashtakavarga(chart, "Jupiter")
        best = max(bav, key=bav.get)
        te = transit_election(chart, "Jupiter", best)
        assert te.verdict == "auspicious" and "veda_study" in te.activities

    def test_rahu_has_no_asp_15_rule(self, chart):
        """ASP-15 states band rules for the seven grahas only; the module returns None
        rather than inventing one."""
        assert transit_election(chart, "Rahu", 1) is None
