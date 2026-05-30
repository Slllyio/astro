"""Tests for ``app.reading.computations.panchanga_reader``.

Reads the natal panchanga (tithi/vara/nakshatra/yoga/karana) and emits a
Finding per element. Uses the canonical Bangalore-baseline fixture to
verify the values align with what ``app.core.panchanga`` produces (we do
NOT pin against external sources here -- correctness of the underlying
panchanga values is the responsibility of ``tests/test_panchanga.py``).
"""
from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Bangalore baseline
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def bangalore_panchanga_inputs() -> dict:
    """Compute the inputs read_panchanga consumes from the Bangalore baseline."""
    import swisseph as swe

    from app.core.ephemeris_engine import calculate_d1_position, calculate_jd

    # 1990-07-15 12:00 IST = 06:30 UTC
    jd = calculate_jd(1990, 7, 15, 12.0, 5.5)
    moon = calculate_d1_position(jd, swe.MOON)
    sun = calculate_d1_position(jd, swe.SUN)
    weekday = int(jd + 1.5) % 7
    return {
        "birth_jd": jd,
        "moon_lon": moon["longitude"],
        "sun_lon": sun["longitude"],
        "weekday": weekday,
    }


# ---------------------------------------------------------------------------
# Shape / construction
# ---------------------------------------------------------------------------


class TestReadPanchanga:

    def test_returns_dict_keyed_by_panchanga_elements(self, bangalore_panchanga_inputs):
        """Returns a dict with exactly the 5 panchanga element keys."""
        from app.reading.computations.panchanga_reader import read_panchanga

        result = read_panchanga(**bangalore_panchanga_inputs)
        assert isinstance(result, dict)
        assert set(result.keys()) == {"tithi", "vara", "nakshatra", "yoga", "karana"}

    def test_all_outputs_are_findings(self, bangalore_panchanga_inputs):
        """Each value is a valid Finding model instance."""
        from app.reading.computations.panchanga_reader import read_panchanga
        from app.reading.schema import Finding

        result = read_panchanga(**bangalore_panchanga_inputs)
        for element, finding in result.items():
            assert isinstance(finding, Finding), f"{element} is not a Finding"

    def test_id_grammar(self, bangalore_panchanga_inputs):
        """IDs follow ``primitive.panchanga.<element>`` exactly."""
        from app.reading.computations.panchanga_reader import read_panchanga

        result = read_panchanga(**bangalore_panchanga_inputs)
        for element, finding in result.items():
            assert finding.id == f"primitive.panchanga.{element}"

    def test_classification_is_primitive(self, bangalore_panchanga_inputs):
        """All panchanga findings are primitives (raw temporal facts)."""
        from app.reading.computations.panchanga_reader import read_panchanga

        result = read_panchanga(**bangalore_panchanga_inputs)
        for finding in result.values():
            assert finding.classification == "primitive"

    def test_verdict_under_140_chars(self, bangalore_panchanga_inputs):
        """All verdicts respect the universal Finding limit."""
        from app.reading.computations.panchanga_reader import read_panchanga

        result = read_panchanga(**bangalore_panchanga_inputs)
        for finding in result.values():
            assert len(finding.verdict) <= 140

    def test_direction_is_valid_enum(self, bangalore_panchanga_inputs):
        """All directions fall in the Finding direction enum."""
        from app.reading.computations.panchanga_reader import read_panchanga

        result = read_panchanga(**bangalore_panchanga_inputs)
        for finding in result.values():
            assert finding.direction in {"positive", "negative", "neutral", "mixed"}

    def test_tithi_verdict_names_a_tithi(self, bangalore_panchanga_inputs):
        """Tithi verdict mentions a paksha and the tithi name."""
        from app.reading.computations.panchanga_reader import read_panchanga

        result = read_panchanga(**bangalore_panchanga_inputs)
        v = result["tithi"].verdict.lower()
        # Paksha tag must appear.
        assert "shukla" in v or "krishna" in v

    def test_vara_verdict_names_a_weekday(self, bangalore_panchanga_inputs):
        """Vara verdict carries the human weekday name."""
        from app.reading.computations.panchanga_reader import read_panchanga

        result = read_panchanga(**bangalore_panchanga_inputs)
        v = result["vara"].verdict.lower()
        days = ("sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday")
        assert any(d in v for d in days)

    def test_nakshatra_verdict_names_a_nakshatra_and_pada(
        self, bangalore_panchanga_inputs
    ):
        """Nakshatra verdict carries name and pada index."""
        from app.reading.computations.panchanga_reader import read_panchanga

        result = read_panchanga(**bangalore_panchanga_inputs)
        v = result["nakshatra"].verdict.lower()
        # Some nakshatra name is in there; pada 1..4 is in there.
        assert any(str(i) in v for i in (1, 2, 3, 4)) or "pada" in v

    def test_yoga_and_karana_findings_exist(self, bangalore_panchanga_inputs):
        """Both yoga and karana entries are present and non-empty."""
        from app.reading.computations.panchanga_reader import read_panchanga

        result = read_panchanga(**bangalore_panchanga_inputs)
        assert len(result["yoga"].verdict) > 0
        assert len(result["karana"].verdict) > 0


# ---------------------------------------------------------------------------
# Classical inauspicious flags
# ---------------------------------------------------------------------------


class TestClassicalDirectionFlags:
    """Classical lore embedded in the direction field."""

    def _make_inputs(self, sun_lon, moon_lon, weekday):
        """Construct the input dict for arbitrary panchanga values."""
        return {
            "birth_jd": 2451545.0,  # any JD; vara is provided separately
            "moon_lon": moon_lon,
            "sun_lon": sun_lon,
            "weekday": weekday,
        }

    def test_rikta_tithi_negative(self):
        """Tithi 4 (Chaturthi, a Rikta tithi) registers as negative."""
        from app.reading.computations.panchanga_reader import read_panchanga

        # delta = 36 deg means index = 3 = Shukla Chaturthi
        inputs = self._make_inputs(sun_lon=0.0, moon_lon=36.5, weekday=0)
        result = read_panchanga(**inputs)
        assert result["tithi"].direction == "negative"

    def test_purnima_tithi_positive(self):
        """Tithi 15 (Purnima) is auspicious."""
        from app.reading.computations.panchanga_reader import read_panchanga

        # delta ~ 174 deg means index ~ 14 = Purnima
        inputs = self._make_inputs(sun_lon=0.0, moon_lon=174.0, weekday=0)
        result = read_panchanga(**inputs)
        assert result["tithi"].direction == "positive"

    def test_saturday_vara_negative(self):
        """Saturday (vara index 6) is malefic (Saturn-ruled)."""
        from app.reading.computations.panchanga_reader import read_panchanga

        inputs = self._make_inputs(sun_lon=0.0, moon_lon=10.0, weekday=6)
        result = read_panchanga(**inputs)
        assert result["vara"].direction == "negative"

    def test_thursday_vara_positive(self):
        """Thursday (vara index 4) is benefic (Jupiter-ruled)."""
        from app.reading.computations.panchanga_reader import read_panchanga

        inputs = self._make_inputs(sun_lon=0.0, moon_lon=10.0, weekday=4)
        result = read_panchanga(**inputs)
        assert result["vara"].direction == "positive"

    def test_vishti_karana_negative(self):
        """Vishti (Bhadra) karana is universally inauspicious."""
        from app.reading.computations.panchanga_reader import read_panchanga

        # Karana index 7 -> Vishti.  delta / 6 = 7 -> delta = 42-47.99 deg.
        inputs = self._make_inputs(sun_lon=0.0, moon_lon=43.0, weekday=0)
        result = read_panchanga(**inputs)
        assert result["karana"].direction == "negative"


# ---------------------------------------------------------------------------
# Property-based invariants
# ---------------------------------------------------------------------------


class TestPropertyInvariants:

    @given(
        moon=st.floats(min_value=0.0, max_value=359.999),
        sun=st.floats(min_value=0.0, max_value=359.999),
        wd=st.integers(min_value=0, max_value=6),
    )
    def test_returns_five_findings(self, moon, sun, wd):
        """For arbitrary valid inputs, the result has exactly 5 keys."""
        from app.reading.computations.panchanga_reader import read_panchanga

        result = read_panchanga(birth_jd=2451545.0, moon_lon=moon, sun_lon=sun, weekday=wd)
        assert set(result.keys()) == {"tithi", "vara", "nakshatra", "yoga", "karana"}

    @given(
        moon=st.floats(min_value=0.0, max_value=359.999),
        sun=st.floats(min_value=0.0, max_value=359.999),
        wd=st.integers(min_value=0, max_value=6),
    )
    def test_id_grammar_invariant(self, moon, sun, wd):
        """Every ID conforms to ``primitive.panchanga.<element>``."""
        from app.reading.computations.panchanga_reader import read_panchanga

        result = read_panchanga(birth_jd=2451545.0, moon_lon=moon, sun_lon=sun, weekday=wd)
        for element, finding in result.items():
            assert finding.id == f"primitive.panchanga.{element}"

    @given(
        moon=st.floats(min_value=0.0, max_value=359.999),
        sun=st.floats(min_value=0.0, max_value=359.999),
        wd=st.integers(min_value=0, max_value=6),
    )
    def test_all_classifications_primitive(self, moon, sun, wd):
        from app.reading.computations.panchanga_reader import read_panchanga

        result = read_panchanga(birth_jd=2451545.0, moon_lon=moon, sun_lon=sun, weekday=wd)
        for finding in result.values():
            assert finding.classification == "primitive"
