"""Tests for ``app.reading.domains.career``.

Doctrine source: Composition of D10 Dashamsha + Career Executive sequence
+ Vimshottari MD/AD + Amatya Karaka + MKS doctrine. The domain synthesizer
is a *pure composer*: every cross-check Finding must REFERENCE upstream
finding ids in its ``evidence`` list — no recomputation of chart math.

Bangalore baseline (1990-07-15 12:00 IST / 12.97 N, 77.59 E) is the
canonical fixture (CLAUDE.md test-pinning policy).
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
    """Build the upstream primitives the career domain composes from."""
    from app.reading.computations.karakas import compute_karakas
    from app.reading.computations.karaka_triangulation import (
        compute_karaka_triangulation,
    )
    from app.reading.computations.marana_karaka_sthana import detect_mks
    from app.reading.computations.divisional_readings.d10_dashamsha import (
        read_d10_dashamsha,
    )
    from app.reading.computations.arudha_upapada import compute_arudha_padas

    asc_sign = bangalore_chart["ascendant"]["sign"]
    moon_sign = bangalore_chart["d1"]["Moon"]["sign"]

    karakas = compute_karakas(bangalore_chart["d1"])

    # Extract AmK planet name from karaka evidence.
    amk_planet = "Jupiter"  # canonical for the Bangalore baseline
    for line in karakas["amatyakaraka"].evidence:
        if line.startswith("planet="):
            amk_planet = line.split("=", 1)[1]
            break

    return {
        "karakas": karakas,
        "amk_planet": amk_planet,
        "karaka_triangulation": compute_karaka_triangulation(
            bangalore_chart["d1"], asc_sign, moon_sign,
        ),
        "marana_karaka_sthana": detect_mks(
            bangalore_chart["d1"], asc_sign,
        ),
        "d10_findings": read_d10_dashamsha(
            bangalore_chart["d1"], bangalore_chart["d10"], asc_sign, amk_planet,
        ),
        "arudha_padas": compute_arudha_padas(bangalore_chart["d1"], asc_sign),
    }


@pytest.fixture(scope="module")
def baseline_sequences(bangalore_chart) -> dict:
    """Build the upstream sequence results the career domain composes from."""
    from app.reading.sequences.career_executive import run_sequence as run_career
    from app.reading.sequences.vimshottari_md import run_sequence as run_md
    from app.reading.sequences.vimshottari_ad import run_sequence as run_ad

    asc_sign = bangalore_chart["ascendant"]["sign"]
    moon_sign = bangalore_chart["d1"]["Moon"]["sign"]
    md = bangalore_chart["current_mahadasha"]
    current_md_lord = md["mahadasha_lord"]

    md_result = run_md(bangalore_chart, asc_sign, moon_sign)
    current_md = md_result.current_md_judgment
    ad_result = run_ad(
        bangalore_chart, asc_sign, moon_sign,
        current_md_lord=current_md_lord,
        current_md_start_jd=current_md.start_jd,
        current_md_end_jd=current_md.end_jd,
    )
    career_exec = run_career(
        chart=bangalore_chart, asc_sign=asc_sign, moon_sign=moon_sign,
        current_md_lord=current_md_lord,
        birth_jd=bangalore_chart["birth_jd"],
        birth_lat=12.97, birth_lon=77.59,
        is_daytime=True, weekday=0,
    )
    return {
        "career_executive": career_exec,
        "vimshottari_md": md_result,
        "vimshottari_ad": ad_result,
        "current_md_lord": current_md_lord,
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
def career_reading(
    bangalore_chart, baseline_primitives, baseline_sequences, baseline_foundations,
):
    from app.reading.domains.career import synthesize_career

    return synthesize_career(
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


class TestSynthesizeCareer:

    def test_returns_domain_reading(self, career_reading):
        from app.reading.schema import DomainReading
        assert isinstance(career_reading, DomainReading)

    def test_domain_label(self, career_reading):
        assert career_reading.domain == "career"

    def test_promise_is_finding(self, career_reading):
        from app.reading.schema import Finding
        assert isinstance(career_reading.promise, Finding)
        assert career_reading.promise.classification == "promise"

    def test_overall_verdict_is_finding(self, career_reading):
        from app.reading.schema import Finding
        assert isinstance(career_reading.overall_verdict, Finding)

    def test_confidence_is_confidence_score(self, career_reading):
        from app.reading.schema import ConfidenceScore
        assert isinstance(career_reading.confidence, ConfidenceScore)
        assert 0.0 <= career_reading.confidence.score <= 1.0

    def test_triggers_are_findings(self, career_reading):
        from app.reading.schema import Finding
        for t in career_reading.triggers:
            assert isinstance(t, Finding)

    def test_afflictions_are_findings(self, career_reading):
        from app.reading.schema import Finding
        for a in career_reading.afflictions:
            assert isinstance(a, Finding)

    def test_cross_checks_are_findings(self, career_reading):
        from app.reading.schema import Finding
        for c in career_reading.cross_checks:
            assert isinstance(c, Finding)
        assert len(career_reading.cross_checks) >= 1

    def test_timing_windows_typed(self, career_reading):
        from app.reading.schema import TimingWindow
        for tw in career_reading.timing_windows:
            assert isinstance(tw, TimingWindow)

    def test_remedies_typed(self, career_reading):
        from app.reading.schema import RemedyRecommendation
        for r in career_reading.remedies:
            assert isinstance(r, RemedyRecommendation)

    def test_finding_ids_use_domain_grammar(self, career_reading):
        """Domain findings must begin with ``domain.career.``."""
        for f in (
            [career_reading.promise, career_reading.overall_verdict]
            + list(career_reading.triggers)
            + list(career_reading.afflictions)
            + list(career_reading.cross_checks)
        ):
            assert f.id.startswith("domain.career."), (
                f"finding {f.id!r} must use ``domain.career.`` prefix"
            )


# ---------------------------------------------------------------------------
# Architectural-purity check — cross_checks must reference upstream finding ids
# ---------------------------------------------------------------------------


class TestCompositionDiscipline:
    """The domain MUST compose upstream findings, NEVER recompute chart math.

    The contract: at least one cross_check / promise / trigger Finding's
    ``evidence`` list references an upstream finding id (e.g. one of
    ``d10.*`` or ``seq_2.*``). If a domain produced NO references to upstream
    ids it almost certainly recomputed something — failing the architectural
    purity gate per Phase 5 brief.
    """

    def test_career_domain_references_d10_finding_ids(
        self, career_reading, baseline_primitives,
    ):
        d10_ids = list(baseline_primitives["d10_findings"].keys())
        assert d10_ids, "fixture must supply d10 findings"

        all_evidence: list[str] = []
        for f in (
            [career_reading.promise, career_reading.overall_verdict]
            + list(career_reading.triggers)
            + list(career_reading.afflictions)
            + list(career_reading.cross_checks)
        ):
            all_evidence.extend(f.evidence)
        flat = " ".join(all_evidence)
        assert any(d10_id in flat for d10_id in d10_ids), (
            "Career domain does not reference any d10 finding id — appears "
            "to recompute D10 instead of compose"
        )

    def test_career_domain_references_career_executive_seq_ids(
        self, career_reading,
    ):
        """Composition test: must reference at least one seq_2.* finding id."""
        all_evidence: list[str] = []
        for f in (
            [career_reading.promise, career_reading.overall_verdict]
            + list(career_reading.triggers)
            + list(career_reading.cross_checks)
        ):
            all_evidence.extend(f.evidence)
        flat = " ".join(all_evidence)
        assert "seq_2." in flat, (
            "Career domain does not reference Sequence 2 (career_executive) — "
            "expected at least one seq_2.* id in evidence"
        )


# ---------------------------------------------------------------------------
# Promise content — career-specific
# ---------------------------------------------------------------------------


class TestCareerPromise:

    def test_promise_mentions_amk_or_d10(self, career_reading):
        text = career_reading.promise.verdict + " " + " ".join(
            career_reading.promise.evidence
        )
        text_lc = text.lower()
        assert (
            "amatya" in text_lc
            or "amk" in text_lc
            or "d10" in text_lc
            or "career" in text_lc
        )


class TestCareerTriggers:

    def test_triggers_reference_current_md_or_ad(
        self, career_reading, baseline_sequences,
    ):
        md_lord = baseline_sequences["current_md_lord"]
        all_evidence: list[str] = []
        for t in career_reading.triggers:
            all_evidence.extend(t.evidence)
        flat = " ".join(all_evidence)
        # Allow either: the MD lord name OR an explicit md/dasha label.
        assert (
            md_lord in flat
            or "md_lord" in flat.lower()
            or "mahadasha" in flat.lower()
        )


class TestCareerDoctrineSentinel:

    def test_module_docstring_starts_with_doctrine_source(self):
        import app.reading.domains.career as career_module
        assert career_module.__doc__ is not None
        assert career_module.__doc__.lstrip().startswith("Doctrine source:")
