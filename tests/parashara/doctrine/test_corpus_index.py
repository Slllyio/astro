"""The general numbered-sloka corpus indexer (any BPHS/allied chapter).

Pins the robustness that every structured doctrine module depends on: numbered slokas are found in
order, citations resolve, OCR noise (non-increasing numbers, Devanagari titles) is rejected, and an
unresolvable work yields nothing rather than raising.
"""
from __future__ import annotations

from app.parashara.doctrine.corpus_index import find_slokas, slokas_of
from app.parashara.doctrine.sources import verify


class TestSlokasOf:
    def test_indexes_a_clean_chapter(self):
        """ch.24 (the clean lord-grid) yields a long, ordered, fully-cited sloka run."""
        s = slokas_of("BPHS-24")
        assert len(s) >= 130
        assert [x.number for x in s] == sorted(x.number for x in s)
        assert all(verify(x.source) for x in s)

    def test_broad_corpus_coverage(self):
        """The indexer works across the whole BPHS, not just one chapter — coverage is substantial."""
        indexed = [c for c in range(1, 98) if slokas_of(f"BPHS-{c}")]
        total = sum(len(slokas_of(f"BPHS-{c}")) for c in range(1, 98))
        assert len(indexed) >= 80              # ~88/97 chapters present resolve to slokas
        assert total >= 900                    # ~1035 slokas across the corpus

    def test_unknown_work_is_empty_not_error(self):
        assert slokas_of("BPHS-999") == ()
        assert slokas_of("NOSUCHBOOK-1") == ()

    def test_topics_are_clean_ascii(self):
        for s in slokas_of("BPHS-13"):            # wealth chapter — has ALL-CAPS headings
            if s.topic:
                letters = [c for c in s.topic if c.isalpha()]
                assert sum(ord(c) < 128 for c in letters) / len(letters) >= 0.85


class TestFindSlokas:
    def test_cited_grep(self):
        """find_slokas returns only matching, still-cited slokas."""
        hits = find_slokas("BPHS-24", r"co-?bo")     # ch.24 mentions co-born under the 3rd lord
        assert hits
        assert all(verify(h.source) for h in hits)
        assert all("co" in h.text.lower() for h in hits)
