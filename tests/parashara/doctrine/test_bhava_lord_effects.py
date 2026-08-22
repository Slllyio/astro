"""Bhava-lord effects (BPHS ch.24) — the 144-statement predictive catalogue, indexed from corpus.

Fidelity is pinned three ways: full coverage (all 144 lord×house pairs keyed), every citation
resolves to a real line, and the keying is correct (a spot-checked pair's text names the right
ordinals). The six OCR-number-repaired pairs are asserted present so a regression in the repair
table is caught.
"""
from __future__ import annotations

import pytest

from app.parashara.doctrine import bhava_lord_effects as B
from app.parashara.doctrine.sources import verify


class TestCoverage:
    def test_all_144_pairs_present(self):
        eff = B.all_effects()
        assert len(eff) == 144
        assert set(eff) == {(l, k) for l in range(1, 13) for k in range(1, 13)}

    def test_every_citation_resolves(self):
        for e in B.all_effects().values():
            assert verify(e.source), (e.lord_house, e.in_house, e.source)

    def test_ocr_repaired_pairs_present(self):
        """The six slokas whose number OCR destroyed must still be keyed (repair-table regression)."""
        for key in [(3, 3), (10, 2), (11, 3), (11, 11), (12, 3), (12, 4)]:
            e = B.effect_of(*key)
            assert e is not None and e.text


class TestKeying:
    def test_ascendant_lord_in_second(self):
        e = B.effect_of(1, 2)
        assert "ascendant" in e.text.lower() and "2nd" in e.text
        assert e.source.work == "BPHS-24"

    def test_third_lord_in_third_is_the_repaired_sloka(self):
        e = B.effect_of(3, 3)
        assert "3rd lord is in the 3rd" in e.text
        assert e.source.line == 338

    def test_every_pair_names_its_own_lord_or_house_mostly(self):
        """Sanity: for the cleanly-numbered slokas, the text should mention 'in the {in_house}'."""
        eff = B.all_effects()
        hits = sum(1 for (l, k), e in eff.items()
                   if f"in the {_ord(k)}" in e.text or f"in the {k}th" in e.text)
        assert hits >= 120                     # OCR mangles a few; the vast majority self-describe


class TestValidation:
    def test_out_of_range_raises(self):
        with pytest.raises(ValueError):
            B.effect_of(0, 5)
        with pytest.raises(ValueError):
            B.effect_of(5, 13)


def _ord(n: int) -> str:
    return {1: "ascendant", 2: "2nd", 3: "3rd"}.get(n, f"{n}th")
