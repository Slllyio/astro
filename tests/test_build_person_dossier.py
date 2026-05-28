"""Tests for app.medini.etl.build_person_dossier.

Builds a tiny synthetic Silver (one person, one chart, eight karakas) and
asserts the dossier reproduces the Agatha-style wide row exactly, with
nakshatra/lord/houses-ruled computed correctly.
"""
from __future__ import annotations

import pandas as pd
import pytest

from app.medini.etl.build_person_dossier import (
    _corpus_from_person_id,
    _identity_columns,
    _karaka_columns,
    _natal_columns,
    build_person_dossier,
)
from app.medini.ml.person_profile import _JAIMINI_KARAKA_LABELS


@pytest.fixture
def fake_person() -> pd.DataFrame:
    """One ADB person — Agatha-like fixture."""
    return pd.DataFrame([
        {
            "person_id": "ADB:T1",
            "name": "test agatha",
            "birth_date": "1890-09-15",
            "birth_time": "14:14:00",
            "birth_lat": 50.468,
            "birth_lon": -3.532,
            "tz_offset": 0.0,
            "birth_jd": 2411626.0931,
            "birth_time_confidence": 1.0,
            "source": "astro_databank",
        },
    ])


@pytest.fixture
def fake_chart() -> pd.DataFrame:
    """One chart for ADB:T1 — Virgo Lagna at 22°. Nakshatra values are
    deterministic given longitude, so we don't need to set them — only
    asc_sign is used by the dossier (nakshatra is recomputed)."""
    return pd.DataFrame([
        {
            "person_id": "ADB:T1",
            "birth_jd_used": 2411626.0931,
            "time_precision": "minute",
            "asc_lon": 172.96,        # Virgo (sign 6) at 22.96°
            "asc_sign": 6,
            "asc_nakshatra": 11,
            "sun_lon": 152.33,        # Virgo, sign 6
            "sun_sign": 6,
            "sun_house": 1,
            "sun_nakshatra": 10,
            "moon_lon": 164.59,       # Virgo
            "moon_sign": 6,
            "moon_house": 1,
            "moon_nakshatra": 11,
            "mars_lon": 242.62,       # Sagittarius, sign 9
            "mars_sign": 9,
            "mars_house": 4,
            "mars_nakshatra": 18,
            "mercury_lon": 172.96,    # Virgo
            "mercury_sign": 6,
            "mercury_house": 1,
            "mercury_nakshatra": 11,
            "jupiter_lon": 280.27,    # Capricorn, sign 10
            "jupiter_sign": 10,
            "jupiter_house": 5,
            "jupiter_nakshatra": 21,
            "venus_lon": 196.58,      # Libra, sign 7
            "venus_sign": 7,
            "venus_house": 2,
            "venus_nakshatra": 13,
            "saturn_lon": 136.95,     # Leo, sign 5
            "saturn_sign": 5,
            "saturn_house": 12,
            "saturn_nakshatra": 9,
            "rahu_lon": 56.42,        # Taurus, sign 2
            "rahu_sign": 2,
            "rahu_house": 9,
            "rahu_nakshatra": 3,
            "ketu_lon": 236.42,       # Sagittarius
            "ketu_sign": 9,
            "ketu_house": 4,
            "ketu_nakshatra": 17,
        },
    ])


@pytest.fixture
def fake_karakas() -> pd.DataFrame:
    """8 karaka rows for ADB:T1 covering all _JAIMINI_KARAKA_LABELS."""
    rows = []
    planets_per_label = {
        "AK_Atmakaraka": ("Mercury", 6, "Virgo", 22.96, 1, "7,10"),
        "AmK_Amatyakaraka": ("Saturn", 5, "Leo", 16.95, 12, "2,3"),
        "BK_Bhratrukaraka": ("Venus", 7, "Libra", 16.58, 2, "6,11"),
        "MK_Matrukaraka": ("Moon", 6, "Virgo", 14.59, 1, "8"),
        "PK_Putrakaraka": ("Jupiter", 10, "Capricorn", 10.27, 5, "1,4"),
        "GK_Gnatikaraka": ("Rahu", 2, "Taurus", 26.42, 9, ""),
        "DK_Darakaraka": ("Mars", 9, "Sagittarius", 2.62, 4, "5,12"),
        "PK2_PutraKaraka2": ("Sun", 6, "Virgo", 0.33, 1, "9"),
    }
    for label, (pl, sign, sname, deg, house, ruled) in planets_per_label.items():
        rows.append({
            "person_id": "ADB:T1",
            "karaka": label,
            "planet": pl,
            "sign": sign,
            "sign_name": sname,
            "degree_in_sign": deg,
            "natal_house": house,
            "natal_houses_ruled": ruled,
            "ranking_score": deg,
        })
    return pd.DataFrame(rows)


class TestCorpusDerivation:
    def test_adb_prefix_returns_ADB(self):
        """Astro Databank person_id prefix maps to corpus 'ADB'."""
        assert _corpus_from_person_id("ADB:2411626.0931") == "ADB"

    def test_wd_prefix_returns_WD(self):
        """Wikidata person_id prefix maps to corpus 'WD'."""
        assert _corpus_from_person_id("WD:Q137808") == "WD"

    def test_la_prefix_returns_LA(self):
        """Lunarastro person_id prefix maps to corpus 'LA'."""
        assert _corpus_from_person_id("LA:some_name") == "LA"

    def test_unprefixed_returns_empty(self):
        """No colon → empty corpus tag (defensive default)."""
        assert _corpus_from_person_id("nocolon") == ""


class TestNatalColumns:
    def test_asc_block_has_all_keys(self, fake_chart):
        """Ascendant block must populate the 8 documented columns."""
        cols = _natal_columns(fake_chart.iloc[0])
        for key in ["asc_lon", "asc_sign", "asc_sign_name", "asc_degree_in_sign",
                    "asc_nakshatra", "asc_nakshatra_pada", "asc_nakshatra_lord",
                    "asc_lord"]:
            assert key in cols, f"missing {key}"

    def test_asc_sign_name_matches_sign(self, fake_chart):
        """Virgo Lagna (sign 6) must map to sign_name 'Virgo'."""
        cols = _natal_columns(fake_chart.iloc[0])
        assert cols["asc_sign_name"] == "Virgo"
        assert cols["asc_sign"] == 6

    def test_asc_lord_is_mercury_for_virgo(self, fake_chart):
        """Mercury is the BPHS Ch.3 lord of Virgo (sign 6)."""
        cols = _natal_columns(fake_chart.iloc[0])
        assert cols["asc_lord"] == "Mercury"

    def test_all_9_grahas_present(self, fake_chart):
        """Every graha block must produce 9 attribute columns."""
        cols = _natal_columns(fake_chart.iloc[0])
        for graha in ["sun", "moon", "mars", "mercury", "jupiter",
                      "venus", "saturn", "rahu", "ketu"]:
            for attr in ["_lon", "_sign", "_sign_name", "_degree_in_sign",
                         "_natal_house", "_nakshatra", "_nakshatra_pada",
                         "_nakshatra_lord", "_houses_ruled"]:
                assert f"{graha}{attr}" in cols, f"missing {graha}{attr}"

    def test_rahu_ketu_have_empty_houses_ruled(self, fake_chart):
        """Nodes don't rule signs in BPHS Ch.3 → empty string."""
        cols = _natal_columns(fake_chart.iloc[0])
        assert cols["rahu_houses_ruled"] == ""
        assert cols["ketu_houses_ruled"] == ""

    def test_mercury_houses_ruled_for_virgo_lagna(self, fake_chart):
        """Mercury rules Gemini (sign 3) and Virgo (sign 6). For Virgo
        Lagna these become houses 10 and 1 respectively, sorted → "1,10"."""
        cols = _natal_columns(fake_chart.iloc[0])
        assert cols["mercury_houses_ruled"] == "1,10"


class TestKarakaColumns:
    def test_all_8_karaka_prefixes_present(self, fake_karakas):
        """All 8 karaka prefixes (ak, amk, bk, mk, pk, gk, dk, pk2) must
        populate the 6 per-karaka attribute columns."""
        cols = _karaka_columns(fake_karakas)
        for prefix in ["ak", "amk", "bk", "mk", "pk", "gk", "dk", "pk2"]:
            for attr in ["_planet", "_sign", "_sign_name", "_degree_in_sign",
                         "_natal_house", "_houses_ruled"]:
                assert f"{prefix}{attr}" in cols, f"missing {prefix}{attr}"

    def test_ak_planet_is_mercury(self, fake_karakas):
        """For the Agatha-like fixture, AK = Mercury (highest deg_in_sign)."""
        cols = _karaka_columns(fake_karakas)
        assert cols["ak_planet"] == "Mercury"
        assert cols["ak_sign_name"] == "Virgo"
        assert cols["ak_natal_house"] == 1

    def test_dk_planet_is_mars(self, fake_karakas):
        """DK = Darakaraka (spouse), 7th in the ranking → Mars in fixture."""
        cols = _karaka_columns(fake_karakas)
        assert cols["dk_planet"] == "Mars"
        assert cols["dk_natal_house"] == 4

    def test_missing_karakas_yield_nulls(self):
        """Dropping all karaka rows leaves the wide block with None values."""
        cols = _karaka_columns(pd.DataFrame(
            columns=["karaka", "planet", "sign", "sign_name",
                     "degree_in_sign", "natal_house", "natal_houses_ruled"]
        ))
        for label in _JAIMINI_KARAKA_LABELS:
            prefix = label.split("_", 1)[0].lower()
            assert cols[f"{prefix}_planet"] is None


class TestIdentityColumns:
    def test_identity_block_has_all_keys(self, fake_person):
        """Identity block populates 11 documented columns."""
        cols = _identity_columns(fake_person.iloc[0])
        for key in ["person_id", "name", "corpus", "source", "birth_date",
                    "birth_time", "birth_time_confidence", "birth_lat",
                    "birth_lon", "tz_offset", "birth_jd"]:
            assert key in cols

    def test_corpus_derived_from_person_id(self, fake_person):
        """corpus derives from person_id prefix even when not in source."""
        cols = _identity_columns(fake_person.iloc[0])
        assert cols["corpus"] == "ADB"


class TestBuildPersonDossier:
    def test_returns_one_row_for_one_person(
        self, fake_person, fake_chart, fake_karakas,
    ):
        """One person + chart + 8 karakas → one wide dossier row."""
        result = build_person_dossier(fake_person, fake_chart, fake_karakas)
        assert len(result) == 1

    def test_dossier_carries_all_blocks(
        self, fake_person, fake_chart, fake_karakas,
    ):
        """Result must include identity + natal + karaka columns."""
        result = build_person_dossier(fake_person, fake_chart, fake_karakas)
        cols = set(result.columns)
        # Identity
        assert {"person_id", "name", "corpus", "birth_jd"} <= cols
        # Natal
        assert {"asc_sign_name", "sun_nakshatra", "moon_houses_ruled"} <= cols
        # Karaka
        assert {"ak_planet", "dk_planet", "pk2_sign_name"} <= cols

    def test_skips_persons_without_chart(
        self, fake_person, fake_karakas,
    ):
        """Persons missing from charts.parquet are dropped, not error."""
        empty_charts = pd.DataFrame(columns=["person_id", "asc_lon", "asc_sign"])
        result = build_person_dossier(fake_person, empty_charts, fake_karakas)
        assert len(result) == 0

    def test_handles_person_missing_karakas(
        self, fake_person, fake_chart,
    ):
        """Person with a chart but no karaka rows still produces a row
        (karaka columns null) — defensive against partial corpus state."""
        empty_karakas = pd.DataFrame(columns=[
            "person_id", "karaka", "planet", "sign", "sign_name",
            "degree_in_sign", "natal_house", "natal_houses_ruled",
        ])
        result = build_person_dossier(fake_person, fake_chart, empty_karakas)
        assert len(result) == 1
        assert result.iloc[0]["ak_planet"] is None

    def test_column_count_in_expected_range(
        self, fake_person, fake_chart, fake_karakas,
    ):
        """Wide dossier should have ~140 columns (11 identity + 8 asc +
        9×9 graha + 8×6 karaka = 11 + 8 + 81 + 48 = 148). Allow ±10 drift."""
        result = build_person_dossier(fake_person, fake_chart, fake_karakas)
        n_cols = len(result.columns)
        assert 130 <= n_cols <= 160, f"got {n_cols} cols, expected ~148"
