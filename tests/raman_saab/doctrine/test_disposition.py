"""Disposition: Raman's fortified / afflicted axis is INFLUENCE, not strength.

"If the Moon is fortified, that is well aspected or conjoined" (HTJAH-I:4283); "Venus is the
strongest planet ... and even he is afflicted" (NH:14852-14854). Fortification and affliction are
TWO flags (NH:2843 "fortification as well as affliction"); only one set gives a clear reading.
All charts here are Aries rising: Jupiter, Mars (Lagna lord) and the Sun are functional
benefics; Saturn, Mercury and Venus functional malefics (HTJAH-I:525-527).
"""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.disposition import disposition
from app.raman_saab.doctrine.rule_sets import ALL_RULES
from app.raman_saab.judges import rule_firing as RF


def _chart(planets: dict[str, float]) -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": lon, "bhava": 1} for p, lon in planets.items()},
        asc_lon=5.0, ayanamsa="raman")


def _reading(planet: str, planets: dict[str, float]) -> str:
    return disposition(planet, _chart(planets)).reading


class TestContacts:
    def test_a_functional_benefic_aspect_fortifies(self) -> None:
        """Jupiter (9th/12th lord, Aries' best benefic) in Aries aspects the Moon in Leo (5th)."""
        assert _reading("Moon", {"Moon": 130.0, "Jupiter": 10.0}) == "good"

    def test_a_natural_malefic_conjunction_afflicts(self) -> None:
        """HTJAH-I:8434 'afflicted, by aspect or association, by malefic planets': Saturn joins
        the Moon in Leo."""
        assert _reading("Moon", {"Moon": 130.0, "Saturn": 135.0}) == "bad"

    def test_a_natural_benefic_does_not_afflict_whatever_it_rules(self) -> None:
        """Raman is split on dusthana-lord benefics (NH:14854 counts them; NH:4727-4732 calls a
        Saturn joined by the 6th-lord Moon 'free from affliction'), so they are not counted.
        Mercury owns Aries' 3rd and 6th; joining the Moon it neither afflicts nor fortifies."""
        assert _reading("Moon", {"Moon": 130.0, "Mercury": 132.0}) == "none"

    def test_a_node_always_afflicts(self) -> None:
        assert _reading("Moon", {"Moon": 130.0, "Rahu": 135.0}) == "bad"

    def test_the_dispositor_never_afflicts(self) -> None:
        """HTJAH-I:13221: the lord of the sign occupied 'only strengthens'. The Moon in Libra is
        aspected by Venus, Libra's lord, though Venus is a functional malefic for Aries."""
        assert _reading("Moon", {"Moon": 190.0, "Venus": 10.0}) == "good"

    def test_a_malefic_lagna_lord_is_both_never_one_pole(self) -> None:
        """Raman is split on a planet: 'ruler of Lagna is always the most benefic planet'
        (NH:15662) and 'does not afflict in the strict sense' (HTJAH-I:13193), yet he blames the
        Aries Lagna lord Mars for 'affliction of the 5th lord' (HTJAH-I:5925-5937). Mars in Aries
        aspecting the Moon in Libra therefore sets both flags."""
        d = disposition("Moon", _chart({"Moon": 190.0, "Mars": 10.0}))
        assert d.reading == "mixed" and d.good and d.bad

    def test_a_benefic_lagna_lord_simply_fortifies(self) -> None:
        """Taurus rising: Venus is the Lagna lord and a natural benefic -- no conflict."""
        chart = RamanChart.from_stated_positions(
            {"Moon": {"lon": 70.0, "bhava": 1}, "Venus": {"lon": 72.0, "bhava": 1}},
            asc_lon=35.0, ayanamsa="raman")
        assert disposition("Moon", chart).reading == "good"

    def test_jupiter_does_not_net_away_an_affliction(self) -> None:
        """A netted 'Jupiter relieves' rule failed the holdout: Raman calls Buddha's Saturn
        'considerably afflicted by his conjunction with Mars' with Jupiter in the same sign
        (NH:1335-1336). Jupiter aspects, Saturn joins -- both flags, so mixed."""
        assert _reading("Moon", {"Moon": 130.0, "Jupiter": 10.0, "Saturn": 135.0}) == "mixed"

    def test_jupiter_is_good_even_where_the_table_calls_him_evil(self) -> None:
        """HTJAH-II:1033 (Virgo Lagna, where the table makes Jupiter evil): Venus 'quite
        fortified by Jupiter's aspect'. Virgo rising; Jupiter in Sagittarius aspects Venus in
        Gemini."""
        chart = RamanChart.from_stated_positions(
            {"Venus": {"lon": 70.0, "bhava": 1}, "Jupiter": {"lon": 250.0, "bhava": 1}},
            asc_lon=155.0, ayanamsa="raman")
        assert disposition("Venus", chart).reading == "good"

    def test_venus_fortifies(self) -> None:
        """HTJAH-I:2338 'joined with or aspected by benefices'."""
        assert _reading("Moon", {"Moon": 130.0, "Venus": 135.0}) == "good"

    def test_both_flags_is_mixed(self) -> None:
        """HTJAH-I:5117 'moderately good, mixed results': Venus joins, Saturn aspects from
        Aquarius."""
        assert _reading("Moon", {"Moon": 130.0, "Venus": 135.0, "Saturn": 310.0}) == "mixed"

    def test_no_testimony_is_none(self) -> None:
        assert _reading("Moon", {"Moon": 130.0}) == "none"


class TestOtherTestimony:
    def test_own_sign_fortifies(self) -> None:
        """HTJAH-I:2339-2340: exaltation or own house 'will fortify him'. The Moon in Cancer."""
        assert _reading("Moon", {"Moon": 100.0}) == "good"

    def test_combustion_afflicts(self) -> None:
        """NH:15229-15231 'combustion with the Sun'. Saturn 2 deg from the Sun in Leo; the Sun is
        Saturn's enemy dispositor, but combustion still afflicts."""
        d = disposition("Saturn", _chart({"Saturn": 132.0, "Sun": 130.0}))
        assert "combust" in d.bad

    def test_debility_alone_is_not_affliction(self) -> None:
        """HTJAH-I:1709 files debility under weakness, not affliction: the Sun in Libra, alone."""
        assert _reading("Sun", {"Sun": 190.0}) == "none"


class TestThePlanetInHouseTablesUseIt:
    def test_an_afflicted_sun_in_the_6th_shows_the_affliction_reading(self) -> None:
        """HTJAH-I:6116-6117 'Sun afflicted: Long and troublesome illness'. Saturn joins the Sun at
        15 deg Virgo (the 6th) -- in Hasta, not his own Uttara Phalguni, which would fortify him.
        The chart carries no Shadbala, which used to mean the general text."""
        rule = next(r for r in ALL_RULES if r.id == "H6.P.Sun")
        assert RF._branch(rule, _chart({"Sun": 165.0, "Saturn": 168.0})) == "afflicted"

    def test_a_fortified_sun_shows_the_fortified_reading(self) -> None:
        """Jupiter in Pisces aspects the Sun in Virgo by his 7th."""
        rule = next(r for r in ALL_RULES if r.id == "H6.P.Sun")
        assert RF._branch(rule, _chart({"Sun": 165.0, "Jupiter": 345.0})) == "fortified"

    def test_mixed_shows_ramans_unconditioned_reading(self) -> None:
        rule = next(r for r in ALL_RULES if r.id == "H6.P.Sun")
        """Venus (2nd/7th lord for Aries) joins the Sun in Virgo; Saturn aspects from Pisces."""
        chart = _chart({"Sun": 165.0, "Venus": 168.0, "Saturn": 345.0})
        assert RF._branch(rule, chart) == "general"
