"""Unit tests for the pure helpers in astrocrm_geocode_importer.

Only the dependency-free parsing/normalization helpers are tested here so the
suite stays fast and doesn't require geonamescache/timezonefinder to be
installed (those are exercised by the importer's integration run).
"""
from __future__ import annotations

from app.medini.etl.astrocrm_geocode_importer import (
    _normalize_city,
    _parse_date,
    _parse_time,
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
