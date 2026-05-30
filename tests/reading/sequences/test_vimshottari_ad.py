"""Tests for ``app.reading.sequences.vimshottari_ad``.

Doctrine source: notebook NotebookLM proforma — "How To Read
Antardasha In Vedic Astrology". The sequence runs **7 named checks**
in fixed order (see D-15 in ``docs/doctrine-decisions.md``) and emits
a :class:`VimshottariADResult` containing:

  - ``current_md_ads`` — the leftover Antardashas of the *current*
    Mahadasha (from "now" onward).
  - ``next_md_first_3_ads`` — the first 3 Antardashas of the *next*
    Mahadasha.

Bangalore baseline (1990-07-15 12:00 IST / 12.97 N, 77.59 E) is the
canonical fixture per CLAUDE.md test-pinning policy. The chart is in
Mercury MD (start 1978-03-26, end 1995-03-26); the next MD is Ketu MD.
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
def baseline_inputs(bangalore_chart) -> dict:
    md = bangalore_chart["current_mahadasha"]
    # MD start_jd derived from time_elapsed_years and birth_jd, mirroring
    # the run_sequence-internal computation.
    from app.core.ephemeris_engine import DAYS_PER_VEDIC_YEAR
    birth_jd = bangalore_chart["birth_jd"]
    start_jd = birth_jd - md["time_elapsed_years"] * DAYS_PER_VEDIC_YEAR
    end_jd = birth_jd + md["years_remaining"] * DAYS_PER_VEDIC_YEAR
    return {
        "chart": bangalore_chart,
        "asc_sign": bangalore_chart["ascendant"]["sign"],
        "moon_sign": bangalore_chart["d1"]["Moon"]["sign"],
        "current_md_lord": md["mahadasha_lord"],
        "current_md_start_jd": start_jd,
        "current_md_end_jd": end_jd,
    }


# ---------------------------------------------------------------------------
# Public API + structural conformance
# ---------------------------------------------------------------------------


class TestRunSequence:

    def test_returns_vimshottari_ad_result(self, baseline_inputs):
        from app.reading.sequences.vimshottari_ad import (
            VimshottariADResult, run_sequence,
        )

        result = run_sequence(**baseline_inputs)
        assert isinstance(result, VimshottariADResult)

    def test_current_md_ads_nonempty(self, baseline_inputs):
        from app.reading.sequences.vimshottari_ad import run_sequence

        result = run_sequence(**baseline_inputs)
        assert len(result.current_md_ads) >= 1

    def test_next_md_first_3_ads_is_3(self, baseline_inputs):
        from app.reading.sequences.vimshottari_ad import run_sequence

        result = run_sequence(**baseline_inputs)
        assert len(result.next_md_first_3_ads) == 3

    def test_all_ads_have_7_check_keys(self, baseline_inputs):
        from app.reading.schema import AD_CHECK_KEYS
        from app.reading.sequences.vimshottari_ad import run_sequence

        result = run_sequence(**baseline_inputs)
        expected = set(AD_CHECK_KEYS)
        for ad in result.current_md_ads + result.next_md_first_3_ads:
            assert set(ad.checks.keys()) == expected, (
                f"AD lord={ad.ad_lord} (MD={ad.md_lord}) checks mismatch: "
                f"missing={expected - set(ad.checks.keys())}, "
                f"extra={set(ad.checks.keys()) - expected}"
            )

    def test_each_check_is_finding(self, baseline_inputs):
        from app.reading.schema import Finding
        from app.reading.sequences.vimshottari_ad import run_sequence

        result = run_sequence(**baseline_inputs)
        for ad in result.current_md_ads:
            for key, finding in ad.checks.items():
                assert isinstance(finding, Finding), (
                    f"AD {ad.ad_lord} check {key} not a Finding"
                )

    def test_check_finding_ids_use_seq_6_grammar(self, baseline_inputs):
        from app.reading.sequences.vimshottari_ad import run_sequence

        result = run_sequence(**baseline_inputs)
        for ad in result.current_md_ads:
            for key, finding in ad.checks.items():
                assert finding.id.startswith("seq_6."), (
                    f"AD {ad.ad_lord} check {key} id {finding.id!r} "
                    "must start with 'seq_6.'"
                )

    def test_source_sequence_tagged(self, baseline_inputs):
        from app.reading.sequences.vimshottari_ad import run_sequence

        result = run_sequence(**baseline_inputs)
        for ad in result.current_md_ads:
            for finding in ad.checks.values():
                assert finding.source_sequence == "vimshottari_ad"

    def test_overall_verdict_present(self, baseline_inputs):
        from app.reading.schema import Finding
        from app.reading.sequences.vimshottari_ad import run_sequence

        result = run_sequence(**baseline_inputs)
        for ad in result.current_md_ads:
            assert isinstance(ad.overall_verdict, Finding)


class TestADStructure:

    def test_current_ads_share_md_lord(self, baseline_inputs):
        from app.reading.sequences.vimshottari_ad import run_sequence

        result = run_sequence(**baseline_inputs)
        md_lord = baseline_inputs["current_md_lord"]
        for ad in result.current_md_ads:
            assert ad.md_lord == md_lord

    def test_next_ads_share_next_md_lord(self, baseline_inputs):
        from app.reading.sequences.vimshottari_ad import run_sequence

        result = run_sequence(**baseline_inputs)
        # Next MD for Mercury MD baseline is Ketu MD (Vimshottari order).
        # We don't hardcode but enforce internal consistency:
        next_md_lords = {ad.md_lord for ad in result.next_md_first_3_ads}
        assert len(next_md_lords) == 1, "Next-MD ADs must share one MD lord"
        assert next_md_lords.pop() != baseline_inputs["current_md_lord"]

    def test_iso_dates_well_formed(self, baseline_inputs):
        from app.reading.sequences.vimshottari_ad import run_sequence

        result = run_sequence(**baseline_inputs)
        for ad in result.current_md_ads:
            assert len(ad.start_date) == 10
            assert ad.start_date.count("-") == 2
            assert ad.end_jd > ad.start_jd
