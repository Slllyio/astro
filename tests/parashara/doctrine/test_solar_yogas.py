"""Solar yogas (BPHS ch.38) — Vesi/Vasi/Ubhayachari from the Sun.

Parallel to the lunar yogas: a tara-graha in the 2nd/12th/both from the Sun; the Moon is excluded.
"""
from __future__ import annotations

from app.parashara.doctrine import solar_yogas as S
from app.parashara.doctrine.sources import verify


def _names(y):
    return {x.name for x in y}


class TestDetect:
    def test_vesi_graha_in_2nd_from_sun(self):
        # Sun in Aries(1); Jupiter in Taurus(2) = 2nd from Sun.
        assert "Vesi" in _names(S.detect({"Jupiter": 2}, sun_sign=1))

    def test_vasi_graha_in_12th_from_sun(self):
        assert "Vasi" in _names(S.detect({"Venus": 12}, sun_sign=1))

    def test_ubhayachari_both_sides(self):
        assert "Ubhayachari" in _names(S.detect({"Jupiter": 2, "Venus": 12}, sun_sign=1))

    def test_moon_is_excluded(self):
        # Only the Moon in the 2nd from the Sun -> no solar yoga (barred by the text).
        assert S.detect({"Moon": 2}, sun_sign=1) == ()

    def test_empty_when_nothing_flanks_the_sun(self):
        assert S.detect({"Jupiter": 6, "Saturn": 8}, sun_sign=1) == ()


class TestCitation:
    def test_sources_resolve(self):
        assert verify(S.SOURCE) and verify(S.EFFECTS_SOURCE)
