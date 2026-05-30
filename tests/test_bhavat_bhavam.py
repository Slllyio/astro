"""Tests for Bhāvāt Bhāvam + Karaka chains — Gap J."""
from __future__ import annotations

import pytest

from app.core.bhavat_bhavam import (
    BhavaFromBhava, KarakaChain, bhava_from_bhava, bhava_from_moon,
    bhava_from_sun, common_chains, karaka_chains_for_bhava,
    triple_lagna_view,
)
from app.core.chart_model import Chart


def _baseline_chart() -> Chart:
    return Chart(
        asc_sign=6, asc_lon=173.99,
        planet_signs={"Sun": 3, "Moon": 12, "Mars": 4, "Mercury": 3,
                      "Jupiter": 4, "Venus": 4, "Saturn": 9,
                      "Rahu": 12, "Ketu": 6},
        planet_houses={"Sun": 10, "Moon": 7, "Mars": 11, "Mercury": 10,
                       "Jupiter": 11, "Venus": 11, "Saturn": 4,
                       "Rahu": 7, "Ketu": 1},
        planet_lons={"Sun": 88.6, "Moon": 351.0, "Mars": 120.5,
                     "Mercury": 95.2, "Jupiter": 101.8, "Venus": 102.0,
                     "Saturn": 268.4, "Rahu": 348.5, "Ketu": 168.5},
    )


class TestBhavaFromBhava:
    def test_ninth_from_ninth_is_fifth(self):
        """Father's father (9th-from-9H) = 5H in natal Lagna frame."""
        r = bhava_from_bhava(9, 9)
        assert r.derived_bhava == 5

    def test_seventh_from_seventh_is_first(self):
        """Spouse's spouse (7th-from-7H) = self (1H)."""
        r = bhava_from_bhava(7, 7)
        assert r.derived_bhava == 1

    def test_distance_one_returns_same_bhava(self):
        """1st-from-N = N itself (inclusive count)."""
        for b in range(1, 13):
            assert bhava_from_bhava(b, 1).derived_bhava == b

    def test_returns_natural_karakas_of_derived(self):
        """Derived bhava carries its natural karaka(s)."""
        r = bhava_from_bhava(9, 9)  # = 5H, karaka Jupiter
        assert "Jupiter" in r.natural_karaka_of_derived

    def test_interpretation_hint_includes_phrases(self):
        """Hint mentions both base and derived bhava phrases."""
        r = bhava_from_bhava(9, 9)
        assert "father" in r.interpretation_hint.lower() or "dharma" in r.interpretation_hint.lower()
        assert "children" in r.interpretation_hint.lower() or "intellect" in r.interpretation_hint.lower()

    def test_rejects_invalid_bhava(self):
        with pytest.raises(ValueError):
            bhava_from_bhava(0, 5)
        with pytest.raises(ValueError):
            bhava_from_bhava(13, 5)

    def test_rejects_invalid_distance(self):
        with pytest.raises(ValueError):
            bhava_from_bhava(5, 0)
        with pytest.raises(ValueError):
            bhava_from_bhava(5, 13)


class TestKarakaChains:
    def test_chains_for_1h_include_sun(self):
        """1H natural karaka is Sun; chain shows where Sun sits."""
        chains = karaka_chains_for_bhava(1, _baseline_chart())
        suns = [c for c in chains if c.karaka == "Sun"]
        assert len(suns) == 1
        # Baseline chart has Sun in 10H
        assert suns[0].karaka_natal_house == 10

    def test_chains_for_10h_include_all_four_karakas(self):
        """10H has 4 karakas per BPHS Ch.6 — Sun, Mercury, Jupiter, Saturn."""
        chains = karaka_chains_for_bhava(10, _baseline_chart())
        karakas = {c.karaka for c in chains}
        assert karakas == {"Sun", "Mercury", "Jupiter", "Saturn"}

    def test_chain_phrase_mentions_karaka_and_house(self):
        """Chain phrase is human-readable: 'vitality via career', etc."""
        chains = karaka_chains_for_bhava(1, _baseline_chart())
        sun_chain = next(c for c in chains if c.karaka == "Sun")
        assert "Sun" in sun_chain.chain_phrase
        assert "10H" in sun_chain.chain_phrase or "career" in sun_chain.chain_phrase.lower()

    def test_rejects_invalid_bhava(self):
        with pytest.raises(ValueError):
            karaka_chains_for_bhava(0, _baseline_chart())


class TestTripleLagnaView:
    def test_from_lagna_equals_input(self):
        """from_lagna is always the input bhava."""
        view = triple_lagna_view(7, _baseline_chart())
        assert view["from_lagna"] == 7

    def test_from_moon_uses_moon_house(self):
        """Baseline Moon in 7H. Natal 7H from Moon-as-Lagna = ((7-7)%12)+1 = 1."""
        view = triple_lagna_view(7, _baseline_chart())
        assert view["from_moon"] == 1

    def test_from_sun_uses_sun_house(self):
        """Baseline Sun in 10H. Natal 7H from Sun-as-Lagna = ((7-10)%12)+1 = 10."""
        view = triple_lagna_view(7, _baseline_chart())
        assert view["from_sun"] == 10


class TestBhavaFromMoonSun:
    def test_moon_house_4_natal_bhava_4_yields_1(self):
        """If Moon is in 4H, the natal 4H IS the 1st from Moon."""
        assert bhava_from_moon(4, 4) == 1

    def test_wraps_correctly(self):
        """Moon in 12H, natal 1H is 2nd from Moon."""
        assert bhava_from_moon(1, 12) == 2

    def test_sun_symmetric_with_moon(self):
        """bhava_from_sun uses identical arithmetic."""
        for b in (1, 5, 7, 10, 12):
            for s in (1, 4, 7, 10, 12):
                assert bhava_from_sun(b, s) == bhava_from_moon(b, s)

    def test_rejects_invalid_bhava(self):
        with pytest.raises(ValueError):
            bhava_from_moon(13, 5)


class TestCommonChains:
    def test_returns_at_least_10_named_relationships(self):
        """The classical-canon list has 10 commonly-queried Bhāvāt Bhāvam pairs."""
        chains = common_chains()
        assert len(chains) >= 10

    def test_all_returns_are_bhavafrombhava(self):
        chains = common_chains()
        assert all(isinstance(c, BhavaFromBhava) for c in chains)

    def test_ninth_from_ninth_in_common_list(self):
        chains = common_chains()
        assert any(c.base_bhava == 9 and c.distance == 9 for c in chains)
