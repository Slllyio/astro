"""CLI smoke — the new -> add-event -> add-fact -> run -> status verb sequence works
in-process on a tmp session file, and bad inputs exit loudly with hints.
"""
from __future__ import annotations

import pytest

from tools.raman_saab.rectify import main


def test_full_verb_sequence(tmp_path, capsys) -> None:
    """End-to-end CLI drive on the anonymized rect-case inputs."""
    s = str(tmp_path / "s.json")
    assert main(["new", "--session", s, "--mode", "rectify", "--date", "1989-10-12",
                 "--time", "10:02", "--window-min", "15", "--tz", "5.5",
                 "--lat", "27.23", "--lon", "79.03"]) == 0
    assert main(["add-event", "--session", s, "--type", "marriage",
                 "--date", "2017-12-04"]) == 0
    assert main(["add-event", "--session", s, "--type", "career_start",
                 "--date", "2016-02"]) == 0
    assert main(["add-fact", "--session", s, "--subject", "mother",
                 "--observed", "afflicted"]) == 0
    assert main(["run", "--session", s, "--top", "4"]) == 0
    out = capsys.readouterr().out
    assert "RECTIFICATION REPORT" in out
    assert "raman" in out and "lahiri" in out          # dual-track mandate
    assert "VERDICT" in out
    assert main(["status", "--session", s]) == 0
    out = capsys.readouterr().out
    assert "round 1" in out and "2ev/1fa" in out


def test_unknown_event_type_exits_with_hint(tmp_path) -> None:
    """An untypeable event is a hard exit listing valid types + a nearest-match hint."""
    s = str(tmp_path / "s.json")
    main(["new", "--session", s, "--mode", "rectify", "--date", "1989-10-12",
          "--time", "10:02", "--tz", "5.5", "--lat", "27.23", "--lon", "79.03"])
    with pytest.raises(SystemExit, match="mariage|valid types"):
        main(["add-event", "--session", s, "--type", "mariage", "--date", "2017"])
