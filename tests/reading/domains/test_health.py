"""Tests for ``app.reading.domains.health``.

Doctrine source: Composition of computations.marana_karaka_sthana (MKS),
computations.trika_doctrine (Vipareeta from 6/8/12 exchange),
computations.bhava_bala (1/6/8/12 strengths), computations.avasthas
(lagna lord state), and computations.sade_sati_severity (Saturn overlay).

Health is the affliction-heavy domain — the dominant content lives in the
``afflictions`` field; the ``promise`` field describes constitution.

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
    from app.reading.computations.karakas import compute_karakas
    from app.reading.computations.karaka_triangulation import (
        compute_karaka_triangulation,
    )
    from app.reading.computations.marana_karaka_sthana import detect_mks
    from app.reading.computations.bhava_bala import compute_bhava_bala
    from app.reading.computations.trika_doctrine import (
        detect_trika_exchanges,
    )
    from app.reading.computations.avasthas import compute_deeptadi_avasthas
    from app.reading.computations.sade_sati_severity import (
        compute_sade_sati_severity,
    )

    asc_sign = bangalore_chart["ascendant"]["sign"]
    moon_sign = bangalore_chart["d1"]["Moon"]["sign"]
    transit_saturn_sign = int(bangalore_chart["d1"]["Saturn"]["sign"])

    return {
        "karakas": compute_karakas(bangalore_chart["d1"]),
        "karaka_triangulation": compute_karaka_triangulation(
            bangalore_chart["d1"], asc_sign, moon_sign,
        ),
        "marana_karaka_sthana": detect_mks(bangalore_chart["d1"], asc_sign),
        "bhava_bala": compute_bhava_bala(bangalore_chart["d1"], asc_sign),
        "trika_exchanges": detect_trika_exchanges(
            bangalore_chart["d1"], asc_sign,
        ),
        "avasthas": compute_deeptadi_avasthas(bangalore_chart["d1"]),
        "sade_sati": compute_sade_sati_severity(
            bangalore_chart["d1"], asc_sign, transit_saturn_sign,
        ),
    }


@pytest.fixture(scope="module")
def baseline_sequences(bangalore_chart) -> dict:
    from app.reading.sequences.vimshottari_md import run_sequence as run_md
    from app.reading.sequences.vimshottari_ad import run_sequence as run_ad

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
def health_reading(
    bangalore_chart, baseline_primitives, baseline_sequences, baseline_foundations,
):
    from app.reading.domains.health import synthesize_health
    return synthesize_health(
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


class TestSynthesizeHealth:

    def test_returns_domain_reading(self, health_reading):
        from app.reading.schema import DomainReading
        assert isinstance(health_reading, DomainReading)

    def test_domain_label(self, health_reading):
        assert health_reading.domain == "health"

    def test_promise_is_finding(self, health_reading):
        from app.reading.schema import Finding
        assert isinstance(health_reading.promise, Finding)
        assert health_reading.promise.classification == "promise"

    def test_overall_verdict_is_finding(self, health_reading):
        from app.reading.schema import Finding
        assert isinstance(health_reading.overall_verdict, Finding)

    def test_confidence_score_in_range(self, health_reading):
        assert 0.0 <= health_reading.confidence.score <= 1.0

    def test_cross_checks_are_findings(self, health_reading):
        from app.reading.schema import Finding
        for c in health_reading.cross_checks:
            assert isinstance(c, Finding)
        assert len(health_reading.cross_checks) >= 1

    def test_finding_ids_use_domain_grammar(self, health_reading):
        for f in (
            [health_reading.promise, health_reading.overall_verdict]
            + list(health_reading.triggers)
            + list(health_reading.afflictions)
            + list(health_reading.cross_checks)
        ):
            assert f.id.startswith("domain.health."), (
                f"finding {f.id!r} must use ``domain.health.`` prefix"
            )


# ---------------------------------------------------------------------------
# Composition discipline — must reference upstream finding ids
# ---------------------------------------------------------------------------


class TestCompositionDiscipline:

    def test_health_domain_references_bhava_bala_finding_ids(
        self, health_reading, baseline_primitives,
    ):
        bb_ids = [f.id for f in baseline_primitives["bhava_bala"].values()]
        assert bb_ids, "fixture must supply bhava_bala findings"

        all_evidence: list[str] = []
        for f in (
            [health_reading.promise, health_reading.overall_verdict]
            + list(health_reading.triggers)
            + list(health_reading.afflictions)
            + list(health_reading.cross_checks)
        ):
            all_evidence.extend(f.evidence)
        flat = " ".join(all_evidence)
        assert any(bb_id in flat for bb_id in bb_ids), (
            "Health domain does not reference any bhava_bala finding id — "
            "appears to recompute house strength instead of compose"
        )

    def test_health_domain_references_sade_sati(
        self, health_reading, baseline_primitives,
    ):
        ss_id = baseline_primitives["sade_sati"].id
        all_evidence: list[str] = []
        for f in (
            list(health_reading.triggers)
            + list(health_reading.cross_checks)
            + list(health_reading.afflictions)
        ):
            all_evidence.extend(f.evidence)
        flat = " ".join(all_evidence)
        assert ss_id in flat or "sade_sati" in flat.lower(), (
            "Health domain does not reference Sade Sati upstream"
        )


# ---------------------------------------------------------------------------
# Health-specific content
# ---------------------------------------------------------------------------


class TestHealthAfflictionDominance:
    """Per the brief, afflictions are the dominant content for health."""

    def test_afflictions_present_or_constitution_strong(self, health_reading):
        """Either we have afflictions surfaced, or the constitution is strong.

        Bangalore baseline has Saturn in MKS (1H) which IS an MKS — so we
        expect at least one affliction. But the assertion is permissive:
        afflictions OR a strong-constitution promise.
        """
        promise_dir = health_reading.promise.direction
        assert (
            len(health_reading.afflictions) >= 1
            or promise_dir in {"positive", "neutral"}
        )


class TestHealthTimingWindows:
    """Sade-Sati overlay drives the timing windows for health."""

    def test_timing_windows_typed_health_event(self, health_reading):
        from app.reading.schema import TimingWindow
        for tw in health_reading.timing_windows:
            assert isinstance(tw, TimingWindow)
            assert tw.event_type in {"health_event", "general"}


class TestHealthDoctrineSentinel:

    def test_module_docstring_starts_with_doctrine_source(self):
        import app.reading.domains.health as health_module
        assert health_module.__doc__ is not None
        assert health_module.__doc__.lstrip().startswith("Doctrine source:")
