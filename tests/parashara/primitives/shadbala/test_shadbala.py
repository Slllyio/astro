"""Shadbala (partial: Sthana + Dig + Naisargika) — BPHS ch.27.

Values pinned to Parashara's own numbers and worked example (Uchcha 152°15'/3 = 50.75, BPHS-27:97).
The partial total is asserted to declare itself incomplete (three of six balas).
"""
from __future__ import annotations

import pytest

from app.parashara.doctrine.sources import verify
from app.parashara.primitives.longevity import deep_exaltation_point
from app.parashara.primitives.shadbala import naisargika as N
from app.parashara.primitives.shadbala import dig as D
from app.parashara.primitives.shadbala import sthana as S
from app.parashara.primitives.shadbala import total as T


class TestNaisargika:
    def test_values_are_k_over_7_rupas(self):
        """BPHS-27:1406 — Sun 7/7, Moon 6/7, Venus 5/7, Jupiter 4/7, Mercury 3/7, Mars 2/7,
        Saturn 1/7 of a rupa (in virupas, x60)."""
        assert N.naisargika_bala("Sun") == pytest.approx(60.0)
        assert N.naisargika_bala("Moon") == pytest.approx(60 * 6 / 7)     # 51.43
        assert N.naisargika_bala("Saturn") == pytest.approx(60 * 1 / 7)   # 8.57

    def test_brightest_strongest(self):
        order = ["Sun", "Moon", "Venus", "Jupiter", "Mercury", "Mars", "Saturn"]
        vals = [N.naisargika_bala(p) for p in order]
        assert vals == sorted(vals, reverse=True)

    def test_nodes_rejected(self):
        with pytest.raises(ValueError):
            N.naisargika_bala("Rahu")


class TestUchcha:
    def test_full_at_exaltation(self):
        for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
            assert S.uchcha_bala(p, deep_exaltation_point(p)) == pytest.approx(60.0), p

    def test_zero_at_debilitation(self):
        for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
            debil = (deep_exaltation_point(p) + 180.0) % 360.0
            assert S.uchcha_bala(p, debil) == pytest.approx(0.0), p

    def test_parasharas_worked_example(self):
        """BPHS-27:97 — a planet 152°15' from its debilitation gets 152.25/3 = 50.75 virupas.
        Sun debilitates at 190°; a longitude 152.25° away (37.75°) reproduces it."""
        assert S.uchcha_bala("Sun", 37.75) == pytest.approx(50.75, abs=0.01)


class TestDig:
    def test_full_at_the_direction_cusp(self):
        """Jupiter/Mercury are full at the ascendant; on the asc degree they get 60."""
        asc = 100.0
        assert D.dig_bala("Jupiter", asc, asc) == pytest.approx(60.0)
        assert D.dig_bala("Mercury", asc, asc) == pytest.approx(60.0)

    def test_zero_at_the_powerless_cusp(self):
        """Saturn is powerless on the ascending degree (full at the 7th)."""
        asc = 100.0
        assert D.dig_bala("Saturn", asc, asc) == pytest.approx(0.0)

    def test_sun_full_on_the_meridian(self):
        """Sun/Mars are full at the 10th (meridian). 10th cusp = asc + 270 (equal house)."""
        asc = 0.0
        assert D.dig_bala("Sun", 270.0, asc) == pytest.approx(60.0)


class TestSthanaSubComponents:
    def test_kendradi(self):
        """angle 60 / succedent 30 / cadent 15 (BPHS-27:5)."""
        assert [S.kendradi_bala(h) for h in (1, 4, 7, 10)] == [60.0] * 4
        assert [S.kendradi_bala(h) for h in (2, 5, 8, 11)] == [30.0] * 4
        assert [S.kendradi_bala(h) for h in (3, 6, 9, 12)] == [15.0] * 4

    def test_drekkana_matches_planet_sex(self):
        """Male (Sun/Mars/Jupiter) 1st decanate, female (Venus/Moon) 2nd, eunuch (Merc/Sat) 3rd."""
        assert S.drekkana_bala("Sun", 5.0) == 15.0        # Aries 5 = 1st decanate, male
        assert S.drekkana_bala("Sun", 15.0) == 0.0        # 2nd decanate, no
        assert S.drekkana_bala("Venus", 15.0) == 15.0     # 2nd decanate, female
        assert S.drekkana_bala("Mercury", 25.0) == 15.0   # 3rd decanate, eunuch

    def test_ojhayugma_rasi_and_navamsa(self):
        """15 per favoured parity; the Sun (odd-favoured) in an odd rasi gets at least 15."""
        val = S.ojhayugmarasiamsa_bala("Sun", 5.0)        # Aries (odd)
        assert val in (15.0, 30.0)                        # +15 if navamsa also odd

    def test_saptavargaja_within_bounds(self):
        """7 vargas, each 2..45 virupas -> total in [14, 315]."""
        lons = {"Sun": 5.0, "Moon": 40.0, "Mars": 200.0, "Mercury": 100.0,
                "Jupiter": 95.0, "Venus": 300.0, "Saturn": 250.0}
        for p in lons:
            v = S.saptavargaja_bala(p, lons)
            assert 14.0 <= v <= 315.0, (p, v)


class TestTotal:
    _LONS = {"Sun": 89.1, "Moon": 355.3, "Mars": 21.7, "Mercury": 111.4,
             "Jupiter": 96.8, "Venus": 62.5, "Saturn": 262.9}

    def test_partial_is_flagged_incomplete(self):
        r = T.partial_shadbala("Jupiter", self._LONS, asc_sign=6, asc_longitude=173.99)
        assert r.complete is False
        assert T.PENDING_BALAS == ("kala", "cheshta", "drik")

    def test_virupas_is_the_three_bala_sum(self):
        r = T.partial_shadbala("Saturn", self._LONS, asc_sign=6, asc_longitude=173.99)
        assert r.virupas == pytest.approx(r.sthana.total + r.dig + r.naisargika)
        assert r.rupas == pytest.approx(r.virupas / 60.0)

    def test_all_seven_scored(self):
        got = T.partial_shadbala_all(self._LONS, asc_sign=6, asc_longitude=173.99)
        assert len(got) == 7
        for r in got.values():
            assert r.virupas > 0


class TestCitations:
    def test_sources_resolve(self):
        assert verify(N.SOURCE) and verify(D.SOURCE)
        assert verify(S.SOURCE) and verify(S.SAPTAVARGAJA_SOURCE)
