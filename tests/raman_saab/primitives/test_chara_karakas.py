"""Chara karakas — `primitives/chara_karakas.py`.

Pins the strict 7-karaka Jaimini ranking on Track-B synthetic charts (no swisseph): the seven
visible planets ranked by degree-within-sign descending, AK identical to the locked
`special_points.atmakaraka`, nodes never assigned, deterministic ties, and None-safe sparsity.
Each test states the divisional-astronomy fact it checks (degree-in-sign = `lon % 30`).
"""
from __future__ import annotations

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.primitives import special_points
from app.raman_saab.primitives.chara_karakas import (
    chara_karakas, karaka_planet, role_name)


def _chart(planets: dict[str, float], asc_lon: float = 5.0) -> RamanChart:
    """Track-B chart from explicit sidereal longitudes; degree-in-sign = lon % 30."""
    stated = {n: {"lon": lo, "bhava": 1} for n, lo in planets.items()}
    return RamanChart.from_stated_positions(stated, asc_lon=asc_lon, ayanamsa="raman")


# Seven distinct degrees-in-sign, one planet each, so the rank order is unambiguous.
_SEVEN_CHART = {
    "Jupiter": 29.0,   # Aries 29  -> deg 29 -> AK
    "Saturn": 55.0,    # Taurus 25 -> deg 25 -> AmK
    "Venus": 80.0,     # Gemini 20 -> deg 20 -> BK
    "Mercury": 105.0,  # Cancer 15 -> deg 15 -> MK
    "Mars": 130.0,     # Leo 10    -> deg 10 -> PK
    "Moon": 155.0,     # Virgo 5   -> deg 5  -> GK
    "Sun": 182.0,      # Libra 2   -> deg 2  -> DK
}


class TestCharaKarakas:
    def test_full_seven_karaka_ranking(self) -> None:
        """Seven planets at descending degrees-in-sign map to AK..DK in that exact order."""
        ck = chara_karakas(_chart(_SEVEN_CHART))
        assert ck == {"AK": "Jupiter", "AmK": "Saturn", "BK": "Venus", "MK": "Mercury",
                      "PK": "Mars", "GK": "Moon", "DK": "Sun"}

    def test_ak_matches_locked_atmakaraka(self) -> None:
        """AK is identical to special_points.atmakaraka by construction (same lon%30 keying)."""
        c = _chart(_SEVEN_CHART)
        assert karaka_planet(c, "AK") == special_points.atmakaraka(c)

    def test_nodes_are_never_assigned(self) -> None:
        """Rahu at a higher degree than any visible planet is still NOT the AK (chayagrahas are
        excluded; AK can never be a node)."""
        c = _chart({**_SEVEN_CHART, "Rahu": 29.9, "Ketu": 209.9})
        ck = chara_karakas(c)
        assert "Rahu" not in ck.values() and "Ketu" not in ck.values()
        assert ck["AK"] == "Jupiter"

    def test_degree_tie_breaks_deterministically_by_seven_order(self) -> None:
        """Two planets at the same degree-in-sign break by _SEVEN order: Sun (earlier) outranks
        Moon. Sun deg 10, Moon deg 10 -> Sun is the higher karaka."""
        c = _chart({"Sun": 10.0, "Moon": 40.0})   # both deg 10
        ck = chara_karakas(c)
        assert ck["AK"] == "Sun" and ck["AmK"] == "Moon"

    def test_sparse_chart_omits_unfilled_roles(self) -> None:
        """A chart with only three visible planets fills AK/AmK/BK; later roles are absent."""
        c = _chart({"Sun": 20.0, "Mars": 15.0, "Venus": 5.0})
        ck = chara_karakas(c)
        assert set(ck) == {"AK", "AmK", "BK"}
        assert karaka_planet(c, "DK") is None

    def test_role_name_is_human_readable(self) -> None:
        """Role codes resolve to their classical names."""
        assert role_name("AK").startswith("Atmakaraka")
        assert role_name("DK").startswith("Darakaraka")
