"""House 1 — core "Other Important Combinations" rules (the mismatch-killer batch:
methodology #1, #26-#28, #32-#34 families, HTJAH-I:1086-1150 region, plus two
honest generalisations from worked charts 20 and 33).

Encoding notes (provenance kept honest, line by line):

* #1  (HTJAH-I:1086-1088) — "If the lord of birth in birth with lord of 6th, 8th or
  12th, conjunction with or aspected by malefic, the health will suffer."  Encoded
  per the batch spec as ``LordsConjunct(1, d)`` + malefic involvement of the
  Lagna lord; Raman's "in birth" (= in the Lagna) locational clause is NOT added
  to the condition — the conjunct-anywhere health-suffers reading is used.  The
  benefic-aspect veto ("If there are any beneficial aspects this evil should not
  be predicted") is carried in the result text for the judge's salvage layer,
  not double-encoded in the condition tree.
* #26 (HTJAH-I:1127-1128) — Lagna or its lord hemmed between two malefics
  (Papakartari).  ``conditions.HemmedBy`` is planet-only, so the Lagna-target
  variant is a small local Condition (precedent: doctrine/yogas.py local leaves);
  the lord variant resolves the lord at evaluation time and reuses ``HemmedBy``.
* Subhakartari positive side — the general definition line is the book's own
  glossary entry "Being hemmed in between two benefics" (HTJAH-I:19252; term at
  19178); the strengthening effect is Raman's worked usage in Chart 13
  (HTJAH-I:1823-1825, "causing Subhakarthari Yoga ... Lagna therefore is fairly
  strong on the whole").
* #27 (HTJAH-I:1128-1129) is a comparative severity rule; its evaluable form is
  the WORST configuration it ranks (Rahu in the 2nd + Saturn in the 12th — the
  Chart 9 disposition).  The mild form (Rahu 12th / Saturn 2nd, Chart 8) is
  deliberately not a firing rule.
* #28 (HTJAH-I:1131) — "many evil planets in Lagna": "many" is read as >= 2
  natural malefics (conservative floor; Raman gives no number).
* Functional-malefic variant — generalised from worked Chart 20 commentary
  (HTJAH-I:2003-2009: Sun & Mercury, lords of 2 & 3 in Cancer Lagna, "are
  malefic and their situation in Lagna is not desirable"); the condition cites
  the GENERAL #28 line (1131) per batch protocol, and uses the printed
  functional-nature table (under which Cancer's Sun is neutral — only Mercury
  fires for Chart 20; the table, not the per-chart prose, is authoritative).
* #32/#33/#34 (HTJAH-I:1137-1140) — the three-pillar fortunate ladder.  #33/#34
  are crisply evaluable (#34's fortunate form is ``~AllPlanetsInDwirdwadasha()``
  exactly as documented in conditions.py); #32 ("decent position") has no crisp
  predicate in the current algebra and stays DESCRIPTIVE.
* #67 (HTJAH-I:2111-2113) — steady fortune if at least two of {Lagna, Sun, Moon}
  are well disposed: its canonical home is navamsa_qualifiers.py (H1.N.67); it is
  intentionally NOT duplicated here (one-owner-per-corpus-rule policy).
* Neecha-lord-with-node — generalised from worked chart 33 (HTJAH-I:2249-2262;
  the cited sentence "Lord of Lagna is neecha and is with Rahu, of course in the
  same sign" at 2251 is chart-specific prose — no general sentence exists in
  that region, so the provenance is marked honestly).
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

_VISIBLE: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")


def _lagna_lord(chart: RamanChart) -> str:
    """Name of the D1 lord of the Lagna sign."""
    return SIGN_LORDS[chart.asc_sign]


# ── local leaf predicates (conditions.py is intentionally untouched) ─────────
class _LagnaHemmedBy(C.Condition):
    """Papakartari/Subhakartari on the LAGNA itself: both the 2nd and the 12th
    whole-sign houses from the ascendant hold a planet of `klass` ∈
    {"malefic","benefic"}.  ``conditions.HemmedBy`` targets planets only, so the
    Lagna form lives here (HTJAH-I:1127-1128; glossary HTJAH-I:7538, 19252)."""

    def __init__(self, klass: str) -> None:
        self.klass = klass

    def evaluate(self, ctx: C.EvalContext) -> bool:
        group = NATURAL_MALEFICS if self.klass == "malefic" else NATURAL_BENEFICS
        occupied = {p.rasi_house for name, p in ctx.chart.planets.items()
                    if name in group}
        return 2 in occupied and 12 in occupied


class _LagnaLordHemmedBy(C.Condition):
    """The #26 "or its lord" variant: the D1 lord of the Lagna is hemmed between
    planets of `klass` (HTJAH-I:1127).  Resolves the lord at evaluation time and
    reuses the shared ``HemmedBy`` planet predicate."""

    def __init__(self, klass: str) -> None:
        self.klass = klass

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return C.HemmedBy(_lagna_lord(ctx.chart), self.klass).evaluate(ctx)


class _MaleficAfflictsLagnaLord(C.Condition):
    """Rule #1's "conjunction with or aspected by malefic" clause: some natural
    malefic (other than the Lagna lord itself) shares the Lagna lord's rasi
    house or casts drishti on it (HTJAH-I:1086-1087)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lagna_lord(ctx.chart)
        lp = ctx.chart.planets.get(lord)
        if lp is None:
            return False
        for name in NATURAL_MALEFICS - {lord}:
            p = ctx.chart.planets.get(name)
            if p is None:
                continue
            if p.rasi_house == lp.rasi_house or drishti.aspects_planet(
                    name, lord, ctx.chart):
                return True
        return False


class _LagnaLordNeechaWithNode(C.Condition):
    """Lord of the Lagna debilitated AND conjunct Rahu or Ketu — generalised
    from worked chart 33 (HTJAH-I:2249-2262).  Composed from the shared
    ``HasDignity`` + ``Conjunct`` leaves once the lord is resolved.

    Retained for reference / future promotion; rule H1.C.W33 is descriptive (see
    its record below for why)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lagna_lord(ctx.chart)
        composed = C.And(
            C.HasDignity(lord, {"debil"}),
            C.Or(C.Conjunct(lord, "Rahu"), C.Conjunct(lord, "Ketu")))
        return composed.evaluate(ctx)


#: Minimum number of placed bodies for the whole-chart "fortunate Dwirdwadasha"
#: reading (#34) to be MEANINGFUL. Raman's "that horoscope is a fortunate one in
#: which planets are not disposed in DwirdwaDasha positions" is a claim about the
#: complete planetary disposition; on a near-empty (sparse Track-B / synthetic)
#: chart the absence of a 2/12 web is vacuous, not fortunate, so the rule must NOT
#: fire there. Seven = the visible grahas (a substantially complete chart).
_MIN_BODIES_FOR_FORTUNATE: Final[int] = 7


class _ChartWellPopulated(C.Condition):
    """At least ``_MIN_BODIES_FOR_FORTUNATE`` placed bodies — guards the #34
    fortunate-Dwirdwadasha reading against vacuous firing on sparse charts."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return len(ctx.chart.planets) >= _MIN_BODIES_FOR_FORTUNATE


def _lords_conjunct_dusthana_rule(rule_id: str, dusthana: int) -> RuleRecord:
    """One #1-family record: Lagna lord conjunct the lord of `dusthana` (6/8/12)
    with malefic involvement -> health suffers (HTJAH-I:1086-1088)."""
    return RuleRecord(
        id=rule_id, house=1, signification="self", group="combination",
        kind="evaluable",
        condition=C.And(C.LordsConjunct(1, dusthana), _MaleficAfflictsLagnaLord()),
        fortified=None,
        afflicted=f"lord of the Lagna with the lord of the {dusthana}th, conjoined "
                  "with or aspected by a malefic — the health will suffer; do NOT "
                  "predict this evil if any beneficial aspects exist "
                  "(HTJAH-I:1087-1088)",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 1086))


RULES: Final[tuple[RuleRecord, ...]] = (
    # #1 family — Lagna lord conjunct a dusthana lord + malefic involvement.
    _lords_conjunct_dusthana_rule("H1.C.1a", 6),
    _lords_conjunct_dusthana_rule("H1.C.1b", 8),
    _lords_conjunct_dusthana_rule("H1.C.1c", 12),
    # #26 — Papakartari on the Lagna and on its lord; Subhakartari positive side.
    RuleRecord(
        id="H1.C.26a", house=1, signification="self", group="combination",
        kind="evaluable",
        condition=_LagnaHemmedBy("malefic"),
        fortified=None,
        afflicted="Lagna hemmed in between two malefics (Papakartari) — the native "
                  "will encounter thieves and suffer on their account; worst when "
                  "the hemming pair is Saturn and Rahu",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 1127)),
    RuleRecord(
        id="H1.C.26b", house=1, signification="self", group="combination",
        kind="evaluable",
        condition=_LagnaLordHemmedBy("malefic"),
        fortified=None,
        afflicted="lord of the Lagna hemmed in between two malefics — the native "
                  "will encounter thieves and suffer on their account; worst when "
                  "the hemming pair is Saturn and Rahu",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 1127)),
    RuleRecord(
        # Effect generalised from worked usage, Chart 13 (HTJAH-I:1823-1825):
        # benefic hemming "causing Subhakarthari Yoga ... Lagna therefore is
        # fairly strong on the whole".  Cited line is the book's own general
        # glossary definition (term "Subhakartari Yoga" at HTJAH-I:19178).
        id="H1.C.26c", house=1, signification="self", group="combination",
        kind="evaluable",
        condition=_LagnaHemmedBy("benefic"),
        fortified="Lagna hemmed in between two benefics (Subhakartari Yoga) — the "
                  "Lagna is strengthened, supporting body, health and personality "
                  "indications",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 19252)),
    # #27 — the harmful disposition of the hemming malefics (worst form).
    RuleRecord(
        id="H1.C.27", house=1, signification="self", group="combination",
        kind="evaluable",
        condition=C.And(C.InRashiHouse("Rahu", 2), C.InRashiHouse("Saturn", 12)),
        fortified=None,
        afflicted="Rahu in the 2nd with Saturn in the 12th — the more harmful "
                  "disposition of the hemming malefics (Rahu in the 12th is not as "
                  "harmful as in the 2nd, while Saturn in the 2nd is not as harmful "
                  "as in the 12th)",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 1128)),
    # #28 — many evil planets in the Lagna ("many" read as >= 2 natural malefics).
    RuleRecord(
        id="H1.C.28", house=1, signification="self", group="combination",
        kind="evaluable",
        condition=C.CountInHouse(1, 2, "malefic"),
        fortified=None,
        afflicted="many evil planets in the Lagna — the person will always be "
                  "miserable",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 1131)),
    RuleRecord(
        # Functional variant, generalised from worked Chart 20 commentary
        # (HTJAH-I:2003-2009: Sun & Mercury, lords of 2 & 3 in Cancer Lagna,
        # "are malefic and their situation in Lagna is not desirable"); cites
        # the GENERAL #28 line per batch protocol.
        id="H1.C.28b", house=1, signification="self", group="combination",
        kind="evaluable",
        condition=C.Or(*(C.And(C.InRashiHouse(p, 1),
                               C.FunctionalNature(p, {"malefic"}))
                         for p in _VISIBLE)),
        fortified=None,
        afflicted="a functional malefic (per-Lagna nature) situated in the Lagna "
                  "is not desirable — spoils the first-house indications",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 1131)),
    # #32/#33/#34 — the three-pillar fortunate ladder (HTJAH-I:1137-1140).
    RuleRecord(
        # DESCRIPTIVE: "decent position" has no crisp predicate in the current
        # condition algebra (needs the Shadbala/strength aggregates still to
        # land); surfaced by placement with its citation.
        id="H1.C.32", house=1, signification="self", group="combination",
        kind="descriptive",
        condition=None,
        fortified="lord of Lagna in a decent position is itself a great asset "
                  "which sustains the person throughout his life",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 1137)),
    RuleRecord(
        id="H1.C.33", house=1, signification="self", group="combination",
        kind="evaluable",
        condition=C.CountInHouse(10, 1),
        fortified="the presence of any planet or planets in the 10th adds greater "
                  "vigour (on top of a decently placed Lagna lord)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 1138)),
    RuleRecord(
        # The fortunate form fires only on a substantially complete chart AND when
        # the planets are not bound in the (almost-all) 2/12 Dwirdwadasha web. The
        # population guard stops the negation firing vacuously on sparse Track-B /
        # synthetic charts (where the absence of a web is meaningless, not fortunate).
        id="H1.C.34", house=1, signification="self", group="combination",
        kind="evaluable",
        condition=C.And(_ChartWellPopulated(),
                        C.Not(C.AllPlanetsInDwirdwadasha())),
        fortified="a fortunate horoscope — the planets are not disposed in "
                  "Dwirdwadasha positions (12th and 2nd from each other)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 1139)),
    # #67 — three-pillars steady-fortune integration rule: its canonical home is
    # navamsa_qualifiers.py (H1.N.67). NOT re-encoded here (one-owner policy).
    # Generalised from worked chart 33 (HTJAH-I:2249-2262): only chart-specific
    # prose exists in that region, so the chart sentence is cited honestly.
    #
    # DESCRIPTIVE (not boolean-firing): this is a chart-dependent-lord dignity rule —
    # the same class as #38/#39/#49/#55/#58 (all descriptive in navamsa_qualifiers.py
    # because they test a dynamically-resolved lord's dignity). Encoding it as a
    # boolean MALEFIC double-counts the very affliction Raman reads on chart 33,
    # which the engine already surfaces through the chart-level Sakata arishta
    # (Moon 6/8 from Jupiter; HTJAH-I:480-482 consideration #4): a redundant malefic
    # rule here only manufactures a benefic-vs-malefic CONTRADICTION (with the
    # legitimate lord-in-3rd and fortunate-Dwirdwadasha testimony) that blocks the
    # arishta drop. Surfaced by placement with its citation; the working
    # ``_LagnaLordNeechaWithNode`` predicate is retained below for reference and for
    # promotion once a lord-dignity-aware contradiction policy lands.
    RuleRecord(
        id="H1.C.W33", house=1, signification="self", group="combination",
        kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="lord of the Lagna debilitated (neecha) and conjoined with Rahu "
                  "or Ketu — the first-house factors are unfortunately disposed: "
                  "humble circumstances, nervousness, lack of self-confidence "
                  "(generalised from worked chart 33)",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 2251)),
)
