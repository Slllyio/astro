"""Raman's HTJAH ch. IV judgment method, executed (pure doctrine).

Covers the bucket classifier, the five-factor timing sub-verdict + dasa
windows + current-period activation, and that the previously-inert ``method``
records are now cited by every house judgment.
"""
import pytest

from app.medini.doctrine import raman_chart as rc
from app.medini.doctrine.domains.house_judgment import (
    ACTIVATION_TIERS, VERDICT_SCALE, Finding, _antardasha_spans, _assess_bhava,
    _assess_from_moon, _assess_karaka, _assess_lord, _associated, _classify,
    _combine, _influence_factors, _is_benefic, _is_combination, _kartari,
    _lord_from_moon, _maha_sequence, _pair_tier, _planet_nature, _verdict_label,
    judge_all_houses_doctrine, judge_house_doctrine,
)

_LABELS = set(VERDICT_SCALE)

# Mainpuri chart: Scorpio lagna, lord Mars in Virgo/11th, Mercury conjunct Mars.
MAINPURI = dict(
    positions={"Sun": 176.562, "Moon": 319.0817, "Mars": 172.4476,
               "Mercury": 158.7869, "Jupiter": 78.1407, "Venus": 221.6724,
               "Saturn": 255.8022, "Rahu": 300.4694, "Ketu": 120.4694},
    lagna=225.5089, jd=2447811.6888)


@pytest.fixture(scope="module")
def mainpuri():
    return rc.from_printed_positions(
        MAINPURI["positions"], MAINPURI["lagna"], birth_jd=MAINPURI["jd"])


def _rule(rt, ante, timing=None):
    return {"rule_type": rt, "antecedent": ante,
            "consequent": {"timing": timing, "polarity": "favorable"}}


class TestClassifier:
    def test_lord_bucket(self):
        r = _rule("bhava_judgment",
                  {"op": "lord_of_house_in_house", "of_house": 1, "in_house": 8})
        assert _classify(r, 1) == "lord"
        assert _classify(_rule("graha_effect",
                               {"op": "planet_is_lord_of", "planet": "Mars",
                                "house": 1}), 1) == "lord"

    def test_occupants_bucket(self):
        r = _rule("graha_effect", {"op": "planet_in_house", "planet": "Sun",
                                   "house": 1})
        assert _classify(r, 1) == "occupants"
        # group/list house specs resolve too
        assert _classify(_rule("graha_effect",
                               {"op": "planet_in_house", "planet": "malefic",
                                "house": "kendra"}), 1) == "occupants"

    def test_bhava_bucket(self):
        assert _classify(_rule("graha_effect",
                               {"op": "planet_aspects_house", "planet": "Saturn",
                                "house": 1}), 1) == "bhava"
        assert _classify(_rule("bhava_judgment",
                               {"op": "lagna_sign_is", "sign": "scorpio"}), 1) == "bhava"

    def test_timing_bucket(self):
        assert _classify(_rule("dasha_timing",
                               {"op": "lord_of_house_in_house", "of_house": 1,
                                "in_house": 2}), 1) == "timing"
        assert _classify(_rule("graha_effect",
                               {"op": "planet_influences_house", "planet": "Sun",
                                "house": 1}), 1) == "timing"

    def test_karaka_bucket(self):
        # 4th karaka = Moon; a Moon rule that isn't lord/occupant/aspect of H4
        r = _rule("graha_effect", {"op": "own_sign", "planet": "Moon"})
        assert _classify(r, 4) == "karaka"


class TestTiming:
    def test_maha_sequence_covers_nine(self):
        seq = _maha_sequence(MAINPURI["positions"]["Moon"])
        assert len(seq) == 9
        assert {l for l, _, _ in seq} == {
            "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
            "Rahu", "Ketu"}
        # windows are contiguous and increasing
        for (_, _, e0), (_, s1, _) in zip(seq, seq[1:]):
            assert abs(e0 - s1) < 1e-6

    def test_mainpuri_mercury_activation(self, mainpuri):
        j = judge_house_doctrine(mainpuri, 1, dasha={"md": "Mercury", "ad": "Mercury"})
        # Mercury conjoins the lagna-lord Mars -> influences the 1st (5th factor)
        assert "Mercury" in j.timing.influencers
        assert j.timing.current_md == "Mercury"
        assert j.timing.current_is_activator
        assert any(e.rule_id.endswith(".mercury_dasa_first")
                   for e in j.timing.active_outcomes)
        # the running mahadasha is flagged current in the windows
        cur = [w for w in j.timing.windows if w.is_current]
        assert len(cur) == 1 and cur[0].lord == "Mercury" and cur[0].influences

    def test_no_activation_when_dasha_lord_not_influencer(self, mainpuri):
        # The Moon does NOT influence the 1st on this chart; its dasa shouldn't activate.
        j = judge_house_doctrine(mainpuri, 1, dasha={"md": "Moon", "ad": "Moon"})
        assert not j.timing.current_is_activator
        assert j.timing.active_outcomes == ()


class TestAshtakavargaFeature:
    """Increment 9 (documented NEGATIVE): the ashtakavarga strength machinery is wired
    but DORMANT (weight 0) -- it did not improve held-out agreement. These guard the
    machinery: the bindu count matches the rule-path computation, it is inert at the
    committed weight, and it moves the score when a weight is enabled."""

    def test_sav_bindu_count_matches_rule_path(self, mainpuri):
        from app.medini.doctrine.domains.house_judgment import _ashtakavarga
        from app.core.ashtakavarga import compute_ashtakavarga
        c = mainpuri.bundle.chart
        d1 = {p: {"sign": s} for p, s in c.planet_signs.items()}
        assert _ashtakavarga(mainpuri)["sav"] == compute_ashtakavarga(d1, {"sign": c.asc_sign})["sav"]

    def test_dormant_at_committed_weight(self, mainpuri):
        from app.medini.doctrine.domains.house_judgment import _sav_finding, _bav_finding, _W
        assert _W["av_bindu"] == 0.0 and _W["bav_bindu"] == 0.0
        assert _sav_finding(mainpuri, 8).delta == 0.0          # measured but unweighted
        bf = _bav_finding(mainpuri, "Saturn")
        assert bf is not None and bf.delta == 0.0

    def test_weight_activates_the_feature(self, mainpuri):
        from app.medini.doctrine.domains import house_judgment as HJ
        base = HJ._sav_finding(mainpuri, 8).delta
        HJ._W["av_bindu"] = 0.05
        try:
            assert HJ._sav_finding(mainpuri, 8).delta != base   # a live weight bites
        finally:
            HJ._W["av_bindu"] = 0.0


class TestAntardashaTiming:
    """Vimshottari antardasha (bhukti) nesting + Raman's MD x AD fructification
    tiers (HTJAH pp. 44-48)."""

    def test_antardasha_partitions_each_mahadasha(self):
        # Every mahadasha holds nine sub-periods summing to its own length.
        spans = _antardasha_spans("Saturn", 10.0, 29.0)   # full 19-year Saturn MD
        assert [l for l, _, _ in spans] == [
            "Saturn", "Mercury", "Ketu", "Venus", "Sun", "Moon", "Mars",
            "Rahu", "Jupiter"]                             # order begins with MD lord
        total = sum(e - s for _, s, e in spans)
        assert total == pytest.approx(19.0, abs=1e-2)
        assert spans[0][1] == 10.0 and spans[-1][2] == pytest.approx(29.0, abs=1e-2)

    def test_partial_birth_mahadasha_clipped_to_birth(self):
        # A partial birth MD drops pre-birth sub-periods; the running one starts at 0.
        spans = _antardasha_spans("Mars", 0.0, 6.11, elapsed_into_md=7 - 6.11)
        assert spans[0][1] == 0.0
        # Saturn sub-period in Mars MD ends ~2.6y (Raman's Chart 11: "about April 1915").
        sat = next(e for l, s, e in spans if l == "Saturn")
        assert 2.4 < sat < 2.8

    def test_windows_carry_nested_antardashas(self, mainpuri):
        nine = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn",
                "Rahu", "Ketu"}
        j = judge_house_doctrine(mainpuri, 1, dasha={"md": "Mercury", "ad": "Venus"})
        # full mahadashas hold all nine bhuktis; only the partial birth MD is short
        for w in j.timing.windows[1:]:
            assert {a.lord for a in w.antardashas} == nine
        assert j.timing.windows[0].antardashas  # birth MD has its (clipped) bhuktis

    def test_md_ad_fructification_tiers(self, mainpuri):
        # both lords influence + associated -> par excellence; both -> predominant;
        # one -> limited; neither -> dormant. (Scorpio: Mars owns, Saturn aspects
        # the lord, so Saturn+Mars are associated influencers.)
        assert _pair_tier(mainpuri, 1, "Saturn", "Mercury") == "par excellence"
        assert _pair_tier(mainpuri, 1, "Saturn", "Saturn") == "predominant"
        assert _pair_tier(mainpuri, 1, "Jupiter", "Saturn") == "limited"
        assert _pair_tier(mainpuri, 1, "Rahu", "Moon") == "dormant"
        assert set(ACTIVATION_TIERS) == {
            "par excellence", "predominant", "limited", "dormant"}

    def test_current_tier_and_factor_grouping(self, mainpuri):
        j = judge_house_doctrine(mainpuri, 1, dasha={"md": "Mercury", "ad": "Venus"})
        assert j.timing.current_tier in ACTIVATION_TIERS
        # Raman's (a)-(e): Mars owns the 1st, Venus is posited there.
        fbf = j.timing.influence_by_factor
        assert "Mars" in fbf.get("owns", ())
        assert "Venus" in fbf.get("occupies", ())

    def test_associated_is_conjunction_or_mutual_aspect(self, mainpuri):
        # Sun conjoins the lagna-lord Mars -> associated; a planet is not
        # 'associated' with itself.
        assert _associated(mainpuri, "Mars", "Sun")
        assert not _associated(mainpuri, "Mars", "Mars")


class TestMethodSpine:
    def test_method_records_cited_every_house(self, mainpuri):
        judged = judge_all_houses_doctrine(mainpuri, dasha={"md": "Mercury", "ad": "Mercury"})
        assert set(judged) == set(range(1, 13))
        for h, j in judged.items():
            # the previously-inert method records are now referenced
            assert j.frame_citation
            assert j.timing.method_citation
            assert len(j.method_records_cited) >= 3

    def test_house1_spine_structured(self, mainpuri):
        j = judge_house_doctrine(mainpuri, 1, dasha={"md": "Mercury", "ad": "Mercury"})
        keys = [s.key for s in j.steps]
        assert keys == ["bhava", "lord", "occupants", "karaka", "combinations"]
        assert j.n_fired > 0
        assert j.blend_label in ("favourable", "afflicted", "mixed")


class TestStrengthAssessor:
    def test_verdict_labels(self, mainpuri):
        j = judge_house_doctrine(mainpuri, 1, dasha={"md": "Mercury", "ad": "Mercury"})
        for v in (j.lagna_verdict, j.lord_verdict, j.karaka_verdict):
            assert v.label in _LABELS
            assert v.findings  # every factor is judged from cited findings
            assert all(f.frame in ("Rasi", "Navamsa", "both") for f in v.findings)

    def test_rasi_and_navamsa_cross_check(self, mainpuri):
        # Raman judges each factor in both charts — findings from both frames.
        lord = _assess_lord(mainpuri, 1)
        frames = {f.frame for f in lord.findings}
        assert "Rasi" in frames and "Navamsa" in frames

    def test_mercury_exalted_conjunction_on_lord(self, mainpuri):
        # Lord Mars conjoins Mercury, exalted in Virgo — must be captured (+).
        lord = _assess_lord(mainpuri, 1)
        assert any("Mercury" in f.text and "exalted" in f.text and f.delta > 0
                   for f in lord.findings)

    def test_navamsa_neechabhanga_flip(self, mainpuri):
        # Mars is debilitated in the Navamsa (Cancer) but neechabhanga cancels it.
        lord = _assess_lord(mainpuri, 1)
        assert any("neechabhanga" in f.text and f.delta > 0 for f in lord.findings)

    def test_lagna_occupant_and_navamsa_aspect(self, mainpuri):
        lagna = _assess_bhava(mainpuri, 1)
        assert any("Venus" in f.text and f.frame == "Rasi" for f in lagna.findings)
        assert any(f.frame == "Navamsa" for f in lagna.findings)

    def test_exalted_occupant_credited_not_bare_malefic(self, mainpuri):
        # Phase 2 / increment 1 -- occupant DIGNITY colours the bhava. Mainpuri's
        # 11th holds exalted Mercury (in Virgo): it must be credited as exalted
        # (like an exalted companion in _conjunction_findings), not scored -0.7 as a
        # functional malefic, so the crowded 11th is no longer graded "afflicted".
        b = _assess_bhava(mainpuri, 11)
        exalt = [f for f in b.findings if "occupied by Mercury" in f.text]
        assert exalt and "(exalted)" in exalt[0].text and exalt[0].delta > 1.0
        assert b.label != "afflicted"

    def test_friendly_or_neutral_occupant_stays_on_nature(self, mainpuri):
        # Only high-signal dignities (exalted/own/debilitated) add an occupant
        # dignity term; a plain malefic/benefic occupant keeps its single ±0.7
        # nature finding and gains no extra dignity line.
        b = _assess_bhava(mainpuri, 1)   # Venus in Scorpio: not exalted/own/debil
        venus = [f for f in b.findings if "Venus" in f.text and f.frame == "Rasi"]
        assert len(venus) == 1 and venus[0].criterion == "conjunction"

    def test_dusthana_lord_penalised_lagna_lord_exempt(self, mainpuri):
        # Phase 2.4 -- a planet owning a dusthana (6/8/12) is a functional malefic and
        # afflicted in itself (Raman: "the Moon owns the 6th and hence afflicted").
        # Mainpuri: the 8th lord Mercury (owns Gemini=8th) is penalised; the lagna lord
        # Mars (owns Scorpio=1 AND Aries=6) is EXEMPT -- its ascendant lordship redeems
        # the coincidental 6th ownership (so house-1 stays byte-stable).
        merc = _assess_lord(mainpuri, 8)
        assert any("dusthana lord" in f.text and f.delta < 0 for f in merc.findings)
        mars = _assess_lord(mainpuri, 1)
        assert not any("dusthana lord" in f.text for f in mars.findings)

    def test_exalted_aspect_on_bhava_is_credited(self, mainpuri):
        # Phase 2.3 -- an EXALTED planet aspecting a bhava strengthens it, whatever
        # its functional nature (mirrors conjunct_exalted / occupant-exalted). On
        # Mainpuri, exalted Mercury aspects the 5th: a positive aspect finding, not
        # the -0.35 malefic aspect it scored before.
        b = _assess_bhava(mainpuri, 5)
        asp = [f for f in b.findings
               if "aspected by Mercury" in f.text and f.frame == "Rasi"]
        assert asp and "(exalted)" in asp[0].text and asp[0].delta > 0

    def test_is_benefic_waxing_moon(self, mainpuri):
        # Mainpuri Moon (Aqu 19) vs Sun (Vir 26): elongation ~ 142 -> waxing -> benefic
        assert _is_benefic(mainpuri, "Moon")
        assert _is_benefic(mainpuri, "Jupiter")
        assert not _is_benefic(mainpuri, "Saturn")

    def test_influence_factors_specific(self, mainpuri):
        # Mars owns the 1st; Mercury conjoins the lord; Venus occupies.
        assert _influence_factors(mainpuri, 1, "Mars") == ("owns",)
        assert "conjoins lord" in _influence_factors(mainpuri, 1, "Mercury")
        assert "occupies" in _influence_factors(mainpuri, 1, "Venus")

    def test_kartari_shapes(self, mainpuri):
        kind, occ2, occ12 = _kartari(mainpuri, 1)
        assert kind in (None, "papa", "subha")

    def test_conclusion_ranks_and_synthesizes(self, mainpuri):
        j = judge_house_doctrine(mainpuri, 1, dasha={"md": "Mercury", "ad": "Mercury"})
        c = j.conclusion
        assert c.label in _LABELS
        assert c.influencers  # the five-factor influencers, ranked
        assert "influencing the 1st house" in c.synthesis
        assert "1th" not in c.synthesis  # ordinal bug guard
        # afflicted (malefic) influencers surfaced for timed caution
        assert set(c.afflicted_activators) <= {i.planet for i in c.influencers}

    def test_verdict_label_thresholds(self):
        # 9-grade scale decoded from Raman's ch. IV worked charts.
        assert _verdict_label(3.5) == "very powerful"
        assert _verdict_label(1.3) == "fairly powerful"
        assert _verdict_label(0.6) == "fairly good"
        assert _verdict_label(0.0) == "moderate"
        assert _verdict_label(-2.0) == "afflicted"

    def test_positive_soft_cap(self):
        # Consolidation: stacked positives suffer diminishing returns past the
        # knee (1.6), so a planet does not reach the top grade from placement +
        # dignity + conjunction alone. A single strong positive is untouched;
        # the negative side stays linear.
        one = [Finding("own sign", 1.2, "Rasi", "dignity")]
        assert _combine(one, additive=False)[0] == 1.2          # <= knee, unchanged
        stacked = [Finding("kendra", 1.2, "Rasi", "placement"),
                   Finding("exalted", 1.6, "Rasi", "dignity"),
                   Finding("conjunct benefic", 0.7, "Rasi", "conjunction")]
        raw = 1.2 + 1.6 + 0.7                                    # 3.5 additive-style
        capped = _combine(stacked, additive=False)[0]
        assert capped < raw and capped < 2.0                    # compressed toward the ceiling
        # negatives are NOT capped — an afflicted bhava stays afflicted (additive).
        afflicted = [Finding("debilitated", -1.6, "Rasi", "dignity"),
                     Finding("dusthana", -1.0, "Rasi", "placement")]
        assert _combine(afflicted, additive=True)[0] == -2.6


class TestCalibration:
    """The weighting is DECODED from Raman's worked charts (HTJAH ch. IV, Charts
    12-14; scratchpad/htjah_h1_calibration.json) and must reproduce his stated
    per-factor verdicts within one grade."""

    def test_mild_frame_does_not_rescue_a_deeply_afflicted_one(self):
        # Phase 2.5 -- a DEEPLY-afflicted frame (< -1.0) is not fully rescued by a
        # merely-mild opposite frame: the optimistic 30% discount is withheld
        # (Raman grades such a karaka "afflicted", not "moderately good"). A MILDLY
        # afflicted frame is still rescued as before, keeping the change narrow.
        deep = [Finding("deep affliction", -1.5, "Rasi", "dignity"),
                Finding("mild plus", 0.8, "Navamsa", "dignity")]
        score, _r, _n = _combine(deep, additive=False)
        assert score < -0.3            # NOT rescued to a positive "moderately good"
        mild = [Finding("mild affliction", -0.6, "Rasi", "dignity"),
                Finding("nav plus", 0.9, "Navamsa", "dignity")]
        score2, _r2, _n2 = _combine(mild, additive=False)
        assert score2 > 0.5            # a mild affliction is still optimistically rescued

    def test_unassessed_frame_does_not_rescue_affliction(self):
        # Phase 2.2 -- an UN-assessed varga must not stand in as a phantom 0 that
        # rescues an afflicted Rasi via the optimistic blend. A planet with only
        # Rasi findings, net negative, keeps its Rasi score (not 0.3x it upward).
        rasi_only = [Finding("dusthana", -1.0, "Rasi", "placement"),
                     Finding("exalted", 1.6, "Rasi", "dignity"),
                     Finding("papakartari", -1.0, "Rasi", "kartari"),
                     Finding("malefic aspect", -0.7, "Rasi", "aspect")]
        score, rasi, nav = _combine(rasi_only, additive=False)
        assert nav == 0.0 and rasi < -1.0
        assert score == rasi           # NOT rescued to 0.3 * rasi
        assert _verdict_label(score) in ("afflicted", "weak")

    def test_navamsa_redeems_afflicted_lord(self):
        # Chart 12 (Capricorn): Saturn (lord) is bad on EVERY Rasi count — 8th
        # (dusthana), enemy sign, aspected by malefic Moon — yet Raman calls the
        # lord "fairly good" because in the Navamsa it is with Jupiter in a
        # friend's sign. The optimistic cross-varga combine must reproduce that.
        findings = (
            Finding("placed in the 8th (dusthana)", -1.0, "Rasi", "placement"),
            Finding("Saturn in a inimical sign", -0.8, "Rasi", "dignity"),
            Finding("aspected by Moon (malefic)", -0.7, "Rasi", "aspect"),
            Finding("Saturn in a friendly sign", 0.8, "Navamsa", "dignity"),
            Finding("conjunct Jupiter (benefic)", 0.7, "Navamsa", "conjunction"),
        )
        score, rasi, nav = _combine(findings, additive=False)
        assert rasi < -1.5 and nav > 0.5          # Rasi bad, Navamsa good
        assert _verdict_label(score) == "fairly good"   # Raman's verdict

    def test_bhava_is_additive_not_optimistic(self):
        # The BHAVA blends its vargas additively (a mild Navamsa boon adds to,
        # not replaces, the Rasi reading) — Chart 12 ascendant: nothing in Rasi,
        # a Jupiter aspect in the Navamsa -> "moderate", not lifted to good.
        findings = (
            Finding("occupied by no planet", 0.0, "Rasi", "conjunction"),
            Finding("aspected by no planet", 0.0, "Rasi", "aspect"),
            Finding("aspected by Jupiter (benefic)", 0.35, "Navamsa", "aspect"),
        )
        score, rasi, nav = _combine(findings, additive=True)
        assert score == pytest.approx(0.35)
        assert _verdict_label(score) in ("moderate", "moderately good")

    def test_functional_malefic_precedence(self, mainpuri):
        # Scorpio lagna: Venus rules 7 & 12 -> a functional malefic though a
        # NATURAL benefic; the classifier must call it malefic (two-malefic rule).
        ben, tag = _planet_nature(mainpuri, "Venus")
        assert ben is False and tag == "functional malefic"
        # Jupiter rules 2 & 5 -> functional benefic for Scorpio.
        jben, jtag = _planet_nature(mainpuri, "Jupiter")
        assert jben is True and jtag == "functional benefic"

    def test_functional_benefic_overrides_natural_malefic(self):
        # Saturn is a NATURAL malefic but the yogakaraka for Libra lagna: benefic.
        from app.medini.doctrine import raman_chart as rc
        libra = rc.from_printed_positions(
            {"Sun": 10.0, "Moon": 40.0, "Mars": 70.0, "Mercury": 15.0,
             "Jupiter": 100.0, "Venus": 20.0, "Saturn": 130.0,
             "Rahu": 200.0, "Ketu": 20.0},
            185.0, birth_jd=MAINPURI["jd"])   # ~Libra ascendant
        ben, tag = _planet_nature(libra, "Saturn")
        assert ben is True and tag == "yogakaraka"


class TestFirstHouseTestimony:
    """Signs-Ascending preamble (HTJAH pp. 30-31): mind by the Moon, health by
    Sun + Moon + Lagna. The rising sign's own nature is NOT scored."""

    def test_present_only_for_house_one(self, mainpuri):
        j1 = judge_house_doctrine(mainpuri, 1, dasha={"md": "Mercury", "ad": "Mercury"})
        j2 = judge_house_doctrine(mainpuri, 2, dasha={"md": "Mercury", "ad": "Mercury"})
        assert j1.first_house is not None
        assert j2.first_house is None

    def test_mind_judged_by_moon(self, mainpuri):
        t = judge_house_doctrine(mainpuri, 1).first_house
        assert t.mind_verdict in VERDICT_SCALE
        assert "Moon" in t.mind_note
        assert t.citation.startswith("How to Judge a Horoscope")

    def test_health_flag_shape(self, mainpuri):
        t = judge_house_doctrine(mainpuri, 1).first_house
        assert isinstance(t.health_flag, bool)
        # a raised flag must name more than one afflicting malefic
        if t.health_flag:
            assert len(t.afflicting_malefics) > 1


class TestChandraLagna:
    """The house judged from the Moon (Chandra Lagna) on the same lines as the
    Lagna — Raman's method throughout HTJAH (82 'from the Moon' references)."""

    def test_present_on_every_house(self, mainpuri):
        judged = judge_all_houses_doctrine(mainpuri, dasha={"md": "Mercury", "ad": "Mercury"})
        for h, j in judged.items():
            assert j.chandra is not None
            assert j.chandra.reference.startswith("Chandra Lagna")

    def test_lord_from_moon_is_moon_sign_lord(self, mainpuri):
        # Mainpuri Moon is in Aquarius (sign 11) -> lord Saturn.
        assert _lord_from_moon(mainpuri, 1) == "Saturn"
        cm = judge_house_doctrine(mainpuri, 1).chandra
        assert cm.reference_sign == 11 and cm.lord_planet == "Saturn"

    def test_bhava_and_lord_graded(self, mainpuri):
        cm = _assess_from_moon(mainpuri, 1)
        assert cm.bhava.label in VERDICT_SCALE
        assert cm.lord.label in VERDICT_SCALE
        # Chandra Lagna (Aquarius) carries Rahu with the Moon -> afflicted. The Moon
        # itself defines the lagna and is not counted as its own occupant-affliction.
        assert any("Rahu" in f.text for f in cm.bhava.findings)
        assert not any("occupied by Moon" in f.text for f in cm.bhava.findings)

    def test_functional_nature_read_from_chandra_lagna(self, mainpuri):
        # From Aquarius, the Moon rules the 6th -> a functional malefic 'from the
        # Moon', though a natural benefic. (Contrast: from the Lagna it may differ.)
        ben_moon_ref, tag = _planet_nature(mainpuri, "Moon", ref_sign=11)
        assert ben_moon_ref is False and tag == "functional malefic"

    def test_factor_f_lord_from_moon_is_an_influencer(self, mainpuri):
        j = judge_house_doctrine(mainpuri, 1, dasha={"md": "Mercury", "ad": "Mercury"})
        assert "Saturn" in j.timing.influencers
        assert "Saturn" in j.timing.influence_by_factor.get("lord from Moon", ())
        assert "lord from Moon" in _influence_factors(mainpuri, 1, "Saturn")


class TestCombinations:
    """Raman's named combinations (yogas) for the house — compound antecedents are
    recognised as combinations and surfaced with their result text (HTJAH ch. IV)."""

    def _rule(self, ante, rt="graha_effect", timing=None):
        return {"rule_type": rt, "antecedent": ante,
                "consequent": {"timing": timing, "polarity": "favorable"}}

    def test_compound_yoga_detected(self):
        # 'benefics in 1, 11, 12 with the lagna lord in a trikona' -> a combination.
        yoga = self._rule({"op": "all", "args": [
            {"op": "planet_in_house", "planet": "benefic", "house": 1},
            {"op": "planet_in_house", "planet": "benefic", "house": 11},
            {"op": "lord_of_house_in_house", "of_house": 1, "in_house": [1, 5, 9]}]})
        assert _is_combination(yoga)
        assert _classify(yoga, 1) == "combinations"

    def test_single_factor_is_not_a_combination(self):
        # a lone planet-in-house is an Occupant, not a combination.
        simple = self._rule({"op": "planet_in_house", "planet": "Sun", "house": 1})
        assert not _is_combination(simple)
        assert _classify(simple, 1) == "occupants"

    def test_compound_yoga_not_stolen_by_occupants(self):
        # a multi-placement yoga that MENTIONS a planet in house 1 must still be a
        # combination, not mis-filed under Occupants.
        yoga = self._rule({"op": "all", "args": [
            {"op": "planet_in_house", "planet": "Mars", "house": 1},
            {"op": "planet_in_house", "planet": "Saturn", "house": 7}]})
        assert _classify(yoga, 1) == "combinations"

    def test_mainpuri_surfaces_lagnalord_11_combination(self, mainpuri):
        # Scorpio lagna: Mars (lagna lord) and Mercury (11th lord) both in the 11th
        # -> Raman's 'lagna lord joins the 11th lord in the 11th', gain from trade,
        # manifesting in the lagna-lord's (Mars) dasa.
        j = judge_house_doctrine(mainpuri, 1, dasha={"md": "Mars", "ad": "Mars"})
        ids = [c.rule_id for c in j.combinations]
        assert any("lagnalord_11_with_lord11" in i for i in ids)
        c = next(c for c in j.combinations if "lagnalord_11_with_lord11" in c.rule_id)
        assert c.dasha_lord == "Mars" and c.active_now is True
        assert c.polarity == "favorable"

    def test_combinations_have_text_and_polarity(self, mainpuri):
        j = judge_house_doctrine(mainpuri, 1, dasha={"md": "Mercury", "ad": "Mercury"})
        assert j.combinations
        for c in j.combinations:
            assert c.text and c.polarity in ("favorable", "unfavorable", "mixed")


class TestChapterRules:
    """A house reads its own HTJAH chapter (ch. V = 2nd house) irrespective of the
    coarse topic-domain tag, so its eye/speech/learning sutras fire (they would be
    missed by the wealth-only domain sweep)."""

    def test_new_ch5_sutras_are_encoded(self):
        from app.medini.doctrine.compendium import load_compendium
        ids = {r["id"] for r in load_compendium()["htjah_vol1"] if ".ch5." in r["id"]}
        for slug in ("mars_moon_2_mathematician",
                     "sun_moon_aspected_jupiter_venus_debator",
                     "lord12_in_2_or_lord2_in_12_penalty",
                     "jupiter_venus_mercury_exalted_2_supports_men"):
            assert f"raman.htjah_vol1.ch5.{slug}" in ids

    def test_house2_reads_ch5_health_body_rule(self, mainpuri):
        # saturn_2_bad_eyesight is tagged health_body (house-1's domain) yet is a
        # ch5 rule -> it must now fire in the 2nd-house judgment via the chapter map.
        j = judge_house_doctrine(mainpuri, 2, dasha={"md": "Mercury", "ad": "Mercury"})
        fired = {e.rule_id for s in j.steps for e in s.evidence}
        assert any("saturn_2_bad_eyesight" in i for i in fired)

    def test_house2_surfaces_new_debator_combination(self, mainpuri):
        # Sun/Moon aspected by Jupiter or Venus is present on this chart.
        j = judge_house_doctrine(mainpuri, 2, dasha={"md": "Mercury", "ad": "Mercury"})
        assert any("debator" in c.rule_id for c in j.combinations)

    def test_house1_unchanged_by_chapter_map(self, mainpuri):
        # House 1 is deliberately absent from HOUSE_CHAPTERS -> its verdicts stand.
        j = judge_house_doctrine(mainpuri, 1, dasha={"md": "Mercury", "ad": "Mercury"})
        assert j.lagna_verdict.label == "very powerful"
        assert j.lord_verdict.label == "fairly good"
        assert j.conclusion.label == "fairly strong"

    def test_house3_reads_ch6(self, mainpuri):
        # HOUSE_CHAPTERS[3] -> the 3rd house reads its own ch. VI rules.
        j = judge_house_doctrine(mainpuri, 3, dasha={"md": "Mercury", "ad": "Mercury"})
        fired = {e.rule_id for s in j.steps for e in s.evidence}
        assert any(".ch6." in i for i in fired)

    def test_house4_reads_ch7(self, mainpuri):
        # HOUSE_CHAPTERS[4] -> the 4th house reads its own ch. VII rules.
        j = judge_house_doctrine(mainpuri, 4, dasha={"md": "Mercury", "ad": "Mercury"})
        fired = {e.rule_id for s in j.steps for e in s.evidence}
        assert any(".ch7." in i for i in fired)

    def test_house5_reads_ch8(self, mainpuri):
        # HOUSE_CHAPTERS[5] -> the 5th house reads its own ch. VIII rules.
        j = judge_house_doctrine(mainpuri, 5, dasha={"md": "Mercury", "ad": "Mercury"})
        fired = {e.rule_id for s in j.steps for e in s.evidence}
        assert any(".ch8." in i for i in fired)

    def test_house6_reads_ch9(self, mainpuri):
        # HOUSE_CHAPTERS[6] -> the 6th house reads its own ch. IX rules.
        j = judge_house_doctrine(mainpuri, 6, dasha={"md": "Mercury", "ad": "Mercury"})
        fired = {e.rule_id for s in j.steps for e in s.evidence}
        assert any(".ch9." in i for i in fired)

    def test_house7_reads_ch11(self, mainpuri):
        # HOUSE_CHAPTERS[7] -> the 7th house reads its own ch. XI rules, which
        # live in vol. TWO of the compendium (houses 7-12 -> ch. XI-XVI).
        j = judge_house_doctrine(mainpuri, 7, dasha={"md": "Mercury", "ad": "Mercury"})
        fired = {e.rule_id for s in j.steps for e in s.evidence}
        assert any(".ch11." in i for i in fired)

    def test_house7_reads_cross_domain_ch11_from_vol2(self):
        # The chapter map must span BOTH htjah volumes: the ch. XI sutra
        # "7th lord in the 10th" is tagged domain=career, so the marriage-only
        # domain sweep would miss it -- it reaches the 7th house solely via the
        # vol-two chapter scan. Lagna Aries -> 7th lord Venus, placed in the 10th.
        pos = {"Sun": 20.0, "Moon": 50.0, "Mars": 100.0, "Mercury": 30.0,
               "Jupiter": 130.0, "Venus": 280.0, "Saturn": 200.0,
               "Rahu": 160.0, "Ketu": 340.0}
        chart = rc.from_printed_positions(pos, 5.0, birth_jd=MAINPURI["jd"])
        j = judge_house_doctrine(chart, 7, dasha={"md": "Venus", "ad": "Venus"})
        fired = {e.rule_id for s in j.steps for e in s.evidence}
        assert any("ch11.lord7_in_10" in i for i in fired)

    def test_house8_reads_ch12(self, mainpuri):
        # HOUSE_CHAPTERS[8] -> the 8th house reads its own ch. XII rules (vol. II).
        j = judge_house_doctrine(mainpuri, 8, dasha={"md": "Mercury", "ad": "Mercury"})
        fired = {e.rule_id for s in j.steps for e in s.evidence}
        assert any(".ch12." in i for i in fired)

    def test_house9_reads_ch13(self, mainpuri):
        # HOUSE_CHAPTERS[9] -> the 9th house reads its own ch. XIII rules (vol. II).
        j = judge_house_doctrine(mainpuri, 9, dasha={"md": "Mercury", "ad": "Mercury"})
        fired = {e.rule_id for s in j.steps for e in s.evidence}
        assert any(".ch13." in i for i in fired)

    def test_house10_reads_ch14(self, mainpuri):
        # HOUSE_CHAPTERS[10] -> the 10th house reads its own ch. XIV rules (vol. II).
        j = judge_house_doctrine(mainpuri, 10, dasha={"md": "Mercury", "ad": "Mercury"})
        fired = {e.rule_id for s in j.steps for e in s.evidence}
        assert any(".ch14." in i for i in fired)

    def test_house11_reads_ch15(self, mainpuri):
        # HOUSE_CHAPTERS[11] -> the 11th house reads its own ch. XV rules (vol. II).
        j = judge_house_doctrine(mainpuri, 11, dasha={"md": "Mercury", "ad": "Mercury"})
        fired = {e.rule_id for s in j.steps for e in s.evidence}
        assert any(".ch15." in i for i in fired)

    def test_house12_reads_ch16(self, mainpuri):
        # HOUSE_CHAPTERS[12] -> the 12th house reads its own ch. XVI rules (vol. II).
        j = judge_house_doctrine(mainpuri, 12, dasha={"md": "Mercury", "ad": "Mercury"})
        fired = {e.rule_id for s in j.steps for e in s.evidence}
        assert any(".ch16." in i for i in fired)


class TestInterpretGrounding:
    """The LLM interpretation layer's grounding packet — the anti-hallucination
    contract. These exercise serialization only (no API key, no network): the
    reading Claude produces must be traceable to exactly this evidence."""

    def test_packet_carries_the_three_testimonies_and_headline(self, mainpuri):
        from app.medini.doctrine.interpret import build_grounding
        hj = judge_house_doctrine(mainpuri, 1)
        p = build_grounding(hj)
        # Raman's house verdict is the Lagna+lord+karaka synthesis, not the raw
        # sutra-polarity blend -- the two must be reported as distinct fields.
        assert p["headline_verdict"] == hj.conclusion.label
        assert p["sutra_polarity_blend"]["label"] == hj.blend_label
        for role in ("bhava", "lord", "karaka"):
            assert p[role]["verdict"] in _LABELS
            assert p[role]["findings"]  # every testimony shows its evidence

    def test_findings_and_sutras_are_verbatim_and_traceable(self, mainpuri):
        from app.medini.doctrine.interpret import build_grounding
        hj = judge_house_doctrine(mainpuri, 1)
        p = build_grounding(hj)
        # Each fired sutra is the engine's verbatim text keyed by its rule id.
        fired_ids = {e.rule_id for s in hj.steps for e in s.evidence}
        assert {s["id"] for s in p["fired_sutras"]} <= fired_ids
        assert all(s["text"] for s in p["fired_sutras"])
        # Findings preserve the signed contribution the verdict was built from.
        f0 = p["bhava"]["findings"][0]
        assert set(f0) == {"observation", "contribution", "frame", "criterion"}

    def test_first_house_and_from_moon_present_for_house1(self, mainpuri):
        from app.medini.doctrine.interpret import build_grounding
        p = build_grounding(judge_house_doctrine(mainpuri, 1))
        assert "first_house_testimony" in p and "from_moon" in p
        assert p["from_moon"]["reference"].startswith("Chandra")

    def test_compact_grounding_bounds_findings_for_whole_chart(self, mainpuri):
        from app.medini.doctrine.interpret import build_grounding, _compact_grounding
        c = _compact_grounding(build_grounding(judge_house_doctrine(mainpuri, 1)))
        # Whole-chart synthesis keeps only the strongest findings per testimony.
        for role in ("bhava", "lord", "karaka"):
            assert len(c["key_findings"][role]) <= 3
        assert c["headline_verdict"] in _LABELS


class TestChartGroundingCostAndTiming:
    """The de-duplicated whole-chart grounding (lossless + cheap) and the dasa
    resolver that time-anchors it. Serialization/arithmetic only -- no API key."""

    def test_planets_deduped_and_houses_reference_them(self, mainpuri):
        from app.medini.doctrine.interpret import build_chart_grounding
        J = judge_all_houses_doctrine(mainpuri)
        g = build_chart_grounding(J)
        # Each planet appears once in the dossier, keyed by its own name.
        for name, dossier in g["planets"].items():
            assert dossier["planet"] == name
        # Every house's lord/karaka is a name resolvable in the dossier.
        for h in g["houses"]:
            assert h["lord"] in g["planets"]
            assert h["karaka"] in g["planets"]
        # Dedup is real: 12 houses x 2 role-slots collapse onto <=9 planets.
        assert len(g["planets"]) <= 9

    def test_grounding_is_lossless_for_lord_and_karaka_findings(self, mainpuri):
        from app.medini.doctrine.interpret import (
            build_chart_grounding, build_grounding)
        J = judge_all_houses_doctrine(mainpuri)
        g = build_chart_grounding(J)
        dossier = {(f["observation"], f["contribution"])
                   for p in g["planets"].values() for f in p["findings"]}
        # No lord/karaka finding is dropped in the collapse -- the dossier is a
        # superset of every per-house lord/karaka finding.
        for h in range(1, 13):
            p = build_grounding(J[h])
            for role in ("lord", "karaka"):
                for f in p[role]["findings"]:
                    assert (f["observation"], f["contribution"]) in dossier

    def test_resolver_picks_bracketing_period(self, mainpuri):
        from app.medini.doctrine.interpret import resolve_current_dasha
        birth_jd = MAINPURI["jd"]
        target = birth_jd + 36.73 * 365.2425  # ~age 36.73
        d = resolve_current_dasha(mainpuri, birth_jd, target)
        assert d["md"] and d["ad"]
        # The running MD's window brackets the target age.
        cur = [w for w in d["windows"] if w["is_current"]]
        assert len(cur) == 1
        s, e = cur[0]["age_span"]
        assert s <= d["age"] < e
        # Exactly one antardasa is current, inside the current MD.
        cad = [a for w in d["windows"] for a in w["antardashas"] if a["is_current"]]
        assert len(cad) == 1 and cad[0]["lord"] == d["ad"]

    def test_resolver_feeds_engine_current_period(self, mainpuri):
        from app.medini.doctrine.interpret import resolve_current_dasha
        birth_jd = MAINPURI["jd"]
        d = resolve_current_dasha(mainpuri, birth_jd, birth_jd + 36.73 * 365.2425)
        # Passing the resolved md/ad populates the engine's current-period fields.
        J = judge_all_houses_doctrine(mainpuri, dasha={"md": d["md"], "ad": d["ad"]})
        assert J[1].timing.current_md == d["md"]
        assert J[1].timing.current_tier in ACTIVATION_TIERS

    def test_chart_readings_schema_validates_and_rejects(self):
        import pydantic
        from app.medini.doctrine.interpret import ChartReadings
        ok = ChartReadings(readings=[{"house": h, "reading": f"r{h}"}
                                     for h in range(1, 13)])
        assert len(ok.readings) == 12
        # House number out of the 1..12 range is rejected by the schema.
        with pytest.raises(pydantic.ValidationError):
            ChartReadings(readings=[{"house": 13, "reading": "x"}])
