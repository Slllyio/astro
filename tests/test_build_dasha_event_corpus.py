"""Tests for the Fork-A dasha-event corpus builder.

Covers the deterministic core (mahadasha sequence) and the
event-attribution logic for one synthetic person. The full ETL is
exercised separately as a smoke run on a small slice of real data.
"""
from __future__ import annotations

import math

import pytest

from app.core.ephemeris_engine import DASHA_LORDS, DAYS_PER_VEDIC_YEAR
from app.medini.etl.build_dasha_event_corpus import (
    DashaWindow,
    ThreeLevelWindow,
    _ad_durations_within_md,
    _pd_durations_within_ad,
    _slug,
    mahadasha_sequence,
    vimshottari_3_level_sequence,
)


# --------------------------------------------------------------------------- #
# mahadasha_sequence — core invariants                                        #
# --------------------------------------------------------------------------- #

class TestMahadashaSequence:
    def test_first_window_starts_at_birth(self) -> None:
        birth_jd = 2450000.0
        windows = mahadasha_sequence(moon_longitude=10.0, birth_jd=birth_jd,
                                     observation_years=100.0)
        assert windows[0].start_jd == birth_jd

    def test_first_window_truncated_for_mid_nakshatra_birth(self) -> None:
        """Birth at exact start of a nakshatra → first window is full duration.
        Birth at mid-nakshatra → first window is roughly half the lord's total."""
        # Nakshatra 0 (Ashwini, Ketu lord, 7y). At lon=0 → full 7y remaining.
        full = mahadasha_sequence(moon_longitude=0.0, birth_jd=0.0,
                                  observation_years=100.0)[0]
        assert full.lord == "Ketu"
        assert full.duration_years == pytest.approx(7.0, abs=0.01)

        # At mid-nakshatra (lon = nakshatra_span/2) → half remaining = 3.5y.
        half_lon = (360.0 / 27.0) / 2.0
        half = mahadasha_sequence(moon_longitude=half_lon, birth_jd=0.0,
                                  observation_years=100.0)[0]
        assert half.lord == "Ketu"
        assert half.duration_years == pytest.approx(3.5, abs=0.01)

    def test_consecutive_windows_are_contiguous(self) -> None:
        """Window N's end_jd == Window N+1's start_jd, no gaps or overlaps."""
        windows = mahadasha_sequence(moon_longitude=37.0, birth_jd=2450000.0,
                                     observation_years=80.0)
        assert len(windows) > 5
        for i in range(len(windows) - 1):
            assert windows[i].end_jd == windows[i + 1].start_jd

    def test_lord_cycle_follows_dasha_lords_order(self) -> None:
        """After the first window, lords follow the DASHA_LORDS cycle."""
        windows = mahadasha_sequence(moon_longitude=5.0, birth_jd=0.0,
                                     observation_years=100.0)
        # First lord is Ketu (nakshatra 0); next should be Venus, then Sun…
        expected_after = ["Venus", "Sun", "Moon", "Mars", "Rahu",
                          "Jupiter", "Saturn", "Mercury", "Ketu"]
        for i, expected in enumerate(expected_after[:len(windows) - 1]):
            assert windows[i + 1].lord == expected, f"window {i+1}: {windows[i+1].lord!r} != {expected}"

    def test_observation_window_bounds_total_duration(self) -> None:
        """Total duration covered ≤ observation_years + last-dasha-span overshoot."""
        obs = 60.0
        birth = 2450000.0
        windows = mahadasha_sequence(moon_longitude=10.0, birth_jd=birth,
                                     observation_years=obs)
        # Final window's end JD shouldn't be more than max-dasha-span past
        # birth + obs.
        max_dasha_span = max(d[1] for d in DASHA_LORDS) * DAYS_PER_VEDIC_YEAR
        assert windows[-1].end_jd <= birth + obs * DAYS_PER_VEDIC_YEAR + max_dasha_span

    def test_zero_observation_years_returns_empty(self) -> None:
        assert mahadasha_sequence(10.0, 0.0, observation_years=0.0) == []
        assert mahadasha_sequence(10.0, 0.0, observation_years=-1.0) == []

    def test_window_durations_match_classical_table(self) -> None:
        """Full-duration windows match the classical 7/20/6/10/7/18/16/19/17 table."""
        windows = mahadasha_sequence(moon_longitude=0.0, birth_jd=0.0,
                                     observation_years=200.0)
        expected_lords_durs = [
            ("Ketu", 7), ("Venus", 20), ("Sun", 6), ("Moon", 10), ("Mars", 7),
            ("Rahu", 18), ("Jupiter", 16), ("Saturn", 19), ("Mercury", 17),
        ]
        # First window is full because lon=0 (start of Ketu nakshatra).
        for window, (lord, dur) in zip(windows, expected_lords_durs):
            assert window.lord == lord
            assert window.duration_years == pytest.approx(float(dur), abs=0.01)


# --------------------------------------------------------------------------- #
# slug helper                                                                  #
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# 3-level sub-cycle: AD durations within MD                                   #
# --------------------------------------------------------------------------- #

class TestADWithinMD:
    def test_venus_md_first_ad_is_venus(self) -> None:
        """AD sequence starts with the MD lord itself."""
        ads = _ad_durations_within_md("Venus")
        assert ads[0][0] == "Venus"

    def test_venus_md_ad_durations_sum_to_md_total(self) -> None:
        """Sum of AD durations within a 20y Venus MD = exactly 20y."""
        ads = _ad_durations_within_md("Venus")
        total = sum(yrs for _, yrs in ads)
        assert total == pytest.approx(20.0, abs=1e-9)

    def test_venus_md_sun_ad_duration_classical(self) -> None:
        """Venus MD × Sun AD = 20 × 6 / 120 = 1.0 year."""
        ads = dict(_ad_durations_within_md("Venus"))
        assert ads["Sun"] == pytest.approx(1.0, abs=1e-9)

    def test_jupiter_md_saturn_ad_duration_classical(self) -> None:
        """Jupiter MD (16y) × Saturn AD (19y total) = 16 × 19 / 120 = 2.533y."""
        ads = dict(_ad_durations_within_md("Jupiter"))
        assert ads["Saturn"] == pytest.approx(16 * 19 / 120.0, abs=1e-9)

    def test_ad_order_follows_dasha_lords_cycle(self) -> None:
        """After Venus AD, the next AD is Sun (Venus's successor in DASHA_LORDS)."""
        ads = _ad_durations_within_md("Venus")
        # DASHA_LORDS order: Ketu, Venus, Sun, Moon, Mars, Rahu, Jup, Sat, Mer
        expected = ["Venus", "Sun", "Moon", "Mars", "Rahu",
                    "Jupiter", "Saturn", "Mercury", "Ketu"]
        assert [a[0] for a in ads] == expected


# --------------------------------------------------------------------------- #
# 3-level sub-cycle: PD durations within AD                                   #
# --------------------------------------------------------------------------- #

class TestPDWithinAD:
    def test_pd_sequence_starts_with_ad_lord(self) -> None:
        pds = _pd_durations_within_ad("Saturn", ad_years=2.533)
        assert pds[0][0] == "Saturn"

    def test_pd_durations_sum_to_ad_total(self) -> None:
        ad_years = 1.0  # Venus MD × Sun AD
        pds = _pd_durations_within_ad("Sun", ad_years=ad_years)
        assert sum(yrs for _, yrs in pds) == pytest.approx(ad_years, abs=1e-9)

    def test_sun_ad_in_venus_md_jupiter_pd_duration(self) -> None:
        """Venus MD × Sun AD × Jupiter PD = 20 × 6 × 16 / 120^2 = 0.1333y."""
        pds = dict(_pd_durations_within_ad("Sun", ad_years=1.0))
        # 1.0 year × 16/120 = 0.1333y
        assert pds["Jupiter"] == pytest.approx(16.0 / 120.0, abs=1e-9)


# --------------------------------------------------------------------------- #
# 3-level full sequence                                                       #
# --------------------------------------------------------------------------- #

class TestVimshottari3Level:
    def test_returns_leaf_windows_with_three_lords(self) -> None:
        leaves = vimshottari_3_level_sequence(
            moon_longitude=10.0, birth_jd=2450000.0, observation_years=20.0
        )
        assert len(leaves) > 50  # 20y is several MDs × 9 ADs × 9 PDs
        first = leaves[0]
        assert isinstance(first, ThreeLevelWindow)
        assert first.md_lord in {"Ketu", "Venus", "Sun", "Moon", "Mars",
                                 "Rahu", "Jupiter", "Saturn", "Mercury"}
        assert first.ad_lord in {"Ketu", "Venus", "Sun", "Moon", "Mars",
                                 "Rahu", "Jupiter", "Saturn", "Mercury"}
        assert first.pd_lord in {"Ketu", "Venus", "Sun", "Moon", "Mars",
                                 "Rahu", "Jupiter", "Saturn", "Mercury"}

    def test_first_window_starts_no_earlier_than_birth(self) -> None:
        """Truncation: no PD window can begin before birth_jd."""
        birth_jd = 2450000.0
        leaves = vimshottari_3_level_sequence(
            moon_longitude=200.0, birth_jd=birth_jd, observation_years=10.0
        )
        assert all(w.start_jd >= birth_jd for w in leaves)

    def test_first_md_first_ad_first_pd_chain_matches_md_lord(self) -> None:
        """At birth (moon at start of Ashwini, Ketu nakshatra), first leaf
        should have md_lord=ad_lord=pd_lord=Ketu (since AD and PD both start
        with the MD lord)."""
        leaves = vimshottari_3_level_sequence(
            moon_longitude=0.0, birth_jd=0.0, observation_years=10.0
        )
        first = leaves[0]
        assert first.md_lord == "Ketu"
        assert first.ad_lord == "Ketu"
        assert first.pd_lord == "Ketu"

    def test_leaf_durations_within_md_sum_to_md_total(self) -> None:
        """For a full unrabbited Ketu MD, the leaf durations should sum to 7y."""
        # Birth at lon=0 = start of Ashwini → first MD is full 7y Ketu.
        leaves = vimshottari_3_level_sequence(
            moon_longitude=0.0, birth_jd=0.0, observation_years=8.0,
        )
        ketu_md_leaves = [w for w in leaves if w.md_seq_idx == 0]
        total_days = sum(w.duration_days for w in ketu_md_leaves)
        from app.core.ephemeris_engine import DAYS_PER_VEDIC_YEAR
        assert total_days == pytest.approx(7.0 * DAYS_PER_VEDIC_YEAR, abs=1e-6)

    def test_consecutive_leaves_are_contiguous(self) -> None:
        """No gaps between consecutive leaf windows (within a person's timeline)."""
        leaves = vimshottari_3_level_sequence(
            moon_longitude=37.0, birth_jd=2450000.0, observation_years=20.0
        )
        for i in range(len(leaves) - 1):
            assert leaves[i].end_jd == pytest.approx(leaves[i + 1].start_jd, abs=1e-6), \
                f"gap between leaf {i} and {i+1}"

    def test_zero_observation_years_returns_empty(self) -> None:
        assert vimshottari_3_level_sequence(10.0, 0.0, 0.0) == []


class TestSlug:
    def test_basic_lowercase(self) -> None:
        assert _slug("Career") == "career"

    def test_spaces_to_underscores(self) -> None:
        assert _slug("Death by Disease") == "death_by_disease"

    def test_slash_to_underscore(self) -> None:
        assert _slug("Published/ Exhibited/ Released") == "published_exhibited_released"

    def test_comma_dropped(self) -> None:
        assert _slug("Death, Cause unspecified") == "death_cause_unspecified"

    def test_collapses_double_underscores(self) -> None:
        assert "__" not in _slug("Death, Cause unspecified")
