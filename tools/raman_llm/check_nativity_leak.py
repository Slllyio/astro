"""Interim read-only check: do nativities cross folds under different chart ids?"""
import collections as C, glob, json, re, sys
sys.path.insert(0, ".")
from tools.raman_llm.score import b3, mcnemar
rows = [json.loads(l) for l in open("data/raman_llm/dataset.jsonl", encoding="utf-8")]
PL = "Lagna Sun Moon Mars Mercury Jupiter Venus Saturn Rahu Ketu".split()
def sg(r):
    block = r["prompt"].split("CHART:")[1].split("RULES")[0]
    return tuple((re.search(rf"^{p}: (\w+)", block, re.M) or [0, "?"])[1] for p in PL)
chart = {r["chart"]: sg(r) for r in rows}
fold = {r["chart"]: r["fold"] for r in rows}
ids = list(chart)
parent = {c: c for c in ids}
def find(c):
    while parent[c] != c:
        parent[c] = parent[parent[c]]; c = parent[c]
    return c
for maxdiff in (0, 2):
    parent = {c: c for c in ids}
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if sum(x != y for x, y in zip(chart[a], chart[b])) <= maxdiff:
                parent[find(a)] = find(b)
    grp = C.defaultdict(set)
    for c in ids: grp[find(c)].add(c)
    multi = [g for g in grp.values() if len(g) > 1]
    cross = {c for g in multi if len({fold[x] for x in g}) > 1 for c in g}
    print(f"maxdiff {maxdiff}: nativities {len(grp)} of {len(ids)} ids; multi-id groups {len(multi)}; chart ids crossing folds {len(cross)}; rows touched {sum(r['chart'] in cross for r in rows)}/{len(rows)}")
    pr = {v["key"]: v["pred"] for p in glob.glob("data/raman_llm/runs/v1/fold*_verdicts.jsonl") for v in map(json.loads, open(p))}
    H = [r for r in rows if r["split"] != "pool" and r["key"] in pr]
    for name, S in (("seen-in-training", [r for r in H if r["chart"] in cross]), ("clean", [r for r in H if r["chart"] not in cross])):
        print(f"  {name}: n={len(S)} LLM {sum(pr[r['key']]==r['gold'] for r in S)} B3 {sum(b3(r)==r['gold'] for r in S)} alwaysfav {sum(r['gold']=='favourable' for r in S)} mcnemar {mcnemar(S, pr, {r['key']: b3(r) for r in S})}")
    print("  clean by split:", {s: (sum(1 for r in H if r['split']==s and r['chart'] not in cross), sum(pr[r['key']]==r['gold'] for r in H if r['split']==s and r['chart'] not in cross), sum(b3(r)==r['gold'] for r in H if r['split']==s and r['chart'] not in cross)) for s in ('H1','H2','H3','H4','H5')})
tr = C.defaultdict(list)
for r in rows: tr[(sg(r), r["prompt"].split("\n")[0])].append(r)
dup = [v for v in tr.values() if len({x["fold"] for x in v}) > 1]
print("same nativity+matter across folds:", len(dup), "groups; same gold within group:", sum(len({x["gold"] for x in v}) == 1 for v in dup))
print("H1 gold:", C.Counter(r["gold"] for r in rows if r["split"] == "H1"), "H1 charts by book:", C.Counter(r["chart"].split(".")[0] for r in rows if r["split"] == "H1"))
