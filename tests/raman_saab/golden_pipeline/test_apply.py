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


def _rec(review="DRAFT", note=None):
    v = {**REC["expected_verdicts"]["H4"], "verdict_review": review}
    if note:
        v["review_note"] = note
    return json.dumps({**REC, "expected_verdicts": {"H4": v}})


def _conf():
    return _dec("CONFIRMED", verdict="afflicted", signification="mother", revised=False)


class TestGuards:
    @pytest.mark.parametrize("line", [_rec("CONFIRMED"), _rec("DUPLICATE"),
                                      _rec(note="REJECTED earlier")])
    def test_non_draft_or_rejected_target_refused(self, line):
        """Only a live DRAFT may be written; settled rows are never re-judged."""
        with pytest.raises(ValueError):
            AP.edit_goldens_lines([line], [_conf()], "r1")

    def test_prior_note_is_appended(self):
        """An existing review_note is kept and extended."""
        out = AP.edit_goldens_lines([_rec(note="old note")], [_conf()], "r1")
        n = json.loads(out[0])["expected_verdicts"]["H4"]["review_note"]
        assert n.startswith("old note | CONFIRM by")

    def test_unmatched_decision_raises(self):
        """A decision that hit no line is an error, not a silent no-op."""
        d = {**_conf(), "record_id": "NH.nope", "item_id": "NH.nope#H4"}
        with pytest.raises(ValueError, match="NH.nope#H4"):
            AP.edit_goldens_lines(LINES, [d], "r1")

    def test_missing_house_raises(self):
        """Record found but house absent is also unmatched."""
        d = {**_conf(), "house": 9, "item_id": "NH.chart_1#H9"}
        with pytest.raises(ValueError, match="H9"):
            AP.edit_goldens_lines(LINES, [d], "r1")

    def test_duplicate_item_id_raises(self):
        """The same item twice would double-apply."""
        with pytest.raises(ValueError, match="duplicate"):
            AP.edit_goldens_lines(LINES, [_conf(), _conf()], "r1")


class TestPaths:
    def test_goldens_anchored_absolute(self):
        """Paths must not depend on cwd."""
        assert AP.GOLDENS.is_absolute()
        assert AP.GOLDENS.as_posix().endswith("tests/fixtures/raman_goldens.jsonl")


class TestRunApplyFlow:
    def test_snapshot_env_not_set_and_restore_on_keyboardinterrupt(self, tmp_path, monkeypatch):
        """No UPDATE_RAMAN_SNAPSHOTS anywhere; BaseException restores both files."""
        g, b, bl = tmp_path / "g.jsonl", tmp_path / "b.json", tmp_path / "bl.md"
        g.write_text(_rec(), encoding="utf-8")
        b.write_text("{}", encoding="utf-8")
        bl.write_text("", encoding="utf-8")
        for n, p in (("GOLDENS", g), ("BASELINE", b), ("BACKLOG", bl)):
            monkeypatch.setattr(AP, n, p)
        monkeypatch.setattr(AP, "_git_status", lambda: "")
        monkeypatch.setattr(AP, "measure", lambda: ((1, 2), (2, 2)))
        calls = []

        def fake_pytest(*a, env=None):
            calls.append(env)
            raise KeyboardInterrupt

        monkeypatch.setattr(AP, "_pytest", fake_pytest)
        before = g.read_text(encoding="utf-8")
        with pytest.raises(KeyboardInterrupt):
            AP.run_apply([_conf()], "r1", "2026-10-13")
        assert g.read_text(encoding="utf-8") == before and b.read_text(encoding="utf-8") == "{}"
        assert calls == [None]
