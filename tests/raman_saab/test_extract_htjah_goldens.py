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
        ex.gate(c)
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
        ex.gate(c)
        assert c.status == "verified", c.reason
        assert c.cast_lord == "Ketu"
        assert abs(c.cast_years - c.printed_years) * 365.2425 < 10

    def test_a_wrong_birth_hour_fails_the_gate(self):
        """The gate has to actually bite. Same chart, birth time moved twelve hours — the Moon
        moves ~6°, the balance shifts by well over a year, and the record must be rejected."""
        c = ex.Candidate(book="HTJAH-II", chart_no=20, line=2002)
        c.birth = {"dt": "1893-04-07T21:31:00", "tz": 75.9167 / 15, "lat": 20.9333, "lon": 75.9167}
        c.printed_lord, c.printed_years = "Ketu", 6 + 4 / 12 + 4 / 365.2425
        ex.gate(c)
        assert c.status == "gate-failed", c.reason

    def test_a_chart_without_a_printed_balance_is_never_verified(self):
        """No independent check exists for these, so they may be reported but never emitted."""
        c = ex.Candidate(book="HTJAH-I", chart_no=1, line=1)
        c.birth = {"dt": "1900-01-01T06:00:00", "tz": 5.5, "lat": 13.0, "lon": 77.0}
        ex.gate(c)
        assert c.status == "ungated"


@needs_corpus
class TestAgainstTheVendoredBooks:
    def test_extraction_finds_charts_and_gates_a_subset(self):
        """End-to-end over the real scans: the tool must find worked charts, and the verified
        set must be a strict subset of what it found — a gate that passes everything is broken."""
        cands = [ex.gate(c) for c in ex.collect("HTJAH-II", ex._BOOKS["HTJAH-II"])]
        assert len(cands) > 100, f"only {len(cands)} chart presentations found"
        verified = [c for c in cands if c.status == "verified"]
        assert 0 < len(verified) < len(cands)

    def test_every_emitted_record_is_draft_and_carries_its_provenance(self):
        """The tool MAY now author a verdict — read off Raman's own Conclusion paragraph by the
        existing conservative classifier — but every one must be DRAFT, and only CONFIRMED
        verdicts are scored, so extraction still cannot inflate fidelity. Each record must also
        carry the printed-vs-cast balance that justified emitting it, and the prose that
        justified the verdict, so a reviewer can promote it without reopening the book."""
        cands = [ex.gate(c) for c in ex.collect("HTJAH-II", ex._BOOKS["HTJAH-II"])]
        for c in (x for x in cands if x.status == "verified"):
            rec = ex.to_record(c)
            for tag, v in rec["expected_verdicts"].items():
                assert v["verdict_review"] == "DRAFT", f"{tag} must not be asserted"
                assert v["verdict_prose"], f"{tag} must carry the prose it was read from"
                assert 1 <= int(tag[1:]) <= 12
            prov = rec["_extraction"]
            assert prov["printed_balance"]["lord"] == prov["cast_balance"]["lord"]
            assert rec["birth"] and rec["citations"]

    def test_the_longevity_house_is_never_given_a_verdict(self):
        """H8's primary signification is `longevity`, which the judge deliberately defers to the
        ayurdaya pre-pass under LONGEVITY_GUARD. A verdict there would measure the guard, not the
        doctrine, so H8 charts are extracted without one."""
        c = ex.Candidate(book="HTJAH-II", chart_no=1, line=1, house=8)
        c.conclusion = "The native died early; the eighth house is afflicted."
        assert ex.draft_verdict(c) == {}


class TestVerdictExtraction:
    def test_verdict_is_draft_and_read_from_the_conclusion(self):
        c = ex.Candidate(book="HTJAH-I", chart_no=9, line=1, house=1)
        c.conclusion = "The native rose to great eminence and enjoyed high position and fame."
        v = ex.draft_verdict(c)
        assert list(v) == ["H1"]
        assert v["H1"]["verdict"] == "favourable"
        assert v["H1"]["verdict_review"] == "DRAFT"
        assert v["H1"]["signification"] == "self"

    def test_no_house_means_no_verdict(self):
        """A chart printed before its chapter heading cannot be attributed, and an unattributed
        verdict would be assigned to the wrong matter."""
        c = ex.Candidate(book="HTJAH-I", chart_no=2, line=1, house=None)
        c.conclusion = "The native was fortunate and prosperous."
        assert ex.draft_verdict(c) == {}


class TestHouseAttribution:
    def test_chapter_heading_sets_the_house(self):
        assert ex.house_of_chapter("XI. Concerning the Seventh House") == 7
        assert ex.house_of_chapter("Concerning the Twelfth House") == 12

    def test_ocr_variants_of_the_ordinal_are_accepted(self):
        """'Twelth', 'Eleveath', 'Eieventh' and 'Elevanth' all occur in these scans."""
        assert ex.house_of_chapter("Concerning the Twelth House") == 12
        assert ex.house_of_chapter("Concerning the Eleveath House") == 11

    def test_a_table_of_contents_row_is_not_a_chapter(self):
        """The contents page names every chapter; treating those rows as headings pinned the
        first charts of Vol I to the twelfth house."""
        toc = ("IV. Concerning the First House ....................... 21\n"
               "XVI. Concerning the Twelfth House .................... 389\n")
        assert ex.house_of_chapter(toc) is None

    def test_the_last_real_heading_wins(self):
        text = "Concerning the First House\nsome prose\nConcerning the Second House\nmore prose"
        assert ex.house_of_chapter(text) == 2


class TestDegreeGate:
    def test_offset_is_scale_free_across_dasha_spans(self):
        """The same half-year balance disagreement is a much larger Moon error inside a short
        dasha than a long one — which is exactly why the gate compares degrees, not days."""
        short = ex.moon_offset_deg(3.5, 4.0, "Sun")       # 6-year span
        long_ = ex.moon_offset_deg(19.5, 20.0, "Venus")   # 20-year span
        assert short > long_ * 3
        assert ex.moon_offset_deg(5.0, 5.0, "Ketu") == 0.0


class TestReviewFoundDefects:
    """Both defects an engine-blind reviewer found in the 2026-08-23 sample. They matter more
    than they look: under the confirmation-rule amendment a DRAFT can now be promoted regardless
    of engine agreement, so a mislabelled draft can reach the scored pool."""

    def test_the_ordinal_is_read_from_the_outcome_not_the_factors(self):
        """Raman concedes factors, then states the result. HTJAH-I.x71's real conclusion —
        'The mother lived till the 36th year of the native on account of the general strength of
        the fourth house... The Matru-Karaka Moon is considerably afflicted.' — was drafted
        `afflicted` because the factor clause dominated; the reviewer revised it to `mixed`."""
        prose = ("The fourth house is moderately strong, but the lord and the Karaka are "
                 "considerably afflicted. Hence the native lost his mother very early.")
        assert "Hence the native lost his mother" in ex.outcome_clause(prose)
        assert "moderately strong" not in ex.outcome_clause(prose)

    def test_outcome_clause_falls_back_to_the_whole_paragraph(self):
        plain = "The native was very unfortunate in regard to his children."
        assert ex.outcome_clause(plain) == plain

    def test_a_chapter_covering_two_matters_picks_by_prose(self):
        """HTJAH-I ch.4 judges the mother AND education; blanket-mapping H4 to `mother`
        mislabelled every learning row (HTJAH-I.x79, Goethe, was one)."""
        assert ex._signification_for(4, "the influences blended in relation to the house of "
                                        "learning; the native got a fine education") == "education"
        assert ex._signification_for(4, "the native lost his mother very early") == "mother"

    def test_the_chosen_signification_always_belongs_to_the_house(self):
        """A key the house does not own scores against nothing at all."""
        from app.raman_saab.doctrine.significations import significations_of
        for h in range(1, 13):
            sig = ex._signification_for(h, "the native prospered greatly")
            assert sig in {s.key for s in significations_of(h)}
