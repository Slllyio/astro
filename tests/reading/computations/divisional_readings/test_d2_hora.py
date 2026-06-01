"""Tests for ``app.reading.computations.divisional_readings.d2_hora``.

Doctrine source: BPHS Vol.I Ch.6-7 (Shodashavarga). D2 is the Hora
chart: each 30° rashi is split into 2 × 15° halves; each half maps to
either Leo (the Sun's Hora) or Cancer (the Moon's Hora). Odd signs put
Sun's Hora first; even signs put Moon's Hora first.

The reading layer interprets each planet's D2 placement for wealth /
source-of-income themes:

  - **Moon's Hora (Cancer = sign 4)** → emotional / nurturing / domestic
    / fluid sources of income.
  - **Sun's Hora (Leo = sign 5)** → authoritative / public / self-made /
    structural sources of income.

The lagna lord's D2 Hora is the most informative single signal; the
module additionally surfaces a per-planet Finding for each member of the
seven natural significators (Sun, Moon, Mars, Mercury, Jupiter, Venus,
Saturn).
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


def _build_d2_chart(placements: dict[str, int]) -> dict:
    """Build a D2 chart where each planet sits in the specified D2 sign.

    The D2 chart only has TWO valid signs (4=Cancer and 5=Leo). The
    helper does not validate; callers can supply any sign for negative
    tests if needed.
    """
    return {name: _planet(sign) for name, sign in placements.items()}


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------


class TestShape:

    def test_returns_dict_of_findings(self):
        from app.reading.computations.divisional_readings.d2_hora import (
            read_d2_hora,
        )
        from app.reading.schema import Finding

        d2 = _build_d2_chart({
            "Sun": 5, "Moon": 4, "Mars": 5, "Mercury": 4,
            "Jupiter": 4, "Venus": 5, "Saturn": 5,
        })
        out = read_d2_hora(d2, asc_sign=1)
        assert isinstance(out, dict)
        assert out  # non-empty
        for v in out.values():
            assert isinstance(v, Finding)

    def test_id_grammar(self):
        from app.reading.computations.divisional_readings.d2_hora import (
            read_d2_hora,
        )

        d2 = _build_d2_chart({
            "Sun": 5, "Moon": 4, "Mars": 5, "Mercury": 4,
            "Jupiter": 4, "Venus": 5, "Saturn": 5,
        })
        out = read_d2_hora(d2, asc_sign=1)
        for fid in out:
            assert fid.startswith("d2.")

    def test_classification_is_primitive(self):
        from app.reading.computations.divisional_readings.d2_hora import (
            read_d2_hora,
        )

        d2 = _build_d2_chart({
            "Sun": 5, "Moon": 4, "Mars": 5, "Mercury": 4,
            "Jupiter": 4, "Venus": 5, "Saturn": 5,
        })
        out = read_d2_hora(d2, asc_sign=1)
        for f in out.values():
            assert f.classification == "primitive"

    def test_verdict_under_140(self):
        from app.reading.computations.divisional_readings.d2_hora import (
            read_d2_hora,
        )

        d2 = _build_d2_chart({
            "Sun": 5, "Moon": 4, "Mars": 5, "Mercury": 4,
            "Jupiter": 4, "Venus": 5, "Saturn": 5,
        })
        out = read_d2_hora(d2, asc_sign=1)
        for f in out.values():
            assert len(f.verdict) <= 140


# ---------------------------------------------------------------------------
# Per-planet Hora membership.
# ---------------------------------------------------------------------------


class TestHoraMembership:

    def test_jupiter_in_moon_hora_verdict_emotional(self):
        """Jupiter in Cancer (sign 4 = Moon's Hora) -> wealth via
        emotional/nurturing sources."""
        from app.reading.computations.divisional_readings.d2_hora import (
            read_d2_hora,
        )

        d2 = _build_d2_chart({
            "Sun": 5, "Moon": 4, "Mars": 5, "Mercury": 4,
            "Jupiter": 4, "Venus": 5, "Saturn": 5,
        })
        out = read_d2_hora(d2, asc_sign=1)
        jup_finding = next(
            f for fid, f in out.items() if "jupiter" in fid.lower()
        )
        verdict_lower = jup_finding.verdict.lower()
        assert "moon" in verdict_lower or "cancer" in verdict_lower

    def test_saturn_in_sun_hora_verdict_authoritative(self):
        from app.reading.computations.divisional_readings.d2_hora import (
            read_d2_hora,
        )

        d2 = _build_d2_chart({
            "Sun": 5, "Moon": 4, "Mars": 5, "Mercury": 4,
            "Jupiter": 4, "Venus": 5, "Saturn": 5,
        })
        out = read_d2_hora(d2, asc_sign=1)
        sat_finding = next(
            f for fid, f in out.items() if "saturn" in fid.lower()
        )
        verdict_lower = sat_finding.verdict.lower()
        assert "sun" in verdict_lower or "leo" in verdict_lower


# ---------------------------------------------------------------------------
# Lagna lord Hora.
# ---------------------------------------------------------------------------


class TestLagnaLordHora:

    def test_lagna_lord_finding_present(self):
        """For Aries asc, lagna lord is Mars."""
        from app.reading.computations.divisional_readings.d2_hora import (
            read_d2_hora,
        )

        d2 = _build_d2_chart({
            "Sun": 5, "Moon": 4, "Mars": 5, "Mercury": 4,
            "Jupiter": 4, "Venus": 5, "Saturn": 5,
        })
        out = read_d2_hora(d2, asc_sign=1)
        ids = list(out.keys())
        assert any("lagna_lord" in fid for fid in ids)

    def test_lagna_lord_verdict_names_planet(self):
        """Aries asc -> Mars is lagna lord -> verdict mentions Mars."""
        from app.reading.computations.divisional_readings.d2_hora import (
            read_d2_hora,
        )

        d2 = _build_d2_chart({
            "Sun": 5, "Moon": 4, "Mars": 5, "Mercury": 4,
            "Jupiter": 4, "Venus": 5, "Saturn": 5,
        })
        out = read_d2_hora(d2, asc_sign=1)
        ll_finding = next(
            f for fid, f in out.items() if "lagna_lord" in fid
        )
        assert "mars" in ll_finding.verdict.lower()


# ---------------------------------------------------------------------------
# Evidence carries machine-readable D2 sign.
# ---------------------------------------------------------------------------


class TestEvidence:

    def test_evidence_records_d2_sign(self):
        from app.reading.computations.divisional_readings.d2_hora import (
            read_d2_hora,
        )

        d2 = _build_d2_chart({
            "Sun": 5, "Moon": 4, "Mars": 5, "Mercury": 4,
            "Jupiter": 4, "Venus": 5, "Saturn": 5,
        })
        out = read_d2_hora(d2, asc_sign=1)
        jup = next(f for fid, f in out.items() if "jupiter" in fid.lower())
        blob = " ".join(jup.evidence)
        assert "d2_sign=" in blob


# ---------------------------------------------------------------------------
# Property: works across all 12 ascendants.
# ---------------------------------------------------------------------------


class TestPropertyAllAsc:

    @pytest.mark.parametrize("asc", list(range(1, 13)))
    def test_runs_for_every_ascendant(self, asc):
        from app.reading.computations.divisional_readings.d2_hora import (
            read_d2_hora,
        )

        d2 = _build_d2_chart({
            "Sun": 5, "Moon": 4, "Mars": 5, "Mercury": 4,
            "Jupiter": 4, "Venus": 5, "Saturn": 5,
        })
        out = read_d2_hora(d2, asc_sign=asc)
        assert out
        for f in out.values():
            assert f.id.startswith("d2.")
