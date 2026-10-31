"""Every KP quote must appear verbatim (whitespace-collapsed) in the Reader 3 source file.

The book text is gitignored (``data/``), so this runs where the library is present (the
project PC) or when ``KP_READER3`` points at the file; otherwise it skips.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

from app.kp.citations import CITATIONS, SOURCE_FILE


def _source() -> Path | None:
    for cand in (os.environ.get("KP_READER3"), SOURCE_FILE):
        if cand and Path(cand).is_file():
            return Path(cand)
    return None


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


@pytest.mark.skipif(_source() is None, reason="KP Reader 3 text not present (data/ is gitignored)")
class TestCitations:
    def test_every_quote_is_at_its_lines(self) -> None:
        """Each quote occurs within ±3 lines of its cited line range."""
        raw = _source().read_text(encoding="utf-8").splitlines()
        for c in CITATIONS.values():
            a, _, b = c.lines.partition("-")
            window = _norm(" ".join(raw[int(a) - 4:int(b or a) + 3]))
            assert _norm(c.quote) in window, c.key
