"""Tests for ``app.reading.computations.marriage_trigger``.

Doctrine source: Sanjay Rath's *Crux of Vedic Astrology* (UL + 7L + D9
dispositor compound rule) layered with classical Parashari transit
triggers (Jupiter/Saturn over natal 7H or 7L).

Algorithm
=========

Marriage fires when:

1. Either the current Mahadasha lord OR the current Antardasha lord is
   in the compound karaka set:
       {7L, planet in 7H, dispositor of 7L, navamsa-lord of 7L,
        dispositor of UL, Venus (M) or Jupiter (F), Darakaraka}

   AND

2. Transit Jupiter OR transit Saturn aspects natal 7H (whole-sign
   Vedic aspect: 7th from aspecter; Jupiter adds 5/9; Saturn adds 3/10).

When both legs fire, direction = "positive" with the verdict naming the
matching karaka and the transiting outer.  When either leg is absent,
direction = "neutral" and the verdict describes what is missing.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _planet(sign: int, *, longitude: float | None = None) -> dict:
    lon = longitude if longitude is not None else (sign - 1) * 30.0 + 15.0
    return {
        "sign": sign,
        "sign_name": "X",
        "longitude": lon,
        "degree_in_sign": lon % 30.0,
        "is_retrograde": False,
    }


def _build_d1(*, asc_sign: int, seven_l_sign: int, venus_sign: int,
              venus_planet: str = "Venus", **extras: int) -> dict:
    """Build a D1 chart with controllable 7H, 7L, Venus, and dispositor.

    asc_sign: ascendant sign (1-indexed).
    seven_l_sign: the sign where the 7th-house lord sits.
    venus_sign: where Venus sits.
    extras: additional {planet_name: sign} overrides.
    """
    from app.core.dignity import SIGN_RULERS

    seventh_sign = ((asc_sign - 1) + 6) % 12 + 1
    seven_lord = SIGN_RULERS[seventh_sign]

    placements = {
        "Sun":     1,
        "Moon":    4,
        "Mars":    3,
        "Mercury": 5,
        "Jupiter": 9,
        "Venus":   venus_sign,
        "Saturn":  10,
        "Rahu":    7,
        "Ketu":    1,
    }
    placements[seven_lord] = seven_l_sign  # ensure 7L lands where caller asks
    placements.update(extras)               # allow overrides

    chart = {name: _planet(s) for name, s in placements.items()}
    return chart


def _build_d9(d1_chart: dict) -> dict:
    """Cheap D9: deterministic copy of D1 for tests where D9 dispositor
    correctness is not the focus. Tests that *do* care override the
    navamsa lord of 7L explicitly."""
    return {name: dict(pos) for name, pos in d1_chart.items()}


def _build_arudha_padas_with_ul(ul_sign: int) -> dict:
    """Minimal arudha-pada dict for the marriage trigger to consume.

    Only the ``ul`` entry's evidence is read for the dispositor-of-UL
    check; everything else can be opaque.
    """
    from app.reading.schema import ConfidenceScore, Finding

    conf = ConfidenceScore(
        score=0.0,
        votes={"house": False, "lord": False, "karaka": False},
        band="indicative_only",
    )
    ul_finding = Finding(
        id="primitive.arudha.ul",
        rule="arudha_upapada",
        source_sequence=None,
        classification="primitive",
        direction="neutral",
        verdict="UL placeholder",
        evidence=[f"pada_sign={ul_sign}"],
        confidence=conf,
    )
    return {"ul": ul_finding}


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------


class TestShape:

    def test_returns_finding(self):
        from app.reading.computations.marriage_trigger import (
            compute_marriage_trigger,
        )
        from app.reading.schema import Finding

        # asc=Aries(1), 7H=Libra(7), 7L=Venus.
        # Place Venus in Libra so 7L sits in own sign 7. (dispositor=Venus too.)
        d1 = _build_d1(asc_sign=1, seven_l_sign=7, venus_sign=7)
        d9 = _build_d9(d1)
        padas = _build_arudha_padas_with_ul(ul_sign=7)
        finding = compute_marriage_trigger(
            d1_chart=d1,
            d9_chart=d9,
            asc_sign=1,
            moon_sign=4,
            arudha_padas=padas,
            current_md_lord="Venus",       # in karaka set => leg 1 fires
            current_ad_lord="Sun",
            transit_jupiter_sign=1,        # 7th from Libra => aspects 7H
            transit_saturn_sign=4,
            is_male=True,
        )
        assert isinstance(finding, Finding)

    def test_id_pin(self):
        from app.reading.computations.marriage_trigger import (
            compute_marriage_trigger,
        )

        d1 = _build_d1(asc_sign=1, seven_l_sign=7, venus_sign=7)
        d9 = _build_d9(d1)
        padas = _build_arudha_padas_with_ul(ul_sign=7)
        finding = compute_marriage_trigger(
            d1_chart=d1, d9_chart=d9, asc_sign=1, moon_sign=4,
            arudha_padas=padas,
            current_md_lord="Venus", current_ad_lord="Sun",
            transit_jupiter_sign=1, transit_saturn_sign=4,
            is_male=True,
        )
        assert finding.id == "practitioner.marriage_trigger.compound"

    def test_classification_is_trigger(self):
        from app.reading.computations.marriage_trigger import (
            compute_marriage_trigger,
        )

        d1 = _build_d1(asc_sign=1, seven_l_sign=7, venus_sign=7)
        d9 = _build_d9(d1)
        padas = _build_arudha_padas_with_ul(ul_sign=7)
        finding = compute_marriage_trigger(
            d1_chart=d1, d9_chart=d9, asc_sign=1, moon_sign=4,
            arudha_padas=padas,
            current_md_lord="Venus", current_ad_lord="Sun",
            transit_jupiter_sign=1, transit_saturn_sign=4,
            is_male=True,
        )
        assert finding.classification == "trigger"

    def test_verdict_under_140(self):
        from app.reading.computations.marriage_trigger import (
            compute_marriage_trigger,
        )

        d1 = _build_d1(asc_sign=1, seven_l_sign=7, venus_sign=7)
        d9 = _build_d9(d1)
        padas = _build_arudha_padas_with_ul(ul_sign=7)
        finding = compute_marriage_trigger(
            d1_chart=d1, d9_chart=d9, asc_sign=1, moon_sign=4,
            arudha_padas=padas,
            current_md_lord="Venus", current_ad_lord="Sun",
            transit_jupiter_sign=1, transit_saturn_sign=4,
            is_male=True,
        )
        assert len(finding.verdict) <= 140


# ---------------------------------------------------------------------------
# Compound trigger ACTIVE (both legs fire).
# ---------------------------------------------------------------------------


class TestCompoundTriggerActive:

    def test_md_venus_plus_jupiter_aspects_7h(self):
        from app.reading.computations.marriage_trigger import (
            compute_marriage_trigger,
        )

        d1 = _build_d1(asc_sign=1, seven_l_sign=7, venus_sign=7)
        d9 = _build_d9(d1)
        padas = _build_arudha_padas_with_ul(ul_sign=7)
        finding = compute_marriage_trigger(
            d1_chart=d1, d9_chart=d9, asc_sign=1, moon_sign=4,
            arudha_padas=padas,
            current_md_lord="Venus",
            current_ad_lord="Sun",
            transit_jupiter_sign=1,   # Aries, 7th from Libra (=7H)
            transit_saturn_sign=5,
            is_male=True,
        )
        assert finding.direction == "positive"

    def test_ad_seven_lord_plus_saturn_aspect(self):
        """AD = 7L (Venus); transit Saturn in Cancer (4) 10th from Libra
        (sign 7) -> Saturn aspect 3/10 hits 7H."""
        from app.reading.computations.marriage_trigger import (
            compute_marriage_trigger,
        )

        d1 = _build_d1(asc_sign=1, seven_l_sign=7, venus_sign=7)
        d9 = _build_d9(d1)
        padas = _build_arudha_padas_with_ul(ul_sign=7)
        finding = compute_marriage_trigger(
            d1_chart=d1, d9_chart=d9, asc_sign=1, moon_sign=4,
            arudha_padas=padas,
            current_md_lord="Sun",        # Sun is NOT in karaka set...
            current_ad_lord="Venus",      # but AD Venus IS (=7L)
            transit_jupiter_sign=12,      # Jupiter does not aspect 7H
            transit_saturn_sign=10,       # Capricorn -> 10th from Libra? 10-7+1=4, no.
                                          # We want a Saturn aspect to sign 7. Saturn's 3/10
                                          # aspects from sign S hit (S+2)%12+1 and (S+9)%12+1
                                          # plus 7th (S+6). So Saturn at sign X hits sign 7
                                          # when X = 5, 10, or 1. Saturn at 5 -> 7th aspect
                                          # to 11; 3rd aspect to 7. So Saturn at 5 works.
                                          # Easiest: Saturn at sign 1 (Aries) -> 7th aspect
                                          # hits Libra.
            is_male=True,
        )
        # Use Saturn at 5 to test the 3rd aspect path.
        finding = compute_marriage_trigger(
            d1_chart=d1, d9_chart=d9, asc_sign=1, moon_sign=4,
            arudha_padas=padas,
            current_md_lord="Sun",
            current_ad_lord="Venus",
            transit_jupiter_sign=12,
            transit_saturn_sign=5,
            is_male=True,
        )
        assert finding.direction == "positive"


# ---------------------------------------------------------------------------
# Compound trigger INACTIVE (one or both legs absent).
# ---------------------------------------------------------------------------


class TestCompoundTriggerInactive:

    def test_md_ad_neither_in_karaka_set(self):
        from app.reading.computations.marriage_trigger import (
            compute_marriage_trigger,
        )

        d1 = _build_d1(asc_sign=1, seven_l_sign=7, venus_sign=7)
        d9 = _build_d9(d1)
        padas = _build_arudha_padas_with_ul(ul_sign=7)
        # Karaka set for this fixture computes to {Venus, Rahu, Sun}
        # (7L+dispositor+UL-dispositor+natural-karaka all collapse onto
        # Venus; Rahu sits in 7H; Sun is the Darakaraka). Mars and Moon
        # are NOT in the set, so an MD Mars / AD Moon should miss leg 1.
        finding = compute_marriage_trigger(
            d1_chart=d1, d9_chart=d9, asc_sign=1, moon_sign=4,
            arudha_padas=padas,
            current_md_lord="Mars",
            current_ad_lord="Moon",
            transit_jupiter_sign=1,
            transit_saturn_sign=5,
            is_male=True,
        )
        assert finding.direction == "neutral"

    def test_md_venus_but_no_transit_aspect(self):
        from app.reading.computations.marriage_trigger import (
            compute_marriage_trigger,
        )

        d1 = _build_d1(asc_sign=1, seven_l_sign=7, venus_sign=7)
        d9 = _build_d9(d1)
        padas = _build_arudha_padas_with_ul(ul_sign=7)
        # MD Venus passes leg 1; but Jupiter at sign 2 (Taurus): aspects
        # 7th (sign 8), 5th (sign 6), 9th (sign 10). None is 7. Saturn at
        # sign 2: aspects 7th (8), 3rd (4), 10th (11). None is 7.
        finding = compute_marriage_trigger(
            d1_chart=d1, d9_chart=d9, asc_sign=1, moon_sign=4,
            arudha_padas=padas,
            current_md_lord="Venus",
            current_ad_lord="Sun",
            transit_jupiter_sign=2,
            transit_saturn_sign=2,
            is_male=True,
        )
        assert finding.direction == "neutral"


# ---------------------------------------------------------------------------
# Karaka set membership: each sub-member by itself activates leg 1.
# ---------------------------------------------------------------------------


class TestKarakaSet:

    def test_natural_karaka_venus_male(self):
        """Male charts use Venus as natural karaka of marriage."""
        from app.reading.computations.marriage_trigger import (
            compute_marriage_trigger,
        )

        d1 = _build_d1(asc_sign=1, seven_l_sign=7, venus_sign=7)
        d9 = _build_d9(d1)
        padas = _build_arudha_padas_with_ul(ul_sign=7)
        finding = compute_marriage_trigger(
            d1_chart=d1, d9_chart=d9, asc_sign=1, moon_sign=4,
            arudha_padas=padas,
            current_md_lord="Venus",
            current_ad_lord="Sun",
            transit_jupiter_sign=1, transit_saturn_sign=5,
            is_male=True,
        )
        assert finding.direction == "positive"

    def test_natural_karaka_jupiter_female(self):
        """Female charts use Jupiter as natural karaka of marriage."""
        from app.reading.computations.marriage_trigger import (
            compute_marriage_trigger,
        )

        d1 = _build_d1(asc_sign=1, seven_l_sign=7, venus_sign=8)
        d9 = _build_d9(d1)
        padas = _build_arudha_padas_with_ul(ul_sign=7)
        # MD Jupiter (female natural karaka), Venus not in 7L set here
        # (we placed Venus at 8, 7L still Venus because Aries asc -> 7H
        # is Libra). Actually 7L = Venus regardless of Venus' sign. So
        # Jupiter at MD must trigger via the female-natural-karaka rule
        # alone. To make this unambiguous we use AD Sun (not in set).
        finding = compute_marriage_trigger(
            d1_chart=d1, d9_chart=d9, asc_sign=1, moon_sign=4,
            arudha_padas=padas,
            current_md_lord="Jupiter",
            current_ad_lord="Sun",
            transit_jupiter_sign=1,
            transit_saturn_sign=5,
            is_male=False,
        )
        assert finding.direction == "positive"


# ---------------------------------------------------------------------------
# Evidence + verdict mention what fired.
# ---------------------------------------------------------------------------


class TestEvidenceAndVerdict:

    def test_evidence_lists_compound_match(self):
        from app.reading.computations.marriage_trigger import (
            compute_marriage_trigger,
        )

        d1 = _build_d1(asc_sign=1, seven_l_sign=7, venus_sign=7)
        d9 = _build_d9(d1)
        padas = _build_arudha_padas_with_ul(ul_sign=7)
        finding = compute_marriage_trigger(
            d1_chart=d1, d9_chart=d9, asc_sign=1, moon_sign=4,
            arudha_padas=padas,
            current_md_lord="Venus",
            current_ad_lord="Sun",
            transit_jupiter_sign=1, transit_saturn_sign=5,
            is_male=True,
        )
        blob = " ".join(finding.evidence).lower()
        assert "venus" in blob
        assert any(s in blob for s in ("jupiter", "saturn"))

    def test_verdict_says_active_when_positive(self):
        from app.reading.computations.marriage_trigger import (
            compute_marriage_trigger,
        )

        d1 = _build_d1(asc_sign=1, seven_l_sign=7, venus_sign=7)
        d9 = _build_d9(d1)
        padas = _build_arudha_padas_with_ul(ul_sign=7)
        finding = compute_marriage_trigger(
            d1_chart=d1, d9_chart=d9, asc_sign=1, moon_sign=4,
            arudha_padas=padas,
            current_md_lord="Venus",
            current_ad_lord="Sun",
            transit_jupiter_sign=1, transit_saturn_sign=5,
            is_male=True,
        )
        assert "active" in finding.verdict.lower()


# ---------------------------------------------------------------------------
# Property: never raises on any reasonable input.
# ---------------------------------------------------------------------------


class TestPropertyRobust:

    @pytest.mark.parametrize("transit_j", list(range(1, 13)))
    def test_runs_for_every_transit_jupiter(self, transit_j):
        from app.reading.computations.marriage_trigger import (
            compute_marriage_trigger,
        )

        d1 = _build_d1(asc_sign=1, seven_l_sign=7, venus_sign=7)
        d9 = _build_d9(d1)
        padas = _build_arudha_padas_with_ul(ul_sign=7)
        finding = compute_marriage_trigger(
            d1_chart=d1, d9_chart=d9, asc_sign=1, moon_sign=4,
            arudha_padas=padas,
            current_md_lord="Sun",
            current_ad_lord="Moon",
            transit_jupiter_sign=transit_j,
            transit_saturn_sign=5,
            is_male=True,
        )
        assert finding.id == "practitioner.marriage_trigger.compound"

    @pytest.mark.parametrize("asc", list(range(1, 13)))
    def test_runs_for_every_ascendant(self, asc):
        from app.reading.computations.marriage_trigger import (
            compute_marriage_trigger,
        )
        from app.core.dignity import SIGN_RULERS

        # 7H = (asc - 1 + 6) % 12 + 1; 7L = SIGN_RULERS[7H]
        seven_sign = ((asc - 1) + 6) % 12 + 1
        seven_lord = SIGN_RULERS[seven_sign]
        d1 = _build_d1(asc_sign=asc, seven_l_sign=seven_sign, venus_sign=seven_sign)
        d9 = _build_d9(d1)
        padas = _build_arudha_padas_with_ul(ul_sign=seven_sign)
        finding = compute_marriage_trigger(
            d1_chart=d1, d9_chart=d9, asc_sign=asc, moon_sign=4,
            arudha_padas=padas,
            current_md_lord=seven_lord,
            current_ad_lord="Sun",
            transit_jupiter_sign=asc,    # always 7th aspect to 7H from asc
            transit_saturn_sign=5,
            is_male=True,
        )
        assert finding.id == "practitioner.marriage_trigger.compound"
