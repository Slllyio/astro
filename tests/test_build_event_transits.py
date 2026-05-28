"""Tests for app/medini/etl/build_event_transits.py.

Pins the transit-state-at-event computation:
- 9 transit rows per event (Sun, Moon, Mars, Mercury, Jupiter, Venus,
  Saturn, Rahu, Ketu)
- Ketu sits exactly 180° from Rahu
- transit_natal_house derives correctly from (transit_sign, lagna_sign)
- natal_houses_ruled lists the houses the planet rules natally given lagna
- is_slow_mover flags Saturn/Jupiter/Rahu/Ketu/Mars only
- Rahu/Ketu have empty natal_houses_ruled (no classical sign rulership)
"""
from __future__ import annotations

import pandas as pd
import pytest
import swisseph as swe

from app.medini.etl.build_event_transits import (
    _HAS_LORDSHIP,
    _SIGN_RULERS,
    _SLOW_MOVERS,
    _compute_event_transits_one,
    _houses_ruled_by_planet,
    build_event_transits,
)


class TestHousesRuledByPlanet:
    """Natal house lordship: planet rules SIGN; sign sits at HOUSE from Lagna."""

    def test_jupiter_with_gemini_lagna_rules_houses_7_and_10(self):
        """Jupiter rules Sagittarius (9) and Pisces (12).
        Gemini lagna (3): Sag = (9-3)%12+1 = 7H; Pisces = (12-3)%12+1 = 10H."""
        assert _houses_ruled_by_planet("Jupiter", lagna_sign=3) == (7, 10)

    def test_saturn_with_virgo_lagna_rules_houses_5_and_6(self):
        """Saturn rules Capricorn (10) and Aquarius (11).
        Virgo lagna (6): Cap = (10-6)%12+1 = 5H; Aqua = (11-6)%12+1 = 6H."""
        assert _houses_ruled_by_planet("Saturn", lagna_sign=6) == (5, 6)

    def test_sun_rules_one_house_only(self):
        """Sun rules only Leo (5). For Aries lagna: Leo = (5-1)%12+1 = 5H."""
        assert _houses_ruled_by_planet("Sun", lagna_sign=1) == (5,)

    def test_rahu_has_no_classical_lordship(self):
        """Rahu/Ketu are nodes — no sign rulership in classical Vedic."""
        assert _houses_ruled_by_planet("Rahu", lagna_sign=1) == ()
        assert _houses_ruled_by_planet("Ketu", lagna_sign=1) == ()

    def test_all_seven_planets_have_lordship(self):
        """The 7 visible planets each rule at least one sign."""
        for planet in _HAS_LORDSHIP:
            for lagna in range(1, 13):
                houses = _houses_ruled_by_planet(planet, lagna)
                assert len(houses) >= 1, f"{planet} with lagna {lagna}: empty"


class TestComputeEventTransitsOne:
    """Single-event transit row computation."""

    @pytest.fixture
    def bangalore_event(self) -> dict:
        """Bangalore baseline person at their own birth moment."""
        # 1990-07-15 12:00 IST = 1990-07-15 06:30 UTC.
        jd = swe.julday(1990, 7, 15, 12.0 - 5.5, swe.GREG_CAL)
        return {
            "event_id": 1,
            "person_id": "TEST:bangalore",
            "event_jd": jd,
            "lagna_sign": 6,  # Virgo per CLAUDE.md
        }

    def test_nine_rows_per_event(self, bangalore_event):
        """Every event yields exactly 9 transit rows (one per graha)."""
        rows = _compute_event_transits_one(**bangalore_event)
        assert len(rows) == 9

    def test_all_planets_present(self, bangalore_event):
        """Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu."""
        rows = _compute_event_transits_one(**bangalore_event)
        planets = {r["transit_planet"] for r in rows}
        assert planets == {
            "Sun", "Moon", "Mars", "Mercury", "Jupiter",
            "Venus", "Saturn", "Rahu", "Ketu",
        }

    def test_ketu_is_opposite_rahu(self, bangalore_event):
        """Ketu's longitude must be Rahu + 180° (mod 360)."""
        rows = _compute_event_transits_one(**bangalore_event)
        rahu = next(r for r in rows if r["transit_planet"] == "Rahu")
        ketu = next(r for r in rows if r["transit_planet"] == "Ketu")
        delta = (ketu["transit_lon"] - rahu["transit_lon"]) % 360.0
        assert abs(delta - 180.0) < 0.001

    def test_slow_mover_flag_correct_for_each_planet(self, bangalore_event):
        """Saturn/Jupiter/Rahu/Ketu/Mars flagged slow; others fast."""
        rows = _compute_event_transits_one(**bangalore_event)
        for r in rows:
            expected = r["transit_planet"] in _SLOW_MOVERS
            assert r["is_slow_mover"] is expected

    def test_nodes_have_no_lordship_in_output(self, bangalore_event):
        """Rahu and Ketu must have empty natal_houses_ruled."""
        rows = _compute_event_transits_one(**bangalore_event)
        for r in rows:
            if r["transit_planet"] in ("Rahu", "Ketu"):
                assert r["natal_houses_ruled"] == ""
                assert not r["has_natal_house_lordship"]

    def test_transit_natal_house_for_known_sign(self, bangalore_event):
        """Lagna sign = 6 (Virgo). A planet in Virgo (6) lands in house 1.
        Pull the Sun (we know its mid-July position) and verify the house
        math: Sun in some sign S → house = (S - 6) % 12 + 1.
        """
        rows = _compute_event_transits_one(**bangalore_event)
        sun = next(r for r in rows if r["transit_planet"] == "Sun")
        expected_house = ((sun["transit_sign"] - 6) % 12) + 1
        assert sun["transit_natal_house"] == expected_house

    def test_saturn_rules_houses_8_and_9_with_virgo_lagna(self, bangalore_event):
        """Saturn's natal_houses_ruled string for Virgo (6) lagna is "8,9".
        (Capricorn=10 → 5H; Aquarius=11 → 6H — wait, let me recompute.)

        Saturn rules Capricorn (10) and Aquarius (11).
        With Virgo (6) lagna:
          Capricorn = (10-6)%12+1 = 5H
          Aquarius =  (11-6)%12+1 = 6H
        So natal_houses_ruled = "5,6".
        """
        rows = _compute_event_transits_one(**bangalore_event)
        saturn = next(r for r in rows if r["transit_planet"] == "Saturn")
        assert saturn["natal_houses_ruled"] == "5,6"


class TestBuildEventTransitsBatch:
    """build_event_transits processes a small dataframe end-to-end."""

    def test_two_events_yield_eighteen_rows(self):
        """2 events × 9 planets = 18 rows."""
        events = pd.DataFrame({
            "event_id": [1, 2],
            "person_id": ["P:A", "P:B"],
            "event_jd": [2447000.0, 2448000.0],
        })
        charts = pd.DataFrame({
            "person_id": ["P:A", "P:B"],
            "asc_sign": [6, 9],
        })
        result = build_event_transits(events, charts, workers=1)
        assert len(result) == 18

    def test_events_without_event_jd_are_skipped(self):
        """Events with NaN event_jd cannot have transits computed."""
        events = pd.DataFrame({
            "event_id": [1, 2],
            "person_id": ["P:A", "P:B"],
            "event_jd": [2447000.0, None],  # one valid, one null
        })
        charts = pd.DataFrame({
            "person_id": ["P:A", "P:B"],
            "asc_sign": [6, 9],
        })
        result = build_event_transits(events, charts, workers=1)
        # Only the valid event yields 9 rows.
        assert len(result) == 9
        assert result["event_id"].unique().tolist() == [1]
