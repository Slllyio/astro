"""KP casting pinned to Krishnamurti's printed chart (KP Reader 3, native born 18 July 1922)."""

from __future__ import annotations

import pytest
import swisseph as swe

from app.kp.chart import Birth, KPUndefined, cast, kp_ayanamsa
from app.kp.ruling import ruling_planets

# KPR3:18866-18871 'Born on 18th July, 1922, Tuesday at 8-18' A.M. I.S.T. ... Lat. 24 48' N.
# Long. 85 0? E. K.P. Ayanamsa - 22 40'.'
NATIVE_1922 = Birth(1922, 7, 18, 8, 18, tz=5.5, lat=24.8, lon=85.0)

# KPR3:18960-18990 printed star and sub lords, in the book's row order.
PRINTED_STAR_SUB = {
    "Moon": ("Ketu", "Mercury"), "Mercury": ("Rahu", "Mercury"), "Venus": ("Ketu", "Saturn"),
    "Sun": ("Jupiter", "Rahu"), "Mars": ("Mercury", "Mercury"), "Jupiter": ("Moon", "Mercury"),
    "Saturn": ("Sun", "Venus"), "Rahu": ("Moon", "Moon"), "Ketu": ("Saturn", "Sun"),
}
# Printed degrees within sign (minutes) for the planets whose OCR is clean.
PRINTED_DEG = {"Sun": 2 + 2 / 60, "Moon": 12 + 6 / 60, "Venus": 10 + 47 / 60, "Mars": 18 + 30 / 60,
               "Saturn": 9 + 47 / 60, "Jupiter": 18 + 47 / 60, "Rahu": 10 + 28 / 60}


@pytest.fixture(scope="module")
def chart():
    return cast(NATIVE_1922)


class TestAyanamsa:
    def test_1922_value_matches_print(self) -> None:
        """KPR3:18871 prints 22°40' for July 1922; SIDM_KRISHNAMURTI gives it within 2'."""
        assert abs(kp_ayanamsa(NATIVE_1922.jd_ut()) - (22 + 40 / 60)) < 2 / 60

    def test_1969_value_matches_print(self) -> None:
        """KPR3:19559 prints 23°20' for 1969."""
        assert abs(kp_ayanamsa(swe.julday(1969, 9, 13, 3.0)) - (23 + 20 / 60)) < 2 / 60

    def test_global_mode_is_restored_to_lahiri(self) -> None:
        """A KP cast must not leave swisseph in Krishnamurti mode (Lahiri is the repo lock)."""
        kp_ayanamsa(2451545.0)
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        lahiri = swe.get_ayanamsa_ut(2451545.0)
        kp_ayanamsa(2451545.0)
        assert swe.get_ayanamsa_ut(2451545.0) == lahiri


class TestPrinted1922Chart:
    def test_all_star_and_sub_lords_match_print(self, chart) -> None:
        """All 18 printed star/sub lords of the 1922 native are reproduced."""
        got = {p: (chart.planets[p].star_lord, chart.planets[p].sub_lord) for p in PRINTED_STAR_SUB}
        assert got == PRINTED_STAR_SUB

    def test_degrees_within_five_arcminutes(self, chart) -> None:
        """Printed degrees agree within 5'. (Mercury prints 13°08', cast 12°49': not pinned.)"""
        for p, deg in PRINTED_DEG.items():
            assert abs(chart.planets[p].longitude % 30 - deg) < 5 / 60, p

    def test_ascendant_leo_12(self, chart) -> None:
        """Printed Ascendant 12°11' Leo."""
        asc = chart.cusp(1)
        assert asc.lords.sign == "Leo" and abs(asc.longitude % 30 - (12 + 11 / 60)) < 5 / 60

    def test_house_facts_stated_in_text(self, chart) -> None:
        """KPR3 text on this chart: 1st unoccupied, lord Sun; Sun in 11; Moon occupies 9;
        Mars lord of 9 is in 4; Mercury lord of 2 and 11; Moon lord of 12; Jupiter lord of 5."""
        assert chart.occupants(1) == ()
        assert chart.house_lord(1) == "Sun"
        assert chart.planets["Sun"].bhava == 11
        assert "Moon" in chart.occupants(9)
        assert chart.house_lord(9) == "Mars" and chart.planets["Mars"].bhava == 4
        assert set(chart.owned_houses("Mercury")) == {2, 11}
        assert chart.house_lord(12) == "Moon"
        assert chart.house_lord(5) == "Jupiter"

    def test_mean_node_matches_print_true_node_does_not(self) -> None:
        """Printed Rahu 10°28' Virgo: mean node 10°30', true node 9°38' (ruling R4)."""
        mean = cast(NATIVE_1922, node_mode="mean").planets["Rahu"].longitude % 30
        true = cast(NATIVE_1922, node_mode="true").planets["Rahu"].longitude % 30
        assert abs(mean - (10 + 28 / 60)) < 5 / 60
        assert abs(true - (10 + 28 / 60)) > 30 / 60


class TestRulingPlanets:
    def test_tuesday_birth_has_mars_day_lord(self, chart) -> None:
        """The 1922 native was born on a Tuesday (printed)."""
        assert ruling_planets(chart).day_lord == "Mars"

    def test_7_april_1966_example(self) -> None:
        """KPR3:24929-24935: 7-4-66 7.35 am: Jupiter (Thursday), Rahu (Swathi), Venus (Libra)."""
        rp = ruling_planets(cast(Birth(1966, 4, 7, 7, 35, tz=5.5, lat=13.08, lon=80.27)))
        assert (rp.day_lord, rp.moon_star_lord, rp.moon_sign_lord) == ("Jupiter", "Rahu", "Venus")

    def test_before_sunrise_counts_as_previous_day(self) -> None:
        """At 04:00 IST on a Thursday the weekday lord is still Wednesday's (ruling R10)."""
        rp = ruling_planets(cast(Birth(1966, 4, 7, 4, 0, tz=5.5, lat=13.08, lon=80.27)))
        assert rp.day_lord == "Mercury"


class TestPolar:
    def test_placidus_undefined_raises(self) -> None:
        """Inside the polar circle Placidus is undefined; no substitute system is used."""
        with pytest.raises(KPUndefined):
            cast(Birth(2000, 6, 21, 12, 0, tz=1.0, lat=78.0, lon=15.0))
