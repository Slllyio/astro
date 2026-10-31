"""KP engine pre-flight: verdict base rates and birth-time stability.

Answers two questions before any real-people test, using ordinary charts and
no outcomes at all:

1. Base rate. For each matter, what share of charts gets PROMISED / DENIED /
   MIXED / NOT_SIGNIFIED? A matter that is PROMISED for nearly everyone
   cannot beat "always yes" on real people.
2. Birth-time stability. For each matter, how often does the verdict change
   when the time moves by ±2, ±5, ±15 minutes?
3. Timing coverage. Over ages 20-40, what share of the time is covered by
   candidate marriage periods? Near 100% means the timing rule cannot miss.

Charts: uniform random dates 1940-2005, uniform random local time, places
drawn from a fixed list of Indian cities. Seeded, so reruns give identical
numbers.

Usage:
    python -m tools.kp.base_rates --n 2000 --seed 20261031 --out data/kp/base_rates.json
"""

from __future__ import annotations

import argparse
import json
import logging
import random
from collections import Counter, defaultdict
from pathlib import Path

from app.kp.chart import Birth, cast
from app.kp.judgment import MATTERS, _core, timing_windows

logger = logging.getLogger(__name__)

CITIES = (
    ("Delhi", 28.61, 77.21), ("Mumbai", 19.08, 72.88), ("Chennai", 13.08, 80.27),
    ("Kolkata", 22.57, 88.36), ("Bangalore", 12.97, 77.59), ("Kanpur", 26.45, 80.33),
    ("Hyderabad", 17.39, 78.49), ("Ahmedabad", 23.02, 72.57), ("Lucknow", 26.85, 80.95),
    ("Pune", 18.52, 73.86), ("Patna", 25.59, 85.14), ("Jaipur", 26.91, 75.79),
)
WINDOWS = (2, 5, 15)


def random_birth(rng: random.Random) -> Birth:
    """One uniformly random Indian birth, 1940-2005."""
    _, lat, lon = rng.choice(CITIES)
    y = rng.randint(1940, 2005)
    m = rng.randint(1, 12)
    d = rng.randint(1, 28)
    mins = rng.randrange(1440)
    return Birth(y, m, d, mins // 60, mins % 60, tz=5.5, lat=lat, lon=lon)


def run(n: int, seed: int) -> dict:
    """Compute base rates, stability and timing coverage on ``n`` random charts."""
    rng = random.Random(seed)
    verdicts: dict[str, Counter] = defaultdict(Counter)
    changed: dict[str, Counter] = defaultdict(Counter)
    coverage: list[float] = []
    csl_breadth: list[int] = []
    for i in range(n):
        b = random_birth(rng)
        chart = cast(b)
        for key, m in MATTERS.items():
            v, _, houses, _ = _core(chart, m)
            verdicts[key][v] += 1
            if key == "marriage":
                csl_breadth.append(len(houses))
            for w in WINDOWS:
                alt = {_core(cast(b.shifted(s)), m)[0] for s in (-w, w)}
                if alt != {v}:
                    changed[key][w] += 1
        if i % 4 == 0:  # timing is slower; sample a quarter of charts
            j0, j1 = chart.jd_ut + 20 * 365.2425, chart.jd_ut + 40 * 365.2425
            tw = timing_windows(chart, "marriage", j0, j1)
            covered = sum(min(t.period.end_jd, j1) - max(t.period.start_jd, j0) for t in tw)
            coverage.append(covered / (j1 - j0))
    out = {
        "n": n, "seed": seed,
        "verdict_share": {k: {v: round(c / n, 4) for v, c in cnt.items()} for k, cnt in verdicts.items()},
        "changes_within_window": {
            k: {f"±{w}min": round(changed[k][w] / n, 4) for w in WINDOWS} for k in MATTERS
        },
        "marriage_timing_coverage_age20_40": {
            "charts": len(coverage),
            "mean": round(sum(coverage) / len(coverage), 4),
            "min": round(min(coverage), 4), "max": round(max(coverage), 4),
        },
        "marriage_csl_houses_signified_mean": round(sum(csl_breadth) / len(csl_breadth), 2),
    }
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261031)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    res = run(a.n, a.seed)
    text = json.dumps(res, indent=2)
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
