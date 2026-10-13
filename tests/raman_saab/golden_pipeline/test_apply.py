from __future__ import annotations

import json

import pytest

from tools.raman_saab.golden_pipeline import apply as AP

REC = {"id": "NH.chart_1", "expected_verdicts": {"H4": {
    "signification": "mother", "verdict": "afflicted", "verdict_prose": "p",
    "verdict_review": "DRAFT"}}}
OTHER = {"id": "NH.chart_2", "expected_verdicts": {}}
LINES = ["# a comment block line", json.dumps(REC, ensure_ascii=False),
         json.dumps(OTHER, ensure_ascii=False), ""]


def _dec(outcome, **kw):
    return {"item_id": "NH.chart_1#H4", "record_id": "NH.chart_1", "house": 4,
            "outcome": outcome, "quotes": {"A": ["q", 6]}, **kw}


class TestEditLines:
    def test_comments_and_untouched_rows_survive_byte_for_byte(self):
        """Line-level edit: '#' blocks and other records are not re-serialised."""
        out = AP.edit_goldens_lines(LINES, [_dec("CONFIRMED", verdict="afflicted",
                                                 signification="mother", revised=False)], "r1")
        assert out[0] == LINES[0] and out[2] == LINES[2] and out[3] == LINES[3]

    def test_confirm_changes_only_review_fields(self):
        """CONFIRMED sets verdict_review + review_note and nothing else."""
        out = AP.edit_goldens_lines(LINES, [_dec("CONFIRMED", verdict="afflicted",
                                                 signification="mother", revised=False)], "r1")
        v = json.loads(out[1])["expected_verdicts"]["H4"]
        assert v["verdict_review"] == "CONFIRMED" and "r1" in v["review_note"]
        assert {k: v[k] for k in ("signification", "verdict", "verdict_prose")} == \
               {"signification": "mother", "verdict": "afflicted", "verdict_prose": "p"}

    def test_revise_changes_verdict_and_signification(self):
        """A REVISE'd confirmation carries the corrected label."""
        out = AP.edit_goldens_lines(LINES, [_dec("CONFIRMED", verdict="mixed",
                                                 signification="parents", revised=True)], "r1")
        v = json.loads(out[1])["expected_verdicts"]["H4"]
        assert (v["verdict"], v["signification"]) == ("mixed", "parents")

    def test_rejected_stays_draft_with_rejected_note(self):
        """REJECTED keeps DRAFT and writes the note that stops re-queueing."""
        out = AP.edit_goldens_lines(LINES, [_dec("REJECTED")], "r1")
        v = json.loads(out[1])["expected_verdicts"]["H4"]
        assert v["verdict_review"] == "DRAFT" and v["review_note"].startswith("REJECTED")

    def test_contested_sets_state(self):
        """No-majority items become CONTESTED."""
        out = AP.edit_goldens_lines(LINES, [_dec("CONTESTED")], "r1")
        assert json.loads(out[1])["expected_verdicts"]["H4"]["verdict_review"] == "CONTESTED"

    def test_unscorable_outcomes_are_refused(self):
        """INCOMPLETE / TIEBREAK / UNVERIFIED are never written."""
        with pytest.raises(ValueError):
            AP.edit_goldens_lines(LINES, [_dec("TIEBREAK")], "r1")


class TestLineage:
    def test_both_floors_updated_and_lineage_appended(self):
        """Two-axis baseline, history preserved, never replaced."""
        base = {"_comment": "old", "track_b": {"correct": 1, "total": 2},
                "_comment_ordinal": "oldo", "track_b_ordinal": {"correct": 2, "total": 2}}
        new = AP.append_lineage(base, (3, 5), (4, 5), "r1", "2026-10-13")
        assert new["track_b"] == {"correct": 3, "total": 5}
        assert new["track_b_ordinal"] == {"correct": 4, "total": 5}
        assert new["_comment"].startswith("old") and "r1" in new["_comment"]
        assert new["_comment_ordinal"].startswith("oldo") and "user-signed" in new["_comment_ordinal"]
        assert base["_comment"] == "old"  # input not mutated


class TestCleanTree:
    def test_apply_refuses_dirty_tree(self, monkeypatch):
        """No mixing with another session's uncommitted edits."""
        monkeypatch.setattr(AP, "_git_status", lambda: " M some/file.py\n")
        with pytest.raises(AP.DirtyTree):
            AP.require_clean_tree()
