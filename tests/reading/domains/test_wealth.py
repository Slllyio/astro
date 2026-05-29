"""Tests for ``app.reading.domains.wealth``.

Doctrine source: Composition of D2 Hora + extended yogas (Lakshmi,
Saraswati, Daridra) + 2H/11H bhava_bala (two-engine retention/inflow
model) + karaka_triangulation (wealth) + Jupiter/Venus avastha +
vimshottari MD/AD.

Bangalore baseline (1990-07-15 12:00 IST / 12.97 N, 77.59 E).
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Bangalore baseline shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def bangalore_chart() -> dict:
    from app.core.ephemeris_engine import calculate_all_charts

    return calculate_all_charts(
        year=1990, month=7, day=15, hour=12, minute=0,
        tz_offset=5.5, latitude=12.97, longitude=77.59,
    )


@pytest.fixture(scope="module")
def baseline_primitives(bangalore_chart) -> dict:
    from app.reading.computations.avasthas import compute_deeptadi_avasthas
    from app.reading.computations.bhava_bala import compute_bhava_bala
    from app.reading.computations.divisional_readings.d2_hora import read_d2_hora
    from app.reading.computations.karaka_triangulation import (
        compute_karaka_triangulation,
    )
    from app.reading.computations.karakas import compute_karakas
    from app.reading.computations.marana_karaka_sthana import detect_mks
    from app.reading.computations.yogas_extended import detect_yogas

    asc_sign = bangalore_chart["ascendant"]["sign"]
    moon_sign = bangalore_chart["d1"]["Moon"]["sign"]
    d2_chart = bangalore_chart["divisional_charts"]["D2_Hora"]

    return {
        "karakas": compute_karakas(bangalore_chart["d1"]),
        "karaka_triangulation": compute_karaka_triangulation(
            bangalore_chart["d1"], asc_sign, moon_sign,
        ),
        "marana_karaka_sthana": detect_mks(
            bangalore_chart["d1"], asc_sign,
        ),
        "bhava_bala": compute_bhava_bala(
            bangalore_chart["d1"], asc_sign=asc_sign,
        ),
        "avasthas": compute_deeptadi_avasthas(bangalore_chart["d1"]),
        "d2_findings": read_d2_hora(d2_chart, asc_sign),
        "yogas_extended": detect_yogas(
            bangalore_chart["d1"], asc_sign, moon_sign,
        ),
    }


@pytest.fixture(scope="module")
def baseline_sequences(bangalore_chart) -> dict:
    from app.reading.sequences.vimshottari_ad import run_sequence as run_ad
    from app.reading.sequences.vimshottari_md import run_sequence as run_md

    asc_sign = bangalore_chart["ascendant"]["sign"]
    moon_sign = bangalore_chart["d1"]["Moon"]["sign"]
    md_lord = bangalore_chart["current_mahadasha"]["mahadasha_lord"]

    md_result = run_md(bangalore_chart, asc_sign, moon_sign)
    cur = md_result.current_md_judgment
    ad_result = run_ad(
        bangalore_chart, asc_sign, moon_sign,
        current_md_lord=md_lord,
        current_md_start_jd=cur.start_jd,
        current_md_end_jd=cur.end_jd,
    )
    return {
        "vimshottari_md": md_result,
        "vimshottari_ad": ad_result,
        "current_md_lord": md_lord,
    }


@pytest.fixture(scope="module")
def baseline_foundations(bangalore_chart) -> dict:
    from app.reading.computations.functional_nature import (
        compute_functional_nature,
    )
    asc_sign = bangalore_chart["ascendant"]["sign"]
    return {
        "functional_nature": compute_functional_nature(asc_sign),
    }


@pytest.fixture(scope="module")
def wealth_reading(
    bangalore_chart, baseline_primitives, baseline_sequences, baseline_foundations,
):
    from app.reading.domains.wealth import synthesize_wealth

    return synthesize_wealth(
        chart=bangalore_chart,
        asc_sign=bangalore_chart["ascendant"]["sign"],
        moon_sign=bangalore_chart["d1"]["Moon"]["sign"],
        sequences_result=baseline_sequences,
        primitives=baseline_primitives,
        foundations=baseline_foundations,
    )


# ---------------------------------------------------------------------------
# Structural conformance
# ---------------------------------------------------------------------------


class TestSynthesizeWealth:

    def test_returns_domain_reading(self, wealth_reading):
        from app.reading.schema import DomainReading
        assert isinstance(wealth_reading, DomainReading)

    def test_domain_label(self, wealth_reading):
        assert wealth_reading.domain == "wealth"

    def test_promise_is_finding(self, wealth_reading):
        from app.reading.schema import Finding
        assert isinstance(wealth_reading.promise, Finding)
        assert wealth_reading.promise.classification == "promise"

    def test_overall_verdict_is_finding(self, wealth_reading):
        from app.reading.schema import Finding
        assert isinstance(wealth_reading.overall_verdict, Finding)

    def test_confidence_score_in_range(self, wealth_reading):
        assert 0.0 <= wealth_reading.confidence.score <= 1.0

    def test_finding_ids_use_domain_grammar(self, wealth_reading):
        for f in (
            [wealth_reading.promise, wealth_reading.overall_verdict]
            + list(wealth_reading.triggers)
            + list(wealth_reading.afflictions)
            + list(wealth_reading.cross_checks)
        ):
            assert f.id.startswith("domain.wealth."), (
                f"finding {f.id!r} must use ``domain.wealth.`` prefix"
            )

    def test_triggers_are_findings(self, wealth_reading):
        from app.reading.schema import Finding
        for t in wealth_reading.triggers:
            assert isinstance(t, Finding)

    def test_afflictions_are_findings(self, wealth_reading):
        from app.reading.schema import Finding
        for a in wealth_reading.afflictions:
            assert isinstance(a, Finding)

    def test_cross_checks_are_findings(self, wealth_reading):
        from app.reading.schema import Finding
        for c in wealth_reading.cross_checks:
            assert isinstance(c, Finding)
        assert len(wealth_reading.cross_checks) >= 1

    def test_timing_windows_typed(self, wealth_reading):
        from app.reading.schema import TimingWindow
        for tw in wealth_reading.timing_windows:
            assert isinstance(tw, TimingWindow)

    def test_remedies_typed(self, wealth_reading):
        from app.reading.schema import RemedyRecommendation
        for r in wealth_reading.remedies:
            assert isinstance(r, RemedyRecommendation)


# ---------------------------------------------------------------------------
# Architectural-purity check — must reference upstream d2 finding ids
# ---------------------------------------------------------------------------


class TestCompositionDiscipline:
    """Domain MUST compose upstream findings, NEVER recompute chart math."""

    def test_wealth_domain_references_d2_finding_ids(
        self, wealth_reading, baseline_primitives,
    ):
        d2_ids = list(baseline_primitives["d2_findings"].keys())
        assert d2_ids, "fixture must supply d2 findings"

        all_evidence: list[str] = []
        for f in (
            [wealth_reading.promise, wealth_reading.overall_verdict]
            + list(wealth_reading.triggers)
            + list(wealth_reading.afflictions)
            + list(wealth_reading.cross_checks)
        ):
            all_evidence.extend(f.evidence)
        flat = " ".join(all_evidence)
        assert any(d2_id in flat for d2_id in d2_ids), (
            "Wealth domain does not reference any d2 finding id — appears "
            "to recompute D2 instead of compose"
        )

    def test_wealth_domain_references_bhava_bala_2h_or_11h(
        self, wealth_reading, baseline_primitives,
    ):
        bb = baseline_primitives["bhava_bala"]
        h2_id = bb[2].id
        h11_id = bb[11].id
        all_evidence: list[str] = []
        for f in (
            [wealth_reading.promise, wealth_reading.overall_verdict]
            + list(wealth_reading.cross_checks)
            + list(wealth_reading.afflictions)
        ):
            all_evidence.extend(f.evidence)
        flat = " ".join(all_evidence)
        assert h2_id in flat or h11_id in flat, (
            "Wealth domain does not reference 2H or 11H bhava_bala upstream — "
            "violates two-engine model"
        )


# ---------------------------------------------------------------------------
# Two-engine retention/inflow signal
# ---------------------------------------------------------------------------


class TestWealthTwoEngineModel:

    def test_cross_checks_or_promise_mentions_2h_or_11h(self, wealth_reading):
        all_text: list[str] = [
            wealth_reading.promise.verdict,
            *[c.verdict for c in wealth_reading.cross_checks],
            *(
                line for c in wealth_reading.cross_checks for line in c.evidence
            ),
            *(line for line in wealth_reading.promise.evidence),
        ]
        flat = " ".join(all_text).lower()
        assert (
            "2h" in flat or "11h" in flat
            or "retention" in flat or "inflow" in flat
            or "house=2" in flat or "house=11" in flat
        ), "two-engine retention/inflow signal not surfaced"


# ---------------------------------------------------------------------------
# Timing windows
# ---------------------------------------------------------------------------


class TestWealthTiming:

    def test_at_least_one_timing_window(self, wealth_reading):
        assert len(wealth_reading.timing_windows) >= 1

    def test_timing_windows_event_type(self, wealth_reading):
        for tw in wealth_reading.timing_windows:
            assert tw.event_type in {"wealth_event", "general"}


class TestWealthDoctrineSentinel:

    def test_module_docstring_starts_with_doctrine_source(self):
        import app.reading.domains.wealth as wealth_module
        assert wealth_module.__doc__ is not None
        assert wealth_module.__doc__.lstrip().startswith("Doctrine source:")
