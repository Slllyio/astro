"""KP significators pinned to Krishnamurti's own reading of the 1922 native (KPR3:19030-19050)."""

from __future__ import annotations

import pytest

from app.kp.chart import cast
from app.kp.significators import house_significators, node_represents, planet_significations
from tests.kp.test_chart import NATIVE_1922


@pytest.fixture(scope="module")
def chart():
    return cast(NATIVE_1922)


def _levels(chart, planet: str, house: int) -> set[str]:
    return {s.level for s in planet_significations(chart)[planet] if s.house == house}


class TestKrishnamurtiReading1922:
    def test_saturn_in_sun_star_signifies_house_1(self, chart) -> None:
        """'The 1st house is unoccupied. Its lord is Sun. In its constellation Saturn is posited.
        Therefore, Saturn is a strong significator.' -> Saturn signifies 1 at level C."""
        assert "C" in _levels(chart, "Saturn", 1)

    def test_planets_in_moon_star_signify_house_9(self, chart) -> None:
        """'The 9th house is occupied by the Moon. Rahu and Jupiter are in the constellation of the
        Moon.' -> both signify 9 at level A; Moon at level B."""
        assert "A" in _levels(chart, "Rahu", 9)
        assert "A" in _levels(chart, "Jupiter", 9)
        assert "B" in _levels(chart, "Moon", 9)

    def test_jupiter_carries_moon_lordship_of_12(self, chart) -> None:
        """'Jupiter being in the constellation of the Moon, lord of 12 and occupant of 9'."""
        assert "C" in _levels(chart, "Jupiter", 12)

    def test_sun_in_jupiter_star_signifies_5(self, chart) -> None:
        """'Its lord is Jupiter. Sun is in Jupiter's star' (5th house) -> Sun signifies 5 at C."""
        assert "C" in _levels(chart, "Sun", 5)


class TestLadderOrder:
    def test_house_significators_sorted_a_to_d(self, chart) -> None:
        """Tenant is stronger than owner (KPR3-TENANT): A, B before C, D."""
        order = "ABCD"
        lv = [order.index(s.level) for s in house_significators(chart, 9)]
        assert lv == sorted(lv)

    def test_nodes_represent_conjoined_then_sign_lord(self, chart) -> None:
        """Rahu in Virgo with Jupiter and Saturn represents them, then Mercury (KPR3-NODE-AGENT)."""
        assert node_represents(chart, "Rahu") == ("Jupiter", "Saturn", "Mercury")

    def test_agent_significations_are_tagged(self, chart) -> None:
        """Every node 'owned' signification is marked as agent, never as true ownership."""
        for s in planet_significations(chart)["Rahu"]:
            if s.level == "D":
                assert s.agent
