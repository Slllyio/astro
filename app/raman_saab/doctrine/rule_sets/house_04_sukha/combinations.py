"""House 4 (Sukha — mother / home / vehicles / lands / happiness) — "Important
Combinations".

Encodes the combination rule-atoms of the "Important Combinations" tables in
``docs/raman_saab/methodology/house_04_sukha.md`` (HTJAH-I:4206-4953).

Encoding policy (honest, atom by atom — mirrors H2/H3/H7/H8/H10):

* Existing predicates compose directly. Combos route to the FINE significations
  (mother / happiness / education / vehicles / property) — each H4 sig's rule_tags
  was extended to ("<key>","mother_home") so it aggregates the shared placements
  AND its own combos (the H1/H7 aggregate-bridge pattern).
* H4 mother-death rules are NOT longevity-guarded (the guard keys on
  rule_tags∋"longevity" / key=="death"; the `mother` sig tags mother_home), so they
  are measurable once mother goldens exist.
* Rules needing predicates not yet in the algebra — planet strength/weak/"extremely
  strong" gates, Gopuramsa / shashtiamsa / thrimsamsa varga ranks, lord-friendship
  relations, the derived-Lagna "4th as mother's Lagna" technique, and lords-
  associated-in-a-named-house — go in as ``kind="descriptive"`` with a
  ``TODO(predicate)`` note.
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


def _lord_of(house: int, chart: RamanChart) -> str:
    return SIGN_LORDS[((chart.asc_sign - 1) + (house - 1)) % 12 + 1]


# ── local leaf predicates ─────────────────────────────────────────────────────

class _AspectedByClass(C.Condition):
    """A natural planet of `klass` (other than `target`) casts a drishti on `target`."""
    def __init__(self, target: str, klass: str) -> None:
        self.target, self.klass = target, klass

    def evaluate(self, ctx: C.EvalContext) -> bool:
        if self.target not in ctx.chart.planets:
            return False
        group = NATURAL_MALEFICS if self.klass == "malefic" else NATURAL_BENEFICS
        return any(name != self.target and name in group
                   and drishti.aspects_planet(name, self.target, ctx.chart)
                   for name in ctx.chart.planets)


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


class _HouseHemmedBy(C.Condition):
    """Papakartari/Subhakartari on a HOUSE: the house-before and house-after `house`
    both hold a planet of `klass`."""
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


class _PlanetInOrAspectsHouse(C.Condition):
    """`planet` occupies OR casts a whole-sign drishti on whole-sign `house`."""
    def __init__(self, planet: str, house: int) -> None:
        self.planet, self.house = planet, house

    def evaluate(self, ctx: C.EvalContext) -> bool:
        p = ctx.chart.planets.get(self.planet)
        if p is None:
            return False
        return p.rasi_house == self.house or drishti.aspects_house(self.planet, self.house, ctx.chart)


class _FourthLordConjunctMoon(C.Condition):
    """The 4th lord shares a whole-sign house with the Moon (identity → False: when the Moon
    itself lords the 4th, 'conjunct the Moon' is not a configuration)."""
    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lord_of(4, ctx.chart)
        if lord == "Moon":
            return False
        p, moon = ctx.chart.planets.get(lord), ctx.chart.planets.get("Moon")
        return p is not None and moon is not None and p.rasi_house == moon.rasi_house


class _LagnaAndFourthLordsFriendly(C.Condition):
    """Lagna-lord and 4th-lord are mutual friends AND both are beneficially disposed —
    Raman's "He wins the affection of mother if lord of Lagna and the fourth are friendly,
    and are otherwise beneficially disposed" (HTJAH-I:4228-4229).

    "Friendly" reads `dignity.compound_relation` in BOTH directions (his word is mutual).
    "Otherwise beneficially disposed" is read as the conservative pair the corpus uses
    elsewhere: neither lord carries a natural-malefic contact (conjunction or drishti).
    Identity (one planet lording both) returns False: a planet is not "friendly with"
    itself, and Raman's sentence is about two significators agreeing."""
    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.primitives.dignity import compound_relation
        chart = ctx.chart
        l1, l4 = _lord_of(1, chart), _lord_of(4, chart)
        if l1 == l4 or l1 not in chart.planets or l4 not in chart.planets:
            return False
        if compound_relation(l1, l4, chart) != "friend":
            return False
        if compound_relation(l4, l1, chart) != "friend":
            return False
        for lord in (l1, l4):
            for m in NATURAL_MALEFICS:
                if m == lord or m not in chart.planets:
                    continue
                if (chart.planets[m].rasi_house == chart.planets[lord].rasi_house
                        or drishti.aspects_planet(m, lord, chart)):
                    return False
        return True


class _FourthLordNeechaWithSun(C.Condition):
    """The 4th lord is debilitated AND shares a house with the Sun — Raman's "The person
    loses lands by royal or Government orders if the lord of the fourth is neecha with Sun"
    (HTJAH-I:4219-4220). Both legs are his; the Sun's presence is what makes the loss
    ROYAL/governmental, which is why this is scoped to `property` and not to happiness."""
    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.primitives.dignity import dignity as _dig
        chart = ctx.chart
        l4 = _lord_of(4, chart)
        p = chart.planets.get(l4)
        sun = chart.planets.get("Sun")
        if p is None or sun is None or l4 == "Sun":
            return False
        return _dig(l4, chart) == "debil" and p.rasi_house == sun.rasi_house


class _FourthHouseHemmedByMalefics(C.Condition):
    """H4.C.49: a natural malefic in each sign adjacent to the 4th sign (papakartari on the
    bhava). Sign-level hemming, same form as H9.A.21's leg."""
    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        s4 = ((chart.asc_sign - 1 + 3) % 12) + 1
        prev_s = ((s4 - 2) % 12) + 1
        next_s = (s4 % 12) + 1
        malefics = ("Sun", "Mars", "Saturn", "Rahu", "Ketu")
        hem_prev = any(chart.planets[m].sign == prev_s for m in malefics if m in chart.planets)
        hem_next = any(chart.planets[m].sign == next_s for m in malefics if m in chart.planets)
        return hem_prev and hem_next


class _JupiterAspectsFourthLord(C.Condition):
    """H4.C.50: the Gnanakaraka Jupiter casts whole-sign drishti on the 4th lord (identity
    excluded — when Jupiter lords the 4th, 'aspects the lord' is not a configuration)."""
    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lord_of(4, ctx.chart)
        if lord == "Jupiter":
            return False
        return drishti.aspects_planet("Jupiter", lord, ctx.chart)


class _MoonInLagnaVargottama(C.Condition):
    """H4.C.51: the Matru-Karaka Moon occupies the Lagna AND is Vargottama. Needs a degree
    (vargottama is a navamsa fact); sign-midpoint materializations evaluate honestly off
    their derived navamsa, and Shaw's chart is fresh-cast."""
    def evaluate(self, ctx: C.EvalContext) -> bool:
        moon = ctx.chart.planets.get("Moon")
        return moon is not None and moon.rasi_house == 1 and moon.vargottama


class _MatruKarakaDoublyAfflicted(C.Condition):
    """>= 2 of the first-rate malefics {Mars, Saturn, Rahu, Ketu} contact the Matru-Karaka
    Moon — conjunction (same sign) or whole-sign drishti (nodes 7th-only via the drishti
    module). H4.C.48's predicate, the exact H4 twin of H5.C.40's _PutraKarakaDoublyAfflicted;
    the Sun's exclusion is the same empirical documented limit (see the rule's comment)."""
    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        moon = chart.planets.get("Moon")
        if moon is None:
            return False
        count = 0
        for name in ("Mars", "Saturn", "Rahu", "Ketu"):
            p = chart.planets.get(name)
            if p is None:
                continue
            if p.sign == moon.sign or drishti.aspects_planet(name, "Moon", chart):
                count += 1
        return count >= 2


class _LagnaInSignsLocal(C.Condition):
    """The ascendant sign is one of `signs` (1..12)."""
    def __init__(self, signs: frozenset[int]) -> None:
        self.signs = signs

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return ctx.chart.asc_sign in self.signs


# ── RULES ─────────────────────────────────────────────────────────────────────

RULES: Final[tuple[RuleRecord, ...]] = (
    # ===== A. General / property / happiness (HTJAH-I:4206-4232) =====
    RuleRecord(
        id="H4.C.1", house=4, signification="mother", group="combination", kind="evaluable",
        condition=C.Or(C.LordIn(4, 6), C.LordIn(4, 8), C.LordIn(4, 12)),
        fortified=None,
        afflicted="4th lord in the 6th/8th/12th (no beneficial aspect) → early death of the mother",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4206)),
    RuleRecord(
        id="H4.C.2", house=4, signification="property", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(4, 1), C.InRashiHouse("Venus", 4)),
        fortified="4th lord in the Lagna with Venus strongly in the 4th → vehicles, jewels, wealth",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4207)),
    # H4.C.3 is DESCRIPTIVE (de-dup, 2026-06-25): EVERY arm of its Or — LordIn(4,6/8/12)
    # and Mars/Saturn-in-4 — is a placement already scored into the `property` verdict by the
    # mother_home BRIDGE rules (H4.L.6/8/12 in lord_in_12.py, H4.P.Mars/H4.P.Saturn in
    # planets_in_4th.py; the `property` sig aggregates property+mother_home, significations.py).
    # Keeping it evaluable double-counted one placement in the property preponderance, violating
    # the H7 policy "no rule re-scores a placement already fired within the SAME signification".
    # Made descriptive (citation preserved) per that policy and the H4.C.30 precedent; the
    # property-loss testimony survives via the bridge. Zero golden regression — the double-count
    # was inert (DOCTRINE_BACKLOG B6-adjacent, measured 2026-06-25).
    RuleRecord(
        id="H4.C.3", house=4, signification="property", group="combination", kind="descriptive",
        condition=C.Or(C.LordIn(4, 6), C.LordIn(4, 8), C.LordIn(4, 12),
                       C.InRashiHouse("Mars", 4), C.InRashiHouse("Saturn", 4)),
        fortified=None,
        afflicted="4th lord in a dusthana, or Mars/Saturn occupying the 4th → loses property "
                  "and wealth (scored via the mother_home bridge placements H4.L.6/8/12 + "
                  "H4.P.Mars/Saturn; kept descriptive to avoid double-counting in `property`)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4208)),
    RuleRecord(
        id="H4.C.5", house=4, signification="happiness", group="combination", kind="evaluable",
        condition=_HouseHemmedBy(4, "malefic"),
        fortified=None,
        afflicted="the 4th house under papakartari (hemmed by malefics) → associates with bad people",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4211)),
    RuleRecord(
        id="H4.C.7", house=4, signification="property", group="combination", kind="evaluable",
        condition=C.Or(C.LordIn(4, 1), C.LordIn(4, 7)),
        fortified="4th lord in the Lagna or the 7th → gets a house without difficulty",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4213)),
    RuleRecord(
        id="H4.C.9", house=4, signification="property", group="combination", kind="evaluable",
        condition=C.Parivartana(4, 10),
        fortified="parivartana (interchange) between the 4th and 10th lords → gets lands",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4215)),
    RuleRecord(
        id="H4.C.11", house=4, signification="property", group="combination", kind="evaluable",
        condition=C.Parivartana(4, 6),
        fortified="parivartana between the 4th and 6th lords → gets lands from enemies, by right",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4217)),
    RuleRecord(
        id="H4.C.17", house=4, signification="happiness", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Sun", 4), C.InRashiHouse("Mars", 4)),
        fortified=None,
        afflicted="Sun and Mars in the 4th → wounds from stones",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4223)),
    RuleRecord(
        id="H4.C.18", house=4, signification="mother", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Moon", 4), _AspectedByClass("Moon", "malefic")),
        fortified=None,
        afflicted="Moon in the 4th ASPECTED by an evil planet → injurious to the mother (the "
                  "aspect arm of HTJAH-I:4224; the stronger JOINED/conjunct arm is the decisive "
                  "H4.C.18a, so this arm stays non-decisive to avoid double-counting)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4224)),
    # DECISIVE (mother): the Moon (Matru-Karaka) in the 4th CONJOINED by a natural malefic ->
    # kills the mother early. The conjunct (JOINED) arm of HTJAH-I:4224 ("Moon in the 4th joined
    # ... by evil planets -> kills the mother early"), corroborated by Chart 64/h4_01 (Saturn
    # conjunct an EXALTED Moon -> "the Matru-Karaka is definitely afflicted; early death of the
    # mother", HTJAH-I:4404) and Chart 66 (Saturn+Moon-in-4 -> mother death, HTJAH-I:4488). The
    # H4 twin of the decisive karaka-affliction rules H9.A.20a / H5.C.38; `mother` is bidirectional
    # (not AFFLICTION_MATTER), so the decisive flag is the lever past the (exalted-Moon) strong-
    # pillar favourable preponderance -- EXALTATION is not a relief. Only the CONJUNCT arm is
    # decisive; a lone distant aspect (the C.18 arm) stays non-decisive (no worked chart supports
    # a decisive mother-death on aspect alone). Fires on h4_01 across the H4/mother goldens.
    # bphs-doctrine-reviewer SOUND-WITH-CAVEAT (doctrine HIGH; n=2 worked charts 64/66).
    RuleRecord(
        id="H4.C.18a", house=4, signification="mother", group="combination", kind="evaluable",
        # DECISIVE early-death of the mother requires a CRUEL (non-nodal) malefic conjoining
        # the Matru-Karaka Moon — Mars or Saturn, the fatality signature. Raman's worked
        # instance is Saturn+Moon-in-4th (Chart 64/h4_01, HTJAH-I:4404 "the Matru-Karaka is
        # definitely afflicted; early death of mother"). A NODAL conjunction (Rahu/Ketu-Moon)
        # is a Grahana/eclipse affliction of the mother's HEALTH/mind, not the decisive
        # longevity-kill — it is still scored as ordinary malefic pressure via H4.P.Rahu +
        # H4.C.18 (aspect arm), routing the mother to a preponderance-weighed mixed rather than
        # a false "early death". (Field-case fix #2: the owner's living, cordial mother has a
        # Rahu-Moon-in-4th that this rule previously over-called as maternal death.)
        # bphs-doctrine-reviewer VALIDATED (HIGH): Raman's distilled list names Saturn as THE
        # 4th-conjoined instance (HTJAH-I:4401-4402); Chart 71 (HTJAH-I:4616-4621) is a real
        # Rahu-conjunct-Moon Matru-Karaka whose mother LIVED to the native's 36th year (death
        # then via Mars/Saturn marakas) -- direct proof nodal-Moon is not the fatal signature;
        # Rahu/Ketu+Moon = "honour/health in jeopardy" (HTJAH-I:6386) / "mental derangement"
        # (HTJAH-I:6171). CAVEAT (watch): a deeply combust amavasya Moon (Sun+Moon) is a severe
        # affliction carried by the SEPARATE combustion path (combust_fraction), not this rule.
        condition=C.And(C.InRashiHouse("Moon", 4),
                        C.Or(C.Conjunct("Moon", "Mars"), C.Conjunct("Moon", "Saturn"))),
        fortified=None,
        afflicted="the Moon (Matru-Karaka) in the 4th conjoined by a cruel malefic (Mars/Saturn) "
                  "→ the mother's longevity is killed; early death of the mother",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4224)),
    RuleRecord(
        id="H4.C.19", house=4, signification="happiness", group="combination", kind="evaluable",
        condition=C.CountInHouse(4, 1, "malefic"),
        fortified=None,
        afflicted="evil planets in the 4th (Mars/Saturn/Rahu without good associations) → "
                  "the native is reserved",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4224)),
    RuleRecord(
        id="H4.C.20", house=4, signification="happiness", group="combination", kind="evaluable",
        condition=_PlanetInOrAspectsHouse("Jupiter", 4),
        fortified="Jupiter in or aspecting the 4th → the heart will be clean",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4226)),
    RuleRecord(
        id="H4.C.21", house=4, signification="happiness", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Rahu", 4),
                        C.Or(_AspectedByClass("Rahu", "malefic"), _ConjunctAnyMalefic("Rahu"))),
        fortified=None,
        afflicted="Rahu in the 4th joined OR aspected by evil planets → a hypocrite, sweet in "
                  "words but dangerous at heart",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4227)),
    RuleRecord(
        id="H4.C.24", house=4, signification="happiness", group="combination", kind="descriptive",
        condition=None,
        fortified="strong 4th & 9th lords aspected by Jupiter in a kendra/kona → favours from "
                  "royalty; 4th lord with Mars favourably → army commission. "
                  "TODO(predicate: strength gate)",
        afflicted="many evil planets in the 4th + 4th lord in an enemy's house → a great "
                  "sinner; weak Lagna-lord in a watery 4th → drowning. "
                  "TODO(predicate: weak/debil + lord gates)",
        # PARTIALLY SPLIT OUT 2026-08-31 (stale-TODO audit). This record bundled SIX distinct
        # sentences of Raman's — royal favours, mother's affection, an army commission, loss
        # of lands, sinfulness, drowning — under one neutral polarity, which is why it could
        # never be made evaluable as a unit: the outcomes carry different significations AND
        # opposite poles. The two whose signification maps cleanly and whose predicate is
        # narrow are now C.52 (mother) and C.53 (property) below. What remains here is
        # genuinely still blocked or genuinely unscoped: the royalty and army sentences want
        # a strength gate and have no `status`/`career` key on H4, and the sinner/drowning
        # pair are life-event readings with no signification to route to.
        # Citation corrected 2026-09-01: it pointed at HTJAH-I:4219, "The person loses lands
        # by royal or Government orders if the lord of the fourth is neecha with Sun" — a
        # sentence that was SPLIT OUT of this bundle into H4.C.53 on 2026-08-31, which now
        # cites 4219 itself. This record therefore cited a line whose content it no longer
        # contained. Its four surviving sentences begin at 4220 (great sinner, drowning) with
        # the fortified pair at 4230-4232.
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 4220)),

    # #52 — the mother-affection sentence, split out of C.24's bundle. Raman verbatim
    # (HTJAH-I:4228-4229): "He wins the affection of mother if lord of Lagna and the fourth
    # are friendly, and are otherwise beneficially disposed." Both legs are his; the
    # friendship reads the shipped `dignity.compound_relation` in BOTH directions, which is
    # what "are friendly" means for a pair. Scoped to `mother`, where it belongs — the
    # bundle had it under `happiness`.
    RuleRecord(
        id="H4.C.52", house=4, signification="mother", group="combination", kind="evaluable",
        condition=_LagnaAndFourthLordsFriendly(),
        fortified="the lords of the Lagna and the 4th mutually friendly and otherwise "
                  "beneficially disposed → the native wins the affection of the mother",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4228)),

    # #53 — the loss-of-lands sentence, split out of C.24's bundle. Raman verbatim
    # (HTJAH-I:4219-4220): "The person loses lands by royal or Government orders if the lord
    # of the fourth is neecha with Sun." Two legs, both his. Scoped to `property` — the
    # matter the sentence is actually about — rather than the bundle's `happiness`.
    RuleRecord(
        id="H4.C.53", house=4, signification="property", group="combination", kind="evaluable",
        condition=_FourthLordNeechaWithSun(),
        fortified=None,
        afflicted="the 4th lord debilitated and with the Sun → loss of lands by royal or "
                  "Government order",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4219)),

    # ===== B. Mother — longevity & death timing (HTJAH-I:4394-4402) — sig mother =====
    RuleRecord(
        id="H4.C.29", house=4, signification="mother", group="combination", kind="evaluable",
        condition=C.And(C.MoonPhase("waning"),
                        C.Or(C.InRashiHouse("Moon", 6), C.InRashiHouse("Moon", 8)),
                        _ConjunctAnyMalefic("Moon")),
        fortified=None,
        afflicted="a waning Moon with a malefic in the 6th or 8th → early loss of the mother",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4401)),
    RuleRecord(
        id="H4.C.30", house=4, signification="mother", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="Saturn in the 4th with the Moon → early loss of the mother (the Saturn-joined "
                  "instance of HTJAH-I:4224; scored by the decisive H4.C.18a conjunct arm, so kept "
                  "descriptive here to avoid double-counting Saturn+Moon-in-4 in the `mother` verdict)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4401)),
    RuleRecord(
        id="H4.C.26", house=4, signification="mother", group="combination", kind="descriptive",
        condition=None,
        fortified="a strong 4th + Moon in a benefic sign in a kendra aspected by a benefic → "
                  "long life of the mother; treat the 4th house or Matru-Karaka as the mother's "
                  "Lagna and judge the 8th therefrom for her longevity. TODO(predicate: strength "
                  "gate, derived-Lagna)",
        afflicted="4th lord in the 6th/12th weak + Lagna joined by a malefic → early loss of "
                  "the mother (overlaps H4.C.1; the weak gate is a TODO)",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 4394)),

    # ===== C. Education / learning (HTJAH-I:4715-4922) — sig education =====
    RuleRecord(
        id="H4.C.31", house=4, signification="education", group="combination", kind="evaluable",
        condition=C.InRashiHouse("Venus", 4),
        fortified="Venus in the 4th → proficient in music",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4715)),
    RuleRecord(
        id="H4.C.32", house=4, signification="education", group="combination", kind="evaluable",
        condition=C.InRashiHouse("Mercury", 4),
        fortified="Mercury in the 4th → proficient in astrology",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4715)),
    RuleRecord(
        id="H4.C.33", house=4, signification="education", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Sun", 4), C.InRashiHouse("Moon", 4)),
        fortified="Sun and Moon in the 4th → favours political science, psychology, metaphysics",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4716)),
    RuleRecord(
        id="H4.C.34", house=4, signification="education", group="combination", kind="evaluable",
        condition=C.Conjunct("Sun", "Mercury"),
        fortified="a Sun-Mercury combination → proficiency in mathematics",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4717)),
    RuleRecord(
        id="H4.C.37", house=4, signification="education", group="combination", kind="evaluable",
        condition=_PlanetInOrAspectsHouse("Jupiter", 4),
        fortified="Jupiter connected with the 4th → expert in the Vedas and Vedangas",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4720)),
    RuleRecord(
        id="H4.C.40", house=4, signification="education", group="combination", kind="evaluable",
        condition=C.Or(C.HasDignity("Jupiter", {"exalt"}),
                       C.InRashiHouse("Jupiter", 2), C.InRashiHouse("Jupiter", 9),
                       C.InRashiHouse("Jupiter", 5), C.InRashiHouse("Jupiter", 10)),
        fortified="Jupiter exalted, or in the 2nd/9th/5th/10th → great learning in the "
                  "Vedas and scriptures",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4919)),
    RuleRecord(
        id="H4.C.41", house=4, signification="education", group="combination", kind="evaluable",
        condition=C.Or(C.InRashiHouse("Rahu", 4), C.InRashiHouse("Rahu", 5)),
        fortified="Rahu in the 4th or 5th → favours diplomacy; can probe others' minds",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4921)),

    # ===== D. Conveyances / vehicles (HTJAH-I:4928-4941) — sig vehicles =====
    RuleRecord(
        id="H4.C.43", house=4, signification="vehicles", group="combination", kind="evaluable",
        condition=C.Or(C.InRashiHouse("Venus", 4), C.InRashiHouse("Venus", 11)),
        fortified="Venus in the 4th (with the 4th lord) or in the 11th → confers vehicles",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4931)),
    RuleRecord(
        id="H4.C.45", house=4, signification="vehicles", group="combination", kind="evaluable",
        condition=C.And(_PlanetInOrAspectsHouse("Jupiter", 4), C.InRashiHouse("Venus", 7)),
        fortified="Jupiter in/aspecting the 4th with Venus in the 7th → sure acquisition of a "
                  "fitting vahana",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4937)),
    # C.42 — the "lords-associated-in-house, lord-conjunct" TODOs were stale: LordsConjunct,
    #        LordIn and _LagnaInSigns-style checks all exist. Encoded 2026-08-23 as the
    #        three-disjunct transcription. Review in DOCTRINE_BACKLOG "H8-H3 sweep finale".
    RuleRecord(
        id="H4.C.42", house=4, signification="vehicles", group="combination", kind="evaluable",
        condition=C.Or(
            # lords of the 4th & 9th associated (conjunct) IN the Lagna or the 7th
            C.And(C.LordsConjunct(4, 9), C.Or(C.LordIn(4, 1), C.LordIn(4, 7))),
            # the 4th lord conjunct the Moon
            _FourthLordConjunctMoon(),
            # Venus-as-4th-lord (Aquarius/Cancer Lagna) in the 11th/10th/9th
            C.And(_LagnaInSignsLocal(frozenset({11, 4})),
                  C.Or(C.LordIn(4, 11), C.LordIn(4, 10), C.LordIn(4, 9))),
        ),
        fortified="lords of the 4th & 9th associated in the Lagna or 7th, OR the 4th lord "
                  "conjunct the Moon, OR Venus-as-4th-lord (Aquarius/Cancer Lagna) in 11/10/9 → "
                  "possession of a vehicle",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4929)),

    # ===== E. Houses / property (HTJAH-I:4946-4953) — sig property =====
    RuleRecord(
        id="H4.C.46", house=4, signification="property", group="combination", kind="evaluable",
        condition=C.Or(C.LordIn(1, 1), C.LordIn(1, 4), C.LordIn(7, 1), C.LordIn(7, 4)),
        fortified="the lord of the Lagna or the 7th joining the Lagna or the 4th → possession "
                  "of houses",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4946)),
    RuleRecord(
        id="H4.C.47", house=4, signification="property", group="combination", kind="descriptive",
        condition=None,
        fortified="a strong 4th lord in exaltation or a kendra; the 4th lord in Gopura/Mridwa/"
                  "Simhasana shashtiamsa; Venus (Vahana-karaka) in his own Thrimsamsa; or the "
                  "lords of the 4th & 10th associated in a kendra → possession of houses. "
                  "TODO(predicate: strength gate, shashtiamsa/thrimsamsa varga, lords-in-kendra)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 4950)),

    # #48 — the Matru-Karaka Moon under the COMBINED contact of two first-rate malefics ->
    # the mother's significator is considerably afflicted. The exact H4 twin of H5.C.40 —
    # SAME idiom, SAME >= 2 gradient, stated on Chart 68 (HTJAH-I:4550-4560): "This benefice
    # disposition is more than counterbalanced by the combined aspect of two first-rate
    # malefic, viz., Saturn and Mars ... Consequently Matru-Karaka is considerably afflicted"
    # -> Conclusion "the fourth house is considerably afflicted"; the mother died in the
    # native's 16th year (:4572). The Conclusion also teaches the general lesson: Saturn's
    # aspect "could have been construed as beneficial [he is the 4th lord there] but for the
    # fact Saturn happens to be a natural malefic" (:4558-4559) — own-lordship does not
    # sanitize a natural malefic's contact. Same-series corroborations (reviewer-verified):
    # x67 :4529-4539 ("Mars and Saturn, two first-rate malefic"), x70 :4595-4601 ("aspected
    # powerfully by Saturn and Mars ... considerably afflicted", mother died 18th year), x71
    # :4616-4617 (Rahu conjunct + Saturn aspect -> "considerably afflicted"). Thyagaraja
    # (chart_23) is Raman-supported TOO: "Matrukaraja or indicator of mother is with Ketu
    # while ... Lord of the 4th is in the 11th with Saturn ... These combinations explain the
    # fact of his parents having died early" (NH:6060-6063) + "Saturn aspects Cancer"
    # (NH:6071-6072) — two of the engine's three contacts are in his printed text; only the
    # Rahu 7th-aspect is engine-derived via the locked node convention.
    # PRINTED COUNTERBALANCE CASE (record, not a reversal): Chart 74/x74 :4673-4678 — exalted
    # Moon with Ketu AND Mars (two contacts, the rule fires) "counterbalanced by Jupiter's
    # aspect" + benefic Navamsha -> "all the three elements are feebly blemished", mother died
    # when the native was 46. Raman registers the double contact AS an affliction and then
    # outweighs it — exactly what a NON-decisive testimony models. If x74 is ever confirmed
    # mixed/favourable, the fire there is expected, not a surprise.
    # CONTACT SET {Mars, Saturn, Rahu, Ketu}: same empirical-documented-limit reading as
    # H5.C.40 (reviewer-corrected 2026-08-30 — "first-rate" in Raman's own idiom INCLUDES the
    # Sun, HTJAH-I:5673, but no printed MK/PK condemnation names the Sun as the contact).
    # NON-decisive testimony per the C.39/C.40 pattern. The >= 2 bar spares every favourable
    # H4 twin (chart_42/54/57 and x75 each carry exactly ONE contact); no printed chart
    # condemns the mother on a single MK contact alone — h4_01's single Saturn is CONJUNCT
    # Moon-in-the-4th, which is the separate decisive H4.C.18a. Fires (engine drishti,
    # nodes 7th-only) on x67, x68, chart_23 (afflicted) + x71 (mixed) across the 16 confirmed
    # H4 mother goldens; zero favourable fires.
    RuleRecord(
        id="H4.C.48", house=4, signification="mother", group="combination", kind="evaluable",
        condition=_MatruKarakaDoublyAfflicted(),
        fortified=None,
        afflicted="the Matru-Karaka Moon carries the combined contact of two or more "
                  "first-rate malefics → the mother's significator is considerably afflicted",
        frame="KARAKA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 4550)),

    # C.49 — the 4th house hemmed by papakartari -> book-learning impaired. Shivaji verbatim
    # (NH:4961-4963): "the 4th house is subjected to Papakarthari Yoga. Evidently Shivaji
    # was unlettered." NON-decisive testimony: Raman's own next sentence supplies the
    # compensation (C.50 below), and his conclusion for Shivaji is two-sided — under the
    # sparse-contradiction rule the pair correctly lands MIXED there. Independent
    # corroboration (review sweep): Prophet Mahamud, "The 4th house is highly afflicted
    # indicating that he was illiterate" (NH:2818-2819). Counter-balance recorded: h4_03's
    # education is favourable with a hemmed 4th (measured pillars outweigh, the x74 shape).
    RuleRecord(
        id="H4.C.49", house=4, signification="education", group="combination", kind="evaluable",
        condition=_FourthHouseHemmedByMalefics(),
        fortified=None,
        afflicted="the 4th house subjected to Papakartari Yoga → book-learning is impaired",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("NH", 4961)),

    # C.50 — the Gnanakaraka Jupiter aspecting the 4th LORD -> learning fortified. Shivaji
    # verbatim (NH:4963-4966): "since Gnanakaraka Jupiter is strongly placed aspecting as he
    # does the lord of the 4th, want of book-learning was more than compensated by his
    # mastery of the great Hindu epics"; reinforced two sentences later ("the 4th lord in
    # the intellectual sign of Gemini receiving the aspect of Jupiter did not leave his mind
    # dull and sterile"). Benefic testimony; fires on the education rows h4_03/x80/h6_12
    # without changing any (their verdicts already sit favourable-side).
    RuleRecord(
        id="H4.C.50", house=4, signification="education", group="combination", kind="evaluable",
        condition=_JupiterAspectsFourthLord(),
        fortified="the Gnanakaraka Jupiter aspecting the lord of the 4th → learning is "
                  "fortified; the mind is not left dull",
        afflicted=None,
        frame="KARAKA", varga="D1", polarity="benefic", source=Citation("NH", 4963)),

    # C.51 — the Matru-Karaka Moon in the LAGNA, Vargottama -> the mother is a powerful,
    # favourable presence. Shaw verbatim (NH:7305-7307): "Shaw's mother was a powerful
    # factor in his life and the Moon's presence in Lagna accounts for this. The benefic
    # disposition of Matrukaraka gave good longevity to his mother". PROVENANCE, stated
    # honestly (reviewer amendment): the "benefic disposition" is left UNNAMED in the
    # mother sentence; the Vargottama leg is INFERRED from the adjacent sentence ("Lagna
    # and the Moon being in Vargottama", NH:7307-7309), which Raman prints for a
    # Rajayoga/career effect, not explicitly for the mother. The inference is reasonable —
    # it is the only printed strength of Shaw's Moon, and something must outweigh the
    # printed Mars aspect ("The Moon (mind) aspected by Mars") — and the leg strictly
    # NARROWS firing, erring safe. Fires on Shaw alone across the confirmed H4 mother rows.
    RuleRecord(
        id="H4.C.51", house=4, signification="mother", group="combination", kind="evaluable",
        condition=_MoonInLagnaVargottama(),
        fortified="the Matru-Karaka Moon in the Lagna, Vargottama → the mother a powerful "
                  "benefic presence; good longevity to the mother",
        afflicted=None,
        frame="KARAKA", varga="D1", polarity="benefic", source=Citation("NH", 7305)),
)
