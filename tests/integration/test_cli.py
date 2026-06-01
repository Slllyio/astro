"""CLI smoke tests for ``python -m app.integration``.

Verifies the CLI parses arguments, dispatches to the right handler, and
emits valid JSON. Does NOT run the full Track-A pipeline (that's covered
by tests/reading/test_cli_subprocess.py) — these tests exercise only the
integration adapters.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.integration.cli import main


def _minimal_reading_dict() -> dict:
    """Smallest dict that passes the enhancer walker without errors."""
    return {
        "meta": {"schema_version": "1.2.0"},
        "chart": {},
        "primitives": {},
        "foundations": {},
        "practitioner": {},
        "sequences": {},
        "domains": {
            "career": {
                "verdict": "test",
                "findings": [
                    {
                        "id": "cli.test.1",
                        "rule": "yogas_extended.lakshmi",
                        "source_sequence": None,
                        "classification": "yoga",
                        "direction": "positive",
                        "verdict": "Lakshmi active",
                        "verdict_language": "en",
                        "evidence": [],
                        "confidence": {"score": 0.7, "tier": "medium"},
                        "enrichment_level": 0,
                        "citations": [],
                        "consensus": None,
                        "consensus_status": "not_computed",
                        "dispute": None,
                        "robustness": None,
                        "contradicts_finding_ids": [],
                    }
                ],
                "cross_checks": [],
            }
        },
        "contradictions": [],
        "warnings": [],
    }


class TestEnhanceMode:
    """CLI --mode enhance reads input JSON, writes IntegratedReadingOutput."""

    def test_enhance_writes_envelope_to_out_file(self, tmp_path: Path):
        in_path = tmp_path / "reading.json"
        out_path = tmp_path / "enhanced.json"
        in_path.write_text(json.dumps(_minimal_reading_dict()), encoding="utf-8")

        exit_code = main([
            "--mode", "enhance",
            "--in", str(in_path),
            "--out", str(out_path),
        ])

        assert exit_code == 0
        assert out_path.exists()
        envelope = json.loads(out_path.read_text(encoding="utf-8"))
        assert envelope["integration_version"] == "0.1.0"
        assert "reading" in envelope
        assert "dkp_translations_summary" in envelope
        # Lakshmi was attached
        assert "Lakshmi" in envelope["dkp_translations_summary"]["records"]

    def test_enhance_missing_in_file_exits_with_error(self, tmp_path: Path):
        with pytest.raises(SystemExit):
            main(["--mode", "enhance", "--in", str(tmp_path / "nope.json")])

    def test_enhance_requires_in_flag(self):
        with pytest.raises(SystemExit):
            main(["--mode", "enhance"])


class TestCompareMode:
    """CLI --mode compare extracts Chara Dasha from input, diffs against Track B."""

    def test_compare_missing_chara_block_errors(self, tmp_path: Path):
        in_path = tmp_path / "reading.json"
        in_path.write_text(json.dumps(_minimal_reading_dict()), encoding="utf-8")
        with pytest.raises(SystemExit) as excinfo:
            main(["--mode", "compare", "--in", str(in_path)])
        assert "chara_dasha" in str(excinfo.value).lower()


class TestArgparseUX:
    """Ensure --help and --mode validation surface usefully."""

    def test_mode_required(self):
        with pytest.raises(SystemExit):
            main([])

    def test_unknown_mode_rejected(self):
        with pytest.raises(SystemExit):
            main(["--mode", "frobnicate"])
