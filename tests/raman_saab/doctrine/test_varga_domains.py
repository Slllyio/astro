"""Varga domain-table tests — completeness, citation resolution, karaka validity, and
the two Raman-explicit rows (Saptamsa=children, Dwadasamsa=parents).
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.varga import SUPPORTED_VARGAS
from app.raman_saab.doctrine.sources import verify
from corpus_presence import needs_corpus
from app.raman_saab.doctrine.varga_domains import DOMAINS, domain_for

_SEVEN = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}


class TestTableShape:
    def test_sixteen_rows_matching_supported_vargas(self) -> None:
        assert {d.n for d in DOMAINS} == set(SUPPORTED_VARGAS)
        assert len(DOMAINS) == 16
        assert [d.n for d in DOMAINS] == sorted(d.n for d in DOMAINS)

    @needs_corpus
    def test_every_citation_resolves_on_disk(self) -> None:
        """Each row's source passes the citation-resolution firewall."""
        for d in DOMAINS:
            assert verify(d.source), f"D{d.n}: {d.source.work}:{d.source.line}"

    def test_karakas_are_valid_grahas(self) -> None:
        for d in DOMAINS:
            assert set(d.karakas) <= _SEVEN, f"D{d.n}: {d.karakas}"

    def test_related_houses_are_valid(self) -> None:
        for d in DOMAINS:
            assert all(1 <= h <= 12 for h in d.related_houses), f"D{d.n}"


class TestRamanExplicitRows:
    def test_saptamsa_is_children(self) -> None:
        """HPA-11:198-199 names 'Saptamsa for children' explicitly."""
        d = domain_for(7)
        assert "children" in d.domain
        assert d.karakas == ("Jupiter",)          # PutraKaraka

    def test_dwadasamsa_is_parents(self) -> None:
        """HPA-11:198 names 'Dwadasamsa for parents' explicitly."""
        d = domain_for(12)
        assert "father" in d.domain and "mother" in d.domain
        assert set(d.karakas) == {"Sun", "Moon"}  # Pitru- and Matru-karakas

    def test_navamsa_is_the_verdict_varga(self) -> None:
        """The D9 row records its unique D1-verdict-modulating role."""
        d = domain_for(9)
        assert "ONLY division that modulates" in d.notes

    def test_unsupported_division_raises(self) -> None:
        with pytest.raises(ValueError):
            domain_for(5)
