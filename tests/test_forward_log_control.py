"""Forward log: the swapped-chart control (pre-registration addendum 5)."""

from __future__ import annotations

import pytest

from tools.predictive import forward_log as fl

ASK = ["ask", "--text", "Will the deal close?", "--area", "wealth", "--matter", "house11", "--number", "35",
       "--when", "2026-11-05 10:42", "--tz", "5.5", "--lat", "28.6139", "--lon", "77.209", "--prior", "0.5",
       "--quarter", "2027Q1", "--window", "2026-11-05:2027-11-04"]


class TestSwappedAnswers:
    def test_ask_locks_twenty_other_numbers(self, tmp_path) -> None:
        """Each question seals 20 distinct swapped horary numbers, never the asker's own, inside the hash."""
        log = tmp_path / "log.jsonl"
        fl.main([*ASK, "--log", str(log)])
        d = fl.read(log)[0]["decoys"]
        assert len(d["numbers"]) == len(set(d["numbers"])) == fl.N_DECOYS == len(d["verdicts"])
        assert 35 not in d["numbers"] and all(1 <= n <= 249 for n in d["numbers"])
        assert fl.cmd_verify(type("A", (), {"log": log})())

    def test_add_decoys_once_and_only_before_resolution(self, tmp_path) -> None:
        """Older entries get swaps as a chained record; never twice, never after the outcome is known."""
        log = tmp_path / "log.jsonl"
        fl.main([*ASK, "--log", str(log)])
        e = fl.read(log)
        e[0].pop("decoys")
        e[0]["hash"] = fl._hash(e[0])
        log.write_text(fl.json.dumps(e[0], sort_keys=True) + "\n")
        fl.main(["add-decoys", "--log", str(log), "--id", "1"])
        with pytest.raises(SystemExit):
            fl.main(["add-decoys", "--log", str(log), "--id", "1"])
        assert fl.cmd_verify(type("A", (), {"log": log})())


class TestControlStatistic:
    def test_always_right_real_chart_beats_coin_swaps(self) -> None:
        """A real chart right on all 40 questions against half-right swaps gives a tiny p."""
        rows = [{"yes": True, "real": True, "swaps": [True] * 10 + [False] * 10} for _ in range(40)]
        c = fl.control(rows, draws=20_000)
        assert c["real_accuracy"] == 1.0 and abs(c["swapped_mean_accuracy"] - 0.5) < 1e-9
        assert c["p"] < 0.001 and c["difference_ci95"][0] > 0.4

    def test_real_chart_like_its_swaps_is_not_significant(self) -> None:
        """When the real answer is just another swap, p is not small."""
        rows = [{"yes": i % 2 == 0, "real": True, "swaps": [True] * 10 + [False] * 10} for i in range(40)]
        assert fl.control(rows, draws=20_000)["p"] > 0.2

    def test_score_reports_control_blocks(self, tmp_path) -> None:
        """score() carries the horary control once a question is resolved."""
        log = tmp_path / "log.jsonl"
        fl.main([*ASK, "--log", str(log)])
        rows = [*fl.read(log), {"type": "resolve", "id": 1, "outcome": "yes", "event_date": "2027-02-10"}]
        sc = fl.score(rows)
        real = fl.as_decided(rows[0]["judgment"]["verdict"])
        assert sc["control_horary"]["questions"] == (0 if real is None else 1)
        assert sc["control_natal"] == {"questions": 0}
