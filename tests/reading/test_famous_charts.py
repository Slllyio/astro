"""Famous-chart corpus -- STRUCTURAL ASSERTIONS ONLY (Phase 5 Task 5.7).

Per spec Section 11 prediction-trap ban: this corpus must NEVER assert that
specific charts produce specific life-event outcomes. Test ONLY:

  - Exit code 0 (CLI doesn't crash on diverse birth data)
  - Output validates against the `ReadingOutput` Pydantic schema
  - All required top-level keys are present
  - Schema-version + stability locks hold

Background. The four prior ML methodologies in this project that tried
to validate doctrine via outcome prediction (Wikidata marriage, Stage D
event timing, doctrine-direction pooling, etc.) returned NULL results.
A famous-chart corpus that asserts "Einstein's chart predicted Nobel
timing" or similar is exactly that same falsified paradigm rebranded.
We do NOT do that here. We assert *structure* (the engine ran, the
output is well-formed) and stop. Outcome-faithfulness belongs to the
practitioner-in-the-loop layer, not to automated tests.

The 10 charts cover six "standard" reference birth-data sets (Einstein,
Gandhi, Steve Jobs, Ramana Maharshi, A.P.J. Kalam, Obama) plus four
synthetic edge cases (atmakaraka tiebreaker, polar latitude, equinox at
equator, gandanta Moon) so the CLI is exercised across a wide spread of
latitudes, longitudes, hours-of-day, and astronomical corner conditions.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from app.reading.schema import ReadingOutput


FAMOUS_CHARTS_DIR = Path(__file__).parent / "famous_charts"
ALL_CHARTS = sorted(FAMOUS_CHARTS_DIR.glob("*.json"))
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


# Top-level keys every ReadingOutput must carry. Mirrors `app.reading.schema`.
REQUIRED_TOP_LEVEL_KEYS = (
    "meta",
    "chart",
    "primitives",
    "foundations",
    "practitioner",
    "sequences",
    "domains",
    "contradictions",
    "warnings",
)


def _cli_args(chart: dict, *, out_file: Path | None = None) -> list[str]:
    """Build the argv list for `app.reading.cli` from a chart record.

    Negative tz/lat/lon values would otherwise be interpreted by argparse as
    new option flags (e.g. `--tz -08:00` -> `-08:00` looks like a short flag),
    so we use the `--name=value` form for every value-bearing argument.
    """
    args = [
        sys.executable, "-m", "app.reading.cli",
        f"--dob={chart['dob']}",
        f"--time={chart['time']}",
        f"--tz={chart['tz']}",
        f"--lat={chart['lat']}",
        f"--lon={chart['lon']}",
        "--no-enrich",  # Tier-3 skip keeps the corpus fast / offline.
    ]
    if out_file is not None:
        args.append(f"--out={out_file}")
    return args


def _run_cli_for_chart(chart: dict, *, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    """Run the reading CLI for a single famous-chart record."""
    return subprocess.run(
        _cli_args(chart),
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(REPO_ROOT),
    )


def test_corpus_has_ten_charts():
    """Lock the corpus size at exactly 10 (6 standard + 4 edge cases)."""
    assert len(ALL_CHARTS) == 10, (
        f"Famous-chart corpus must contain exactly 10 files (6 standard + 4 "
        f"edge cases). Found {len(ALL_CHARTS)}: "
        f"{sorted(p.name for p in ALL_CHARTS)}"
    )


@pytest.mark.parametrize("chart_file", ALL_CHARTS, ids=lambda p: p.stem)
def test_famous_chart_cli_exits_zero(chart_file: Path):
    """The CLI must not crash on any chart in the corpus."""
    chart = json.loads(chart_file.read_text(encoding="utf-8"))
    result = _run_cli_for_chart(chart)
    assert result.returncode == 0, (
        f"{chart_file.stem}: exit {result.returncode}; stderr:\n{result.stderr}"
    )


@pytest.mark.parametrize("chart_file", ALL_CHARTS, ids=lambda p: p.stem)
def test_famous_chart_output_validates(chart_file: Path, tmp_path: Path):
    """Output must validate against the `ReadingOutput` Pydantic schema."""
    chart = json.loads(chart_file.read_text(encoding="utf-8"))
    out_file = tmp_path / f"{chart_file.stem}.json"
    # Use --out to avoid stdout encoding issues on Windows consoles.
    result = subprocess.run(
        _cli_args(chart, out_file=out_file),
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"{chart_file.stem}: exit {result.returncode}; stderr:\n{result.stderr}"
    )
    payload = json.loads(out_file.read_text(encoding="utf-8"))

    # Pydantic round-trip - validates structure end-to-end.
    ReadingOutput.model_validate(payload)

    # Schema version + stability locks.
    assert payload["meta"]["schema_version"] == "1.0.0", (
        f"{chart_file.stem}: schema_version drift "
        f"{payload['meta']['schema_version']!r}"
    )
    assert payload["meta"]["stability"] == "experimental", (
        f"{chart_file.stem}: stability drift "
        f"{payload['meta']['stability']!r}"
    )


@pytest.mark.parametrize("chart_file", ALL_CHARTS, ids=lambda p: p.stem)
def test_famous_chart_required_top_level_keys(chart_file: Path, tmp_path: Path):
    """All required top-level keys must be present in the output.

    Phase-5 V1 milestone: we lock the *shape* of the output (the nine top-level
    sections). Finer-grained Finding-ID coverage gates will be added in later
    phases once Tier-0/1/2 modules are all wired into the proforma.
    """
    chart = json.loads(chart_file.read_text(encoding="utf-8"))
    out_file = tmp_path / f"{chart_file.stem}.json"
    result = subprocess.run(
        _cli_args(chart, out_file=out_file),
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, (
        f"{chart_file.stem}: exit {result.returncode}; stderr:\n{result.stderr}"
    )
    payload = json.loads(out_file.read_text(encoding="utf-8"))

    for key in REQUIRED_TOP_LEVEL_KEYS:
        assert key in payload, (
            f"{chart_file.stem}: missing required top-level key {key!r}. "
            f"Found keys: {sorted(payload.keys())}"
        )
