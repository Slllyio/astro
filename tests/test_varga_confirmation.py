"""Tests for varga confirmation layer — Gap B."""
from __future__ import annotations

import pytest

from app.core.varga_confirmation import (
    BHAVA_TO_VARGA, VargaConfirmation, primary_varga_for_bhava,
    varga_confirmation,
)


class TestPrimaryVargaForBhava:
    def test_marriage_bhava_is_d9(self):
        """7H (marriage) → D9 Navamsha."""
        assert primary_varga_for_bhava(7) == "D9"

    def test_career_bhava_is_d10(self):
        """10H (career) → D10 Dasamsa."""
        assert primary_varga_for_bhava(10) == "D10"

    def test_children_bhava_is_d7(self):
        """5H (children) → D7 Saptamsa."""
        assert primary_varga_for_bhava(5) == "D7"

    def test_disease_bhava_is_d30(self):
        """6H (disease) → D30 Trimsamsa."""
        assert primary_varga_for_bhava(6) == "D30"

    def test_dharma_bhava_is_d9(self):
        """9H (dharma) shares D9 with 7H."""
        assert primary_varga_for_bhava(9) == "D9"

    def test_rejects_invalid_bhava(self):
        with pytest.raises(ValueError):
            primary_varga_for_bhava(0)
        with pytest.raises(ValueError):
            primary_varga_for_bhava(13)


class TestConfirmationLabels:
    def test_both_positive_yields_confirmed(self):
        """D1 positive + varga positive = CONFIRMED."""
        c = varga_confirmation(
            7, d1_bhava_pillar_score=0.4, varga_bhava_pillar_score=0.3,
        )
        assert c.confirmation_label == "CONFIRMED"

    def test_d1_positive_varga_negative_promise_no_delivery(self):
        """Classical pattern: promise without delivery."""
        c = varga_confirmation(
            10, d1_bhava_pillar_score=0.5, varga_bhava_pillar_score=-0.3,
        )
        assert c.confirmation_label == "PROMISE_NO_DELIVERY"
        assert "without inner substance" in c.rationale.lower() or "doesn't ultimately deliver" in c.rationale.lower()

    def test_d1_negative_varga_positive_hidden_promise(self):
        """Late-bloom delivery — D1 missed, varga shows it."""
        c = varga_confirmation(
            5, d1_bhava_pillar_score=-0.3, varga_bhava_pillar_score=0.4,
        )
        assert c.confirmation_label == "HIDDEN_PROMISE"

    def test_both_negative_consistent_affliction(self):
        """Both D1 and varga agree negatively."""
        c = varga_confirmation(
            7, d1_bhava_pillar_score=-0.4, varga_bhava_pillar_score=-0.3,
        )
        assert c.confirmation_label == "CONSISTENT_AFFLICTION"

    def test_no_varga_score_yields_unknown(self):
        """Missing varga data → UNKNOWN label."""
        c = varga_confirmation(7, d1_bhava_pillar_score=0.4)
        assert c.confirmation_label == "UNKNOWN"


class TestVargaName:
    def test_uses_canonical_varga_by_default(self):
        """Default varga = canonical mapping for the bhava."""
        c = varga_confirmation(7, 0.4, 0.3)
        assert c.varga_name == "D9"  # canonical for 7H

    def test_can_override_varga_name(self):
        """Caller can pass a different varga for special analysis."""
        c = varga_confirmation(7, 0.4, 0.3, varga_name="D7")
        assert c.varga_name == "D7"


class TestRationaleQuality:
    def test_confirmed_rationale_mentions_domain(self):
        """CONFIRMED rationale mentions the bhava's domain."""
        c = varga_confirmation(7, 0.5, 0.5)
        assert "spouse" in c.rationale.lower() or "marriage" in c.rationale.lower()

    def test_hidden_promise_rationale_mentions_late_bloom(self):
        c = varga_confirmation(10, -0.3, 0.4)
        assert "late" in c.rationale.lower() or "unexpected" in c.rationale.lower()


class TestBhavaToVargaTable:
    def test_all_12_bhavas_covered(self):
        """Every bhava has a primary varga mapping."""
        assert set(BHAVA_TO_VARGA.keys()) == set(range(1, 13))

    def test_no_invalid_varga_names(self):
        """All varga names are well-formed D-numbers."""
        for varga in BHAVA_TO_VARGA.values():
            assert varga.startswith("D")
            assert varga[1:].isdigit()
