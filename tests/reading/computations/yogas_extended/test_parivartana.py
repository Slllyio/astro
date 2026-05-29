"""Tests for ``app.reading.computations.yogas_extended.parivartana``.

Doctrine source: BPHS / Phaladeepika — Parivartana (mutual sign exchange).

Classical rule
==============

Parivartana = mutual sign-exchange between two house lords. If the lord
of house A sits in house B's sign AND the lord of house B sits in house
A's sign (where A and B are 1..12 and the two lords are distinct
planets), the two houses are in **parivartana**.

Variants (by which houses participate):

- **Maha Parivartana**: between a **Trikona** (1/5/9) and a **Kendra**
  (1/4/7/10) lord — creates a strong Raja Yoga.
- **Khala Parivartana**: any other exchange that does NOT involve a
  trika (6/8/12) house — generic exchange yoga.
- **Dainya Parivartana**: an exchange where one of the two houses is a
  **trika** (6/8/12) — creates struggle (dainya = misery), classified
  negative. (When BOTH houses are trika, the exchange is already
  handled by ``trika_doctrine.detect_trika_exchanges`` as Vipareeta;
  this module does not double-detect those.)

ID grammar
==========

``practitioner.yogas_extended.parivartana.<houseA>_<houseB>_<variant>``

where houseA < houseB and ``<variant>`` is ``maha``/``khala``/``dainya``.

Each exchange produces ONE Finding (no duplicate emission for the
mirror-pair).
"""
from __future__ import annotations

import pytest


def _planet_in_house(asc_sign: int, target_house: int) -> int:
    return ((asc_sign + target_house - 2) % 12) + 1


def _planet_dict(sign: int) -> dict:
    return {"sign": sign, "longitude": (sign - 1) * 30.0 + 15.0}


def _chart_with(asc_sign: int, placements: dict[str, int]) -> dict:
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


class TestDetectParivartanaShape:

    def test_returns_list(self):
        from app.reading.computations.yogas_extended.parivartana import (
            detect_parivartana,
        )

        result = detect_parivartana(_chart_with(1, {}), asc_sign=1)
        assert isinstance(result, list)

    def test_invalid_asc_sign_raises(self):
        from app.reading.computations.yogas_extended.parivartana import (
            detect_parivartana,
        )

        with pytest.raises(ValueError):
            detect_parivartana(_chart_with(1, {}), asc_sign=0)
        with pytest.raises(ValueError):
            detect_parivartana(_chart_with(1, {}), asc_sign=13)

    def test_no_exchange_no_finding(self):
        from app.reading.computations.yogas_extended.parivartana import (
            detect_parivartana,
        )

        # All planets in 1st house from asc — no exchanges.
        result = detect_parivartana(_chart_with(1, {}), asc_sign=1)
        assert result == []


# ---------------------------------------------------------------------------
# Maha Parivartana — trikona × kendra
# ---------------------------------------------------------------------------


class TestMahaParivartana:
    """Aries lagna: 5L=Sun (Leo lord), 9L=Jupiter (Sag lord).
    If Sun→9th house (Sag) AND Jupiter→5th house (Leo) ⇒ Maha exchange.
    """

    def test_5_9_exchange_is_maha(self):
        from app.reading.computations.yogas_extended.parivartana import (
            detect_parivartana,
        )

        chart = _chart_with(
            asc_sign=1,
            placements={"Sun": 9, "Jupiter": 5},
        )
        result = detect_parivartana(chart, asc_sign=1)
        ids = [f.id for f in result]
        assert "practitioner.yogas_extended.parivartana.5_9_maha" in ids
        finding = next(
            f for f in result
            if f.id == "practitioner.yogas_extended.parivartana.5_9_maha"
        )
        assert finding.direction == "positive"
        assert finding.classification == "yoga"

    def test_4_10_exchange_is_maha(self):
        """Aries lagna: 4L=Moon (Cancer), 10L=Saturn (Capricorn).
        Moon→10th (Cap) AND Saturn→4th (Cancer) ⇒ Maha (kendra-kendra)."""
        from app.reading.computations.yogas_extended.parivartana import (
            detect_parivartana,
        )

        chart = _chart_with(
            asc_sign=1,
            placements={"Moon": 10, "Saturn": 4},
        )
        result = detect_parivartana(chart, asc_sign=1)
        ids = [f.id for f in result]
        assert "practitioner.yogas_extended.parivartana.4_10_maha" in ids


# ---------------------------------------------------------------------------
# Khala Parivartana — neither trikona/kendra nor trika
# ---------------------------------------------------------------------------


class TestKhalaParivartana:
    """Aries lagna: 2L=Venus (Taurus), 11L=Saturn (Aquarius).
    Neither 2 nor 11 is trika (6/8/12) or trikona/kendra combo. Khala."""

    def test_2_11_exchange_is_khala(self):
        from app.reading.computations.yogas_extended.parivartana import (
            detect_parivartana,
        )

        chart = _chart_with(
            asc_sign=1,
            placements={"Venus": 11, "Saturn": 2},
        )
        result = detect_parivartana(chart, asc_sign=1)
        ids = [f.id for f in result]
        assert "practitioner.yogas_extended.parivartana.2_11_khala" in ids
        finding = next(
            f for f in result
            if f.id == "practitioner.yogas_extended.parivartana.2_11_khala"
        )
        assert finding.direction == "positive"


# ---------------------------------------------------------------------------
# Dainya Parivartana — one (and only one) trika house involved
# ---------------------------------------------------------------------------


class TestDainyaParivartana:
    """Aries lagna: 3L=Mercury (Gemini), 6L=Mercury... wait — same planet.
    Use 5L=Sun and 6L=Mercury instead. Sun→6th (Virgo) AND
    Mercury→5th (Leo) ⇒ Dainya exchange (one trika, one non-trika)."""

    def test_5_6_exchange_is_dainya_negative(self):
        from app.reading.computations.yogas_extended.parivartana import (
            detect_parivartana,
        )

        chart = _chart_with(
            asc_sign=1,
            placements={"Sun": 6, "Mercury": 5},
        )
        result = detect_parivartana(chart, asc_sign=1)
        ids = [f.id for f in result]
        assert "practitioner.yogas_extended.parivartana.5_6_dainya" in ids
        finding = next(
            f for f in result
            if f.id == "practitioner.yogas_extended.parivartana.5_6_dainya"
        )
        assert finding.direction == "negative"
        assert finding.classification == "yoga"


# ---------------------------------------------------------------------------
# Both-trika exchange handled by trika_doctrine.py — NOT emitted here
# ---------------------------------------------------------------------------


class TestBothTrikaExchangeIsTrikaDoctrineNotPrivartana:
    """When both houses are trika (6/8/12), the trika_doctrine module
    already emits Vipareeta. Avoid double-detection here."""

    def test_6_8_both_trika_not_emitted(self):
        """Aries: 6L=Mercury, 8L=Mars. Mercury→8 AND Mars→6 ⇒ both-trika
        exchange — handled by trika_doctrine, not here."""
        from app.reading.computations.yogas_extended.parivartana import (
            detect_parivartana,
        )

        chart = _chart_with(
            asc_sign=1,
            placements={"Mercury": 8, "Mars": 6},
        )
        result = detect_parivartana(chart, asc_sign=1)
        ids = [f.id for f in result]
        # Neither 6_8_dainya nor a generic 6_8 finding should appear.
        for variant in ("dainya", "khala", "maha"):
            assert (
                f"practitioner.yogas_extended.parivartana.6_8_{variant}"
                not in ids
            )


# ---------------------------------------------------------------------------
# Single-finding per pair (no duplicate from mirror enumeration)
# ---------------------------------------------------------------------------


class TestNoDuplicates:

    def test_single_finding_per_house_pair(self):
        """A 5↔9 exchange should yield exactly ONE finding, not two."""
        from app.reading.computations.yogas_extended.parivartana import (
            detect_parivartana,
        )

        chart = _chart_with(
            asc_sign=1,
            placements={"Sun": 9, "Jupiter": 5},
        )
        result = detect_parivartana(chart, asc_sign=1)
        maha_findings = [
            f for f in result
            if f.id == "practitioner.yogas_extended.parivartana.5_9_maha"
        ]
        assert len(maha_findings) == 1


# ---------------------------------------------------------------------------
# Finding envelope
# ---------------------------------------------------------------------------


class TestFindingEnvelope:

    def test_verdict_under_140_chars(self):
        from app.reading.computations.yogas_extended.parivartana import (
            detect_parivartana,
        )

        chart = _chart_with(
            asc_sign=1,
            placements={"Sun": 9, "Jupiter": 5},
        )
        result = detect_parivartana(chart, asc_sign=1)
        for f in result:
            assert len(f.verdict) <= 140

    def test_evidence_contains_doctrine_sentinel(self):
        from app.reading.computations.yogas_extended.parivartana import (
            detect_parivartana,
        )

        chart = _chart_with(
            asc_sign=1,
            placements={"Sun": 9, "Jupiter": 5},
        )
        result = detect_parivartana(chart, asc_sign=1)
        assert result
        for f in result:
            doctrine = next(
                (e for e in f.evidence if e.startswith("doctrine=")), None
            )
            assert doctrine is not None
            assert "Parivartana" in doctrine or "BPHS" in doctrine

    def test_confidence_is_indicative_only(self):
        from app.reading.computations.yogas_extended.parivartana import (
            detect_parivartana,
        )

        chart = _chart_with(
            asc_sign=1,
            placements={"Sun": 9, "Jupiter": 5},
        )
        [finding] = [
            f for f in detect_parivartana(chart, asc_sign=1)
            if f.id.endswith("_maha")
        ]
        assert finding.confidence.band == "indicative_only"
        assert finding.confidence.score == 0.0
