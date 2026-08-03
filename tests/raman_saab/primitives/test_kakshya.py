"""Kakshya micro-transit — `primitives/kakshya.py` (ASP-13).

The fixtures are Raman's own worked statements about the Standard Horoscope (the 16-10-1918
nativity shared across his books; stated Nirayana longitudes from the GBB §10 fixture, built
Track-B so no ephemeris enters):

  - "there are 4 bindus (in Jupiter's Ashtakavarga) in Aquarius and the Prasthara Chakra of
    Jupiter makes it clear that these 4 bindus have been distributed by Mars, Venus, Mercury
    and Lagna" (ASP-13:435-439) — pins BOTH the count and the contributor set.
  - "Jupiter is in 23° 35' of Gemini occupying the Kakshya of the Moon and the Moon has
    contributed a bindu minimising Jupiter's afflictions" (ASP-12, Standard Horoscope) — pins
    the arc arithmetic AND the judgment on a natal placement.
  - The 1962 transit table (ASP-13:443-451): Saturn 300°0'-303°45', Jupiter -307°30', Mars
    -311°15', Sun -315°0', Venus -318°45', Mercury -322°30', Moon -326°15', Lagna -330°0'.

The order test is the fidelity-critical one: the PRINTED PROSE (ASP-13:424-425) drops Mars —
a printer's slip, 7 names for 8 parts — so an implementation transcribed from the sentence
instead of Raman's table would misrule six of the eight Kakshyas.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives.kakshya import (
    KAKSHYA_ORDER,
    KAKSHYA_SPAN,
    kakshya_of,
    transit_kakshya_reading,
)

#: The GBB §10 stated Nirayana longitudes (Track-B — Raman's printed positions, no ephemeris).
_STANDARD = {
    "Sun": 179 + 8 / 60, "Moon": 311 + 40 / 60, "Mars": 229 + 49 / 60,
    "Mercury": 180 + 33 / 60, "Jupiter": 83 + 35 / 60, "Venus": 170 + 4 / 60,
    "Saturn": 124 + 51 / 60, "Rahu": 53 + 23 / 60, "Ketu": 233 + 23 / 60,
}


@pytest.fixture(scope="module")
def standard() -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": lon, "bhava": 1} for p, lon in _STANDARD.items()},
        asc_lon=185.0, ayanamsa="raman")          # Libra Lagna


class TestOrderAndArcs:
    def test_the_order_is_the_tables_not_the_misprinted_sentence(self):
        """ASP-13:443-451. The prose at :424-425 omits Mars in the print; the longitude table
        is the authority. Mars MUST be third or six of eight Kakshyas misrule."""
        assert KAKSHYA_ORDER == ("Saturn", "Jupiter", "Mars", "Sun",
                                 "Venus", "Mercury", "Moon", "Lagna")

    def test_the_1962_table_boundaries_reproduce(self):
        """Each row of Raman's printed Aquarius table lands in its stated Kakshya."""
        rows = [(300.0, "Saturn"), (303.75, "Jupiter"), (307.5, "Mars"), (311.25, "Sun"),
                (315.0, "Venus"), (318.75, "Mercury"), (322.5, "Moon"), (326.25, "Lagna")]
        for start_lon, lord in rows:
            _idx, got = kakshya_of(start_lon + 0.1)
            assert got == lord, f"{start_lon}: {got} != {lord}"

    def test_span_is_three_and_three_quarters(self):
        """'8 parts or Kakshyas (of 3¾° each)' (ASP-13:423-424)."""
        assert KAKSHYA_SPAN == 3.75

    def test_boundary_belongs_to_the_kakshya_it_begins(self):
        """303°45' ends Saturn's and STARTS Jupiter's, per the table's own boundary writing —
        the same floor-division cusp convention CLAUDE.md locks for nakshatras."""
        assert kakshya_of(303.75)[1] == "Jupiter"
        assert kakshya_of(303.749999)[1] == "Saturn"

    def test_every_sign_cycles_identically(self):
        for sign_start in range(0, 360, 30):
            assert kakshya_of(float(sign_start))[1] == "Saturn"
            assert kakshya_of(sign_start + 29.999)[1] == "Lagna"


class TestStandardHoroscopeFixtures:
    def test_jupiters_aquarius_bindus_and_contributors(self, standard):
        """ASP-13:435-439 — 4 bindus in Aquarius, donated by Mars, Venus, Mercury and Lagna.
        Pins the engine's _BENEFIC tables against Raman's own Prasthara reading."""
        r = transit_kakshya_reading(standard, "Jupiter", 301.0)     # anywhere in Aquarius
        assert r.sign == 11
        assert r.bindus_in_sign == 4
        assert r.contributors == frozenset({"Mars", "Venus", "Mercury", "Lagna"})

    def test_natal_jupiter_sits_in_the_moons_kakshya_with_a_moon_bindu(self, standard):
        """ASP-12 (Standard Horoscope): 'Jupiter is in 23°35' of Gemini occupying the Kakshya
        of the Moon and the Moon has contributed a bindu.' Both halves must hold."""
        r = transit_kakshya_reading(standard, "Jupiter", _STANDARD["Jupiter"])
        assert r.sign == 3                                          # Gemini
        assert r.kakshya_lord == "Moon"
        assert r.lord_contributed and r.favourable

    def test_the_1962_judgments_reproduce(self, standard):
        """ASP-13:459-474 — Saturn's and Jupiter's own Kakshyas run adverse (no bindu donated),
        Mars's runs favourable (bindu donated), in Jupiter's Aquarius transit."""
        cases = [(301.0, "Saturn", False), (305.0, "Jupiter", False), (309.0, "Mars", True)]
        for lon, lord, fav in cases:
            r = transit_kakshya_reading(standard, "Jupiter", lon)
            assert r.kakshya_lord == lord
            assert r.favourable is fav, f"{lord}'s Kakshya read {r.favourable}, Raman says {fav}"

    def test_sign_proportion_is_bindus_over_eight(self, standard):
        """ASP-13:280-282 — 5 bindus 'to the extent of 62%'; here 4/8 = 'offset to the extent
        of 50%, gain and loss being in equal measure' (ASP-13:456-458)."""
        r = transit_kakshya_reading(standard, "Jupiter", 301.0)
        assert r.sign_proportion == pytest.approx(0.5)


class TestContract:
    def test_nodes_have_no_ashtakavarga(self, standard):
        """Rahu/Ketu earn no bindus (7-graha lock) — judging their transit here would fabricate
        a table that does not exist, so it must raise rather than return something plausible."""
        with pytest.raises(KeyError):
            transit_kakshya_reading(standard, "Rahu", 301.0)
