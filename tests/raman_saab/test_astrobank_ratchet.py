"""Generalization ratchet — the committed real-outcome floor (astrobank program, Stage 5).

CI-safe by construction: the astrobank data lives only under gitignored data/, so this test SKIPS
cleanly when the results are absent. When present, a corpus/mapping/engine hash mismatch SKIPS
LOUDLY (the baseline must be consciously re-recorded via update_baseline.py --confirm — never a
silent pass/fail on stale data). Only when hashes match are the core-metric floors asserted.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

_RESULTS = Path("data/astro_databank/derived/raman/static_results.json")
_MASTER = Path("data/astro_databank/derived/raman/person_master.parquet")
_TIMING = Path("data/astro_databank/derived/raman/timing_results.json")
_BASE = Path("tools/raman_saab/astrobank/real_outcome_baseline.json")
_MAP = Path("tools/raman_saab/astrobank/mapping/category_house_map.csv")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


@pytest.fixture(scope="module")
def baseline() -> dict:
    if not _RESULTS.is_file() or not _MASTER.is_file():
        pytest.skip("astrobank data absent (local-only, gitignored) — generalization ratchet skipped")
    if not _BASE.is_file():
        pytest.skip("no real_outcome_baseline.json committed yet")
    base = json.loads(_BASE.read_text(encoding="utf-8"))
    if base.get("mapping_sha256") != _sha(_MAP):
        pytest.skip("MAPPING CHANGED vs baseline — re-run the pipeline and consciously bump via "
                    "update_baseline.py --confirm (never silently ratchet on a stale mapping)")
    if base.get("person_master_sha256") != _sha(_MASTER):
        pytest.skip("CORPUS CHANGED vs baseline — rebuild + consciously bump the baseline")
    try:
        engine = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                                text=True).stdout.strip()[:12]
        if base.get("engine_git_sha") not in ("unknown", engine):
            pytest.skip(f"ENGINE CHANGED ({engine} vs baseline {base.get('engine_git_sha')}) — "
                        "rebuild the feature store and consciously bump the baseline")
    except Exception:  # noqa: BLE001
        pass
    return base


def test_core_static_metrics_hold_their_floors(baseline: dict) -> None:
    """Every ratcheted core metric must stay at/above its recorded floor."""
    results = json.loads(_RESULTS.read_text(encoding="utf-8"))["results"]
    timing = json.loads(_TIMING.read_text(encoding="utf-8")) if _TIMING.is_file() else {}
    failures = []
    for tid, m in baseline["metrics"].items():
        if tid.startswith("timing_"):
            r = timing.get(tid[len("timing_"):], {})
            value = r.get("mean_lift")
        else:
            value = results.get(tid, {}).get("auc")
        if value is None:
            failures.append(f"{tid}: metric missing from current results")
        elif value < m["floor"]:
            failures.append(f"{tid}: {value:.4f} < floor {m['floor']:.4f}")
    assert not failures, "generalization regression:\n  " + "\n  ".join(failures)


def test_baseline_is_well_formed() -> None:
    """The committed baseline parses and carries hashes + at least the 3 core statics."""
    if not _BASE.is_file():
        pytest.skip("no baseline committed yet")
    base = json.loads(_BASE.read_text(encoding="utf-8"))
    assert base.get("mapping_sha256") and base.get("person_master_sha256")
    core = [k for k in base.get("metrics", {}) if not k.startswith("timing_")]
    assert len(core) >= 3, "expected at least the 3 core static metrics"
