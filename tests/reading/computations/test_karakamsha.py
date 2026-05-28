"""Tests for ``app.reading.computations.karakamsha``.

Karakamsha Lagna = the D9 (Navamsha) sign in which the Atmakaraka (AK) sits.

This is the single-Finding primitive emitted by ``compute_karakamsha``.
It depends on the karakas primitive (D-1 8-karaka Jaimini scheme).

Bangalore baseline (1990-07-15 12:00 IST / 12.97, 77.59):
    AK = Sun (degree 28.80 in Gemini, highest among 7+Rahu).
    Sun in D9 = Gemini (sign 3).
    => Karakamsha Lagna = Gemini.
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
def d9_chart(bangalore_chart) -> dict:
    return bangalore_chart["d9"]


class TestComputeKarakamsha:

    def test_returns_a_single_finding(self, d1_chart, d9_chart):
        from app.reading.computations.karakamsha import compute_karakamsha
        from app.reading.schema import Finding

        result = compute_karakamsha(d1_chart, d9_chart)
        assert isinstance(result, Finding)

    def test_id_grammar(self, d1_chart, d9_chart):
        from app.reading.computations.karakamsha import compute_karakamsha

        result = compute_karakamsha(d1_chart, d9_chart)
        assert result.id == "primitive.karakamsha.lagna"

    def test_classification_is_primitive(self, d1_chart, d9_chart):
        from app.reading.computations.karakamsha import compute_karakamsha

        result = compute_karakamsha(d1_chart, d9_chart)
        assert result.classification == "primitive"

    def test_verdict_under_140_chars(self, d1_chart, d9_chart):
        from app.reading.computations.karakamsha import compute_karakamsha

        result = compute_karakamsha(d1_chart, d9_chart)
        assert len(result.verdict) <= 140

    def test_verdict_mentions_karakamsha(self, d1_chart, d9_chart):
        from app.reading.computations.karakamsha import compute_karakamsha

        result = compute_karakamsha(d1_chart, d9_chart)
        assert "Karakamsha" in result.verdict


class TestBangaloreBaseline:
    """Bangalore: AK = Sun, Sun in D9 = Gemini."""

    def test_ak_is_sun(self, d1_chart, d9_chart):
        from app.reading.computations.karakamsha import compute_karakamsha

        result = compute_karakamsha(d1_chart, d9_chart)
        # Evidence carries the AK planet explicitly for machine-readable use.
        ak_lines = [
            line for line in result.evidence
            if line.startswith("ak_planet=")
        ]
        assert ak_lines, "result missing 'ak_planet=' evidence"
        assert ak_lines[0] == "ak_planet=Sun"

    def test_karakamsha_lagna_is_gemini(self, d1_chart, d9_chart):
        from app.reading.computations.karakamsha import compute_karakamsha

        result = compute_karakamsha(d1_chart, d9_chart)
        # Verdict like 'Karakamsha Lagna in Gemini (AK Sun in Gemini of D9)'
        assert "Gemini" in result.verdict, (
            f"expected Gemini in verdict, got {result.verdict!r}"
        )

    def test_karakamsha_sign_in_evidence(self, d1_chart, d9_chart):
        from app.reading.computations.karakamsha import compute_karakamsha

        result = compute_karakamsha(d1_chart, d9_chart)
        sign_lines = [
            line for line in result.evidence
            if line.startswith("karakamsha_sign=")
        ]
        assert sign_lines, "result missing 'karakamsha_sign=' evidence"
        sign_n = int(sign_lines[0].split("=", 1)[1])
        assert sign_n == 3, f"expected Gemini (sign 3), got {sign_n}"


class TestProperties:

    def test_karakamsha_sign_in_valid_range(self, d1_chart, d9_chart):
        """The Karakamsha Lagna sign must be in 1..12 (Aries..Pisces)."""
        from app.reading.computations.karakamsha import compute_karakamsha

        result = compute_karakamsha(d1_chart, d9_chart)
        sign_lines = [
            line for line in result.evidence
            if line.startswith("karakamsha_sign=")
        ]
        assert sign_lines
        sign_n = int(sign_lines[0].split("=", 1)[1])
        assert 1 <= sign_n <= 12, (
            f"karakamsha_sign {sign_n} out of range 1..12"
        )

    def test_ak_sign_in_d9_matches_planet_d9_entry(self, d1_chart, d9_chart):
        """Sanity: the Karakamsha sign emitted MUST equal the AK planet's
        actual D9 sign."""
        from app.reading.computations.karakamsha import compute_karakamsha

        result = compute_karakamsha(d1_chart, d9_chart)
        ak_planet = next(
            line.split("=", 1)[1] for line in result.evidence
            if line.startswith("ak_planet=")
        )
        karakamsha_sign = int(
            next(line.split("=", 1)[1] for line in result.evidence
                 if line.startswith("karakamsha_sign="))
        )
        actual_d9_sign = d9_chart[ak_planet]["sign"]
        assert karakamsha_sign == actual_d9_sign, (
            f"karakamsha_sign {karakamsha_sign} does not match "
            f"actual D9 sign {actual_d9_sign} for AK {ak_planet}"
        )
