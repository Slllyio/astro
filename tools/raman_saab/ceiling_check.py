"""Ceiling check, Part A and C (docs/raman_saab/CEILING_CHECK_PREREG_2026-10-30.md).

Scores the shipped engine against four trivial baselines on the pool and the spent hold-outs
1-3, and lists natives Raman judges in more than one set. Never reads hold-out 4 or 5.

Usage: python -m tools.raman_saab.ceiling_check [--out result.json]
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter, defaultdict

SETS = {
    "H1": "tests/fixtures/raman_holdout_sealed.jsonl",
    "H2": "tests/fixtures/raman_holdout2_sealed.jsonl",
    "H3": "tests/fixtures/raman_holdout3_sealed.jsonl",
}
CLASSES = ("favourable", "mixed", "afflicted")
SEED = 20261030


def _load(path: str) -> list[dict]:
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip() and not l.startswith("#")]


def _rows(recs, confirmed_only, tg, ht):
    out = []
    for r in recs:
        ch = tg.build_chart(r)
        pfs = {}
        for h, e in r["expected_verdicts"].items():
            if confirmed_only and not tg._is_confirmed(e):
                continue
            hn = int(h[1:])
            pf = pfs.setdefault(hn, ht.judge_house(ch, hn))
            sv = next((s for s in pf.significations if s.signification == e["signification"]), None)
            nb = len(sv.ledger.fired_benefic) if sv else 0
            nm = len(sv.ledger.fired_malefic) if sv else 0
            out.append({"key": f"{r['id']} {h}/{e['signification']}", "chart": r["id"],
                        "name": r.get("name"), "birth": (r.get("birth") or {}).get("dt"),
                        "house": hn, "sig": e["signification"], "gold": e["verdict"],
                        "E": sv.verdict if sv else None, "nb": nb, "nm": nm})
    return out


def _b2(nb, nm, tie):
    if nb > nm:
        return "favourable"
    if nm > nb:
        return "afflicted"
    return tie if nb else "favourable"


def _metrics(rows, pred, dist):
    n = len(rows)
    ex = sum(r[pred] == r["gold"] for r in rows)
    w1 = sum(dist(r[pred], r["gold"]) <= 1 for r in rows)
    re_ = sum(dist(r[pred], r["gold"]) >= 2 for r in rows)
    rec = []
    for c in CLASSES:
        g = [r for r in rows if r["gold"] == c]
        if g:
            rec.append(sum(r[pred] == c for r in g) / len(g))
    return {"n": n, "exact": ex, "within1": w1, "real": re_, "macro_recall": round(sum(rec) / len(rec), 3)}


def _boot(rows, fn, n=10000):
    by = defaultdict(list)
    for r in rows:
        by[r["chart"]].append(r)
    charts = sorted(by)
    rnd = random.Random(SEED)
    vals = []
    for _ in range(n):
        samp = [x for c in (rnd.choice(charts) for _ in charts) for x in by[c]]
        vals.append(fn(samp))
    vals.sort()
    return vals[int(0.025 * n)], vals[int(0.975 * n) - 1]


def main(out: str | None) -> None:
    sys.path.insert(0, ".")
    from tests.raman_saab import test_goldens as tg
    import app.raman_saab.judges.house_template as ht
    dist = tg._ordinal_distance
    data = {"pool": _rows(tg._TRACK_B_RATCHET, True, tg, ht)}
    for k, p in SETS.items():
        data[k] = _rows(_load(p), False, tg, ht)
    majority = Counter(r["gold"] for r in data["pool"]).most_common(1)[0][0]
    for rows in data.values():
        for r in rows:
            r["B0"] = "favourable"
            r["B1"] = majority
            r["B2"] = _b2(r["nb"], r["nm"], "mixed")
            r["B3"] = _b2(r["nb"], r["nm"], "favourable")
    data["H1-3"] = data["H1"] + data["H2"] + data["H3"]
    res = {"pool_majority": majority, "class_split": {}, "metrics": {}}
    for s, rows in data.items():
        res["class_split"][s] = dict(Counter(r["gold"] for r in rows))
        res["metrics"][s] = {p: _metrics(rows, p, dist) for p in ("E", "B0", "B1", "B2", "B3")}
    oos = data["H1-3"]
    best = max(("B0", "B1", "B2", "B3"), key=lambda p: res["metrics"]["H1-3"][p]["exact"])
    ex = lambda rs, p: sum(r[p] == r["gold"] for r in rs)
    real = lambda rs, p: sum(dist(r[p], r["gold"]) >= 2 for r in rs)
    d = ex(oos, "E") - ex(oos, best)
    lo, hi = _boot(oos, lambda rs: ex(rs, "E") - ex(rs, best))
    rlo, rhi = _boot(oos, lambda rs: real(rs, "E") - real(rs, best))
    verdict = ("engine adds value over baselines out of sample" if lo > 0 else
               "engine below baseline out of sample" if hi < 0 else "no detectable difference")
    res["decision"] = {"best_baseline": best, "D_exact": d, "ci95": [lo, hi],
                       "D_real": real(oos, "E") - real(oos, best), "ci95_real": [rlo, rhi],
                       "verdict": verdict}
    # Part C: natives judged in more than one set
    seen = defaultdict(list)
    for s in ("pool", "H1", "H2", "H3"):
        for r in data[s]:
            nm = (r["name"] or "").split("(")[0].strip().lower()
            for k in filter(None, (("n", nm) if nm and not nm.startswith("chart") else None,
                                   ("b", (r["birth"] or "")[:10]) if r["birth"] else None)):
                seen[k].append((s, r))
    pairs = {}
    for k, lst in seen.items():
        if len({s for s, r in lst}) < 2 and len({r["chart"] for s, r in lst}) < 2:
            continue
        by = defaultdict(list)
        for s, r in lst:
            by[(r["house"], r["sig"])].append((s, r["chart"], r["gold"]))
        for hs, v in by.items():
            if len({c for _, c, _ in v}) > 1:
                pairs[(tuple(v[0][1:2]), hs)] = v
    res["self_consistency"] = [{"matter": f"H{hs[0]}/{hs[1]}", "judgements": v} for (_, hs), v in pairs.items()]
    res["rows"] = data
    for s in ("pool", "H1", "H2", "H3", "H1-3"):
        print(s, res["class_split"][s])
        for p, m in res["metrics"][s].items():
            print(f"   {p}: {m}")
    print("decision:", res["decision"])
    print("self-consistency pairs:", len(res["self_consistency"]))
    for x in res["self_consistency"]:
        print("  ", x["matter"], x["judgements"])
    if out:
        json.dump(res, open(out, "w"), indent=1, default=str)


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[args.index("--out") + 1] if "--out" in args else None)
