from __future__ import annotations

from tools.raman_saab.golden_pipeline.reconcile import reconcile

ITEM = {"verdict": "afflicted", "signification": "mother"}


def ans(decision="CONFIRM", verdict="afflicted", sig="mother", ok=True):
    return {"decision": decision, "verdict": verdict, "signification": sig,
            "quote_ok": ok, "decisive_quote": "q", "quote_line": 1}


class TestReconcile:
    def test_both_confirm_same_label_confirms(self):
        """Agreement on decision + verdict + signification scores the row."""
        r = reconcile(ITEM, {"A": ans(), "B": ans()})
        assert r["outcome"] == "CONFIRMED" and r["revised"] is False

    def test_both_revise_same_label_confirms_revised(self):
        """Agreed REVISE confirms with the corrected label."""
        r = reconcile(ITEM, {"A": ans("REVISE", "mixed"), "B": ans("REVISE", "mixed")})
        assert (r["outcome"], r["verdict"], r["revised"]) == ("CONFIRMED", "mixed", True)

    def test_reviewers_disagree_goes_to_tiebreak(self):
        """A split is never scored directly."""
        r = reconcile(ITEM, {"A": ans(), "B": ans("REVISE", "mixed")})
        assert r["outcome"] == "TIEBREAK"

    def test_single_reject_goes_to_tiebreak(self):
        """One dissent blocks confirmation pending a third reading."""
        assert reconcile(ITEM, {"A": ans(), "B": ans("REJECT", None)})["outcome"] == "TIEBREAK"

    def test_both_reject_is_rejected(self):
        """Agreed REJECT keeps DRAFT with a REJECTED note."""
        r = reconcile(ITEM, {"A": ans("REJECT", None), "B": ans("REJECT", None)})
        assert r["outcome"] == "REJECTED"

    def test_tiebreak_two_of_three_decides(self):
        """2-of-3 agreement resolves (NH.chart_38 precedent)."""
        r = reconcile(ITEM, {"A": ans(), "B": ans("REVISE", "mixed"), "C": ans()})
        assert (r["outcome"], r["verdict"]) == ("CONFIRMED", "afflicted")

    def test_three_way_split_is_contested(self):
        """No majority -> CONTESTED, never scored."""
        r = reconcile(ITEM, {"A": ans(), "B": ans("REVISE", "mixed"), "C": ans("REJECT", None)})
        assert r["outcome"] == "CONTESTED"

    def test_unverified_quote_stays_draft(self):
        """A quote not found in the source cannot support any outcome."""
        assert reconcile(ITEM, {"A": ans(ok=False), "B": ans()})["outcome"] == "UNVERIFIED"

    def test_missing_answer_is_incomplete(self):
        """Both A and B are required."""
        assert reconcile(ITEM, {"A": ans()})["outcome"] == "INCOMPLETE"

    def test_no_path_confirms_without_agreement(self):
        """Invariant: every failure path ends unscored."""
        for answers in ({"A": ans()}, {"A": ans(ok=False), "B": ans(ok=False)},
                        {"A": ans(), "B": ans("REJECT", None)}):
            assert reconcile(ITEM, answers)["outcome"] != "CONFIRMED"
