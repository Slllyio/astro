"""Tests for app.core.shadbala_report — Phase 4 bridge layer."""
from __future__ import annotations

import pytest

from app.core.chart_model import Chart
from app.core.shadbala_report import (
    PlanetShadbala,
    ShadbalaReport,
    compute_planet_shadbala,
    compute_shadbala,
    is_sufficiently_strong,
)


@pytest.fixture
def baseline_chart() -> Chart:
    """Bangalore 1990-07-15 reduced fixture — Virgo Lagna baseline."""
    return Chart(
        asc_sign=6, asc_lon=173.99,
        planet_signs={"Sun": 3, "Moon": 12, "Mars": 4, "Mercury": 3,
                      "Jupiter": 4, "Venus": 4, "Saturn": 9},
        planet_houses={"Sun": 10, "Moon": 7, "Mars": 11, "Mercury": 10,
                       "Jupiter": 11, "Venus": 11, "Saturn": 4},
        planet_lons={"Sun": 88.6, "Moon": 351.0, "Mars": 120.5,
                     "Mercury": 95.2, "Jupiter": 101.8, "Venus": 102.0,
                     "Saturn": 268.4},
    )


class TestPlanetShadbala:
    """Per-planet computation behaviour."""

    def test_returns_planet_shadbala_record(self, baseline_chart):
        """Public type contract — frozen dataclass with named bala components."""
        result = compute_planet_shadbala("Sun", baseline_chart)
        assert isinstance(result, PlanetShadbala)
        assert result.planet == "Sun"

    def test_all_six_bala_components_present(self, baseline_chart):
        """Sthana + Dig + Kala + Cheshta + Naisargika + Drik."""
        result = compute_planet_shadbala("Jupiter", baseline_chart)
        for attr in ("sthana", "dig", "kala", "cheshta",
                     "naisargika", "drik"):
            assert hasattr(result, attr)
            assert isinstance(getattr(result, attr), float)

    def test_total_is_sum_of_components(self, baseline_chart):
        """Defence against double-counting: total = sum(parts)."""
        result = compute_planet_shadbala("Mars", baseline_chart)
        parts_sum = (result.sthana + result.dig + result.kala +
                     result.cheshta + result.naisargika + result.drik)
        assert result.total_virupa == pytest.approx(parts_sum, abs=0.5)

    def test_pinda_rupa_is_total_over_60(self, baseline_chart):
        """1 rupa = 60 virupa — well-known conversion."""
        result = compute_planet_shadbala("Saturn", baseline_chart)
        assert result.pinda_rupa == pytest.approx(result.total_virupa / 60.0)

    def test_is_sufficient_compares_to_threshold(self, baseline_chart):
        """Boolean tracks total ≥ threshold."""
        result = compute_planet_shadbala("Sun", baseline_chart)
        assert result.is_sufficient == (result.total_virupa >= result.threshold_virupa)

    def test_rejects_invisible_planets(self, baseline_chart):
        """Rahu/Ketu have no Shadbala in BPHS — rejected fail-fast."""
        with pytest.raises(ValueError):
            compute_planet_shadbala("Rahu", baseline_chart)


class TestComputeShadbala:
    """Whole-chart report behaviour."""

    def test_report_covers_all_7_visible_planets(self, baseline_chart):
        """Mapping has Sun..Saturn, no nodes."""
        r = compute_shadbala(baseline_chart)
        assert set(r.per_planet.keys()) == {
            "Sun", "Moon", "Mars", "Mercury",
            "Jupiter", "Venus", "Saturn",
        }

    def test_strongest_is_max_by_total(self, baseline_chart):
        """Strongest planet equals argmax(total_virupa)."""
        r = compute_shadbala(baseline_chart)
        assert r.strongest == max(
            r.per_planet, key=lambda p: r.per_planet[p].total_virupa,
        )

    def test_weakest_is_min_by_total(self, baseline_chart):
        """Weakest planet equals argmin(total_virupa)."""
        r = compute_shadbala(baseline_chart)
        assert r.weakest == min(
            r.per_planet, key=lambda p: r.per_planet[p].total_virupa,
        )

    def test_report_carries_caveat_notes(self, baseline_chart):
        """Notes flag missing Kala sub-components — Phase 6 will read this."""
        r = compute_shadbala(baseline_chart)
        assert any("Kala" in n for n in r.notes)

    def test_is_sufficiently_strong_matches_report(self, baseline_chart):
        """Convenience boolean matches the report's per-planet flag."""
        r = compute_shadbala(baseline_chart)
        for planet in r.per_planet:
            assert (
                is_sufficiently_strong(planet, baseline_chart)
                == r.per_planet[planet].is_sufficient
            )
