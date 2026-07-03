"""Run-3 parameterized gate — per-test thresholds + refutable-power rule.

Replaces run 1/2's blanket ``_MIN_POWER_N = 5000`` with a pre-registered
per-test power calculation (docs/raman_saab/run3_gate.toml, frozen in
RUN3_PREREG.md §4 before the observed evaluation):

    power = Φ( (rr_threshold − 1) · E / √var − z_α )

A test that fails its threshold is ``refuted`` only when that power ≥
``min_power``; otherwise it stays ``candidate`` (underpowered). A pass is
capped at ``provisional`` (single corpus — G2 replication unmet). Ledger rows
carry ``power_at_threshold`` so a "refuted" is auditable.

Run 1/2's ``ratchet.py`` is left untouched for ledger reproducibility.
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import tomllib
from pathlib import Path

from scipy.stats import norm

logger = logging.getLogger(__name__)

_DEFAULT_CFG = Path("docs/raman_saab/run3_gate.toml")


def load_gate_config(path: Path = _DEFAULT_CFG) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)


def power_at_threshold(rr_threshold: float, expected: float, var: float,
                       alpha: float) -> float:
    """One-sided power to detect RR == rr_threshold under the PB normal."""
    if var <= 0 or expected <= 0:
        return 0.0
    z_alpha = norm.isf(alpha)
    shift = (rr_threshold - 1.0) * expected / math.sqrt(var)
    return float(norm.cdf(shift - z_alpha))


def apply_gate_run3(result: dict, cfg: dict | None = None) -> list[dict]:
    """One ledger row per configured primary test."""
    cfg = cfg or load_gate_config()
    tests_cfg = cfg["tests"]
    alpha = cfg["alpha_budget"] / len(tests_cfg)
    min_power = cfg["min_power"]
    rows_by_test = {r["test"]: r for r in result["results"]
                    if r["tier"] == "primary"}
    ledger: list[dict] = []
    for test_id, tcfg in tests_cfg.items():
        row = rows_by_test.get(test_id)
        if row is None:
            logger.warning("gate config test %s missing from results", test_id)
            continue
        thr = float(tcfg["rr_threshold"])
        rr = row["rr"] or 0.0
        pw = power_at_threshold(thr, row["expected"], row["var"], alpha)
        g1 = rr >= thr and row["p_one_sided"] < alpha
        if g1:
            status, reason = cfg.get("ceiling", "provisional"), (
                f"cleared G1 (RR={rr} >= {thr}, p={row['p_one_sided']:.2e} "
                f"< {alpha:.4f}); ceiling {cfg.get('ceiling')} pending G2")
        elif pw >= min_power:
            status = "refuted"
            reason = (f"failed G1 at adequate power (power={pw:.3f} >= "
                      f"{min_power} for RR>={thr}); observed RR={rr}")
        else:
            status = "candidate"
            reason = f"underpowered (power={pw:.3f} < {min_power})"
        ledger.append({
            "rule_id": f"raman.triple_lock.{test_id}",
            "family": "longevity",
            "direction": tcfg["direction"],
            "from_status": "candidate", "to_status": status,
            "gate": {"G1": g1, "G2_replication": False,
                     "power_at_threshold": round(pw, 4)},
            "best_result": {k: row[k] for k in
                            ("rr", "z", "p_one_sided", "observed", "expected")},
            "n": result["n_persons"], "alpha": alpha,
            "rr_threshold": thr, "reason": reason,
        })
    return ledger


def append_ledger(entries: list[dict], ledger_path: Path, run_id: str) -> None:
    """Append a run block to the ratchet ledger (append-only discipline)."""
    payload = json.loads(ledger_path.read_text()) if ledger_path.exists() else {}
    runs = payload.get("runs")
    if runs is None:
        # migrate the flat run-1/2 shape {run_id, corpus, entries} in place
        runs = [payload] if payload else []
    for e in entries:
        e["run_id"] = run_id
    runs.append({"run_id": run_id, "entries": entries})
    ledger_path.write_text(json.dumps({"runs": runs}, indent=2))
    logger.info("appended %d entries -> %s", len(entries), ledger_path)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--result", type=Path,
                   default=Path("data/ml_runs/raman_saab/run3/"
                                "triple_lock_validation.json"))
    p.add_argument("--ledger", type=Path,
                   default=Path("docs/raman_saab/RATCHET_LEDGER.json"))
    p.add_argument("--run-id", required=True)
    p.add_argument("--dry-run", action="store_true",
                   help="print the gate outcome without touching the ledger")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    result = json.loads(args.result.read_text())
    entries = apply_gate_run3(result)
    print(f"{'test':<34}{'status':<14}{'power':>7}  reason")
    for e in entries:
        print(f"{e['rule_id']:<34}{e['to_status']:<14}"
              f"{e['gate']['power_at_threshold']:>7.3f}  {e['reason']}")
    if not args.dry_run:
        append_ledger(entries, args.ledger, args.run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
