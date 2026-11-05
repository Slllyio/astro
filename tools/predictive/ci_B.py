"""Per-area and per-tier 95% person-level bootstrap intervals for Task B (addendum 1, item 2).

phase2_B stored only the pooled interval; this recomputes the (deterministic, seeded) observed
per-set deltas and bootstraps each area and tier. The observed stat is identical to phase2_B's.

Usage:
    python -m tools.predictive.ci_B --cache /tmp/claude-0/pred/cache --out /mnt/project-files/astro/predictive
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from tools.predictive import evaluate as E
from tools.predictive.run import _load_B


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    _p, _B, tB = _load_B(a.cache)
    obs = tB.stats(tB.B.case.to_numpy())
    d = np.array(obs.pop("_per_set"))
    res = {"pooled_d_full": obs["pooled"]["d_full"], "areas": {}, "tiers": {}}
    for key, lab in (("areas", tB.set_area), ("tiers", tB.set_tier)):
        for v in sorted(set(lab)):
            m = lab == v
            lo, hi = E.boot_ci(d[m], tB.set_person[m], np.random.default_rng([E.SEED, 12]))
            res[key][v] = {"n_sets": int(m.sum()), "d_full": float(d[m].mean()), "ci95": [lo, hi]}
    (a.out / "phase2_B_ci_by_area.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
