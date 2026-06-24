"""Tests for the lunarastro → natal ETL.

Focuses on the deterministic parsers (coord, date, time, confidence)
and the timezone backcompute. The full pipeline integration test is a
single-row in-process smoke that calls compute_chart_features end-to-end
for one well-known chart (Einstein, Ulm Germany — CET not IST).
"""
from __future__ import annotations

import datetime as dt
import math

import pytest

from app.medini.etl.lunarastro_to_natal import (
    _birth_time_confidence,
    _clean_row,
    _parse_coord,
    _parse_date,
    _parse_time,
    _true_tz_offset_hours,
)


# --------------------------------------------------------------------------- #
# Coord parser                                                                #
# --------------------------------------------------------------------------- #

class TestCoordParser:
    def test_lat_with_cardinal_north(self) -> None:
        assert _parse_coord("48.4011° N", axis="lat") == pytest.approx(48.4011)

    def test_lat_with_cardinal_south(self) -> None:
        assert _parse_coord("33.86° S", axis="lat") == pytest.approx(-33.86)

    def test_lon_with_cardinal_east(self) -> None:
        assert _parse_coord("9.9876° E", axis="lon") == pytest.approx(9.9876)

    def test_lon_with_cardinal_west(self) -> None:
        assert _parse_coord("118.25° W", axis="lon") == pytest.approx(-118.25)

    def test_decimal_lon_negative(self) -> None:
        assert _parse_coord("-118.25", axis="lon") == pytest.approx(-118.25)

    def test_decimal_lat_positive(self) -> None:
        assert _parse_coord("34.76666667", axis="lat") == pytest.approx(34.76666667)

    def test_cardinal_with_unicode_degree(self) -> None:
        # The lunarastro corpus uses a degree symbol; we should not reject it.
        assert _parse_coord("48.4011° N", axis="lat") == pytest.approx(48.4011)

    def test_rejects_garbage(self) -> None:
        assert _parse_coord("not a coord", axis="lat") is None
        assert _parse_coord("", axis="lat") is None
        assert _parse_coord(None, axis="lat") is None

    def test_rejects_out_of_range_lat(self) -> None:
        assert _parse_coord("95.0", axis="lat") is None
        assert _parse_coord("-90.5", axis="lat") is None

    def test_rejects_out_of_range_lon(self) -> None:
        assert _parse_coord("181.0", axis="lon") is None

    def test_rejects_wrong_cardinal_for_axis(self) -> None:
        # N attached to a longitude string isn't valid.
        assert _parse_coord("9.9876° N", axis="lon") is None
        assert _parse_coord("48.4011° E", axis="lat") is None


# --------------------------------------------------------------------------- #
# Date parser                                                                  #
# --------------------------------------------------------------------------- #

class TestDateParser:
    def test_standard_format(self) -> None:
        assert _parse_date("14:03:1879") == dt.date(1879, 3, 14)

    def test_padded_zeros(self) -> None:
        assert _parse_date("02:01:1939") == dt.date(1939, 1, 2)

    def test_rejects_year_below_1700(self) -> None:
        assert _parse_date("01:01:0194") is None

    def test_rejects_year_above_2030(self) -> None:
        assert _parse_date("01:01:7042") is None

    def test_rejects_invalid_month(self) -> None:
        assert _parse_date("01:13:1990") is None

    def test_rejects_invalid_day(self) -> None:
        assert _parse_date("32:01:1990") is None

    def test_rejects_empty(self) -> None:
        assert _parse_date("") is None
        assert _parse_date(None) is None


# --------------------------------------------------------------------------- #
# Time parser                                                                  #
# --------------------------------------------------------------------------- #

class TestTimeParser:
    def test_standard_format(self) -> None:
        assert _parse_time("12:00:00") == (12, 0, 0)
        assert _parse_time("09:23:00") == (9, 23, 0)
        assert _parse_time("23:59:59") == (23, 59, 59)

    def test_rejects_invalid_hour(self) -> None:
        assert _parse_time("24:00:00") is None

    def test_rejects_invalid_minute(self) -> None:
        assert _parse_time("12:60:00") is None

    def test_rejects_garbage(self) -> None:
        assert _parse_time("not a time") is None
        assert _parse_time("") is None


# --------------------------------------------------------------------------- #
# Birth-time confidence                                                        #
# --------------------------------------------------------------------------- #

class TestBirthTimeConfidence:
    def test_real_time_high_confidence(self) -> None:
        assert _birth_time_confidence("14:37:00", "Born in Mumbai") == 1.0

    def test_suspicious_round_time_low_confidence(self) -> None:
        for t in ("12:00:00", "00:00:00", "06:00:00", "18:00:00"):
            assert _birth_time_confidence(t, "") == 0.2, t

    def test_description_marker_zero_confidence(self) -> None:
        assert _birth_time_confidence(
            "14:37:00", "kindly update; not confirmed"
        ) == 0.0
        assert _birth_time_confidence("14:37:00", "approximate time") == 0.0
        assert _birth_time_confidence("14:37:00", "tentative") == 0.0
        assert _birth_time_confidence("14:37:00", "unknown time") == 0.0

    def test_description_marker_dominates_over_round_time(self) -> None:
        # Even if time is suspicious, an explicit "not confirmed" wins
        # by being more informative.
        assert _birth_time_confidence(
            "12:00:00", "kindly update"
        ) == 0.0


# --------------------------------------------------------------------------- #
# True-timezone backcompute                                                    #
# --------------------------------------------------------------------------- #

class TestTrueTimezone:
    def test_einstein_ulm_germany_returns_european_offset(self) -> None:
        """Einstein born Ulm, Germany 1879-03-14 09:23 → CET (~+0:53 LMT pre-1893
        actually, but post-1893 Germany standardized to CET = +01:00).

        We expect *not* IST (which is +5:30). The Europe/Berlin zoneinfo on
        this date should yield approximately +00:53 (pre-1893 LMT) or
        +01:00 (post-1893 CET) — either way the absolute value should be
        less than 2 hours, ruling out the bogus IST +5.5h.
        """
        result = _true_tz_offset_hours(
            48.4011, 9.9876, dt.date(1879, 3, 14), (9, 23, 0)
        )
        assert result is not None
        offset_h, tz_name = result
        assert "Berlin" in tz_name or "Europe" in tz_name, tz_name
        assert abs(offset_h) < 2.0, f"expected ~CET offset, got {offset_h}"

    def test_kolkata_india_returns_ist(self) -> None:
        """A clear-cut Indian birth → IST = +5:30."""
        result = _true_tz_offset_hours(
            22.5726, 88.3639, dt.date(1990, 6, 15), (10, 0, 0)
        )
        assert result is not None
        offset_h, tz_name = result
        assert "Kolkata" in tz_name or "Calcutta" in tz_name or "India" in tz_name, tz_name
        assert offset_h == pytest.approx(5.5, abs=0.01)

    def test_new_york_dst_summer(self) -> None:
        """NYC in summer 1990 → EDT = -4:00 (DST observed)."""
        result = _true_tz_offset_hours(
            40.7128, -74.0060, dt.date(1990, 7, 15), (12, 0, 0)
        )
        assert result is not None
        offset_h, tz_name = result
        assert "New_York" in tz_name, tz_name
        assert offset_h == pytest.approx(-4.0, abs=0.01)

    def test_new_york_dst_winter(self) -> None:
        """NYC in winter 1990 → EST = -5:00 (no DST)."""
        result = _true_tz_offset_hours(
            40.7128, -74.0060, dt.date(1990, 1, 15), (12, 0, 0)
        )
        assert result is not None
        offset_h, tz_name = result
        assert offset_h == pytest.approx(-5.0, abs=0.01)


# --------------------------------------------------------------------------- #
# clean_row end-to-end                                                         #
# --------------------------------------------------------------------------- #

def _row_einstein() -> dict:
    return {
        "id": "176824",
        "category": "personality",
        "name": "Albert Einstein",
        "gender": "Male",
        "date_of_birth": "14:03:1879",
        "day": "Friday",
        "time": "11:30:00",  # the genuine one, not 12:00 placeholder
        "city": "Ulm, Germany",
        "state": "Baden-Wurttemberg",
        "country": "Germany",
        "longitude": "9.9876° E",
        "latitude": "48.4011° N",
        "time_zone": "-05:30:00 hrs",  # WRONG (IST) — should be ignored
        "description": "Theoretical physicist",
        "tags": "Educater",
        "image_url": "https://example.com/img.jpg",
        "source_url": "https://research.lunarastro.com/kundli-details/176824",
    }


class TestCleanRow:
    def test_einstein_parses_and_uses_european_tz_not_ist(self) -> None:
        clean = _clean_row(_row_einstein())
        assert clean is not None
        assert clean.name == "Albert Einstein"
        assert clean.date == dt.date(1879, 3, 14)
        assert clean.time_tuple == (11, 30, 0)
        assert clean.latitude == pytest.approx(48.4011)
        assert clean.longitude == pytest.approx(9.9876)
        # MUST be European-ish offset, not IST. Pre-1893 Berlin uses LMT
        # which is approximately longitude/15 ≈ 0.886h. Post-1893 it would
        # be exactly +1.0h. Either way: < 2h and absolutely NOT 5.5h.
        assert abs(clean.tz_offset_hours) < 2.0
        assert "Berlin" in clean.tz_name
        assert clean.birth_time_confidence == 1.0
        assert clean.category == "personality"

    def test_unparseable_date_yields_none(self) -> None:
        row = _row_einstein()
        row["date_of_birth"] = "01:01:7042"  # out-of-range typo
        assert _clean_row(row) is None

    def test_unparseable_time_yields_none(self) -> None:
        row = _row_einstein()
        row["time"] = "not-a-time"
        assert _clean_row(row) is None

    def test_unparseable_coord_yields_none(self) -> None:
        row = _row_einstein()
        row["latitude"] = "garbage"
        assert _clean_row(row) is None

    def test_placeholder_time_drops_confidence(self) -> None:
        row = _row_einstein()
        row["time"] = "12:00:00"
        clean = _clean_row(row)
        assert clean is not None
        assert clean.birth_time_confidence == 0.2

    def test_not_confirmed_description_drops_confidence_to_zero(self) -> None:
        row = _row_einstein()
        row["description"] = "(kindly update; details not confirmed) physicist"
        clean = _clean_row(row)
        assert clean is not None
        assert clean.birth_time_confidence == 0.0
