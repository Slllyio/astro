"""Forward log: the optional natal KP block (consent, sealing, scoring against the asker's quarter)."""

from __future__ import annotations

import json

import pytest

from tools.predictive import forward_log as fl

ASK = ["ask", "--text", "Will I change jobs?", "--area", "career", "--matter", "service", "--number", "117",
       "--when", "2026-11-03 10:42", "--tz", "5.5", "--lat", "26.45", "--lon", "80.33", "--prior", "0.6",
       "--quarter", "2027Q1", "--window", "2026-11-03:2028-11-02"]
BIRTH = ["--birth", "1990-07-15 12:00", "--birth-tz", "5.5", "--birth-lat", "12.97", "--birth-lon", "77.59",
         "--birth-matter", "service"]


class TestNatalBlock:
    def test_default_stores_no_birth_data(self, tmp_path) -> None:
        """Without --birth the entry has no natal block and no birth fields."""
        log = tmp_path / "log.jsonl"
        fl.main([*ASK, "--log", str(log)])
        e = fl.read(log)[0]
        assert "natal" not in e and "birth" not in json.dumps(e)

    def test_birth_without_consent_is_refused(self, tmp_path) -> None:
        """Birth data is stored only with the asker's consent."""
        with pytest.raises(SystemExit):
            fl.main([*ASK, *BIRTH, "--log", str(tmp_path / "log.jsonl")])

    def test_natal_block_is_sealed_and_scored(self, tmp_path) -> None:
        """Bangalore 1990-07-15 12:00: the R26 selection, windows and quarter are in the hashed entry."""
        log = tmp_path / "log.jsonl"
        fl.main([*ASK, *BIRTH, "--consent-birth", "--log", str(log)])
        e = fl.read(log)[0]
        n = e["natal"]
        assert n["selection"]["ruling_planets"] is not None
        assert n["verdict"] in ("YES", "NO") and 0 <= n["window_coverage"] <= 1
        assert (n["quarter"] is None) == (n["verdict"] == "NO")
        assert fl.cmd_verify(type("A", (), {"log": log})())
        ev = n["windows"][0][0] if n["windows"] else "2027-02-10"
        rows = [*fl.read(log), {"type": "resolve", "id": 1, "outcome": "yes", "event_date": ev}]
        sc = fl.score(rows)["natal"]
        assert sc["with_birth_data"] == 1 and sc["events_that_happened"] == 1
        assert sc["event_inside_kp_window"] == (1 if n["windows"] else 0)
