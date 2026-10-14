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
    """anchored + toc-only + illegible + beyond-scan == 300, no overlaps.

    Updated 2026-08-08 (conscious, same-commit): the COMPLETE edition arrived from the user's
    Drive, so the span cap is 300 when that source is present — the truncated-scan era's 162
    applies only if the complete copy ever vanishes."""
    anchored, unanchored = inv.parse_combinations()
    nums = {n for n, *_ in anchored}
    toc_only = {n for n, _ in unanchored}
    assert not nums & toc_only
    last = 300 if inv.SOURCE_COMPLETE.is_file() else 162
    illegible = set(range(1, last + 1)) - nums - toc_only
    beyond = set(range(last + 1, 301))
    assert len(nums) + len(toc_only) + len(illegible) + len(beyond) == 300


def test_known_anchors_hold():
    """Spot-pins against the text: Gajakesari opens the body, and with the complete edition
    present the anchors must reach deep into the far half (the truncated scans stopped at
    162 — reaching past it is exactly what the acquisition changed)."""
    anchored, _ = inv.parse_combinations()
    by_num = {n: (name, line) for n, name, line in anchored}
    assert 1 in by_num and "GAJAKESARI" in by_num[1][0].upper()
    if inv.SOURCE_COMPLETE.is_file():
        assert max(by_num) >= 290, "the complete edition must anchor the far half"
        assert 296 in by_num, "Nishturabhashi (296) was read directly during ingest"
    else:
        assert max(by_num) == 162


def test_encoded_join_sees_the_registry():
    """The 'encoded' bucket joins by normalized NAME across all three 3HC-family tags
    (updated 2026-08-09 when the legacy line-span join was found blind to 3HCH/3HCC and
    undercounting 28-vs-84). If the registry grows, the inventory must see it without edits."""
    names = inv.encoded_yoga_names()
    assert names, "no 3HC-family-cited yogas found — the cross-reference regex broke"
    assert "gajakesari" in names            # legacy 3HC cite
    assert "nishturabhashi" in names        # 3HCC cite (the far half)
    assert "lakshmi" in names               # 3HCH cite (tranche 2)
