"""Measure a salience ranking against Raman's own attention — the number everything must beat.

Scores a chart-ranking of houses against the houses Raman actually emphasised in his worked
readings. Run BEFORE any salience code exists, to fix the baseline for today's fixed-order
digest; run again after, to see whether the faculty is real.

Comparisons are PAIRED and bootstrapped, never unpaired proportions. With ~14 holdout charts an
unpaired 95% CI is about +/-21 points, so an unpaired difference of any plausible size is
unreadable; comparing two rankings on the SAME chart removes the between-chart variance that
swamps it.

The bar is not zero. Raman genuinely judges the Lagna first (HTJAH-I:16001), so "always say the
Lagna" already scores ~63% precision@1. That trivial ranking is reported alongside every result.

Usage:
    py -3.12 tools/raman_saab/measure_salience.py --split holdout
    py -3.12 tools/raman_saab/measure_salience.py --split all --ranker digest
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
from pathlib import Path
from typing import Callable, Optional

from app.raman_saab.detailed_report import build_detailed_report
from tools.raman_saab.admit_attention_charts import parse_birth

BENCH = "tests/fixtures/notable_attention.json"

#: the constant ranking any real faculty has to beat, in Raman's own order of habit
TRIVIAL_ORDER: tuple[int, ...] = (1, 10, 7, 9, 2, 4, 5, 8, 11, 3, 6, 12)


def rank_digest(report) -> list[int]:
    """Houses in the order today's fixed-template digest surfaces them."""
    seen: list[int] = []
    for item in report.digest.items:
        for h in item.houses:
            if h not in seen:
                seen.append(h)
    return seen


def rank_trivial(report) -> list[int]:
    return list(TRIVIAL_ORDER)


RANKERS: dict[str, Callable[[object], list[int]]] = {
    "digest": rank_digest,
    "trivial": rank_trivial,
}


def score(ranked: list[int], truth: set[int]) -> dict[str, float]:
    """precision@1, precision@3, recall@3 and reciprocal rank of the first correct house."""
    if not ranked or not truth:
        return {}
    top3 = ranked[:3]
    rr = 0.0
    for i, h in enumerate(ranked, start=1):
        if h in truth:
            rr = 1.0 / i
            break
    return {
        "p@1": 1.0 if ranked[0] in truth else 0.0,
        "p@3": len(set(top3) & truth) / 3.0,
        "r@3": len(set(top3) & truth) / len(truth),
        "mrr": rr,
    }


def _paired_bootstrap(a: list[float], b: list[float], n: int = 10000) -> tuple[float, float, float]:
    """(mean difference a-b, lo, hi) — resample CHARTS, keeping each chart's pair together."""
    diffs = [x - y for x, y in zip(a, b)]
    obs = statistics.mean(diffs)
    rng = random.Random(20260805)
    means = []
    for _ in range(n):
        s = [diffs[rng.randrange(len(diffs))] for _ in range(len(diffs))]
        means.append(statistics.mean(s))
    means.sort()
    return obs, means[int(0.025 * n)], means[int(0.975 * n)]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bench", default=BENCH)
    ap.add_argument("--split", default="holdout", choices=("tune", "holdout", "all"))
    ap.add_argument("--ranker", default="digest", choices=sorted(RANKERS))
    ap.add_argument("--target", default="emphasis", choices=("emphasis", "top3count"))
    args = ap.parse_args()

    data = json.loads(Path(args.bench).read_text(encoding="utf-8"))
    charts = [c for c in data["charts"] if c.get("admitted")
              and (args.split == "all" or c.get("split") == args.split)]

    rows: list[tuple[str, dict, dict]] = []
    skipped: list[str] = []
    for rec in charts:
        truth: set[int]
        if args.target == "emphasis":
            truth = set(rec.get("emphasised_houses") or [])
        else:
            hs = {int(k): v for k, v in (rec.get("houses") or {}).items()}
            truth = {h for h, _ in sorted(hs.items(), key=lambda kv: -kv[1])[:3]}
        if not truth:
            skipped.append(rec["name"])
            continue
        birth = parse_birth(rec)
        if birth is None:
            skipped.append(rec["name"])
            continue
        # Read the chart DURING the life, not in 2026. Two reasons: the Vimshottari sequence is
        # generated for 120 years from birth, so anyone born before ~1906 has no "currently
        # running" period and `synthesize` raises; and Raman was reading a life in progress, so
        # a mid-life reference date is the faithful one. Age 35 sits inside every life here.
        on = (birth.year + 35, birth.month, birth.day)
        try:
            report = build_detailed_report(birth, on=on, ayanamsa="raman")
        except Exception as exc:                                     # noqa: BLE001
            skipped.append(f"{rec['name']} ({exc})")
            continue
        rows.append((rec["name"],
                     score(RANKERS[args.ranker](report), truth),
                     score(rank_trivial(report), truth)))

    if not rows:
        print("no scorable charts"); return

    print(f"benchmark {args.bench} | split={args.split} | ranker={args.ranker} "
          f"| target={args.target}")
    print(f"charts scored: {len(rows)}   skipped: {len(skipped)}")
    print()
    print(f"{'chart':32s} {'p@1':>6s} {'p@3':>6s} {'r@3':>6s} {'mrr':>6s}   "
          f"{'(trivial p@1)':>14s}")
    for name, s, t in rows:
        print(f"{name[:32]:32s} {s['p@1']:6.2f} {s['p@3']:6.2f} {s['r@3']:6.2f} "
              f"{s['mrr']:6.2f}   {t['p@1']:14.2f}")

    print()
    print(f"{'metric':8s} {args.ranker:>10s} {'trivial':>10s} {'diff':>8s}  "
          f"{'95% CI (paired bootstrap)':>28s}")
    for k in ("p@1", "p@3", "r@3", "mrr"):
        a = [s[k] for _, s, _ in rows]
        b = [t[k] for _, _, t in rows]
        obs, lo, hi = _paired_bootstrap(a, b)
        verdict = "" if lo <= 0 <= hi else ("  BETTER" if obs > 0 else "  WORSE")
        print(f"{k:8s} {statistics.mean(a):10.3f} {statistics.mean(b):10.3f} "
              f"{obs:+8.3f}  [{lo:+.3f}, {hi:+.3f}]{verdict}")

    print()
    print("A CI spanning zero means NO DETECTABLE DIFFERENCE at this sample size — not a tie,")
    print("and not evidence of equivalence. It means the benchmark cannot yet tell them apart.")
    if skipped:
        print(f"\nskipped: {', '.join(skipped[:8])}{' ...' if len(skipped) > 8 else ''}")


if __name__ == "__main__":
    main()
