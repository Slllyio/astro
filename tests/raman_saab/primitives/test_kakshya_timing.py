"""Kakshya time-division of Dasa periods — `primitives/kakshya_timing.py` (ASP-12).

The fixture is again the Standard Horoscope (Raman's printed 1918 longitudes, Track-B), whose
Jupiter-Dasa working the chapter prints in full: Saturn's first interval runs ADVERSE ("Saturn
has not contributed a bindu to the sign occupied by Jupiter. Hence the first two years ...
should be adverse", ASP-12:211-214) but is NEUTRALISED ("Saturn['s] two Rasis ... have 5 and 4
bindus respectively so that the evil ... gets neutralised", ASP-12:215-219). Both halves of
that judgment are pinned, plus the natal-Kakshya device on the same chart (ASP-12:151:
Jupiter in the Moon's Kakshya, Moon donated).
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives.ashtakavarga import bhinnashtakavarga
from app.raman_saab.primitives.kakshya import KAKSHYA_ORDER
from app.raman_saab.primitives.kakshya_timing import (
    dasa_lord_natal_kakshya,
    kakshya_intervals,
)

_STANDARD = {
    "Sun": 179 + 8 / 60, "Moon": 311 + 40 / 60, "Mars": 229 + 49 / 60,
    "Mercury": 180 + 33 / 60, "Jupiter": 83 + 35 / 60, "Venus": 170 + 4 / 60,
    "Saturn": 124 + 51 / 60, "Rahu": 53 + 23 / 60, "Ketu": 233 + 23 / 60,
}


@pytest.fixture(scope="module")
def standard() -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": lon, "bhava": 1} for p, lon in _STANDARD.items()},
        asc_lon=185.0, ayanamsa="raman")


class TestDasaLordNatalKakshya:
    def test_jupiter_sits_in_the_moons_kakshya_with_a_bindu(self, standard):
        """ASP-12:151 — 'Jupiter is in 23°35' of Gemini occupying the Kakshya of the Moon and
        the Moon has contributed a bindu.'"""
        r = dasa_lord_natal_kakshya(standard, "Jupiter")
        assert r is not None
        assert r.kakshya_lord == "Moon" and r.favourable

    def test_nodes_are_undecidable_not_adverse(self, standard):
        assert dasa_lord_natal_kakshya(standard, "Rahu") is None


class TestJupiterDasaIntervals:
    """Raman's own working of the 1930-1946 Jupiter Dasa (ASP-12:186-219)."""

    @pytest.fixture(scope="class")
    def intervals(self, standard):
        return kakshya_intervals(standard, "Jupiter", 0.0, 16.0)

    def test_eight_equal_intervals_in_kakshya_order(self, intervals):
        """'divided into 8 equal parts ... ruled by Saturn, Jupiter, Mars, Sun, Venus,
        Mercury, Moon and the Lagna' (ASP-12:174-182)."""
        assert tuple(iv.ruler for iv in intervals) == KAKSHYA_ORDER
        assert all(iv.end_jd - iv.start_jd == pytest.approx(2.0) for iv in intervals)
        assert intervals[0].start_jd == 0.0 and intervals[-1].end_jd == 16.0

    def test_saturns_interval_is_adverse_but_neutralised(self, standard, intervals):
        """The chapter's own double judgment: Saturn did NOT donate to Gemini (adverse,
        ASP-12:211-214) yet his two signs hold 5 and 4 bindus in Jupiter's Ashtakavarga
        (neutralised, ASP-12:215-219). Both the raw call and the relief must reproduce —
        and the stated 5/4 counts are themselves asserted against our tables."""
        sat = intervals[0]
        assert sat.ruler == "Saturn"
        assert not sat.donated
        bav = bhinnashtakavarga(standard, "Jupiter")
        assert sorted((bav[10], bav[11]), reverse=True) == [5, 4]     # Capricorn, Aquarius
        assert sat.neutralised
        assert not sat.adverse_unrelieved

    def test_a_donating_interval_is_favourable(self, standard, intervals):
        """Every ruler that donated to Gemini in Jupiter's own Ashtakavarga must read
        favourable — the Moon is guaranteed by the natal-Kakshya fixture above."""
        by = {iv.ruler: iv for iv in intervals}
        assert by["Moon"].donated and by["Moon"].favourable

    def test_the_lagna_interval_is_never_neutralised(self, intervals):
        """The Lagna owns no signs, so an undonated Lagna interval has no relief path."""
        lagna = intervals[-1]
        assert lagna.ruler == "Lagna"
        if not lagna.donated:
            assert not lagna.neutralised

    def test_nodes_yield_no_intervals(self, standard):
        """The scheme is undefined for a lord with no Ashtakavarga — () not a guess."""
        assert kakshya_intervals(standard, "Ketu", 0.0, 16.0) == ()
