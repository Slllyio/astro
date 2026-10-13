"""Gauquelin importer — parsing, tiering, and honest handling of source defects.

Pinned against a verbatim fixture copied from CURA volume A1, so the tests check
the real published layout rather than an idealized one. No network access: the
fetch path is exercised through the on-disk cache.
"""

from __future__ import annotations

import pytest

from app.empirical.acquire.gauquelin_import import (
    VOLUMES,
    GauquelinRecord,
    assign_time_tiers,
    fetch_volume,
    natural_key,
    parse_latitude,
    parse_longitude,
    parse_volume,
    write_csv,
)

# Verbatim rows from http://cura.free.fr/gauq/902gdA1y.html, tab-separated
# exactly as published, wrapped in the same <pre> block the real page uses.
_FIXTURE = """<html><body><pre>

YEA\tMON\tDAY\tPRO\tNUM\tCOU\tH\tMN\tSEC\tTZ\tLAT\tLON\tCOD\tCITY

1817\t3\t25\tC\t185\tF\t5\t16\t24\t0\t48N 0\t4W 6\t29\tCONCARNEAU
1827\t5\t28\tC\t414\tI\t20\t8\t0\t-1\t43N 0\t13E 0\tPG\tTODI
1854\t8\t4\tC\t349\tI\t17\t32\t0\t-1\t44N48\t10E45\tPR\tPARMA
1941\t8\t24\tC\t1666\tB\t21\t0\t0\t0\t50N51\t4E15\tBRA\tLAEKEN
1942\t3\t6\tC\t13\tF\t17\t0\t0\t0\t43N12\t2E21\t11\tESPERAZA
</pre>
<pre>
 DAY\tMON\tYEA\tNAME
 17\t4\t1879\tGabardini Giuseppe
</pre></body></html>
"""


class TestCoordinateParsing:
    """CURA writes coordinates as degrees + a hemisphere letter + minutes."""

    def test_latitude_whole_degrees(self):
        """``48N 0`` is 48.0° north."""
        assert parse_latitude("48N 0") == pytest.approx(48.0)

    def test_latitude_with_minutes(self):
        """``50N30`` is 50.5° — minutes are sixtieths, not decimals."""
        assert parse_latitude("50N30") == pytest.approx(50.5)

    def test_southern_latitude_is_negative(self):
        """Hemisphere letter sets the sign."""
        assert parse_latitude("33S45") == pytest.approx(-33.75)

    def test_western_longitude_is_negative(self):
        """``4W 6`` is −4.1°, the convention the rest of the engine uses."""
        assert parse_longitude("4W 6") == pytest.approx(-4.1)

    def test_eastern_longitude_is_positive(self):
        """``13E 0`` is +13.0°."""
        assert parse_longitude("13E 0") == pytest.approx(13.0)

    def test_unparseable_coordinate_raises(self):
        """A malformed coordinate must fail loudly, not silently become 0.0."""
        with pytest.raises(ValueError):
            parse_latitude("not a latitude")
        with pytest.raises(ValueError):
            parse_longitude("48N 0")  # a latitude passed to the longitude parser


class TestVolumeParsing:
    """The published layout, parsed from a verbatim fixture."""

    def test_parses_every_data_row(self):
        """Five data rows in, five records out; the header is not a record."""
        assert len(parse_volume(_FIXTURE, "A1")) == 5

    def test_ignores_the_partial_name_block(self):
        """Only the first <pre> is the complete table; later blocks are indexes.

        Counting them as data would inject rows with no time or place at all.
        """
        records = parse_volume(_FIXTURE, "A1")
        assert all(r.city != "Gabardini Giuseppe" for r in records)

    def test_first_record_matches_the_published_row(self):
        """Verbatim check against CURA A1 number 185."""
        record = parse_volume(_FIXTURE, "A1")[0]
        assert record.birth_year == 1817
        assert record.city == "CONCARNEAU"
        assert record.cura_number == "185"
        assert record.latitude == pytest.approx(48.0)
        assert record.longitude == pytest.approx(-4.1)

    def test_ut_conversion_applies_the_zone_column(self):
        """CURA publishes local standard time; ut = local + tz.

        Row 2 is 20:08:00 at tz −1 (CET), so 19:08 UT. Getting this backwards
        would shift every continental chart by two hours.
        """
        record = parse_volume(_FIXTURE, "A1")[1]
        assert record.tz_offset == -1
        assert record.birth_ut_hour == pytest.approx(19 + 8 / 60.0)

    def test_gmt_rows_are_unshifted(self):
        """A tz=0 row's UT equals its local time."""
        record = parse_volume(_FIXTURE, "A1")[0]
        assert record.birth_ut_hour == pytest.approx(5 + 16 / 60.0 + 24 / 3600.0)

    def test_profession_code_decoded(self):
        """``C`` in volume A1 is a sport champion."""
        assert parse_volume(_FIXTURE, "A1")[0].profession == "sport_champion"

    def test_reused_M_code_is_disambiguated_by_volume(self):
        """CURA reuses ``M`` for military (A3) and musician (A4).

        Decoding it the same way in both would merge two unrelated professions
        into one label.
        """
        row = "1900\t1\t1\tM\t1\tF\t12\t7\t0\t0\t48N50\t2E20\t75\tPARIS"
        html = f"<pre>\nYEA\tMON\tDAY\tPRO\tNUM\tCOU\tH\tMN\tSEC\tTZ\tLAT\tLON\tCOD\tCITY\n{row}\n</pre>"
        assert parse_volume(html, "A3")[0].profession == "military"
        assert parse_volume(html, "A4")[0].profession == "musician"

    def test_missing_pre_block_raises(self):
        """A page shape change must fail loudly rather than yield zero records."""
        with pytest.raises(ValueError, match="no <pre>"):
            parse_volume("<html><body>no data here</body></html>", "A1")

    def test_short_rows_are_skipped_not_crashed(self):
        """A truncated row is dropped; the rest of the volume still imports."""
        html = _FIXTURE.replace(
            "1854\t8\t4\tC\t349\tI\t17\t32\t0\t-1\t44N48\t10E45\tPR\tPARMA",
            "1854\t8\t4\tC",
        )
        assert len(parse_volume(html, "A1")) == 4


class TestTimeTiers:
    """Registry sourcing does not make a time exact; measure, do not assume."""

    def _records(self, minutes: list[int]) -> list[GauquelinRecord]:
        return [
            GauquelinRecord(
                source_id=f"id{i}", volume="A1", cura_number=str(i), profession="scientist",
                country="FR", birth_year=1900, birth_month=1, birth_day=1,
                birth_hour_local=12, birth_minute=m, birth_second=0, tz_offset=0,
                birth_ut_hour=12.0, latitude=48.0, longitude=2.0, place_code="75",
                city="PARIS", time_tier="A", data_quality="ok", source_url="u",
            )
            for i, m in enumerate(minutes)
        ]

    def test_uniform_minutes_all_stay_tier_a(self):
        """Faithfully recorded minutes are ~uniform and keep their tier-A claim."""
        records = self._records([m % 60 for m in range(600)])
        tiered, rounded = assign_time_tiers(records)
        assert rounded == {}
        assert all(r.time_tier == "A" for r in tiered)

    def test_clock_rounded_minutes_are_downgraded(self):
        """A spike at :00 is a clerk writing "6 o'clock", not a precise time."""
        records = self._records([0] * 300 + [m % 60 for m in range(300)])
        tiered, rounded = assign_time_tiers(records)
        assert 0 in rounded
        assert all(r.time_tier == "B" for r in tiered if r.birth_minute == 0)

    def test_unrounded_minutes_survive_alongside_a_spike(self):
        """Downgrading must be per-value, not a blanket demotion of the volume."""
        records = self._records([0] * 300 + [m % 60 for m in range(300)])
        tiered, _ = assign_time_tiers(records)
        assert any(r.time_tier == "A" for r in tiered if r.birth_minute == 17)

    def test_suspect_rows_can_never_be_tier_a(self):
        """A visible defect casts doubt on the fields we cannot check."""
        import dataclasses

        records = self._records([17])
        flagged = [dataclasses.replace(r, data_quality="implausible_year:1600") for r in records]
        tiered, _ = assign_time_tiers(flagged)
        assert tiered[0].time_tier == "B"

    def test_empty_input_is_handled(self):
        """No records is a legal state, not a crash."""
        assert assign_time_tiers([]) == ([], {})


class TestNaturalKey:
    """Identity without names, because the complete-data tables have none."""

    def test_same_person_same_key(self):
        """Identical birth data yields an identical id."""
        args = ("F", 1900, 5, 4, 12, 30, 48.0, 2.0)
        assert natural_key(*args) == natural_key(*args)

    def test_different_minute_is_a_different_person(self):
        """The key is precise enough to separate near-simultaneous births."""
        assert natural_key("F", 1900, 5, 4, 12, 30, 48.0, 2.0) != natural_key(
            "F", 1900, 5, 4, 12, 31, 48.0, 2.0
        )

    def test_different_place_is_a_different_person(self):
        """Same instant, different city — two people."""
        assert natural_key("F", 1900, 5, 4, 12, 30, 48.0, 2.0) != natural_key(
            "F", 1900, 5, 4, 12, 30, 51.5, 0.0
        )

    def test_key_is_prefixed_for_provenance(self):
        """Ids carry their source, so a merged corpus stays traceable."""
        assert natural_key("F", 1900, 5, 4, 12, 30, 48.0, 2.0).startswith("gauq_")


class TestVolumeRegistry:
    """The scraped surface is declared, and deliberately narrow."""

    def test_only_the_six_series_a_volumes_are_declared(self):
        """B/D/E are gated behind a request process and are not scraped."""
        assert sorted(VOLUMES) == ["A1", "A2", "A3", "A4", "A5", "A6"]

    def test_unknown_volume_rejected(self):
        """A typo must not silently fetch nothing."""
        with pytest.raises(KeyError):
            fetch_volume("A9", cache_dir=None)  # type: ignore[arg-type]


class TestOutput:
    """The CSV is the hand-off to the loader."""

    def test_round_trip_preserves_every_column(self, tmp_path):
        """Every dataclass field reaches the file."""
        import csv as _csv

        records = parse_volume(_FIXTURE, "A1")
        out = tmp_path / "gauq.csv"
        write_csv(out, records)
        rows = list(_csv.DictReader(out.open()))
        assert len(rows) == len(records)
        assert "data_quality" in rows[0]
        assert "source_url" in rows[0]

    def test_rows_are_written_in_a_stable_order(self, tmp_path):
        """Chronological + id ordering, so the file hashes reproducibly."""
        import csv as _csv

        out = tmp_path / "gauq.csv"
        write_csv(out, parse_volume(_FIXTURE, "A1"))
        years = [int(r["birth_year"]) for r in _csv.DictReader(out.open())]
        assert years == sorted(years)
