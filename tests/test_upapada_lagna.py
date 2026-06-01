"""Tests for app.core.upapada_lagna.compute_upapada.

Canonical fixture: Mainpuri chart — Scorpio Lagna (asc_sign=8).

Doctrine derivation for Mainpuri:
  12th house sign = _step_signs(8, 12) = 7 (Libra)
  12th lord       = Venus (rules Libra)
  Venus natal sign = 8 (Scorpio)
  Distance D = ((8 - 7) % 12) + 1 = 2
  D not in (1, 7) → no substitution
  UPL = _step_signs(8, 2) = 9 (Sagittarius)
  2nd from UPL    = _step_signs(9, 2) = 10 (Capricorn)
  UPL house from Lagna = ((9 - 8) % 12) + 1 = 2
"""
from __future__ import annotations

import pytest

from app.core.chart_model import Chart
from app.core.upapada_lagna import UpapadaResult, compute_upapada


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mainpuri_chart() -> Chart:
    """Mainpuri 1989 — Scorpio Lagna, canonical test fixture."""
    return Chart(
        asc_sign=8,
        asc_lon=224.06,
        planet_signs={
            "Sun": 6, "Moon": 11, "Mars": 6, "Mercury": 6,
            "Jupiter": 3, "Venus": 8, "Saturn": 9,
            "Rahu": 11, "Ketu": 5,
        },
        planet_houses={
            "Sun": 11, "Moon": 4, "Mars": 11, "Mercury": 11,
            "Jupiter": 8, "Venus": 1, "Saturn": 2,
            "Rahu": 4, "Ketu": 10,
        },
        planet_lons={
            "Sun": 175.12, "Moon": 317.64, "Mars": 171.00,
            "Mercury": 157.34, "Jupiter": 76.69, "Venus": 220.23,
            "Saturn": 254.36, "Rahu": 300.74, "Ketu": 120.74,
        },
    )


@pytest.fixture
def aries_lagna_chart() -> Chart:
    """Synthetic Aries Lagna — 12H = Pisces, 12L = Jupiter.

    Jupiter placed in Gemini (sign 3).
    Distance from Pisces(12) to Gemini(3) = ((3-12)%12)+1 = 4.
    D=4, no substitution. UPL = _step_signs(3, 4) = 6 (Virgo).
    2nd from UPL = 7 (Libra).
    """
    return Chart(
        asc_sign=1,
        asc_lon=0.0,
        planet_signs={
            "Sun": 1, "Moon": 4, "Mars": 1, "Mercury": 2,
            "Jupiter": 3, "Venus": 2, "Saturn": 10,
            "Rahu": 9, "Ketu": 3,
        },
        planet_houses={
            "Sun": 1, "Moon": 4, "Mars": 1, "Mercury": 2,
            "Jupiter": 3, "Venus": 2, "Saturn": 10,
            "Rahu": 9, "Ketu": 3,
        },
        planet_lons={
            "Sun": 5.0, "Moon": 95.0, "Mars": 10.0, "Mercury": 35.0,
            "Jupiter": 65.0, "Venus": 40.0, "Saturn": 275.0,
            "Rahu": 260.0, "Ketu": 80.0,
        },
    )


@pytest.fixture
def substitution_chart() -> Chart:
    """Synthetic chart where 12L lands on its own 12H → substitution triggers.

    Libra Lagna (asc_sign=7): 12H = Virgo (sign 6), 12L = Mercury.
    Mercury placed in Virgo (sign 6) itself.
    Distance D = ((6-6)%12)+1 = 1 → substitution triggered.
    UPL = _step_signs(mercury_sign=6, 10) = _step_signs(6, 10) = 3 (Gemini).
    """
    return Chart(
        asc_sign=7,
        asc_lon=180.0,
        planet_signs={
            "Sun": 7, "Moon": 10, "Mars": 7, "Mercury": 6,
            "Jupiter": 1, "Venus": 7, "Saturn": 4,
            "Rahu": 3, "Ketu": 9,
        },
        planet_houses={
            "Sun": 1, "Moon": 4, "Mars": 1, "Mercury": 12,
            "Jupiter": 7, "Venus": 1, "Saturn": 10,
            "Rahu": 9, "Ketu": 3,
        },
        planet_lons={
            "Sun": 185.0, "Moon": 275.0, "Mars": 190.0, "Mercury": 167.0,
            "Jupiter": 5.0, "Venus": 188.0, "Saturn": 95.0,
            "Rahu": 65.0, "Ketu": 245.0,
        },
    )


# ---------------------------------------------------------------------------
# Tests — return type
# ---------------------------------------------------------------------------


class TestUpapadaReturnType:
    """compute_upapada always returns a UpapadaResult dataclass."""

    def test_returns_upapada_result_instance(self, mainpuri_chart: Chart) -> None:
        """Verify return is UpapadaResult."""
        result = compute_upapada(mainpuri_chart)
        assert isinstance(result, UpapadaResult)

    def test_upapada_sign_in_range(self, mainpuri_chart: Chart) -> None:
        """upapada_sign must be a valid zodiac sign 1..12."""
        result = compute_upapada(mainpuri_chart)
        assert 1 <= result.upapada_sign <= 12

    def test_second_from_upl_in_range(self, mainpuri_chart: Chart) -> None:
        """second_from_upl_sign must be 1..12."""
        result = compute_upapada(mainpuri_chart)
        assert 1 <= result.second_from_upl_sign <= 12


# ---------------------------------------------------------------------------
# Tests — Mainpuri canonical values
# ---------------------------------------------------------------------------


class TestMainpuriUPL:
    """Verify computed UPL against the hand-traced formula for Mainpuri."""

    def test_twelfth_lord_is_venus(self, mainpuri_chart: Chart) -> None:
        """12H of Scorpio = Libra; lord of Libra = Venus."""
        result = compute_upapada(mainpuri_chart)
        assert result.twelfth_lord == "Venus"

    def test_twelfth_lord_house_is_first(self, mainpuri_chart: Chart) -> None:
        """Venus is in house 1 of the Mainpuri chart."""
        result = compute_upapada(mainpuri_chart)
        assert result.twelfth_lord_house == 1

    def test_upapada_sign_is_sagittarius(self, mainpuri_chart: Chart) -> None:
        """UPL = step(Venus_sign=8, D=2) = 9 (Sagittarius)."""
        result = compute_upapada(mainpuri_chart)
        assert result.upapada_sign == 9

    def test_upapada_house_from_lagna_is_second(self, mainpuri_chart: Chart) -> None:
        """Sagittarius (sign 9) is 2nd from Scorpio Lagna (sign 8)."""
        result = compute_upapada(mainpuri_chart)
        assert result.upapada_house_from_lagna == 2

    def test_second_from_upl_is_capricorn(self, mainpuri_chart: Chart) -> None:
        """2nd from Sagittarius = Capricorn (sign 10)."""
        result = compute_upapada(mainpuri_chart)
        assert result.second_from_upl_sign == 10

    def test_no_substitution_for_mainpuri(self, mainpuri_chart: Chart) -> None:
        """Distance D=2 does not trigger the 10th-rule substitution (D=1 or D=7)."""
        result = compute_upapada(mainpuri_chart)
        assert result.substitution_applied is False

    def test_distance_used_is_two(self, mainpuri_chart: Chart) -> None:
        """Jaimini step-distance D=2 (Venus in Scorpio, 12H=Libra)."""
        result = compute_upapada(mainpuri_chart)
        assert result.distance_used == 2


# ---------------------------------------------------------------------------
# Tests — Aries Lagna formula walkthrough
# ---------------------------------------------------------------------------


class TestAriesLagnaUPL:
    """Walkthrough for Aries Lagna where Jupiter is 12L placed in Gemini."""

    def test_twelfth_lord_is_jupiter(self, aries_lagna_chart: Chart) -> None:
        """12H of Aries = Pisces (sign 12); 12L = Jupiter."""
        result = compute_upapada(aries_lagna_chart)
        assert result.twelfth_lord == "Jupiter"

    def test_upapada_sign_is_virgo(self, aries_lagna_chart: Chart) -> None:
        """D=4 (Pisces→Gemini inclusive). UPL = step(Gemini=3, 4) = 6 (Virgo)."""
        result = compute_upapada(aries_lagna_chart)
        assert result.upapada_sign == 6

    def test_second_from_upl_is_libra(self, aries_lagna_chart: Chart) -> None:
        """2nd from Virgo = Libra (sign 7)."""
        result = compute_upapada(aries_lagna_chart)
        assert result.second_from_upl_sign == 7

    def test_no_substitution(self, aries_lagna_chart: Chart) -> None:
        """D=4 does not trigger substitution."""
        result = compute_upapada(aries_lagna_chart)
        assert result.substitution_applied is False


# ---------------------------------------------------------------------------
# Tests — Substitution (D=1)
# ---------------------------------------------------------------------------


class TestSubstitutionRule:
    """When D=1 or D=7, the 10th-from-lord substitution must fire."""

    def test_substitution_applied_when_d_equals_1(
        self, substitution_chart: Chart
    ) -> None:
        """Libra Lagna: 12L Mercury in Virgo (12H) → D=1 → substitution applied."""
        result = compute_upapada(substitution_chart)
        assert result.substitution_applied is True

    def test_upapada_sign_is_10th_from_lord_when_substituted(
        self, substitution_chart: Chart
    ) -> None:
        """Substituted UPL = step(Mercury_sign=6, 10) = Gemini (sign 3)."""
        result = compute_upapada(substitution_chart)
        # _step_signs(6, 10) = ((6-1+10-1)%12)+1 = (14%12)+1 = 3
        assert result.upapada_sign == 3

    def test_distance_used_is_10_when_substituted(
        self, substitution_chart: Chart
    ) -> None:
        """distance_used reflects the 10th-rule override, not the raw D=1."""
        result = compute_upapada(substitution_chart)
        assert result.distance_used == 10


# ---------------------------------------------------------------------------
# Tests — Error handling
# ---------------------------------------------------------------------------


class TestUpapadaErrors:
    """compute_upapada raises ValueError on incomplete charts."""

    def test_raises_when_twelfth_lord_missing(self) -> None:
        """Missing 12H lord sign must raise ValueError with descriptive message."""
        # Scorpio Lagna (8): 12H = Libra, 12L = Venus. Omit Venus.
        chart = Chart(
            asc_sign=8,
            asc_lon=224.0,
            planet_signs={
                "Sun": 6, "Moon": 11, "Mars": 6, "Mercury": 6,
                "Jupiter": 3, "Saturn": 9,
                "Rahu": 11, "Ketu": 5,
                # Venus deliberately omitted
            },
            planet_houses={
                "Sun": 11, "Moon": 4, "Mars": 11, "Mercury": 11,
                "Jupiter": 8, "Saturn": 2,
                "Rahu": 4, "Ketu": 10,
            },
            planet_lons={
                "Sun": 175.12, "Moon": 317.64, "Mars": 171.00,
                "Mercury": 157.34, "Jupiter": 76.69,
                "Saturn": 254.36, "Rahu": 300.74, "Ketu": 120.74,
            },
        )
        with pytest.raises(ValueError, match="Venus"):
            compute_upapada(chart)
