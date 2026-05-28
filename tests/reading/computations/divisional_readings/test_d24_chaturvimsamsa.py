"""Tests for ``app.reading.computations.divisional_readings.d24_chaturvimsamsa``.

Doctrine lock: **D-16** (education routes through D24 per BPHS Vol.I
Ch.6 v.21; D24 is the Vidya / formal-education chart). The reading
module is the sole consumer expected by ``domains/education.py``.

D24 structure: each 30° rashi split into 24 × 1.25° parts. Odd signs
start counting from Leo (sign 5), even signs start from Cancer (sign 4).
The construction itself lives in ``app.core.shodashavarga._chaturvimsamsa_d24``;
this module reads the finished D24 chart and emits Findings for the
education-relevant signifiers:

  - **D24 Lagna** (overall educational framing).
  - **D24 4H lord** (formal-education foundation; 4H = primary schooling).
  - **D24 5H lord** (intellectual capacity; 5H = creativity, higher
    intelligence, also "purva-punya").
  - **D24 Jupiter** (natural karaka of wisdom, vidya).
  - **D24 Mercury** (natural karaka of academic intellect).

This module is ★NEW per the post-review revision; a doctrine-reviewer
audit should pay extra attention to the verdict phrasings.
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
        from app.reading.computations.divisional_readings.d24_chaturvimsamsa import (
            read_d24_chaturvimsamsa,
        )
        from app.reading.schema import Finding

        d24 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d24_chaturvimsamsa(d24, asc_sign=1)
        assert isinstance(out, dict)
        for v in out.values():
            assert isinstance(v, Finding)

    def test_id_grammar(self):
        from app.reading.computations.divisional_readings.d24_chaturvimsamsa import (
            read_d24_chaturvimsamsa,
        )

        d24 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d24_chaturvimsamsa(d24, asc_sign=1)
        for fid in out:
            assert fid.startswith("d24.")

    def test_classification_primitive(self):
        from app.reading.computations.divisional_readings.d24_chaturvimsamsa import (
            read_d24_chaturvimsamsa,
        )

        d24 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d24_chaturvimsamsa(d24, asc_sign=1)
        for f in out.values():
            assert f.classification == "primitive"

    def test_verdict_under_140(self):
        from app.reading.computations.divisional_readings.d24_chaturvimsamsa import (
            read_d24_chaturvimsamsa,
        )

        d24 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d24_chaturvimsamsa(d24, asc_sign=1)
        for f in out.values():
            assert len(f.verdict) <= 140


# ---------------------------------------------------------------------------
# Required findings.
# ---------------------------------------------------------------------------


class TestRequiredFindings:

    def test_lagna_finding(self):
        from app.reading.computations.divisional_readings.d24_chaturvimsamsa import (
            read_d24_chaturvimsamsa,
        )

        d24 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d24_chaturvimsamsa(d24, asc_sign=1)
        assert "d24.lagna" in out

    def test_jupiter_finding(self):
        from app.reading.computations.divisional_readings.d24_chaturvimsamsa import (
            read_d24_chaturvimsamsa,
        )

        d24 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d24_chaturvimsamsa(d24, asc_sign=1)
        assert any("jupiter" in fid for fid in out)

    def test_mercury_finding(self):
        from app.reading.computations.divisional_readings.d24_chaturvimsamsa import (
            read_d24_chaturvimsamsa,
        )

        d24 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d24_chaturvimsamsa(d24, asc_sign=1)
        assert any("mercury" in fid for fid in out)

    def test_fourth_house_lord_finding(self):
        """Aries asc -> 4H = Cancer -> 4L = Moon."""
        from app.reading.computations.divisional_readings.d24_chaturvimsamsa import (
            read_d24_chaturvimsamsa,
        )

        d24 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d24_chaturvimsamsa(d24, asc_sign=1)
        ids = " ".join(out.keys()).lower()
        assert "4h_lord" in ids or "fourth_house_lord" in ids

    def test_fifth_house_lord_finding(self):
        """Aries asc -> 5H = Leo -> 5L = Sun."""
        from app.reading.computations.divisional_readings.d24_chaturvimsamsa import (
            read_d24_chaturvimsamsa,
        )

        d24 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d24_chaturvimsamsa(d24, asc_sign=1)
        ids = " ".join(out.keys()).lower()
        assert "5h_lord" in ids or "fifth_house_lord" in ids


# ---------------------------------------------------------------------------
# D-16 doctrine sentinel: verdict/evidence reference education / Vidya.
# ---------------------------------------------------------------------------


class TestEducationDomain:

    def test_jupiter_evidence_mentions_education_or_vidya(self):
        from app.reading.computations.divisional_readings.d24_chaturvimsamsa import (
            read_d24_chaturvimsamsa,
        )

        d24 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d24_chaturvimsamsa(d24, asc_sign=1)
        jup = next(f for fid, f in out.items() if "jupiter" in fid)
        blob = (jup.verdict + " " + " ".join(jup.evidence)).lower()
        assert "education" in blob or "vidya" in blob or "wisdom" in blob

    def test_lagna_verdict_mentions_education_frame(self):
        from app.reading.computations.divisional_readings.d24_chaturvimsamsa import (
            read_d24_chaturvimsamsa,
        )

        d24 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d24_chaturvimsamsa(d24, asc_sign=1)
        lagna = out["d24.lagna"]
        blob = (lagna.verdict + " " + " ".join(lagna.evidence)).lower()
        assert "education" in blob or "vidya" in blob

    def test_doctrine_sentinel_references_d_16(self):
        """The D-16 lock must appear in evidence so doctrine-reviewers
        can trace the routing decision back to the lockfile."""
        from app.reading.computations.divisional_readings.d24_chaturvimsamsa import (
            read_d24_chaturvimsamsa,
        )

        d24 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d24_chaturvimsamsa(d24, asc_sign=1)
        all_evidence = []
        for f in out.values():
            all_evidence.extend(f.evidence)
        blob = " ".join(all_evidence)
        assert "D-16" in blob


# ---------------------------------------------------------------------------
# Evidence carries d24_sign.
# ---------------------------------------------------------------------------


class TestEvidence:

    def test_per_planet_evidence_has_d24_sign(self):
        from app.reading.computations.divisional_readings.d24_chaturvimsamsa import (
            read_d24_chaturvimsamsa,
        )

        d24 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d24_chaturvimsamsa(d24, asc_sign=1)
        for fid, f in out.items():
            if fid == "d24.lagna":
                continue
            blob = " ".join(f.evidence)
            assert "d24_sign=" in blob, f"{fid} evidence missing d24_sign"


# ---------------------------------------------------------------------------
# Property: all 12 ascendants.
# ---------------------------------------------------------------------------


class TestPropertyAllAsc:

    @pytest.mark.parametrize("asc", list(range(1, 13)))
    def test_runs_for_every_ascendant(self, asc):
        from app.reading.computations.divisional_readings.d24_chaturvimsamsa import (
            read_d24_chaturvimsamsa,
        )

        d24 = _build_chart({
            "Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
            "Jupiter": 9, "Venus": 7, "Saturn": 10,
        })
        out = read_d24_chaturvimsamsa(d24, asc_sign=asc)
        assert out
        for f in out.values():
            assert f.id.startswith("d24.")
