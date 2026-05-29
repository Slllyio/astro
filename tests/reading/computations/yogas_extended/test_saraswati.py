"""Tests for ``app.reading.computations.yogas_extended.saraswati``.

Doctrine source: Phaladeepika (Mantreshwara) — Saraswati Yoga.

Classical rule
==============

Saraswati Yoga indicates extreme scholarly, literary, and artistic
talent — the blessings of Saraswati (the goddess of knowledge). It
forms when:

    Mercury, Jupiter, AND Venus all simultaneously occupy a
    **kendra** (1/4/7/10), **kona** (5/9), or the **2nd house**
    (each independently, not necessarily the same house), AND
    at least ONE of the three is in **own sign** or **exaltation**.

So the qualifying-house set is {1, 2, 4, 5, 7, 9, 10}. The yoga
requires all three benefics in this set plus one dignified.

ID grammar
==========

``practitioner.yogas_extended.saraswati.detected``

classification="yoga", direction="positive".

Doctrine echoes
================

Phaladeepika's full Sanskrit verse pins the houses as
"kendra-trikona-dvitiya-sthita" — kendra (1/4/7/10), trikona (5/9),
and dvitiya (2nd). The dignity gate (one of the three in own/exalted)
is stated explicitly in Mantreshwara to distinguish a "full" Saraswati
from a "weak echo" placement (which the brief excludes here).
"""
from __future__ import annotations

import pytest


def _planet_dict(sign: int) -> dict:
    return {"sign": sign, "longitude": (sign - 1) * 30.0 + 15.0}


def _sign_for_house(asc_sign: int, house: int) -> int:
    return ((asc_sign - 1 + house - 1) % 12) + 1


def _chart(asc_sign: int, placements: dict[str, int]) -> dict:
    chart: dict[str, dict] = {}
    for planet in (
        "Sun", "Moon", "Mars", "Mercury", "Jupiter",
        "Venus", "Saturn", "Rahu", "Ketu",
    ):
        # Default benign placement: 3rd house (NOT in qualifying-house set)
        # so non-specified benefics don't accidentally form Saraswati.
        default_sign = _sign_for_house(asc_sign, 3)
        chart[planet] = _planet_dict(placements.get(planet, default_sign))
    return chart


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------


class TestDetectSaraswatiShape:

    def test_returns_list(self):
        from app.reading.computations.yogas_extended.saraswati import detect_saraswati

        result = detect_saraswati(_chart(1, {}), asc_sign=1)
        assert isinstance(result, list)

    def test_no_qualifying_placement_no_yoga(self):
        """All three benefics in 3rd/6th/8th/11th/12th (NOT qualifying)."""
        from app.reading.computations.yogas_extended.saraswati import detect_saraswati

        chart = _chart(asc_sign=1, placements={
            "Mercury": _sign_for_house(1, 3),
            "Jupiter": _sign_for_house(1, 6),
            "Venus":   _sign_for_house(1, 8),
        })
        result = detect_saraswati(chart, asc_sign=1)
        assert result == []

    def test_invalid_asc_sign_raises(self):
        from app.reading.computations.yogas_extended.saraswati import detect_saraswati

        with pytest.raises(ValueError):
            detect_saraswati(_chart(1, {}), asc_sign=0)
        with pytest.raises(ValueError):
            detect_saraswati(_chart(1, {}), asc_sign=13)


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------


class TestSaraswatiDetection:

    def test_all_three_in_kendra_one_in_own_sign(self):
        """Aries lagna. Mercury in 3rd-sign Gemini (own, but Gemini=3H from
        Aries — NOT kendra). Use: place Mercury in 1H (Aries=1) which is
        kendra but not own (not own for Mercury). Better: Place Mercury in
        Virgo (6=own) — Virgo is 6H from Aries = NOT qualifying.

        Cleanest: Aries lagna, place Mercury in 4H = Cancer (4) — kendra.
        Cancer is not Mercury-own/exalted but qualifies as kendra.
        Jupiter in 5H = Leo (5) — kona, not own. Venus in 7H = Libra (7)
        — own. At least one (Venus) in own sign → Saraswati forms."""
        from app.reading.computations.yogas_extended.saraswati import detect_saraswati

        chart = _chart(asc_sign=1, placements={
            "Mercury": 4,   # Cancer — kendra
            "Jupiter": 5,   # Leo — kona
            "Venus":   7,   # Libra — own + kendra
        })
        result = detect_saraswati(chart, asc_sign=1)
        assert len(result) == 1
        assert result[0].id == "practitioner.yogas_extended.saraswati.detected"
        assert result[0].direction == "positive"
        assert result[0].classification == "yoga"

    def test_all_three_qualifying_houses_no_dignity_no_yoga(self):
        """All three in qualifying houses but NONE in own/exalted."""
        from app.reading.computations.yogas_extended.saraswati import detect_saraswati

        chart = _chart(asc_sign=1, placements={
            "Mercury": _sign_for_house(1, 1),   # Aries — not own/exalted
            "Jupiter": _sign_for_house(1, 5),   # Leo — not own/exalted
            "Venus":   _sign_for_house(1, 10),  # Capricorn — not own/exalted
        })
        result = detect_saraswati(chart, asc_sign=1)
        assert result == []

    def test_only_two_in_qualifying_no_yoga(self):
        """Two of three in qualifying — yoga does NOT form."""
        from app.reading.computations.yogas_extended.saraswati import detect_saraswati

        chart = _chart(asc_sign=1, placements={
            "Mercury": _sign_for_house(1, 4),   # kendra
            "Jupiter": _sign_for_house(1, 5),   # kona
            "Venus":   _sign_for_house(1, 6),   # NOT qualifying
        })
        result = detect_saraswati(chart, asc_sign=1)
        assert result == []

    def test_jupiter_exalted_one_qualifies(self):
        """Jupiter exalted in Cancer (4H from Aries=kendra). Mercury &
        Venus also in qualifying houses."""
        from app.reading.computations.yogas_extended.saraswati import detect_saraswati

        chart = _chart(asc_sign=1, placements={
            "Jupiter": 4,    # Cancer — exalted AND kendra
            "Mercury": _sign_for_house(1, 5),   # 5H kona
            "Venus":   _sign_for_house(1, 2),   # 2H (qualifying)
        })
        result = detect_saraswati(chart, asc_sign=1)
        assert len(result) == 1

    def test_two_in_2nd_house(self):
        """Phaladeepika allows 2H. Two benefics in 2H, one in kona."""
        from app.reading.computations.yogas_extended.saraswati import detect_saraswati

        # Aries lagna, 2H = Taurus (2). Venus in 2H = Taurus = own.
        chart = _chart(asc_sign=1, placements={
            "Mercury": 2,   # 2H from Aries
            "Jupiter": 2,   # 2H
            "Venus":   2,   # 2H = Taurus = own for Venus
        })
        result = detect_saraswati(chart, asc_sign=1)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# Finding envelope
# ---------------------------------------------------------------------------


class TestFindingEnvelope:

    def test_verdict_under_140_chars(self):
        from app.reading.computations.yogas_extended.saraswati import detect_saraswati

        chart = _chart(asc_sign=1, placements={
            "Mercury": 4, "Jupiter": 5, "Venus": 7,
        })
        result = detect_saraswati(chart, asc_sign=1)
        for f in result:
            assert len(f.verdict) <= 140

    def test_evidence_contains_doctrine_sentinel(self):
        from app.reading.computations.yogas_extended.saraswati import detect_saraswati

        chart = _chart(asc_sign=1, placements={
            "Mercury": 4, "Jupiter": 5, "Venus": 7,
        })
        result = detect_saraswati(chart, asc_sign=1)
        for f in result:
            doctrine = next(
                (e for e in f.evidence if e.startswith("doctrine=")),
                None,
            )
            assert doctrine is not None
            assert "Phaladeepika" in doctrine or "Saraswati" in doctrine

    def test_confidence_is_indicative_only(self):
        from app.reading.computations.yogas_extended.saraswati import detect_saraswati

        chart = _chart(asc_sign=1, placements={
            "Mercury": 4, "Jupiter": 5, "Venus": 7,
        })
        [finding] = detect_saraswati(chart, asc_sign=1)
        assert finding.confidence.band == "indicative_only"
