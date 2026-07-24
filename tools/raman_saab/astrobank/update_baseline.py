"""Stage 5 — record the generalization baseline (the ONLY path to a ratchet bump).

Reads static_results.json (+ timing_results.json when present), stamps the mapping/person-master/
engine hashes, and writes the committed real_outcome_baseline.json with core-metric floors at
observed - 1.5 * bootstrap-SE. Requires --confirm (a conscious act; the commit message must state
why the baseline moved).

Usage: py -3.12 -m tools.raman_saab.astrobank.update_baseline --confirm
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

_OUT = Path("data/astro_databank/derived/raman")
_BASE = Path(__file__).parent / "real_outcome_baseline.json"
_MAP = Path(__file__).parent / "mapping" / "category_house_map.csv"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _engine_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                              text=True).stdout.strip()[:12]
    except Exception:  # noqa: BLE001
        return "unknown"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--confirm", action="store_true")
    a = ap.parse_args(argv)
    if not a.confirm:
        print("refusing without --confirm (baseline bumps are conscious acts)")
        return 2
    static = json.loads((_OUT / "static_results.json").read_text(encoding="utf-8"))["results"]
    timing_path = _OUT / "timing_results.json"
    timing = json.loads(timing_path.read_text(encoding="utf-8")) if timing_path.is_file() else {}

    metrics: dict[str, dict] = {}
    for tid, r in static.items():
        if r.get("strength") != "core" or "auc" not in r:
            continue
        se = float(r.get("se") or 0.02)
        metrics[tid] = {"metric": "auc", "value": round(float(r["auc"]), 4),
                        "floor": round(float(r["auc"]) - 1.5 * se, 4),
                        "n": int(r.get("n_case", 0)),
                        "ci": [round(float(r.get("ci_lo", 0)), 4), round(float(r.get("ci_hi", 0)), 4)]}
    for tid, r in timing.items():
        if r.get("n_events") and not r.get("withheld_saturated"):
            se = (float(r["ci_hi"]) - float(r["ci_lo"])) / 3.92 or 0.02
            metrics[f"timing_{tid}"] = {"metric": "mean_lift", "value": round(float(r["mean_lift"]), 4),
                                        "floor": round(float(r["mean_lift"]) - 1.5 * se, 4),
                                        "n": int(r["n_events"]),
                                        "ci": [round(float(r["ci_lo"]), 4), round(float(r["ci_hi"]), 4)]}

    base = {
        "mapping_version": 2,
        "mapping_sha256": _sha(_MAP),
        "person_master_sha256": _sha(_OUT / "person_master.parquet"),
        "engine_git_sha": _engine_sha(),
        "created": time.strftime("%Y-%m-%d %H:%M"),
        "metrics": metrics,
        "_note": ("Floors = observed - 1.5*SE. Only core-tier statics + non-withheld timing ratchet. "
                  "The honest headline lives in docs/raman_saab/REAL_OUTCOME_GENERALIZATION.md."),
    }
    _BASE.write_text(json.dumps(base, indent=2), encoding="utf-8")
    print(f"[baseline] wrote {_BASE} with {len(metrics)} ratcheted metrics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
