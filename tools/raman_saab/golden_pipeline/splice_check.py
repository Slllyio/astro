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


def flags(prose: str, lines: list[str], line: int, window: int = 80) -> list[str]:
    out: list[str] = []
    if _FOOTNOTE_INLINE.search(prose):
        out.append("footnote")
    if _HEADING_INLINE.search(prose):
        out.append("section_heading")
    if _ARTIFACT.search(prose):
        out.append("artifact")
    lo, hi = max(0, line - 1 - window), min(len(lines), line + window)
    if normalise(prose) not in normalise("\n".join(lines[lo:hi])) and not out:
        out.append("two_passage")
    return out
