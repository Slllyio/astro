"""Special yogas (BPHS ch.36) — Gaja-Kesari in its strict four-condition form.

Every clause is exercised: the kendra (from lagna/Moon), the benefic conjunction/aspect, and the
three disqualifiers (debilitation, combustion, enemy's sign). Citation must resolve.
"""
from __future__ import annotations

from app.parashara.doctrine import special_yogas as S
from app.parashara.doctrine.sources import verify


def _names(y):
    return {x.name for x in y}


class TestGajaKesari:
    # Base: Jupiter in Cancer (exalted, 4th from Aries Moon), Venus conjunct it, Sun far.
    _BASE = {"Jupiter": 100.0, "Moon": 10.0, "Sun": 200.0, "Venus": 105.0}

    def test_forms_when_all_conditions_hold(self):
        y = S.detect(self._BASE, asc_sign=1, moon_waxing=True)
        assert "Gaja-Kesari" in _names(y)

    def test_combustion_disqualifies(self):
        # Sun brought next to Jupiter -> combust -> no yoga.
        lons = {**self._BASE, "Sun": 103.0}
        assert S.detect(lons, asc_sign=1, moon_waxing=True) == ()

    def test_no_benefic_influence_disqualifies(self):
        # Remove Venus; nothing benefic conjoins/aspects Jupiter -> no yoga.
        lons = {"Jupiter": 100.0, "Moon": 10.0, "Sun": 200.0}
        assert S.detect(lons, asc_sign=1, moon_waxing=True) == ()

    def test_debilitation_disqualifies(self):
        # Jupiter in Capricorn (debilitation), 4th from a Libra Moon, Venus conjunct.
        lons = {"Jupiter": 280.0, "Moon": 190.0, "Sun": 20.0, "Venus": 285.0}
        assert "Gaja-Kesari" not in _names(S.detect(lons, asc_sign=1, moon_waxing=True))

    def test_not_in_kendra_disqualifies(self):
        # Jupiter in Leo (5th from Aries Moon, not a kendra), Venus conjunct.
        lons = {"Jupiter": 130.0, "Moon": 10.0, "Sun": 300.0, "Venus": 135.0}
        assert S.detect(lons, asc_sign=1, moon_waxing=True) == ()


class TestCitation:
    def test_source_resolves(self):
        assert verify(S.GAJA_KESARI_SOURCE)
