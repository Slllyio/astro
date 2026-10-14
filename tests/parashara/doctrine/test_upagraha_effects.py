"""Upagraha house-effects — BPHS ch.25, the 5x12 grid.

Pins full coverage (incl. the OCR-number-destroyed Vyatipata-2nd, recovered from the merged cell),
citation resolution, the block-arithmetic endpoints, and the guards.
"""
from __future__ import annotations

import pytest

from app.parashara.doctrine.upagraha_effects import all_effects, house_effect
from app.parashara.doctrine.sources import verify

_UPAGRAHAS = ("Dhuma", "Vyatipata", "Parivesha", "Indrachapa", "Upaketu")


class TestGrid:
    def test_full_60_cell_grid(self):
        g = all_effects()
        assert len(g) == 60
        for u in _UPAGRAHAS:
            for h in range(1, 13):
                assert (u, h) in g, (u, h)

    def test_every_citation_resolves(self):
        for s in all_effects().values():
            assert verify(s.source) and s.source.work == "BPHS-25"

    def test_every_cell_has_text(self):
        for s in all_effects().values():
            assert s.text.strip()

    def test_vyatipata_2nd_recovered(self):
        # sl.15's number was OCR-destroyed; its 2nd-house clause is recovered as its own cell
        eff = house_effect("Vyatipata", 2)
        assert eff is not None and "2nd" in eff.text

    def test_block_endpoints(self):
        # each block's 12th-house cell names the 12th (the arithmetic lands correctly)
        assert "12th" in house_effect("Dhuma", 12).text
        assert "12th" in house_effect("Upaketu", 12).text

    def test_dhuma_first_is_ascendant(self):
        assert "ascendant" in house_effect("Dhuma", 1).text.lower()


class TestGuards:
    def test_bad_upagraha_raises(self):
        with pytest.raises(ValueError):
            house_effect("Gulika", 1)          # Gulika is ch.25 too but not in this Sun-derived grid

    def test_bad_house_raises(self):
        with pytest.raises(ValueError):
            house_effect("Dhuma", 13)
