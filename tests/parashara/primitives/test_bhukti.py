"""Antardasha (bhukti) subdivision (BPHS-46:110) — proportional sub-periods within a mahadasha.

Pinned to the definitional arithmetic: bhuktis run in cycle order from the mahadasha lord, each
= antardasha_years * mahadasha_years / total, and they sum to exactly the mahadasha's length.
"""
from __future__ import annotations

import pytest

from app.parashara.primitives.nakshatra_dasha import bhukti_timeline, pratyantar_timeline
from app.parashara.primitives.vimshottari_dasha import CYCLE, seed


class TestBhukti:
    def test_bhuktis_total_the_mahadasha_length(self):
        for idx in range(len(CYCLE)):
            md_years = CYCLE[idx][1]
            b = bhukti_timeline(CYCLE, idx)
            assert sum(p.years for p in b) == pytest.approx(md_years)
            assert len(b) == len(CYCLE)

    def test_first_bhukti_is_the_mahadasha_lord(self):
        idx = seed(27).index                      # Mercury (canonical Revati)
        b = bhukti_timeline(CYCLE, idx)
        assert b[0].lord == "Mercury"

    def test_known_vimshottari_bhukti_values(self):
        idx = seed(27).index                      # Mercury MD (17 yrs)
        b = {p.lord: p.years for p in bhukti_timeline(CYCLE, idx)}
        assert b["Mercury"] == pytest.approx(17 * 17 / 120)   # 2.408
        assert b["Venus"] == pytest.approx(20 * 17 / 120)     # 2.833
        assert b["Sun"] == pytest.approx(6 * 17 / 120)        # 0.850

    def test_start_year_offset_is_absolute(self):
        b = bhukti_timeline(CYCLE, seed(27).index, mahadasha_start_year=40.0)
        assert b[0].start_year == 40.0
        assert b[-1].end_year == pytest.approx(40.0 + 17.0)

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError):
            bhukti_timeline(CYCLE, 99)


class TestPratyantar:
    def test_pratyantars_total_the_bhukti_length(self):
        idx = seed(27).index                       # Mercury MD
        for bi in range(len(CYCLE)):
            bhukti = bhukti_timeline(CYCLE, idx)[bi]
            pr = pratyantar_timeline(CYCLE, idx, bi)
            assert sum(p.years for p in pr) == pytest.approx(bhukti.years)
            assert pr[0].lord == bhukti.lord        # first pratyantar = the bhukti lord's own

    def test_known_triple_value(self):
        idx = seed(27).index                       # Mercury MD, Mercury bhukti (index 0)
        pr = {p.lord: p.years for p in pratyantar_timeline(CYCLE, idx, 0)}
        assert pr["Mercury"] == pytest.approx(17 * 17 * 17 / 120 / 120)   # Merc-Merc-Merc

    def test_start_year_is_absolute(self):
        pr = pratyantar_timeline(CYCLE, seed(27).index, 0, bhukti_start_year=40.0)
        assert pr[0].start_year == 40.0
