"""Tests for ``app.reading.computations.ashtakavarga_reader``.

Doctrine source: Phaladeepika Ch.23-24 -- Ashtakavarga interpretive layer.

The raw BAV (Bhinnashtakavarga) and SAV (Sarvashtakavarga) computations
live in ``app.core.ashtakavarga``. This reader layer applies the
classical interpretive thresholds from Phaladeepika Ch.23-24:

- **SAV per house**: bindus < 25 = weak house; 25-30 = moderate;
  > 30 = strong.
- **BAV per planet per house**: < 4 bindus = transit-weak; >= 4 = transit-
  capable. (Used by transit forecasting to decide if a transiting planet
  can deliver house-significant results when it lands in that bhava.)

Reader emits a Finding-per-house for SAV plus a Finding-per-(planet, house)
for BAV, totalling 12 + 7*12 = 96 Findings. (Lunar nodes are not BAV
contributors per classical Ashtakavarga and are excluded.)
"""
from __future__ import annotations

import pytest

from app.reading.schema import Finding


_BAV_PLANETS = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")


# ---------------------------------------------------------------------------
# Bangalore baseline fixtures
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


class TestReadAshtakavarga:

    def test_returns_dict(self, d1_chart, asc_sign):
        from app.reading.computations.ashtakavarga_reader import (
            read_ashtakavarga,
        )

        result = read_ashtakavarga(d1_chart, asc_sign)
        assert isinstance(result, dict)

    def test_contains_12_sav_house_keys(self, d1_chart, asc_sign):
        from app.reading.computations.ashtakavarga_reader import (
            read_ashtakavarga,
        )

        result = read_ashtakavarga(d1_chart, asc_sign)
        expected = {f"sav_house_{n}" for n in range(1, 13)}
        assert expected.issubset(set(result.keys()))

    def test_contains_84_bav_house_keys(self, d1_chart, asc_sign):
        """7 planets x 12 houses = 84 BAV-per-house Findings."""
        from app.reading.computations.ashtakavarga_reader import (
            read_ashtakavarga,
        )

        result = read_ashtakavarga(d1_chart, asc_sign)
        bav_keys = [
            k for k in result.keys()
            if k.startswith("bav_") and "_house_" in k
        ]
        assert len(bav_keys) == 84

    def test_all_values_are_findings(self, d1_chart, asc_sign):
        from app.reading.computations.ashtakavarga_reader import (
            read_ashtakavarga,
        )

        result = read_ashtakavarga(d1_chart, asc_sign)
        for key, finding in result.items():
            assert isinstance(finding, Finding), (
                f"{key} value is not a Finding"
            )

    def test_classification_is_primitive(self, d1_chart, asc_sign):
        from app.reading.computations.ashtakavarga_reader import (
            read_ashtakavarga,
        )

        result = read_ashtakavarga(d1_chart, asc_sign)
        for finding in result.values():
            assert finding.classification == "primitive"

    def test_id_grammar_sav(self, d1_chart, asc_sign):
        from app.reading.computations.ashtakavarga_reader import (
            read_ashtakavarga,
        )

        result = read_ashtakavarga(d1_chart, asc_sign)
        for house in range(1, 13):
            key = f"sav_house_{house}"
            assert result[key].id == f"foundation.ashtakavarga_reader.{key}"

    def test_id_grammar_bav(self, d1_chart, asc_sign):
        from app.reading.computations.ashtakavarga_reader import (
            read_ashtakavarga,
        )

        result = read_ashtakavarga(d1_chart, asc_sign)
        for planet in _BAV_PLANETS:
            for house in range(1, 13):
                key = f"bav_{planet.lower()}_house_{house}"
                assert result[key].id == (
                    f"foundation.ashtakavarga_reader.{key}"
                )

    def test_verdict_under_140_chars(self, d1_chart, asc_sign):
        from app.reading.computations.ashtakavarga_reader import (
            read_ashtakavarga,
        )

        result = read_ashtakavarga(d1_chart, asc_sign)
        for finding in result.values():
            assert len(finding.verdict) <= 140

    def test_doctrine_sentinel_in_evidence(self, d1_chart, asc_sign):
        from app.reading.computations.ashtakavarga_reader import (
            read_ashtakavarga,
        )

        result = read_ashtakavarga(d1_chart, asc_sign)
        for finding in result.values():
            joined = " ".join(finding.evidence)
            assert "Phaladeepika" in joined or "Ashtakavarga" in joined


# ---------------------------------------------------------------------------
# Threshold correctness (Phaladeepika Ch.23-24)
# ---------------------------------------------------------------------------


class TestSAVBands:
    """Test the SAV interpretive bands at boundary values."""

    def test_sav_band_strong(self):
        from app.reading.computations.ashtakavarga_reader import _sav_band

        assert _sav_band(31) == "strong"
        assert _sav_band(40) == "strong"

    def test_sav_band_moderate(self):
        from app.reading.computations.ashtakavarga_reader import _sav_band

        assert _sav_band(25) == "moderate"
        assert _sav_band(30) == "moderate"

    def test_sav_band_weak(self):
        from app.reading.computations.ashtakavarga_reader import _sav_band

        assert _sav_band(0) == "weak"
        assert _sav_band(24) == "weak"


class TestBAVBands:
    """BAV-per-house bands: < 4 = weak, >= 4 = transit-capable."""

    def test_bav_band_capable(self):
        from app.reading.computations.ashtakavarga_reader import _bav_band

        assert _bav_band(4) == "transit_capable"
        assert _bav_band(8) == "transit_capable"

    def test_bav_band_weak(self):
        from app.reading.computations.ashtakavarga_reader import _bav_band

        assert _bav_band(0) == "weak"
        assert _bav_band(3) == "weak"


# ---------------------------------------------------------------------------
# Direction mapping
# ---------------------------------------------------------------------------


class TestDirection:
    """Direction reflects bindu strength."""

    def test_sav_strong_is_positive(self, d1_chart, asc_sign):
        from app.reading.computations.ashtakavarga_reader import (
            read_ashtakavarga,
        )

        result = read_ashtakavarga(d1_chart, asc_sign)
        # find at least one strong SAV house
        strong = [
            v for v in result.values()
            if v.id.endswith("_sav_house_1") or "strong" in v.verdict
        ]
        # Should have at least one strong sav house in bangalore baseline
        # (SAV has values up to 38)
        assert any(
            f.direction == "positive"
            for f in result.values()
            if f.id.split(".")[-1].startswith("sav_house_")
        )

    def test_sav_weak_is_negative(self, d1_chart, asc_sign):
        from app.reading.computations.ashtakavarga_reader import (
            read_ashtakavarga,
        )

        result = read_ashtakavarga(d1_chart, asc_sign)
        # find at least one weak SAV house (bangalore baseline has houses
        # with SAV=20, 24 which are weak)
        assert any(
            f.direction == "negative"
            for f in result.values()
            if f.id.split(".")[-1].startswith("sav_house_")
        )


# ---------------------------------------------------------------------------
# Argument validation
# ---------------------------------------------------------------------------


class TestArgumentValidation:

    def test_invalid_asc_sign_raises(self, d1_chart):
        from app.reading.computations.ashtakavarga_reader import (
            read_ashtakavarga,
        )

        with pytest.raises(ValueError):
            read_ashtakavarga(d1_chart, asc_sign=0)
        with pytest.raises(ValueError):
            read_ashtakavarga(d1_chart, asc_sign=13)


# ---------------------------------------------------------------------------
# Pin: SAV-per-house aligns with rotated SAV-by-sign
# ---------------------------------------------------------------------------


class TestSAVHouseAlignment:
    """SAV house N corresponds to rashi ((asc_sign - 1 + N - 1) % 12) + 1."""

    def test_sav_house_1_matches_lagna_sign(self, d1_chart, asc_sign):
        """SAV at house 1 = SAV at the lagna sign."""
        from app.core.ashtakavarga import compute_ashtakavarga
        from app.reading.computations.ashtakavarga_reader import (
            read_ashtakavarga, _parse_bindus,
        )

        # build ascendant dict (the ashtakavarga API requires it)
        ascendant = {"sign": asc_sign}
        sav = compute_ashtakavarga(d1_chart, ascendant)["sav"]
        expected_bindus = sav[asc_sign - 1]

        result = read_ashtakavarga(d1_chart, asc_sign)
        h1 = result["sav_house_1"]
        assert _parse_bindus(h1) == expected_bindus
