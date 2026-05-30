"""Tests for ``app.reading.sequences.chara_dasha``.

Doctrine source: Jaimini Sutras Adhyaya 2 + Sanjay Rath "Crux of Vedic
Astrology" Ch.16. See D-17 in ``docs/doctrine-decisions.md``.

Bangalore baseline (1990-07-15 12:00 IST / 12.97 N, 77.59 E) is the
canonical fixture per CLAUDE.md test-pinning policy. For Bangalore:

  - Ascendant sign = 6 (Virgo, **dual**)
  - Per D-17 dual-lagna rule, starting MD = 9th from Virgo = Taurus (2)
    (count: Virgo, Libra, Scorpio, Sagittarius, Capricorn, Aquarius,
    Pisces, Aries, Taurus = 9th sign inclusive)
  - Years per sign: movable=3, fixed=7, dual=11
  - Total cycle = 4*3 + 4*7 + 4*11 = 84 years
"""
from __future__ import annotations

import pytest

from app.reading.sequences.chara_dasha import (
    CHARA_DASHA_MD_CHECK_KEYS,
    CharaDashaADPeriod,
    CharaDashaJudgment,
    CharaDashaMDPeriod,
    CharaDashaResult,
    run_sequence,
)


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
    return {
        "chart": bangalore_chart,
        "asc_sign": bangalore_chart["ascendant"]["sign"],
        "moon_sign": bangalore_chart["d1"]["Moon"]["sign"],
    }


# ---------------------------------------------------------------------------
# Public API + structural conformance
# ---------------------------------------------------------------------------


class TestRunSequence:

    def test_returns_chara_dasha_result(self, baseline_inputs):
        """run_sequence emits a CharaDashaResult."""
        result = run_sequence(**baseline_inputs)
        assert isinstance(result, CharaDashaResult)

    def test_timeline_has_12_mds(self, baseline_inputs):
        """One full Chara cycle covers all 12 signs."""
        result = run_sequence(**baseline_inputs)
        assert len(result.timeline) == 12

    def test_timeline_signs_are_unique(self, baseline_inputs):
        """Each of the 12 MDs hits a distinct sign."""
        result = run_sequence(**baseline_inputs)
        signs = [p.md_sign for p in result.timeline]
        assert sorted(signs) == list(range(1, 13))

    def test_exactly_one_current_md(self, baseline_inputs):
        """Exactly one MD in the cycle contains the birth moment."""
        result = run_sequence(**baseline_inputs)
        currents = [p for p in result.timeline if p.is_current]
        assert len(currents) == 1

    def test_current_md_judgment_present(self, baseline_inputs):
        """current_md_judgment is a CharaDashaJudgment."""
        result = run_sequence(**baseline_inputs)
        assert isinstance(result.current_md_judgment, CharaDashaJudgment)

    def test_current_ads_has_12_periods(self, baseline_inputs):
        """Each MD subdivides into 12 AD sub-periods."""
        result = run_sequence(**baseline_inputs)
        assert len(result.current_ads) == 12
        for ad in result.current_ads:
            assert isinstance(ad, CharaDashaADPeriod)


# ---------------------------------------------------------------------------
# D-17 doctrine — sign categorization + total cycle math
# ---------------------------------------------------------------------------


class TestD17DoctrineRules:

    def test_movable_signs_have_3_years(self, baseline_inputs):
        """Movable signs (1/4/7/10) all carry 3 years per D-17."""
        result = run_sequence(**baseline_inputs)
        for p in result.timeline:
            if p.md_sign in (1, 4, 7, 10):
                assert p.sign_category == "movable"
                assert p.total_years == pytest.approx(3.0)

    def test_fixed_signs_have_7_years(self, baseline_inputs):
        """Fixed signs (2/5/8/11) all carry 7 years per D-17."""
        result = run_sequence(**baseline_inputs)
        for p in result.timeline:
            if p.md_sign in (2, 5, 8, 11):
                assert p.sign_category == "fixed"
                assert p.total_years == pytest.approx(7.0)

    def test_dual_signs_have_11_years(self, baseline_inputs):
        """Dual signs (3/6/9/12) all carry 11 years per D-17."""
        result = run_sequence(**baseline_inputs)
        for p in result.timeline:
            if p.md_sign in (3, 6, 9, 12):
                assert p.sign_category == "dual"
                assert p.total_years == pytest.approx(11.0)

    def test_total_cycle_is_84_years(self, baseline_inputs):
        """Per D-17 literal formula: 4*3 + 4*7 + 4*11 = 84 years total.

        (Note: this departs from the variable-per-chart Sanjay-Rath
        formula in Crux of Vedic Astrology Ch.16; D-17 codifies the
        brief-specified simplified literal formula. The PVR Narasimha
        Rao variant gives a different total — see D-17 alternatives.)
        """
        result = run_sequence(**baseline_inputs)
        total = sum(p.total_years for p in result.timeline)
        assert total == pytest.approx(84.0)

    def test_bangalore_starting_md_is_taurus(self, baseline_inputs):
        """Bangalore lagna = Virgo (dual); D-17 dual rule -> 9th from
        Virgo = Taurus (sign 2). The first MD in the timeline must be
        Taurus (and is_current because the cycle begins at birth)."""
        result = run_sequence(**baseline_inputs)
        first = result.timeline[0]
        assert first.md_sign == 2
        assert first.md_sign_name == "Taurus"
        assert first.is_current is True


# ---------------------------------------------------------------------------
# Schema-conformance: the 7 named check keys
# ---------------------------------------------------------------------------


class TestCheckKeysSchema:

    def test_check_keys_constant_is_7(self):
        """CHARA_DASHA_MD_CHECK_KEYS holds exactly the 7 named keys."""
        assert len(CHARA_DASHA_MD_CHECK_KEYS) == 7
        assert set(CHARA_DASHA_MD_CHECK_KEYS) == {
            "sign_character",
            "sign_lord_placement",
            "karaka_in_sign",
            "occupants_of_sign",
            "argala_on_sign",
            "drishti_to_sign",
            "atmakaraka_relationship",
        }

    def test_judgment_carries_all_7_check_keys(self, baseline_inputs):
        """The current-MD judgment dict contains exactly the 7 keys."""
        result = run_sequence(**baseline_inputs)
        keys = set(result.current_md_judgment.checks.keys())
        assert keys == set(CHARA_DASHA_MD_CHECK_KEYS)

    def test_each_check_is_a_finding(self, baseline_inputs):
        """Each check value is a Finding (schema.Finding instance)."""
        from app.reading.schema import Finding

        result = run_sequence(**baseline_inputs)
        for key, finding in result.current_md_judgment.checks.items():
            assert isinstance(finding, Finding), (
                f"check {key} is not a Finding instance"
            )

    def test_overall_verdict_is_finding(self, baseline_inputs):
        from app.reading.schema import Finding

        result = run_sequence(**baseline_inputs)
        assert isinstance(
            result.current_md_judgment.overall_verdict, Finding,
        )

    def test_check_ids_use_seq_chara_grammar(self, baseline_inputs):
        """All check Finding IDs are namespaced under seq_chara.*"""
        result = run_sequence(**baseline_inputs)
        for key, finding in result.current_md_judgment.checks.items():
            assert finding.id.startswith("seq_chara."), (
                f"check {key} id {finding.id!r} must start with 'seq_chara.'"
            )

    def test_source_sequence_tagged(self, baseline_inputs):
        result = run_sequence(**baseline_inputs)
        for finding in result.current_md_judgment.checks.values():
            assert finding.source_sequence == "chara_dasha"


# ---------------------------------------------------------------------------
# AD sub-period invariants
# ---------------------------------------------------------------------------


class TestADSubPeriods:

    def test_ad_signs_are_unique(self, baseline_inputs):
        """The 12 AD signs of any MD hit each sign exactly once."""
        result = run_sequence(**baseline_inputs)
        signs = [ad.ad_sign for ad in result.current_ads]
        assert sorted(signs) == list(range(1, 13))

    def test_first_ad_starts_with_md_sign(self, baseline_inputs):
        """The first AD of an MD is keyed on the MD sign itself."""
        result = run_sequence(**baseline_inputs)
        first_ad = result.current_ads[0]
        assert first_ad.ad_sign == result.current_md_judgment.md_sign

    def test_ad_total_years_match_md(self, baseline_inputs):
        """Sum of AD lengths equals the MD's total years (within 1e-6)."""
        result = run_sequence(**baseline_inputs)
        md_years = next(
            p.total_years for p in result.timeline if p.is_current
        )
        ad_sum = sum(ad.total_years for ad in result.current_ads)
        assert ad_sum == pytest.approx(md_years, rel=1e-9)

    def test_at_most_one_current_ad(self, baseline_inputs):
        """At most one AD in the current MD contains the birth moment."""
        result = run_sequence(**baseline_inputs)
        currents = [ad for ad in result.current_ads if ad.is_current]
        assert len(currents) <= 1


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


class TestInputValidation:

    def test_invalid_asc_sign_raises(self, bangalore_chart):
        with pytest.raises(ValueError):
            run_sequence(chart=bangalore_chart, asc_sign=13, moon_sign=1)

    def test_invalid_moon_sign_raises(self, bangalore_chart):
        with pytest.raises(ValueError):
            run_sequence(chart=bangalore_chart, asc_sign=1, moon_sign=0)

    def test_missing_d1_raises(self):
        with pytest.raises(ValueError, match="d1"):
            run_sequence(chart={"birth_jd": 2400000.0}, asc_sign=1, moon_sign=1)

    def test_missing_birth_jd_raises(self):
        with pytest.raises(ValueError, match="birth_jd"):
            run_sequence(chart={"d1": {}}, asc_sign=1, moon_sign=1)
