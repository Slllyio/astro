"""Tests for ``app.reading.computations.yogas_extended.vipareeta``.

Doctrine source: BPHS Vol.I — positional variants of Vipareeta Raja Yoga.

Classical rule
==============

Positional Vipareeta variants fire when a single trika lord (6L, 8L, or
12L) sits in one of the three trika houses (6, 8, or 12). The misfortune
signification of the lord's home house is neutralised by its placement in
another dusthana (negation-of-negation, positional form).

Variants (single-lord placement — no exchange required):

- **Harsha Vipareeta**: 6L placed in 6, 8, or 12 from Lagna
- **Sarala Vipareeta**: 8L placed in 6, 8, or 12 from Lagna
- **Vimala Vipareeta**: 12L placed in 6, 8, or 12 from Lagna

ID grammar
==========

``practitioner.yogas_extended.vipareeta.harsha``
``practitioner.yogas_extended.vipareeta.sarala``
``practitioner.yogas_extended.vipareeta.vimala``

Each detection produces one Finding per matched variant. All carry
``classification="yoga"`` and ``direction="positive"`` (reversal-yoga).

Coordination
============

The EXCHANGE variant (6L↔8L, 6L↔12L, 8L↔12L) is already detected by
``trika_doctrine.detect_trika_exchanges``. This module detects POSITIONAL
variants (no exchange required). When a placement coexists with a
``trika_doctrine`` exchange-variant, the evidence carries a
``coexists_with=...`` note so downstream synthesis can deduplicate.
"""
from __future__ import annotations

import pytest


def _planet_in_house(asc_sign: int, target_house: int) -> int:
    return ((asc_sign + target_house - 2) % 12) + 1


def _planet_dict(sign: int) -> dict:
    return {"sign": sign, "longitude": (sign - 1) * 30.0 + 15.0}


def _chart_with(asc_sign: int, placements: dict[str, int]) -> dict:
    """Build a d1_chart with each named planet placed in the requested
    HOUSE (1..12 from asc_sign). All other planets default to the 1st
    house (benign — out of 6/8/12)."""
    chart: dict[str, dict] = {}
    benign_sign = asc_sign
    for planet in (
        "Sun", "Moon", "Mars", "Mercury", "Jupiter",
        "Venus", "Saturn", "Rahu", "Ketu",
    ):
        if planet in placements:
            chart[planet] = _planet_dict(
                _planet_in_house(asc_sign, placements[planet])
            )
        else:
            chart[planet] = _planet_dict(benign_sign)
    return chart


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------


class TestDetectVipareetaShape:

    def test_returns_list(self):
        from app.reading.computations.yogas_extended.vipareeta import (
            detect_vipareeta,
        )

        result = detect_vipareeta(_chart_with(1, {}), asc_sign=1)
        assert isinstance(result, list)

    def test_invalid_asc_sign_raises(self):
        from app.reading.computations.yogas_extended.vipareeta import (
            detect_vipareeta,
        )

        with pytest.raises(ValueError):
            detect_vipareeta(_chart_with(1, {}), asc_sign=0)
        with pytest.raises(ValueError):
            detect_vipareeta(_chart_with(1, {}), asc_sign=13)

    def test_no_trika_lord_in_trika_no_finding(self):
        """All planets placed in 1st house — no positional Vipareeta."""
        from app.reading.computations.yogas_extended.vipareeta import (
            detect_vipareeta,
        )

        result = detect_vipareeta(_chart_with(1, {}), asc_sign=1)
        assert result == []


# ---------------------------------------------------------------------------
# Variants
# ---------------------------------------------------------------------------


class TestVipareetaVariants:
    """Aries lagna (asc=1): 6L=Mercury, 8L=Mars, 12L=Jupiter."""

    def test_harsha_6L_in_6(self):
        from app.reading.computations.yogas_extended.vipareeta import (
            detect_vipareeta,
        )

        # Aries lagna: 6L = Mercury. Place Mercury in 6th house.
        chart = _chart_with(asc_sign=1, placements={"Mercury": 6})
        result = detect_vipareeta(chart, asc_sign=1)
        ids = [f.id for f in result]
        assert "practitioner.yogas_extended.vipareeta.harsha" in ids

    def test_harsha_6L_in_8(self):
        from app.reading.computations.yogas_extended.vipareeta import (
            detect_vipareeta,
        )

        chart = _chart_with(asc_sign=1, placements={"Mercury": 8})
        result = detect_vipareeta(chart, asc_sign=1)
        ids = [f.id for f in result]
        assert "practitioner.yogas_extended.vipareeta.harsha" in ids

    def test_harsha_6L_in_12(self):
        from app.reading.computations.yogas_extended.vipareeta import (
            detect_vipareeta,
        )

        chart = _chart_with(asc_sign=1, placements={"Mercury": 12})
        result = detect_vipareeta(chart, asc_sign=1)
        ids = [f.id for f in result]
        assert "practitioner.yogas_extended.vipareeta.harsha" in ids

    def test_sarala_8L_in_6(self):
        from app.reading.computations.yogas_extended.vipareeta import (
            detect_vipareeta,
        )

        # Aries lagna: 8L = Mars. Place Mars in 6th house.
        chart = _chart_with(asc_sign=1, placements={"Mars": 6})
        result = detect_vipareeta(chart, asc_sign=1)
        ids = [f.id for f in result]
        assert "practitioner.yogas_extended.vipareeta.sarala" in ids

    def test_vimala_12L_in_8(self):
        from app.reading.computations.yogas_extended.vipareeta import (
            detect_vipareeta,
        )

        # Aries lagna: 12L = Jupiter. Place Jupiter in 8th house.
        chart = _chart_with(asc_sign=1, placements={"Jupiter": 8})
        result = detect_vipareeta(chart, asc_sign=1)
        ids = [f.id for f in result]
        assert "practitioner.yogas_extended.vipareeta.vimala" in ids

    def test_6L_NOT_in_dusthana_no_harsha(self):
        from app.reading.computations.yogas_extended.vipareeta import (
            detect_vipareeta,
        )

        # 6L=Mercury placed in 5th — NOT a dusthana.
        chart = _chart_with(asc_sign=1, placements={"Mercury": 5})
        result = detect_vipareeta(chart, asc_sign=1)
        ids = [f.id for f in result]
        assert "practitioner.yogas_extended.vipareeta.harsha" not in ids

    def test_multiple_variants_coexist(self):
        """Harsha + Sarala fire simultaneously when 6L AND 8L both in trika."""
        from app.reading.computations.yogas_extended.vipareeta import (
            detect_vipareeta,
        )

        chart = _chart_with(
            asc_sign=1,
            placements={
                "Mercury": 6,  # 6L in 6 → Harsha
                "Mars": 12,    # 8L in 12 → Sarala
            },
        )
        result = detect_vipareeta(chart, asc_sign=1)
        ids = {f.id for f in result}
        assert "practitioner.yogas_extended.vipareeta.harsha" in ids
        assert "practitioner.yogas_extended.vipareeta.sarala" in ids


# ---------------------------------------------------------------------------
# Coordination with trika_doctrine.py
# ---------------------------------------------------------------------------


class TestTrikaDoctrineCoordination:
    """When 6L is placed in 8H AND 8L is placed in 6H, both the positional
    Harsha/Sarala fire here AND trika_doctrine emits the exchange variant.
    The positional findings carry a ``coexists_with`` evidence note."""

    def test_coexists_with_note_on_exchange_pattern(self):
        from app.reading.computations.yogas_extended.vipareeta import (
            detect_vipareeta,
        )

        # Aries: 6L=Mercury, 8L=Mars. Mercury→8th, Mars→6th = exchange.
        chart = _chart_with(
            asc_sign=1,
            placements={"Mercury": 8, "Mars": 6},
        )
        result = detect_vipareeta(chart, asc_sign=1)
        # Both Harsha (6L Mercury in 8) and Sarala (8L Mars in 6) should fire.
        ids = {f.id for f in result}
        assert "practitioner.yogas_extended.vipareeta.harsha" in ids
        assert "practitioner.yogas_extended.vipareeta.sarala" in ids
        # Each must reference its coexisting trika_doctrine pair.
        for f in result:
            coexists = [e for e in f.evidence if e.startswith("coexists_with=")]
            assert coexists, (
                f"Finding {f.id} should carry a coexists_with note when "
                "the trika_doctrine exchange variant is implied."
            )


# ---------------------------------------------------------------------------
# Finding envelope
# ---------------------------------------------------------------------------


class TestFindingEnvelope:

    def test_verdict_under_140_chars(self):
        from app.reading.computations.yogas_extended.vipareeta import (
            detect_vipareeta,
        )

        chart = _chart_with(asc_sign=1, placements={"Mercury": 8})
        result = detect_vipareeta(chart, asc_sign=1)
        for f in result:
            assert len(f.verdict) <= 140

    def test_evidence_contains_doctrine_sentinel(self):
        from app.reading.computations.yogas_extended.vipareeta import (
            detect_vipareeta,
        )

        chart = _chart_with(asc_sign=1, placements={"Mercury": 6})
        result = detect_vipareeta(chart, asc_sign=1)
        assert result
        for f in result:
            doctrine = next(
                (e for e in f.evidence if e.startswith("doctrine=")), None
            )
            assert doctrine is not None
            assert "BPHS" in doctrine or "Vipareeta" in doctrine

    def test_classification_is_yoga_and_positive(self):
        from app.reading.computations.yogas_extended.vipareeta import (
            detect_vipareeta,
        )

        chart = _chart_with(asc_sign=1, placements={"Mercury": 6})
        result = detect_vipareeta(chart, asc_sign=1)
        assert result
        for f in result:
            assert f.classification == "yoga"
            assert f.direction == "positive"

    def test_confidence_is_indicative_only(self):
        from app.reading.computations.yogas_extended.vipareeta import (
            detect_vipareeta,
        )

        chart = _chart_with(asc_sign=1, placements={"Mercury": 6})
        [finding, *_] = detect_vipareeta(chart, asc_sign=1)
        assert finding.confidence.band == "indicative_only"
        assert finding.confidence.score == 0.0
