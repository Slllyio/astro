"""Vargottama (Saravali ch.3 sl.13) — D9 sign equals D1 sign.

Pinned to the positional definition (1st navamsa of movable, 5th of fixed, 9th of dual) and to a
clear non-case. Citation (allied) must resolve.
"""
from __future__ import annotations

from app.parashara.doctrine import vargottama as V
from app.parashara.doctrine.sources import verify


class TestIsVargottama:
    def test_movable_first_navamsa(self):
        assert V.is_vargottama(1.0) is True        # Aries, 1st navamsa

    def test_fixed_fifth_navamsa(self):
        assert V.is_vargottama(44.0) is True        # Taurus, 5th navamsa

    def test_dual_ninth_navamsa(self):
        assert V.is_vargottama(86.7) is True        # Gemini, 9th navamsa

    def test_non_vargottama(self):
        assert V.is_vargottama(15.0) is False       # Aries mid -> Leo navamsa


class TestBodies:
    def test_lists_grahas_and_lagna(self):
        lons = {"Sun": 1.0, "Mars": 15.0, "Venus": 44.0}
        got = V.vargottama_bodies(lons, asc_longitude=86.7)
        assert got[0] == "Lagna"                    # ascendant listed first when vargottama
        assert set(got) == {"Lagna", "Sun", "Venus"}
        assert "Mars" not in got

    def test_no_ascendant_arg(self):
        assert set(V.vargottama_bodies({"Sun": 1.0, "Mars": 15.0})) == {"Sun"}


class TestCitation:
    def test_source_resolves(self):
        assert verify(V.SOURCE)
