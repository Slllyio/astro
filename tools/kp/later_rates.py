"""Fire rates of the later-author rules on ordinary charts, and their ±5-minute stability.

Pre-flight only: how often each rule fires on random births, and how often its
answer changes when the birth time moves five minutes either way. A rule that
fires on nearly every chart says nothing about any one of them. No outcome data
is read.

Usage:
    python -m tools.kp.later_rates --n 2000 --seed 20261101 --out docs/kp/kp_later_rates_2026-11-01.json
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from dataclasses import replace
from datetime import datetime, timedelta

from app.kp.chart import Birth, cast
from app.kp.later.registry import LATER_RULES
from app.kp.later.rules import later_indications
from tools.kp.base_rates import random_birth


def _shift(b: Birth, minutes: int) -> Birth:
    t = datetime(b.year, b.month, b.day, int(b.hour), int(b.minute)) + timedelta(minutes=minutes)
    return replace(b, year=t.year, month=t.month, day=t.day, hour=t.hour, minute=t.minute)


def run(n: int, seed: int) -> dict:
    """Fire rate and ±5-minute flip rate per rule on ``n`` random charts."""
    rng = random.Random(seed)
    fired: Counter[str] = Counter()
    flips: Counter[str] = Counter()
    per_chart = []
    for _ in range(n):
        b = random_birth(rng)
        keys = {f.rule.key for f in later_indications(cast(b))}
        per_chart.append(len([k for k in keys if LATER_RULES[k].context == "natal"]))
        fired.update(keys)
        around = [{f.rule.key for f in later_indications(cast(_shift(b, m)))} for m in (-5, 5)]
        for k in LATER_RULES:
            if any((k in s) != (k in keys) for s in around):
                flips[k] += 1
    rows = {k: {"fire": fired[k] / n, "flip5": flips[k] / n, "context": r.context, "source": r.source}
            for k, r in LATER_RULES.items()}
    per_chart.sort()
    return {"n": n, "seed": seed, "rules": rows,
            "natal_fired_per_chart_median": per_chart[n // 2],
            "natal_rules": sum(r.context == "natal" for r in LATER_RULES.values())}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261101)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    res = run(a.n, a.seed)
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)


if __name__ == "__main__":
    main()
