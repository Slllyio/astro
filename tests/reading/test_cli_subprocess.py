"""End-to-end subprocess tests for `app.reading.cli`.

These tests invoke the CLI as a real `python -m app.reading.cli` subprocess
(spec Section 17 item 1: subprocess test is mandatory). They lock the
process-boundary contract that consumers depend on:

- stdout = valid JSON readable by `json.loads`.
- exit code 0 on a valid Bangalore-baseline input.
- exit code 1 on a Pydantic `ValidationError` (e.g. latitude out of range).
- `--no-enrich` runs cleanly (Tier-3 stub returns base unchanged in Phase 1).

Exit codes per spec Section 5:
    0 = success
    1 = bad input (ValidationError on ChartInput)
    2 = ephemeris / chart failure
    3 = schema validation failure
    4 = RAG index missing (Tier-3 fallback)
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _run_cli(*args: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    """Invoke `python -m app.reading.cli ...` as a subprocess."""
    return subprocess.run(
        [sys.executable, "-m", "app.reading.cli", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(REPO_ROOT),
    )


class TestCliHappyPath:
    """Happy path: valid input emits valid JSON to stdout with exit 0."""

    def test_cli_emits_valid_json(self):
        """Stdout must be JSON-parseable and carry schema_version='1.1.0'."""
        result = _run_cli(
            "--dob", "1990-07-15",
            "--time", "12:00",
            "--tz", "+05:30",
            "--lat", "12.97",
            "--lon", "77.59",
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        output = json.loads(result.stdout)
        assert output["meta"]["schema_version"] == "1.1.0"
        assert output["meta"]["stability"] == "experimental"
        assert output["meta"]["chart_input"]["dob"] == "1990-07-15"

    def test_cli_no_enrich_flag_still_exits_zero(self):
        """`--no-enrich` runs the bare core pipeline; same exit code, valid JSON."""
        result = _run_cli(
            "--dob", "1990-07-15",
            "--time", "12:00",
            "--tz", "+05:30",
            "--lat", "12.97",
            "--lon", "77.59",
            "--no-enrich",
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        output = json.loads(result.stdout)
        assert output["meta"]["schema_version"] == "1.1.0"

    def test_cli_writes_to_out_file_when_specified(self, tmp_path: Path):
        """`--out reading.json` writes the payload to disk rather than stdout."""
        out_file = tmp_path / "reading.json"
        result = _run_cli(
            "--dob", "1990-07-15",
            "--time", "12:00",
            "--tz", "+05:30",
            "--lat", "12.97",
            "--lon", "77.59",
            "--out", str(out_file),
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert out_file.exists()
        payload = json.loads(out_file.read_text(encoding="utf-8"))
        assert payload["meta"]["schema_version"] == "1.1.0"


class TestCliBadInput:
    """Exit code 1 for ChartInput ValidationError surfaces."""

    def test_cli_bad_latitude_exits_1(self):
        """Latitude 200 violates the [-90, 90] range -> exit code 1."""
        result = _run_cli(
            "--dob", "1990-07-15",
            "--time", "12:00",
            "--tz", "+05:30",
            "--lat", "200",
            "--lon", "77.59",
        )
        assert result.returncode == 1
        # Error message must surface for the operator to diagnose.
        assert "Invalid chart input" in result.stderr or "lat" in result.stderr.lower()

    def test_cli_bad_longitude_exits_1(self):
        """Longitude 200 violates the [-180, 180] range -> exit code 1."""
        result = _run_cli(
            "--dob", "1990-07-15",
            "--time", "12:00",
            "--tz", "+05:30",
            "--lat", "12.97",
            "--lon", "200",
        )
        assert result.returncode == 1
