"""Tests for app.medini.etl.build_event_dossier.

Validates the wide event-dossier output — event meta + dasha block + 9-planet
transit block with self-trigger detection — against deterministic fixtures.
"""
from __future__ import annotations

import pandas as pd
import pytest

from app.medini.etl.build_event_dossier import (
    _build_active_pd_lookup,
    _event_columns,
    _transit_block,
    _transit_block_empty,
    build_event_dossier,
)


@pytest.fixture
def fake_events_wd() -> pd.DataFrame:
    """Two events for one person, both with dasha lords known."""
    return pd.DataFrame([
        {
            "event_id": 100,
            "person_id": "ADB:T1",
            "event_class": "marriage",
            "event_date": "1914-12-24",
            "event_jd": 2420466.5,
            "birth_jd": 2411626.0931,
            "age_at_event_years": 24.2,
            "md_lord_at_event": "Saturn",
            "ad_lord_at_event": "Venus",
            "md_seq": 0,
            "ad_seq": 3,
            "md_elapsed_years": 4.1,
            "ad_elapsed_years": 0.8,
            "ad_duration_days": 1095.0,
            "source": "astro_databank",
        },
        {
            "event_id": 101,
            "person_id": "ADB:T1",
            "event_class": "career",
            "event_date": "1920-01-15",
            "event_jd": 2422327.5,
            "birth_jd": 2411626.0931,
            "age_at_event_years": 29.3,
            "md_lord_at_event": "Saturn",
            "ad_lord_at_event": "Mercury",
            "md_seq": 0,
            "ad_seq": 4,
            "md_elapsed_years": 9.2,
            "ad_elapsed_years": 0.5,
            "ad_duration_days": 970.0,
            "source": "astro_databank",
        },
    ])


@pytest.fixture
def fake_persons() -> pd.DataFrame:
    return pd.DataFrame([
        {"person_id": "ADB:T1", "name": "test agatha"},
    ])


@pytest.fixture
def fake_charts() -> pd.DataFrame:
    """Virgo Lagna (asc_sign=6) — same as person_dossier test fixture."""
    return pd.DataFrame([
        {"person_id": "ADB:T1", "asc_sign": 6},
    ])


@pytest.fixture
def fake_transits() -> pd.DataFrame:
    """9 transit rows for event_id=100 covering all grahas. Sun in
    Sagittarius (sign 9) → for Virgo Lagna, that's natal_house 4.
    """
    base_jd = 2420466.5
    grahas = [
        ("Sun", 250.04, 9, False, False),     # Sagittarius, slow=False
        ("Moon", 69.67, 3, False, False),     # Gemini
        ("Mars", 106.91, 4, True, True),      # Cancer, slow + retro
        ("Mercury", 268.50, 9, False, False),
        ("Jupiter", 320.10, 11, True, False), # Aquarius, slow
        ("Venus", 285.20, 10, False, False),  # Capricorn
        ("Saturn", 175.00, 6, True, False),   # Virgo, slow
        ("Rahu", 200.50, 7, True, True),      # Libra, slow + retro (nodes always retro)
        ("Ketu", 20.50, 1, True, True),       # Aries, slow + retro
    ]
    rows = []
    for graha, lon, sign, slow, retro in grahas:
        rows.append({
            "event_id": 100,
            "person_id": "ADB:T1",
            "event_jd": base_jd,
            "transit_planet": graha,
            "transit_lon": lon,
            "transit_sign": sign,
            "transit_natal_house": ((sign - 6) % 12) + 1,
            "natal_houses_ruled": "",  # unused — recomputed in dossier
            "is_slow_mover": slow,
            "is_retrograde": retro,
            "has_natal_house_lordship": False,
        })
    return pd.DataFrame(rows)


@pytest.fixture
def fake_pd_windows() -> pd.DataFrame:
    """PD windows covering event_jd=2420466.5 (PD lord = Venus) and
    event_jd=2422327.5 (PD lord = Mercury)."""
    return pd.DataFrame([
        {
            "person_id": "ADB:T1", "pd_lord": "Venus",
            "start_jd": 2420400.0, "end_jd": 2420600.0,
        },
        {
            "person_id": "ADB:T1", "pd_lord": "Mercury",
            "start_jd": 2422300.0, "end_jd": 2422400.0,
        },
        {
            "person_id": "ADB:T1", "pd_lord": "Moon",   # not active for any event
            "start_jd": 2425000.0, "end_jd": 2425100.0,
        },
    ])


class TestEmptyTransitBlock:
    def test_returns_all_9_graha_columns(self):
        """Empty block must include all 9 planet × 12 attr keys + self-trig."""
        b = _transit_block_empty()
        for graha in ["sun", "moon", "mars", "mercury", "jupiter",
                      "venus", "saturn", "rahu", "ketu"]:
            assert f"t_{graha}_lon" in b
            assert b[f"t_{graha}_sign_name"] is None
            assert b[f"t_{graha}_in_own_lord_house"] is False
        assert b["has_self_trigger_slow_mover"] is False
        assert b["n_self_trigger_slow_movers"] == 0


class TestTransitBlock:
    def test_sun_natal_house_for_virgo_lagna(self, fake_transits):
        """Sun in Sagittarius (sign 9), Virgo Lagna (asc_sign=6):
        natal_house = ((9-6) % 12) + 1 = 4."""
        b = _transit_block(fake_transits, asc_sign=6)
        assert b["t_sun_natal_house"] == 4

    def test_houses_ruled_recomputed_from_asc_sign(self, fake_transits):
        """Saturn houses_ruled for Virgo Lagna = sorted([5, 6]) → "5,6".
        (Saturn rules Capricorn=sign10 and Aquarius=sign11; from Virgo
        these become houses 5 and 6.)"""
        b = _transit_block(fake_transits, asc_sign=6)
        assert b["t_saturn_houses_ruled"] == "5,6"

    def test_self_trigger_detected_when_slow_in_own_house(self, fake_transits):
        """Saturn (slow=True) is transiting sign 6 = Virgo. For Virgo
        Lagna, that's natal_house 1. Saturn rules houses 5,6 — house 1
        is NOT in 5,6, so NO self-trigger from Saturn.
        Jupiter in sign 11 (Aquarius), Virgo Lagna → natal_house 6.
        Jupiter rules Sagittarius=9 and Pisces=12. From Virgo: houses
        4 and 7. So Jupiter in house 6 ≠ ruled house — also no self-trigger.
        Expected: has_self_trigger_slow_mover = False for this fixture."""
        b = _transit_block(fake_transits, asc_sign=6)
        assert b["has_self_trigger_slow_mover"] is False

    def test_self_trigger_when_engineered(self):
        """Engineer Mars in own ruled house. Mars rules Aries (sign 1)
        and Scorpio (sign 8). For Aries Lagna (asc_sign=1), houses ruled
        = sorted([1, 8]). Put Mars transit in sign 1 (Aries) →
        natal_house = ((1-1)%12)+1 = 1. 1 ∈ {1,8} → self-trigger."""
        engineered = pd.DataFrame([{
            "event_id": 999, "person_id": "X", "event_jd": 2400000.0,
            "transit_planet": "Mars",
            "transit_lon": 15.0, "transit_sign": 1,
            "transit_natal_house": 1, "natal_houses_ruled": "",
            "is_slow_mover": True, "is_retrograde": False,
            "has_natal_house_lordship": True,
        }])
        b = _transit_block(engineered, asc_sign=1)
        assert b["t_mars_in_own_lord_house"] is True
        assert b["has_self_trigger_slow_mover"] is True
        assert b["n_self_trigger_slow_movers"] == 1


class TestActivePDLookup:
    def test_lookup_finds_correct_pd_for_event(
        self, fake_events_wd, fake_pd_windows,
    ):
        """Event 100 at jd=2420466.5 should map to Venus PD window
        [2420400, 2420600). Event 101 at jd=2422327.5 → Mercury PD."""
        lookup = _build_active_pd_lookup(fake_events_wd, fake_pd_windows)
        assert lookup[100]["active_pd_lord"] == "Venus"
        assert lookup[101]["active_pd_lord"] == "Mercury"

    def test_lookup_excludes_events_past_pd_end(self):
        """An event past every PD's end_jd should not appear in lookup."""
        ev = pd.DataFrame([{
            "event_id": 999, "person_id": "X", "event_jd": 9_000_000.0,
        }])
        pdw = pd.DataFrame([{
            "person_id": "X", "pd_lord": "Sun",
            "start_jd": 1000.0, "end_jd": 2000.0,
        }])
        lookup = _build_active_pd_lookup(ev, pdw)
        assert 999 not in lookup


class TestEventColumns:
    def test_md_houses_ruled_for_virgo_lagna(self, fake_events_wd):
        """Saturn (MD) rules Capricorn (sign10) and Aquarius (sign11).
        For Virgo Lagna these become houses 5 and 6 → "5,6"."""
        e = fake_events_wd.iloc[0]
        cols = _event_columns(e, person_name="agatha", asc_sign=6, pd_info=None)
        assert cols["active_md_natal_houses_ruled"] == "5,6"
        assert cols["active_md_lord"] == "Saturn"

    def test_pd_block_populated_from_lookup(self, fake_events_wd):
        """pd_info from the lookup should populate active_pd_lord +
        pd_start_jd + pd_end_jd."""
        e = fake_events_wd.iloc[0]
        pd_info = {
            "active_pd_lord": "Venus",
            "pd_start_jd": 2420400.0,
            "pd_end_jd": 2420600.0,
        }
        cols = _event_columns(e, person_name="x", asc_sign=6, pd_info=pd_info)
        assert cols["active_pd_lord"] == "Venus"
        assert cols["pd_start_jd"] == 2420400.0


class TestBuildEventDossier:
    def test_returns_one_row_per_event(
        self, fake_events_wd, fake_persons, fake_charts,
        fake_transits, fake_pd_windows,
    ):
        """Two input events → two dossier rows."""
        result = build_event_dossier(
            fake_events_wd, fake_persons, fake_charts,
            fake_transits, fake_pd_windows,
        )
        assert len(result) == 2

    def test_skips_events_without_chart(
        self, fake_events_wd, fake_persons,
        fake_transits, fake_pd_windows,
    ):
        """Events whose person has no chart are dropped, not error."""
        empty_charts = pd.DataFrame(columns=["person_id", "asc_sign"])
        result = build_event_dossier(
            fake_events_wd, fake_persons, empty_charts,
            fake_transits, fake_pd_windows,
        )
        assert len(result) == 0

    def test_dossier_includes_event_dasha_transit_blocks(
        self, fake_events_wd, fake_persons, fake_charts,
        fake_transits, fake_pd_windows,
    ):
        """Each block (event meta, dasha, transit) must appear in cols."""
        result = build_event_dossier(
            fake_events_wd, fake_persons, fake_charts,
            fake_transits, fake_pd_windows,
        )
        cols = set(result.columns)
        # Event meta
        assert {"event_id", "person_name", "event_class", "event_jd"} <= cols
        # Dasha
        assert {"active_md_lord", "active_ad_lord", "active_pd_lord"} <= cols
        # Transit
        assert {"t_sun_lon", "t_saturn_natal_house",
                "t_rahu_in_own_lord_house"} <= cols
        # Self-trigger summary
        assert {"has_self_trigger_slow_mover",
                "n_self_trigger_slow_movers"} <= cols

    def test_event_without_transit_gets_empty_block(
        self, fake_events_wd, fake_persons, fake_charts,
        fake_transits, fake_pd_windows,
    ):
        """Event #101 has no transit rows in the fixture — dossier still
        produces a row, with the transit block filled with NaN/None."""
        result = build_event_dossier(
            fake_events_wd, fake_persons, fake_charts,
            fake_transits, fake_pd_windows,
        )
        row_101 = result[result["event_id"] == 101].iloc[0]
        assert pd.isna(row_101["t_sun_lon"])
        # Pandas reads parquet bools as numpy bool — use bool() coercion
        # before `is` identity check.
        assert bool(row_101["has_self_trigger_slow_mover"]) is False

    def test_column_count_in_expected_range(
        self, fake_events_wd, fake_persons, fake_charts,
        fake_transits, fake_pd_windows,
    ):
        """Wide event dossier should have ~100-120 cols (8 meta + 12 dasha
        + 9×12 transit + 2 self-trig = 8 + 12 + 108 + 2 = 130). Allow drift."""
        result = build_event_dossier(
            fake_events_wd, fake_persons, fake_charts,
            fake_transits, fake_pd_windows,
        )
        n_cols = len(result.columns)
        assert 100 <= n_cols <= 150, f"got {n_cols} cols, expected ~130"
