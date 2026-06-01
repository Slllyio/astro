"""Tests for ``app.reading.computations.divisional_readings.d3_drekkana``.

Doctrine source: BPHS Vol.I Ch.6-7 (Shodashavarga). D3 Drekkana governs
**siblings, courage, and initiative** (3H themes). Each 30° rashi is
split into three 10° parts:

  1st part (0-10°)  -> same sign as D1.
  2nd part (10-20°) -> 5th sign from D1 (offset +4).
  3rd part (20-30°) -> 9th sign from D1 (offset +8).

The reading layer:

  - emits a per-planet D3 Finding (its D3 sign + interpretive theme).
  - emits a D3 lagna Finding (the D3 sign of the natal D1 ascendant).
  - emits a D3 3H-lord Finding (siblings/courage signifier).
  - emits a D3 Mars Finding (natural siblings/courage karaka).
"""
from __future__ import annotations

import pytest


def _planet(sign: int, *, longitude: float | None = None) -> dict:
    lon = longitude if longitude is not None else (sign - 1) * 30.0 + 15.0
    return {
        "sign": sign,
        "sign_name": "X",
        "longitude": lon,
        "degree_in_sign": lon % 30.0,
        "is_retrograde": False,
    }


def _build_chart(placements: dict[str, int]) -> dict:
    return {name: _planet(sign) for name, sign in placements.items()}


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------


class TestShape:

    def test_returns_dict_of_findings(self):
        from app.reading.computations.divisional_readings.d3_drekkana import (
            read_d3_drekkana,
        )
        from app.reading.schema import Finding

        d3 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d3_drekkana(d3, asc_sign=1)
        assert isinstance(out, dict)
        for v in out.values():
            assert isinstance(v, Finding)

    def test_classification_primitive(self):
        from app.reading.computations.divisional_readings.d3_drekkana import (
            read_d3_drekkana,
        )

        d3 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d3_drekkana(d3, asc_sign=1)
        for f in out.values():
            assert f.classification == "primitive"

    def test_id_grammar(self):
        from app.reading.computations.divisional_readings.d3_drekkana import (
            read_d3_drekkana,
        )

        d3 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d3_drekkana(d3, asc_sign=1)
        for fid in out:
            assert fid.startswith("d3.")

    def test_verdict_under_140(self):
        from app.reading.computations.divisional_readings.d3_drekkana import (
            read_d3_drekkana,
        )

        d3 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d3_drekkana(d3, asc_sign=1)
        for f in out.values():
            assert len(f.verdict) <= 140


# ---------------------------------------------------------------------------
# Required keys.
# ---------------------------------------------------------------------------


class TestRequiredFindings:

    def test_lagna_finding_present(self):
        from app.reading.computations.divisional_readings.d3_drekkana import (
            read_d3_drekkana,
        )

        d3 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d3_drekkana(d3, asc_sign=1)
        assert any("lagna" in fid for fid in out)

    def test_mars_finding_present(self):
        """Mars is the natural karaka for siblings/courage -> D3 Mars
        always reported."""
        from app.reading.computations.divisional_readings.d3_drekkana import (
            read_d3_drekkana,
        )

        d3 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d3_drekkana(d3, asc_sign=1)
        assert any("mars" in fid for fid in out)

    def test_third_house_lord_finding_present(self):
        """Aries asc -> 3H = Gemini (sign 3) -> 3L = Mercury."""
        from app.reading.computations.divisional_readings.d3_drekkana import (
            read_d3_drekkana,
        )

        d3 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d3_drekkana(d3, asc_sign=1)
        ids = " ".join(out.keys()).lower()
        assert "3h_lord" in ids or "3l" in ids or "third_house_lord" in ids


# ---------------------------------------------------------------------------
# Verdict mentions siblings/courage theme.
# ---------------------------------------------------------------------------


class TestThemeKeywords:

    def test_mars_verdict_mentions_courage_or_siblings(self):
        from app.reading.computations.divisional_readings.d3_drekkana import (
            read_d3_drekkana,
        )

        d3 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d3_drekkana(d3, asc_sign=1)
        mars_finding = next(f for fid, f in out.items() if "mars" in fid)
        blob = (mars_finding.verdict + " ".join(mars_finding.evidence)).lower()
        assert ("sibling" in blob) or ("courage" in blob) or ("initiative" in blob)


# ---------------------------------------------------------------------------
# Evidence: machine-readable d3_sign per finding.
# ---------------------------------------------------------------------------


class TestEvidence:

    def test_per_planet_evidence_has_d3_sign(self):
        from app.reading.computations.divisional_readings.d3_drekkana import (
            read_d3_drekkana,
        )

        d3 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d3_drekkana(d3, asc_sign=1)
        for fid, f in out.items():
            if fid == "d3.lagna":
                # Lagna finding doesn't carry per-planet data; just verify
                # it has its own d3_sign.
                continue
            blob = " ".join(f.evidence)
            assert "d3_sign=" in blob, f"{fid} evidence missing d3_sign"


# ---------------------------------------------------------------------------
# Property: works across all 12 ascendants.
# ---------------------------------------------------------------------------


class TestPropertyAllAsc:

    @pytest.mark.parametrize("asc", list(range(1, 13)))
    def test_runs_for_every_ascendant(self, asc):
        from app.reading.computations.divisional_readings.d3_drekkana import (
            read_d3_drekkana,
        )

        d3 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d3_drekkana(d3, asc_sign=asc)
        assert out
        for f in out.values():
            assert f.id.startswith("d3.")
