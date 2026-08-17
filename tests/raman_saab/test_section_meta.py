"""The per-section plain-language layer (section_meta) stays honest and complete.

Three guarantees: (1) every English string passes the decree/forecast guard —
subtitles describe what a section examines, never assert a future life event;
(2) both languages are always present (the EN+HI-together decision, 2026-08-17);
(3) keys stay within the section contract plus the declared page-only set, so a
typo'd id fails loudly instead of silently rendering nothing.
"""
from __future__ import annotations

import pytest

from app.llm.report_explainer import _FORBIDDEN_RE
from app.raman_saab.detailed_report import SECTION_CONTRACT
from app.raman_saab.section_meta import _PAGE_ONLY_IDS, SECTION_META, section_meta_json


class TestSectionMeta:
    def test_every_english_string_passes_the_decree_guard(self):
        """No subtitle or answers line asserts a future life event (guard-clean)."""
        for sid, m in SECTION_META.items():
            for text in (m.subtitle_en, m.answers_en):
                hit = _FORBIDDEN_RE.search(text)
                assert hit is None, f"{sid}: guard tripped on {hit.group(0)!r} in {text!r}"

    def test_both_languages_always_present(self):
        """EN and HI are both non-empty for every field of every entry."""
        for sid, m in SECTION_META.items():
            assert m.subtitle_en.strip() and m.subtitle_hi.strip(), sid
            assert m.answers_en.strip() and m.answers_hi.strip(), sid

    def test_keys_stay_within_contract_plus_page_only(self):
        """Every key is a real SECTION_CONTRACT id or a declared page-only id."""
        contract_ids = {s.section_id for s in SECTION_CONTRACT}
        for sid in SECTION_META:
            assert sid in contract_ids or sid in _PAGE_ONLY_IDS, (
                f"{sid} is neither a contract section id nor in _PAGE_ONLY_IDS")

    def test_steps_are_reading_order_steps(self):
        """step is 0 (appendix) or one of interpretation_guide's five reading steps."""
        for sid, m in SECTION_META.items():
            assert 0 <= m.step <= 5, f"{sid}: step {m.step}"

    def test_method_not_prediction_idiom_kept_where_mandatory(self):
        """The sensitive sections keep the standing 'method, not a prediction' frame."""
        for sid in ("longevity", "maraka", "maraka_saturn"):
            joined = (SECTION_META[sid].subtitle_en + " " + SECTION_META[sid].answers_en).lower()
            assert "method" in joined and "prediction" not in joined.replace(
                "not a prediction", ""), sid

    def test_json_shape_round_trips(self):
        """section_meta_json mirrors the dataclass fields exactly, per entry."""
        j = section_meta_json()
        assert set(j) == set(SECTION_META)
        sample = j["plain_reading"]
        assert set(sample) == {"subtitle_en", "subtitle_hi", "answers_en",
                               "answers_hi", "step", "explain_scope"}
        assert sample["explain_scope"] == "summary"
