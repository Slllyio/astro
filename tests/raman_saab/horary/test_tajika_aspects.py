"""Tajika aspects — geometry pinned to the PRASNA-4/VARSHA-7 definitions."""
from __future__ import annotations

import pytest

from app.raman_saab.horary.tajika_aspects import (
    DEEPTAMSA, SPEED_ORDER, easarapha, in_aspect, ithasala, kamboola, naktha, speed_rank,
    yamaya)


class TestOrbsAndSpeed:
    def test_the_printed_deeptamsa_table(self):
        """PRASNA-2:262-264 as printed: Sun 15, Moon 12, Mars 7, Mercury 7, Jupiter 9,
        Venus 7, Saturn 9."""
        assert DEEPTAMSA == {"Sun": 15, "Moon": 12, "Mars": 7, "Mercury": 7,
                             "Jupiter": 9, "Venus": 7, "Saturn": 9}

    def test_the_speed_order_saturn_slowest_moon_fastest(self):
        """PRASNA-4:1085-1088."""
        assert SPEED_ORDER == ("Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury",
                               "Moon")
        assert speed_rank("Saturn") < speed_rank("Moon")

    def test_the_varsha_orb_micro_example_guru_sukra_within_7(self):
        """VARSHA-7:43-47: Guru 9, Sukra 7 -> the yoga needs them within 7 degrees (the
        smaller deeptamsa governs). At 8 apart from conjunction: no aspect."""
        assert in_aspect("Jupiter", 10.0, "Venus", 16.9)
        assert not in_aspect("Jupiter", 10.0, "Venus", 18.1)


class TestIthasalaEasarapha:
    def test_applying_within_orb_is_ithasala(self):
        """Venus (faster) at 84, Saturn at 90: separation 6 above exact conjunction? No —
        Venus 6 behind Saturn, applying to conjunction (angle 0, gap 6 <= orb 7)."""
        y = ithasala("Venus", 84.0, "Saturn", 90.0)
        assert y is not None and y.yoga == "Ithasala" and y.planets == ("Venus", "Saturn")

    def test_within_one_degree_is_poorna(self):
        """PRASNA-4:1116-1119: within a degree of exactness it is Poorna (complete)."""
        y = ithasala("Venus", 89.5, "Saturn", 90.0)
        assert y is not None and y.yoga == "Poorna Ithasala"

    def test_separating_is_easarapha_not_ithasala(self):
        """PRASNA-4 stanza 56: the faster planet AHEAD by a degree — separating,
        unfavourable."""
        assert ithasala("Venus", 91.0, "Saturn", 90.0) is None
        e = easarapha("Venus", 91.0, "Saturn", 90.0)
        assert e is not None and not e.favourable

    def test_the_sign_boundary_does_not_break_the_geometry(self):
        """Circular-orb rule: Venus 358, Saturn 2 — separation 4 toward conjunction,
        applying across 0 Aries."""
        y = ithasala("Venus", 358.0, "Saturn", 2.0)
        assert y is not None

    def test_out_of_orb_is_nothing(self):
        assert ithasala("Venus", 70.0, "Saturn", 90.0) is None
        assert easarapha("Venus", 110.0, "Saturn", 90.0) is None


class TestTransferYogas:
    def test_naktha_fires_on_a_clean_configuration(self):
        """PRASNA-4 stanza 57: Jupiter 0 and Mercury 30 share no aspect (30 apart, both
        nearest angles out of orb); the Moon at 120 — exact trine to Jupiter, exact square
        to Mercury, faster than both — transfers the light."""
        y = naktha("Jupiter", 0.0, "Mercury", 30.0, "Moon", 120.0)
        assert y is not None and y.yoga == "Naktha" and "Moon" in y.planets

    def test_naktha_rejects_a_transferor_out_of_aspect(self):
        """Same pair, Moon at 100: 100 from Jupiter is a square 10 out — beyond the 9-degree
        mutual orb — so no transfer."""
        assert naktha("Jupiter", 0.0, "Mercury", 30.0, "Moon", 100.0) is None

    def test_naktha_rejects_a_pair_already_in_aspect(self):
        """Jupiter 0, Mercury 60.5 — an in-orb sextile — needs no light-transfer."""
        assert naktha("Jupiter", 0.0, "Mercury", 60.5, "Moon", 120.0) is None

    def test_yamaya_needs_a_slower_transferor(self):
        """PRASNA-4 stanza 60: Venus and Moon share no aspect; Jupiter (slower than both)
        aspects both."""
        y = yamaya("Venus", 0.0, "Moon", 30.0, "Jupiter", 120.0)
        # Jupiter trine Venus (gap 0, orb 7); Jupiter-Moon 90 exact square (orb 9). Venus-
        # Moon 30 apart: no tajika angle within orb 7.
        assert y is not None and y.yoga == "Yamaya"

    def test_yamaya_rejects_a_faster_transferor(self):
        assert yamaya("Saturn", 0.0, "Jupiter", 30.0, "Moon", 120.0) is None


class TestKamboola:
    def test_ithasala_pair_plus_moon_ithasala_is_kamboola(self):
        """PRASNA-4 stanza 61. Venus 84 applying Saturn 90 (Ithasala); Moon 80 applying
        to Venus 84 (conjunction, gap 4 <= 7, Moon faster and behind)."""
        y = kamboola("Venus", 84.0, "Saturn", 90.0, moon_lon=80.0)
        assert y is not None and y.yoga == "Kamboola" and y.planets[-1] == "Moon"

    def test_no_kamboola_without_the_moon_link(self):
        """Moon at 230: 214 from Venus and 220 from Saturn — both 20+ degrees from any
        tajika exactness, far beyond every orb."""
        assert kamboola("Venus", 84.0, "Saturn", 90.0, moon_lon=230.0) is None
