"""Tests for ``app.reading.computations.divisional_readings.d60_shashtiamsa``.

Doctrine source: BPHS Vol.I Ch.6-7 (Shodashavarga). Parashara calls
**D60 (Shashtiamsa) the most important divisional chart**; it carries
past-life karma signatures (sanchita karma). Each 30° rashi is split
into 60 × 0.5° parts; this makes D60 EXTREMELY birth-time-sensitive
(a 1-minute rectification error can shift D60 placements).

The reading layer emits:

  - **D60 Lagna** — the single most important point in D60 (past-life
    karmic anchor).
  - **D60 lagna lord** — its placement.
  - **D60 Atmakaraka** — the soul-karaka's D60 sign (Jaimini's most
    important signifier of past-life karma direction).
  - **D60 <planet>** — per-planet placement.

Every Finding's evidence must carry an explicit
``birth_time_sensitivity=very_high`` marker so consumers know not to
over-rely on D60 without rectified time.
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
        from app.reading.computations.divisional_readings.d60_shashtiamsa import (
            read_d60_shashtiamsa,
        )
        from app.reading.schema import Finding

        d60 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d60_shashtiamsa(d60, asc_sign=1, atmakaraka="Jupiter")
        assert isinstance(out, dict)
        assert out
        for v in out.values():
            assert isinstance(v, Finding)

    def test_id_grammar(self):
        from app.reading.computations.divisional_readings.d60_shashtiamsa import (
            read_d60_shashtiamsa,
        )

        d60 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d60_shashtiamsa(d60, asc_sign=1, atmakaraka="Jupiter")
        for fid in out:
            assert fid.startswith("d60.")

    def test_classification_primitive(self):
        from app.reading.computations.divisional_readings.d60_shashtiamsa import (
            read_d60_shashtiamsa,
        )

        d60 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d60_shashtiamsa(d60, asc_sign=1, atmakaraka="Jupiter")
        for f in out.values():
            assert f.classification == "primitive"

    def test_verdict_under_140(self):
        from app.reading.computations.divisional_readings.d60_shashtiamsa import (
            read_d60_shashtiamsa,
        )

        d60 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d60_shashtiamsa(d60, asc_sign=1, atmakaraka="Jupiter")
        for f in out.values():
            assert len(f.verdict) <= 140


# ---------------------------------------------------------------------------
# Required findings
# ---------------------------------------------------------------------------


class TestRequiredFindings:

    def test_lagna_present(self):
        from app.reading.computations.divisional_readings.d60_shashtiamsa import (
            read_d60_shashtiamsa,
        )

        d60 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d60_shashtiamsa(d60, asc_sign=1, atmakaraka="Jupiter")
        assert "d60.lagna" in out

    def test_lagna_lord_present(self):
        """Aries asc -> lagna lord Mars."""
        from app.reading.computations.divisional_readings.d60_shashtiamsa import (
            read_d60_shashtiamsa,
        )

        d60 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d60_shashtiamsa(d60, asc_sign=1, atmakaraka="Jupiter")
        ids = " ".join(out.keys()).lower()
        assert "lagna_lord" in ids

    def test_atmakaraka_finding(self):
        from app.reading.computations.divisional_readings.d60_shashtiamsa import (
            read_d60_shashtiamsa,
        )

        d60 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d60_shashtiamsa(d60, asc_sign=1, atmakaraka="Jupiter")
        ids = " ".join(out.keys()).lower()
        assert "atmakaraka" in ids


# ---------------------------------------------------------------------------
# Birth-time sensitivity marker (REQUIRED in EVERY Finding's evidence)
# ---------------------------------------------------------------------------


class TestBirthTimeSensitivity:

    def test_every_finding_carries_sensitivity_marker(self):
        from app.reading.computations.divisional_readings.d60_shashtiamsa import (
            read_d60_shashtiamsa,
        )

        d60 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d60_shashtiamsa(d60, asc_sign=1, atmakaraka="Jupiter")
        for fid, f in out.items():
            blob = " ".join(f.evidence).lower()
            assert "birth_time_sensitivity=very_high" in blob, (
                f"{fid} missing birth-time sensitivity marker"
            )


# ---------------------------------------------------------------------------
# Past-life karma theme phrasing
# ---------------------------------------------------------------------------


class TestPastLifeTheme:

    def test_lagna_verdict_mentions_past_life_or_karma(self):
        from app.reading.computations.divisional_readings.d60_shashtiamsa import (
            read_d60_shashtiamsa,
        )

        d60 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d60_shashtiamsa(d60, asc_sign=1, atmakaraka="Jupiter")
        lagna = out["d60.lagna"]
        blob = (lagna.verdict + " " + " ".join(lagna.evidence)).lower()
        assert "past-life" in blob or "past life" in blob or "karma" in blob

    def test_atmakaraka_verdict_mentions_soul_or_atma(self):
        from app.reading.computations.divisional_readings.d60_shashtiamsa import (
            read_d60_shashtiamsa,
        )

        d60 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d60_shashtiamsa(d60, asc_sign=1, atmakaraka="Jupiter")
        ak = next(f for fid, f in out.items() if "atmakaraka" in fid)
        blob = (ak.verdict + " " + " ".join(ak.evidence)).lower()
        assert "soul" in blob or "atma" in blob or "karma" in blob


# ---------------------------------------------------------------------------
# Doctrine sentinel
# ---------------------------------------------------------------------------


class TestDoctrineSentinel:

    def test_every_finding_carries_doctrine_sentinel(self):
        from app.reading.computations.divisional_readings.d60_shashtiamsa import (
            read_d60_shashtiamsa,
        )

        d60 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d60_shashtiamsa(d60, asc_sign=1, atmakaraka="Jupiter")
        for fid, f in out.items():
            blob = " ".join(f.evidence)
            assert "doctrine=" in blob, f"{fid} missing doctrine sentinel"


# ---------------------------------------------------------------------------
# Evidence shape
# ---------------------------------------------------------------------------


class TestEvidence:

    def test_per_planet_evidence_has_d60_sign(self):
        from app.reading.computations.divisional_readings.d60_shashtiamsa import (
            read_d60_shashtiamsa,
        )

        d60 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d60_shashtiamsa(d60, asc_sign=1, atmakaraka="Jupiter")
        for fid, f in out.items():
            if fid == "d60.lagna":
                continue
            blob = " ".join(f.evidence)
            assert "d60_sign=" in blob, f"{fid} evidence missing d60_sign"


# ---------------------------------------------------------------------------
# Property: all 12 ascendants
# ---------------------------------------------------------------------------


class TestPropertyAllAsc:

    @pytest.mark.parametrize("asc", list(range(1, 13)))
    def test_runs_for_every_ascendant(self, asc):
        from app.reading.computations.divisional_readings.d60_shashtiamsa import (
            read_d60_shashtiamsa,
        )

        d60 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d60_shashtiamsa(d60, asc_sign=asc, atmakaraka="Jupiter")
        assert out
        for f in out.values():
            assert f.id.startswith("d60.")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidation:

    def test_rejects_bad_asc_sign(self):
        from app.reading.computations.divisional_readings.d60_shashtiamsa import (
            read_d60_shashtiamsa,
        )

        d60 = _build_chart({"Jupiter": 9})
        with pytest.raises(ValueError):
            read_d60_shashtiamsa(d60, asc_sign=0, atmakaraka="Jupiter")
        with pytest.raises(ValueError):
            read_d60_shashtiamsa(d60, asc_sign=13, atmakaraka="Jupiter")

    def test_rejects_invalid_atmakaraka(self):
        from app.reading.computations.divisional_readings.d60_shashtiamsa import (
            read_d60_shashtiamsa,
        )

        d60 = _build_chart({"Jupiter": 9})
        with pytest.raises(ValueError):
            read_d60_shashtiamsa(d60, asc_sign=1, atmakaraka="NotAPlanet")
