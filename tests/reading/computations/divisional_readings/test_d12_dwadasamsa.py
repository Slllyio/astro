"""Tests for ``app.reading.computations.divisional_readings.d12_dwadasamsa``.

Doctrine source: BPHS Vol.I Ch.6-7 (Shodashavarga). D12 Dwadasamsa
governs **parents, heritage, and ancestry**. Each 30° rashi is split
into 12 × 2.5° parts, starting from the same sign and cycling through
the zodiac.

The reading layer emits:

  - the D12 Lagna anchor (parents/heritage frame).
  - a per-planet D12 placement Finding.
  - a D12 4H-lord Finding (4H = home/parents in BPHS).
  - a D12 Sun Finding (natural karaka of father).
  - a D12 Moon Finding (natural karaka of mother).
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
        from app.reading.computations.divisional_readings.d12_dwadasamsa import (
            read_d12_dwadasamsa,
        )
        from app.reading.schema import Finding

        d12 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d12_dwadasamsa(d12, asc_sign=1)
        assert isinstance(out, dict)
        for v in out.values():
            assert isinstance(v, Finding)

    def test_classification_primitive(self):
        from app.reading.computations.divisional_readings.d12_dwadasamsa import (
            read_d12_dwadasamsa,
        )

        d12 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d12_dwadasamsa(d12, asc_sign=1)
        for f in out.values():
            assert f.classification == "primitive"

    def test_id_grammar(self):
        from app.reading.computations.divisional_readings.d12_dwadasamsa import (
            read_d12_dwadasamsa,
        )

        d12 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d12_dwadasamsa(d12, asc_sign=1)
        for fid in out:
            assert fid.startswith("d12.")

    def test_verdict_under_140(self):
        from app.reading.computations.divisional_readings.d12_dwadasamsa import (
            read_d12_dwadasamsa,
        )

        d12 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d12_dwadasamsa(d12, asc_sign=1)
        for f in out.values():
            assert len(f.verdict) <= 140


# ---------------------------------------------------------------------------
# Required findings.
# ---------------------------------------------------------------------------


class TestRequiredFindings:

    def test_lagna_finding_present(self):
        from app.reading.computations.divisional_readings.d12_dwadasamsa import (
            read_d12_dwadasamsa,
        )

        d12 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d12_dwadasamsa(d12, asc_sign=1)
        assert "d12.lagna" in out

    def test_sun_father_finding(self):
        from app.reading.computations.divisional_readings.d12_dwadasamsa import (
            read_d12_dwadasamsa,
        )

        d12 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d12_dwadasamsa(d12, asc_sign=1)
        assert any("sun" in fid for fid in out)

    def test_moon_mother_finding(self):
        from app.reading.computations.divisional_readings.d12_dwadasamsa import (
            read_d12_dwadasamsa,
        )

        d12 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d12_dwadasamsa(d12, asc_sign=1)
        assert any("moon" in fid for fid in out)

    def test_fourth_house_lord_finding(self):
        """Aries asc -> 4H = Cancer -> 4L = Moon."""
        from app.reading.computations.divisional_readings.d12_dwadasamsa import (
            read_d12_dwadasamsa,
        )

        d12 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d12_dwadasamsa(d12, asc_sign=1)
        ids = " ".join(out.keys()).lower()
        assert ("4h_lord" in ids) or ("4l" in ids) or ("fourth_house_lord" in ids)


# ---------------------------------------------------------------------------
# Verdict mentions parental theme.
# ---------------------------------------------------------------------------


class TestParentalTheme:

    def test_sun_verdict_mentions_father(self):
        from app.reading.computations.divisional_readings.d12_dwadasamsa import (
            read_d12_dwadasamsa,
        )

        d12 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d12_dwadasamsa(d12, asc_sign=1)
        sun_finding = next(f for fid, f in out.items() if "sun" in fid)
        blob = (sun_finding.verdict + " ".join(sun_finding.evidence)).lower()
        assert "father" in blob

    def test_moon_verdict_mentions_mother(self):
        from app.reading.computations.divisional_readings.d12_dwadasamsa import (
            read_d12_dwadasamsa,
        )

        d12 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d12_dwadasamsa(d12, asc_sign=1)
        moon_finding = next(f for fid, f in out.items() if "moon" in fid)
        blob = (moon_finding.verdict + " ".join(moon_finding.evidence)).lower()
        assert "mother" in blob


# ---------------------------------------------------------------------------
# Property: all 12 ascendants.
# ---------------------------------------------------------------------------


class TestPropertyAllAsc:

    @pytest.mark.parametrize("asc", list(range(1, 13)))
    def test_runs_for_every_ascendant(self, asc):
        from app.reading.computations.divisional_readings.d12_dwadasamsa import (
            read_d12_dwadasamsa,
        )

        d12 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d12_dwadasamsa(d12, asc_sign=asc)
        assert out
        for f in out.values():
            assert f.id.startswith("d12.")
