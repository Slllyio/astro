"""The conclusion step: Raman's two-of-three tally with the matter-specific tie-breaks.

Spec 4.1: with house, lord and karaka graded, the verdict goes with the majority
(HTJAH:2111-2113, 5729-5730). Spec 4.2: which factor wins a split, by matter (brothers and
children: the lord over the house; the mother: the Moon decides an early loss, the house and
lord how long; education: two separate answers; the father: an afflicted karaka; longevity:
the Lagna lord against the 8th lord, then Saturn, unless they are one planet; gains: wealth
yogas outrank the 11th house; elder brothers: agreement of the Lagna and Moon views). Spec 4.4: one benefic sets a floor (the
thing comes but suffers) and none means denial. Spec 4.5: a blemish shows as a quality or a
shorter duration.

The sentence follows his formula, "[house grade]; [lord grade]; [karaka grade]. Hence ..."
(spec 3.6 of the H3-H6 extraction; e.g. HTJAH:4485-4486), in the classical indication idiom:
every sentence passes the engine's report guard ``_FORBIDDEN_RE``.

CONVENTIONS: a factor's vote is good at "fairly strong" or above, bad at "blemished" or below,
neutral at "moderate"; the plain tally needs two good votes for favourable and two bad votes
for afflicted, else mixed. Where a matter has no karaka (the 9th's fortune, the 10th) the view
from the Moon takes the third vote. For longevity, Saturn moving the band DOWN when weak is the
mirror of his printed upward move (HTJAH:11703-11704) and is marked convention.

Usage:
    from app.raman_saab.procedure.conclusion import conclude
"""
from __future__ import annotations

from typing import Optional

from app.raman_saab.ordinals import ordinal
from app.raman_saab.procedure.citations import cite
from app.raman_saab.procedure.grading import FIXES
from app.raman_saab.procedure.matters import Matter
from app.raman_saab.procedure.model import GRADES, Conclusion, Factor

_VERDICT_OF_VOTE = {"good": "favourable", "bad": "afflicted", "neutral": "mixed"}


def _tally(votes: list[str]) -> str:
    if votes.count("good") >= 2:
        return "favourable"
    if votes.count("bad") >= 2:
        return "afflicted"
    return "mixed"


def tally_steps(matter: Matter) -> tuple[str, str, str]:
    """The three factors that vote: house, lord and the karaka (or the Moon view)."""
    third = "karaka" if matter.karaka is not None and matter.decider != "profession" else "moon"
    return ("house", "lord", third)


def _children_floor(factors: dict[str, Factor]) -> bool:
    """T1 (2026-10-28): whether any of the four factors, the view from the Moon included,
    carries a redeeming benefic testimony. Raman denies a matter only when none does
    (HTJAH:8669-8670, spec 4.4)."""
    return any(f.redeeming for f in factors.values())


_DENIED = "none: children denied"
_FEW = "few or delayed: the house and lord are afflicted, but a benefic testimony redeems"


def conclude(matter: Matter, factors: dict[str, Factor], *,
             lagna_lord: Optional[Factor] = None, wealth_links: tuple[str, ...] = (),
             life: Optional[tuple[float, str]] = None) -> Conclusion:
    """Settle the verdict for ``matter`` from its graded factors. ``life`` is the engine's
    computed span of life ``(years, class)`` when the chart has birth data (longevity only)."""
    steps = tally_steps(matter)
    votes = {s: factors[s].vote for s in steps}
    if matter.decider == "gains" and wealth_links:
        votes["house"] = "good"
    tally = _tally([votes[s] for s in steps])
    verdict, rule, rule_cite, basis = tally, "two of the three factors carry the verdict", \
        cite("two_of_three"), "doctrine"
    outcome: Optional[str] = None
    subs: list[tuple[str, str]] = []
    h, lo, k = votes["house"], votes["lord"], votes[steps[2]]
    d = matter.decider

    if d in ("lord_over_house", "children") and tally == "mixed" and lo != "neutral":
        verdict = _VERDICT_OF_VOTE[lo]
        rule, rule_cite = "the lord outweighs the house", cite("lord_over_house_brothers")
    if d == "children":
        if h == "bad" and lo == "bad":
            verdict, outcome = "afflicted", (_FEW if _children_floor(factors) else _DENIED)
            rule, rule_cite = ("the house and lord are afflicted, so the karaka is set aside",
                               cite("two_afflicted_ignore_karaka"))
        elif h != "bad" and lo != "bad" and k == "bad":
            verdict, outcome = "mixed", "born, but with sorrow through them"
            rule, rule_cite = ("house and lord promise birth; the afflicted karaka brings sorrow",
                               cite("children_born_sorrow"))
        elif h == "bad" and lo == "neutral":
            verdict, outcome = "mixed", "born, but their survival is not shown"
            rule, rule_cite = ("birth denoted, but the afflicted house and weak lord do not show "
                               "survival", cite("children_not_surviving"))
        elif h == "bad" and lo != "bad" and k != "bad":
            verdict = "favourable" if lo == "good" else "mixed"
            outcome = "born: birth of children is not denied"
            rule, rule_cite = ("the lord and karaka are clean against an afflicted house",
                               cite("children_not_denied"))
        else:
            outcome = {"favourable": "born", "mixed": "born, with blemish",
                       "afflicted": _FEW if _children_floor(factors) else _DENIED}[verdict]
    elif d == "mother":
        early = {"bad": "early loss of the mother is indicated",
                 "good": "no early loss is indicated",
                 "neutral": "the Moon does not decide it"}[k]
        hl = (h, lo)
        length = ("the house and lord lengthen her life" if hl.count("good") >= 1
                  and "bad" not in hl else
                  "the house and lord shorten her life" if hl.count("bad") >= 1
                  and "good" not in hl else "the house and lord are balanced")
        subs = [("early loss (the Moon decides)", early),
                ("how long (the house and lord decide)", length)]
        if k == "bad":
            verdict = "afflicted"
            rule, rule_cite = ("the Moon, the primary indicator, decides an early loss",
                               cite("mother_karaka_decides"))
        elif k == "good":
            verdict = "mixed" if "bad" in hl and "good" not in hl else "favourable"
            rule, rule_cite = ("the Moon shows no early loss; the house and lord decide how long",
                               cite("mother_house_lord_duration"))
    elif d == "education":
        school = ("favourable" if h == lo == "good" else
                  "afflicted" if h == lo == "bad" else "mixed")
        subs = [("knowledge (the karaka Jupiter)", _VERDICT_OF_VOTE[k]),
                ("schooling (the house and lord)", school)]
        rule = "two separate answers; the overall verdict is the tally (convention)"
        rule_cite, basis = cite("education_karaka_vs_house"), "convention"
    elif d == "father" and k == "bad":
        # Round 2 (A1): "Afflictions to the pitruKaraka by association, aspect, placement or
        # otherwise are very important in depriving a native of his father" (HTJAH:13126-13127).
        # The sentence is about afflictions: an afflicted Sun decides, a strong Sun does not
        # rescue an afflicted 9th house and lord (the two-of-three tally stands).
        verdict = "afflicted"
        rule, rule_cite = ("afflictions to the karaka Sun are decisive for the father",
                           cite("father_karaka_decides"))
    elif d == "father" and k == "good":
        rule = ("a strong Sun does not overrule the 9th house and lord; two of the three "
                "factors carry the verdict")
    elif d == "longevity" and lagna_lord is not None and _same_planet(lagna_lord, factors["lord"]):
        # Round 2 (A6): for an Aries or Libra Lagna the Lagna lord is the 8th lord, so "the 8th
        # lord stronger than Lagna lord" (HTJAH:11415-11416) compares a planet with itself. The
        # comparison does not apply; the plain tally (HTJAH:2111-2113) stands.
        rule = ("the Lagna lord is also the 8th lord, so the two cannot be compared; two of the "
                "three factors carry the verdict")
        subs = [("the Lagna lord against the 8th lord",
                 f"the same planet ({lagna_lord.subject.split()[-1]}): not compared")]
    elif d == "longevity" and lagna_lord is not None:
        li, ei = GRADES.index(lagna_lord.grade), GRADES.index(factors["lord"].grade)
        band = "favourable" if li > ei else ("mixed" if li == ei else "afflicted")
        order = ("afflicted", "mixed", "favourable")
        sat = factors["karaka"].vote
        moved = band
        if sat == "good" and band != "favourable":
            moved = order[order.index(band) + 1]
        elif sat == "bad" and band != "afflicted":
            moved = order[order.index(band) - 1]
            basis = "convention"
        verdict = moved
        span = {"favourable": "long (Purnayu)", "mixed": "middle (Madhyayu)",
                "afflicted": "short (Alpayu)"}
        subs = [("the Lagna lord against the 8th lord",
                 f"Lagna lord {lagna_lord.grade}, 8th lord {factors['lord'].grade}: {span[band]}"),
                ("Saturn moves the band", f"Saturn {factors['karaka'].grade}: {span[moved]}")]
        rule, rule_cite = ("the Lagna lord against the 8th lord, then Saturn moves the band",
                           cite("longevity_lords") + ", " + cite("longevity_saturn"))
        if life is not None:
            years, cls = life
            by_span = {"purna": "favourable", "madhya": "mixed", "alpa": "afflicted"}[cls]
            # T2 (2026-10-28): the computed span is shown beside the lords' band.
            subs.append(("the computed span (stage zero)",
                         f"{years:.1f} years: {span[by_span]}"
                         + ("" if by_span == moved else "; the lords' band above disagrees")))
            if FIXES["F5_span_decides_longevity"]:
                # F5: "the span of life comes first" (spec 2.2; HTJAH:763-765, 1578-1580).
                verdict = by_span
                rule = ("the computed span of life comes first; the lords and Saturn are shown "
                        "beside it")
                rule_cite = cite("span_first")
    elif d == "gains" and wealth_links:
        rule = ("yogas linking the 2nd, 5th, 9th and 11th lords outrank the 11th house ("
                + "; ".join(wealth_links) + ")")
        rule_cite = cite("gains_wider")
    elif d == "elder_brothers" and h == "bad" and lo == "bad" and factors["moon"].vote == "bad":
        verdict = "afflicted"
        rule, rule_cite = ("the house and lord are afflicted from both the Lagna and the Moon",
                           cite("elder_brothers_lagna_moon"))
    elif d == "profession":
        rule = ("two of three, with the view from the Moon as the third factor: Raman uses no "
                "karaka for the 10th (convention)")
        basis = "convention"

    redeeming = any(factors[s].redeeming for s in steps)
    if outcome is None:
        if verdict == "afflicted":
            outcome = ("the matter comes but suffers: a benefic influence sets a floor"
                       if redeeming else "denial or rupture: no redeeming benefic influence")
        elif verdict == "mixed":
            outcome = "the matter comes with a blemish, shown as a quality or a shorter duration"
        else:
            outcome = "the matter comes and lasts"
    sentence = _sentence(matter, factors, steps, verdict, outcome)
    return Conclusion(tuple((s, votes[s]) for s in steps), tally, rule, rule_cite, basis,
                      verdict, outcome, tuple(subs), sentence)


def _same_planet(a: Factor, b: Factor) -> bool:
    """Whether two graded planet factors are the same planet (their subject ends in its name)."""
    return a.subject.split()[-1] == b.subject.split()[-1]


def _clause(f: Factor) -> str:
    return f"{f.subject} is {f.grade}"


def _sentence(matter: Matter, factors: dict[str, Factor], steps: tuple[str, ...],
              verdict: str, outcome: str) -> str:
    parts = [_clause(factors[s]) for s in steps]
    parts[0] = parts[0][0].upper() + parts[0][1:]
    word = {"favourable": "favourable", "mixed": "mixed", "afflicted": "afflicted"}[verdict]
    return ("; ".join(parts) + f". Hence the indications for {matter.label} in the "
            f"{ordinal(matter.house)} house are {word}: {outcome}.")
