"""Vimshottari dasha (BPHS ch.46 sl.12-15) — the 120-year primary system.

Pinned to Parashara's own numbers and to the canonical baseline: the Moon at Revati (nakshatra 27)
seeds the Mercury mahadasha, matching the project's canonical chart ("Produces Mercury MD"). The
nakshatra->lord seed is also checked against the standard scheme (Aswini->Ketu, Krittika->Sun).
"""
from __future__ import annotations

import pytest

from app.parashara.doctrine.sources import verify
from app.parashara.primitives import vimshottari_dasha as V


class TestCycle:
    def test_totals_120_years(self):
        assert V.total_years(V.CYCLE) == 120
        assert V.TOTAL_YEARS == 120

    def test_durations_match_parashara(self):
        d = dict(V.CYCLE)
        assert (d["Sun"], d["Moon"], d["Mars"], d["Rahu"], d["Jupiter"],
                d["Saturn"], d["Mercury"], d["Ketu"], d["Venus"]) == (6, 10, 7, 18, 16, 19, 17, 7, 20)


class TestSeed:
    def test_canonical_revati_seeds_mercury(self):
        """The canonical baseline: Moon at Revati (27) -> Mercury mahadasha."""
        assert V.seed(27).lord == "Mercury"

    def test_standard_nakshatra_lords(self):
        # Krittika-start reckoning reproduces the familiar assignment.
        assert V.seed(1).lord == "Ketu"       # Aswini
        assert V.seed(2).lord == "Venus"      # Bharani
        assert V.seed(3).lord == "Sun"        # Krittika
        assert V.seed(4).lord == "Moon"       # Rohini
        assert V.seed(6).lord == "Rahu"       # Ardra

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError):
            V.seed(28)


class TestTimeline:
    def test_first_period_is_the_seed_lord(self):
        tl = V.timeline(27)
        assert tl[0].lord == "Mercury"
        assert tl[1].lord == "Ketu"            # Ketu follows Mercury in the cycle
        assert len(tl) == 9                    # one wrap through all nine lords
        assert tl[-1].lord == "Saturn"         # the lord just before Mercury in the cycle

    def test_succession_is_cyclic_from_seed(self):
        tl = V.timeline(1)                     # Aswini -> Ketu first
        lords = [p.lord for p in tl]
        assert lords[:3] == ["Ketu", "Venus", "Sun"]

    def test_elapsed_fraction_shortens_first_period(self):
        full = V.timeline(3)[0]
        half = V.timeline(3, elapsed_fraction=0.5)[0]
        assert half.end_year == pytest.approx(full.years * 0.5)


class TestCitations:
    def test_sources_resolve(self):
        assert verify(V.SEED_SOURCE) and verify(V.DURATIONS_SOURCE)
