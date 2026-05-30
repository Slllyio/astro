"""Tests for ``app.reading.domains.education``.

Doctrine source: D-16 lockfile — education routes through D24
Chaturvimsamsa. Composition of D24 reading + D9 (dharma/values context
ONLY — D24 dominates) + 4H + 5H bhava_bala + Mercury (Buddhi karaka) +
Jupiter (Vidya karaka) avastha + karaka_triangulation (education) +
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
    from app.reading.computations.divisional_readings.d24_chaturvimsamsa import (
        read_d24_chaturvimsamsa,
    )
    from app.reading.computations.divisional_readings.d9_navamsha import (
        read_d9_navamsha,
    )
    from app.reading.computations.karaka_triangulation import (
        compute_karaka_triangulation,
    )
    from app.reading.computations.karakas import compute_karakas
    from app.reading.computations.marana_karaka_sthana import detect_mks

    asc_sign = bangalore_chart["ascendant"]["sign"]
    moon_sign = bangalore_chart["d1"]["Moon"]["sign"]
    d24_chart = bangalore_chart["divisional_charts"]["D24_Chaturvimsamsa"]

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
        "d24_findings": read_d24_chaturvimsamsa(d24_chart, asc_sign),
        "d9_findings": read_d9_navamsha(
            bangalore_chart["d1"], bangalore_chart["d9"], asc_sign,
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
def education_reading(
    bangalore_chart, baseline_primitives, baseline_sequences, baseline_foundations,
):
    from app.reading.domains.education import synthesize_education

    return synthesize_education(
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


class TestSynthesizeEducation:

    def test_returns_domain_reading(self, education_reading):
        from app.reading.schema import DomainReading
        assert isinstance(education_reading, DomainReading)

    def test_domain_label(self, education_reading):
        assert education_reading.domain == "education"

    def test_promise_is_finding(self, education_reading):
        from app.reading.schema import Finding
        assert isinstance(education_reading.promise, Finding)
        assert education_reading.promise.classification == "promise"

    def test_overall_verdict_is_finding(self, education_reading):
        from app.reading.schema import Finding
        assert isinstance(education_reading.overall_verdict, Finding)

    def test_confidence_score_in_range(self, education_reading):
        assert 0.0 <= education_reading.confidence.score <= 1.0

    def test_finding_ids_use_domain_grammar(self, education_reading):
        for f in (
            [education_reading.promise, education_reading.overall_verdict]
            + list(education_reading.triggers)
            + list(education_reading.afflictions)
            + list(education_reading.cross_checks)
        ):
            assert f.id.startswith("domain.education."), (
                f"finding {f.id!r} must use ``domain.education.`` prefix"
            )

    def test_triggers_are_findings(self, education_reading):
        from app.reading.schema import Finding
        for t in education_reading.triggers:
            assert isinstance(t, Finding)

    def test_afflictions_are_findings(self, education_reading):
        from app.reading.schema import Finding
        for a in education_reading.afflictions:
            assert isinstance(a, Finding)

    def test_cross_checks_are_findings(self, education_reading):
        from app.reading.schema import Finding
        for c in education_reading.cross_checks:
            assert isinstance(c, Finding)
        assert len(education_reading.cross_checks) >= 1

    def test_timing_windows_typed(self, education_reading):
        from app.reading.schema import TimingWindow
        for tw in education_reading.timing_windows:
            assert isinstance(tw, TimingWindow)

    def test_remedies_typed(self, education_reading):
        from app.reading.schema import RemedyRecommendation
        for r in education_reading.remedies:
            assert isinstance(r, RemedyRecommendation)


# ---------------------------------------------------------------------------
# D-16 LOCK GATE — education MUST route through D24 cross-checks
# ---------------------------------------------------------------------------


class TestD16DoctrineGate:
    """D-16 lockfile: education routes through D24 Chaturvimsamsa.

    The cross-checks MUST reference at least one ``d24.*`` upstream
    finding id — violating this is violating the lockfile.
    """

    def test_education_domain_references_d24_finding_ids(
        self, education_reading, baseline_primitives,
    ):
        d24_ids = list(baseline_primitives["d24_findings"].keys())
        assert d24_ids, "fixture must supply d24 findings"

        # Per spec: D-16 lock — D24 ids MUST appear in cross_checks evidence.
        cross_evidence: list[str] = []
        for c in education_reading.cross_checks:
            cross_evidence.extend(c.evidence)
        flat = " ".join(cross_evidence)
        assert any(d24_id in flat for d24_id in d24_ids), (
            "D-16 LOCK VIOLATION: education domain.cross_checks does NOT "
            "reference any D24 upstream finding id. "
            "Per docs/doctrine-decisions.md D-16, education MUST route "
            "through D24 Chaturvimsamsa."
        )

    def test_education_overall_evidence_mentions_d24_doctrine(
        self, education_reading,
    ):
        """D-16 sentinel must be reachable in the domain's evidence."""
        all_text: list[str] = []
        for f in (
            [education_reading.promise, education_reading.overall_verdict]
            + list(education_reading.cross_checks)
        ):
            all_text.append(f.verdict)
            all_text.extend(f.evidence)
        flat = " ".join(all_text).lower()
        assert "d24" in flat or "d-16" in flat or "chaturvimsamsa" in flat, (
            "Education domain must explicitly tag the D-16 / D24 doctrine"
        )


# ---------------------------------------------------------------------------
# Architectural-purity check — must reference upstream d24 finding ids
# ---------------------------------------------------------------------------


class TestCompositionDiscipline:

    def test_education_domain_references_d24_finding_ids_in_any_field(
        self, education_reading, baseline_primitives,
    ):
        d24_ids = list(baseline_primitives["d24_findings"].keys())
        all_evidence: list[str] = []
        for f in (
            [education_reading.promise, education_reading.overall_verdict]
            + list(education_reading.triggers)
            + list(education_reading.afflictions)
            + list(education_reading.cross_checks)
        ):
            all_evidence.extend(f.evidence)
        flat = " ".join(all_evidence)
        assert any(d24_id in flat for d24_id in d24_ids), (
            "Education domain does not reference any d24 finding id"
        )

    def test_education_domain_references_4h_or_5h_bhava_bala(
        self, education_reading, baseline_primitives,
    ):
        bb = baseline_primitives["bhava_bala"]
        h4_id = bb[4].id
        h5_id = bb[5].id
        all_evidence: list[str] = []
        for f in (
            [education_reading.promise, education_reading.overall_verdict]
            + list(education_reading.cross_checks)
            + list(education_reading.afflictions)
        ):
            all_evidence.extend(f.evidence)
        flat = " ".join(all_evidence)
        assert h4_id in flat or h5_id in flat, (
            "Education domain must reference 4H or 5H bhava_bala upstream"
        )


# ---------------------------------------------------------------------------
# Timing windows
# ---------------------------------------------------------------------------


class TestEducationTiming:

    def test_at_least_one_timing_window(self, education_reading):
        assert len(education_reading.timing_windows) >= 1

    def test_timing_windows_event_type(self, education_reading):
        for tw in education_reading.timing_windows:
            assert tw.event_type in {"education_milestone", "general"}


class TestEducationDoctrineSentinel:

    def test_module_docstring_starts_with_doctrine_source(self):
        import app.reading.domains.education as education_module
        assert education_module.__doc__ is not None
        assert education_module.__doc__.lstrip().startswith("Doctrine source:")
