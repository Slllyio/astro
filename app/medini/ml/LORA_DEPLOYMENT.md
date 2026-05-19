# LoRA Fine-Tune — Cloud Deployment Guide

The chart-language LLM training pipeline is GPU-bound; local CPU
validation works, GPU training requires either Colab, Modal, RunPod,
or another cloud provider. This guide covers all three.

## Dataset

- Local path: `data/ml_runs/verbalizer_round6_phase9/chart_qa_dataset.jsonl`
- 5,664 records, format: `{chart, prompt, answer, _meta}`
- Avg chart 1,170 chars; max 1,380 (fits any small LLM context)
- Event distribution: death (1401), work (629), relationship (605),
  fame (415), career (401), death by disease (378), family (260),
  health (228), crime (159), death by heart attack (99), social (93),
  death of mate (88), legal (83), death by accident (75), business (73)

CPU validation:
```bash
python -m app.medini.ml.train_llm --validate-only
```

## Recommended training setups by budget

### Option A — Google Colab Free (T4, 16GB VRAM, ~6 hr session limit)

```bash
# In Colab notebook (T4 GPU runtime):
!pip install -q torch transformers peft trl accelerate bitsandbytes datasets

# Upload chart_qa_dataset.jsonl + the train_llm.py module
!python -m app.medini.ml.train_llm \
    --dataset chart_qa_dataset.jsonl \
    --base-model Qwen/Qwen2.5-1.5B-Instruct \
    --epochs 2 --batch-size 2 --grad-accum-steps 4 \
    --output ./llm_checkpoints/
```

Qwen2.5-1.5B at 4-bit fits in T4. ~2 hours for 2 epochs.

### Option B — Modal (recommended for production, ~$5–10 total)

`modal_train.py`:
```python
import modal

app = modal.App("astro-llm-lora")
image = (
    modal.Image.debian_slim()
    .pip_install(
        "torch==2.4.1", "transformers", "peft", "trl",
        "accelerate", "bitsandbytes", "datasets",
    )
)
vol = modal.Volume.from_name("astro-data", create_if_missing=True)

@app.function(
    image=image, gpu="A10G", timeout=14_400,
    volumes={"/data": vol},
)
def train():
    from app.medini.ml.train_llm import train_lora
    from pathlib import Path
    train_lora(
        base_model="Qwen/Qwen2.5-1.5B-Instruct",
        dataset_path=Path("/data/chart_qa_dataset.jsonl"),
        output_dir=Path("/data/llm_out/"),
        epochs=3, lora_r=16, lora_alpha=32,
        batch_size=4, grad_accum_steps=4,
    )

@app.local_entrypoint()
def main(): train.remote()
```

Run: `modal run modal_train.py`. A10G is ~$1.10/hr; ~3 hours → ~$3.30.

### Option C — RunPod (cheap pre-emptible)

- RunPod RTX 4090 spot: ~$0.30/hr
- Phi-3-mini-128k-instruct or Qwen2.5-3B-Instruct fits
- 3 epochs × ~1.5 hr per epoch = ~$1.30 total

Upload dataset + train_llm.py to pod; `python -m app.medini.ml.train_llm ...`.

## Recommended base model choice

| Base | Params | VRAM @ 4-bit | Strengths |
|---|---|---|---|
| Qwen2.5-1.5B-Instruct (default) | 1.5B | ~3 GB | Fast, good multilingual (Sanskrit references) |
| Llama-3.2-3B-Instruct | 3B | ~5 GB | Better instruction following |
| Phi-3-mini-128k-instruct | 3.8B | ~6 GB | Long context, strong reasoning |
| Qwen2.5-7B-Instruct | 7B | ~10 GB | Best quality if you have an A10G+ |

For first pass, **Qwen2.5-1.5B** is recommended — small enough to
iterate cheaply, good enough to validate the SFT pipeline. Once the
adapter merges + serves correctly, scale up.

## After training

The output dir contains:
- `final/adapter_config.json` + `adapter_model.safetensors` — the LoRA adapter
- Training logs from SFTTrainer

To serve via Ollama (after LoRA merge):
```bash
# Local merge step (CPU OK for merge, ~5 min):
python -c "
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer
base = AutoModelForCausalLM.from_pretrained('Qwen/Qwen2.5-1.5B-Instruct')
merged = PeftModel.from_pretrained(base, 'llm_out/final').merge_and_unload()
merged.save_pretrained('astro_qwen2.5_merged/')
AutoTokenizer.from_pretrained('Qwen/Qwen2.5-1.5B-Instruct').save_pretrained('astro_qwen2.5_merged/')
"

# Convert to GGUF for Ollama:
python -m llama.cpp.convert-hf-to-gguf astro_qwen2.5_merged/ --outfile astro_qwen2.5.gguf
ollama create astro -f Modelfile  # Modelfile points to astro_qwen2.5.gguf
ollama run astro
```

## Eval after training

To measure improvement vs base model:
```bash
# Hold out 10% of QA records, measure event_root match rate
python -m app.medini.ml.eval_llm_chart_predictions \
    --adapter llm_out/final \
    --dataset chart_qa_dataset.jsonl \
    --eval-fraction 0.1
```

(eval script not yet written; trivial wrapper around the dataset.)

## Cost / time estimates

| Setup | Epochs | Time | Cost |
|---|---|---|---|
| Colab Free T4 | 2 | ~2 hr | $0 |
| Modal A10G | 3 | ~3 hr | ~$3.30 |
| RunPod 4090 spot | 3 | ~2.5 hr | ~$0.75 |

## Validation checklist

Before running cloud training, verify locally:

```bash
# 1. Dataset structure
python -m app.medini.ml.train_llm --validate-only
# Should print: "Dataset validation OK: 5664 records"

# 2. Tokenization sanity (10-record dry run)
python -c "
from app.medini.ml.train_llm import validate_dataset
from pathlib import Path
stats = validate_dataset(Path('data/ml_runs/verbalizer_round6_phase9/chart_qa_dataset.jsonl'))
print('max chart chars:', stats['max_chart_chars'])
# Should be ~1380; well under Qwen2.5-1.5B's 32k context
"

# 3. Import the train_lora function (should be CPU-importable)
python -c "from app.medini.ml.train_llm import train_lora; print('OK')"
```
