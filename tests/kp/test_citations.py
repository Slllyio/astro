"""Every KP quote must appear verbatim (whitespace-collapsed) in its Reader's source file.

The book texts are gitignored (``data/``), so these run where the library is present (the
project PC) or when ``KP_READER<n>`` (n = 1, 3, 4, 5, 6) point at the files; otherwise skip.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

from app.kp.citations import CITATIONS, PAGE_SOURCES, SOURCE_FILE


def _find(env: str, default: str) -> Path | None:
    for cand in (os.environ.get(env), default):
        if cand and Path(cand).is_file():
            return Path(cand)
    return None


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


R3 = _find("KP_READER3", SOURCE_FILE)
PAGED = {src: _find(f"KP_READER{src[-1]}", path) for src, path in PAGE_SOURCES.items()}


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


@pytest.mark.parametrize("source", sorted(PAGE_SOURCES))
class TestPagedCitations:
    def test_every_quote_is_on_its_page(self, source: str) -> None:
        """Each quote occurs on its page marker (or runs on into the next page)."""
        path = PAGED[source]
        if path is None:
            pytest.skip(f"{source} text not present (data/ is gitignored)")
        text = path.read_text(encoding="utf-8")
        pages = {int(m.group(1)): m.end() for m in re.finditer(r"<!-- page (-?\d+) \(scan \d+\) -->", text)}
        order = sorted(pages)
        cites = [c for c in CITATIONS.values() if c.source == source]
        assert cites, f"no citations for {source}"
        for c in cites:
            p = int(c.lines.removeprefix("p."))
            i = order.index(p)
            end = pages[order[i + 2]] if i + 2 < len(order) else len(text)
            seg = re.sub(r"<!-- page .*? -->", " ", text[pages[p]:end])
            assert _norm(c.quote) in _norm(seg), c.key


def test_every_citation_source_is_known() -> None:
    """Each citation names Reader 3 or one of the page-cited Readers."""
    assert {c.source for c in CITATIONS.values()} <= {"KPR3", *PAGE_SOURCES}
