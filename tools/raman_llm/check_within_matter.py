"""Does the model read the chart, or only the matter? Exploratory, no model calls.

For two rows on the same matter where Raman said favourable on one and afflicted on the other, how
often does a score rank the favourable row higher? 0.5 means no information from the chart.
Gold is shuffled within matter for the p-value; rows from one chart are not independent, so read it
as a guide. Usage: python -m tools.raman_llm.check_within_matter data/raman_llm/runs/v1
"""
from __future__ import annotations

import collections as C
import glob
import json
import random
import re
import sys

PL = "Lagna Sun Moon Mars Mercury Jupiter Venus Saturn Rahu Ketu".split()


def within_auc(items):
    """items: (matter, gold_is_favourable, score). Pair-weighted AUC within matter."""
    by = C.defaultdict(lambda: ([], []))
    for m, g, s in items:
        by[m][0 if g else 1].append(s)
    win = pairs = 0
    for fav, aff in by.values():
        for a in fav:
            for b in aff:
                win += 1 if a > b else 0.5 if a == b else 0
                pairs += 1
    return win / pairs if pairs else float("nan"), pairs


def perm_p(items, n=2000, seed=20261103):
    obs, _ = within_auc(items)
    rng = random.Random(seed)
    groups = C.defaultdict(list)
    for it in items:
        groups[it[0]].append(it)
    extreme = 0
    for _ in range(n):
        shuffled = []
        for m, g in groups.items():
            golds = [x[1] for x in g]
            rng.shuffle(golds)
            shuffled += [(m, y, x[2]) for x, y in zip(g, golds)]
        extreme += abs(within_auc(shuffled)[0] - 0.5) >= abs(obs - 0.5)
    return (extreme + 1) / (n + 1)


def main(run):
    rows = {}
    for l in open("data/raman_llm/dataset.jsonl", encoding="utf-8"):
        r = json.loads(l)
        rows[r["key"]] = r

    def sg(r):
        block = r["prompt"].split("CHART:")[1].split("RULES")[0]
        return tuple((re.search(rf"^{p}: (\w+)", block, re.M) or [0, "?"])[1] for p in PL)

    folds = C.defaultdict(set)
    for r in rows.values():
        folds[sg(r)].add(r["fold"])
    llm = {v["key"]: v["logp"] for p in glob.glob(f"{run}/fold*_verdicts.jsonl") for v in map(json.loads, open(p))}
    base = {v["key"]: v["logp"] for v in map(json.loads, open(f"{run}/base_verdicts.jsonl"))}
    margin = lambda lp: lp["favourable"] - lp["afflicted"]
    scores = {"tuned model": lambda r: margin(llm[r["key"]]), "count (for minus against)": lambda r: r["nb"] - r["nm"],
              "untrained model": lambda r: margin(base[r["key"]])}
    subsets = {"hold-out": lambda r: r["split"] != "pool",
               "hold-out, nativity in one fold": lambda r: r["split"] != "pool" and len(folds[sg(r)]) == 1,
               "pool": lambda r: r["split"] == "pool",
               "pool, nativity in one fold": lambda r: r["split"] == "pool" and len(folds[sg(r)]) == 1}
    matter = lambda r: r["prompt"].split("\n")[0]
    for sname, keep in subsets.items():
        S = [r for r in rows.values() if keep(r) and r["gold"] != "mixed" and r["key"] in llm]
        print(f"{sname}: {len(S)} rows")
        for name, f in scores.items():
            items = [(matter(r), r["gold"] == "favourable", f(r)) for r in S]
            a, n = within_auc(items)
            print(f"   {name}: within-matter AUC {a:.3f} on {n} pairs, permutation p {perm_p(items):.4f}")


if __name__ == "__main__":
    assert within_auc([("m", True, 2), ("m", False, 1)])[0] == 1.0
    assert within_auc([("m", True, 1), ("m", False, 2), ("n", True, 5)])[0] == 0.0
    main(sys.argv[1])
