"""Tests for app.medini.etl._freshness.skip_if_fresh."""
from __future__ import annotations

import os
import time
from pathlib import Path

from app.medini.etl._freshness import skip_if_fresh


def _touch(p: Path, mtime: float | None = None) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("x")
    if mtime is not None:
        os.utime(p, (mtime, mtime))


class TestSkipIfFresh:
    def test_output_missing_means_rebuild(self, tmp_path: Path):
        """No output file → must rebuild."""
        inp = tmp_path / "input.parquet"
        out = tmp_path / "output.parquet"
        _touch(inp)
        assert skip_if_fresh(out, [inp]) is False

    def test_output_newer_skips(self, tmp_path: Path):
        """Output newer than all inputs → skip."""
        inp = tmp_path / "input.parquet"
        out = tmp_path / "output.parquet"
        now = time.time()
        _touch(inp, mtime=now - 100)
        _touch(out, mtime=now)
        assert skip_if_fresh(out, [inp]) is True

    def test_input_newer_means_rebuild(self, tmp_path: Path):
        """One input newer than output → rebuild."""
        inp1 = tmp_path / "in1.parquet"
        inp2 = tmp_path / "in2.parquet"
        out = tmp_path / "output.parquet"
        now = time.time()
        _touch(inp1, mtime=now - 100)
        _touch(out, mtime=now - 50)
        _touch(inp2, mtime=now)  # newer than output
        assert skip_if_fresh(out, [inp1, inp2]) is False

    def test_missing_input_means_rebuild(self, tmp_path: Path):
        """Caller's input doesn't exist → don't skip (caller will error)."""
        inp = tmp_path / "missing.parquet"
        out = tmp_path / "output.parquet"
        _touch(out)
        assert skip_if_fresh(out, [inp]) is False

    def test_force_always_rebuilds(self, tmp_path: Path):
        """--force / force=True bypasses freshness."""
        inp = tmp_path / "input.parquet"
        out = tmp_path / "output.parquet"
        now = time.time()
        _touch(inp, mtime=now - 100)
        _touch(out, mtime=now)
        assert skip_if_fresh(out, [inp], force=True) is False

    def test_empty_inputs_skips_when_output_exists(self, tmp_path: Path):
        """No inputs to compare → if output exists, treat as fresh."""
        out = tmp_path / "output.parquet"
        _touch(out)
        assert skip_if_fresh(out, []) is True

    def test_works_with_generator_inputs(self, tmp_path: Path):
        """Generator inputs are consumed exactly once internally."""
        inp = tmp_path / "input.parquet"
        out = tmp_path / "output.parquet"
        now = time.time()
        _touch(inp, mtime=now - 100)
        _touch(out, mtime=now)
        assert skip_if_fresh(out, (p for p in [inp])) is True
