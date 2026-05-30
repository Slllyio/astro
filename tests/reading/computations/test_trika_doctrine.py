"""Tests for ``app.reading.computations.trika_doctrine``.

Doctrine source: Vipareeta Raja Yoga — classical Parashari + Sanjay Rath
synthesis (the "negation of negation" rule). When two trika lords (the
lords of the 6th, 8th, and 12th houses) are in PARIVARTANA (mutual
exchange) AND neither participates with the lagna lord, the cumulative
misfortune flips into Vipareeta Raja Yoga — a reversal-yoga.

Algorithm
=========

1. Identify the lagna lord and the three trika lords (6L, 8L, 12L) for
   the given ``asc_sign``.
2. For each pair of trika lords (6L+8L, 6L+12L, 8L+12L), check
   parivartana: lord A sits in lord B's house AND lord B sits in lord
   A's house.
3. Lagna-lord exclusion: the lagna lord must NOT be in either of the
   exchanged houses — otherwise the yoga is contaminated and demoted to
   a non-Vipareeta exchange.

Fixture pattern
===============

Charts are built programmatically: an asc_sign + per-planet houses map
yields a minimal d1_chart compatible with the detector.
"""
from __future__ import annotations

import pytest


def _planet_in_house(asc_sign: int, target_house: int) -> int:
    """Return the 1..12 sign that places a planet in ``target_house`` from
    the given asc_sign."""
    return ((asc_sign + target_house - 2) % 12) + 1


def _planet_dict(sign: int) -> dict:
    return {"sign": sign, "longitude": (sign - 1) * 30.0 + 15.0}


def _chart_with(asc_sign: int, placements: dict[str, int]) -> dict:
    """Build a d1_chart with each planet in the requested house."""
    chart: dict[str, dict] = {}
    benign_sign = asc_sign  # 1st house default
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


class TestDetectTrikaShape:

    def test_returns_list(self):
        from app.reading.computations.trika_doctrine import detect_trika_exchanges

        # Empty chart: nothing in exchange.
        result = detect_trika_exchanges(_chart_with(1, {}), asc_sign=1)
        assert isinstance(result, list)

    def test_no_exchange_no_findings(self):
        from app.reading.computations.trika_doctrine import detect_trika_exchanges

        # All planets in 1st house — no exchange possible.
        result = detect_trika_exchanges(_chart_with(1, {}), asc_sign=1)
        assert result == []


# ---------------------------------------------------------------------------
# Aries lagna pin: 6L=Mercury, 8L=Mars, 12L=Jupiter, 1L=Mars (BUT 1L=8L=Mars
# for Aries, so this lagna isn't ideal for testing Mars-as-trika-only).
# Use Cancer lagna: 1L=Moon, 6L=Jupiter, 8L=Saturn, 12L=Mercury — clean.
# ---------------------------------------------------------------------------


class TestCancerLagnaVipareeta:

    def test_jupiter_8_saturn_6_parivartana_detected(self):
        """Cancer: 6L=Jupiter, 8L=Saturn. Jupiter in 8th (Aquarius for Saturn)
        AND Saturn in 6th (Sagittarius for Jupiter) = parivartana."""
        from app.reading.computations.trika_doctrine import detect_trika_exchanges

        chart = _chart_with(
            asc_sign=4,
            placements={
                "Jupiter": 8,   # 6L in 8H
                "Saturn": 6,    # 8L in 6H
                "Moon": 1,      # 1L NOT in 6 or 8 — clean
            },
        )
        result = detect_trika_exchanges(chart, asc_sign=4)
        assert len(result) >= 1
        verdicts = " | ".join(f.verdict for f in result)
        # Pair labelled by lords (Jupiter/6L + Saturn/8L).
        assert "Jupiter" in verdicts and "Saturn" in verdicts

    def test_classification_is_yoga_positive(self):
        from app.reading.computations.trika_doctrine import detect_trika_exchanges

        chart = _chart_with(
            asc_sign=4,
            placements={
                "Jupiter": 8,
                "Saturn": 6,
                "Moon": 1,
            },
        )
        [finding] = detect_trika_exchanges(chart, asc_sign=4)
        assert finding.classification == "yoga"
        assert finding.direction == "positive"

    def test_id_grammar(self):
        from app.reading.computations.trika_doctrine import detect_trika_exchanges

        chart = _chart_with(
            asc_sign=4,
            placements={"Jupiter": 8, "Saturn": 6, "Moon": 1},
        )
        [finding] = detect_trika_exchanges(chart, asc_sign=4)
        # id pattern: practitioner.trika.vipareeta_<lord_pair>
        assert finding.id.startswith("practitioner.trika.vipareeta_")

    def test_verdict_under_140_chars(self):
        from app.reading.computations.trika_doctrine import detect_trika_exchanges

        chart = _chart_with(
            asc_sign=4,
            placements={"Jupiter": 8, "Saturn": 6, "Moon": 1},
        )
        for f in detect_trika_exchanges(chart, asc_sign=4):
            assert len(f.verdict) <= 140


# ---------------------------------------------------------------------------
# Lagna-lord contamination: 1L sitting in either exchanged house must
# DEMOTE the finding (no Vipareeta).
# ---------------------------------------------------------------------------


class TestLagnaLordExclusion:

    def test_lagna_lord_in_6h_blocks_vipareeta(self):
        """Cancer 6L=Jupiter, 8L=Saturn parivartana — but 1L=Moon sits in 6H.
        That contamination blocks the Vipareeta classification."""
        from app.reading.computations.trika_doctrine import detect_trika_exchanges

        chart = _chart_with(
            asc_sign=4,
            placements={
                "Jupiter": 8,
                "Saturn": 6,
                "Moon": 6,   # 1L in 6H — contamination
            },
        )
        result = detect_trika_exchanges(chart, asc_sign=4)
        # The parivartana still exists structurally, but the Vipareeta
        # finding is suppressed.
        assert result == []

    def test_lagna_lord_in_8h_blocks_vipareeta(self):
        from app.reading.computations.trika_doctrine import detect_trika_exchanges

        chart = _chart_with(
            asc_sign=4,
            placements={
                "Jupiter": 8,
                "Saturn": 6,
                "Moon": 8,   # 1L in 8H — contamination
            },
        )
        result = detect_trika_exchanges(chart, asc_sign=4)
        assert result == []


# ---------------------------------------------------------------------------
# 6L+12L variant — exhaustively verify the other pair fires too.
# ---------------------------------------------------------------------------


class TestSecondaryPair:

    def test_aries_lagna_6l_12l_parivartana(self):
        """Aries: 1L=Mars, 6L=Mercury, 12L=Jupiter. (Note: 8L is also Mars,
        same as 1L; we focus on the 6L/12L pair.)

        Mercury in 12H (Pisces) AND Jupiter in 6H (Virgo) is parivartana.
        1L=Mars must avoid both 6 and 12.
        """
        from app.reading.computations.trika_doctrine import detect_trika_exchanges

        chart = _chart_with(
            asc_sign=1,
            placements={
                "Mercury": 12,  # 6L in 12H
                "Jupiter": 6,   # 12L in 6H
                "Mars": 1,      # 1L (and 8L for Aries) safe in 1H
            },
        )
        result = detect_trika_exchanges(chart, asc_sign=1)
        # Should detect Mercury+Jupiter pair.
        assert len(result) >= 1
        verdicts = " | ".join(f.verdict for f in result)
        assert "Mercury" in verdicts and "Jupiter" in verdicts


# ---------------------------------------------------------------------------
# Property: works across all 12 lagnas.
# ---------------------------------------------------------------------------


class TestProperty:

    def test_no_false_positives_on_empty_chart(self):
        """For every lagna, a chart with no exchanges should produce no
        findings."""
        from app.reading.computations.trika_doctrine import detect_trika_exchanges

        for asc_sign in range(1, 13):
            chart = _chart_with(asc_sign, {})
            result = detect_trika_exchanges(chart, asc_sign=asc_sign)
            assert result == [], (
                f"False positive at asc_sign={asc_sign}: {result}"
            )
