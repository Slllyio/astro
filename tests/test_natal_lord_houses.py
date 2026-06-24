"""Tests for the per-person lord-house relationships ETL helpers.

The pure-function part (houses_ruled_by / house_occupied_by /
houses_aspected_by) is fully unit-testable without ephemeris.
"""
from __future__ import annotations

import pytest

from app.medini.etl.build_natal_lord_houses import (
    house_occupied_by,
    houses_aspected_by,
    houses_ruled_by,
)


# --------------------------------------------------------------------------- #
# houses_ruled_by                                                              #
# --------------------------------------------------------------------------- #

class TestHousesRuledBy:
    def test_aries_asc_mars_rules_1st_and_8th(self) -> None:
        """For Aries-ascendant: Mars rules Aries (1H) and Scorpio (8H)."""
        ruled = houses_ruled_by("Mars", asc_sign=1)
        assert ruled == [1, 8]

    def test_aries_asc_venus_rules_2nd_and_7th(self) -> None:
        """For Aries-ascendant: Venus rules Taurus (2H) and Libra (7H)."""
        ruled = houses_ruled_by("Venus", asc_sign=1)
        assert ruled == [2, 7]

    def test_aries_asc_sun_rules_5th_only(self) -> None:
        """For Aries-ascendant: Sun rules Leo (5H) only — single sign rulership."""
        ruled = houses_ruled_by("Sun", asc_sign=1)
        assert ruled == [5]

    def test_aries_asc_jupiter_rules_9th_and_12th(self) -> None:
        """For Aries-ascendant: Jupiter rules Sagittarius (9H) and Pisces (12H)."""
        ruled = houses_ruled_by("Jupiter", asc_sign=1)
        assert ruled == [9, 12]

    def test_taurus_asc_mars_rules_7th_and_12th(self) -> None:
        """For Taurus-ascendant: Mars rules Aries (12H) and Scorpio (7H)."""
        ruled = houses_ruled_by("Mars", asc_sign=2)
        assert ruled == [7, 12]


# --------------------------------------------------------------------------- #
# house_occupied_by                                                            #
# --------------------------------------------------------------------------- #

class TestHouseOccupiedBy:
    def test_planet_in_lagna_sign_is_1st_house(self) -> None:
        """Planet in the ascendant's own sign = 1H."""
        assert house_occupied_by(planet_sign=1, asc_sign=1) == 1
        assert house_occupied_by(planet_sign=4, asc_sign=4) == 1

    def test_planet_one_sign_ahead_is_2nd_house(self) -> None:
        """Aries-asc, planet in Taurus = 2H."""
        assert house_occupied_by(planet_sign=2, asc_sign=1) == 2

    def test_planet_opposite_sign_is_7th_house(self) -> None:
        """Aries-asc, planet in Libra = 7H."""
        assert house_occupied_by(planet_sign=7, asc_sign=1) == 7

    def test_wraps_around_zodiac(self) -> None:
        """Pisces-asc (12), planet in Aries (1) = 2H."""
        assert house_occupied_by(planet_sign=1, asc_sign=12) == 2

    def test_planet_one_sign_behind_is_12th_house(self) -> None:
        """Aries-asc, planet in Pisces = 12H."""
        assert house_occupied_by(planet_sign=12, asc_sign=1) == 12


# --------------------------------------------------------------------------- #
# houses_aspected_by                                                           #
# --------------------------------------------------------------------------- #

class TestHousesAspectedBy:
    def test_sun_aspects_only_seventh_from_self(self) -> None:
        """Sun in 1H aspects only 7H (standard 7th-house drishti)."""
        # Aries-asc, Sun in Aries = 1H. Should aspect 7H (Libra).
        assert houses_aspected_by("Sun", planet_sign=1, asc_sign=1) == [7]

    def test_mars_aspects_4_7_8_from_self(self) -> None:
        """Mars in 1H aspects 4H, 7H, 8H per classical special-drishti."""
        # Aries-asc, Mars in Aries = 1H.
        aspects = houses_aspected_by("Mars", planet_sign=1, asc_sign=1)
        assert set(aspects) == {4, 7, 8}

    def test_jupiter_aspects_5_7_9_from_self(self) -> None:
        """Jupiter in 1H aspects 5H, 7H, 9H per classical special-drishti."""
        aspects = houses_aspected_by("Jupiter", planet_sign=1, asc_sign=1)
        assert set(aspects) == {5, 7, 9}

    def test_saturn_aspects_3_7_10_from_self(self) -> None:
        """Saturn in 1H aspects 3H, 7H, 10H per classical special-drishti."""
        aspects = houses_aspected_by("Saturn", planet_sign=1, asc_sign=1)
        assert set(aspects) == {3, 7, 10}

    def test_jupiter_in_10th_aspects_2_4_6(self) -> None:
        """Jupiter in 10H aspects 5+10=15 wraps to 3rd; 7+10=17 wraps to 5th;
        9+10=19 wraps to 7th — so 2H, 4H, 6H actually... let me recompute.

        Jupiter aspect distances are {5, 7, 9}. From 10H:
          - 10 + 5 - 1 mod 12 + 1 = 2H
          - 10 + 7 - 1 mod 12 + 1 = 4H
          - 10 + 9 - 1 mod 12 + 1 = 6H
        """
        # Aries-asc, Jupiter in Capricorn (sign 10) = 10H.
        aspects = houses_aspected_by("Jupiter", planet_sign=10, asc_sign=1)
        assert set(aspects) == {2, 4, 6}

    def test_rahu_uses_jupiter_like_5_7_9(self) -> None:
        """Project convention: Rahu/Ketu also use 5/7/9 drishti houses."""
        aspects = houses_aspected_by("Rahu", planet_sign=1, asc_sign=1)
        assert set(aspects) == {5, 7, 9}
