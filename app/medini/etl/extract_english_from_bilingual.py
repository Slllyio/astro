"""Extract English-only paragraphs from Sanskrit/Hindi bilingual texts.

Several scraped sources contain English COMMENTARY interleaved with
Sanskrit/Hindi/Tamil original text:

  * vidyamadhaviyam — Horary classical, mostly Sanskrit with English commentary
  * (future) lal_kitab_vol1-3 — Urdu original with possible English notes
  * (future) bhrigu_samhita variants — Hindi original

The existing shloka harvester skips these because the OCR-noisy mixed-
script content breaks its English-sentence detection. This module pre-
processes the markdown to KEEP ONLY English-language paragraphs, then
writes the cleaned text back to a sibling directory the shloka harvester
can consume normally.

## Algorithm

For each markdown file:
  1. Split on blank lines into paragraphs.
  2. For each paragraph, compute the ratio of ASCII Latin letters to
     total characters. ASCII >= 0.85 = likely English.
  3. Skip paragraphs with < 0.85 ASCII ratio (likely Sanskrit/Hindi/Tamil).
  4. Skip paragraphs < 50 chars (likely fragments / verse markers).
  5. Concatenate surviving paragraphs into the output.

Output goes to ``data/knowledge_library/sources/<slug>_english/`` with
the same chapter file structure, so the standard shloka harvester can
pick it up via the SHLOKA_SOURCES registry.

## What this is NOT

Not a true language detector — uses ASCII ratio as a proxy. Misses
English text with many Sanskrit transliteration words (e.g. 'sutra'
'graha' 'lagna' are common; 'jyotirvit' is unusual). The 0.85 threshold
is permissive enough to keep most prose but skip Devanagari/Tamil.

Usage:
    python -m app.medini.etl.extract_english_from_bilingual --source vidyamadhaviyam
    python -m app.medini.etl.extract_english_from_bilingual --source all
"""
from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Final

logger = logging.getLogger(__name__)


# Sources known to be Sanskrit/Hindi/Tamil-dominant with English commentary
BILINGUAL_SOURCES: Final[tuple[str, ...]] = (
    "vidyamadhaviyam",
    # Future candidates if scraped: lal_kitab_vol1-3 (Urdu), various
    # Sanskrit-Hindi editions
)


def _ascii_ratio(text: str) -> float:
    """Ratio of ASCII Latin chars to total non-whitespace chars."""
    if not text:
        return 0.0
    chars = [c for c in text if not c.isspace()]
    if not chars:
        return 0.0
    ascii_count = sum(1 for c in chars if c.isascii() and (c.isalpha() or c in ".,;:?!()'\"-—"))
    return ascii_count / len(chars)


def filter_to_english_paragraphs(
    text: str, *, min_ascii_ratio: float = 0.85, min_chars: int = 50,
) -> str:
    """Keep only English-dominant paragraphs from mixed-script text."""
    paragraphs = text.split("\n\n")
    kept: list[str] = []
    for p in paragraphs:
        p_stripped = p.strip()
        if len(p_stripped) < min_chars:
            continue
        if _ascii_ratio(p_stripped) < min_ascii_ratio:
            continue
        kept.append(p_stripped)
    return "\n\n".join(kept)


def process_source(
    knowledge_dir: Path, source_slug: str, *, dry_run: bool = False,
) -> tuple[int, int]:
    """Process all markdown files in a source dir; write English-only copy.

    Returns (n_files_processed, n_files_with_english_content).
    """
    src_dir = knowledge_dir / source_slug
    out_slug = f"{source_slug}_english"
    out_dir = knowledge_dir / out_slug

    if not src_dir.is_dir():
        logger.warning("Source dir missing: %s", src_dir)
        return (0, 0)

    md_files = sorted(src_dir.glob("*.md"))
    if not md_files:
        logger.warning("No .md files in %s", src_dir)
        return (0, 0)

    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    n_processed = 0
    n_with_content = 0
    total_input_lines = 0
    total_output_lines = 0
    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8", errors="ignore")
        # Preserve frontmatter (between --- ... ---)
        if text.startswith("---"):
            end = text.find("\n---\n", 4)
            if end > 0:
                frontmatter = text[: end + 5]
                body = text[end + 5 :]
            else:
                frontmatter = ""
                body = text
        else:
            frontmatter = ""
            body = text

        english_only = filter_to_english_paragraphs(body)
        total_input_lines += body.count("\n")
        total_output_lines += english_only.count("\n")
        n_processed += 1
        if not english_only:
            continue
        n_with_content += 1
        # Update frontmatter slug
        new_frontmatter = frontmatter.replace(
            f"source: {source_slug}", f"source: {out_slug}"
        ).replace(
            f"id: {source_slug}-", f"id: {out_slug}-"
        )
        out_file = out_dir / md_file.name
        out_text = new_frontmatter + english_only + "\n"
        if not dry_run:
            out_file.write_text(out_text, encoding="utf-8")

    pct = (total_output_lines / total_input_lines * 100) if total_input_lines else 0
    logger.info(
        "%s: processed %d files, %d retained English content "
        "(%d lines in, %d lines kept, %.1f%% retained)",
        source_slug, n_processed, n_with_content,
        total_input_lines, total_output_lines, pct,
    )
    return (n_processed, n_with_content)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--knowledge-dir", type=Path,
                        default=Path("data/knowledge_library/sources"))
    parser.add_argument("--source", type=str, default="all",
                        help="Source slug to process, or 'all'.")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(name)s | %(message)s")

    sources = BILINGUAL_SOURCES if args.source == "all" else (args.source,)
    for src in sources:
        process_source(args.knowledge_dir, src, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
