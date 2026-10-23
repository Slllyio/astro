"""Apply the reviewed, line-preserving OCR corrections to the local Raman book corpus.

The corpus (``data/knowledge_library/sources``) is git-ignored, so corrections travel as data:
``tools/raman_saab/ocr_corrections.json`` holds one entry per corrected line with the exact
``before`` and ``after`` text. Applying is idempotent and refuses to guess: a line that matches
neither text is reported and left alone, and no line is ever added or removed, so every
``WORK:line`` citation keeps pointing at the same passage.

After applying, re-lock the sources (the file hashes change, the line numbers do not):

    UPDATE_SOURCE_LOCK=1 py -3.12 -m pytest tests/raman_saab/doctrine/test_source_lock.py -q

Usage:
    py -3.12 -m tools.raman_saab.apply_ocr_corrections --check
    py -3.12 -m tools.raman_saab.apply_ocr_corrections --apply
"""
from __future__ import annotations

import argparse
import json
import logging
from collections import defaultdict
from pathlib import Path

from app.raman_saab.doctrine.sources import _CORPUS

logger = logging.getLogger(__name__)

CORRECTIONS_PATH: Path = Path(__file__).resolve().parent / "ocr_corrections.json"


def load_corrections(path: Path = CORRECTIONS_PATH) -> list[dict]:
    """The committed correction entries: ``file`` (relative to the corpus), ``line``, ``before``, ``after``."""
    return json.loads(path.read_text(encoding="utf-8"))["corrections"]


def plan(corpus: Path = _CORPUS, corrections: list[dict] | None = None) -> dict[str, list]:
    """Classify every entry against the files on disk: pending, applied, mismatch or missing."""
    status: dict[str, list] = defaultdict(list)
    by_file: dict[str, list[dict]] = defaultdict(list)
    for c in corrections if corrections is not None else load_corrections():
        by_file[c["file"]].append(c)
    for rel, entries in by_file.items():
        path = corpus / rel
        if not path.is_file():
            status["missing"].extend(entries)
            continue
        lines = path.read_bytes().decode("utf-8").split("\n")
        for c in entries:
            current = lines[c["line"] - 1].removesuffix("\r") if c["line"] <= len(lines) else None
            if current == c["after"]:
                status["applied"].append(c)
            elif current == c["before"]:
                status["pending"].append(c)
            else:
                status["mismatch"].append(c)
    return status


def apply(corpus: Path = _CORPUS, corrections: list[dict] | None = None) -> int:
    """Rewrite every pending line in place; returns the number of lines changed."""
    pending = plan(corpus, corrections)["pending"]
    by_file: dict[str, list[dict]] = defaultdict(list)
    for c in pending:
        by_file[c["file"]].append(c)
    for rel, entries in by_file.items():
        path = corpus / rel
        raw = path.read_bytes().decode("utf-8")
        lines = raw.split("\n")
        n = len(lines)
        for c in entries:
            # Keep the file's own line ending: some books are CRLF, and a mixed file would
            # count lines differently in readers that split on a lone CR.
            cr = "\r" if lines[c["line"] - 1].endswith("\r") else ""
            lines[c["line"] - 1] = c["after"] + cr
        assert len(lines) == n, f"line count changed in {rel}"
        path.write_bytes("\n".join(lines).encode("utf-8"))
    return len(pending)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="report status without writing")
    mode.add_argument("--apply", action="store_true", help="rewrite pending lines in place")
    args = ap.parse_args()
    status = plan()
    for key in ("applied", "pending", "mismatch", "missing"):
        logger.info("%-8s %d", key, len(status[key]))
    for c in status["mismatch"]:
        logger.warning("mismatch (left alone): %s:%d", c["file"], c["line"])
    if args.apply:
        logger.info("changed %d line(s); now re-lock with UPDATE_SOURCE_LOCK=1", apply())


if __name__ == "__main__":
    main()
