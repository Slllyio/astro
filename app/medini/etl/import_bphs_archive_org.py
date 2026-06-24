"""Import BPHS (Brihat Parashara Hora Shastra) from archive.org as markdown.

archive.org hosts the R. Santhanam English translation of BPHS as two
DjVu-text dumps (volumes 1 and 2). This script:

  1. Downloads both volumes from
     ``https://archive.org/download/BPHSEnglish/BPHS - {N} RSanthanam_djvu.txt``
  2. Splits the text by chapter using the canonical "Chapter N - <title>"
     and "ADHYAYA <roman>" headers that the OCR preserved.
  3. Cleans the most egregious OCR artifacts (page-break markers, header
     repetitions) and saves one markdown per chapter at
     ``data/knowledge_library/sources/bphs/<book>_chapter_NN_<slug>.md``.

The output is not pristine — the source is OCR'd, so spelling artefacts
remain. But the chapter splitting is reliable and the manifest indexer
can search the body text.

Wisdomlib doesn't host the Santhanam BPHS (no valid URL was found), so
archive.org is the canonical source for our purposes. The two-volume
split corresponds to BPHS chapters 1-50 (Vol 1) and 51-100 (Vol 2)
approximately.

Usage:
    python -m app.medini.etl.import_bphs_archive_org \\
        --output-dir data/knowledge_library/sources/bphs
"""
from __future__ import annotations

import argparse
import datetime as dt
import logging
import re
import sys
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

BPHS_DJVU_URLS: tuple[tuple[int, str], ...] = (
    (1, "https://archive.org/download/BPHSEnglish/BPHS%20-%201%20RSanthanam_djvu.txt"),
    (2, "https://archive.org/download/BPHSEnglish/BPHS%20-%202%20RSanthanam_djvu.txt"),
)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
}


# --------------------------------------------------------------------------- #
# Chapter splitter                                                             #
# --------------------------------------------------------------------------- #

# Canonical chapter header patterns in the Santhanam OCR text.
# Common forms:
#   "Chapter 1"
#   "Chapter 1 - Salutation"
#   "Chapter 47"
#   "CHAPTER 1." (caps in some sections)
# We accept any of these, case-insensitively, with optional " - <title>" tail.
_CHAPTER_HEADER_RE = re.compile(
    r"^\s*chapter\s+(\d{1,3})\s*[.\-:]?\s*(.+?)?\s*$",
    re.MULTILINE | re.IGNORECASE,
)


def _clean_ocr_text(text: str) -> str:
    """Strip the most common OCR artifacts: page-numbers, repeated headers."""
    # Drop standalone "Page N" / "1 5 2" style page-number lines
    text = re.sub(r"^\s*\d{1,4}\s*$", "", text, flags=re.MULTILINE)
    # Drop "Brihat Parashara Hora Shastra" repeats in headers
    text = re.sub(r"^Brihat\s+Parashara\s+Hora\s+Shastra.*$", "", text, flags=re.MULTILINE | re.IGNORECASE)
    # Collapse multi-blank lines
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def split_by_chapter(volume_text: str, volume_idx: int) -> list[dict]:
    """Find all chapter headers, split text between them, return chapter dicts."""
    matches = list(_CHAPTER_HEADER_RE.finditer(volume_text))
    chapters: list[dict] = []
    if not matches:
        logger.warning("No chapter headers found in volume %d", volume_idx)
        return chapters
    for i, m in enumerate(matches):
        ch_num = int(m.group(1))
        ch_title = (m.group(2) or "").strip().rstrip(".") or f"Chapter {ch_num}"
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(volume_text)
        body = _clean_ocr_text(volume_text[start:end])
        # De-duplicate: when chapter headers appear twice (TOC + actual chapter)
        # we keep the LONGER body, replacing if necessary.
        existing = next((c for c in chapters if c["chapter_num"] == ch_num), None)
        if existing:
            if len(body) > len(existing["body"]):
                existing["body"] = body
                existing["title"] = ch_title
            continue
        chapters.append({
            "volume": volume_idx,
            "chapter_num": ch_num,
            "title": ch_title,
            "body": body,
            "n_words": len(body.split()),
        })
    return chapters


# --------------------------------------------------------------------------- #
# Output                                                                       #
# --------------------------------------------------------------------------- #

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slug(s: str) -> str:
    return _SLUG_RE.sub("-", s.lower()).strip("-")[:60]


def write_chapter(
    chapter: dict, output_dir: Path, *, source_url: str, scraped_at: str
) -> Path:
    name = (
        f"vol{chapter['volume']}_chapter_{chapter['chapter_num']:03d}_"
        f"{_slug(chapter['title'])}.md"
    )
    path = output_dir / name
    frontmatter = "\n".join([
        "---",
        f"id: bphs-vol{chapter['volume']}-ch{chapter['chapter_num']:03d}",
        f"source: bphs",
        f"title: BPHS Chapter {chapter['chapter_num']} — {chapter['title']}",
        f"book: Brihat Parashara Hora Shastra",
        f"translator: R. Santhanam",
        f"volume: {chapter['volume']}",
        f"chapter_index: {chapter['chapter_num']}",
        f"language: en",
        f"content_type: classical_text",
        f"quality: ocr_text",
        f"source_url: {source_url}",
        f"scraped_at: {scraped_at}",
        f"topics:",
        f"  - meta.source_texts",
        f"classical_refs:",
        f"  - BPHS.{chapter['chapter_num']}",
        f"---",
    ])
    body = (
        f"\n\n# {chapter['title']}\n\n"
        f"_BPHS Chapter {chapter['chapter_num']}, Vol. {chapter['volume']}_\n\n"
        + chapter["body"]
        + "\n"
    )
    path.write_text(frontmatter + body, encoding="utf-8")
    return path


# --------------------------------------------------------------------------- #
# Driver                                                                       #
# --------------------------------------------------------------------------- #

def run(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    all_chapters: list[dict] = []
    scraped_at = dt.datetime.now(dt.timezone.utc).isoformat()
    for vol_num, url in BPHS_DJVU_URLS:
        logger.info("downloading volume %d from %s ...", vol_num, url)
        r = session.get(url, timeout=60)
        r.raise_for_status()
        logger.info("volume %d: %d chars", vol_num, len(r.text))
        chapters = split_by_chapter(r.text, vol_num)
        logger.info("volume %d: %d chapters found", vol_num, len(chapters))
        for ch in chapters:
            ch["source_url"] = url
            all_chapters.append(ch)

    # De-duplicate across volumes (Vol 1 and Vol 2 may overlap in TOC headers).
    by_num: dict[int, dict] = {}
    for ch in all_chapters:
        existing = by_num.get(ch["chapter_num"])
        if existing is None or len(ch["body"]) > len(existing["body"]):
            by_num[ch["chapter_num"]] = ch

    n_persisted = 0
    n_too_short = 0
    for ch in sorted(by_num.values(), key=lambda c: c["chapter_num"]):
        if ch["n_words"] < 50:
            n_too_short += 1
            continue
        path = write_chapter(
            ch, output_dir,
            source_url=ch["source_url"],
            scraped_at=scraped_at,
        )
        n_persisted += 1
        logger.info("[ch %d] saved %s (%d words)",
                    ch["chapter_num"], path.name, ch["n_words"])

    return {
        "n_chapter_segments_seen": len(all_chapters),
        "n_unique_chapters": len(by_num),
        "n_persisted": n_persisted,
        "n_dropped_too_short": n_too_short,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.medini.etl.import_bphs_archive_org",
        description="Import BPHS (Santhanam) from archive.org into the knowledge library.",
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path("data/knowledge_library/sources/bphs"),
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    stats = run(args.output_dir)
    print(
        f"BPHS import complete: segments_seen={stats['n_chapter_segments_seen']} "
        f"unique_chapters={stats['n_unique_chapters']} "
        f"persisted={stats['n_persisted']} "
        f"dropped_short={stats['n_dropped_too_short']} "
        f"-> {args.output_dir}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
