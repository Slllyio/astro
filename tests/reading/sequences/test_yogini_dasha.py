"""Tests for ``app.reading.sequences.yogini_dasha``.

Doctrine source: Maha Tantra + Sanjay Rath "Crux of Vedic Astrology"
Ch.17 (D-18 locked in ``docs/doctrine-decisions.md``). The Yogini Dasha
is a **36-year specialty cycle** practitioners use to cross-validate
Vimshottari predictions, especially for shorter-cycle (yearly) events.

Bangalore baseline fixture (1990-07-15 12:00 IST / 12.97 N, 77.59 E) per
CLAUDE.md test-pinning policy. Baseline Moon at Revati pada 3
(nakshatra index 27, 1-indexed) — verified by ``nakshatra_for_longitude``
in ``app/core/nakshatra.py``. Per D-18 table, Revati maps to **Dhanya**
(yogini index 2 — ruled by Jupiter), which is the canonical
yogini-system starting state for this birth.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Bangalore baseline fixture (matches vimshottari_md test fixture)
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
    """Bangalore baseline inputs for the Yogini run_sequence call.

    The brief specifies passing the Moon's natal nakshatra (1-indexed).
    Bangalore baseline Moon is at Revati pada 3 → nakshatra index 27.
    """
    from app.core.nakshatra import nakshatra_for_longitude

    moon_lon = bangalore_chart["d1"]["Moon"]["longitude"]
    moon_nak = nakshatra_for_longitude(moon_lon)
    # nakshatra_for_longitude returns 0-indexed; convert to 1-indexed.
    return {
        "chart": bangalore_chart,
        "asc_sign": bangalore_chart["ascendant"]["sign"],
        "moon_nakshatra": moon_nak["index"] + 1,
    }


# ---------------------------------------------------------------------------
# D-18 table constants
# ---------------------------------------------------------------------------


class TestDoctrineConstants:
    """Pin the Yogini Dasha doctrine constants per D-18."""

    def test_eight_yoginis_named(self):
        from app.reading.sequences.yogini_dasha import YOGINI_NAMES

        assert YOGINI_NAMES == (
            "Mangala", "Pingala", "Dhanya", "Bhramari",
            "Bhadrika", "Ulka", "Siddha", "Sankata",
        )

    def test_yogini_lengths_sum_to_36(self):
        """The Yogini cycle is canonically 36 years."""
        from app.reading.sequences.yogini_dasha import YOGINI_LENGTHS

        assert YOGINI_LENGTHS == (1, 2, 3, 4, 5, 6, 7, 8)
        assert sum(YOGINI_LENGTHS) == 36

    def test_yogini_ruling_planets(self):
        from app.reading.sequences.yogini_dasha import (
            YOGINI_NAMES, YOGINI_RULING_PLANETS,
        )

        # Spec table: Mangala-Sun, Pingala-Moon, Dhanya-Jupiter, Bhramari-Mars,
        # Bhadrika-Mercury, Ulka-Saturn, Siddha-Venus, Sankata-Rahu.
        assert YOGINI_RULING_PLANETS == (
            "Sun", "Moon", "Jupiter", "Mars",
            "Mercury", "Saturn", "Venus", "Rahu",
        )
        # Sanity: ordered parallel with YOGINI_NAMES.
        assert len(YOGINI_NAMES) == len(YOGINI_RULING_PLANETS) == 8

    def test_yogini_md_check_keys_are_the_five_named(self):
        from app.reading.sequences.yogini_dasha import YOGINI_MD_CHECK_KEYS

        assert YOGINI_MD_CHECK_KEYS == (
            "ruling_yogini_nature",
            "ruling_planet_placement",
            "ruling_planet_dignity",
            "ruling_planet_in_kendra_or_kona",
            "cross_check_with_vimshottari",
        )

    def test_nakshatra_to_yogini_table_size_and_range(self):
        from app.reading.sequences.yogini_dasha import NAKSHATRA_TO_YOGINI

        # All 27 nakshatras must be present.
        assert set(NAKSHATRA_TO_YOGINI.keys()) == set(range(1, 28))
        # Every value is a valid yogini index 0..7.
        for nak, yog_idx in NAKSHATRA_TO_YOGINI.items():
            assert 0 <= yog_idx < 8, (
                f"nakshatra {nak} mapped to invalid yogini index {yog_idx}"
            )

    def test_revati_maps_to_dhanya(self):
        """Bangalore baseline Moon at Revati (nakshatra 27) → Dhanya."""
        from app.reading.sequences.yogini_dasha import (
            NAKSHATRA_TO_YOGINI, YOGINI_NAMES,
        )

        assert NAKSHATRA_TO_YOGINI[27] == 2
        assert YOGINI_NAMES[2] == "Dhanya"

    def test_ashwini_maps_to_mangala(self):
        """Per D-18, Ashwini (nakshatra 1) starts the cycle at Mangala."""
        from app.reading.sequences.yogini_dasha import (
            NAKSHATRA_TO_YOGINI, YOGINI_NAMES,
        )

        assert NAKSHATRA_TO_YOGINI[1] == 0
        assert YOGINI_NAMES[0] == "Mangala"


# ---------------------------------------------------------------------------
# Bangalore baseline structural conformance
# ---------------------------------------------------------------------------


class TestRunSequenceBaseline:

    def test_returns_yogini_dasha_result(self, baseline_inputs):
        from app.reading.sequences.yogini_dasha import (
            YoginiDashaResult, run_sequence,
        )

        result = run_sequence(**baseline_inputs)
        assert isinstance(result, YoginiDashaResult)

    def test_starting_yogini_for_revati_is_dhanya(self, baseline_inputs):
        """Bangalore baseline Moon at Revati (nakshatra 27) → Dhanya."""
        from app.reading.sequences.yogini_dasha import run_sequence

        result = run_sequence(**baseline_inputs)
        assert result.starting_yogini == "Dhanya"
        assert result.starting_yogini_index == 2

    def test_timeline_nonempty(self, baseline_inputs):
        from app.reading.sequences.yogini_dasha import run_sequence

        result = run_sequence(**baseline_inputs)
        assert len(result.timeline) >= 1

    def test_timeline_covers_three_cycles(self, baseline_inputs):
        """The lifetime timeline must cover at least 3 × 36-year cycles
        to span the standard 100-year forecast horizon."""
        from app.reading.sequences.yogini_dasha import run_sequence

        result = run_sequence(**baseline_inputs)
        # 3 cycles = 24 MDs (8 yoginis × 3).
        assert len(result.timeline) == 24

    def test_timeline_total_years_equals_three_cycles(self, baseline_inputs):
        """Total span of timeline should be 3 × 36 = 108 years."""
        from app.reading.sequences.yogini_dasha import run_sequence

        result = run_sequence(**baseline_inputs)
        total_years = sum(j.length_years for j in result.timeline)
        assert total_years == 108

    def test_exactly_one_current_judgment(self, baseline_inputs):
        from app.reading.sequences.yogini_dasha import run_sequence

        result = run_sequence(**baseline_inputs)
        currents = [j for j in result.timeline if j.is_current]
        assert len(currents) == 1

    def test_current_md_at_birth_is_first_period(self, baseline_inputs):
        """For birth-time evaluation, the first period (the starting
        Yogini) is always the current MD."""
        from app.reading.sequences.yogini_dasha import run_sequence

        result = run_sequence(**baseline_inputs)
        assert result.current_md_judgment.yogini == "Dhanya"
        assert result.current_md_judgment.ruling_planet == "Jupiter"
        assert result.current_md_judgment.length_years == 3
        assert result.current_md_judgment is result.timeline[0]

    def test_current_md_age_at_start_is_zero(self, baseline_inputs):
        """Current Yogini MD at birth starts at age 0."""
        from app.reading.sequences.yogini_dasha import run_sequence

        result = run_sequence(**baseline_inputs)
        # Allow tiny float wobble.
        assert abs(result.current_md_judgment.age_at_start) < 1e-6


# ---------------------------------------------------------------------------
# Per-MD judgment shape: 5 named checks, Finding instances, ID grammar
# ---------------------------------------------------------------------------


class TestJudgmentShape:

    def test_all_judgments_have_five_check_keys(self, baseline_inputs):
        from app.reading.sequences.yogini_dasha import (
            YOGINI_MD_CHECK_KEYS, run_sequence,
        )

        result = run_sequence(**baseline_inputs)
        expected = set(YOGINI_MD_CHECK_KEYS)
        for j in result.timeline:
            assert set(j.checks.keys()) == expected, (
                f"Yogini={j.yogini} checks mismatch: "
                f"missing={expected - set(j.checks.keys())}, "
                f"extra={set(j.checks.keys()) - expected}"
            )

    def test_each_check_is_finding(self, baseline_inputs):
        from app.reading.schema import Finding
        from app.reading.sequences.yogini_dasha import run_sequence

        result = run_sequence(**baseline_inputs)
        for key, finding in result.current_md_judgment.checks.items():
            assert isinstance(finding, Finding), (
                f"check {key} is not a Finding instance"
            )

    def test_overall_verdict_is_finding(self, baseline_inputs):
        from app.reading.schema import Finding
        from app.reading.sequences.yogini_dasha import run_sequence

        result = run_sequence(**baseline_inputs)
        assert isinstance(result.current_md_judgment.overall_verdict, Finding)

    def test_check_finding_ids_use_seq_yogini_grammar(self, baseline_inputs):
        from app.reading.sequences.yogini_dasha import run_sequence

        result = run_sequence(**baseline_inputs)
        for key, finding in result.current_md_judgment.checks.items():
            assert finding.id.startswith("seq_yogini."), (
                f"check {key} id {finding.id!r} must start with 'seq_yogini.'"
            )

    def test_source_sequence_tagged(self, baseline_inputs):
        from app.reading.sequences.yogini_dasha import run_sequence

        result = run_sequence(**baseline_inputs)
        for f in result.current_md_judgment.checks.values():
            assert f.source_sequence == "yogini_dasha"


# ---------------------------------------------------------------------------
# Antardasha sub-period structure
# ---------------------------------------------------------------------------


class TestAntardashas:

    def test_eight_ads_per_md(self, baseline_inputs):
        """Each Yogini MD contains 8 ADs (one per Yogini in cycle order)."""
        from app.reading.sequences.yogini_dasha import run_sequence

        result = run_sequence(**baseline_inputs)
        for md in result.timeline:
            assert len(md.antardashas) == 8, (
                f"Yogini={md.yogini}: expected 8 ADs, got {len(md.antardashas)}"
            )

    def test_first_ad_is_md_yogini_itself(self, baseline_inputs):
        """The first AD of an MD is the MD-yogini repeated (per cycle order)."""
        from app.reading.sequences.yogini_dasha import run_sequence

        result = run_sequence(**baseline_inputs)
        for md in result.timeline:
            assert md.antardashas[0].ad_yogini == md.yogini

    def test_ad_fractions_sum_to_one(self, baseline_inputs):
        """Sum of AD fraction-of-MD weights must equal 1.0 (full coverage)."""
        from app.reading.sequences.yogini_dasha import run_sequence

        result = run_sequence(**baseline_inputs)
        for md in result.timeline:
            total = sum(ad.fraction_of_md for ad in md.antardashas)
            assert abs(total - 1.0) < 1e-9, (
                f"Yogini={md.yogini} AD fractions sum {total} != 1.0"
            )

    def test_ads_chain_without_gaps(self, baseline_inputs):
        """AD boundaries must chain: end of ad[i] == start of ad[i+1]."""
        from app.reading.sequences.yogini_dasha import run_sequence

        result = run_sequence(**baseline_inputs)
        for md in result.timeline:
            for i in range(len(md.antardashas) - 1):
                assert (
                    abs(md.antardashas[i].end_jd - md.antardashas[i + 1].start_jd)
                    < 1e-6
                ), f"AD gap in MD={md.yogini} between ADs {i} and {i + 1}"


# ---------------------------------------------------------------------------
# Timeline chronological invariants
# ---------------------------------------------------------------------------


class TestTimelineInvariants:

    def test_md_boundaries_chain(self, baseline_inputs):
        """MD boundaries chain end-to-start through the lifetime."""
        from app.reading.sequences.yogini_dasha import run_sequence

        result = run_sequence(**baseline_inputs)
        for i in range(len(result.timeline) - 1):
            assert abs(
                result.timeline[i].end_jd - result.timeline[i + 1].start_jd
            ) < 1e-6, (
                f"MD gap between {result.timeline[i].yogini} and "
                f"{result.timeline[i + 1].yogini}"
            )

    def test_md_lengths_follow_cycle(self, baseline_inputs):
        """Lengths must follow the 1,2,3,4,5,6,7,8 cycle starting from
        the moon-determined starting yogini."""
        from app.reading.sequences.yogini_dasha import (
            YOGINI_LENGTHS, run_sequence,
        )

        result = run_sequence(**baseline_inputs)
        start_idx = result.starting_yogini_index
        for i, judgment in enumerate(result.timeline):
            expected_len = YOGINI_LENGTHS[(start_idx + i) % 8]
            assert judgment.length_years == expected_len, (
                f"timeline[{i}]={judgment.yogini}: expected length "
                f"{expected_len}, got {judgment.length_years}"
            )


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


class TestInputValidation:

    def test_invalid_asc_sign_raises(self, bangalore_chart):
        from app.reading.sequences.yogini_dasha import run_sequence

        with pytest.raises(ValueError, match="asc_sign"):
            run_sequence(
                chart=bangalore_chart, asc_sign=0, moon_nakshatra=27,
            )

    def test_invalid_moon_nakshatra_raises(self, bangalore_chart):
        from app.reading.sequences.yogini_dasha import run_sequence

        with pytest.raises(ValueError, match="moon_nakshatra"):
            run_sequence(
                chart=bangalore_chart, asc_sign=6, moon_nakshatra=28,
            )

    def test_missing_d1_raises(self):
        from app.reading.sequences.yogini_dasha import run_sequence

        with pytest.raises(ValueError, match="d1"):
            run_sequence(
                chart={"birth_jd": 2448087.5}, asc_sign=6, moon_nakshatra=27,
            )

    def test_missing_birth_jd_raises(self):
        from app.reading.sequences.yogini_dasha import run_sequence

        with pytest.raises(ValueError, match="birth_jd"):
            run_sequence(
                chart={"d1": {}}, asc_sign=6, moon_nakshatra=27,
            )


# ---------------------------------------------------------------------------
# Spot-check the cross-check-with-vimshottari semantics
# ---------------------------------------------------------------------------


class TestVimshottariCrossCheck:
    """The Yogini's design purpose is to cross-validate Vimshottari.

    Bangalore baseline: Vimshottari MD = Mercury (from prior test pinning
    in ``test_vimshottari_md.py``); starting Yogini = Dhanya (Jupiter
    ruled). Neither resonance condition holds, but neither does the
    classification "malefic"; Dhanya is benefic, so we expect a positive
    direction with the supportive-cross-check verdict.
    """

    def test_cross_check_evidence_present(self, baseline_inputs):
        from app.reading.sequences.yogini_dasha import run_sequence

        result = run_sequence(**baseline_inputs)
        cross = result.current_md_judgment.checks["cross_check_with_vimshottari"]
        evidence_keys = [line.split("=", 1)[0] for line in cross.evidence]
        assert "yogini" in evidence_keys
        assert "vimshottari_md_lord" in evidence_keys
        assert "same_planet" in evidence_keys
