"""Planetary relationships — checked against Parashara's OWN worked examples (BPHS ch.3).

The module derives relationships from sloka 55's formula rather than copying the chapter's table.
That is only trustworthy if the derivation reproduces the two cases Parashara works by hand in his
own notes — so those are the load-bearing tests here:

    "Take for example the case of Mars. The Moolatrikona for him is Aries. The 11th lord from
     there is Saturn and hence he is inimical. But he is as well a friend, as he is the lord of
     exaltation sign of Mars. Since we get enmity on one count and friendship on the other,
     Saturn becomes equal to Mars."                                            (BPHS-3:952-956)

    "Take again the relationship of Venus. He owns the 2nd and 7th from the Moolatrikona of Mars,
     thus becoming friend and enemy respectively. Hence he is neutral to Mars."  (BPHS-3:956-959)

If the formula is encoded wrongly, these two fail — no table lookup can paper over it.
"""
from __future__ import annotations

import pytest

from app.parashara.doctrine.sources import passage, verify
from app.parashara.primitives import relationships as R


class TestParasharasOwnWorkedExamples:
    def test_saturn_is_equal_to_mars(self):
        """Saturn owns the 11th from Mars's moolatrikona (enemy) but lords Mars's exaltation sign
        Capricorn (always friendly) — 'Saturn becomes equal to Mars'."""
        assert R.naisargika("Mars", "Saturn") == "sama"

    def test_venus_is_neutral_to_mars(self):
        """Venus owns Taurus (2nd from Aries — friend) and Libra (7th — enemy). Both lists, so
        equal. This is the case a table copied from OCR most easily gets wrong."""
        assert R.naisargika("Mars", "Venus") == "sama"

    def test_the_exaltation_lord_is_always_friendly(self):
        """Sloka 55's override: 'apart from the lord of its exaltation sign' — friendly even when
        the house-count alone would make an enemy. Jupiter exalts in Cancer, lord Moon."""
        assert R.SIGN_LORDS[R.EXALTATION["Jupiter"]] == "Moon"
        assert R.naisargika("Jupiter", "Moon") == "mitra"


class TestNaisargika:
    def test_every_ordered_pair_resolves_to_a_known_state(self):
        for a in R.GRAHAS:
            for b in R.GRAHAS:
                assert R.naisargika(a, b) in ("mitra", "sama", "shatru")

    def test_a_planet_is_equal_to_itself(self):
        for g in R.GRAHAS:
            assert R.naisargika(g, g) == "sama"

    def test_relationships_need_not_be_symmetric(self):
        """A real property of the scheme, not a bug: the formula counts from EACH planet's own
        moolatrikona, so A's view of B need not match B's view of A. Asserting symmetry would be
        encoding a modern simplification Parashara does not make."""
        pairs = [(a, b) for a in R.GRAHAS for b in R.GRAHAS
                 if a != b and R.naisargika(a, b) != R.naisargika(b, a)]
        assert pairs, "expected at least one asymmetric pair — the formula is not symmetric"

    def test_nodes_are_rejected_rather_than_defaulted(self):
        """Sloka 55's formula needs a moolatrikona and an exaltation lordship; Rahu/Ketu have
        neither here. Raising beats inventing a default the text does not give."""
        with pytest.raises(ValueError):
            R.naisargika("Rahu", "Sun")


class TestTemporary:
    def test_the_six_friendly_houses(self):
        """Sloka 56 — 'posited in the 10th, 4th, 11th, 3rd, 2nd or the 12th from another'."""
        for d in (2, 3, 4, 10, 11, 12):
            assert R.temporary(d) == "mitra", d

    def test_everything_else_is_enmity(self):
        """'There is enmity otherwise' — including the 1st (same sign)."""
        for d in (1, 5, 6, 7, 8, 9):
            assert R.temporary(d) == "shatru", d

    def test_there_is_no_temporary_neutral(self):
        """The sloka admits only two states; a third would be an invention."""
        assert {R.temporary(d) for d in range(1, 13)} == {"mitra", "shatru"}


class TestCompound:
    def test_the_slokas_57_58_table(self):
        """Natural + temporary -> compound, exactly as slokas 57-58 state it."""
        cases = {
            ("mitra", "mitra"): "adhi_mitra",     # "extremely friendly"
            ("mitra", "shatru"): "sama",          # "enmity ... with affinity ... turns to equality"
            ("sama", "mitra"): "mitra",           # "friendship on one count and neutrality"
            ("sama", "shatru"): "shatru",         # "enmity and neutralship cause only enmity"
            ("shatru", "mitra"): "sama",
            ("shatru", "shatru"): "adhi_shatru",  # "extreme enmity"
        }
        assert R._COMPOUND == cases

    def test_compound_covers_every_reachable_combination(self):
        """Natural has 3 states, temporary 2 -> all 6 must be mapped, or some chart hits a
        KeyError in production."""
        for nat in ("mitra", "sama", "shatru"):
            for tmp in ("mitra", "shatru"):
                assert (nat, tmp) in R._COMPOUND

    def test_compound_produces_a_valid_varga_viswa_key(self):
        """Every compound output must be a key the Vimsopaka scale knows — the two modules meet
        exactly here, and a mismatch would only surface at runtime."""
        from app.parashara.primitives.vimsopaka import VARGA_VISWA
        for nat in ("mitra", "sama", "shatru"):
            for tmp in ("mitra", "shatru"):
                assert R._COMPOUND[(nat, tmp)] in VARGA_VISWA

    def test_worked_pair(self):
        """Jupiter->Moon is naturally friendly (exaltation lord); 4 houses away is temporarily
        friendly; friend + friend = extremely friendly."""
        assert R.compound("Jupiter", "Moon", house_distance=4) == "adhi_mitra"


class TestVargaViswaKey:
    def test_own_sign_short_circuits_to_own(self):
        """'The Vimsopaka strength remains as 20 ... only when the planet is in own house Vargas'
        (BPHS-7:266) — own sign takes the full 20 without consulting any relationship."""
        assert R.varga_viswa_key("Mars", 1) == "own"          # Aries
        assert R.varga_viswa_key("Saturn", 11) == "own"       # Aquarius

    def test_foreign_sign_requires_the_relationship(self):
        """Refuses to guess: scoring a foreign varga without its relationship would silently
        invent a dignity."""
        with pytest.raises(ValueError, match="compound relation"):
            R.varga_viswa_key("Mars", 4)

    def test_foreign_sign_passes_the_relationship_through(self):
        assert R.varga_viswa_key("Mars", 4, compound_relation="shatru") == "shatru"


class TestCitations:
    def test_the_three_slokas_resolve(self):
        for cite in (R.NAISARGIKA_SOURCE, R.TEMPORARY_SOURCE, R.COMPOUND_SOURCE):
            assert verify(cite), f"{cite.work}:{cite.line} does not resolve"

    def test_citations_point_at_the_right_slokas(self):
        assert "NATURAL RELATIONSHIP" in passage("BPHS-3:934")["text"].upper()
        assert "TEMPORARY" in passage("BPHS-3:1045")["text"].upper()
        assert "COMPOUND RELATIONSHIP" in passage("BPHS-3:1063")["text"].upper()
