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


# ── detection API ────────────────────────────────────────────────────────────
class TestDetectYogas:
    def test_returns_fired_yogas_with_verifying_citations(self):
        """detect_yogas surfaces exactly the active yogas, each with a citation
        that resolves on disk."""
        fired = detect_yogas(_chart({"Mercury": 155.0, "Jupiter": 160.0}))
        assert isinstance(fired, tuple)
        assert all(isinstance(f, FiredYoga) for f in fired)
        assert [f.id for f in fired] == ["Y.VIPAREETA"]
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
