"""Raman's philosophy, applied to one chart — how he would weigh it, and why.

`RAMAN_PHILOSOPHY_2026-10-30.md` (project files) traced the reasons Raman himself gives for
his verdicts across HTJAH, NH, 3HC, PI, HPA, Muhurtha and Varshaphal. Several of those reasons
were tested as engine changes and did not survive pre-registration (C2, FIDELITY_FIXES_PREREG
Addenda 29-30): the principle is Raman's, but the engine has no faithful trigger that improves
the scored verdicts. This module puts them where they do belong — in the reading, as the
explanation of how a verdict should be held.

Three parts:

- `FRAME` — chart-independent statements of what a horoscope is (tendency, not fate), what
  remedies can and cannot do, how promise, period and transit rank, and why the reading must
  fit the person. Each is Raman's own sentence with its line.
- `foundation` — the Lagna as the foundation of the chart (HTJAH-I:3871-3878), read off the
  Lagna lord's strength and the 1st house's verdict.
- per-house notes — which of Raman's weighing principles is at work in each house, from the
  ledger the judge already built: an affliction that is mere weakness rather than a malefic's
  work, an affliction that is met by benefic influences, two of three factors deciding, a
  strong house carrying a minor affliction, and a lord held by a node and a malefic.

PREC-10: a pure re-read. No verdict is re-judged, none is suppressed, and nothing here feeds
the judge.

Usage:
    from app.raman_saab.philosophy import chart_philosophy, FRAME
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final, Optional

if TYPE_CHECKING:  # pragma: no cover
    from app.raman_saab.detailed_report import DetailedReport


#: (heading, Raman's words, citation, what it means for this reading). Verbatim quotes from the
#: PC corpus; the last field is the report's own sentence, never attributed to Raman.
FRAME: Final[tuple[tuple[str, str, str, str], ...]] = (
    ("A tendency, not a fate",
     "There is nothing like destiny in astrology. The proper term to be used is Adrishta or that "
     "which is not seen.",
     "HTJAH-I:369-370",
     "Every verdict below describes the strength of a tendency the chart shows, not an outcome "
     "fixed in advance."),
    ("Partly free, partly determined",
     "Man has enough freedom to make or mar himself. He has not enough freedom to command "
     "nature and history to suit his fancies.",
     "PI:5043-5046",
     "The chart sets the capital and the seasons; how they are used is the native's own."),
    ("What remedies can do",
     "...not only take remedies to avert the evils indicated by the planets from time to time "
     "but also adjust his affairs where the remedies prove ineffectual.",
     "3HCC:576-579",
     "Remedies work on degree and timing. Raman puts the ordinary remedy first (medicine is "
     "\"the first shanti\", HTJAH-I:6193) and says plainly that remedies can fail."),
    ("Promise, period, trigger",
     "Unless the placement of the Ascendant and other planets warrants, the Dasha by "
     "themselves cannot give these results.",
     "HTJAH-I:13446-13447",
     "A period delivers only what the birth chart promises, and transits are \"always "
     "secondary\" (HTJAH-I:11039). Read the timing sections in that order of weight."),
    ("The person and the times",
     "The result should be consistent with the person for whom it is intended, under the "
     "condition of life in which he is brought up as well as the physical possibility at the "
     "time.",
     "HPA-24:64-67",
     "A house is read against the native's age, station and way of life; the same 7th house "
     "means one thing for a householder and another for a renunciate."),
    ("Weigh, never count",
     "No single yoga, including KSY, is capable of marring or making a horoscope.",
     "3HCC:11229-11230",
     "No one combination below decides a life. Read the houses together."),
)

PRINCIPLE_WEAK: Final[str] = "weakness-not-evil"
PRINCIPLE_RELIEVED: Final[str] = "relieved"
PRINCIPLE_TWO_OF_THREE: Final[str] = "two-of-three"
PRINCIPLE_CARRIES: Final[str] = "strength-carries"
PRINCIPLE_OBSTRUCTED: Final[str] = "obstructed-carrier"

#: principle -> (title, how to hold the verdict, Raman's words, citation). Report sentences, Raman
#: quoted. Ordered as they are shown.
PRINCIPLES: Final[dict[str, tuple[str, str, str, str]]] = {
    PRINCIPLE_TWO_OF_THREE: (
        "Two of three factors decide",
        "two of the three factors (lord, karaka, the house itself) are weak, and Raman lets two "
        "outweigh the third's strength.",
        "Though Jupiter (the third lord) is well-disposed in the horoscope, the Karaka and the "
        "third house are subject to affliction. The native has no brothers.",
        "HTJAH-I:3815-3816"),
    PRINCIPLE_WEAK: (
        "Weakness, not harm",
        "they are called afflicted because their factors are weak, not because a malefic works "
        "against them. In Raman's grammar weakness withholds the good; it does not of itself do "
        "harm, so read them as less given rather than as damage done.",
        "no evil results will be given by him in regard to a beneficial yoga if the negative "
        "units predominate",
        "3HCC:879-881"),
    PRINCIPLE_RELIEVED: (
        "Affliction met by benefic influence",
        "the headline matter has a malefic indication that benefic ones answer. Raman treats an affliction "
        "as decisive only when nothing neutralises it, so these are a balance, not a denial.",
        "affliction by Mars and Saturn, without any neutralising effects",
        "NH:6230-6231"),
    PRINCIPLE_CARRIES: (
        "Strength carries a minor affliction",
        "a malefic indication is present with no benefic one, yet the house's strength carries "
        "it. Raman sizes such an affliction as colouring the matter, not denying it.",
        "The Gajakesari Yoga ... is powerful enough to overcome the minor afflictions.",
        "NH:13416-13417"),
    PRINCIPLE_OBSTRUCTED: (
        "A promise held back",
        "the lord is joined by Rahu or Ketu and touched by Saturn or Mars. Raman reads that grip "
        "as a promise whose full enjoyment is obstructed in practice, even where the house shows "
        "strength: expect delay or less than the strength suggests. (Tested as a verdict rule "
        "and not adopted; it is shown here as Raman's reason, not scored.)",
        "Rahu's association and the aspect of Saturn hardens the political life obstructing the "
        "expression of the yoga in concrete terms, i.e., the actual enjoyment of the yoga "
        "results is denied.",
        "NH:7196-7199"),
}

#: Principles read at the level of the whole house (its lord, its headline matter): shown by
#: house number only, so a house's full list of matters is not repeated.
_HOUSE_LEVEL: Final[frozenset[str]] = frozenset({PRINCIPLE_RELIEVED, PRINCIPLE_OBSTRUCTED})

FOUNDATION_CITE: Final[str] = "HTJAH-I:3871-3878"
FOUNDATION_QUOTE: Final[str] = (
    "If the Lagna is powerful, even though other malefic combinations may be present, the "
    "native will have a more or less smooth sailing of his affairs.")
TELLING_CITE: Final[str] = "HTJAH-I:18216-18222"


@dataclass(frozen=True)
class PrincipleAtWork:
    """One of Raman's weighing principles, and the houses (with their matters) where it is at
    work on this chart."""

    principle: str
    title: str
    how: str
    quote: str
    cite: str
    houses: tuple[tuple[int, tuple[str, ...]], ...]

    @property
    def where(self) -> str:
        if self.principle in _HOUSE_LEVEL:
            hs = [str(h) for h, _ms in self.houses]
            return ("house " if len(hs) == 1 else "houses ") + ", ".join(hs)
        return "; ".join(f"house {h} ({', '.join(ms)})" for h, ms in self.houses)


@dataclass(frozen=True)
class ChartPhilosophy:
    foundation_strong: Optional[bool]
    foundation: str
    houses: tuple[PrincipleAtWork, ...]
    #: Lagna lord, Moon or Mercury weak — Raman's own test for telling hard news gently.
    gentle: bool
    telling: str


def _matter_name(key: str) -> str:
    return key.replace("_", " ")


def _principles_of(sv, chart) -> list[str]:
    from app.raman_saab.judges import house_template as ht
    from app.raman_saab.detailed_report import _lagna_ledger

    L = _lagna_ledger(sv)
    out: list[str] = []
    v = sv.verdict
    # Disease, enemies, debts, death, loss: there 'afflicted' means the evil is strong, so the
    # weighing principles below (which speak of good withheld or carried) do not apply.
    if "AFFLICTION_MATTER" in L.flags or sv.house in (6, 8, 12):
        return [PRINCIPLE_OBSTRUCTED] if (
            v != "afflicted" and L.lord and ht._lord_obstructed(L.lord, chart)
            and sv.house not in (6, 8, 12)) else []
    pillars = [L.lord_strong, L.karaka_strong, L.bhava_bala_strong]
    known = [p for p in pillars if p is not None]
    if v == "afflicted" and not L.fired_malefic:
        out.append(PRINCIPLE_WEAK)
    if v == "afflicted" and len(known) == 3 and sum(p is False for p in known) == 2:
        out.append(PRINCIPLE_TWO_OF_THREE)
    if v in ("mixed", "favourable") and L.fired_malefic and L.fired_benefic:
        out.append(PRINCIPLE_RELIEVED)
    if v == "favourable" and L.fired_malefic and not L.fired_benefic:
        out.append(PRINCIPLE_CARRIES)
    if v != "afflicted" and L.lord and ht._lord_obstructed(L.lord, chart):
        out.append(PRINCIPLE_OBSTRUCTED)
    return out


def _weak(planet: str, chart) -> bool:
    from app.raman_saab.judges import house_template as ht
    return ht._strong(planet, chart) is False or bool(ht._lord_hard_afflicted(planet, chart))


def chart_philosophy(r: "DetailedReport") -> ChartPhilosophy:
    """Apply Raman's weighing principles to this chart. Pure re-read of the judged ledgers."""
    from app.raman_saab.judges import house_template as ht

    chart = r.chart
    proformas = getattr(r, "proformas", ()) or ()
    found: dict[tuple[int, str], list[str]] = {}
    for pf in proformas:
        for i, sv in enumerate(getattr(pf, "significations", ()) or ()):
            if getattr(sv, "ledger", None) is None:
                continue
            for pr in _principles_of(sv, chart):
                # the benefic-answers-malefic balance is read on the headline matter only; on
                # the sub-matters it is nearly universal and would say nothing
                if pr == PRINCIPLE_RELIEVED and i > 0:
                    continue
                found.setdefault((pf.house, pr), []).append(_matter_name(sv.signification))
    houses = []
    for pr, (title, how, quote, cite) in PRINCIPLES.items():
        at = tuple((h, tuple(dict.fromkeys(ms))) for (h, p), ms in sorted(found.items()) if p == pr)
        if at:
            houses.append(PrincipleAtWork(principle=pr, title=title, how=how, quote=quote,
                                          cite=cite, houses=at))

    lagna_lord = ht._lord_of_sign(chart.asc_sign, 1)
    h1 = next((pf for pf in proformas if pf.house == 1), None)
    ll_strong = ht._strong(lagna_lord, chart)
    if ll_strong is None or h1 is None:
        f_strong, foundation = None, (
            "The Lagna's strength could not be measured on this chart, so the foundation "
            "test is not applied.")
    elif ll_strong and h1.rollup != "afflicted":
        f_strong, foundation = True, (
            f"The foundation stands: the Lagna lord {lagna_lord} is strong and the 1st house is "
            f"not afflicted. On Raman's reading, scattered afflictions elsewhere weigh less "
            f"against such a chart, though an affliction of a particular matter still has its "
            f"say (NH:12466-12469).")
    else:
        f_strong, foundation = False, (
            f"The foundation needs care: the Lagna lord {lagna_lord} is "
            f"{'strong' if ll_strong else 'weak'} and the 1st house reads {h1.rollup}. Raman "
            f"makes the Lagna the hinge of the whole chart (NH:4758), so afflictions elsewhere "
            f"are carried less easily.")

    soft = [p for p in (lagna_lord, "Moon", "Mercury") if p in chart.planets and _weak(p, chart)]
    soft = list(dict.fromkeys(soft))
    if soft:
        telling = (f"{', '.join(soft)} {'is' if len(soft) == 1 else 'are'} weak in this chart. "
                   f"Raman asks that hard readings then be given with particular care, the "
                   f"truth told \"without adversely affecting one psychologically\" "
                   f"({TELLING_CITE}). Read the afflicted matters below as tendencies to work "
                   f"with, never as sentences.")
    else:
        telling = (f"The Lagna lord, the Moon and Mercury are not weak here; on Raman's test "
                   f"({TELLING_CITE}) the native can take a plain reading, hard parts included.")
    return ChartPhilosophy(foundation_strong=f_strong, foundation=foundation,
                           houses=tuple(houses), gentle=bool(soft), telling=telling)
