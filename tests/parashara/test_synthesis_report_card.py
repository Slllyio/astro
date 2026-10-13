"""Synthesis report card — the yardstick itself must stay runnable and honest.

Does not pin the score (it is the engine's honest output, free to move with doctrine); pins that the
card covers every synthesis verdict, skips rather than stubs positions-only charts, and scores.
"""
from __future__ import annotations

from tools.parashara.synthesis_report_card import SYNTH_TO_RAMAN, score
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
