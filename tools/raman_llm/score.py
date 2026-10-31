"""Score a Raman reader LLM run against the pre-registered bar.

Prereg: docs/raman_llm/RAMAN_READER_LLM_PREREG_2026-10-31.md.

Usage: python -m tools.raman_llm.score data/raman_llm/runs/v1
Writes <run>/score.json and <run>/blind_packet.md + <run>/blind_key.json (the key is for
after the reader has marked the packet).
"""
from __future__ import annotations

import json
import math
import random
import re
import sys
from pathlib import Path

CLASSES = ("favourable", "mixed", "afflicted")
ORD = {"favourable": 0, "mixed": 1, "afflicted": 2}


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def b3(r):
    return "favourable" if r["nb"] >= r["nm"] else "afflicted"


def score(rows, pred):
    n = len(rows)
    d = [abs(ORD[pred[r["key"]]] - ORD[r["gold"]]) for r in rows]
    return {"n": n, "exact": sum(x == 0 for x in d), "within1": sum(x <= 1 for x in d),
            "real_errors": sum(x == 2 for x in d),
            "says": {c: sum(pred[r["key"]] == c for r in rows) for c in CLASSES}}


def mcnemar(rows, a, b):
    """Exact two-sided McNemar on exact-match: rows a got right and b wrong, and the reverse."""
    x = sum(a[r["key"]] == r["gold"] and b[r["key"]] != r["gold"] for r in rows)
    y = sum(a[r["key"]] != r["gold"] and b[r["key"]] == r["gold"] for r in rows)
    n = x + y
    if n == 0:
        return {"a_only": 0, "b_only": 0, "p": 1.0}
    k = min(x, y)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)
    return {"a_only": x, "b_only": y, "p": round(p, 4)}


def _lcs(a, b):
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            cur.append(prev[j] + 1 if x == y else max(prev[j + 1], cur[-1]))
        prev = cur
    return prev[-1]


def rouge_l(hyp, ref):
    h, r = re.findall(r"[a-z']+", hyp.lower()), re.findall(r"[a-z']+", ref.lower())
    if not h or not r:
        return 0.0
    l = _lcs(h, r)
    if l == 0:
        return 0.0
    p, rc = l / len(h), l / len(r)
    return 2 * p * rc / (p + rc)


def conclusion_of(text):
    m = re.search(r"CONCLUSION:\s*(.*)", text, re.S)
    return (m.group(1) if m else text).strip().split("\n")[0]


def template_reading(row):
    """No-model baseline: the first two rule readings on the side the count leans to."""
    side = "+ " if row["nb"] >= row["nm"] else "- "
    lines = [l[2:] for l in row["prompt"].split("\n") if l.startswith(side)]
    return " ".join(re.sub(r"^\[[^\]]+\]\s*", "", l) for l in lines[:2])


def verdict_of(text):
    m = re.search(r"VERDICT:\s*(favourable|mixed|afflicted)", text)
    return m.group(1) if m else None


def verdict_bar(rows, llm, b3p):
    s_llm, s_b3 = score(rows, llm), score(rows, b3p)
    t = mcnemar(rows, llm, b3p)
    if s_llm["exact"] > s_b3["exact"] and t["p"] < 0.05:
        outcome = "SIGNAL (beats the count)"
    elif s_llm["exact"] < s_b3["exact"] and t["p"] < 0.05:
        outcome = "WORSE than the count"
    else:
        outcome = "NULL (no detectable difference from the count)"
    return outcome, t


def main(run):
    run = Path(run)
    data = {r["key"]: r for r in jl("data/raman_llm/dataset.jsonl")}
    llm = {}
    for f in sorted(run.glob("fold*_verdicts.jsonl")):
        for v in jl(f):
            llm[v["key"]] = v["pred"]
    base = {v["key"]: v["pred"] for v in jl(run / "base_verdicts.jsonl")} if (run / "base_verdicts.jsonl").exists() else {}
    readings = {}
    for f in sorted(run.glob("fold*_readings.jsonl")):
        for v in jl(f):
            readings[v["key"]] = v["reading"]
    rows = [data[k] for k in llm]
    b3p = {r["key"]: b3(r) for r in rows}
    fav = {r["key"]: "favourable" for r in rows}
    eng = {r["key"]: r["engine_verdict"] or "mixed" for r in rows}
    subsets = {"PRIMARY hold-outs H1-H5": lambda r: r["split"] != "pool",
               "H4+H5 (the 40/64 comparison)": lambda r: r["split"] in ("H4", "H5"),
               "H1-H3": lambda r: r["split"] in ("H1", "H2", "H3"),
               "pool (engine tuned here; LLM still out-of-fold)": lambda r: r["split"] == "pool",
               "all 651": lambda r: True}
    res = {"run": str(run), "rows_scored": len(rows), "complete": len(rows) == len(data), "subsets": {}}
    for name, keep in subsets.items():
        rs = [r for r in rows if keep(r)]
        if not rs:
            continue
        outcome, t = verdict_bar(rs, llm, b3p)
        res["subsets"][name] = {
            "LLM (fine-tuned, out-of-fold)": score(rs, llm),
            "count B3": score(rs, b3p), "always favourable": score(rs, fav),
            "engine clause judge": score(rs, eng),
            **({"LLM untrained base": score(rs, {k: base[k] for k in base})} if base else {}),
            "LLM vs count McNemar": t, "outcome": outcome}
    # prose: generated conclusions on hold-out rows vs Raman's own words
    hk = [k for k in readings if data[k]["raman_words"]]
    if hk:
        rl_m = [rouge_l(conclusion_of(readings[k]), data[k]["raman_words"]) for k in hk]
        rl_t = [rouge_l(template_reading(data[k]), data[k]["raman_words"]) for k in hk]
        gen_v = [verdict_of(readings[k]) for k in hk]
        res["prose"] = {"n": len(hk),
                        "rougeL_llm_mean": round(sum(rl_m) / len(hk), 4),
                        "rougeL_template_mean": round(sum(rl_t) / len(hk), 4),
                        "llm_better_rows": sum(a > b for a, b in zip(rl_m, rl_t)),
                        "template_better_rows": sum(a < b for a, b in zip(rl_m, rl_t)),
                        "generated_verdict_parsable": sum(v is not None for v in gen_v),
                        "generated_verdict_agrees_with_scored": sum(v == llm.get(k) for v, k in zip(gen_v, hk)),
                        "human_blind_judged": False}
        # blind packet: Raman's own words vs the model's, order shuffled, key kept apart
        rng = random.Random(7)
        pick = rng.sample(hk, min(30, len(hk)))
        key, lines = {}, ["# Blind packet: which conclusion is Raman's?", "",
                          "For each matter, one conclusion is Raman's own and one was written by the model. "
                          "Mark A or B as Raman's, and say whether the other one would pass as his. "
                          "Do not open blind_key.json until done.", ""]
        for i, k in enumerate(pick, 1):
            a_is_raman = rng.random() < 0.5
            ram, mod = data[k]["raman_words"], conclusion_of(readings[k])
            a, b = (ram, mod) if a_is_raman else (mod, ram)
            key[f"item_{i:02d}"] = {"key": k, "raman_is": "A" if a_is_raman else "B"}
            matter = data[k]["prompt"].split("\n")[0].replace("MATTER: ", "")
            lines += [f"## {i}. {matter}", f"A: {a}", "", f"B: {b}", "", "Raman's is: __   Other passes as Raman? __", ""]
        (run / "blind_packet.md").write_text("\n".join(lines), encoding="utf-8")
        json.dump(key, open(run / "blind_key.json", "w"), indent=1)
    json.dump(res, open(run / "score.json", "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
