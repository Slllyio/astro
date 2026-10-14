"""Shashtiamsa (D60) primitive: the Manual's rule, pinned against Raman's OWN degree
arithmetic in 3HC combo 234 — the two texts must agree, and the classification's absence
is asserted (the vaiseshikamsa precedent)."""
from __future__ import annotations

import pytest

from app.raman_saab.primitives import shashtiamsa as sx


class TestShashtiamsaIndex:
    def test_sixty_names_exactly(self):
        """The Manual names sixty parts; the tuple must hold exactly sixty."""
        assert len(sx.SHASHTIAMSA_NAMES) == 60

    def test_odd_sign_counts_forward(self):
        """Aries 0.2 deg is the 1st part (Ghora); Aries 29.9 the 60th (Indurekha)."""
        assert sx.shashtiamsa_index(0.2) == 1
        assert sx.shashtiamsa_name(0.2) == "Ghora"
        assert sx.shashtiamsa_index(29.9) == 60
        assert sx.shashtiamsa_name(29.9) == "Indurekha"

    def test_even_sign_reverses(self):
        """Taurus 0.2 deg must name Indurekha (the Manual: 'In case of even signs, the
        order of naming must be reversed')."""
        assert sx.shashtiamsa_index(30.2) == 60
        assert sx.shashtiamsa_name(30.2) == "Indurekha"
        assert sx.shashtiamsa_name(59.9) == "Ghora"

    def test_boundary_uses_floor_division(self):
        """An exact cusp longitude belongs to the part it BEGINS (the nakshatra-cusp
        rule): Aries 9.5 exactly opens the 20th part, not the 19th."""
        assert sx.shashtiamsa_index(9.0) == 19
        assert sx.shashtiamsa_index(9.5) == 20


class TestCrossSourceAgreement:
    """3HC combo 234's Remark: Mridwamsa 'will be the 19th part (9 to 9-1/2 deg) of this
    division in an odd sign or the 42nd (20-1/2 to 21 deg) part in an even sign'. The
    Manual's rule must reproduce Raman's own arithmetic exactly."""

    def test_mridwamsa_is_the_19th_part_in_odd_signs(self):
        # Gemini (odd) 9.25 deg -> lon 69.25.
        assert sx.shashtiamsa_name(69.25) == "Mridwamsa"
        assert sx.shashtiamsa_index(69.25) == 19

    def test_mridwamsa_is_the_42nd_part_in_even_signs(self):
        # Taurus (even) 20.75 deg -> lon 50.75: the 42nd part reversed lands name 19.
        assert int((50.75 % 30.0) // 0.5) + 1 == 42
        assert sx.shashtiamsa_name(50.75) == "Mridwamsa"
        assert sx.shashtiamsa_index(50.75) == 19

    def test_preta_puriha_is_the_12th(self):
        # 3HC 264 names Mars in Preta Puriha; the 12th part of an odd sign spans
        # 5.5-6.0 deg.
        assert sx.shashtiamsa_name(5.7) == "Preta Puriha"


class TestAppliedNatureIsPointwiseOnly:
    def test_ramans_applied_rulings_are_present(self):
        """Rakshasa cruel (Chart 135), Preta Puriha cruel (264), Mridwamsa benign (234)."""
        assert sx.RAMAN_APPLIED_NATURE["Rakshas"] == "cruel"
        assert sx.RAMAN_APPLIED_NATURE["Preta Puriha"] == "cruel"
        assert sx.RAMAN_APPLIED_NATURE["Mridwamsa"] == "benign"

    def test_classical_table_agrees_with_every_raman_ruling(self):
        """THE CONSISTENCY GATE (deliberate test update, 2026-08-11, user-approved band
        decision): the Phaladeepika Krura table corroborates Raman — it must agree with
        every applied ruling of his. Rakshas #2 and Preta Puriha #12 cruel, Mridwamsa
        #19 benign. If a future source revision breaks this, the TABLE loses, not
        Raman."""
        assert 2 in sx.CRUEL_SHASHTIAMSAS
        assert 12 in sx.CRUEL_SHASHTIAMSAS
        assert 19 not in sx.CRUEL_SHASHTIAMSAS

    def test_nature_attaches_to_the_name_across_sign_parity(self):
        """Ghora (#1, cruel) sits at part 1 of odd signs and part 60 of even signs —
        is_cruel_shashtiamsa must follow the NAME both ways (Phaladeepika's even-sign
        reversal composed with the Manual's name reversal)."""
        assert sx.is_cruel_shashtiamsa(0.2)      # Aries part 1 = Ghora
        assert sx.is_cruel_shashtiamsa(59.9)     # Taurus part 60 = Ghora
        assert not sx.is_cruel_shashtiamsa(69.25)  # Mridwamsa, odd
        assert not sx.is_cruel_shashtiamsa(50.75)  # Mridwamsa, even
