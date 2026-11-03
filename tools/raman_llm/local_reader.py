"""Free version of the Claude reader test: the same 262 few-shot requests, sent to a local Ollama model.

Prereg: docs/raman_llm/RAMAN_READER_LLM_PREREG_2026-11-03_claude.md, addendum "Local model instead"
(written before any local call). Requests are read unchanged from
data/raman_llm/runs/claude_v1/requests.jsonl (same system prompt, same 16 examples, same JSON
shape); only the model differs. Resumable: rows already answered are skipped.

Usage:
  python -m tools.raman_llm.local_reader run   [--model gemma4:12b] [--host http://localhost:11434]
  python -m tools.raman_llm.local_reader compare [--model gemma4:12b]
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.request
from pathlib import Path

REQ = Path("data/raman_llm/runs/claude_v1/requests.jsonl")


def out_dir(model: str) -> Path:
    return Path("data/raman_llm/runs") / ("local_" + model.replace(":", "_").replace("/", "_"))


def call(host, model, system, user, schema, num_ctx):
    body = {"model": model, "stream": False, "think": False, "format": schema,
            "options": {"temperature": 0, "seed": 20261103, "num_ctx": num_ctx},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    req = urllib.request.Request(f"{host}/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as r:
        return json.loads(r.read())


def run(a):
    out = out_dir(a.model)
    out.mkdir(parents=True, exist_ok=True)
    raw_p = out / "raw_answers.jsonl"
    done = {json.loads(l)["key"] for l in open(raw_p, encoding="utf-8")} if raw_p.exists() else set()
    reqs = [json.loads(l) for l in open(REQ, encoding="utf-8")]
    json.dump({"model": a.model, "num_ctx": a.num_ctx, "temperature": 0, "requests": str(REQ),
               "started": time.strftime("%Y-%m-%dT%H:%M:%S")}, open(out / "run_meta.json", "w"), indent=1)
    for i, q in enumerate(reqs):
        if q["key"] in done:
            continue
        p = q["params"]
        t0 = time.time()
        ans = {"verdict": None, "reasons": [], "conclusion": "", "status": "succeeded"}
        try:
            r = call(a.host, a.model, p["system"], p["messages"][0]["content"],
                     p["output_config"]["format"]["schema"], a.num_ctx)
            text = r.get("message", {}).get("content", "")
            ans["prompt_tokens"], ans["eval_tokens"] = r.get("prompt_eval_count"), r.get("eval_count")
            try:
                ans.update(json.loads(text))
            except json.JSONDecodeError:
                ans["status"], ans["parse_error"] = "unparsable", text[:300]
        except Exception as e:   # recorded and scored as wrong, never retried with a different prompt
            ans["status"], ans["error"] = "errored", repr(e)[:300]
        with open(raw_p, "a", encoding="utf-8") as f:
            f.write(json.dumps({"key": q["key"], "fold": q["fold"], "split": q["split"], **ans}, ensure_ascii=False) + "\n")
        print(time.strftime("%H:%M:%S"), f"{i + 1}/{len(reqs)}", ans.get("verdict"), f"{time.time() - t0:.0f}s",
              ans.get("prompt_tokens"), flush=True)
    write_folds(out)


def write_folds(out):
    gold = {json.loads(l)["key"]: json.loads(l)["gold"] for l in open("data/raman_llm/dataset.jsonl", encoding="utf-8")}
    raw = [json.loads(l) for l in open(out / "raw_answers.jsonl", encoding="utf-8")]
    for k in sorted({r["fold"] for r in raw}):
        rs = [r for r in raw if r["fold"] == k]
        with open(out / f"fold{k}_verdicts.jsonl", "w", encoding="utf-8") as f:
            for r in rs:
                f.write(json.dumps({"key": r["key"], "split": r["split"], "fold": k, "gold": gold[r["key"]],
                                    "pred": r["verdict"] or "none"}) + "\n")
        with open(out / f"fold{k}_readings.jsonl", "w", encoding="utf-8") as f:
            for r in rs:
                txt = f"VERDICT: {r['verdict']}\nREASONS:\n" + "\n".join(r.get("reasons") or []) + f"\nCONCLUSION: {r.get('conclusion', '')}"
                f.write(json.dumps({"key": r["key"], "split": r["split"], "fold": k, "reading": txt}, ensure_ascii=False) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "compare"])
    ap.add_argument("--model", default="gemma4:12b")
    ap.add_argument("--host", default="http://localhost:11434")
    ap.add_argument("--num-ctx", type=int, default=16384)
    a = ap.parse_args()
    if a.cmd == "run":
        run(a)
    else:
        import tools.raman_llm.claude_reader as cr
        cr.OUT = out_dir(a.model)
        cr.compare()


if __name__ == "__main__":
    main()
