"""Bootstrap a synthetic noise_floor.json from the 5 main seeds.

The proper noise floor (Task 18) needs 20 seeds (~60 hours more compute).
We skipped it because the 5-seed main run already showed mean Delta = -0.16,
far below zero — no noise-floor choice would flip the outcome from FAIL.

What we do here: estimate per-class sigma from the 5 main-run seeds and
write it as if it were the noise floor. This CONFLATES model variance
with noise variance, so it's:
- Conservative for FAIL outcomes (overstates the threshold needed to clear)
- INVALID for PASS claims (under-counts true noise variance)

DECISION.md must footnote this deviation.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import statistics
from pathlib import Path

from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES

OUT = Path("data/ml_runs/fork_a_stage_d_subsample")
MAIN_JSONL = OUT / "main_run.jsonl"
NF_PATH = OUT / "noise_floor.json"


def main() -> None:
    records = [json.loads(line) for line in MAIN_JSONL.read_text().splitlines() if line.strip()]
    assert len(records) >= 4, f"need >=4 seeds to estimate sigma, got {len(records)}"

    sigma_per_class: dict[str, float | None] = {}
    for cls in QUALIFYING_EVENT_CLASSES:
        deltas = [
            r["per_class"][cls]["delta_test"]
            for r in records
            if cls in r["per_class"]
            and r["per_class"][cls]["delta_test"] is not None
            and not math.isnan(r["per_class"][cls]["delta_test"])
        ]
        sigma_per_class[cls] = statistics.stdev(deltas) if len(deltas) >= 2 else None

    K_qual = sum(1 for v in sigma_per_class.values() if v is not None)
    threshold = max(1, math.ceil(K_qual * 5 / 14))

    out = {
        "corpus": "subsample_2000p",
        "K_qualifying": K_qual,
        "g2_threshold": threshold,
        "g2_threshold_formula": "ceil(K * 5/14)",
        "sigma_noise_per_class": sigma_per_class,
        "sigma_noise_3x_per_class": {
            k: (v * 3 if v else None) for k, v in sigma_per_class.items()
        },
        "n_seeds": len(records),
        "computed_at": dt.date.today().isoformat(),
        "_BOOTSTRAP_NOTICE": (
            "Estimated from the 5 main-run seeds, NOT from a proper 20-seed "
            "noise-floor run (Task 18 was skipped). This conflates model "
            "variance with noise variance, so it is conservative for FAIL "
            "outcomes but INVALID for PASS claims. See DECISION.md footnote."
        ),
    }
    NF_PATH.write_text(json.dumps(out, indent=2))
    print(f"wrote {NF_PATH}")
    print(f"  K_qualifying={K_qual}  g2_threshold={threshold}")
    print(f"  median sigma_noise: {statistics.median(s for s in sigma_per_class.values() if s):.4f}")


if __name__ == "__main__":
    main()
