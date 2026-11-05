"""Gochara Vedha (transit obstruction) — `primitives/transits.py`.

Pins the Vedha cancellation logic (pure, no swisseph): the paired obstruction house, the exempt
pairs (Sun↔Saturn, Moon↔Mercury), and the table-completeness invariant (every benefic Gochara
house has a Vedha pair). Plus a public-baseline integration smoke.
"""
from __future__ import annotations

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.primitives import transits as tr


class TestVedhaLogic:
    def test_vedha_obstructs_when_paired_house_occupied(self) -> None:
        """The Sun's benefic transit in the 3rd (from Moon) is obstructed by a graha in the 9th."""
        vh, obstr = tr._vedha("Sun", 3, {"Sun": 3, "Mars": 9})
        assert vh == 9 and "Mars" in obstr

    def test_no_vedha_when_paired_house_empty(self) -> None:
        """No graha in the Vedha house → the benefic result stands."""
        vh, obstr = tr._vedha("Sun", 3, {"Sun": 3})
        assert vh == 9 and obstr == ()

    def test_sun_saturn_are_mutually_exempt(self) -> None:
        """Sun & Saturn cause no Vedha to each other (Raman's exception)."""
        _vh, obstr = tr._vedha("Sun", 3, {"Sun": 3, "Saturn": 9})
        assert obstr == ()

    def test_moon_mercury_are_mutually_exempt(self) -> None:
        """Moon & Mercury cause no Vedha to each other (Raman's exception)."""
        _vh, obstr = tr._vedha("Moon", 3, {"Moon": 3, "Mercury": 9})
        assert obstr == ()

    def test_vedha_table_covers_every_benefic_gochara_house(self) -> None:
        """Raman's Vedha table covers every benefic house of the seven grahas; the nodes have no
        row (fix 9, 2026-10-24: HPA-34:185-226 prints seven rows only)."""
        for planet, good in tr._GOCHARA_GOOD.items():
            if planet in ("Rahu", "Ketu"):
                assert planet not in tr._VEDHA, planet
                continue
            assert set(good) == set(tr._VEDHA[planet]), planet


class TestRamanVedhaTable:
    def test_mercury_tenth_is_obstructed_from_the_seventh(self) -> None:
        """Raman prints Mercury's row 2-4-6-8-10-11 over 5-3-9-1-7-12 (HPA-34:203, 207): the
        10th's Vedha point is the 7th, not the 8th of the common table (fix 9)."""
        assert tr._VEDHA["Mercury"][10] == 7
        vh, obstr = tr._vedha("Mercury", 10, {"Mercury": 10, "Jupiter": 7})
        assert vh == 7 and obstr == ("Jupiter",)

    def test_a_node_obstructs_another_planet(self) -> None:
        """The nodes are among "any other planet" that obstructs (HPA-34:159-160)."""
        _vh, obstr = tr._vedha("Jupiter", 5, {"Jupiter": 5, "Rahu": 4})
        assert obstr == ("Rahu",)

    def test_a_nodes_own_transit_has_no_vedha_point(self) -> None:
        """Raman gives no node row, so a node's good transit carries no Vedha point (fix 9)."""
        assert tr._vedha("Rahu", 3, {"Rahu": 3, "Saturn": 12}) == (None, ())


class TestReverseVedha:
    def test_sun_in_fifth_is_relieved_by_a_planet_in_eleventh(self) -> None:
        """"if the Sun is in the 5th ... no evil ... provided the 11th is being transitted at
        the same time by any other planet, excepting Saturn" (HPA-34:161-164)."""
        assert tr._reverse_vedha("Sun", 5, {"Sun": 5, "Mars": 11}) == (11, ("Mars",))

    def test_saturn_does_not_relieve_the_sun(self) -> None:
        """The Sun-Saturn exemption holds in reverse too ("excepting Saturn", HPA-34:164)."""
        assert tr._reverse_vedha("Sun", 5, {"Sun": 5, "Saturn": 11}) == (11, ())

    def test_a_good_house_or_non_vedha_point_has_no_reverse_vedha(self) -> None:
        """Reverse Vedha applies only to an adverse station that is a Vedha point."""
        assert tr.reverse_vedha_pair("Sun", 11) is None      # a good house
        assert tr.reverse_vedha_pair("Sun", 1) is None       # not a Vedha point
        assert tr.reverse_vedha_pair("Rahu", 12) is None     # nodes have no row


class TestGocharaIntegration:
    def test_gochara_rows_carry_vedha_and_net_good(self) -> None:
        """gochara() on the public baseline returns rows with the Vedha fields wired."""
        natal = cast_chart(BirthData(name="b", year=1990, month=7, day=15, hour=12, minute=0,
                                     tz_offset=5.5, latitude=12.97, longitude=77.59),
                           ayanamsa="raman")
        rows = tr.gochara(natal, 2026, 7, 24)
        assert rows
        for r in rows:
            assert isinstance(r.net_good, bool)
            # net_good can only be True on a benefic house that is un-obstructed
            assert r.net_good == (r.gochara_good and not r.vedha_by)
            if not r.gochara_good:
                assert r.vedha_house is None and r.vedha_by == ()
