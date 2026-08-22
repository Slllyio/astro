"""Lunar (Chandra) yogas (BPHS ch.37) — detectors pinned to Parashara's definitions.

Sunapha/Anapha/Durudhara by a graha in the 2nd/12th/both from the Moon (sl.7); Kemadruma when the
Moon is bare (sl.11); Adhi by benefics in the 6th/7th/8th from her (sl.5). Citations must resolve to
real doctrine (the platform guard also checks this).
"""
from __future__ import annotations

from app.parashara.doctrine import chandra_yogas as C
from app.parashara.doctrine.sources import verify


def _names(yogas):
    return {y.name for y in yogas}


class TestSunaphaFamily:
    def test_sunapha_graha_in_2nd_from_moon(self):
        # Moon in Aries(1); Jupiter in Taurus(2) = 2nd from Moon.
        ps = {"Moon": 1, "Jupiter": 2, "Sun": 7, "Mars": 5, "Saturn": 9}
        assert "Sunapha" in _names(C.detect(ps, moon_sign=1, asc_sign=1))

    def test_anapha_graha_in_12th_from_moon(self):
        # Moon in Aries(1); Venus in Pisces(12) = 12th from Moon.
        ps = {"Moon": 1, "Venus": 12, "Sun": 7, "Mars": 5}
        assert "Anapha" in _names(C.detect(ps, moon_sign=1, asc_sign=1))

    def test_durudhara_both_sides(self):
        ps = {"Moon": 1, "Jupiter": 2, "Venus": 12, "Sun": 7}
        assert "Durudhara" in _names(C.detect(ps, moon_sign=1, asc_sign=1))

    def test_sun_alone_does_not_make_sunapha(self):
        # Only the Sun in the 2nd from the Moon — excluded by the text.
        ps = {"Moon": 1, "Sun": 2, "Mars": 5, "Jupiter": 5}
        assert not ({"Sunapha", "Anapha", "Durudhara"} & _names(C.detect(ps, moon_sign=1, asc_sign=1)))


class TestKemadruma:
    def test_bare_moon_is_kemadruma(self):
        # Moon in Aries(1); every tara-graha far from her AND out of kendras from lagna(Aries).
        # Kendras from Aries = 1,4,7,10 -> signs Aries,Cancer,Libra,Capricorn. 2nd/12th from Moon =
        # Taurus,Pisces. Put grahas in Gemini(3), Leo(5), Virgo(6), Scorpio(8), Sagittarius(9).
        ps = {"Moon": 1, "Mars": 3, "Mercury": 5, "Jupiter": 6, "Venus": 8, "Saturn": 9, "Sun": 11}
        assert "Kemadruma" in _names(C.detect(ps, moon_sign=1, asc_sign=1))

    def test_a_graha_in_kendra_from_lagna_cancels_kemadruma(self):
        # Same, but Jupiter in Cancer(4) = a kendra from lagna -> no Kemadruma (BPHS cancellation).
        ps = {"Moon": 1, "Mars": 3, "Mercury": 5, "Jupiter": 4, "Venus": 8, "Saturn": 9}
        assert "Kemadruma" not in _names(C.detect(ps, moon_sign=1, asc_sign=1))


class TestAdhi:
    def test_benefics_in_6_7_8_from_moon(self):
        # Moon in Aries(1): 6th/7th/8th = Virgo(6)/Libra(7)/Scorpio(8).
        ps = {"Moon": 1, "Mercury": 6, "Venus": 7, "Jupiter": 8, "Sun": 2, "Mars": 3}
        assert "Adhi" in _names(C.detect(ps, moon_sign=1, asc_sign=1))


class TestCitations:
    def test_all_sources_resolve(self):
        assert verify(C.SUNAPHA_SOURCE) and verify(C.KEMADRUMA_SOURCE)
        assert verify(C.ADHI_SOURCE) and verify(C.DHANA_SOURCE)
