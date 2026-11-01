"""Krishnamurti's horary question registry (KP Reader 6) and level E significators."""

from __future__ import annotations

import pytest

from app.kp.chart import Birth, cast, sign_index
from app.kp.citations import CITATIONS
from app.kp.horary import questions as Q
from app.kp.horary.cast import cast_horary
from app.kp.significators import DRISHTI, LEVEL_CITE, _aspects, planet_significations

MADRAS = Birth(1969, 12, 11, 10, 0, tz=5.5, lat=13.08, lon=80.27)
ALIBAG = Birth(1924, 12, 23, 21, 0, tz=5.5, lat=18 + 39 / 60, lon=72 + 55 / 60)


class TestRegistry:
    def test_every_question_is_cited_in_reader6(self) -> None:
        """Each of the 35 rules points at a Reader 6 quote."""
        assert len(Q.QUESTIONS) == 35
        for q in Q.QUESTIONS.values():
            assert CITATIONS[q.citation].source == "KPR6", q.key

    def test_no_death_or_lifespan_questions(self) -> None:
        """Death, lifespan, suicide and murder rules are never encoded (ruling R20)."""
        for q in Q.QUESTIONS.values():
            text = (q.key + " " + q.label).lower()
            assert not any(w in text for w in ("death", "die", "life span", "lifespan", "suicide", "murder"))

    def test_and_groups_need_every_house(self) -> None:
        """'6 and 11' is two groups: both houses needed; '6 or 11' is one group: either suffices."""
        and_ = (frozenset({6}), frozenset({11}))
        or_ = (frozenset({6, 11}),)
        assert Q._meets(frozenset({6, 11, 3}), and_)
        assert not Q._meets(frozenset({6, 3}), and_)
        assert Q._meets(frozenset({11}), or_)
        assert not Q._meets(frozenset({1, 2}), or_)
        assert not Q._meets(frozenset({1, 2}), ())

    def test_appeal_reads_six_and_eleven(self) -> None:
        """KPR6 p.168: success needs the star lord to signify 6 and 11; failure 5 and 12."""
        q = Q.QUESTIONS["appeal"]
        assert q.cusp == 3 and q.via == "star"
        assert q.yes == (frozenset({6}), frozenset({11}))
        assert q.no == (frozenset({5}), frozenset({12}))


class TestJudgement:
    @pytest.mark.parametrize("key", sorted(Q.QUESTIONS))
    def test_verdict_follows_the_rule(self, key: str) -> None:
        """Every rule gives one of four verdicts consistent with its own house groups."""
        chart = cast_horary(48, MADRAS)
        a = Q.judge_question(chart, key)
        q = a.question
        assert a.csl == chart.cusp(q.cusp).sub_lord
        assert a.star_lord == chart.planets[a.csl].star_lord
        assert a.judged_planet == (a.star_lord if q.via == "star" else a.csl)
        assert a.verdict in (Q.YES, Q.NO, Q.MIXED, Q.NOT_SIGNIFIED)
        if a.verdict in (Q.YES, Q.MIXED):
            assert Q._meets(a.judged_houses, q.yes)
        d = a.to_dict()
        assert "not a validated prediction" in d["framing"]

    def test_retrograde_fails_children_as_no(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """KPR6: a retrograde 5th CSL (or its star lord) denies the child outright."""
        chart = cast_horary(48, MADRAS)
        monkeypatch.setattr(Q, "_retro", lambda c, p: True)
        assert Q.judge_question(chart, "children").verdict == Q.NO

    def test_dual_condition(self) -> None:
        """KPR6 p.165: Mercury as CSL always meets the dual-sign condition."""
        chart = cast_horary(48, MADRAS)
        assert Q._dual(chart, "Mercury")
        for p in ("Sun", "Moon", "Mars", "Venus", "Saturn"):
            star = chart.planets[p].star_lord
            expect = (sign_index(chart.planets[p].longitude) in Q.DUAL_SIGNS
                      or star in ("Mercury", "Jupiter")
                      or sign_index(chart.planets[star].longitude) in Q.DUAL_SIGNS)
            assert Q._dual(chart, p) == expect, p


class TestLevelE:
    def test_default_ladder_unchanged(self) -> None:
        """Without the flag no level E rows appear (Krishnamurti's Alibag table stays exact)."""
        c = cast(ALIBAG)
        assert all(s.level != "E" for rows in planet_significations(c).values() for s in rows)

    def test_level_e_only_adds_new_houses(self) -> None:
        """KPR5 p.153 level (5): E rows add houses a planet does not already hold at A-D."""
        c = cast(ALIBAG)
        base = planet_significations(c)
        full = planet_significations(c, level_e=True)
        for p in base:
            assert full[p][:len(base[p])] == base[p]
            held = {s.house for s in base[p]}
            for s in full[p][len(base[p]):]:
                assert s.level == "E" and s.house not in held
                same = sign_index(c.planets[s.via].longitude) == sign_index(c.planets[p].longitude)
                assert same or _aspects(c, s.via, p)

    def test_special_aspects(self) -> None:
        """KPR6 p.288: Saturn aspects by its 10th, Jupiter by its 5th; the nodes cast none."""
        assert 10 in DRISHTI["Saturn"] and 3 in DRISHTI["Saturn"]
        assert 5 in DRISHTI["Jupiter"] and 9 in DRISHTI["Jupiter"]
        assert DRISHTI["Mars"] == (4, 7, 8)
        assert "Rahu" not in DRISHTI and "Ketu" not in DRISHTI
        assert LEVEL_CITE["E"] in CITATIONS and "KPR6-DRISHTI" in CITATIONS
