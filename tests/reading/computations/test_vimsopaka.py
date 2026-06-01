"""Tests for ``app.reading.computations.vimsopaka``.

Doctrine lock D-3: Shodashavarga (16-varga) scheme with canonical
BPHS Ch.7 vv.21-25 weights summing to **exactly 20.0**.

Per the spec dignity coefficients:
    Exalted / Moolatrikona / Own sign  -> 1.0  (full)
    Friend's sign                       -> 0.5  (half)
    Neutral                             -> 0.25 (quarter)
    Enemy / Debilitated                 -> 0.0  (nil)

For each planet, the Vimsopaka score = sum over 16 vargas of
    (varga_weight * dignity_coefficient(planet, varga_sign))
yielding a score in [0.0, 20.0].
"""
from __future__ import annotations

import pytest


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
def varga_charts_by_divisor(d1_chart) -> dict[int, dict]:
    """Compose the 16-varga input dict keyed by divisor.

    For each planet, key 1 is the D1 chart entry; keys 2,3,4,7,9,10,12,16,
    20,24,27,30,40,45,60 come from compute_divisional_charts (D2..D60).
    """
    from app.core.shodashavarga import (
        SHODASHAVARGA_NAMES,
        compute_divisional_charts,
    )

    div_charts = compute_divisional_charts(d1_chart)
    out: dict[int, dict] = {1: d1_chart}
    # SHODASHAVARGA_NAMES is keyed by divisor 1..60.
    for divisor, name in SHODASHAVARGA_NAMES.items():
        if divisor == 1:
            continue
        out[divisor] = div_charts[name]
    return out


# ---------------------------------------------------------------------------
# Hard invariants
# ---------------------------------------------------------------------------


class TestWeightSumInvariant:
    """D-3 invariant: VIMSOPAKA_WEIGHTS_SHODASHAVARGA must sum to EXACTLY 20.0."""

    def test_weights_sum_to_20(self):
        from app.reading.computations.vimsopaka import (
            VIMSOPAKA_WEIGHTS_SHODASHAVARGA,
        )

        total = sum(VIMSOPAKA_WEIGHTS_SHODASHAVARGA.values())
        assert abs(total - 20.0) < 1e-9, (
            f"weights must sum to 20.0 by D-3 invariant, got {total!r}"
        )

    def test_weights_cover_16_vargas(self):
        from app.reading.computations.vimsopaka import (
            VIMSOPAKA_WEIGHTS_SHODASHAVARGA,
        )

        assert len(VIMSOPAKA_WEIGHTS_SHODASHAVARGA) == 16

    def test_weights_match_doctrine_lockfile(self):
        """Per D-3 (revision 1) the canonical table is exactly this."""
        from app.reading.computations.vimsopaka import (
            VIMSOPAKA_WEIGHTS_SHODASHAVARGA,
        )

        expected = {
            1: 3.5, 2: 1.0, 3: 1.0, 4: 0.5, 7: 0.5, 9: 3.0, 10: 0.5,
            12: 0.5, 16: 2.0, 20: 0.5, 24: 0.5, 27: 0.5, 30: 1.0,
            40: 0.5, 45: 0.5, 60: 4.0,
        }
        assert dict(VIMSOPAKA_WEIGHTS_SHODASHAVARGA) == expected


# ---------------------------------------------------------------------------
# Shape / output contract
# ---------------------------------------------------------------------------


class TestComputeVimsopaka:

    def test_returns_mapping(self, d1_chart, varga_charts_by_divisor):
        from app.reading.computations.vimsopaka import compute_vimsopaka

        result = compute_vimsopaka(d1_chart, varga_charts_by_divisor)
        assert isinstance(result, dict)

    def test_one_finding_per_natal_planet(
        self, d1_chart, varga_charts_by_divisor
    ):
        from app.reading.computations.vimsopaka import compute_vimsopaka

        result = compute_vimsopaka(d1_chart, varga_charts_by_divisor)
        # All seven natural lights + Rahu + Ketu = 9 planets in Bangalore D1.
        for planet in (
            "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"
        ):
            assert planet in result, (
                f"missing Vimsopaka Finding for {planet}"
            )

    def test_findings_are_finding_instances(
        self, d1_chart, varga_charts_by_divisor
    ):
        from app.reading.computations.vimsopaka import compute_vimsopaka
        from app.reading.schema import Finding

        result = compute_vimsopaka(d1_chart, varga_charts_by_divisor)
        for planet, finding in result.items():
            assert isinstance(finding, Finding), (
                f"{planet} did not return a Finding"
            )

    def test_id_grammar(self, d1_chart, varga_charts_by_divisor):
        from app.reading.computations.vimsopaka import compute_vimsopaka

        result = compute_vimsopaka(d1_chart, varga_charts_by_divisor)
        for planet, finding in result.items():
            assert finding.id == f"primitive.vimsopaka.{planet.lower()}", (
                f"unexpected id {finding.id!r} for planet {planet!r}"
            )

    def test_classification_is_primitive(
        self, d1_chart, varga_charts_by_divisor
    ):
        from app.reading.computations.vimsopaka import compute_vimsopaka

        result = compute_vimsopaka(d1_chart, varga_charts_by_divisor)
        for finding in result.values():
            assert finding.classification == "primitive"

    def test_verdict_under_140_chars(self, d1_chart, varga_charts_by_divisor):
        from app.reading.computations.vimsopaka import compute_vimsopaka

        result = compute_vimsopaka(d1_chart, varga_charts_by_divisor)
        for finding in result.values():
            assert len(finding.verdict) <= 140

    def test_verdict_mentions_score(self, d1_chart, varga_charts_by_divisor):
        from app.reading.computations.vimsopaka import compute_vimsopaka

        result = compute_vimsopaka(d1_chart, varga_charts_by_divisor)
        for finding in result.values():
            assert "Vimsopaka" in finding.verdict


# ---------------------------------------------------------------------------
# Numerical properties
# ---------------------------------------------------------------------------


class TestVimsopakaProperties:

    def test_score_in_valid_range(self, d1_chart, varga_charts_by_divisor):
        """Every planet's score must be in [0.0, 20.0] inclusive."""
        from app.reading.computations.vimsopaka import compute_vimsopaka

        result = compute_vimsopaka(d1_chart, varga_charts_by_divisor)
        for planet, finding in result.items():
            score_str = next(
                line.split("=", 1)[1] for line in finding.evidence
                if line.startswith("score=")
            )
            score = float(score_str)
            assert 0.0 <= score <= 20.0, (
                f"{planet} Vimsopaka score {score} out of [0, 20]"
            )

    def test_synthetic_all_exalted_yields_20(self):
        """If a planet is exalted/own/MT in EVERY varga, score = 20.0."""
        from app.reading.computations.vimsopaka import (
            VIMSOPAKA_WEIGHTS_SHODASHAVARGA,
            compute_vimsopaka,
        )

        # Synthetic: a planet "Sun" with sign 5 (its own sign Leo) in EVERY
        # varga chart. We must build a fake d1 + 15 varga charts that all
        # place Sun in Leo.
        sun_pos = {
            "longitude": 130.0,  # mid-Leo
            "sign": 5,
            "sign_name": "Leo",
            "degree_in_sign": 10.0,
            "is_retrograde": False,
            "name": "Sun",
        }
        synthetic_d1 = {"Sun": sun_pos}
        varga_in = {div: {"Sun": dict(sun_pos)} for div in VIMSOPAKA_WEIGHTS_SHODASHAVARGA}

        result = compute_vimsopaka(synthetic_d1, varga_in)
        finding = result["Sun"]
        score = float(next(
            line.split("=", 1)[1] for line in finding.evidence
            if line.startswith("score=")
        ))
        # Sun owns Leo -> coefficient 1.0 in every varga. score = sum of
        # weights = 20.0.
        assert abs(score - 20.0) < 1e-9, f"expected 20.0, got {score}"

    def test_synthetic_all_debilitated_yields_0(self):
        """If a planet is debilitated in EVERY varga, score = 0.0."""
        from app.reading.computations.vimsopaka import (
            VIMSOPAKA_WEIGHTS_SHODASHAVARGA,
            compute_vimsopaka,
        )

        # Sun is debilitated in Libra (sign 7). Build a synthetic input
        # placing Sun in Libra in every varga.
        sun_pos = {
            "longitude": 190.0,  # mid-Libra
            "sign": 7,
            "sign_name": "Libra",
            "degree_in_sign": 10.0,
            "is_retrograde": False,
            "name": "Sun",
        }
        synthetic_d1 = {"Sun": sun_pos}
        varga_in = {div: {"Sun": dict(sun_pos)} for div in VIMSOPAKA_WEIGHTS_SHODASHAVARGA}

        result = compute_vimsopaka(synthetic_d1, varga_in)
        finding = result["Sun"]
        score = float(next(
            line.split("=", 1)[1] for line in finding.evidence
            if line.startswith("score=")
        ))
        # Sun in Libra = debilitated -> coefficient 0.0 in every varga.
        assert abs(score - 0.0) < 1e-9, f"expected 0.0, got {score}"


# ---------------------------------------------------------------------------
# Import-time invariant
# ---------------------------------------------------------------------------


class TestImportTimeInvariant:

    def test_module_import_does_not_raise(self):
        """If the D-3 weight sum was wrong, import should fail loudly."""
        # Just importing already runs the assert at module top-level. The
        # test exists so a future weight-table edit that breaks the sum
        # produces a clear, attributable failure.
        import app.reading.computations.vimsopaka as v
        assert hasattr(v, "VIMSOPAKA_WEIGHTS_SHODASHAVARGA")
