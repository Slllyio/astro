"""Every KP quote must appear verbatim (whitespace-collapsed) in its Reader's source file.

The book texts are gitignored (``data/``), so these run where the library is present (the
project PC) or when ``KP_READER3`` / ``KP_READER4`` point at the files; otherwise they skip.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

from app.kp.citations import CITATIONS, READER4_FILE, SOURCE_FILE


def _find(env: str, default: str) -> Path | None:
    for cand in (os.environ.get(env), default):
        if cand and Path(cand).is_file():
            return Path(cand)
    return None


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


R3 = _find("KP_READER3", SOURCE_FILE)
R4 = _find("KP_READER4", READER4_FILE)


@pytest.mark.skipif(R3 is None, reason="KP Reader 3 text not present (data/ is gitignored)")
class TestReader3Citations:
    def test_every_quote_is_at_its_lines(self) -> None:
        """Each Reader 3 quote occurs within ±3 lines of its cited line range."""
        raw = R3.read_text(encoding="utf-8").splitlines()
        for c in CITATIONS.values():
            if c.source != "KPR3":
                continue
            a, _, b = c.lines.partition("-")
            window = _norm(" ".join(raw[int(a) - 4:int(b or a) + 3]))
            assert _norm(c.quote) in window, c.key


@pytest.mark.skipif(R4 is None, reason="KP Reader 4 text not present (data/ is gitignored)")
class TestReader4Citations:
    def test_every_quote_is_on_its_page(self) -> None:
        """Each Reader 4 quote occurs on its printed page (or runs on into the next one)."""
        text = R4.read_text(encoding="utf-8")
        pages = {int(m.group(1)): m.end() for m in re.finditer(r"<!-- page (-?\d+) \(scan \d+\) -->", text)}
        order = sorted(pages)
        for c in CITATIONS.values():
            if c.source != "KPR4":
                continue
            p = int(c.lines.removeprefix("p."))
            nxt = order[order.index(p) + 2] if order.index(p) + 2 < len(order) else None
            seg = text[pages[p]: (pages[nxt] if nxt is not None else len(text))]
            seg = re.sub(r"<!-- page .*? -->", " ", seg)
            assert _norm(c.quote) in _norm(seg), c.key
