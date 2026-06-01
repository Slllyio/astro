"""Tests for ``app.reading.computations.gulika``.

Doctrine lock D-6 (``docs/doctrine-decisions.md``):

    Gulika and Mandi are TWO DISTINCT upagrahas:
      * Gulika = ascendant at the START of Saturn's day/night segment.
      * Mandi  = ascendant at the MIDPOINT of the same segment.

Additional Saturn-derived auxiliary upagrahas (Yamakantaka, Kala) are
also surfaced for downstream sequences. These auxiliary outputs are
v1-stub-tolerant: structural conformance (Finding shape, IDs,
classification) is asserted; precise value pinning to BPHS Ch.5 tables
is deferred to a follow-up task.

Bangalore baseline (1990-07-15 12:00 IST / 12.97, 77.59) is used as the
canonical fixture.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Bangalore baseline fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def bangalore_chart() -> dict:
    from app.core.ephemeris_engine import calculate_all_charts

    return calculate_all_charts(
        year=1990, month=7, day=15, hour=12, minute=0,
        tz_offset=5.5, latitude=12.97, longitude=77.59,
    )


@pytest.fixture(scope="module")
def bangalore_inputs(bangalore_chart) -> dict:
    """Inputs the ``compute_gulika_and_mandi`` API needs."""
    # 1990-07-15 is a Sunday (weekday=0 with our 0=Sunday convention).
    return {
        "birth_jd": bangalore_chart["birth_jd"],
        "lat": 12.97,
        "lon": 77.59,
        "is_daytime": True,  # 12:00 IST is daytime in July at 12.97 N
        "weekday": 0,         # Sunday
    }


# ---------------------------------------------------------------------------
# Public-API + structural conformance
# ---------------------------------------------------------------------------


_EXPECTED_KEYS = {"gulika", "mandi", "yamakantaka", "kala"}


class TestComputeGulikaAndMandi:

    def test_returns_named_dict(self, bangalore_inputs):
        from app.reading.computations.gulika import compute_gulika_and_mandi

        result = compute_gulika_and_mandi(**bangalore_inputs)
        assert isinstance(result, dict)
        assert set(result.keys()) == _EXPECTED_KEYS

    def test_emits_findings(self, bangalore_inputs):
        from app.reading.computations.gulika import compute_gulika_and_mandi
        from app.reading.schema import Finding

        result = compute_gulika_and_mandi(**bangalore_inputs)
        for key, finding in result.items():
            assert isinstance(finding, Finding), f"{key} is not a Finding"

    def test_id_grammar(self, bangalore_inputs):
        from app.reading.computations.gulika import compute_gulika_and_mandi

        result = compute_gulika_and_mandi(**bangalore_inputs)
        for key, finding in result.items():
            assert finding.id == f"primitive.gulika.{key}"

    def test_classification_is_primitive(self, bangalore_inputs):
        from app.reading.computations.gulika import compute_gulika_and_mandi

        result = compute_gulika_and_mandi(**bangalore_inputs)
        for finding in result.values():
            assert finding.classification == "primitive"

    def test_verdict_under_140_chars(self, bangalore_inputs):
        from app.reading.computations.gulika import compute_gulika_and_mandi

        result = compute_gulika_and_mandi(**bangalore_inputs)
        for finding in result.values():
            assert len(finding.verdict) <= 140

    def test_gulika_and_mandi_distinct(self, bangalore_inputs):
        """D-6: Gulika and Mandi must be TWO DISTINCT upagrahas.

        Gulika is the START of Saturn's segment, Mandi the MIDPOINT —
        they must yield different longitudes for any non-degenerate
        input.
        """
        from app.reading.computations.gulika import compute_gulika_and_mandi

        result = compute_gulika_and_mandi(**bangalore_inputs)
        gulika_lon = _parse_longitude(result["gulika"])
        mandi_lon = _parse_longitude(result["mandi"])
        if gulika_lon is None or mandi_lon is None:
            # Stub mode tolerated — just ensure the verdicts are distinct.
            assert result["gulika"].verdict != result["mandi"].verdict
        else:
            assert abs(gulika_lon - mandi_lon) > 1e-6, (
                "Gulika START and Mandi MIDPOINT must yield distinct longitudes"
            )

    def test_gulika_longitude_in_range(self, bangalore_inputs):
        """When the implementation emits a numeric longitude, it must be
        in ``[0, 360)``."""
        from app.reading.computations.gulika import compute_gulika_and_mandi

        result = compute_gulika_and_mandi(**bangalore_inputs)
        for key, finding in result.items():
            lon = _parse_longitude(finding)
            if lon is not None:
                assert 0.0 <= lon < 360.0, (
                    f"{key} longitude {lon} out of [0, 360)"
                )

    def test_daytime_vs_nighttime_yields_distinct_gulika(self, bangalore_inputs):
        """Day-birth and night-birth on the same JD must produce different
        Gulika longitudes (since the segment-time anchor differs)."""
        from app.reading.computations.gulika import compute_gulika_and_mandi

        day_result = compute_gulika_and_mandi(**bangalore_inputs)
        night_inputs = {**bangalore_inputs, "is_daytime": False}
        night_result = compute_gulika_and_mandi(**night_inputs)

        day_lon = _parse_longitude(day_result["gulika"])
        night_lon = _parse_longitude(night_result["gulika"])

        if day_lon is not None and night_lon is not None:
            assert abs(day_lon - night_lon) > 1e-6, (
                "day-birth and night-birth Gulika longitudes must differ"
            )
        else:
            assert (
                day_result["gulika"].verdict
                != night_result["gulika"].verdict
            )


class TestInvalidInputs:

    def test_invalid_weekday_raises(self):
        from app.reading.computations.gulika import compute_gulika_and_mandi

        with pytest.raises(ValueError):
            compute_gulika_and_mandi(
                birth_jd=2448000.0,
                lat=12.97,
                lon=77.59,
                is_daytime=True,
                weekday=7,
            )

    def test_negative_weekday_raises(self):
        from app.reading.computations.gulika import compute_gulika_and_mandi

        with pytest.raises(ValueError):
            compute_gulika_and_mandi(
                birth_jd=2448000.0,
                lat=12.97,
                lon=77.59,
                is_daytime=True,
                weekday=-1,
            )


class TestWeekdays:
    """Cycling through all 7 weekdays must produce structurally valid output."""

    @pytest.mark.parametrize("wd", list(range(7)))
    def test_weekday_yields_complete_output(self, wd, bangalore_inputs):
        from app.reading.computations.gulika import compute_gulika_and_mandi

        inputs = {**bangalore_inputs, "weekday": wd}
        result = compute_gulika_and_mandi(**inputs)
        assert set(result.keys()) == _EXPECTED_KEYS
        for key, finding in result.items():
            # Structural: id grammar + classification.
            assert finding.id == f"primitive.gulika.{key}"
            assert finding.classification == "primitive"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_longitude(finding) -> float | None:
    """Extract a numeric ``longitude=`` from a Finding, or None if stub."""
    for line in finding.evidence:
        if line.startswith("longitude="):
            try:
                return float(line.split("=", 1)[1])
            except ValueError:
                return None
    return None
