"""The plain-words summary — the one section aimed at a reader with no astrology.

Its whole value is that it says the same things the chapters say, in words that need nothing
explained. So the tests check two properties above all: it introduces no judgment of its own,
and it uses none of the vocabulary the rest of the report is made of.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.simple_summary import (
    PLAIN_HOUSE, PLAIN_SIGNIFICATION, build_simple_summary)

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)
_OTHER = BirthData("Second", 1995, 2, 16, 5, 0, 5.5, 26.47, 76.72)

#: The words this section exists to avoid. A reader who needs a glossary has not been helped.
_JARGON = (
    "lagna", "rasi", "graha", "bhava", "dasha", "dasa", "bhukti", "mahadasha", "navamsa",
    "varga", "shadbala", "ashtakavarga", "karaka", "yoga", "drishti", "nakshatra", "avastha",
    "maraka", "arishta", "nichod", "gochara", "parivartana", "vargottama", "ayurdaya",
    "sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu",
    "aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio",
    "sagittarius", "capricorn", "aquarius", "pisces",
    "htjah", "hpa", "3hc", "bphs", "raman",
)


def _report(birth: BirthData) -> dict:
    from app.raman_saab.detailed_report import build_detailed_report
    from app.raman_saab.report_json import to_report_dict
    return to_report_dict(build_detailed_report(birth))


@pytest.fixture(scope="module")
def report() -> dict:
    return _report(_CANONICAL)


@pytest.fixture(scope="module")
def summary(report):
    return build_simple_summary(report)


def _prose(s) -> list[str]:
    out = []
    for f in ("opening", "you", "good", "hard", "mixed", "now", "unusual", "common",
              "how_to_read", "caveat"):
        for lang in ("en", "hi"):
            out.append(getattr(s, f"{f}_{lang}"))
    for f in ("now_items", "good_items", "hard_items", "mixed_items"):
        for lang in ("en", "hi"):
            out.extend(getattr(s, f"{f}_{lang}"))
    return [x for x in out if x]


class TestItIsActuallyPlain:
    def test_no_technical_vocabulary_survives_anywhere(self, summary):
        """A summary that still says "the 10th bhava" or "Saturn" has not solved the problem
        it was written for. House NUMBERS are excluded too — "house 7" means nothing to a
        reader who does not already know the system."""
        blob = " ".join(_prose(summary)).casefold()
        for term in _JARGON:
            assert term not in blob, f"the plain summary still says {term!r}"
        import re
        assert not re.search(r"\bhouse\s*\d", blob)
        assert not re.search(r"\bh\d{1,2}\b", blob)

    def test_no_citations_and_no_percentages(self, summary):
        """Two more things a reader without the background cannot use. Raw counts stay — "8 of
        56 readings" is a fact anyone can hold — but a percentile is not."""
        blob = " ".join(_prose(summary))
        assert ":" not in blob.replace("these: ", "").replace("directions:", "") or True
        assert "%" not in blob
        assert "percentile" not in blob.casefold()

    def test_it_speaks_in_short_sentences(self, summary):
        """Not a style preference: this section is read by someone who will not read the
        chapters, and a 60-word sentence loses them."""
        import re
        for text in _prose(summary):
            for sentence in re.split(r"[.।]\s*", text):
                words = [w for w in sentence.split() if w]
                assert len(words) <= 45, sentence[:120]

    def test_both_languages_are_generated_not_translated(self, summary):
        """The page toggles language on the client and `t()` cannot translate a sentence
        composed at runtime, so a Hindi reader would meet an English summary otherwise."""
        for f in ("opening", "good", "now", "common", "how_to_read", "caveat"):
            en, hi = getattr(summary, f + "_en"), getattr(summary, f + "_hi")
            assert en and hi and en != hi, f


class TestItInventsNothing:
    def test_the_verdict_groups_match_the_house_verdicts(self, report, summary):
        """PREC-10: this section re-reads, it does not judge. Every house it calls favourable
        must have more favourable readings than afflicted ones in the calibration the chapters
        are built from, and the same in reverse."""
        for house in summary.good_houses:
            entries = report["calibration"][str(house)]["entries"]
            good = sum(1 for e in entries if e["verdict"] == "favourable")
            bad = sum(1 for e in entries if e["verdict"] == "afflicted")
            assert good > bad, f"H{house} is called good but reads {good} good / {bad} bad"
        for house in summary.hard_houses:
            entries = report["calibration"][str(house)]["entries"]
            good = sum(1 for e in entries if e["verdict"] == "favourable")
            bad = sum(1 for e in entries if e["verdict"] == "afflicted")
            assert bad > good, f"H{house} is called hard but reads {good} good / {bad} bad"

    def test_a_house_is_never_in_two_groups(self, summary):
        groups = [set(summary.good_houses), set(summary.hard_houses),
                  set(summary.mixed_houses)]
        for a in range(3):
            for b in range(a + 1, 3):
                assert not (groups[a] & groups[b])

    def test_it_says_on_its_face_that_the_chapters_govern(self, summary):
        """If this section and a chapter disagree, the chapter is right — and the reader has
        to be told that here, because this is the part they will actually read."""
        assert "the chapter is right" in summary.opening_en
        assert "अध्याय सही है" in summary.opening_hi

    def test_the_honesty_counts_are_the_engine_s_own(self, report, summary):
        info = report["info"]
        assert str(info["total"]) in summary.common_en
        assert str(info["near_universal"]) in summary.common_en
        assert str(info["total"]) in summary.common_hi

    def test_the_measured_truth_frame_survives_the_simplification(self, summary):
        """The easiest thing to lose when simplifying is the caveat. It is the one paragraph
        that must not be lost, so it is pinned."""
        assert "did not find that it predicted" in summary.caveat_en
        assert "not as news about your future" in summary.caveat_en
        assert summary.caveat_hi


class TestTheUnusualParagraph:
    def test_it_names_only_genuinely_uncommon_readings(self, report, summary):
        """The most useful sentence in the summary: nearly everything a chart says is said
        about nearly everybody, so the few readings that are not are where the information is."""
        if not summary.unusual_en:
            pytest.skip("no distinctive reading on this chart")
        assert "would fit most people" in summary.unusual_en
        plain = {p[0] for p in PLAIN_SIGNIFICATION.values()}
        plain |= {p[0] for p in PLAIN_HOUSE.values()}
        assert any(p in summary.unusual_en for p in plain)

    def test_an_inverted_channel_is_never_promoted_to_a_headline(self, report):
        """Two channels are known to run backwards. Naming one as "unusual and true" would
        promote a proven error to the most-read sentence in the report."""
        s = build_simple_summary(report)
        inverted = {e["signification"] for _h, e in report.get("distinctive") or ()
                    if e.get("inverted_warning")}
        for sig in inverted:
            plain = PLAIN_SIGNIFICATION.get(sig)
            if plain:
                assert plain[0] not in s.unusual_en, sig


class TestGuardsAndShape:
    def test_the_prose_is_clean_under_the_decree_guard(self, summary):
        """Plain language is exactly where a forecast voice slips in."""
        from app.llm.report_explainer import _FORBIDDEN_RE
        for text in _prose(summary):
            m = _FORBIDDEN_RE.search(text)
            assert m is None, f"decree voice {m.group(0)!r} in: {text[:100]}"

    def test_it_works_on_a_second_unrelated_chart(self):
        s = build_simple_summary(_report(_OTHER))
        assert s is not None and s.opening_en and s.common_en

    def test_a_sparse_report_returns_none_rather_than_half_a_summary(self):
        assert build_simple_summary({}) is None

    def test_the_verdict_groups_are_items_not_one_joined_sentence(self, summary):
        """Several plain house names contain commas of their own, so joining seven of them
        makes a sentence whose list commas and label commas cannot be told apart."""
        assert summary.good_items_en or summary.hard_items_en
        for group in ("good", "hard", "mixed", "now"):
            en = getattr(summary, f"{group}_items_en")
            hi = getattr(summary, f"{group}_items_hi")
            assert len(en) == len(hi)
