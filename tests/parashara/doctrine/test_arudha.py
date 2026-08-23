"""Arudha padas — BPHS ch.29-30.

The load-bearing tests are Parashara's OWN worked examples: the base counting rule and both special
exceptions (lord in the 1st -> 10th from house; lord in the 7th -> 4th from house) reproduce exactly.
"""
from __future__ import annotations

from app.parashara.chart.cast import cast
from app.parashara.doctrine.arudha import (
    EXCEPTION_SOURCE,
    PADA_NAMES,
    RULE_SOURCE,
    arudha_lagna,
    arudha_pada,
    bhava_arudhas,
    upapada,
)
from app.parashara.doctrine.sources import verify


class TestWorkedExamples:
    def test_base_rule_scorpio_mars_cancer_to_pisces(self):
        # Scorpio asc (8), lord Mars in Cancer (4) -> Pisces (12)
        assert arudha_pada(8, 4) == 12

    def test_exception_lord_in_first_is_tenth_from_house(self):
        # Sagittarius (9), lord Jupiter in Sagittarius (9) -> Virgo (6)
        assert arudha_pada(9, 9) == 6

    def test_exception_lord_in_seventh_is_fourth_from_house(self):
        # Aquarius (11), lord Saturn in Leo (5, the 7th) -> Taurus (2)
        assert arudha_pada(11, 5) == 2

    def test_lord_in_fourth_is_the_fourth(self):
        # Leo (5), lord Sun in Scorpio (8, the 4th) -> Scorpio (the 4th itself), BPHS ex.3
        assert arudha_pada(5, 8) == 8


class TestProperties:
    def test_pada_never_the_house_or_seventh(self):
        # the whole point of the exceptions: no pada lands on the house itself or its 7th
        for house in range(1, 13):
            for lord in range(1, 13):
                p = arudha_pada(house, lord)
                seventh = ((house - 1 + 6) % 12) + 1
                assert p != house and p != seventh, (house, lord, p)

    def test_all_padas_in_range(self):
        for house in range(1, 13):
            for lord in range(1, 13):
                assert 1 <= arudha_pada(house, lord) <= 12


class TestChart:
    def _chart(self):
        return cast(year=1990, month=7, day=15, hour=12, minute=0,
                    tz_offset=5.5, latitude=12.97, longitude=77.59)

    def test_twelve_arudhas(self):
        a = bhava_arudhas(self._chart())
        assert set(a) == set(range(1, 13)) and all(1 <= s <= 12 for s in a.values())

    def test_al_and_ul_are_the_first_and_twelfth(self):
        ch = self._chart()
        a = bhava_arudhas(ch)
        assert arudha_lagna(ch) == a[1] and upapada(ch) == a[12]

    def test_pada_names_cover_all_houses(self):
        assert set(PADA_NAMES) == set(range(1, 13))


class TestCitations:
    def test_sources_resolve(self):
        assert verify(RULE_SOURCE) and RULE_SOURCE.work == "BPHS-29"
        assert verify(EXCEPTION_SOURCE) and EXCEPTION_SOURCE.work == "BPHS-29"
