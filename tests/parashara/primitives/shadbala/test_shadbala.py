"""Shadbala (complete: all six balas) — BPHS ch.27.

Values pinned to Parashara's own numbers and worked example (Uchcha 152°15'/3 = 50.75, BPHS-27:97).
The total is asserted to declare itself complete and to sum all six balas.
"""
from __future__ import annotations

import pytest

from app.parashara.doctrine.sources import verify
from app.parashara.primitives.longevity import deep_exaltation_point
from app.parashara.primitives.shadbala import naisargika as N
from app.parashara.primitives.shadbala import dig as D
from app.parashara.primitives.shadbala import sthana as S
from app.parashara.primitives.shadbala import total as T
from app.parashara.primitives.shadbala.kala import KalaContext


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
    # A synthetic birth-time context (any consistent one; the assertions are structural).
    _KALA = KalaContext(is_day=True, day_third=2, unnata_fraction=0.6,
                        weekday_lord="Sun", hora_lord="Jupiter",
                        varsha_lord="Moon", masa_lord="Moon")

    def test_total_is_flagged_complete(self):
        r = T.partial_shadbala("Jupiter", self._LONS, asc_sign=6, asc_longitude=173.99, moon_waxing=False, speed=0.5, ayanamsa=24.0, kala_ctx=self._KALA)
        assert r.complete is True
        assert T.PENDING_BALAS == ()

    def test_virupas_is_the_six_bala_sum(self):
        r = T.partial_shadbala("Saturn", self._LONS, asc_sign=6, asc_longitude=173.99, moon_waxing=False, speed=0.5, ayanamsa=24.0, kala_ctx=self._KALA)
        assert r.virupas == pytest.approx(r.sthana.total + r.dig + r.naisargika + r.cheshta + r.drik + r.kala.total)
        assert r.rupas == pytest.approx(r.virupas / 60.0)

    def test_all_seven_scored(self):
        got = T.partial_shadbala_all(self._LONS, asc_sign=6, asc_longitude=173.99, moon_waxing=False, speeds={p: 0.5 for p in self._LONS}, ayanamsa=24.0, kala_ctx=self._KALA)
        assert len(got) == 7
        for r in got.values():
            assert r.virupas > 0


class TestCitations:
    def test_sources_resolve(self):
        assert verify(N.SOURCE) and verify(D.SOURCE)
        assert verify(S.SOURCE) and verify(S.SAPTAVARGAJA_SOURCE)

    def test_kala_sources_resolve(self):
        from app.parashara.primitives.shadbala import kala as K
        assert verify(K.PAKSHA_SOURCE) and verify(K.AYANA_SOURCE)
        assert verify(K.NATHONNATA_SOURCE) and verify(K.TRIBHAGA_SOURCE) and verify(K.CALENDAR_SOURCE)


class TestKalaTime:
    """The four time-based Kala sub-components (BPHS-27:232-363), driven by a KalaContext."""

    def _ctx(self, **kw):
        base = dict(is_day=True, day_third=2, unnata_fraction=1.0,
                    weekday_lord="Sun", hora_lord="Jupiter", varsha_lord="Moon", masa_lord="Mars")
        base.update(kw)
        return KalaContext(**base)

    def test_nathonnata_noon_favours_day_group(self):
        """At noon (unnata_fraction=1) Sun/Jupiter/Venus get 60, Moon/Mars/Saturn 0, Mercury 60."""
        from app.parashara.primitives.shadbala import kala as K
        ctx = self._ctx(unnata_fraction=1.0)
        for g in ("Sun", "Jupiter", "Venus"):
            assert K.nathonnata_bala(g, ctx) == pytest.approx(60.0)
        for g in ("Moon", "Mars", "Saturn"):
            assert K.nathonnata_bala(g, ctx) == pytest.approx(0.0)
        assert K.nathonnata_bala("Mercury", ctx) == 60.0

    def test_nathonnata_midnight_flips(self):
        """At midnight (unnata_fraction=0) the night group gets 60 and the day group 0."""
        from app.parashara.primitives.shadbala import kala as K
        ctx = self._ctx(unnata_fraction=0.0)
        assert K.nathonnata_bala("Moon", ctx) == pytest.approx(60.0)
        assert K.nathonnata_bala("Sun", ctx) == pytest.approx(0.0)

    def test_tribhaga_two_planets_score(self):
        """Jupiter always 60; the ruler of the birth's third (2nd of day -> Sun) 60; others 0."""
        from app.parashara.primitives.shadbala import kala as K
        ctx = self._ctx(is_day=True, day_third=2)
        assert K.tribhaga_bala("Jupiter", ctx) == 60.0
        assert K.tribhaga_bala("Sun", ctx) == 60.0            # 2nd third of day -> Sun
        scored = [g for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
                  if K.tribhaga_bala(g, ctx) > 0]
        assert set(scored) == {"Jupiter", "Sun"}              # exactly two

    def test_tribhaga_night_ruler(self):
        """1st third of night -> the Moon (plus Jupiter)."""
        from app.parashara.primitives.shadbala import kala as K
        ctx = self._ctx(is_day=False, day_third=1)
        assert K.tribhaga_bala("Moon", ctx) == 60.0

    def test_calendar_lord_values(self):
        """Varsha 15, Masa 30, Vara 45, Hora 60 to the named lord; 0 to anyone else (BPHS-27:363)."""
        from app.parashara.primitives.shadbala import kala as K
        ctx = self._ctx(varsha_lord="Moon", masa_lord="Mars", weekday_lord="Sun", hora_lord="Jupiter")
        assert K.varsha_bala("Moon", ctx) == 15.0 and K.varsha_bala("Sun", ctx) == 0.0
        assert K.masa_bala("Mars", ctx) == 30.0 and K.masa_bala("Moon", ctx) == 0.0
        assert K.vara_bala("Sun", ctx) == 45.0 and K.vara_bala("Mars", ctx) == 0.0
        assert K.hora_bala("Jupiter", ctx) == 60.0 and K.hora_bala("Moon", ctx) == 0.0


class TestCheshta:
    from app.parashara.primitives.shadbala import cheshta as _C

    def test_retrograde_is_vakra_60(self):
        from app.parashara.primitives.shadbala import cheshta as C
        assert C.cheshta_bala("Saturn", speed=-0.05) == 60.0        # retrograde -> Vakra
        assert C.MOTION_VIRUPAS["vakra"] == 60.0

    def test_sun_cheshta_is_its_ayana(self):
        from app.parashara.primitives.shadbala import cheshta as C
        assert C.cheshta_bala("Sun", speed=0.98, sun_ayana=42.0) == 42.0

    def test_moon_cheshta_is_its_paksha(self):
        from app.parashara.primitives.shadbala import cheshta as C
        assert C.cheshta_bala("Moon", speed=13.0, moon_paksha=50.0) == 50.0

    def test_near_mean_is_sama(self):
        from app.parashara.primitives.shadbala import cheshta as C
        assert C.cheshta_bala("Mars", speed=0.524) == C.MOTION_VIRUPAS["sama"]   # ~mean

    def test_fast_is_chara_or_atichara(self):
        from app.parashara.primitives.shadbala import cheshta as C
        assert C.cheshta_bala("Mars", speed=0.524 * 2.0) == C.MOTION_VIRUPAS["atichara"]

    def test_sun_without_ayana_raises(self):
        from app.parashara.primitives.shadbala import cheshta as C
        with pytest.raises(ValueError):
            C.cheshta_bala("Sun", speed=0.98)


class TestAyana:
    def test_sun_doubled_and_maxes_at_120(self):
        """Sun's Ayana is doubled; maximal at its favoured (north) solstice ~ sayana 90."""
        from app.parashara.primitives.shadbala.kala import ayana_bala
        # sidereal + ayanamsa = 90 -> max north declination; Sun favours north.
        assert ayana_bala("Sun", 90 - 24.0, 24.0) == pytest.approx(120.0, abs=0.5)

    def test_saturn_favours_south(self):
        """Moon/Saturn favour southern declination: Saturn at max SOUTH (sayana 270) -> ~60."""
        from app.parashara.primitives.shadbala.kala import ayana_bala
        assert ayana_bala("Saturn", 270 - 24.0, 24.0) == pytest.approx(60.0, abs=0.5)

    def test_mercury_always_positive_kranti(self):
        """Mercury always takes +Kranti, so its Ayana never drops below the 23ded27' floor/... i.e.
        it is >= half of the max regardless of hemisphere."""
        from app.parashara.primitives.shadbala.kala import ayana_bala
        for lon in (0.0, 90.0, 180.0, 270.0):
            assert ayana_bala("Mercury", lon, 24.0) >= 30.0

    def test_ayana_in_range(self):
        from app.parashara.primitives.shadbala.kala import ayana_bala
        for p in ("Mars", "Jupiter", "Venus", "Moon", "Saturn"):
            for lon in range(0, 360, 30):
                v = ayana_bala(p, float(lon), 24.0)
                assert 0.0 - 1e-9 <= v <= 60.0 + 1e-6, (p, lon, v)


class TestDrik:
    def test_benefic_aspect_adds_malefic_subtracts(self):
        """Sloka 19: +1/4 drishti for a benefic aspect, -1/4 for a malefic."""
        from app.parashara.primitives.shadbala.drik import drik_bala
        # Jupiter (benefic) in Aries(1) aspects Leo(5) with its special 5th -> full 60 -> +60 super
        # + 60/4 quarter. Saturn (malefic) elsewhere not aspecting keeps it positive.
        signs = {"Jupiter": 1, "Sun": 5}          # target Sun in Leo, Jupiter 5th aspect (full)
        v = drik_bala("Sun", signs, moon_waxing=True)
        assert v > 0                               # benefic Jupiter full aspect

    def test_malefic_only_is_negative(self):
        """A target aspected only by a malefic loses aspectual strength (Drik can be negative)."""
        from app.parashara.primitives.shadbala.drik import drik_bala
        signs = {"Saturn": 1, "Moon": 10}          # Saturn 10th aspect (special full) on Moon
        v = drik_bala("Moon", signs, moon_waxing=True)
        assert v < 0

    def test_mercury_jupiter_super_added(self):
        """Merc/Jup aspects are added ENTIRE on top of their quarter (super-add)."""
        from app.parashara.primitives.shadbala.drik import drik_bala
        from app.parashara.primitives.graha_drishti import drishti_value
        signs = {"Jupiter": 1, "Venus": 7}         # Jupiter 7th on Venus -> full 60
        dv = drishti_value("Jupiter", 1, 7)
        v = drik_bala("Venus", signs, moon_waxing=True)
        assert v == pytest.approx(dv / 4 + dv)     # quarter + entire super-add

    def test_nodes_cast_no_drishti(self):
        from app.parashara.primitives.graha_drishti import drishti_value
        assert drishti_value("Rahu", 1, 7) == 0.0
        assert drishti_value("Ketu", 1, 7) == 0.0
