"""Wikidata importer — coordinates, dates, and the tier-C contract.

The critical test is the coordinate swap: WKT writes ``Point(longitude latitude)``
while everything else in this repo is (lat, lon). Getting it backwards relocates
every birth on Earth without raising anything.
"""

from __future__ import annotations

import pytest

from app.empirical.acquire.wikidata_import import (
    LifeEvent,
    WikidataPerson,
    parse_point,
    parse_rows,
)


def _binding(qid="Q42", birth="+1900-05-04T00:00:00Z", death="+1970-03-11T00:00:00Z",
             coord="Point(2.3333 48.8666)"):
    return {
        "person": {"value": f"http://www.wikidata.org/entity/{qid}"},
        "birth": {"value": birth},
        "death": {"value": death},
        "coord": {"value": coord},
    }


def _payload(*bindings):
    return {"results": {"bindings": list(bindings)}}


class TestCoordinateOrder:
    """WKT is (lon lat). Everything else here is (lat, lon)."""

    def test_point_is_parsed_longitude_first(self):
        """Point(2.33 48.87) is Paris — 48.87 N, 2.33 E, not the reverse."""
        lat, lon = parse_point("Point(2.3333 48.8666)")
        assert lat == pytest.approx(48.8666)
        assert lon == pytest.approx(2.3333)

    def test_negative_coordinates_survive(self):
        """Western/southern hemispheres keep their sign."""
        lat, lon = parse_point("Point(-58.3816 -34.6037)")
        assert lat == pytest.approx(-34.6037)
        assert lon == pytest.approx(-58.3816)

    def test_out_of_range_latitude_rejected(self):
        """A swapped pair usually shows up as an impossible latitude."""
        with pytest.raises(ValueError, match="out of range"):
            parse_point("Point(48.8666 200.0)")

    def test_unparseable_point_raises(self):
        """Malformed geometry must fail loudly, not default to (0, 0)."""
        with pytest.raises(ValueError):
            parse_point("somewhere in France")


class TestParsing:
    """Rows become persons plus their dated events."""

    def test_person_and_event_are_both_produced(self):
        """A death date is a dated life event, not just a person attribute."""
        persons, events = parse_rows(_payload(_binding()))
        assert len(persons) == 1 and len(events) == 1

    def test_dates_are_split_correctly(self):
        """Wikidata ISO timestamps carry a leading '+'."""
        persons, events = parse_rows(_payload(_binding()))
        assert (persons[0].birth_year, persons[0].birth_month, persons[0].birth_day) == (1900, 5, 4)
        assert (events[0].event_year, events[0].event_month, events[0].event_day) == (1970, 3, 11)

    def test_age_is_computed(self):
        """Age at event drives the immortal-time and age controls."""
        _, events = parse_rows(_payload(_binding()))
        assert events[0].age_years == pytest.approx(69.85, abs=0.1)

    def test_event_is_day_precision(self):
        """Only day precision is admitted — a year cannot evidence a transit."""
        _, events = parse_rows(_payload(_binding()))
        assert events[0].date_precision == "day"

    def test_duplicate_qids_collapse(self):
        """One entity, one person, even if the query returns it twice."""
        persons, _ = parse_rows(_payload(_binding(), _binding()))
        assert len(persons) == 1

    def test_unparseable_row_is_skipped_not_fatal(self):
        """One bad row must not lose the other 14,000."""
        bad = _binding(qid="Q99", coord="not a point")
        persons, _ = parse_rows(_payload(bad, _binding()))
        assert len(persons) == 1


class TestTierContract:
    """Wikidata has no birth times, and the data must say so."""

    def test_every_person_is_tier_c(self):
        """Not 'unverified time' — no time at all."""
        persons, _ = parse_rows(_payload(_binding()))
        assert persons[0].time_tier == "C"

    def test_tier_c_is_excluded_by_house_requiring_tiers(self):
        """A test needing houses must not silently admit timeless charts."""
        from app.empirical.tournament.controls import check_tier

        assert not check_tier(["C"], "A").passed
        assert not check_tier(["C"], "AB").passed
        assert not check_tier(["C"], "ABS").passed

    def test_tier_c_is_admitted_only_by_ANY(self):
        """ANY exists for tests that genuinely need no birth time."""
        from app.empirical.tournament.controls import check_tier

        assert check_tier(["C"], "ANY").passed


class TestQualityFlags:
    """Impossible lives are flagged, not dropped."""

    def test_death_before_birth_is_flagged(self):
        """Wikidata contains such rows; they must not reach a cohort."""
        persons, _ = parse_rows(_payload(_binding(
            birth="+1970-01-01T00:00:00Z", death="+1900-01-01T00:00:00Z")))
        assert persons[0].data_quality.startswith("death_before_birth")

    def test_implausible_lifespan_is_flagged(self):
        """Beyond the documented human maximum is a data error."""
        persons, _ = parse_rows(_payload(_binding(
            birth="+1700-01-01T00:00:00Z", death="+1900-01-01T00:00:00Z")))
        assert persons[0].data_quality.startswith("implausible_lifespan")

    def test_ordinary_life_is_ok(self):
        """The common case carries no flag."""
        persons, _ = parse_rows(_payload(_binding()))
        assert persons[0].data_quality == "ok"


class TestProvenance:
    """Every row traces back to its source entity."""

    def test_qid_is_retained(self):
        """A claim must be checkable against the source."""
        persons, _ = parse_rows(_payload(_binding(qid="Q7186")))
        assert persons[0].qid == "Q7186"

    def test_person_id_is_deterministic_and_prefixed(self):
        """Stable across runs, and namespaced so corpora can merge."""
        a, _ = parse_rows(_payload(_binding(qid="Q7186")))
        b, _ = parse_rows(_payload(_binding(qid="Q7186")))
        assert a[0].person_id == b[0].person_id
        assert a[0].person_id.startswith("wd_")

    def test_event_names_its_source_property(self):
        """P570 is 'date of death' — the row says where it came from."""
        _, events = parse_rows(_payload(_binding()))
        assert events[0].source == "wikidata:P570"
