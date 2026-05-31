"""Tests for S-2 doctrinal additions to app.core.panchanga.

The existing tests/test_panchanga.py pins the TypedDict-based basic
API (compute_panchanga, _tithi_info etc.). This file pins ONLY the
new dataclass-based richness layer added in S-2:

  * TithiReading       — adds group + lord + is_auspicious_default
  * NityaYogaReading   — adds is_inauspicious flag
  * KaranaReading      — adds is_movable + is_inauspicious flags
  * VaraReading        — adds lord
  * BirthPanchanga     — aggregate with has_caution_flag
  * compute_birth_panchanga(sun_lon, moon_lon, jd, nakshatra_index)
  * format_birth_panchanga()

These additions are used by master_reading.MasterReading.birth_panchanga.
"""
from __future__ import annotations

import pytest

from app.core.panchanga import (
    BirthPanchanga, KaranaReading, NityaYogaReading,
    TITHI_GROUP, TithiReading, VARA_LORDS, VaraReading,
    compute_birth_panchanga, format_birth_panchanga,
)


class TestTithiReadingDoctrinal:
    """The S-2 layer adds group + lord + is_auspicious to plain TithiInfo."""

    def test_rikta_group_for_shukla_4_9_14(self):
        """Tithis 4/9/14 in any paksha belong to Rikta group."""
        for shukla_num in (4, 9, 14):
            # moon-sun diff = (shukla_num-1)*12 + small offset → idx shukla_num-1
            bp = compute_birth_panchanga(
                sun_lon=0.0,
                moon_lon=(shukla_num - 1) * 12.0 + 6.0,
                birth_jd=2447988.0, moon_nakshatra_index=0,
            )
            assert bp.tithi.number_in_paksha == shukla_num
            assert bp.tithi.group == "Rikta"

    def test_krishna_rikta_marked_inauspicious(self):
        """Krishna 4/9/14 = is_auspicious_default False (Phaladeepika Ch.3)."""
        # Krishna Chaturthi: diff = 15*12 + 3*12 = 216 deg
        bp = compute_birth_panchanga(
            sun_lon=0.0, moon_lon=216.0,
            birth_jd=2447988.0, moon_nakshatra_index=0,
        )
        assert bp.tithi.paksha == "Krishna"
        assert bp.tithi.number_in_paksha == 4
        assert bp.tithi.is_auspicious_default is False

    def test_shukla_rikta_still_auspicious_default(self):
        """Shukla 4/9/14 keeps default-auspicious (only Krishna Rikta is bad)."""
        bp = compute_birth_panchanga(
            sun_lon=0.0, moon_lon=42.0,  # Shukla Chaturthi
            birth_jd=2447988.0, moon_nakshatra_index=0,
        )
        assert bp.tithi.paksha == "Shukla" and bp.tithi.number_in_paksha == 4
        assert bp.tithi.is_auspicious_default is True

    def test_lord_cycles_through_7_planets(self):
        """Tithi lord cycles Sun→Mars→Mercury→Jupiter→Venus→Saturn→Rahu."""
        expected = ["Sun", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu"]
        for idx, expected_lord in enumerate(expected):
            bp = compute_birth_panchanga(
                sun_lon=0.0, moon_lon=idx * 12.0 + 6.0,
                birth_jd=2447988.0, moon_nakshatra_index=0,
            )
            assert bp.tithi.lord == expected_lord, f"tithi idx {idx}"

    def test_tithi_group_set_complete(self):
        """All 5 classical groups present."""
        assert TITHI_GROUP == ("Nanda", "Bhadra", "Jaya", "Rikta", "Purna")


class TestYogaCautionFlag:
    def test_vyatipata_marked_inauspicious(self):
        """Vyatipata (idx 16, name 'Vyatipata') is in the caution set."""
        # Sun+Moon = 16*13.33 + small = 213.4 → idx 16 = Vyatipata
        bp = compute_birth_panchanga(
            sun_lon=106.0, moon_lon=107.5,
            birth_jd=2447988.0, moon_nakshatra_index=0,
        )
        assert bp.yoga.name == "Vyatipata"
        assert bp.yoga.is_inauspicious is True

    def test_preeti_marked_auspicious(self):
        """Preeti (idx 1) is not in the caution set."""
        bp = compute_birth_panchanga(
            sun_lon=0.0, moon_lon=14.0,
            birth_jd=2447988.0, moon_nakshatra_index=0,
        )
        assert bp.yoga.name == "Priti"
        assert bp.yoga.is_inauspicious is False


class TestKaranaCautionFlag:
    def test_first_karana_is_kimstughna_fixed(self):
        bp = compute_birth_panchanga(
            sun_lon=0.0, moon_lon=1.0,
            birth_jd=2447988.0, moon_nakshatra_index=0,
        )
        assert bp.karana.name == "Kimstughna"
        assert bp.karana.is_movable is False
        assert bp.karana.is_inauspicious is False

    def test_vishti_marked_inauspicious_when_found(self):
        """Vishti (last movable in each cycle) is the caution karana."""
        for diff in range(1, 360, 1):
            bp = compute_birth_panchanga(
                sun_lon=0.0, moon_lon=float(diff),
                birth_jd=2447988.0, moon_nakshatra_index=0,
            )
            if bp.karana.name == "Vishti":
                assert bp.karana.is_movable is True
                assert bp.karana.is_inauspicious is True
                return
        pytest.fail("Vishti not found in 360-deg sweep")


class TestVaraLord:
    def test_jd_2451545_saturday_lord_saturn(self):
        """JD 2451545.0 (2000-01-01 noon UT) = Saturday, lord Saturn."""
        bp = compute_birth_panchanga(
            sun_lon=0.0, moon_lon=0.0,
            birth_jd=2451545.0, moon_nakshatra_index=0,
        )
        assert bp.vara.name == "Saturday"
        assert bp.vara.lord == "Saturn"

    def test_lord_array_has_7_entries(self):
        assert len(VARA_LORDS) == 7


class TestBirthPanchangaCautionFlag:
    def test_caution_fires_on_vyatipata_yoga(self):
        """Birth at Vyatipata-yoga moment sets has_caution_flag True."""
        bp = compute_birth_panchanga(
            sun_lon=106.0, moon_lon=107.5,
            birth_jd=2447988.0, moon_nakshatra_index=0,
        )
        assert bp.yoga.name == "Vyatipata"
        assert bp.has_caution_flag is True

    def test_no_caution_on_clean_birth(self):
        """Shukla Preeti yoga, Bava karana, Sunday → no caution."""
        # Sun=0, Moon=14 → tithi idx 1, yoga Priti, karana Bava (Shukla 2nd half)
        bp = compute_birth_panchanga(
            sun_lon=0.0, moon_lon=14.0,
            birth_jd=2447988.0, moon_nakshatra_index=0,
        )
        # If all three components are clean, caution stays False
        if (bp.tithi.is_auspicious_default
                and not bp.yoga.is_inauspicious
                and not bp.karana.is_inauspicious):
            assert bp.has_caution_flag is False


class TestFormatting:
    def test_format_returns_string_with_all_limbs(self):
        bp = compute_birth_panchanga(
            sun_lon=88.6, moon_lon=351.0,
            birth_jd=2447988.0, moon_nakshatra_index=26,
        )
        text = format_birth_panchanga(bp)
        assert "BIRTH PANCHANGA" in text
        assert bp.vara.name in text
        assert bp.tithi.name in text
        assert bp.yoga.name in text
        assert bp.karana.name in text
