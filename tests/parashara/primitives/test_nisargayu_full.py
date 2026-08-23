"""Nisargayu's Ascendant contribution + the complete span — BPHS ch.43 sl.411-431.

The load-bearing test is Parashara's OWN worked nativity: with the navamsa-lagna lord stronger,
Navamsa Lagna Cancer and ascendant 0-48-34 give 3.2428 years. Also pins the rasi-case rule, the
strength fork, and that the complete span = post-harana planetary + ascendant.
"""
from __future__ import annotations

import pytest

from app.parashara.chart.cast import cast
from app.parashara.primitives.longevity import (
    ASCENDANT_SOURCE,
    _ascendant_years_navamsa,
    _ascendant_years_rasi,
    ascendant_contribution,
    nisargayu_after_haranas,
    nisargayu_full,
)
from app.parashara.doctrine.sources import verify


class TestWorkedExample:
    def test_navamsa_case_matches_parashara(self):
        # BPHS-43: Navamsa Lagna Cancer (4), ascendant 0deg 48' 34" -> 3.2428 years
        deg = 0 + 48 / 60.0 + 34 / 3600.0
        assert _ascendant_years_navamsa(4, deg) == pytest.approx(3.2428, abs=1e-4)

    def test_rasi_case_signs_before_ascendant(self):
        # Sagittarius (9) ascendant at 0 deg -> 8 years (Aries..Scorpio)
        assert _ascendant_years_rasi(9, 0.0) == 8.0
        assert _ascendant_years_rasi(9, 15.0) == pytest.approx(8.5)


class TestFullSpan:
    def _chart(self):
        return cast(year=1990, month=7, day=15, hour=12, minute=0,
                    tz_offset=5.5, latitude=12.97, longitude=77.59)

    def test_total_is_planetary_plus_ascendant(self):
        nf = nisargayu_full(self._chart())
        assert nf.total_years == pytest.approx(nf.planetary_years + nf.ascendant_years)

    def test_planetary_matches_the_harana_span(self):
        ch = self._chart()
        assert nisargayu_full(ch).planetary_years == pytest.approx(
            nisargayu_after_haranas(ch).planetary_years)

    def test_method_is_one_of_the_two_forks(self):
        assert nisargayu_full(self._chart()).ascendant_method in ("rasi", "navamsa")

    def test_ascendant_years_positive_and_bounded(self):
        nf = nisargayu_full(self._chart())
        assert 0.0 <= nf.ascendant_years <= 12.0    # at most ~12 sign-years

    def test_contribution_matches_full(self):
        ch = self._chart()
        yrs, method = ascendant_contribution(ch)
        nf = nisargayu_full(ch)
        assert yrs == pytest.approx(nf.ascendant_years) and method == nf.ascendant_method


class TestCitation:
    def test_source_resolves(self):
        assert verify(ASCENDANT_SOURCE) and ASCENDANT_SOURCE.work == "BPHS-43"
