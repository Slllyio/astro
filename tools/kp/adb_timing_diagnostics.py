"""Why the KP marriage windows missed on Astro-Databank: exploratory diagnostics (not a test).

Run after ``tools.kp.adb_test`` (addendum A). Uses the same locked people and their dated marriages,
which are already spent, so nothing here is confirmatory. It asks six questions:

1. Coverage: how much of each life the windows cover, and so what hit rate chance alone gives.
2. Saturation: how many of the nine bodies signify the marriage houses at all.
3. Levels: at the real date, do the dasa, bhukti, antara and sookshma lords signify 2/7/11 more often
   than they do over the same person's own ages 18-45 (within-person, no shuffling)?
4. Birth-time sensitivity (tier A): how far 1-5 minutes move the windows and flip hits.
5. Same-day control: windows cast for random times on the same birth date and place.
6. Attenuation: if KP were exactly true and the recorded time were off by up to N minutes, how much
   of a planted effect would survive (simulation).

Usage:
    python -m tools.kp.adb_timing_diagnostics --locked data/private/kp_outcomes/adb_locked.json --events data/private/kp_outcomes/adb_events.json --gated data/private/kp_outcomes/adb_gated.json --out docs/kp/kp_adb_timing_diagnostics_2026-11-02.json
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from collections import Counter
from collections.abc import Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Final

from app.kp.chart import Birth, KPChart, cast
from app.kp.dasa import periods_between, periods_on
from app.kp.judgment import _matter, timing_windows
from app.kp.selection import select, selected_windows
from app.kp.significators import houses_signified, planet_significations

YEAR: Final[float] = 365.2425
MARRIAGE: Final = _matter("marriage")
SHIFTS: Final[tuple[int, ...]] = (-5, -3, -2, -1, 1, 2, 3, 5)
SAME_DAY_DRAWS: Final[int] = 20
SEED: Final[int] = 20261102


def _birth(rec: Mapping, minutes: float = 0.0) -> Birth:
    b = Birth(rec["year"], rec["month"], rec["day"], rec["hour"], rec["minute"], tz=rec["tz"],
              lat=rec["lat"], lon=rec["lon"], label=rec["id"])
    return b.shifted(minutes) if minutes else b


def _windows(chart: KPChart, a: float, b: float) -> dict[str, list[tuple[float, float]]]:
    return {"r25": [(w.period.start_jd, w.period.end_jd) for w in selected_windows(chart, "marriage", a, b)],
            "r17": [(w.period.start_jd, w.period.end_jd) for w in timing_windows(chart, "marriage", a, b)]}


def _covered(ws: Sequence[tuple[float, float]], a: float, b: float) -> float:
    return sum(max(0.0, min(e, b) - max(s, a)) for s, e in ws)


def _inside(jd: float, ws: Sequence[tuple[float, float]]) -> bool:
    return any(s <= jd < e for s, e in ws)


def _overlap(w1: Sequence[tuple[float, float]], w2: Sequence[tuple[float, float]], a: float, b: float) -> float:
    """Jaccard overlap of the time two window sets cover inside [a, b)."""
    inter = 0.0
    for s1, e1 in w1:
        for s2, e2 in w2:
            inter += max(0.0, min(e1, e2, b) - max(s1, s2, a))
    union = _covered(w1, a, b) + _covered(w2, a, b) - inter
    return inter / union if union else 1.0


def person(args: tuple[Mapping, float]) -> dict:
    rec, event_jd = args
    rng = random.Random(f"{SEED}-{rec['id']}")
    chart = cast(_birth(rec))
    a, b = chart.jd_ut + 18 * YEAR, chart.jd_ut + 45 * YEAR
    w = _windows(chart, a, b)
    sigs = planet_significations(chart)
    hs = {p: houses_signified(chart, p, sigs) for p in sigs}
    sel = select(chart, "marriage")
    out: dict = {
        "id": rec["id"], "tier": rec["tier"], "age": (event_jd - chart.jd_ut) / YEAR,
        "n_significators": len(sel.significators), "n_fruitful": len(sel.selected),
        "n_denial": sum(bool(hs[p] & MARRIAGE.denial) for p in hs),
        "cov": {k: _covered(v, a, b) / (b - a) for k, v in w.items()},
        "hit": {k: _inside(event_jd, v) for k, v in w.items()},
    }
    # 3. levels: share of the person's ages 18-45 under a favourable lord, vs at the event
    lv = {}
    chain = periods_on(chart, event_jd, depth=4)
    for depth in (1, 2, 3, 4):
        tot = fav = fr = 0.0
        for p in periods_between(chart, a, b, depth=depth):
            span = max(0.0, min(p.end_jd, b) - max(p.start_jd, a))
            tot += span
            fav += span * bool(hs[p.lords[-1]] & MARRIAGE.favourable)
            fr += span * (p.lords[-1] in sel.selected)
        lord = chain[depth - 1].lords[-1] if len(chain) >= depth else None
        lv[depth] = {"share_fav": fav / tot, "share_fruitful": fr / tot,
                     "event_fav": bool(lord and hs[lord] & MARRIAGE.favourable),
                     "event_fruitful": bool(lord and lord in sel.selected)}
    out["levels"] = lv
    out["csl7"] = chart.cusp(7).sub_lord
    # 4. birth-time sensitivity (computed for everyone; reported for tier A)
    sens = {}
    for m in SHIFTS:
        c2 = cast(_birth(rec, m))
        w2 = _windows(c2, a, b)
        sens[m] = {"jaccard_r25": _overlap(w["r25"], w2["r25"], a, b),
                   "flip_r25": _inside(event_jd, w2["r25"]) != out["hit"]["r25"],
                   "csl7_changed": c2.cusp(7).sub_lord != out["csl7"],
                   "selected_changed": set(select(c2, "marriage").selected) != set(sel.selected)}
    out["sens"] = sens
    # 5. same-day control: random clock times on the same date and place
    same = []
    for _ in range(SAME_DAY_DRAWS):
        r2 = dict(rec, hour=rng.randrange(24), minute=rng.randrange(60))
        c2 = cast(_birth(r2))
        w2 = _windows(c2, a, b)
        same.append({"hit_r25": _inside(event_jd, w2["r25"]), "cov_r25": _covered(w2["r25"], a, b) / (b - a)})
    out["same_day"] = same
    # 6. attenuation: a planted event inside the windows of the chart at (stated + d) minutes,
    #    scored on the stated chart's windows, for |d| up to 0, 2, 5, 10 minutes
    att = {}
    for err in (0, 2, 5, 10):
        hits = n = 0
        for _ in range(5):
            d = rng.uniform(-err, err)
            wt = _windows(cast(_birth(rec, d)), a, b)["r25"] if err else w["r25"]
            if not wt:
                continue
            s, e = rng.choice(wt)
            jd = rng.uniform(s, e)
            hits += _inside(jd, w["r25"])
            n += 1
        att[err] = (hits, n)
    out["attenuation"] = att
    return out


def summarise(rows: list[dict], gated: Sequence[Mapping]) -> dict:
    def mean(xs):
        xs = list(xs)
        return round(sum(xs) / len(xs), 4) if xs else None

    res: dict = {"people": len(rows), "tier_a": sum(r["tier"] == "A" for r in rows)}
    res["ages"] = {"median": round(statistics.median(r["age"] for r in rows), 1),
                   "q10": round(sorted(r["age"] for r in rows)[len(rows) // 10], 1),
                   "q90": round(sorted(r["age"] for r in rows)[9 * len(rows) // 10], 1)}
    res["coverage"] = {k: {"mean": mean(r["cov"][k] for r in rows), "hit_rate": mean(r["hit"][k] for r in rows)}
                       for k in ("r25", "r17")}
    res["saturation"] = {
        "significators_of_2_7_11_of_9": dict(sorted(Counter(r["n_significators"] for r in rows).items())),
        "fruitful_of_9": dict(sorted(Counter(r["n_fruitful"] for r in rows).items())),
        "bodies_also_signifying_1_6_10": dict(sorted(Counter(r["n_denial"] for r in rows).items())),
    }
    names = {1: "dasa", 2: "bhukti", 3: "antara", 4: "sookshma"}
    res["levels"] = {}
    for d in (1, 2, 3, 4):
        k = str(d) if str(d) in rows[0]["levels"] else d
        res["levels"][names[d]] = {
            "lord_signifies_2_7_11": {"observed": sum(r["levels"][k]["event_fav"] for r in rows),
                                      "expected": round(sum(r["levels"][k]["share_fav"] for r in rows), 1)},
            "lord_fruitful_R25": {"observed": sum(r["levels"][k]["event_fruitful"] for r in rows),
                                  "expected": round(sum(r["levels"][k]["share_fruitful"] for r in rows), 1)},
        }
    ta = [r for r in rows if r["tier"] == "A"]
    res["birth_time_sensitivity_tier_a"] = {}
    for m in SHIFTS:
        k = str(m) if str(m) in ta[0]["sens"] else m
        res["birth_time_sensitivity_tier_a"][f"{m:+d} min"] = {
            "r25_window_overlap": mean(r["sens"][k]["jaccard_r25"] for r in ta),
            "event_hit_flips": mean(r["sens"][k]["flip_r25"] for r in ta),
            "csl7_changes": mean(r["sens"][k]["csl7_changed"] for r in ta),
            "fruitful_set_changes": mean(r["sens"][k]["selected_changed"] for r in ta),
        }
    res["same_day_control"] = {
        "own_time_hit_rate_r25": mean(r["hit"]["r25"] for r in rows),
        "random_time_same_day_hit_rate_r25": mean(s["hit_r25"] for r in rows for s in r["same_day"]),
        "random_time_same_day_coverage_r25": mean(s["cov_r25"] for r in rows for s in r["same_day"]),
    }
    att = {}
    for err in (0, 2, 5, 10):
        k = str(err) if str(err) in rows[0]["attenuation"] else err
        h = sum(r["attenuation"][k][0] for r in rows)
        n = sum(r["attenuation"][k][1] for r in rows)
        att[f"up to {err} min"] = round(h / n, 4) if n else None
    res["attenuation_planted_hit_rate"] = att
    res["attenuation_note"] = "chance level = mean R25 coverage; 1.0 = a true KP effect fully recovered"
    mins = Counter(int(r["minute"]) for r in gated if r["tier"] == "A")
    n = sum(mins.values())
    res["recorded_minutes_tier_a"] = {
        "n": n, "on_00_15_30_45": round(sum(v for m, v in mins.items() if m % 15 == 0) / n, 4),
        "on_multiple_of_5": round(sum(v for m, v in mins.items() if m % 5 == 0) / n, 4),
        "expected_if_uniform": {"15": 0.0667, "5": 0.2},
    }
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--locked", required=True)
    ap.add_argument("--events", required=True)
    ap.add_argument("--gated", required=True)
    ap.add_argument("--out", default="")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    locked = json.loads(Path(a.locked).read_text(encoding="utf-8"))
    gated = json.loads(Path(a.gated).read_text(encoding="utf-8"))
    by_id = {r["id"]: r for r in gated}
    births = {p["id"]: p["birth_jd"] for p in locked["people"]}
    jobs = []
    for e in json.loads(Path(a.events).read_text(encoding="utf-8")):
        if e["matter"] != "marriage" or e["id"] not in by_id:
            continue
        y, m, d = (int(x) for x in e["date"].split("-"))
        import swisseph as swe
        jd = swe.julday(y, m, d, 12.0)
        age = (jd - births[e["id"]]) / YEAR
        if 18 <= age < 45:
            jobs.append((by_id[e["id"]], jd))
    with ProcessPoolExecutor(a.workers) as ex:
        rows = list(ex.map(person, jobs, chunksize=4))
    res = summarise(rows, gated)
    text = json.dumps(res, indent=1)
    if a.out:
        Path(a.out).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
