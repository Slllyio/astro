"""Ephemeris differential harness (Layer 0) — the engine's astronomy vs Swiss Ephemeris directly.

`cast_chart` (chart/adapter.py) is the only place the engine touches swisseph. This harness re-runs
swisseph INDEPENDENTLY with the engine's exact settings — the same `_jd_ut`, `_FLAGS`,
`sidereal_mode("raman")`, and `set_ephe_path(None)` (Moshier) — for a seeded sample of dates and a
curated boundary/extreme set, and asserts the engine's stored longitudes, ascendant, node, and the
pure-python derivations (sign / rasi-house / nakshatra / navamsa / retrograde) all match. Because
both paths use identical inputs, the match is exact (float tolerance only for rounding). This is a
differential against the authoritative ephemeris — not engine self-output.
"""
from __future__ import annotations

import random

import pytest
import swisseph as swe

from app.raman_saab.chart import varga
from app.raman_saab.chart.adapter import _FLAGS, _jd_ut, cast_chart
from app.raman_saab.chart.ayanamsa import sidereal_mode
from app.raman_saab.chart.constants import SWE_PLANETS
from app.raman_saab.chart.model import BirthData, RamanChart

swe.set_ephe_path(None)          # Moshier — identical to the engine (adapter.py:15)
_TOL = 1e-6                      # identical inputs -> identical output; tol only guards FP rounding
_SEED = 20260724
_SAMPLE = 250


def _independent(birth: BirthData) -> dict[str, object]:
    """Re-derive the raw astronomy for `birth` straight from swisseph, mirroring adapter.cast_chart
    exactly (Raman ayanamsa, Porphyry houses, MEAN node)."""
    jd = _jd_ut(birth)
    with sidereal_mode("raman"):
        _cusps, ascmc = swe.houses_ex(jd, birth.latitude, birth.longitude, b"O", swe.FLG_SIDEREAL)
        asc_lon = float(ascmc[0])
        lons: dict[str, tuple[float, bool]] = {}
        for name, pid in SWE_PLANETS.items():
            res, _ = swe.calc_ut(jd, pid, _FLAGS)
            lons[name] = (float(res[0]) % 360.0, res[3] < 0)
        node, _ = swe.calc_ut(jd, swe.MEAN_NODE, _FLAGS)
        lons["Rahu"] = (float(node[0]) % 360.0, True)
        lons["Ketu"] = ((float(node[0]) + 180.0) % 360.0, True)
    return {"asc_lon": asc_lon, "lons": lons}


def _random_births(n: int) -> list[BirthData]:
    rng = random.Random(_SEED)
    out: list[BirthData] = []
    for i in range(n):
        year = rng.randint(1850, 2050)
        month = rng.randint(1, 12)
        day = rng.randint(1, 28)               # 28 -> valid in every month, avoids calendar edge
        out.append(BirthData(
            name=f"s{i}", year=year, month=month, day=day,
            hour=rng.randint(0, 23), minute=rng.randint(0, 59),
            tz_offset=rng.choice([-8.0, -5.0, 0.0, 3.0, 5.5, 8.0, 9.5]),
            latitude=round(rng.uniform(-60.0, 60.0), 4),
            longitude=round(rng.uniform(-179.0, 179.0), 4)))
    return out


def _assert_planet_invariants(chart: RamanChart) -> None:
    """Laws that must hold for every planet in every chart (lat-independent)."""
    houses_seen: list[int] = []
    for name, p in chart.planets.items():
        assert 0.0 <= p.lon < 360.0, f"{name} lon out of range: {p.lon}"
        assert p.sign == int(p.lon // 30) + 1
        assert 1 <= p.sign <= 12 and 1 <= p.rasi_house <= 12
        assert 1 <= p.nakshatra <= 27 and 1 <= p.pada <= 4
        assert 1 <= p.navamsa_sign <= 12
        assert p.nakshatra == varga.nakshatra_pada(p.lon)[0]
        assert p.navamsa_sign == varga.navamsa_sign(p.lon)
        houses_seen.append(p.rasi_house)
    # Ketu is exactly opposite Rahu (7th sign, 180 deg).
    r, k = chart.planets["Rahu"], chart.planets["Ketu"]
    assert abs(((k.lon - r.lon) % 360.0) - 180.0) < _TOL
    assert (k.sign - r.sign) % 12 == 6


class TestEphemerisDifferential:
    @pytest.mark.parametrize("birth", _random_births(_SAMPLE), ids=lambda b: b.name)
    def test_engine_astronomy_matches_swisseph(self, birth: BirthData) -> None:
        """Every stored longitude / node / ascendant / derivation matches an independent swe run."""
        chart = cast_chart(birth, ayanamsa="raman")
        ind = _independent(birth)
        assert abs(chart.asc_lon - ind["asc_lon"]) < _TOL, "ascendant mismatch"
        assert chart.asc_sign == int(ind["asc_lon"] // 30) + 1
        for name, (lon, retro) in ind["lons"].items():  # type: ignore[union-attr]
            p = chart.planets[name]
            assert abs(p.lon - lon) < _TOL, f"{name} longitude: engine {p.lon} vs swe {lon}"
            assert p.retrograde == retro, f"{name} retrograde flag"
            assert p.sign == int(lon // 30) + 1
            assert p.rasi_house == ((p.sign - chart.asc_sign) % 12) + 1
        _assert_planet_invariants(chart)


class TestBoundaryAndExtreme:
    """cast_chart must survive the untested regime — high latitude, poles, historical/1800s dates,
    the date line, extreme tz, leap days — producing a chart whose PLANET-level invariants hold
    (planet longitudes are latitude-independent), or raising a clean ValueError. Never an uncaught
    swisseph/index error."""

    _CASES = [
        ("high_lat_arctic_circle", BirthData("b", 1975, 6, 21, 12, 0, 1.0, 66.5, 25.0)),
        ("high_lat_75N", BirthData("b", 1975, 6, 21, 12, 0, 1.0, 75.0, 25.0)),
        ("near_pole_89N", BirthData("b", 1975, 6, 21, 12, 0, 1.0, 89.0, 25.0)),
        ("south_high_lat", BirthData("b", 1975, 12, 21, 12, 0, 12.0, -75.0, 170.0)),
        ("dateline_east", BirthData("b", 2001, 3, 3, 6, 30, 12.0, 0.0, 179.9)),
        ("dateline_west", BirthData("b", 2001, 3, 3, 6, 30, -11.0, 0.0, -179.9)),
        ("extreme_tz_plus14", BirthData("b", 2001, 3, 3, 23, 59, 14.0, -20.0, 179.0)),
        ("historical_1850", BirthData("b", 1850, 1, 1, 0, 0, 0.0, 51.5, -0.1)),
        ("raman_era_1888", BirthData("b", 1888, 11, 8, 4, 15, 5.5, 12.97, 77.59)),
        ("pre_1800", BirthData("b", 1701, 7, 4, 9, 0, -5.0, 40.7, -74.0)),
        ("leap_2000", BirthData("b", 2000, 2, 29, 12, 0, 5.5, 12.97, 77.59)),
        ("leap_2024", BirthData("b", 2024, 2, 29, 23, 59, 9.0, 35.7, 139.7)),
        ("far_future_2050", BirthData("b", 2050, 12, 31, 12, 0, 0.0, 0.0, 0.0)),
    ]

    @pytest.mark.parametrize("label,birth", _CASES, ids=[c[0] for c in _CASES])
    def test_cast_survives_and_planet_invariants_hold(self, label: str, birth: BirthData) -> None:
        try:
            chart = cast_chart(birth, ayanamsa="raman")
        except ValueError:
            return  # a clean, documented refusal is acceptable
        _assert_planet_invariants(chart)
        # Planet longitudes are latitude-independent, so a full independent match must still hold
        # even where the ascendant/houses may be degenerate at extreme latitude.
        ind = _independent(birth)
        for name, (lon, _retro) in ind["lons"].items():  # type: ignore[union-attr]
            assert abs(chart.planets[name].lon - lon) < _TOL, f"{label}/{name} longitude drift"

    def test_pole_does_not_raise_uncaught(self) -> None:
        """Exact north pole (lat 90) — either a valid chart or a clean ValueError, never a crash."""
        try:
            chart = cast_chart(BirthData("b", 2000, 6, 21, 12, 0, 0.0, 90.0, 0.0), ayanamsa="raman")
        except ValueError:
            return
        _assert_planet_invariants(chart)
