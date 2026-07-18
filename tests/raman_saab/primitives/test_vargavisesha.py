"""Vargavisesha (GBB-3 Art.28) tests — the Parijatadi ladder verbatim, the Standard-
Horoscope Example-7 pins on the OCR-clean cells, and the documented Mars-D30 cusp
artifact (mirrors tests/raman_saab/primitives/shadbala/test_fixture_standard_horoscope.py).
"""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives.shadbala.sthana import _varga_lord
from app.raman_saab.primitives.varga_lords import varga_lord_of
from app.raman_saab.primitives.vargavisesha import LADDER, SAPTAVARGA, vargavisesha

# GBB Standard Horoscope stated longitudes (Libra Lagna, asc 185 deg) — the same fixture
# the Shadbala suite pins.
_POS = {
    "Sun": 179 + 8 / 60, "Moon": 311 + 40 / 60, "Mars": 229 + 49 / 60,
    "Mercury": 180 + 33 / 60, "Jupiter": 83 + 35 / 60, "Venus": 170 + 4 / 60,
    "Saturn": 124 + 51 / 60}
_CHART = RamanChart.from_stated_positions(
    {p: {"lon": l, "bhava": 1} for p, l in _POS.items()},
    asc_lon=185.0, ayanamsa="raman")


class TestLadder:
    def test_raman_ladder_is_verbatim_gbb(self) -> None:
        """The twelve-rung Parijatadi ladder carries Raman's GBB-3:383-395 labels."""
        assert LADDER[2] == "Parijatamsa"
        assert LADDER[3] == "Parvathamsa"
        assert LADDER[12] == "Vaiseshikamsam"
        assert set(LADDER) == set(range(2, 13))

    def test_saptavarga_is_the_gbb_seven(self) -> None:
        assert SAPTAVARGA == (1, 2, 3, 7, 9, 12, 30)


class TestExampleSeven:
    def test_sun_and_venus_reproduce_parijatamsa(self) -> None:
        """GBB-3 Example 7: Ravi and Sukra occupy their own varga twice -> Parijatamsa.
        (The engine's clean cells reproduce the book exactly.)"""
        by = {v.planet: v for v in vargavisesha(_CHART)}
        assert by["Sun"].own_varga_count == 2 and by["Sun"].label == "Parijatamsa"
        assert by["Venus"].own_varga_count == 2 and by["Venus"].label == "Parijatamsa"

    def test_mars_carries_the_documented_d30_cusp_artifact(self) -> None:
        """Book: Kuja twice (Parijatamsa). Engine: once — Mars at Scorpio 19d49' sits
        0.18d below the 20d thrimsamsa cusp, the SAME hand-table artifact the Shadbala
        fixture xfails (test_fixture_standard_horoscope.py). Pinned as the engine's
        honest scheme-table reading, not silently forced to the book."""
        by = {v.planet: v for v in vargavisesha(_CHART)}
        assert by["Mars"].own_varga_count == 1
        assert by["Mars"].label is None
        assert by["Mars"].own_vargas == ("D1",)   # Scorpio rasi — Mars's own sign

    def test_no_planet_below_two_gets_a_label(self) -> None:
        """'The other planets ... have no special amsas' (GBB-3:404-405)."""
        for v in vargavisesha(_CHART):
            if v.own_varga_count < 2:
                assert v.label is None


class TestVargaLordDispatcher:
    def test_agrees_with_sthana_varga_lord(self) -> None:
        """varga_lord_of mirrors the Shadbala path's _varga_lord for every saptavarga
        division on every fixture longitude (guards the mirrored logic)."""
        names = {1: "D1", 2: "D2", 3: "D3", 7: "D7", 9: "D9", 12: "D12", 30: "D30"}
        for planet, lon in _POS.items():
            for n, vname in names.items():
                assert varga_lord_of(lon, n) == _varga_lord(planet, lon, vname), \
                    f"{planet} D{n}"

    def test_non_saptavarga_division_raises(self) -> None:
        import pytest
        with pytest.raises(ValueError):
            varga_lord_of(100.0, 10)
