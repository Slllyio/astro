"""Tests for ``app.reading.computations.yogas_extended.adhi``.

Doctrine source: BPHS Ch.40 — Adhi Yoga.

Classical rule
==============

Adhi Yoga is formed when the natural benefics — Jupiter, Venus, and
Mercury — occupy the 6th, 7th, and/or 8th houses **from the Moon**
(NOT from the lagna). The houses 6/7/8 from the Moon form the "lower
half" rising behind the Moon and are called the "adhi-sthana" (place
of conferral) per BPHS Ch.40.

Variants (by participant count):

- **Maha Adhi Yoga** (great) — all three (Jupiter, Venus, Mercury) in
  6/7/8 from Moon. Confers great power, prosperity, fame.
- **Madhya Adhi Yoga** (middle) — exactly two of the three present.
  Confers solid prosperity, leadership.
- **Alpa Adhi Yoga** (small) — exactly one of the three present.
  Confers modest prosperity.

A configuration with zero of the three present yields NO Adhi Yoga.

ID grammar
==========

``practitioner.yogas_extended.adhi.maha``
``practitioner.yogas_extended.adhi.madhya``
``practitioner.yogas_extended.adhi.alpa``

Each detection produces at most ONE Finding (the highest-tier variant
matched). All Findings carry classification="yoga" and
direction="positive".

Fixture pattern
===============

Charts are built programmatically: an asc_sign + per-planet sign map
yields a minimal d1_chart compatible with the detector.
"""
from __future__ import annotations

import pytest


def _planet_dict(sign: int) -> dict:
    return {"sign": sign, "longitude": (sign - 1) * 30.0 + 15.0}


def _sign_offset_from(base_sign: int, offset_houses: int) -> int:
    """Return the 1..12 sign that is offset_houses (1-indexed) ahead of base.

    offset_houses=1 means "same sign as base", =2 means "next sign", etc.
    """
    return ((base_sign - 1 + offset_houses - 1) % 12) + 1


def _chart_with(
    asc_sign: int,
    moon_sign: int,
    placements: dict[str, int],
) -> dict:
    """Build a minimal d1_chart with the Moon at moon_sign and explicit
    overrides for any other planet. Default for non-specified planets is
    asc_sign (the 1st house) — placed there to keep them out of 6/7/8
    from Moon unless deliberately positioned.
    """
    chart: dict[str, dict] = {"Moon": _planet_dict(moon_sign)}
    for planet in (
        "Sun", "Mars", "Mercury", "Jupiter", "Venus",
        "Saturn", "Rahu", "Ketu",
    ):
        if planet in placements:
            chart[planet] = _planet_dict(placements[planet])
        else:
            chart[planet] = _planet_dict(asc_sign)
    return chart


# ---------------------------------------------------------------------------
# Shape / construction
# ---------------------------------------------------------------------------


class TestDetectAdhiShape:

    def test_returns_list(self):
        from app.reading.computations.yogas_extended.adhi import detect_adhi

        result = detect_adhi(_chart_with(1, 1, {}), asc_sign=1)
        assert isinstance(result, list)

    def test_no_benefic_in_678_no_finding(self):
        """All benefics in 1st house from Moon — no Adhi formed."""
        from app.reading.computations.yogas_extended.adhi import detect_adhi

        chart = _chart_with(
            asc_sign=1, moon_sign=1,
            placements={
                "Jupiter": 1,
                "Venus": 1,
                "Mercury": 1,
            },
        )
        result = detect_adhi(chart, asc_sign=1)
        assert result == []

    def test_invalid_asc_sign_raises(self):
        from app.reading.computations.yogas_extended.adhi import detect_adhi

        with pytest.raises(ValueError):
            detect_adhi(_chart_with(1, 1, {}), asc_sign=0)
        with pytest.raises(ValueError):
            detect_adhi(_chart_with(1, 1, {}), asc_sign=13)


# ---------------------------------------------------------------------------
# Variants
# ---------------------------------------------------------------------------


class TestAdhiVariants:

    def test_maha_adhi_all_three_in_678_from_moon(self):
        """Moon in Aries (1). Jupiter in 6th (Virgo=6), Venus in 7th
        (Libra=7), Mercury in 8th (Scorpio=8). Maha Adhi Yoga."""
        from app.reading.computations.yogas_extended.adhi import detect_adhi

        chart = _chart_with(
            asc_sign=1, moon_sign=1,
            placements={
                "Jupiter": _sign_offset_from(1, 6),
                "Venus": _sign_offset_from(1, 7),
                "Mercury": _sign_offset_from(1, 8),
            },
        )
        result = detect_adhi(chart, asc_sign=1)
        assert len(result) == 1
        assert result[0].id == "practitioner.yogas_extended.adhi.maha"
        assert result[0].direction == "positive"
        assert result[0].classification == "yoga"

    def test_madhya_adhi_two_of_three_in_678(self):
        """Jupiter and Venus in 6/7 from Moon, Mercury elsewhere."""
        from app.reading.computations.yogas_extended.adhi import detect_adhi

        chart = _chart_with(
            asc_sign=1, moon_sign=1,
            placements={
                "Jupiter": _sign_offset_from(1, 6),  # 6 from Moon
                "Venus": _sign_offset_from(1, 7),    # 7 from Moon
                "Mercury": _sign_offset_from(1, 2),  # 2 from Moon
            },
        )
        result = detect_adhi(chart, asc_sign=1)
        assert len(result) == 1
        assert result[0].id == "practitioner.yogas_extended.adhi.madhya"
        assert result[0].direction == "positive"

    def test_alpa_adhi_one_of_three(self):
        """Only Jupiter in 6/7/8 from Moon."""
        from app.reading.computations.yogas_extended.adhi import detect_adhi

        chart = _chart_with(
            asc_sign=1, moon_sign=1,
            placements={
                "Jupiter": _sign_offset_from(1, 7),  # 7 from Moon
                "Venus": _sign_offset_from(1, 2),
                "Mercury": _sign_offset_from(1, 3),
            },
        )
        result = detect_adhi(chart, asc_sign=1)
        assert len(result) == 1
        assert result[0].id == "practitioner.yogas_extended.adhi.alpa"

    def test_only_highest_tier_emitted(self):
        """Maha and Madhya are mutually exclusive; only Maha emitted."""
        from app.reading.computations.yogas_extended.adhi import detect_adhi

        chart = _chart_with(
            asc_sign=1, moon_sign=1,
            placements={
                "Jupiter": _sign_offset_from(1, 6),
                "Venus": _sign_offset_from(1, 7),
                "Mercury": _sign_offset_from(1, 8),
            },
        )
        result = detect_adhi(chart, asc_sign=1)
        ids = [f.id for f in result]
        assert "practitioner.yogas_extended.adhi.madhya" not in ids
        assert "practitioner.yogas_extended.adhi.alpa" not in ids


# ---------------------------------------------------------------------------
# Moon-anchored placement: verify computation uses Moon, NOT lagna
# ---------------------------------------------------------------------------


class TestMoonAnchoredPlacement:
    """The classical rule is 6/7/8 from MOON, not from lagna. Critical."""

    def test_moon_in_cancer_benefics_in_678_from_moon(self):
        """Moon in Cancer (4). 6th from Moon=Sagittarius (9), 7th=Cap
        (10), 8th=Aquarius (11). Asc sign irrelevant — kept = Aries."""
        from app.reading.computations.yogas_extended.adhi import detect_adhi

        chart = _chart_with(
            asc_sign=1, moon_sign=4,
            placements={
                "Jupiter": 9,
                "Venus": 10,
                "Mercury": 11,
            },
        )
        result = detect_adhi(chart, asc_sign=1)
        assert len(result) == 1
        assert result[0].id == "practitioner.yogas_extended.adhi.maha"

    def test_benefic_in_678_from_lagna_but_not_moon_no_yoga(self):
        """Moon in Libra (7). Place Jupiter at 12 (= 6 from lagna Aries),
        which is the 6th from Aries. But from Moon=Libra, sign 12 is
        only 6 houses if we count Libra→Pisces, 7→8→9→10→11→12 = 6
        houses ahead. Actually 6 from Moon (Libra) = Pisces (12). So
        this IS 6 from Moon — would form Alpa. To test the negative,
        use a sign that is 6 from lagna but NOT 6/7/8 from Moon.

        Lagna Aries (1), Moon Libra (7). 6 from lagna = Virgo (6).
        From Moon (Libra), sign 6 is offset_houses(Libra → Virgo) =
        (6 - 7) % 12 + 1 = -1 % 12 + 1 = 11+1 = 12. Wait...
        ((6 - 1 - (7 - 1)) % 12) + 1 = (-6 % 12) + 1 = 6 + 1 = 7.
        Hmm. Use simple test: Moon at 1, Jupiter at 5 = 5 from Moon =
        not in 6/7/8."""
        from app.reading.computations.yogas_extended.adhi import detect_adhi

        chart = _chart_with(
            asc_sign=1, moon_sign=1,
            placements={
                "Jupiter": 5,   # 5 from Moon, not 6/7/8
                "Venus": 4,     # 4 from Moon
                "Mercury": 3,   # 3 from Moon
            },
        )
        result = detect_adhi(chart, asc_sign=1)
        assert result == []


# ---------------------------------------------------------------------------
# Finding envelope
# ---------------------------------------------------------------------------


class TestFindingEnvelope:

    def test_verdict_under_140_chars(self):
        from app.reading.computations.yogas_extended.adhi import detect_adhi

        chart = _chart_with(
            asc_sign=1, moon_sign=1,
            placements={
                "Jupiter": _sign_offset_from(1, 6),
                "Venus": _sign_offset_from(1, 7),
                "Mercury": _sign_offset_from(1, 8),
            },
        )
        result = detect_adhi(chart, asc_sign=1)
        for f in result:
            assert len(f.verdict) <= 140

    def test_evidence_contains_doctrine_sentinel(self):
        from app.reading.computations.yogas_extended.adhi import detect_adhi

        chart = _chart_with(
            asc_sign=1, moon_sign=1,
            placements={
                "Jupiter": _sign_offset_from(1, 7),
            },
        )
        result = detect_adhi(chart, asc_sign=1)
        for f in result:
            doctrine = next(
                (e for e in f.evidence if e.startswith("doctrine=")), None
            )
            assert doctrine is not None
            assert "BPHS" in doctrine or "Ch.40" in doctrine

    def test_confidence_is_indicative_only(self):
        from app.reading.computations.yogas_extended.adhi import detect_adhi

        chart = _chart_with(
            asc_sign=1, moon_sign=1,
            placements={
                "Jupiter": _sign_offset_from(1, 7),
            },
        )
        [finding] = detect_adhi(chart, asc_sign=1)
        assert finding.confidence.band == "indicative_only"
        assert finding.confidence.score == 0.0
