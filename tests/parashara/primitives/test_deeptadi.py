"""Deeptadi avasthas (BPHS-45:113) — dignity/placement state + Vikala/Kopa flags.

Pinned to Parashara's mapping: exaltation -> Deepta, own -> Swastha, enemy -> Khala; a malefic in
the sign -> Vikala; combustion -> Kopa. Citation resolves.
"""
from __future__ import annotations

from app.parashara.doctrine.sources import verify
from app.parashara.primitives.deeptadi_avastha import SOURCE, deeptadi


class TestDignityState:
    def test_exaltation_is_deepta(self):
        assert deeptadi("Jupiter", {"Jupiter": 100.0, "Sun": 200.0}).state == "Deepta"  # Cancer

    def test_own_sign_is_swastha(self):
        assert deeptadi("Sun", {"Sun": 130.0}).state == "Swastha"                       # Leo

    def test_enemy_sign_is_khala(self):
        # Sun in Saturn's Capricorn(10): Saturn is the Sun's enemy -> Khala.
        st = deeptadi("Sun", {"Sun": 280.0, "Saturn": 40.0}).state
        assert st == "Khala"


class TestFlags:
    def test_malefic_company_sets_vikala(self):
        d = deeptadi("Venus", {"Venus": 100.0, "Saturn": 108.0, "Sun": 300.0})
        assert d.vikala is True

    def test_combustion_sets_kopa(self):
        assert deeptadi("Mercury", {"Mercury": 102.0, "Sun": 100.0}).kopa is True

    def test_far_from_sun_no_kopa(self):
        assert deeptadi("Mercury", {"Mercury": 100.0, "Sun": 250.0}).kopa is False


class TestCitation:
    def test_source_resolves(self):
        assert verify(SOURCE)
