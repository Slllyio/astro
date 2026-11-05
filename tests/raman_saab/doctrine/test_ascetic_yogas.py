"""Ascetic yogas (HTJAH-II:11025-11053) and the two 9th-lord-in-the-7th sentences they unlock.

All charts are Aries rising: the 9th is Sagittarius, the 10th Capricorn, the 9th lord Jupiter.
"""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import ascetic_yogas as A
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rule_sets import ALL_RULES

_R = {r.id: r for r in ALL_RULES}


def _chart(planets: dict[str, float]) -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": lon, "bhava": 1} for p, lon in planets.items()},
        asc_lon=5.0, ayanamsa="raman")


class TestRamansStatedRules:
    def test_four_planets_in_the_10th(self) -> None:
        """HTJAH-II:11032 'Four planets in the 10th house make one a renunciate'."""
        assert A._four_in_the_10th(_chart({"Mars": 275.0, "Saturn": 280.0, "Jupiter": 285.0,
                                           "Venus": 290.0})) is True

    def test_the_sun_combusting_them_cancels_it(self) -> None:
        """HTJAH-II:11033-11035: if the Sun is one of them 'and causes combustion', no
        renunciation. Mars 7 deg from the Sun is inside his orb."""
        assert A._four_in_the_10th(_chart({"Mars": 275.0, "Saturn": 280.0, "Jupiter": 300.0,
                                           "Sun": 282.0})) is False

    def test_moon_in_a_saturn_decanate_aspected_by_saturn(self) -> None:
        """HTJAH-II:11037: Taurus 25 deg is its third decanate, Capricorn (Saturn's); Saturn in
        Scorpio aspects the Moon by his 7th."""
        assert A._moon_in_saturn_amsa_aspected_by_saturn(_chart({"Moon": 55.0, "Saturn": 220.0}))

    def test_saturn_aspecting_the_moon_sign_lord(self) -> None:
        """HTJAH-II:11043: the Moon in Leo; its lord the Sun in Aquarius; Saturn in Leo aspects
        Aquarius."""
        assert A._moon_sign_lord_aspected(_chart({"Moon": 130.0, "Sun": 310.0, "Saturn": 132.0}))

    def test_saturn_being_the_moon_sign_lord_is_not_an_aspect(self) -> None:
        """The strict rule needs an aspect; Raman's looser identity reading (NH:6921) is not
        followed. The Moon in Capricorn with Saturn its lord, the Lagna lord absent."""
        assert not A._moon_sign_lord_aspected(_chart({"Moon": 280.0, "Saturn": 100.0}))

    def test_moon_in_the_9th_free_of_aspects(self) -> None:
        """HTJAH-II:11049. Saturn in Gemini aspecting it spoils the yoga."""
        assert A._moon_in_the_9th_unaspected(_chart({"Moon": 250.0}))
        assert not A._moon_in_the_9th_unaspected(_chart({"Moon": 250.0, "Saturn": 70.0}))


class TestTheNinthLordInTheSeventh:
    def test_h9_l7a_fires_with_an_ascetic_yoga(self) -> None:
        """Jupiter (9th lord) in Libra; the Moon alone and unaspected in Sagittarius."""
        r = _R["H9.L.7a"]
        assert r.kind == "evaluable" and r.polarity == "neutral"
        assert r.condition.evaluate(C.EvalContext(_chart({"Jupiter": 190.0, "Moon": 250.0})))
        assert not r.condition.evaluate(C.EvalContext(_chart({"Jupiter": 190.0})))

    def test_h9_l7b_fires_when_a_malefic_spoils_the_9th_lord(self) -> None:
        """Glossary (HTJAH-I:18681-18685): 'Asubhayoga -- A combination caused by evil planets'.
        Saturn joins Jupiter in Libra."""
        r = _R["H9.L.7b"]
        assert r.kind == "evaluable" and r.polarity == "neutral"
        assert r.condition.evaluate(C.EvalContext(_chart({"Jupiter": 190.0, "Saturn": 195.0})))

    def test_papakartari_relieved_by_a_benefic_does_not_spoil(self) -> None:
        """HTJAH-II:975-977 papakartari is hemming 'with out any benefic influence'. Mars in Virgo
        and Saturn in Scorpio hem Jupiter in Libra; Venus joining him relieves it."""
        hemmed = {"Jupiter": 190.0, "Mars": 160.0, "Saturn": 225.0}
        cond = _R["H9.L.7b"].condition
        assert cond.evaluate(C.EvalContext(_chart(hemmed)))
        assert not cond.evaluate(C.EvalContext(_chart({**hemmed, "Venus": 195.0})))
