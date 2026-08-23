"""Rasi drishti — sign aspects (BPHS ch.8). Pinned to Parashara's own worked examples."""
from __future__ import annotations

import pytest

from app.parashara.doctrine.sources import verify
from app.parashara.primitives import rasi_drishti as rd


class TestRasiAspects:
    def test_aries_worked_example(self):
        # Aries (movable) aspects Leo/Scorpio/Aquarius, NOT Taurus (BPHS-8).
        assert rd.rasi_aspects(1) == frozenset({5, 8, 11})
        assert not rd.aspects_sign(1, 2)

    def test_taurus_worked_example(self):
        # Taurus (fixed) aspects Cancer/Libra/Capricorn, NOT Aries.
        assert rd.rasi_aspects(2) == frozenset({4, 7, 10})
        assert not rd.aspects_sign(2, 1)

    def test_dual_aspects_the_other_duals(self):
        assert rd.rasi_aspects(3) == frozenset({6, 9, 12})       # Gemini -> Virgo/Sag/Pisces

    def test_every_sign_aspects_exactly_three(self):
        for s in range(1, 13):
            assert len(rd.rasi_aspects(s)) == 3
            assert s not in rd.rasi_aspects(s)                   # never itself

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError):
            rd.rasi_aspects(13)


class TestPlanetsAspecting:
    def test_planet_aspects_as_its_sign(self):
        # A planet in Aries aspects a target in Leo.
        assert "Sun" in rd.planets_aspecting_sign(5, {"Sun": 1, "Moon": 3})
        assert "Moon" not in rd.planets_aspecting_sign(5, {"Sun": 1, "Moon": 3})


def test_source_resolves():
    assert verify(rd.SOURCE)
