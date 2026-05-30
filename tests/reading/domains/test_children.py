"""Tests for ``app.reading.domains.children``.

Doctrine source: Composition of D7 Saptamsa + karaka_triangulation
(children row) + 5H bhava_bala + Jupiter avastha (putra karaka) +
vimshottari MD/AD + MKS on Jupiter (e.g. Jupiter-in-3H affliction).

Triple-chart confirmation: D1-5H (via bhava_bala[5]) + D9 (via
d9.planet_in_jupiter / d9 lagna) + D7-5H (via d7.fifth_house_lord) —
all three must be non-afflicted for a strong children indication.

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
    from app.reading.computations.divisional_readings.d7_saptamsa import (
        read_d7_saptamsa,
    )
    from app.reading.computations.divisional_readings.d9_navamsha import (
        read_d9_navamsha,
    )
    from app.reading.computations.karaka_triangulation import (
        compute_karaka_triangulation,
    )
    from app.reading.computations.karakas import compute_karakas
    from app.reading.computations.marana_karaka_sthana import detect_mks
    from app.reading.computations.yogas_extended import detect_yogas

    asc_sign = bangalore_chart["ascendant"]["sign"]
    moon_sign = bangalore_chart["d1"]["Moon"]["sign"]
    d7_chart = bangalore_chart["divisional_charts"]["D7_Saptamsa"]

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
        "d7_findings": read_d7_saptamsa(d7_chart, asc_sign),
        "d9_findings": read_d9_navamsha(
            bangalore_chart["d1"], bangalore_chart["d9"], asc_sign,
        ),
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
def children_reading(
    bangalore_chart, baseline_primitives, baseline_sequences, baseline_foundations,
):
    from app.reading.domains.children import synthesize_children

    return synthesize_children(
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


class TestSynthesizeChildren:

    def test_returns_domain_reading(self, children_reading):
        from app.reading.schema import DomainReading
        assert isinstance(children_reading, DomainReading)

    def test_domain_label(self, children_reading):
        assert children_reading.domain == "children"

    def test_promise_is_finding(self, children_reading):
        from app.reading.schema import Finding
        assert isinstance(children_reading.promise, Finding)
        assert children_reading.promise.classification == "promise"

    def test_overall_verdict_is_finding(self, children_reading):
        from app.reading.schema import Finding
        assert isinstance(children_reading.overall_verdict, Finding)

    def test_confidence_score_in_range(self, children_reading):
        assert 0.0 <= children_reading.confidence.score <= 1.0

    def test_finding_ids_use_domain_grammar(self, children_reading):
        for f in (
            [children_reading.promise, children_reading.overall_verdict]
            + list(children_reading.triggers)
            + list(children_reading.afflictions)
            + list(children_reading.cross_checks)
        ):
            assert f.id.startswith("domain.children."), (
                f"finding {f.id!r} must use ``domain.children.`` prefix"
            )

    def test_triggers_are_findings(self, children_reading):
        from app.reading.schema import Finding
        for t in children_reading.triggers:
            assert isinstance(t, Finding)

    def test_afflictions_are_findings(self, children_reading):
        from app.reading.schema import Finding
        for a in children_reading.afflictions:
            assert isinstance(a, Finding)

    def test_cross_checks_are_findings(self, children_reading):
        from app.reading.schema import Finding
        for c in children_reading.cross_checks:
            assert isinstance(c, Finding)
        assert len(children_reading.cross_checks) >= 1

    def test_timing_windows_typed(self, children_reading):
        from app.reading.schema import TimingWindow
        for tw in children_reading.timing_windows:
            assert isinstance(tw, TimingWindow)

    def test_remedies_typed(self, children_reading):
        from app.reading.schema import RemedyRecommendation
        for r in children_reading.remedies:
            assert isinstance(r, RemedyRecommendation)


# ---------------------------------------------------------------------------
# Architectural-purity check — must reference upstream d7 finding ids
# ---------------------------------------------------------------------------


class TestCompositionDiscipline:
    """Domain MUST compose upstream findings, NEVER recompute chart math."""

    def test_children_domain_references_d7_finding_ids(
        self, children_reading, baseline_primitives,
    ):
        d7_ids = list(baseline_primitives["d7_findings"].keys())
        assert d7_ids, "fixture must supply d7 findings"

        all_evidence: list[str] = []
        for f in (
            [children_reading.promise, children_reading.overall_verdict]
            + list(children_reading.triggers)
            + list(children_reading.afflictions)
            + list(children_reading.cross_checks)
        ):
            all_evidence.extend(f.evidence)
        flat = " ".join(all_evidence)
        assert any(d7_id in flat for d7_id in d7_ids), (
            "Children domain does not reference any d7 finding id — appears "
            "to recompute D7 instead of compose"
        )

    def test_children_domain_references_5h_bhava_bala(
        self, children_reading, baseline_primitives,
    ):
        """5H is THE children house — must be referenced."""
        h5_id = baseline_primitives["bhava_bala"][5].id
        all_evidence: list[str] = []
        for f in (
            [children_reading.promise, children_reading.overall_verdict]
            + list(children_reading.cross_checks)
            + list(children_reading.afflictions)
        ):
            all_evidence.extend(f.evidence)
        flat = " ".join(all_evidence)
        assert h5_id in flat, (
            "Children domain does not reference 5H bhava_bala upstream"
        )


# ---------------------------------------------------------------------------
# Triple-chart confirmation
# ---------------------------------------------------------------------------


class TestChildrenTripleChartConfirmation:
    """Per practitioner research: D1-5H + D9 + D7-5H must concord."""

    def test_cross_checks_surface_triple_chart_signal(self, children_reading):
        cross_text = " ".join(
            c.verdict + " " + " ".join(c.evidence)
            for c in children_reading.cross_checks
        ).lower()
        # Either explicit triple_chart marker, or at least 2 of D1/D9/D7.
        has_triple = "triple_chart" in cross_text or "triple-chart" in cross_text
        has_d1 = "h5" in cross_text or "house=5" in cross_text or "bhava_bala" in cross_text
        has_d9 = "d9" in cross_text
        has_d7 = "d7" in cross_text
        present = sum([has_d1, has_d9, has_d7])
        assert has_triple or present >= 2, (
            "Children domain must expose triple-chart (D1-5H + D9 + D7-5H) "
            "confirmation in cross_checks"
        )


# ---------------------------------------------------------------------------
# Timing windows
# ---------------------------------------------------------------------------


class TestChildrenTiming:

    def test_at_least_one_timing_window(self, children_reading):
        assert len(children_reading.timing_windows) >= 1

    def test_timing_windows_event_type(self, children_reading):
        for tw in children_reading.timing_windows:
            assert tw.event_type in {"child_birth", "general"}


class TestChildrenDoctrineSentinel:

    def test_module_docstring_starts_with_doctrine_source(self):
        import app.reading.domains.children as children_module
        assert children_module.__doc__ is not None
        assert children_module.__doc__.lstrip().startswith("Doctrine source:")
