"""Named-drekkana classification — cells pinned to Raman's own degree-derived instances."""
from __future__ import annotations

import dataclasses

import pytest

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives import drekkana


def _chart_with(planet: str, lon: float) -> RamanChart:
    return RamanChart.from_stated_positions(
        {planet: {"lon": lon, "bhava": 1}, "Sun": {"lon": 200.0, "bhava": 4}},
        asc_lon=65.0, ayanamsa="raman")


class TestDrekkanaIndex:
    def test_ten_degree_bands_with_floor_division(self):
        """0-10 -> 1st, 10-20 -> 2nd, 20-30 -> 3rd; exact 10.0 belongs to the SECOND band
        (floor division, the project's cusp convention)."""
        assert drekkana.drekkana_index(0.0) == 1
        assert drekkana.drekkana_index(9.99) == 1
        assert drekkana.drekkana_index(10.0) == 2
        assert drekkana.drekkana_index(19.99) == 2
        assert drekkana.drekkana_index(20.0) == 3

    def test_longitude_reduces_within_sign(self):
        """The band is read from the degree WITHIN the sign, not the absolute longitude."""
        assert drekkana.drekkana_index(155.0) == 1   # Virgo 5deg
        assert drekkana.drekkana_index(165.0) == 2   # Virgo 15deg
        assert drekkana.drekkana_index(295.0) == 3   # Capricorn 25deg


class TestWorkedChartCells:
    """Each cell here was derived by Raman himself from a printed longitude."""

    def test_godse_saturn_aries_9_is_ayudha(self):
        """Godse: Saturn 9deg04' Aries -> Aries-1, 'Saturn lord of the 8th occupying Ayudha
        Drekkana' (NH:14641/14735) — the hanging-manner citation."""
        chart = _chart_with("Saturn", 9.07)
        assert "ayudha" in drekkana.planet_drekkana_classes("Saturn", chart)

    def test_marie_antoinette_saturn_capricorn_4_is_nigala(self):
        """Marie Antoinette: Saturn 4deg Capricorn -> Cap-1, 'Ayushkaraka is also in a Nigala
        Drekkana' (NH:5944-5947) — the best-attested cell in the table."""
        chart = _chart_with("Saturn", 274.0)
        assert "nigala" in drekkana.planet_drekkana_classes("Saturn", chart)

    def test_lincoln_virgo_second_is_ayudha(self):
        """Lincoln: 'The 22nd Drekkana is an Ayudha Drekkana, being the 2nd of Virgo'
        (HTJAH-II:6752-6753)."""
        chart = _chart_with("Mars", 164.0)   # Virgo 14deg -> 2nd drekkana (off the sentinel)
        assert "ayudha" in drekkana.planet_drekkana_classes("Mars", chart)

    def test_scorpio_second_is_dual_tagged_pasa_and_nigala(self):
        """The recorded conflict: PASA per the printed table/Phaladeepika, NIGADA per Raman's
        worked charts 66/67 — dual-tagged, and both sit inside the captivity triad. Scorpio
        17deg avoids the 15.0 midpoint sentinel."""
        chart = _chart_with("Mars", 227.0)   # Scorpio 17deg -> 2nd drekkana
        classes = drekkana.planet_drekkana_classes("Mars", chart)
        assert classes == frozenset({"pasa", "nigala"})
        assert classes <= drekkana.CAPTIVITY_TRIAD

    def test_tantris_ketu_anomaly_is_not_encoded(self):
        """Pisces-1 is NOT Sarpa: no table in the library supports Raman's one-off 'Ketu ...
        occupying a Sarpa Drekkana' at Pisces 3deg43 (NH:11492) — anomaly recorded, cell
        deliberately absent."""
        chart = _chart_with("Ketu", 333.72)  # Pisces 3deg43
        assert drekkana.planet_drekkana_classes("Ketu", chart) == frozenset()


class TestMidpointSentinel:
    def test_sign_midpoint_means_degree_unknown(self):
        """A Track-B record without a printed degree materializes at exactly 15.0 within the
        sign; a named drekkana must never be manufactured from that absence of knowledge."""
        chart = _chart_with("Saturn", 225.0)  # Scorpio 15.0 = the midpoint sentinel...
        # 225.0 % 30 == 15.0 -> None, NOT the Scorpio-2 classes.
        assert drekkana.planet_drekkana_classes("Saturn", chart) is None

    def test_absent_planet_is_none(self):
        chart = _chart_with("Mars", 164.0)
        assert drekkana.planet_drekkana_classes("Venus", chart) is None
