"""Tests for ``app.reading.computations.special_lagnas``.

Doctrine source: Classical Jaimini / Sri Sushil Kumar Jain tradition for
the five special lagnas:

  - **Hora Lagna**:    advances 30° per hour from sunrise
  - **Ghatika Lagna**: advances 30° per ghati (24 min) from sunrise
  - **Sree Lagna**:    Lagna + Moon-nakshatra-portion (Sanjay Rath
                       formulation)
  - **Bhava Lagna**:   advances 30° per 2 hours from sunrise (Sun-based)
  - **Pranapada Lagna**: 24-second time-units from Sun position

All five are reference points for sub-domain forecasting (career,
wealth, longevity). This module is a structural primitive: the precise
formulas are simplified for v1 and flagged with TODO for refinement
against jagannathahora.io pinning.
"""
from __future__ import annotations

import pytest


_EXPECTED_KEYS = {"hora", "ghatika", "sree", "bhava", "pranapada"}


@pytest.fixture
def bangalore_inputs() -> dict:
    """Bangalore baseline. birth ~12:00 IST on 1990-07-15.

    For testing purposes we supply a sunrise_jd 0.25 days (6 hours)
    before birth_jd — i.e. birth is 6 hours after sunrise.

    Birth_jd is the canonical Bangalore 1990-07-15 12:00 IST value.
    """
    # birth_jd from app.core.ephemeris_engine.calculate_all_charts for
    # the canonical Bangalore baseline (CLAUDE.md).
    birth_jd = 2448087.7708333335
    sunrise_jd = birth_jd - 0.25  # ~6 hours before noon = ~6 am sunrise
    return {
        "birth_jd": birth_jd,
        "sunrise_jd": sunrise_jd,
        "asc_sign": 6,  # Virgo lagna (project canonical pin)
    }


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------


class TestShape:

    def test_returns_dict_with_five_keys(self, bangalore_inputs):
        from app.reading.computations.special_lagnas import compute_special_lagnas

        result = compute_special_lagnas(**bangalore_inputs)
        assert isinstance(result, dict)
        assert set(result.keys()) == _EXPECTED_KEYS

    def test_emits_findings(self, bangalore_inputs):
        from app.reading.computations.special_lagnas import compute_special_lagnas
        from app.reading.schema import Finding

        result = compute_special_lagnas(**bangalore_inputs)
        for key, finding in result.items():
            assert isinstance(finding, Finding), f"{key} not a Finding"


# ---------------------------------------------------------------------------
# Finding contract
# ---------------------------------------------------------------------------


class TestFindingContract:

    def test_id_grammar(self, bangalore_inputs):
        from app.reading.computations.special_lagnas import compute_special_lagnas

        result = compute_special_lagnas(**bangalore_inputs)
        for key, finding in result.items():
            assert finding.id == f"practitioner.special_lagnas.{key}", (
                f"{key} has unexpected id {finding.id}"
            )

    def test_classification_is_primitive(self, bangalore_inputs):
        from app.reading.computations.special_lagnas import compute_special_lagnas

        result = compute_special_lagnas(**bangalore_inputs)
        for finding in result.values():
            assert finding.classification == "primitive"

    def test_direction_is_neutral(self, bangalore_inputs):
        from app.reading.computations.special_lagnas import compute_special_lagnas

        result = compute_special_lagnas(**bangalore_inputs)
        for finding in result.values():
            assert finding.direction == "neutral"

    def test_verdict_under_140(self, bangalore_inputs):
        from app.reading.computations.special_lagnas import compute_special_lagnas

        result = compute_special_lagnas(**bangalore_inputs)
        for finding in result.values():
            assert len(finding.verdict) <= 140

    def test_verdict_mentions_sign_name(self, bangalore_inputs):
        from app.reading.computations.special_lagnas import compute_special_lagnas

        result = compute_special_lagnas(**bangalore_inputs)
        valid_signs = {
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius",
            "Pisces",
        }
        for key, finding in result.items():
            assert any(s in finding.verdict for s in valid_signs), (
                f"{key} verdict {finding.verdict!r} missing sign name"
            )


# ---------------------------------------------------------------------------
# Algorithmic invariants
# ---------------------------------------------------------------------------


class TestAlgorithmInvariants:

    def test_sunrise_birth_hora_equals_lagna(self):
        """Hora Lagna at sunrise time = the ascendant itself."""
        from app.reading.computations.special_lagnas import compute_special_lagnas

        birth_jd = 2448087.5  # arbitrary
        sunrise_jd = birth_jd  # birth IS at sunrise
        result = compute_special_lagnas(
            birth_jd=birth_jd, sunrise_jd=sunrise_jd, asc_sign=1,
        )
        # Sign should be Aries (the supplied asc_sign).
        assert "Aries" in result["hora"].verdict

    def test_evidence_carries_doctrine_marker(self, bangalore_inputs):
        from app.reading.computations.special_lagnas import compute_special_lagnas

        result = compute_special_lagnas(**bangalore_inputs)
        for key, finding in result.items():
            evidence_blob = " ".join(finding.evidence)
            assert "doctrine" in evidence_blob.lower(), (
                f"{key} evidence missing doctrine marker"
            )


# ---------------------------------------------------------------------------
# All-asc-sign sanity sweep
# ---------------------------------------------------------------------------


class TestPropertyAllLagnas:

    @pytest.mark.parametrize("asc_sign", list(range(1, 13)))
    def test_runs_for_every_lagna(self, asc_sign):
        from app.reading.computations.special_lagnas import compute_special_lagnas

        birth_jd = 2448087.7708333335
        sunrise_jd = birth_jd - 0.25
        result = compute_special_lagnas(
            birth_jd=birth_jd, sunrise_jd=sunrise_jd, asc_sign=asc_sign,
        )
        assert set(result.keys()) == _EXPECTED_KEYS
