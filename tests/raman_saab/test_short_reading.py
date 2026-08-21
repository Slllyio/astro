"""The short reading — the second way to read the same report.

Two things are being protected here. The first is the promise the feature makes: no
astrological vocabulary, no house numbers, no citations, no quoted book text. That promise is
easy to make and easy to break by one careless sentence six months from now, so it is
enforced by a screen rather than by review — built from the project's own glossary, run over
every string the builder emits, across many real charts rather than the canonical one.

The second is that this is a VIEW, not a smaller report: it must judge nothing of its own, so
every claim it makes is checked against the section it re-reads.
"""
from __future__ import annotations

import dataclasses
import json
import pathlib
import re

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import build_detailed_report
from app.raman_saab.plain_terms import TERM_GLOSS
from app.raman_saab.report_json import to_report_dict
from app.raman_saab.short_reading import (
    PLAIN_YOGA,
    _KIND_FALLBACK,
    _plain_name,
    build_short_reading,
)

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)

#: Everything the short reading promises not to say. The glossary supplies the technical
#: terms; the rest are the words the user named ("houses, rashis") plus the planet and sign
#: names, which are the other half of the same vocabulary.
_BANNED = sorted(set(TERM_GLOSS) | {
    "house", "houses", "rashi", "rashis", "rasi", "sign", "signs", "lord", "lords",
    "aspect", "aspects", "bhava", "graha", "yoga", "dasha", "dasa", "bhukti",
    "antardasha", "mahadasha", "navamsa", "lagna", "ascendant", "karaka", "malefic",
    "benefic", "exalted", "debilitated", "combust", "retrograde", "kendra", "trikona",
    "dusthana", "drishti", "ayanamsa", "shadbala", "ashtakavarga",
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
}, key=len, reverse=True)
_JARGON = re.compile(r"(?<![\w-])(" + "|".join(re.escape(t) for t in _BANNED) + r")(?![\w-])",
                     re.I)
_CITATION = re.compile(r"\b(HTJAH|HPA|GBB|3HC|JAIMINI|ASP|AFB)[-:\d]")
_HOUSE_NUMBER = re.compile(r"\bH\d{1,2}\b")


def _strings(obj, path: str = "short"):
    """Every string the builder emits, with the field path that produced it."""
    if dataclasses.is_dataclass(obj):
        for f in dataclasses.fields(obj):
            yield from _strings(getattr(obj, f.name), f"{path}.{f.name}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            yield from _strings(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        yield path, obj


def _screen(short) -> list[str]:
    """Every promise-breaking token, as readable complaints. A combination's own NAME is
    exempt: it is a proper noun, and the sentence under it is what has to be plain."""
    out: list[str] = []
    for path, text in _strings(short):
        if path.endswith(".name"):
            continue
        for rx, label in ((_JARGON, "jargon"), (_CITATION, "citation"),
                          (_HOUSE_NUMBER, "house number")):
            m = rx.search(text)
            if m:
                out.append(f"{label} {m.group(0)!r} in {path}: "
                           f"...{text[max(0, m.start() - 50):m.end() + 50]}...")
    return out


@pytest.fixture(scope="module")
def report_dict() -> dict:
    return to_report_dict(build_detailed_report(_CANONICAL))


@pytest.fixture(scope="module")
def short(report_dict):
    sr = build_short_reading(report_dict)
    assert sr is not None
    return sr


class TestItKeepsItsPromise:
    def test_the_canonical_chart_says_nothing_technical(self, short):
        assert _screen(short) == []

    def test_a_spread_of_real_charts_say_nothing_technical(self):
        """One chart proves nothing: the prose varies with which combinations fire and which
        matters read well, so the screen has to see a spread. Charts come from the golden
        ledger because they are real nativities with real variety."""
        ledger = (pathlib.Path(__file__).resolve().parents[2]
                  / "tests" / "fixtures" / "raman_goldens.jsonl")
        if not ledger.is_file():
            pytest.skip("golden ledger not present on this machine")
        # the fixture is JSONL WITH `#` comment lines — same skip rule as its own loader
        rows = [json.loads(ln) for ln in ledger.read_text(encoding="utf-8").splitlines()
                if ln.strip() and not ln.lstrip().startswith("#")]
        # Births more than ~120 years back have no running period at today's reference date —
        # the Vimshottari cycle has run out — and `build_detailed_report` raises on them.
        # That is a real (pre-existing, unrelated) limit; this test is about the vocabulary
        # screen, so it reads charts the engine can actually report on.
        import datetime
        cutoff = datetime.date.today().year - 115
        records = [r for r in rows if r.get("birth")
                   and int(str(r["birth"]["dt"])[:4]) >= cutoff]
        assert records, "no golden record carries birth data"
        complaints: list[str] = []
        built = 0
        for rec in records[::6]:                       # a stride, not the first N in a book
            b = rec["birth"]
            date, _, clock = str(b["dt"]).partition("T")
            y, mo, d = (int(x) for x in date.split("-"))
            hh, mm = (int(x) for x in clock.split(":")[:2])
            sr = build_short_reading(to_report_dict(build_detailed_report(
                BirthData("golden", y, mo, d, hh, mm, float(b["tz"]),
                          float(b["lat"]), float(b["lon"])))))
            if sr is None:
                continue
            built += 1
            complaints += [f"{rec['id']}: {c}" for c in _screen(sr)]
        assert built >= 10, f"only {built} short readings built — the screen saw almost nothing"
        assert complaints == [], complaints[:10]

    def test_the_written_glosses_are_themselves_clean(self):
        """The glosses are the one place a technical word would be easiest to reach for."""
        for yid, (en, hi) in PLAIN_YOGA.items():
            for text in (en, hi):
                m = _JARGON.search(text)
                assert m is None, f"{yid}: {m.group(0)!r} in {text[:70]}"
        for kind, (en, hi) in _KIND_FALLBACK.items():
            for text in (en, hi):
                m = _JARGON.search(text)
                assert m is None, f"{kind}: {m.group(0)!r} in {text[:70]}"

    def test_a_combinations_technical_qualifier_is_dropped_from_its_label(self):
        """The record disambiguates itself with exactly the vocabulary this view avoids."""
        assert _plain_name("Raja Yoga (9th-10th lords exchanged or in each other's houses)") \
            == "Raja Yoga"
        assert _plain_name("Gajakesari Yoga") == "Gajakesari Yoga"

    def test_no_classical_effect_text_is_reprinted(self, report_dict, short):
        """The records carry Raman's printed effects, several of which read as verdicts on a
        person ("a rogue and a swindler"). The full reading prints them inside their method
        and their citation; this view must not hand them over bare."""
        effects = {str(y.get("effect") or "") for y in report_dict["yogas"]}
        emitted = " ".join(t for _p, t in _strings(short))
        for effect in effects:
            head = effect.split(";")[0].strip()
            if len(head) > 25:
                assert head not in emitted, head


class TestItJudgesNothing:
    def test_every_combination_shown_actually_fired(self, report_dict, short):
        fired = {_plain_name(str(y["name"])) for y in report_dict["yogas"]}
        for c in short.combinations:
            assert c.name in fired, c.name

    def test_the_difficult_ones_are_listed_first(self, short):
        """A reader who skims must not have the one flagged thing buried under six pleasant
        lines. Not a scare tactic — the tone word is beside it and the caveat closes."""
        rank = {"difficult": 0, "mixed": 1, "supportive": 2}
        seen = [rank[c.tone] for c in short.combinations]
        assert seen == sorted(seen), [c.tone for c in short.combinations]

    def test_every_period_is_a_real_row_of_the_graded_timeline(self, report_dict, short):
        """The stretches are re-read from the timeline the engine already graded, at the same
        grain. Coarsening them here would be a new judgment."""
        import swisseph as swe

        def label(jd):
            y, m, _d, _h = swe.revjul(jd, swe.GREG_CAL)
            return int(y), int(m)

        starts = {label(float(p["start_jd"])) for p in report_dict["timeline"]}
        for p in short.periods:
            year = int(p.from_label_en.split()[-1])
            assert any(y == year for y, _m in starts), p.from_label_en

    def test_exactly_one_period_is_marked_as_now(self, short):
        assert sum(1 for p in short.periods if p.is_now) == 1

    def test_the_periods_run_forward_in_time(self, short):
        years = [int(p.from_label_en.split()[-1]) for p in short.periods]
        assert years == sorted(years), years

    def test_the_matter_lists_come_from_the_plain_house_names(self, short):
        from app.raman_saab.simple_summary import PLAIN_HOUSE
        allowed = {en for en, _hi in PLAIN_HOUSE.values()}
        for p in short.periods:
            for name in (*p.supportive_en, *p.strained_en):
                assert name in allowed, name

    def test_the_verdict_groups_match_the_summary_it_re_reads(self, report_dict, short):
        from app.raman_saab.simple_summary import build_simple_summary
        s = build_simple_summary(report_dict)
        assert short.strengths_en == s.good_items_en
        assert short.difficulties_en == s.hard_items_en
        assert short.mixed_en == s.mixed_items_en


class TestBothLanguages:
    def test_every_english_field_has_a_hindi_twin(self, short):
        for f in dataclasses.fields(short):
            if not f.name.endswith("_en"):
                continue
            hi = f.name[:-3] + "_hi"
            assert hasattr(short, hi), hi
            en_v, hi_v = getattr(short, f.name), getattr(short, hi)
            assert bool(en_v) == bool(hi_v), f"{f.name} and {hi} disagree on emptiness"

    def test_the_period_and_combination_rows_are_bilingual_too(self, short):
        for p in short.periods:
            assert p.strength_hi and p.from_label_hi and p.to_label_hi
            assert len(p.supportive_en) == len(p.supportive_hi)
            assert len(p.strained_en) == len(p.strained_hi)
        for c in short.combinations:
            assert c.plain_hi and c.tone_hi
            assert bool(c.when_en) == bool(c.when_hi)

    def test_the_hindi_is_actually_hindi(self, short):
        """A missing translation shows up as English inside a Hindi page, which reads as a
        bug to the reader and as nothing at all to a test that only checks non-emptiness."""
        deva = re.compile(r"[ऀ-ॿ]")
        for path, text in _strings(short):
            if path.endswith("_hi") and text:
                assert deva.search(text), f"{path} carries no Devanagari: {text[:60]}"


class TestItTellsTheReaderTheRestExists:
    def test_it_says_there_is_a_full_reading(self, short):
        """A view that hides fifty chapters without saying so is the completeness law's
        exact failure mode. It is a view because it says it is one."""
        assert short.more_en and short.more_hi
        assert "full reading" in short.more_en

    def test_the_honesty_lines_survive_the_shortening(self, short):
        """The two lines that may never be dropped: how much of a reading like this is true
        of nearly everybody, and that this method is not a validated forecast."""
        assert short.common_en
        assert short.caveat_en
