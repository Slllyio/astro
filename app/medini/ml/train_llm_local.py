"""Phase-3 LOCAL LoRA fine-tune of the analysis student on DirectML (AMD GPU).

★ PARKED 2026-08-03 — the 1.5B student is CAPACITY-LIMITED for this task; do not resume
  training here expecting a better result without changing the base model size.

  Measured head-to-head on 34 held-out rows, scored by the serving guard (see
  `eval_analysis_llm.py`; the student rows were genuinely unseen — `drop_holdout` was added the
  same day after finding training had been eating its own eval set):

      citation-clean   gemma4:12b (NO fine-tune) 85.3% | this LoRA 44.1% | Claude teacher 91.2%
      guard pass                                 88.2% |          73.5% |               100%
      crisp pass                                 70.6% |          47.1% |               100%
      mis-attributed/answer                       0.18 |           1.21 |               0.09

  A stock 12B beats the fine-tuned 1.5B on EVERY axis — including voice and crispness, the two
  things the LoRA existed to teach — at ~4s more per answer and the same $0 local cost. The app
  now serves it via `REPORT_LLM_MODEL` (app/core/config.py). Corpus quality was NOT the binding
  constraint: the same corpus's teacher rows score 91.2%, so the targets were fine and the
  student simply could not track which of ~20 facts holds which number.

  What stays live and valuable: `build_analysis_corpus.py` (the citation gate + repair that took
  training targets from 63.9% to 94.0% clean), `eval_analysis_llm.py` (the harness that produced
  every number above), and this file's own guards. Resuming makes sense only against a
  materially larger base — note 3B would not train here: 16GB VRAM cannot hold a 3B LoRA at
  4096 tokens with eager attention, and 4-bit base loading is CUDA-only.

Trains a small instruct model (default Qwen2.5-1.5B-Instruct — the same family Ollama
serves as `qwen2.5:1.5b`) on the Phase-2 analysis corpus (`build_analysis_corpus.py`
output: {"system","prompt","completion","_meta.weight"} JSONL). Differences from the
cloud script (`train_llm.py`, kept unchanged as the CUDA fallback):

- **DirectML device** via the proven `stage_d_device.resolve_device` (dml -> cuda -> cpu).
- **No bitsandbytes** (CUDA-only): the frozen base loads fp32; LoRA params are the only
  trainables, so a 1.5B model fits a 16GB card comfortably without quantization.
- **Manual torch loop** (the proven Stage-D pattern), not trl.SFTTrainer —
  accelerate+DirectML is unproven and the loop needs nothing fancy.
- **Completion-only loss** (prompt tokens masked to -100) with per-row `_meta.weight`
  (Raman voice anchors carry weight 3).

Serving after training — GGUF conversion IS needed (verified 2026-07-29/30 on Ollama 0.32.4+:
raw PEFT safetensors adapters are rejected, "no Modelfile or safetensors files found"; the
docstring here previously claimed otherwise and misled the next session). The working recipe,
run from a shallow llama.cpp clone (only `convert_lora_to_gguf.py` is needed):

    git clone --depth 1 https://github.com/ggml-org/llama.cpp <somewhere>
    py -3.12 <somewhere>/convert_lora_to_gguf.py <output>/final \
        --outfile <output>/final/adapter.gguf --outtype f16 \
        --base <LOCAL base-model directory, e.g. the HF cache snapshot dir>
    # --base wants a real directory containing config.json, NOT a bare hub id like
    # "Qwen/Qwen2.5-1.5B-Instruct" — that gets misparsed as a Windows path and fails. Find
    # the cached snapshot dir under
    # ~/.cache/huggingface/hub/models--Qwen--Qwen2.5-1.5B-Instruct/snapshots/<hash>/
    ollama create astro-analyst -f <output>/Modelfile     # written by this script
    OLLAMA_MODEL=astro-analyst                            # the app now serves it

Usage:
    # smoke (a few steps, any device):
    py -3.12 -m app.medini.ml.train_llm_local --dataset data/ml_runs/analysis_corpus/sft.jsonl \\
        --output data/ml_runs/astro_analyst_lora --max-steps 3 --device auto

    # the real run:
    py -3.12 -m app.medini.ml.train_llm_local --dataset data/ml_runs/analysis_corpus/sft.jsonl \\
        --output data/ml_runs/astro_analyst_lora --epochs 2 --device dml
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from collections import Counter
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_BASE = "Qwen/Qwen2.5-1.5B-Instruct"

#: HF base id -> the Ollama tag serving the SAME weights. A LoRA adapter is only meaningful on the
#: base it was trained against, but `_write_modelfile` used to hard-code the 1.5B tag regardless of
#: `--base-model` — so training a 3B student would emit `FROM qwen2.5:1.5b ADAPTER <3B adapter>`,
#: which Ollama accepts silently and then serves as garbage. Derive it, and refuse what we cannot.
OLLAMA_BASE_TAGS: dict[str, str] = {
    "Qwen/Qwen2.5-1.5B-Instruct": "qwen2.5:1.5b",
    "Qwen/Qwen2.5-3B-Instruct": "qwen2.5:3b",
    "Qwen/Qwen2.5-7B-Instruct": "qwen2.5:7b",
    "Qwen/Qwen2.5-14B-Instruct": "qwen2.5:14b",
}


def ollama_tag_for(base_model: str) -> str:
    """The Ollama tag serving `base_model`'s weights, or an abort naming the fix."""
    tag = OLLAMA_BASE_TAGS.get(base_model)
    if tag is None:
        raise SystemExit(
            f"no Ollama base tag known for --base-model {base_model!r}. An adapter served on the "
            f"wrong base produces silent garbage, so add the mapping to OLLAMA_BASE_TAGS (and "
            f"`ollama pull` that tag) rather than guessing. Known: "
            f"{', '.join(sorted(OLLAMA_BASE_TAGS))}")
    return tag


# ─── dataset ────────────────────────────────────────────────────────────────────

def load_rows(dataset_path: Path) -> list[dict]:
    """The corpus rows, schema-checked. Rows missing prompt/completion are dropped
    loudly (count logged) — silent truncation would misreport coverage."""
    rows, dropped = [], 0
    with dataset_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                dropped += 1
                continue
            if not (r.get("prompt") and r.get("completion")):
                dropped += 1
                continue
            rows.append(r)
    if dropped:
        logger.warning("dropped %d malformed rows (of %d lines)", dropped, dropped + len(rows))
    if not rows:
        raise SystemExit(f"no usable rows in {dataset_path}")
    return rows


def encode_row(row: dict, tokenizer, max_len: int):
    """One corpus row -> (input_ids, labels, weight). Chat-templated for the base model;
    ONLY the completion tokens carry loss (prompt labels are -100)."""
    system = row.get("system") or "You are a careful Vedic-astrology explainer."
    msgs_prompt = [{"role": "system", "content": system},
                   {"role": "user", "content": row["prompt"]}]
    # ids of the prompt part alone (with generation header) — its length is the mask.
    # transformers 5.x returns a BatchEncoding (possibly nested) here; normalize to a list.
    enc = tokenizer.apply_chat_template(msgs_prompt, tokenize=True,
                                        add_generation_prompt=True)
    prompt_ids = enc["input_ids"] if not isinstance(enc, list) else enc
    if prompt_ids and isinstance(prompt_ids[0], list):
        prompt_ids = prompt_ids[0]
    prompt_ids = list(prompt_ids)
    full_ids = prompt_ids + list(tokenizer(
        row["completion"] + tokenizer.eos_token, add_special_tokens=False)["input_ids"])
    full_ids = full_ids[:max_len]
    labels = [-100] * min(len(prompt_ids), len(full_ids)) + \
             list(full_ids[len(prompt_ids):])
    if not any(l != -100 for l in labels):
        # the prompt alone exceeds max_len: no supervised tokens -> NaN loss. Skip loudly.
        return None
    weight = float(row.get("_meta", {}).get("weight", 1) or 1)
    return full_ids, labels, weight


# ─── training ───────────────────────────────────────────────────────────────────

#: corpus sources that carry STYLE only — Raman's own diction, with no [Fact N] citations in the
#: completion. A run that trains on these alone has no grounding supervision whatsoever.
VOICE_SOURCES = ("raman_voice", "raman_golden_voice")


def assert_grounded_rows_survive(all_sources: "Counter", skipped: "Counter", max_len: int) -> None:
    """Abort when `max_len` has dropped every grounded (non-voice) row.

    Hit for real 2026-08-02: the Phase-7 evidence decomposition roughly doubled prompt length
    (teacher prompts now ~3.1k tokens median, 3.4k max), so at the then-default max_len=2048
    EVERY teacher row lost its supervised tokens and the run trained happily on nothing but the
    426 voice anchors — a pure-style student with zero grounding, announced only by one warning
    line lost among HuggingFace's own chatter. Nobody ever wants that model, so it is an abort."""
    survivors = all_sources - skipped
    if not skipped:
        return
    if any(src not in VOICE_SOURCES for src in survivors.elements()):
        return
    raise SystemExit(
        f"max_len={max_len} drops EVERY grounded row — skipped {dict(skipped)} — leaving only "
        f"Raman voice anchors, which carry no [Fact N] citations at all. That trains pure style "
        f"with zero grounding supervision. Raise --max-len (4096 fits the current evidence shape "
        f"with no truncation).")


def completion_loss(logits, labels, n_sup: int):
    """Cross-entropy over ONLY the supervised completion tail.

    `encode_row` masks the entire prompt to -100 and leaves the completion as the trailing block,
    so the model needs logits for just the last ``n_sup + 1`` positions (via the model's
    ``logits_to_keep``) rather than all ~3.4k. Passing ``labels=`` instead makes transformers
    materialise the full ``[seq, vocab]`` logit tensor and upcast it to fp32 — 3400 x 151936 x 4 =
    **2.03 GB**, which OOM'd the 16GB card on 2026-08-02 once the Phase-7 evidence decomposition
    pushed prompts past 3k tokens. Restricted to the completion this is ~180 MB.

    Alignment: position *t* predicts token *t+1*, so the kept window's first ``n_sup`` positions
    are exactly the predictors of the last ``n_sup`` labels."""
    import torch.nn.functional as F

    lg = logits[:, :-1, :]                      # drops the final position (predicts nothing kept)
    tgt = labels[:, -n_sup:]
    return F.cross_entropy(lg.float().reshape(-1, lg.size(-1)), tgt.reshape(-1),
                           ignore_index=-100)


def drop_holdout(rows: list[dict]) -> tuple[list[dict], int]:
    """Remove the TEACHER rows `eval_analysis_llm` holds out, so the eval measures generalisation
    rather than memorisation.

    The eval has always selected its held-out set by a stable hash of `_meta.person_id` and its
    docstring has always said "training must EXCLUDE them by the same rule" — but training never
    did (found 2026-08-02), so every reported student score was computed on rows the student had
    been fine-tuned on. Only `source == "teacher"` rows are subject to it, matching exactly what
    the eval samples; the Raman voice anchors are style supervision and are never evaluated."""
    from app.medini.ml.eval_analysis_llm import is_holdout

    kept = [r for r in rows
            if not (r.get("_meta", {}).get("source") == "teacher"
                    and is_holdout(r.get("_meta", {}).get("person_id", "")))]
    return kept, len(rows) - len(kept)


def train(dataset_path: Path, output_dir: Path, base_model: str, device_pref: str,
          epochs: int, lr: float, lora_r: int, lora_alpha: int, max_len: int,
          grad_accum: int, max_steps: int | None, seed: int,
          exclude_holdout: bool = True) -> dict:
    import torch
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer

    from app.medini.ml.stage_d_device import device_label, resolve_device

    torch.manual_seed(seed)
    device = resolve_device(device_pref)
    label = device_label(device)
    logger.info("device: %s", label)

    tokenizer = AutoTokenizer.from_pretrained(base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    # eager attention: scaled-dot-product kernels are not guaranteed on DirectML.
    # fp16 weights + gradient checkpointing keep the eager attention matrices
    # (batch*heads*seq^2 — the DML OOM culprit at fp32/3072) inside VRAM.
    dtype = torch.float16 if device.type != "cpu" else torch.float32
    model = AutoModelForCausalLM.from_pretrained(
        base_model, torch_dtype=dtype, attn_implementation="eager")
    model.config.use_cache = False
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()
    lora = LoraConfig(r=lora_r, lora_alpha=lora_alpha, lora_dropout=0.05, bias="none",
                      task_type="CAUSAL_LM",
                      target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                                      "gate_proj", "up_proj", "down_proj"])
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()
    model.to(device)
    model.train()

    rows = load_rows(dataset_path)
    held_out = 0
    if exclude_holdout:
        rows, held_out = drop_holdout(rows)
        logger.info("excluded %d held-out teacher rows (eval_analysis_llm's own hash rule)",
                    held_out)
    encoded, skipped_by_source = [], Counter()
    for r in rows:
        e = encode_row(r, tokenizer, max_len)
        if e is None:
            skipped_by_source[r.get("_meta", {}).get("source", "?")] += 1
        else:
            encoded.append(e)
    skipped = len(rows) - len(encoded)
    if skipped:
        logger.warning("%d/%d rows skipped: prompt alone exceeds max_len=%d — raise "
                       "--max-len to train on them (%s)", skipped, len(rows), max_len,
                       dict(skipped_by_source))
    if not encoded:
        raise SystemExit(f"no trainable rows at max_len={max_len}; raise --max-len")
    assert_grounded_rows_survive(
        Counter(r.get("_meta", {}).get("source", "?") for r in rows), skipped_by_source, max_len)
    logger.info("dataset: %d rows (max_len=%d)", len(encoded), max_len)

    trainable = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(trainable, lr=lr, weight_decay=0.01)

    output_dir.mkdir(parents=True, exist_ok=True)
    loss_log = (output_dir / "loss_log.jsonl").open("a", encoding="utf-8")
    step, t0 = 0, time.time()
    losses: list[float] = []
    # deterministic order shuffled per-epoch by a seeded generator (reproducible)
    g = torch.Generator().manual_seed(seed)

    # static loss scaling for the fp16 path (no torch.cuda.amp on DirectML): scale up the
    # loss so fp16 grads don't underflow, unscale before clipping, skip a step on inf/nan.
    loss_scale = 128.0 if dtype == torch.float16 else 1.0

    for epoch in range(epochs):
        order = torch.randperm(len(encoded), generator=g).tolist()
        optimizer.zero_grad()
        for i, idx in enumerate(order):
            ids, labels, weight = encoded[idx]
            input_ids = torch.tensor([ids], dtype=torch.long, device=device)
            lab = torch.tensor([labels], dtype=torch.long, device=device)
            # only the completion tail carries loss — ask for just those logits (see
            # completion_loss): `labels=` here would build the whole [seq, 151936] fp32 tensor.
            n_sup = sum(1 for l in labels if l != -100)
            out = model(input_ids=input_ids, logits_to_keep=n_sup + 1)
            step_loss = completion_loss(out.logits, lab, n_sup)
            loss = step_loss * (weight / grad_accum) * loss_scale
            loss.backward()
            losses.append(float(step_loss.detach().cpu()))
            if (i + 1) % grad_accum == 0:
                if loss_scale != 1.0:
                    for p in trainable:
                        if p.grad is not None:
                            p.grad.div_(loss_scale)
                grad_norm = torch.nn.utils.clip_grad_norm_(trainable, 1.0)
                if torch.isfinite(grad_norm):
                    optimizer.step()
                else:
                    logger.warning("non-finite grad norm at step %d; step skipped", step)
                optimizer.zero_grad()
                step += 1
                if step % 5 == 0 or max_steps:
                    avg = sum(losses[-grad_accum * 5:]) / len(losses[-grad_accum * 5:])
                    logger.info("epoch %d step %d loss %.4f (%.1fs)",
                                epoch, step, avg, time.time() - t0)
                    loss_log.write(json.dumps({"epoch": epoch, "step": step,
                                               "loss": avg, "device": label}) + "\n")
                    loss_log.flush()
                if max_steps and step >= max_steps:
                    break
        # save the adapter every epoch. DirectML tensors don't implement the storage
        # introspection PEFT's save_pretrained needs (`NotImplementedError: Cannot access
        # storage of OpaqueTensorImpl`, hit live 2026-07-29 on the AMD DML backend) — move to
        # CPU for the save, then back to the training device to continue.
        #
        # `final/` is refreshed at the SAME time (2026-08-02): a 3-epoch run OOM'd at step 180 of
        # 240 on a 10MB allocation (DirectML fragments VRAM over a long run), and because final/
        # was only written after the loop, a fully-trained 2-epoch adapter existed on disk but
        # nothing pointed at it and no Modelfile had been generated. Every completed epoch now
        # leaves an immediately servable adapter behind.
        if device.type == "privateuseone":
            model.to("cpu")
            model.save_pretrained(str(output_dir / f"epoch_{epoch}"))
            model.save_pretrained(str(output_dir / "final"))
            model.to(device)
        else:
            model.save_pretrained(str(output_dir / f"epoch_{epoch}"))
            model.save_pretrained(str(output_dir / "final"))
        tokenizer.save_pretrained(str(output_dir / "final"))
        _write_modelfile(output_dir, base_model)
        logger.info("epoch %d saved (final/ now holds %d completed epoch(s))", epoch, epoch + 1)
        if max_steps and step >= max_steps:
            break

    if device.type == "privateuseone":
        model.to("cpu")
    model.save_pretrained(str(output_dir / "final"))
    tokenizer.save_pretrained(str(output_dir / "final"))
    _write_modelfile(output_dir, base_model)
    loss_log.close()
    first = losses[0] if losses else float("nan")
    last = sum(losses[-10:]) / max(1, len(losses[-10:])) if losses else float("nan")
    summary = {"rows": len(encoded), "held_out_excluded": held_out, "steps": step,
               "epochs": epochs, "device": label,
               "first_loss": round(first, 4), "last_loss_avg10": round(last, 4),
               "adapter": str(output_dir / "final")}
    (output_dir / "run_summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def _write_modelfile(output_dir: Path, base_model: str = DEFAULT_BASE) -> None:
    """The Ollama import recipe: modern Ollama reads PEFT safetensors adapters directly —
    no GGUF conversion step."""
    # NOTE (verified 2026-07-28 on Ollama 0.32.4): `ADAPTER <peft safetensors dir>` is
    # rejected for this stack ("no Modelfile or safetensors files found") — convert the
    # adapter to GGUF first (llama.cpp convert_lora_to_gguf.py, see LORA_DEPLOYMENT.md)
    # and point ADAPTER at the .gguf. The Modelfile below assumes that conversion.
    adapter_abs = (output_dir / "final" / "adapter.gguf").resolve()
    (output_dir / "Modelfile").write_text(
        f"FROM {ollama_tag_for(base_model)}\n"
        f"ADAPTER {adapter_abs}\n".replace("\\", "/"),
        encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m app.medini.ml.train_llm_local",
                                 description=__doc__.splitlines()[0])
    ap.add_argument("--dataset", type=Path,
                    default=Path("data/ml_runs/analysis_corpus/sft.jsonl"))
    ap.add_argument("--output", type=Path, default=Path("data/ml_runs/astro_analyst_lora"))
    ap.add_argument("--base-model", default=DEFAULT_BASE)
    ap.add_argument("--device", default="auto", choices=("auto", "dml", "cuda", "cpu"))
    ap.add_argument("--epochs", type=int, default=2)
    ap.add_argument("--learning-rate", type=float, default=1e-4)
    ap.add_argument("--lora-r", type=int, default=16)
    ap.add_argument("--lora-alpha", type=int, default=32)
    ap.add_argument("--max-len", type=int, default=4096,
                    help="token budget per row. 4096 fits the post-Phase-7 evidence "
                         "shape (teacher prompts ~3.1k tokens) with no truncation; "
                         "the previous 2048 default silently dropped every teacher row.")
    ap.add_argument("--grad-accum", type=int, default=8)
    ap.add_argument("--max-steps", type=int, default=None,
                    help="stop after N optimizer steps (smoke runs)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--include-holdout", action="store_true",
                    help="train on eval_analysis_llm's held-out teacher rows too. OFF by "
                         "default: including them (which every run before 2026-08-02 did) makes "
                         "the eval report memorisation instead of generalisation.")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    summary = train(args.dataset, args.output, args.base_model, args.device, args.epochs,
                    args.learning_rate, args.lora_r, args.lora_alpha, args.max_len,
                    args.grad_accum, args.max_steps, args.seed,
                    exclude_holdout=not args.include_holdout)
    print(json.dumps(summary, indent=2))
    print(f"\nServe it:  ollama create astro-analyst -f {args.output / 'Modelfile'}\n"
          f"Then set   OLLAMA_MODEL=astro-analyst")
    return 0


if __name__ == "__main__":
    sys.exit(main())
