"""The chart feedback instrument — the questionnaire that can actually be scored.

Each test states the property it defends. The properties that matter most are the ones that make
an answer worth collecting at all: the key never ships, the forced choices are ordered by rarity
rather than by how loudly the engine speaks, and the shuffle is stable across processes.
"""
from __future__ import annotations

import subprocess
import sys

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab import feedback_instrument as fi
from app.raman_saab.feedback_instrument import (
    ANSWER_SCALE, CONFIDENCE_SCALE, EXCLUDED_SIGNIFICATIONS, TOPIC,
    build_feedback_instrument, instrument_key, validate_instrument_answers)

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)
#: A second, unrelated nativity — several properties are only observable across charts (the
#: shuffle must not be constant, the rarest reading must differ).
_OTHER = BirthData("Second", 1995, 2, 16, 5, 0, 5.5, 26.47, 76.72)


def _report(birth: BirthData) -> dict:
    from app.raman_saab.detailed_report import build_detailed_report
    from app.raman_saab.report_json import to_report_dict
    return to_report_dict(build_detailed_report(birth))


@pytest.fixture(scope="module")
def report():
    return _report(_CANONICAL)


@pytest.fixture(scope="module")
def other():
    return _report(_OTHER)


@pytest.fixture(scope="module")
def payload(report):
    return build_feedback_instrument(report)


@pytest.fixture(scope="module")
def key(report):
    return instrument_key(report)


def _all_questions(payload: dict) -> list[dict]:
    return [q for p in payload["parts"] for q in p["questions"]]


def _all_text(node) -> list[str]:
    """Every string anywhere in the payload — for the checks that must hold on ALL of it."""
    if isinstance(node, str):
        return [node]
    if isinstance(node, dict):
        return [s for v in node.values() for s in _all_text(v)]
    if isinstance(node, (list, tuple)):
        return [s for v in node for s in _all_text(v)]
    return []


class TestTheKeyNeverShips:
    def test_the_payload_carries_no_indication_of_which_option_is_the_charts(self, payload, key):
        """The whole instrument rests on the reader not knowing. If the payload carried the
        calibration metadata each item was built from — the signification, the verdict, the
        population share — the key could be reconstructed from it and a forced choice would be
        worth exactly what the old show-then-ask question is worth, which is nothing."""
        import json
        blob = json.dumps(payload, ensure_ascii=False)
        for leak in ("band_share", "signification", "inverted_warning", "favourability",
                     "rarity", "verdict", "forced_choice\", \"house"):
            assert leak not in blob, leak
        for q in _all_questions(payload):
            assert set(q) == {"qid", "part", "group", "group_label", "kind", "text", "hint",
                              "options", "confidence", "allow_free_text"}
            for o in q["options"]:
                assert set(o) == {"value", "text"}

    def test_the_inverted_channels_are_flagged_only_in_the_key(self, payload, key):
        """Two readings sit on channels the atlas proved run BACKWARDS. They stay in the set as
        the honesty check — a reader who agrees there while disagreeing elsewhere is agreeing
        with whatever is shown — so the reader must not be able to tell which they are."""
        assert not any("inverted" in s for s in _all_text(payload))
        for qid in key["inverted"]:
            assert key["meta"][qid]["inverted_warning"] is True

    def test_the_key_covers_every_forced_choice_and_nothing_else(self, payload, key):
        choices = [q for q in _all_questions(payload)
                   if q["kind"] == "choice"]
        assert {q["qid"] for q in choices} == set(key["answers"])
        for qid, val in key["answers"].items():
            q = next(q for q in choices if q["qid"] == qid)
            assert val in {o["value"] for o in q["options"]}


class TestDeterminism:
    def test_the_same_chart_builds_the_same_instrument_twice(self, report):
        """A stored answer names an option by value. If a rebuild reshuffled the pair, every
        answer already collected would silently invert."""
        assert build_feedback_instrument(report) == build_feedback_instrument(report)
        assert instrument_key(report) == instrument_key(report)

    def test_the_shuffle_survives_a_fresh_interpreter(self):
        """`hash()` is salted per process, so a shuffle built on it would differ between the
        request that asked the questions and the request that scores them. The seed is sha256;
        this runs a SEPARATE interpreter with a different PYTHONHASHSEED to prove it."""
        code = (
            "from app.raman_saab.chart.model import BirthData;"
            "from app.raman_saab.detailed_report import build_detailed_report;"
            "from app.raman_saab.report_json import to_report_dict;"
            "from app.raman_saab.feedback_instrument import instrument_key;"
            "d=to_report_dict(build_detailed_report("
            "BirthData('Canonical Test',1990,7,15,12,0,5.5,12.97,77.59)));"
            "print(sorted(instrument_key(d)['answers'].items()))")
        outs = []
        for seed in ("0", "12345"):
            import os
            env = {**os.environ, "PYTHONHASHSEED": seed, "PYTHONPATH": "."}
            outs.append(subprocess.run([sys.executable, "-c", code], capture_output=True,
                                       text=True, env=env, timeout=600).stdout.strip())
        assert outs[0] and outs[0] == outs[1], outs

    def test_the_qids_do_not_depend_on_the_display_language(self, report):
        """Answers given in Hindi must pool with answers given in English."""
        en = build_feedback_instrument(report, lang="en")
        hi = build_feedback_instrument(report, lang="hi")
        assert [q["qid"] for q in _all_questions(en)] == [q["qid"] for q in _all_questions(hi)]
        assert instrument_key(report)["answers"] == instrument_key(report)["answers"]

    def test_the_shuffle_is_not_constant(self, report, other):
        """A shuffle that always puts the chart's claim first is not a shuffle. Across both
        charts' items, both option positions must actually be used."""
        vals = set(instrument_key(report)["answers"].values())
        vals |= set(instrument_key(other)["answers"].values())
        assert vals == {"opt1", "opt2"}


class TestForcedChoicesAreRankedByInformation:
    def test_the_items_run_rarest_first(self, report, key):
        """Ordering by the digest would lead with whatever the engine says loudest, and the
        engine is loudest where every chart agrees. Ordering is by `band_share` ascending —
        the fraction of the population carrying this exact reading."""
        shares = [m["band_share"] for qid, m in key["meta"].items()
                  if m["kind"] == "forced_choice"]
        assert shares == sorted(shares)

    def test_the_rarest_item_is_genuinely_rare(self, key):
        """If the top item were a coin-flip reading the whole ranking would be pointless."""
        first = min(m["band_share"] for m in key["meta"].values()
                    if m["kind"] == "forced_choice")
        assert first < 0.25

    def test_no_house_dominates_the_set(self, key):
        """The rarest readings cluster in a house or two; asking six questions about the 12th
        would measure one corner of a life. At most two per house."""
        counts: dict[int, int] = {}
        for m in key["meta"].values():
            if m["kind"] == "forced_choice":
                counts[m["house"]] = counts.get(m["house"], 0) + 1
        assert counts and max(counts.values()) <= 2

    def test_a_near_universal_reading_is_not_asked_first(self, report, key):
        """The engine's older generator leads with a 42%-share wealth reading. This one must
        not: check that nothing in the asked set is more common than the population median."""
        for m in key["meta"].values():
            if m["kind"] == "forced_choice":
                assert m["band_share"] < 0.5, m


class TestWhatIsNeverAsked:
    def test_lifespan_is_not_put_to_the_reader(self, payload):
        """No answer a person can give confirms or refutes a longevity band, the question does
        harm, and the engine's own guard refuses the decree voice on this material."""
        assert {"death", "longevity"} <= EXCLUDED_SIGNIFICATIONS
        blob = " ".join(_all_text(payload)).casefold()
        assert "how long you will live" not in blob
        assert "lifespan" not in blob

    def test_no_excluded_signification_reaches_a_question(self, report, other):
        for rep in (report, other):
            for m in instrument_key(rep)["meta"].values():
                assert m.get("signification") not in EXCLUDED_SIGNIFICATIONS

    def test_every_signification_the_engine_emits_has_a_plain_topic(self, report, other):
        """A missing topic silently drops that reading from every instrument forever. The
        engine's own calibration output is the list of record, checked on two charts."""
        emitted = {e["signification"]
                   for rep in (report, other)
                   for blk in rep["calibration"].values()
                   for e in blk["entries"]}
        missing = emitted - set(TOPIC) - EXCLUDED_SIGNIFICATIONS
        assert not missing, f"significations with no plain topic phrase: {sorted(missing)}"


class TestPartsAndWording:
    def test_all_four_parts_are_built_in_order(self, payload):
        assert [p["part"] for p in payload["parts"]] == ["A", "B", "C", "D"]
        for p in payload["parts"]:
            assert p["title"] and p["note"] and p["questions"]

    def test_part_a_mentions_no_astrology(self, payload):
        """Part A is the only unbiased evidence the reader can give, and it stops being that
        the moment a rasi, a graha or a dasha appears in it."""
        part_a = next(p for p in payload["parts"] if p["part"] == "A")
        blob = " ".join(_all_text(part_a)).casefold()
        for term in ("dasha", "dasa", "rasi", "graha", "lagna", "ascendant", "nakshatra",
                     "house", "planet", "yoga", "bhukti"):
            assert term not in blob, f"Part A leaks {term!r}"

    def test_part_a_says_to_answer_it_before_reading(self, payload):
        part_a = next(p for p in payload["parts"] if p["part"] == "A")
        assert "BEFORE reading" in part_a["note"]

    def test_every_choice_offers_two_genuinely_different_options(self, payload):
        for q in _all_questions(payload):
            if q["kind"] != "choice":
                continue
            texts = [o["text"] for o in q["options"]]
            assert len(texts) == 2 and texts[0] != texts[1], q["qid"]
            assert [o["value"] for o in q["options"]] == ["opt1", "opt2"]

    def test_the_dated_spine_asks_for_three_months_not_six(self, payload):
        """The period changes cluster, so a six-month window covers much of a life and
        half-passes the test by itself."""
        q = next(q for q in _all_questions(payload) if q["qid"].endswith(".C0"))
        assert "three months" in q["text"]
        assert "cluster" in q["hint"]

    def test_the_caveat_keeps_the_measured_truth_frame(self, payload):
        assert "calibrate" in payload["caveat"] or "calibrates" in payload["caveat"]
        assert "never a claim" in payload["caveat"]
        assert "validate" in payload["caveat"]

    def test_every_emitted_string_is_clean_under_the_decree_guard(self, payload):
        """The instrument asks about a life already lived; nothing in it may slip into the
        voice that tells a reader what will happen."""
        from app.llm.report_explainer import _FORBIDDEN_RE
        for s in _all_text(payload):
            m = _FORBIDDEN_RE.search(s)
            assert m is None, f"decree voice {m.group(0)!r} in: {s[:90]}"

    def test_both_languages_are_complete(self, report):
        """A half-translated form is worse than an English one — the reader stops trusting it
        mid-page. Every question carries text in whichever language was asked for."""
        for lang in ("en", "hi"):
            for q in _all_questions(build_feedback_instrument(report, lang=lang)):
                assert q["text"].strip(), (lang, q["qid"])
                for o in q["options"]:
                    assert o["text"].strip(), (lang, q["qid"])


class TestRectification:
    def test_the_cusp_gap_is_computed_and_the_neighbour_is_adjacent(self, payload):
        r = payload["rectification"]
        assert r is not None
        assert 0 <= r["degrees_into_sign"] < 30
        assert abs(((r["asc_sign"] - r["neighbour_sign"]) % 12)) in (1, 11)
        assert r["approx_gap_minutes"] >= 0

    def test_a_chart_near_its_cusp_is_marked_tight(self, other):
        """The 1995 nativity rises at Sagittarius 27.8 — about nine minutes from Capricorn, on
        a birth time recorded as a round 05:00. That is exactly the case the flag exists for."""
        r = build_feedback_instrument(other)["rectification"]
        assert r["tight"] is True
        assert r["neighbour_sign_name"] == "Capricorn"
        assert r["approx_gap_minutes"] <= 15

    def test_the_two_portraits_differ(self, payload):
        r = payload["rectification"]
        assert r["portrait_here"] != r["portrait_neighbour"]


class TestBoundaries:
    def test_the_boundaries_are_mahadasha_changes_as_dates(self, payload):
        rows = payload["boundaries"]
        assert rows
        for row in rows:
            assert set(row) == {"date", "maha"}
            assert len(row["date"]) == 10 and row["date"][4] == "-"
        assert [r["date"] for r in rows] == sorted(r["date"] for r in rows)

    def test_consecutive_rows_never_repeat_a_lord(self, payload):
        lords = [r["maha"] for r in payload["boundaries"]]
        assert all(a != b for a, b in zip(lords, lords[1:]))


class TestValidation:
    def test_legal_answers_pass(self, report, payload):
        choice = next(q for q in _all_questions(payload)
                      if q["kind"] == "choice" and q["confidence"])
        scale = next(q for q in _all_questions(payload) if q["kind"] == "scale")
        answers = [
            {"qid": choice["qid"], "answer": choice["options"][0]["value"]},
            {"qid": choice["qid"] + ".confidence", "answer": "4"},
            {"qid": scale["qid"], "answer": ANSWER_SCALE[0]},
        ]
        assert validate_instrument_answers(report, answers) == []

    def test_an_unknown_question_is_refused(self, report):
        assert validate_instrument_answers(report, [{"qid": "inst.v1.ZZ", "answer": "opt1"}])

    def test_an_option_the_instrument_never_offered_is_refused(self, report, payload):
        choice = next(q for q in _all_questions(payload) if q["kind"] == "choice")
        assert validate_instrument_answers(
            report, [{"qid": choice["qid"], "answer": "opt7"}])

    def test_a_confidence_outside_the_scale_is_refused(self, report, payload):
        choice = next(q for q in _all_questions(payload)
                      if q["kind"] == "choice" and q["confidence"])
        assert validate_instrument_answers(
            report, [{"qid": choice["qid"] + ".confidence", "answer": "9"}])
        assert "9" not in CONFIDENCE_SCALE

    def test_confidence_on_an_item_that_does_not_ask_for_it_is_refused(self, report, payload):
        """The rectification choice takes no confidence rating; a client that sends one is
        confused about which instrument it is answering, and its other answers are suspect."""
        plain = next(q for q in _all_questions(payload)
                     if q["kind"] == "choice" and not q["confidence"])
        assert validate_instrument_answers(
            report, [{"qid": plain["qid"] + ".confidence", "answer": "3"}])

    def test_validation_rebuilds_rather_than_trusting_the_client(self, report):
        """The client sends only a qid and a value; the legal set is recomputed from the chart.
        Nothing the client says about the QUESTION reaches the scoring path."""
        import inspect
        src = inspect.getsource(fi.validate_instrument_answers)
        assert "_build(report" in src
        assert "question_text" not in src


class TestVerdictAuthorityInvariant:
    def test_the_verdict_path_does_not_import_the_instrument(self):
        """Asking a reader about a house must never be able to change how the house is judged."""
        import pathlib
        root = pathlib.Path(__file__).resolve().parents[2] / "app" / "raman_saab"
        for f in (root / "judges" / "house_template.py",
                  root / "judges" / "total.py",
                  root / "judges" / "conditions.py"):
            if f.exists():
                assert "feedback_instrument" not in f.read_text(encoding="utf-8"), f
