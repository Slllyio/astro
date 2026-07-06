"""Raman's HTJAH ch. IV judgment method, executed (pure doctrine).

Covers the bucket classifier, the five-factor timing sub-verdict + dasa
windows + current-period activation, and that the previously-inert ``method``
records are now cited by every house judgment.
"""
import pytest

from app.medini.doctrine import raman_chart as rc
from app.medini.doctrine.domains.house_judgment import (
    _classify, _maha_sequence, judge_all_houses_doctrine, judge_house_doctrine,
)

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
