"""Mechanical char-offset -> printed-page maps for archive.org OCR dumps.

`_djvu.txt` OCR output preserves the printed page number of most pages as a
standalone integer line (the running folio). This module turns those lines
into a page map so every extracted quote can carry a *mechanically derived*
page citation — pages are assigned by lookup, never guessed by a model.

Method:
  1. Scan the text for candidate lines that contain only an integer
     (optionally flanked by OCR noise like ``*`` or ``.``).
  2. Keep the longest near-monotonic chain of candidates: each accepted
     anchor must be strictly greater than its predecessor and within
     ``max_jump`` of it (folio numbers advance by 1-2 per OCR page; a large
     jump is almost always a year, a table figure, or a chart position).
     Chain selection is a DP over candidates, so isolated noise — a year in
     the front matter, a stray table figure — cannot poison the map.
  3. The map is a sorted list of ``(char_offset, page)`` anchors;
     ``page_for_offset`` returns the page of the last anchor at or before
     the offset (i.e. the page whose folio line most recently opened).

The acceptance rate (``monotonic_fraction``) doubles as a QC signal: an
English book scan yields a long accepted chain; a garbled scan (the hpa2.txt
Hindi-OCR precedent) yields almost none.
"""
from __future__ import annotations

import bisect
import dataclasses
import json
import re
from pathlib import Path

# Standalone integer line, tolerating leading/trailing OCR specks.
STANDALONE_FOLIO = r"^[\s*.\-—•']{0,4}(\d{1,4})[\s*.\-—•']{0,4}$"
_CANDIDATE_RE = re.compile(STANDALONE_FOLIO)


@dataclasses.dataclass(frozen=True)
class PageAnchor:
    offset: int  # char offset of the folio line's first character
    page: int


@dataclasses.dataclass
class PageMap:
    anchors: list[PageAnchor]
    candidates_seen: int

    @property
    def max_page(self) -> int:
        return self.anchors[-1].page if self.anchors else 0

    @property
    def monotonic_fraction(self) -> float:
        """Accepted candidates / all standalone-integer lines seen."""
        if not self.candidates_seen:
            return 0.0
        return len(self.anchors) / self.candidates_seen

    def page_for_offset(self, offset: int, *, folio_at: str = "top") -> int | None:
        """Printed page containing ``offset``.

        ``folio_at="top"``: a folio line opens its page (running heads),
        so the page is the last anchor at or before the offset — None
        before the first anchor. ``folio_at="bottom"``: a folio line
        closes its page (standalone page numbers at the foot, the usual
        style in these prints), so the page is the first anchor at or
        after the offset — None after the last anchor.
        """
        keys = [a.offset for a in self.anchors]
        if folio_at == "bottom":
            i = bisect.bisect_left(keys, offset)
            return self.anchors[i].page if i < len(self.anchors) else None
        i = bisect.bisect_right(keys, offset) - 1
        return self.anchors[i].page if i >= 0 else None

    def to_json(self) -> dict:
        return {
            "anchors": [[a.offset, a.page] for a in self.anchors],
            "candidates_seen": self.candidates_seen,
            "max_page": self.max_page,
            "monotonic_fraction": round(self.monotonic_fraction, 4),
        }

    @classmethod
    def from_json(cls, data: dict) -> "PageMap":
        return cls(
            anchors=[PageAnchor(o, p) for o, p in data["anchors"]],
            candidates_seen=data["candidates_seen"],
        )


def build_page_map(
    text: str,
    *,
    max_jump: int = 8,
    min_page: int = 1,
    max_page: int = 800,
    lookback: int = 400,
    patterns: tuple[str, ...] = (STANDALONE_FOLIO,),
) -> PageMap:
    """Build a near-monotonic page map from folio-number lines.

    ``patterns`` are regexes (one integer capture group each) describing how
    the book prints its folio; the default is a standalone integer line, and
    books with running heads (e.g. HTJAH's "50 How to Judge a Horoscope" /
    "Concerning the Seventh House 51") add their own. ``max_jump`` bounds
    the folio advance between consecutive accepted anchors: OCR loses some
    folio lines, so gaps of a few pages are normal, but a jump like
    137 -> 1962 is a date, not a folio. ``lookback`` caps the DP predecessor
    search; real folio lines are dense, so the true predecessor is always
    among the recent candidates. ``max_page`` excludes candidates that no
    printed Raman book can reach — without it, a year-by-year ayanamsa
    table (1826, 1827, …) forms a perfectly monotonic fake chain.
    """
    compiled = [re.compile(p) for p in patterns]
    cands: list[PageAnchor] = []
    offset = 0
    for line in text.splitlines(keepends=True):
        for rx in compiled:
            m = rx.search(line)
            if m:
                page = int(m.group(1))
                if min_page <= page <= max_page:
                    cands.append(PageAnchor(offset, page))
                break
        offset += len(line)

    n = len(cands)
    if n == 0:
        return PageMap(anchors=[], candidates_seen=0)

    # Longest chain with page[j] < page[i] <= page[j] + max_jump.
    dp = [1] * n
    prev = [-1] * n
    for i in range(n):
        pi = cands[i].page
        for j in range(i - 1, max(-1, i - 1 - lookback), -1):
            pj = cands[j].page
            if pj < pi <= pj + max_jump and dp[j] + 1 > dp[i]:
                dp[i] = dp[j] + 1
                prev[i] = j
    best = max(range(n), key=lambda i: dp[i])
    chain: list[PageAnchor] = []
    while best != -1:
        chain.append(cands[best])
        best = prev[best]
    chain.reverse()
    return PageMap(anchors=chain, candidates_seen=n)


def save_page_map(pmap: PageMap, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(pmap.to_json(), indent=1), encoding="utf-8")


def load_page_map(path: Path) -> PageMap:
    return PageMap.from_json(json.loads(path.read_text(encoding="utf-8")))
