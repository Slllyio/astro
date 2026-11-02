"""Krishnamurti's natal indications: the "If the sub-lord of the Nth cusp ..." rules.

Readers 3 and 4 give dozens of short rules that read one cusp sub-lord (CSL)
and name what it indicates: the ascendant CSL signifying 1 and 10 gives honour
(KPR3), the 2nd CSL being Mercury makes one talkative, the ascendant CSL in the
star of a planet in Virgo makes one chatty, and so on. Each is one
:class:`Indication`, cited verbatim (``app.kp.citations``). Kinds:

* ``signifies``       the CSL signifies the house groups (ruling RH7 groups:
  each group needs one hit, so "1 and 10" is ``({1}, {10})``).
* ``star_signifies``  the planet in whose star the CSL sits signifies them.
* ``is``              the CSL is one of the named planets.
* ``retrograde``      the CSL is retrograde (nodes never are).
* ``star_in_sign``    the CSL's star lord occupies one of the signs (0 = Aries).
* ``plural``          KPR4 p.182: the CSL is Mercury, in a dual sign, or in the
  star of a planet in a dual sign.

Indications are descriptive (what Krishnamurti says the configuration shows),
never timed and never validated. Left out on purpose (ruling R22):
death, lifespan and partner-death rules (KPR3 8th-cusp rules, KPR4 p.209,
p.249 "end will be unnatural", p.242 short-lived first issue); rules whose
cusp is not named (KPR4 p.69); rules that rest on an undefined "connected
in any manner" (KPR3 2nd/12th-cusp speech and spending rules, 4th-cusp
vehicle); rules that need a second chart (KPR4 p.177 sons-in-law); and the
"chaste wife" rule (KPR4 p.100), whose "occupying" clause cannot be parsed
unambiguously from the print.

Usage:
    from app.kp.chart import Birth, cast
    from app.kp.indications import indications
    for f in indications(cast(Birth(1990, 7, 15, 12, 0, tz=5.5, lat=12.97, lon=77.59))):
        print(f.to_dict())
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.kp.chart import NODES, KPChart, sign_index
from app.kp.citations import CITATIONS
from app.kp.significators import houses_signified, planet_significations

#: Gemini, Virgo, Sagittarius, Pisces (0-based).
DUAL_SIGNS: Final = frozenset({2, 5, 8, 11})
KINDS: Final = ("signifies", "star_signifies", "is", "retrograde", "star_in_sign", "plural")


@dataclass(frozen=True, slots=True)
class Indication:
    """One printed rule: cusp ``cusp``'s sub-lord, tested by ``kind`` with ``arg``."""

    key: str
    cusp: int
    kind: str
    arg: object
    indicates: str
    citation: str


INDICATIONS: Final[dict[str, Indication]] = {i.key: i for i in (
    Indication('asc_1_2', 1, 'signifies', (frozenset({1}), frozenset({2}),), 'gains money; enters service or increases the bank position', 'KPR3-IND-ASC_1_2'),
    Indication('asc_1_3', 1, 'signifies', (frozenset({1}), frozenset({3}),), 'good mental development; gains knowledge through short journeys', 'KPR3-IND-ASC_1_3'),
    Indication('asc_1_4', 1, 'signifies', (frozenset({1}), frozenset({4}),), 'good education; gains through estates', 'KPR3-IND-ASC_1_4'),
    Indication('asc_1_5', 1, 'signifies', (frozenset({1}), frozenset({5}),), 'delight in sports, speculation and pleasure', 'KPR3-IND-ASC_1_5'),
    Indication('asc_1_6', 1, 'signifies', (frozenset({1}), frozenset({6}),), 'sickness; poor resistance to infection', 'KPR3-IND-ASC_1_6'),
    Indication('asc_1_7', 1, 'signifies', (frozenset({1}), frozenset({7}),), 'union, partnership, marital happiness', 'KPR3-IND-ASC_1_7'),
    Indication('asc_1_8', 1, 'signifies', (frozenset({1}), frozenset({8}),), 'meets with danger', 'KPR3-IND-ASC_1_8'),
    Indication('asc_1_9', 1, 'signifies', (frozenset({1}), frozenset({9}),), 'religious, philosophical; long journeys; research', 'KPR3-IND-ASC_1_9'),
    Indication('asc_1_10', 1, 'signifies', (frozenset({1}), frozenset({10}),), 'honour, prestige, rise in status', 'KPR3-IND-ASC_1_10'),
    Indication('asc_1_11', 1, 'signifies', (frozenset({1}), frozenset({11}),), 'large profits; many benefactors', 'KPR3-IND-ASC_1_11'),
    Indication('asc_1_12', 1, 'signifies', (frozenset({1}), frozenset({12}),), 'troubles, jealousy, secret enmity, hindrances', 'KPR3-IND-ASC_1_12'),
    Indication('second_2_1', 2, 'signifies', (frozenset({2}), frozenset({1}),), 'money made easily by personal effort', 'KPR3-IND-SECOND_2_1'),
    Indication('second_2_3', 2, 'signifies', (frozenset({2}), frozenset({3}),), 'gain through writing, publicity, agencies, travel', 'KPR3-IND-SECOND_2_3'),
    Indication('second_2_4', 2, 'signifies', (frozenset({2}), frozenset({4}),), 'estates and money by inheritance', 'KPR3-IND-SECOND_2_4'),
    Indication('second_2_5', 2, 'signifies', (frozenset({2}), frozenset({5}),), 'gain through music, cinema, entertainment', 'KPR3-IND-SECOND_2_5'),
    Indication('second_2_6', 2, 'signifies', (frozenset({2}), frozenset({6}),), 'profit in transactions; gains through service and labour', 'KPR3-IND-SECOND_2_6'),
    Indication('second_2_7', 2, 'signifies', (frozenset({2}), frozenset({7}),), 'gain through partner or marriage; success in litigation', 'KPR3-IND-SECOND_2_7'),
    Indication('second_2_8', 2, 'signifies', (frozenset({2}), frozenset({8}),), 'gain by legacy, insurance, gratuity', 'KPR3-IND-SECOND_2_8'),
    Indication('second_2_9', 2, 'signifies', (frozenset({2}), frozenset({9}),), 'money through trade abroad, publishing, long journeys', 'KPR3-IND-SECOND_2_9'),
    Indication('second_2_10', 2, 'signifies', (frozenset({2}), frozenset({10}),), 'steady progress; government service; honours', 'KPR3-IND-SECOND_2_10'),
    Indication('second_2_11', 2, 'signifies', (frozenset({2}), frozenset({11}),), 'money without much effort; friends oblige', 'KPR3-IND-SECOND_2_11'),
    Indication('second_2_12', 2, 'signifies', (frozenset({2}), frozenset({12}),), 'money by serving in hospitals, asylums, jails', 'KPR3-IND-SECOND_2_12'),
    Indication('second_is_mercury', 2, 'is', ('Mercury',), 'speaks a lot; fit for sales and propaganda', 'KPR3-IND-SECOND_IS_MERCURY'),
    Indication('second_is_mars', 2, 'is', ('Mars',), 'blunt and outspoken', 'KPR3-IND-SECOND_IS_MARS'),
    Indication('second_is_saturn', 2, 'is', ('Saturn',), 'speaks little and drags on', 'KPR3-IND-SECOND_IS_MARS'),
    Indication('second_is_jupiter', 2, 'is', ('Jupiter',), 'wise talk', 'KPR3-IND-SECOND_IS_MARS'),
    Indication('second_is_venus', 2, 'is', ('Venus',), 'talk mostly about the other sex', 'KPR3-IND-SECOND_IS_MARS'),
    Indication('third_is_mars', 3, 'is', ('Mars',), 'never contented', 'KPR3-IND-THIRD_IS_MARS'),
    Indication('eleventh_retro', 11, 'retrograde', None, 'what one desires will not be had', 'KPR3-IND-ELEVENTH_RETRO'),
    Indication('asc_star_6_8_12', 1, 'star_signifies', (frozenset({6, 8, 12}),), 'disease, danger or hospitalisation', 'KPR3-IND-ASC_STAR_6_8_12'),
    Indication('eighth_debt', 8, 'signifies', (frozenset({5}), frozenset({6}), frozenset({8}), frozenset({12}),), 'difficulties; borrowing from friends', 'KPR3-IND-EIGHTH_DEBT'),
    Indication('eighth_repay', 8, 'signifies', (frozenset({2, 10, 11}),), 'debts repaid in its period', 'KPR3-IND-EIGHTH_REPAY'),
    Indication('fifth_musician', 5, 'star_in_sign', frozenset({4, 10}), 'a popular musician', 'KPR3-IND-FIFTH_MUSICIAN'),
    Indication('tenth_aries', 10, 'star_in_sign', frozenset({0}), 'army, police, fire-brigade, work with fire or metal', 'KPR3-IND-TENTH_ARIES'),
    Indication('asc_star_in_aries', 1, 'star_in_sign', frozenset({0}), 'changes views suddenly', 'KPR3-IND-ASC_STAR_IN_ARIES'),
    Indication('asc_star_in_taurus', 1, 'star_in_sign', frozenset({1}), 'concentrated feelings that create enemies', 'KPR3-IND-ASC_STAR_IN_TAURUS'),
    Indication('asc_star_in_gemini', 1, 'star_in_sign', frozenset({2}), 'speedy, thorough changes of view', 'KPR3-IND-ASC_STAR_IN_GEMINI'),
    Indication('asc_star_in_cancer', 1, 'star_in_sign', frozenset({3}), 'imagines slights', 'KPR3-IND-ASC_STAR_IN_CANCER'),
    Indication('asc_star_in_leo', 1, 'star_in_sign', frozenset({4}), 'unquenchable thirst for glory', 'KPR3-IND-ASC_STAR_IN_LEO'),
    Indication('asc_star_in_virgo', 1, 'star_in_sign', frozenset({5}), 'chatty', 'KPR3-IND-ASC_STAR_IN_VIRGO'),
    Indication('asc_star_in_libra', 1, 'star_in_sign', frozenset({6}), 'must keep emotions in check', 'KPR3-IND-ASC_STAR_IN_LIBRA'),
    Indication('asc_star_in_scorpio', 1, 'star_in_sign', frozenset({7}), 'over-estimates self', 'KPR3-IND-ASC_STAR_IN_SCORPIO'),
    Indication('asc_star_in_sagittarius', 1, 'star_in_sign', frozenset({8}), 'selfish and inconsiderate', 'KPR3-IND-ASC_STAR_IN_SAGITTARIUS'),
    Indication('asc_star_in_capricorn', 1, 'star_in_sign', frozenset({9}), 'over-ambitious for money and power', 'KPR3-IND-ASC_STAR_IN_CAPRICORN'),
    Indication('asc_star_in_aquarius', 1, 'star_in_sign', frozenset({10}), 'prefers solitude', 'KPR3-IND-ASC_STAR_IN_AQUARIUS'),
    Indication('asc_star_in_pisces', 1, 'star_in_sign', frozenset({11}), 'broods when things go wrong', 'KPR3-IND-ASC_STAR_IN_PISCES'),
    Indication('asc_2_r4', 1, 'signifies', (frozenset({2}),), 'works long hours after money', 'KPR4-IND-ASC_2_R4'),
    Indication('asc_3_r4', 1, 'signifies', (frozenset({3}),), 'mental development; gain by short journeys', 'KPR4-IND-ASC_3_R4'),
    Indication('asc_4_r4', 1, 'signifies', (frozenset({4}),), 'interest in land, buildings, vehicles, study', 'KPR4-IND-ASC_4_R4'),
    Indication('asc_5_r4', 1, 'signifies', (frozenset({5}),), 'delight in sports, music, speculation', 'KPR4-IND-ASC_5_R4'),
    Indication('asc_6_r4', 1, 'signifies', (frozenset({6}),), 'ill-health; susceptible to disease', 'KPR4-IND-ASC_6_R4'),
    Indication('asc_7_r4', 1, 'signifies', (frozenset({7}),), 'good partners in life', 'KPR4-IND-ASC_7_R4'),
    Indication('asc_9_r4', 1, 'signifies', (frozenset({9}),), 'desire for long journeys', 'KPR4-IND-ASC_9_R4'),
    Indication('asc_10_r4', 1, 'signifies', (frozenset({10}),), 'name and fame', 'KPR4-IND-ASC_10_R4'),
    Indication('asc_11_r4', 1, 'signifies', (frozenset({11}),), 'all success', 'KPR4-IND-ASC_11_R4'),
    Indication('asc_12_r4', 1, 'signifies', (frozenset({12}),), 'secret unhappiness, secret enemies', 'KPR4-IND-ASC_12_R4'),
    Indication('career_partner', 4, 'signifies', (frozenset({4, 8, 12}),), 'a working (career) partner', 'KPR4-IND-CAREER_PARTNER'),
    Indication('plural_marriage', 7, 'plural', None, 'more than one marriage', 'KPR4-IND-PLURAL_MARRIAGE'),
    Indication('second_marriage_2nd', 2, 'signifies', (frozenset({7}),), 'second marriage', 'KPR4-IND-SECOND_MARRIAGE_2ND'),
)}


@dataclass(frozen=True, slots=True)
class Fired:
    """An indication whose condition holds in the chart, with the facts that made it hold."""

    indication: Indication
    csl: str
    star_lord: str
    houses: tuple[int, ...]

    def to_dict(self) -> dict:
        i = self.indication
        c = CITATIONS[i.citation]
        return {
            "key": i.key, "cusp": i.cusp, "kind": i.kind, "indicates": i.indicates,
            "csl": self.csl, "csl_star_lord": self.star_lord, "houses": list(self.houses),
            "citation": f'{c.ref()} "{c.quote}"',
            "framing": "What Krishnamurti says this configuration shows; not a validated prediction.",
        }


def _holds(chart: KPChart, i: Indication, csl: str, star: str, sigs) -> tuple[bool, tuple[int, ...]]:
    if i.kind in ("signifies", "star_signifies"):
        who = csl if i.kind == "signifies" else star
        hs = houses_signified(chart, who, sigs)
        return all(hs & g for g in i.arg), tuple(sorted(hs))
    if i.kind == "is":
        return csl in i.arg, ()
    if i.kind == "retrograde":
        return csl not in NODES and chart.planets[csl].retrograde, ()
    if i.kind == "star_in_sign":
        return sign_index(chart.planets[star].longitude) in i.arg, ()
    if i.kind == "plural":
        return (csl == "Mercury" or sign_index(chart.planets[csl].longitude) in DUAL_SIGNS
                or sign_index(chart.planets[star].longitude) in DUAL_SIGNS), ()
    raise ValueError(f"unknown kind {i.kind!r}")


def indications(chart: KPChart) -> tuple[Fired, ...]:
    """Every registry rule that holds in ``chart``, in registry order."""
    sigs = planet_significations(chart)
    out = []
    for i in INDICATIONS.values():
        csl = chart.cusp(i.cusp).sub_lord
        star = chart.planets[csl].star_lord
        ok, hs = _holds(chart, i, csl, star, sigs)
        if ok:
            out.append(Fired(i, csl, star, hs))
    return tuple(out)


__all__ = ["DUAL_SIGNS", "KINDS", "Indication", "INDICATIONS", "Fired", "indications"]
