"""raman_saab orchestrator — validate the death-timing family, then ratchet.

Runs the population validation and writes both the machine ledger
(docs/raman_saab/RATCHET_LEDGER.json) and the JSON result
(data/ml_runs/raman_saab/population_validation.json). The human-readable
VERDICT.md is authored from these artifacts.

Usage:
    python -m app.medini.ml.raman_saab.cli \
        --corpus app/medini/data/raman_saab/death_corpus.parquet \
        --run-id 2026-07-02T-wikidata
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from app.medini.ml.raman_saab.population_validate import run as run_validation
from app.medini.ml.raman_saab.ratchet import write_ledger


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus", type=Path,
                   default=Path("app/medini/data/raman_saab/death_corpus.parquet"))
    p.add_argument("--out", type=Path, default=Path("data/ml_runs/raman_saab"))
    p.add_argument("--ledger", type=Path,
                   default=Path("docs/raman_saab/RATCHET_LEDGER.json"))
    p.add_argument("--hour", type=float, default=12.0)
    p.add_argument("--run-id", default="manual")
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    result = run_validation(args.corpus, args.out, hour=args.hour)
    ledger = write_ledger(result, args.ledger, args.run_id)
    n_ref = sum(1 for r in ledger if r["to_status"] == "refuted")
    n_prov = sum(1 for r in ledger if r["to_status"] == "provisional")
    print(f"\nraman_saab: {len(ledger)} rules -> "
          f"{n_prov} provisional, {n_ref} refuted (N={result['n_persons']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
