"""Pratyantardasha (sub-sub-period) tests — ``vimshottari.pratyantars`` / ``pratyantar_on``.

The proportional split mirrors ``bhuktis()`` one level down (HPA ch.24's self-similar
Dasa/Bhukti/Antara hierarchy; HTJAH-II:668-702 names all three levels as carriers of a
house's results). The rect_case_01 pins are EXTERNAL truth: the (MD, AD, PD) chains were
hand-computed during the 2026-07-18 rectification session for the anonymized nativity
1989-10-12 10:02 IST @ (27.23 N, 79.03 E) and are pinned here against engine drift.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.primitives import vimshottari as vim

_BIRTH = BirthData(name="rect_case_01", year=1989, month=10, day=12, hour=10, minute=2,
                   tz_offset=5.5, latitude=27.23, longitude=79.03)
_MARRIAGE_JD = vim.date_to_jd(2017, 12, 4)


def _year(jd: float) -> float:
    """JD -> fractional Gregorian year (J2000 anchor), for readable interval pins."""
    return 2000.0 + (jd - 2451545.0) / 365.25


@pytest.fixture(scope="module")
def charts() -> dict[str, object]:
    return {ay: cast_chart(_BIRTH, ayanamsa=ay) for ay in ("lahiri", "raman")}


class TestPratyantarsStructure:
    def test_nine_pratyantars_partition_the_bhukti(self, charts) -> None:
        """A Bhukti splits into exactly 9 contiguous PDs whose union is the Bhukti span."""
        bh = vim.dasha_on(charts["lahiri"], _MARRIAGE_JD)
        pds = vim.pratyantars(bh)
        assert len(pds) == 9
        assert abs(pds[0].start_jd - bh.start_jd) < 1e-9
        assert abs(pds[-1].end_jd - bh.end_jd) < 1e-6
        for a, b in zip(pds, pds[1:]):
            assert abs(a.end_jd - b.start_jd) < 1e-9

    def test_first_pratyantar_lord_is_the_bhukti_lord(self, charts) -> None:
        """The PD sequence opens with the Bhukti lord itself (Vimshottari self-similarity)."""
        bh = vim.dasha_on(charts["raman"], _MARRIAGE_JD)
        pds = vim.pratyantars(bh)
        assert pds[0].pratyantar == bh.antar
        assert all(pd.maha == bh.maha and pd.antar == bh.antar for pd in pds)

    def test_md_level_span_is_rejected(self, charts) -> None:
        """pratyantars() requires a Bhukti-level span; an MD-level span raises ValueError."""
        md = vim.mahadasha_timeline(charts["lahiri"])[0]
        with pytest.raises(ValueError):
            vim.pratyantars(md)

    def test_dasha_on_is_unchanged_bhukti_level(self, charts) -> None:
        """dasha_on still resolves to Bhukti depth only (pratyantar=None) — zero-regression."""
        bh = vim.dasha_on(charts["lahiri"], _MARRIAGE_JD)
        assert bh.pratyantar is None


class TestRectCase01Pins:
    def test_lahiri_marriage_chain_is_saturn_venus_saturn(self, charts) -> None:
        """Under Lahiri the 2017-12-04 marriage runs in Sa/Venus/Saturn, PD ~2017.81-2018.31."""
        pd = vim.pratyantar_on(charts["lahiri"], _MARRIAGE_JD)
        assert (pd.maha, pd.antar, pd.pratyantar) == ("Saturn", "Venus", "Saturn")
        assert _year(pd.start_jd) == pytest.approx(2017.811, abs=0.01)
        assert _year(pd.end_jd) == pytest.approx(2018.312, abs=0.01)

    def test_raman_marriage_chain_is_saturn_sun_venus(self, charts) -> None:
        """Under raman ayanamsa the same date runs in Sa/Sun/Venus, PD ~2017.78-2017.94."""
        pd = vim.pratyantar_on(charts["raman"], _MARRIAGE_JD)
        assert (pd.maha, pd.antar, pd.pratyantar) == ("Saturn", "Sun", "Venus")
        assert _year(pd.start_jd) == pytest.approx(2017.784, abs=0.01)
        assert _year(pd.end_jd) == pytest.approx(2017.943, abs=0.01)
