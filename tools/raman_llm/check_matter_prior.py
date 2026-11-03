"""Interim read-only check: how far does a chart-blind 'typical verdict for this matter' go, out of fold?"""
import collections as C, glob, json, re, sys
sys.path.insert(0, ".")
from tools.raman_llm.score import b3, mcnemar
rows = [json.loads(l) for l in open("data/raman_llm/dataset.jsonl", encoding="utf-8")]
PL = "Lagna Sun Moon Mars Mercury Jupiter Venus Saturn Rahu Ketu".split()
def sg(r):
    block = r["prompt"].split("CHART:")[1].split("RULES")[0]
    return tuple((re.search(rf"^{p}: (\w+)", block, re.M) or [0, "?"])[1] for p in PL)
gf = C.defaultdict(set)
for r in rows: gf[sg(r)].add(r["fold"])
clean = lambda r: len(gf[sg(r)]) == 1
matter = lambda r: r["prompt"].split("\n")[0]
scored = {v["key"]: v["pred"] for p in glob.glob("data/raman_llm/runs/v1/fold*_verdicts.jsonl") for v in map(json.loads, open(p))}
H = [r for r in rows if r["split"] != "pool" and r["key"] in scored]
def prior(r):
    c = C.Counter(x["gold"] for x in rows if x["fold"] != r["fold"] and matter(x) == matter(r))
    return c.most_common(1)[0][0] if c else "favourable"
def prior_count(r):
    side = b3(r)
    c = C.Counter(x["gold"] for x in rows if x["fold"] != r["fold"] and matter(x) == matter(r) and b3(x) == side)
    return c.most_common(1)[0][0] if c else side
base = {v["key"]: v["pred"] for v in map(json.loads, open("data/raman_llm/runs/v1/base_verdicts.jsonl"))}
P = {r["key"]: prior(r) for r in H}; PC = {r["key"]: prior_count(r) for r in H}; B = {r["key"]: b3(r) for r in H}
for name, S in (("all hold-out so far", H), ("clean nativities", [r for r in H if clean(r)])):
    hit = lambda d: sum(d[r["key"]] == r["gold"] for r in S)
    print(f"{name}: n={len(S)} LLM {hit(scored)} count {hit(B)} matter-prior {hit(P)} matter+count {hit(PC)} base {hit(base)}")
    print("   LLM vs matter-prior", mcnemar(S, scored, P), "| LLM vs matter+count", mcnemar(S, scored, PC), "| LLM agrees with matter-prior on", sum(scored[r['key']] == P[r['key']] for r in S))
print("distinct matters", len({matter(r) for r in rows}))
print("sample prompt rule lines:", [l[:90] for l in rows[300]["prompt"].split("\n") if l.startswith(("+", "-"))][:4])
