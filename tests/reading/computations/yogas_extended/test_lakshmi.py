"""Tests for ``app.reading.computations.yogas_extended.lakshmi``.

Doctrine source: BPHS Ch.40 — Lakshmi Yoga.

Classical rule
==============

Lakshmi Yoga is a "fortune" yoga indicating great prosperity, wealth,
and material blessings. The yoga forms when:

    The 9th-house lord (Bhagyesh / 9L) is in **exaltation, own sign,
    or moolatrikona**, AND Venus (the karaka of Lakshmi / fortune) is
    in **exaltation, own sign, or moolatrikona**.

A **stricter sub-variant** (locked here as ``lakshmi.strict``):

    The 9L is also placed in the 9th house itself AND Venus is in
    own/exalted dignity in a kendra (1/4/7/10) or kona (5/9) from
    lagna.

Variants
========

- ``practitioner.yogas_extended.lakshmi.detected`` — primary detection:
  9L dignified + Venus dignified.
- ``practitioner.yogas_extended.lakshmi.strict`` — primary AND 9L in 9H
  AND Venus in kendra/kona.

If strict fires, the primary `detected` is suppressed (highest tier
wins). If only primary fires, only `detected` is emitted.

ID grammar
==========

``practitioner.yogas_extended.lakshmi.detected``
``practitioner.yogas_extended.lakshmi.strict``

classification="yoga", direction="positive".

Doctrine
========

Sign rulers (BPHS Vol.I Ch.3):

    1 Aries → Mars        7 Libra → Venus
    2 Taurus → Venus      8 Scorpio → Mars
    3 Gemini → Mercury    9 Sagittarius → Jupiter
    4 Cancer → Moon      10 Capricorn → Saturn
    5 Leo → Sun          11 Aquarius → Saturn
    6 Virgo → Mercury    12 Pisces → Jupiter

Exaltation signs (BPHS Vol.I Ch.3 v.50–55):
    Sun=Aries, Moon=Taurus, Mars=Cap, Mercury=Virgo, Jupiter=Cancer,
    Venus=Pisces, Saturn=Libra.

Own signs:
    Sun=Leo, Moon=Cancer, Mars=Aries/Scorpio, Mercury=Gemini/Virgo,
    Jupiter=Sagittarius/Pisces, Venus=Taurus/Libra, Saturn=Cap/Aquarius.

Moolatrikona (BPHS Vol.I Ch.3 v.31–32) — degree-stripped form:
    Sun=Leo, Moon=Taurus, Mars=Aries, Mercury=Virgo, Jupiter=Sagittarius,
    Venus=Libra, Saturn=Aquarius.
"""
from __future__ import annotations

import pytest


def _planet_dict(sign: int) -> dict:
    return {"sign": sign, "longitude": (sign - 1) * 30.0 + 15.0}


def _chart(asc_sign: int, placements: dict[str, int]) -> dict:
    chart: dict[str, dict] = {}
    for planet in (
        "Sun", "Moon", "Mars", "Mercury", "Jupiter",
        "Venus", "Saturn", "Rahu", "Ketu",
    ):
        chart[planet] = _planet_dict(placements.get(planet, asc_sign))
    return chart


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------


class TestDetectLakshmiShape:

    def test_returns_list(self):
        from app.reading.computations.yogas_extended.lakshmi import detect_lakshmi

        result = detect_lakshmi(_chart(1, {}), asc_sign=1)
        assert isinstance(result, list)

    def test_no_yoga_when_both_planets_undignified(self):
        from app.reading.computations.yogas_extended.lakshmi import detect_lakshmi

        # Aries lagna: 9L=Jupiter. Put Jupiter+Venus in undignified signs.
        chart = _chart(asc_sign=1, placements={
            "Jupiter": 1,  # Aries, not own/exalted/MT for Jupiter
            "Venus": 1,    # Aries, not own/exalted/MT for Venus
        })
        result = detect_lakshmi(chart, asc_sign=1)
        assert result == []

    def test_invalid_asc_sign_raises(self):
        from app.reading.computations.yogas_extended.lakshmi import detect_lakshmi

        with pytest.raises(ValueError):
            detect_lakshmi(_chart(1, {}), asc_sign=0)
        with pytest.raises(ValueError):
            detect_lakshmi(_chart(1, {}), asc_sign=13)


# ---------------------------------------------------------------------------
# Primary variant: 9L dignified + Venus dignified
# ---------------------------------------------------------------------------


class TestLakshmiPrimary:

    def test_aries_lagna_jupiter_exalted_venus_exalted(self):
        """Aries lagna: 9L=Jupiter. Jupiter exalted in Cancer (4),
        Venus exalted in Pisces (12). Lakshmi forms."""
        from app.reading.computations.yogas_extended.lakshmi import detect_lakshmi

        chart = _chart(asc_sign=1, placements={
            "Jupiter": 4,   # exalted
            "Venus": 12,    # exalted
        })
        result = detect_lakshmi(chart, asc_sign=1)
        assert len(result) == 1
        # Either detected or strict — both are positive lakshmi.
        assert result[0].id.startswith("practitioner.yogas_extended.lakshmi.")
        assert result[0].direction == "positive"
        assert result[0].classification == "yoga"

    def test_taurus_lagna_saturn_own_venus_own(self):
        """Taurus lagna (asc=2): 9L=Saturn (Capricorn=10). Place Saturn
        in own sign (10 or 11), Venus in own (2 or 7)."""
        from app.reading.computations.yogas_extended.lakshmi import detect_lakshmi

        chart = _chart(asc_sign=2, placements={
            "Saturn": 10,   # own
            "Venus": 2,     # own (Taurus, which is also lagna)
        })
        result = detect_lakshmi(chart, asc_sign=2)
        assert len(result) == 1

    def test_venus_undignified_no_yoga(self):
        """9L dignified but Venus not dignified → no Lakshmi."""
        from app.reading.computations.yogas_extended.lakshmi import detect_lakshmi

        # Aries lagna, Jupiter exalted but Venus in Gemini (3) = neutral
        chart = _chart(asc_sign=1, placements={
            "Jupiter": 4,
            "Venus": 3,
        })
        result = detect_lakshmi(chart, asc_sign=1)
        assert result == []

    def test_9l_undignified_no_yoga(self):
        """Venus dignified but 9L not dignified → no Lakshmi."""
        from app.reading.computations.yogas_extended.lakshmi import detect_lakshmi

        chart = _chart(asc_sign=1, placements={
            "Jupiter": 1,    # not dignified
            "Venus": 12,     # exalted
        })
        result = detect_lakshmi(chart, asc_sign=1)
        assert result == []


# ---------------------------------------------------------------------------
# Strict sub-variant
# ---------------------------------------------------------------------------


class TestLakshmiStrict:

    def test_strict_9l_in_9h_venus_in_kendra(self):
        """Aries: 9L=Jupiter, 9th house = Sagittarius (9). Place Jupiter
        in Sagittarius (own, in 9H from lagna) and Venus in Pisces (12)
        which is a kona neither — Pisces from Aries = 12H. That's not
        kendra/kona. Try Venus in own sign Libra (7) = 7H = kendra."""
        from app.reading.computations.yogas_extended.lakshmi import detect_lakshmi

        chart = _chart(asc_sign=1, placements={
            "Jupiter": 9,   # own (Sagittarius) AND in 9th house from Aries
            "Venus": 7,     # own (Libra) AND in 7th house = kendra
        })
        result = detect_lakshmi(chart, asc_sign=1)
        assert len(result) == 1
        assert result[0].id == "practitioner.yogas_extended.lakshmi.strict"

    def test_strict_suppresses_primary(self):
        """When strict variant matches, primary 'detected' is suppressed."""
        from app.reading.computations.yogas_extended.lakshmi import detect_lakshmi

        chart = _chart(asc_sign=1, placements={
            "Jupiter": 9,
            "Venus": 7,
        })
        result = detect_lakshmi(chart, asc_sign=1)
        ids = [f.id for f in result]
        assert "practitioner.yogas_extended.lakshmi.detected" not in ids

    def test_primary_only_when_9l_not_in_9h(self):
        """9L+Venus dignified but 9L NOT in 9H — primary `detected`."""
        from app.reading.computations.yogas_extended.lakshmi import detect_lakshmi

        chart = _chart(asc_sign=1, placements={
            "Jupiter": 4,   # exalted (Cancer = 4H from Aries, kendra) — not 9H
            "Venus": 12,    # exalted (Pisces = 12H from Aries, not kendra/kona)
        })
        result = detect_lakshmi(chart, asc_sign=1)
        # Jupiter not in 9H so cannot be strict. So primary.
        assert len(result) == 1
        assert result[0].id == "practitioner.yogas_extended.lakshmi.detected"


# ---------------------------------------------------------------------------
# Finding envelope
# ---------------------------------------------------------------------------


class TestFindingEnvelope:

    def test_verdict_under_140_chars(self):
        from app.reading.computations.yogas_extended.lakshmi import detect_lakshmi

        chart = _chart(asc_sign=1, placements={"Jupiter": 4, "Venus": 12})
        result = detect_lakshmi(chart, asc_sign=1)
        for f in result:
            assert len(f.verdict) <= 140

    def test_evidence_contains_doctrine_sentinel(self):
        from app.reading.computations.yogas_extended.lakshmi import detect_lakshmi

        chart = _chart(asc_sign=1, placements={"Jupiter": 4, "Venus": 12})
        result = detect_lakshmi(chart, asc_sign=1)
        for f in result:
            assert any(
                e.startswith("doctrine=") and ("BPHS" in e or "Lakshmi" in e)
                for e in f.evidence
            )

    def test_confidence_is_indicative_only(self):
        from app.reading.computations.yogas_extended.lakshmi import detect_lakshmi

        chart = _chart(asc_sign=1, placements={"Jupiter": 4, "Venus": 12})
        [finding] = detect_lakshmi(chart, asc_sign=1)
        assert finding.confidence.band == "indicative_only"
