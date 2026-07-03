"""Run-5 weight calibration — scripted, seeded, calibration half ONLY.

Coarse coordinate descent over a small pinned grid per key (few values, two
passes — deliberately coarse: ~10 tunables against ~24 cases; the doctrine
ORDERING_CONSTRAINTS are enforced as hard filters, and the held-out half is
the audit). Objective, lexicographic:

    1. minimise the calibration-half MEDIAN death-window percentile,
    2. then maximise the killer hit-rate,
    3. then minimise the mean percentile (tie-break).

After the weight search, the pre-registered TRANSIT INCLUSION RULE runs:
transit terms (tr2.*) enter the frozen weights iff they improve the
calibration median percentile by ≥ 0.05 absolute without lowering the killer
hit-rate; otherwise they are zeroed and reported as a secondary.

Output: ``data/raman_saab/run5_weights.json`` (+ a calibration log JSON).
This module never touches the held-out half or the population corpus.
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from app.medini.ml.raman_saab.fidelity_v2 import evaluate_half
from app.medini.ml.raman_saab.golden_registry import split, validate_all
from app.medini.ml.raman_saab.raman_method_v2 import (
    ORDERING_CONSTRAINTS, RAMAN_WEIGHTS_V2,
)

logger = logging.getLogger(__name__)

# Pinned coarse grid (few points per key; two passes of coordinate descent).
GRID: dict[str, tuple[float, ...]] = {
    "fp2.weakness": (0.3, 0.6, 0.9),
    "fp2.nakshatra_transfer": (0.6, 0.8, 1.0),
    "fp2.node_sign_dispositor": (0.4, 0.6, 0.8),
    "fp2.tara_death": (0.2, 0.4, 0.6),
    "fp2.dasha_sandhi": (0.15, 0.3, 0.5),
    "fp2.md_ad_shashtashtaka": (0.1, 0.25, 0.4),
    "fp2.gate_adjacent": (0.4, 0.6, 0.8),
    "fp2.gate_far": (0.1, 0.25, 0.4),
    "mk2.saturn_ayushkaraka_base": (0.2, 0.4, 0.6),
    "mk2.override_spare": (0.1, 0.25, 0.4),
    "mk2.ref_moon": (0.3, 0.5, 0.7),
    "mk2.ref_navamsa": (0.3, 0.5, 0.7),
    "lng2.promotion_margin": (0.05, 0.15, 0.25),
}

_TRANSIT_KEYS = ("tr2.sadesathi_3rd", "tr2.composite_point")
_TRANSIT_RULE_MIN_GAIN = 0.05


def _ordering_ok(w: dict) -> bool:
    return all(w[hi] > w[lo] for hi, lo in ORDERING_CONSTRAINTS)


def _score(cases, w) -> tuple:
    r = evaluate_half(cases, w, use_transits=False)
    return (r["median_pctile"], -(r["killer_hit_rate"] or 0.0),
            r["mean_pctile"]), r


def calibrate(out_weights: Path, out_log: Path) -> dict:
    calib, _held = split(validate_all())
    w = dict(RAMAN_WEIGHTS_V2)
    best_key, best = _score(calib, w)
    log = [{"step": "defaults", "median": best["median_pctile"],
            "killer_hit_rate": best["killer_hit_rate"]}]
    logger.info("defaults: median=%.3f killers=%.2f",
                best["median_pctile"], best["killer_hit_rate"])

    for pass_i in range(2):
        for key, values in GRID.items():
            for v in values:
                if w[key] == v:
                    continue
                trial = dict(w)
                trial[key] = v
                if not _ordering_ok(trial):
                    continue
                trial_key, trial_res = _score(calib, trial)
                if trial_key < best_key:
                    w, best_key, best = trial, trial_key, trial_res
                    log.append({"step": f"pass{pass_i}:{key}={v}",
                                "median": best["median_pctile"],
                                "killer_hit_rate": best["killer_hit_rate"]})
                    logger.info("pass%d %s=%.2f -> median=%.3f killers=%.2f",
                                pass_i, key, v, best["median_pctile"],
                                best["killer_hit_rate"])

    # Pre-registered transit inclusion rule (calibration half only).
    with_t = evaluate_half(calib, w, use_transits=True)
    gain = (best["median_pctile"] or 1.0) - (with_t["median_pctile"] or 1.0)
    keep_transits = (gain >= _TRANSIT_RULE_MIN_GAIN
                     and (with_t["killer_hit_rate"] or 0.0)
                     >= (best["killer_hit_rate"] or 0.0))
    if not keep_transits:
        for k in _TRANSIT_KEYS:
            w[k] = 0.0
    transit_decision = {
        "median_without": best["median_pctile"],
        "median_with": with_t["median_pctile"],
        "gain": round(gain, 4),
        "killer_without": best["killer_hit_rate"],
        "killer_with": with_t["killer_hit_rate"],
        "included_in_primaries": keep_transits,
    }
    logger.info("transit inclusion: gain=%.3f -> %s", gain,
                "INCLUDED" if keep_transits else "zeroed (secondary only)")

    out_weights.parent.mkdir(parents=True, exist_ok=True)
    out_weights.write_text(json.dumps(w, indent=1))
    final = evaluate_half(calib, w, use_transits=keep_transits)
    payload = {
        "calibration_final": {k: v for k, v in final.items() if k != "cases"},
        "calibration_cases": final["cases"],
        "transit_decision": transit_decision,
        "search_log": log,
        "grid": {k: list(v) for k, v in GRID.items()},
    }
    out_log.parent.mkdir(parents=True, exist_ok=True)
    out_log.write_text(json.dumps(payload, indent=1))
    return payload


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-weights", type=Path,
                   default=Path("data/raman_saab/run5_weights.json"))
    p.add_argument("--out-log", type=Path,
                   default=Path("data/ml_runs/raman_saab/run5/calibration.json"))
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    payload = calibrate(args.out_weights, args.out_log)
    print(json.dumps(payload["calibration_final"], indent=1))
    print("transit decision:", payload["transit_decision"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
