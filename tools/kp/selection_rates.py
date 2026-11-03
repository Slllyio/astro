"""How much Krishnamurti's significator selection (R24-R26) narrows the timing windows.

Pre-flight only, no outcome data: on random births, the share of ages 20-40 covered
by R17 candidate periods, by the R25 (fruitful) periods, and by the R26 (ruling
planets) periods for a moment of judgment at age 25, plus how often the R26 set
changes when the moment of judgment moves by one day.

Usage:
    python -m tools.kp.selection_rates --n 2000 --seed 20261102 --out docs/kp/kp_selection_rates_2026-11-02.json
"""

from __future__ import annotations

import argparse
import json
import random
import statistics

import swisseph as swe

from app.kp.chart import Birth, cast
from app.kp.judgment import timing_windows
from app.kp.selection import select, selected_windows
from tools.kp.base_rates import random_birth

MATTERS = ("marriage", "children", "service")


def _judged(chart, days: float) -> Birth:
    b = chart.birth
    jd = chart.jd_ut + 25 * 365.2425 + days + b.tz / 24
    y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
    return Birth(y, m, d, int(h), round((h % 1) * 60) % 60, tz=b.tz, lat=b.lat, lon=b.lon)


def _cover(ws, a: float, b: float) -> float:
    return sum(min(w.period.end_jd, b) - max(w.period.start_jd, a) for w in ws) / (b - a)


def run(n: int, seed: int) -> dict:
    rng = random.Random(seed)
    acc = {m: {"r17": [], "r25": [], "r26": [], "r26_empty": 0, "r26_changes_next_day": 0} for m in MATTERS}
    for _ in range(n):
        c = cast(random_birth(rng))
        a, b = c.jd_ut + 20 * 365.2425, c.jd_ut + 40 * 365.2425
        j0, j1 = _judged(c, 0), _judged(c, 1)
        for m in MATTERS:
            r = acc[m]
            r["r17"].append(_cover(timing_windows(c, m, a, b), a, b))
            r["r25"].append(_cover(selected_windows(c, m, a, b), a, b))
            w26 = selected_windows(c, m, a, b, judged=j0)
            r["r26"].append(_cover(w26, a, b))
            r["r26_empty"] += not w26
            r["r26_changes_next_day"] += set(select(c, m, judged=j0).selected) != set(select(c, m, judged=j1).selected)
    out = {"n": n, "seed": seed, "matters": {}}
    for m, r in acc.items():
        out["matters"][m] = {
            "coverage_median": {k: statistics.median(r[k]) for k in ("r17", "r25", "r26")},
            "coverage_mean": {k: statistics.fmean(r[k]) for k in ("r17", "r25", "r26")},
            "r26_no_window_share": r["r26_empty"] / n,
            "r26_selection_changes_next_day_share": r["r26_changes_next_day"] / n,
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261102)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(run(a.n, a.seed), fh, indent=1)


if __name__ == "__main__":
    main()
