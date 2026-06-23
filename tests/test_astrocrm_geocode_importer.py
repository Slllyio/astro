"""Unit tests for the pure helpers in astrocrm_geocode_importer.

Only the dependency-free parsing/normalization helpers are tested here so the
suite stays fast and doesn't require geonamescache/timezonefinder to be
installed (those are exercised by the importer's integration run).
"""
from __future__ import annotations

from app.medini.etl.astrocrm_geocode_importer import (
    _City,
    _extract_hints,
    _normalize_city,
    _parse_date,
    _parse_time,
    _resolve_city,
)


class TestNormalizeCity:
    def test_strips_parenthetical(self) -> None:
        assert _normalize_city("Aba (Sichuan)") == "aba"

    def test_keeps_part_before_comma(self) -> None:
        assert _normalize_city("New York, NY, USA") == "new york"

    def test_lowercases_and_strips_accents(self) -> None:
        assert _normalize_city("München") == "munchen"

    def test_multiword_city_preserved(self) -> None:
        assert _normalize_city("Thonon les Bains") == "thonon les bains"


class TestParseDate:
    def test_slash_format(self) -> None:
        assert _parse_date("1943/09/06") == "1943-09-06"

    def test_iso_passthrough(self) -> None:
        assert _parse_date("2015-11-14") == "2015-11-14"

    def test_empty_is_none(self) -> None:
        assert _parse_date("") is None
        assert _parse_date("   ") is None

    def test_garbage_is_none(self) -> None:
        assert _parse_date("not-a-date") is None
        assert _parse_date("1943/13/40") is None  # invalid month/day


class TestParseTime:
    def test_hh_mm(self) -> None:
        assert _parse_time("18:06") == "18:06:00"

    def test_hh_mm_ss(self) -> None:
        assert _parse_time("09:27:15") == "09:27:15"

    def test_empty_is_none(self) -> None:
        assert _parse_time("") is None

    def test_out_of_range_is_none(self) -> None:
        assert _parse_time("25:00") is None
        assert _parse_time("12:99") is None


class TestExtractHints:
    def test_parenthetical(self) -> None:
        assert _extract_hints("Aba (Sichuan)") == ["sichuan"]

    def test_comma_tail(self) -> None:
        assert _extract_hints("New York, NY, USA") == ["ny", "usa"]

    def test_country(self) -> None:
        assert _extract_hints("Poitiers, France") == ["france"]

    def test_bare_city_no_hints(self) -> None:
        assert _extract_hints("Strasbourg") == []


def _c(lat, lon, pop, cc, admin1="") -> _City:
    return _City(lat=lat, lon=lon, population=pop, countrycode=cc,
                 admin1=admin1, tz_name="UTC")


class TestResolveCity:
    INDEX = {
        "springfield": [
            _c(39.80, -89.64, 116250, "US", "IL"),   # Springfield, Illinois
            _c(37.21, -93.29, 169176, "US", "MO"),   # Springfield, Missouri (largest)
        ],
        "paris": [
            _c(48.85, 2.35, 2138551, "FR"),          # Paris, France (largest)
            _c(33.66, -95.55, 25171, "US", "TX"),    # Paris, Texas
        ],
    }
    COUNTRIES = {"france": "FR", "fr": "FR", "usa": "US", "us": "US"}

    def test_bare_picks_max_population(self) -> None:
        c = _resolve_city("paris", [], self.INDEX, self.COUNTRIES)
        assert c is not None and c.countrycode == "FR"

    def test_country_hint_overrides_population(self) -> None:
        c = _resolve_city("paris", ["usa"], self.INDEX, self.COUNTRIES)
        assert c is not None and c.countrycode == "US" and c.admin1 == "TX"

    def test_us_state_hint_disambiguates(self) -> None:
        c = _resolve_city("springfield", ["il"], self.INDEX, self.COUNTRIES)
        assert c is not None and c.admin1 == "IL"

    def test_unknown_city_returns_none(self) -> None:
        assert _resolve_city("atlantis", [], self.INDEX, self.COUNTRIES) is None
