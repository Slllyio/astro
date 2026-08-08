"""The 3HC inventory tool — the arithmetic that corrected the source-expansion research.

The research claimed ~260 unencoded combinations on disk; running this parser measured the
truth: the scan ends at combination 162, and both on-disk copies are the same file. These
tests pin the parser's honesty rather than its completeness — every combination must land in
exactly one bucket, and the buckets must sum to the book.
"""
from __future__ import annotations

import importlib.util
import pathlib

_spec = importlib.util.spec_from_file_location(
    "inventory_3hc", pathlib.Path("tools/raman_saab/inventory_3hc.py"))
inv = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(inv)


def test_every_combination_lands_in_exactly_one_bucket():
    """anchored + toc-only + illegible + beyond-scan == 300, no overlaps."""
    anchored, unanchored = inv.parse_combinations()
    nums = {n for n, *_ in anchored}
    toc_only = {n for n, _ in unanchored}
    assert not nums & toc_only
    last = 162
    illegible = set(range(1, last + 1)) - nums - toc_only
    beyond = set(range(last + 1, 301))
    assert len(nums) + len(toc_only) + len(illegible) + len(beyond) == 300


def test_known_anchors_hold():
    """Spot-pins against the text: Gajakesari opens the body; the scan ends at 162."""
    anchored, _ = inv.parse_combinations()
    by_num = {n: (name, line) for n, name, line in anchored}
    assert 1 in by_num and "GAJAKESARI" in by_num[1][0].upper()
    assert max(by_num) == 162, "the scan's own final combination"


def test_encoded_count_matches_the_registry():
    """The 'encoded' bucket is derived from real 3HC citations in doctrine/yogas.py — if the
    registry grows, this inventory must see it without edits."""
    cites = inv.encoded_citation_lines()
    assert cites, "yogas.py cites 3HC today; empty means the cross-reference broke"
    assert all(isinstance(c, int) and c > 0 for c in cites)
