"""Fork-A Stage D — gate verdict + DECISION.md generator.

Reads noise_floor.json + main_run.jsonl (+ replication_run.jsonl if present)
and writes DECISION.md following the phase3c_wedge/DECISION.md template.

Usage:
    py -3.12 -m app.medini.ml.stage_d_evaluate \\
        --out-dir data/ml_runs/fork_a_stage_d
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

from app.medini.ml.stage_d_features import QUALIFYING_EVENT_CLASSES

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PerClassVerdict:
    cls: str
    delta_mean: float
    sigma_model: float
    sigma_noise: float
    threshold_3sigma: float
    clears_g2: bool
    stable_g3: bool


@dataclass(frozen=True, slots=True)
class GateVerdict:
    n_seeds: int
    K_qualifying: int
    g2_threshold: int
    per_class: tuple[PerClassVerdict, ...]
    passes_g1: bool
    passes_g2: bool
    passes_g3: bool
    passes_g4: bool | None     # None if replication didn't run
    outcome: str               # one of the spec §5 decision-table strings


def _records_from_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def evaluate_gate(main_records: list[dict], *,
                  noise_floor: dict,
                  replication_records: list[dict] | None = None) -> GateVerdict:
    sigma_noise = noise_floor["sigma_noise_per_class"]
    g2_threshold = noise_floor["g2_threshold"]
    K = noise_floor["K_qualifying"]

    per_class: list[PerClassVerdict] = []
    n_clear = 0
    delta_sum, threshold_sum = 0.0, 0.0
    n_summed = 0
    for cls in QUALIFYING_EVENT_CLASSES:
        deltas = [r["per_class"][cls]["delta_test"] for r in main_records
                  if cls in r["per_class"]
                  and not (r["per_class"][cls]["delta_test"] is None
                           or math.isnan(r["per_class"][cls]["delta_test"]))]
        stage_d_cs = [r["per_class"][cls]["c_index_test_stage_d"]
                      for r in main_records if cls in r["per_class"]
                      and r["per_class"][cls]["c_index_test_stage_d"] is not None
                      and not math.isnan(r["per_class"][cls]["c_index_test_stage_d"])]
        sigma_n = sigma_noise.get(cls)
        if len(deltas) < 5 or sigma_n is None:
            continue
        d_mean = statistics.mean(deltas)
        sd_m = statistics.stdev(stage_d_cs) if len(stage_d_cs) >= 2 else float("inf")
        threshold = 3 * sigma_n
        clears = d_mean >= threshold
        stable = sd_m <= max(d_mean, 1e-9)
        per_class.append(PerClassVerdict(
            cls=cls, delta_mean=d_mean, sigma_model=sd_m,
            sigma_noise=sigma_n, threshold_3sigma=threshold,
            clears_g2=clears, stable_g3=stable,
        ))
        if clears:
            n_clear += 1
        delta_sum += d_mean
        threshold_sum += threshold
        n_summed += 1

    passes_g1 = n_summed > 0 and (delta_sum / n_summed) >= (threshold_sum / n_summed)
    passes_g2 = n_clear >= g2_threshold
    passes_g3 = all(p.stable_g3 for p in per_class if p.clears_g2)

    passes_g4 = None
    if replication_records and passes_g1 and passes_g2 and passes_g3:
        rep_verdict = evaluate_gate(replication_records, noise_floor=noise_floor)
        passes_g4 = rep_verdict.passes_g1 and rep_verdict.passes_g2 and rep_verdict.passes_g3

    # Decision-table mapping (spec §5).
    if passes_g1 and passes_g2 and passes_g3 and passes_g4 is True:
        outcome = "PASS strong"
    elif passes_g1 and passes_g2 and passes_g3 and passes_g4 is False:
        outcome = "PASS weak / replication fail"
    elif passes_g1 and passes_g2 and passes_g3 and passes_g4 is None:
        outcome = "G1+G2+G3 pass; replication not yet run"
    elif passes_g1 and passes_g2 and not passes_g3:
        outcome = "FAIL: model unstable"
    elif passes_g1 and not passes_g2:
        outcome = "FAIL: signal too narrow"
    else:
        outcome = "FAIL: no aggregate signal"

    return GateVerdict(
        n_seeds=len(main_records), K_qualifying=K, g2_threshold=g2_threshold,
        per_class=tuple(per_class),
        passes_g1=passes_g1, passes_g2=passes_g2, passes_g3=passes_g3,
        passes_g4=passes_g4, outcome=outcome,
    )


def render_decision_md(v: GateVerdict, *, noise_floor: dict) -> str:
    lines = [
        "# Fork A · Stage D — DECISION",
        "",
        f"**Outcome**: **{v.outcome}**",
        f"**n_seeds (main)**: {v.n_seeds}",
        f"**K_qualifying**: {v.K_qualifying}",
        f"**G2 threshold**: ≥{v.g2_threshold} of {v.K_qualifying}",
        "",
        "## Gate criteria",
        "",
        f"| Criterion | Verdict |",
        f"|---|---|",
        f"| G1 (aggregate Δ ≥ 3σ_noise mean) | {'✓ PASS' if v.passes_g1 else '✗ FAIL'} |",
        f"| G2 (≥{v.g2_threshold} of {v.K_qualifying} clear 3σ_noise individually) | "
        f"{'✓ PASS' if v.passes_g2 else '✗ FAIL'} "
        f"({sum(1 for p in v.per_class if p.clears_g2)} clear) |",
        f"| G3 (σ_model ≤ Δ_class for all G2-clearing classes) | "
        f"{'✓ PASS' if v.passes_g3 else '✗ FAIL'} |",
    ]
    if v.passes_g4 is None:
        lines.append("| G4 (replication) | — (not yet run) |")
    else:
        lines.append(f"| G4 (replication held-back-fold) | "
                     f"{'✓ PASS' if v.passes_g4 else '✗ FAIL'} |")
    lines.extend([
        "",
        "## Per-class results",
        "",
        "| Class | Δ_mean | σ_model | σ_noise | 3σ_noise | G2? | G3? |",
        "|---|---:|---:|---:|---:|---|---|",
    ])
    for p in v.per_class:
        lines.append(
            f"| {p.cls} | {p.delta_mean:+.4f} | {p.sigma_model:.4f} | "
            f"{p.sigma_noise:.4f} | {p.threshold_3sigma:.4f} | "
            f"{'✓' if p.clears_g2 else '·'} | {'✓' if p.stable_g3 else '✗'} |"
        )
    lines.extend([
        "",
        "## Next step (per spec §5 decision table)",
        "",
    ])
    if v.outcome == "PASS strong":
        lines.append("Proceed to **lunarastro replication** (separate spec).")
    elif v.outcome == "PASS weak / replication fail":
        lines.append("Treat as FAIL-with-partial-signal. Investigate the borderline classes that "
                     "passed main but flipped on replication.")
    elif v.outcome == "FAIL: model unstable":
        lines.append("Reduce model capacity (dropout↑ or hidden↓) OR pivot to Fork B.")
    elif v.outcome == "FAIL: signal too narrow":
        lines.append("Lift is concentrated in <11 classes. Cannot claim general astrology-predicts-events. "
                     "Consider class-specific Phase-6-style follow-on for the few classes that did clear.")
    elif v.outcome.startswith("FAIL: no aggregate"):
        lines.append("Honest null. Trigger pivot decision: **Fork B (DML deepen)** OR **Fork C (write-up as null)**.")
    return "\n".join(lines)


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out-dir", type=Path, default=Path("data/ml_runs/fork_a_stage_d"))
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s :: %(message)s")

    nf = json.loads((args.out_dir / "noise_floor.json").read_text())
    main_recs = _records_from_jsonl(args.out_dir / "main_run.jsonl")
    rep_recs = _records_from_jsonl(args.out_dir / "replication_run.jsonl") or None

    verdict = evaluate_gate(main_recs, noise_floor=nf, replication_records=rep_recs)
    md = render_decision_md(verdict, noise_floor=nf)
    (args.out_dir / "DECISION.md").write_text(md, encoding="utf-8")
    logger.info("Wrote DECISION.md — outcome: %s", verdict.outcome)
    return 0


if __name__ == "__main__":
    sys.exit(main())
