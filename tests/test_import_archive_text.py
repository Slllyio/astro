"""Paired test for the classical-text importer's chapter splitter.

Focus: the `monotonic` real-heading split added 2026-08-21 for BPHS. BPHS OCR repeats the chapter
number as a per-page running header ("Chapter 7 93"), and a stray "Chapter N" page-header can be
followed by a capitalised body line that looks like a real heading. Without the monotonic guard the
splitter truncates a chapter at the first such false match (this is why the old import left BPHS
ch.6 a single page). These are pure-function, offline checks — no network.
"""
from __future__ import annotations

import re

from app.medini.etl.import_archive_text import (
    _BPHS_HEADER_REGEX, split_by_chapter)

_RX = re.compile(_BPHS_HEADER_REGEX, re.MULTILINE | re.IGNORECASE)

# Synthetic BPHS-shaped OCR: real headings ("Chapter N\n\nTitle"), a running page-header
# ("Chapter 6 88" — same-line page number), and an out-of-sequence false heading
# ("Chapter 1\n\nBandhu") sitting INSIDE chapter 7.
_SAMPLE = """\
Chapter 6

The Sixteen Divisions

body six alpha
Chapter 6 88
body six beta after a running page-header

Chapter 7

Divisional Consideration

body seven alpha

Chapter 1

Bandhu

body seven omega still chapter seven

Chapter 8

Aspects Of The Signs

body eight
"""


def _by_num(text: str, *, monotonic: bool) -> dict[int, dict]:
    chs = split_by_chapter(text, header_regex=_RX, monotonic=monotonic)
    return {c["chapter_num"]: c for c in chs}


def test_running_header_does_not_start_a_new_chapter():
    """'Chapter 6 88' (page number on the same line) is not a real heading and must not split
    chapter 6 — the two-line regex simply never matches it."""
    chs = _by_num(_SAMPLE, monotonic=True)
    assert set(chs) == {6, 7, 8}
    assert "body six beta" in chs[6]["body"], "running-header page number wrongly split ch.6"


def test_monotonic_rejects_out_of_sequence_false_heading():
    """The stray 'Chapter 1 / Bandhu' inside chapter 7 is out of sequence (1 < 7), so monotonic
    skips it and chapter 7's body runs whole through to chapter 8 — including text AFTER the false
    heading. Without monotonic, ch.7 would truncate at 'Bandhu'."""
    chs = _by_num(_SAMPLE, monotonic=True)
    assert 1 not in chs, "out-of-sequence false heading leaked in as chapter 1"
    assert "body seven alpha" in chs[7]["body"]
    assert "body seven omega" in chs[7]["body"], "false heading truncated chapter 7"


def test_non_monotonic_would_truncate():
    """Guard-the-guard: with monotonic OFF the same false heading DOES break chapter 7 (proving the
    monotonic flag is what fixes it, not the regex alone)."""
    chs = _by_num(_SAMPLE, monotonic=False)
    assert 1 in chs, "expected the false 'Chapter 1' to be captured when monotonic is off"
    assert "body seven omega" not in chs[7]["body"], "expected truncation without monotonic"
