"""Tests for Prashna chart + verdict modules — Gap K."""
from __future__ import annotations

import pytest

from app.core.chart_model import Chart
from app.core.prashna_chart import (
    PrashnaVerdict, element_of_lagna, element_question_match,
    lagna_modality_verdict, prashna_career, prashna_lost_item,
    prashna_marriage,
)


def _sample_prashna_chart(asc_sign: int = 4) -> Chart:
    """A sample prashna chart at the question moment."""
    return Chart(
        asc_sign=asc_sign, asc_lon=(asc_sign - 1) * 30 + 10.0,
        planet_signs={"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 6,
                      "Jupiter": 9, "Venus": 2, "Saturn": 11,
                      "Rahu": 3, "Ketu": 9},
        planet_houses={p: 1 for p in ["Sun", "Moon", "Mars", "Mercury",
                                       "Jupiter", "Venus", "Saturn",
                                       "Rahu", "Ketu"]},
        planet_lons={"Sun": 130.0, "Moon": 100.0, "Mars": 10.0, "Mercury": 175.0,
                     "Jupiter": 250.0, "Venus": 40.0, "Saturn": 310.0,
                     "Rahu": 70.0, "Ketu": 250.0},
    )


class TestLagnaModality:
    def test_chara_lagna_yes_quick(self):
        for sign in (1, 4, 7, 10):
            label, conf, timing = lagna_modality_verdict(sign)
            assert label == "YES_QUICK"
            assert timing == "days"

    def test_sthira_lagna_no_long_delay(self):
        for sign in (2, 5, 8, 11):
            label, _, timing = lagna_modality_verdict(sign)
            assert label == "NO_OR_LONG_DELAY"
            assert timing == "years"

    def test_dual_lagna_conditional(self):
        for sign in (3, 6, 9, 12):
            label, _, timing = lagna_modality_verdict(sign)
            assert label == "CONDITIONAL_PARTIAL"
            assert timing == "months"

    def test_rejects_invalid_sign(self):
        with pytest.raises(ValueError):
            lagna_modality_verdict(13)


class TestPanchaMahabhuta:
    def test_aries_is_fire(self):
        assert element_of_lagna(1) == "fire"

    def test_cancer_is_water(self):
        assert element_of_lagna(4) == "water"

    def test_marriage_water_lagna_boosted(self):
        """Marriage prashna with water Lagna → multiplier 1.2."""
        assert element_question_match(4, "marriage") == 1.2

    def test_career_fire_lagna_boosted(self):
        assert element_question_match(1, "career") == 1.2

    def test_travel_air_lagna_boosted(self):
        assert element_question_match(3, "travel") == 1.2


class TestPrashnaMarriage:
    def test_returns_verdict(self):
        v = prashna_marriage(_sample_prashna_chart(asc_sign=4))
        assert isinstance(v, PrashnaVerdict)
        assert v.question_domain == "marriage"
        assert v.karya_bhava == 7

    def test_chara_lagna_yields_quick_verdict(self):
        """Cancer (chara) Lagna marriage prashna → quick result."""
        v = prashna_marriage(_sample_prashna_chart(asc_sign=4))
        assert v.timing_estimate == "days"


class TestPrashnaCareer:
    def test_returns_career_verdict(self):
        v = prashna_career(_sample_prashna_chart(asc_sign=1))
        assert v.question_domain == "career"
        assert v.karya_bhava == 10


class TestPrashnaLostItem:
    def test_returns_verdict_with_direction_hint(self):
        v = prashna_lost_item(_sample_prashna_chart(asc_sign=1))
        # Direction should appear in rationale (West/East/etc)
        joined = " ".join(v.rationale)
        assert any(d in joined for d in ("East", "West", "South", "North"))


class TestRefusalProtocol:
    def test_rahu_kalam_yields_refuse(self):
        v = prashna_marriage(
            _sample_prashna_chart(), is_rahu_kalam=True,
        )
        assert v.verdict_label == "REFUSE"
        assert v.confidence == 0.0
        assert "Rahu Kalam" in (v.refused_reason or "")

    def test_yamagandam_yields_refuse(self):
        v = prashna_career(
            _sample_prashna_chart(), is_yamagandam=True,
        )
        assert v.verdict_label == "REFUSE"

    def test_bhadra_yields_refuse(self):
        v = prashna_lost_item(
            _sample_prashna_chart(), is_bhadra=True,
        )
        assert v.verdict_label == "REFUSE"


class TestHoraModifier:
    def test_jupiter_hora_boosts_confidence(self):
        """Jupiter hora → 1.15x confidence multiplier."""
        v_no_hora = prashna_marriage(_sample_prashna_chart(asc_sign=4))
        v_jup_hora = prashna_marriage(_sample_prashna_chart(asc_sign=4), hora_lord="Jupiter")
        assert v_jup_hora.confidence >= v_no_hora.confidence

    def test_saturn_hora_suppresses_confidence(self):
        """Saturn hora → 0.85x confidence multiplier."""
        v_no_hora = prashna_marriage(_sample_prashna_chart(asc_sign=4))
        v_sat_hora = prashna_marriage(_sample_prashna_chart(asc_sign=4), hora_lord="Saturn")
        # Saturn should not boost
        assert v_sat_hora.confidence <= v_no_hora.confidence * 1.05
