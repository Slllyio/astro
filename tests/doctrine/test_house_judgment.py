"""Raman's HTJAH ch. IV judgment method, executed (pure doctrine).

Covers the bucket classifier, the five-factor timing sub-verdict + dasa
windows + current-period activation, and that the previously-inert ``method``
records are now cited by every house judgment.
"""
import pytest

from app.medini.doctrine import raman_chart as rc
from app.medini.doctrine.domains.house_judgment import (
    _assess_bhava, _assess_karaka, _assess_lord, _classify, _influence_factors,
    _is_benefic, _kartari, _maha_sequence, _verdict_label,
    judge_all_houses_doctrine, judge_house_doctrine,
)

_LABELS = {"afflicted", "weak", "moderate", "fairly good", "good", "powerful"}

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
        assert _verdict_label(3.5) == "powerful"
        assert _verdict_label(0.0) == "moderate"
        assert _verdict_label(-2.0) == "afflicted"
