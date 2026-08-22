"""Effects of the houses (BPHS ch.12-23) — the per-house cited sloka index.

This archive.org scan's ch.12-23 are OCR-damaged essays, so the index is honestly PARTIAL: the
tests pin a coverage FLOOR (not a fixed count — a cleaner source should only raise it), that every
indexed citation resolves, that houses are correctly mapped to chapters, and that the clean topic
headings are captured. Nothing is asserted to be complete that is not.
"""
from __future__ import annotations

import pytest

from app.parashara.doctrine import bhava_effects as BE
from app.parashara.doctrine.sources import Citation, verify


class TestCoverage:
    def test_all_twelve_houses_indexed(self):
        cov = BE.coverage()
        assert set(cov) == set(range(1, 13))
        assert all(n >= 1 for n in cov.values())          # every house yields at least one sloka

    def test_total_sloka_floor(self):
        """A floor, not an exact count — a cleaner OCR source should only raise it."""
        assert sum(BE.coverage().values()) >= 100

    def test_every_citation_resolves(self):
        for effs in BE.all_bhava_effects().values():
            for e in effs:
                assert verify(e.source), (e.house, e.sloka, e.source)


class TestMapping:
    def test_house_maps_to_chapter(self):
        """House H is chapter H+11: the citations for house 1 point at BPHS-12, house 12 at BPHS-23."""
        assert BE.effects_for_house(1)[0].source.work == "BPHS-12"
        assert BE.effects_for_house(12)[0].source.work == "BPHS-23"

    def test_effects_are_in_sloka_order(self):
        for h in range(1, 13):
            slokas = [e.sloka for e in BE.effects_for_house(h)]
            assert slokas == sorted(slokas)

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError):
            BE.effects_for_house(13)


class TestTopics:
    def test_clean_topic_headings_captured(self):
        """Wealth/poverty for the 2nd, children for the 5th — the caps headings survive where clean."""
        topics = {e.topic for effs in BE.all_bhava_effects().values() for e in effs if e.topic}
        assert len(topics) >= 20
        joined = " ".join(topics)
        assert "WEALTH" in joined

    def test_no_garbage_topics(self):
        """A captured topic must be mostly ASCII letters (OCR-Devanagari titles are rejected)."""
        for effs in BE.all_bhava_effects().values():
            for e in effs:
                if e.topic is None:
                    continue
                letters = [c for c in e.topic if c.isalpha()]
                assert sum(ord(c) < 128 for c in letters) / len(letters) >= 0.85
