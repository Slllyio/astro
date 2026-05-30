"""Tests for ``app.reading.computations.divisional_readings.d9_navamsha``.

Doctrine source: BPHS Vol.I Ch.6-7 (Shodashavarga). The D9 Navamsha is
the most important secondary chart, governing **dharma, marriage
potential, and ultimate fruit of planets** (phaladayaka). Each 30°
rashi splits into 9 × 3.333° parts; odd signs start from the same sign,
even signs start from the 7th sign from D1.

The reading layer interprets the D9 chart for dharma + marriage:

  - **D9 Lagna** (overall dharma frame; spouse / marriage anchor).
  - **D9 lagna lord** placement.
  - **Vargottama planets** — same sign in D1 and D9 → unusually strong /
    consistent influence (this is why the public API takes BOTH d1 and
    d9 charts).
  - **D9 7H lord** (spouse signifier).
  - **D9 Venus** placement (spouse karaka for male charts / general
    relationship karaka).
  - **D9 Jupiter** placement (husband karaka for female charts / dharma
    karaka).
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
        from app.reading.computations.divisional_readings.d9_navamsha import (
            read_d9_navamsha,
        )
        from app.reading.schema import Finding

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d9 = _build_chart({"Sun": 5, "Moon": 6, "Mars": 1, "Mercury": 11,
                           "Jupiter": 9, "Venus": 7, "Saturn": 8})
        out = read_d9_navamsha(d1, d9, asc_sign=1)
        assert isinstance(out, dict)
        assert out
        for v in out.values():
            assert isinstance(v, Finding)

    def test_id_grammar(self):
        from app.reading.computations.divisional_readings.d9_navamsha import (
            read_d9_navamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d9 = _build_chart({"Sun": 5, "Moon": 6, "Mars": 1, "Mercury": 11,
                           "Jupiter": 9, "Venus": 7, "Saturn": 8})
        out = read_d9_navamsha(d1, d9, asc_sign=1)
        for fid in out:
            assert fid.startswith("d9.")

    def test_classification_primitive(self):
        from app.reading.computations.divisional_readings.d9_navamsha import (
            read_d9_navamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d9 = _build_chart({"Sun": 5, "Moon": 6, "Mars": 1, "Mercury": 11,
                           "Jupiter": 9, "Venus": 7, "Saturn": 8})
        out = read_d9_navamsha(d1, d9, asc_sign=1)
        for f in out.values():
            assert f.classification == "primitive"

    def test_verdict_under_140(self):
        from app.reading.computations.divisional_readings.d9_navamsha import (
            read_d9_navamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d9 = _build_chart({"Sun": 5, "Moon": 6, "Mars": 1, "Mercury": 11,
                           "Jupiter": 9, "Venus": 7, "Saturn": 8})
        out = read_d9_navamsha(d1, d9, asc_sign=1)
        for f in out.values():
            assert len(f.verdict) <= 140


# ---------------------------------------------------------------------------
# Required findings
# ---------------------------------------------------------------------------


class TestRequiredFindings:

    def test_lagna_finding_present(self):
        from app.reading.computations.divisional_readings.d9_navamsha import (
            read_d9_navamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d9 = _build_chart({"Sun": 5, "Moon": 6, "Mars": 1, "Mercury": 11,
                           "Jupiter": 9, "Venus": 7, "Saturn": 8})
        out = read_d9_navamsha(d1, d9, asc_sign=1)
        assert "d9.lagna" in out

    def test_per_planet_findings(self):
        from app.reading.computations.divisional_readings.d9_navamsha import (
            read_d9_navamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d9 = _build_chart({"Sun": 5, "Moon": 6, "Mars": 1, "Mercury": 11,
                           "Jupiter": 9, "Venus": 7, "Saturn": 8})
        out = read_d9_navamsha(d1, d9, asc_sign=1)
        for p in ["sun", "moon", "venus", "jupiter"]:
            assert any(p in fid for fid in out)

    def test_seventh_house_lord_finding(self):
        """Aries asc -> 7H = Libra -> 7L = Venus."""
        from app.reading.computations.divisional_readings.d9_navamsha import (
            read_d9_navamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d9 = _build_chart({"Sun": 5, "Moon": 6, "Mars": 1, "Mercury": 11,
                           "Jupiter": 9, "Venus": 7, "Saturn": 8})
        out = read_d9_navamsha(d1, d9, asc_sign=1)
        ids = " ".join(out.keys()).lower()
        assert "7h_lord" in ids or "seventh_house_lord" in ids


# ---------------------------------------------------------------------------
# Vargottama detection
# ---------------------------------------------------------------------------


class TestVargottama:

    def test_vargottama_planets_detected(self):
        """Sun in Leo in both D1 and D9 -> Vargottama. Mars in Aries in
        both -> Vargottama. Jupiter in Sagittarius in both -> Vargottama.
        Venus in Libra in both -> Vargottama."""
        from app.reading.computations.divisional_readings.d9_navamsha import (
            read_d9_navamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d9 = _build_chart({"Sun": 5, "Moon": 6, "Mars": 1, "Mercury": 11,
                           "Jupiter": 9, "Venus": 7, "Saturn": 8})
        out = read_d9_navamsha(d1, d9, asc_sign=1)
        all_ev = " ".join(" ".join(f.evidence) for f in out.values())
        # at least one vargottama mention somewhere
        assert "vargottama" in all_ev.lower()

    def test_vargottama_appears_in_per_planet_finding(self):
        """Sun is vargottama in this fixture -> the Sun Finding should
        flag it explicitly."""
        from app.reading.computations.divisional_readings.d9_navamsha import (
            read_d9_navamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d9 = _build_chart({"Sun": 5, "Moon": 6, "Mars": 1, "Mercury": 11,
                           "Jupiter": 9, "Venus": 7, "Saturn": 8})
        out = read_d9_navamsha(d1, d9, asc_sign=1)
        sun_finding = next(f for fid, f in out.items() if fid.endswith("sun"))
        blob = (sun_finding.verdict + " " + " ".join(sun_finding.evidence)).lower()
        assert "vargottama" in blob

    def test_non_vargottama_planet_does_not_flag_vargottama(self):
        """Moon is in 4 (D1) and 6 (D9) — not vargottama; the Moon
        Finding's evidence should NOT mistakenly say 'is_vargottama=yes'."""
        from app.reading.computations.divisional_readings.d9_navamsha import (
            read_d9_navamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d9 = _build_chart({"Sun": 5, "Moon": 6, "Mars": 1, "Mercury": 11,
                           "Jupiter": 9, "Venus": 7, "Saturn": 8})
        out = read_d9_navamsha(d1, d9, asc_sign=1)
        moon_finding = next(f for fid, f in out.items() if fid.endswith("moon"))
        # evidence must carry an explicit "is_vargottama=no" marker
        blob = " ".join(moon_finding.evidence).lower()
        assert "is_vargottama=no" in blob


# ---------------------------------------------------------------------------
# Spouse/dharma karaka themes
# ---------------------------------------------------------------------------


class TestKarakaThemes:

    def test_venus_evidence_flags_spouse_karaka(self):
        from app.reading.computations.divisional_readings.d9_navamsha import (
            read_d9_navamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d9 = _build_chart({"Sun": 5, "Moon": 6, "Mars": 1, "Mercury": 11,
                           "Jupiter": 9, "Venus": 7, "Saturn": 8})
        out = read_d9_navamsha(d1, d9, asc_sign=1)
        venus_finding = next(f for fid, f in out.items() if fid.endswith("venus"))
        blob = (venus_finding.verdict + " " + " ".join(venus_finding.evidence)).lower()
        assert "spouse" in blob or "marriage" in blob or "karaka" in blob

    def test_jupiter_evidence_flags_dharma_or_husband_karaka(self):
        from app.reading.computations.divisional_readings.d9_navamsha import (
            read_d9_navamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d9 = _build_chart({"Sun": 5, "Moon": 6, "Mars": 1, "Mercury": 11,
                           "Jupiter": 9, "Venus": 7, "Saturn": 8})
        out = read_d9_navamsha(d1, d9, asc_sign=1)
        jup_finding = next(f for fid, f in out.items() if fid.endswith("jupiter"))
        blob = (jup_finding.verdict + " " + " ".join(jup_finding.evidence)).lower()
        assert "dharma" in blob or "husband" in blob or "karaka" in blob

    def test_lagna_verdict_mentions_dharma_or_marriage(self):
        from app.reading.computations.divisional_readings.d9_navamsha import (
            read_d9_navamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d9 = _build_chart({"Sun": 5, "Moon": 6, "Mars": 1, "Mercury": 11,
                           "Jupiter": 9, "Venus": 7, "Saturn": 8})
        out = read_d9_navamsha(d1, d9, asc_sign=1)
        lagna = out["d9.lagna"]
        blob = (lagna.verdict + " " + " ".join(lagna.evidence)).lower()
        assert "dharma" in blob or "marriage" in blob or "spouse" in blob


# ---------------------------------------------------------------------------
# Doctrine sentinel
# ---------------------------------------------------------------------------


class TestDoctrineSentinel:

    def test_every_finding_carries_doctrine_sentinel(self):
        from app.reading.computations.divisional_readings.d9_navamsha import (
            read_d9_navamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d9 = _build_chart({"Sun": 5, "Moon": 6, "Mars": 1, "Mercury": 11,
                           "Jupiter": 9, "Venus": 7, "Saturn": 8})
        out = read_d9_navamsha(d1, d9, asc_sign=1)
        for fid, f in out.items():
            blob = " ".join(f.evidence)
            assert "doctrine=" in blob, f"{fid} missing doctrine sentinel"


# ---------------------------------------------------------------------------
# Evidence shape
# ---------------------------------------------------------------------------


class TestEvidence:

    def test_per_planet_evidence_has_d9_sign(self):
        from app.reading.computations.divisional_readings.d9_navamsha import (
            read_d9_navamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d9 = _build_chart({"Sun": 5, "Moon": 6, "Mars": 1, "Mercury": 11,
                           "Jupiter": 9, "Venus": 7, "Saturn": 8})
        out = read_d9_navamsha(d1, d9, asc_sign=1)
        for fid, f in out.items():
            if fid == "d9.lagna":
                continue
            blob = " ".join(f.evidence)
            assert "d9_sign=" in blob, f"{fid} evidence missing d9_sign"


# ---------------------------------------------------------------------------
# Property: all 12 ascendants
# ---------------------------------------------------------------------------


class TestPropertyAllAsc:

    @pytest.mark.parametrize("asc", list(range(1, 13)))
    def test_runs_for_every_ascendant(self, asc):
        from app.reading.computations.divisional_readings.d9_navamsha import (
            read_d9_navamsha,
        )

        d1 = _build_chart({"Sun": 5, "Moon": 4, "Mars": 1, "Mercury": 3,
                           "Jupiter": 9, "Venus": 7, "Saturn": 10})
        d9 = _build_chart({"Sun": 5, "Moon": 6, "Mars": 1, "Mercury": 11,
                           "Jupiter": 9, "Venus": 7, "Saturn": 8})
        out = read_d9_navamsha(d1, d9, asc_sign=asc)
        assert out
        for f in out.values():
            assert f.id.startswith("d9.")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidation:

    def test_rejects_bad_asc_sign(self):
        from app.reading.computations.divisional_readings.d9_navamsha import (
            read_d9_navamsha,
        )

        d1 = _build_chart({"Jupiter": 9})
        d9 = _build_chart({"Jupiter": 9})
        with pytest.raises(ValueError):
            read_d9_navamsha(d1, d9, asc_sign=0)
        with pytest.raises(ValueError):
            read_d9_navamsha(d1, d9, asc_sign=13)
