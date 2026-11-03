"""Vimshottari periods from the KP Moon."""

from __future__ import annotations

import pytest

from app.kp.chart import cast
from app.kp.dasa import DAYS_PER_VEDIC_YEAR, mahadashas, periods_on, subdivide
from tests.kp.test_chart import NATIVE_1922


@pytest.fixture(scope="module")
def chart():
    return cast(NATIVE_1922)


class TestDasa:
    def test_moon_in_aswini_starts_ketu(self, chart) -> None:
        """Moon 12°03' Aries is in Aswini (Ketu), so the first dasa is Ketu."""
        assert mahadashas(chart)[0].lords == ("Ketu",)

    def test_balance_is_unelapsed_fraction(self, chart) -> None:
        """Balance = (13°20' - 12°03')/13°20' x 7 years."""
        md = mahadashas(chart)[0]
        frac = (40 / 3 - chart.planets["Moon"].longitude) / (40 / 3)
        assert abs((md.end_jd - chart.jd_ut) / DAYS_PER_VEDIC_YEAR - 7 * frac) < 1e-6

    def test_cycle_is_120_years(self, chart) -> None:
        """Nine dasas sum to 120 years."""
        md = mahadashas(chart)[:9]
        assert abs((md[-1].end_jd - md[0].start_jd) / DAYS_PER_VEDIC_YEAR - 120) < 1e-6

    def test_subperiods_tile_parent(self, chart) -> None:
        """Bhuktis start with the dasa lord and exactly fill the dasa."""
        md = mahadashas(chart)[2]
        sub = subdivide(md)
        assert sub[0].lords == (md.lords[0], md.lords[0])
        assert abs(sub[0].start_jd - md.start_jd) < 1e-9 and abs(sub[-1].end_jd - md.end_jd) < 1e-6

    def test_periods_on_returns_four_levels(self, chart) -> None:
        """A date inside the life yields dasa, bhukti, antara and sookshma."""
        chain = periods_on(chart, chart.jd_ut + 40 * DAYS_PER_VEDIC_YEAR)
        assert [p.level for p in chain] == ["dasa", "bhukti", "antara", "sookshma"]
