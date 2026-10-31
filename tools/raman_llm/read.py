"""Read a chart with the trained Raman reader LLM (engine output in, Raman-style reading out).

Usage:
  python -m tools.raman_llm.read --adapter data/raman_llm/runs/v1/final_adapter \
      --dt 1989-10-12T10:02:00 --tz 5.5 --lat 27.23 --lon 79.02 [--houses 1,2,7,10]

For each house and each of its matters, the engine is run, its output is laid out exactly as in
training (tools/raman_llm/build_dataset.py), and the model writes VERDICT / REASONS / CONCLUSION.
The verdict also comes with the model's likelihood for each of the three verdicts.

What this is: a model of how Raman wrote about charts. On his own conclusions it was not shown,
its verdicts are measured against a plain count of for/against rules (see the run's score.json);
it is not a forecast of the native's life.
"""
from __future__ import annotations

import argparse
import json
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--dt", required=True)
    ap.add_argument("--tz", type=float, required=True)
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--houses", default="1,2,3,4,5,6,7,8,9,10,11,12")
    ap.add_argument("--max-new", type=int, default=260)
    args = ap.parse_args()
    sys.path.insert(0, ".")
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from tests.raman_saab import test_goldens as tg
    import app.raman_saab.judges.house_template as ht
    from tools.raman_saab.tally_judge import factors
    from tools.raman_llm.build_dataset import SYSTEM, prompt_for
    from tools.raman_llm.train_eval import CLASSES, encode_prompt, verdict_scores

    info = json.load(open(f"{args.adapter}/raman_reader.json"))
    base = info["base_model"]
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(args.adapter)
    kw = {"torch_dtype": torch.bfloat16 if dev == "cuda" else torch.float32}
    if info.get("four_bit") and dev == "cuda":
        from transformers import BitsAndBytesConfig
        kw["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                                       bnb_4bit_use_double_quant=True,
                                                       bnb_4bit_compute_dtype=torch.bfloat16)
        kw["device_map"] = {"": 0}
    m = AutoModelForCausalLM.from_pretrained(base, **kw)
    m = PeftModel.from_pretrained(m, args.adapter)
    m = (m if "device_map" in kw else m.to(dev)).eval()

    ch = tg.build_chart({"birth": {"dt": args.dt, "tz": args.tz, "lat": args.lat, "lon": args.lon}})
    for h in [int(x) for x in args.houses.split(",")]:
        pf = ht.judge_house(ch, h)
        for sv in pf.significations:
            fx = factors(ch, h, sv.signification, sv.karaka or "")
            row = {"key": f"H{h}/{sv.signification}", "split": "new", "fold": -1, "gold": "mixed",
                   "system": SYSTEM, "prompt": prompt_for(ch, h, sv.signification, sv, fx)}
            v = verdict_scores(m, tok, [row], torch)[0]
            p = encode_prompt(tok, row)
            x = torch.tensor([p], device=dev)
            with torch.no_grad():
                g = m.generate(input_ids=x, attention_mask=torch.ones_like(x), max_new_tokens=args.max_new,
                               do_sample=False, pad_token_id=tok.pad_token_id or tok.eos_token_id)
            text = tok.decode(g[0][len(p):], skip_special_tokens=True)
            z = max(v["logp"].values())
            pr = {c: round(2.718281828 ** (v["logp"][c] - z), 3) for c in CLASSES}
            s = sum(pr.values())
            print(f"\n=== House {h}, {sv.signification.replace('_', ' ')} ===")
            print("model's verdict weights:", {c: round(pr[c] / s, 2) for c in CLASSES})
            print(text.strip())


if __name__ == "__main__":
    main()
