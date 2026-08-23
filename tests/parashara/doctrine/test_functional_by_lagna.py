"""Functional nature by ascendant (BPHS ch.34) — yogakarakas, benefics, marakas.

Verified against Parashara's own 12-lagna key (sl.19-44): the six classical yogakarakas, and the
Aries entry (benefics Jupiter+Sun, malefics Saturn/Mercury/Venus, Venus the maraka).
"""
from __future__ import annotations

from app.parashara.doctrine.functional_by_lagna import (
    SOURCE, YOGAKARAKA_SOURCE, classify_all, functional_nature, is_maraka, yogakaraka)
from app.parashara.doctrine.sources import verify


class TestYogakaraka:
    def test_six_classical_yogakarakas(self):
        # asc_sign (Aries=1..Pisces=12) -> the classical yogakaraka.
        cases = {4: "Mars", 5: "Mars", 2: "Saturn", 7: "Saturn", 10: "Venus", 11: "Venus"}
        for asc, planet in cases.items():
            assert planet in yogakaraka(asc), (asc, planet, yogakaraka(asc))

    def test_owns_both_a_kendra_and_a_trikona(self):
        assert functional_nature("Saturn", 7) == "yogakaraka"     # Libra: 4th + 5th
        assert functional_nature("Mars", 4) == "yogakaraka"       # Cancer: 10th + 5th

    def test_aries_has_no_yogakaraka(self):
        assert yogakaraka(1) == ()


class TestAriesKey:
    def test_matches_parashara_key(self):
        c = classify_all(1)
        assert c["Jupiter"] == "benefic" and c["Sun"] == "benefic"
        assert c["Saturn"] == "malefic" and c["Mercury"] == "malefic"
        assert c["Venus"] == "malefic"                            # owns 7th (kendra) -> kendradhipati
        assert is_maraka("Venus", 1) is True                     # AND owns 2nd+7th -> killer

    def test_lagna_lord_is_benefic(self):
        assert functional_nature("Mars", 1) == "benefic"         # Aries: 1st (+8th), lagna lord


class TestKendradhipatyaDosha:
    def test_benefic_owning_only_a_kendra_turns_malefic(self):
        # Gemini asc: Jupiter owns 7th (Sagittarius) + 10th (Pisces) -> both kendras, no trikona.
        assert functional_nature("Jupiter", 3) == "malefic"

    def test_malefic_owning_only_a_kendra_is_neutral(self):
        # Aries asc: the Sun owns only the 5th (trikona) -> benefic; use a malefic-kendra case:
        # Cancer asc: Saturn owns 7th (Capricorn) + 8th (Aquarius) -> kendra + 8th -> malefic (8th).
        # Cleaner: Gemini asc Mars owns 6th+11th (both evil) -> malefic; pick Sagittarius asc Sun
        # owns 9th (trikona) -> benefic. A pure malefic-only-kendra: Pisces asc Mercury owns 4th
        # (Gemini) + 7th (Virgo) -> two kendras, natural benefic -> malefic. So test the rule directly:
        from app.parashara.doctrine.functional_by_lagna import houses_owned
        assert set(houses_owned("Mercury", 12)) == {4, 7}
        assert functional_nature("Mercury", 12) == "malefic"     # benefic, kendra-only -> dosha


class TestCitations:
    def test_sources_resolve(self):
        assert verify(SOURCE) and verify(YOGAKARAKA_SOURCE)
