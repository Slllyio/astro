"""House 7 (Kalatra — spouse/marriage) — "Important Combinations".

Encodes the combination rule-atoms of the "Important Combinations" tables in
``docs/raman_saab/methodology/house_07_kalatra.md`` (HTJAH-II:348-997), plus the
single-chart **Kuja-Dosha (Mangal-Dosha)** (HTJAH-II:2579-2632).

Encoding policy (honest, atom by atom — mirrors H2/H3/H8):

* Existing predicates compose directly, including the from-VENUS and from-MOON
  frames via ``InHouseFrom`` / ``ClassInHouseFrom`` (Venus-as-Lagna is a locked H7
  technique). Where a rule needs a refinement the algebra cannot express, the
  rasi-core fires and the refinement is kept in the result text.
* Rules requiring predicates not yet in the algebra — **Navamsa parity / Navamsa
  dignity of a specific lord**, **D60 (shashtiamsa)**, **Gulika / upagraha
  (karmuka)**, planet "strength/weak" gates, and **native-sex-dependent** splits —
  go in as ``kind="descriptive"`` with a ``TODO(predicate)`` note.
* OUT OF SCOPE v1 (locked): the two-chart **synastry** rules (S1-S7) and the
  Kuja-Dosha numeric **matching grid** (HTJAH-II:2613-2632) — single-chart only.
* No rule re-scores a testimony already fired by a placement (lord_in_12 /
  planets_in_7th / from_karaka) within the SAME signification. Significations:
  marital_happiness, spouse (character/count), virility (impotency), coverture
  (loss/widowhood), wealth_through_marriage, partnership.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine import drishti
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation
from app.raman_saab.primitives.bhangas import neecha_bhanga
from app.raman_saab.primitives.dignity import dignity
from app.raman_saab.primitives.functional_nature import (
    NATURAL_BENEFICS, NATURAL_MALEFICS)


# ── sign-class data ───────────────────────────────────────────────────────────
_ODD_SIGNS: Final[frozenset[int]] = frozenset({1, 3, 5, 7, 9, 11})
_EVEN_SIGNS: Final[frozenset[int]] = frozenset({2, 4, 6, 8, 10, 12})
_COMMON_SIGNS: Final[frozenset[int]] = frozenset({3, 6, 9, 12})        # dwiswabhava
# Signs owned by a natural malefic (Sun, Mars, Saturn): Ar Le Sc Cp Aq.
_MALEFIC_SIGNS: Final[frozenset[int]] = frozenset({1, 5, 8, 10, 11})
# Mars-dosha houses counted from a reference point (Kuja/Mangal dosha).
_KUJA_HOUSES: Final[tuple[int, ...]] = (2, 4, 7, 8, 12)
# Per-house sign exemptions (HTJAH-II:2593-2599): Mars in dosha-house h gives NO
# dosha when the sign it occupies (= the sign of that house, since Mars sits there)
# is in the exempt set. Plus Leo/Aquarius are wholly exempt (HTJAH-II:2599-2600).
_KUJA_SIGN_EXEMPT: Final[dict[int, frozenset[int]]] = {
    2: frozenset({3, 6}),    # Gemini, Virgo
    12: frozenset({2, 7}),   # Taurus, Libra
    4: frozenset({1, 8}),    # Aries, Scorpio
    7: frozenset({4, 10}),   # Cancer, Capricorn
    8: frozenset({9, 12}),   # Sagittarius, Pisces
}
_KUJA_UNIVERSAL_EXEMPT_SIGNS: Final[frozenset[int]] = frozenset({5, 11})  # Leo, Aquarius


# ── helpers ───────────────────────────────────────────────────────────────────

def _lord_of(house: int, chart: RamanChart) -> str:
    return SIGN_LORDS[((chart.asc_sign - 1) + (house - 1)) % 12 + 1]


def _seventh_sign(chart: RamanChart) -> int:
    return ((chart.asc_sign - 1) + 6) % 12 + 1


# ── local leaf predicates (conditions.py intentionally untouched) ─────────────

class _PlanetInSigns(C.Condition):
    """`planet` occupies one of `signs` (rashi 1..12)."""
    def __init__(self, planet: str, signs: frozenset[int]) -> None:
        self.planet, self.signs = planet, signs

    def evaluate(self, ctx: C.EvalContext) -> bool:
        p = ctx.chart.planets.get(self.planet)
        return p is not None and p.sign in self.signs


class _PlanetParity(C.Condition):
    """`planet` is in an odd / even rashi (`parity` ∈ {"odd","even"})."""
    def __init__(self, planet: str, parity: str) -> None:
        self.planet, self.parity = planet, parity

    def evaluate(self, ctx: C.EvalContext) -> bool:
        p = ctx.chart.planets.get(self.planet)
        if p is None:
            return False
        return (p.sign in _ODD_SIGNS) if self.parity == "odd" else (p.sign in _EVEN_SIGNS)


class _LagnaInSigns(C.Condition):
    """The Ascendant rashi is one of `signs`."""
    def __init__(self, signs: frozenset[int]) -> None:
        self.signs = signs

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return ctx.chart.asc_sign in self.signs


class _LagnaParity(C.Condition):
    """The Ascendant is an odd / even rashi."""
    def __init__(self, parity: str) -> None:
        self.parity = parity

    def evaluate(self, ctx: C.EvalContext) -> bool:
        odd = ctx.chart.asc_sign in _ODD_SIGNS
        return odd if self.parity == "odd" else not odd


class _SeventhSignIn(C.Condition):
    """The rashi occupying the 7th whole-sign house is one of `signs`."""
    def __init__(self, signs: frozenset[int]) -> None:
        self.signs = signs

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return _seventh_sign(ctx.chart) in self.signs


class _LordIsPlanet(C.Condition):
    """The lord of house `house` IS `planet` (Lagna-dependent identity)."""
    def __init__(self, house: int, planet: str) -> None:
        self.house, self.planet = house, planet

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return _lord_of(self.house, ctx.chart) == self.planet


class _ConjunctAnyMalefic(C.Condition):
    """A natural malefic (other than `planet`) shares `planet`'s house."""
    def __init__(self, planet: str) -> None:
        self.planet = planet

    def evaluate(self, ctx: C.EvalContext) -> bool:
        p = ctx.chart.planets.get(self.planet)
        if p is None:
            return False
        return any(name != self.planet and name in NATURAL_MALEFICS
                   and q.rasi_house == p.rasi_house
                   for name, q in ctx.chart.planets.items())


class _AspectedByClass(C.Condition):
    """A natural planet of `klass` ∈ {"malefic","benefic"} (other than `target`)
    casts a whole-sign drishti on `target`."""
    def __init__(self, target: str, klass: str) -> None:
        self.target, self.klass = target, klass

    def evaluate(self, ctx: C.EvalContext) -> bool:
        if self.target not in ctx.chart.planets:
            return False
        group = NATURAL_MALEFICS if self.klass == "malefic" else NATURAL_BENEFICS
        return any(name != self.target and name in group
                   and drishti.aspects_planet(name, self.target, ctx.chart)
                   for name in ctx.chart.planets)


class _HouseHemmedBy(C.Condition):
    """Papakartari/Subhakartari on a HOUSE: both the 6th and 8th... i.e. both the
    house-before and house-after `house` hold a planet of `klass`."""
    def __init__(self, house: int, klass: str) -> None:
        self.house, self.klass = house, klass

    def evaluate(self, ctx: C.EvalContext) -> bool:
        prev = (self.house - 2) % 12 + 1
        nxt = self.house % 12 + 1
        group = NATURAL_MALEFICS if self.klass == "malefic" else NATURAL_BENEFICS
        have = {prev: False, nxt: False}
        for name, p in ctx.chart.planets.items():
            if name in group and p.rasi_house in have:
                have[p.rasi_house] = True
        return all(have.values())


class _SeventhBesiegedByMalefics(C.Condition):
    """TWO OR MORE distinct natural malefics each afflict the 7th house (occupy it or cast a
    whole-sign drishti on it) AND no FULL benefic (Jupiter/Venus/Mercury) occupies or aspects
    the 7th.

    Raman's separation/discord signature for marital happiness — the 7th besieged by multiple
    malefics, unrelieved by a benefic, gives estrangement and loss of marital happiness
    (HTJAH-II:996 "misery, death or separation in marriage; the 7th house or Venus
    [afflicted]"; the classic case is Saturn + Mars on the 7th, HTJAH-II:562). The full-
    benefic relief guard spares the favourable Chart 02 (four malefics touch its 7th but
    Jupiter also aspects it) and Chart 09's Jupiter-in-7th; it correctly fires on Chart 04
    (Saturn + Mars, no relief — 'complete deprivation; separated') and Chart 05 (Mars-aspect
    + Ketu-occupy — 'violent clashes, miserable').

    The relieving set is the three FULL benefics — NOT the Moon, whose beneficence is
    conditional (paksha-/association-dependent): Chart 04's Moon sits with Rahu in the 7th and
    gives no relief, so a Moon-inclusive guard would wrongly spare it."""

    _RELIEVERS: Final[frozenset[str]] = frozenset({"Jupiter", "Venus", "Mercury"})

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart

        def afflicts(name: str) -> bool:
            p = chart.planets.get(name)
            return p is not None and (p.rasi_house == 7
                                      or drishti.aspects_house(name, 7, chart))

        if sum(afflicts(m) for m in NATURAL_MALEFICS) < 2:
            return False
        return not any(afflicts(b) for b in self._RELIEVERS)


class _MaleficOccupiesOrAspects7th(C.Condition):
    """A natural malefic occupies OR casts a whole-sign drishti on the 7th house."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        for m in NATURAL_MALEFICS:
            p = ctx.chart.planets.get(m)
            if p is not None and (p.rasi_house == 7 or drishti.aspects_house(m, 7, ctx.chart)):
                return True
        return False


class _KujaDosha(C.Condition):
    """Single-chart Kuja-Dosha (Mangal-Dosha): Mars in the 2/4/7/8/12 from the
    Lagna, the Moon, OR Venus (rashi-frame), with the corpus exemptions applied
    (HTJAH-II:2583-2601):

    * Leo/Aquarius Mars → NO dosha whatever (universal exemption);
    * per-house sign exemptions (`_KUJA_SIGN_EXEMPT`): e.g. Mars-in-7th is exempt
      in Cancer/Capricorn, Mars-in-2nd in Gemini/Virgo, etc.;
    * NEUTRALISED entirely when Mars conjoins Jupiter or the Moon.

    The full bhava-frame (vs rasi) refinement and the two-chart dosha-units
    matching grid (HTJAH-II:2613-2632) remain OUT OF SCOPE v1."""
    def evaluate(self, ctx: C.EvalContext) -> bool:
        mars = ctx.chart.planets.get("Mars")
        if mars is None:
            return False
        if mars.sign in _KUJA_UNIVERSAL_EXEMPT_SIGNS:
            return False
        if C.Conjunct("Mars", "Jupiter").evaluate(ctx) or C.Conjunct("Mars", "Moon").evaluate(ctx):
            return False
        return any(
            C.InHouseFrom("Mars", origin, h).evaluate(ctx) and mars.sign not in _KUJA_SIGN_EXEMPT[h]
            for origin in ("LAGNA", "MOON", "Venus") for h in _KUJA_HOUSES)


class _SeventhLordInEighthVaidhavya(C.Condition):
    """The 7th LORD cast into the 8th (the spouse's maraka / house of death) AND aggravated
    by a node conjoining it OR Saturn's aspect, with NO full-benefic relief on the 8th ->
    death of the married partner (vaidhavya).

    The 7th-lord-in-8th is Raman's 'early death of partner' placement (HTJAH-II:298-305:
    "In the Eighth House ... Affliction causes the early death of partner"); the node/Saturn
    aggravator makes it DECISIVE. Chart 21 (h7_09): Mars=7th-lord in the 8th with Rahu,
    aspected by exalted Saturn -> the husband drowned 10 months after marriage. Cross-cited
    Phaladeepika 10.2 ("loss of the wife is certain if the 5th/8th lord be in the 7th") and
    10.8 (malefics in the 7th/8th/2nd -> demise of the partner). The 8th-house twin of the
    decisive H7.C.83 (7th-lord-in-12th); GENERALISES the non-decisive H7.C.78 (Rahu+Saturn+
    Mars ALL in the 8th) to the lord-centric form, so it is additive, not a duplicate. The
    full-benefic-on-8th guard is the genuine sowbhagya cancellation (HTJAH-II:961, the same
    relieving set as _SeventhBesiegedByMalefics). bphs-doctrine-reviewer SOUND-WITH-CAVEAT."""

    _RELIEVERS: Final[frozenset[str]] = frozenset({"Jupiter", "Venus", "Mercury"})

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        lord = _lord_of(7, chart)
        p = chart.planets.get(lord)
        if p is None or p.rasi_house != 8:
            return False
        node_conj = any(chart.planets.get(n) is not None and chart.planets[n].rasi_house == 8
                        for n in ("Rahu", "Ketu"))
        sat = chart.planets.get("Saturn")
        sat_afflict = sat is not None and (drishti.aspects_house("Saturn", 8, chart)
                                           or drishti.aspects_planet("Saturn", lord, chart))
        if not (node_conj or sat_afflict):
            return False
        for b in self._RELIEVERS:
            bp = chart.planets.get(b)
            if bp is not None and (bp.rasi_house == 8 or drishti.aspects_house(b, 8, chart)):
                return False
        return True


class _MarsInEighthLordDebilVaidhavya(C.Condition):
    """Mars (the natural maraka / death-aggressor) in the 8th (the spouse's death house) AND
    the 7th lord debilitated-without-cancellation (the mangalya rendered powerless), with no
    full-benefic relief on the 8th -> death of the married partner.

    Chart 22 (h7_10) verbatim: "death of the wife -- debilitated 7th lord with Mars in the
    8th." The Mars-in-8th SIBLING of H7.C.84 (7th-lord-in-8th): here the two factors are the
    maraka Mars occupying the death-house and the debilitated 7th lord, rather than the lord
    itself cast into the 8th. This PROMOTES the Mars-in-8th sub-case of the existing non-
    decisive H7.C.67 (Mars in 2/4/8/12 -> partner death, HTJAH-II:929-931) to DECISIVE, gated
    on the powerless mangalya (debilitated 7th lord) -- bare Mars-in-8th alone is one testimony
    among the pillars and must NOT be decisive (it would over-fire). The debilitation is
    bhanga-gated (a cancelled debility / parivartana = the lord is not truly powerless, so no
    decisive vaidhavya -- Chart 22's narrative explicitly notes "no neechabhanga"). cite
    HTJAH-II:929-931 (rule 67) + 955-960 (rule 75, malefic-in-8th); Phaladeepika 10.8/10.15.
    bphs-doctrine-reviewer SOUND-WITH-CAVEAT (HIGH); LAGNA-framed so it cannot fire on the
    neighbouring Chart 25's from-Moon Mars-in-8th."""

    _RELIEVERS: Final[frozenset[str]] = frozenset({"Jupiter", "Venus", "Mercury"})

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        mars = chart.planets.get("Mars")
        if mars is None or mars.rasi_house != 8:
            return False
        lord = _lord_of(7, chart)
        if dignity(lord, chart) != "debil" or neecha_bhanga(lord, chart):
            return False
        for b in self._RELIEVERS:
            bp = chart.planets.get(b)
            if bp is not None and (bp.rasi_house == 8 or drishti.aspects_house(b, 8, chart)):
                return False
        return True


class _SeventhLordAfflictedVitiatesSpouse(C.Condition):
    """The 7th LORD heavily afflicted -> the spouse/marriage CHARACTER is vitiated (an immoral,
    unfaithful or dissolute partner / disharmony). Two affliction modes:
      (a) the 7th lord CONJOINS a node (Rahu/Ketu) AND is aspected by >= 1 natural malefic, OR
      (b) the 7th lord is hemmed by PAPAKARTARI (a natural malefic flanking it on both sides).

    Raman reads a heavily-afflicted 7th lord as a vitiated spouse: Chart 14/h7_02 "the 7th lords
    are afflicted by Rahu ... makes him immoral" (HTJAH-II:1773); Chart 17/h7_05 "the papakartari
    yoga of the 7th lord Mars resulted in disharmony ... the wife left the husband" (HTJAH-II:1906);
    Chart 27/h7_15 "both the lord of the 7th and Venus have been much afflicted ... a profligate"
    (HTJAH-II:2528). Branch (a) promotes the existing descriptive H7.C.14 (7th-lord/Venus +
    node + malefic aspect -> adultery, HTJAH-II:447-449) to evaluable; branch (b) mirrors H7.C.80
    (papakartari on the 7th lord -> loss of spouse, HTJAH-II:974). `spouse` is bidirectional, so
    this is flagged decisive to carry the verdict past the engine's favourable preponderance (the
    7th-lord Shadbala pillar reads strong despite the nodal/papakartari taint).

    GUARDS (bphs-doctrine-reviewer SOUND-WITH-CAVEAT): (i) the 7th lord must NOT be DEBILITATED --
    a debilitated lord routes to the milder unconventional-marriage reading (mixed), NOT
    character-vitiation; this excludes the over-harsh inter-faith trio, esp. h7_19 (debil Mars,
    "married outside caste" = mixed). (ii) NO BLEMISHLESS full benefic (Jupiter/Venus/Mercury;
    good dignity, not combust/papakartari/node-touched) conjoins or aspects the 7th lord -- a
    genuine reliever cancels the vitiation (mirrors the H7.C.84/85 relief guard). The confirmed
    mixed twin h7_06 (clean 7th lord) and the aspect-only h7_14 are spared by the affliction gate;
    h7_15's Venus touches the lord but is node-conjunct (not blemishless), so guard (ii) is safe."""

    _FULL_BENEFICS: Final[frozenset[str]] = frozenset({"Jupiter", "Venus", "Mercury"})

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        lord = _lord_of(7, chart)
        p = chart.planets.get(lord)
        if p is None or dignity(lord, chart) == "debil":            # guard (i): not debilitated
            return False
        if not self._afflicted(ctx, chart, lord, p):
            return False
        return not self._blemishless_benefic_on_lord(ctx, chart, lord, p)   # guard (ii)

    def _afflicted(self, ctx: C.EvalContext, chart: RamanChart, lord: str, p) -> bool:
        if C.HemmedBy(lord, "malefic").evaluate(ctx):                # (b) papakartari
            return True
        node_conj = any(chart.planets.get(n) is not None            # (a) node-conjunction ...
                        and chart.planets[n].rasi_house == p.rasi_house
                        for n in ("Rahu", "Ketu"))
        return node_conj and any(                                   # ... + a malefic aspect
            m in chart.planets and drishti.aspects_planet(m, lord, chart)
            for m in NATURAL_MALEFICS if m != lord)

    def _blemishless_benefic_on_lord(self, ctx: C.EvalContext, chart: RamanChart, lord: str, p) -> bool:
        for b in self._FULL_BENEFICS:
            if b == lord or b not in chart.planets:
                continue
            bp = chart.planets[b]
            if not (bp.rasi_house == p.rasi_house or drishti.aspects_planet(b, lord, chart)):
                continue
            if dignity(b, chart) in ("debil", "enemy") or getattr(bp, "combust_fraction", 0) > 0:
                continue
            if C.HemmedBy(b, "malefic").evaluate(ctx):
                continue
            if any(chart.planets.get(n) is not None and chart.planets[n].rasi_house == bp.rasi_house
                   for n in ("Rahu", "Ketu")):
                continue
            return True   # a blemishless full benefic relieves the lord
        return False


# ── RULES ─────────────────────────────────────────────────────────────────────

RULES: Final[tuple[RuleRecord, ...]] = (
    # ===== A. Marriage happiness (HTJAH-II:353-372) — sig marital_happiness =====
    RuleRecord(
        id="H7.C.1", house=7, signification="marital_happiness", group="combination",
        kind="evaluable", condition=C.CountInHouse(7, 1, "benefic"),
        fortified="benefics influencing the 7th (from Lagna or Moon) → a happy marriage and a "
                  "loving, fortunate wife",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 353)),
    RuleRecord(
        id="H7.C.4", house=7, signification="marital_happiness", group="combination",
        kind="evaluable",
        condition=C.And(C.InRashiHouse("Mars", 7), C.InRashiHouse("Saturn", 7),
                        _SeventhSignIn(frozenset({10}))),
        fortified="Mars and Saturn in the 7th in Capricorn → a chaste, beautiful, lucky wife",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 361)),
    RuleRecord(
        id="H7.C.6", house=7, signification="marital_happiness", group="combination",
        kind="evaluable", condition=C.InRashiHouse("Jupiter", 7),
        fortified="Jupiter in the 7th → the native is devoted to his wife",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 367)),
    RuleRecord(
        id="H7.C.7", house=7, signification="marital_happiness", group="combination",
        kind="evaluable", condition=C.HasDignity("Venus", {"exalt", "own", "moolatrikona"}),
        fortified="Venus exalted or in own sign (or Gopura/Vaiseshikamsa varga) → a good and "
                  "beautiful wife",
        afflicted=None,
        frame="KARAKA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 368)),
    RuleRecord(
        id="H7.C.5", house=7, signification="marital_happiness", group="combination",
        kind="descriptive", condition=None,
        fortified="7th lord & Venus in even signs, the 7th an even sign, and the 5th & 7th lords "
                  "not combust/weak → good wife and children. TODO(predicate: combust+weak gate)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 364)),
    RuleRecord(
        id="H7.C.8", house=7, signification="marital_happiness", group="combination",
        kind="descriptive", condition=None,
        fortified="a benefic 7th sign, OR Venus-as-7th-lord aspected by a benefic → a devoted, "
                  "charming spouse. TODO(predicate: benefic-sign + karaka-is-lord aspect)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 370)),

    # ===== B. Character / chastity (HTJAH-II:402-475, 979-988) — sig spouse =====
    RuleRecord(
        id="H7.C.9", house=7, signification="spouse", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Moon", 7), _PlanetInSigns("Moon", _MALEFIC_SIGNS)),
        fortified=None,
        afflicted="Moon in the 7th in a malefic sign → a wicked, mean, menial-like wife",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 402)),
    RuleRecord(
        id="H7.C.16", house=7, signification="spouse", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Venus", 7),
                        C.Or(C.Aspects("Saturn", "Venus"), C.Aspects("Mars", "Venus"))),
        fortified=None,
        afflicted="Saturn or Mars aspecting Venus in the 7th → the native indulges in adultery",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 451)),
    RuleRecord(
        id="H7.C.17", house=7, signification="spouse", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Saturn", 7), C.InRashiHouse("Moon", 7),
                        C.InRashiHouse("Mars", 7)),
        fortified=None,
        afflicted="Saturn, Moon and Mars in the 7th → both the native and the wife are immoral",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 452)),
    RuleRecord(
        id="H7.C.18", house=7, signification="spouse", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(2, 7), C.LordIn(7, 7), C.LordIn(10, 7)),
        fortified=None,
        afflicted="the 2nd, 7th and 10th lords together in the 7th → the native is a profligate",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 454)),
    RuleRecord(
        id="H7.C.21", house=7, signification="spouse", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Venus", 7), C.InRashiHouse("Mars", 7),
                        C.InRashiHouse("Moon", 7)),
        fortified=None,
        afflicted="Venus, Mars and the Moon in the 7th → the wife associates with other men with "
                  "the husband's connivance",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 980)),
    RuleRecord(
        id="H7.C.14", house=7, signification="spouse", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="7th lord or Venus conjoined Rahu/Ketu and aspected by a malefic → native or "
                  "wife adulterous (and the Navamsa-of-Saturn/Mars chastity rules, D60 mother-"
                  "adultery cluster). TODO(predicate: lord+node conjunction, Navamsa, D60)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 447)),

    # ===== C. Impotency / eunuch (HTJAH-II:415-445) — sig virility =====
    RuleRecord(
        id="H7.C.24", house=7, signification="virility", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Venus", 7), _AspectedByClass("Venus", "malefic")),
        fortified=None,
        afflicted="a weak, malefic-afflicted Venus in the 7th → wife barren or husband impotent",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 415)),
    RuleRecord(
        id="H7.C.25", house=7, signification="virility", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Mars", 7), C.CountInHouse(7, 2, "malefic")),
        fortified=None,
        afflicted="Mars with another malefic in the 7th → impotency via urinary problems",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 416)),
    RuleRecord(
        id="H7.C.26", house=7, signification="virility", group="combination", kind="evaluable",
        condition=C.And(C.Conjunct("Saturn", "Venus"),
                        C.Or(C.InRashiHouse("Saturn", 10), C.InRashiHouse("Saturn", 8))),
        fortified=None,
        afflicted="Saturn and Venus together in the 10th or 8th (no benefic aspect) → impotent",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 421)),
    RuleRecord(
        id="H7.C.28", house=7, signification="virility", group="combination", kind="evaluable",
        condition=C.And(C.HasDignity("Saturn", {"debil"}),
                        C.Or(C.InRashiHouse("Saturn", 6), C.InRashiHouse("Saturn", 12))),
        fortified=None,
        afflicted="Saturn debilitated in the 6th or 12th → impotent",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 428)),
    RuleRecord(
        id="H7.C.30", house=7, signification="virility", group="combination", kind="evaluable",
        condition=C.And(_PlanetParity("Moon", "even"), _PlanetParity("Mercury", "odd"),
                        C.Aspects("Mars", "Moon"), C.Aspects("Mars", "Mercury")),
        fortified=None,
        afflicted="Moon in an even sign and Mercury in an odd sign, both aspected by Mars → impotent",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 432)),
    RuleRecord(
        id="H7.C.32", house=7, signification="virility", group="combination", kind="evaluable",
        condition=C.And(_PlanetParity("Mars", "even"), _LagnaParity("odd")),
        fortified=None,
        afflicted="Mars in an even sign and the Lagna an odd sign → impotent",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 438)),
    RuleRecord(
        id="H7.C.34", house=7, signification="virility", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(7, 6), C.InRashiHouse("Venus", 6)),
        fortified=None,
        afflicted="the 7th lord and Venus together in the 6th house → impotent",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 445)),
    RuleRecord(
        id="H7.C.31", house=7, signification="virility", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="Lagna, Venus and Moon in odd Navamsas (rec.31); or the Sun-Moon / Mars-Sun / "
                  "Saturn-Mercury odd/even mutually-aspecting pairs (rec.33) → impotent. "
                  "TODO(predicate: Navamsa parity, paired mutual-aspect parity)",
        frame="LAGNA", varga="D9", polarity="malefic", source=Citation("HTJAH-II", 435)),

    # ===== D. Number of marriages (HTJAH-II:477-510) — sig spouse =====
    RuleRecord(
        id="H7.C.38", house=7, signification="spouse", group="combination", kind="evaluable",
        condition=C.And(_PlanetInSigns("Venus", _COMMON_SIGNS),
                        _SeventhSignIn(_COMMON_SIGNS)),
        fortified=None,
        afflicted="the 7th sign (and Venus) in common (dual) signs → marries at least twice "
                  "(the strongest dual-sign remarriage signature; the 7th-lord-in-dual-Navamsa "
                  "refinement is kept in text)",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 484)),
    RuleRecord(
        id="H7.C.39", house=7, signification="spouse", group="combination", kind="evaluable",
        condition=C.And(C.Or(C.InRashiHouse("Mercury", 7), C.InRashiHouse("Saturn", 7)),
                        C.CountInHouse(11, 2)),
        fortified=None,
        afflicted="Mercury or Saturn in the 7th with two planets in the 11th → two wives",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 485)),
    RuleRecord(
        id="H7.C.40", house=7, signification="spouse", group="combination", kind="evaluable",
        condition=C.And(_LordIsPlanet(7, "Saturn"), _ConjunctAnyMalefic("Saturn")),
        fortified=None,
        afflicted="the 7th lord is Saturn conjoined a malefic → many wives",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 487)),
    RuleRecord(
        id="H7.C.41", house=7, signification="spouse", group="combination", kind="evaluable",
        condition=C.CountInHouse(7, 3, "malefic"),
        fortified=None,
        afflicted="three or more malefics in the 7th → two wives or more (one of several "
                  "rec.41 disjuncts; the Venus-eclipsed / 8th-lord-in-1st-or-7th branches are "
                  "kept in text)",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 488)),
    RuleRecord(
        id="H7.C.35", house=7, signification="spouse", group="combination", kind="descriptive",
        condition=None,
        fortified="2nd & 7th lords in depression with benefics in kendras/trikonas → only ONE "
                  "marriage; Jupiter & Mercury in Sun/Mars Navamsas, or Mercury-in-7th-in-Jupiter-"
                  "Navamsa → marries once. TODO(predicate: multi-lord-depression, Navamsa lordship)",
        afflicted=None,
        frame="LAGNA", varga="D9", polarity="benefic", source=Citation("HTJAH-II", 477)),

    # ===== E. Loss / death of partner & widowhood (HTJAH-II:374-977) — sig coverture =====
    # (rec.45 — "malefics in 4/8/12 from Venus OR Venus hemmed → wife dies soon",
    #  HTJAH-II:374 — is encoded as a single two-branch rule in from_karaka.H7.K.2,
    #  which owns both branches; not duplicated here to avoid double-counting.)
    RuleRecord(
        id="H7.C.46", house=7, signification="coverture", group="combination", kind="evaluable",
        condition=C.And(_LagnaInSigns(frozenset({2})), C.InRashiHouse("Venus", 7)),
        fortified=None,
        afflicted="Venus in the 7th for a Taurus Ascendant → threatens death to the wife",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 377)),
    RuleRecord(
        id="H7.C.48", house=7, signification="coverture", group="combination", kind="evaluable",
        condition=C.And(C.CountInHouse(2, 1, "malefic"), C.CountInHouse(7, 1, "malefic")),
        fortified=None,
        afflicted="the 2nd and 7th occupied by malefics → loss of wife or husband",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 384)),
    RuleRecord(
        id="H7.C.49", house=7, signification="coverture", group="combination", kind="evaluable",
        condition=C.Or(C.LordIn(5, 7), C.LordIn(8, 7)),
        fortified=None,
        afflicted="the 5th or 8th lord in the 7th → death of wife or husband",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 386)),
    RuleRecord(
        id="H7.C.52", house=7, signification="spouse", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Moon", 7), C.InRashiHouse("Saturn", 7)),
        fortified=None,
        afflicted="Moon and Saturn in the 7th → (woman's chart) remarriage; (man's chart) denies "
                  "marriage/progeny [native-sex split kept in text]. Routed to `spouse` (a "
                  "marriage-count/denial matter), not coverture (partner-death)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 392)),
    RuleRecord(
        id="H7.C.53", house=7, signification="coverture", group="combination", kind="evaluable",
        condition=C.And(C.CountInHouse(2, 1, "malefic"), C.CountInHouse(7, 1, "malefic"),
                        C.CountInHouse(8, 1, "malefic")),
        fortified=None,
        afflicted="malefics in the 2nd, 7th and 8th from Lagna → demise of the married partner",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 394)),
    RuleRecord(
        id="H7.C.55", house=7, signification="coverture", group="combination", kind="evaluable",
        condition=C.Or(C.And(C.InRashiHouse("Mercury", 7), C.InSign("Mercury", 2)),
                       C.And(C.InRashiHouse("Jupiter", 7), C.InSign("Jupiter", 10)),
                       C.And(C.InRashiHouse("Saturn", 7), C.InRashiHouse("Mars", 7),
                             C.InSign("Saturn", 12))),
        fortified=None,
        afflicted="Mercury-in-7th-in-Taurus, OR Jupiter-in-7th-in-Capricorn, OR Saturn & Mars "
                  "in-7th-in-Pisces → injurious to the partner's life",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 398)),
    RuleRecord(
        id="H7.C.56", house=7, signification="coverture", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Saturn", 7), C.InRashiHouse("Mercury", 7)),
        fortified=None,
        afflicted="Saturn and Mercury in the 7th → widow/widower for the life-partner",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 401)),
    RuleRecord(
        id="H7.C.59", house=7, signification="coverture", group="combination", kind="evaluable",
        condition=C.And(_LagnaInSigns(frozenset({6})), C.InSign("Sun", 6),
                        C.InRashiHouse("Saturn", 7)),
        fortified=None,
        afflicted="Sun in Virgo (= Ascendant) and Saturn in the 7th → the wife will die",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 911)),
    RuleRecord(
        id="H7.C.60", house=7, signification="coverture", group="combination", kind="evaluable",
        condition=C.InRashiHouse("Mars", 7),
        fortified=None,
        afflicted="Mars in the 7th → the wife will die (the core Mangal-dosha 7th placement)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 913)),
    RuleRecord(
        id="H7.C.65", house=7, signification="coverture", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Venus", 7), C.InRashiHouse("Mars", 7)),
        fortified=None,
        afflicted="Venus and Mars conjoining in the 7th → the native is bereft of his wife",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 925)),
    RuleRecord(
        id="H7.C.67", house=7, signification="coverture", group="combination", kind="evaluable",
        condition=C.Or(C.InRashiHouse("Mars", 2), C.InRashiHouse("Mars", 4),
                       C.InRashiHouse("Mars", 8), C.InRashiHouse("Mars", 12)),
        fortified=None,
        afflicted="Mars in the 2nd, 12th, 4th or 8th → the native loses his married partner by "
                  "death (the rasi-from-Lagna Mangal affliction; the 7th-house leg is owned by "
                  "H7.C.60 to avoid double-counting Mars-in-7th in coverture)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 929)),
    RuleRecord(
        id="H7.C.74", house=7, signification="coverture", group="combination", kind="evaluable",
        condition=C.And(_SeventhSignIn(_MALEFIC_SIGNS), C.InRashiHouse("Saturn", 7)),
        fortified=None,
        afflicted="a malefic 7th sign occupied by Saturn → widowed",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 954)),
    RuleRecord(
        id="H7.C.77", house=7, signification="coverture", group="combination", kind="evaluable",
        condition=C.And(C.Or(C.CountInHouse(7, 1, "malefic"), C.CountInHouse(8, 1, "malefic")),
                        C.CountInHouse(9, 1, "benefic")),
        fortified="malefics in the 7th/8th but benefics in the 9th → a long, happy life with the "
                  "husband (the 9th-house sowbhagya rescue)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 961)),
    RuleRecord(
        id="H7.C.78", house=7, signification="coverture", group="combination", kind="evaluable",
        condition=C.Or(C.And(C.InRashiHouse("Rahu", 7), C.InRashiHouse("Saturn", 7),
                             C.InRashiHouse("Mars", 7)),
                       C.And(C.InRashiHouse("Rahu", 8), C.InRashiHouse("Saturn", 8),
                             C.InRashiHouse("Mars", 8))),
        fortified=None,
        afflicted="Rahu conjoining Saturn and Mars in the 7th or 8th → early widowhood",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 966)),
    RuleRecord(
        id="H7.C.80", house=7, signification="coverture", group="combination", kind="evaluable",
        condition=_HouseHemmedBy(7, "malefic"),
        fortified=None,
        afflicted="the 7th house under papakartari (hemmed by malefics), no benefic influence → "
                  "loss of husband",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 974)),
    RuleRecord(
        id="H7.C.54", house=7, signification="wealth_through_marriage", group="combination",
        kind="evaluable", condition=C.And(C.InRashiHouse("Sun", 7), C.InRashiHouse("Rahu", 7)),
        fortified=None,
        afflicted="Sun and Rahu in the 7th → loss of wealth through women",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 395)),

    # ===== Kuja-Dosha (single-chart, HTJAH-II:2579-2632) — sig marital_happiness =====
    RuleRecord(
        id="H7.KD.1", house=7, signification="marital_happiness", group="combination",
        kind="evaluable", condition=_KujaDosha(),
        fortified=None,
        afflicted="Kuja/Mangal Dosha — Mars in the 2/4/7/8/12 from the Lagna, the Moon or Venus "
                  "(not neutralised by a Mars+Jupiter or Mars+Moon conjunction) → affliction to "
                  "marriage and the partner. Bhava-frame + per-sign exceptions (7th exempt in "
                  "Cn/Cp, Le/Aq wholly exempt) kept in text; two-chart matching grid is v1-OOS",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 2579)),

    # ===== F. Timing of marriage (HTJAH-II:847-883) — Dasa activation → descriptive =====
    RuleRecord(
        id="H7.C.81", house=7, signification="spouse", group="combination", kind="descriptive",
        condition=None,
        fortified="marriage is timed by the strongest of: the dispositor of the sign/Navamsa held "
                  "by the 7th lord, Venus, the Moon, the 2nd lord, the 9th/10th lords, a planet "
                  "with/occupying the 7th; transiting Jupiter over (Lagna-lord+7th-lord longitude) "
                  "is secondary. TODO(predicate: Dasa selection — Phase-F)",
        afflicted="Saturn aspecting the 7th, 7th lord and Venus, or a 6/8/12 lord touching them → "
                  "delays/denies early marriage",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 852)),

    # ===== G. Separation / deprivation of marital happiness — sig marital_happiness =====
    # DECISIVE: TWO OR MORE malefics afflict the 7th (occupy or aspect) with NO full-benefic
    # (Jupiter/Venus/Mercury) relieving it -> estrangement / loss of marital happiness.
    # Flagged in _DECISIVE_AFFLICTION_RULE_IDS so it carries the marital_happiness verdict
    # past the benefic-starved bucket's strong-pillar preponderance (the bucket otherwise
    # holds 6 benefics vs only Kuja-Dosha + a from-Venus malefic). Generalised from the
    # specific Saturn+Mars case (HTJAH-II:562) to "the 7th besieged by malefics" — fires on
    # chart_04 (Saturn+Mars, "complete deprivation; separated 1974") AND chart_05 (Mars-aspect
    # + Ketu-occupy, "violent clashes, miserable"); the full-benefic guard spares favourable
    # chart_02 (4 malefics touch its 7th but Jupiter aspects it too) and leaves chart_03/08
    # (1 malefic each) for the maraka-leak fix to rescue.
    RuleRecord(
        id="H7.C.82", house=7, signification="marital_happiness", group="combination",
        kind="evaluable", condition=_SeventhBesiegedByMalefics(),
        fortified=None,
        afflicted="two or more malefics afflicting the 7th (occupation or aspect) with no "
                  "full benefic relieving it -> estrangement and loss of marital happiness; "
                  "separation should be predicted",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 996)),
    # DECISIVE: the 7th LORD in the 12th (the house of loss) AND a malefic afflicting the 7th
    # -> loss / separation in marriage. The lord of marriage cast into the 12th is the
    # classic loss signature; the cumulative malefic-on-7th conjunct keeps it from firing on
    # a 7th-lord-in-12 chart whose 7th is otherwise clean (per the C.37 reviewer pattern, and
    # matching HTJAH-II:834 "[7th lord] is in the 12th house and the karaka is also very weak,
    # marital [happiness suffers]"). Flagged decisive (the marital_happiness bucket is
    # benefic-starved). Fires on chart_06 (Mercury=7th-lord in 12th, Mars aspects the 7th —
    # "two marriages, both unhappy") and chart_09 (Mars=7th-lord in 12th, Saturn in the 7th —
    # "separated 1964"); no favourable H7 golden has the 7th lord in the 12th.
    RuleRecord(
        id="H7.C.83", house=7, signification="marital_happiness", group="combination",
        kind="evaluable",
        condition=C.And(C.LordIn(7, 12), _MaleficOccupiesOrAspects7th()),
        fortified=None,
        afflicted="the 7th lord cast into the 12th (house of loss) with a malefic also "
                  "afflicting the 7th -> loss and separation in marriage; marital happiness "
                  "is denied",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 834)),
    # DECISIVE (coverture): the 7th LORD cast into the 8th (the spouse's maraka / house of
    # death) aggravated by a node conjoining it OR Saturn's aspect, no full-benefic relief on
    # the 8th -> death of the married partner (vaidhavya). The 8th-house twin of H7.C.83;
    # generalises the non-decisive H7.C.78 (Rahu+Saturn+Mars all in the 8th) to the lord-
    # centric form. Fires on chart_21/h7_09 (Mars=7th-lord in 8th with Rahu, Saturn aspect ->
    # husband drowned); only h7_09 has the 7th lord in the 8th across the coverture goldens.
    # bphs-doctrine-reviewer SOUND-WITH-CAVEAT/FLAG (HIGH); cross-cited Phaladeepika 10.2/10.8.
    RuleRecord(
        id="H7.C.84", house=7, signification="coverture", group="combination",
        kind="evaluable", condition=_SeventhLordInEighthVaidhavya(),
        fortified=None,
        afflicted="the 7th lord cast into the 8th (the spouse's maraka / house of death) and "
                  "further afflicted by a node conjoining it or Saturn's aspect, with no full-"
                  "benefic relief on the 8th -> death of the married partner; vaidhavya should "
                  "be predicted",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 300)),
    # DECISIVE (coverture): Mars (the natural maraka) in the 8th (the spouse's death house)
    # AND the 7th lord debilitated-without-cancellation (mangalya powerless), no full-benefic
    # relief on the 8th -> death of the married partner. The Mars-in-8th SIBLING of H7.C.84;
    # PROMOTES the Mars-in-8th sub-case of the non-decisive H7.C.67 (HTJAH-II:929) to decisive,
    # gated on the debilitated lord (bare Mars-in-8th must NOT be decisive -> over-fires).
    # Chart_22/h7_10 verbatim: "death of the wife -- debilitated 7th lord with Mars in the 8th."
    # Only h7_10 has Mars-in-8th + debilitated-7th-lord across the H7 goldens; LAGNA-framed +
    # bhanga-gated. bphs-doctrine-reviewer SOUND-WITH-CAVEAT (HIGH); cross-cited Phaladeepika 10.8/10.15.
    RuleRecord(
        id="H7.C.85", house=7, signification="coverture", group="combination",
        kind="evaluable", condition=_MarsInEighthLordDebilVaidhavya(),
        fortified=None,
        afflicted="Mars (the maraka) in the 8th (the spouse's death house) with the 7th lord "
                  "debilitated (mangalya powerless) and no full-benefic relief on the 8th -> "
                  "death of the married partner; vaidhavya should be predicted",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 929)),
    # DECISIVE (spouse): a heavily-afflicted 7th lord (conjunct a node AND malefic-aspected, OR
    # hemmed by papakartari) -> a vitiated spouse / disharmonious marriage. The engine read these
    # FAVOURABLE because the 7th-lord Shadbala pillar reads strong despite the nodal/papakartari
    # taint; the decisive flag carries the verdict past that preponderance. Fixes the three
    # HIGH-confidence reversals h7_02 (lord+Rahu, immoral), h7_05 (lord papakartari, wife left),
    # h7_15 (lord+Venus much afflicted, profligate). cite HTJAH-II:1773 (+ h7_05 leg :1906, h7_15
    # leg :2528). The node-AND-aspect / papakartari gate spares the clean-lord twins (h7_06, h7_14).
    RuleRecord(
        id="H7.C.86", house=7, signification="spouse", group="combination", kind="evaluable",
        condition=_SeventhLordAfflictedVitiatesSpouse(),
        fortified=None,
        afflicted="the 7th lord heavily afflicted (conjunct a node and malefic-aspected, or "
                  "hemmed by papakartari) → a vitiated spouse / disharmonious marriage",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 1773)),
)
