"""Sudarshana Chakra — the three-lagna house view (BPHS ch.74).

Pins the three reference reckonings (a body is house 1 from its own reference: Sun-from-Sun,
Moon-from-Moon), full body coverage, occupant/consensus derivations, guards, and the citation.
"""
from __future__ import annotations

import pytest

from app.parashara.chart.cast import cast
from app.parashara.chart.sudarshana import (
    REFERENCES,
    SOURCE,
    confirmed_occupied,
    house_occupants,
    sudarshana_positions,
)
from app.parashara.doctrine.sources import verify


def _chart():
    return cast(year=1990, month=7, day=15, hour=12, minute=0,
                tz_offset=5.5, latitude=12.97, longitude=77.59)


class TestPositions:
    def test_all_bodies_covered(self):
        pos = sudarshana_positions(_chart())
        for b in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"):
            assert b in pos

    def test_body_is_first_house_from_its_own_reference(self):
        pos = sudarshana_positions(_chart())
        assert pos["Sun"].from_sun == 1        # Surya Lagna
        assert pos["Moon"].from_moon == 1      # Chandra Lagna

    def test_houses_are_in_range(self):
        for p in sudarshana_positions(_chart()).values():
            assert 1 <= p.from_lagna <= 12 and 1 <= p.from_moon <= 12 and 1 <= p.from_sun <= 12

    def test_lagna_reckoning_matches_ascendant(self):
        ch = _chart()
        pos = sudarshana_positions(ch)
        for body, p in pos.items():
            s = int(ch.longitudes[body] % 360.0 // 30) + 1
            assert p.from_lagna == ((s - ch.asc_sign) % 12) + 1


class TestOccupantsAndConsensus:
    def test_occupants_partition_all_bodies(self):
        occ = house_occupants(_chart(), "Moon")
        assert sum(len(v) for v in occ.values()) == 9      # every body placed once
        assert "Moon" in occ[1]                            # the Moon heads its own circle

    def test_bad_reference_raises(self):
        with pytest.raises(ValueError):
            house_occupants(_chart(), "Mercury")

    def test_confirmed_needs_all_three_to_agree(self):
        ch = _chart()
        conf = confirmed_occupied(ch)
        pos = sudarshana_positions(ch)
        for house, bodies in conf.items():
            for b in bodies:
                p = pos[b]
                assert p.from_lagna == p.from_moon == p.from_sun == house


class TestMeta:
    def test_references_are_the_three_lagnas(self):
        assert REFERENCES == ("Lagna", "Moon", "Sun")

    def test_source_resolves(self):
        assert verify(SOURCE) and SOURCE.work == "BPHS-74"
