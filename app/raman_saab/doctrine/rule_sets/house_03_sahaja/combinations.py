"""House 3 (Sahaja / Bhratru Bhava) — "Important Combinations".

Encodes the 30 rule-atoms of the "Important Combinations" table in
`docs/raman_saab/methodology/house_03_sahaja.md` (frame key: L = from Lagna,
K = Karaka Mars, D9 = Navamsha). Corpus span HTJAH-I:3351-3468 plus the
"A Practical Experience" worked-chart dictum at HTJAH-I:4087-4089 (rule #30).

Karaka = Mars (Kuja / Bhratru-Karaka). Where the 3rd lord is itself Mars
(Aries / Scorpio Lagnas) lord and Karaka collapse into one planet — the rules
read that collapse but do not double-count it.

Encoding policy (kept honest, atom by atom):

* The condition algebra has no Mars-frame "from the karaka" varga-count machinery
  and no D9 *sibling-count* predicate (number-of-Navamsa-gained / -passed / -yet-to-
  pass). The four counting / strength-aggregate atoms — #4, #15, #16, #17 — are
  therefore encoded as ``kind="descriptive"`` with a ``TODO(predicate)`` note; they
  are surfaced by placement with their citation, NOT faked with a stand-in boolean.
* The other 26 atoms compose from the existing predicate set (``LordIn``,
  ``InRashiHouse``, ``Conjunct``, ``HasDignity``, ``Combust``, ``VargaDignity``,
  ``InHouseClass``, ``LordsConjunct``, ``CountInHouse``) plus a handful of local
  leaf predicates (the precedent set by ``house_01_lagna/combinations_core.py``)
  for "the 3rd LORD conjuncts X", "the 3rd lord is an evil planet", odd/even-sign +
  masculine/feminine-planet aspect, and benefic occupation/aspect of the 3rd.
* "esp. in Dwadasamsa" (#29) and the masculine/feminine-aspect refinement carry no
  D12 / sex-of-sibling predicate; the rasi-frame core fires and the varga refinement
  is kept in the result text.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine import drishti
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation
from app.raman_saab.primitives.functional_nature import (
    NATURAL_BENEFICS, NATURAL_MALEFICS)
from app.raman_saab.primitives.relationships import naisargika

# Karaka for the 3rd house — the single natural significator of brothers.
_KARAKA: Final[str] = "Mars"

# Sex-of-aspecting-planet classification (engine note in the methodology):
# masculine = Sun, Mars, Jupiter; feminine = Moon, Venus; Mercury & Saturn are
# treated as neutral and do not decide brother-vs-sister. Used by #11 / #12.
_MASCULINE: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Jupiter"})
_FEMININE: Final[frozenset[str]] = frozenset({"Moon", "Venus"})


def _third_lord(chart: RamanChart) -> str:
    """Name of the D1 lord of the 3rd whole-sign house counted from the Lagna."""
    return SIGN_LORDS[((chart.asc_sign - 1) + 2) % 12 + 1]


# ── local leaf predicates (conditions.py is intentionally untouched) ─────────
class _ThirdLordConjunct(C.Condition):
    """The 3rd LORD shares a whole-sign house with `planet`. Resolves the lord at
    evaluation time and reuses the shared ``Conjunct`` leaf. If the 3rd lord *is*
    `planet` (identity), that is not a conjunction of two bodies -> False.
    Backs the "3rd lord with X" courage atoms #19-#28 (HTJAH-I:3458-3466)."""

    def __init__(self, planet: str) -> None:
        self.planet = planet

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _third_lord(ctx.chart)
        if lord == self.planet:
            return False
        return C.Conjunct(lord, self.planet).evaluate(ctx)


class _ThirdLordIsMalefic(C.Condition):
    """The 3rd lord is a natural malefic (Sun, Mars, Saturn, Rahu, Ketu) — Raman's
    "evil planet" for the 3rd lord (HTJAH-I:3435). Nodes never lord a sign, so in
    practice this resolves to Sun / Mars / Saturn."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return _third_lord(ctx.chart) in NATURAL_MALEFICS


class _ThirdLordIsKaraka(C.Condition):
    """The 3rd lord IS Mars (Aries / Scorpio Lagna) — lord and Karaka collapse."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return _third_lord(ctx.chart) == _KARAKA


class _BodyWithInimical(C.Condition):
    """`planet` shares a whole-sign house with another planet that is naisargika
    (naturally) inimical to it. Backs the "with inimical planets" clause of #10
    (HTJAH-I:3436-3437). Nodes carry no naisargika relation table -> never
    inimical co-tenant by this leaf."""

    def __init__(self, planet: str) -> None:
        self.planet = planet

    def evaluate(self, ctx: C.EvalContext) -> bool:
        p = ctx.chart.planets.get(self.planet)
        if p is None:
            return False
        for name, q in ctx.chart.planets.items():
            if name == self.planet or q.rasi_house != p.rasi_house:
                continue
            if naisargika(self.planet, name) == "enemy":
                return True
        return False


class _BeneficOccupiesOrAspects3rd(C.Condition):
    """A natural benefic resides in OR casts a whole-sign aspect on the 3rd house.
    Backs #7 "good planets reside in 3 or aspect it" (HTJAH-I:3430-3431)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        for name in NATURAL_BENEFICS:
            p = ctx.chart.planets.get(name)
            if p is None:
                continue
            if p.rasi_house == 3 or drishti.aspects_house(name, 3, ctx.chart):
                return True
        return False


class _MarsAndThirdLordClearOfDusthana(C.Condition):
    """Both Mars (Karaka) and the 3rd lord are placed OUTSIDE the 6th, 8th and 11th
    whole-sign houses. The core of #6 (the well-disposed-brothers combination,
    HTJAH-I:3428-3430). The benefic-association / aspect refinement is carried in
    the result text, not over-encoded here."""

    _BAD: Final[frozenset[int]] = frozenset({6, 8, 11})

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _third_lord(ctx.chart)
        lp, kp = ctx.chart.planets.get(lord), ctx.chart.planets.get(_KARAKA)
        if lp is None or kp is None:
            return False
        return lp.rasi_house not in self._BAD and kp.rasi_house not in self._BAD


class _MarsAndThirdLordInParity(C.Condition):
    """Mars (Karaka) AND the 3rd lord both occupy signs of the given parity, and at
    least one planet of `aspect_class` aspects either of them. parity="odd" +
    masculine planets -> brothers (#11); parity="even" + feminine planets -> sisters
    (#12) (HTJAH-I:3439-3441). 'sign' here is the rasi sign (1..12); odd signs are
    the odd-numbered rashis (Aries, Gemini, ...)."""

    def __init__(self, parity: str, aspect_class: frozenset[str]) -> None:
        self.parity, self.aspect_class = parity, aspect_class

    def _sign_ok(self, sign: int) -> bool:
        return (sign % 2 == 1) if self.parity == "odd" else (sign % 2 == 0)

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _third_lord(ctx.chart)
        lp, kp = ctx.chart.planets.get(lord), ctx.chart.planets.get(_KARAKA)
        if lp is None or kp is None:
            return False
        if not (self._sign_ok(lp.sign) and self._sign_ok(kp.sign)):
            return False
        targets = {lord, _KARAKA}
        return any(
            name in self.aspect_class and name not in targets
            and any(drishti.aspects_planet(name, t, ctx.chart) for t in targets)
            for name in ctx.chart.planets)


def _karaka_or_lord_dignity(states: set[str]) -> C.Condition:
    """Mars (Karaka) OR the 3rd lord holds one of `states` D1 dignities. Used to
    compose #8 (exalt / own) and #10 (debil)."""
    return C.Or(
        C.HasDignity(_KARAKA, states),
        _ThirdLordHasDignity(states))


class _ThirdLordHasDignity(C.Condition):
    """The 3rd lord's D1 compound dignity is one of `states`. Resolves the lord then
    reuses the shared ``HasDignity`` leaf."""

    def __init__(self, states: set[str]) -> None:
        self.states = states

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return C.HasDignity(_third_lord(ctx.chart), self.states).evaluate(ctx)


class _KarakaOrLordVargaDignity(C.Condition):
    """Mars (Karaka) OR the 3rd lord is exalted / own / in a benefic's sign IN the
    Navamsha. Backs the "own Navamsha, or Navamsha of benefics" clause of #8
    (HTJAH-I:3432-3433). 'Navamsha of benefics' -> the D9 sign is owned by a
    natural benefic (Jupiter/Venus/Mercury/Moon); expressed via VargaDignity
    'own' (own benefic varga) is too narrow, so a benefic-lord check is added."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        for who in (_KARAKA, _third_lord(ctx.chart)):
            if C.VargaDignity(who, "D9", {"exalt", "own"}).evaluate(ctx):
                return True
            p = ctx.chart.planets.get(who)
            if p is not None and SIGN_LORDS[p.navamsa_sign] in NATURAL_BENEFICS:
                return True
        return False


class _ThirdLordDebilAndMaleficConjunct(C.Condition):
    """The 3rd lord is debilitated AND shares its house with a natural malefic.
    Backs #18 (HTJAH-I:3457-3458)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _third_lord(ctx.chart)
        if not C.HasDignity(lord, {"debil"}).evaluate(ctx):
            return False
        lp = ctx.chart.planets.get(lord)
        if lp is None:
            return False
        return any(name != lord and name in NATURAL_MALEFICS
                   and q.rasi_house == lp.rasi_house
                   for name, q in ctx.chart.planets.items())


class _ThirdLordCombust(C.Condition):
    """The 3rd lord is combust. Resolves the lord then reuses ``Combust`` (#10)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return C.Combust(_third_lord(ctx.chart)).evaluate(ctx)


class _ThirdLordWithInimical(C.Condition):
    """The 3rd lord shares its house with a naisargika-inimical planet (#10)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return _BodyWithInimical(_third_lord(ctx.chart)).evaluate(ctx)


def _lord_with(rule_id: str, planet: str, result: str, line: int,
               polarity: str) -> RuleRecord:
    """One "3rd lord with <planet>" courage atom (#19-#26 family)."""
    frame = "LAGNA/KARAKA" if planet == _KARAKA else "LAGNA"
    return RuleRecord(
        id=rule_id, house=3, signification="courage", group="combination",
        kind="evaluable", condition=_ThirdLordConjunct(planet),
        fortified=None, afflicted=result, frame=frame, varga="D1",
        polarity=polarity, source=Citation("HTJAH-I", line))


RULES: Final[tuple[RuleRecord, ...]] = (
    # — A. siblings: presence / count / disposition (HTJAH-I:3351-3454) —
    # #1 — 3rd lord well-disposed in 3rd/6th/11th -> a number of younger brothers.
    RuleRecord(
        id="H3.C.1", house=3, signification="siblings", group="combination",
        kind="evaluable",
        condition=C.Or(C.LordIn(3, 3), C.LordIn(3, 6), C.LordIn(3, 11)),
        fortified="the 3rd lord well-disposed in the 3rd, 6th or 11th -> a number of "
                  "younger brothers",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 3351)),
    # #2 — 3rd lord = Mars occupying the 3rd -> loses all younger brothers (Saturn
    #      similar). Encoded as the lord-is-Karaka collapse + Mars in the 3rd.
    RuleRecord(
        id="H3.C.2", house=3, signification="siblings", group="combination",
        kind="evaluable",
        condition=C.And(_ThirdLordIsKaraka(), C.InRashiHouse("Mars", 3)),
        fortified=None,
        afflicted="when the 3rd lord is Mars and occupies the 3rd, the native loses "
                  "ALL his younger brothers; Saturn in the same position gives a "
                  "similar effect",
        frame="LAGNA/KARAKA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 3352)),
    # #3 — Sun in the 3rd -> kills ELDER brothers (the elder is an 11th-house matter).
    RuleRecord(
        id="H3.C.3", house=3, signification="siblings", group="combination",
        kind="evaluable",
        condition=C.InRashiHouse("Sun", 3),
        fortified=None,
        afflicted="the Sun in the 3rd kills elder brothers (the elder brother is read "
                  "from the 11th)",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 3353)),
    # #4 — DESCRIPTIVE: beneficial Nakshatra + Navamsha + benefic aspect + Mars well
    #      disposed -> man of character. TODO(predicate): needs a "beneficial
    #      nakshatra" classifier and a Mars strength-aggregate that the condition
    #      algebra does not yet carry; surfaced by placement, not faked.
    RuleRecord(
        id="H3.C.4", house=3, signification="courage", group="combination",
        kind="descriptive", condition=None,
        fortified="3rd lord in a beneficial Nakshatra and Navamsha, aspected by "
                  "benefics, with Mars equally well disposed -> a man of character and "
                  "conviction, brave and straightforward",
        afflicted=None,
        frame="LAGNA/KARAKA/D9", varga="D9", polarity="benefic",
        source=Citation("HTJAH-I", 3421)),
    # #5 — friendly 3rd lord in a Trikona from Lagna OR with Lagnadhipati -> family
    #      of brothers. Trikona placement + lords-conjunct; "friendly" -> result text.
    RuleRecord(
        id="H3.C.5", house=3, signification="siblings", group="combination",
        kind="evaluable",
        condition=C.Or(C.LordIn(3, 1), C.LordIn(3, 5), C.LordIn(3, 9),
                       C.LordsConjunct(3, 1)),
        fortified="a friendly 3rd lord occupying a Trikona (1/5/9) from the Lagna, or "
                  "joined with the Lagna lord, generally assures a family of brothers",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 3423)),
    # #6 — 3rd lord AND Mars clear of 6/8/11, with benefics -> many long-lived
    #      well-to-do brothers (the benefic-association refinement -> result text).
    RuleRecord(
        id="H3.C.6", house=3, signification="siblings", group="combination",
        kind="evaluable",
        condition=_MarsAndThirdLordClearOfDusthana(),
        fortified="the 3rd lord and the Karaka (Mars) both clear of the 6th/8th/11th "
                  "and (when aspected by or conjoined with benefics and otherwise well "
                  "disposed) -> many long-lived, well-to-do brothers",
        afflicted=None,
        frame="LAGNA/KARAKA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 3428)),
    # #7 — good planets reside in or aspect the 3rd -> many brothers.
    RuleRecord(
        id="H3.C.7", house=3, signification="siblings", group="combination",
        kind="evaluable",
        condition=_BeneficOccupiesOrAspects3rd(),
        fortified="good (benefic) planets residing in or aspecting the 3rd -> he will "
                  "get many brothers (same when Mars and the 3rd house are similarly "
                  "well situated)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 3430)),
    # #8 — 3rd lord or Mars in exaltation / own house / own Navamsha / Navamsha of
    #      benefics -> increase in brothers.
    RuleRecord(
        id="H3.C.8", house=3, signification="siblings", group="combination",
        kind="evaluable",
        condition=C.Or(_karaka_or_lord_dignity({"exalt", "own"}),
                       _KarakaOrLordVargaDignity()),
        fortified="the 3rd lord or Mars in exaltation, own house, own Navamsha, or the "
                  "Navamsha of benefics -> an increase in brothers may be expected",
        afflicted=None,
        frame="LAGNA/KARAKA/D9", varga="D9", polarity="benefic",
        source=Citation("HTJAH-I", 3432)),
    # #9 — 3rd lord is an evil planet, or evil planets occupy the 3rd -> very few
    #      brothers.
    RuleRecord(
        id="H3.C.9", house=3, signification="siblings", group="combination",
        kind="evaluable",
        condition=C.Or(_ThirdLordIsMalefic(), C.CountInHouse(3, 1, "malefic")),
        fortified=None,
        afflicted="the 3rd lord an evil (malefic) planet, or evil planets occupying "
                  "the 3rd -> very few brothers",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 3435)),
    # #10 — Mars or 3rd lord debilitated, combust, or with inimical planets ->
    #       destruction of the indications of the 3rd house.
    RuleRecord(
        id="H3.C.10", house=3, signification="siblings", group="combination",
        kind="evaluable",
        condition=C.Or(
            _karaka_or_lord_dignity({"debil"}),
            C.Combust(_KARAKA), _ThirdLordCombust(),
            _BodyWithInimical(_KARAKA), _ThirdLordWithInimical()),
        fortified=None,
        afflicted="the Karaka (Mars) or the 3rd lord debilitated, in combustion, or "
                  "with inimical planets -> destruction of the indications of the 3rd "
                  "house should be predicted",
        frame="LAGNA/KARAKA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 3436)),
    # #11 — Mars + 3rd lord in ODD signs, aspected by MASCULINE planets -> brothers.
    RuleRecord(
        id="H3.C.11", house=3, signification="siblings", group="combination",
        kind="evaluable",
        condition=_MarsAndThirdLordInParity("odd", _MASCULINE),
        fortified="Mars and the 3rd lord in odd signs, aspected by masculine planets "
                  "(Sun/Mars/Jupiter) -> the person will have brothers",
        afflicted=None,
        frame="LAGNA/KARAKA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 3439)),
    # #12 — Mars + the 3rd house in EVEN signs, aspected by FEMININE planets ->
    #       sisters.
    RuleRecord(
        id="H3.C.12", house=3, signification="siblings", group="combination",
        kind="evaluable",
        condition=_MarsAndThirdLordInParity("even", _FEMININE),
        fortified="Mars and the 3rd (lord) in even signs, aspected by feminine planets "
                  "(Moon/Venus) -> the person will have sisters",
        afflicted=None,
        frame="LAGNA/KARAKA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 3440)),
    # #13 — 3rd house weak but associated with Mars AND Jupiter -> still brothers.
    RuleRecord(
        id="H3.C.13", house=3, signification="siblings", group="combination",
        kind="evaluable",
        condition=C.And(C.InRashiHouse("Mars", 3), C.InRashiHouse("Jupiter", 3)),
        fortified="even if the 3rd house is weak, the person will have brothers when it "
                  "is associated with Mars and Jupiter",
        afflicted=None,
        frame="LAGNA/KARAKA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 3441)),
    # #14 — Jupiter in the 11th -> worry on account of the ELDER brother.
    RuleRecord(
        id="H3.C.14", house=3, signification="siblings", group="combination",
        kind="evaluable",
        condition=C.InRashiHouse("Jupiter", 11),
        fortified=None,
        afflicted="Jupiter in the 11th -> worry on account of the elder brother (the "
                  "elder brother, his prosperity and adversity are judged from the 11th)",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 3444)),
    # #15 — DESCRIPTIVE: sibling COUNT = number of Navamsa gained by the strongest of
    #       {3rd lord, Mars, planets-in-3rd}. TODO(predicate): the D9 Navamsa-gained
    #       count + strongest-of selection is not yet built; surfaced, not faked.
    RuleRecord(
        id="H3.C.15", house=3, signification="siblings", group="combination",
        kind="descriptive", condition=None,
        fortified="the number of brothers/sisters = the number of Navamsa gained by "
                  "the 3rd lord, Mars, or the planets in the 3rd, whichever is the most "
                  "powerful",
        afflicted=None,
        frame="STRONGEST_OF([LORD_OF:3,Mars,IN_3])", varga="D9", polarity="neutral",
        source=Citation("HTJAH-I", 3447)),
    # #16 — DESCRIPTIVE: elder-brother count = Navamsa passed by the 11th (Kalidasa /
    #       Uttara Kalamrita). TODO(predicate): D9 Navamsa-passed count not yet built.
    RuleRecord(
        id="H3.C.16", house=3, signification="siblings", group="combination",
        kind="descriptive", condition=None,
        fortified="the number of ELDER brothers = the number of Navamsa passed by the "
                  "11th house (Kalidasa, Uttara Kalamrita)",
        afflicted=None,
        frame="FROM(11)", varga="D9", polarity="neutral",
        source=Citation("HTJAH-I", 3449)),
    # #17 — DESCRIPTIVE: younger-brother count = Navamsa of the 3rd Bhava yet to pass.
    #       TODO(predicate): D9 Navamsa-yet-to-pass count not yet built.
    RuleRecord(
        id="H3.C.17", house=3, signification="siblings", group="combination",
        kind="descriptive", condition=None,
        fortified="the number of Navamsa of the 3rd Bhava yet to pass indicates the "
                  "YOUNGER brothers",
        afflicted=None,
        frame="FROM(3)", varga="D9", polarity="neutral",
        source=Citation("HTJAH-I", 3453)),

    # — B. courage / personality: the "3rd lord with X" atoms (HTJAH-I:3456-3463) —
    # #18 — 3rd lord debilitated + conjunct malefic -> unskilful and timid.
    RuleRecord(
        id="H3.C.18", house=3, signification="courage", group="combination",
        kind="evaluable",
        condition=_ThirdLordDebilAndMaleficConjunct(),
        fortified=None,
        afflicted="the 3rd lord in debilitation and conjunct a malefic -> the person "
                  "becomes unskilful and timid",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 3457)),
    # #19-#26 — "3rd lord with <planet>" courage colourings.
    _lord_with("H3.C.19", "Sun",
               "the 3rd lord with the Sun -> headstrong and furious", 3458,
               "malefic"),
    _lord_with("H3.C.20", "Moon",
               "the 3rd lord with the Moon -> bold in mind", 3459, "benefic"),
    _lord_with("H3.C.21", "Mars",
               "the 3rd lord with Mars -> powerful and brave", 3459, "benefic"),
    _lord_with("H3.C.22", "Mercury",
               "the 3rd lord with Mercury -> cautious and chivalrous", 3459,
               "benefic"),
    _lord_with("H3.C.23", "Jupiter",
               "the 3rd lord with Jupiter -> shrewd of mind and bold in "
               "temperament", 3460, "benefic"),
    _lord_with("H3.C.24", "Venus",
               "the 3rd lord with Venus -> passionate; enters quarrels arising out "
               "of connections with women", 3460, "neutral"),
    _lord_with("H3.C.25", "Saturn",
               "the 3rd lord with Saturn -> dull and stupid", 3461, "malefic"),
    # #26 — 3rd lord with Rahu OR Ketu -> bold/martial outside, timid heart, weak
    #       mind. Encoded as a disjunction over the two nodes.
    RuleRecord(
        id="H3.C.26", house=3, signification="courage", group="combination",
        kind="evaluable",
        condition=C.Or(_ThirdLordConjunct("Rahu"), _ThirdLordConjunct("Ketu")),
        fortified=None,
        afflicted="the 3rd lord with Rahu or Ketu -> the person looks bold and martial "
                  "outside but has a timid heart and a weak mind",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 3462)),

    # — C. deafness / throat / ears (HTJAH-I:3465-3468) —
    # #27 — 3rd lord with Rahu (the lord-of-Rahu's-house clause has no clean
    #       predicate, kept in result text) -> fear from reptiles.
    RuleRecord(
        id="H3.C.27", house=3, signification="courage", group="combination",
        kind="evaluable",
        condition=_ThirdLordConjunct("Rahu"),
        fortified=None,
        afflicted="the 3rd lord with Rahu (or with the lord of the house where Rahu "
                  "is) -> fear from reptiles",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 3465)),
    # #28 — Mercury with the 3rd lord -> throat disease.
    RuleRecord(
        id="H3.C.28", house=3, signification="ear_throat", group="combination",
        kind="evaluable",
        condition=_ThirdLordConjunct("Mercury"),
        fortified=None,
        afflicted="Mercury with the 3rd lord -> throat disease",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 3466)),
    # #29 — evil planets in the 3rd (esp. in Dwadasamsa) -> throat troubles, ear
    #       defects and deafness. Rasi core fires; the D12 refinement -> result text.
    RuleRecord(
        id="H3.C.29", house=3, signification="ear_throat", group="combination",
        kind="evaluable",
        condition=C.CountInHouse(3, 1, "malefic"),
        fortified=None,
        afflicted="evil planets in the 3rd -> troubles connected with the throat; ear "
                  "defects and deafness should be predicted, particularly when the "
                  "affliction also falls in the Dwadasamsa (D12)",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 3467)),
    # #30 — (Practical Experience / Chart 63) Lagna lord + 2nd lord connect with the
    #       3rd lord -> cordial relations with brothers + mutual financial benefit.
    RuleRecord(
        id="H3.C.30", house=3, signification="siblings", group="combination",
        kind="evaluable",
        condition=C.Or(C.LordsConjunct(1, 3), C.LordsConjunct(2, 3)),
        fortified="the Lagna lord and the lord of wealth (2nd) connected with the lord "
                  "of the house of brothers (3rd) -> cordial relations between brothers "
                  "and mutual financial benefit; the native's finances improve through "
                  "the brothers",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 4087)),
)
