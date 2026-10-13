"""Deterministic splice flags. Reuses the extractor's guard vocabulary (extract_htjah_goldens
`_SECTION_HEADING` / `_FOOTNOTE`), un-anchored because stored prose is single-line."""
from __future__ import annotations

import re
from typing import Final

from tools.raman_saab.extract_htjah_goldens import _FOOTNOTE, _SECTION_HEADING
from tools.raman_saab.golden_pipeline.sources import normalise

# The extractor patterns require a leading newline; drop it for single-line prose.
_HEADING_INLINE: Final = re.compile(_SECTION_HEADING.pattern.replace(r"\n\s*", r"(?:^|[.;:]\s+)", 1))
_FOOTNOTE_INLINE: Final = re.compile(_FOOTNOTE.pattern.replace(r"\n\s*", r"(?:^|\s)", 1))
_ARTIFACT: Final = re.compile(r"linked image cannot be displayed", re.I)


_HEAD_WORDS: Final = 8


def flags(prose: str, lines: list[str], line: int | list[int], window: int = 80) -> list[str]:
    """`line` may be one cited start or all cited starts (windows are pooled)."""
    out: list[str] = []
    if _FOOTNOTE_INLINE.search(prose):
        out.append("footnote")
    if _HEADING_INLINE.search(prose):
        out.append("section_heading")
    if _ARTIFACT.search(prose):
        out.append("artifact")
    starts = [line] if isinstance(line, int) else line
    text = normalise("\n".join("\n".join(lines[max(0, s - 1 - window):min(len(lines), s + window)])
                              for s in starts))
    # Stored prose is often a curated paraphrase; a splice STARTS verbatim but does not finish.
    head = " ".join(normalise(prose).split()[:_HEAD_WORDS])
    if not out and head in text and normalise(prose) not in text:
        out.append("two_passage")
    return out
