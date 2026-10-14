"""Pancha Mahapurusha yogas (Saravali ch.37) — a non-luminary in own/exaltation, in a kendra.

Pinned to Saravali's definition: Ruchaka(Mars), Bhadra(Mercury), Hamsa(Jupiter), Malavya(Venus),
Sasa(Saturn). Dignity + kendra both required; citations (allied tier) must resolve.
"""
from __future__ import annotations

from app.parashara.doctrine import mahapurusha as M
from app.parashara.doctrine.sources import verify


def _names(yogas):
    return {y.name for y in yogas}


class TestDetect:
    def test_sasa_saturn_exalted_in_kendra(self):
        # Aries lagna; Saturn in Libra(7, its exaltation) = 7th house (a kendra).
        y = M.detect({"Saturn": 7}, asc_sign=1)
        assert "Sasa" in _names(y)
        assert y[0].planet == "Saturn" and y[0].dignity == "exaltation" and y[0].house == 7

    def test_ruchaka_mars_own_sign_in_lagna(self):
        # Aries lagna; Mars in Aries(1, own) = 1st house.
        y = M.detect({"Mars": 1}, asc_sign=1)
        assert "Ruchaka" in _names(y) and y[0].dignity == "own"

    def test_hamsa_jupiter_exalted_in_kendra(self):
        # Aries lagna; Jupiter in Cancer(4, exaltation) = 4th house.
        assert "Hamsa" in _names(M.detect({"Jupiter": 4}, asc_sign=1))

    def test_dignity_without_kendra_is_no_yoga(self):
        # Taurus lagna; Mars in Aries(own) = 12th house -> not a kendra -> no Ruchaka.
        assert M.detect({"Mars": 1}, asc_sign=2) == ()

    def test_kendra_without_dignity_is_no_yoga(self):
        # Aries lagna; Mars in Cancer(4, a kendra) but neither own nor exalted -> nothing.
        assert M.detect({"Mars": 4}, asc_sign=1) == ()

    def test_sun_and_moon_never_form_these(self):
        assert M.detect({"Sun": 1, "Moon": 4}, asc_sign=1) == ()


class TestCitations:
    def test_definition_and_effects_resolve(self):
        assert verify(M.DEF_SOURCE)
        for y in M.detect({"Saturn": 7, "Mars": 1}, asc_sign=1):
            assert verify(y.effect)
