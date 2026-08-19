"""Quote verification — the compendium's honesty gate.

Every rule record carries a verbatim OCR quote. This module proves the
quote actually appears in the pinned source text and assigns its printed
page mechanically via the page map. A quote that cannot be found is
REJECTED (``quote_verified: false``) and never evaluated — extraction
agents cannot invent doctrine.

Matching is OCR-tolerant but deterministic, applying the *same*
normalization to quote and source:

  * casefold
  * every hyphen (incl. soft hyphen U+00AD and OCR's ``¬``) joins what it
    separates, consuming any following whitespace — so line-break
    hyphenation (``combi- nation``), inline compounds (``ill-disposed``)
    and a transcriber's re-joined form all normalize identically
  * every other non-alphanumeric run collapses to a single space
  * a small table of archaic/OCR spelling variants is canonicalized
    (matching only — the stored quote and its sha256 stay verbatim)

The normalized source keeps a char-offset map back to the original text,
so a match yields the original offset, and the offset yields the page.
"""
from __future__ import annotations

import dataclasses

from app.medini.doctrine.tools.page_map import PageMap

# Applied identically to normalized quote and normalized source, in order.
# Keep entries lowercase-alphanumeric (they run after normalization).
SPELLING_VARIANTS: tuple[tuple[str, str], ...] = (
    ("thrikona", "trikona"),
    ("karacamsa", "karakamsa"),
    ("navamsha", "navamsa"),
    ("rasee", "rasi"),
    ("dassa", "dasa"),
)

_HYPHENS = "­‐‑‒–—¬-"


@dataclasses.dataclass(frozen=True)
class VerifyResult:
    found: bool
    offset: int | None  # char offset of the match in the ORIGINAL text
    page: int | None


def normalize(text: str) -> str:
    """Normalized form used for matching (no offset map)."""
    norm, _ = normalize_with_map(text)
    return norm


def normalize_with_map(text: str) -> tuple[str, list[int]]:
    """Return (normalized text, offsets) where offsets[i] is the original
    char offset that produced normalized char i."""
    folded = text.casefold()
    # Pass 1: char-level edit stream with provenance.
    chars: list[str] = []
    offs: list[int] = []
    i = 0
    n = len(folded)
    while i < n:
        ch = folded[i]
        if ch in _HYPHENS:
            # Join across the hyphen, consuming any whitespace after it —
            # identical result whether the hyphenation kept its line break
            # ("combi- nation"), was re-joined ("combi-nation"), or is a
            # legitimate compound ("ill-disposed").
            i += 1
            while i < n and folded[i].isspace():
                i += 1
            continue
        chars.append(ch)
        offs.append(i)
        i += 1
    # Pass 2: collapse non-alphanumeric runs to single spaces.
    out: list[str] = []
    out_offs: list[int] = []
    pending_space = False
    for ch, off in zip(chars, offs):
        if ch.isalnum() and ch.isascii():
            if pending_space and out:
                out.append(" ")
                out_offs.append(off)
            out.append(ch)
            out_offs.append(off)
            pending_space = False
        else:
            pending_space = True
    norm = "".join(out)
    # Pass 3: canonicalize spelling variants (rebuilding the offset map).
    for old, new in SPELLING_VARIANTS:
        if old not in norm:
            continue
        rebuilt: list[str] = []
        rebuilt_offs: list[int] = []
        pos = 0
        while True:
            hit = norm.find(old, pos)
            if hit == -1:
                rebuilt.append(norm[pos:])
                rebuilt_offs.extend(out_offs[pos:])
                break
            rebuilt.append(norm[pos:hit])
            rebuilt_offs.extend(out_offs[pos:hit])
            rebuilt.append(new)
            rebuilt_offs.extend([out_offs[hit]] * len(new))
            pos = hit + len(old)
        norm = "".join(rebuilt)
        out_offs = rebuilt_offs
    return norm, out_offs


def verify_quote(
    quote: str,
    source_text: str,
    page_map: PageMap | None = None,
    *,
    folio_at: str = "top",
) -> VerifyResult:
    """Locate ``quote`` in ``source_text``; assign its printed page."""
    return SourceVerifier(source_text, page_map, folio_at=folio_at).verify(quote)


class SourceVerifier:
    """Verify many quotes against one source without re-normalizing it.

    ``folio_at`` describes where the book prints its page number ("top"
    for running heads, "bottom" for standalone folios at the page foot) —
    it decides whether an offset resolves to the previous or next anchor.
    """

    def __init__(self, source_text: str, page_map: PageMap | None = None,
                 *, folio_at: str = "top"):
        self._norm, self._offs = normalize_with_map(source_text)
        self._page_map = page_map
        self._folio_at = folio_at

    def verify(self, quote: str) -> VerifyResult:
        norm_quote = normalize(quote)
        if not norm_quote:
            return VerifyResult(found=False, offset=None, page=None)
        hit = self._norm.find(norm_quote)
        if hit == -1:
            return VerifyResult(found=False, offset=None, page=None)
        orig = self._offs[hit]
        page = (self._page_map.page_for_offset(orig, folio_at=self._folio_at)
                if self._page_map else None)
        return VerifyResult(found=True, offset=orig, page=page)

    def stamp(self, rule: dict) -> dict:
        """Return a copy of ``rule`` with quote_verified/page set from this
        source. Page is only overwritten when the map yields one."""
        res = self.verify(rule["quote"])
        out = dict(rule)
        out["quote_verified"] = res.found
        if res.found and res.page is not None:
            out["page"] = res.page
        return out
