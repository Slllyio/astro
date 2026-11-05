"""Pratyantardasha (sub-sub-period) tests — ``vimshottari.pratyantars`` / ``pratyantar_on``.

The proportional split mirrors ``bhuktis()`` one level down (HPA ch.24's self-similar
Dasa/Bhukti/Antara hierarchy; HTJAH-II:668-702 names all three levels as carriers of a
house's results). The test chart is a neutral, made-up birth (no real person); the
personal rectification-session pins that used to live here were removed on 2026-11-05
together with event-based rectification.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.primitives import vimshottari as vim

_BIRTH = BirthData(name="neutral_test_chart", year=2000, month=1, day=1, hour=12, minute=0,
                   tz_offset=5.5, latitude=28.61, longitude=77.21)
_PROBE_JD = vim.date_to_jd(2025, 6, 15)


@pytest.fixture(scope="module")
def charts() -> dict[str, object]:
    return {ay: cast_chart(_BIRTH, ayanamsa=ay) for ay in ("lahiri", "raman")}


class TestPratyantarsStructure:
    def test_nine_pratyantars_partition_the_bhukti(self, charts) -> None:
        """A Bhukti splits into exactly 9 contiguous PDs whose union is the Bhukti span."""
        bh = vim.dasha_on(charts["lahiri"], _PROBE_JD)
        pds = vim.pratyantars(bh)
        assert len(pds) == 9
        assert abs(pds[0].start_jd - bh.start_jd) < 1e-9
        assert abs(pds[-1].end_jd - bh.end_jd) < 1e-6
        for a, b in zip(pds, pds[1:]):
            assert abs(a.end_jd - b.start_jd) < 1e-9

    def test_first_pratyantar_lord_is_the_bhukti_lord(self, charts) -> None:
        """The PD sequence opens with the Bhukti lord itself (Vimshottari self-similarity)."""
        bh = vim.dasha_on(charts["raman"], _PROBE_JD)
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
        bh = vim.dasha_on(charts["lahiri"], _PROBE_JD)
        assert bh.pratyantar is None
