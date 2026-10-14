"""Synthesis report card — the yardstick itself must stay runnable and honest.

Does not pin the score (it is the engine's honest output, free to move with doctrine); pins that the
card covers every synthesis verdict, skips rather than stubs positions-only charts, and scores.
"""
from __future__ import annotations

from app.parashara.doctrine.sources import Citation, verify
from tools.parashara.synthesis_report_card import (
    SYNTH_TO_RAMAN, score, score_bphs, score_field_case)
from app.parashara.synthesis.judgment import VERDICT_MEANING


class TestReportCard:
    def test_mapping_covers_every_synthesis_verdict(self):
        """Every verdict the synthesis can emit has an explicit mapping (or abstention)."""
        assert set(SYNTH_TO_RAMAN) == set(VERDICT_MEANING)

    def test_scores_a_sample_with_baselines(self):
        """A small run scores verdicts and carries the older judges' baselines on the same set."""
        s = score(limit=12)
        assert s["total"] >= 12
        assert 0 <= s["exact"] <= s["within1"] <= s["total"]
        assert set(s["baselines"]) == {"ch11", "richer"}
        assert sum(s["confusion"].values()) == s["total"]

    def test_field_case_scores_every_verdict_and_event_with_chance(self):
        """Track 2 scores all 50 owner-confirmed verdicts and all 14 dated events, each event
        carrying its chance rate (so a timing hit is never read without its base rate)."""
        f = score_field_case()
        assert f["static_total"] == 50
        assert len(f["events"]) == 14
        assert all(0.0 <= e["chance"] <= 1.0 for e in f["events"])

    def test_bphs_track_scores_every_assertion_with_resolving_citations(self):
        """Track 3 scores all 12 BPHS-note assertions, each pinned to a real corpus line."""
        t = score_bphs()
        assert len(t["rows"]) == 12
        assert t["agree"] + t["partial"] + t["disagree"] == 12
        for r in t["rows"]:
            work, _, line = r["citation"].rpartition(":")
            assert verify(Citation(work, int(line))), r["citation"]
