"""Yoga-layer tests: every YogaRecord citation resolves to a real on-disk corpus
line (same guard pattern as test_rule_sets.py), and each encoded yoga fires on a
positive synthetic chart and stays silent on a negative one.

All synthetic charts use ``RamanChart.from_stated_positions`` with Aries lagna
(asc_lon=0.0): whole-sign house h spans lon [(h-1)*30, h*30).
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine.sources import verify
from app.raman_saab.doctrine.yogas import (
    YOGAS, FiredYoga, YogaRecord, detect_yogas, has_yoga)

_VALID_KINDS = {"raja", "dhana", "arishta", "lunar", "other"}


def _chart(lons: dict[str, float], asc_lon: float = 0.0) -> RamanChart:
    return RamanChart.from_stated_positions(
        {p: {"lon": l, "bhava": 1} for p, l in lons.items()},
        asc_lon=asc_lon, ayanamsa="raman")


def _yoga(yid: str) -> YogaRecord:
    return next(y for y in YOGAS if y.id == yid)


# ── registry guards (spec §5.4 pattern) ──────────────────────────────────────
@pytest.mark.parametrize("yoga", list(YOGAS), ids=lambda y: y.id)
def test_every_yoga_cites_a_real_corpus_line(yoga):
    """Every YogaRecord citation must resolve to an on-disk corpus line."""
    assert verify(yoga.source), (
        f"{yoga.id} cites {yoga.source} which does not resolve on disk")


@pytest.mark.parametrize("yoga", list(YOGAS), ids=lambda y: y.id)
def test_every_yoga_is_well_formed(yoga):
    """Each record has a condition, a non-empty effect, and a valid kind."""
    assert yoga.condition is not None
    assert yoga.effect.strip()
    assert yoga.kind in _VALID_KINDS


def test_yoga_ids_are_unique():
    """No duplicate ids in the YOGAS registry."""
    ids = [y.id for y in YOGAS]
    assert len(ids) == len(set(ids))


# ── lunar yogas ──────────────────────────────────────────────────────────────
class TestGajakesari:
    @pytest.mark.parametrize("n,jup_lon", [(1, 40.0), (4, 125.0), (7, 215.0), (10, 305.0)])
    def test_jupiter_in_each_kendra_from_moon_fires(self, n, jup_lon):
        """Jupiter in the 1st/4th/7th/10th from the Moon forms Gajakesari (3HC:1589)."""
        chart = _chart({"Moon": 35.0, "Jupiter": jup_lon})
        moon_h = chart.planets["Moon"].rasi_house
        jup_h = chart.planets["Jupiter"].rasi_house
        assert ((jup_h - moon_h) % 12) + 1 == n, "fixture must place Jupiter in the n-th from Moon"
        assert _yoga("Y.GAJAKESARI").fires(chart) is True

    def test_jupiter_in_second_from_moon_does_not_fire(self):
        """Jupiter in the 2nd from the Moon is not a kendra — no Gajakesari."""
        assert _yoga("Y.GAJAKESARI").fires(_chart({"Moon": 35.0, "Jupiter": 65.0})) is False


class TestSunapha:
    def test_mars_in_second_from_moon_fires(self):
        """A non-Sun planet in the 2nd from the Moon forms Sunapha (3HC:1834)."""
        assert _yoga("Y.SUNAPHA").fires(_chart({"Moon": 35.0, "Mars": 65.0})) is True

    def test_sun_in_second_from_moon_does_not_fire(self):
        """The Sun is explicitly excepted from causing Sunapha."""
        assert _yoga("Y.SUNAPHA").fires(_chart({"Moon": 35.0, "Sun": 65.0})) is False

    def test_node_in_second_from_moon_does_not_fire(self):
        """Chaya-grahas never count as Sunapha occupiers."""
        assert _yoga("Y.SUNAPHA").fires(_chart({"Moon": 35.0, "Rahu": 65.0})) is False


class TestAnapha:
    def test_venus_in_twelfth_from_moon_fires(self):
        """A planet in the 12th from the Moon forms Anapha (3HC:1982)."""
        assert _yoga("Y.ANAPHA").fires(_chart({"Moon": 35.0, "Venus": 5.0})) is True

    def test_planet_in_second_from_moon_does_not_fire(self):
        """A planet only in the 2nd from the Moon is Sunapha, not Anapha."""
        assert _yoga("Y.ANAPHA").fires(_chart({"Moon": 35.0, "Venus": 65.0})) is False


class TestDurudhara:
    def test_planets_on_both_sides_of_moon_fire(self):
        """Planets on either side of the Moon form Durudhara (3HC:2066)."""
        assert _yoga("Y.DURUDHARA").fires(
            _chart({"Moon": 35.0, "Mars": 65.0, "Venus": 5.0})) is True

    def test_one_side_only_does_not_fire(self):
        """A planet on one side only (Sunapha alone) is not Durudhara."""
        assert _yoga("Y.DURUDHARA").fires(_chart({"Moon": 35.0, "Mars": 65.0})) is False


class TestChandramangala:
    def test_moon_mars_conjunction_fires(self):
        """Mars conjoining the Moon forms Chandramangala (3HC:2272)."""
        assert _yoga("Y.CHANDRAMANGALA").fires(_chart({"Moon": 35.0, "Mars": 40.0})) is True

    def test_moon_mars_mutual_aspect_fires(self):
        """Raman extends the yoga to the Moon-Mars mutual aspect (HTJAH-I:2908)."""
        assert _yoga("Y.CHANDRAMANGALA").fires(_chart({"Moon": 35.0, "Mars": 215.0})) is True

    def test_unrelated_moon_and_mars_do_not_fire(self):
        """Moon h2 and Mars h5 neither conjoin nor mutually aspect."""
        assert _yoga("Y.CHANDRAMANGALA").fires(_chart({"Moon": 35.0, "Mars": 125.0})) is False


class TestAdhi:
    def test_benefics_spread_over_6_7_8_from_moon_fire(self):
        """Mercury/Jupiter/Venus in the 6th, 7th and 8th from the Moon (3HC:2442)."""
        assert _yoga("Y.ADHI").fires(_chart(
            {"Moon": 35.0, "Mercury": 185.0, "Jupiter": 215.0, "Venus": 245.0})) is True

    def test_all_benefics_in_one_of_the_three_houses_fire(self):
        """Raman: all of them may be in any one of these signs — still Adhi."""
        assert _yoga("Y.ADHI").fires(_chart(
            {"Moon": 35.0, "Mercury": 215.0, "Jupiter": 218.0, "Venus": 222.0})) is True

    def test_one_benefic_outside_does_not_fire(self):
        """Venus in the 4th from the Moon breaks the full Adhi form."""
        assert _yoga("Y.ADHI").fires(_chart(
            {"Moon": 35.0, "Mercury": 185.0, "Jupiter": 215.0, "Venus": 125.0})) is False


class TestAmala:
    def test_benefic_in_tenth_from_moon_fires(self):
        """Jupiter in the 10th from the Moon forms Amala (3HC:3037)."""
        assert _yoga("Y.AMALA").fires(_chart({"Moon": 35.0, "Jupiter": 305.0})) is True

    def test_benefic_in_tenth_from_lagna_fires(self):
        """A benefic in the 10th from the Lagna also forms Amala."""
        assert _yoga("Y.AMALA").fires(_chart({"Moon": 35.0, "Mercury": 275.0})) is True

    def test_malefic_in_tenth_does_not_fire(self):
        """If no benefic is present (only Saturn/Sun in the 10ths), Amala is not caused."""
        assert _yoga("Y.AMALA").fires(
            _chart({"Moon": 35.0, "Saturn": 305.0, "Sun": 275.0})) is False


# ── arishta yogas ────────────────────────────────────────────────────────────
# Kemadruma-positive base (Aries lagna, Moon h2). The yoga must stand fully
# uncancelled per 3HC:2182-2185, so every other planet sits in houses 6/9/12:
#   * not in h1/h2/h3 -> the Moon stays isolated (formation, 3HC:2172-2174);
#   * not in h1/h4/h7/h10 -> no kendra from the Lagna (and Moon h2 is no kendra);
#   * not in h2/h5/h8/h11 -> no kendra from the Moon;
#   * nothing shares h2 -> no Moon-conjunction (the Sun included);
#   * no benefic drishti on h2 (Mercury/Venus h9 aspect h3; Jupiter h12
#     aspects h4/h6/h8) -> the EXTENDED branch stays silent too.
_KEMADRUMA_BASE = {"Moon": 35.0, "Sun": 155.0, "Mars": 158.0, "Saturn": 165.0,
                   "Mercury": 245.0, "Venus": 250.0, "Jupiter": 335.0}


class TestKemadruma:
    def test_isolated_moon_without_bhanga_fires(self):
        """No planets flanking the Moon and no cancellation -> Kemadruma (3HC:2172)."""
        assert _yoga("Y.KEMADRUMA").fires(_chart(dict(_KEMADRUMA_BASE))) is True

    def test_planet_in_kendra_from_lagna_cancels(self):
        """Saturn in h7 (kendra from the Lagna, 6th from the Moon — NOT a kendra
        from the Moon) isolates the kendra-from-birth branch (3HC:2182-2185)."""
        cancelled = dict(_KEMADRUMA_BASE, Saturn=185.0)
        assert _yoga("Y.KEMADRUMA").fires(_chart(cancelled)) is False

    def test_planet_in_kendra_from_moon_cancels(self):
        """Saturn in h5 (4th from the Moon in h2, NOT a kendra from the Lagna)
        isolates the kendra-from-Moon branch (3HC:2182-2185)."""
        cancelled = dict(_KEMADRUMA_BASE, Saturn=125.0)
        assert _yoga("Y.KEMADRUMA").fires(_chart(cancelled)) is False

    def test_sun_conjunct_moon_cancels(self):
        """The Sun conjunct the Moon does not stop formation (Sun is excluded
        there) but the Moon-conjunct-a-planet clause of 3HC:2182-2185 cancels."""
        cancelled = dict(_KEMADRUMA_BASE, Sun=40.0)
        assert _yoga("Y.KEMADRUMA").fires(_chart(cancelled)) is False

    def test_flanked_moon_does_not_fire(self):
        """Mars in the 2nd from the Moon means the Moon is not isolated at all."""
        assert _yoga("Y.KEMADRUMA").fires(_chart({"Moon": 35.0, "Mars": 65.0})) is False


class TestSakata:
    @pytest.mark.parametrize("n,moon_lon", [(6, 165.0), (8, 215.0), (12, 335.0)])
    def test_moon_in_6_8_12_from_jupiter_fires(self, n, moon_lon):
        """Moon in the 12th, 6th or 8th from Jupiter forms Sakata (3HC:2984)."""
        chart = _chart({"Jupiter": 5.0, "Moon": moon_lon})
        jup_h = chart.planets["Jupiter"].rasi_house
        moon_h = chart.planets["Moon"].rasi_house
        assert ((moon_h - jup_h) % 12) + 1 == n, "fixture must place the Moon in the n-th from Jupiter"
        assert _yoga("Y.SAKATA").fires(chart) is True

    def test_moon_in_seventh_from_jupiter_does_not_fire(self):
        """Moon in the 7th from Jupiter is Gajakesari territory, not Sakata."""
        assert _yoga("Y.SAKATA").fires(_chart({"Jupiter": 5.0, "Moon": 185.0})) is False


# ── raja yogas ───────────────────────────────────────────────────────────────
class TestVipareeta:
    """Aries lagna: 6th lord = Mercury (Virgo), 8th lord = Mars (Scorpio),
    12th lord = Jupiter (Pisces)."""

    def test_dusthana_lords_conjoined_in_dusthana_fires(self):
        """6th and 12th lords conjoined in the 6th -> prosperity (HTJAH-I:6302-6303)."""
        assert _yoga("Y.VIPAREETA").fires(_chart({"Mercury": 155.0, "Jupiter": 160.0})) is True

    def test_eighth_house_variant_fires(self):
        """8th lord in the 8th with the 12th lord mirrors HTJAH-I:15864 (Chart 200 form)."""
        assert _yoga("Y.VIPAREETA").fires(_chart({"Mars": 215.0, "Jupiter": 218.0})) is True

    def test_no_phaladeepika_isolation_clause(self):
        """Extra planets conjoined do NOT break the yoga — Raman states no isolation."""
        assert _yoga("Y.VIPAREETA").fires(_chart(
            {"Mercury": 155.0, "Jupiter": 160.0, "Venus": 158.0, "Sun": 150.0})) is True

    def test_dusthana_lords_conjoined_in_kendra_does_not_fire(self):
        """The same lords conjoined in the Lagna (a kendra) is NOT the Raman form."""
        assert _yoga("Y.VIPAREETA").fires(_chart({"Mercury": 5.0, "Jupiter": 8.0})) is False

    def test_single_dusthana_lord_in_dusthana_does_not_fire(self):
        """One dusthana lord alone in a dusthana does not make the yoga."""
        assert _yoga("Y.VIPAREETA").fires(_chart({"Mercury": 155.0})) is False

    def test_unconjoined_dusthana_lords_do_not_fire(self):
        """Dusthana lords each in a dusthana but NOT conjoined do not fire."""
        assert _yoga("Y.VIPAREETA").fires(_chart({"Mercury": 155.0, "Jupiter": 215.0})) is False


class TestRajaKendraTrikona:
    def test_ninth_and_tenth_lords_conjoined_fires(self):
        """Aries lagna: Jupiter (9th lord) with Saturn (10th lord) in the 4th
        is a kendra-trikona lord association (HTJAH-I:622-626)."""
        assert _yoga("Y.RAJA.KT").fires(_chart({"Jupiter": 95.0, "Saturn": 97.0})) is True

    def test_separated_lords_do_not_fire(self):
        """The same lords unconjoined produce no association Raja yoga."""
        assert _yoga("Y.RAJA.KT").fires(_chart({"Jupiter": 95.0, "Saturn": 275.0})) is False


class TestRaja910Exchange:
    def test_9_10_parivartana_fires(self):
        """Aries lagna: Jupiter (9th lord) in the 10th, Saturn (10th lord) in
        the 9th — exchange confers Raja yoga (HTJAH-I:630-631)."""
        assert _yoga("Y.RAJA.910X").fires(_chart({"Jupiter": 275.0, "Saturn": 245.0})) is True

    def test_ninth_lord_in_tenth_alone_fires(self):
        """HTJAH-I:631-632 second disjunct: the 9th lord in the 10th (no
        exchange — Saturn stays in the 4th) still causes Raja yoga."""
        assert _yoga("Y.RAJA.910X").fires(_chart({"Jupiter": 275.0, "Saturn": 95.0})) is True

    def test_tenth_lord_in_ninth_alone_fires(self):
        """HTJAH-I:631-632 third disjunct: the 10th lord in the 9th (no
        exchange — Jupiter stays in the 5th) still causes Raja yoga."""
        assert _yoga("Y.RAJA.910X").fires(_chart({"Saturn": 245.0, "Jupiter": 125.0})) is True

    def test_lords_in_own_houses_do_not_fire(self):
        """Each lord in its own house is neither exchange nor cross-placement."""
        assert _yoga("Y.RAJA.910X").fires(_chart({"Jupiter": 245.0, "Saturn": 275.0})) is False


class TestRaja910MutualAspect:
    def test_9_10_lords_mutually_aspecting_fire(self):
        """Jupiter in the 4th and Saturn in the 10th cast mutual 7th-house
        drishti — Raja yoga (HTJAH-I:634)."""
        assert _yoga("Y.RAJA.910A").fires(_chart({"Jupiter": 95.0, "Saturn": 275.0})) is True

    def test_one_sided_aspect_does_not_fire(self):
        """Saturn in the 11th does not aspect Jupiter in the 4th — no mutual aspect."""
        assert _yoga("Y.RAJA.910A").fires(_chart({"Jupiter": 95.0, "Saturn": 305.0})) is False


# ── dhana yogas ──────────────────────────────────────────────────────────────
class TestDhanaExchange:
    def test_2_5_lords_exchanged_fires(self):
        """Aries lagna: Sun (5th lord) in the 2nd, Venus (2nd lord) in the 5th
        — exchanged wealth lords (HTJAH-I:2709)."""
        assert _yoga("Y.DHANA.EXCH").fires(_chart({"Sun": 35.0, "Venus": 125.0})) is True

    def test_2_11_lords_exchanged_fires(self):
        """Venus (2nd lord) in the 11th, Saturn (11th lord) in the 2nd."""
        assert _yoga("Y.DHANA.EXCH").fires(_chart({"Venus": 305.0, "Saturn": 35.0})) is True

    def test_lords_in_own_houses_do_not_fire(self):
        """2nd and 5th lords each at home is no exchange."""
        assert _yoga("Y.DHANA.EXCH").fires(_chart({"Venus": 35.0, "Sun": 125.0})) is False


class TestDhana59:
    def test_5th_and_9th_lords_in_own_houses_fire(self):
        """Aries lagna: Sun in the 5th and Jupiter in the 9th (HTJAH-I:2710)."""
        assert _yoga("Y.DHANA.59").fires(_chart({"Sun": 125.0, "Jupiter": 245.0})) is True

    def test_displaced_ninth_lord_does_not_fire(self):
        """Jupiter in the 10th breaks the 5th-and-9th-in-own-houses form."""
        assert _yoga("Y.DHANA.59").fires(_chart({"Sun": 125.0, "Jupiter": 275.0})) is False


class TestDhanaChain:
    @pytest.mark.parametrize("lons", [
        {"Mars": 35.0},      # lagna lord in the 2nd
        {"Venus": 305.0},    # 2nd lord in the 11th
        {"Saturn": 5.0},     # 11th lord in the Lagna
    ], ids=["lagna_lord_in_2", "2nd_lord_in_11", "11th_lord_in_1"])
    def test_each_chain_link_fires(self, lons):
        """Lord of Lagna in the 2nd, 2nd lord in the 11th, or 11th lord in
        Lagna acquires great wealth (HTJAH-I:2480-2481)."""
        assert _yoga("Y.DHANA.CHAIN").fires(_chart(lons)) is True

    def test_no_link_does_not_fire(self):
        """Lagna lord in the 3rd matches no chain link."""
        assert _yoga("Y.DHANA.CHAIN").fires(_chart({"Mars": 65.0})) is False


# ── HPA-20 remaining named yogas (the purely-geometric batch) ─────────────────
class TestSarada:
    """Aries lagna: 10th lord = Saturn, Sun's own sign = Leo (h5)."""

    def test_arm1_jupiter_trine_from_moon_and_mars_trine_from_mercury_fires(self):
        """Jupiter in the 5th from the Moon AND Mars in the 5th from Mercury (HPA-20:106)."""
        assert _yoga("Y.SARADA").fires(
            _chart({"Moon": 35.0, "Jupiter": 165.0, "Mercury": 65.0, "Mars": 195.0})) is True

    def test_arm2_jupiter_in_eleventh_from_mercury_fires(self):
        """Jupiter in the 11th from Mercury is a self-standing Sarada disjunct."""
        assert _yoga("Y.SARADA").fires(_chart({"Mercury": 5.0, "Jupiter": 315.0})) is True

    def test_arm3_tenth_lord_in_fifth_mercury_kendra_sun_own_fires(self):
        """10th lord (Saturn) in the 5th, Mercury in a quadrant, the Sun in his own sign (Leo)."""
        assert _yoga("Y.SARADA").fires(
            _chart({"Saturn": 135.0, "Mercury": 95.0, "Sun": 145.0})) is True

    def test_no_arm_does_not_fire(self):
        """Jupiter conjunct Mercury in the Lagna satisfies none of the three arms."""
        assert _yoga("Y.SARADA").fires(_chart({"Jupiter": 35.0, "Mercury": 35.0})) is False


class TestKusuma:
    """Taurus lagna (asc_lon=30): the four kendras are all fixed signs; h5/h9 are trikonas;
    h10 = Aquarius."""

    def test_venus_fixed_kendra_weak_moon_trine_sun_tenth_fires(self):
        """Venus in a fixed quadrant, a waning Moon in a trine, the Sun in the 10th (HPA-20:200)."""
        assert _yoga("Y.KUSUMA").fires(
            _chart({"Venus": 45.0, "Moon": 165.0, "Sun": 315.0}, asc_lon=30.0)) is True

    def test_waxing_moon_does_not_fire(self):
        """A strong (waxing) Moon fails the 'weak Moon' clause even with the rest intact."""
        assert _yoga("Y.KUSUMA").fires(
            _chart({"Venus": 45.0, "Moon": 45.0, "Sun": 315.0}, asc_lon=30.0)) is False

    def test_sun_outside_tenth_does_not_fire(self):
        """The Sun away from the 10th breaks the yoga."""
        assert _yoga("Y.KUSUMA").fires(
            _chart({"Venus": 45.0, "Moon": 165.0, "Sun": 200.0}, asc_lon=30.0)) is False


class TestBrihadbija:
    """Aries lagna: lagna lord = Mars, 8th house = Scorpio (h8)."""

    def test_arm_a_rahu_mars_saturn_in_lagna_fires(self):
        """Rahu with Mars and Saturn in the ascendant (HPA-20:216)."""
        assert _yoga("Y.BRIHADBIJA").fires(
            _chart({"Rahu": 10.0, "Mars": 12.0, "Saturn": 14.0})) is True

    def test_arm_b_lagna_lord_in_eighth_with_rahu_and_a_malefic_fires(self):
        """Lagna lord (Mars) in the 8th with Rahu and a second malefic (two malefics there)."""
        assert _yoga("Y.BRIHADBIJA").fires(_chart({"Mars": 225.0, "Rahu": 227.0})) is True

    def test_rahu_and_mars_alone_in_lagna_does_not_fire(self):
        """Only two of the three ascendant malefics (Saturn elsewhere) does not form arm A."""
        assert _yoga("Y.BRIHADBIJA").fires(
            _chart({"Rahu": 10.0, "Mars": 12.0, "Saturn": 200.0})) is False


class TestAsatyavadi:
    """Aries lagna: 2nd lord = Venus. The yoga needs Venus' dispositor to be Saturn,
    i.e. Venus in Capricorn or Aquarius."""

    def test_second_lord_dispositor_saturn_fires(self):
        """Venus (the 2nd lord) in Capricorn -> its dispositor is Saturn (HPA-20:225)."""
        assert _yoga("Y.ASATYAVADI").fires(_chart({"Venus": 285.0})) is True

    def test_second_lord_in_own_sign_does_not_fire(self):
        """Venus in Taurus is dispositor-of-self (Venus, not Saturn) -> no yoga."""
        assert _yoga("Y.ASATYAVADI").fires(_chart({"Venus": 35.0})) is False


# ── detection API ────────────────────────────────────────────────────────────
class TestDetectYogas:
    def test_returns_fired_yogas_with_verifying_citations(self):
        """detect_yogas surfaces exactly the active yogas, each with a citation
        that resolves on disk."""
        fired = detect_yogas(_chart({"Mercury": 155.0, "Jupiter": 160.0}))
        assert isinstance(fired, tuple)
        assert all(isinstance(f, FiredYoga) for f in fired)
        # membership, not exact equality: broad sign-level yogas (Nishkapata-205's
        # benefic-4th-sign arm) legitimately co-fire on this two-planet fixture, and an
        # exact-list pin would break on every future broad addition
        assert "Y.VIPAREETA" in [f.id for f in fired]
        assert all(verify(f.source) for f in fired)

    def test_empty_chart_fires_nothing(self):
        """A chart with no planets activates no yoga."""
        assert detect_yogas(_chart({})) == ()

    def test_multiple_yogas_detected_together(self):
        """Moon h2 + Jupiter h5 gives Gajakesari AND (Jupiter being a benefic in
        the 4th from the Moon...) at least the kendra-from-Moon lunar yoga."""
        fired_ids = {f.id for f in detect_yogas(
            _chart({"Moon": 35.0, "Jupiter": 125.0, "Mars": 65.0}))}
        assert "Y.GAJAKESARI" in fired_ids
        assert "Y.SUNAPHA" in fired_ids


class TestHasYoga:
    def test_kind_filter_matches_fired_kind(self):
        """has_yoga reports the Vipareeta chart as raja-bearing but not dhana/arishta."""
        chart = _chart({"Mercury": 155.0, "Jupiter": 160.0})
        assert has_yoga(chart, "raja") is True
        assert has_yoga(chart, "dhana") is False
        assert has_yoga(chart, "arishta") is False

    def test_lunar_kind_detected(self):
        """A Gajakesari chart registers as lunar-yoga-bearing."""
        assert has_yoga(_chart({"Moon": 35.0, "Jupiter": 125.0}), "lunar") is True

    def test_unknown_kind_raises_value_error(self):
        """A kind outside the YogaKind Literal is rejected at runtime."""
        with pytest.raises(ValueError, match="unknown yoga kind"):
            has_yoga(_chart({"Moon": 35.0}), "bogus")  # type: ignore[arg-type]


# ── first 3HC tranche (2026-08-08): each fires on a constructed positive and stays silent on
# a negative — the can-it-produce-the-other-answer discipline, per yoga ──────────────────────
class TestMatsyaYoga:
    def test_fires_on_the_full_occupancy_pattern(self):
        """3HCH:1814 — malefics in 1 and 9; the 5th holds malefics AND benefics; 4 and 8
        occupied by malefics. Aries lagna: Sun H1, Mars H9, Saturn+Jupiter H5, Rahu H4,
        Ketu H8."""
        c = _chart({"Sun": 10.0, "Mars": 250.0, "Saturn": 128.0, "Jupiter": 133.0,
                    "Rahu": 95.0, "Ketu": 275.0, "Moon": 40.0, "Mercury": 70.0,
                    "Venus": 300.0})
        # Ketu must sit in H8 (Scorpio 210-240)
        c = _chart({"Sun": 10.0, "Mars": 250.0, "Saturn": 128.0, "Jupiter": 133.0,
                    "Rahu": 95.0, "Ketu": 215.0, "Moon": 40.0, "Mercury": 70.0,
                    "Venus": 300.0})
        assert _yoga("Y.MATSYA").fires(c)

    def test_silent_without_the_benefic_in_the_fifth(self):
        """Remove the benefic from H5 — the fifth must contain BOTH classes."""
        c = _chart({"Sun": 10.0, "Mars": 250.0, "Saturn": 128.0, "Jupiter": 40.0,
                    "Rahu": 95.0, "Ketu": 215.0, "Moon": 45.0, "Mercury": 70.0,
                    "Venus": 300.0})
        assert not _yoga("Y.MATSYA").fires(c)


class TestRaviYoga:
    def test_fires_sun_in_10th_with_lord_in_3rd_conjunct_saturn(self):
        """3HCH:1982. Leo lagna (asc 120): H10 = Taurus, lord Venus; Venus and Saturn
        together in H3 (Libra); Sun in H10."""
        c = _chart({"Sun": 45.0, "Venus": 190.0, "Saturn": 195.0, "Moon": 130.0,
                    "Mars": 10.0, "Mercury": 70.0, "Jupiter": 250.0}, asc_lon=120.0)
        assert _yoga("Y.RAVI").fires(c)

    def test_silent_when_saturn_is_elsewhere(self):
        c = _chart({"Sun": 45.0, "Venus": 190.0, "Saturn": 280.0, "Moon": 130.0,
                    "Mars": 10.0, "Mercury": 70.0, "Jupiter": 250.0}, asc_lon=120.0)
        assert not _yoga("Y.RAVI").fires(c)


class TestGauriYoga:
    def test_fires_on_the_navamsa_chain(self):
        """3HCH:1637. Aries lagna: 10th lord Saturn at 282.0 — Capricorn, whose navamsa
        cycle starts at Capricorn (movable sign, classical scheme), so 282 falls in the ARIES
        navamsa — its dispositor Mars stands exalted in the 10th and IS the lagna lord,
        satisfying the conjunction by identity."""
        c = _chart({"Saturn": 282.0, "Mars": 272.5, "Sun": 10.0, "Moon": 40.0,
                    "Mercury": 70.0, "Jupiter": 100.0, "Venus": 130.0})
        assert _yoga("Y.GAURI").fires(c)

    def test_silent_when_the_dispositor_leaves_the_10th(self):
        c = _chart({"Saturn": 280.0, "Mars": 40.0, "Sun": 10.0, "Moon": 45.0,
                    "Mercury": 70.0, "Jupiter": 100.0, "Venus": 130.0})
        assert not _yoga("Y.GAURI").fires(c)


class TestBrahmaYoga:
    def test_fires_on_all_three_benefic_kendra_relations(self):
        """3HCH:1931. Aries lagna: Jupiter is itself the 9th lord (1st from itself is a
        kendra by the letter of the text); Venus 4th from Saturn (11th lord); Mercury 7th
        from Mars (lagna lord)."""
        c = _chart({"Jupiter": 250.0, "Saturn": 40.0, "Venus": 130.0, "Mars": 10.0,
                    "Mercury": 190.0, "Sun": 70.0, "Moon": 100.0})
        assert _yoga("Y.BRAHMA").fires(c)

    def test_silent_when_venus_falls_out_of_kendra(self):
        c = _chart({"Jupiter": 250.0, "Saturn": 40.0, "Venus": 70.0, "Mars": 10.0,
                    "Mercury": 190.0, "Sun": 100.0, "Moon": 130.0})
        assert not _yoga("Y.BRAHMA").fires(c)


class TestNishturabhashiYoga:
    """The first yoga encoded from the complete edition's far half (3HCC:10205)."""

    def test_fires_on_moon_saturn_conjunction(self):
        c = _chart({"Moon": 100.0, "Saturn": 105.0, "Jupiter": 40.0, "Sun": 10.0,
                    "Mars": 130.0, "Mercury": 160.0, "Venus": 190.0})
        assert _yoga("Y.NISHTURABHASHI").fires(c)

    def test_jupiters_aspect_neutralises_it(self):
        """Raman's own cancellation in the same passage: Jupiter aspecting the conjunction
        (here from H10, a trine onto H4... whole-sign 9th-aspect H2..; use H12->H4? place
        Jupiter so a 5/7/9 drishti lands on H4) — Jupiter in H10 casts its 7th onto H4."""
        c = _chart({"Moon": 100.0, "Saturn": 105.0, "Jupiter": 280.0, "Sun": 10.0,
                    "Mars": 130.0, "Mercury": 160.0, "Venus": 190.0})
        assert not _yoga("Y.NISHTURABHASHI").fires(c)

    def test_silent_without_the_conjunction(self):
        c = _chart({"Moon": 100.0, "Saturn": 135.0, "Jupiter": 40.0, "Sun": 10.0,
                    "Mars": 160.0, "Mercury": 190.0, "Venus": 220.0})
        assert not _yoga("Y.NISHTURABHASHI").fires(c)


# ── tranche 2 (2026-08-09): Lakshmi measured out of its deferral + the far-half 2nd-house
# block and the Andha pair — same fire/silent discipline per yoga ───────────────────────────
class TestLakshmiYoga:
    """Graduated its deferral by measurement: 26/225 geometric, 12/225 with the B1 gate.
    The synthetic here exercises the GEOMETRIC arm; the strength gate depends on Shadbala,
    which stated-position charts do not carry — so the positive asserts the geometry and the
    negative asserts the dignity clause refuses a mere kendra placement."""

    def test_silent_when_ninth_lord_lacks_dignity(self):
        # Aries lagna: 9th = Sagittarius, lord Jupiter; Jupiter in H7 (Libra) — kendra but
        # neither own nor exalted -> the conjunctive parse must refuse.
        c = _chart({"Jupiter": 190.0, "Mars": 10.0, "Sun": 40.0, "Moon": 70.0,
                    "Mercury": 100.0, "Venus": 130.0, "Saturn": 250.0})
        assert not _yoga("Y.LAKSHMI").fires(c)

    def test_silent_when_dignified_but_out_of_kendra_trikona(self):
        # Jupiter in own Sagittarius but that is H9 for Aries... H9 IS a trikona; use Pisces
        # (H12, own sign, neither kendra nor trikona) instead.
        c = _chart({"Jupiter": 340.0, "Mars": 10.0, "Sun": 40.0, "Moon": 70.0,
                    "Mercury": 100.0, "Venus": 130.0, "Saturn": 250.0})
        assert not _yoga("Y.LAKSHMI").fires(c)


class TestMookaYoga:
    def test_fires_second_lord_in_eighth_with_jupiter(self):
        # Aries lagna: 2nd = Taurus, lord Venus; Venus and Jupiter together in H8 (Scorpio).
        c = _chart({"Venus": 220.0, "Jupiter": 225.0, "Sun": 10.0, "Moon": 40.0,
                    "Mars": 70.0, "Mercury": 100.0, "Saturn": 130.0})
        assert _yoga("Y.MOOKA").fires(c)

    def test_silent_without_jupiter(self):
        c = _chart({"Venus": 220.0, "Jupiter": 100.0, "Sun": 10.0, "Moon": 40.0,
                    "Mars": 70.0, "Mercury": 130.0, "Saturn": 160.0})
        assert not _yoga("Y.MOOKA").fires(c)


class TestNetranasaYoga:
    def test_fires_when_all_three_lords_join_lagna(self):
        """Raman's remark states the arm plainly: the lords of the 2nd, 6th and 10th all in
        the Lagna. Aries: Venus (2nd), Mercury (6th), Saturn (10th) all in H1."""
        c = _chart({"Venus": 10.0, "Mercury": 15.0, "Saturn": 20.0, "Sun": 40.0,
                    "Moon": 70.0, "Mars": 100.0, "Jupiter": 130.0})
        assert _yoga("Y.NETRANASA").fires(c)

    def test_silent_when_one_lord_is_elsewhere(self):
        c = _chart({"Venus": 10.0, "Mercury": 15.0, "Saturn": 250.0, "Sun": 40.0,
                    "Moon": 70.0, "Mars": 100.0, "Jupiter": 130.0})
        assert not _yoga("Y.NETRANASA").fires(c)


class TestSumukhaYoga:
    def test_fires_on_benefics_in_the_second(self):
        c = _chart({"Jupiter": 40.0, "Sun": 10.0, "Moon": 70.0, "Mars": 100.0,
                    "Mercury": 130.0, "Venus": 160.0, "Saturn": 190.0})
        assert _yoga("Y.SUMUKHA").fires(c)

    def test_silent_when_the_second_is_empty_and_lord_unaspected(self):
        # 2nd lord Venus in H3 (not a kendra), 2nd house empty of benefics.
        c = _chart({"Venus": 70.0, "Sun": 10.0, "Moon": 100.0, "Mars": 130.0,
                    "Mercury": 160.0, "Jupiter": 250.0, "Saturn": 190.0})
        assert not _yoga("Y.SUMUKHA").fires(c)


class TestDurmukhaYoga:
    def test_fires_malefic_in_second_with_afflicted_lord(self):
        # Saturn (malefic) in H2; 2nd lord Venus conjunct Mars (evil planet) in H5.
        c = _chart({"Saturn": 40.0, "Venus": 130.0, "Mars": 133.0, "Sun": 10.0,
                    "Moon": 70.0, "Mercury": 100.0, "Jupiter": 250.0})
        assert _yoga("Y.DURMUKHA").fires(c)

    def test_silent_when_the_lord_is_clean(self):
        c = _chart({"Saturn": 40.0, "Venus": 130.0, "Mars": 300.0, "Sun": 10.0,
                    "Moon": 70.0, "Mercury": 100.0, "Jupiter": 250.0})
        assert not _yoga("Y.DURMUKHA").fires(c)


class TestSraddhannabhukthaYoga:
    def test_fires_when_saturn_owns_the_second(self):
        """Sagittarius lagna (asc 240): the 2nd is Capricorn — Saturn's own sign."""
        c = _chart({"Saturn": 100.0, "Sun": 10.0, "Moon": 40.0, "Mars": 70.0,
                    "Mercury": 130.0, "Jupiter": 160.0, "Venus": 190.0}, asc_lon=240.0)
        assert _yoga("Y.SRADDHANNABHUKTHA").fires(c)

    def test_fires_when_saturn_joins_the_second_lord(self):
        # Aries lagna: 2nd lord Venus; Saturn with Venus in H5.
        c = _chart({"Saturn": 130.0, "Venus": 133.0, "Sun": 10.0, "Moon": 40.0,
                    "Mars": 70.0, "Mercury": 100.0, "Jupiter": 250.0})
        assert _yoga("Y.SRADDHANNABHUKTHA").fires(c)

    def test_silent_when_saturn_is_unrelated(self):
        # Aries lagna; Saturn alone in H6 (Virgo): not own-2nd, not with Venus (H5), and from
        # H6 its 3rd/7th/10th aspects land on H8/H12/H3 — never the 2nd.
        c = _chart({"Saturn": 160.0, "Venus": 130.0, "Sun": 10.0, "Moon": 40.0,
                    "Mars": 70.0, "Mercury": 100.0, "Jupiter": 250.0})
        assert not _yoga("Y.SRADDHANNABHUKTHA").fires(c)


class TestAndhaYoga:
    def test_fires_form_288_sun_rahu_rising_with_trikona_malefics(self):
        c = _chart({"Sun": 10.0, "Rahu": 15.0, "Mars": 130.0, "Saturn": 250.0,
                    "Moon": 40.0, "Mercury": 70.0, "Jupiter": 100.0, "Venus": 160.0})
        assert _yoga("Y.ANDHA").fires(c)

    def test_fires_form_289_the_four_malefic_seats(self):
        c = _chart({"Mars": 40.0, "Moon": 160.0, "Saturn": 340.0, "Sun": 220.0,
                    "Mercury": 10.0, "Jupiter": 100.0, "Venus": 130.0})
        assert _yoga("Y.ANDHA").fires(c)

    def test_silent_when_neither_form_holds(self):
        c = _chart({"Sun": 10.0, "Rahu": 40.0, "Mars": 70.0, "Saturn": 100.0,
                    "Moon": 130.0, "Mercury": 160.0, "Jupiter": 190.0, "Venus": 220.0})
        assert not _yoga("Y.ANDHA").fires(c)


class TestSumukha167Arm:
    """Combination 167, graduated when the Gopuramsa primitive landed: the 2nd lord in a
    dignified-or-friendly kendra whose sign-lord attains rung 8 of Raman's ladder."""

    def test_fires_on_the_gopuramsa_chain(self):
        # Aries lagna: 2nd lord Venus in H7 (Libra — own sign, a kendra) at its best seat
        # (180.75: 10 own-vargas, >= 8); the kendra's sign-lord is Venus itself, which
        # therefore attains Gopuramsa. Self-reference satisfies the letter of the text.
        c = _chart({"Venus": 180.75, "Sun": 10.0, "Moon": 40.0, "Mars": 70.0,
                    "Mercury": 100.0, "Jupiter": 130.0, "Saturn": 250.0})
        assert _yoga("Y.SUMUKHA").fires(c)

    def test_silent_when_the_lord_is_out_of_kendra_and_no_other_arm_holds(self):
        # Venus (2nd lord) in H3; 2nd empty of benefics; no benefic aspects Venus from a
        # kendra chain — all three Or-arms must refuse together.
        c = _chart({"Venus": 70.0, "Sun": 10.0, "Moon": 100.0, "Mars": 130.0,
                    "Mercury": 160.0, "Jupiter": 250.0, "Saturn": 190.0})
        assert not _yoga("Y.SUMUKHA").fires(c)


# ── tranche 3 (2026-08-09) ──────────────────────────────────────────────────────────────────
class TestIndraYoga:
    def test_fires_on_the_5_11_exchange_with_moon_in_5th(self):
        # Aries lagna: 5th = Leo (Sun), 11th = Aquarius (Saturn). Sun in H11, Saturn in H5,
        # Moon in H5.
        c = _chart({"Sun": 310.0, "Saturn": 130.0, "Moon": 135.0, "Mars": 10.0,
                    "Mercury": 40.0, "Jupiter": 70.0, "Venus": 100.0})
        assert _yoga("Y.INDRA").fires(c)

    def test_silent_without_the_moon(self):
        c = _chart({"Sun": 310.0, "Saturn": 130.0, "Moon": 40.0, "Mars": 10.0,
                    "Mercury": 45.0, "Jupiter": 70.0, "Venus": 100.0})
        assert not _yoga("Y.INDRA").fires(c)


class TestTrilochanaYoga:
    def test_fires_on_mutual_trines(self):
        # Sun H1, Moon H5, Mars H9 — every pair 1/5/9 apart.
        c = _chart({"Sun": 10.0, "Moon": 130.0, "Mars": 250.0, "Mercury": 40.0,
                    "Jupiter": 70.0, "Venus": 100.0, "Saturn": 160.0})
        assert _yoga("Y.TRILOCHANA").fires(c)

    def test_silent_when_one_falls_out(self):
        c = _chart({"Sun": 10.0, "Moon": 130.0, "Mars": 220.0, "Mercury": 40.0,
                    "Jupiter": 70.0, "Venus": 100.0, "Saturn": 160.0})
        assert not _yoga("Y.TRILOCHANA").fires(c)


class TestKulavardhanaYoga:
    def test_fires_all_seven_in_fifth_from_lagna(self):
        # every graha in H5 (Leo, 120-150)
        lons = {n: 121.0 + i for i, n in enumerate(
            ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"))}
        c = _chart(lons)
        assert _yoga("Y.KULAVARDHANA").fires(c)

    def test_silent_when_one_strays(self):
        lons = {n: 121.0 + i for i, n in enumerate(
            ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus"))}
        lons["Saturn"] = 200.0
        c = _chart(lons)
        assert not _yoga("Y.KULAVARDHANA").fires(c)


class TestVishnuYoga:
    def test_fires_on_the_three_planet_chain_in_the_2nd(self):
        """Aries lagna: 9th lord Jupiter at 34.0 (Taurus = H2; its navamsa there resolves to
        a sign whose lord must also stand in H2 with the 10th lord Saturn)."""
        # Jupiter (9th lord) in H2 at 34.0 -> navamsa: Taurus is fixed; cycle starts 9th from
        # it (Capricorn); 34.0 is the 2nd navamsa -> Aquarius -> dispositor Saturn, who is
        # ALSO the 10th lord — both roles land on one planet, placed in H2.
        c = _chart({"Jupiter": 34.0, "Saturn": 40.0, "Sun": 10.0, "Moon": 70.0,
                    "Mars": 100.0, "Mercury": 130.0, "Venus": 160.0})
        assert _yoga("Y.VISHNU").fires(c)

    def test_silent_when_the_ninth_lord_leaves_the_2nd(self):
        c = _chart({"Jupiter": 250.0, "Saturn": 40.0, "Sun": 10.0, "Moon": 70.0,
                    "Mars": 100.0, "Mercury": 130.0, "Venus": 160.0})
        assert not _yoga("Y.VISHNU").fires(c)


class TestGoYoga:
    """The strength gate rides effective_strength, which stated-position charts cannot carry
    — so the synthetics assert the GEOMETRIC refusals, mirroring the Lakshmi test pattern.

    Plus one FIRE test with the strength gate patched: Y.GO shipped DEAD (2026-08-09 fix) —
    ``dignity_state`` never returns "moolatrikona", so the original gate always refused and
    silence-only tests could not see it. Every strength-gated yoga now needs a patched-gate
    fire proof."""

    def test_fires_when_geometry_holds_and_strength_gate_is_patched(self, monkeypatch):
        """Jupiter 245.0 (Sagittarius 5, inside the 240-250 Moolatrikona range) with 2nd
        lord Venus; lagna lord Mars exalted in Capricorn; strength gate stubbed strong."""
        import app.raman_saab.primitives.effective_strength as es_mod

        class _Strong:
            band = "strong"
            decisively_weak = False

        monkeypatch.setattr(es_mod, "effective_strength", lambda *a, **k: _Strong())
        c = _chart({"Jupiter": 245.0, "Venus": 247.0, "Mars": 280.0, "Sun": 40.0,
                    "Moon": 70.0, "Mercury": 100.0, "Saturn": 130.0})
        assert _yoga("Y.GO").fires(c)

    def test_silent_when_jupiter_is_out_of_moolatrikona(self):
        c = _chart({"Jupiter": 100.0, "Venus": 105.0, "Mars": 280.0, "Sun": 10.0,
                    "Moon": 40.0, "Mercury": 70.0, "Saturn": 130.0})
        assert not _yoga("Y.GO").fires(c)

    def test_silent_when_the_lagna_lord_is_unexalted(self):
        # Jupiter in Moolatrikona (Sagittarius early degrees, H9 for Aries) with 2nd lord
        # Venus beside it — but lagna lord Mars NOT exalted -> must refuse before strength.
        c = _chart({"Jupiter": 245.0, "Venus": 247.0, "Mars": 10.0, "Sun": 40.0,
                    "Moon": 70.0, "Mercury": 100.0, "Saturn": 130.0})
        assert not _yoga("Y.GO").fires(c)


class TestVakchalanaYoga:
    def test_fires_malefic_lord_cruel_navamsa_unrelieved_second(self):
        """Capricorn lagna (asc 270): the 2nd is Aquarius, lord Saturn (a malefic). Saturn at
        305.0 -> Aquarius (fixed; navamsa cycle starts 9th from it = Libra); 305.0 is the 2nd
        navamsa -> Scorpio, a MALEFIC-owned (cruel) navamsa. Keep every benefic off H2 and
        off any aspect to it. Jupiter must avoid H6/H8/H10 (whose 9th/7th/5th land on H2 —
        the first fixture had him in H6 and his trine relieved the house)."""
        c = _chart({"Saturn": 305.0, "Sun": 275.0, "Mars": 245.0, "Moon": 155.0,
                    "Mercury": 150.0, "Jupiter": 15.0, "Venus": 185.0}, asc_lon=270.0)
        assert _yoga("Y.VAKCHALANA").fires(c)

    def test_silent_when_a_benefic_aspects_the_second(self):
        # Jupiter moved to H8 (Leo) — its 7th aspect lands on H2 (Aquarius) -> relieved.
        c = _chart({"Saturn": 305.0, "Sun": 275.0, "Mars": 245.0, "Moon": 155.0,
                    "Mercury": 150.0, "Jupiter": 125.0, "Venus": 185.0}, asc_lon=270.0)
        assert not _yoga("Y.VAKCHALANA").fires(c)


class TestVishaprayogaYoga:
    def test_fires_on_the_full_affliction(self):
        """Capricorn lagna: Mars sits IN H2 (joined); Sun in H8 casts the 7th onto H2
        (aspected); 2nd lord Saturn in cruel navamsa (305 -> Scorpio) aspected by Mars
        (Mars in H2 = Aquarius casts its 4th onto... use Mars aspecting Saturn in H2 itself:
        same house = no; Mars' 4th from H2 is H5, 7th is H8, 8th is H9 — put Saturn IN H2
        with Mars? conjunction is not aspect. Instead: Saturn stays at 305 (H2), Mars in H7
        (Cancer) casts its 7th onto H1... recompute: Mars in H11 (Scorpio 220) casts 4th ->
        H2. So Mars at 220 aspects both house 2 and Saturn in it."""
        c = _chart({"Saturn": 305.0, "Mars": 220.0, "Sun": 305.5, "Moon": 155.0,
                    "Mercury": 150.0, "Jupiter": 60.0, "Venus": 185.0}, asc_lon=270.0)
        # Sun at 305.5 joins H2 (malefic in the 2nd); Mars from H11 aspects H2 and Saturn.
        assert _yoga("Y.VISHAPRAYOGA").fires(c)

    def test_silent_without_the_cruel_navamsa(self):
        # Saturn at 331.0 -> Pisces navamsa region... choose 330.5: Aquarius 60.5 deg in?
        # 330.5 is Pisces sign — wrong house. Use 301.0: Aquarius, navamsa Libra (1st of the
        # cycle) — Venus-owned, NOT cruel.
        c = _chart({"Saturn": 301.0, "Mars": 220.0, "Sun": 305.5, "Moon": 155.0,
                    "Mercury": 150.0, "Jupiter": 60.0, "Venus": 185.0}, asc_lon=270.0)
        assert not _yoga("Y.VISHAPRAYOGA").fires(c)


# ── tranche 4 (2026-08-09): the 3rd/4th-house block ─────────────────────────────────────────
class TestEkabhaginiYoga:
    def test_fires_on_the_distributive_triple(self):
        """Capricorn lagna (asc 270): 3rd = Pisces, lord Jupiter. Mercury in H3 (340),
        Jupiter joins the Moon (Leo), Mars joins Saturn (Aries) — the three RESPECTIVE
        pairings of Raman's sentence."""
        c = _chart({"Mercury": 340.0, "Jupiter": 130.0, "Moon": 135.0,
                    "Mars": 10.0, "Saturn": 15.0, "Sun": 300.0, "Venus": 200.0},
                   asc_lon=270.0)
        assert _yoga("Y.EKABHAGINI").fires(c)

    def test_silent_when_mars_leaves_saturn(self):
        c = _chart({"Mercury": 340.0, "Jupiter": 130.0, "Moon": 135.0,
                    "Mars": 10.0, "Saturn": 200.0, "Sun": 300.0, "Venus": 205.0},
                   asc_lon=270.0)
        assert not _yoga("Y.EKABHAGINI").fires(c)


class TestDwadasaSahodaraYoga:
    def test_fires_l3_in_kendra_exalted_mars_with_jupiter_in_trikona(self):
        """Aries lagna: l3 Mercury in H10 (Capricorn, a kendra); Mars EXALTED in
        Capricorn joins Jupiter there — H10 is the 1st (a trikona seat) from the 3rd lord."""
        c = _chart({"Mercury": 275.0, "Mars": 280.0, "Jupiter": 285.0,
                    "Sun": 10.0, "Moon": 40.0, "Venus": 100.0, "Saturn": 130.0})
        assert _yoga("Y.DWADASA_SAHODARA").fires(c)

    def test_silent_when_mars_is_unexalted(self):
        # Mars moved to Cancer (debilitation) — the exaltation clause must refuse.
        c = _chart({"Mercury": 275.0, "Mars": 100.0, "Jupiter": 285.0,
                    "Sun": 10.0, "Moon": 40.0, "Venus": 105.0, "Saturn": 130.0})
        assert not _yoga("Y.DWADASA_SAHODARA").fires(c)


class TestParakramaYoga:
    """Navamsa longitudes engine-scanned, not head-math: Mercury at 60.0 (Gemini) falls in
    the Libra navamsa (Venus-owned, benefic); 63.5 falls in Scorpio (Mars-owned, cruel)."""

    def test_fires_benefic_amsa_benefic_contact_mars_in_benefic_sign(self):
        # l3 Mercury at 60.0 -> benefic navamsa; Venus conjunct in H3; Mars in Taurus.
        c = _chart({"Mercury": 60.0, "Venus": 65.0, "Mars": 40.0, "Sun": 10.0,
                    "Moon": 130.0, "Jupiter": 250.0, "Saturn": 310.0})
        assert _yoga("Y.PARAKRAMA").fires(c)

    def test_silent_when_the_amsa_turns_cruel(self):
        c = _chart({"Mercury": 63.5, "Venus": 65.0, "Mars": 40.0, "Sun": 10.0,
                    "Moon": 130.0, "Jupiter": 250.0, "Saturn": 310.0})
        assert not _yoga("Y.PARAKRAMA").fires(c)


class TestSatkathadisravanaYoga:
    def test_fires_benefic_third_sign_aspected_lord_in_benefic_amsa(self):
        """Aries lagna: 3rd = Gemini (Mercury-owned, benefic); Jupiter in H9 (Sagittarius)
        casts the 7th onto H3; l3 Mercury at 60.0 sits in the Libra (benefic) navamsa."""
        c = _chart({"Mercury": 60.0, "Jupiter": 250.0, "Mars": 10.0,
                    "Sun": 15.0, "Moon": 130.0, "Venus": 190.0, "Saturn": 310.0})
        assert _yoga("Y.SATKATHADISRAVANA").fires(c)

    def test_silent_when_the_lords_amsa_turns_cruel(self):
        # Only the amsa clause changes (63.5 -> Scorpio navamsa) — sign and aspect hold.
        c = _chart({"Mercury": 63.5, "Jupiter": 250.0, "Mars": 10.0,
                    "Sun": 15.0, "Moon": 130.0, "Venus": 190.0, "Saturn": 310.0})
        assert not _yoga("Y.SATKATHADISRAVANA").fires(c)


class TestUttamaGrihaYoga:
    def test_fires_fourth_lord_with_a_benefic_in_a_trikona(self):
        # Aries lagna: l4 Moon in H5 (Leo, a trikona) joined by Jupiter.
        c = _chart({"Moon": 130.0, "Jupiter": 135.0, "Sun": 10.0, "Mars": 40.0,
                    "Mercury": 70.0, "Venus": 190.0, "Saturn": 310.0})
        assert _yoga("Y.UTTAMA_GRIHA").fires(c)

    def test_silent_when_the_lord_stands_alone(self):
        # Jupiter moved to H9 — the lord is in a trikona but joins no benefic.
        c = _chart({"Moon": 130.0, "Jupiter": 250.0, "Sun": 10.0, "Mars": 40.0,
                    "Mercury": 70.0, "Venus": 190.0, "Saturn": 310.0})
        assert not _yoga("Y.UTTAMA_GRIHA").fires(c)


class TestVichitraSaudhaYoga:
    def test_fires_on_the_four_planet_conjunction(self):
        """Gemini lagna (asc 60): l4 Mercury (Virgo) and l10 Jupiter (Pisces) conjoin
        Saturn AND Mars in Leo — four DISTINCT planets in one house, exactly the reading
        Raman's own Remarks fix."""
        c = _chart({"Mercury": 130.0, "Jupiter": 132.0, "Saturn": 134.0, "Mars": 136.0,
                    "Sun": 10.0, "Moon": 40.0, "Venus": 200.0}, asc_lon=60.0)
        assert _yoga("Y.VICHITRA_SAUDHA").fires(c)

    def test_silent_when_saturn_leaves_the_conjunction(self):
        c = _chart({"Mercury": 130.0, "Jupiter": 132.0, "Saturn": 200.0, "Mars": 136.0,
                    "Sun": 10.0, "Moon": 40.0, "Venus": 205.0}, asc_lon=60.0)
        assert not _yoga("Y.VICHITRA_SAUDHA").fires(c)


# ── tranche 5 (2026-08-09): the 4th-house/mother block ──────────────────────────────────────
class TestAyatnaGrihaYoga:
    def test_fires_on_189_lords_in_lagna_or_fourth_with_benefic(self):
        """Aries lagna: l1 Mars in H1, l7 Venus in H4 joined by Jupiter — Raman's Chart 87
        counts association as the benefic clause. Moon debilitated keeps the 190 arm out."""
        c = _chart({"Mars": 10.0, "Venus": 100.0, "Jupiter": 105.0, "Moon": 220.0,
                    "Sun": 130.0, "Mercury": 160.0, "Saturn": 310.0})
        assert _yoga("Y.AYATNA_GRIHA").fires(c)

    def test_silent_when_neither_arm_holds(self):
        # l1 Mars in H2 (189 out); l9 Jupiter in H3, not a kendra (190 out).
        c = _chart({"Mars": 40.0, "Venus": 100.0, "Jupiter": 70.0, "Moon": 220.0,
                    "Sun": 130.0, "Mercury": 160.0, "Saturn": 310.0})
        assert not _yoga("Y.AYATNA_GRIHA").fires(c)


class TestGrihanasaYoga:
    def test_fires_on_191_fourth_lord_in_third_aspected_by_malefic(self):
        """Aries lagna: l4 Moon in H3 (the 12th FROM THE 4TH per Raman's Remarks
        correction), Saturn in H9 casting the 7th onto it."""
        c = _chart({"Moon": 70.0, "Saturn": 250.0, "Mars": 10.0, "Sun": 130.0,
                    "Mercury": 160.0, "Jupiter": 190.0, "Venus": 280.0})
        assert _yoga("Y.GRIHANASA").fires(c)

    def test_silent_when_the_fourth_lord_leaves_the_third(self):
        c = _chart({"Moon": 100.0, "Saturn": 250.0, "Mars": 10.0, "Sun": 130.0,
                    "Mercury": 160.0, "Jupiter": 190.0, "Venus": 280.0})
        assert not _yoga("Y.GRIHANASA").fires(c)


class TestBandhuPujya193:
    def test_fires_benefic_fourth_lord_aspected_mercury_in_lagna(self):
        # Aries lagna: l4 Moon (natural benefic) in H4; Jupiter H8 casts the 9th onto it;
        # Mercury in Lagna.
        c = _chart({"Moon": 100.0, "Jupiter": 220.0, "Mercury": 10.0, "Mars": 40.0,
                    "Sun": 130.0, "Venus": 160.0, "Saturn": 310.0})
        assert _yoga("Y.BANDHU_PUJYA_193").fires(c)

    def test_silent_when_mercury_leaves_lagna(self):
        c = _chart({"Moon": 100.0, "Jupiter": 220.0, "Mercury": 70.0, "Mars": 40.0,
                    "Sun": 130.0, "Venus": 160.0, "Saturn": 310.0})
        assert not _yoga("Y.BANDHU_PUJYA_193").fires(c)


class TestBandhuPujya194:
    def test_fires_when_jupiter_aspects_the_fourth(self):
        c = _chart({"Jupiter": 220.0, "Moon": 100.0, "Mercury": 10.0, "Mars": 40.0,
                    "Sun": 130.0, "Venus": 160.0, "Saturn": 310.0})
        assert _yoga("Y.BANDHU_PUJYA_194").fires(c)

    def test_silent_when_jupiter_touches_neither_house_nor_lord(self):
        # Jupiter H2 aspects H6/H8/H10; l4 Moon parked in H12 out of reach.
        c = _chart({"Jupiter": 40.0, "Moon": 340.0, "Mercury": 10.0, "Mars": 70.0,
                    "Sun": 130.0, "Venus": 160.0, "Saturn": 310.0})
        assert not _yoga("Y.BANDHU_PUJYA_194").fires(c)


class TestMatrugamiYoga:
    def test_fires_afflicted_moon_in_kendra_with_malefic_in_fourth(self):
        # Mars in H4 (also supplying the evil-planet-in-4th clause) casts its 4th onto
        # the Moon in H7.
        c = _chart({"Mars": 100.0, "Moon": 190.0, "Sun": 130.0, "Mercury": 160.0,
                    "Jupiter": 250.0, "Venus": 280.0, "Saturn": 310.0})
        assert _yoga("Y.MATRUGAMI").fires(c)

    def test_silent_without_a_malefic_in_the_fourth(self):
        c = _chart({"Mars": 40.0, "Moon": 130.0, "Sun": 70.0, "Mercury": 160.0,
                    "Jupiter": 250.0, "Venus": 280.0, "Saturn": 310.0})
        assert not _yoga("Y.MATRUGAMI").fires(c)


class TestKapataYoga:
    def test_fires_on_202_malefic_in_fourth_and_afflicted_lord(self):
        # Sun in H4; l4 Moon conjunct Mars in H7.
        c = _chart({"Sun": 100.0, "Moon": 190.0, "Mars": 195.0, "Mercury": 160.0,
                    "Jupiter": 250.0, "Venus": 280.0, "Saturn": 310.0})
        assert _yoga("Y.KAPATA").fires(c)

    def test_fires_on_the_203_four_malefic_stack(self):
        """Saturn (the l10, itself malefic), Mars and Rahu all in H4, the Sun casting the
        7th onto Saturn from H10 — the full 203 stack."""
        c = _chart({"Saturn": 100.0, "Mars": 102.0, "Rahu": 104.0, "Sun": 285.0,
                    "Moon": 130.0, "Mercury": 160.0, "Jupiter": 220.0, "Venus": 250.0})
        assert _yoga("Y.KAPATA").fires(c)

    def test_silent_when_the_fourth_is_clean(self):
        c = _chart({"Sun": 10.0, "Moon": 130.0, "Mars": 40.0, "Mercury": 160.0,
                    "Jupiter": 250.0, "Venus": 280.0, "Saturn": 165.0})
        assert not _yoga("Y.KAPATA").fires(c)


class TestMatruSatrutwaYoga:
    def test_fires_only_for_gemini_lagna_with_afflicted_mercury(self):
        """Raman's Remarks: applicable only to Mithuna Lagna, where Mercury owns both
        Lagna and the 4th. Saturn conjunct Mercury supplies the affliction."""
        c = _chart({"Mercury": 100.0, "Saturn": 105.0, "Sun": 130.0, "Moon": 160.0,
                    "Mars": 190.0, "Jupiter": 250.0, "Venus": 280.0}, asc_lon=60.0)
        assert _yoga("Y.MATRU_SATRUTWA").fires(c)

    def test_silent_for_any_other_lagna(self):
        # Identical longitudes, Aries lagna — the Mithuna guard must refuse.
        c = _chart({"Mercury": 100.0, "Saturn": 105.0, "Sun": 130.0, "Moon": 160.0,
                    "Mars": 190.0, "Jupiter": 250.0, "Venus": 280.0}, asc_lon=0.0)
        assert not _yoga("Y.MATRU_SATRUTWA").fires(c)


class TestVahanaYoga:
    def test_fires_on_209_lagna_lord_in_ninth(self):
        c = _chart({"Mars": 250.0, "Moon": 130.0, "Sun": 10.0, "Mercury": 160.0,
                    "Jupiter": 190.0, "Venus": 280.0, "Saturn": 310.0})
        assert _yoga("Y.VAHANA").fires(c)

    def test_fires_on_210_exalted_fourth_lord_with_dispositor_in_kendra(self):
        # l4 Moon exalted in Taurus; its dispositor Venus in H7 (a kendra); l1 Mars kept
        # out of 4/9/11 so only the 210 arm carries it.
        c = _chart({"Moon": 40.0, "Venus": 190.0, "Mars": 70.0, "Sun": 10.0,
                    "Mercury": 160.0, "Jupiter": 220.0, "Saturn": 310.0})
        assert _yoga("Y.VAHANA").fires(c)

    def test_silent_when_neither_arm_holds(self):
        c = _chart({"Mars": 40.0, "Moon": 130.0, "Sun": 10.0, "Mercury": 160.0,
                    "Jupiter": 190.0, "Venus": 280.0, "Saturn": 310.0})
        assert not _yoga("Y.VAHANA").fires(c)


# ── tranche 6 (2026-08-09): the queued bars cleared ─────────────────────────────────────────
class _StubStrong:
    band = "strong"
    decisively_weak = False


class _StubWeak:
    band = "weak"
    decisively_weak = True


class TestMatrudeerghayurYoga:
    """Strength-gated: fire tests patch the B1 gate (the Y.GO discipline — silences alone
    cannot tell rare from dead)."""

    def test_fires_on_196_with_the_strength_gate_patched(self, monkeypatch):
        # Aries: l4 Moon EXALTED in Taurus; Jupiter (a benefic) in H4; Moon stubbed strong.
        import app.raman_saab.primitives.effective_strength as es_mod
        monkeypatch.setattr(es_mod, "effective_strength", lambda *a, **k: _StubStrong())
        c = _chart({"Moon": 40.0, "Jupiter": 100.0, "Mars": 10.0, "Sun": 130.0,
                    "Mercury": 160.0, "Venus": 190.0, "Saturn": 310.0})
        assert _yoga("Y.MATRUDEERGHAYUR").fires(c)

    def test_fires_on_197_self_dispositor_collapse(self, monkeypatch):
        """Moon at 93.3 (Cancer) falls in its OWN navamsa — the dispositor chain collapses
        onto the Moon itself, standing in H4: a kendra from Lagna and trivially from
        Chandra Lagna. Raman's Chart 90 remark legitimizes the collapse ("the third
        condition becomes merged with the 2nd"). The 196 arm stays out: own-sign, not
        exalted."""
        import app.raman_saab.primitives.effective_strength as es_mod
        monkeypatch.setattr(es_mod, "effective_strength", lambda *a, **k: _StubStrong())
        c = _chart({"Moon": 93.3, "Mars": 10.0, "Sun": 130.0, "Mercury": 160.0,
                    "Jupiter": 250.0, "Venus": 190.0, "Saturn": 310.0})
        assert _yoga("Y.MATRUDEERGHAYUR").fires(c)

    def test_silent_when_the_strength_gate_is_real(self):
        # Same 196 geometry, unpatched: stated charts carry no Shadbala -> band unknown.
        c = _chart({"Moon": 40.0, "Jupiter": 100.0, "Mars": 10.0, "Sun": 130.0,
                    "Mercury": 160.0, "Venus": 190.0, "Saturn": 310.0})
        assert not _yoga("Y.MATRUDEERGHAYUR").fires(c)


class TestMatrunasaYoga:
    def test_fires_on_198_moon_conjunct_saturn(self):
        c = _chart({"Moon": 130.0, "Saturn": 135.0, "Mars": 10.0, "Sun": 40.0,
                    "Mercury": 160.0, "Jupiter": 250.0, "Venus": 190.0})
        assert _yoga("Y.MATRUNASA").fires(c)

    def test_fires_on_the_199_navamsa_chain(self):
        """Moon (l4) at 103.3 -> Libra navamsa -> Venus; Venus at 130 -> a navamsa owned by
        Mercury; Mercury stands in H6 — the chain's terminal in a dusthana, with the Moon
        itself UNAFFLICTED so only the 199 arm carries it. Engine-scanned, not head-math."""
        c = _chart({"Moon": 103.3, "Mars": 40.0, "Sun": 340.0, "Mercury": 160.0,
                    "Jupiter": 250.0, "Venus": 130.0, "Saturn": 310.0})
        assert _yoga("Y.MATRUNASA").fires(c)

    def test_silent_when_moon_is_clean_and_the_chain_lands_well(self):
        # Moon 100.0: chain terminal Jupiter in H9 (not a dusthana); same clean layout.
        c = _chart({"Moon": 100.0, "Mars": 40.0, "Sun": 340.0, "Mercury": 160.0,
                    "Jupiter": 250.0, "Venus": 130.0, "Saturn": 310.0})
        assert not _yoga("Y.MATRUNASA").fires(c)


class TestNishkapataYoga:
    def test_fires_on_a_benefic_fourth_sign(self):
        # Aries lagna: the 4th is Cancer, Moon-owned — a benefic sign.
        c = _chart({"Sun": 10.0, "Moon": 40.0, "Mars": 70.0, "Mercury": 160.0,
                    "Jupiter": 250.0, "Venus": 190.0, "Saturn": 310.0})
        assert _yoga("Y.NISHKAPATA").fires(c)

    def test_silent_for_a_malefic_fourth_with_no_dignified_occupant(self):
        # Leo lagna: the 4th is Scorpio (Mars-owned), kept empty.
        c = _chart({"Sun": 130.0, "Moon": 160.0, "Mars": 10.0, "Mercury": 190.0,
                    "Jupiter": 280.0, "Venus": 100.0, "Saturn": 310.0}, asc_lon=120.0)
        assert not _yoga("Y.NISHKAPATA").fires(c)


class TestMatruSnehaYoga:
    def test_fires_on_the_common_lord(self):
        # Gemini lagna: Mercury owns both Lagna and the 4th (Virgo) — Raman's own remark
        # names Mithuna and Dhanus as the two common-lord lagnas.
        c = _chart({"Mercury": 100.0, "Sun": 130.0, "Moon": 160.0, "Mars": 190.0,
                    "Jupiter": 250.0, "Venus": 280.0, "Saturn": 310.0}, asc_lon=60.0)
        assert _yoga("Y.MATRU_SNEHA").fires(c)

    def test_silent_when_every_arm_fails(self):
        """Aries: Mars-Moon are NOT mutual natural friends (Mars befriends the Moon, the
        Moon is neutral back); Moon 5th from Mars makes them mutual TEMPORAL enemies; and
        benefics stay off Mars so the aspect arm fails too."""
        c = _chart({"Mars": 10.0, "Moon": 130.0, "Sun": 40.0, "Mercury": 70.0,
                    "Jupiter": 220.0, "Venus": 250.0, "Saturn": 310.0})
        assert not _yoga("Y.MATRU_SNEHA").fires(c)


class TestAnapathyaYoga:
    def test_fires_when_all_four_are_decisively_weak(self, monkeypatch):
        # Aries: Jupiter + Mars (l1) + Venus (l7) + Sun (l5), weakness stubbed per the
        # patched-gate discipline.
        import app.raman_saab.primitives.effective_strength as es_mod
        monkeypatch.setattr(es_mod, "effective_strength", lambda *a, **k: _StubWeak())
        c = _chart({"Jupiter": 40.0, "Mars": 10.0, "Venus": 70.0, "Sun": 130.0,
                    "Moon": 160.0, "Mercury": 190.0, "Saturn": 310.0})
        assert _yoga("Y.ANAPATHYA").fires(c)

    def test_silent_when_the_planets_are_well_placed(self):
        # Same chart, real effective_strength: no dusthana, no combustion, no uncancelled
        # debilitation -> nobody is decisively weak.
        c = _chart({"Jupiter": 40.0, "Mars": 10.0, "Venus": 70.0, "Sun": 130.0,
                    "Moon": 160.0, "Mercury": 190.0, "Saturn": 310.0})
        assert not _yoga("Y.ANAPATHYA").fires(c)


# ── tranche 7 (2026-08-09): the sapa (curse) block + Bahuputra ──────────────────────────────
class TestSarpasapaYoga:
    def test_fires_on_212_rahu_in_fifth_aspected_by_mars(self):
        # Aries: Rahu H5 (Leo); Mars in H10 casts its 8th onto H5.
        c = _chart({"Rahu": 130.0, "Mars": 280.0, "Sun": 10.0, "Moon": 40.0,
                    "Mercury": 70.0, "Jupiter": 220.0, "Venus": 250.0, "Saturn": 310.0})
        assert _yoga("Y.SARPASAPA").fires(c)

    def test_fires_on_213_fifth_lord_with_rahu_saturn_moon_in_fifth(self):
        # Aries: l5 Sun conjunct Rahu in H2; Saturn in H5 joined by the Moon.
        c = _chart({"Sun": 40.0, "Rahu": 45.0, "Saturn": 130.0, "Moon": 135.0,
                    "Mars": 340.0, "Mercury": 70.0, "Jupiter": 220.0, "Venus": 250.0})
        assert _yoga("Y.SARPASAPA").fires(c)

    def test_fires_on_214_karaka_with_mars_rahu_in_lagna_lord_in_dusthana(self):
        # Jupiter+Mars in H10, Rahu in Lagna, l5 Sun in H8. Stated charts carry no
        # Shadbala, so Raman's strength nullifier stays open and the geometry fires.
        c = _chart({"Jupiter": 280.0, "Mars": 285.0, "Rahu": 10.0, "Sun": 220.0,
                    "Moon": 40.0, "Mercury": 70.0, "Venus": 100.0, "Saturn": 160.0})
        assert _yoga("Y.SARPASAPA").fires(c)

    def test_214_is_nullified_when_jupiter_is_b1_strong(self, monkeypatch):
        """Raman's own Remarks nullifier: "if he has sufficient Shadbala strength, the
        yoga becomes null and void" — his worked example had ~8 rupas and 2 living
        children. Stubbing Jupiter B1-strong must silence the 214 arm."""
        import app.raman_saab.primitives.effective_strength as es_mod

        class _Strong:
            band = "strong"
            decisively_weak = False

        monkeypatch.setattr(es_mod, "effective_strength", lambda *a, **k: _Strong())
        c = _chart({"Jupiter": 280.0, "Mars": 285.0, "Rahu": 10.0, "Sun": 220.0,
                    "Moon": 40.0, "Mercury": 70.0, "Venus": 100.0, "Saturn": 160.0})
        assert not _yoga("Y.SARPASAPA").fires(c)

    def test_fires_on_215_mars_sign_fifth_with_rahu_and_mercury(self):
        # Kataka lagna: the 5th is Scorpio (a Mars sign); Rahu there with Mercury.
        c = _chart({"Rahu": 220.0, "Mercury": 225.0, "Mars": 160.0, "Sun": 100.0,
                    "Moon": 130.0, "Jupiter": 300.0, "Venus": 340.0, "Saturn": 40.0},
                   asc_lon=90.0)
        assert _yoga("Y.SARPASAPA").fires(c)

    def test_silent_when_rahu_leaves_the_picture(self):
        c = _chart({"Rahu": 70.0, "Sun": 10.0, "Moon": 40.0, "Mercury": 100.0,
                    "Jupiter": 130.0, "Mars": 190.0, "Venus": 250.0, "Saturn": 160.0})
        assert not _yoga("Y.SARPASAPA").fires(c)


class TestPitrusapaSutakshayaYoga:
    def test_fires_on_the_debilitated_sun_arm(self):
        # Gemini lagna: the 5th is Libra — the Sun's debilitation, exactly the one lagna
        # Raman's Remarks name for this arm.
        c = _chart({"Sun": 190.0, "Moon": 100.0, "Mars": 130.0, "Mercury": 70.0,
                    "Jupiter": 250.0, "Venus": 280.0, "Saturn": 310.0}, asc_lon=60.0)
        assert _yoga("Y.PITRUSAPA_SUTAKSHAYA").fires(c)

    def test_fires_on_the_makara_amsa_arm(self):
        """Libra lagna, Sun at 312.0 in Aquarius (H5) — engine-scanned to fall in the
        Makara navamsa (Chart 97's own configuration: Libra Lagna, Sun in the 5th joining
        Makaramsa)."""
        c = _chart({"Sun": 312.0, "Moon": 100.0, "Mars": 130.0, "Mercury": 250.0,
                    "Jupiter": 160.0, "Venus": 220.0, "Saturn": 70.0}, asc_lon=180.0)
        assert _yoga("Y.PITRUSAPA_SUTAKSHAYA").fires(c)

    def test_silent_when_no_arm_holds(self):
        # Sun at 300.0: Libra navamsa (Venus-owned), Aquarius is not debilitation, and
        # the houses flanking H5 are empty.
        c = _chart({"Sun": 300.0, "Moon": 100.0, "Mars": 130.0, "Mercury": 250.0,
                    "Jupiter": 160.0, "Venus": 220.0, "Saturn": 70.0}, asc_lon=180.0)
        assert not _yoga("Y.PITRUSAPA_SUTAKSHAYA").fires(c)


class TestMatrusapaSutakshayaYoga:
    def test_fires_on_the_5_8_parivartana_with_moon_and_l4_in_sixth(self):
        # Aries: l8 Mars in H5, l5 Sun in H8, Moon (also l4 — the collapse is legitimate)
        # in H6.
        c = _chart({"Mars": 130.0, "Sun": 220.0, "Moon": 160.0, "Mercury": 70.0,
                    "Jupiter": 250.0, "Venus": 280.0, "Saturn": 310.0})
        assert _yoga("Y.MATRUSAPA_SUTAKSHAYA").fires(c)

    def test_silent_when_the_moon_leaves_the_sixth(self):
        c = _chart({"Mars": 130.0, "Sun": 220.0, "Moon": 100.0, "Mercury": 70.0,
                    "Jupiter": 250.0, "Venus": 280.0, "Saturn": 310.0})
        assert not _yoga("Y.MATRUSAPA_SUTAKSHAYA").fires(c)


class TestBhratrusapaSutakshayaYoga:
    def test_fires_on_the_full_disposition(self):
        # Taurus lagna: l1 Venus and l5 Mercury in H8 (Sagittarius); l3 Moon with Mars
        # and Rahu in H5 (Virgo).
        c = _chart({"Venus": 250.0, "Mercury": 255.0, "Moon": 160.0, "Mars": 165.0,
                    "Rahu": 170.0, "Sun": 30.0, "Jupiter": 300.0, "Saturn": 100.0},
                   asc_lon=30.0)
        assert _yoga("Y.BHRATRUSAPA_SUTAKSHAYA").fires(c)

    def test_silent_when_rahu_leaves_the_fifth(self):
        c = _chart({"Venus": 250.0, "Mercury": 255.0, "Moon": 160.0, "Mars": 165.0,
                    "Rahu": 100.0, "Sun": 30.0, "Jupiter": 300.0, "Saturn": 40.0},
                   asc_lon=30.0)
        assert not _yoga("Y.BHRATRUSAPA_SUTAKSHAYA").fires(c)


class TestPretasapaYoga:
    def test_fires_with_the_weakness_gate_patched(self, monkeypatch):
        # Sun+Saturn H5, Moon H7, Rahu H1, Jupiter H12; Moon weakness stubbed per the
        # patched-gate discipline.
        import app.raman_saab.primitives.effective_strength as es_mod

        class _Weak:
            band = "weak"
            decisively_weak = True

        monkeypatch.setattr(es_mod, "effective_strength", lambda *a, **k: _Weak())
        c = _chart({"Sun": 130.0, "Saturn": 135.0, "Moon": 190.0, "Rahu": 10.0,
                    "Jupiter": 340.0, "Mars": 40.0, "Mercury": 70.0, "Venus": 100.0})
        assert _yoga("Y.PRETASAPA").fires(c)

    def test_silent_when_the_moon_is_not_weak(self):
        c = _chart({"Sun": 130.0, "Saturn": 135.0, "Moon": 190.0, "Rahu": 10.0,
                    "Jupiter": 340.0, "Mars": 40.0, "Mercury": 70.0, "Venus": 100.0})
        assert not _yoga("Y.PRETASAPA").fires(c)


class TestBahuputraYoga:
    def test_fires_on_220_rahu_in_fifth_outside_saturns_amsa(self):
        # Aries: Rahu at 132.0 (H5) falls in the Cancer navamsa (Moon's) — the exception
        # Raman highlights to "Rahu in the 5th is harmful".
        c = _chart({"Rahu": 132.0, "Sun": 10.0, "Moon": 40.0, "Mercury": 70.0,
                    "Jupiter": 250.0, "Venus": 280.0, "Mars": 310.0, "Saturn": 200.0})
        assert _yoga("Y.BAHUPUTRA").fires(c)

    def test_fires_on_the_221_navamsa_dispositor_route(self):
        """Chart 100's shape: Mars associates with the 7th lord (Venus, H9); Mars at
        252.0 occupies the Cancer navamsa, whose lord the Moon stands in H2 —
        engine-scanned."""
        c = _chart({"Venus": 245.0, "Mars": 252.0, "Sun": 10.0, "Moon": 40.0,
                    "Mercury": 130.0, "Jupiter": 300.0, "Saturn": 200.0, "Rahu": 70.0})
        assert _yoga("Y.BAHUPUTRA").fires(c)

    def test_silent_when_neither_route_exists(self):
        # Rahu off the 5th; no planet shares a house with the 7th lord.
        c = _chart({"Venus": 245.0, "Mars": 130.0, "Sun": 10.0, "Moon": 40.0,
                    "Mercury": 160.0, "Jupiter": 300.0, "Saturn": 200.0, "Rahu": 70.0})
        assert not _yoga("Y.BAHUPUTRA").fires(c)


# ── tranche 8 (2026-08-09): the progeny block ───────────────────────────────────────────────
class TestDattaputraYoga:
    def test_fires_on_222_mars_saturn_in_fifth_lagna_lord_in_mercury_sign(self):
        # Cancer lagna: l1 Moon in Virgo (a Mercury sign) conjunct Mercury; Mars and
        # Saturn together in H5 (Scorpio).
        c = _chart({"Moon": 160.0, "Mercury": 165.0, "Mars": 220.0, "Saturn": 225.0,
                    "Sun": 100.0, "Jupiter": 300.0, "Venus": 340.0, "Rahu": 40.0},
                   asc_lon=90.0)
        assert _yoga("Y.DATTAPUTRA").fires(c)

    def test_fires_on_223_chart_101_shape(self):
        # Aries: l7 Venus in H11; l5 Sun joins Jupiter; Saturn occupies H5 — the same
        # three clauses Raman reads off Chart 101.
        c = _chart({"Venus": 310.0, "Sun": 40.0, "Jupiter": 45.0, "Saturn": 130.0,
                    "Moon": 70.0, "Mars": 190.0, "Mercury": 100.0, "Rahu": 250.0})
        assert _yoga("Y.DATTAPUTRA").fires(c)

    def test_silent_when_the_lagna_lord_sits_in_its_own_sign(self):
        # Moon in Cancer (H1) is not a Mercury sign; the 223 arm fails too (l7 Saturn
        # not in H11).
        c = _chart({"Moon": 100.0, "Mercury": 165.0, "Mars": 220.0, "Saturn": 225.0,
                    "Sun": 130.0, "Jupiter": 300.0, "Venus": 340.0, "Rahu": 40.0},
                   asc_lon=90.0)
        assert not _yoga("Y.DATTAPUTRA").fires(c)


class TestAputraYoga:
    def test_fires_on_the_fifth_lord_in_a_dusthana(self):
        # Aries: l5 Sun in H8. The dusthana trio is 6/8/12 — the printed "5th, 8th and
        # 12th" is an OCR garble the condition docstring records.
        c = _chart({"Sun": 220.0, "Moon": 40.0, "Mars": 10.0, "Mercury": 70.0,
                    "Jupiter": 100.0, "Venus": 130.0, "Saturn": 310.0})
        assert _yoga("Y.APUTRA").fires(c)

    def test_silent_when_the_lord_is_well_placed(self):
        c = _chart({"Sun": 280.0, "Moon": 40.0, "Mars": 10.0, "Mercury": 70.0,
                    "Jupiter": 100.0, "Venus": 130.0, "Saturn": 310.0})
        assert not _yoga("Y.APUTRA").fires(c)


class TestEkaputraYoga:
    def test_fires_on_the_fifth_lord_in_a_trikona(self):
        c = _chart({"Sun": 250.0, "Moon": 40.0, "Mars": 10.0, "Mercury": 70.0,
                    "Jupiter": 100.0, "Venus": 130.0, "Saturn": 310.0})
        assert _yoga("Y.EKAPUTRA").fires(c)

    def test_silent_when_the_lord_avoids_kendra_and_trikona(self):
        c = _chart({"Sun": 40.0, "Moon": 70.0, "Mars": 10.0, "Mercury": 100.0,
                    "Jupiter": 130.0, "Venus": 160.0, "Saturn": 310.0})
        assert not _yoga("Y.EKAPUTRA").fires(c)


class TestKalanirdesatPutraYoga:
    def test_fires_on_227_jupiter_in_fifth_lord_with_venus(self):
        c = _chart({"Jupiter": 130.0, "Sun": 40.0, "Venus": 45.0, "Moon": 70.0,
                    "Mars": 190.0, "Mercury": 100.0, "Saturn": 310.0})
        assert _yoga("Y.KALANIRDESAT_PUTRA").fires(c)

    def test_fires_on_228_venus_ninth_from_jupiter_with_lagna_lord(self):
        # Jupiter H9; Venus in the 9th from Jupiter (= H5 from Lagna, Raman's own
        # simplification) conjunct l1 Mars.
        c = _chart({"Jupiter": 250.0, "Venus": 130.0, "Mars": 135.0, "Sun": 10.0,
                    "Moon": 40.0, "Mercury": 70.0, "Saturn": 310.0})
        assert _yoga("Y.KALANIRDESAT_PUTRA").fires(c)

    def test_silent_when_neither_arm_holds(self):
        c = _chart({"Jupiter": 70.0, "Venus": 100.0, "Mars": 10.0, "Sun": 160.0,
                    "Moon": 40.0, "Mercury": 190.0, "Saturn": 310.0})
        assert not _yoga("Y.KALANIRDESAT_PUTRA").fires(c)


class TestKalanirdesatPutranasaYoga:
    def test_fires_on_229_the_threefold_affliction(self):
        # Rahu in H5, l5 Sun conjunct Saturn, Jupiter debilitated in Capricorn — house,
        # lord and karaka all afflicted, exactly Raman's reading.
        c = _chart({"Rahu": 130.0, "Jupiter": 280.0, "Sun": 40.0, "Saturn": 45.0,
                    "Moon": 70.0, "Mars": 190.0, "Mercury": 100.0, "Venus": 250.0})
        assert _yoga("Y.KALANIRDESAT_PUTRANASA").fires(c)

    def test_fires_on_230_malefics_in_the_fifth_from_both(self):
        # Mars in H5 from Lagna; Jupiter in H9 with Saturn in H1 — the 5th from Jupiter.
        c = _chart({"Mars": 130.0, "Jupiter": 250.0, "Saturn": 10.0, "Sun": 40.0,
                    "Moon": 70.0, "Mercury": 100.0, "Venus": 160.0, "Rahu": 220.0})
        assert _yoga("Y.KALANIRDESAT_PUTRANASA").fires(c)

    def test_silent_when_the_fifths_are_clean(self):
        c = _chart({"Mars": 190.0, "Jupiter": 250.0, "Saturn": 310.0, "Sun": 40.0,
                    "Moon": 130.0, "Mercury": 100.0, "Venus": 160.0, "Rahu": 220.0})
        assert not _yoga("Y.KALANIRDESAT_PUTRANASA").fires(c)


# ── tranche 9 (2026-08-09): the buddhi + marriage block ─────────────────────────────────────
class TestBuddhimaturyaYoga:
    def test_fires_on_the_printed_definition_arm(self):
        # Taurus lagna: l5 Mercury (a benefic) in Gemini — its own, benefic-owned sign.
        c = _chart({"Mercury": 70.0, "Sun": 30.0, "Moon": 100.0, "Mars": 190.0,
                    "Jupiter": 250.0, "Venus": 220.0, "Saturn": 310.0}, asc_lon=30.0)
        assert _yoga("Y.BUDDHIMATURYA").fires(c)

    def test_fires_on_ramans_remarks_extension(self):
        """Aries — one of the five lagnas the printed definition excludes; Raman's own
        Remarks extension carries it: a benefic occupying the 5th with the 5th lord
        conjunct a benefic."""
        c = _chart({"Jupiter": 130.0, "Sun": 40.0, "Venus": 45.0, "Moon": 220.0,
                    "Mars": 190.0, "Mercury": 280.0, "Saturn": 310.0})
        assert _yoga("Y.BUDDHIMATURYA").fires(c)

    def test_silent_when_no_arm_holds(self):
        c = _chart({"Sun": 40.0, "Saturn": 45.0, "Moon": 220.0, "Mars": 190.0,
                    "Jupiter": 250.0, "Mercury": 280.0, "Venus": 310.0})
        assert not _yoga("Y.BUDDHIMATURYA").fires(c)


class TestTheevrabuddhiYoga:
    def test_fires_when_the_navamsa_dispositor_is_benefic_touched(self):
        # l5 Sun at 103.3 falls in the Libra navamsa; its lord Venus sits with Jupiter —
        # Raman's conjunction extension. Engine-scanned.
        c = _chart({"Sun": 103.3, "Venus": 250.0, "Jupiter": 255.0, "Moon": 40.0,
                    "Mars": 10.0, "Mercury": 70.0, "Saturn": 310.0})
        assert _yoga("Y.THEEVRABUDDHI").fires(c)

    def test_silent_when_the_dispositor_stands_alone(self):
        c = _chart({"Sun": 103.3, "Venus": 250.0, "Jupiter": 100.0, "Moon": 10.0,
                    "Mars": 40.0, "Mercury": 315.0, "Saturn": 310.0})
        assert not _yoga("Y.THEEVRABUDDHI").fires(c)


class TestBuddhiJadaYoga:
    def test_fires_when_saturn_in_fifth_aspects_the_afflicted_lagna_lord(self):
        # Saturn in H5 casts its 3rd onto H7, where l1 Mars stands — one aspect satisfies
        # both the affliction and the Saturn-aspect clause.
        c = _chart({"Mars": 190.0, "Saturn": 130.0, "Sun": 10.0, "Moon": 40.0,
                    "Mercury": 70.0, "Jupiter": 250.0, "Venus": 280.0})
        assert _yoga("Y.BUDDHI_JADA").fires(c)

    def test_silent_when_saturn_leaves_the_fifth(self):
        c = _chart({"Mars": 190.0, "Saturn": 160.0, "Sun": 10.0, "Moon": 40.0,
                    "Mercury": 70.0, "Jupiter": 250.0, "Venus": 280.0})
        assert not _yoga("Y.BUDDHI_JADA").fires(c)


class TestPutraSukhaYoga:
    def test_fires_on_mercury_in_the_fifth(self):
        c = _chart({"Mercury": 130.0, "Sun": 10.0, "Moon": 40.0, "Mars": 190.0,
                    "Jupiter": 250.0, "Venus": 280.0, "Saturn": 310.0})
        assert _yoga("Y.PUTRA_SUKHA").fires(c)

    def test_silent_when_the_fifth_is_bare(self):
        # Aries: the 5th (Leo) is a malefic-owned sign holding only the Sun.
        c = _chart({"Mercury": 70.0, "Sun": 130.0, "Moon": 40.0, "Mars": 190.0,
                    "Jupiter": 250.0, "Venus": 280.0, "Saturn": 310.0})
        assert not _yoga("Y.PUTRA_SUKHA").fires(c)


class TestJaraYoga:
    def test_fires_only_with_ramans_narrowing_satisfied(self):
        # Aries: l7 Venus (within Raman's Mars-or-Venus narrowing); Venus (also l2) and
        # Saturn (l10) together in H10.
        c = _chart({"Venus": 280.0, "Saturn": 285.0, "Sun": 10.0, "Moon": 100.0,
                    "Mars": 40.0, "Mercury": 70.0, "Jupiter": 130.0})
        assert _yoga("Y.JARA").fires(c)

    def test_silent_for_a_seventh_lord_outside_the_narrowing(self):
        """Identical longitudes from Cancer lagna: l7 is Saturn — the very case Raman's
        Remarks refuse ("unless the 7th lord happens to be Mars or Venus... it is not
        advisable to conclude")."""
        c = _chart({"Venus": 280.0, "Saturn": 285.0, "Sun": 10.0, "Moon": 100.0,
                    "Mars": 40.0, "Mercury": 70.0, "Jupiter": 130.0}, asc_lon=90.0)
        assert not _yoga("Y.JARA").fires(c)


class TestJarajaputraYoga:
    def test_fires_with_the_strength_gates_patched(self, monkeypatch):
        # l5 Sun, l7 Venus, l6 Mercury conjunct in H2; Jupiter casts the 9th onto H2;
        # both lords stubbed B1-strong per the patched-gate discipline.
        import app.raman_saab.primitives.effective_strength as es_mod

        class _Strong:
            band = "strong"
            decisively_weak = False

        monkeypatch.setattr(es_mod, "effective_strength", lambda *a, **k: _Strong())
        c = _chart({"Sun": 40.0, "Venus": 45.0, "Mercury": 50.0, "Jupiter": 160.0,
                    "Moon": 100.0, "Mars": 10.0, "Saturn": 310.0})
        assert _yoga("Y.JARAJAPUTRA").fires(c)

    def test_silent_when_the_strength_gate_is_real(self):
        c = _chart({"Sun": 40.0, "Venus": 45.0, "Mercury": 50.0, "Jupiter": 160.0,
                    "Moon": 100.0, "Mars": 10.0, "Saturn": 310.0})
        assert not _yoga("Y.JARAJAPUTRA").fires(c)


class TestBahuStreeYoga:
    def test_fires_on_the_lords_in_conjunction(self):
        c = _chart({"Mars": 70.0, "Venus": 75.0, "Sun": 10.0, "Moon": 100.0,
                    "Mercury": 130.0, "Jupiter": 250.0, "Saturn": 310.0})
        assert _yoga("Y.BAHU_STREE").fires(c)

    def test_silent_without_conjunction_or_mutual_aspect(self):
        # Mars H1 aspects H4/H7/H8; Venus H3 aspects H9 — neither reaches the other, and
        # the Remarks variant arm is dead (l9 Jupiter in H9, not H7).
        c = _chart({"Mars": 10.0, "Venus": 75.0, "Sun": 40.0, "Moon": 100.0,
                    "Mercury": 130.0, "Jupiter": 250.0, "Saturn": 310.0})
        assert not _yoga("Y.BAHU_STREE").fires(c)


class TestSatkalatraYoga:
    def test_fires_on_venus_joined_by_jupiter(self):
        c = _chart({"Jupiter": 250.0, "Venus": 255.0, "Sun": 10.0, "Moon": 40.0,
                    "Mars": 70.0, "Mercury": 100.0, "Saturn": 310.0})
        assert _yoga("Y.SATKALATRA").fires(c)

    def test_silent_when_neither_target_is_touched(self):
        # Chart 112's shape: neither the 7th lord nor Venus under Jupiter or Mercury.
        c = _chart({"Venus": 40.0, "Jupiter": 130.0, "Mercury": 340.0, "Sun": 10.0,
                    "Moon": 70.0, "Mars": 100.0, "Saturn": 310.0})
        assert not _yoga("Y.SATKALATRA").fires(c)


class TestBhagaChumbanaYoga:
    def test_fires_on_the_seventh_lord_in_fourth_with_venus(self):
        # Taurus lagna: l7 Mars in H4 (Leo) conjunct Venus.
        c = _chart({"Mars": 130.0, "Venus": 135.0, "Sun": 30.0, "Moon": 70.0,
                    "Mercury": 100.0, "Jupiter": 250.0, "Saturn": 310.0}, asc_lon=30.0)
        assert _yoga("Y.BHAGA_CHUMBANA").fires(c)

    def test_silent_when_the_conjunction_leaves_the_fourth(self):
        # Mars to H5; l1 Venus in Leo is neither rasi- nor navamsa-debilitated, so the
        # Remarks arm stays quiet too.
        c = _chart({"Mars": 160.0, "Venus": 135.0, "Sun": 30.0, "Moon": 70.0,
                    "Mercury": 100.0, "Jupiter": 250.0, "Saturn": 310.0}, asc_lon=30.0)
        assert not _yoga("Y.BHAGA_CHUMBANA").fires(c)


# ── tranche 10 (2026-08-09): fortune + the Raja group opening ───────────────────────────────
class TestBhagyaYoga:
    def test_fires_with_the_strength_gate_patched(self, monkeypatch):
        # Jupiter in Lagna casts the 9th onto H9 — the one benefic Raman notes can raise
        # the yoga from Lagna; strength stubbed per the patched-gate discipline.
        import app.raman_saab.primitives.effective_strength as es_mod

        class _Strong:
            band = "strong"
            decisively_weak = False

        monkeypatch.setattr(es_mod, "effective_strength", lambda *a, **k: _Strong())
        c = _chart({"Jupiter": 10.0, "Sun": 40.0, "Moon": 70.0, "Mars": 100.0,
                    "Mercury": 160.0, "Venus": 220.0, "Saturn": 310.0})
        assert _yoga("Y.BHAGYA").fires(c)

    def test_silent_when_the_strength_gate_is_real(self):
        c = _chart({"Jupiter": 10.0, "Sun": 40.0, "Moon": 70.0, "Mars": 100.0,
                    "Mercury": 160.0, "Venus": 220.0, "Saturn": 310.0})
        assert not _yoga("Y.BHAGYA").fires(c)


class TestJananatpurvamPitruMaranaYoga:
    def test_fires_when_the_entire_yoga_is_present(self):
        # Chart 113's structure: Sun in the 8th, l8 in the 9th, l12 in Lagna, l6 in the
        # 5th — Raman: the ENTIRE yoga, not a part of it.
        c = _chart({"Sun": 220.0, "Mars": 250.0, "Jupiter": 10.0, "Mercury": 130.0,
                    "Moon": 40.0, "Venus": 100.0, "Saturn": 310.0})
        assert _yoga("Y.JANANATPURVAM_PITRU_MARANA").fires(c)

    def test_silent_when_the_sun_leaves_the_dusthanas(self):
        c = _chart({"Sun": 280.0, "Mars": 250.0, "Jupiter": 10.0, "Mercury": 130.0,
                    "Moon": 40.0, "Venus": 100.0, "Saturn": 310.0})
        assert not _yoga("Y.JANANATPURVAM_PITRU_MARANA").fires(c)


class TestDhatrutwaYoga:
    def test_fires_on_the_exalted_ninth_lord_fully_supported(self):
        # l9 Jupiter exalted in Cancer; Venus casts the 7th onto it; Mercury occupies H9.
        c = _chart({"Jupiter": 100.0, "Venus": 280.0, "Mercury": 250.0, "Sun": 10.0,
                    "Moon": 40.0, "Mars": 190.0, "Saturn": 310.0})
        assert _yoga("Y.DHATRUTWA").fires(c)

    def test_silent_when_the_lord_is_unexalted(self):
        c = _chart({"Jupiter": 130.0, "Venus": 280.0, "Mercury": 250.0, "Sun": 10.0,
                    "Moon": 40.0, "Mars": 190.0, "Saturn": 310.0})
        assert not _yoga("Y.DHATRUTWA").fires(c)


class TestApakeertiYoga:
    def test_fires_on_sun_saturn_in_tenth_aspected_by_mars(self):
        c = _chart({"Sun": 280.0, "Saturn": 285.0, "Mars": 70.0, "Moon": 40.0,
                    "Mercury": 130.0, "Jupiter": 250.0, "Venus": 340.0})
        assert _yoga("Y.APAKEERTI").fires(c)

    def test_silent_in_benefic_amsas_unaspected(self):
        """Raman's own converse: mere presence in the 10th, unaspected and in benefic
        navamsas, is NOT the yoga. Sun 291.0 / Saturn 292.5 both fall in Moon-owned
        navamsas (engine-scanned); Mars parked in H5 aspects H8/H11/H12."""
        c = _chart({"Sun": 291.0, "Saturn": 292.5, "Mars": 130.0, "Moon": 40.0,
                    "Mercury": 100.0, "Jupiter": 250.0, "Venus": 340.0})
        assert not _yoga("Y.APAKEERTI").fires(c)


class TestRaja245:
    def test_fires_on_three_dignified_planets_in_kendras_and_trikonas(self):
        # Mars own in H1, Moon own in H4, Saturn exalted in H7.
        c = _chart({"Mars": 10.0, "Moon": 100.0, "Saturn": 190.0, "Sun": 40.0,
                    "Mercury": 70.0, "Jupiter": 130.0, "Venus": 220.0})
        assert _yoga("Y.RAJA_245").fires(c)

    def test_silent_below_the_count(self):
        # Only Saturn (exalted, H7) qualifies.
        c = _chart({"Mars": 40.0, "Moon": 70.0, "Saturn": 190.0, "Sun": 160.0,
                    "Mercury": 220.0, "Jupiter": 130.0, "Venus": 250.0})
        assert not _yoga("Y.RAJA_245").fires(c)


class TestRaja246:
    def test_fires_on_a_bright_debilitated_planet_outside_dusthanas(self):
        # Jupiter neecha in Capricorn (H10), uncombust — Chart 116's pattern.
        c = _chart({"Jupiter": 280.0, "Sun": 10.0, "Moon": 40.0, "Mars": 100.0,
                    "Mercury": 160.0, "Venus": 190.0, "Saturn": 220.0})
        assert _yoga("Y.RAJA_246").fires(c)

    def test_silent_without_a_qualifying_debilitation(self):
        c = _chart({"Jupiter": 100.0, "Sun": 10.0, "Moon": 40.0, "Mars": 70.0,
                    "Mercury": 160.0, "Venus": 190.0, "Saturn": 310.0})
        assert not _yoga("Y.RAJA_246").fires(c)


class TestRaja247:
    def test_fires_on_chart_117s_digbala_pair(self):
        # Jupiter in Lagna and the Moon in the 4th — the exact pair Raman reads off
        # Chart 117.
        c = _chart({"Jupiter": 10.0, "Moon": 100.0, "Sun": 40.0, "Mars": 70.0,
                    "Mercury": 130.0, "Venus": 220.0, "Saturn": 310.0})
        assert _yoga("Y.RAJA_247").fires(c)

    def test_silent_when_no_planet_holds_digbala(self):
        c = _chart({"Jupiter": 40.0, "Moon": 130.0, "Sun": 70.0, "Mars": 100.0,
                    "Mercury": 160.0, "Venus": 220.0, "Saturn": 310.0})
        assert not _yoga("Y.RAJA_247").fires(c)


class TestRaja249:
    def test_fires_in_toto(self):
        # Moon in Lagna, Jupiter in the 4th, Venus in the 10th, Saturn exalted.
        c = _chart({"Moon": 10.0, "Jupiter": 100.0, "Venus": 280.0, "Saturn": 190.0,
                    "Sun": 40.0, "Mars": 70.0, "Mercury": 130.0})
        assert _yoga("Y.RAJA_249").fires(c)

    def test_silent_when_saturn_is_undignified(self):
        c = _chart({"Moon": 10.0, "Jupiter": 100.0, "Venus": 280.0, "Saturn": 130.0,
                    "Sun": 40.0, "Mars": 70.0, "Mercury": 160.0})
        assert not _yoga("Y.RAJA_249").fires(c)


class TestRaja250:
    def test_fires_on_chart_119s_neechabhanga(self):
        """The Sun neecha in Libra with Saturn — the planet exalted THERE, Raman's
        resolution of thaduchchanatha via Prof. B. Suryanarain Rao — in a kendra from
        Lagna: Chart 119's own configuration."""
        c = _chart({"Sun": 190.0, "Saturn": 280.0, "Moon": 40.0, "Mars": 100.0,
                    "Mercury": 130.0, "Jupiter": 250.0, "Venus": 160.0})
        assert _yoga("Y.RAJA_250").fires(c)

    def test_silent_when_no_candidate_reaches_a_kendra(self):
        # Sun neecha, but Saturn (H3) and Venus (H12) miss every kendra from Lagna and
        # from the Moon; no other planet is debilitated.
        c = _chart({"Sun": 190.0, "Saturn": 70.0, "Moon": 40.0, "Mars": 133.0,
                    "Mercury": 100.0, "Jupiter": 250.0, "Venus": 340.0})
        assert not _yoga("Y.RAJA_250").fires(c)


# ── tranche 11 (2026-08-10): the Raja group completes ───────────────────────────────────────
class TestRaja251:
    def test_fires_with_the_strength_gate_patched(self, monkeypatch):
        # Moon in H4 (a kendra other than Lagna), Jupiter casting the 7th onto it;
        # "otherwise powerful" stubbed per the patched-gate discipline.
        import app.raman_saab.primitives.effective_strength as es_mod

        class _Strong:
            band = "strong"
            decisively_weak = False

        monkeypatch.setattr(es_mod, "effective_strength", lambda *a, **k: _Strong())
        c = _chart({"Moon": 100.0, "Jupiter": 280.0, "Sun": 10.0, "Mars": 40.0,
                    "Mercury": 130.0, "Venus": 190.0, "Saturn": 310.0})
        assert _yoga("Y.RAJA_251").fires(c)

    def test_silent_when_the_strength_gate_is_real(self):
        c = _chart({"Moon": 100.0, "Jupiter": 280.0, "Sun": 10.0, "Mars": 40.0,
                    "Mercury": 130.0, "Venus": 190.0, "Saturn": 310.0})
        assert not _yoga("Y.RAJA_251").fires(c)


class TestRaja252:
    def test_fires_when_every_neecha_planet_is_exalted_in_amsa(self):
        # Jupiter neecha in Capricorn at 291.0 — engine-scanned to fall in the Cancer
        # (exaltation) navamsa; no other planet debilitated. Chart 122's total reading.
        c = _chart({"Jupiter": 291.0, "Sun": 10.0, "Moon": 40.0, "Mars": 15.0,
                    "Mercury": 160.0, "Venus": 190.0, "Saturn": 220.0})
        assert _yoga("Y.RAJA_252").fires(c)

    def test_silent_when_the_amsa_is_not_exaltation(self):
        # Jupiter 279.0 falls in the Pisces navamsa — own, not exalted.
        c = _chart({"Jupiter": 279.0, "Sun": 10.0, "Moon": 40.0, "Mars": 15.0,
                    "Mercury": 160.0, "Venus": 190.0, "Saturn": 220.0})
        assert not _yoga("Y.RAJA_252").fires(c)


class TestRaja253:
    def test_fires_with_self_lordship_satisfying_the_aspect_clause(self):
        """Aries lagna: Jupiter in Lagna IS the 9th lord (Chart 123's principle —
        self-lordship satisfies); Mercury in H10 receives the 3rd aspect of the 11th
        lord Saturn."""
        c = _chart({"Jupiter": 10.0, "Mercury": 280.0, "Saturn": 220.0, "Sun": 40.0,
                    "Moon": 70.0, "Mars": 100.0, "Venus": 190.0})
        assert _yoga("Y.RAJA_253").fires(c)

    def test_silent_when_jupiter_leaves_lagna(self):
        c = _chart({"Jupiter": 40.0, "Mercury": 280.0, "Saturn": 220.0, "Sun": 10.0,
                    "Moon": 70.0, "Mars": 100.0, "Venus": 190.0})
        assert not _yoga("Y.RAJA_253").fires(c)


class TestRaja254:
    def test_fires_on_exalted_saturn_in_trikona_aspected_by_tenth_lord(self):
        # Gemini lagna: Saturn in Thula (H5, a trikona); l10 Jupiter in Lagna casts the
        # 5th onto him.
        c = _chart({"Saturn": 190.0, "Jupiter": 70.0, "Sun": 100.0, "Moon": 130.0,
                    "Mars": 160.0, "Mercury": 220.0, "Venus": 250.0}, asc_lon=60.0)
        assert _yoga("Y.RAJA_254").fires(c)

    def test_silent_when_saturn_leaves_thula_and_kumbha(self):
        c = _chart({"Saturn": 160.0, "Jupiter": 70.0, "Sun": 100.0, "Moon": 130.0,
                    "Mars": 190.0, "Mercury": 220.0, "Venus": 250.0}, asc_lon=60.0)
        assert not _yoga("Y.RAJA_254").fires(c)


class TestRaja255:
    def test_fires_on_chandra_mangala_in_second_with_rahu_in_fifth(self):
        c = _chart({"Moon": 40.0, "Mars": 45.0, "Rahu": 130.0, "Sun": 10.0,
                    "Mercury": 70.0, "Jupiter": 250.0, "Venus": 280.0, "Saturn": 310.0})
        assert _yoga("Y.RAJA_255").fires(c)

    def test_silent_when_rahu_leaves_the_fifth(self):
        c = _chart({"Moon": 40.0, "Mars": 45.0, "Rahu": 250.0, "Sun": 10.0,
                    "Mercury": 70.0, "Jupiter": 130.0, "Venus": 280.0, "Saturn": 310.0})
        assert not _yoga("Y.RAJA_255").fires(c)


class TestRaja257:
    def test_fires_for_a_fixed_lagna_in_full(self):
        # Taurus (fixed): Jupiter H5, Moon in the 4th from Jupiter (H8), l1 Venus in H10.
        c = _chart({"Jupiter": 160.0, "Moon": 250.0, "Venus": 310.0, "Sun": 30.0,
                    "Mars": 70.0, "Mercury": 100.0, "Saturn": 190.0}, asc_lon=30.0)
        assert _yoga("Y.RAJA_257").fires(c)

    def test_silent_for_a_movable_lagna(self):
        # Identical longitudes from Aries — the fixed-sign gate must refuse.
        c = _chart({"Jupiter": 160.0, "Moon": 250.0, "Venus": 310.0, "Sun": 30.0,
                    "Mars": 70.0, "Mercury": 100.0, "Saturn": 190.0}, asc_lon=0.0)
        assert not _yoga("Y.RAJA_257").fires(c)


class TestRaja258:
    def test_fires_when_the_moons_amsa_lord_holds_a_trikona(self):
        # Moon 103.3 -> Libra navamsa -> Venus, standing in H9. Engine-scanned.
        c = _chart({"Moon": 103.3, "Venus": 250.0, "Sun": 10.0, "Mars": 40.0,
                    "Mercury": 130.0, "Jupiter": 280.0, "Saturn": 310.0})
        assert _yoga("Y.RAJA_258").fires(c)

    def test_silent_when_the_amsa_lord_misses_both_seats(self):
        c = _chart({"Moon": 103.3, "Venus": 40.0, "Sun": 10.0, "Mars": 70.0,
                    "Mercury": 340.0, "Jupiter": 280.0, "Saturn": 310.0})
        assert not _yoga("Y.RAJA_258").fires(c)


class TestRaja259:
    def test_fires_on_the_sambhu_hora_prakasha_pattern(self):
        # Taurus Lagna, Moon in it; Saturn/Sun/Jupiter in 10/4/7.
        c = _chart({"Moon": 40.0, "Saturn": 310.0, "Sun": 130.0, "Jupiter": 220.0,
                    "Mars": 70.0, "Mercury": 100.0, "Venus": 250.0}, asc_lon=30.0)
        assert _yoga("Y.RAJA_259").fires(c)

    def test_silent_when_jupiter_leaves_the_seventh(self):
        c = _chart({"Moon": 40.0, "Saturn": 310.0, "Sun": 130.0, "Jupiter": 250.0,
                    "Mars": 70.0, "Mercury": 100.0, "Venus": 220.0}, asc_lon=30.0)
        assert not _yoga("Y.RAJA_259").fires(c)


class TestRaja260:
    def test_fires_on_chart_128s_structure(self):
        """Makara Lagna (movable), its lord Saturn in Thula (movable); Jupiter neecha at
        270.0, whose navamsa dispositor Saturn stands in H10 — a kendra. The dispositor
        collapsing onto the Lagna lord is Chart 128's own shape."""
        c = _chart({"Saturn": 190.0, "Jupiter": 270.0, "Sun": 100.0, "Moon": 130.0,
                    "Mars": 40.0, "Mercury": 160.0, "Venus": 220.0}, asc_lon=270.0)
        assert _yoga("Y.RAJA_260").fires(c)

    def test_silent_when_the_dispositor_misses_kendra_and_trikona(self):
        # Jupiter 285.0 -> a Venus-owned navamsa; Venus stands in H11.
        c = _chart({"Saturn": 190.0, "Jupiter": 285.0, "Sun": 100.0, "Moon": 130.0,
                    "Mars": 40.0, "Mercury": 160.0, "Venus": 220.0}, asc_lon=270.0)
        assert not _yoga("Y.RAJA_260").fires(c)


class TestRaja261:
    def test_fires_on_chart_129s_structure(self):
        # Rahu+Saturn in H10 aspected by l9 Jupiter (5th from H2); l1 Mars conjunct the
        # debilitated Moon in Scorpio.
        c = _chart({"Rahu": 280.0, "Saturn": 285.0, "Jupiter": 40.0, "Mars": 225.0,
                    "Moon": 220.0, "Sun": 10.0, "Mercury": 100.0, "Venus": 130.0})
        assert _yoga("Y.RAJA_261").fires(c)

    def test_silent_when_the_lagna_lord_keeps_clean_company(self):
        c = _chart({"Rahu": 280.0, "Saturn": 285.0, "Jupiter": 40.0, "Mars": 225.0,
                    "Moon": 100.0, "Sun": 10.0, "Mercury": 130.0, "Venus": 160.0})
        assert not _yoga("Y.RAJA_261").fires(c)


class TestRaja262:
    def test_fires_for_a_jupiter_lorded_eleventh(self):
        # Taurus lagna: Jupiter owns the 11th (Pisces) and, as its lord, stands with the
        # Moon — the 1st (a kendra seat) from her.
        c = _chart({"Jupiter": 105.0, "Moon": 100.0, "Sun": 30.0, "Mars": 70.0,
                    "Mercury": 130.0, "Venus": 190.0, "Saturn": 250.0}, asc_lon=30.0)
        assert _yoga("Y.RAJA_262").fires(c)

    def test_silent_where_jupiter_owns_none_of_2_5_11(self):
        # Aries lagna: Jupiter owns the 9th and 12th — Raman's own lagna restriction.
        c = _chart({"Jupiter": 105.0, "Moon": 100.0, "Sun": 30.0, "Mars": 70.0,
                    "Mercury": 130.0, "Venus": 190.0, "Saturn": 250.0}, asc_lon=0.0)
        assert not _yoga("Y.RAJA_262").fires(c)


class TestRaja263:
    def test_fires_on_uncombust_jupiter_in_ninth_with_a_friend(self):
        # Jupiter in H9 joined by the Sun — a naisargika friend — and free of combustion
        # on a stated chart.
        c = _chart({"Jupiter": 250.0, "Sun": 255.0, "Moon": 40.0, "Mars": 100.0,
                    "Mercury": 130.0, "Venus": 190.0, "Saturn": 310.0})
        assert _yoga("Y.RAJA_263").fires(c)

    def test_silent_when_no_friendly_planet_touches_the_ninth_occupant(self):
        c = _chart({"Jupiter": 250.0, "Sun": 130.0, "Moon": 190.0, "Mars": 220.0,
                    "Mercury": 130.0, "Venus": 190.0, "Saturn": 310.0})
        assert not _yoga("Y.RAJA_263").fires(c)


# ── tranche 12 (2026-08-11): the Arishta chapter's mechanical half ──────────────────────────
class TestVranaYoga:
    def test_fires_on_a_malefic_sixth_lord_in_the_tenth(self):
        # Gemini lagna: l6 Mars (a malefic) in H10 — Chart 131's own house.
        c = _chart({"Mars": 340.0, "Sun": 70.0, "Moon": 100.0, "Mercury": 130.0,
                    "Jupiter": 250.0, "Venus": 280.0, "Saturn": 310.0}, asc_lon=60.0)
        assert _yoga("Y.VRANA").fires(c)

    def test_silent_for_scorpio_per_ramans_exception(self):
        """Scorpio lagna: the 6th lord IS the Lagna lord (Mars) — the one lagna Raman's
        Remarks except from the yoga, even with Mars in Lagna."""
        c = _chart({"Mars": 220.0, "Sun": 70.0, "Moon": 100.0, "Mercury": 130.0,
                    "Jupiter": 250.0, "Venus": 280.0, "Saturn": 310.0}, asc_lon=210.0)
        assert not _yoga("Y.VRANA").fires(c)


class TestSisnavyadhiYoga:
    def test_fires_on_mercury_with_both_lords_in_lagna(self):
        # Taurus lagna: Mercury joined by l6 Venus and l8 Jupiter, all in Lagna.
        c = _chart({"Mercury": 35.0, "Venus": 40.0, "Jupiter": 45.0, "Sun": 70.0,
                    "Moon": 100.0, "Mars": 190.0, "Saturn": 310.0}, asc_lon=30.0)
        assert _yoga("Y.SISNAVYADHI").fires(c)

    def test_silent_when_the_eighth_lord_is_absent(self):
        c = _chart({"Mercury": 35.0, "Venus": 40.0, "Jupiter": 130.0, "Sun": 70.0,
                    "Moon": 100.0, "Mars": 190.0, "Saturn": 310.0}, asc_lon=30.0)
        assert not _yoga("Y.SISNAVYADHI").fires(c)


class TestKalatrashandaYoga:
    def test_fires_on_the_seventh_lord_in_sixth_with_venus(self):
        # Taurus lagna: l7 Mars in H6 (Libra) joined by Venus.
        c = _chart({"Mars": 190.0, "Venus": 195.0, "Sun": 70.0, "Moon": 100.0,
                    "Mercury": 130.0, "Jupiter": 250.0, "Saturn": 310.0}, asc_lon=30.0)
        assert _yoga("Y.KALATRASHANDA").fires(c)

    def test_silent_when_venus_leaves_the_sixth(self):
        c = _chart({"Mars": 190.0, "Venus": 280.0, "Sun": 70.0, "Moon": 100.0,
                    "Mercury": 130.0, "Jupiter": 250.0, "Saturn": 310.0}, asc_lon=30.0)
        assert not _yoga("Y.KALATRASHANDA").fires(c)


class TestKushtarogaYoga:
    def test_fires_on_268_lagna_lord_mars_mercury_in_twelfth(self):
        # Aries: l1 IS Mars — the set collapses to Mars+Mercury, together in H12.
        c = _chart({"Mars": 340.0, "Mercury": 345.0, "Sun": 70.0, "Moon": 100.0,
                    "Jupiter": 250.0, "Venus": 280.0, "Saturn": 310.0})
        assert _yoga("Y.KUSHTAROGA").fires(c)

    def test_fires_on_269_jupiter_saturn_moon_in_sixth(self):
        c = _chart({"Jupiter": 160.0, "Saturn": 165.0, "Moon": 170.0, "Sun": 10.0,
                    "Mars": 40.0, "Mercury": 70.0, "Venus": 280.0})
        assert _yoga("Y.KUSHTAROGA").fires(c)

    def test_silent_when_the_moon_leaves_the_sixth(self):
        c = _chart({"Jupiter": 160.0, "Saturn": 165.0, "Moon": 100.0, "Sun": 10.0,
                    "Mars": 40.0, "Mercury": 70.0, "Venus": 280.0})
        assert not _yoga("Y.KUSHTAROGA").fires(c)


class TestBandhanaYoga:
    def test_fires_on_both_lords_seated_with_saturn(self):
        # Aries: l1 Mars in H10 with Saturn; l6 Mercury in H4 — both lords in kendras,
        # Saturn conjunct one of them.
        c = _chart({"Mars": 280.0, "Saturn": 285.0, "Mercury": 100.0, "Sun": 10.0,
                    "Moon": 40.0, "Jupiter": 250.0, "Venus": 130.0, "Rahu": 70.0})
        assert _yoga("Y.BANDHANA").fires(c)

    def test_silent_when_no_shadow_malefic_joins_either_lord(self):
        c = _chart({"Mars": 280.0, "Saturn": 40.0, "Mercury": 100.0, "Sun": 10.0,
                    "Moon": 70.0, "Jupiter": 250.0, "Venus": 130.0, "Rahu": 70.0})
        assert not _yoga("Y.BANDHANA").fires(c)


class TestDurmaranaYoga:
    def test_fires_on_the_afflicted_moon_in_the_eighth(self):
        # Moon in H8 with Saturn; l1 Mars casts its 8th onto H8 from Lagna.
        c = _chart({"Moon": 220.0, "Saturn": 225.0, "Mars": 10.0, "Sun": 40.0,
                    "Mercury": 70.0, "Jupiter": 250.0, "Venus": 130.0})
        assert _yoga("Y.DURMARANA").fires(c)

    def test_silent_when_saturn_and_rahu_leave_the_moon(self):
        # The Mandi arm is deliberately unencoded (Gulika queue) — with Saturn and Rahu
        # away the record must stay quiet.
        c = _chart({"Moon": 220.0, "Saturn": 310.0, "Mars": 10.0, "Sun": 40.0,
                    "Mercury": 70.0, "Jupiter": 250.0, "Venus": 130.0})
        assert not _yoga("Y.DURMARANA").fires(c)


class TestPeenasarogaYoga:
    def test_fires_on_the_full_disposition(self):
        """Moon H6, Saturn H8, the Sun (a malefic) H12, and l1 Mars at 30.0 — falling in
        a Saturn-owned (cruel) navamsa, engine-scanned."""
        c = _chart({"Mars": 30.0, "Moon": 160.0, "Saturn": 220.0, "Sun": 340.0,
                    "Mercury": 100.0, "Jupiter": 250.0, "Venus": 130.0})
        assert _yoga("Y.PEENASAROGA").fires(c)

    def test_silent_when_the_lagna_lords_amsa_is_benefic(self):
        # Mars at 51.0 falls in the Moon-owned navamsa — only that clause flips.
        c = _chart({"Mars": 51.0, "Moon": 160.0, "Saturn": 220.0, "Sun": 340.0,
                    "Mercury": 100.0, "Jupiter": 250.0, "Venus": 130.0})
        assert not _yoga("Y.PEENASAROGA").fires(c)


# ── tranche 13 (2026-08-11): the shashtiamsa (D60) unlocks ──────────────────────────────────
class TestThrikalagnanaYoga:
    def test_fires_at_ramans_own_window(self):
        """Jupiter at 9.25 deg of Thula (lon 189.25) — inside the ONLY windows the
        reachability scan found (9-9.5 deg of Mithuna/Thula/Kumbha), which are exactly
        the sign-and-degree bounds Raman's Remark prints."""
        c = _chart({"Jupiter": 189.25, "Sun": 10.0, "Moon": 40.0, "Mars": 70.0,
                    "Mercury": 100.0, "Venus": 250.0, "Saturn": 310.0})
        assert _yoga("Y.THRIKALAGNANA").fires(c)

    def test_silent_outside_the_mridwamsa(self):
        # Jupiter at 10.0 deg of Thula: still own navamsa territory but past the 19th
        # part — only the D60 clause flips.
        c = _chart({"Jupiter": 190.0, "Sun": 10.0, "Moon": 40.0, "Mars": 70.0,
                    "Mercury": 100.0, "Venus": 250.0, "Saturn": 310.0})
        assert not _yoga("Y.THRIKALAGNANA").fires(c)


class TestGalakarnaYoga:
    def test_fires_on_mars_in_third_in_preta_puriha(self):
        # Aries lagna: H3 is Gemini (odd); the 12th part spans 5.5-6.0 deg -> lon 65.7.
        c = _chart({"Mars": 65.7, "Sun": 10.0, "Moon": 40.0, "Mercury": 100.0,
                    "Jupiter": 250.0, "Venus": 130.0, "Saturn": 310.0})
        assert _yoga("Y.GALAKARNA").fires(c)

    def test_silent_when_the_amsa_is_wrong(self):
        # Mars at Gemini 7.0 (lon 67.0): the 15th part — same house, wrong amsa.
        c = _chart({"Mars": 67.0, "Sun": 10.0, "Moon": 40.0, "Mercury": 100.0,
                    "Jupiter": 250.0, "Venus": 130.0, "Saturn": 310.0})
        assert not _yoga("Y.GALAKARNA").fires(c)
