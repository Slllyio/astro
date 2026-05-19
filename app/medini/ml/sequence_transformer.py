"""Round 6 Phase 4: Event Sequence Transformer.

Treats a person's life as a sequence of events. Trains a decoder-only
Transformer to GENERATE the sequence conditioned on the natal chart
embedding (Phase 3 output).

Why this is the headline of Round 6: classical Vedic astrology
predicts events independently. Reality is sequential — events
correlate temporally and contextually. A divorce at 33 changes
what's likely at 38 in ways the static chart doesn't capture.
This model captures it autoregressively.

Output: a generative model of life trajectories. Given a chart,
sample 100 possible life sequences → probability distribution over
futures.

Tokenization
============
Each life = [BOS, (event_class, age_bin), ..., EOS].

  event_classes: top-K event_roots from Round 5 multi-class (default
                  K=27, matches the trained multiclass)
  age_bins:      0-5, 5-10, ..., 90+  (19 bins for 0..100)

Combined into a single vocab of (class, age_bin) pairs plus BOS/EOS:
  vocab_size = K_classes × N_bins + 3

Architecture
============
- Chart embedding (128-D from Phase 3) projected to model dim
- Prepended as a "context token" at position 0
- Decoder-only Transformer (4 layers, 4 heads, dim 128, ~1M params)
- Cross-entropy loss on next-token prediction

Inference
=========
- Given a natal chart, beam-sample 100 trajectories
- Aggregate to: P(next_event_class | so_far), expected age of next event

CLI
===
    python -m app.medini.ml.sequence_transformer \\
        --embeddings data/ml_runs/embeddings_round6_phase3/chart_embeddings.npy \\
        --names data/ml_runs/embeddings_round6_phase3/chart_names.parquet \\
        --events data/astro_databank/events_all.csv \\
        --raw data/astro_databank/merged_with_events.csv \\
        --output data/ml_runs/sequence_round6_phase4/
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger(__name__)


# ---------- Tokenizer ----------

class LifeTokenizer:
    """Converts (event_class, age) → integer token id and back.

    Reserves token ids 0/1/2 for PAD/BOS/EOS.
    Token ids 3..(3+K*N-1) encode (event_class_idx, age_bin_idx).
    """

    PAD = 0
    BOS = 1
    EOS = 2
    SPECIAL_OFFSET = 3

    def __init__(
        self,
        event_classes: list[str],
        max_age: int = 100,
        age_bin_width: int = 5,
    ):
        self.event_classes = event_classes
        self.class_to_idx = {c: i for i, c in enumerate(event_classes)}
        self.max_age = max_age
        self.age_bin_width = age_bin_width
        self.n_age_bins = max_age // age_bin_width + 1
        self.vocab_size = (
            self.SPECIAL_OFFSET + len(event_classes) * self.n_age_bins
        )

    def encode(self, event_class: str, age: float) -> int:
        class_idx = self.class_to_idx.get(event_class)
        if class_idx is None:
            return self.PAD  # treat unknown as padding (skipped)
        age_clamped = max(0, min(int(age), self.max_age))
        age_bin = age_clamped // self.age_bin_width
        token_id = (
            self.SPECIAL_OFFSET
            + class_idx * self.n_age_bins
            + age_bin
        )
        return token_id

    def decode(self, token_id: int) -> tuple[str, int] | str:
        if token_id == self.PAD:
            return "<PAD>"
        if token_id == self.BOS:
            return "<BOS>"
        if token_id == self.EOS:
            return "<EOS>"
        idx = token_id - self.SPECIAL_OFFSET
        class_idx = idx // self.n_age_bins
        age_bin = idx % self.n_age_bins
        if 0 <= class_idx < len(self.event_classes):
            return (
                self.event_classes[class_idx],
                age_bin * self.age_bin_width,
            )
        return "<UNK>"


def build_person_sequences(
    events_csv: Path,
    raw_csv: Path,
    name_set: set[str],
    tokenizer: LifeTokenizer,
) -> dict[str, list[int]]:
    """Build {name_lower → [BOS, tok1, tok2, ..., EOS]}."""
    events = pd.read_csv(events_csv)
    events["_n"] = events["name"].astype(str).str.strip().str.lower()
    events["root_lower"] = events["event_root"].astype(str).str.lower().str.strip()
    events["event_date"] = pd.to_datetime(events["event_date"], errors="coerce")
    events = events.dropna(subset=["event_date"])
    events = events.loc[events["_n"].isin(name_set)]

    raw = pd.read_csv(raw_csv, low_memory=False)
    raw["_n"] = raw["name"].astype(str).str.strip().str.lower()
    raw["date_of_birth"] = pd.to_datetime(raw["date_of_birth"], errors="coerce")
    raw = raw.drop_duplicates(subset="_n").set_index("_n")

    sequences: dict[str, list[int]] = {}
    for name, group in events.groupby("_n"):
        if name not in raw.index:
            continue
        birth = raw.loc[name, "date_of_birth"]
        if pd.isna(birth):
            continue
        group_sorted = group.sort_values("event_date")
        tokens: list[int] = [tokenizer.BOS]
        for _, row in group_sorted.iterrows():
            age = (row["event_date"] - birth).days / 365.25
            if not (0 <= age <= tokenizer.max_age):
                continue
            tok = tokenizer.encode(row["root_lower"], age)
            if tok == tokenizer.PAD:
                continue
            tokens.append(tok)
        if len(tokens) < 2:
            continue
        tokens.append(tokenizer.EOS)
        sequences[name] = tokens
    logger.info(
        "built sequences for %d people; mean length %.1f",
        len(sequences),
        np.mean([len(s) for s in sequences.values()]) if sequences else 0.0,
    )
    return sequences


# ---------- Model ----------

class SeqTransformer(nn.Module):
    """Decoder-only Transformer with chart-embedding prefix conditioning."""

    def __init__(
        self,
        vocab_size: int,
        chart_dim: int = 128,
        model_dim: int = 128,
        n_heads: int = 4,
        n_layers: int = 4,
        max_seq_len: int = 32,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.tok_emb = nn.Embedding(vocab_size, model_dim)
        self.pos_emb = nn.Embedding(max_seq_len + 1, model_dim)  # +1 for chart prefix
        self.chart_proj = nn.Linear(chart_dim, model_dim)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=model_dim, nhead=n_heads, dim_feedforward=4 * model_dim,
            dropout=dropout, activation="gelu", batch_first=True,
            norm_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        self.head = nn.Linear(model_dim, vocab_size)
        self.max_seq_len = max_seq_len
        self.model_dim = model_dim

    def forward(
        self,
        token_ids: torch.Tensor,            # (B, T)
        chart_emb: torch.Tensor,            # (B, chart_dim)
    ) -> torch.Tensor:
        B, T = token_ids.shape
        tok_h = self.tok_emb(token_ids)                  # (B, T, D)
        chart_h = self.chart_proj(chart_emb).unsqueeze(1)  # (B, 1, D)
        h = torch.cat([chart_h, tok_h], dim=1)           # (B, T+1, D)
        pos = torch.arange(T + 1, device=h.device).unsqueeze(0)
        h = h + self.pos_emb(pos)
        # Causal mask: each position can only attend to ≤ itself
        attn_mask = torch.triu(
            torch.full((T + 1, T + 1), float("-inf"), device=h.device),
            diagonal=1,
        )
        h = self.transformer(h, mask=attn_mask)
        logits = self.head(h)                            # (B, T+1, V)
        # We predict tokens (1..T) from positions (0..T-1). Drop position
        # T (which would predict beyond EOS) and keep positions (0..T-1)
        # plus the chart prefix produced position 0's logits.
        return logits[:, :-1, :]                         # (B, T, V)


# ---------- Training ----------

def collate(
    batch: list[tuple[np.ndarray, list[int]]], pad_id: int, max_len: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    """Right-pad sequences to max_len; return (token_ids, chart_emb)."""
    embeds, tokens = zip(*batch, strict=True)
    chart_emb = torch.from_numpy(np.stack(embeds)).float()
    tok_tensor = torch.full(
        (len(batch), max_len), pad_id, dtype=torch.long,
    )
    for i, tok in enumerate(tokens):
        truncated = tok[:max_len]
        tok_tensor[i, :len(truncated)] = torch.tensor(truncated, dtype=torch.long)
    return tok_tensor, chart_emb


def train(
    model: SeqTransformer,
    train_pairs: list[tuple[np.ndarray, list[int]]],
    *,
    tokenizer: LifeTokenizer,
    epochs: int = 30,
    batch_size: int = 64,
    lr: float = 1e-3,
    seed: int = 42,
    max_len: int = 32,
) -> list[float]:
    rng = random.Random(seed)
    optim = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    losses: list[float] = []
    for epoch in range(1, epochs + 1):
        rng.shuffle(train_pairs)
        epoch_loss = 0.0
        n_batches = 0
        for start in range(0, len(train_pairs), batch_size):
            batch = train_pairs[start:start + batch_size]
            if len(batch) < 4:
                continue
            tok_ids, chart_emb = collate(batch, tokenizer.PAD, max_len)
            logits = model(tok_ids[:, :-1], chart_emb)        # predict tok[1:]
            targets = tok_ids[:, 1:]
            loss = F.cross_entropy(
                logits.reshape(-1, logits.size(-1)),
                targets.reshape(-1),
                ignore_index=tokenizer.PAD,
            )
            optim.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optim.step()
            epoch_loss += float(loss.item())
            n_batches += 1
        avg = epoch_loss / max(n_batches, 1)
        losses.append(avg)
        logger.info("epoch %2d/%d  loss=%.4f", epoch, epochs, avg)
    return losses


# ---------- Inference ----------

@torch.no_grad()
def sample_trajectory(
    model: SeqTransformer,
    chart_emb: torch.Tensor,                    # (chart_dim,)
    tokenizer: LifeTokenizer,
    *,
    max_steps: int = 16,
    temperature: float = 1.0,
    top_k: int = 5,
) -> list[int]:
    """Sample a single life trajectory from a chart embedding."""
    model.eval()
    tokens = [tokenizer.BOS]
    chart_in = chart_emb.unsqueeze(0)
    for _ in range(max_steps):
        tok_in = torch.tensor([tokens], dtype=torch.long)
        logits = model(tok_in, chart_in)          # (1, T, V)
        next_logits = logits[0, -1] / max(temperature, 1e-6)
        # Top-k sampling
        if top_k > 0 and top_k < next_logits.size(0):
            top_vals, top_idx = next_logits.topk(top_k)
            probs = F.softmax(top_vals, dim=-1)
            choice = top_idx[torch.multinomial(probs, 1)].item()
        else:
            probs = F.softmax(next_logits, dim=-1)
            choice = int(torch.multinomial(probs, 1).item())
        if choice == tokenizer.EOS or choice == tokenizer.PAD:
            tokens.append(choice)
            break
        tokens.append(choice)
    return tokens


def evaluate_next_token_accuracy(
    model: SeqTransformer,
    eval_pairs: list[tuple[np.ndarray, list[int]]],
    tokenizer: LifeTokenizer,
    max_len: int = 32,
) -> dict[str, float]:
    """Measure next-event prediction accuracy on a held-out set.

    For each (chart, sequence), feed the prefix [BOS, e_1, ..., e_t] and
    ask the model for e_{t+1}. Top-1 and top-5 accuracy over the
    event_class portion of the token (ignoring exact age).
    """
    model.eval()
    correct1 = 0
    correct5 = 0
    correct_class_only = 0
    total = 0
    with torch.no_grad():
        for chart, tokens in eval_pairs:
            if len(tokens) < 3:
                continue
            chart_t = torch.from_numpy(chart).float().unsqueeze(0)
            for t in range(1, len(tokens) - 1):  # predict tokens[t+1] from tokens[:t+1]
                prefix = torch.tensor([tokens[:t + 1]], dtype=torch.long)
                if prefix.size(1) > max_len:
                    break
                logits = model(prefix, chart_t)
                next_logits = logits[0, -1]
                pred = int(next_logits.argmax().item())
                top5 = set(next_logits.topk(5).indices.tolist())
                actual = tokens[t + 1]
                if pred == actual:
                    correct1 += 1
                if actual in top5:
                    correct5 += 1
                # Class-only accuracy: ignore the age bin component
                if pred >= tokenizer.SPECIAL_OFFSET and actual >= tokenizer.SPECIAL_OFFSET:
                    pred_class = (pred - tokenizer.SPECIAL_OFFSET) // tokenizer.n_age_bins
                    act_class = (actual - tokenizer.SPECIAL_OFFSET) // tokenizer.n_age_bins
                    if pred_class == act_class:
                        correct_class_only += 1
                total += 1
    if total == 0:
        return {"top1": 0.0, "top5": 0.0, "class_only": 0.0, "total": 0}
    return {
        "top1": correct1 / total,
        "top5": correct5 / total,
        "class_only": correct_class_only / total,
        "total": total,
    }


# ---------- Main ----------

def run_phase4(
    *,
    embeddings_path: Path,
    names_parquet: Path,
    events_csv: Path,
    raw_csv: Path,
    output_dir: Path,
    epochs: int = 30,
    batch_size: int = 64,
    test_split: float = 0.2,
    seed: int = 42,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(seed)
    random.seed(seed)
    np.random.seed(seed)

    logger.info("loading embeddings + names ...")
    embeddings = np.load(embeddings_path)
    names_df = pd.read_parquet(names_parquet)
    names = names_df["name_lower"].tolist()
    name_to_idx = {n: i for i, n in enumerate(names)}
    logger.info("loaded %d embeddings × %d dims", *embeddings.shape)

    # Determine top event classes by frequency
    events = pd.read_csv(events_csv)
    events["root_lower"] = events["event_root"].astype(str).str.lower().str.strip()
    class_counts = events["root_lower"].value_counts()
    top_classes = [
        c for c in class_counts.head(30).index
        if c and c != "nan"
    ]
    logger.info("using top %d event classes", len(top_classes))

    tokenizer = LifeTokenizer(event_classes=top_classes)
    logger.info("vocab size: %d", tokenizer.vocab_size)

    logger.info("building per-person sequences ...")
    sequences = build_person_sequences(
        events_csv, raw_csv, set(names), tokenizer,
    )
    # Restrict to sequences with at least 1 real event (length ≥ 3 = BOS+1+EOS)
    sequences = {k: v for k, v in sequences.items() if len(v) >= 3}
    logger.info("trainable sequences: %d", len(sequences))

    # Build (chart_emb, tokens) pairs
    all_pairs: list[tuple[np.ndarray, list[int]]] = []
    for name, tokens in sequences.items():
        if name not in name_to_idx:
            continue
        emb = embeddings[name_to_idx[name]]
        all_pairs.append((emb, tokens))
    logger.info("built %d (embedding, tokens) pairs", len(all_pairs))

    # Train/eval split
    rng = random.Random(seed)
    rng.shuffle(all_pairs)
    n_eval = max(int(len(all_pairs) * test_split), 50)
    eval_pairs = all_pairs[:n_eval]
    train_pairs = all_pairs[n_eval:]
    logger.info("train=%d  eval=%d", len(train_pairs), len(eval_pairs))

    chart_dim = embeddings.shape[1]
    max_len = 32
    model = SeqTransformer(
        vocab_size=tokenizer.vocab_size,
        chart_dim=chart_dim,
        model_dim=128,
        n_heads=4,
        n_layers=4,
        max_seq_len=max_len,
    )
    n_params = sum(p.numel() for p in model.parameters())
    logger.info("model parameters: %d (%.2f M)", n_params, n_params / 1e6)

    losses = train(
        model, train_pairs, tokenizer=tokenizer,
        epochs=epochs, batch_size=batch_size, seed=seed, max_len=max_len,
    )

    # Evaluate
    eval_metrics = evaluate_next_token_accuracy(
        model, eval_pairs, tokenizer, max_len=max_len,
    )
    logger.info(
        "eval: top1=%.4f  top5=%.4f  class_only=%.4f  (n=%d)",
        eval_metrics["top1"], eval_metrics["top5"],
        eval_metrics["class_only"], eval_metrics["total"],
    )

    # Save artifacts
    torch.save(model.state_dict(), output_dir / "sequence_model.pt")
    with (output_dir / "tokenizer.json").open("w", encoding="utf-8") as f:
        json.dump({
            "event_classes": tokenizer.event_classes,
            "max_age": tokenizer.max_age,
            "age_bin_width": tokenizer.age_bin_width,
            "vocab_size": tokenizer.vocab_size,
            "n_age_bins": tokenizer.n_age_bins,
        }, f, indent=2)

    # Demo: sample 5 trajectories for the first eval chart
    demo_emb, demo_tokens = eval_pairs[0]
    demo_emb_t = torch.from_numpy(demo_emb).float()
    sampled = []
    for _ in range(5):
        traj = sample_trajectory(model, demo_emb_t, tokenizer, max_steps=10)
        decoded = [tokenizer.decode(t) for t in traj]
        sampled.append(decoded)

    # Random baseline: predict the marginal class distribution at each step
    class_counts_in_train = Counter()
    for _, toks in train_pairs:
        for t in toks:
            if t >= tokenizer.SPECIAL_OFFSET:
                class_counts_in_train[t] += 1
    total_train_toks = sum(class_counts_in_train.values()) or 1
    most_common_token = class_counts_in_train.most_common(1)[0][0]
    random_top1 = sum(
        1 for _, toks in eval_pairs
        for t in toks[2:]
        if t == most_common_token
    ) / max(sum(len(toks) - 2 for _, toks in eval_pairs), 1)

    # Report
    report = output_dir / "report.md"
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Phase 4 — Event Sequence Transformer",
        "",
        f"_Generated {now}_",
        "",
        "## Setup",
        f"- Event classes: {len(top_classes)}",
        f"- Vocab size: {tokenizer.vocab_size}",
        f"- Age bins: {tokenizer.n_age_bins} (width {tokenizer.age_bin_width}y)",
        f"- Chart embedding dim: {chart_dim}",
        f"- Model: 4 layers, 4 heads, dim 128 (~{n_params/1e6:.2f}M params)",
        f"- Trainable pairs: {len(train_pairs):,}",
        f"- Eval pairs: {len(eval_pairs):,}",
        "",
        "## Training loss",
        "",
        "| Epoch | Loss |",
        "|---|---|",
    ]
    for i, l in enumerate(losses, start=1):
        lines.append(f"| {i} | {l:.4f} |")
    lines.extend([
        "",
        "## Evaluation (next-token prediction on held-out cohort)",
        "",
        f"- **Top-1 token accuracy**: {eval_metrics['top1']:.4f}",
        f"- **Top-5 token accuracy**: {eval_metrics['top5']:.4f}",
        f"- **Class-only accuracy** (ignoring age bin): "
        f"{eval_metrics['class_only']:.4f}",
        f"- **Eval token count**: {eval_metrics['total']:,}",
        f"- **Random baseline** (most common class): {random_top1:.4f}",
        "",
        "Top-1 includes both class AND age-bin. Class-only ignores the age",
        "bin to measure 'does the model know WHAT comes next, even if wrong",
        "about when'. Random baseline = always predict the most common",
        "event/age combination.",
        "",
        "## Sample trajectories (one demo chart, 5 sampled lives)",
        "",
    ])
    for i, traj in enumerate(sampled, start=1):
        lines.append(f"**Trajectory {i}**: " + " → ".join(str(t) for t in traj))
        lines.append("")

    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("wrote report to %s", report)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.sequence_transformer",
    )
    parser.add_argument(
        "--embeddings", type=Path,
        default=Path("data/ml_runs/embeddings_round6_phase3/chart_embeddings.npy"),
    )
    parser.add_argument(
        "--names", type=Path,
        default=Path("data/ml_runs/embeddings_round6_phase3/chart_names.parquet"),
    )
    parser.add_argument(
        "--events", type=Path,
        default=Path("data/astro_databank/events_all.csv"),
    )
    parser.add_argument(
        "--raw", type=Path,
        default=Path("data/astro_databank/merged_with_events.csv"),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("data/ml_runs/sequence_round6_phase4/"),
    )
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    run_phase4(
        embeddings_path=args.embeddings,
        names_parquet=args.names,
        events_csv=args.events,
        raw_csv=args.raw,
        output_dir=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
    )
    print(f"Phase 4 artifacts in: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
