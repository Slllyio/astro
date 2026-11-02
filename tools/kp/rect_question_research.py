"""Research: which rectification questions split the candidate minutes, across many charts?

For N synthetic births (Indian places, 1950-1995, any time of day) and a +/- W minute window:

1. Information value of every fact in ``app.kp.rect_questions.FACTS`` under a uniform prior:
   expected bits, share of charts where the fact splits the window at all, share where it is in
   that chart's top five. This says which questions are generally useful and how chart-specific
   the choice is.
2. Resolution floor: runs of adjacent minutes that NO fact in the bank can tell apart.
3. Simulated sessions (greedy: always ask the highest-information question, then update):
   * ``model``  answers drawn from the rules at the true minute (best case: the rules are right);
   * ``half``   each answer from the true minute with probability 0.5, otherwise from the
     window-average answer (rules half right);
   * ``null``   every answer from the window-average answer, independent of the true minute
     (the rules carry no truth, which is what the validation program measured on real lives).
   After k questions: median 90 % credible-set width, how often it contains the true minute,
   and median |peak - truth|. The null row shows how much narrowing the method produces with
   no truth in it at all.

Usage:
    python -m tools.kp.rect_question_research --n 200 --window 30 --out docs/kp/RECTIFICATION_QUESTIONS_RESEARCH
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import random
import statistics
from collections import defaultdict
from multiprocessing import Pool

import numpy as np
import swisseph as swe

from app.kp.chart import Birth
from app.kp.rect_questions import (FACT_BY_KEY, answer_probs, boundaries, build, credible, info_gain,
                                   resolution_classes, uniform)

logger = logging.getLogger(__name__)

SEED = 20261102
TODAY = (2026, 11, 2)
PLACES = [(28.61, 77.21), (19.08, 72.88), (13.08, 80.27), (22.57, 88.36), (12.97, 77.59),
          (17.39, 78.49), (26.85, 80.95), (23.03, 72.58), (26.91, 75.79), (11.02, 76.96),
          (30.73, 76.78), (25.32, 82.97), (21.15, 79.09), (27.23, 79.03), (9.93, 76.27)]
KS = (1, 2, 3, 5, 8, 12)
#: What a typical adult can answer: every yes/no and choice fact, and the common dated events.
TYPICAL_DATES = {"date_marriage", "date_child", "date_job", "date_move", "date_property"}
SIMS_PER_CHART = 4


def births(n: int, seed: int) -> list[Birth]:
    rng = random.Random(seed)
    out = []
    a, z = swe.julday(1950, 1, 1, 0.0), swe.julday(1995, 12, 31, 0.0)
    for _ in range(n):
        y, m, d, _ = swe.revjul(a + rng.random() * (z - a))
        lat, lon = rng.choice(PLACES)
        out.append(Birth(y, m, d, rng.randint(0, 23), rng.randint(0, 59), tz=5.5, lat=lat, lon=lon))
    return out


def _simulate(P: dict[str, np.ndarray], offsets: list[int], rng: np.random.Generator, mode: str) -> list[dict]:
    M = len(offsets)
    t = int(rng.integers(M))
    post = np.full(M, 1.0 / M)
    flat = np.full(M, 1.0 / M)
    asked: set[str] = set()
    out = []
    for k in range(1, max(KS) + 1):
        best, bits = None, -1.0
        for key, mat in P.items():
            if key in asked:
                continue
            marg = post @ mat
            ig = _H(marg) - float(sum(pi * _H(row) for pi, row in zip(post, mat)))
            if ig > bits:
                best, bits = key, ig
        if best is None:
            break
        asked.add(best)
        mat = P[best]
        truth_row = mat[t]
        avg_row = flat @ mat
        if mode == "model":
            dist = truth_row
        elif mode == "half":
            dist = truth_row if rng.random() < 0.5 else avg_row
        else:
            dist = avg_row
        a = int(rng.choice(len(dist), p=dist / dist.sum()))
        post = post * mat[:, a]
        post /= post.sum()
        if k in KS:
            order = np.argsort(-post)
            acc, keep = 0.0, []
            for i in order:
                keep.append(int(i)); acc += post[i]
                if acc >= 0.9:
                    break
            out.append({"k": k, "width90": len(keep), "covers": t in keep,
                        "err": abs(offsets[int(order[0])] - offsets[t]), "asked": best})
    return out


def _H(p: np.ndarray) -> float:
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def one(args: tuple[int, Birth, int]) -> dict | None:
    try:
        return _one(args)
    except Exception:  # one bad chart must not lose the run; it is logged and counted
        logger.exception("chart %s failed", args[0])
        return None


def _one(args: tuple[int, Birth, int]) -> dict:
    idx, b, W = args
    offsets = list(range(-W, W + 1))
    q = build(b, offsets, today=TODAY)
    prior = uniform(q)
    P = {f.key: answer_probs(q, f.key) for f in q.facts()}
    bits = {k: info_gain(q, k, prior) for k in P}
    splits = {k: bool(np.ptp(P[k], axis=0).max() > 1e-9) for k in P}
    classes = resolution_classes(q)
    classes_nd = resolution_classes(q, dates=False)
    rng = np.random.default_rng(SEED + idx)
    Pt = {k: v for k, v in P.items() if FACT_BY_KEY[k].kind != "date" or k in TYPICAL_DATES}
    sims = {mode: [_simulate(P, offsets, rng, mode) for _ in range(SIMS_PER_CHART)] for mode in ("model", "half", "null")}
    sims.update({f"typical_{mode}": [_simulate(Pt, offsets, rng, mode) for _ in range(SIMS_PER_CHART)]
                 for mode in ("model", "null")})
    asc_sign = int(__import__("app.kp.chart", fromlist=["cast"]).cast(b).cusp(1).longitude // 30)
    return {"idx": idx, "birth": [b.year, b.month, b.day, b.hour, b.minute, b.lat, b.lon], "asc_sign": asc_sign,
            "bits": bits, "splits": splits, "classes": [z - a + 1 for a, z in classes],
            "classes_nodate": [z - a + 1 for a, z in classes_nd],
            "n_boundaries": len(boundaries(q)), "sims": sims}


def summarise(rows: list[dict], W: int) -> dict:
    keys = sorted({k for r in rows for k in r["bits"]})
    per = {}
    for k in keys:
        vals = [r["bits"].get(k, 0.0) for r in rows]
        top5 = sum(k in sorted(r["bits"], key=r["bits"].get, reverse=True)[:5] for r in rows)
        per[k] = {"median_bits": statistics.median(vals), "mean_bits": statistics.fmean(vals),
                  "p90_bits": float(np.percentile(vals, 90)),
                  "splits_share": sum(r["splits"].get(k, False) for r in rows) / len(rows),
                  "top5_share": top5 / len(rows),
                  "kind": FACT_BY_KEY[k].kind}
    widths = [w for r in rows for w in r["classes"]]
    ncls = [len(r["classes"]) for r in rows]
    widths_nd = [w for r in rows for w in r["classes_nodate"]]
    ncls_nd = [len(r["classes_nodate"]) for r in rows]
    tops = defaultdict(int)
    for r in rows:
        tops[tuple(sorted(sorted(r["bits"], key=r["bits"].get, reverse=True)[:5]))] += 1
    sim = {}
    for mode in ("model", "half", "null", "typical_model", "typical_null"):
        sim[mode] = {}
        for k in KS:
            pts = [s for r in rows for run in r["sims"][mode] for s in run if s["k"] == k]
            if pts:
                sim[mode][k] = {"median_width90": statistics.median(p["width90"] for p in pts),
                                "covers_truth": sum(p["covers"] for p in pts) / len(pts),
                                "median_err": statistics.median(p["err"] for p in pts),
                                "n": len(pts)}
    by_sign = defaultdict(list)
    for r in rows:
        by_sign[r["asc_sign"]].append(sum(sorted(r["bits"].values(), reverse=True)[:5]))
    return {"n_charts": len(rows), "window": W, "per_fact": per,
            "resolution": {"median_classes": statistics.median(ncls), "min_classes": min(ncls), "max_classes": max(ncls),
                           "median_class_width": statistics.median(widths), "share_width1": sum(w == 1 for w in widths) / len(widths),
                           "nodate_median_classes": statistics.median(ncls_nd),
                           "nodate_median_class_width": statistics.median(widths_nd),
                           "nodate_max_class_width": max(widths_nd)},
            "distinct_top5_sets": len(tops), "most_common_top5": [[list(k), v] for k, v in sorted(tops.items(), key=lambda kv: -kv[1])[:3]],
            "top5_bits_by_asc_sign": {s: statistics.median(v) for s, v in sorted(by_sign.items())},
            "median_boundaries": statistics.median(r["n_boundaries"] for r in rows),
            "sim": sim}


SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn",
         "Aquarius", "Pisces")


def to_markdown(S: dict) -> str:
    W = S["window"]
    M = 2 * W + 1
    L = [f"# Rectification questions: what splits the window (research run)", "",
         f"{S['n_charts']} synthetic births (15 Indian places, 1950-1995, any time of day), window +/- {W} min "
         f"({M} candidate minutes, {math.log2(M):.2f} bits of uncertainty), engines KP + Raman, today {TODAY}.",
         "Bits are expected information gain under a uniform prior, with the reliabilities in "
         "`app.kp.rect_questions` (0.8 facts and dates, 0.65 self-descriptions). Date questions assume month precision.", "",
         "## 1. Value of each question", "",
         "| fact | kind | median bits | mean | 90th pct | splits the window in | in the chart's top 5 in |",
         "|---|---|---|---|---|---|---|"]
    for k, v in sorted(S["per_fact"].items(), key=lambda kv: -kv[1]["mean_bits"]):
        L.append(f"| {k} | {v['kind']} | {v['median_bits']:.3f} | {v['mean_bits']:.3f} | {v['p90_bits']:.3f} | "
                 f"{v['splits_share']:.0%} | {v['top5_share']:.0%} |")
    R = S["resolution"]
    L += ["", "## 2. How chart-specific the best questions are", "",
          f"Distinct top-5 question sets across {S['n_charts']} charts: {S['distinct_top5_sets']}.",
          "Most common top-5 sets: " + "; ".join(f"{', '.join(k)} ({v})" for k, v in S["most_common_top5"]) + ".",
          f"Median number of changes inside the window (lagna sign, navamsa, any cusp sub-lord): {S['median_boundaries']}.", "",
          "Sum of the top 5 questions' bits by rising sign (short- and long-ascension signs rise at different speeds):", "",
          "| lagna | median top-5 bits |", "|---|---|"]
    for s, v in S["top5_bits_by_asc_sign"].items():
        L.append(f"| {SIGNS[int(s)]} | {v:.2f} |")
    L += ["", "## 3. Resolution floor", "",
          f"Runs of adjacent minutes that no question in the bank can tell apart: median {R['median_classes']} distinct "
          f"classes per {M}-minute window (range {R['min_classes']}-{R['max_classes']}); median class width "
          f"{R['median_class_width']} min; {R['share_width1']:.0%} of classes are a single minute "
          "(date windows compared at month precision).",
          f"Without date questions (yes/no and choice facts only): median {R['nodate_median_classes']} classes, median "
          f"width {R['nodate_median_class_width']} min, widest {R['nodate_max_class_width']} min.", "",
          "## 4. Simulated sessions (greedy, highest-information question first)", "",
          "| answers come from | questions asked | median 90 % set (min) | 90 % set holds the truth | median peak error (min) |",
          "|---|---|---|---|---|"]
    names = {"model": "the rules at the true minute", "half": "half the rules, half chance",
             "null": "chance only (rules carry no truth)",
             "typical_model": "typical person's questions; the rules", "typical_null": "typical person's questions; chance only"}
    for mode in ("model", "half", "null", "typical_model", "typical_null"):
        for k, v in S["sim"][mode].items():
            L.append(f"| {names[mode]} | {k} | {v['median_width90']} | {v['covers_truth']:.0%} | {v['median_err']} |")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--window", type=int, default=30)
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--out", required=True, help="path stem; writes .json and .md")
    a = ap.parse_args(argv)
    bs = births(a.n, SEED)
    with Pool(a.procs) as pool:
        rows = pool.map(one, [(i, b, a.window) for i, b in enumerate(bs)], chunksize=1)
    failed = sum(r is None for r in rows)
    rows = [r for r in rows if r is not None]
    S = summarise(rows, a.window)
    S["failed_charts"] = failed
    with open(a.out + ".json", "w") as fh:
        json.dump({"summary": S, "rows": [{k: v for k, v in r.items() if k != "sims"} for r in rows]}, fh, indent=1, default=str)
    with open(a.out + ".md", "w") as fh:
        fh.write(to_markdown(S))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
