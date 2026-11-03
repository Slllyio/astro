"""Claude as the Raman reader: few-shot, no training. Same rows, folds and baselines as the 14B run.

Prereg: docs/raman_llm/RAMAN_READER_LLM_PREREG_2026-10-31.md, addendum 2026-11-03 (written before
any Claude call).

For each of the 262 hold-out rows, Claude gets the same engine-output prompt the 14B saw, plus 16
worked examples (input -> Raman's verdict, reasons, conclusion) drawn ONLY from other folds and
NEVER from the same nativity (lagna + nine planet signs), 6 on the same matter and 10 others,
seeded. It answers in a fixed JSON shape. Runs through the Message Batches API (half price).

Usage:
  python -m tools.raman_llm.claude_reader build              # writes requests, no API call
  python -m tools.raman_llm.claude_reader submit             # needs ANTHROPIC_API_KEY (or ant auth)
  python -m tools.raman_llm.claude_reader collect            # waits, then writes fold*_verdicts/readings
  python -m tools.raman_llm.claude_reader compare            # Claude vs matter prior, count, 14B
"""
from __future__ import annotations

import collections
import json
import random
import re
import sys
import time
from pathlib import Path

DATA = Path("data/raman_llm/dataset.jsonl")
OUT = Path("data/raman_llm/runs/claude_v1")
MODEL = "claude-opus-5-5"
EFFORT = "high"
N_SAME, N_OTHER, SEED = 6, 10, 20261103
PL = "Lagna Sun Moon Mars Mercury Jupiter Venus Saturn Rahu Ketu".split()

SYSTEM = (
    "You read horoscopes as B.V. Raman did in his worked charts. For one matter of a chart you get "
    "what a rule engine built from his books reports: the chart, the rules for and against with "
    "their book lines, and counts. Weigh them as Raman weighs them and give his verdict "
    "(favourable, mixed or afflicted), the reasons he would give (each marked + or -), and a short "
    "conclusion in his manner.\n\n"
    "Rules:\n"
    "- Work only from the input. Do not name, guess or identify the native, and do not use anything "
    "you may remember about published charts.\n"
    "- The conclusion says what the chart indicates for this matter. Do not invent biography the "
    "input cannot support: no professions, titles, names, dates or events stated as facts.\n"
    "- The worked examples show how Raman's verdicts fall; they are other natives, not this one.")

SCHEMA = {"type": "object",
          "properties": {"verdict": {"type": "string", "enum": ["favourable", "mixed", "afflicted"]},
                         "reasons": {"type": "array", "items": {"type": "string"}},
                         "conclusion": {"type": "string"}},
          "required": ["verdict", "reasons", "conclusion"], "additionalProperties": False}


def rows():
    return [json.loads(l) for l in open(DATA, encoding="utf-8")]


def nativity(r):
    block = r["prompt"].split("CHART:")[1].split("RULES")[0]
    return tuple((re.search(rf"^{p}: (\w+)", block, re.M) or [0, "?"])[1] for p in PL)


def matter(r):
    return r["prompt"].split("\n")[0]


def examples_for(r, allr):
    nat = nativity(r)
    ok = [x for x in allr if x["fold"] != r["fold"] and nativity(x) != nat]
    rng = random.Random(f"{SEED}:{r['key']}")
    same = [x for x in ok if matter(x) == matter(r)]
    pick = rng.sample(same, min(N_SAME, len(same)))
    rest = [x for x in ok if x not in pick]
    pick += rng.sample(rest, N_OTHER + N_SAME - len(pick))
    rng.shuffle(pick)
    return pick


def user_message(r, ex):
    parts = ["Worked examples (other natives, Raman's own verdicts and words):"]
    for i, x in enumerate(ex, 1):
        parts.append(f"<example {i}>\nINPUT:\n{x['prompt']}\n\nRAMAN:\n{x['target']}\n</example {i}>")
    parts.append("Now this matter. Answer in the JSON shape.\n\nINPUT:\n" + r["prompt"])
    return "\n\n".join(parts)


def build():
    allr = rows()
    test = [r for r in allr if r["split"] != "pool"]
    OUT.mkdir(parents=True, exist_ok=True)
    reqs = []
    for i, r in enumerate(test):
        ex = examples_for(r, allr)
        assert all(x["fold"] != r["fold"] and nativity(x) != nativity(r) for x in ex)
        reqs.append({"custom_id": f"r{i:03d}", "key": r["key"], "fold": r["fold"], "split": r["split"],
                     "examples": [x["key"] for x in ex],
                     "params": {"model": MODEL, "max_tokens": 16000, "system": SYSTEM,
                                "thinking": {"type": "adaptive"},
                                "output_config": {"effort": EFFORT, "format": {"type": "json_schema", "schema": SCHEMA}},
                                "messages": [{"role": "user", "content": user_message(r, ex)}]}})
    with open(OUT / "requests.jsonl", "w", encoding="utf-8") as f:
        for q in reqs:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    chars = sum(len(q["params"]["messages"][0]["content"]) + len(SYSTEM) for q in reqs)
    print(len(reqs), "requests; input chars", chars, "~tokens", chars // 4,
          "; est. cost at batch price (~$2/MTok in, ~$10/MTok out, ~1.5k out each): $%.1f"
          % (chars / 4 / 1e6 * 2 + len(reqs) * 1500 / 1e6 * 10))


def submit():
    import anthropic
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request
    reqs = [json.loads(l) for l in open(OUT / "requests.jsonl", encoding="utf-8")]
    client = anthropic.Anthropic()
    b = client.messages.batches.create(requests=[
        Request(custom_id=q["custom_id"], params=MessageCreateParamsNonStreaming(**q["params"])) for q in reqs])
    json.dump({"batch_id": b.id, "submitted": time.strftime("%Y-%m-%dT%H:%M:%S")}, open(OUT / "batch.json", "w"))
    print("batch", b.id, b.processing_status)


def collect():
    import anthropic
    client = anthropic.Anthropic()
    bid = json.load(open(OUT / "batch.json"))["batch_id"]
    while (b := client.messages.batches.retrieve(bid)).processing_status != "ended":
        print(time.strftime("%H:%M:%S"), b.processing_status, b.request_counts, flush=True)
        time.sleep(60)
    meta = {q["custom_id"]: q for q in map(json.loads, open(OUT / "requests.jsonl", encoding="utf-8"))}
    gold = {r["key"]: r["gold"] for r in rows()}
    verd, read, raw, usage = collections.defaultdict(list), collections.defaultdict(list), [], collections.Counter()
    for res in client.messages.batches.results(bid):
        q = meta[res.custom_id]
        out = {"verdict": None, "reasons": [], "conclusion": "", "status": res.result.type}
        if res.result.type == "succeeded":
            msg = res.result.message
            out["stop_reason"] = msg.stop_reason
            for k in ("input_tokens", "output_tokens"):
                usage[k] += getattr(msg.usage, k) or 0
            text = next((c.text for c in msg.content if c.type == "text"), "")
            try:
                out.update(json.loads(text))
            except json.JSONDecodeError:
                out["parse_error"] = text[:300]
        raw.append({"key": q["key"], **out})
        # a refusal, error or unparsable answer is scored as wrong ("none" never matches gold)
        pred = out["verdict"] or "none"
        verd[q["fold"]].append({"key": q["key"], "split": q["split"], "fold": q["fold"], "gold": gold[q["key"]], "pred": pred})
        reading = f"VERDICT: {out['verdict']}\nREASONS:\n" + "\n".join(out["reasons"]) + f"\nCONCLUSION: {out['conclusion']}"
        read[q["fold"]].append({"key": q["key"], "split": q["split"], "fold": q["fold"], "reading": reading})
    for k in verd:
        with open(OUT / f"fold{k}_verdicts.jsonl", "w", encoding="utf-8") as f:
            f.writelines(json.dumps(v, ensure_ascii=False) + "\n" for v in verd[k])
        with open(OUT / f"fold{k}_readings.jsonl", "w", encoding="utf-8") as f:
            f.writelines(json.dumps(v, ensure_ascii=False) + "\n" for v in read[k])
    with open(OUT / "raw_answers.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(v, ensure_ascii=False) + "\n" for v in raw)
    json.dump({"model": MODEL, "effort": EFFORT, "usage": usage, "n": len(raw),
               "statuses": collections.Counter(r["status"] for r in raw)}, open(OUT / "run_meta.json", "w"), indent=1)
    print("collected", len(raw), dict(usage))


def compare():
    sys.path.insert(0, ".")
    from tools.raman_llm.score import b3, mcnemar
    allr = rows()
    byk = {r["key"]: r for r in allr}
    jl = lambda p: [json.loads(l) for l in open(p, encoding="utf-8")]
    cl = {v["key"]: v["pred"] for p in sorted(OUT.glob("fold*_verdicts.jsonl")) for v in jl(p)}
    q14 = {v["key"]: v["pred"] for p in sorted(Path("data/raman_llm/runs/v1").glob("fold*_verdicts.jsonl")) for v in jl(p)}
    H = [byk[k] for k in cl]

    def prior(r):
        c = collections.Counter(x["gold"] for x in allr if x["fold"] != r["fold"] and matter(x) == matter(r))
        return c.most_common(1)[0][0] if c else "favourable"
    gf = collections.defaultdict(set)
    for r in allr:
        gf[nativity(r)].add(r["fold"])
    P = {r["key"]: prior(r) for r in H}
    B = {r["key"]: b3(r) for r in H}
    res = {}
    for name, S in (("PRIMARY all hold-outs", H), ("H4+H5", [r for r in H if r["split"] in ("H4", "H5")]),
                    ("clean nativities", [r for r in H if len(gf[nativity(r)]) == 1])):
        hit = lambda d: sum(d.get(r["key"]) == r["gold"] for r in S)
        res[name] = {"n": len(S), "claude": hit(cl), "matter_prior": hit(P), "count": hit(B), "qwen14b": hit(q14),
                     "always_fav": sum(r["gold"] == "favourable" for r in S),
                     "claude_vs_matter_prior": mcnemar(S, cl, P), "claude_vs_count": mcnemar(S, cl, B),
                     "claude_vs_qwen14b": mcnemar(S, cl, q14),
                     "claude_agrees_matter_prior": sum(cl[r["key"]] == P[r["key"]] for r in S),
                     "real_errors": sum({cl[r["key"]], r["gold"]} == {"favourable", "afflicted"} for r in S)}
    t = res["PRIMARY all hold-outs"]
    m = t["claude_vs_matter_prior"]
    t["outcome"] = ("SIGNAL (beats the chart-blind matter rule)" if t["claude"] > t["matter_prior"] and m["p"] < 0.05
                    else "WORSE than the chart-blind matter rule" if t["claude"] < t["matter_prior"] and m["p"] < 0.05
                    else "NULL (no detectable difference from the chart-blind matter rule)")
    raw = jl(OUT / "raw_answers.jsonl")
    concl = [a["conclusion"] for a in raw if a["conclusion"]]
    res["prose"] = {"n": len(concl), "distinct": len(set(concl)),
                    "median_words": sorted(len(c.split()) for c in concl)[len(concl) // 2] if concl else 0,
                    "human_blind_judged": False}
    json.dump(res, open(OUT / "compare.json", "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    {"build": build, "submit": submit, "collect": collect, "compare": compare}[sys.argv[1]]()
