"""Shodasavarga casting tests — varga lagnas pinned on the field_case_01 nativity,
cross-module consistency with the existing D9 machinery, the D1 identity, the D2
two-sign peculiarity, and Track-B sparse-chart safety.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.raman_saab.chart import varga
from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData, RamanChart
from app.raman_saab.chart.varga_chart import cast_all_vargas, cast_varga_chart
from app.raman_saab.primitives import special_points

_FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "field_case_01.json"

#: The 16 varga lagnas of the field_case_01 nativity (raman ayanamsa) — deterministic
#: from the committed fixture birth, same exposure class as the existing goldens.
_EXPECTED_LAGNAS = {1: 8, 2: 5, 3: 12, 4: 2, 7: 5, 9: 8, 10: 9, 12: 2,
                    16: 1, 20: 7, 24: 4, 27: 11, 30: 12, 40: 3, 45: 4, 60: 3}


@pytest.fixture(scope="module")
def chart() -> RamanChart:
    b = json.loads(_FIXTURE.read_text(encoding="utf-8"))["birth"]
    return cast_chart(BirthData(name="field", year=b["year"], month=b["month"],
                                day=b["day"], hour=b["hour"], minute=b["minute"],
                                tz_offset=b["tz_offset"], latitude=b["latitude"],
                                longitude=b["longitude"]), ayanamsa="raman")


class TestVargaLagnas:
    def test_all_sixteen_lagnas_pinned(self, chart) -> None:
        """Every division's lagna on the field-case nativity matches the pinned table
        (Scorpio D1; the D9 lagna is ALSO Scorpio — a vargottama lagna)."""
        got = {n: cast_varga_chart(chart, n).lagna_sign
               for n in sorted(varga.SUPPORTED_VARGAS)}
        assert got == _EXPECTED_LAGNAS

    def test_d9_lagna_agrees_with_special_points(self, chart) -> None:
        """The generalized varga lagna reproduces the existing D9 lagna machinery."""
        vc = cast_varga_chart(chart, 9)
        assert vc.lagna_sign == special_points.navamsa_lagna(chart).sign
        assert vc.lagna_vargottama            # Scorpio rises in both D1 and D9

    def test_lagna_lord_is_the_sign_lord(self, chart) -> None:
        vc = cast_varga_chart(chart, 10)
        assert vc.lagna_sign == 9 and vc.lagna_lord == "Jupiter"


class TestCrossModuleConsistency:
    def test_d9_positions_match_planetpos_navamsa(self, chart) -> None:
        """Per-planet D9 signs and vargottama flags equal the cached PlanetPos fields."""
        vc = cast_varga_chart(chart, 9)
        for name, p in chart.planets.items():
            assert vc.positions[name].sign == p.navamsa_sign
            assert vc.positions[name].vargottama == p.vargottama

    def test_d1_houses_reproduce_rasi_houses(self, chart) -> None:
        """D1 cast through the generic machinery is exactly the rasi chart."""
        vc = cast_varga_chart(chart, 1)
        assert vc.lagna_sign == chart.asc_sign
        for name, p in chart.planets.items():
            assert vc.positions[name].house == p.rasi_house
            assert vc.positions[name].sign == p.sign


class TestHoraPeculiarity:
    def test_d2_has_no_house_frame_and_only_two_signs(self, chart) -> None:
        """The hora is a two-sign division: houses are None, signs in {Cancer, Leo}."""
        vc = cast_varga_chart(chart, 2)
        assert all(pos.house is None for pos in vc.positions.values())
        assert {pos.sign for pos in vc.positions.values()} <= {4, 5}


class TestRobustness:
    def test_track_b_sparse_chart_casts_without_crash(self) -> None:
        """A stated-positions chart with a partial planet set casts every varga."""
        sparse = RamanChart.from_stated_positions(
            {"Moon": {"lon": 100.0, "bhava": 4}, "Saturn": {"lon": 250.0, "bhava": 9}},
            asc_lon=15.0, ayanamsa="raman")
        all16 = cast_all_vargas(sparse)
        assert set(all16) == set(varga.SUPPORTED_VARGAS)
        assert set(all16[9].positions) == {"Moon", "Saturn"}

    def test_cast_all_covers_supported_vargas_ascending(self, chart) -> None:
        all16 = cast_all_vargas(chart)
        assert list(all16) == sorted(varga.SUPPORTED_VARGAS)

    def test_unsupported_division_raises(self, chart) -> None:
        with pytest.raises(ValueError):
            cast_varga_chart(chart, 5)
