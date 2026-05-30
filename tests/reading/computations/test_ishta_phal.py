"""Tests for ``app.reading.computations.ishta_phal``.

Doctrine lock D-4: BPHS Ch.47 v.3 formula
    Ishta_Phal  = sqrt(Cheshta_bala * Uchcha_bala)
    Kashta_Phal = 60 - Ishta_Phal

Both Cheshta_bala and Uchcha_bala are taken in their Shadbala "Rupa"
form (i.e. on the 60-point virupa scale).

Hard invariants (asserted by property tests):
    ishta ∈ [0, 60]
    kashta ∈ [0, 60]
    ishta + kashta == 60.0 (within float epsilon)
"""
from __future__ import annotations

import math

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
def shadbala_components(d1_chart) -> dict:
    """Build the {planet: {"cheshta": x, "uchcha": y}} input dict.

    The reading layer prefers an explicit precomputed input over reaching
    into ``shadbala_total`` so unit tests can substitute fixtures freely.
    """
    from app.core.shadbala import cheshta_bala, uchcha_bala

    out: dict[str, dict[str, float]] = {}
    for planet, entry in d1_chart.items():
        lon = float(entry.get("longitude", 0.0))
        is_retro = bool(entry.get("is_retrograde", False))
        try:
            uc = uchcha_bala(planet, lon)
        except ValueError:
            uc = 0.0
        try:
            cb = cheshta_bala(planet, is_retro)
        except ValueError:
            cb = 0.0
        out[planet] = {"cheshta": cb, "uchcha": uc}
    return out


# ---------------------------------------------------------------------------
# Shape / output contract
# ---------------------------------------------------------------------------


class TestComputeIshtaPhal:

    def test_returns_mapping(self, d1_chart, shadbala_components):
        from app.reading.computations.ishta_phal import compute_ishta_phal

        result = compute_ishta_phal(d1_chart, shadbala_components)
        assert isinstance(result, dict)

    def test_one_finding_per_planet(self, d1_chart, shadbala_components):
        from app.reading.computations.ishta_phal import compute_ishta_phal

        result = compute_ishta_phal(d1_chart, shadbala_components)
        for planet in (
            "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"
        ):
            assert planet in result, f"missing Ishta_Phal for {planet}"

    def test_findings_are_finding_instances(self, d1_chart, shadbala_components):
        from app.reading.computations.ishta_phal import compute_ishta_phal
        from app.reading.schema import Finding

        result = compute_ishta_phal(d1_chart, shadbala_components)
        for planet, finding in result.items():
            assert isinstance(finding, Finding), f"{planet} not a Finding"

    def test_id_grammar(self, d1_chart, shadbala_components):
        from app.reading.computations.ishta_phal import compute_ishta_phal

        result = compute_ishta_phal(d1_chart, shadbala_components)
        for planet, finding in result.items():
            assert finding.id == f"primitive.ishta_phal.{planet.lower()}"

    def test_classification_is_primitive(self, d1_chart, shadbala_components):
        from app.reading.computations.ishta_phal import compute_ishta_phal

        result = compute_ishta_phal(d1_chart, shadbala_components)
        for finding in result.values():
            assert finding.classification == "primitive"

    def test_verdict_under_140_chars(self, d1_chart, shadbala_components):
        from app.reading.computations.ishta_phal import compute_ishta_phal

        result = compute_ishta_phal(d1_chart, shadbala_components)
        for finding in result.values():
            assert len(finding.verdict) <= 140

    def test_verdict_mentions_ishta(self, d1_chart, shadbala_components):
        from app.reading.computations.ishta_phal import compute_ishta_phal

        result = compute_ishta_phal(d1_chart, shadbala_components)
        for finding in result.values():
            assert "Ishta" in finding.verdict

    def test_direction_logic(self, d1_chart, shadbala_components):
        """direction = positive if ishta > 30, negative if kashta > 30, else neutral."""
        from app.reading.computations.ishta_phal import compute_ishta_phal

        result = compute_ishta_phal(d1_chart, shadbala_components)
        for planet, finding in result.items():
            ishta = float(
                next(line.split("=", 1)[1] for line in finding.evidence
                     if line.startswith("ishta="))
            )
            kashta = float(
                next(line.split("=", 1)[1] for line in finding.evidence
                     if line.startswith("kashta="))
            )
            if ishta > 30.0:
                assert finding.direction == "positive", (
                    f"{planet}: ishta={ishta:.2f} -> expected positive"
                )
            elif kashta > 30.0:
                assert finding.direction == "negative", (
                    f"{planet}: kashta={kashta:.2f} -> expected negative"
                )
            else:
                assert finding.direction == "neutral", (
                    f"{planet}: ishta={ishta:.2f} kashta={kashta:.2f}"
                    " -> expected neutral"
                )


# ---------------------------------------------------------------------------
# D-4 formula correctness on Bangalore baseline
# ---------------------------------------------------------------------------


class TestBangaloreBaselineFormulaCorrectness:
    """Re-derive expected ishta from raw cheshta/uchcha and assert match."""

    def test_jupiter_ishta_matches_formula(self, d1_chart, shadbala_components):
        from app.reading.computations.ishta_phal import compute_ishta_phal

        result = compute_ishta_phal(d1_chart, shadbala_components)
        jup = result["Jupiter"]
        uc = shadbala_components["Jupiter"]["uchcha"]
        cb = shadbala_components["Jupiter"]["cheshta"]
        expected = math.sqrt(max(0.0, cb * uc))
        actual = float(
            next(line.split("=", 1)[1] for line in jup.evidence
                 if line.startswith("ishta="))
        )
        # Evidence stores ishta at 6-decimal precision, so we tolerate
        # the corresponding round-off.
        assert abs(actual - expected) < 1e-5, (
            f"Jupiter Ishta_Phal {actual} doesn't match sqrt({cb}*{uc}) = {expected}"
        )

    def test_sun_zero_cheshta_yields_zero_ishta(self, d1_chart, shadbala_components):
        """Sun has Cheshta_bala = 0 by BPHS convention (Cheshta is for the
        five star-planets, not luminaries). => Ishta_Phal = 0, Kashta = 60."""
        from app.reading.computations.ishta_phal import compute_ishta_phal

        result = compute_ishta_phal(d1_chart, shadbala_components)
        sun = result["Sun"]
        ishta = float(
            next(line.split("=", 1)[1] for line in sun.evidence
                 if line.startswith("ishta="))
        )
        kashta = float(
            next(line.split("=", 1)[1] for line in sun.evidence
                 if line.startswith("kashta="))
        )
        assert ishta == 0.0
        assert abs(kashta - 60.0) < 1e-9


# ---------------------------------------------------------------------------
# Hard invariants (D-4)
# ---------------------------------------------------------------------------


class TestIshtaPhalInvariants:

    def test_ishta_plus_kashta_equals_60(self, d1_chart, shadbala_components):
        from app.reading.computations.ishta_phal import compute_ishta_phal

        result = compute_ishta_phal(d1_chart, shadbala_components)
        for planet, finding in result.items():
            ishta = float(
                next(line.split("=", 1)[1] for line in finding.evidence
                     if line.startswith("ishta="))
            )
            kashta = float(
                next(line.split("=", 1)[1] for line in finding.evidence
                     if line.startswith("kashta="))
            )
            assert abs(ishta + kashta - 60.0) < 1e-9, (
                f"{planet}: ishta + kashta != 60 (got {ishta + kashta})"
            )

    def test_ishta_and_kashta_in_range(self, d1_chart, shadbala_components):
        """Both must be in [0, 60]."""
        from app.reading.computations.ishta_phal import compute_ishta_phal

        result = compute_ishta_phal(d1_chart, shadbala_components)
        for planet, finding in result.items():
            ishta = float(
                next(line.split("=", 1)[1] for line in finding.evidence
                     if line.startswith("ishta="))
            )
            kashta = float(
                next(line.split("=", 1)[1] for line in finding.evidence
                     if line.startswith("kashta="))
            )
            assert 0.0 <= ishta <= 60.0, f"{planet} ishta {ishta} OOR"
            assert 0.0 <= kashta <= 60.0, f"{planet} kashta {kashta} OOR"

    def test_max_ishta_synthetic(self):
        """Max ishta = sqrt(60*60) = 60.0 (deep exalt + retrograde star planet)."""
        from app.reading.computations.ishta_phal import compute_ishta_phal

        d1 = {"Mars": {"longitude": 297.0, "is_retrograde": True, "sign": 10}}
        comps = {"Mars": {"cheshta": 60.0, "uchcha": 60.0}}
        result = compute_ishta_phal(d1, comps)
        mars = result["Mars"]
        ishta = float(
            next(line.split("=", 1)[1] for line in mars.evidence
                 if line.startswith("ishta="))
        )
        kashta = float(
            next(line.split("=", 1)[1] for line in mars.evidence
                 if line.startswith("kashta="))
        )
        assert abs(ishta - 60.0) < 1e-9
        assert abs(kashta - 0.0) < 1e-9


# ---------------------------------------------------------------------------
# Missing Cheshta -> graceful concern Finding
# ---------------------------------------------------------------------------


class TestMissingCheshtaGracefulDegradation:
    """If a planet has no Cheshta key in the input dict (or it's None),
    the Finding should still be emitted with direction=neutral and a
    pending-cheshta verdict."""

    def test_missing_cheshta_emits_neutral_finding(self, d1_chart):
        from app.reading.computations.ishta_phal import compute_ishta_phal

        # Construct a stub input with no 'cheshta' key at all.
        comps = {"Mars": {"uchcha": 50.0}}  # 'cheshta' deliberately missing
        d1 = {"Mars": d1_chart["Mars"]}
        result = compute_ishta_phal(d1, comps)
        mars = result["Mars"]
        assert mars.direction == "neutral"
        assert "pending" in mars.verdict.lower() or "missing" in mars.verdict.lower()
