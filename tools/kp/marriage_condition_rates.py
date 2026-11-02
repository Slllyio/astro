"""Pre-flight for ruling R28: how often each traditional marriage condition fires on random births.

No outcome data. Reports the share of random charts meeting each encoded condition, and how many
"youth" and "late" conditions the median chart meets, so a reader can see how common they are.

Usage:
    python -m tools.kp.marriage_condition_rates --n 2000 --seed 7 --out docs/kp/kp_marriage_condition_rates_2026-11-02.json
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from collections import Counter

from app.kp.chart import cast
from app.kp.marriage_conditions import marriage_conditions
from tools.kp.base_rates import random_birth


def run(n: int, seed: int) -> dict:
    rng = random.Random(seed)
    fired: Counter[str] = Counter()
    youth, late, both = [], [], 0
    for _ in range(n):
        cs = marriage_conditions(cast(random_birth(rng)))
        met = [c for c in cs if c.met]
        fired.update(c.key for c in met)
        y = sum(c.group == "youth" for c in met)
        lt = sum(c.group == "late" for c in met)
        youth.append(y)
        late.append(lt)
        both += bool(y and lt)
    keys = [c.key for c in cs]
    return {
        "n": n, "seed": seed,
        "rate": {k: round(fired[k] / n, 3) for k in keys},
        "median_youth_met": statistics.median(youth),
        "share_any_youth": round(sum(y > 0 for y in youth) / n, 3),
        "median_late_met": statistics.median(late),
        "share_any_late": round(sum(x > 0 for x in late) / n, 3),
        "share_both": round(both / n, 3),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    r = run(a.n, a.seed)
    text = json.dumps(r, indent=1)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
