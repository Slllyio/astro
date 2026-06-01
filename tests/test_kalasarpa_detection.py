"""Tests for app.core.kalasarpa_detection.detect_kalasarpa.

Canonical fixture: Mainpuri 1989 — Scorpio Lagna.

Mainpuri arc analysis:
  Rahu = 300.74° (Aquarius, sign 11, house 4)
  Ketu = 120.74° (Leo, sign 5, house 10)

  Forward arc from Rahu (300.74) to each planet:
    Sun     (175.12) → (175.12 - 300.74) % 360 = 234.38 → second_half
    Moon    (317.64) → (317.64 - 300.74) % 360 =  16.90 → first_half
    Mars    (171.00) → (171.00 - 300.74) % 360 = 230.26 → second_half
    Mercury (157.34) → (157.34 - 300.74) % 360 = 216.60 → second_half
    Jupiter  (76.69) → ( 76.69 - 300.74) % 360 = 135.95 → first_half
    Venus   (220.23) → (220.23 - 300.74) % 360 = 279.49 → second_half
    Saturn  (254.36) → (254.36 - 300.74) % 360 = 313.62 → second_half

  first_half (Moon, Jupiter) ≠ all 7 → Kalasarpa BROKEN → active=False
  outside_planets = (Moon, Jupiter) — the minority hemicycle
"""
from __future__ import annotations

import pytest

from app.core.chart_model import Chart
from app.core.kalasarpa_detection import KalasarpaResult, detect_kalasarpa


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
def anant_kalasarpa_chart() -> Chart:
    """Synthetic chart where all 7 visible planets are in the Rahu→Ketu arc.

    Rahu at 10° (Aries, sign 1, house 1) → type = "Anant".
    Ketu at 190° (Libra, sign 7).
    All 7 visibles between 15° and 175° — strictly inside the first-half arc.
    Forward arc for each planet from Rahu(10°) is between 5° and 165°
    (all < 180) → all in first_half → Kalasarpa active.
    """
    return Chart(
        asc_sign=1,
        asc_lon=0.0,
        planet_signs={
            "Sun": 1, "Moon": 2, "Mars": 3, "Mercury": 4,
            "Jupiter": 5, "Venus": 6, "Saturn": 7,
            "Rahu": 1, "Ketu": 7,
        },
        planet_houses={
            "Sun": 1, "Moon": 2, "Mars": 3, "Mercury": 4,
            "Jupiter": 5, "Venus": 6, "Saturn": 7,
            "Rahu": 1, "Ketu": 7,
        },
        planet_lons={
            "Sun": 15.0,
            "Moon": 45.0,
            "Mars": 75.0,
            "Mercury": 105.0,
            "Jupiter": 135.0,
            "Venus": 155.0,
            "Saturn": 175.0,
            "Rahu": 10.0,
            "Ketu": 190.0,
        },
    )


@pytest.fixture
def ghatak_kalasarpa_chart() -> Chart:
    """Synthetic chart: all 7 visibles in the Ketu→Rahu arc (second_half).

    Rahu at 200° (Libra, sign 7, house 7) → type = "Takshaka".
    All planets between 210° and 380° (i.e., 10-20°) in forward arc
    from Rahu — that means arc > 180 → second_half.

    Actually let's use Rahu at 320° (Aquarius, sign 11, house 11 for Vishadhar).
    All 7 visibles between 325° and 135° (second_half arc from 320°).
    Forward arc = (planet_lon - 320) % 360.
    Planet at 330° → arc = 10 < 180 → first_half!
    Need planets where arc > 180, i.e., planet_lon < 320 and > (320 - 180) = 140.
    Place all 7 between 145° and 315°: arc = (145-320)%360=185 > 180 ✓
    """
    return Chart(
        asc_sign=11,
        asc_lon=300.0,
        planet_signs={
            "Sun": 5, "Moon": 6, "Mars": 7, "Mercury": 8,
            "Jupiter": 9, "Venus": 10, "Saturn": 11,
            "Rahu": 11, "Ketu": 5,
        },
        planet_houses={
            "Sun": 7, "Moon": 8, "Mars": 9, "Mercury": 10,
            "Jupiter": 11, "Venus": 12, "Saturn": 1,
            "Rahu": 11, "Ketu": 5,
        },
        planet_lons={
            "Sun": 145.0,
            "Moon": 165.0,
            "Mars": 185.0,
            "Mercury": 205.0,
            "Jupiter": 225.0,
            "Venus": 265.0,
            "Saturn": 305.0,
            "Rahu": 320.0,
            "Ketu": 140.0,
        },
    )


# ---------------------------------------------------------------------------
# Tests — return type
# ---------------------------------------------------------------------------


class TestKalasarpaReturnType:
    """detect_kalasarpa always returns a KalasarpaResult."""

    def test_returns_kalasarpa_result(self, mainpuri_chart: Chart) -> None:
        """Return value is a KalasarpaResult dataclass."""
        result = detect_kalasarpa(mainpuri_chart)
        assert isinstance(result, KalasarpaResult)

    def test_rahu_sign_matches_chart(self, mainpuri_chart: Chart) -> None:
        """rahu_sign in result matches chart.sign_of('Rahu')."""
        result = detect_kalasarpa(mainpuri_chart)
        assert result.rahu_sign == mainpuri_chart.sign_of("Rahu")

    def test_ketu_sign_matches_chart(self, mainpuri_chart: Chart) -> None:
        """ketu_sign in result matches chart.sign_of('Ketu')."""
        result = detect_kalasarpa(mainpuri_chart)
        assert result.ketu_sign == mainpuri_chart.sign_of("Ketu")

    def test_all_planets_signs_has_seven_entries(self, mainpuri_chart: Chart) -> None:
        """all_planets_signs carries exactly 7 (planet, sign) pairs."""
        result = detect_kalasarpa(mainpuri_chart)
        assert len(result.all_planets_signs) == 7


# ---------------------------------------------------------------------------
# Tests — Mainpuri (Kalasarpa broken)
# ---------------------------------------------------------------------------


class TestMainpuriKalasarpaBroken:
    """Mainpuri: Venus (Scorpio) is outside the Rahu→Ketu arc → dosha broken."""

    def test_active_is_false(self, mainpuri_chart: Chart) -> None:
        """Venus at 220.23° lies in second_half arc from Rahu(300.74°), while
        Moon and Jupiter are in first_half. Planets split across hemicycles
        → Kalasarpa MUST be inactive."""
        result = detect_kalasarpa(mainpuri_chart)
        assert result.active is False

    def test_kalasarpa_type_is_none(self, mainpuri_chart: Chart) -> None:
        """Type must be 'None' string when inactive."""
        result = detect_kalasarpa(mainpuri_chart)
        assert result.kalasarpa_type == "None"

    def test_planets_on_one_side_is_false(self, mainpuri_chart: Chart) -> None:
        """planets_on_one_side mirrors active."""
        result = detect_kalasarpa(mainpuri_chart)
        assert result.planets_on_one_side is False

    def test_outside_planets_contains_moon(self, mainpuri_chart: Chart) -> None:
        """Moon (first_half, minority group) must appear in outside_planets."""
        result = detect_kalasarpa(mainpuri_chart)
        assert "Moon" in result.outside_planets

    def test_outside_planets_contains_jupiter(self, mainpuri_chart: Chart) -> None:
        """Jupiter (first_half, minority group) must appear in outside_planets."""
        result = detect_kalasarpa(mainpuri_chart)
        assert "Jupiter" in result.outside_planets

    def test_outside_planets_excludes_majority(self, mainpuri_chart: Chart) -> None:
        """Sun, Mars, Mercury, Venus, Saturn are majority — not in outside_planets."""
        result = detect_kalasarpa(mainpuri_chart)
        majority = {"Sun", "Mars", "Mercury", "Venus", "Saturn"}
        assert not majority.intersection(set(result.outside_planets))

    def test_rahu_sign_is_aquarius(self, mainpuri_chart: Chart) -> None:
        """Rahu at 300.74° is in Aquarius (sign 11)."""
        result = detect_kalasarpa(mainpuri_chart)
        assert result.rahu_sign == 11

    def test_ketu_sign_is_leo(self, mainpuri_chart: Chart) -> None:
        """Ketu at 120.74° is in Leo (sign 5)."""
        result = detect_kalasarpa(mainpuri_chart)
        assert result.ketu_sign == 5


# ---------------------------------------------------------------------------
# Tests — Active Kalasarpa (all 7 in Rahu→Ketu arc)
# ---------------------------------------------------------------------------


class TestAnantKalasarpaActive:
    """anant_kalasarpa_chart: all 7 visibles inside the Rahu→Ketu (first_half) arc."""

    def test_active_is_true(self, anant_kalasarpa_chart: Chart) -> None:
        """All 7 visibles are between Rahu(10°) and Ketu(190°) → active=True."""
        result = detect_kalasarpa(anant_kalasarpa_chart)
        assert result.active is True

    def test_type_is_anant(self, anant_kalasarpa_chart: Chart) -> None:
        """Rahu in house 1 → Anant Kalasarpa."""
        result = detect_kalasarpa(anant_kalasarpa_chart)
        assert result.kalasarpa_type == "Anant"

    def test_outside_planets_empty(self, anant_kalasarpa_chart: Chart) -> None:
        """No planets outside the arc when yoga is active."""
        result = detect_kalasarpa(anant_kalasarpa_chart)
        assert result.outside_planets == ()

    def test_planets_on_one_side_true(self, anant_kalasarpa_chart: Chart) -> None:
        """planets_on_one_side == active when yoga fires."""
        result = detect_kalasarpa(anant_kalasarpa_chart)
        assert result.planets_on_one_side is True

    def test_rahu_sign_is_aries(self, anant_kalasarpa_chart: Chart) -> None:
        """Rahu at 10° → Aries (sign 1)."""
        result = detect_kalasarpa(anant_kalasarpa_chart)
        assert result.rahu_sign == 1


# ---------------------------------------------------------------------------
# Tests — Active Kalasarpa (all 7 in Ketu→Rahu / second_half arc)
# ---------------------------------------------------------------------------


class TestGhatakKalasarpaSecondHalf:
    """ghatak_kalasarpa_chart: all 7 in the Ketu→Rahu (second_half) arc."""

    def test_active_is_true(self, ghatak_kalasarpa_chart: Chart) -> None:
        """All 7 visibles in second_half → yoga still active."""
        result = detect_kalasarpa(ghatak_kalasarpa_chart)
        assert result.active is True

    def test_type_is_vishadhar(self, ghatak_kalasarpa_chart: Chart) -> None:
        """Rahu in house 11 → Vishadhar Kalasarpa."""
        result = detect_kalasarpa(ghatak_kalasarpa_chart)
        assert result.kalasarpa_type == "Vishadhar"

    def test_outside_planets_empty(self, ghatak_kalasarpa_chart: Chart) -> None:
        """No outside planets when all 7 are in the same hemicycle."""
        result = detect_kalasarpa(ghatak_kalasarpa_chart)
        assert result.outside_planets == ()


# ---------------------------------------------------------------------------
# Tests — Edge cases
# ---------------------------------------------------------------------------


class TestKalasarpaEdgeCases:
    """Edge-case behaviour."""

    def test_raises_on_missing_rahu(self) -> None:
        """Missing Rahu position must raise ValueError."""
        chart = Chart(
            asc_sign=1,
            asc_lon=0.0,
            planet_signs={
                "Sun": 1, "Moon": 2, "Mars": 3, "Mercury": 4,
                "Jupiter": 5, "Venus": 6, "Saturn": 7, "Ketu": 7,
            },
            planet_houses={
                "Sun": 1, "Moon": 2, "Mars": 3, "Mercury": 4,
                "Jupiter": 5, "Venus": 6, "Saturn": 7, "Ketu": 7,
            },
            planet_lons={
                "Sun": 5.0, "Moon": 35.0, "Mars": 65.0, "Mercury": 95.0,
                "Jupiter": 125.0, "Venus": 155.0, "Saturn": 185.0,
                "Ketu": 190.0,
            },
        )
        with pytest.raises(ValueError, match="Rahu"):
            detect_kalasarpa(chart)

    def test_ketu_sign_derived_when_absent(self) -> None:
        """If Ketu is missing from planet_signs, ketu_sign is derived from Rahu+6."""
        # Rahu at sign 3 → Ketu derived as sign 9.
        chart = Chart(
            asc_sign=1,
            asc_lon=0.0,
            planet_signs={
                "Sun": 1, "Moon": 2, "Mars": 3, "Mercury": 4,
                "Jupiter": 5, "Venus": 6, "Saturn": 7,
                "Rahu": 3,
                # Ketu deliberately omitted from planet_signs
            },
            planet_houses={
                "Sun": 1, "Moon": 2, "Mars": 3, "Mercury": 4,
                "Jupiter": 5, "Venus": 6, "Saturn": 7,
                "Rahu": 3, "Ketu": 9,
            },
            planet_lons={
                "Sun": 15.0, "Moon": 45.0, "Mars": 75.0, "Mercury": 105.0,
                "Jupiter": 135.0, "Venus": 155.0, "Saturn": 175.0,
                "Rahu": 65.0, "Ketu": 245.0,
            },
        )
        result = detect_kalasarpa(chart)
        # Derived: ((3 + 6 - 1) % 12) + 1 = (8 % 12) + 1 = 9
        assert result.ketu_sign == 9
