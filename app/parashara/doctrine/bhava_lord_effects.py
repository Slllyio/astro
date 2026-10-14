"""Effects of the bhava-lords in the houses (BPHS ch.24) — Parashara's predictive catalogue.

Chapter 24 gives, for each of the twelve house-LORDS, its effect in each of the twelve houses:
144 statements ("If the lord of the 3rd is in the 3rd, the native will be endowed with happiness
through co-born..."). This module INDEXES that chapter in place — it never transcribes the effect
text into code; it keys each (lord_house, in_house) to the real corpus line and reads the text from
the file. So every effect is citable to Parashara's own sloka, and the corpus stays the one source.

Parsing is anchored on the twelve block headers ("EFFECTS OF Nth LORD IN VARIOUS HOUSES"), which are
distinctive and OCR-clean; within a block the slokas are numbered continuously, so
``in_house = sloka_number - block_start + 1``. Six slokas whose NUMBER the OCR destroyed (a dropped
period, a letter-for-digit, a lost leading digit) are recovered by a small hand-verified repair
table — each line was read and confirmed to be the named sloka. Nothing is approximated: a pair we
cannot key returns None, it is never guessed.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Final, Mapping, Optional

from app.parashara.doctrine.sources import Citation, resolve_file

_WORK: Final[str] = "BPHS-24"

#: Ordinal words used in the block headers -> house number.
_ORD_WORD: Final[Mapping[str, int]] = {
    "ASCENDANT": 1, "1ST": 1, "FIRST": 1, "2ND": 2, "SECOND": 2, "3RD": 3, "THIRD": 3,
    "4TH": 4, "FOURTH": 4, "5TH": 5, "FIFTH": 5, "6TH": 6, "SIXTH": 6, "7TH": 7, "SEVENTH": 7,
    "8TH": 8, "EIGHTH": 8, "9TH": 9, "NINTH": 9, "10TH": 10, "TENTH": 10, "11TH": 11,
    "ELEVENTH": 11, "12TH": 12, "TWELFTH": 12}
_OALT: Final[str] = "|".join(sorted(_ORD_WORD, key=len, reverse=True))
_HDR_RE: Final[re.Pattern] = re.compile(
    r"^\s*(\d+)\.\s+EFFECTS OF (?:THE )?(" + _OALT + r")\s+LORD", re.I)
#: A sloka-number line start, tolerant of OCR separators (period, hyphen, colon, bare space).
_NUM_RE: Final[re.Pattern] = re.compile(r"^\s*(\d+)\s*[.\-):]\s")

#: Six slokas whose sloka-NUMBER the OCR destroyed — hand-verified to the real line (see docstring).
#: (lord_house, in_house) -> 1-indexed line in chapter_024.
_OCR_NUMBER_REPAIRS: Final[Mapping[tuple[int, int], int]] = {
    (3, 3): 338, (10, 2): 1648, (11, 3): 1877, (11, 11): 2028, (12, 3): 2063, (12, 4): 2070}


@dataclass(frozen=True)
class BhavaLordEffect:
    """One (lord-of-house, occupied-house) effect, cited to its BPHS ch.24 sloka."""
    lord_house: int          # 1..12 — the bhava whose LORD this is
    in_house: int            # 1..12 — the bhava the lord occupies
    text: str                # the sloka's effect, read verbatim from the corpus (Notes stripped)
    source: Citation         # BPHS-24 : the sloka's line


def _clean(raw: list[str]) -> str:
    """The sloka's effect prose: stop at the translator's Notes, drop OCR/Devanagari junk lines,
    strip the leading sloka number and any block-header prefix, collapse whitespace."""
    kept: list[str] = []
    for ln in raw:
        s = ln.strip()
        if not s:
            continue
        if re.match(r"note", s, re.I):           # translator commentary begins -> sloka body ended
            break
        letters = [c for c in s if c.isalpha()]
        if letters and sum(ord(c) < 128 for c in letters) / len(letters) < 0.6:
            continue                             # mostly-non-ASCII line = Devanagari OCR garbage
        kept.append(s)
    text = " ".join(kept)
    text = re.sub(r"^\s*\d+\s*[.\-):]?\s*", "", text)          # leading sloka number
    text = re.sub(r"^EFFECTS OF .*?:\s*", "", text, flags=re.I)  # block-header prefix (in_house 1)
    text = re.sub(r"\s+", " ", text).strip()
    # Slokas end on a period; anything after the last one is the trailing Devanagari verse rendered
    # as OCR gibberish. Trim it, but only when a substantial English sentence remains.
    cut = text.rfind(".")
    if cut >= 20:
        text = text[:cut + 1]
    return text


@lru_cache(maxsize=1)
def _index() -> dict[tuple[int, int], BhavaLordEffect]:
    path = resolve_file(_WORK)
    if path is None:
        return {}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()

    # 1) the twelve block headers -> (lord_house, block_start_sloka_num, line_index)
    blocks: list[tuple[int, int, int]] = []
    for i, ln in enumerate(lines):
        m = _HDR_RE.match(ln)
        if m:
            blocks.append((_ORD_WORD[m.group(2).upper()], int(m.group(1)), i))

    # 2) within each block, key numbered slokas by in_house = num - start + 1
    starts: dict[tuple[int, int], int] = {}     # (lord, in_house) -> line_index
    for b, (lord, start, i0) in enumerate(blocks):
        end = blocks[b + 1][2] if b + 1 < len(blocks) else len(lines)
        starts[(lord, 1)] = i0                   # the header line itself is in_house 1
        for j in range(i0 + 1, end):
            m = _NUM_RE.match(lines[j])
            if not m:
                continue
            in_house = int(m.group(1)) - start + 1
            if 2 <= in_house <= 12:
                starts.setdefault((lord, in_house), j)

    # 3) OCR-number repairs (line is 1-indexed in the file)
    for key, line1 in _OCR_NUMBER_REPAIRS.items():
        starts.setdefault(key, line1 - 1)

    # 4) each sloka's text spans to the next sloka start (in file order)
    ordered = sorted(starts.items(), key=lambda kv: kv[1])
    out: dict[tuple[int, int], BhavaLordEffect] = {}
    for n, (key, i0) in enumerate(ordered):
        end = ordered[n + 1][1] if n + 1 < len(ordered) else len(lines)
        out[key] = BhavaLordEffect(lord_house=key[0], in_house=key[1],
                                   text=_clean(lines[i0:end]), source=Citation(_WORK, i0 + 1))
    return out


def effect_of(lord_house: int, in_house: int) -> Optional[BhavaLordEffect]:
    """Parashara's effect for the lord of `lord_house` occupying `in_house` (BPHS ch.24), or None if
    the OCR left that pair unrecoverable (never guessed)."""
    if not (1 <= lord_house <= 12 and 1 <= in_house <= 12):
        raise ValueError("houses must be 1..12")
    return _index().get((lord_house, in_house))


def all_effects() -> Mapping[tuple[int, int], BhavaLordEffect]:
    """The whole ch.24 catalogue as {(lord_house, in_house): effect}."""
    return dict(_index())
