"""Tests for ``app.reading.computations.divisional_readings.d7_saptamsa``.

Doctrine source: BPHS Vol.I Ch.6-7 (Shodashavarga). D7 is the
**Saptamsa** chart and governs **children / progeny** (santana). Each
30° rashi is split into 7 × 4.286° parts; odd signs start counting from
the same sign, even signs start counting from the 7th sign from D1.

The reading layer interprets the D7 chart for progeny themes:

  - **D7 Lagna** (overall children frame).
  - **D7 5H lord** (children house lord; primary signifier).
  - **D7 Jupiter** (natural Putra-karaka of progeny).
  - **D7 <planet>** placements per natural significator set.

Construction lives in ``app.core.shodashavarga._saptamsa_d7``; this
module *reads* the finished D7 chart.
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
        from app.reading.computations.divisional_readings.d7_saptamsa import (
            read_d7_saptamsa,
        )
        from app.reading.schema import Finding

        d7 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d7_saptamsa(d7, asc_sign=1)
        assert isinstance(out, dict)
        assert out  # non-empty
        for v in out.values():
            assert isinstance(v, Finding)

    def test_id_grammar(self):
        from app.reading.computations.divisional_readings.d7_saptamsa import (
            read_d7_saptamsa,
        )

        d7 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d7_saptamsa(d7, asc_sign=1)
        for fid in out:
            assert fid.startswith("d7.")

    def test_classification_primitive(self):
        from app.reading.computations.divisional_readings.d7_saptamsa import (
            read_d7_saptamsa,
        )

        d7 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d7_saptamsa(d7, asc_sign=1)
        for f in out.values():
            assert f.classification == "primitive"

    def test_verdict_under_140(self):
        from app.reading.computations.divisional_readings.d7_saptamsa import (
            read_d7_saptamsa,
        )

        d7 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d7_saptamsa(d7, asc_sign=1)
        for f in out.values():
            assert len(f.verdict) <= 140


# ---------------------------------------------------------------------------
# Required findings
# ---------------------------------------------------------------------------


class TestRequiredFindings:

    def test_lagna_finding_present(self):
        from app.reading.computations.divisional_readings.d7_saptamsa import (
            read_d7_saptamsa,
        )

        d7 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d7_saptamsa(d7, asc_sign=1)
        assert "d7.lagna" in out

    def test_jupiter_putrakaraka_finding(self):
        """Jupiter is the natural Putra-karaka; a per-planet Finding must emit."""
        from app.reading.computations.divisional_readings.d7_saptamsa import (
            read_d7_saptamsa,
        )

        d7 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d7_saptamsa(d7, asc_sign=1)
        assert any("jupiter" in fid for fid in out)

    def test_fifth_house_lord_finding(self):
        """Aries asc -> 5H = Leo -> 5L = Sun (present in chart)."""
        from app.reading.computations.divisional_readings.d7_saptamsa import (
            read_d7_saptamsa,
        )

        d7 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d7_saptamsa(d7, asc_sign=1)
        ids = " ".join(out.keys()).lower()
        assert "5h_lord" in ids or "fifth_house_lord" in ids


# ---------------------------------------------------------------------------
# Children domain theme phrasing
# ---------------------------------------------------------------------------


class TestProgenyTheme:

    def test_jupiter_evidence_mentions_progeny_or_children(self):
        from app.reading.computations.divisional_readings.d7_saptamsa import (
            read_d7_saptamsa,
        )

        d7 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d7_saptamsa(d7, asc_sign=1)
        jup = next(f for fid, f in out.items() if "jupiter" in fid)
        blob = (jup.verdict + " " + " ".join(jup.evidence)).lower()
        assert "children" in blob or "progeny" in blob or "putra" in blob

    def test_lagna_verdict_mentions_children_frame(self):
        from app.reading.computations.divisional_readings.d7_saptamsa import (
            read_d7_saptamsa,
        )

        d7 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d7_saptamsa(d7, asc_sign=1)
        lagna = out["d7.lagna"]
        blob = (lagna.verdict + " " + " ".join(lagna.evidence)).lower()
        assert "children" in blob or "progeny" in blob or "putra" in blob


# ---------------------------------------------------------------------------
# Doctrine sentinel in every Finding's evidence
# ---------------------------------------------------------------------------


class TestDoctrineSentinel:

    def test_every_finding_evidence_carries_doctrine_sentinel(self):
        from app.reading.computations.divisional_readings.d7_saptamsa import (
            read_d7_saptamsa,
        )

        d7 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d7_saptamsa(d7, asc_sign=1)
        for fid, f in out.items():
            blob = " ".join(f.evidence)
            assert "doctrine=" in blob, f"{fid} missing doctrine sentinel"


# ---------------------------------------------------------------------------
# Evidence shape: machine-readable d7 sign
# ---------------------------------------------------------------------------


class TestEvidence:

    def test_per_planet_evidence_has_d7_sign(self):
        from app.reading.computations.divisional_readings.d7_saptamsa import (
            read_d7_saptamsa,
        )

        d7 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d7_saptamsa(d7, asc_sign=1)
        for fid, f in out.items():
            if fid == "d7.lagna":
                continue
            blob = " ".join(f.evidence)
            assert "d7_sign=" in blob, f"{fid} evidence missing d7_sign"


# ---------------------------------------------------------------------------
# Property: all 12 ascendants
# ---------------------------------------------------------------------------


class TestPropertyAllAsc:

    @pytest.mark.parametrize("asc", list(range(1, 13)))
    def test_runs_for_every_ascendant(self, asc):
        from app.reading.computations.divisional_readings.d7_saptamsa import (
            read_d7_saptamsa,
        )

        d7 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d7_saptamsa(d7, asc_sign=asc)
        assert out
        for f in out.values():
            assert f.id.startswith("d7.")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidation:

    def test_rejects_bad_asc_sign(self):
        from app.reading.computations.divisional_readings.d7_saptamsa import (
            read_d7_saptamsa,
        )

        d7 = _build_chart({"Jupiter": 9})
        with pytest.raises(ValueError):
            read_d7_saptamsa(d7, asc_sign=0)
        with pytest.raises(ValueError):
            read_d7_saptamsa(d7, asc_sign=13)
