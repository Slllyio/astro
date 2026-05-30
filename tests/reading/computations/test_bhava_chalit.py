"""Tests for ``app.reading.computations.bhava_chalit``.

Doctrine lock D-8 (``docs/doctrine-decisions.md``):

    Use the Sripati system (BPHS Vol.II Ch.51) for the Bhava Chalit chart.
    The Lagna degree IS the bhava-madhya of house 1. House N's madhya
    sits at ``(lagna_deg + (N-1) * 30) mod 360``. Sandhi at madhya +/- 15.
    A planet's chalit-bhava is the bhava whose sandhi-bounded arc contains
    the planet's sidereal longitude.

Algorithm summary
=================

For a planet at sidereal longitude ``lon`` and Lagna at degree ``L``
(absolute longitude in 0..360):

    chalit_bhava = floor(((lon - (L - 15)) mod 360) / 30) + 1

Equivalently: shift the reference so that the **start of bhava-1
sandhi** is at zero, divide the circle into 12 sectors of 30 degrees
each, and pick the sector index.

A planet's rashi-house (from existing engine) is the whole-sign house
from the Lagna's rashi. The chalit-bhava can differ from the rashi-house
when the planet sits within +/- 15 degrees of an adjacent bhava madhya.

Output direction (per spec D-8):
- ``positive`` if chalit-bhava != rashi-bhava (significant shift detected)
- ``neutral`` if chalit-bhava == rashi-bhava (no shift)

Bangalore baseline pins (Virgo Lagna at ~173.99 deg sidereal):

  - Mars at Aries 8.06 deg (~8.06 abs): rashi-house 8, chalit-bhava 7
    (Mars is just past the lagna-madhya by ~14 deg in the "previous"
    direction, which puts it in bhava 7 — the rashi shift is the whole
    point of the chalit chart.)
  - Sun at Gemini 28.80 deg (~88.80 abs): rashi-house 10, chalit-bhava
    10 (no shift, Sun sits comfortably in its bhava).
"""
from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import strategies as st


# ---------------------------------------------------------------------------
# Bangalore baseline fixture (shared with other reading-layer tests)
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
def lagna_abs_lon(bangalore_chart) -> float:
    """Absolute (0..360) sidereal Lagna longitude."""
    return float(bangalore_chart["ascendant"]["longitude"])


@pytest.fixture(scope="module")
def asc_sign(bangalore_chart) -> int:
    return int(bangalore_chart["ascendant"]["sign"])


# ---------------------------------------------------------------------------
# Shape / construction
# ---------------------------------------------------------------------------


class TestComputeBhavaChalit:

    def test_returns_mapping_per_planet(
        self, d1_chart, lagna_abs_lon, asc_sign,
    ):
        from app.reading.computations.bhava_chalit import compute_bhava_chalit

        result = compute_bhava_chalit(d1_chart, lagna_abs_lon, asc_sign)
        assert isinstance(result, dict)
        assert set(result.keys()) == set(d1_chart.keys())

    def test_emits_findings(self, d1_chart, lagna_abs_lon, asc_sign):
        from app.reading.computations.bhava_chalit import compute_bhava_chalit
        from app.reading.schema import Finding

        result = compute_bhava_chalit(d1_chart, lagna_abs_lon, asc_sign)
        for planet, finding in result.items():
            assert isinstance(finding, Finding), (
                f"{planet} value is not a Finding"
            )

    def test_id_grammar(self, d1_chart, lagna_abs_lon, asc_sign):
        from app.reading.computations.bhava_chalit import compute_bhava_chalit

        result = compute_bhava_chalit(d1_chart, lagna_abs_lon, asc_sign)
        for planet, finding in result.items():
            assert finding.id == (
                f"foundation.bhava_chalit.{planet.lower()}"
            ), f"unexpected id {finding.id!r}"

    def test_classification_is_primitive(
        self, d1_chart, lagna_abs_lon, asc_sign,
    ):
        from app.reading.computations.bhava_chalit import compute_bhava_chalit

        result = compute_bhava_chalit(d1_chart, lagna_abs_lon, asc_sign)
        for finding in result.values():
            assert finding.classification == "primitive"

    def test_verdict_under_140_chars(
        self, d1_chart, lagna_abs_lon, asc_sign,
    ):
        from app.reading.computations.bhava_chalit import compute_bhava_chalit

        result = compute_bhava_chalit(d1_chart, lagna_abs_lon, asc_sign)
        for finding in result.values():
            assert len(finding.verdict) <= 140


# ---------------------------------------------------------------------------
# Sripati formula correctness
# ---------------------------------------------------------------------------


class TestFormulaCorrectness:
    """Verify the Sripati cusp formula at canonical boundary points."""

    def test_planet_at_lagna_is_bhava_1(self):
        """A planet at exactly the Lagna degree -> chalit-bhava 1."""
        from app.reading.computations.bhava_chalit import compute_bhava_chalit

        # Lagna at Aries 10 deg (abs 10 deg), planet right at lagna.
        chart = {
            "Sun": {
                "longitude": 10.0, "sign": 1, "degree_in_sign": 10.0,
                "is_retrograde": False, "house": 1,
            },
        }
        result = compute_bhava_chalit(chart, lagna_abs_lon=10.0, asc_sign=1)
        assert _parse_chalit(result["Sun"]) == 1

    def test_planet_at_lagna_plus_30_is_bhava_2(self):
        """A planet exactly 30 deg past the Lagna -> chalit-bhava 2."""
        from app.reading.computations.bhava_chalit import compute_bhava_chalit

        chart = {
            "Sun": {
                "longitude": 40.0, "sign": 2, "degree_in_sign": 10.0,
                "is_retrograde": False, "house": 2,
            },
        }
        result = compute_bhava_chalit(chart, lagna_abs_lon=10.0, asc_sign=1)
        assert _parse_chalit(result["Sun"]) == 2

    def test_planet_within_15deg_of_lagna_is_bhava_1(self):
        """A planet within +/- 15 deg of the Lagna degree -> bhava 1.

        Specifically the spec example: Lagna in Virgo at 28 deg
        (abs ~178), planet in Libra at 5 deg (abs 185). The planet is
        in rashi-house 2 (Libra from Virgo) but chalit-bhava 1
        (within 15 deg of lagna-madhya).
        """
        from app.reading.computations.bhava_chalit import compute_bhava_chalit

        chart = {
            "Sun": {
                "longitude": 185.0, "sign": 7, "degree_in_sign": 5.0,
                "is_retrograde": False, "house": 2,
            },
        }
        result = compute_bhava_chalit(
            chart, lagna_abs_lon=178.0, asc_sign=6,  # Virgo lagna
        )
        # planet is +7 deg from madhya of house 1; sandhi at +15 deg.
        assert _parse_chalit(result["Sun"]) == 1
        # rashi-house Libra-from-Virgo = 2; chalit = 1; SHIFTED
        # direction should be 'positive' (significant shift).
        assert result["Sun"].direction == "positive"

    def test_planet_just_past_15deg_is_bhava_2(self):
        """A planet at 15.001 deg past Lagna -> chalit-bhava 2."""
        from app.reading.computations.bhava_chalit import compute_bhava_chalit

        # Lagna at 10.0, planet at 25.01 (15.01 deg past).
        chart = {
            "Sun": {
                "longitude": 25.01, "sign": 1, "degree_in_sign": 25.01,
                "is_retrograde": False, "house": 1,
            },
        }
        result = compute_bhava_chalit(chart, lagna_abs_lon=10.0, asc_sign=1)
        assert _parse_chalit(result["Sun"]) == 2

    def test_planet_just_before_lagna_is_bhava_12(self):
        """A planet 16 deg before Lagna -> chalit-bhava 12."""
        from app.reading.computations.bhava_chalit import compute_bhava_chalit

        # Lagna at 100.0, planet at 84.0 (16 deg before).
        chart = {
            "Sun": {
                "longitude": 84.0, "sign": 3, "degree_in_sign": 24.0,
                "is_retrograde": False, "house": 12,
            },
        }
        result = compute_bhava_chalit(chart, lagna_abs_lon=100.0, asc_sign=4)
        assert _parse_chalit(result["Sun"]) == 12

    def test_lagna_wrap_through_zero_degrees(self):
        """Lagna near 0/360 boundary: planet 'before' Lagna at 349.99,
        Lagna at 5 -> chalit-bhava 12 (wraparound past -15 deg sandhi).

        Half-open sandhi convention: the LOWER sandhi (lagna - 15) belongs
        to bhava-1 (inclusive); the UPPER sandhi (lagna + 15) belongs to
        bhava-2 (exclusive for bhava-1). So a planet at 349.99 (16.01 deg
        before lagna 5) is in bhava 12.
        """
        from app.reading.computations.bhava_chalit import compute_bhava_chalit

        chart = {
            "Sun": {
                "longitude": 349.99, "sign": 12, "degree_in_sign": 19.99,
                "is_retrograde": False, "house": 12,
            },
        }
        result = compute_bhava_chalit(chart, lagna_abs_lon=5.0, asc_sign=1)
        bhava = _parse_chalit(result["Sun"])
        assert bhava == 12, f"expected 12 at -16.01 deg, got {bhava}"

    def test_planet_at_lagna_plus_180_is_bhava_7(self):
        """Planet exactly opposite the Lagna -> chalit-bhava 7."""
        from app.reading.computations.bhava_chalit import compute_bhava_chalit

        chart = {
            "Sun": {
                "longitude": 190.0, "sign": 7, "degree_in_sign": 10.0,
                "is_retrograde": False, "house": 7,
            },
        }
        result = compute_bhava_chalit(chart, lagna_abs_lon=10.0, asc_sign=1)
        assert _parse_chalit(result["Sun"]) == 7

    def test_planet_exactly_at_29deg_cusp(self):
        """A planet exactly at madhya + 14.999 deg -> still in same bhava;
        +15.001 -> next bhava. Sandhi cusp."""
        from app.reading.computations.bhava_chalit import compute_bhava_chalit

        # Lagna at 10; bhava 1 madhya = 10, sandhi 25.
        chart = {
            "Sun": {
                "longitude": 24.999, "sign": 1, "degree_in_sign": 24.999,
                "is_retrograde": False, "house": 1,
            },
        }
        result = compute_bhava_chalit(chart, lagna_abs_lon=10.0, asc_sign=1)
        assert _parse_chalit(result["Sun"]) == 1


# ---------------------------------------------------------------------------
# Direction semantics: shift detection
# ---------------------------------------------------------------------------


class TestShiftDetection:
    """The whole point of the chalit chart: detect when a planet's
    chalit-bhava differs from its rashi-house."""

    def test_no_shift_planet_in_middle_of_rashi(self):
        """A planet near the centre of its rashi (15 deg in sign)
        is in the same chalit-bhava as rashi-bhava."""
        from app.reading.computations.bhava_chalit import compute_bhava_chalit

        # Lagna at 10.0 (Aries); planet at Aries 15 -> rashi=1, chalit=1.
        chart = {
            "Sun": {
                "longitude": 15.0, "sign": 1, "degree_in_sign": 15.0,
                "is_retrograde": False, "house": 1,
            },
        }
        result = compute_bhava_chalit(chart, lagna_abs_lon=10.0, asc_sign=1)
        assert result["Sun"].direction == "neutral"
        assert _parse_rashi(result["Sun"]) == _parse_chalit(result["Sun"])

    def test_shift_planet_at_sign_boundary(self):
        """A planet near a sign boundary often shifts chalit-bhava
        vs rashi-bhava."""
        from app.reading.computations.bhava_chalit import compute_bhava_chalit

        # Lagna at Aries 25; planet at Taurus 5. Rashi: Taurus from
        # Aries-lagna = house 2. Chalit: planet is 10 deg past lagna
        # (25 -> 35), within +/- 15 of lagna-madhya -> bhava 1.
        chart = {
            "Sun": {
                "longitude": 35.0, "sign": 2, "degree_in_sign": 5.0,
                "is_retrograde": False, "house": 2,
            },
        }
        result = compute_bhava_chalit(chart, lagna_abs_lon=25.0, asc_sign=1)
        assert _parse_rashi(result["Sun"]) == 2
        assert _parse_chalit(result["Sun"]) == 1
        assert result["Sun"].direction == "positive"


class TestBangaloreBaseline:
    """Pin specific chalit-bhava values for the Bangalore baseline chart.

    Bangalore Lagna: Virgo (sign 6) at degree-in-sign 23.988
    => absolute Lagna longitude ~173.988.
    """

    def test_lagna_is_virgo_around_174deg(
        self, lagna_abs_lon, asc_sign,
    ):
        # Sanity: confirm the baseline.
        assert asc_sign == 6
        assert abs(lagna_abs_lon - 173.988) < 0.1

    def test_mars_chalit_bhava_7(
        self, d1_chart, lagna_abs_lon, asc_sign,
    ):
        """Mars at Aries 8.06 deg (abs ~8.06): rashi-house 8 (Aries from
        Virgo), chalit-bhava 7 (Mars is 14 deg before lagna-madhya — sits
        in the latter half of bhava 7 by the Sripati formula)."""
        from app.reading.computations.bhava_chalit import compute_bhava_chalit

        result = compute_bhava_chalit(d1_chart, lagna_abs_lon, asc_sign)
        chalit = _parse_chalit(result["Mars"])
        rashi = _parse_rashi(result["Mars"])
        assert rashi == 8
        assert chalit == 7
        assert result["Mars"].direction == "positive"

    def test_sun_no_shift(
        self, d1_chart, lagna_abs_lon, asc_sign,
    ):
        """Sun at Gemini 28.80 deg (abs ~88.80): bhava 10 in both."""
        from app.reading.computations.bhava_chalit import compute_bhava_chalit

        result = compute_bhava_chalit(d1_chart, lagna_abs_lon, asc_sign)
        chalit = _parse_chalit(result["Sun"])
        rashi = _parse_rashi(result["Sun"])
        assert rashi == 10
        assert chalit == 10
        assert result["Sun"].direction == "neutral"


# ---------------------------------------------------------------------------
# Validation / error paths
# ---------------------------------------------------------------------------


class TestInputValidation:

    def test_invalid_lagna_longitude_raises(self):
        from app.reading.computations.bhava_chalit import compute_bhava_chalit

        chart = {
            "Sun": {
                "longitude": 10.0, "sign": 1, "degree_in_sign": 10.0,
                "is_retrograde": False, "house": 1,
            },
        }
        with pytest.raises(ValueError):
            compute_bhava_chalit(chart, lagna_abs_lon=-1.0, asc_sign=1)
        with pytest.raises(ValueError):
            compute_bhava_chalit(chart, lagna_abs_lon=361.0, asc_sign=1)

    def test_invalid_asc_sign_raises(self):
        from app.reading.computations.bhava_chalit import compute_bhava_chalit

        chart = {
            "Sun": {
                "longitude": 10.0, "sign": 1, "degree_in_sign": 10.0,
                "is_retrograde": False, "house": 1,
            },
        }
        with pytest.raises(ValueError):
            compute_bhava_chalit(chart, lagna_abs_lon=10.0, asc_sign=0)
        with pytest.raises(ValueError):
            compute_bhava_chalit(chart, lagna_abs_lon=10.0, asc_sign=13)

    def test_missing_longitude_raises(self):
        from app.reading.computations.bhava_chalit import compute_bhava_chalit

        chart = {"Sun": {"sign": 1, "is_retrograde": False, "house": 1}}
        with pytest.raises(KeyError):
            compute_bhava_chalit(chart, lagna_abs_lon=10.0, asc_sign=1)


# ---------------------------------------------------------------------------
# Property-based invariants
# ---------------------------------------------------------------------------


_PLANET_NAMES = (
    "Sun", "Moon", "Mars", "Mercury",
    "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)


@st.composite
def _synthetic_d1(draw):
    return {
        name: {
            "longitude": draw(st.floats(min_value=0.0, max_value=359.999)),
            "sign": draw(st.integers(min_value=1, max_value=12)),
            "degree_in_sign": draw(
                st.floats(min_value=0.0, max_value=29.999)
            ),
            "is_retrograde": False,
            "house": draw(st.integers(min_value=1, max_value=12)),
        }
        for name in _PLANET_NAMES
    }


class TestPropertyInvariants:

    @given(
        d1=_synthetic_d1(),
        lagna=st.floats(min_value=0.0, max_value=359.999),
        asc=st.integers(min_value=1, max_value=12),
    )
    def test_every_planet_in_a_valid_bhava(self, d1, lagna, asc):
        """Every planet must end up in a bhava 1..12."""
        from app.reading.computations.bhava_chalit import compute_bhava_chalit

        result = compute_bhava_chalit(d1, lagna, asc)
        for finding in result.values():
            bhava = _parse_chalit(finding)
            assert 1 <= bhava <= 12

    @given(
        d1=_synthetic_d1(),
        lagna=st.floats(min_value=0.0, max_value=359.999),
        asc=st.integers(min_value=1, max_value=12),
    )
    def test_directions_are_valid(self, d1, lagna, asc):
        from app.reading.computations.bhava_chalit import compute_bhava_chalit

        result = compute_bhava_chalit(d1, lagna, asc)
        for finding in result.values():
            assert finding.direction in {"positive", "negative", "neutral", "mixed"}

    @given(
        d1=_synthetic_d1(),
        lagna=st.floats(min_value=0.0, max_value=359.999),
        asc=st.integers(min_value=1, max_value=12),
    )
    def test_ids_unique(self, d1, lagna, asc):
        from app.reading.computations.bhava_chalit import compute_bhava_chalit

        result = compute_bhava_chalit(d1, lagna, asc)
        ids = [f.id for f in result.values()]
        assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_chalit(finding) -> int:
    """Extract ``chalit_bhava=`` from a Finding's evidence list."""
    for line in finding.evidence:
        if line.startswith("chalit_bhava="):
            return int(line.split("=", 1)[1])
    raise AssertionError(
        f"finding {finding.id!r} missing 'chalit_bhava=' evidence line; "
        f"evidence={finding.evidence!r}"
    )


def _parse_rashi(finding) -> int:
    """Extract ``rashi_bhava=`` from a Finding's evidence list."""
    for line in finding.evidence:
        if line.startswith("rashi_bhava="):
            return int(line.split("=", 1)[1])
    raise AssertionError(
        f"finding {finding.id!r} missing 'rashi_bhava=' evidence line; "
        f"evidence={finding.evidence!r}"
    )
