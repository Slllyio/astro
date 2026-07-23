"""Reversibility guard for the soul-destiny experiment.

The Jaimini citation firewall is deliberately lifted on the `soul-destiny-experiment` branch (see
book_registry.py). This test asserts the loud `EXPERIMENT-BRANCH-ONLY (soul-destiny)` sentinel is
present, so anyone deleting the experiment is forced to acknowledge it, and confirms the unlock
actually makes JAIMINI + JS citable and on-disk-resolvable. NEVER MERGE THIS BRANCH TO MAIN
without re-review.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.raman_saab.doctrine import book_registry, sources
from app.raman_saab.doctrine.sources import Citation

_SENTINEL = "EXPERIMENT-BRANCH-ONLY (soul-destiny)"
_REGISTRY = (Path(__file__).resolve().parents[3]
             / "app" / "raman_saab" / "doctrine" / "book_registry.py")


def test_experiment_sentinel_present_in_registry() -> None:
    """The unlock is sentinel-marked so `git grep` enumerates the whole blast radius."""
    assert _SENTINEL in _REGISTRY.read_text(encoding="utf-8")


def test_jaimini_and_js_are_live_and_citable() -> None:
    """The firewall is lifted: JAIMINI-* and JS-* resolve to a live BookEntry (were None before)."""
    assert book_registry.entry_for("JAIMINI-49") is not None
    assert book_registry.entry_for("JS-1") is not None


def test_out_of_scope_books_stay_firewalled() -> None:
    """The mechanism is intact: PRASNA/MUHURTHA/VARSHA remain NON-citable."""
    assert book_registry.entry_for("PRASNA-1") is None
    assert book_registry.entry_for("MUHURTHA-1") is None
    assert book_registry.entry_for("VARSHA-1") is None


def test_jaimini_citations_verify_on_disk() -> None:
    """With the corpus present, a JAIMINI-49 / JS-1 citation physically resolves + verifies."""
    for work in ("JAIMINI-49", "JS-1"):
        if sources._resolve_file(work) is None:
            pytest.skip(f"corpus for {work} not vendored in this checkout")
        assert sources.verify(Citation(work, 1))
