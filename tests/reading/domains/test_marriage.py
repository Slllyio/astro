"""Tests for ``app.reading.domains.marriage``.

Doctrine source: Composition of D9 Navamsha + marriage_trigger
(compound UL + 7L + D9 + transit Jupiter/Saturn) + arudha_upapada
(UL/UL_2) + karaka_triangulation (marriage) + vimshottari MD/AD.

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
    from app.reading.computations.arudha_upapada import compute_arudha_padas
    from app.reading.computations.karakas import compute_karakas
    from app.reading.computations.karaka_triangulation import (
        compute_karaka_triangulation,
    )
    from app.reading.computations.divisional_readings.d9_navamsha import (
        read_d9_navamsha,
    )
    from app.reading.computations.marriage_trigger import (
        compute_marriage_trigger,
    )

    asc_sign = bangalore_chart["ascendant"]["sign"]
    moon_sign = bangalore_chart["d1"]["Moon"]["sign"]
    md_lord = bangalore_chart["current_mahadasha"]["mahadasha_lord"]

    arudha = compute_arudha_padas(bangalore_chart["d1"], asc_sign)
    karakas = compute_karakas(bangalore_chart["d1"])
    d9_findings = read_d9_navamsha(
        bangalore_chart["d1"], bangalore_chart["d9"], asc_sign,
    )

    # Transit Jupiter/Saturn — for the Bangalore baseline we use natal
    # positions as a stand-in (test is structural, not date-dependent).
    transit_jupiter_sign = int(bangalore_chart["d1"]["Jupiter"]["sign"])
    transit_saturn_sign = int(bangalore_chart["d1"]["Saturn"]["sign"])

    trigger = compute_marriage_trigger(
        d1_chart=bangalore_chart["d1"],
        d9_chart=bangalore_chart["d9"],
        asc_sign=asc_sign,
        moon_sign=moon_sign,
        arudha_padas=arudha,
        current_md_lord=md_lord,
        current_ad_lord=md_lord,  # placeholder; trigger leg A is structural
        transit_jupiter_sign=transit_jupiter_sign,
        transit_saturn_sign=transit_saturn_sign,
        is_male=True,
    )

    return {
        "arudha_padas": arudha,
        "karakas": karakas,
        "karaka_triangulation": compute_karaka_triangulation(
            bangalore_chart["d1"], asc_sign, moon_sign,
        ),
        "d9_findings": d9_findings,
        "marriage_trigger": trigger,
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
def marriage_reading(
    bangalore_chart, baseline_primitives, baseline_sequences, baseline_foundations,
):
    from app.reading.domains.marriage import synthesize_marriage
    return synthesize_marriage(
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


class TestSynthesizeMarriage:

    def test_returns_domain_reading(self, marriage_reading):
        from app.reading.schema import DomainReading
        assert isinstance(marriage_reading, DomainReading)

    def test_domain_label(self, marriage_reading):
        assert marriage_reading.domain == "marriage"

    def test_promise_is_finding(self, marriage_reading):
        from app.reading.schema import Finding
        assert isinstance(marriage_reading.promise, Finding)
        assert marriage_reading.promise.classification == "promise"

    def test_overall_verdict_is_finding(self, marriage_reading):
        from app.reading.schema import Finding
        assert isinstance(marriage_reading.overall_verdict, Finding)

    def test_confidence_score_in_range(self, marriage_reading):
        assert 0.0 <= marriage_reading.confidence.score <= 1.0

    def test_triggers_include_marriage_trigger(
        self, marriage_reading, baseline_primitives,
    ):
        """The marriage_trigger primitive must be surfaced as a trigger."""
        trigger_evidence = []
        for t in marriage_reading.triggers:
            trigger_evidence.extend(t.evidence)
        flat = " ".join(trigger_evidence)
        trigger_id = baseline_primitives["marriage_trigger"].id
        assert trigger_id in flat, (
            "Marriage domain.triggers does NOT reference upstream "
            f"marriage_trigger id {trigger_id!r}"
        )

    def test_finding_ids_use_domain_grammar(self, marriage_reading):
        for f in (
            [marriage_reading.promise, marriage_reading.overall_verdict]
            + list(marriage_reading.triggers)
            + list(marriage_reading.afflictions)
            + list(marriage_reading.cross_checks)
        ):
            assert f.id.startswith("domain.marriage."), (
                f"finding {f.id!r} must use ``domain.marriage.`` prefix"
            )


# ---------------------------------------------------------------------------
# Composition discipline — must reference upstream d9 finding ids
# ---------------------------------------------------------------------------


class TestCompositionDiscipline:

    def test_marriage_domain_references_d9_finding_ids(
        self, marriage_reading, baseline_primitives,
    ):
        d9_ids = list(baseline_primitives["d9_findings"].keys())
        assert d9_ids, "fixture must supply d9 findings"

        all_evidence: list[str] = []
        for f in (
            [marriage_reading.promise, marriage_reading.overall_verdict]
            + list(marriage_reading.triggers)
            + list(marriage_reading.afflictions)
            + list(marriage_reading.cross_checks)
        ):
            all_evidence.extend(f.evidence)
        flat = " ".join(all_evidence)
        assert any(d9_id in flat for d9_id in d9_ids), (
            "Marriage domain does not reference any d9 finding id — appears "
            "to recompute D9 instead of compose"
        )

    def test_marriage_domain_references_upapada(
        self, marriage_reading, baseline_primitives,
    ):
        ul_finding = baseline_primitives["arudha_padas"]["ul"]
        all_evidence: list[str] = []
        for f in (
            [marriage_reading.promise]
            + list(marriage_reading.cross_checks)
        ):
            all_evidence.extend(f.evidence)
        flat = " ".join(all_evidence)
        assert ul_finding.id in flat or "upapada" in flat.lower(), (
            "Marriage domain does not reference Upapada Lagna upstream"
        )


# ---------------------------------------------------------------------------
# Timing windows — must surface dasha periods
# ---------------------------------------------------------------------------


class TestMarriageTiming:

    def test_timing_windows_have_marriage_event_type(self, marriage_reading):
        for tw in marriage_reading.timing_windows:
            assert tw.event_type in {"marriage", "general"}

    def test_at_least_one_timing_window(self, marriage_reading):
        assert len(marriage_reading.timing_windows) >= 1


class TestMarriageDoctrineSentinel:

    def test_module_docstring_starts_with_doctrine_source(self):
        import app.reading.domains.marriage as marriage_module
        assert marriage_module.__doc__ is not None
        assert marriage_module.__doc__.lstrip().startswith("Doctrine source:")
