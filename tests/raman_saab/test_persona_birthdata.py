"""Birth-data parsing for the persona study — the step whose failures are silent.

A wrong birth time means a wrong ascendant, which makes every house-based answer in the
study noise, and nothing downstream ever complains: the run finishes and reports a
confident, meaningless number. So the parser is pinned against a committed page rather than
trusted, and each test names the specific way a real page misleads a naive reader.

No network and no ephemeris here — `parse_astrotheme` takes text, `standard_time_offset`
takes a record, and both are pure.
"""
from __future__ import annotations

import pathlib

import pytest

from tools.raman_saab.persona_birthdata import (
    ACCEPTED_RATINGS, BirthRecord, parse_astrotheme, standard_time_offset)

_FIX = pathlib.Path(__file__).resolve().parents[1] / "fixtures" / "astro_databank"


@pytest.fixture(scope="module")
def page() -> str:
    return (_FIX / "astrotheme_sample.html").read_text(encoding="utf-8")


class TestTheNativityIsReadFromTheBirthLine:
    def test_it_reads_the_stated_date_time_and_place(self, page):
        """Einstein is 1879-03-14 11:30 in Ulm — the value published on the page and the
        same one the repo's own golden ledger carries at NH.chart_45."""
        rec = parse_astrotheme(page, slug="Albert_Einstein")
        assert (rec.year, rec.month, rec.day) == (1879, 3, 14)
        assert (rec.hour, rec.minute) == (11, 30)
        assert rec.place == "Ulm (Germany)"

    def test_it_ignores_the_live_transits_widget(self, page):
        """Every person page opens with 'Fri. 28 Aug., 04:19 AM UT' — page furniture that
        is the FIRST clock-like string in the document. A time regex over the whole page
        reads it, and does so identically for every person, so the error is invisible."""
        rec = parse_astrotheme(page, slug="Albert_Einstein")
        assert (rec.hour, rec.minute) != (4, 19), "picked up the transits widget"

    def test_a_page_with_no_birth_time_is_refused(self):
        """A date without a time cannot be cast. It must leave the roster rather than
        enter it with a default hour that would look like a real one."""
        html = (_FIX / "astrotheme_no_time.html").read_text(encoding="utf-8")
        assert parse_astrotheme(html, slug="Oscar_Wilde") is None

    def test_an_empty_document_is_refused_rather_than_guessed(self):
        assert parse_astrotheme("", slug="nobody") is None

    def test_a_pm_birth_converts_to_a_24_hour_clock(self):
        """7:15 PM is hour 19, and noon and midnight are the two that trip a naive %12."""
        for text, expect in (("Born: Monday, June 2 , 1955, 7:15 PM In: Rome (Italy) Sun:", 19),
                             ("Born: Monday, June 2 , 1955, 12:00 PM In: Rome (Italy) Sun:", 12),
                             ("Born: Monday, June 2 , 1955, 12:30 AM In: Rome (Italy) Sun:", 0)):
            assert parse_astrotheme(text, slug="x").hour == expect, text


class TestTheRatingIsAGradeNotAPersonsName:
    def test_it_reads_the_token_before_reliability(self, page):
        rec = parse_astrotheme(page, slug="Albert_Einstein")
        assert rec.rodden == "AA"

    def test_the_contributor_line_is_not_mistaken_for_a_rating(self, page):
        """The page reads 'Contributor : Lois Rodden'. Searching for the word 'Rodden' to
        find the rating lands on a person's surname on every page that has one."""
        assert "Lois Rodden" in page
        assert parse_astrotheme(page, slug="Albert_Einstein").rodden in ACCEPTED_RATINGS

    def test_the_source_note_is_carried_for_the_record(self, page):
        """The provenance is reported in the results, so it has to be captured, not just
        gated on."""
        assert parse_astrotheme(page, slug="Albert_Einstein").source_note == \
            "birth certificate or birth record"

    def test_a_weak_rating_is_read_rather_than_dropped_at_parse_time(self):
        """Parsing records what the page says; ADMISSION is a separate decision, so that a
        dropped person can be reported as dropped instead of vanishing."""
        rec = parse_astrotheme(
            "Born: Monday, June 2 , 1955, 7:15 PM In: Rome (Italy) Sun: C Reliability",
            slug="x")
        assert rec.rodden == "C" and not rec.usable


class TestStandardTimeIsRequired:
    """`zoneinfo` answers a pre-standard-time date with the ZONE's local mean time — the
    reference city's, not the birth city's. For 1879 Ulm that is Berlin's +00:53:28 against
    Ulm's own +00:39:58: fourteen minutes, roughly 3.5 degrees of ascendant, on a study
    whose own rectification question turns on how close the ascendant sits to a cusp.
    """

    @staticmethod
    def _rec(year: int, place: str = "x") -> BirthRecord:
        return BirthRecord(slug="s", name="n", year=year, month=6, day=1, hour=9, minute=30,
                           place=place, rodden="AA", source_note="")

    def test_a_standard_offset_is_returned(self):
        assert standard_time_offset("America/Los_Angeles", self._rec(1926)) == -8.0

    def test_a_half_hour_zone_is_accepted(self):
        """India is +5.5 — a quarter-hour multiple, so the gate must not demand whole hours."""
        assert standard_time_offset("Asia/Kolkata", self._rec(1969)) == 5.5

    def test_a_local_mean_time_birth_is_refused(self):
        """1879 Ulm and 1907 Mexico City both predate their country's standard time."""
        assert standard_time_offset("Europe/Berlin", self._rec(1879)) is None
        assert standard_time_offset("America/Mexico_City", self._rec(1907)) is None

    def test_an_unknown_zone_is_refused_rather_than_raising(self):
        assert standard_time_offset("Mars/Olympus", self._rec(1960)) is None

    def test_usable_requires_every_part(self):
        """Rating, coordinates and offset — a record missing any one of them is not castable
        or not admissible, and either way must not reach the roster."""
        full = BirthRecord(slug="s", name="n", year=1955, month=2, day=24, hour=19, minute=15,
                           place="p", rodden="AA", source_note="", latitude=1.0,
                           longitude=2.0, zone="UTC", tz_offset=0.0)
        assert full.usable
        from dataclasses import replace
        assert not replace(full, rodden="C").usable
        assert not replace(full, latitude=None).usable
        assert not replace(full, tz_offset=None).usable
