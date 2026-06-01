"""Tests for ``app.reading.computations.yogas_extended.neech_bhanga``.

Doctrine source: D-11 lockfile — BPHS Vol.I Ch.39 v.10 primary rule.

Primary rule (the ONLY trigger for a positive cancellation Finding)
====================================================================

A debilitated planet P (sitting in its debilitation sign S) has its
debilitation cancelled when:

    The **rashi-lord (dispositor) of sign S** sits in a kendra
    (1st / 4th / 7th / 10th) from either the Lagna OR the natal Moon.

Example: Saturn debilitated in Aries. Aries-lord = Mars. If Mars sits in
a kendra from Lagna or Moon, Neech Bhanga fires for Saturn.

Supplementary rules (CITED IN EVIDENCE, NEVER SOLELY TRIGGER)
=============================================================

If the primary rule is satisfied, these are additionally flagged in
evidence when also true:

- The lord of P's exaltation sign sits in a kendra from P's depositor.
- The exaltation-lord (planet whose exaltation IS S) sits in a kendra
  from Lagna or Moon.
- P aspects (or conjoins) its own debilitation-sign lord.

These three never independently trigger a Finding — they are only
supplementary evidence when the primary rule already holds.

ID grammar
==========

``practitioner.yogas_extended.neech_bhanga.<planet>``

One Finding per debilitated planet whose debilitation is cancelled by
the primary rule. classification="yoga", direction="positive".
"""
from __future__ import annotations

import pytest


# Map planet → its debilitation sign (BPHS).
_DEBILITATION: dict[str, int] = {
    "Sun":     7,    # Libra
    "Moon":    8,    # Scorpio
    "Mars":    4,    # Cancer
    "Mercury": 12,   # Pisces
    "Jupiter": 10,   # Capricorn
    "Venus":   6,    # Virgo
    "Saturn":  1,    # Aries
}


def _planet_in_house(asc_sign: int, target_house: int) -> int:
    return ((asc_sign + target_house - 2) % 12) + 1


def _planet_dict(sign: int) -> dict:
    return {"sign": sign, "longitude": (sign - 1) * 30.0 + 15.0}


def _chart_with(
    asc_sign: int,
    moon_sign: int,
    placements: dict[str, int],
) -> dict:
    """``placements`` keyed by planet → SIGN (1..12). Moon is forced to
    moon_sign. Unspecified planets default to asc_sign."""
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
# Shape
# ---------------------------------------------------------------------------


class TestDetectNeechBhangaShape:

    def test_returns_list(self):
        from app.reading.computations.yogas_extended.neech_bhanga import (
            detect_neech_bhanga,
        )

        result = detect_neech_bhanga(
            _chart_with(1, 1, {}), asc_sign=1, moon_sign=1,
        )
        assert isinstance(result, list)

    def test_invalid_asc_sign_raises(self):
        from app.reading.computations.yogas_extended.neech_bhanga import (
            detect_neech_bhanga,
        )

        with pytest.raises(ValueError):
            detect_neech_bhanga(
                _chart_with(1, 1, {}), asc_sign=0, moon_sign=1,
            )
        with pytest.raises(ValueError):
            detect_neech_bhanga(
                _chart_with(1, 1, {}), asc_sign=13, moon_sign=1,
            )

    def test_invalid_moon_sign_raises(self):
        from app.reading.computations.yogas_extended.neech_bhanga import (
            detect_neech_bhanga,
        )

        with pytest.raises(ValueError):
            detect_neech_bhanga(
                _chart_with(1, 1, {}), asc_sign=1, moon_sign=0,
            )

    def test_no_debilitated_planet_no_finding(self):
        from app.reading.computations.yogas_extended.neech_bhanga import (
            detect_neech_bhanga,
        )

        # All planets in 1st house (asc=1 → Aries). Saturn in Aries IS
        # debilitated, so place it in Taurus (2) to avoid spurious deb.
        chart = _chart_with(
            asc_sign=1, moon_sign=1,
            placements={"Saturn": 2},
        )
        result = detect_neech_bhanga(chart, asc_sign=1, moon_sign=1)
        assert result == []


# ---------------------------------------------------------------------------
# Primary rule — dispositor of debilitation sign in kendra from Lagna or Moon
# ---------------------------------------------------------------------------


class TestPrimaryRule:

    def test_saturn_deb_mars_in_10H_from_lagna_fires(self):
        """Saturn deb. in Aries (1). Aries-lord = Mars. Mars in 10H from
        Lagna (Aries asc → 10H = Capricorn = sign 10). Kendra → cancel."""
        from app.reading.computations.yogas_extended.neech_bhanga import (
            detect_neech_bhanga,
        )

        chart = _chart_with(
            asc_sign=1, moon_sign=1,
            placements={
                "Saturn": 1,   # Aries — debilitation
                "Mars":   10,  # Capricorn = 10H from Aries asc (kendra)
            },
        )
        result = detect_neech_bhanga(chart, asc_sign=1, moon_sign=1)
        ids = [f.id for f in result]
        assert "practitioner.yogas_extended.neech_bhanga.Saturn" in ids

    def test_saturn_deb_mars_in_4H_from_moon_fires(self):
        """Saturn in Aries (deb.). Mars in 4H from Moon (kendra-from-Moon
        is sufficient even if not kendra-from-Lagna)."""
        from app.reading.computations.yogas_extended.neech_bhanga import (
            detect_neech_bhanga,
        )

        # Place Moon at sign 7 (Libra). 4H from Moon (Libra) = Capricorn (10).
        chart = _chart_with(
            asc_sign=1, moon_sign=7,
            placements={
                "Saturn": 1,
                "Mars":   10,  # 4H from Moon(Libra)
            },
        )
        result = detect_neech_bhanga(chart, asc_sign=1, moon_sign=7)
        ids = [f.id for f in result]
        assert "practitioner.yogas_extended.neech_bhanga.Saturn" in ids

    def test_saturn_deb_mars_NOT_in_kendra_no_finding(self):
        """Saturn deb. in Aries. Mars in 3rd from Lagna and 3rd from Moon
        (not kendra from either) → NO cancellation."""
        from app.reading.computations.yogas_extended.neech_bhanga import (
            detect_neech_bhanga,
        )

        # Mars in sign 3 (Gemini) = 3H from Aries asc; Moon at 1 (Aries) →
        # 3H from Moon also.
        chart = _chart_with(
            asc_sign=1, moon_sign=1,
            placements={
                "Saturn": 1,
                "Mars":   3,
            },
        )
        result = detect_neech_bhanga(chart, asc_sign=1, moon_sign=1)
        assert result == []

    def test_jupiter_deb_saturn_in_kendra_fires(self):
        """Jupiter deb. in Capricorn (10). Capricorn-lord = Saturn. Place
        Saturn in 7H from Lagna (Aries asc → 7H = Libra = 7)."""
        from app.reading.computations.yogas_extended.neech_bhanga import (
            detect_neech_bhanga,
        )

        chart = _chart_with(
            asc_sign=1, moon_sign=1,
            placements={
                "Jupiter": 10,  # Capricorn — deb.
                "Saturn":  7,   # Libra = 7H from Aries asc (kendra)
            },
        )
        result = detect_neech_bhanga(chart, asc_sign=1, moon_sign=1)
        ids = [f.id for f in result]
        assert "practitioner.yogas_extended.neech_bhanga.Jupiter" in ids


# ---------------------------------------------------------------------------
# Supplementary rules — flagged in evidence ONLY when primary holds
# ---------------------------------------------------------------------------


class TestSupplementaryRulesFlagged:

    def test_supplementary_evidence_includes_exaltation_lord_kendra(self):
        """Saturn deb. in Aries. Aries' exalted-of-Aries planet = Sun.
        Place Sun in 7H from Lagna (kendra). Mars (primary trigger) also
        in 10H. Supplementary should be cited."""
        from app.reading.computations.yogas_extended.neech_bhanga import (
            detect_neech_bhanga,
        )

        chart = _chart_with(
            asc_sign=1, moon_sign=1,
            placements={
                "Saturn": 1,
                "Mars":   10,   # primary kendra
                "Sun":    7,    # supp — Sun exalts in Aries; in kendra
            },
        )
        result = detect_neech_bhanga(chart, asc_sign=1, moon_sign=1)
        saturn = next(
            (f for f in result
             if f.id == "practitioner.yogas_extended.neech_bhanga.Saturn"),
            None,
        )
        assert saturn is not None
        supp = [e for e in saturn.evidence if e.startswith("supplementary_")]
        assert supp, "expected at least one supplementary evidence entry"

    def test_supplementary_alone_does_not_trigger(self):
        """Saturn deb. in Aries. Sun (exalts-in-Aries) in 7H from Lagna
        (a supplementary-rule-only condition). Mars (primary) NOT in
        kendra. Result: no Finding (supplementary alone does NOT trigger)."""
        from app.reading.computations.yogas_extended.neech_bhanga import (
            detect_neech_bhanga,
        )

        # Note: Sun at sign 7 (Libra) is itself debilitated. Sun's
        # dispositor = Venus. Place Venus in a non-kendra (3H = Gemini)
        # so Sun's OWN primary rule cannot fire either.
        chart = _chart_with(
            asc_sign=1, moon_sign=1,
            placements={
                "Saturn": 1,
                "Mars":   3,   # 3H — not kendra
                "Sun":    7,   # supp condition only (and itself deb.)
                "Venus":  3,   # Venus in 3H — neutralises Sun's primary
            },
        )
        result = detect_neech_bhanga(chart, asc_sign=1, moon_sign=1)
        assert result == []


# ---------------------------------------------------------------------------
# Finding envelope
# ---------------------------------------------------------------------------


class TestFindingEnvelope:

    def test_verdict_under_140_chars(self):
        from app.reading.computations.yogas_extended.neech_bhanga import (
            detect_neech_bhanga,
        )

        chart = _chart_with(
            asc_sign=1, moon_sign=1,
            placements={"Saturn": 1, "Mars": 10},
        )
        result = detect_neech_bhanga(chart, asc_sign=1, moon_sign=1)
        for f in result:
            assert len(f.verdict) <= 140

    def test_evidence_contains_doctrine_sentinel(self):
        from app.reading.computations.yogas_extended.neech_bhanga import (
            detect_neech_bhanga,
        )

        chart = _chart_with(
            asc_sign=1, moon_sign=1,
            placements={"Saturn": 1, "Mars": 10},
        )
        result = detect_neech_bhanga(chart, asc_sign=1, moon_sign=1)
        assert result
        for f in result:
            doctrine = next(
                (e for e in f.evidence if e.startswith("doctrine=")), None
            )
            assert doctrine is not None
            assert "BPHS" in doctrine and ("Ch.39" in doctrine or "D-11" in doctrine)

    def test_classification_yoga_and_positive(self):
        from app.reading.computations.yogas_extended.neech_bhanga import (
            detect_neech_bhanga,
        )

        chart = _chart_with(
            asc_sign=1, moon_sign=1,
            placements={"Saturn": 1, "Mars": 10},
        )
        result = detect_neech_bhanga(chart, asc_sign=1, moon_sign=1)
        assert result
        for f in result:
            assert f.classification == "yoga"
            assert f.direction == "positive"

    def test_confidence_is_indicative_only(self):
        from app.reading.computations.yogas_extended.neech_bhanga import (
            detect_neech_bhanga,
        )

        chart = _chart_with(
            asc_sign=1, moon_sign=1,
            placements={"Saturn": 1, "Mars": 10},
        )
        [finding] = detect_neech_bhanga(chart, asc_sign=1, moon_sign=1)
        assert finding.confidence.band == "indicative_only"
        assert finding.confidence.score == 0.0
