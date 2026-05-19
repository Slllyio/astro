"""Round 6 Phase 3: contrastive chart embeddings.

Learns a 128-dim "destiny embedding" per natal chart such that
charts whose owners had similar life trajectories sit close in the
embedding space. Then **chart similarity becomes a learned distance**:

  embed_chart_a, embed_chart_b → cosine_distance(a, b)
  → "how similar are their destinies?"

Why this matters classically: Vedic astrology has always implicitly
done nearest-neighbour reasoning ("you have similar yogas to
Napoleon, so..."). Contrastive embeddings make that explicit and
data-driven. The manifold structure may reveal archetypes the
classical literature didn't name.

Approach (SimCLR-style)
=======================

1. **Outcome fingerprint per person**: bag-of-event-roots they
   experienced (one-hot over ~27 classes). Two charts whose owners
   experienced similar event mixes get high Jaccard similarity.

2. **Positive / negative pairs**:
   - Positive: (chart_A, chart_B) where Jaccard(fp_A, fp_B) > 0.5.
   - Negative: a random other chart.

3. **Encoder**: 525-D natal features → 256 hidden → 128 embedding.
   2-layer MLP, ReLU + BatchNorm.

4. **Loss**: InfoNCE / NT-Xent over a minibatch. Each batch picks
   K anchors + their positives; everyone else in the batch is a
   negative.

5. **Output**: 91k × 128 embeddings parquet + nearest-neighbour
   index (FAISS or sklearn BallTree).

Restricting positive-pair construction to the 5k people who appear
in `events_all.csv` is fine; the encoder still learns generally
useful representations that generalise to the other 86k charts.
"""
from __future__ import annotations

import argparse
import datetime as dt
import logging
import random
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


# ---------- Feature selection ----------

NON_FEATURE_PREFIXES: tuple[str, ...] = (
    # Per-event columns leaked from event_corpus parquets — we want a
    # natal-only embedding here.
    "t_", "active_", "md_elapsed_years", "ad_elapsed_years",
    "pd_elapsed_years", "cross_lon_", "transit_bav_",
    "sade_sati_active", "kantaka_shani", "ashtama_shani",
)

NON_FEATURE_NAMES: frozenset[str] = frozenset({
    "name", "rodden_rating", "categories_raw", "categories_lower",
    "categories_tokens", "source_url", "duration", "event",
    "event_date", "event_jd", "birth_jd", "event_root",
    "event_subtype", "is_event",
})


def _is_natal_feature(col: str) -> bool:
    if col in NON_FEATURE_NAMES:
        return False
    return not any(col.startswith(p) for p in NON_FEATURE_PREFIXES)


def _select_numeric_natal(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Restrict df to numeric natal-only columns, drop constants."""
    natal_cols = [c for c in df.columns if _is_natal_feature(c)]
    keep: list[str] = []
    for c in natal_cols:
        s = df[c]
        if pd.api.types.is_bool_dtype(s):
            keep.append(c)
            continue
        if not pd.api.types.is_numeric_dtype(s):
            continue
        if s.nunique(dropna=False) < 2:
            continue  # constant
        keep.append(c)
    logger.info("kept %d numeric natal features (from %d candidates)",
                len(keep), len(natal_cols))
    return df[keep].fillna(0.0).astype(np.float32), keep


# ---------- Outcome fingerprint ----------

def build_outcome_fingerprints(
    events_csv: Path,
    natal_names: set[str],
) -> dict[str, frozenset[str]]:
    """{name_lower → frozenset of event_root strings they experienced}."""
    events = pd.read_csv(events_csv)
    events["_n"] = events["name"].astype(str).str.strip().str.lower()
    events["root_lower"] = events["event_root"].astype(str).str.lower().str.strip()
    events = events.loc[events["_n"].isin(natal_names)]

    fingerprints: dict[str, set[str]] = defaultdict(set)
    for name, root in zip(events["_n"], events["root_lower"], strict=True):
        if root and root != "nan":
            fingerprints[name].add(root)
    logger.info("%d people have at least 1 event in fingerprints",
                len(fingerprints))
    return {k: frozenset(v) for k, v in fingerprints.items()}


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / max(len(a | b), 1)


def build_positive_pairs(
    fingerprints: dict[str, frozenset[str]],
    threshold: float = 0.5,
    max_per_anchor: int = 5,
    seed: int = 42,
) -> list[tuple[str, str]]:
    """Find (a, b) pairs whose outcome fingerprints have Jaccard ≥ threshold.

    O(N²) in the cohort size — fine for 5k people. Per anchor, keep
    at most max_per_anchor positive partners to balance pair counts.
    """
    rng = random.Random(seed)
    names = list(fingerprints.keys())
    pairs: list[tuple[str, str]] = []
    for anchor in names:
        anchor_fp = fingerprints[anchor]
        if not anchor_fp:
            continue
        candidates = []
        for other in names:
            if other == anchor:
                continue
            j = jaccard(anchor_fp, fingerprints[other])
            if j >= threshold:
                candidates.append((other, j))
        # Sort by similarity desc, keep top max_per_anchor
        candidates.sort(key=lambda x: -x[1])
        for other, _ in candidates[:max_per_anchor]:
            pairs.append((anchor, other))
    rng.shuffle(pairs)
    logger.info("built %d positive pairs (Jaccard ≥ %g)", len(pairs), threshold)
    return pairs


# ---------- Encoder ----------

class ChartEncoder(nn.Module):
    """525 (or whatever input dim) → 256 → 128 embedding."""

    def __init__(self, input_dim: int, hidden_dim: int = 256, embed_dim: int = 128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, embed_dim),
        )
        self.embed_dim = embed_dim

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.net(x)
        return F.normalize(z, dim=-1)


# ---------- InfoNCE loss ----------

def info_nce_loss(
    embeddings_a: torch.Tensor, embeddings_b: torch.Tensor,
    temperature: float = 0.1,
) -> torch.Tensor:
    """Standard symmetric InfoNCE. Each row of A's positive is the
    corresponding row of B; all other rows are negatives.

    Returns scalar loss.
    """
    batch = embeddings_a.size(0)
    # Cosine similarity matrix (BxB) — embeddings already L2-normalized
    sim = (embeddings_a @ embeddings_b.T) / temperature
    targets = torch.arange(batch, device=sim.device)
    loss_a = F.cross_entropy(sim, targets)
    loss_b = F.cross_entropy(sim.T, targets)
    return (loss_a + loss_b) * 0.5


# ---------- Training loop ----------

def train(
    encoder: ChartEncoder,
    feature_matrix: torch.Tensor,
    name_to_idx: dict[str, int],
    pairs: list[tuple[str, str]],
    *,
    epochs: int = 20,
    batch_size: int = 256,
    lr: float = 1e-3,
    seed: int = 42,
) -> list[float]:
    """Minimal SimCLR-style training loop. Returns per-epoch loss."""
    rng = random.Random(seed)
    optim = torch.optim.AdamW(encoder.parameters(), lr=lr, weight_decay=1e-4)

    losses: list[float] = []
    for epoch in range(1, epochs + 1):
        rng.shuffle(pairs)
        epoch_loss = 0.0
        n_batches = 0
        for start in range(0, len(pairs), batch_size):
            batch_pairs = pairs[start:start + batch_size]
            if len(batch_pairs) < 16:
                continue
            anchor_idx = [name_to_idx[a] for a, _ in batch_pairs]
            partner_idx = [name_to_idx[b] for _, b in batch_pairs]
            x_a = feature_matrix[anchor_idx]
            x_b = feature_matrix[partner_idx]
            z_a = encoder(x_a)
            z_b = encoder(x_b)
            loss = info_nce_loss(z_a, z_b)
            optim.zero_grad()
            loss.backward()
            optim.step()
            epoch_loss += float(loss.item())
            n_batches += 1
        avg_loss = epoch_loss / max(n_batches, 1)
        losses.append(avg_loss)
        logger.info("epoch %2d/%d  loss=%.4f", epoch, epochs, avg_loss)
    return losses


# ---------- Output ----------

def encode_all(
    encoder: ChartEncoder, feature_matrix: torch.Tensor,
    batch_size: int = 1024,
) -> np.ndarray:
    """Run encoder over all charts; return numpy embedding matrix."""
    encoder.eval()
    embeds: list[np.ndarray] = []
    with torch.no_grad():
        for start in range(0, len(feature_matrix), batch_size):
            chunk = feature_matrix[start:start + batch_size]
            z = encoder(chunk).cpu().numpy()
            embeds.append(z)
    return np.concatenate(embeds, axis=0)


# ---------- Evaluation ----------

def nearest_neighbor_event_jaccard(
    embeddings: np.ndarray,
    names: list[str],
    fingerprints: dict[str, frozenset[str]],
    k: int = 5,
) -> float:
    """For each person WITH a fingerprint, find K nearest neighbors in
    embedding space; compute mean Jaccard similarity of their
    fingerprints. Random baseline ~ E[Jaccard between random pairs].

    Higher = embedding manifold preserves outcome similarity.
    """
    # Restrict to indexed-fingerprint people
    fp_names = [n for n in names if n in fingerprints and fingerprints[n]]
    fp_indices = [names.index(n) for n in fp_names]
    nn_index = NearestNeighbors(n_neighbors=k + 1, metric="cosine")
    nn_index.fit(embeddings)
    _, nbr_idx = nn_index.kneighbors(embeddings[fp_indices], n_neighbors=k + 1)

    jaccards = []
    for src_pos, neighbors in zip(fp_indices, nbr_idx, strict=True):
        src_name = names[src_pos]
        src_fp = fingerprints[src_name]
        for n_idx in neighbors[1:]:  # skip self at position 0
            n_name = names[n_idx]
            if n_name in fingerprints:
                jaccards.append(jaccard(src_fp, fingerprints[n_name]))
    if not jaccards:
        return 0.0
    return float(np.mean(jaccards))


def random_baseline_jaccard(
    fingerprints: dict[str, frozenset[str]], n_samples: int = 5000,
    seed: int = 42,
) -> float:
    """Expected Jaccard between random pairs — the null hypothesis."""
    rng = random.Random(seed)
    fps = list(fingerprints.values())
    js = []
    for _ in range(n_samples):
        a, b = rng.sample(fps, 2)
        js.append(jaccard(a, b))
    return float(np.mean(js))


# ---------- Main ----------

def run_phase3(
    *,
    natal_parquet: Path,
    events_csv: Path,
    output_dir: Path,
    epochs: int = 20,
    batch_size: int = 256,
    embed_dim: int = 128,
    threshold: float = 0.5,
    seed: int = 42,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(seed)
    random.seed(seed)
    np.random.seed(seed)

    logger.info("loading natal parquet ...")
    df = pd.read_parquet(natal_parquet)
    df["_n"] = df["name"].astype(str).str.strip().str.lower()
    df = df.drop_duplicates(subset="_n").reset_index(drop=True)
    names = df["_n"].tolist()
    name_to_idx = {n: i for i, n in enumerate(names)}

    logger.info("selecting numeric natal features ...")
    feature_df, feature_cols = _select_numeric_natal(df)
    scaler = StandardScaler()
    feature_arr = scaler.fit_transform(feature_df.to_numpy()).astype(np.float32)
    feature_matrix = torch.from_numpy(feature_arr)
    logger.info("feature matrix shape: %s", tuple(feature_matrix.shape))

    logger.info("building outcome fingerprints from events ...")
    fingerprints = build_outcome_fingerprints(events_csv, set(names))

    logger.info("building positive pairs (Jaccard >= %g) ...", threshold)
    pairs = build_positive_pairs(fingerprints, threshold=threshold, seed=seed)
    if len(pairs) < 1000:
        logger.warning("only %d positive pairs — try lower threshold", len(pairs))

    encoder = ChartEncoder(input_dim=feature_matrix.size(1), embed_dim=embed_dim)
    logger.info("training encoder for %d epochs ...", epochs)
    losses = train(
        encoder, feature_matrix, name_to_idx, pairs,
        epochs=epochs, batch_size=batch_size, seed=seed,
    )

    logger.info("encoding all %d charts ...", len(feature_matrix))
    embeddings = encode_all(encoder, feature_matrix)

    # Evaluate: does the embedding manifold preserve outcome similarity?
    knn_jaccard = nearest_neighbor_event_jaccard(
        embeddings, names, fingerprints, k=5,
    )
    baseline_jaccard = random_baseline_jaccard(fingerprints)
    logger.info(
        "k=5 NN Jaccard: %.4f  |  random baseline: %.4f  |  lift: %+.4f",
        knn_jaccard, baseline_jaccard, knn_jaccard - baseline_jaccard,
    )

    # Persist artifacts
    np.save(output_dir / "chart_embeddings.npy", embeddings)
    pd.DataFrame({"name_lower": names}).to_parquet(
        output_dir / "chart_names.parquet", index=False,
    )
    torch.save(encoder.state_dict(), output_dir / "encoder.pt")
    with (output_dir / "feature_columns.json").open("w", encoding="utf-8") as f:
        import json
        json.dump(feature_cols, f, indent=2)

    # Report
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    report = output_dir / "report.md"
    lines = [
        "# Phase 3 — Contrastive Chart Embeddings",
        "",
        f"_Generated {now}_",
        "",
        "## Setup",
        f"- Natal features: {len(feature_cols)} numeric cols",
        f"- Charts embedded: {len(feature_matrix):,}",
        f"- Embedding dim: {embed_dim}",
        f"- Positive-pair Jaccard threshold: {threshold}",
        f"- Positive pairs: {len(pairs):,}",
        f"- Training epochs: {epochs} | batch size: {batch_size}",
        "",
        "## Training loss curve",
        "",
        "| Epoch | Loss |",
        "|---|---|",
    ]
    for i, l in enumerate(losses, start=1):
        lines.append(f"| {i} | {l:.4f} |")
    lines.extend([
        "",
        "## Manifold evaluation",
        "",
        "For each person with an outcome fingerprint, find their 5 nearest",
        "neighbours in embedding space; compute mean Jaccard similarity of",
        "their fingerprints. Higher = embedding preserves destiny structure.",
        "",
        f"- **K=5 NN Jaccard**: {knn_jaccard:.4f}",
        f"- **Random pair baseline**: {baseline_jaccard:.4f}",
        f"- **Lift over random**: {knn_jaccard - baseline_jaccard:+.4f}",
        "",
        "Lift > +0.05 indicates the embedding manifold meaningfully captures",
        "outcome-similarity structure beyond random nearest-neighbour chance.",
    ])
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    logger.info("wrote report to %s", report)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.contrastive_embeddings",
        description="Phase 3: contrastive chart embeddings.",
    )
    parser.add_argument(
        "--natal", type=Path,
        default=Path("app/medini/data/ml_astro_round5.parquet"),
    )
    parser.add_argument(
        "--events", type=Path,
        default=Path("data/astro_databank/events_all.csv"),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("data/ml_runs/embeddings_round6_phase3/"),
    )
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--embed-dim", type=int, default=128)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    run_phase3(
        natal_parquet=args.natal,
        events_csv=args.events,
        output_dir=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
        embed_dim=args.embed_dim,
        threshold=args.threshold,
        seed=args.seed,
    )
    print(f"Phase 3 artifacts in: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
