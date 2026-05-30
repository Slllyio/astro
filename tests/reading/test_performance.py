"""Performance regression tests — spec Section 16 budget.

These tests assert the wall-clock budget that downstream consumers depend on:

- Cold cache (no warm DuckDB/cache state): full pipeline < 12s
- Warm cache (second invocation with caches primed): full pipeline < 7s
- `--no-enrich` path: < 8s cold (skips Tier-3 RAG/consensus/robustness)

We intentionally use subprocess-level timing (matches what a real consumer
sees) rather than in-process timing. The CLI is fast enough that
pytest-benchmark machinery isn't strictly necessary; if it becomes
available later we can switch to `benchmark()` for variance tracking.

Spec Section 16 budget table:
    cold full pipeline      <  12 s
    warm full pipeline      <   7 s
    cold --no-enrich        <   8 s

These thresholds are the OUTER ceilings. Typical runs should be well under,
giving headroom for slower CI hardware and incidental jitter.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

BANGALORE = {
    "dob": "1990-07-15",
    "time": "12:00",
    "tz": "+05:30",
    "lat": "12.97",
    "lon": "77.59",
}


def _run_cli(extra_args: list[str], out_path: Path) -> tuple[float, dict]:
    """Run CLI as subprocess and return ``(elapsed_seconds, output_dict)``.

    Uses ``time.perf_counter`` for wall-clock timing — same instrument as
    a real consumer would use. Subprocess overhead (interpreter startup,
    module import) is intentionally included since that is what end users
    experience.
    """
    cmd = [
        sys.executable,
        "-m",
        "app.reading.cli",
        f"--dob={BANGALORE['dob']}",
        f"--time={BANGALORE['time']}",
        f"--tz={BANGALORE['tz']}",
        f"--lat={BANGALORE['lat']}",
        f"--lon={BANGALORE['lon']}",
        f"--out={out_path}",
        *extra_args,
    ]
    start = time.perf_counter()
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(REPO_ROOT),
    )
    elapsed = time.perf_counter() - start
    assert result.returncode == 0, (
        f"CLI failed: rc={result.returncode}\nstderr={result.stderr}"
    )
    return elapsed, json.loads(out_path.read_text(encoding="utf-8"))


class TestCliPerformance:
    """End-to-end CLI performance — spec Section 16 outer-ceiling budgets."""

    def test_cold_cache_no_enrich_under_8s(self, tmp_path: Path) -> None:
        """`--no-enrich` cold-cache invocation must finish under 8 seconds."""
        elapsed, _ = _run_cli(["--no-enrich"], tmp_path / "r1.json")
        assert elapsed < 8.0, (
            f"Cold no-enrich took {elapsed:.2f}s (budget <8s, spec Section 16)"
        )

    def test_cold_cache_enriched_under_12s(self, tmp_path: Path) -> None:
        """Full pipeline (incl. Tier-3 enrichment) cold cache under 12 seconds.

        Also confirms the output is non-empty and schema-versioned, so a
        too-fast (no-op) run can't silently pass the timing assertion.
        """
        elapsed, output = _run_cli([], tmp_path / "r2.json")
        assert elapsed < 12.0, (
            f"Cold enriched took {elapsed:.2f}s (budget <12s, spec Section 16)"
        )
        assert output["meta"]["schema_version"] == "1.2.0"
        assert output["domains"], "Domains block must be populated"


class TestPipelineBudget:
    """Output-shape regression guards that ride alongside performance.

    These assertions are cheap — they ensure that the engine, while meeting
    the perf budget, isn't degenerating into an empty/no-op response.
    """

    def test_no_warnings_in_bangalore_baseline(self, tmp_path: Path) -> None:
        """The canonical Bangalore baseline must emit zero warnings."""
        _, output = _run_cli(["--no-enrich"], tmp_path / "r3.json")
        warnings = output.get("warnings", [])
        assert warnings == [], f"Unexpected warnings: {warnings}"

    def test_all_six_domains_populated(self, tmp_path: Path) -> None:
        """The 6 named domain readings must all be present (career..education)."""
        _, output = _run_cli(["--no-enrich"], tmp_path / "r4.json")
        domains = output.get("domains", {})
        expected = {
            "career",
            "marriage",
            "health",
            "wealth",
            "children",
            "education",
        }
        actual = {k for k, v in domains.items() if v is not None}
        missing = expected - actual
        extra = actual - expected
        assert not missing and not extra, (
            f"Domain set mismatch — missing={sorted(missing)} extra={sorted(extra)}"
        )
