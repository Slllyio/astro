"""Fine-tune a small open LLM (LoRA) to read like Raman from engine output, and measure it.

Prereg: docs/raman_llm/RAMAN_READER_LLM_PREREG_2026-10-31.md. Dataset: tools/raman_llm/build_dataset.py.

What it does, in order (each step writes its file, so a crash can resume with --skip-done):
  1. base model, untrained: verdict scores for every row            -> base_verdicts.jsonl
  2. for each of 5 chart folds: LoRA-train on the other 4 folds, then
       verdict scores for the held fold (all rows)                    -> fold{k}_verdicts.jsonl
       a generated reading for the held fold's hold-out rows          -> fold{k}_readings.jsonl
  3. final adapter trained on all 651 rows, for use by tools/raman_llm/read.py -> final_adapter/

The verdict is read off the model's likelihood of "VERDICT: favourable|mixed|afflicted" after
the prompt (no sampling), so the score does not depend on generation settings.

Usage:
  python -m tools.raman_llm.train_eval --out data/raman_llm/runs/v1   # auto: biggest Qwen3 the GPU fits (4-bit QLoRA)
  python -m tools.raman_llm.train_eval --model Qwen/Qwen3-14B --four-bit --out ...
  python -m tools.raman_llm.train_eval --smoke    # tiny random model, 2 folds, checks the plumbing
"""
from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path

CLASSES = ("favourable", "mixed", "afflicted")
DATA = Path("data/raman_llm/dataset.jsonl")


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def load_rows():
    return [json.loads(l) for l in open(DATA, encoding="utf-8")]


def messages(row, with_target):
    m = [{"role": "system", "content": row["system"]}, {"role": "user", "content": row["prompt"]}]
    if with_target:
        m.append({"role": "assistant", "content": row["target"]})
    return m


def encode_prompt(tok, row):
    kw = {"enable_thinking": False} if "enable_thinking" in (getattr(tok, "chat_template", "") or "") else {}
    return tok.apply_chat_template(messages(row, False), add_generation_prompt=True, tokenize=True,
                                   return_dict=False, **kw)


def encode_train(tok, row, max_len):
    p = encode_prompt(tok, row)
    t = tok(row["target"] + (tok.eos_token or ""), add_special_tokens=False)["input_ids"]
    ids = (p + t)[:max_len]
    labels = ([-100] * len(p) + t)[:max_len]
    return ids, labels


def train(model, tok, rows, args, torch):
    model.train()
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=args.lr, weight_decay=0.0)
    data = [encode_train(tok, r, args.max_len) for r in rows]
    steps_total = args.epochs * math.ceil(len(data) / args.grad_accum)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / 10) * max(0.0, 1 - s / steps_total))
    rng = random.Random(args.seed)
    step = 0
    for ep in range(args.epochs):
        order = list(range(len(data)))
        rng.shuffle(order)
        run = 0.0
        for i, j in enumerate(order):
            ids, labels = data[j]
            x = torch.tensor([ids], device=model.device)
            y = torch.tensor([labels], device=model.device)
            loss = model(input_ids=x, labels=y).loss / args.grad_accum
            loss.backward()
            run += loss.item() * args.grad_accum
            if (i + 1) % args.grad_accum == 0 or i == len(order) - 1:
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                opt.step(); sched.step(); opt.zero_grad()
                step += 1
            if (i + 1) % 50 == 0:
                log(f"  epoch {ep + 1} ex {i + 1}/{len(order)} loss {run / 50:.3f}")
                run = 0.0
    model.eval()


def verdict_scores(model, tok, rows, torch):
    """log P("VERDICT: <c>" | prompt) for each class, summed over the label's tokens."""
    out = []
    model.eval()
    with torch.no_grad():
        for r in rows:
            p = encode_prompt(tok, r)
            lp = {}
            for c in CLASSES:
                t = tok(f"VERDICT: {c}", add_special_tokens=False)["input_ids"]
                x = torch.tensor([p + t], device=model.device)
                logits = model(input_ids=x).logits[0].float()
                logp = torch.log_softmax(logits[len(p) - 1:-1], dim=-1)
                lp[c] = float(sum(logp[i, tid] for i, tid in enumerate(t)))
            pred = max(CLASSES, key=lambda c: lp[c])
            out.append({"key": r["key"], "split": r["split"], "fold": r["fold"], "gold": r["gold"],
                        "logp": lp, "pred": pred})
    return out


def generate(model, tok, rows, torch, max_new):
    out = []
    with torch.no_grad():
        for r in rows:
            p = encode_prompt(tok, r)
            x = torch.tensor([p], device=model.device)
            g = model.generate(input_ids=x, attention_mask=torch.ones_like(x), max_new_tokens=max_new,
                               do_sample=False, pad_token_id=tok.pad_token_id or tok.eos_token_id)
            text = tok.decode(g[0][len(p):], skip_special_tokens=True)
            out.append({"key": r["key"], "split": r["split"], "fold": r["fold"], "reading": text})
    return out


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def pick_model(torch):
    """Biggest Qwen3 the GPU can LoRA-train in 4-bit with room for activations."""
    if not torch.cuda.is_available():
        return "Qwen/Qwen3-1.7B", False
    gb = torch.cuda.get_device_properties(0).total_memory / 2 ** 30
    for need, name in ((44, "Qwen/Qwen3-32B"), (20, "Qwen/Qwen3-14B"), (11, "Qwen/Qwen3-8B"), (7, "Qwen/Qwen3-4B")):
        if gb >= need:
            return name, True
    return "Qwen/Qwen3-1.7B", False


def smoke_model(rows):
    """Tiny random Qwen2 + a word-level tokenizer trained on the data: checks plumbing only."""
    from tokenizers import Tokenizer, models, pre_tokenizers, trainers
    from transformers import PreTrainedTokenizerFast, Qwen2Config, Qwen2ForCausalLM
    tk = Tokenizer(models.WordLevel(unk_token="<unk>"))
    tk.pre_tokenizer = pre_tokenizers.Whitespace()
    tk.train_from_iterator([r["system"] + r["prompt"] + r["target"] for r in rows],
                           trainers.WordLevelTrainer(special_tokens=["<unk>", "<pad>", "<eos>", "<s>", "<u>", "<a>"]))
    tok = PreTrainedTokenizerFast(tokenizer_object=tk, unk_token="<unk>", pad_token="<pad>", eos_token="<eos>")
    tok.chat_template = ("{% for m in messages %}{{ '<s>' if m.role == 'system' else '<u>' if m.role == 'user' else '<a>' }}"
                         "{{ m.content }}{% endfor %}{% if add_generation_prompt %}<a>{% endif %}")
    cfg = Qwen2Config(vocab_size=tok.vocab_size + 8, hidden_size=64, intermediate_size=128, num_hidden_layers=2,
                      num_attention_heads=4, num_key_value_heads=2, max_position_embeddings=4096)
    return Qwen2ForCausalLM(cfg), tok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("--out", default="data/raman_llm/runs/v1")
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--lora-r", type=int, default=16)
    ap.add_argument("--grad-accum", type=int, default=8)
    ap.add_argument("--max-len", type=int, default=1536)
    ap.add_argument("--max-new", type=int, default=220)
    ap.add_argument("--seed", type=int, default=20261031)
    ap.add_argument("--folds", default="0,1,2,3,4")
    ap.add_argument("--skip-done", action="store_true")
    ap.add_argument("--no-final", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--four-bit", action="store_true", help="with --model: load it in 4-bit (QLoRA)")
    args = ap.parse_args()

    import torch
    from peft import LoraConfig, get_peft_model
    torch.manual_seed(args.seed)
    rows = load_rows()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cuda = torch.cuda.is_available()
    dev = "cuda" if cuda else "cpu"

    if args.smoke:
        rows = [r for r in rows if r["split"] == "pool"][:30] + [r for r in rows if r["split"] != "pool"][:30]
        args.folds, args.epochs, args.max_new = "0", 1, 12
        build = lambda: smoke_model(load_rows())
        targets = ["q_proj", "v_proj"]
        model_name = "smoke-random"
    else:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        auto_name, auto_4bit = pick_model(torch)
        model_name = args.model or auto_name
        use_4bit = (auto_4bit if args.model is None else args.four_bit) and cuda
        dtype = torch.bfloat16 if cuda and torch.cuda.is_bf16_supported() else (torch.float16 if cuda else torch.float32)

        def build():
            tok = AutoTokenizer.from_pretrained(model_name)
            kw = {"torch_dtype": dtype}
            if use_4bit:
                from transformers import BitsAndBytesConfig
                kw["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True,
                    bnb_4bit_compute_dtype=dtype)
                kw["device_map"] = {"": 0}
            m = AutoModelForCausalLM.from_pretrained(model_name, **kw)
            if use_4bit:
                from peft import prepare_model_for_kbit_training
                m = prepare_model_for_kbit_training(m, use_gradient_checkpointing=True)
            elif cuda:
                m.gradient_checkpointing_enable()
                m.enable_input_require_grads()
            return m, tok
        targets = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

    meta = {"model": model_name, "device": dev,
            "gpu": torch.cuda.get_device_name(0) if cuda else None,
            "gpu_gb": round(torch.cuda.get_device_properties(0).total_memory / 2 ** 30, 1) if cuda else None, "torch": torch.__version__, "args": vars(args),
            "n_rows": len(rows), "started": time.strftime("%Y-%m-%dT%H:%M:%S")}
    json.dump(meta, open(out / "run_meta.json", "w"), indent=1)
    log("model", model_name, "device", dev, "rows", len(rows))

    def lora(m):
        cfg = LoraConfig(r=args.lora_r, lora_alpha=2 * args.lora_r, lora_dropout=0.05,
                         target_modules=targets, task_type="CAUSAL_LM")
        m = get_peft_model(m, cfg)
        return m if getattr(m, "is_loaded_in_4bit", False) or hasattr(m, "hf_device_map") else m.to(dev)

    # 1. untrained base model
    f = out / "base_verdicts.jsonl"
    if not (args.skip_done and f.exists()):
        m, tok = build()
        if not hasattr(m, "hf_device_map"):
            m = m.to(dev)
        log("scoring untrained base model on", len(rows), "rows")
        write_jsonl(f, verdict_scores(m, tok, rows, torch))
        del m
        if cuda:
            torch.cuda.empty_cache()

    # 2. leave-charts-out folds
    for k in [int(x) for x in args.folds.split(",")]:
        fv, fr = out / f"fold{k}_verdicts.jsonl", out / f"fold{k}_readings.jsonl"
        if args.skip_done and fv.exists() and fr.exists():
            continue
        tr = [r for r in rows if r["fold"] != k]
        te = [r for r in rows if r["fold"] == k]
        assert not ({r["chart"] for r in tr} & {r["chart"] for r in te}), "chart leak across folds"
        m, tok = build()
        m = lora(m)
        log(f"fold {k}: train {len(tr)} rows, test {len(te)} rows")
        train(m, tok, tr, args, torch)
        write_jsonl(fv, verdict_scores(m, tok, te, torch))
        log(f"fold {k}: generating readings for {sum(r['split'] != 'pool' for r in te)} hold-out rows")
        write_jsonl(fr, generate(m, tok, [r for r in te if r["split"] != "pool"], torch, args.max_new))
        del m
        if cuda:
            torch.cuda.empty_cache()

    # 3. final adapter on everything (for use, not for scoring)
    if not args.no_final and not args.smoke:
        m, tok = build()
        m = lora(m)
        log("final: training on all", len(rows), "rows")
        train(m, tok, rows, args, torch)
        m.save_pretrained(out / "final_adapter")
        tok.save_pretrained(out / "final_adapter")
        json.dump({"base_model": model_name, "four_bit": bool(use_4bit)}, open(out / "final_adapter" / "raman_reader.json", "w"))
    meta["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    json.dump(meta, open(out / "run_meta.json", "w"), indent=1)
    log("done")


if __name__ == "__main__":
    main()
