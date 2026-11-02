"""Exploratory: do Krishnamurti's own elimination rules sharpen the marriage windows? (not a test)

On the same spent Astro-Databank marriages as ``adb_timing_diagnostics``, windows are rebuilt with
only the significators that survive each of his filters, and the hit rate is compared with the
share of ages 18-45 the windows cover (chance) and with windows of the same filter cast for random
clock times on the same birth date.

Filters (all on top of R25, fruitful sub-lord):
* ``retro``: drop a significator in the star of a planet retrograde at birth (KPR6 pp.146-147).
* ``tempter``: drop a significator whose sub-lord also signifies 1, 6 or 10 (KPR5 pp.201-202).
* ``strong``: keep only R24's strong significators (KPR4 p.118, KPR5 pp.208-209).

Usage:
    python -m tools.kp.adb_filter_check --locked data/private/kp_outcomes/adb_locked.json --events data/private/kp_outcomes/adb_events.json --gated data/private/kp_outcomes/adb_gated.json --out docs/kp/kp_adb_filter_check_2026-11-02.json
"""

from __future__ import annotations

import argparse
import json
import random
from concurrent.futures import ProcessPoolExecutor
from itertools import combinations
from pathlib import Path
from typing import Final

import swisseph as swe

from app.kp.chart import NODES, KPChart, cast
from app.kp.dasa import periods_between
from app.kp.selection import select
from tools.kp.adb_timing_diagnostics import YEAR, _birth, _covered, _inside

FILTERS: Final[tuple[str, ...]] = ("retro", "tempter", "strong")
COMBOS: Final[tuple[tuple[str, ...], ...]] = ((),) + tuple(
    c for n in (1, 2, 3) for c in combinations(FILTERS, n))
DRAWS: Final[int] = 10


def keep(chart: KPChart, combo: tuple[str, ...]) -> set[str]:
    sel = select(chart, "marriage")
    out = set(sel.selected)
    if "retro" in combo:
        out = {p for p in out if not (chart.planets[p].star_lord not in NODES
                                      and chart.planets[chart.planets[p].star_lord].retrograde)}
    if "tempter" in combo:
        out = {p for p in out if not sel.fruit[p].denial}
    if "strong" in combo:
        out &= {s.planet for s in sel.strong}
    return out


def windows(chart: KPChart, k: set[str], a: float, b: float) -> list[tuple[float, float]]:
    return [(p.start_jd, p.end_jd) for p in periods_between(chart, a, b, depth=3) if set(p.lords) <= k]


def person(args: tuple[dict, float]) -> dict:
    rec, ev = args
    rng = random.Random(f"filter-{rec['id']}")
    chart = cast(_birth(rec))
    a, b = chart.jd_ut + 18 * YEAR, chart.jd_ut + 45 * YEAR
    others = [cast(_birth(dict(rec, hour=rng.randrange(24), minute=rng.randrange(60)))) for _ in range(DRAWS)]
    out = {}
    for combo in COMBOS:
        w = windows(chart, keep(chart, combo), a, b)
        same = [_inside(ev, windows(c, keep(c, combo), a, b)) for c in others]
        out["+".join(combo) or "r25"] = {"cov": _covered(w, a, b) / (b - a), "hit": _inside(ev, w),
                                         "same_day_hit": sum(same) / len(same)}
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--locked", required=True)
    ap.add_argument("--events", required=True)
    ap.add_argument("--gated", required=True)
    ap.add_argument("--out", default="")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    births = {p["id"]: p["birth_jd"] for p in json.loads(Path(a.locked).read_text())["people"]}
    by_id = {r["id"]: r for r in json.loads(Path(a.gated).read_text())}
    jobs = []
    for e in json.loads(Path(a.events).read_text()):
        if e["matter"] == "marriage" and e["id"] in by_id:
            y, m, d = (int(x) for x in e["date"].split("-"))
            jd = swe.julday(y, m, d, 12.0)
            if 18 <= (jd - births[e["id"]]) / YEAR < 45:
                jobs.append((by_id[e["id"]], jd))
    with ProcessPoolExecutor(a.workers) as ex:
        rows = list(ex.map(person, jobs, chunksize=4))
    res = {"people": len(rows)}
    for k in rows[0]:
        n = len(rows)
        cov = sum(r[k]["cov"] for r in rows) / n
        hit = sum(r[k]["hit"] for r in rows) / n
        res[k] = {"coverage": round(cov, 4), "hit_rate": round(hit, 4),
                  "lift_vs_coverage": round(hit / cov, 3) if cov else None,
                  "same_day_random_time_hit_rate": round(sum(r[k]["same_day_hit"] for r in rows) / n, 4),
                  "people_with_no_window": sum(r[k]["cov"] == 0 for r in rows)}
    text = json.dumps(res, indent=1)
    if a.out:
        Path(a.out).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
