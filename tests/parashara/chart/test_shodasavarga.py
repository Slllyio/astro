"""Shodasavarga — the sixteen divisional-chart signs (BPHS ch.6-7).

Pins the full sixteen-varga set, the self-checks (D1==Rasi, D9==navamsa, Vargottama coincidence),
all signs in range, per-body coverage, and citation resolution.
"""
from __future__ import annotations

from app.parashara.chart.cast import cast
from app.parashara.chart.shodasavarga import (
    DIVISIONS_SOURCE,
    SOURCE,
    VARGAS,
    shodasavarga,
    shodasavarga_all,
)
from app.parashara.doctrine.sources import verify
from app.raman_saab.chart import varga as _varga


def _chart():
    return cast(year=1990, month=7, day=15, hour=12, minute=0,
                tz_offset=5.5, latitude=12.97, longitude=77.59)


class TestVargas:
    def test_sixteen_vargas(self):
        assert len(VARGAS) == 16
        sv = shodasavarga(100.0)
        assert len(sv) == 16 and set(sv) == {t for t, _, _ in VARGAS}

    def test_d1_is_the_rasi(self):
        for lon in (5.0, 173.99, 350.0):
            assert shodasavarga(lon)["D1"] == int(lon // 30) + 1

    def test_d9_matches_navamsa(self):
        for lon in (5.0, 173.99, 350.0):
            assert shodasavarga(lon)["D9"] == _varga.navamsa_sign(lon)

    def test_all_signs_in_range(self):
        for lon in (0.0, 88.8, 359.99):
            for s in shodasavarga(lon).values():
                assert 1 <= s <= 12

    def test_vargottama_coincidence(self):
        # a longitude in the first navamsa of a movable sign is Vargottama: D1 == D9
        assert shodasavarga(2.0)["D1"] == shodasavarga(2.0)["D9"]   # early Aries


class TestChart:
    def test_all_bodies_covered(self):
        sv = shodasavarga_all(_chart().longitudes)
        for body in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"):
            assert body in sv and len(sv[body]) == 16


class TestCitations:
    def test_sources_resolve(self):
        assert verify(SOURCE) and SOURCE.work == "BPHS-7"
        assert verify(DIVISIONS_SOURCE) and DIVISIONS_SOURCE.work == "BPHS-6"
