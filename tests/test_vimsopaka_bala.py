"""Tests for Vimsopaka Bala — Gap G."""
from __future__ import annotations

import pytest

from app.core.chart_model import Chart
from app.core.vimsopaka_bala import (
    VimsopakaReport, vimsopaka_bala, vimsopaka_for_chart,
)


class TestVimsopakaBala:
    def test_all_exalted_yields_max_20(self):
        """If a planet is exalted in EVERY varga in a scheme, composite = 20."""
        # Sun exalted in Aries (sign 1) across all D1-D60
        per_varga = {v: 1 for v in ["D1", "D2", "D3", "D7", "D9", "D12", "D30"]}
        r = vimsopaka_bala("Sun", per_varga, scheme="saptavargaja")
        assert abs(r.composite_rupas - 20.0) < 0.01
        assert r.strength_label == "STRONG"

    def test_all_debilitated_yields_low_score(self):
        """All debilitated → composite ≈ 2 (very weak)."""
        # Sun debilitated in Libra (sign 7) across all vargas
        per_varga = {v: 7 for v in ["D1", "D2", "D3", "D7", "D9", "D12", "D30"]}
        r = vimsopaka_bala("Sun", per_varga, scheme="saptavargaja")
        assert r.composite_rupas < 3.0
        assert r.strength_label == "VERY WEAK"

    def test_neutral_yields_10_rupas(self):
        """All neutral → composite = 10 (Average)."""
        # Sun in neutral signs (not 1, 5, or 7) — use 4 (Cancer)
        per_varga = {v: 4 for v in ["D1", "D2", "D3", "D7", "D9", "D12", "D30"]}
        r = vimsopaka_bala("Sun", per_varga, scheme="saptavargaja")
        assert abs(r.composite_rupas - 10.0) < 0.01
        assert r.strength_label == "AVERAGE"

    def test_mixed_dignity_yields_intermediate(self):
        """D1 exalted (weight 5) + D9 debilitated (weight 4.5) + others neutral
        → composite somewhere between 10 and 20."""
        # Sun exalt in D1 Aries, debilitated in D9 Libra, rest neutral Cancer
        per_varga = {"D1": 1, "D9": 7, "D2": 4, "D3": 4, "D7": 4, "D12": 4, "D30": 4}
        r = vimsopaka_bala("Sun", per_varga, scheme="saptavargaja")
        # Calculation: 20×(5/20) + 2×(4.5/20) + 10×((2+3+2.5+2+1)/20)
        # = 5 + 0.45 + 10*(10.5/20) = 5 + 0.45 + 5.25 = 10.7
        assert 9.0 <= r.composite_rupas <= 12.0

    def test_returns_per_varga_dignity_dict(self):
        """Result carries dignity values per varga for transparency."""
        per_varga = {"D1": 1, "D9": 1}  # exalted in both
        r = vimsopaka_bala("Sun", per_varga, scheme="saptavargaja")
        assert "D1" in r.per_varga_dignity
        assert "D9" in r.per_varga_dignity
        assert r.per_varga_dignity["D1"] == 20.0
        assert r.per_varga_dignity["D9"] == 20.0

    def test_rejects_invalid_scheme(self):
        with pytest.raises(ValueError):
            vimsopaka_bala("Sun", {"D1": 1}, scheme="bogus")

    def test_missing_varga_contributes_zero(self):
        """A varga absent from per_varga_sign contributes 0 dignity."""
        per_varga = {"D1": 1}  # only D1 — Sun exalted
        r = vimsopaka_bala("Sun", per_varga, scheme="saptavargaja")
        # 20 × (5/20) + 0 = 5
        assert abs(r.composite_rupas - 5.0) < 0.01


class TestSchemeWeightsSumTo20:
    def test_saptavargaja_weights_sum(self):
        """Saptavargaja weights sum to 20."""
        from app.core.vimsopaka_bala import _SAPTAVARGAJA_WEIGHTS
        assert abs(sum(_SAPTAVARGAJA_WEIGHTS.values()) - 20.0) < 0.01

    def test_dashavargaja_weights_sum(self):
        from app.core.vimsopaka_bala import _DASHAVARGAJA_WEIGHTS
        assert abs(sum(_DASHAVARGAJA_WEIGHTS.values()) - 20.0) < 0.01

    def test_shodashavargaja_weights_sum(self):
        from app.core.vimsopaka_bala import _SHODASHAVARGAJA_WEIGHTS
        assert abs(sum(_SHODASHAVARGAJA_WEIGHTS.values()) - 20.0) < 0.01


class TestVimsopakaForChart:
    def test_falls_back_to_d1_only_when_no_varga_data(self):
        """Without per_planet_varga_signs, computes D1-only Vimsopaka."""
        chart = Chart(
            asc_sign=6, asc_lon=173.99,
            planet_signs={"Sun": 1, "Moon": 4, "Mars": 10, "Mercury": 6,
                          "Jupiter": 4, "Venus": 7, "Saturn": 7,
                          "Rahu": 12, "Ketu": 6},
            planet_houses={p: 1 for p in ["Sun", "Moon", "Mars", "Mercury",
                                          "Jupiter", "Venus", "Saturn",
                                          "Rahu", "Ketu"]},
            planet_lons={"Sun": 10, "Moon": 100, "Mars": 280, "Mercury": 175,
                         "Jupiter": 95, "Venus": 195, "Saturn": 200,
                         "Rahu": 340, "Ketu": 160},
        )
        # Sun in Aries = exalted → D1 contribution = 20 * 5/20 = 5
        results = vimsopaka_for_chart(chart)
        assert results["Sun"].composite_rupas == 5.0  # D1-only with exalt

    def test_excludes_rahu_ketu(self):
        """Rahu and Ketu are excluded from Vimsopaka (no dignity table)."""
        chart = Chart(
            asc_sign=1, asc_lon=0.0,
            planet_signs={p: 1 for p in ["Sun", "Moon", "Mars", "Mercury",
                                          "Jupiter", "Venus", "Saturn",
                                          "Rahu", "Ketu"]},
            planet_houses={p: 1 for p in ["Sun", "Moon", "Mars", "Mercury",
                                           "Jupiter", "Venus", "Saturn",
                                           "Rahu", "Ketu"]},
            planet_lons={p: 5.0 for p in ["Sun", "Moon", "Mars", "Mercury",
                                           "Jupiter", "Venus", "Saturn",
                                           "Rahu", "Ketu"]},
        )
        results = vimsopaka_for_chart(chart)
        assert "Rahu" not in results
        assert "Ketu" not in results
        assert "Sun" in results
