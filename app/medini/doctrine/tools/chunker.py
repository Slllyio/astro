"""Chapter chunking for extraction sweeps.

Splits a source text into chapter chunks so extraction agents work one
chapter at a time and the coverage manifest can prove no chapter was
silently skipped. Chapter heads in these OCR dumps are lines like
``CHAPTER XVII`` (Roman numerals, OCR-mangled ones like ``XXIU``
tolerated); Three Hundred Important Combinations instead numbers its yogas
(``1. Gajakesari Yoga``), so the pattern is parameterizable.
"""
from __future__ import annotations

import dataclasses
import re

# Roman numeral with common OCR confusions (U for II, 1 for I, etc.).
CHAPTER_PATTERN = r"^\s*CHAPTER\s+([IVXLC1U]+)\b.*$"


@dataclasses.dataclass(frozen=True)
class Chunk:
    label: str        # e.g. "XVII" (chapter) or "42" (yoga number)
    title: str        # first non-blank line after the head, best-effort
    start: int        # char offset of the head line
    end: int          # char offset one past the chunk (start of next head)

    def slice(self, text: str) -> str:
        return text[self.start:self.end]


def chunk_chapters(text: str, pattern: str = CHAPTER_PATTERN) -> list[Chunk]:
    """Split ``text`` at every line matching ``pattern`` (group 1 = label).

    The text before the first head (front matter) is not a chunk; sweeps
    that need it (title-page provenance) read it directly.
    """
    rx = re.compile(pattern, re.MULTILINE)
    heads: list[tuple[int, int, str]] = []  # (start, end_of_line, label)
    for m in rx.finditer(text):
        heads.append((m.start(), m.end(), m.group(1)))
    chunks: list[Chunk] = []
    for i, (start, line_end, label) in enumerate(heads):
        end = heads[i + 1][0] if i + 1 < len(heads) else len(text)
        title = _first_prose_line(text[line_end:end])
        chunks.append(Chunk(label=label, title=title, start=start, end=end))
    return chunks


def _first_prose_line(body: str, max_scan: int = 2000) -> str:
    for line in body[:max_scan].splitlines():
        stripped = line.strip()
        if len(stripped) >= 4 and any(c.isalpha() for c in stripped):
            return stripped
    return ""
