"""Tests for app.core.chart_model — Chart dataclass invariants."""
from __future__ import annotations

import pytest

from app.core.chart_model import Chart


def _complete_chart() -> Chart:
    """Full 9-graha chart used as the positive-case fixture."""
    return Chart(
        asc_sign=1, asc_lon=0.0,
        planet_signs={p: 1 for p in ["Sun", "Moon", "Mars", "Mercury",
                                      "Jupiter", "Venus", "Saturn",
                                      "Rahu", "Ketu"]},
        planet_houses={p: 1 for p in ["Sun", "Moon", "Mars", "Mercury",
                                       "Jupiter", "Venus", "Saturn",
                                       "Rahu", "Ketu"]},
        planet_lons={p: 0.0 for p in ["Sun", "Moon", "Mars", "Mercury",
                                       "Jupiter", "Venus", "Saturn",
                                       "Rahu", "Ketu"]},
    )


class TestValidateComplete:
    """Audit-fix: fail-fast validator surfaces partial input."""

    def test_complete_chart_passes(self):
        """All 9 grahas present with sign/house/lon → no exception."""
        _complete_chart().validate_complete()

    def test_missing_planet_raises(self):
        """Sun absent → ValueError naming Sun.sign / Sun.house / Sun.lon."""
        chart = Chart(
            asc_sign=1, asc_lon=0.0,
            planet_signs={"Moon": 4},
            planet_houses={"Moon": 4},
            planet_lons={"Moon": 100.0},
        )
        with pytest.raises(ValueError) as exc:
            chart.validate_complete()
        assert "Sun" in str(exc.value)

    def test_missing_only_lon_raises(self):
        """Partial population (sign+house but no lon) still fails."""
        full = _complete_chart()
        partial = Chart(
            asc_sign=full.asc_sign, asc_lon=full.asc_lon,
            planet_signs=dict(full.planet_signs),
            planet_houses=dict(full.planet_houses),
            planet_lons={p: v for p, v in full.planet_lons.items() if p != "Sun"},
        )
        with pytest.raises(ValueError) as exc:
            partial.validate_complete()
        assert "Sun.lon" in str(exc.value)


class TestRetrogradeDefaults:
    """Audit-fix documented contract: retrograde defaults are implicit."""

    def test_from_dossier_row_defaults_nodes_retrograde(self):
        """Rahu/Ketu default to True when dossier has no retrograde col."""
        row = {
            "asc_sign": 1, "asc_lon": 0.0,
            **{f"{p}_lon": 0.0 for p in ["sun", "moon", "mars", "mercury",
                                          "jupiter", "venus", "saturn",
                                          "rahu", "ketu"]},
            **{f"{p}_sign": 1 for p in ["sun", "moon", "mars", "mercury",
                                         "jupiter", "venus", "saturn",
                                         "rahu", "ketu"]},
            **{f"{p}_natal_house": 1 for p in ["sun", "moon", "mars", "mercury",
                                                "jupiter", "venus", "saturn",
                                                "rahu", "ketu"]},
        }
        chart = Chart.from_dossier_row(row)
        assert chart.planet_retrograde["Rahu"] is True
        assert chart.planet_retrograde["Ketu"] is True
        assert chart.planet_retrograde["Sun"] is False
