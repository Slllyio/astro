"""The doctrine ratchet — turn validation results into monotonic rule statuses.

Reads a ``population_validation.json`` (from population_validate.run) and applies
the pre-registered gate (DOCTRINE_RATCHET_PLAN.md §4) to assign each rule a
status on the promotion ladder:

    candidate -> provisional -> validated -> locked   (monotonic up)
    candidate -> refuted                              (terminal, high power)

Because this is a **single corpus**, no rule can reach `validated` here (that
needs cross-corpus replication, G2). A rule that clears G1 is `provisional`; a
rule that fails G1 at high power is `refuted`.

The gate is evaluated on the **permutation null** only (the exposure null is
length-biased and descriptive). Verdicts are written to
docs/raman_saab/RATCHET_LEDGER.json — the append-only source of truth.
"""
from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from app.medini.ml.raman_saab.rules import CANDIDATE_RULES

logger = logging.getLogger(__name__)

# Pre-registered G1 thresholds (DOCTRINE_RATCHET_PLAN.md §4).
_RR_ENRICH = 1.20
_RR_DEPLETE = 0.83
_MIN_POWER_N = 5000  # below this, a failure is "underpowered", not "refuted"


def _rule_by_id() -> dict:
    return {r.rule_id: r for r in CANDIDATE_RULES}


def apply_gate(result: dict) -> list[dict]:
    """Return one ledger row per rule with its post-gate status."""
    rules = _rule_by_id()
    n = result["n_persons"]
    alpha = result["bonferroni_alpha"]
    # Best permutation-null result per rule (most extreme in predicted direction).
    perm = [r for r in result["rule_results"] if r["null"] == "permutation"]
    by_rule: dict[str, list] = {}
    for r in perm:
        by_rule.setdefault(r["rule_id"], []).append(r)

    ledger: list[dict] = []
    for rid, rule in rules.items():
        rows = by_rule.get(rid, [])
        passed = False
        best = None
        for row in rows:
            if rule.direction == "enrich":
                g1 = row["rr"] >= _RR_ENRICH and row["p_one_sided"] < alpha
            else:
                g1 = row["rr"] <= _RR_DEPLETE and row["p_one_sided"] < alpha
            if g1:
                passed = True
            # track the most favourable level for reporting
            if best is None or (
                rule.direction == "enrich" and row["rr"] > best["rr"]
            ) or (rule.direction == "deplete" and row["rr"] < best["rr"]):
                best = row
        if passed:
            status = "provisional"  # single corpus -> cannot reach 'validated'
            reason = "cleared G1 on the permutation null; awaiting cross-corpus (G2)"
        elif n >= _MIN_POWER_N:
            status = "refuted"
            reason = (f"failed G1 at high power (N={n}); "
                      f"best {best['level']} RR={best['rr']} "
                      f"(need {'>=1.20' if rule.direction=='enrich' else '<=0.83'})")
        else:
            status = "candidate"
            reason = "underpowered; inconclusive"
        ledger.append({
            "rule_id": rid, "family": rule.family, "direction": rule.direction,
            "from_status": "candidate", "to_status": status,
            "gate": {"G1": passed, "G2_replication": False, "G3": None, "G4": None},
            "best_result": best, "n": n, "bonferroni_alpha": alpha,
            "citation": rule.citation, "reason": reason,
        })
    return ledger


def write_ledger(result: dict, ledger_path: Path, run_id: str) -> list[dict]:
    ledger = apply_gate(result)
    for row in ledger:
        row["run_id"] = run_id
    payload = {"run_id": run_id, "corpus": result.get("corpus"),
               "entries": ledger}
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(json.dumps(payload, indent=2))
    logger.info("wrote ledger -> %s", ledger_path)
    return ledger


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--result", type=Path,
                   default=Path("data/ml_runs/raman_saab/population_validation.json"))
    p.add_argument("--ledger", type=Path,
                   default=Path("docs/raman_saab/RATCHET_LEDGER.json"))
    p.add_argument("--run-id", default="manual")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    result = json.loads(args.result.read_text())
    ledger = write_ledger(result, args.ledger, args.run_id)
    print(f"{'rule':<36}{'status':<14}{'reason'}")
    for row in ledger:
        print(f"{row['rule_id']:<36}{row['to_status']:<14}{row['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
