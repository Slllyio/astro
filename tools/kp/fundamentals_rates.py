"""Pre-flight for ruling R29: how often each Reader 2 sign rule fires on random births.

No outcome data. Reports the share of random charts meeting each encoded rule, so a reader can see
how common each indication is and which ones could be tested with a sample of a given size.

Usage:
    python -m tools.kp.fundamentals_rates --n 2000 --seed 7 --out docs/kp/kp_fundamentals_rates_2026-11-02.json
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter

from app.kp.chart import cast
from app.kp.fundamentals import fundamentals
from tools.kp.base_rates import random_birth


def run(n: int, seed: int) -> dict:
    rng = random.Random(seed)
    fired: Counter[str] = Counter()
    keys: list[str] = []
    for _ in range(n):
        fs = fundamentals(cast(random_birth(rng)))
        keys = [f.key for f in fs]
        fired.update(f.key for f in fs if f.met)
    return {"n": n, "seed": seed, "rate": {k: round(fired[k] / n, 3) for k in keys}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    text = json.dumps(run(a.n, a.seed), indent=1)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
