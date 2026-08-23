"""The HTJAH extractor must not invent charts — it must reproduce Raman's own arithmetic.

`extract_htjah_goldens` fresh-casts worked nativities out of OCR'd birth lines, which is exactly
the operation that can silently corrupt the fidelity measurement: a mis-read hour or a dropped
coordinate yields a WRONG chart, and a wrong chart scored against Raman's verdict is worse than
no chart at all. The tool's whole safety argument is the gate — a candidate is emitted ONLY when
the cast chart reproduces the Vimshottari balance Raman printed for that nativity, a value fixed
by the Moon's longitude and therefore an independent function of date, time and place.

These tests pin the two halves of that argument: the coordinate grammar the scans actually use
(both minute orders, and the run-together ``77 E35`` form that has no word boundary after the
hemisphere letter), and the gate's willingness to REJECT a chart whose birth line has been
corrupted the way the scans corrupt them.
"""
from __future__ import annotations

import pytest

from corpus_presence import needs_corpus

from tools.raman_saab import extract_htjah_goldens as ex


class TestCoordinateGrammar:
    def test_hemisphere_letter_between_degrees_and_minutes(self):
        """Raman's dominant form: '20 N 56, 75 E 55' — the letter splits degrees from minutes."""
        birth, _ = ex._parse_birth("Born 7-4-1893 at 9-31 a.m. (L.M.T.) at 20 N 56, 75 E 55.")
        assert birth is not None
        assert birth["lat"] == pytest.approx(20 + 56 / 60, abs=1e-3)
        assert birth["lon"] == pytest.approx(75 + 55 / 60, abs=1e-3)

    def test_minutes_run_into_the_hemisphere_letter(self):
        """'77 E35' has NO word boundary between 'E' and '3'; a \\b there loses the longitude
        entirely, which is what silently halved the extractor's yield before this was fixed."""
        birth, _ = ex._parse_birth("Born 16-8-1937 at 8-31 a.m. (I.S.T)at 13° N. \n77 E35.")
        assert birth is not None
        assert birth["lon"] == pytest.approx(77 + 35 / 60, abs=1e-3)

    def test_minutes_before_the_hemisphere_letter(self):
        """The other order also occurs and must not regress when the first is supported."""
        birth, _ = ex._parse_birth("Born 1-1-1900 at 6 a.m. (I.S.T.) at 13° 30' N, 77° 45' E.")
        assert birth is not None
        assert birth["lat"] == pytest.approx(13.5, abs=1e-3)
        assert birth["lon"] == pytest.approx(77.75, abs=1e-3)

    def test_western_hemisphere_is_signed(self):
        birth, _ = ex._parse_birth("Born 14-4-1857 at 1-45 p.m. (L.M.T.) at 51 N 30, 0 W 05.")
        assert birth is not None
        assert birth["lon"] < 0

    def test_meridiem_converts_to_24_hour(self):
        birth, _ = ex._parse_birth("Born 8-8-1912 at 7-35 p.m. (I.S.T.) at 13 N 0, 77 E 0.")
        assert birth is not None and birth["dt"].endswith("T19:35:00")


class TestRefusals:
    """Every one of these is an OCR corruption observed in the vendored scans. The tool must
    return None rather than repair a value it cannot know."""

    def test_ocr_mangled_year_is_refused(self):
        birth, why = ex._parse_birth("Born 24-3-7883 at 6 a.m. (L.M.T) at 13 N 0, 77 E 35.")
        assert birth is None and "year" in why[0]

    def test_missing_zone_is_hypothesised_and_loudly_flagged(self):
        """A zone the printing omits is HYPOTHESISED as L.M.T. rather than refused — but the
        hypothesis is never silent, and it is never trusted on its own. It carries a flag, and
        the dasha gate adjudicates it: a wrong zone moves the Moon, the printed balance fails to
        reproduce, and the record is dropped. Only `verified` candidates are ever emitted, so a
        hypothesised zone cannot reach the corpus unchecked."""
        birth, notes = ex._parse_birth("Born 3-8-1942 at 7-23 a.m. at 13 N 0, 77 E 35.")
        assert birth is not None
        assert any("ZONE ABSENT" in n for n in notes)

    def test_a_hypothesised_zone_still_has_to_pass_the_gate(self):
        """The safety of hypothesising rests entirely on the gate being independent, so pin it:
        an unverifiable candidate never reaches 'verified'."""
        c = ex.Candidate(book="HTJAH-II", chart_no=999, line=1)
        c.birth, _ = ex._parse_birth("Born 3-8-1942 at 7-23 a.m. at 13 N 0, 77 E 35.")
        c.printed_lord, c.printed_years = "Saturn", 5.0      # deliberately not this chart's
        ex.gate(c, tolerance_days=30.0)
        assert c.status == "gate-failed"

    def test_truncated_longitude_is_refused(self):
        birth, why = ex._parse_birth("Born 3-8-1942 at 7-23 a.m. (I.S.T.) at 13 N 0.")
        assert birth is None and "longitude" in why[0]

    def test_lmt_zone_is_derived_from_longitude_and_flagged(self):
        birth, notes = ex._parse_birth("Born 7-4-1893 at 9-31 a.m. (L.M.T.) at 20 N 56, 75 E 55.")
        assert birth is not None
        assert birth["tz"] == pytest.approx(75.9167 / 15, abs=1e-3)
        assert any("L.M.T." in n for n in notes)


class TestPrintedBalance:
    def test_parses_lord_and_duration(self):
        lord, years = ex._parse_balance("Balance of Ketu Dasa at birth : 6 years, 4 months and 4 days.")
        assert lord == "Ketu"
        assert years == pytest.approx(6 + 4 / 12 + 4 / 365.2425, abs=1e-3)

    def test_possessive_form_is_accepted(self):
        """The scans print both 'Jupiter Dasa' and “Jupiter's Dasa”."""
        lord, _ = ex._parse_balance("Balance of Jupiter's Dasa at birth: 1 year, 6 months and 22 days.")
        assert lord == "Jupiter"

    def test_non_lord_word_is_rejected(self):
        assert ex._parse_balance("Balance of Something Dasa at birth: 2 years.") == (None, None)


class TestGate:
    def test_chart_20_reproduces_ramans_printed_balance(self):
        """HTJAH-II Chart No. 20 (HTJAH-II:2002): Raman prints 'Balance of Ketu Dasa at birth :
        6 years, 4 months and 4 days'. Casting his stated birth data must land on Ketu and on
        that duration — this is the tool's entire claim to trustworthiness, so it is pinned."""
        c = ex.Candidate(book="HTJAH-II", chart_no=20, line=2002)
        c.birth = {"dt": "1893-04-07T09:31:00", "tz": 75.9167 / 15, "lat": 20.9333, "lon": 75.9167}
        c.printed_lord, c.printed_years = "Ketu", 6 + 4 / 12 + 4 / 365.2425
        ex.gate(c, tolerance_days=30.0)
        assert c.status == "verified", c.reason
        assert c.cast_lord == "Ketu"
        assert abs(c.cast_years - c.printed_years) * 365.2425 < 10

    def test_a_wrong_birth_hour_fails_the_gate(self):
        """The gate has to actually bite. Same chart, birth time moved twelve hours — the Moon
        moves ~6°, the balance shifts by well over a year, and the record must be rejected."""
        c = ex.Candidate(book="HTJAH-II", chart_no=20, line=2002)
        c.birth = {"dt": "1893-04-07T21:31:00", "tz": 75.9167 / 15, "lat": 20.9333, "lon": 75.9167}
        c.printed_lord, c.printed_years = "Ketu", 6 + 4 / 12 + 4 / 365.2425
        ex.gate(c, tolerance_days=30.0)
        assert c.status == "gate-failed", c.reason

    def test_a_chart_without_a_printed_balance_is_never_verified(self):
        """No independent check exists for these, so they may be reported but never emitted."""
        c = ex.Candidate(book="HTJAH-I", chart_no=1, line=1)
        c.birth = {"dt": "1900-01-01T06:00:00", "tz": 5.5, "lat": 13.0, "lon": 77.0}
        ex.gate(c, tolerance_days=30.0)
        assert c.status == "ungated"


@needs_corpus
class TestAgainstTheVendoredBooks:
    def test_extraction_finds_charts_and_gates_a_subset(self):
        """End-to-end over the real scans: the tool must find worked charts, and the verified
        set must be a strict subset of what it found — a gate that passes everything is broken."""
        cands = [ex.gate(c, 30.0) for c in ex.collect("HTJAH-II", ex._BOOKS["HTJAH-II"])]
        assert len(cands) > 100, f"only {len(cands)} chart presentations found"
        verified = [c for c in cands if c.status == "verified"]
        assert 0 < len(verified) < len(cands)

    def test_every_emitted_record_is_draft_and_carries_its_provenance(self):
        """A DRAFT is not scored by the accuracy ratchet, so extraction can never inflate it.
        Each record must also carry the printed-vs-cast balance that justified emitting it."""
        cands = [ex.gate(c, 30.0) for c in ex.collect("HTJAH-II", ex._BOOKS["HTJAH-II"])]
        for c in (x for x in cands if x.status == "verified"):
            rec = ex.to_record(c)
            assert rec["expected_verdicts"] == {}, "the tool must not author verdicts"
            prov = rec["_extraction"]
            assert prov["printed_balance"]["lord"] == prov["cast_balance"]["lord"]
            assert rec["birth"] and rec["citations"]
