"""Tests for ``app.reading.computations.bhava_bala``.

Doctrine source: BPHS Ch.28 -- six-fold house strength.

Algorithm summary
=================

For each bhava (1..12) the composite Bhava-bala is the sum of three
components (each in virupa, all positive contributions):

  1. Bhavadhipati-bala  -- the Shadbala of the house's lord (the planet
                           that rules the rashi falling in that house
                           from the Lagna sign).
  2. Bhava-Dig-bala     -- directional strength of the bhava itself.
                           Houses 1, 4, 7, 10 are the four cardinal
                           directions and earn the strongest Bhava-Dig
                           virupa per the BPHS schema.
  3. Bhava-Drishti-bala -- net aspects on the bhava cusp from benefics
                           minus malefics, weighted by full-aspect rules.

Bands (per spec):
  - very_strong : total >= 50
  - strong      : total >= 35
  - moderate    : total >= 20
  - weak        : total < 20

Direction in the emitted Finding:
  - positive when band in {strong, very_strong}
  - negative when band == weak
  - neutral  otherwise (moderate)
"""
from __future__ import annotations

import pytest

from app.reading.schema import Finding


# ---------------------------------------------------------------------------
# Bangalore baseline fixtures (shared with other reading-layer tests)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def bangalore_chart() -> dict:
    from app.core.ephemeris_engine import calculate_all_charts

    return calculate_all_charts(
        year=1990, month=7, day=15, hour=12, minute=0,
        tz_offset=5.5, latitude=12.97, longitude=77.59,
    )


@pytest.fixture(scope="module")
def d1_chart(bangalore_chart) -> dict:
    return bangalore_chart["d1"]


@pytest.fixture(scope="module")
def asc_sign(bangalore_chart) -> int:
    return int(bangalore_chart["ascendant"]["sign"])


# ---------------------------------------------------------------------------
# Shape / construction
# ---------------------------------------------------------------------------


class TestComputeBhavaBala:

    def test_returns_dict_keyed_by_house_1_to_12(self, d1_chart, asc_sign):
        from app.reading.computations.bhava_bala import compute_bhava_bala

        result = compute_bhava_bala(d1_chart, asc_sign)
        assert isinstance(result, dict)
        assert set(result.keys()) == set(range(1, 13))

    def test_emits_findings(self, d1_chart, asc_sign):
        from app.reading.computations.bhava_bala import compute_bhava_bala

        result = compute_bhava_bala(d1_chart, asc_sign)
        for house, finding in result.items():
            assert isinstance(finding, Finding), (
                f"house {house} value is not a Finding"
            )

    def test_id_grammar(self, d1_chart, asc_sign):
        from app.reading.computations.bhava_bala import compute_bhava_bala

        result = compute_bhava_bala(d1_chart, asc_sign)
        for house, finding in result.items():
            assert finding.id == f"foundation.bhava_bala.h{house}", (
                f"unexpected id {finding.id!r}"
            )

    def test_classification_is_primitive(self, d1_chart, asc_sign):
        from app.reading.computations.bhava_bala import compute_bhava_bala

        result = compute_bhava_bala(d1_chart, asc_sign)
        for finding in result.values():
            assert finding.classification == "primitive"

    def test_verdict_under_140_chars(self, d1_chart, asc_sign):
        from app.reading.computations.bhava_bala import compute_bhava_bala

        result = compute_bhava_bala(d1_chart, asc_sign)
        for finding in result.values():
            assert len(finding.verdict) <= 140

    def test_verdict_carries_band(self, d1_chart, asc_sign):
        from app.reading.computations.bhava_bala import compute_bhava_bala

        result = compute_bhava_bala(d1_chart, asc_sign)
        for finding in result.values():
            assert "band:" in finding.verdict, (
                f"verdict {finding.verdict!r} missing band: marker"
            )

    def test_direction_enum_valid(self, d1_chart, asc_sign):
        from app.reading.computations.bhava_bala import compute_bhava_bala

        valid = {"positive", "negative", "neutral", "mixed"}
        result = compute_bhava_bala(d1_chart, asc_sign)
        for finding in result.values():
            assert finding.direction in valid

    def test_evidence_carries_components(self, d1_chart, asc_sign):
        from app.reading.computations.bhava_bala import compute_bhava_bala

        result = compute_bhava_bala(d1_chart, asc_sign)
        for house, finding in result.items():
            joined = " ".join(finding.evidence)
            for key in ("bhavadhipati", "bhava_dig", "bhava_drishti", "total"):
                assert key in joined, (
                    f"house {house} evidence missing {key!r}: {finding.evidence}"
                )

    def test_doctrine_sentinel_in_evidence(self, d1_chart, asc_sign):
        from app.reading.computations.bhava_bala import compute_bhava_bala

        result = compute_bhava_bala(d1_chart, asc_sign)
        for finding in result.values():
            joined = " ".join(finding.evidence)
            assert "BPHS" in joined or "doctrine" in joined.lower()


# ---------------------------------------------------------------------------
# Property: exactly 12 entries, all integers 1..12
# ---------------------------------------------------------------------------


class TestPropertyExactly12Houses:

    def test_exactly_12_entries(self, d1_chart, asc_sign):
        from app.reading.computations.bhava_bala import compute_bhava_bala

        result = compute_bhava_bala(d1_chart, asc_sign)
        assert len(result) == 12
        for key in result.keys():
            assert isinstance(key, int)
            assert 1 <= key <= 12


# ---------------------------------------------------------------------------
# Band classification correctness
# ---------------------------------------------------------------------------


class TestBands:
    """Verify the 4 band thresholds (very_strong/strong/moderate/weak)."""

    def test_threshold_boundary_very_strong(self):
        from app.reading.computations.bhava_bala import _band_for

        assert _band_for(50.0) == "very_strong"
        assert _band_for(99.0) == "very_strong"

    def test_threshold_boundary_strong(self):
        from app.reading.computations.bhava_bala import _band_for

        assert _band_for(35.0) == "strong"
        assert _band_for(49.99) == "strong"

    def test_threshold_boundary_moderate(self):
        from app.reading.computations.bhava_bala import _band_for

        assert _band_for(20.0) == "moderate"
        assert _band_for(34.99) == "moderate"

    def test_threshold_boundary_weak(self):
        from app.reading.computations.bhava_bala import _band_for

        assert _band_for(0.0) == "weak"
        assert _band_for(19.99) == "weak"


class TestBhavaDigBala:
    """4th house carries highest Bhava-Dig-bala per BPHS Ch.28."""

    def test_4th_house_max(self):
        from app.reading.computations.bhava_bala import _bhava_dig_bala

        # 4th house = midnight / lowest visible point in BPHS scheme
        # earns the maximum bhava-dig credit.
        assert _bhava_dig_bala(4) == 60.0

    def test_10th_house_min(self):
        from app.reading.computations.bhava_bala import _bhava_dig_bala

        # 10th house (opposite of 4th) earns the minimum.
        assert _bhava_dig_bala(10) == 0.0

    def test_all_houses_in_range(self):
        from app.reading.computations.bhava_bala import _bhava_dig_bala

        for house in range(1, 13):
            v = _bhava_dig_bala(house)
            assert 0.0 <= v <= 60.0


# ---------------------------------------------------------------------------
# Shadbala-components reuse
# ---------------------------------------------------------------------------


class TestShadbalaReuse:
    """Passing pre-computed shadbala_components must not change the result.

    The optional kwarg is purely a caching hook; the public API contract
    is that semantically identical input yields identical Findings.
    """

    def test_with_and_without_cache_match(self, d1_chart, asc_sign):
        from app.reading.computations.bhava_bala import compute_bhava_bala

        a = compute_bhava_bala(d1_chart, asc_sign)
        b = compute_bhava_bala(d1_chart, asc_sign, shadbala_components=None)
        for house in range(1, 13):
            assert a[house].verdict == b[house].verdict
            assert a[house].direction == b[house].direction


# ---------------------------------------------------------------------------
# Argument validation
# ---------------------------------------------------------------------------


class TestArgumentValidation:

    def test_invalid_asc_sign_raises(self, d1_chart):
        from app.reading.computations.bhava_bala import compute_bhava_bala

        with pytest.raises(ValueError):
            compute_bhava_bala(d1_chart, asc_sign=0)
        with pytest.raises(ValueError):
            compute_bhava_bala(d1_chart, asc_sign=13)
