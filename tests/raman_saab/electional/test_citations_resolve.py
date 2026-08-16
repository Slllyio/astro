"""Every citation the electional package writes must resolve in the ingested corpus —
the doctrine-first guarantee, post firewall-lift."""
from __future__ import annotations

import pytest

from corpus_presence import needs_corpus

from app.raman_saab.doctrine.sources import Citation, verify


class TestElectionalCitationsResolve:
    @needs_corpus
    def test_every_cited_anchor_verifies(self):
        anchors = [
            ("MUHURTHA-3", 41),     # tarabala remainder table
            ("MUHURTHA-3", 66),     # chandrabala
            ("MUHURTHA-3", 88),     # Bharani condemned
            ("MUHURTHA-3", 104),    # panchaka formula
            ("MUHURTHA-3", 157),    # panchaka per-act exceptions
            ("MUHURTHA-2", 170),    # lagna thyajya
            ("MUHURTHA-2", 194),    # Tuesday/Saturday
            ("MUHURTHA-2", 202),    # tithi list
            ("MUHURTHA-2", 205),    # nakshatra thyajya table
            ("MUHURTHA-4", 290),    # diurnal durmuhurthas
            ("MUHURTHA-18", 767),   # rahu kalam table
            ("MUHURTHA-18", 861),   # bad yogas
            ("MUHURTHA-8", 1171),   # vishti karana
            ("MUHURTHA-10", 226),   # the essentials ordering
            ("ASP-15", 21), ("ASP-15", 55), ("ASP-15", 82), ("ASP-15", 101),
            ("ASP-15", 116), ("ASP-15", 145), ("ASP-15", 155),
        ]
        for work, line in anchors:
            assert verify(Citation(work, line)), f"{work}:{line} does not resolve"
