"""Krishnamurti's horary question rules (KP Reader 6), one registry entry per rule he states.

Each rule in Reader 6 takes the sub-lord of one cusp (the CSL) and asks which
houses are signified either by the planet in whose star the CSL is deposited
(``via="star"``: "If the sub-lord of the 3rd cusp is deposited in the
constellation of a planet which is the significator of 6 and 11 ...") or by
the CSL itself (``via="csl"``). He writes the house conditions with "and" and
"or"; the engine keeps them as printed (ruling RH7): ``yes`` and ``no`` are
lists of groups, and every group needs at least one hit, so "6 and 11" is
``({6}, {11})`` and "6 or 11" is ``({6, 11},)``.

``need_direct``: the CSL and its star lord must be in direct motion (nodes are
never retrograde, KPR6 p.105). ``fail_means_no``: he states that failing the
condition gives "no" (children, lottery, promotion, going abroad, second
marriage); elsewhere failing the yes-condition is only "not signified".
Conditions he adds that need an undefined "connected in any manner" (with
Saturn, Mars, ...) are listed in ``unevaluated`` and reported, never guessed.

Questions about death, lifespan, suicide or murder are not in the registry
(ruling R20 and the project rule); the vehicle rule (p.181) is omitted because
it rests on such a "connection with Venus".

Usage:
    from app.kp.chart import Birth
    from app.kp.horary.questions import QUESTIONS, answer
    a = answer(48, Birth(1969, 12, 11, 10, 0, tz=5.5, lat=13.08, lon=80.27), "appeal")
    print(a.to_dict())
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.kp.chart import NODES, Birth, KPChart, sign_index
from app.kp.citations import CITATIONS
from app.kp.horary.cast import cast_horary
from app.kp.significators import houses_signified, planet_significations

YES: Final = "YES"
NO: Final = "NO"
MIXED: Final = "MIXED"
NOT_SIGNIFIED: Final = "NOT_SIGNIFIED"

#: Dual (common) signs: Gemini, Virgo, Sagittarius, Pisces (0-based indices).
DUAL_SIGNS: Final = frozenset({2, 5, 8, 11})


@dataclass(frozen=True, slots=True)
class Question:
    key: str
    label: str
    cusp: int
    via: str
    yes: tuple[frozenset[int], ...]
    no: tuple[frozenset[int], ...]
    no_via: str | None
    need_direct: bool
    fail_means_no: bool
    special: str | None
    unevaluated: str | None
    citation: str


QUESTIONS: Final[dict[str, Question]] = {q.key: q for q in (
    Question("illness", 'Will an ailment come (6th sub-lord)?', 6, "star", (frozenset({6}), frozenset({1}), ), (frozenset({11}), ), None, False, False, None, 'Saturn connection = chronic, Mars = acute, Mercury = complications (nature of disease, not evaluated)', "KPR6-Q-ILLNESS"),
    Question("second_marriage", 'Is there a second marriage?', 7, "csl", (frozenset({2, 11}), ), (), None, False, True, 'dual', None, "KPR6-Q-SECOND_MARRIAGE"),
    Question("appeal", 'Will the appeal succeed?', 3, "star", (frozenset({6}), frozenset({11}), ), (frozenset({5}), frozenset({12}), ), None, False, False, None, None, "KPR6-Q-APPEAL"),
    Question("exchange_6", 'Shall I exchange my article profitably (6th cusp)?', 6, "star", (frozenset({11, 6}), ), (frozenset({12, 5}), ), None, False, False, None, None, "KPR6-Q-EXCHANGE_6"),
    Question("exchange_12", 'Shall I exchange my article profitably (12th cusp)?', 12, "star", (frozenset({6}), frozenset({11}), ), (frozenset({5}), frozenset({12}), ), None, False, False, None, None, "KPR6-Q-EXCHANGE_12"),
    Question("treasure", 'Any treasure in my building?', 4, "star", (frozenset({2, 11, 6}), ), (), None, False, False, None, 'the star lord should also be connected with Saturn in direct motion (not evaluated)', "KPR6-Q-TREASURE"),
    Question("love_affair", 'Will my love affair materialise?', 5, "star", (frozenset({7}), frozenset({11}), ), (frozenset({12, 6}), ), None, False, False, None, None, "KPR6-Q-LOVE_AFFAIR"),
    Question("child_recovery", 'Will the invalid child pick up health?', 5, "star", (frozenset({3}), frozenset({5}), ), (), None, False, False, None, 'denial: star lord signifies 10 and is connected with Saturn (not evaluated)', "KPR6-Q-CHILD_RECOVERY"),
    Question("business_partner", 'Can I have a partner in my business?', 8, "star", (frozenset({6}), frozenset({11}), ), (frozenset({5}), frozenset({12}), ), None, False, False, None, None, "KPR6-Q-BUSINESS_PARTNER"),
    Question("actor", 'Can I prosper as an actor or actress?', 5, "star", (frozenset({5}), frozenset({6}), frozenset({10}), ), (), None, False, False, None, 'also signifying 11 = prosperous; Mars among them = a leader (not evaluated)', "KPR6-Q-ACTOR"),
    Question("children", 'Any child for me?', 5, "csl", (frozenset({2, 11, 5}), ), (), None, True, True, None, None, "KPR6-Q-CHILDREN"),
    Question("lottery", 'Can I gain in the lottery?', 11, "csl", (frozenset({2, 11, 6}), ), (), None, True, True, None, None, "KPR6-Q-LOTTERY"),
    Question("partnership", 'Will the partnership continue?', 7, "csl", (frozenset({5}), frozenset({11}), ), (frozenset({12, 6}), ), None, False, False, None, None, "KPR6-Q-PARTNERSHIP"),
    Question("dowry", 'Can I expect dowry?', 8, "star", (frozenset({6}), frozenset({11}), ), (frozenset({5}), frozenset({12}), ), 'csl', False, False, None, None, "KPR6-Q-DOWRY"),
    Question("scholarship", 'Will I get a scholarship?', 11, "star", (frozenset({2}), frozenset({6}), frozenset({11}), ), (frozenset({8, 12}), ), None, False, False, None, None, "KPR6-Q-SCHOLARSHIP"),
    Question("go_abroad", 'Will I go abroad?', 12, "csl", (frozenset({9, 3, 12}), ), (), None, True, True, None, None, "KPR6-Q-GO_ABROAD"),
    Question("promotion", 'Will I be promoted?', 11, "csl", (frozenset({11, 2, 10, 6}), ), (), None, True, True, None, None, "KPR6-Q-PROMOTION"),
    Question("press", 'Can I have a press of my own?', 10, "star", (frozenset({2, 10, 6}), ), (), None, False, False, None, 'it must also be connected with Mars and Mercury (not evaluated)', "KPR6-Q-PRESS"),
    Question("spiritual", 'Will I have a satisfactory spiritual life?', 11, "star", (frozenset({5}), frozenset({10}), ), (), None, False, False, None, None, "KPR6-Q-SPIRITUAL"),
    Question("sanyasi", 'Can I become a sanyasi?', 1, "csl", (frozenset({3}), frozenset({10}), frozenset({12}), ), (), None, False, False, None, 'it must also be connected with Saturn (not evaluated)', "KPR6-Q-SANYASI"),
    Question("reappointment", 'Any re-appointment (or new service) for me?', 6, "star", (frozenset({10, 2, 6}), ), (frozenset({1, 12, 5, 9}), ), None, False, False, None, None, "KPR6-Q-REAPPOINTMENT"),
    Question("passport", 'Will I get a passport to go overseas?', 11, "star", (frozenset({3}), frozenset({9}), frozenset({11}), ), (), None, False, False, None, None, "KPR6-Q-PASSPORT"),
    Question("settle_abroad", 'Will I settle down there?', 11, "star", (frozenset({11}), frozenset({2}), ), (), None, False, False, None, None, "KPR6-Q-SETTLE_ABROAD"),
    Question("overseas", 'Will I go overseas?', 11, "star", (frozenset({3}), frozenset({9}), frozenset({12}), ), (), None, False, False, None, None, "KPR6-Q-OVERSEAS"),
    Question("high_position", 'Can I get the position I want (premier)?', 11, "star", (frozenset({9}), frozenset({10}), frozenset({11}), ), (), None, False, False, None, "OCR reads '9th, the Ifith andLitth' (9th, 10th and 11th); also connected with Mars and Jupiter (not evaluated)", "KPR6-Q-HIGH_POSITION"),
    Question("servant", 'Good time to engage a servant?', 1, "csl", (frozenset({6}), frozenset({11}), ), (), None, False, False, None, None, "KPR6-Q-SERVANT"),
    Question("buy_article", 'Good time to buy an article?', 2, "star", (frozenset({6}), frozenset({11}), ), (), None, False, False, None, None, "KPR6-Q-BUY_ARTICLE"),
    Question("sell_article", 'Good time to sell an article?', 12, "star", (frozenset({6}), frozenset({11}), ), (), None, False, False, None, None, "KPR6-Q-SELL_ARTICLE"),
    Question("enter_service", 'Good time to enter service?', 6, "star", (frozenset({10}), frozenset({11}), ), (), None, False, False, None, None, "KPR6-Q-ENTER_SERVICE"),
    Question("sign_agreement", 'Good time to sign an agreement?', 3, "star", (frozenset({6}), frozenset({11}), ), (), None, False, False, None, None, "KPR6-Q-SIGN_AGREEMENT"),
    Question("start_business", 'Good time to start a business?', 7, "star", (frozenset({6}), frozenset({11}), ), (), None, False, False, None, None, "KPR6-Q-START_BUSINESS"),
    Question("release_film", 'Good time to release a film?', 7, "star", (frozenset({6}), frozenset({11}), ), (), None, False, False, None, None, "KPR6-Q-RELEASE_FILM"),
    Question("lay_foundation", 'Good time to lay a foundation?', 4, "star", (frozenset({11}), ), (frozenset({5}), frozenset({12}), ), None, False, False, None, None, "KPR6-Q-LAY_FOUNDATION"),
    Question("overseas_probation", 'Overseas for probation or training?', 6, "star", (frozenset({9}), frozenset({12}), ), (), None, False, False, None, None, "KPR6-Q-OVERSEAS_PROBATION"),
    Question("promotion_6th", 'Promotion (6th cusp)?', 6, "star", (frozenset({11}), frozenset({10, 6}), ), (), None, False, False, None, None, "KPR6-Q-PROMOTION_6TH"),
)}


def _retro(chart: KPChart, p: str) -> bool:
    return p not in NODES and chart.planets[p].retrograde


def _meets(houses: frozenset[int], groups: tuple[frozenset[int], ...]) -> bool:
    return bool(groups) and all(houses & g for g in groups)


def _dual(chart: KPChart, csl: str) -> bool:
    """KPR6 p.165: CSL in a dual sign, or in the star of a planet in or owning a dual sign, or Mercury."""
    if csl == "Mercury" or sign_index(chart.planets[csl].longitude) in DUAL_SIGNS:
        return True
    star = chart.planets[csl].star_lord
    owns_dual = star in ("Mercury", "Jupiter")  # lords of Gemini/Virgo and Sagittarius/Pisces
    return owns_dual or sign_index(chart.planets[star].longitude) in DUAL_SIGNS


@dataclass(frozen=True, slots=True)
class Answer:
    question: Question
    verdict: str
    csl: str
    star_lord: str
    judged_planet: str
    judged_houses: frozenset[int]
    csl_retrograde: bool
    star_lord_retrograde: bool
    special_met: bool | None

    def to_dict(self) -> dict:
        q = self.question
        c = CITATIONS[q.citation]
        return {
            "question": q.key, "label": q.label, "cusp": q.cusp, "via": q.via,
            "verdict": self.verdict, "csl": self.csl, "csl_star_lord": self.star_lord,
            "judged_planet": self.judged_planet, "judged_houses": sorted(self.judged_houses),
            "yes_groups": [sorted(g) for g in q.yes], "no_groups": [sorted(g) for g in q.no],
            "csl_retrograde": self.csl_retrograde, "star_lord_retrograde": self.star_lord_retrograde,
            "special_condition_met": self.special_met, "not_evaluated": q.unevaluated,
            "citation": f'{c.ref()} "{c.quote}"',
            "framing": "What Krishnamurti's horary rule says; not a validated prediction.",
        }


def judge_question(chart: KPChart, key: str) -> Answer:
    """Apply one registry rule to an already cast horary chart."""
    q = QUESTIONS[key]
    sigs = planet_significations(chart)
    csl = chart.cusp(q.cusp).sub_lord
    star = chart.planets[csl].star_lord
    who = star if q.via == "star" else csl
    hs = houses_signified(chart, who, sigs)
    no_who = star if (q.no_via or q.via) == "star" else csl
    no_hs = houses_signified(chart, no_who, sigs)
    yes_ok, no_ok = _meets(hs, q.yes), _meets(no_hs, q.no)
    direct_ok = not (_retro(chart, csl) or _retro(chart, star)) if q.need_direct else True
    special = _dual(chart, csl) if q.special == "dual" else None
    cond_ok = direct_ok and (special is not False)
    if not cond_ok:
        verdict = NO if q.fail_means_no else NOT_SIGNIFIED
    elif yes_ok and no_ok:
        verdict = MIXED
    elif yes_ok:
        verdict = YES
    elif no_ok or q.fail_means_no:
        verdict = NO
    else:
        verdict = NOT_SIGNIFIED
    return Answer(q, verdict, csl, star, who, hs, _retro(chart, csl), _retro(chart, star), special)


def answer(number: int, judged: Birth, key: str, *, node_mode: str = "mean") -> Answer:
    """Cast the horary chart for ``number`` at ``judged`` and apply rule ``key``."""
    return judge_question(cast_horary(number, judged, node_mode=node_mode), key)


__all__ = ["YES", "NO", "MIXED", "NOT_SIGNIFIED", "Question", "QUESTIONS", "Answer",
           "judge_question", "answer"]
