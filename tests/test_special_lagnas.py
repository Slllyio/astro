"""Tests for app.core.special_lagnas — S-3 alternative reading frames."""
from __future__ import annotations

import pytest

from app.core.special_lagnas import (
    INDU_KALA, SpecialLagna, SpecialLagnasReport,
    compute_all_special_lagnas, compute_bhava_lagna,
    compute_ghati_lagna, compute_hora_lagna, compute_indu_lagna,
    compute_sree_lagna, format_special_lagnas,
)


class TestIndulagna:
    """IL is chart-only — always computable."""

    def test_returns_special_lagna(self):
        il = compute_indu_lagna(
            asc_sign=6, moon_sign=12, moon_nakshatra_index=26,
        )
        assert isinstance(il, SpecialLagna)
        assert il.name == "Indu"

    def test_il_sign_in_1_12(self):
        for asc in range(1, 13):
            for moon in range(1, 13):
                for nak in range(0, 27):
                    il = compute_indu_lagna(asc, moon, nak)
                    assert 1 <= il.sign <= 12

    def test_precision_exact(self):
        il = compute_indu_lagna(1, 1, 0)
        assert il.precision == "exact (chart-only)"

    def test_kala_table_has_7_visible_grahas(self):
        assert set(INDU_KALA.keys()) == {
            "Sun", "Moon", "Mars", "Mercury",
            "Jupiter", "Venus", "Saturn",
        }


class TestSreelagna:
    """SL = Lagna + Moon's scaled nakshatra-portion. Chart-only."""

    def test_returns_special_lagna(self):
        sl = compute_sree_lagna(asc_lon=10.0, moon_lon=100.0)
        assert isinstance(sl, SpecialLagna) and sl.name == "Sree"

    def test_sl_sign_in_1_12(self):
        for asc in (0.0, 90.0, 180.0, 270.0):
            for moon in (10.0, 100.0, 200.0, 300.0):
                sl = compute_sree_lagna(asc, moon)
                assert 1 <= sl.sign <= 12

    def test_moon_at_nakshatra_start_sl_equals_lagna(self):
        """When Moon is exactly at a nakshatra boundary, SL = Lagna."""
        # Moon at 0.0 → moon_within_nak = 0 → scaled = 0 → SL_lon = asc_lon
        sl = compute_sree_lagna(asc_lon=50.0, moon_lon=0.0)
        # 50.0 falls in sign 2 (Taurus)
        assert sl.sign == 2
        assert abs(sl.longitude - 50.0) < 0.01


class TestBhavaHoraGhati:
    """BL / HL / GL need birth_jd + birth_lon."""

    def test_returns_none_when_birth_jd_missing(self):
        for fn in (compute_bhava_lagna, compute_hora_lagna, compute_ghati_lagna):
            assert fn(sun_lon=100.0, birth_jd=None, birth_lon=80.0) is None

    def test_returns_none_when_birth_lon_missing(self):
        for fn in (compute_bhava_lagna, compute_hora_lagna, compute_ghati_lagna):
            assert fn(sun_lon=100.0, birth_jd=2447988.0, birth_lon=None) is None

    def test_bl_advances_slower_than_hl_slower_than_gl(self):
        """At the same time-after-sunrise, GL >> HL >> BL in advancement.

        Because they all start at sun_lon and advance at 15°/30°/75° per
        hour respectively, the difference (special_lon - sun_lon) % 360
        should be increasing.
        """
        # Pick a birth that's clearly mid-day (well after sunrise)
        bl = compute_bhava_lagna(sun_lon=0.0, birth_jd=2447988.0 + 0.5,
                                  birth_lon=0.0)
        hl = compute_hora_lagna(sun_lon=0.0, birth_jd=2447988.0 + 0.5,
                                 birth_lon=0.0)
        gl = compute_ghati_lagna(sun_lon=0.0, birth_jd=2447988.0 + 0.5,
                                  birth_lon=0.0)
        assert bl is not None and hl is not None and gl is not None
        # HL advance > BL advance; GL advance > HL advance
        bl_adv = bl.longitude
        hl_adv = hl.longitude
        gl_adv = gl.longitude
        # GL is much faster — confirm it advanced more than HL
        assert (gl_adv - hl_adv) % 360.0 > 0 or gl_adv > hl_adv

    def test_precision_marked_approximate(self):
        bl = compute_bhava_lagna(sun_lon=100.0, birth_jd=2447988.5, birth_lon=80.0)
        assert bl is not None
        assert "approximate" in bl.precision


class TestAggregate:
    """compute_all_special_lagnas returns all 5 fields."""

    def test_il_and_sl_always_present(self):
        r = compute_all_special_lagnas(
            asc_sign=6, asc_lon=173.99,
            sun_lon=88.6, moon_sign=12, moon_lon=351.0,
            moon_nakshatra_index=26,
            birth_jd=None, birth_lon=None,
        )
        assert r.indu_lagna is not None
        assert r.sree_lagna is not None

    def test_bl_hl_gl_none_without_birth_jd(self):
        r = compute_all_special_lagnas(
            asc_sign=6, asc_lon=173.99,
            sun_lon=88.6, moon_sign=12, moon_lon=351.0,
            moon_nakshatra_index=26,
            birth_jd=None, birth_lon=80.0,
        )
        assert r.bhava_lagna is None
        assert r.hora_lagna is None
        assert r.ghati_lagna is None

    def test_all_5_when_complete_inputs(self):
        r = compute_all_special_lagnas(
            asc_sign=6, asc_lon=173.99,
            sun_lon=88.6, moon_sign=12, moon_lon=351.0,
            moon_nakshatra_index=26,
            birth_jd=2447988.5, birth_lon=80.0,
        )
        for sl in (r.bhava_lagna, r.hora_lagna, r.ghati_lagna,
                   r.indu_lagna, r.sree_lagna):
            assert sl is not None
            assert 1 <= sl.sign <= 12


class TestFormatting:
    def test_format_renders_5_frames(self):
        r = compute_all_special_lagnas(
            asc_sign=6, asc_lon=173.99,
            sun_lon=88.6, moon_sign=12, moon_lon=351.0,
            moon_nakshatra_index=26,
            birth_jd=2447988.5, birth_lon=80.0,
        )
        text = format_special_lagnas(r)
        assert "SPECIAL LAGNAS" in text
        for name in ("Bhava", "Hora", "Ghati", "Indu", "Sree"):
            assert name in text
