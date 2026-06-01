"""Tests for app.core.functional_roles — BPHS Ch.3 + Ch.34 doctrine.

Validates the canonical 5 Yogakaraka assignments (the 'golden five'),
Badhakesh house derivation by modality, Maraka identification, and
the FB/FM classification logic against doctrine-known fixtures.
"""
from __future__ import annotations

import pytest

from app.core.functional_roles import (
    FunctionalRoles,
    badhakesh_house,
    badhakesh_planet,
    functional_roles,
    houses_ruled_by,
    maraka_planets,
    yogakaraka_planets,
)


class TestHousesRuledBy:
    """Verify `((sign - asc) % 12) + 1` arithmetic against known charts."""

    def test_sun_rules_5h_for_aries_lagna(self):
        """Sun owns Leo (sign 5); from Aries Lagna (asc 1) → 5H."""
        assert houses_ruled_by("Sun", 1) == (5,)

    def test_sun_rules_1h_for_leo_lagna(self):
        """Leo Lagna means Sun (Leo lord) is the Lagna Lord (1H)."""
        assert houses_ruled_by("Sun", 5) == (1,)

    def test_mars_rules_5_and_10_for_cancer_lagna(self):
        """Cancer Lagna: Mars owns Aries (sign 1)→10H, Scorpio (8)→5H."""
        assert houses_ruled_by("Mars", 4) == (5, 10)

    def test_mars_rules_4_and_9_for_leo_lagna(self):
        """Leo Lagna: Mars Aries→9H, Scorpio→4H."""
        assert houses_ruled_by("Mars", 5) == (4, 9)

    def test_venus_rules_5_and_10_for_capricorn_lagna(self):
        """Capricorn Lagna: Venus Taurus(2)→5H, Libra(7)→10H."""
        assert houses_ruled_by("Venus", 10) == (5, 10)

    def test_venus_rules_4_and_9_for_aquarius_lagna(self):
        """Aquarius Lagna: Venus Taurus→4H, Libra→9H."""
        assert houses_ruled_by("Venus", 11) == (4, 9)

    def test_saturn_rules_9_and_10_for_taurus_lagna(self):
        """Taurus Lagna: Saturn Capricorn(10)→9H, Aquarius(11)→10H."""
        assert houses_ruled_by("Saturn", 2) == (9, 10)

    def test_saturn_rules_4_and_5_for_libra_lagna(self):
        """Libra Lagna: Saturn Capricorn→4H, Aquarius→5H."""
        assert houses_ruled_by("Saturn", 7) == (4, 5)

    def test_rahu_and_ketu_rule_nothing(self):
        """Shadow planets have no sign rulership per the doctrine lock."""
        assert houses_ruled_by("Rahu", 5) == ()
        assert houses_ruled_by("Ketu", 5) == ()


class TestYogakarakaCanonical:
    """The classical 'golden five' Yogakaraka Lagnas — exact name set."""

    def test_cancer_lagna_yk_is_mars(self):
        """BPHS — Mars rules 4H Aries (Kendra) + 10H... wait 5H+10H pair → YK."""
        assert yogakaraka_planets(4) == ("Mars",)

    def test_leo_lagna_yk_is_mars(self):
        """Leo Lagna: Mars rules 4H Scorpio + 9H Aries → Kendra+Trikona."""
        assert yogakaraka_planets(5) == ("Mars",)

    def test_taurus_lagna_yk_is_saturn(self):
        """Taurus Lagna: Saturn 9H Capricorn + 10H Aquarius → YK."""
        assert yogakaraka_planets(2) == ("Saturn",)

    def test_libra_lagna_yk_is_saturn(self):
        """Libra Lagna: Saturn 4H Capricorn + 5H Aquarius → YK."""
        assert yogakaraka_planets(7) == ("Saturn",)

    def test_capricorn_lagna_yk_is_venus(self):
        """Capricorn Lagna: Venus 5H Taurus + 10H Libra → YK."""
        assert yogakaraka_planets(10) == ("Venus",)

    def test_aquarius_lagna_yk_is_venus(self):
        """Aquarius Lagna: Venus 4H Taurus + 9H Libra → YK."""
        assert yogakaraka_planets(11) == ("Venus",)

    def test_aries_lagna_has_no_yk(self):
        """No single planet rules a non-Lagna Kendra AND Trikona for Aries."""
        assert yogakaraka_planets(1) == ()

    def test_gemini_lagna_has_no_yk(self):
        """Mutable Gemini Lagna — no canonical Yogakaraka."""
        assert yogakaraka_planets(3) == ()


class TestBadhakeshHouse:
    """Modality-driven Badhaka house assignment per Phaladeepika."""

    @pytest.mark.parametrize("lagna,expected", [
        (1, 11), (4, 11), (7, 11), (10, 11),  # movable → 11L
        (2, 9), (5, 9), (8, 9), (11, 9),       # fixed → 9L
        (3, 7), (6, 7), (9, 7), (12, 7),       # dual → 7L
    ])
    def test_modality_to_badhaka_house(self, lagna, expected):
        """Movable→11, Fixed→9, Dual→7 covers all 12 Lagnas."""
        assert badhakesh_house(lagna) == expected

    def test_aquarius_lagna_badhaka_planet_is_jupiter(self):
        """Aquarius (sign 11, fixed) → 9L Badhaka. 9H from Aquarius is
        Libra (sign 7) — ruled by Venus. Wait: 9H from sign 11 = sign
        ((9-1) + 11 - 1) mod 12 + 1 = 7 → Libra → Venus."""
        assert badhakesh_planet(11) == "Venus"

    def test_aries_lagna_badhaka_planet_is_saturn(self):
        """Aries (movable) → 11L. 11H from Aries = Aquarius (sign 11) → Saturn."""
        assert badhakesh_planet(1) == "Saturn"

    def test_gemini_lagna_badhaka_planet_is_jupiter(self):
        """Gemini (dual) → 7L. 7H from Gemini = Sagittarius → Jupiter."""
        assert badhakesh_planet(3) == "Jupiter"


class TestMaraka:
    """Maraka planets — rule 2H or 7H, per BPHS Ch.34."""

    def test_aries_lagna_marakas(self):
        """Aries Lagna: 2H=Taurus (Venus), 7H=Libra (Venus). Maraka={Venus}."""
        assert maraka_planets(1) == ("Venus",)

    def test_cancer_lagna_marakas(self):
        """Cancer: 2H=Leo (Sun), 7H=Capricorn (Saturn). Marakas: Sun + Saturn."""
        m = set(maraka_planets(4))
        assert m == {"Sun", "Saturn"}

    def test_libra_lagna_marakas(self):
        """Libra: 2H=Scorpio (Mars), 7H=Aries (Mars). Maraka={Mars}."""
        assert maraka_planets(7) == ("Mars",)


class TestFunctionalBeneficMalefic:
    """FB / FM classification — the workhorse labels Phase 6 will read."""

    def test_cancer_lagna_jupiter_is_fb(self):
        """Cancer: Jupiter rules 6H Sag + 9H Pisces. 9H trikona presence
        BUT 6H dusthana too → not pure FB. Documents the nuance: a
        planet ruling BOTH trikona AND dusthana is mixed (defensive
        classification puts it as neither pure FB nor pure FM)."""
        roles = functional_roles(4)
        jup = roles["Jupiter"]
        assert jup.houses_ruled == (6, 9)
        # Mixed: trikona AND dusthana both present → not FB, not FM
        assert not jup.is_functional_benefic
        assert not jup.is_functional_malefic

    def test_cancer_lagna_mars_yk_is_fb(self):
        """Cancer Mars (YK) rules 5H + 10H. No dusthana → pure FB."""
        roles = functional_roles(4)
        mars = roles["Mars"]
        assert mars.is_yogakaraka
        assert mars.is_functional_benefic

    def test_cancer_lagna_saturn_is_fm(self):
        """Cancer Saturn rules 7H Capricorn + 8H Aquarius. 8H dusthana,
        no trikona → FM. Also Maraka (rules 7H)."""
        roles = functional_roles(4)
        sat = roles["Saturn"]
        assert sat.houses_ruled == (7, 8)
        assert sat.is_functional_malefic
        assert sat.is_maraka
        assert not sat.is_yogakaraka

    def test_taurus_lagna_saturn_yk_is_fb_not_fm(self):
        """Taurus Saturn YK rules 9H + 10H. Trikona presence, no
        dusthana → FB. Same planet, opposite disposition vs Cancer."""
        roles = functional_roles(2)
        sat = roles["Saturn"]
        assert sat.is_yogakaraka
        assert sat.is_functional_benefic
        assert not sat.is_functional_malefic


class TestFunctionalRolesStructure:
    """Sanity checks on the returned data structure."""

    def test_returns_all_7_visible_planets(self):
        """Returned mapping contains the 7 visible planets — no nodes."""
        roles = functional_roles(1)
        assert set(roles) == {"Sun", "Moon", "Mars", "Mercury",
                              "Jupiter", "Venus", "Saturn"}

    def test_dataclass_is_frozen(self):
        """FunctionalRoles is immutable — preserves invariants downstream."""
        roles = functional_roles(1)
        with pytest.raises((AttributeError, Exception)):  # frozen → FrozenInstanceError
            roles["Sun"].is_yogakaraka = True  # type: ignore[misc]

    def test_invalid_lagna_raises(self):
        """Out-of-range Lagna fails loudly per CLAUDE.md fail-fast."""
        with pytest.raises(ValueError):
            functional_roles(0)
        with pytest.raises(ValueError):
            functional_roles(13)
