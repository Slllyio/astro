"""Tests for ``app.reading.computations.yogas_extended.chamara``.

Doctrine source: Phaladeepika (Mantreshwara) — Chamara Yoga.

Classical rule
==============

Chamara Yoga (also called Royal-Chamara) confers regal status,
authoritative power, and lasting eminence. It forms when:

    The **lagna lord (1L)** is in **exaltation** AND placed in a
    **kendra** (1/4/7/10) from lagna, AND **Jupiter** either
    **conjoins** the 1L (same sign) OR **fully aspects** the 1L by
    drishti.

Jupiter's full drishti (BPHS Ch.26): 5th, 7th, and 9th houses from
Jupiter's own position (whole-sign). So Jupiter at sign S fully
aspects signs (S+4) mod 12, (S+6) mod 12, and (S+8) mod 12 (1-indexed).

Edge cases
==========

- 1L in own sign only (NOT exalted) — yoga does NOT form.
- 1L exalted but in 3H/6H (not kendra) — yoga does NOT form.
- 1L exalted in kendra but Jupiter neither conjoins nor aspects —
  yoga does NOT form.
- Jupiter aspecting the 1L means: 1L_sign is in Jupiter's aspect set
  AND Jupiter is in a different sign from 1L (else "conjunction"
  branch applies).

ID grammar
==========

``practitioner.yogas_extended.chamara.detected``

classification="yoga", direction="positive".
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
        # Default: a safe non-interfering placement.
        # Putting Jupiter at 3H so it doesn't accidentally aspect 1L.
        if planet == "Jupiter":
            default_sign = _sign_for_house(asc_sign, 3)
        else:
            default_sign = asc_sign
        chart[planet] = _planet_dict(placements.get(planet, default_sign))
    return chart


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------


class TestDetectChamaraShape:

    def test_returns_list(self):
        from app.reading.computations.yogas_extended.chamara import detect_chamara

        result = detect_chamara(_chart(1, {}), asc_sign=1)
        assert isinstance(result, list)

    def test_no_yoga_when_1l_not_exalted(self):
        """1L not exalted — no Chamara."""
        from app.reading.computations.yogas_extended.chamara import detect_chamara

        chart = _chart(asc_sign=1, placements={
            "Mars": 1,   # Aries — own but not exalted
        })
        result = detect_chamara(chart, asc_sign=1)
        assert result == []

    def test_invalid_asc_sign_raises(self):
        from app.reading.computations.yogas_extended.chamara import detect_chamara

        with pytest.raises(ValueError):
            detect_chamara(_chart(1, {}), asc_sign=0)
        with pytest.raises(ValueError):
            detect_chamara(_chart(1, {}), asc_sign=13)


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------


class TestChamaraDetection:

    def test_aries_lagna_mars_exalted_10h_jupiter_conjunct(self):
        """Aries: 1L=Mars. Mars exalted in Capricorn (10) which is 10H
        from Aries (kendra). Jupiter in Cap (10) too = conjunction."""
        from app.reading.computations.yogas_extended.chamara import detect_chamara

        chart = _chart(asc_sign=1, placements={
            "Mars": 10,      # Capricorn = exalted, 10H kendra
            "Jupiter": 10,   # same sign as Mars = conjunction
        })
        result = detect_chamara(chart, asc_sign=1)
        assert len(result) == 1
        assert result[0].id == "practitioner.yogas_extended.chamara.detected"
        assert result[0].direction == "positive"
        assert result[0].classification == "yoga"

    def test_aries_lagna_mars_exalted_jupiter_aspects(self):
        """Mars exalted in Cap (10H kendra). Jupiter in 4H (Cancer=4).
        Jupiter's 7th aspect from Cancer (4) = Capricorn (10) — aspects Mars."""
        from app.reading.computations.yogas_extended.chamara import detect_chamara

        chart = _chart(asc_sign=1, placements={
            "Mars": 10,     # exalted in 10H kendra
            "Jupiter": 4,   # Cancer; 7th aspect from Cancer = Capricorn
        })
        result = detect_chamara(chart, asc_sign=1)
        assert len(result) == 1

    def test_no_yoga_jupiter_does_not_aspect(self):
        """Mars exalted in 10H kendra but Jupiter neither conjoins nor
        aspects (e.g. Jupiter in 11H = Aquarius for Aries asc; Aquarius
        to Capricorn distance = 11 steps, not in {5,7,9} ahead)."""
        from app.reading.computations.yogas_extended.chamara import detect_chamara

        chart = _chart(asc_sign=1, placements={
            "Mars": 10,
            "Jupiter": 11,   # Aquarius
        })
        # Jupiter at Aquarius (11) aspects: 5th = Gemini (3), 7th = Leo (5),
        # 9th = Libra (7). Mars at Capricorn (10) NOT aspected.
        result = detect_chamara(chart, asc_sign=1)
        assert result == []

    def test_no_yoga_1l_exalted_not_in_kendra(self):
        """1L exalted but NOT in a kendra → no Chamara.

        Cancer: 1L=Moon. Moon exalted in Taurus (2). Taurus is 11H from
        Cancer (not a kendra) — 1, 4, 7, 10 are kendras; Taurus from
        Cancer = 11H, not kendra. Yoga should not form."""
        from app.reading.computations.yogas_extended.chamara import detect_chamara

        chart = _chart(asc_sign=4, placements={
            "Moon": 2,      # exalted in Taurus but Taurus=11H from Cancer
            "Jupiter": 4,   # same sign as lagna — would aspect but moot
        })
        result = detect_chamara(chart, asc_sign=4)
        assert result == []

    def test_cancer_moon_exalted_in_kendra_jupiter_aspects(self):
        """Cancer lagna: 1L=Moon. Place Moon exalted in Taurus (2). For
        kendra: kendra signs from Cancer are Cancer (1), Libra (4),
        Capricorn (7), Aries (10). Taurus = 11H — NOT kendra. So we
        cannot test Cancer with exalted Moon at Taurus.

        Use Pisces lagna: 1L=Jupiter. Jupiter exalted in Cancer (4). For
        Pisces lagna, Cancer = 5H = NOT kendra. So this doesn't work
        either.

        Leo lagna: 1L=Sun. Sun exalted in Aries (1). Aries from Leo =
        9H = kona, not kendra. Doesn't work.

        Scorpio lagna: 1L=Mars. Mars exalted Cap (10). Cap from Scorpio
        (8) = 3H. Not kendra. Doesn't work.

        Sagittarius lagna: 1L=Jupiter. Jupiter exalted Cancer (4). Cancer
        from Sag (9) = 8H. Not kendra. Doesn't work.

        Aries lagna works (Mars exalted in Cap which IS 10H kendra).
        Libra lagna: 1L=Venus. Venus exalted in Pisces (12). Pisces from
        Libra (7) = 6H. Not kendra.

        Capricorn: 1L=Saturn. Saturn exalted in Libra (7). Libra from Cap
        (10) = 10H kendra! YES."""
        from app.reading.computations.yogas_extended.chamara import detect_chamara

        # Capricorn lagna: 1L=Saturn exalted in Libra (7), 10H kendra.
        # Jupiter conjoining at Libra (7).
        chart = _chart(asc_sign=10, placements={
            "Saturn": 7,
            "Jupiter": 7,   # same sign — conjunction
        })
        result = detect_chamara(chart, asc_sign=10)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# Finding envelope
# ---------------------------------------------------------------------------


class TestFindingEnvelope:

    def test_verdict_under_140_chars(self):
        from app.reading.computations.yogas_extended.chamara import detect_chamara

        chart = _chart(asc_sign=1, placements={"Mars": 10, "Jupiter": 10})
        result = detect_chamara(chart, asc_sign=1)
        for f in result:
            assert len(f.verdict) <= 140

    def test_evidence_contains_doctrine_sentinel(self):
        from app.reading.computations.yogas_extended.chamara import detect_chamara

        chart = _chart(asc_sign=1, placements={"Mars": 10, "Jupiter": 10})
        result = detect_chamara(chart, asc_sign=1)
        for f in result:
            doctrine = next(
                (e for e in f.evidence if e.startswith("doctrine=")), None
            )
            assert doctrine is not None
            assert "Phaladeepika" in doctrine or "Chamara" in doctrine

    def test_confidence_is_indicative_only(self):
        from app.reading.computations.yogas_extended.chamara import detect_chamara

        chart = _chart(asc_sign=1, placements={"Mars": 10, "Jupiter": 10})
        [finding] = detect_chamara(chart, asc_sign=1)
        assert finding.confidence.band == "indicative_only"

    def test_evidence_records_1l_and_jupiter_interaction(self):
        from app.reading.computations.yogas_extended.chamara import detect_chamara

        chart = _chart(asc_sign=1, placements={"Mars": 10, "Jupiter": 10})
        [finding] = detect_chamara(chart, asc_sign=1)
        ev_str = " | ".join(finding.evidence)
        assert "Mars" in ev_str
        assert "Jupiter" in ev_str
        # Should indicate conjunction vs aspect.
        assert (
            "conjunction" in ev_str.lower()
            or "aspect" in ev_str.lower()
        )
