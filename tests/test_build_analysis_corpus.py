"""Tests for the Phase-2 corpus distiller (`app.medini.ml.build_analysis_corpus`).

Stateless logic only — parsing, curation, voice extraction, resume keys — plus one
end-to-end distil pass on the stub backend (no API, no parquet read).
"""
from __future__ import annotations

import json

from corpus_presence import needs_file

from app.medini.ml.build_analysis_corpus import (
    GOLDEN_FIXTURES,
    MAX_WORDS,
    MIN_ANCHORS,
    MIN_CHARS,
    SampledChart,
    distil,
    existing_keys,
    golden_verdict_prose_fragments,
    jargon_term_hits,
    keep_reason,
    make_teacher,
    parse_dossier_row,
    seed_golden_voice,
    voice_blocks,
)

_ROW = {"person_id": "ADB:1", "name": "test person", "corpus": "ADB",
        "birth_date": "1990-07-15", "birth_time": "12:00:00",
        "birth_time_confidence": 1.0, "birth_lat": 12.97, "birth_lon": 77.59,
        "tz_offset": 5.5}


class TestParseDossierRow:
    def test_timed_birth_parses(self):
        """A confidence-1.0 dossier row becomes a castable chart with all fields."""
        c = parse_dossier_row(_ROW)
        assert c == SampledChart(person_id="ADB:1", name="test person", corpus="ADB",
                                 year=1990, month=7, day=15, hour=12, minute=0,
                                 latitude=12.97, longitude=77.59, tz_offset=5.5)

    def test_untimed_birth_is_rejected(self):
        """Unknown birth time -> no lagna -> the chart must not enter the corpus."""
        assert parse_dossier_row({**_ROW, "birth_time_confidence": 0.0}) is None

    def test_garbage_coordinates_are_rejected(self):
        assert parse_dossier_row({**_ROW, "birth_lat": 123.0}) is None
        assert parse_dossier_row({**_ROW, "tz_offset": 99.0}) is None


class TestKeepReason:
    def _ans(self, **kw):
        from app.llm.report_explainer import GroundedAnswer
        base = dict(text="x" * (MIN_CHARS + 10),
                    anchors_used=tuple(f"[Fact {i}]" for i in range(1, MIN_ANCHORS + 1)),
                    grounding_ratio=1.0, gloss_ratio=0.0, ungrounded_sentences=(),
                    bad_anchors=(), fabricated_citations=(), forbidden_moves=(),
                    is_deferral=False, model="t", source="llm")
        base.update(kw)
        return GroundedAnswer(**base)

    def test_clean_grounded_answer_is_kept(self):
        assert keep_reason(self._ans(), 0.75) is None

    def test_prediction_language_is_rejected_by_the_hard_guard(self):
        """The corpus can NEVER contain decree language — guard runs first."""
        r = keep_reason(self._ans(forbidden_moves=("will marry",)), 0.75)
        assert r is not None and r.startswith("guard:")

    def test_thin_or_weakly_anchored_answers_are_rejected(self):
        assert "too short" in keep_reason(self._ans(text="short [Fact 1]"), 0.75)
        assert "too few anchors" in keep_reason(self._ans(anchors_used=("[Fact 1]",)), 0.75)

    def test_deferral_is_not_training_data(self):
        assert "deferral" in keep_reason(self._ans(is_deferral=True), 0.75)

    def test_overlong_answer_is_rejected(self):
        """2026-07-29 crispness fix: the prior corpus had a floor (MIN_CHARS) but NO ceiling,
        so an unconstrained teacher's very long answers all passed unfiltered — exactly what
        taught the student its ~400-word default length against the new ~150-word target."""
        long_text = "word " * 250 + " ".join(f"[Fact {i}]" for i in range(1, MIN_ANCHORS + 1))
        r = keep_reason(self._ans(text=long_text), 0.75)
        assert r is not None and "too long" in r

    def test_too_many_paragraphs_is_rejected(self):
        """Mirrors EXPLAINER_SYSTEM's paragraph cap — a well-anchored, appropriately-short-per-
        paragraph answer can still be rejected for sprawling across too many paragraphs."""
        para = "Short grounded paragraph. [Fact 1]\n\n"
        text = para * 6 + "x" * MIN_CHARS
        r = keep_reason(self._ans(text=text), 0.75)
        assert r is not None and "too many paragraphs" in r

    def test_answer_within_both_limits_is_kept(self):
        """The ceiling doesn't hair-trigger on a genuinely crisp, well-formed answer."""
        text = ("The ruler of the nativity is Mercury [Fact 1], the strongest planet is the "
               "Sun [Fact 2], and the longevity band reads purna [Fact 3]. " * 3)
        assert len(text.split()) < MAX_WORDS
        assert keep_reason(self._ans(text=text), 0.75) is None


class TestJargonTermHits:
    """Mirrors EXPLAINER_SYSTEM's "NO EXPOSED PLUMBING" ban list (2026-07-29, after a candid
    review found the prose narrating engine internals instead of reading like Raman).
    Logged-only for now — must NEVER affect keep_reason's keep/reject decision."""

    def test_clean_text_has_no_hits(self):
        assert jargon_term_hits("The 4th house leans toward friction [Fact 8].") == {}

    def test_banned_terms_are_counted_case_insensitively(self):
        text = "Divided Witnesses support the headline verdict, per the WITNESSES on record."
        hits = jargon_term_hits(text)
        assert hits["witnesses"] == 2
        assert hits["headline"] == 1

    def test_jargon_hits_never_affect_keep_reason(self):
        """A jargon-heavy but otherwise clean, well-grounded answer is still KEPT — this stat
        is visibility only, not a gate (see build_analysis_corpus module docstring)."""
        from app.llm.report_explainer import GroundedAnswer
        text = (("The headline follows the weakest witnesses, a common outcomes pattern. "
                "[Fact 1] ") * 8)
        ans = GroundedAnswer(text=text, anchors_used=tuple(f"[Fact {i}]" for i in range(1, 4)),
                             grounding_ratio=1.0, gloss_ratio=0.0, ungrounded_sentences=(),
                             bad_anchors=(), fabricated_citations=(), forbidden_moves=(),
                             is_deferral=False, model="t", source="llm")
        assert keep_reason(ans, 0.75) is None
        assert jargon_term_hits(ans.text)                 # confirms this sample WOULD be flagged


class TestVoiceBlocks:
    def test_special_features_blocks_are_extracted(self):
        """Raman's 'Special Features. — ...' prose is captured up to the next heading."""
        text = ("intro\nSpecial Features. — The Lagna is Taurus and its lord occupies "
                + "a kendra in strength. " * 12 + "\n\n\nNEXT CHAPTER\n")
        blocks = voice_blocks(text)
        assert len(blocks) == 1
        assert blocks[0].startswith("The Lagna is Taurus")

    def test_tiny_fragments_are_dropped(self):
        assert voice_blocks("Special Features. — Too small.\n\n\nX") == []


class TestGoldenVoiceFragments:
    """2026-07-29: the user's own idea — lean on Raman's REAL authenticated words as voice
    anchors — applied to the golden-accuracy fixture (tests/fixtures/raman_goldens.jsonl), a
    much larger source (~389 fragments) than the existing 37-row Notable Horoscopes anchor set
    that alone wasn't enough to shift the model's voice."""

    def test_extracts_non_null_verdict_prose_from_multiple_rows(self, tmp_path):
        fixture = tmp_path / "goldens.jsonl"
        fixture.write_text(
            '{"expected_verdicts": {"H1": {"verdict_prose": "Tall, lean, saturnine."}}}\n'
            '{"expected_verdicts": {"H8": {"verdict_prose": "A full life, purna."}, '
            '"H2": {"verdict_prose": "Sound finances, no debt."}}}\n',
            encoding="utf-8")
        frags = golden_verdict_prose_fragments(fixture)
        assert frags == ["Tall, lean, saturnine.", "A full life, purna.",
                         "Sound finances, no debt."]

    def test_null_or_missing_verdict_prose_is_skipped(self, tmp_path):
        fixture = tmp_path / "goldens.jsonl"
        fixture.write_text(
            '{"expected_verdicts": {"H1": {"verdict_prose": null}}}\n'
            '{"expected_verdicts": {}}\n'
            '{}\n'
            '{"expected_verdicts": {"H3": {"verdict_prose": "Kept."}}}\n',
            encoding="utf-8")
        assert golden_verdict_prose_fragments(fixture) == ["Kept."]

    def test_malformed_and_comment_lines_are_skipped_not_fatal(self, tmp_path):
        """The real fixture carries an occasional `#`-prefixed section-marker comment line —
        extraction must skip it, not crash the whole batch."""
        fixture = tmp_path / "goldens.jsonl"
        fixture.write_text(
            '# --- NH Track-B DRAFT batch ---\n'
            '{"expected_verdicts": {"H1": {"verdict_prose": "Kept anyway."}}}\n'
            'not even close to json\n',
            encoding="utf-8")
        assert golden_verdict_prose_fragments(fixture) == ["Kept anyway."]

    def test_missing_file_returns_empty_not_an_error(self, tmp_path):
        assert golden_verdict_prose_fragments(tmp_path / "nope.jsonl") == []

    def test_real_fixture_has_a_substantial_fragment_pool(self):
        """Loose sanity bound on the actual repo fixture — catches it going missing or
        empty without pinning an exact count that would churn as the fixture grows."""
        assert len(golden_verdict_prose_fragments(GOLDEN_FIXTURES)) > 100


class TestSeedGoldenVoice:
    def test_writes_rows_with_the_expected_shape_and_is_idempotent(self, tmp_path):
        fixture = tmp_path / "goldens.jsonl"
        fixture.write_text(
            '{"expected_verdicts": {"H1": {"verdict_prose": "Tall, lean, saturnine."}}}\n',
            encoding="utf-8")
        out = tmp_path / "sft.jsonl"

        import app.medini.ml.build_analysis_corpus as bac
        original = bac.GOLDEN_FIXTURES
        bac.GOLDEN_FIXTURES = fixture
        try:
            n1 = seed_golden_voice(out)
            assert n1 == 1
            rows = [json.loads(l) for l in out.open(encoding="utf-8")]
            assert rows[0]["completion"] == "Tall, lean, saturnine."
            assert rows[0]["system"] == ""
            assert rows[0]["_meta"]["source"] == "raman_golden_voice"
            assert rows[0]["_meta"]["weight"] == 3

            n2 = seed_golden_voice(out)  # rerun: idempotent, no duplicate rows
            assert n2 == 0
            assert len(out.read_text(encoding="utf-8").splitlines()) == 1
        finally:
            bac.GOLDEN_FIXTURES = original

    def test_voice_weight_is_tunable_to_the_teacher_set_size(self, tmp_path):
        """The voice set is a FIXED 426 rows while the teacher half scales with --limit, so a
        hard-coded weight silently decides the style/grounding balance: weight 3 held 23.7% of
        the weighted token mass over 588 teacher rows (v2) but 41.6% over 248 (v3), tilting most
        of the gradient onto prose carrying no [Fact N] at all."""
        fixture = tmp_path / "goldens.jsonl"
        fixture.write_text(json.dumps(
            {"expected_verdicts": {"h1": {"verdict_prose": "Tall, lean, saturnine."}}}) + "\n",
            encoding="utf-8")
        out = tmp_path / "sft.jsonl"

        import app.medini.ml.build_analysis_corpus as bac
        original = bac.GOLDEN_FIXTURES
        bac.GOLDEN_FIXTURES = fixture
        try:
            seed_golden_voice(out, weight=1)
            rows = [json.loads(l) for l in out.open(encoding="utf-8")]
            assert rows[0]["_meta"]["weight"] == 1
        finally:
            bac.GOLDEN_FIXTURES = original


class TestDistilEndToEnd:
    def test_stub_distil_writes_rows_and_resumes(self, tmp_path):
        """A stub-backend distil pass writes valid SFT rows; a second pass skips them
        (resume), so a crashed batch never duplicates work. 100% of kept rows pass the
        guard by construction — asserted over the emitted file."""
        from app.llm.report_explainer import provenance_check, build_evidence
        chart = parse_dossier_row(_ROW)
        out = tmp_path / "sft.jsonl"
        # a stub whose reply passes the guard AND the quality bar
        from app.llm.client import StubClient, SystemPromptWrapper
        from app.llm.report_explainer import EXPLAINER_SYSTEM
        good = ("The engine reads the Virgo Lagna as the seat of the nativity [Fact 1]. "
                * 12 + "It assesses the ruler with care [Fact 2]. The reading stands as "
                "information content, not prophecy [Fact 3].")
        teacher = SystemPromptWrapper(StubClient(good), EXPLAINER_SYSTEM)

        s1 = distil([chart], ["summary"], teacher, out, min_grounding=0.6, backend="stub")
        assert s1["kept"] == 1 and s1["rejected"] == 0
        rows = [json.loads(l) for l in out.open(encoding="utf-8")]
        # The stub asserts "Virgo Lagna" while citing [Fact 1] (the RULER fact) — the exact
        # mis-attribution measured at 12.8% of the previous corpus's checkable sentences. The
        # stored completion is the REPAIRED text, so the student never learns the wrong pointer.
        assert s1["rows_repaired"] == 1 and s1["citation_repairs"] >= 1
        assert rows[0]["completion"] != good
        from app.llm.citation_support import audit_citations
        from app.raman_saab.chart.model import BirthData
        from app.raman_saab.detailed_report import build_detailed_report
        from app.raman_saab.report_json import to_report_dict
        ev = build_evidence(to_report_dict(build_detailed_report(BirthData(
            name="corpus", year=chart.year, month=chart.month, day=chart.day, hour=chart.hour,
            minute=chart.minute, tz_offset=chart.tz_offset, latitude=chart.latitude,
            longitude=chart.longitude))), "summary")
        assert audit_citations(rows[0]["completion"], ev).is_clean
        assert not audit_citations(good, ev).is_clean          # ...and it was NOT clean before
        assert rows[0]["_meta"]["scope"] == "summary"
        assert rows[0]["system"]                        # serve-time format: system carried

        s2 = distil([chart], ["summary"], teacher, out, min_grounding=0.6, backend="stub")
        assert s2["skipped_done"] == 1 and s2["kept"] == 0
        assert len(existing_keys(out)) == 1

    def test_source_label_reflects_the_actual_backend_not_hardcoded(self, tmp_path):
        """Regression pin for a real bug found live 2026-07-29: every kept row used to be
        hardcoded `_meta.source="teacher"` regardless of which backend produced it, so a $0
        smoke-test run (--backend ollama/stub) silently became indistinguishable from real
        Claude-teacher data — 85% of one corpus turned out to be mislabeled this way. Only
        backend="anthropic" may ever produce "teacher"; anything else is "smoke"."""
        from app.llm.client import StubClient, SystemPromptWrapper
        from app.llm.report_explainer import EXPLAINER_SYSTEM
        good = ("The engine reads the Virgo Lagna as the seat of the nativity [Fact 1]. "
                * 12 + "It assesses the ruler with care [Fact 2]. The reading stands as "
                "information content, not prophecy [Fact 3].")
        chart = parse_dossier_row(_ROW)

        teacher = SystemPromptWrapper(StubClient(good), EXPLAINER_SYSTEM)
        smoke_out = tmp_path / "smoke.jsonl"
        distil([chart], ["summary"], teacher, smoke_out, min_grounding=0.6, backend="stub")
        smoke_row = json.loads(smoke_out.read_text(encoding="utf-8").splitlines()[0])
        assert smoke_row["_meta"]["source"] == "smoke"

        anthropic_out = tmp_path / "anthropic.jsonl"
        distil([chart], ["summary"], teacher, anthropic_out, min_grounding=0.6,
              backend="anthropic")
        real_row = json.loads(anthropic_out.read_text(encoding="utf-8").splitlines()[0])
        assert real_row["_meta"]["source"] == "teacher"

    def test_jargon_hits_are_logged_but_row_is_still_kept(self, tmp_path):
        """A teacher answer that passes the guard AND quality bar but leans on banned
        engine-jargon is still KEPT (this is a visibility stat, not a reject) — and the
        run stats record which term(s) fired, for a later look at the real distribution."""
        from app.llm.client import StubClient, SystemPromptWrapper
        from app.llm.report_explainer import EXPLAINER_SYSTEM
        jargony = ("The headline reads favourable per the witnesses on record [Fact 1]. "
                  "The data structure supports this via common outcomes [Fact 2]. "
                  "This honest disclosure about the headline stands per the witnesses "
                  "[Fact 3]. ") * 3
        teacher = SystemPromptWrapper(StubClient(jargony), EXPLAINER_SYSTEM)
        out = tmp_path / "sft.jsonl"
        s = distil([parse_dossier_row(_ROW)], ["summary"], teacher, out, min_grounding=0.6,
                  backend="stub")
        assert s["kept"] == 1 and s["rejected"] == 0
        assert s["jargon_rows"] == 1
        assert s["jargon_hits"]["witnesses"] > 0 and s["jargon_hits"]["headline"] > 0

    def test_guard_failing_teacher_yields_zero_rows(self, tmp_path):
        """A teacher that predicts produces an EMPTY corpus, not a poisoned one."""
        from app.llm.client import StubClient, SystemPromptWrapper
        from app.llm.report_explainer import EXPLAINER_SYSTEM
        bad = "You will marry in 2027 and inherit wealth [Fact 1]. " * 20
        teacher = SystemPromptWrapper(StubClient(bad), EXPLAINER_SYSTEM)
        out = tmp_path / "sft.jsonl"
        s = distil([parse_dossier_row(_ROW)], ["summary"], teacher, out, min_grounding=0.6,
                  backend="stub")
        assert s["kept"] == 0 and s["rejected"] == 1
        assert not out.exists() or not out.read_text(encoding="utf-8").strip()


class TestMainCliGuard:
    """--allow-non-anthropic-teacher guard (2026-07-29): a $0 smoke-test backend must never
    silently write into what looks like a real corpus file — refuse by default, loudly."""

    def test_non_anthropic_backend_is_refused_by_default(self, tmp_path):
        from app.medini.ml.build_analysis_corpus import main
        import pytest as _pytest
        with _pytest.raises(SystemExit, match="smoke-test only"):
            main(["--backend", "stub", "--out", str(tmp_path / "sft.jsonl"), "--limit", "0"])

    @needs_file("app/medini/data/person_dossier.parquet")
    def test_non_anthropic_backend_proceeds_with_the_explicit_flag(self, tmp_path):
        from app.medini.ml.build_analysis_corpus import main
        # limit=0 -> no charts sampled, so this exercises only the guard-pass path, not a real
        # teacher call; confirms the flag actually unblocks execution past the guard.
        main(["--backend", "stub", "--out", str(tmp_path / "sft.jsonl"), "--limit", "0",
             "--allow-non-anthropic-teacher"])


class TestMakeTeacher:
    def test_stub_backend_builds_a_wrapped_client(self):
        t = make_teacher("stub")
        assert t.system                                  # carries the explainer system
        assert "[Fact 1]" in t.complete("x")
