"""Brahma Graha selection + Sthira end-to-end (BPHS ch.46 sl.170-173).

The integration Shadbala unlocks: the Sthira seed is chosen partly by strength, which the engine
now computes. These check the selection follows the priority order and that Sthira runs whole from
a cast chart.
"""
from __future__ import annotations

import pytest

from app.parashara.chart.brahma_graha import brahma_graha, sthira_for_chart
from app.parashara.chart.cast import cast


@pytest.fixture(scope="module")
def chart():
    return cast(year=1990, month=7, day=15, hour=12, minute=0,
                tz_offset=5.5, latitude=12.97, longitude=77.59)


class TestSelection:
    def test_returns_a_planet_and_its_sign(self, chart):
        bg = brahma_graha(chart)
        assert bg.planet in chart.longitudes
        assert 1 <= bg.sign <= 12
        assert bg.reason
        # the reported sign is the planet's actual sign
        assert int(chart.longitudes[bg.planet] % 360.0 // 30) + 1 == bg.sign

    def test_eighth_lord_in_eighth_takes_priority(self):
        """Rule 1: if the 8th lord occupies the 8th, it is the Brahma Graha, regardless of others."""
        from app.parashara.chart.cast import ParasharaChart
        from app.parashara.primitives.relationships import SIGN_LORDS
        from app.parashara.primitives.shadbala.kala import KalaContext
        asc = 1                              # Aries lagna -> 8th sign = Scorpio (8), lord Mars
        eighth_lord = SIGN_LORDS[8]          # Mars
        assert eighth_lord == "Mars"
        lons = {"Sun": 5.0, "Moon": 40.0, "Mars": 220.0,   # Mars in Scorpio (8th)
                "Mercury": 100.0, "Jupiter": 95.0, "Venus": 62.5, "Saturn": 250.0,
                "Rahu": 300.0, "Ketu": 120.0}
        kala = KalaContext(is_day=True, day_third=1, unnata_fraction=0.5,
                           weekday_lord="Sun", hora_lord="Sun",
                           varsha_lord="Sun", masa_lord="Sun")
        ch = ParasharaChart(longitudes=lons, asc_sign=asc, asc_longitude=5.0,
                            moon_waxing=True, janma_nakshatra=3,
                            speeds={p: 0.5 for p in lons}, ayanamsa=24.0, kala=kala, gulika=15.0)
        bg = brahma_graha(ch)
        assert bg.planet == "Mars" and "8th lord" in bg.reason

    def test_deterministic(self, chart):
        assert brahma_graha(chart) == brahma_graha(chart)


class TestSthiraEndToEnd:
    def test_sthira_runs_from_a_chart(self, chart):
        tl = sthira_for_chart(chart)
        assert len(tl) == 12                       # all twelve signs
        assert sum(p.years for p in tl) == 96      # Sthira total
        # starts on the Brahma Graha's sign
        assert tl[0].sign == brahma_graha(chart).sign

    def test_direction_matches_seed_parity(self, chart):
        bg = brahma_graha(chart)
        tl = sthira_for_chart(chart)
        second = tl[1].sign
        if bg.sign % 2 == 1:                        # odd -> forward
            assert second == bg.sign % 12 + 1
        else:                                       # even -> reverse
            assert second == (bg.sign - 2) % 12 + 1
