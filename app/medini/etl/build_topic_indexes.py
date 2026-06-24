"""Auto-generate per-topic markdown indexes from the knowledge-library manifest.

Walks ``manifest.parquet`` + ``topics.yaml`` and emits a tree of
human-readable markdown files at ``data/knowledge_library/topics/``:

  topics/
  ├── README.md                         # master index of all top-level categories
  ├── primitives/
  │   ├── README.md                     # aggregates all primitives.* artefacts
  │   ├── planets.md                    # everything tagged primitives.planets
  │   ├── houses.md
  │   └── ...
  ├── dasha/
  │   ├── README.md
  │   ├── vimshottari.md
  │   └── ...
  └── ...

Each leaf page lists every artefact tagged with that topic, grouped by source
(classical vs video), with title + author + source_url + local path + a short
snippet. This is the navigation layer over the raw artefacts.

Generation is deterministic — re-running overwrites the indexes from the
current manifest. Hand edits to ``topics/*.md`` will be lost; if you want
curated notes, put them in a separate file (e.g. ``topics/dasha/notes.md``)
that the indexer doesn't touch.

Usage:
    python -m app.medini.etl.build_topic_indexes
"""
from __future__ import annotations

import argparse
import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

logger = logging.getLogger(__name__)


def _read_topics_yaml(path: Path) -> dict[str, dict[str, dict[str, str]]]:
    """Return the parsed topics taxonomy."""
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _topic_path_to_filename(topic: str) -> str:
    """Convert 'primitives.planets' → 'primitives/planets.md'."""
    parts = topic.split(".")
    return "/".join(parts) + ".md"


def _group_by_topic(df: pd.DataFrame) -> dict[str, list[pd.Series]]:
    """Return {topic_path: [artefact rows]} from the manifest."""
    by_topic: dict[str, list[pd.Series]] = defaultdict(list)
    for _, row in df.iterrows():
        topics = row.get("topics")
        if topics is None:
            continue
        # topics is a numpy array from parquet; iterate
        for t in list(topics):
            if t:
                by_topic[t].append(row)
    return by_topic


def _row_to_link(row: pd.Series, library_root: Path) -> str:
    """Format one artefact as a markdown link with provenance."""
    title = row.get("title") or "(untitled)"
    source = row.get("source") or "(unknown)"
    author = row.get("author") or row.get("channel") or ""
    source_url = row.get("source_url") or ""
    local = row.get("local_path") or ""
    n_words = row.get("n_words")
    dur = row.get("duration_seconds")
    quality = row.get("quality") or ""

    # Relative path from topics/ to source file for portability
    try:
        local_rel = Path(local).relative_to(library_root).as_posix()
        local_link = f"[content]({'../../' + local_rel})"
    except (ValueError, TypeError):
        local_link = ""

    meta_bits = []
    if author:
        meta_bits.append(str(author))
    if n_words and not pd.isna(n_words):
        meta_bits.append(f"{int(n_words):,} words")
    if dur and not pd.isna(dur):
        meta_bits.append(f"{int(dur) // 60}min")
    if quality and quality not in {"none", ""}:
        meta_bits.append(quality)
    meta_str = " · ".join(meta_bits) if meta_bits else ""

    url_link = f"[source]({source_url})" if source_url else ""

    return (
        f"- **{title}** — {source}"
        + (f" · {meta_str}" if meta_str else "")
        + (f" · {url_link}" if url_link else "")
        + (f" · {local_link}" if local_link else "")
    )


# --------------------------------------------------------------------------- #
# Per-topic page writers                                                       #
# --------------------------------------------------------------------------- #

def _write_leaf_page(
    topic_path: str,
    topic_meta: dict[str, str],
    artefacts: list[pd.Series],
    out_path: Path,
    library_root: Path,
) -> None:
    """Write a single ``primitives/planets.md`` style leaf index."""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Split artefacts by source type
    classical = [a for a in artefacts if a.get("content_type") == "classical_text"]
    videos = [a for a in artefacts if a.get("content_type") == "video_transcript"]
    other = [a for a in artefacts
             if a.get("content_type") not in {"classical_text", "video_transcript"}]

    leaf_slug = out_path.stem  # e.g. "vimshottari"
    curated_path = out_path.with_name(f"{leaf_slug}_CURATED.md")
    curated_link = (
        f"**See also:** [`{leaf_slug}_CURATED.md`](./{leaf_slug}_CURATED.md) "
        f"— RAG-curated overview with top semantically-relevant passages."
        if curated_path.exists() else None
    )

    lines = [
        f"# Topic: `{topic_path}`",
        "",
        f"_{topic_meta.get('description', '(no description)')}_",
    ]
    bphs_ref = topic_meta.get("bphs_ref")
    if bphs_ref:
        lines.append(f"_Canonical reference_: **{bphs_ref}**")
    lines.extend([
        "",
        f"**{len(artefacts)} artefact(s)** tagged with this topic.",
        "",
    ])
    if curated_link:
        lines.extend([curated_link, ""])

    if classical:
        # Sort by source for consistent display
        classical_sorted = sorted(classical, key=lambda r: (r.get("source") or "", r.get("title") or ""))
        lines.append(f"## Classical texts ({len(classical)})")
        lines.append("")
        for row in classical_sorted:
            lines.append(_row_to_link(row, library_root))
        lines.append("")

    if videos:
        # Sort videos by view count desc (most-watched first)
        videos_sorted = sorted(
            videos,
            key=lambda r: -(r.get("view_count") if not pd.isna(r.get("view_count")) else 0),
        )
        lines.append(f"## Videos ({len(videos)})")
        lines.append("")
        # Show top 50 by view count to keep page readable
        for row in videos_sorted[:50]:
            lines.append(_row_to_link(row, library_root))
        if len(videos_sorted) > 50:
            lines.append("")
            lines.append(f"_... and {len(videos_sorted) - 50} more videos. "
                         f"Filter the manifest directly for the full list._")
        lines.append("")

    if other:
        lines.append(f"## Other ({len(other)})")
        lines.append("")
        for row in other:
            lines.append(_row_to_link(row, library_root))
        lines.append("")

    lines.extend([
        "---",
        "",
        "_Auto-generated by `app.medini.etl.build_topic_indexes` from `manifest.parquet`._",
        "_Hand edits will be lost on re-run. Put curated notes in a separate file._",
    ])
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _write_category_readme(
    category: str,
    leaves: dict[str, dict[str, str]],
    artefact_counts: dict[str, int],
    out_path: Path,
) -> None:
    """Write the per-category README that links to all leaves."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Topic category: `{category}`",
        "",
        f"_{len(leaves)} sub-topics. Each leaf has a raw-artefacts index "
        f"and a RAG-curated overview when available._",
        "",
        "| Topic | Description | Artefacts | Curated | Canonical ref |",
        "|---|---|---|---|---|",
    ]
    cat_dir = out_path.parent
    for leaf_name, leaf_meta in sorted(leaves.items()):
        full_topic = f"{category}.{leaf_name}"
        n = artefact_counts.get(full_topic, 0)
        desc = leaf_meta.get("description", "")
        bphs_ref = leaf_meta.get("bphs_ref", "—")
        curated_cell = (
            f"[curated]({leaf_name}_CURATED.md)"
            if (cat_dir / f"{leaf_name}_CURATED.md").exists() else "—"
        )
        lines.append(
            f"| [`{full_topic}`]({leaf_name}.md) | {desc} | {n} | "
            f"{curated_cell} | {bphs_ref} |"
        )
    lines.extend([
        "",
        "---",
        "",
        "_Auto-generated by `app.medini.etl.build_topic_indexes`._",
    ])
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _count_curated(taxonomy: dict[str, dict[str, dict[str, str]]],
                   topics_dir: Path) -> int:
    """Count how many leaves have a *_CURATED.md generated."""
    n = 0
    for category, leaves in taxonomy.items():
        for leaf_name in leaves:
            if (topics_dir / category / f"{leaf_name}_CURATED.md").exists():
                n += 1
    return n


def _write_master_readme(
    taxonomy: dict[str, dict[str, dict[str, str]]],
    artefact_counts: dict[str, int],
    out_path: Path,
) -> None:
    """Write the top-level topics/README.md as a master navigation index."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    topics_dir = out_path.parent
    n_curated = _count_curated(taxonomy, topics_dir)
    n_total_leaves = sum(len(leaves) for leaves in taxonomy.values())

    lines = [
        "# Knowledge Library — Topic Navigation",
        "",
        "_Browse the library by classical Vedic-astrology topic. "
        "Each category page links to leaf topics; each leaf has both a raw-artefacts "
        "index AND a RAG-curated overview (when available) surfacing the "
        "semantically most-relevant passages from across the corpus._",
        "",
        f"**{n_curated} of {n_total_leaves} leaf topics have a RAG-curated "
        f"overview.** Curated pages aggregate top passages, most-cited sources, "
        f"and ranked artefacts for the topic. They live alongside the raw index "
        f"as `<leaf>_CURATED.md`.",
        "",
        "| Category | Sub-topics | Total artefacts |",
        "|---|---|---|",
    ]
    for category, leaves in sorted(taxonomy.items()):
        total = sum(
            artefact_counts.get(f"{category}.{leaf}", 0) for leaf in leaves
        )
        lines.append(
            f"| [`{category}`]({category}/README.md) | {len(leaves)} | {total} |"
        )

    lines.extend([
        "",
        "## How to use",
        "",
        "1. Pick a category above to see all sub-topics.",
        "2. Each leaf has two views: the raw artefact list (`<leaf>.md`) "
        "and the RAG-curated overview (`<leaf>_CURATED.md`).",
        "3. Each artefact entry links to both the original source URL and the "
        "local mirror (for offline reading + RAG retrieval).",
        "",
        "## Search",
        "",
        "Beyond topic browsing, you can do semantic / hybrid / lexical search "
        "over all chunks:",
        "",
        "```sh",
        "python -m app.medini.ml.search_rag --query \"marriage timing\" --top 10",
        "python -m app.medini.ml.search_rag --query \"shadbala\" --topic dasha.vimshottari",
        "python -m app.medini.ml.search_rag --query \"yogakaraka\" --source bphs",
        "```",
        "",
        "## Regenerate",
        "",
        "```sh",
        "# Raw index pages (cheap, deterministic)",
        "python -m app.medini.etl.build_topic_indexes",
        "",
        "# Curated overviews (re-queries the RAG index per topic; ~10 min)",
        "python -m app.medini.etl.curate_topic_overviews",
        "",
        "# Curated overview for a single topic",
        "python -m app.medini.etl.curate_topic_overviews --topic dasha.vimshottari",
        "```",
        "",
        "---",
        "",
        "_Auto-generated by `app.medini.etl.build_topic_indexes`._",
    ])
    out_path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Driver                                                                       #
# --------------------------------------------------------------------------- #

def run(library_root: Path, manifest_path: Path, topics_yaml: Path) -> dict[str, int]:
    df = pd.read_parquet(manifest_path)
    taxonomy = _read_topics_yaml(topics_yaml)
    logger.info("manifest=%d rows, taxonomy=%d top-level categories",
                len(df), len(taxonomy))

    by_topic = _group_by_topic(df)
    artefact_counts = {t: len(artefacts) for t, artefacts in by_topic.items()}

    topics_dir = library_root / "topics"
    topics_dir.mkdir(parents=True, exist_ok=True)

    # Write master README
    _write_master_readme(taxonomy, artefact_counts, topics_dir / "README.md")
    logger.info("wrote master README")

    n_leaf = 0
    n_category = 0
    for category, leaves in taxonomy.items():
        # Write per-category README
        cat_readme = topics_dir / category / "README.md"
        _write_category_readme(category, leaves, artefact_counts, cat_readme)
        n_category += 1
        # Write each leaf page
        for leaf_name, leaf_meta in leaves.items():
            full_topic = f"{category}.{leaf_name}"
            artefacts = by_topic.get(full_topic, [])
            leaf_path = topics_dir / category / f"{leaf_name}.md"
            _write_leaf_page(full_topic, leaf_meta, artefacts, leaf_path, library_root)
            n_leaf += 1

    return {
        "categories": n_category,
        "leaves": n_leaf,
        "total_artefact_tag_occurrences": sum(artefact_counts.values()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.build_topic_indexes",
        description="Auto-generate per-topic markdown indexes from the manifest.",
    )
    parser.add_argument(
        "--library-root", type=Path,
        default=Path("data/knowledge_library"),
    )
    parser.add_argument(
        "--manifest", type=Path,
        default=Path("data/knowledge_library/manifest.parquet"),
    )
    parser.add_argument(
        "--topics-yaml", type=Path,
        default=Path("data/knowledge_library/topics.yaml"),
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    stats = run(args.library_root, args.manifest, args.topics_yaml)
    print(
        f"Topic indexes built: {stats['categories']} categories, "
        f"{stats['leaves']} leaf pages, "
        f"{stats['total_artefact_tag_occurrences']} total artefact-topic links."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
