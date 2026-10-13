from __future__ import annotations

import json

from tools.raman_saab.golden_pipeline import extract as E
from tools.raman_saab.golden_pipeline import runs as R


def _rec(rid, verdicts, citations=("NH:10",)):
    return {"id": rid, "book": "NH", "case_type": "worked_example",
            "citations": list(citations), "expected_verdicts": verdicts}


def _v(review, note=None, verdict="mixed"):
    d = {"signification": "mother", "verdict": verdict,
         "verdict_prose": "the native lost his mother", "verdict_review": review}
    if note:
        d["review_note"] = note
    return d


class TestSelectPending:
    def test_draft_verdict_is_selected(self):
        """A DRAFT verdict is pending adjudication."""
        items = E.select_pending([_rec("NH.chart_1", {"H4": _v("DRAFT")})])
        assert [i["item_id"] for i in items] == ["NH.chart_1#H4"]

    def test_confirmed_and_terminal_states_are_skipped(self):
        """CONFIRMED / DUPLICATE / CONTESTED are already adjudicated."""
        rec = _rec("NH.chart_1", {"H1": _v("CONFIRMED"), "H2": _v("DUPLICATE"),
                                  "H3": _v("CONTESTED")})
        assert E.select_pending([rec]) == []

    def test_rejected_draft_is_not_requeued(self):
        """A DRAFT carrying a REJECTED review_note was adjudicated and must not return."""
        rec = _rec("NH.chart_1", {"H4": _v("DRAFT", note="REJECTED by engine-blind review x")})
        assert E.select_pending([rec]) == []

    def test_item_carries_proposed_fields_and_citation(self):
        """The item holds exactly what a reviewer needs and nothing from the engine."""
        item = E.select_pending([_rec("NH.chart_1", {"H4": _v("DRAFT")})])[0]
        assert item == {"item_id": "NH.chart_1#H4", "record_id": "NH.chart_1", "house": 4,
                        "book": "NH", "citation": "NH:10", "citations": ["NH:10"], "signification": "mother",
                        "verdict": "mixed", "verdict_prose": "the native lost his mother"}

    def test_all_citations_carried_first_kept(self):
        """Several citations travel on the item; 'citation' stays the first."""
        item = E.select_pending([_rec("NH.chart_1", {"H4": _v("DRAFT")},
                                      citations=("NH:10", "NH:900"))])[0]
        assert item["citation"] == "NH:10" and item["citations"] == ["NH:10", "NH:900"]

    def test_record_without_citation_is_skipped(self):
        """No citation means no source passage, so it cannot be reviewed."""
        assert E.select_pending([_rec("NH.chart_1", {"H4": _v("DRAFT")}, citations=())]) == []


class TestRuns:
    def test_jsonl_roundtrip_and_idempotent_rewrite(self, tmp_path):
        """Stage files round-trip and re-writing replaces, never appends duplicates."""
        p = tmp_path / "x.jsonl"
        R.write_jsonl(p, [{"a": 1}])
        R.write_jsonl(p, [{"a": 1}, {"a": 2}])
        assert R.read_jsonl(p) == [{"a": 1}, {"a": 2}]

    def test_load_goldens_skips_comments(self, tmp_path):
        """The fixture's # comment lines are not records."""
        p = tmp_path / "g.jsonl"
        p.write_text("# note\n" + json.dumps({"id": "x"}) + "\n\n", encoding="utf-8")
        assert R.load_goldens(p) == [{"id": "x"}]
