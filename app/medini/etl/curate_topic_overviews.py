"""Auto-generate evidence-based topic overview pages from the RAG index.

For each leaf topic in ``topics.yaml`` this script:

  1. Queries the RAG index with the topic's name + description as the
     search query.
  2. Pulls the top-N most semantically-similar chunks across all 75+
     classical books and 314 YouTube videos.
  3. Aggregates them by source/author so the page shows which canonical
     texts cover the topic most heavily.
  4. Writes a single ``CURATED.md`` per topic with structured sections:
       - Canonical definition (from ``topics.yaml``)
       - Most-relevant passages (top excerpts with provenance)
       - Most-cited sources for this topic
       - Top-20 ranked artefacts (table)
       - Sibling cross-references (other leaves in the same category)

Unlike the auto-generated leaf pages from ``build_topic_indexes.py``
(which just list artefacts in source order), this curation page surfaces
the SEMANTICALLY most relevant material — so a user studying Vimshottari
sees the specific BPHS Ch.46-47 passages + Phaladeepika Ch.19-21 +
LunarAstro deep-dive videos all on one page, ranked by relevance to the
topic's canonical definition.

The output is evidence-based: every claim resolves to a chunk citation
with source URL + local path. No hand-written interpretation. The
"curation" comes from the structured, retrieval-ranked view.

Usage:
    python -m app.medini.etl.curate_topic_overviews
    python -m app.medini.etl.curate_topic_overviews --topic dasha.vimshottari
"""
from __future__ import annotations

import argparse
import logging
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from app.medini.ml.search_rag import search

logger = logging.getLogger(__name__)

# Tune the per-topic budgets here. Reasonable defaults:
_TOP_CHUNKS = 30          # top chunks pulled per topic for aggregation
_TOP_PASSAGES_SHOWN = 8   # how many full snippet passages to include
_TOP_SOURCES_SHOWN = 12   # how many sources in the "most-cited" table
_TOP_ARTEFACTS_SHOWN = 20 # how many in the ranked table
_SNIPPET_CHARS = 500


# --------------------------------------------------------------------------- #
# Topic query construction                                                     #
# --------------------------------------------------------------------------- #

def _build_query(category: str, leaf_name: str, leaf_meta: dict) -> str:
    """Build the RAG query string for a topic.

    Combines the leaf name + canonical description so semantic matching
    catches both the term and its operational meaning.
    """
    description = leaf_meta.get("description", "")
    return f"{leaf_name.replace('_', ' ')} {description}".strip()


# --------------------------------------------------------------------------- #
# Per-topic curation                                                           #
# --------------------------------------------------------------------------- #

def _format_passage(row: pd.Series, snippet_chars: int = _SNIPPET_CHARS) -> str:
    """Markdown-format a single chunk passage with provenance."""
    text = (row.get("text") or "").strip().replace("\n", " ")
    snippet = text[:snippet_chars] + ("..." if len(text) > snippet_chars else "")
    title = (row.get("title") or "").strip() or "(untitled)"
    source = row.get("source") or "?"
    src_url = row.get("source_url") or ""
    local = row.get("local_path") or ""
    score = row.get("score", 0.0)

    out = [
        f"### `{source}` — {title[:100]}",
        f"_score: {score:.3f}_",
        "",
        f"> {snippet}",
        "",
    ]
    links = []
    if src_url:
        links.append(f"[source]({src_url})")
    if local:
        links.append(f"[content]({local})")
    if links:
        out.append("  ·  ".join(links))
        out.append("")
    return "\n".join(out)


def _aggregate_by_source(results: pd.DataFrame) -> pd.DataFrame:
    """Aggregate chunk hits by source name; sort by total hits then max score."""
    agg = (
        results.assign(_n=1)
        .groupby("source", as_index=False)
        .agg(
            n_chunks=("_n", "sum"),
            max_score=("score", "max"),
            mean_score=("score", "mean"),
        )
        .sort_values(["n_chunks", "max_score"], ascending=[False, False])
    )
    return agg


def _top_artefacts(results: pd.DataFrame, top_n: int) -> pd.DataFrame:
    """Group chunks by artefact_id, take top score per artefact."""
    by_art = (
        results.sort_values("score", ascending=False)
        .groupby("artefact_id", as_index=False)
        .first()
        .sort_values("score", ascending=False)
        .head(top_n)
    )
    return by_art


def curate_topic(
    category: str,
    leaf_name: str,
    leaf_meta: dict,
    out_dir: Path,
    embeddings_dir: Path,
    library_root: Path,
    siblings: list[str],
) -> dict[str, int]:
    """Generate the CURATED.md for one topic."""
    query = _build_query(category, leaf_name, leaf_meta)
    try:
        results = search(
            query, embeddings_dir,
            mode="hybrid", top=_TOP_CHUNKS,
            min_tokens=30,
        )
    except FileNotFoundError as e:
        logger.error("RAG index missing: %s", e)
        return {"status": "no_index"}

    if results.empty:
        logger.warning("no matches for topic %s.%s", category, leaf_name)
        return {"status": "no_matches"}

    full_topic_path = f"{category}.{leaf_name}"
    description = leaf_meta.get("description", "(no description)")
    bphs_ref = leaf_meta.get("bphs_ref")

    # Try to make local_path relative to library_root for portability
    def _rel_path(local: str) -> str:
        try:
            return "../../" + Path(local).relative_to(library_root).as_posix()
        except Exception:
            return local

    lines: list[str] = [
        f"# Topic: `{full_topic_path}`",
        "",
        f"_{description}_",
    ]
    if bphs_ref and bphs_ref != "not_in_BPHS":
        lines.append(f"_Canonical reference_: **{bphs_ref}**")
    lines.extend([
        "",
        f"Auto-generated overview from RAG retrieval (query: _{query}_) — "
        f"{len(results)} top semantically-relevant chunks aggregated below.",
        "",
        "---",
        "",
    ])

    # Section 1: Top passages with full excerpt
    lines.append(f"## Most-relevant passages (top {min(_TOP_PASSAGES_SHOWN, len(results))})")
    lines.append("")
    for _, row in results.head(_TOP_PASSAGES_SHOWN).iterrows():
        # Rewrite local_path to be relative for the markdown link
        row = row.copy()
        row["local_path"] = _rel_path(row["local_path"])
        lines.append(_format_passage(row))
    lines.append("")

    # Section 2: Most-cited sources
    src_agg = _aggregate_by_source(results)
    lines.extend([
        "## Most-cited sources for this topic",
        "",
        "| Source | Chunks matching | Max score | Mean score |",
        "|---|---|---|---|",
    ])
    for _, row in src_agg.head(_TOP_SOURCES_SHOWN).iterrows():
        lines.append(
            f"| `{row['source']}` | {int(row['n_chunks'])} | "
            f"{row['max_score']:.3f} | {row['mean_score']:.3f} |"
        )
    lines.append("")

    # Section 3: Top ranked artefacts
    top_art = _top_artefacts(results, _TOP_ARTEFACTS_SHOWN)
    lines.extend([
        f"## Top {len(top_art)} artefacts by best-chunk score",
        "",
        "| # | Title | Source | Top chunk score | Open |",
        "|---|---|---|---|---|",
    ])
    for i, (_, row) in enumerate(top_art.iterrows(), 1):
        title_full = (row.get("title") or "").strip()
        local = _rel_path(row.get("local_path") or "")
        src_url = row.get("source_url") or ""
        open_cell = f"[local]({local})"
        if src_url:
            open_cell = f"[local]({local})  ·  [src]({src_url})"
        lines.append(
            f"| {i} | {title_full[:80]} | `{row['source']}` | "
            f"{row['score']:.3f} | {open_cell} |"
        )
    lines.append("")

    # Section 4: Sibling cross-references
    if siblings:
        lines.append("## Sibling topics in this category")
        lines.append("")
        for sib in sorted(siblings):
            if sib != leaf_name:
                lines.append(f"- [`{category}.{sib}`]({sib}.md) / [curated]({sib}_CURATED.md)")
        lines.append("")

    lines.extend([
        "---",
        "",
        "_Auto-generated by `app.medini.etl.curate_topic_overviews` "
        "from `data/knowledge_library/embeddings/` (RAG index). "
        "Re-run after corpus changes or RAG rebuild to refresh._",
        "",
    ])

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{leaf_name}_CURATED.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "status": "ok",
        "n_chunks": len(results),
        "n_sources": len(src_agg),
        "n_artefacts": len(top_art),
        "out_path": str(out_path),
    }


# --------------------------------------------------------------------------- #
# Driver                                                                       #
# --------------------------------------------------------------------------- #

def run(
    library_root: Path,
    topics_yaml: Path,
    embeddings_dir: Path,
    only_topic: str | None = None,
) -> dict[str, int]:
    taxonomy = yaml.safe_load(topics_yaml.read_text(encoding="utf-8")) or {}
    topics_dir = library_root / "topics"

    n_done = 0
    n_skipped = 0
    n_failed = 0

    for category, leaves in taxonomy.items():
        sibling_names = list(leaves.keys())
        for leaf_name, leaf_meta in leaves.items():
            full_path = f"{category}.{leaf_name}"
            if only_topic and full_path != only_topic:
                continue
            try:
                result = curate_topic(
                    category, leaf_name, leaf_meta,
                    out_dir=topics_dir / category,
                    embeddings_dir=embeddings_dir,
                    library_root=library_root,
                    siblings=sibling_names,
                )
                if result.get("status") == "ok":
                    n_done += 1
                    logger.info("[%s] %d chunks -> %s",
                                full_path, result["n_chunks"], result["out_path"])
                else:
                    n_skipped += 1
                    logger.info("[%s] skipped: %s", full_path, result.get("status"))
            except Exception as e:
                n_failed += 1
                logger.warning("[%s] failed: %s", full_path, e)

    return {"done": n_done, "skipped": n_skipped, "failed": n_failed}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.curate_topic_overviews",
        description="Auto-generate per-topic CURATED.md overviews from the RAG index.",
    )
    parser.add_argument(
        "--library-root", type=Path,
        default=Path("data/knowledge_library"),
    )
    parser.add_argument(
        "--topics-yaml", type=Path,
        default=Path("data/knowledge_library/topics.yaml"),
    )
    parser.add_argument(
        "--embeddings-dir", type=Path,
        default=Path("data/knowledge_library/embeddings"),
    )
    parser.add_argument(
        "--topic", type=str, default=None,
        help="Only process this single topic path (e.g. dasha.vimshottari)",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    stats = run(args.library_root, args.topics_yaml, args.embeddings_dir,
                only_topic=args.topic)
    print(
        f"Curation complete: done={stats['done']} "
        f"skipped={stats['skipped']} failed={stats['failed']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
