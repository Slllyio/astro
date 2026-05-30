"""Integration tests for V1.5 pipeline wiring.

Locks the contract that ``_run_core_pipeline`` automatically emits the
V1.5 additions in its JSON output, NOT just as standalone APIs:

- ``sequences.chara_dasha``  (D-17 Jaimini sign-frame)
- ``sequences.yogini_dasha`` (D-18 36-year cycle)
- ``domains.<name>.cross_checks`` augmented with ``modern_life.*`` findings

All three run in the ``--no-enrich`` path (deterministic Stage 5/6, not
Tier-3). Pinned against the canonical Bangalore baseline (1990-07-15 12:00 IST,
12.97 / 77.59) per CLAUDE.md.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run_cli(tmp_path: Path) -> dict:
    """Run the reading CLI against the Bangalore baseline and parse JSON."""
    out = tmp_path / "wired.json"
    result = subprocess.run(
        [
            sys.executable, "-m", "app.reading.cli",
            "--dob=1990-07-15", "--time=12:00", "--tz=+05:30",
            "--lat=12.97", "--lon=77.59", "--no-enrich", f"--out={out}",
        ],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    return json.loads(out.read_text(encoding="utf-8"))


class TestV15PipelineWiring:
    """V1.5 additions are wired into `_run_core_pipeline`'s JSON output."""

    def test_chara_dasha_in_sequences_block(self, tmp_path: Path) -> None:
        """sequences.chara_dasha is populated by the deterministic pipeline."""
        output = _run_cli(tmp_path)
        chara = output["sequences"].get("chara_dasha")
        assert chara is not None, "chara_dasha missing from sequences block"
        assert "timeline" in chara
        assert "current_md_judgment" in chara
        # Bangalore baseline (Virgo Lagna, dual) -> starting MD is 9th from Virgo
        # = Taurus. With movable/fixed/dual cycle, current MD at birth = Taurus.
        assert chara["current_md_judgment"]["md_sign_name"] == "Taurus"

    def test_yogini_dasha_in_sequences_block(self, tmp_path: Path) -> None:
        """sequences.yogini_dasha is populated by the deterministic pipeline."""
        output = _run_cli(tmp_path)
        yogini = output["sequences"].get("yogini_dasha")
        assert yogini is not None, "yogini_dasha missing from sequences block"
        assert "timeline" in yogini
        assert "current_md_judgment" in yogini
        # Bangalore baseline Moon nakshatra = Revati (27) -> Yogini start
        # index (27-1) % 8 = 2 -> Dhanya (Jupiter).
        assert yogini["current_md_judgment"]["yogini"] == "Dhanya"
        assert yogini["current_md_judgment"]["ruling_planet"] == "Jupiter"

    def test_modern_life_signals_in_domain_cross_checks(
        self, tmp_path: Path
    ) -> None:
        """Modern-life findings are appended to each domain's cross_checks."""
        output = _run_cli(tmp_path)
        marriage_block = output["domains"].get("marriage") or {}
        marriage_cross_checks = marriage_block.get("cross_checks") or []
        modern_life_findings = [
            f for f in marriage_cross_checks
            if isinstance(f, dict)
            and f.get("id", "").startswith("modern_life.")
        ]
        # Bangalore baseline should produce at least 1 modern_life finding
        # in marriage (the second_marriage check fires for many charts).
        assert len(modern_life_findings) >= 1, (
            "No modern_life findings in marriage cross_checks; "
            "modern-life enrichment did not wire into the pipeline"
        )

    def test_schema_version_bumped(self, tmp_path: Path) -> None:
        """meta.schema_version is bumped to 1.1.0 per V1.5 MINOR bump."""
        output = _run_cli(tmp_path)
        assert output["meta"]["schema_version"] == "1.1.0"
