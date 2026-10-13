from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

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


class TestNotLocated:
    def test_not_located_gets_no_packet_and_is_counted(self, tmp_path, capsys):
        """An item whose passage cannot be found is never sent to reviewers."""
        g, src, runs = _setup(tmp_path)
        rec = json.loads(g.read_text(encoding="utf-8"))
        rec["expected_verdicts"]["H4"]["verdict_prose"] = "words absent from the whole book"
        rec["id"] = "NH.chart_99"
        g.write_text(json.dumps(rec) + "\n", encoding="utf-8")
        CLI.main(["extract", "--input", str(g), "--run", "r1", "--runs-root", str(runs),
                  "--sources-root", str(src)])
        CLI.main(["packets", "--run", "r1", "--runs-root", str(runs), "--sources-root", str(src)])
        pk = runs / "r1" / "packets"
        assert not pk.exists() or not any(pk.iterdir())
        capsys.readouterr()
        CLI.main(["status", "--run", "r1", "--runs-root", str(runs)])
        assert "NOT_LOCATED: 1" in capsys.readouterr().out


class TestGuards:
    def _run(self, tmp_path, monkeypatch, rows):
        from tools.raman_saab.golden_pipeline import runs as R
        runs = tmp_path / "runs"
        R.write_jsonl(R.run_dir("r1", runs) / "decisions.jsonl", rows)
        called = []
        monkeypatch.setattr(CLI, "run_apply", lambda *a, **k: called.append(a))
        return runs, called

    def test_apply_needs_ids_or_all(self, tmp_path, monkeypatch):
        """No selector -> argparse error, nothing applied."""
        runs, called = self._run(tmp_path, monkeypatch, [])
        with pytest.raises(SystemExit):
            CLI.main(["apply", "--run", "r1", "--runs-root", str(runs)])
        with pytest.raises(SystemExit):
            CLI.main(["apply", "--run", "r1", "--runs-root", str(runs), "--ids", "a", "--all"])
        assert called == []

    def test_apply_bad_id_exits_nonzero_before_writing(self, tmp_path, monkeypatch):
        """Missing or non-writable id -> exit 2, run_apply never called."""
        rows = [{"item_id": "a", "outcome": "CONFIRMED"}, {"item_id": "b", "outcome": "TIEBREAK"}]
        runs, called = self._run(tmp_path, monkeypatch, rows)
        for ids in ("a,zzz", "a,b"):
            assert CLI.main(["apply", "--run", "r1", "--runs-root", str(runs), "--ids", ids]) == 2
        assert called == []
        assert CLI.main(["apply", "--run", "r1", "--runs-root", str(runs), "--ids", "a"]) == 0
        assert len(called) == 1

    def test_tiebreak_without_decisions_fails(self, tmp_path):
        """--tiebreak before ingest is an error."""
        g, src, runs = _setup(tmp_path)
        CLI.main(["extract", "--input", str(g), "--run", "r1", "--runs-root", str(runs),
                  "--sources-root", str(src)])
        assert CLI.main(["packets", "--run", "r1", "--runs-root", str(runs),
                         "--sources-root", str(src), "--tiebreak"]) != 0

    def test_run_required_except_extract(self, tmp_path):
        """Non-extract stages without --run are an argparse error."""
        with pytest.raises(SystemExit):
            CLI.main(["ingest", "--runs-root", str(tmp_path)])
