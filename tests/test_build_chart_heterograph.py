"""Tests for app/medini/etl/build_chart_heterograph.py.

Pins BPHS-faithful edge construction:
- 12 fixed rulership edges per BPHS Ch.3
- Karaka assignments per BPHS Ch.34
- Drishti rules per BPHS Ch.26 + project locked decisions
- Dispositor closes the rulership loop on each chart's signs
- Per-chart edge count matches the deterministic formula (~46)
"""
from __future__ import annotations

import pandas as pd
import pytest

from app.medini.etl.build_chart_heterograph import (
    _GRAHA_TO_IDX,
    _SIGN_RULERSHIP,
    _KARAKAS,
    build_chart_edges,
    build_static_edges,
    edges_for_chart,
)

# Synthetic Bangalore-baseline chart row (1990-07-15 12:00 IST).
# CLAUDE.md pins: Virgo Lagna (asc_sign=6), Moon at Revati nakshatra=26.
_BANGALORE_CHART = {
    "person_id": "TEST:bangalore",
    "asc_lon": 173.99,
    "asc_sign": 6,
    "sun_lon": 88.8,   "sun_sign": 3,    "sun_house": 10, "sun_nakshatra": 6,
    "moon_lon": 356.3, "moon_sign": 12,  "moon_house": 7, "moon_nakshatra": 26,
    "mars_lon": 90.0,  "mars_sign": 4,   "mars_house": 11, "mars_nakshatra": 7,
    "mercury_lon": 75.0, "mercury_sign": 3, "mercury_house": 10, "mercury_nakshatra": 5,
    "jupiter_lon": 120.0, "jupiter_sign": 5, "jupiter_house": 12, "jupiter_nakshatra": 8,
    "venus_lon": 75.0, "venus_sign": 3, "venus_house": 10, "venus_nakshatra": 5,
    "saturn_lon": 290.0, "saturn_sign": 10, "saturn_house": 5, "saturn_nakshatra": 21,
    "rahu_lon": 110.0, "rahu_sign": 4, "rahu_house": 11, "rahu_nakshatra": 7,
    "ketu_lon": 290.0, "ketu_sign": 10, "ketu_house": 5, "ketu_nakshatra": 21,
}


class TestStaticEdges:
    """Edges that do not depend on a specific chart."""

    def test_twelve_rules_edges(self):
        """Exactly 12 Graha->Rasi rulership edges (one per sign)."""
        static = build_static_edges()
        rules = static[static["edge_type"] == "rules"]
        assert len(rules) == 12

    def test_aries_ruled_by_mars(self):
        """BPHS Ch.3: Aries (sign 0) is ruled by Mars."""
        static = build_static_edges()
        aries = static[(static["edge_type"] == "rules") & (static["dst_idx"] == 0)]
        assert aries.iloc[0]["attr_label"] == "Mars"
        assert aries.iloc[0]["src_idx"] == _GRAHA_TO_IDX["Mars"]

    def test_mars_rules_two_signs(self):
        """Mars rules both Aries (0) and Scorpio (7)."""
        static = build_static_edges()
        mars_rules = static[
            (static["edge_type"] == "rules") & (static["src_idx"] == _GRAHA_TO_IDX["Mars"])
        ]
        assert sorted(mars_rules["dst_idx"].tolist()) == [0, 7]

    def test_marriage_karakas_are_venus_and_jupiter(self):
        """BPHS Ch.34 + Phaladeepika: Venus + Jupiter karakas for marriage."""
        static = build_static_edges()
        marriage = static[
            (static["edge_type"] == "karaka_for") & (static["attr_label"] == "marriage")
        ]
        karakas = sorted(marriage["src_idx"].map(
            {v: k for k, v in _GRAHA_TO_IDX.items()}
        ).tolist())
        assert karakas == ["Jupiter", "Venus"]

    def test_career_karakas(self):
        """Career karakas: Sun (authority) + Saturn (work) + Mercury (skill)."""
        static = build_static_edges()
        career = static[
            (static["edge_type"] == "karaka_for") & (static["attr_label"] == "career")
        ]
        karakas = sorted(career["src_idx"].map(
            {v: k for k, v in _GRAHA_TO_IDX.items()}
        ).tolist())
        assert karakas == ["Mercury", "Saturn", "Sun"]


class TestPerChartEdges:
    """Per-chart edges respect BPHS rules and the chart's specific placements."""

    def test_edge_count_per_chart(self):
        """46 edges per chart: 9 occupies + 19 drishti + 9 dispositor + 9 nakshatra.

        Drishti breakdown (from _DRISHTI_HOUSES): Sun 1, Moon 1, Mars 3,
        Mercury 1, Jupiter 3, Venus 1, Saturn 3, Rahu 3, Ketu 3 = 19.
        """
        edges = edges_for_chart(_BANGALORE_CHART)
        assert len(edges) == 46

    def test_occupies_count(self):
        """Each of the 9 grahas has exactly one occupies edge."""
        edges = edges_for_chart(_BANGALORE_CHART)
        occ = [e for e in edges if e["edge_type"] == "occupies"]
        assert len(occ) == 9

    def test_drishti_mars_has_three_targets(self):
        """Mars aspects 4th, 7th, 8th from itself (BPHS Ch.26)."""
        edges = edges_for_chart(_BANGALORE_CHART)
        mars_drishti = [
            e for e in edges
            if e["edge_type"] == "drishti" and e["src_idx"] == _GRAHA_TO_IDX["Mars"]
        ]
        distances = sorted([e["attr_value"] for e in mars_drishti])
        assert distances == [4.0, 7.0, 8.0]

    def test_drishti_sun_has_only_seventh_aspect(self):
        """Sun, Moon, Mercury, Venus aspect only the 7th house (no special drishti)."""
        edges = edges_for_chart(_BANGALORE_CHART)
        sun_drishti = [
            e for e in edges
            if e["edge_type"] == "drishti" and e["src_idx"] == _GRAHA_TO_IDX["Sun"]
        ]
        assert len(sun_drishti) == 1
        assert sun_drishti[0]["attr_value"] == 7.0

    def test_drishti_rahu_ketu_jupiter_style(self):
        """Project locked decision (CLAUDE.md): Rahu/Ketu use Jupiter-style 5/7/9.

        Not BV Raman (no nodal drishti), not KP. Sukra Nadi tradition.
        """
        edges = edges_for_chart(_BANGALORE_CHART)
        for node in ("Rahu", "Ketu"):
            nodal_drishti = [
                e for e in edges
                if e["edge_type"] == "drishti" and e["src_idx"] == _GRAHA_TO_IDX[node]
            ]
            distances = sorted([e["attr_value"] for e in nodal_drishti])
            assert distances == [5.0, 7.0, 9.0]

    def test_drishti_target_house_computation(self):
        """Mars in house 11 aspects houses (11+4-1)%12+1=2, (11+7-1)%12+1=5, (11+8-1)%12+1=6."""
        edges = edges_for_chart(_BANGALORE_CHART)
        mars_drishti = [
            (e["dst_idx"], e["attr_value"]) for e in edges
            if e["edge_type"] == "drishti" and e["src_idx"] == _GRAHA_TO_IDX["Mars"]
        ]
        # Mars house=11; targets: 2, 5, 6 (0-indexed: 1, 4, 5).
        target_houses_0idx = sorted([t[0] for t in mars_drishti])
        assert target_houses_0idx == [1, 4, 5]


class TestDispositorClosure:
    """Dispositor edges close the rulership loop on chart-specific signs."""

    def test_sun_in_gemini_dispositor_is_mercury(self):
        """Sun in Gemini (sign 3): Gemini's lord is Mercury -> Mercury disposits Sun."""
        edges = edges_for_chart(_BANGALORE_CHART)
        sun_disp = [
            e for e in edges
            if e["edge_type"] == "dispositor_of"
            and e["dst_idx"] == _GRAHA_TO_IDX["Sun"]
        ][0]
        assert sun_disp["src_idx"] == _GRAHA_TO_IDX["Mercury"]

    def test_dispositor_edges_count(self):
        """Exactly 9 dispositor edges (one per graha)."""
        edges = edges_for_chart(_BANGALORE_CHART)
        disp = [e for e in edges if e["edge_type"] == "dispositor_of"]
        assert len(disp) == 9


class TestNakshatraEdges:
    """Each graha has exactly one Nakshatra edge."""

    def test_moon_in_revati(self):
        """Per CLAUDE.md: Bangalore baseline Moon at Revati (nakshatra index 26)."""
        edges = edges_for_chart(_BANGALORE_CHART)
        moon_nak = [
            e for e in edges
            if e["edge_type"] == "nakshatra_of" and e["src_idx"] == _GRAHA_TO_IDX["Moon"]
        ][0]
        assert moon_nak["dst_idx"] == 26

    def test_nakshatra_edges_count(self):
        """One per graha = 9 nakshatra edges per chart."""
        edges = edges_for_chart(_BANGALORE_CHART)
        nak = [e for e in edges if e["edge_type"] == "nakshatra_of"]
        assert len(nak) == 9


class TestBatchBuild:
    """build_chart_edges yields one row per (chart, edge) pair."""

    def test_two_charts_produce_double_edges(self):
        """Two identical chart rows -> 2x46 = 92 edges total."""
        charts = pd.DataFrame([_BANGALORE_CHART, {**_BANGALORE_CHART, "person_id": "TEST:b2"}])
        result = build_chart_edges(charts)
        assert len(result) == 92

    def test_required_columns_present(self):
        """Schema contract for downstream consumers (R-GCN, etc.)."""
        charts = pd.DataFrame([_BANGALORE_CHART])
        result = build_chart_edges(charts)
        required = {"person_id", "edge_type", "src_type", "src_idx",
                    "dst_type", "dst_idx", "attr_value"}
        assert required.issubset(set(result.columns))
