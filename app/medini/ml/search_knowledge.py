"""Simple BM25/keyword search over the knowledge library manifest.

Until we have embeddings, lexical search is enough. This CLI tool lets you:

  - filter by topic: ``--topic dasha.vimshottari``
  - filter by source: ``--source lunarastro/youtube``
  - filter by quality: ``--quality manual_captions``
  - text query: ``--query "marriage timing"`` (matches in title and content body)
  - show top-N: ``--top 10``

For each match it prints title + source + duration/length + first matching
snippet (~200 chars) + local path so you can ``Read`` the full transcript.

Usage:
    python -m app.medini.ml.search_knowledge --topic dasha.vimshottari
    python -m app.medini.ml.search_knowledge --query "saturn dasha results" --top 5
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def _content_snippet(local_path: str, query: str, window: int = 200) -> str | None:
    """Return a snippet from the artefact body containing ``query`` (case-insens)."""
    try:
        text = Path(local_path).read_text(encoding="utf-8")
    except Exception:
        return None
    if not query:
        return text[:window].replace("\n", " ")
    idx = text.lower().find(query.lower())
    if idx < 0:
        return None
    start = max(0, idx - window // 2)
    end = min(len(text), idx + len(query) + window // 2)
    return ("..." if start > 0 else "") + text[start:end].replace("\n", " ") + (
        "..." if end < len(text) else ""
    )


def _score(row: pd.Series, query: str) -> float:
    """Tiny score: occurrences of query in title (×3) + content (×1)."""
    if not query:
        return 1.0
    q = query.lower()
    title = (row.get("title") or "").lower()
    title_hits = title.count(q)
    try:
        body = Path(row["local_path"]).read_text(encoding="utf-8").lower()
        body_hits = body.count(q)
    except Exception:
        body_hits = 0
    return 3.0 * title_hits + body_hits


def search(
    manifest_path: Path,
    *,
    topic: str | None = None,
    source: str | None = None,
    quality: str | None = None,
    query: str | None = None,
    top: int = 10,
) -> pd.DataFrame:
    df = pd.read_parquet(manifest_path)

    if topic:
        df = df[df["topics"].apply(lambda ts: topic in (ts or []))].copy()
    if source:
        df = df[df["source"].fillna("").str.contains(source, na=False)].copy()
    if quality:
        df = df[df["quality"] == quality].copy()

    if query:
        df["score"] = df.apply(lambda r: _score(r, query), axis=1)
        df = df[df["score"] > 0].sort_values("score", ascending=False)
    else:
        df["score"] = 0.0
        # Default ordering: longest transcripts first (more content)
        df = df.sort_values("n_words", ascending=False)

    return df.head(top)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.ml.search_knowledge",
        description="Search the knowledge library manifest by topic / source / quality / query.",
    )
    parser.add_argument(
        "--manifest", type=Path,
        default=Path("data/knowledge_library/manifest.parquet"),
    )
    parser.add_argument("--topic", type=str, default=None,
                        help="Filter by exact topic path (e.g. dasha.vimshottari)")
    parser.add_argument("--source", type=str, default=None,
                        help="Substring of source path")
    parser.add_argument("--quality", type=str, default=None,
                        choices=["manual_captions", "auto_captions", "written_article", "none"])
    parser.add_argument("--query", type=str, default=None,
                        help="Free-text query (case-insensitive substring)")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    if not args.manifest.exists():
        print(f"ERROR manifest not found at {args.manifest}. "
              f"Run: python -m app.medini.etl.build_knowledge_manifest")
        return 2

    results = search(
        args.manifest,
        topic=args.topic,
        source=args.source,
        quality=args.quality,
        query=args.query,
        top=args.top,
    )
    if results.empty:
        print("No matches.")
        return 0
    print(f"\n=== {len(results)} match(es) ===\n")
    for _, row in results.iterrows():
        dur = row.get("duration_seconds")
        dur_str = f"  {int(dur)//60}min" if dur and not pd.isna(dur) else ""
        views = row.get("view_count")
        views_str = f"  {int(views):,}views" if views and not pd.isna(views) else ""
        topics_raw = row.get("topics")
        topics = list(topics_raw) if topics_raw is not None else []
        topics_str = "  topics: " + ", ".join(topics[:4]) if topics else ""
        print(f"[{row['id']}]  {row['source']}{dur_str}{views_str}")
        print(f"  {(row.get('title') or '')[:100]}")
        print(f"  url: {row.get('source_url')}")
        print(f"  path: {row['local_path']}")
        if topics_str:
            print(topics_str)
        if args.query:
            snippet = _content_snippet(row["local_path"], args.query)
            if snippet:
                print(f"  match: {snippet}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
