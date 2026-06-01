"""Build a RAG retrieval index over the knowledge library.

Chunks every artefact into 200-400 token windows at paragraph boundaries,
embeds each chunk with a multilingual sentence-transformer (handles both
English classical texts and Hindi LunarAstro transcripts), and persists:

  data/knowledge_library/embeddings/
  ├── chunks.parquet          # one row per chunk: chunk_id, artefact_id, text, source, topics
  └── vectors.npy             # (n_chunks, 384) float32 embedding matrix

Multilingual model choice: `paraphrase-multilingual-MiniLM-L12-v2`. This is
384-dim, ~118MB, supports 50+ languages including Hindi, and is the
canonical small multilingual model for semantic search.

Chunking strategy:
  - For markdown: split at blank-line paragraph boundaries.
  - For YouTube transcripts: split at sentence-like breaks (period + space)
    since transcripts often have no paragraph structure.
  - Greedily pack paragraphs/sentences into chunks of ~300 tokens (max 400).
  - Carry source-frontmatter metadata (topics, source_url, title) on every chunk.

Resume support: if embeddings exist, only re-embed chunks whose source
artefact's sha256 has changed (detected via the existing manifest's sha256
column). For now, we always re-embed everything when the script is run —
the manifest's sha256 is recomputed on every build_knowledge_manifest run.

Usage:
    python -m app.medini.ml.build_rag_index \\
        --manifest data/knowledge_library/manifest.parquet \\
        --output-dir data/knowledge_library/embeddings \\
        [--model paraphrase-multilingual-MiniLM-L12-v2] \\
        [--batch-size 32] [--max-tokens 400]
"""
from __future__ import annotations

import argparse
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Chunker                                                                      #
# --------------------------------------------------------------------------- #

_FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)


def _strip_frontmatter(text: str) -> str:
    return _FRONTMATTER_RE.sub("", text, count=1).strip()


def _approx_tokens(text: str) -> int:
    """Cheap whitespace + punctuation-based token estimate.

    Good enough for chunk sizing (we want ~300 tokens, not exactly 300).
    For sentence-transformers' tokenizer the actual count is within ~20%.
    """
    return max(1, len(text.split()))


def _split_paragraphs(text: str) -> list[str]:
    """Markdown-aware paragraph splitter."""
    # Strip headers (single-line)
    paragraphs = re.split(r"\n\s*\n", text)
    return [p.strip() for p in paragraphs if p.strip()]


def _split_sentences(text: str) -> list[str]:
    """Fallback splitter for transcripts: split on period+space + line breaks."""
    sents = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [s.strip() for s in sents if s.strip()]


def chunk_text(text: str, *, max_tokens: int = 400, target_tokens: int = 300) -> list[str]:
    """Split a text body into chunks at paragraph/sentence boundaries.

    Greedy packing: accumulate paragraphs (or sentences for unparagraphed
    texts) until ``target_tokens`` is exceeded; emit; restart. A single
    paragraph above ``max_tokens`` is itself split at sentence boundaries.
    """
    text = text.strip()
    if not text:
        return []

    paragraphs = _split_paragraphs(text)
    # Heuristic: if avg paragraph is very long (single-blob transcript),
    # treat the whole thing as sentences instead.
    if paragraphs and _approx_tokens(paragraphs[0]) > max_tokens * 2:
        paragraphs = _split_sentences(text)

    chunks: list[str] = []
    buffer: list[str] = []
    buffer_tokens = 0
    for p in paragraphs:
        p_tokens = _approx_tokens(p)
        if p_tokens > max_tokens:
            # Flush buffer first
            if buffer:
                chunks.append("\n\n".join(buffer))
                buffer = []
                buffer_tokens = 0
            # Recurse on the big paragraph as sentences
            sents = _split_sentences(p)
            sub_buf: list[str] = []
            sub_tok = 0
            for s in sents:
                s_t = _approx_tokens(s)
                if sub_tok + s_t > target_tokens and sub_buf:
                    chunks.append(" ".join(sub_buf))
                    sub_buf = [s]
                    sub_tok = s_t
                else:
                    sub_buf.append(s)
                    sub_tok += s_t
            if sub_buf:
                chunks.append(" ".join(sub_buf))
            continue

        if buffer_tokens + p_tokens > target_tokens and buffer:
            chunks.append("\n\n".join(buffer))
            buffer = [p]
            buffer_tokens = p_tokens
        else:
            buffer.append(p)
            buffer_tokens += p_tokens
    if buffer:
        chunks.append("\n\n".join(buffer))
    return chunks


# --------------------------------------------------------------------------- #
# Chunk-row builder                                                            #
# --------------------------------------------------------------------------- #

@dataclass(frozen=True, slots=True)
class _Chunk:
    chunk_id: str
    artefact_id: str
    chunk_idx: int
    text: str
    n_tokens: int
    source: str
    title: str
    topics: list[str]
    source_url: str
    local_path: str


def _chunks_for_artefact(row: pd.Series, max_tokens: int, target_tokens: int) -> list[_Chunk]:
    """Read the artefact body from disk and chunk it."""
    local = row.get("local_path")
    if not local:
        return []
    p = Path(local)
    if not p.exists():
        return []
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []
    body = _strip_frontmatter(text) if text.startswith("---") else text
    pieces = chunk_text(body, max_tokens=max_tokens, target_tokens=target_tokens)

    topics_raw = row.get("topics")
    topics = list(topics_raw) if topics_raw is not None else []
    return [
        _Chunk(
            chunk_id=f"{row['id']}#{i}",
            artefact_id=str(row["id"]),
            chunk_idx=i,
            text=piece,
            n_tokens=_approx_tokens(piece),
            source=str(row.get("source") or ""),
            title=str(row.get("title") or ""),
            topics=topics,
            source_url=str(row.get("source_url") or ""),
            local_path=str(local),
        )
        for i, piece in enumerate(pieces)
    ]


# --------------------------------------------------------------------------- #
# Embedding                                                                    #
# --------------------------------------------------------------------------- #

def embed_chunks(
    chunks: list[_Chunk],
    *,
    model_name: str,
    batch_size: int = 32,
) -> np.ndarray:
    """Return an (n_chunks, embedding_dim) float32 matrix."""
    from sentence_transformers import SentenceTransformer

    logger.info("loading model %s (one-time download if needed)", model_name)
    model = SentenceTransformer(model_name)
    texts = [c.text for c in chunks]
    logger.info("embedding %d chunks in batches of %d ...", len(texts), batch_size)
    vectors = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )
    return vectors.astype(np.float32, copy=False)


# --------------------------------------------------------------------------- #
# Driver                                                                       #
# --------------------------------------------------------------------------- #

def run(
    manifest_path: Path,
    output_dir: Path,
    *,
    model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
    batch_size: int = 32,
    max_tokens: int = 400,
    target_tokens: int = 300,
    limit_artefacts: int | None = None,
) -> dict[str, int]:
    df = pd.read_parquet(manifest_path)
    if limit_artefacts is not None:
        df = df.head(limit_artefacts)
    logger.info("manifest has %d artefacts; chunking ...", len(df))

    all_chunks: list[_Chunk] = []
    for _, row in df.iterrows():
        chunks = _chunks_for_artefact(row, max_tokens=max_tokens, target_tokens=target_tokens)
        all_chunks.extend(chunks)
    logger.info("produced %d chunks across %d artefacts", len(all_chunks), len(df))

    if not all_chunks:
        raise RuntimeError("no chunks produced — check manifest paths")

    vectors = embed_chunks(all_chunks, model_name=model_name, batch_size=batch_size)
    assert vectors.shape[0] == len(all_chunks), \
        f"embed count {vectors.shape[0]} != chunk count {len(all_chunks)}"

    output_dir.mkdir(parents=True, exist_ok=True)
    # Write chunks parquet
    chunks_df = pd.DataFrame([
        {
            "chunk_id": c.chunk_id,
            "artefact_id": c.artefact_id,
            "chunk_idx": c.chunk_idx,
            "text": c.text,
            "n_tokens": c.n_tokens,
            "source": c.source,
            "title": c.title,
            "topics": c.topics,
            "source_url": c.source_url,
            "local_path": c.local_path,
        }
        for c in all_chunks
    ])
    chunks_path = output_dir / "chunks.parquet"
    chunks_df.to_parquet(chunks_path, index=False)
    vectors_path = output_dir / "vectors.npy"
    np.save(vectors_path, vectors)
    # Write small meta file for the search CLI to know the model
    meta_path = output_dir / "meta.json"
    import json as _json
    meta_path.write_text(_json.dumps({
        "model_name": model_name,
        "embedding_dim": int(vectors.shape[1]),
        "n_chunks": int(vectors.shape[0]),
        "n_artefacts": int(len(df)),
        "max_tokens": max_tokens,
        "target_tokens": target_tokens,
    }, indent=2))

    logger.info("wrote %s + %s + %s", chunks_path, vectors_path, meta_path)
    return {
        "n_artefacts": int(len(df)),
        "n_chunks": int(len(all_chunks)),
        "embedding_dim": int(vectors.shape[1]),
        "total_tokens": int(chunks_df["n_tokens"].sum()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.build_rag_index",
        description="Build a RAG retrieval index from the knowledge library manifest.",
    )
    parser.add_argument(
        "--manifest", type=Path,
        default=Path("data/knowledge_library/manifest.parquet"),
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path("data/knowledge_library/embeddings"),
    )
    parser.add_argument(
        "--model", type=str,
        default="paraphrase-multilingual-MiniLM-L12-v2",
        help="HuggingFace sentence-transformer model name.",
    )
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--max-tokens", type=int, default=400)
    parser.add_argument("--target-tokens", type=int, default=300)
    parser.add_argument("--limit-artefacts", type=int, default=None,
                        help="Process only first N artefacts (for smoke testing).")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    stats = run(
        args.manifest, args.output_dir,
        model_name=args.model,
        batch_size=args.batch_size,
        max_tokens=args.max_tokens,
        target_tokens=args.target_tokens,
        limit_artefacts=args.limit_artefacts,
    )
    print(
        f"RAG index built: artefacts={stats['n_artefacts']} "
        f"chunks={stats['n_chunks']} dim={stats['embedding_dim']} "
        f"total_tokens={stats['total_tokens']:,}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
