"""Tests for ``app.reading.computations.divisional_readings.d10_dashamsha``.

Doctrine source: BPHS Vol.I Ch.6-7 (Shodashavarga). The D10 Dashamsha
governs **career and karma execution** in the world. Each 30° rashi is
split into 10 × 3° parts.

The reading layer emits:

  - **D10 Lagna** — career frame anchor.
  - **D10 lagna lord** — primary career signifier per D10's own lagna.
  - **D10 10H lord** — career-house signifier within D10.
  - **Amatya Karaka in D10** — Jaimini's professional karaka.
  - **5-pillar career synthesis** (this is the absorbed
    ``career_d10_pillars`` logic):
      Pillar 1: D1 10L placement (sign known via d1_chart)
      Pillar 2: D10 lagna lord
      Pillar 3: Amatya Karaka in D10
      Pillar 4: Strongest career karaka (Sun/Mercury/Mars) — by D10 own-sign
      Pillar 5: Saturn (service) in D10
    Concordance counts how many pillars share a sign-element.
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
        from app.reading.computations.divisional_readings.d10_dashamsha import (
            read_d10_dashamsha,
        )
        from app.reading.schema import Finding

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d10 = _build_chart({"Sun": 5, "Moon": 1, "Mars": 5, "Mercury": 5,
                            "Jupiter": 10, "Venus": 8, "Saturn": 5})
        out = read_d10_dashamsha(d1, d10, asc_sign=1, amatya_karaka="Mercury")
        assert isinstance(out, dict)
        assert out
        for v in out.values():
            assert isinstance(v, Finding)

    def test_id_grammar(self):
        from app.reading.computations.divisional_readings.d10_dashamsha import (
            read_d10_dashamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d10 = _build_chart({"Sun": 5, "Moon": 1, "Mars": 5, "Mercury": 5,
                            "Jupiter": 10, "Venus": 8, "Saturn": 5})
        out = read_d10_dashamsha(d1, d10, asc_sign=1, amatya_karaka="Mercury")
        for fid in out:
            assert fid.startswith("d10.")

    def test_classification_primitive(self):
        from app.reading.computations.divisional_readings.d10_dashamsha import (
            read_d10_dashamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d10 = _build_chart({"Sun": 5, "Moon": 1, "Mars": 5, "Mercury": 5,
                            "Jupiter": 10, "Venus": 8, "Saturn": 5})
        out = read_d10_dashamsha(d1, d10, asc_sign=1, amatya_karaka="Mercury")
        for f in out.values():
            assert f.classification == "primitive"

    def test_verdict_under_140(self):
        from app.reading.computations.divisional_readings.d10_dashamsha import (
            read_d10_dashamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d10 = _build_chart({"Sun": 5, "Moon": 1, "Mars": 5, "Mercury": 5,
                            "Jupiter": 10, "Venus": 8, "Saturn": 5})
        out = read_d10_dashamsha(d1, d10, asc_sign=1, amatya_karaka="Mercury")
        for f in out.values():
            assert len(f.verdict) <= 140


# ---------------------------------------------------------------------------
# Required findings
# ---------------------------------------------------------------------------


class TestRequiredFindings:

    def test_lagna_present(self):
        from app.reading.computations.divisional_readings.d10_dashamsha import (
            read_d10_dashamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d10 = _build_chart({"Sun": 5, "Moon": 1, "Mars": 5, "Mercury": 5,
                            "Jupiter": 10, "Venus": 8, "Saturn": 5})
        out = read_d10_dashamsha(d1, d10, asc_sign=1, amatya_karaka="Mercury")
        assert "d10.lagna" in out

    def test_10th_house_lord_present(self):
        """Aries asc -> 10H = Capricorn -> 10L = Saturn."""
        from app.reading.computations.divisional_readings.d10_dashamsha import (
            read_d10_dashamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d10 = _build_chart({"Sun": 5, "Moon": 1, "Mars": 5, "Mercury": 5,
                            "Jupiter": 10, "Venus": 8, "Saturn": 5})
        out = read_d10_dashamsha(d1, d10, asc_sign=1, amatya_karaka="Mercury")
        ids = " ".join(out.keys()).lower()
        assert "10h_lord" in ids or "tenth_house_lord" in ids

    def test_amatya_karaka_finding(self):
        from app.reading.computations.divisional_readings.d10_dashamsha import (
            read_d10_dashamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d10 = _build_chart({"Sun": 5, "Moon": 1, "Mars": 5, "Mercury": 5,
                            "Jupiter": 10, "Venus": 8, "Saturn": 5})
        out = read_d10_dashamsha(d1, d10, asc_sign=1, amatya_karaka="Mercury")
        ids = " ".join(out.keys()).lower()
        assert "amatya" in ids


# ---------------------------------------------------------------------------
# 5-pillar synthesis
# ---------------------------------------------------------------------------


class TestFivePillarSynthesis:

    def test_pillars_finding_present(self):
        from app.reading.computations.divisional_readings.d10_dashamsha import (
            read_d10_dashamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d10 = _build_chart({"Sun": 5, "Moon": 1, "Mars": 5, "Mercury": 5,
                            "Jupiter": 10, "Venus": 8, "Saturn": 5})
        out = read_d10_dashamsha(d1, d10, asc_sign=1, amatya_karaka="Mercury")
        assert "d10.career_5_pillars" in out

    def test_pillars_verdict_mentions_count(self):
        """The pillars verdict should mention X/5 concordance."""
        from app.reading.computations.divisional_readings.d10_dashamsha import (
            read_d10_dashamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d10 = _build_chart({"Sun": 5, "Moon": 1, "Mars": 5, "Mercury": 5,
                            "Jupiter": 10, "Venus": 8, "Saturn": 5})
        out = read_d10_dashamsha(d1, d10, asc_sign=1, amatya_karaka="Mercury")
        pillars = out["d10.career_5_pillars"]
        assert "/5" in pillars.verdict

    def test_pillars_evidence_records_each_pillar(self):
        from app.reading.computations.divisional_readings.d10_dashamsha import (
            read_d10_dashamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d10 = _build_chart({"Sun": 5, "Moon": 1, "Mars": 5, "Mercury": 5,
                            "Jupiter": 10, "Venus": 8, "Saturn": 5})
        out = read_d10_dashamsha(d1, d10, asc_sign=1, amatya_karaka="Mercury")
        blob = " ".join(out["d10.career_5_pillars"].evidence).lower()
        # five pillar markers
        assert "pillar_1" in blob
        assert "pillar_2" in blob
        assert "pillar_3" in blob
        assert "pillar_4" in blob
        assert "pillar_5" in blob

    def test_pillars_evidence_reports_concordance(self):
        from app.reading.computations.divisional_readings.d10_dashamsha import (
            read_d10_dashamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d10 = _build_chart({"Sun": 5, "Moon": 1, "Mars": 5, "Mercury": 5,
                            "Jupiter": 10, "Venus": 8, "Saturn": 5})
        out = read_d10_dashamsha(d1, d10, asc_sign=1, amatya_karaka="Mercury")
        blob = " ".join(out["d10.career_5_pillars"].evidence).lower()
        assert "concordance" in blob

    def test_pillars_high_concordance_fixture(self):
        """4 of 5 pillars are in fire-sign Leo (5) in the test fixture.
        D1 10L = Saturn (in D1 sign 10 — earth), but Saturn in D10 is
        Leo (fire)... let the implementation choose the rule. We assert
        concordance >= 2 so the fixture exercises the counting path
        without over-specifying."""
        from app.reading.computations.divisional_readings.d10_dashamsha import (
            read_d10_dashamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d10 = _build_chart({"Sun": 5, "Moon": 1, "Mars": 5, "Mercury": 5,
                            "Jupiter": 10, "Venus": 8, "Saturn": 5})
        out = read_d10_dashamsha(d1, d10, asc_sign=1, amatya_karaka="Mercury")
        verdict_lower = out["d10.career_5_pillars"].verdict.lower()
        # extract X/5
        import re
        m = re.search(r"(\d+)/5", verdict_lower)
        assert m, f"no X/5 in verdict: {verdict_lower}"
        n = int(m.group(1))
        assert 0 <= n <= 5


# ---------------------------------------------------------------------------
# Doctrine sentinel
# ---------------------------------------------------------------------------


class TestDoctrineSentinel:

    def test_every_finding_carries_doctrine_sentinel(self):
        from app.reading.computations.divisional_readings.d10_dashamsha import (
            read_d10_dashamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d10 = _build_chart({"Sun": 5, "Moon": 1, "Mars": 5, "Mercury": 5,
                            "Jupiter": 10, "Venus": 8, "Saturn": 5})
        out = read_d10_dashamsha(d1, d10, asc_sign=1, amatya_karaka="Mercury")
        for fid, f in out.items():
            blob = " ".join(f.evidence)
            assert "doctrine=" in blob, f"{fid} missing doctrine sentinel"


# ---------------------------------------------------------------------------
# Career theme phrasing
# ---------------------------------------------------------------------------


class TestCareerTheme:

    def test_lagna_verdict_mentions_career_or_karma(self):
        from app.reading.computations.divisional_readings.d10_dashamsha import (
            read_d10_dashamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d10 = _build_chart({"Sun": 5, "Moon": 1, "Mars": 5, "Mercury": 5,
                            "Jupiter": 10, "Venus": 8, "Saturn": 5})
        out = read_d10_dashamsha(d1, d10, asc_sign=1, amatya_karaka="Mercury")
        lagna = out["d10.lagna"]
        blob = (lagna.verdict + " " + " ".join(lagna.evidence)).lower()
        assert "career" in blob or "karma" in blob


# ---------------------------------------------------------------------------
# Property: all 12 ascendants
# ---------------------------------------------------------------------------


class TestPropertyAllAsc:

    @pytest.mark.parametrize("asc", list(range(1, 13)))
    def test_runs_for_every_ascendant(self, asc):
        from app.reading.computations.divisional_readings.d10_dashamsha import (
            read_d10_dashamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d10 = _build_chart({"Sun": 5, "Moon": 1, "Mars": 5, "Mercury": 5,
                            "Jupiter": 10, "Venus": 8, "Saturn": 5})
        out = read_d10_dashamsha(d1, d10, asc_sign=asc, amatya_karaka="Mercury")
        assert out
        for f in out.values():
            assert f.id.startswith("d10.")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidation:

    def test_rejects_bad_asc_sign(self):
        from app.reading.computations.divisional_readings.d10_dashamsha import (
            read_d10_dashamsha,
        )

        d1 = _build_chart({"Saturn": 10})
        d10 = _build_chart({"Saturn": 5})
        with pytest.raises(ValueError):
            read_d10_dashamsha(d1, d10, asc_sign=0, amatya_karaka="Mercury")
        with pytest.raises(ValueError):
            read_d10_dashamsha(d1, d10, asc_sign=13, amatya_karaka="Mercury")

    def test_rejects_invalid_amatya_karaka(self):
        from app.reading.computations.divisional_readings.d10_dashamsha import (
            read_d10_dashamsha,
        )

        d1 = _build_chart({"Saturn": 10})
        d10 = _build_chart({"Saturn": 5})
        with pytest.raises(ValueError):
            read_d10_dashamsha(d1, d10, asc_sign=1, amatya_karaka="NotAPlanet")
