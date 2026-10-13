from __future__ import annotations

import json
import shutil
from pathlib import Path

from tools.raman_saab.golden_pipeline import __main__ as CLI

FIX = Path(__file__).parent / "fixtures"


def _setup(tmp_path):
    src = tmp_path / "src" / "notable_horoscopes_raman"
    src.mkdir(parents=True)
    shutil.copy(FIX / "excerpt.md", src / "chapter_001_full-text-unsplit.md")
    g = tmp_path / "g.jsonl"
    g.write_text(json.dumps({"id": "NH.chart_1", "book": "NH", "citations": ["NH:6"],
                             "expected_verdicts": {"H4": {
                                 "signification": "mother", "verdict": "afflicted",
                                 "verdict_prose": "The native lost his mother very early in life",
                                 "verdict_review": "DRAFT"}}}) + "\n", encoding="utf-8")
    return g, tmp_path / "src", tmp_path / "runs"


class TestCli:
    def test_extract_then_packets_writes_a_and_b(self, tmp_path):
        """extract + packets produce two blind packets per pending item."""
        g, src, runs = _setup(tmp_path)
        assert CLI.main(["extract", "--input", str(g), "--run", "r1", "--runs-root", str(runs),
                         "--sources-root", str(src)]) == 0
        assert CLI.main(["packets", "--run", "r1", "--runs-root", str(runs),
                         "--sources-root", str(src)]) == 0
        names = sorted(p.name for p in (runs / "r1" / "packets").iterdir())
        assert names == ["NH.chart_1__H4.A.md", "NH.chart_1__H4.B.md"]

    def test_missing_lists_unanswered(self, tmp_path, capsys):
        """`packets --missing` names packets without answers for re-dispatch."""
        g, src, runs = _setup(tmp_path)
        CLI.main(["extract", "--input", str(g), "--run", "r1", "--runs-root", str(runs),
                  "--sources-root", str(src)])
        CLI.main(["packets", "--run", "r1", "--runs-root", str(runs), "--sources-root", str(src)])
        CLI.main(["packets", "--run", "r1", "--runs-root", str(runs), "--sources-root", str(src),
                  "--missing"])
        assert "NH.chart_1__H4.A.md" in capsys.readouterr().out
