from __future__ import annotations

from tools.raman_saab.golden_pipeline.acceptance import answer_key, compare


def _rec(review, verdict="mixed", sig="mother"):
    return {"id": "X", "expected_verdicts": {"H4": {
        "verdict_review": review, "verdict": verdict, "signification": sig}}}


class TestAnswerKey:
    def test_draft_to_confirmed_same_label_is_confirm(self):
        """Unchanged label promoted = CONFIRM."""
        assert answer_key([_rec("DRAFT")], [_rec("CONFIRMED")]) == {"X#H4": "CONFIRM"}

    def test_draft_to_confirmed_new_label_is_revise(self):
        """Label changed on promotion = REVISE."""
        assert answer_key([_rec("DRAFT")], [_rec("CONFIRMED", "afflicted")]) == {"X#H4": "REVISE"}

    def test_draft_stays_draft_is_reject(self):
        """Not promoted = REJECT."""
        assert answer_key([_rec("DRAFT")], [_rec("DRAFT")]) == {"X#H4": "REJECT"}

    def test_compare_counts_agreement_and_lists_divergence(self):
        """Every divergence is listed for reading by hand."""
        agree, div = compare({"a": "CONFIRM", "b": "REJECT"},
                             {"a": "CONFIRM", "b": "CONFIRM"})
        assert agree == 1 and div == [("b", "REJECT", "CONFIRM")]
