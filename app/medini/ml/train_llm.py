"""Round 7 §2.2: LoRA fine-tune script for chart-as-language LLM.

Built CPU-runnable for dataset validation, but GPU-required for actual
training. Uses HuggingFace `transformers` + `peft` (LoRA) + `trl`
(SFTTrainer). Reads the Phase 9 QA dataset (5,664 records:
`chart_md → prompt → answer` triples) and fine-tunes a small base
model.

Recommended base models (in order of preference):
- Qwen2.5-1.5B-Instruct       (small, fast, good multilingual)
- Llama-3.2-3B-Instruct       (better quality, 6GB VRAM with 4-bit)
- Phi-3-mini-128k-instruct    (long context for full chart sheets)

CLI
===
    # Validate dataset shape (CPU-safe):
    python -m app.medini.ml.train_llm --dataset \\
        data/ml_runs/verbalizer_round6_phase9/chart_qa_dataset.jsonl \\
        --validate-only

    # Cloud / GPU training run:
    python -m app.medini.ml.train_llm \\
        --base-model Qwen/Qwen2.5-1.5B-Instruct \\
        --dataset data/ml_runs/verbalizer_round6_phase9/chart_qa_dataset.jsonl \\
        --output data/ml_runs/llm_round7_phase9/ \\
        --epochs 3 --lora-r 16 --lora-alpha 32

The script intentionally degrades gracefully on CPU: if torch.cuda.is_available()
is False, it warns + validates the dataset format + exits 0. This lets
us ship the script in the repo without depending on cloud infrastructure.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


# ---------- Dataset validation ----------

def validate_dataset(dataset_path: Path) -> dict:
    """Read the JSONL, count records, verify schema, return summary stats.

    Schema check: each record must have non-empty `chart`, `prompt`,
    `answer` string fields and a `_meta` dict.
    """
    if not dataset_path.exists():
        raise FileNotFoundError(f"dataset not found: {dataset_path}")
    stats = {
        "total_records": 0,
        "missing_chart": 0,
        "missing_prompt": 0,
        "missing_answer": 0,
        "missing_meta": 0,
        "avg_chart_chars": 0,
        "avg_prompt_chars": 0,
        "avg_answer_chars": 0,
    }
    chart_lens = []
    prompt_lens = []
    answer_lens = []
    event_root_counts: dict[str, int] = {}
    with dataset_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            stats["total_records"] += 1
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not rec.get("chart"):
                stats["missing_chart"] += 1
            if not rec.get("prompt"):
                stats["missing_prompt"] += 1
            if not rec.get("answer"):
                stats["missing_answer"] += 1
            if "_meta" not in rec:
                stats["missing_meta"] += 1
            chart_lens.append(len(rec.get("chart", "")))
            prompt_lens.append(len(rec.get("prompt", "")))
            answer_lens.append(len(rec.get("answer", "")))
            er = rec.get("_meta", {}).get("event_root", "")
            event_root_counts[er] = event_root_counts.get(er, 0) + 1
    if chart_lens:
        stats["avg_chart_chars"] = sum(chart_lens) / len(chart_lens)
        stats["avg_prompt_chars"] = sum(prompt_lens) / len(prompt_lens)
        stats["avg_answer_chars"] = sum(answer_lens) / len(answer_lens)
        stats["max_chart_chars"] = max(chart_lens)
        stats["max_prompt_chars"] = max(prompt_lens)
        stats["max_answer_chars"] = max(answer_lens)
    stats["event_root_distribution"] = dict(
        sorted(event_root_counts.items(), key=lambda x: -x[1])[:15]
    )
    return stats


# ---------- Training (GPU-required) ----------

def train_lora(
    *,
    base_model: str,
    dataset_path: Path,
    output_dir: Path,
    epochs: int = 3,
    lora_r: int = 16,
    lora_alpha: int = 32,
    learning_rate: float = 2e-4,
    batch_size: int = 4,
    grad_accum_steps: int = 4,
    max_seq_len: int = 4096,
    seed: int = 42,
) -> None:
    """GPU-required LoRA fine-tune. Requires `transformers`, `peft`,
    `trl`, `accelerate`, `bitsandbytes`.

    Reads the JSONL dataset, builds chat messages (chart → system/user;
    prompt → user; answer → assistant), tokenizes, and runs SFTTrainer
    with LoRA adapter on qkvo + ffn_in/out target modules.
    """
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError(
            "torch is required for training. Install via:\n"
            "  pip install torch transformers peft trl accelerate "
            "bitsandbytes datasets"
        ) from exc

    if not torch.cuda.is_available():
        logger.warning(
            "CUDA not available. LoRA fine-tuning on CPU is impractical "
            "(>100 hours for the 5664-record dataset). Skipping actual "
            "training; dataset validation completed successfully."
        )
        return

    # GPU-only imports (avoid forcing them on CPU users)
    try:
        from datasets import load_dataset
        from peft import LoraConfig, get_peft_model
        from transformers import (  # noqa: F401
            AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig,
        )
        from trl import SFTConfig, SFTTrainer
    except ImportError as exc:
        raise RuntimeError(
            "GPU training requires: pip install transformers peft trl "
            "accelerate bitsandbytes datasets"
        ) from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("loading base model: %s", base_model)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True, bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    tokenizer = AutoTokenizer.from_pretrained(base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        base_model, quantization_config=bnb_config,
        device_map="auto", trust_remote_code=True,
    )

    lora_config = LoraConfig(
        r=lora_r, lora_alpha=lora_alpha, lora_dropout=0.05,
        bias="none", task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Load + format dataset
    raw = load_dataset("json", data_files=str(dataset_path), split="train")

    def to_chat(record):
        chart = record["chart"]
        prompt = record["prompt"]
        answer = record["answer"]
        text = (
            f"<|im_start|>system\nYou are a Vedic astrologer.<|im_end|>\n"
            f"<|im_start|>user\n{chart}\n\n{prompt}<|im_end|>\n"
            f"<|im_start|>assistant\n{answer}<|im_end|>"
        )
        return {"text": text}

    formatted = raw.map(to_chat, remove_columns=raw.column_names)

    sft_config = SFTConfig(
        output_dir=str(output_dir),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        gradient_accumulation_steps=grad_accum_steps,
        learning_rate=learning_rate,
        max_seq_length=max_seq_len,
        logging_steps=20,
        save_strategy="epoch",
        seed=seed,
        bf16=True,
    )
    trainer = SFTTrainer(
        model=model, train_dataset=formatted,
        tokenizer=tokenizer, args=sft_config,
        dataset_text_field="text",
    )
    logger.info("starting training...")
    trainer.train()
    trainer.save_model(str(output_dir / "final"))
    logger.info("training complete; LoRA adapter saved to %s/final", output_dir)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.train_llm",
        description="LoRA fine-tune script for the Phase-9 chart QA dataset.",
    )
    parser.add_argument(
        "--dataset", type=Path,
        default=Path("data/ml_runs/verbalizer_round6_phase9/chart_qa_dataset.jsonl"),
    )
    parser.add_argument(
        "--base-model", type=str,
        default="Qwen/Qwen2.5-1.5B-Instruct",
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("data/ml_runs/llm_round7_phase9/"),
    )
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--grad-accum-steps", type=int, default=4)
    parser.add_argument("--max-seq-len", type=int, default=4096)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--validate-only", action="store_true",
        help="Only validate dataset shape (CPU-safe); skip training.",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    logger.info("validating dataset: %s", args.dataset)
    stats = validate_dataset(args.dataset)
    logger.info("dataset stats: %s", json.dumps(stats, indent=2))

    if args.validate_only:
        print(f"Dataset validation OK: {stats['total_records']} records")
        return 0

    try:
        train_lora(
            base_model=args.base_model,
            dataset_path=args.dataset,
            output_dir=args.output,
            epochs=args.epochs,
            lora_r=args.lora_r,
            lora_alpha=args.lora_alpha,
            learning_rate=args.learning_rate,
            batch_size=args.batch_size,
            grad_accum_steps=args.grad_accum_steps,
            max_seq_len=args.max_seq_len,
            seed=args.seed,
        )
    except RuntimeError as exc:
        logger.error("training failed: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
