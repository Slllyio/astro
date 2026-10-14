"""Sthira dasha + the rasi-dasha framework (BPHS ch.46 sl.168-173).

Load-bearing: the cycle totals 96 (4x7+4x8+4x9), the modality spans are the sloka's, and the
odd-forward / even-reverse direction rule is Parashara's — checked against his own Yogardha example
('It is an odd sign. So the Dasas will start from Aquarius onwards.', BPHS-46:174).
"""
from __future__ import annotations

import pytest

from app.parashara.doctrine.sources import passage, verify
from app.parashara.primitives import rasi_dasha as rd
from app.parashara.primitives import sthira_dasha as st


class TestModality:
    def test_the_three_modalities(self):
        assert [rd.modality(s) for s in (1, 4, 7, 10)] == ["movable"] * 4
        assert [rd.modality(s) for s in (2, 5, 8, 11)] == ["fixed"] * 4
        assert [rd.modality(s) for s in (3, 6, 9, 12)] == ["dual"] * 4

    def test_bad_sign_rejected(self):
        with pytest.raises(ValueError):
            rd.modality(13)


class TestSpans:
    def test_modality_spans_are_the_sloka(self):
        """BPHS-46:168 — movable 7, fixed 8, dual 9."""
        assert st.MODALITY_SPAN == {"movable": 7, "fixed": 8, "dual": 9}
        assert st.span_for(1) == 7        # Aries, movable
        assert st.span_for(2) == 8        # Taurus, fixed
        assert st.span_for(3) == 9        # Gemini, dual

    def test_full_cycle_is_96_years(self):
        assert rd.total_years(st.span_for) == 96 == st.TOTAL_YEARS


class TestDirection:
    def test_odd_start_goes_forward(self):
        """Aquarius (11, odd) -> onwards, per Parashara's Yogardha example."""
        tl = st.sthira_timeline(11)
        assert [p.sign for p in tl][:3] == [11, 12, 1]     # Aqu -> Pis -> Ari

    def test_even_start_goes_reverse(self):
        """An even start sign traverses in reverse (BPHS-46:169)."""
        tl = st.sthira_timeline(4)                          # Cancer (even)
        assert [p.sign for p in tl][:3] == [4, 3, 2]        # Can -> Gem -> Tau

    def test_timeline_covers_all_twelve_signs_once(self):
        for start in (1, 4, 7, 11):
            signs = [p.sign for p in st.sthira_timeline(start)]
            assert sorted(signs) == list(range(1, 13)), start

    def test_timeline_totals_96_from_any_start(self):
        for start in range(1, 13):
            assert sum(p.years for p in st.sthira_timeline(start)) == 96, start


class TestParasharasYogardhaExample:
    def test_aquarius_start_spans(self):
        """From the Yogardha worked example (BPHS-46:174): starting Aquarius, its Sthira span is 8
        (fixed) and Pisces' is 9 (dual)."""
        tl = {p.sign: p.years for p in st.sthira_timeline(11)}
        assert tl[11] == 8      # Aquarius, fixed
        assert tl[12] == 9      # Pisces, dual


class TestSeedDelegation:
    def test_brahma_graha_rule_is_recorded(self):
        note = st.brahma_graha_note()
        assert "6th/8th/12th" in note and "Shadbala" in note

    def test_sources_resolve(self):
        assert verify(st.SOURCE) and verify(st.SEED_SOURCE)
        # context=1 to catch words that wrap across the OCR line break ("...describe the / Sthira Dasa").
        assert "Sthira" in passage(f"{st.SOURCE.work}:{st.SOURCE.line}", context=1)["text"]
        assert "Brahma Graha" in passage(f"{st.SEED_SOURCE.work}:{st.SEED_SOURCE.line}", context=1)["text"]
