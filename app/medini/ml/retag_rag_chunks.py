"""Cheap re-tag: refresh the ``topics`` column in ``chunks.parquet`` from
the latest ``manifest.parquet`` WITHOUT re-embedding.

Use case: you updated ``_TOPIC_LEXICON`` in ``build_knowledge_manifest.py``,
re-ran the manifest, and now want the RAG search-time topic filter to
reflect the new tags. Re-running ``build_rag_index`` would re-embed all
~23k chunks (~10-30 min). This script just joins on ``artefact_id`` and
overwrites the topics column.

Vectors are untouched. Search behaviour is unchanged for queries without
``--topic`` filters; queries WITH ``--topic`` filters now see the enriched
tag set immediately.

Usage:
    python -m app.medini.ml.retag_rag_chunks
    python -m app.medini.ml.retag_rag_chunks --dry-run  # just report deltas
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def retag(
    manifest_path: Path, chunks_path: Path, *, dry_run: bool = False,
) -> dict[str, int]:
    """Update ``chunks.parquet`` topics from the latest manifest.

    Returns counts ``{n_chunks, n_changed, n_new_tags_added}`` for telemetry.
    """
    manifest = pd.read_parquet(manifest_path)
    chunks = pd.read_parquet(chunks_path)

    # Build artefact_id → topics map from the manifest. The manifest's `id`
    # column matches the chunks' `artefact_id` column (see build_rag_index
    # _Chunk construction).
    art_to_topics: dict[str, list[str]] = {
        str(row["id"]): list(row["topics"]) if row["topics"] is not None else []
        for _, row in manifest.iterrows()
    }

    n_changed = 0
    n_new_tags_added = 0
    new_topics_col: list[list[str]] = []
    for _, row in chunks.iterrows():
        art_id = str(row["artefact_id"])
        cur = list(row["topics"]) if row["topics"] is not None else []
        new = sorted(art_to_topics.get(art_id, cur))
        if sorted(cur) != new:
            n_changed += 1
            n_new_tags_added += max(0, len(new) - len(cur))
        new_topics_col.append(new)

    if dry_run:
        logger.info(
            "DRY RUN: would update %d/%d chunks (+%d tag additions)",
            n_changed, len(chunks), n_new_tags_added,
        )
        return {
            "n_chunks": len(chunks),
            "n_changed": n_changed,
            "n_new_tags_added": n_new_tags_added,
            "dry_run": 1,
        }

    chunks["topics"] = new_topics_col
    chunks.to_parquet(chunks_path, index=False)
    logger.info(
        "updated %d/%d chunks (+%d tag additions); wrote %s",
        n_changed, len(chunks), n_new_tags_added, chunks_path,
    )
    return {
        "n_chunks": len(chunks),
        "n_changed": n_changed,
        "n_new_tags_added": n_new_tags_added,
        "dry_run": 0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.retag_rag_chunks",
        description="Refresh chunks.parquet topics from manifest, no re-embed.",
    )
    parser.add_argument(
        "--manifest", type=Path,
        default=Path("data/knowledge_library/manifest.parquet"),
    )
    parser.add_argument(
        "--chunks", type=Path,
        default=Path("data/knowledge_library/embeddings/chunks.parquet"),
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    stats = retag(args.manifest, args.chunks, dry_run=args.dry_run)
    mode = "(dry-run)" if stats["dry_run"] else ""
    print(
        f"Re-tag {mode}: changed={stats['n_changed']}/{stats['n_chunks']} "
        f"new_tags=+{stats['n_new_tags_added']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
