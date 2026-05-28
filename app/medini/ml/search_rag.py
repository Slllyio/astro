"""Semantic + hybrid search over the knowledge library's RAG index.

Loads ``embeddings/chunks.parquet`` + ``embeddings/vectors.npy``, encodes the
query with the same sentence-transformer model, and ranks chunks by:

  * **--mode semantic** (default): cosine similarity only.
  * **--mode hybrid**: 0.7 * cosine + 0.3 * normalized lexical (BM25-like
    token overlap). Good when the user knows exact terminology.
  * **--mode lexical**: token-overlap only (no embedding needed; fastest).

Filters apply across all modes:
  --topic dasha.vimshottari
  --source bphs (substring match on source field)
  --quality manual_captions
  --min-tokens 50

Output: top-N chunks with chunk_id, artefact title, source, source_url, the
chunk text (truncated to ~400 chars), and a relevance score.

Usage:
    python -m app.medini.ml.search_rag --query "what happens during Saturn dasha for Libra ascendant"
    python -m app.medini.ml.search_rag --query "vipareeta raja yoga effects" --topic yogas.vipareeta_raj_yogas
    python -m app.medini.ml.search_rag --query "shadbala calculation" --mode hybrid --top 5
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Lexical scoring                                                              #
# --------------------------------------------------------------------------- #

_TOKEN_RE = re.compile(r"[A-Za-zॐ-ॿ\d]+")


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def _lexical_score(query: str, text: str) -> float:
    """Token-overlap score normalised by query length."""
    q_tokens = _tokenize(query)
    if not q_tokens:
        return 0.0
    q_set = set(q_tokens)
    # Also weight repeated query terms
    body = text.lower()
    hits = sum(body.count(t) for t in q_set)
    return hits / max(len(q_tokens), 1)


# --------------------------------------------------------------------------- #
# Filters                                                                      #
# --------------------------------------------------------------------------- #

def _apply_filters(
    df: pd.DataFrame,
    *,
    topic: str | None,
    source: str | None,
    min_tokens: int,
) -> np.ndarray:
    """Return a boolean mask selecting rows that match all filters."""
    mask = np.ones(len(df), dtype=bool)
    if topic:
        mask &= df["topics"].apply(
            lambda ts: topic in (list(ts) if ts is not None else [])
        ).to_numpy()
    if source:
        mask &= df["source"].fillna("").str.contains(source, na=False).to_numpy()
    if min_tokens > 0:
        mask &= (df["n_tokens"] >= min_tokens).to_numpy()
    return mask


# --------------------------------------------------------------------------- #
# Driver                                                                       #
# --------------------------------------------------------------------------- #

def search(
    query: str,
    embeddings_dir: Path,
    *,
    mode: str = "hybrid",
    topic: str | None = None,
    source: str | None = None,
    min_tokens: int = 30,
    top: int = 10,
) -> pd.DataFrame:
    chunks_path = embeddings_dir / "chunks.parquet"
    vectors_path = embeddings_dir / "vectors.npy"
    meta_path = embeddings_dir / "meta.json"
    if not all(p.exists() for p in [chunks_path, vectors_path, meta_path]):
        raise FileNotFoundError(
            f"RAG index missing in {embeddings_dir}. "
            f"Run: python -m app.medini.ml.build_rag_index"
        )
    chunks_df = pd.read_parquet(chunks_path)
    vectors = np.load(vectors_path)
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    mask = _apply_filters(chunks_df, topic=topic, source=source, min_tokens=min_tokens)
    if not mask.any():
        return chunks_df.iloc[:0].assign(score=[])

    scores = np.zeros(len(chunks_df), dtype=np.float64)

    if mode in {"semantic", "hybrid"}:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(meta["model_name"])
        q_vec = model.encode(
            [query], convert_to_numpy=True, normalize_embeddings=True,
        )[0].astype(np.float32)
        # Cosine similarity (vectors already L2-normalised by the indexer)
        cos = vectors @ q_vec
        scores += cos
        if mode == "hybrid":
            # Add a normalised lexical bump (0.7 cos + 0.3 lex)
            lex = np.array([_lexical_score(query, t) for t in chunks_df["text"]])
            if lex.max() > 0:
                lex = lex / lex.max()
            scores = 0.7 * cos + 0.3 * lex
    elif mode == "lexical":
        scores = np.array([_lexical_score(query, t) for t in chunks_df["text"]])
    else:
        raise ValueError(f"unknown mode {mode!r}; expected semantic/hybrid/lexical")

    # Apply mask before sorting
    scores[~mask] = -1e9
    top_idx = np.argsort(-scores)[:top]
    result = chunks_df.iloc[top_idx].copy()
    result["score"] = scores[top_idx]
    result = result[result["score"] > -1e8]  # drop masked-out
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.search_rag",
        description="Semantic search over the knowledge library RAG index.",
    )
    parser.add_argument("--query", "-q", required=True, type=str)
    parser.add_argument(
        "--embeddings-dir", type=Path,
        default=Path("data/knowledge_library/embeddings"),
    )
    parser.add_argument(
        "--mode", choices=["semantic", "hybrid", "lexical"], default="hybrid",
    )
    parser.add_argument("--topic", type=str, default=None,
                        help="Filter to chunks tagged with this topic (e.g. dasha.vimshottari)")
    parser.add_argument("--source", type=str, default=None,
                        help="Substring match on source (e.g. bphs, lunarastro)")
    parser.add_argument("--min-tokens", type=int, default=30)
    parser.add_argument("--top", "-k", type=int, default=10)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    results = search(
        args.query, args.embeddings_dir,
        mode=args.mode, topic=args.topic, source=args.source,
        min_tokens=args.min_tokens, top=args.top,
    )
    if results.empty:
        print("No matches.")
        return 0
    print(f"\n=== {len(results)} match(es) for {args.query!r} (mode={args.mode}) ===\n")
    for _, row in results.iterrows():
        text = (row["text"] or "").strip().replace("\n", " ")
        snippet = text[:400] + ("..." if len(text) > 400 else "")
        print(f"[{row['chunk_id']}] score={row['score']:.4f}")
        print(f"  source: {row['source']}  ·  title: {(row.get('title') or '')[:80]}")
        if row.get("source_url"):
            print(f"  url:    {row['source_url']}")
        print(f"  path:   {row['local_path']}")
        print(f"  chunk:  {snippet}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
