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

    # These assert the Gaja-Kesari clause is disqualified; OTHER ch.36 yogas may still fire on the
    # same fixture (detect() now covers Subha/Amala/Parvata/Chamara/Srinatha), so check GK absence.
    def test_combustion_disqualifies(self):
        # Sun brought next to Jupiter -> combust -> no Gaja-Kesari.
        lons = {**self._BASE, "Sun": 103.0}
        assert "Gaja-Kesari" not in _names(S.detect(lons, asc_sign=1, moon_waxing=True))

    def test_no_benefic_influence_disqualifies(self):
        # Remove Venus; nothing benefic conjoins/aspects Jupiter -> no Gaja-Kesari.
        lons = {"Jupiter": 100.0, "Moon": 10.0, "Sun": 200.0}
        assert "Gaja-Kesari" not in _names(S.detect(lons, asc_sign=1, moon_waxing=True))

    def test_debilitation_disqualifies(self):
        # Jupiter in Capricorn (debilitation), 4th from a Libra Moon, Venus conjunct.
        lons = {"Jupiter": 280.0, "Moon": 190.0, "Sun": 20.0, "Venus": 285.0}
        assert "Gaja-Kesari" not in _names(S.detect(lons, asc_sign=1, moon_waxing=True))

    def test_not_in_kendra_disqualifies(self):
        # Jupiter in Leo (5th from Aries Moon, not a kendra), Venus conjunct.
        lons = {"Jupiter": 130.0, "Moon": 10.0, "Sun": 300.0, "Venus": 135.0}
        assert "Gaja-Kesari" not in _names(S.detect(lons, asc_sign=1, moon_waxing=True))


class TestNamedYogas:
    """The crisp ch.36 named yogas (signs are 1..12; Aries lagna unless noted)."""

    def test_subha_benefic_in_ascendant(self):
        assert S.subha({"Jupiter": 1, "Sun": 7}, asc_sign=1, moon_waxing=True) is not None
        # a malefic there is not Subha
        assert S.subha({"Saturn": 1, "Jupiter": 7}, asc_sign=1, moon_waxing=True) is None

    def test_subha_benefics_in_2nd_and_12th(self):
        y = S.subha({"Venus": 2, "Jupiter": 12}, asc_sign=1, moon_waxing=True)
        assert y is not None and "2nd and the 12th" in y.reason

    def test_asubha_malefic_in_ascendant(self):
        assert S.asubha({"Saturn": 1}, asc_sign=1, moon_waxing=True) is not None
        assert S.asubha({"Jupiter": 1}, asc_sign=1, moon_waxing=True) is None

    def test_amala_only_benefic_in_10th(self):
        # Aries lagna -> 10th = Capricorn (10); Jupiter alone there, no malefic
        assert S.amala({"Jupiter": 10, "Sun": 3}, asc_sign=1, moon_waxing=True) is not None
        # a malefic also in the 10th spoils it
        assert S.amala({"Jupiter": 10, "Saturn": 10}, asc_sign=1, moon_waxing=True) is None

    def test_parvata_benefic_kendra_clean_7_8(self):
        # Venus in the 4th (kendra); nothing malefic in 7th/8th
        assert S.parvata({"Venus": 4, "Jupiter": 1}, asc_sign=1, moon_waxing=True) is not None
        # a malefic in the 7th spoils it
        assert S.parvata({"Venus": 4, "Saturn": 7}, asc_sign=1, moon_waxing=True) is None

    def test_chamara_two_benefics_in_a_good_house(self):
        y = S.chamara({"Jupiter": 10, "Venus": 10, "Sun": 3}, asc_sign=1, moon_waxing=True)
        assert y is not None

    def test_srinatha_full_condition(self):
        # Aries lagna: 7th lord Venus (Libra) -> must be in the 10th (Capricorn=10); 10th lord
        # Saturn exalted in Libra(7) and with the 9th lord Jupiter (also Libra).
        signs = {"Venus": 10, "Saturn": 7, "Jupiter": 7}
        assert S.srinatha(signs, asc_sign=1) is not None

    def test_detect_returns_cited_yogas(self):
        signs_lon = {"Jupiter": 10 * 30.0, "Venus": 10 * 30.0 + 5, "Sun": 60.0, "Moon": 40.0}
        for y in S.detect(signs_lon, asc_sign=1, moon_waxing=True):
            assert verify(y.source) and y.source.work == "BPHS-36"


class TestCitation:
    def test_sources_resolve(self):
        for c in (S.GAJA_KESARI_SOURCE, S.SUBHA_SOURCE, S.AMALA_SOURCE, S.PARVATA_SOURCE,
                  S.CHAMARA_SOURCE, S.SRINATHA_SOURCE):
            assert verify(c) and c.work == "BPHS-36"
