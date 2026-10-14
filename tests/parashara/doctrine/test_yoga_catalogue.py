"""Yoga catalogue (BPHS ch.35-42) — cited index of the yoga chapters.

Verifies the catalogue spans all eight yoga chapters, that Raja/Dhana/penury chapters are covered
(they lack clean detectors), that every catalogued sloka's citation resolves, and that the cited
grep works.
"""
from __future__ import annotations

import pytest

from app.parashara.doctrine import yoga_catalogue as Y
from app.parashara.doctrine.sources import verify


class TestCatalogue:
    def test_spans_all_yoga_chapters(self):
        cat = Y.catalogue()
        assert set(cat) == set(Y.YOGA_CHAPTERS.values())

    def test_raja_dhana_penury_covered(self):
        assert len(Y.slokas_for(39)) >= 20      # Raja yogas
        assert len(Y.slokas_for(41)) >= 12      # Dhana yogas
        assert len(Y.slokas_for(42)) >= 1       # penury

    def test_every_catalogued_citation_resolves(self):
        for slokas in Y.catalogue().values():
            for s in slokas:
                assert verify(s.source), (s.work, s.number, s.source)

    def test_not_a_yoga_chapter_raises(self):
        with pytest.raises(ValueError):
            Y.slokas_for(24)


class TestFind:
    def test_cited_grep_finds_wealth(self):
        hits = Y.find(r"affluent|wealthy|riches")
        assert hits
        assert all(verify(h.source) for h in hits)
