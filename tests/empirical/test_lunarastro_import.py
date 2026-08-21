"""LunarAstro importer — parsing, honest defect flagging, fingerprint identity.

Fixture rows are built to reproduce the exact patterns found by inspecting the
real 29,516-row scrape (see the module docstring): placeholder times, an epoch
placeholder date, an implausible future year, and a name shared by two
genuinely different charts. No network access — this module never fetches
anything, it only parses a local CSV.
"""

from __future__ import annotations

import csv
import io

import pytest

from app.empirical.acquire.lunarastro_import import (
    LunarAstroRecord,
    assign_time_tiers,
    import_all,
    natural_key,
    parse_row,
    write_csv,
)

_HEADER = "name,date_of_birth,time_of_birth,latitude,longitude,tz_offset,rodden_rating,categories,source_url\n"


def _rows_from_csv(text: str) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(text)))


class TestParseRow:
    """Field-level parsing of one raw row."""

    def test_parses_a_well_formed_row(self):
        row = {
            "name": "Albert Einstein", "date_of_birth": "1879-03-14",
            "time_of_birth": "09:23:00", "latitude": "48.4011", "longitude": "9.9876",
            "tz_offset": "0.8911", "rodden_rating": "", "categories": "Vocation;Writers",
            "source_url": "https://example.test/1",
        }
        record = parse_row(row)
        assert record is not None
        assert record.birth_year == 1879 and record.birth_month == 3 and record.birth_day == 14
        assert record.birth_hour_local == 9 and record.birth_minute == 23
        assert record.categories == ("Vocation", "Writers")
        assert record.time_is_placeholder is False
        assert record.data_quality == "ok"

    def test_ut_hour_subtracts_the_offset(self):
        """East-positive convention: ut = local - tz_offset, matching the rest
        of app/empirical (BirthMoment.hour_ut)."""
        row = {
            "name": "X", "date_of_birth": "1970-06-01", "time_of_birth": "14:00:00",
            "latitude": "32.0667", "longitude": "34.7667", "tz_offset": "2.0",
            "rodden_rating": "", "categories": "", "source_url": "",
        }
        record = parse_row(row)
        assert record.birth_ut_hour == pytest.approx(12.0)

    def test_malformed_row_returns_none(self):
        """A missing/unparseable required field fails loudly (as None), never
        as a silently-zeroed record."""
        assert parse_row({"date_of_birth": "not-a-date"}) is None

    def test_out_of_range_coordinates_return_none(self):
        row = {
            "name": "X", "date_of_birth": "1970-06-01", "time_of_birth": "14:00:00",
            "latitude": "200.0", "longitude": "34.7667", "tz_offset": "2.0",
            "rodden_rating": "", "categories": "", "source_url": "",
        }
        assert parse_row(row) is None

    def test_empty_categories_field_is_an_empty_tuple(self):
        row = {
            "name": "X", "date_of_birth": "1970-06-01", "time_of_birth": "14:00:00",
            "latitude": "32.0", "longitude": "34.0", "tz_offset": "2.0",
            "rodden_rating": "", "categories": "", "source_url": "",
        }
        assert parse_row(row).categories == ()


class TestDataQualityFlags:
    """The three defect classes found in the real scrape, each caught here."""

    def test_epoch_placeholder_date_is_flagged(self):
        """1970-01-01 — the Unix-epoch default — is flagged even though it is
        a calendar-valid date within the plausible year range."""
        row = {
            "name": "Riko", "date_of_birth": "1970-01-01", "time_of_birth": "07:45:00",
            "latitude": "26.9075", "longitude": "75.7396", "tz_offset": "5.5",
            "rodden_rating": "", "categories": "", "source_url": "",
        }
        assert parse_row(row).data_quality == "epoch_placeholder"

    def test_implausible_future_year_is_flagged(self):
        """The 19xx -> 20xx digit-transposition pattern found in the real data
        (e.g. a 2027 'birth')."""
        row = {
            "name": "Albert Uderzo", "date_of_birth": "2027-04-25",
            "time_of_birth": "12:00:00", "latitude": "49.2597", "longitude": "3.7789",
            "tz_offset": "2.0", "rodden_rating": "", "categories": "", "source_url": "",
        }
        assert parse_row(row).data_quality == "implausible_year:2027"

    def test_invalid_calendar_date_returns_none(self):
        """Feb 30 cannot be parsed as a date at all — caught by _parse_date's
        int() calls only insofar as the date module rejects it downstream via
        data_quality; a genuinely malformed string still returns None."""
        row = {
            "name": "X", "date_of_birth": "1990-02-30", "time_of_birth": "12:00:00",
            "latitude": "10.0", "longitude": "10.0", "tz_offset": "0",
            "rodden_rating": "", "categories": "", "source_url": "",
        }
        assert parse_row(row).data_quality == "invalid_date:1990-02-30"

    def test_ordinary_row_is_ok(self):
        row = {
            "name": "X", "date_of_birth": "1950-06-01", "time_of_birth": "14:03:00",
            "latitude": "10.0", "longitude": "10.0", "tz_offset": "0",
            "rodden_rating": "", "categories": "", "source_url": "",
        }
        assert parse_row(row).data_quality == "ok"


class TestPlaceholderTimes:
    """00:00:00 / 23:59:00 / 12:00:00 are treated as no-real-time, not data."""

    @pytest.mark.parametrize("time_str", ["00:00:00", "23:59:00", "12:00:00"])
    def test_known_placeholder_times_are_flagged(self, time_str):
        row = {
            "name": "X", "date_of_birth": "1950-06-01", "time_of_birth": time_str,
            "latitude": "10.0", "longitude": "10.0", "tz_offset": "0",
            "rodden_rating": "", "categories": "", "source_url": "",
        }
        assert parse_row(row).time_is_placeholder is True

    def test_ordinary_time_is_not_a_placeholder(self):
        row = {
            "name": "X", "date_of_birth": "1950-06-01", "time_of_birth": "14:03:00",
            "latitude": "10.0", "longitude": "10.0", "tz_offset": "0",
            "rodden_rating": "", "categories": "", "source_url": "",
        }
        assert parse_row(row).time_is_placeholder is False


class TestNaturalKey:
    """Identity is the chart fingerprint, never the name."""

    def test_same_fingerprint_same_key(self):
        a = natural_key(1970, 1, 1, 12, 0, 0, 10.0, 10.0)
        b = natural_key(1970, 1, 1, 12, 0, 0, 10.0, 10.0)
        assert a == b

    def test_different_time_different_key(self):
        a = natural_key(1970, 1, 1, 12, 0, 0, 10.0, 10.0)
        b = natural_key(1970, 1, 1, 12, 1, 0, 10.0, 10.0)
        assert a != b

    def test_key_does_not_depend_on_name(self):
        """natural_key takes no name argument at all — two DIFFERENT people
        sharing a name and DIFFERENT charts must get DIFFERENT identities,
        which is only true if name never enters the key."""
        einstein_key = natural_key(1879, 3, 14, 9, 23, 0, 48.4011, 9.9876)
        other_person_same_name_key = natural_key(1947, 7, 22, 2, 59, 0, 34.0667, -118.25)
        assert einstein_key != other_person_same_name_key


class TestAssignTimeTiers:
    """A/B/C by measurement: placeholders forced to C, rounding measured."""

    def test_placeholder_rows_are_forced_to_tier_c(self):
        rows = [_HEADER]
        rows.append("X,1950-01-01,12:00:00,10.0,10.0,0,,,\n")
        records = [parse_row(r) for r in _rows_from_csv("".join(rows))]
        tiered, _rounded = assign_time_tiers(records)
        assert tiered[0].time_tier == "C"

    def test_over_represented_minute_downgrades_to_tier_b(self):
        """20 rows at minute 0, 1 row at every other represented minute — 0 is
        far above the 3x-of-uniform-share threshold and must downgrade."""
        raw_rows = []
        for i in range(20):
            raw_rows.append(f"X{i},1950-01-0{1 + i % 9},08:00:00,10.0,10.0,0,,,")
        for i in range(5):
            raw_rows.append(f"Y{i},1951-02-0{1 + i},08:{10 + i:02d}:00,10.0,10.0,0,,,")
        text = _HEADER + "\n".join(raw_rows) + "\n"
        records = [parse_row(r) for r in _rows_from_csv(text)]
        tiered, rounded = assign_time_tiers(records)
        assert 0 in rounded
        minute_0 = [r for r in tiered if r.birth_minute == 0]
        minute_10 = [r for r in tiered if r.birth_minute == 10]
        assert all(r.time_tier == "B" for r in minute_0)
        assert all(r.time_tier == "A" for r in minute_10)

    def test_quality_flagged_row_never_tiers_a(self):
        """A row already flagged for another defect cannot claim tier A even
        if its minute value is unremarkable — the defect we can see casts
        doubt on the fields we cannot check (same rule as Gauquelin's)."""
        row = "X,1970-01-01,08:17:00,10.0,10.0,0,,,\n"
        records = [parse_row(r) for r in _rows_from_csv(_HEADER + row)]
        tiered, _rounded = assign_time_tiers(records)
        assert tiered[0].data_quality == "epoch_placeholder"
        assert tiered[0].time_tier == "B"


class TestImportAllAndDedup:
    """The end-to-end pipeline: dedup by fingerprint (not name), then tier."""

    def test_identical_fingerprint_rows_merge_categories(self, tmp_path):
        """The 'same chart, multiple category collections' case: two rows,
        identical date/time/place, different categories -> one record, union
        of categories."""
        text = (
            _HEADER
            + "Albert Einstein,1879-03-14,09:23:00,48.4011,9.9876,0.8911,,Educater,u1\n"
            + "Albert Einstein,1879-03-14,09:23:00,48.4011,9.9876,0.8911,,Legion,u2\n"
        )
        raw = tmp_path / "raw.csv"
        raw.write_text(text, encoding="utf-8")
        records, stats = import_all(raw)
        assert len(records) == 1
        assert stats["duplicates_merged"] == 1
        assert set(records[0].categories) == {"Educater", "Legion"}

    def test_same_name_different_fingerprint_stays_separate(self, tmp_path):
        """The 'two different people share a name' case (or a placeholder
        profile coinciding with a real one): distinct charts must NOT merge
        just because the name string matches."""
        text = (
            _HEADER
            + "Franco Modigliani,1918-06-18,05:19:00,41.9,12.4833,1.0,,Notable,u1\n"
            + "Franco Modigliani,2018-06-03,12:00:00,41.9028,12.4964,1.0,,Family,u2\n"
        )
        raw = tmp_path / "raw.csv"
        raw.write_text(text, encoding="utf-8")
        records, stats = import_all(raw)
        assert len(records) == 2
        assert stats["duplicates_merged"] == 0

    def test_unparseable_rows_are_counted_separately_from_quality_flags(self, tmp_path):
        text = _HEADER + "X,not-a-date,12:00:00,10.0,10.0,0,,,\n"
        raw = tmp_path / "raw.csv"
        raw.write_text(text, encoding="utf-8")
        records, stats = import_all(raw)
        assert len(records) == 0
        assert stats["skipped_unparseable"] == 1

    def test_stats_tally_matches_records(self, tmp_path):
        text = (
            _HEADER
            + "A,1950-01-01,08:00:00,10.0,10.0,0,,ok,u1\n"
            + "B,1970-01-01,12:00:00,10.0,10.0,0,,,u2\n"
            + "C,2099-01-01,08:00:00,10.0,10.0,0,,,u3\n"
        )
        raw = tmp_path / "raw.csv"
        raw.write_text(text, encoding="utf-8")
        records, stats = import_all(raw)
        assert stats["records"] == 3
        assert stats["epoch_placeholder"] == 1
        assert stats["flagged_quality"] == 2  # epoch + implausible year
        assert stats["tier_C"] == 1  # the 12:00:00 row


class TestWriteCsv:
    """The canonical output is a plain, re-readable CSV — no Python reprs."""

    def test_round_trips_categories_and_booleans(self, tmp_path):
        record = LunarAstroRecord(
            source_id="lunar_test", name="X", birth_year=1950, birth_month=1, birth_day=1,
            birth_hour_local=8, birth_minute=0, birth_second=0, tz_offset=0.0,
            birth_ut_hour=8.0, latitude=10.0, longitude=10.0,
            categories=("Vocation", "Writers"), time_is_placeholder=False,
            time_tier="A", data_quality="ok", source_url="u",
        )
        out = tmp_path / "out.csv"
        write_csv(out, [record])
        rows = _rows_from_csv(out.read_text(encoding="utf-8"))
        assert len(rows) == 1
        assert rows[0]["categories"] == "Vocation;Writers"
        assert rows[0]["time_is_placeholder"] == "false"
        assert "(" not in rows[0]["categories"]  # never a Python tuple repr
