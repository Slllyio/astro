"""Unit tests for the Run-4 Raman-as-practiced encoder.

Synthetic ChartBundles are constructed directly (no ephemeris) so each
doctrinal mechanism is pinned in isolation: the maraka relationship
hierarchy, the kendradhipati promotion, the longevity-band gate, the
weakness / nakshatra / occupancy multipliers, and the transit terms.
One real-cast integration pin (Gandhi) guards the full path.
"""
from __future__ import annotations

import numpy as np
import pytest

from app.core.chart_model import Chart
from app.medini.ml.raman_saab.ayurdaya import AyuBand
from app.medini.ml.raman_saab.chart_bundle import GRAHAS, ChartBundle
from app.medini.ml.raman_saab.kundali import SIGN_RULER, Kundali, _nth_sign
from app.medini.ml.raman_saab.raman_method import (
    LORD_IDX, RAMAN_WEIGHTS, PotencyModel, _frame_maraka_contrib,
    longevity_score, maraka_scores,
)


# Non-degenerate defaults: spread grahas across neutral houses so nothing is
# accidentally conjunct a maraka lord, and pin a default weakest planet
# (Ketu) so the weakest-planet bonus doesn't land on an arbitrary tie-break.
_DEFAULT_HOUSES = {"Sun": 3, "Moon": 11, "Mars": 6, "Mercury": 12,
                   "Jupiter": 9, "Venus": 10, "Saturn": 5,
                   "Rahu": 4, "Ketu": 10}
_DEFAULT_STRENGTH = {"Ketu": 0.45}


def mk_bundle(
    houses: dict[str, int], *, lagna_sign: int = 1,
    strength: dict[str, float] | None = None,
    navamsa_houses: dict[str, int] | None = None,
    nakshatra_lord: dict[str, str] | None = None,
    moon_waxing: bool = True,
) -> ChartBundle:
    """Hand-built bundle: whole-sign, sign = lagna_sign shifted by house."""
    houses = {g: houses.get(g, _DEFAULT_HOUSES[g]) for g in GRAHAS}
    strength = {**_DEFAULT_STRENGTH, **(strength or {})}
    signs = {g: _nth_sign(lagna_sign, h) for g, h in houses.items()}
    lons = {g: (signs[g] - 1) * 30.0 + 15.0 for g in GRAHAS}
    strength = {g: strength.get(g, 0.5) for g in GRAHAS}
    nav_h = {g: (navamsa_houses or {}).get(g, _DEFAULT_HOUSES[g])
             for g in GRAHAS}
    nav_lagna = 1
    nav_sign = {g: _nth_sign(nav_lagna, h) for g, h in nav_h.items()}
    kund = Kundali(
        lagna_sign=lagna_sign, moon_longitude=lons["Moon"], birth_jd=2400000.0,
        planet_house=houses,
        maraka_lords=frozenset({SIGN_RULER[_nth_sign(lagna_sign, 2)],
                                SIGN_RULER[_nth_sign(lagna_sign, 7)]}),
        lord_8=SIGN_RULER[_nth_sign(lagna_sign, 8)],
        lord_2=SIGN_RULER[_nth_sign(lagna_sign, 2)],
        lord_7=SIGN_RULER[_nth_sign(lagna_sign, 7)],
    )
    chart = Chart(asc_sign=lagna_sign, asc_lon=(lagna_sign - 1) * 30.0 + 5.0,
                  planet_signs=signs, planet_houses=houses, planet_lons=lons)
    return ChartBundle(
        person_id="synthetic", kundali=kund, chart=chart,
        strength=strength, shadbala_ratio={g: 0.6 for g in GRAHAS[:7]},
        navamsa_sign=nav_sign, navamsa_lagna=nav_lagna,
        nakshatra_lord={g: (nakshatra_lord or {}).get(g, "") for g in GRAHAS},
        combust={g: False for g in GRAHAS}, moon_waxing=moon_waxing,
        lagna_lord=SIGN_RULER[lagna_sign],
    )


# --------------------------------------------------------------------------- #
# maraka hierarchy                                                            #
# --------------------------------------------------------------------------- #

class TestMarakaHierarchy:
    def test_conjunct_maraka_lord_outranks_the_lord_itself(self):
        # Aries lagna: 2L = Venus (Taurus), 7L = Venus (Libra) — Venus double
        # maraka lord. Put Moon conjunct Venus (same house 5).
        b = mk_bundle({"Venus": 5, "Moon": 5})
        c = _frame_maraka_contrib(b, "lagna", RAMAN_WEIGHTS)
        assert c["Moon"] == RAMAN_WEIGHTS["mk.conjunct_maraka_lord"]
        assert c["Venus"] >= RAMAN_WEIGHTS["mk.lord_2"]
        assert c["Moon"] > c["Venus"]  # THE Raman inversion

    def test_malefic_occupant_of_maraka_house_beats_benefic(self):
        b = mk_bundle({"Saturn": 7, "Jupiter": 2})
        c = _frame_maraka_contrib(b, "lagna", RAMAN_WEIGHTS)
        assert c["Saturn"] >= RAMAN_WEIGHTS["mk.malefic_in_maraka_house"]
        assert c["Jupiter"] == pytest.approx(
            RAMAN_WEIGHTS["mk.benefic_in_maraka_house"])
        assert c["Saturn"] > c["Jupiter"]

    def test_max_not_sum_within_frame(self):
        # A planet that is both 2L and 7L (Venus for Aries) takes max(0.6, 0.5),
        # not 1.1 — hierarchy is ranked, not additive within a frame.
        b = mk_bundle({})
        c = _frame_maraka_contrib(b, "lagna", RAMAN_WEIGHTS)
        assert c["Venus"] == pytest.approx(RAMAN_WEIGHTS["mk.lord_2"])

    def test_kendradhipati_promotion_requires_both_conditions(self):
        # Gemini lagna (3): Jupiter rules 7H (Sagittarius) and 10H (Pisces) —
        # kendra lord AND maraka lord -> promoted.
        b = mk_bundle({}, lagna_sign=3)
        c = _frame_maraka_contrib(b, "lagna", RAMAN_WEIGHTS)
        assert c["Jupiter"] >= RAMAN_WEIGHTS["mk.kendradhipati_promotion"]
        # Aries lagna: Jupiter rules 9 and 12 — no kendra, no promotion.
        b2 = mk_bundle({"Jupiter": 5}, lagna_sign=1)
        c2 = _frame_maraka_contrib(b2, "lagna", RAMAN_WEIGHTS)
        assert c2["Jupiter"] < RAMAN_WEIGHTS["mk.kendradhipati_promotion"]

    def test_weakest_planet_term_added_once(self):
        b = mk_bundle({}, strength={"Mercury": 0.1})
        mk = maraka_scores(b)
        b2 = mk_bundle({}, strength={"Mercury": 0.5, "Sun": 0.49})
        mk2 = maraka_scores(b2)
        # Mercury weakest in b -> gets the bonus there but not in b2.
        assert mk["Mercury"] - mk2["Mercury"] == pytest.approx(
            RAMAN_WEIGHTS["mk.weakest_planet"])

    def test_three_frames_are_weighted(self):
        b = mk_bundle({})
        mk = maraka_scores(b)
        # Venus (Aries-lagna 2L/7L) accumulates lagna-frame weight at least.
        assert mk["Venus"] >= RAMAN_WEIGHTS["mk.ref_lagna"] * RAMAN_WEIGHTS["mk.lord_2"]


# --------------------------------------------------------------------------- #
# longevity                                                                   #
# --------------------------------------------------------------------------- #

class TestLongevity:
    def test_jupiter_protection_raises_score(self):
        # Jupiter in 1H aspects 5,7,9; put Saturn in 7H so Jupiter aspects it.
        protected = mk_bundle({"Jupiter": 1, "Saturn": 7})
        exposed = mk_bundle({"Jupiter": 1, "Saturn": 6})
        assert (longevity_score(protected).score
                > longevity_score(exposed).score)

    def test_malefics_in_8h_lower_score(self):
        clean = mk_bundle({})
        afflicted = mk_bundle({"Saturn": 8, "Mars": 8})
        assert longevity_score(afflicted).score < longevity_score(clean).score

    def test_balarishta_forces_alpayu(self):
        # Moon in 8H conjunct Saturn, weak lagna lord, waning weak Moon,
        # Jupiter not in kendra -> balarishta, no cancellation.
        b = mk_bundle({"Moon": 8, "Saturn": 8, "Jupiter": 3},
                      strength={"Mars": 0.2, "Moon": 0.2}, moon_waxing=False)
        lng = longevity_score(b)
        assert lng.balarishta and lng.band == AyuBand.ALPAYU

    def test_balarishta_cancelled_by_kendra_jupiter(self):
        b = mk_bundle({"Moon": 8, "Saturn": 8, "Jupiter": 4},
                      strength={"Mars": 0.2, "Moon": 0.2}, moon_waxing=False)
        assert not longevity_score(b).balarishta


# --------------------------------------------------------------------------- #
# potency                                                                     #
# --------------------------------------------------------------------------- #

class TestPotency:
    def test_band_gate_levels(self):
        # Strong protective chart: Jupiter+Venus on lagna, strong Saturn and
        # lagna lord -> comfortably PURNAYU.
        b = mk_bundle({"Jupiter": 1, "Venus": 1},
                      strength={"Jupiter": 0.9, "Saturn": 0.9, "Mars": 0.9})
        pm = PotencyModel.from_bundle(b)
        assert pm.band == AyuBand.PURNAYU
        ages = np.array([80.0, 50.0, 10.0])  # in / adjacent / far
        gate = pm.band_gate(ages)
        assert gate[0] == RAMAN_WEIGHTS["fp.gate_in_band"]
        assert gate[1] == RAMAN_WEIGHTS["fp.gate_adjacent"]
        assert gate[2] == RAMAN_WEIGHTS["fp.gate_far"]

    def test_weakness_amplifies_scoring_lords_only(self):
        strong = mk_bundle({}, strength={"Venus": 0.9})
        weak = mk_bundle({}, strength={"Venus": 0.2})
        f_strong = PotencyModel.from_bundle(strong).lord_factor[LORD_IDX["Venus"]]
        f_weak = PotencyModel.from_bundle(weak).lord_factor[LORD_IDX["Venus"]]
        assert f_weak > f_strong  # weak maraka kills more readily

    def test_nakshatra_dispositor_multiplier(self):
        # Venus is the radix maraka lord for Aries lagna; give Rahu a Venus
        # nakshatra dispositor (the Tilak mechanism).
        with_nak = mk_bundle({}, nakshatra_lord={"Rahu": "Venus"})
        without = mk_bundle({})
        f_with = PotencyModel.from_bundle(with_nak).lord_factor[LORD_IDX["Rahu"]]
        f_without = PotencyModel.from_bundle(without).lord_factor[LORD_IDX["Rahu"]]
        assert f_with / f_without == pytest.approx(
            1.0 + RAMAN_WEIGHTS["fp.nakshatra_maraka"])

    def test_transit_multipliers(self):
        b = mk_bundle({})
        pm = PotencyModel.from_bundle(b)
        md = np.array([LORD_IDX["Venus"]]); ad = np.array([LORD_IDX["Venus"]])
        age = np.array([50.0])
        moon_sign = b.chart.planet_signs["Moon"]
        base = pm.potency(md, ad, age)
        sat_2nd = np.array([_nth_sign(moon_sign, 2)])
        with_sat = pm.potency(md, ad, age, sat_sign=sat_2nd,
                              mars_sign=np.array([1]))
        assert with_sat[0] / base[0] == pytest.approx(
            1.0 + RAMAN_WEIGHTS["tr.saturn_2nd_from_moon"])
        both = pm.potency(md, ad, age, sat_sign=sat_2nd, mars_sign=sat_2nd)
        assert both[0] / with_sat[0] == pytest.approx(
            1.0 + RAMAN_WEIGHTS["tr.mars_saturn_contact"])

    def test_ad_weighted_over_md(self):
        # Raman times by bhukti: potency(md=inert, ad=killer) > reverse.
        b = mk_bundle({})
        pm = PotencyModel.from_bundle(b)
        age = np.array([50.0])
        killer, inert = LORD_IDX["Venus"], LORD_IDX["Sun"]
        p_ad = pm.potency(np.array([inert]), np.array([killer]), age)
        p_md = pm.potency(np.array([killer]), np.array([inert]), age)
        assert p_ad[0] > p_md[0]


# --------------------------------------------------------------------------- #
# real-cast integration pin                                                   #
# --------------------------------------------------------------------------- #

class TestGandhiPin:
    def test_gandhi_libra_lagna_and_mars_top_maraka(self):
        from app.medini.ml.raman_saab.chart_bundle import build_bundle
        b = build_bundle(1869, 10, 2, 7, 11, 4.641, 21.64, 69.61)
        assert b is not None
        assert b.kundali.lagna_sign == 7  # Libra (Raman, Notable Horoscopes)
        mk = maraka_scores(b)
        # Mars rules both 2H (Scorpio) and 7H (Aries) from Libra — the chart's
        # top-tier killer must include Mars.
        top3 = sorted(mk, key=mk.get, reverse=True)[:3]
        assert "Mars" in top3
