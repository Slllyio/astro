"""House 11 (Labha / Aya Bhava — gains / friends / elder-siblings / ambitions) —
"Important Combinations".

Encodes the combination rule-atoms of the "Important Combinations" section of
``docs/raman_saab/methodology/house_11_labha.md`` (sub-sections A–F,
HTJAH-II:14355–14736 + the gains-timing block HTJAH-II:15158–15187).

Encoding policy (honest, atom by atom — mirrors H4/H5/H7/H8/H10):

* Existing predicates compose directly. Gains/wealth/ambition rules route to
  ``gains``; property-acquisition rules to ``acquisitions``; elder-brother /
  co-born rules to ``elder_siblings``; friend-keyed rules to ``friends``. Each
  fine key's ``rule_tags`` is extended by the orchestrator AFTER this module is
  returned so the combo aggregates correctly.
* The **source-of-gains-by-planet** table (doc rules 24–30) has the SAME condition
  as the per-planet 11th-house placements (``InRashiHouse(planet, 11)``, tagged
  ``gains`` in ``house_11_labha.py``) — encoding them evaluable would double-count,
  so they are ``kind="descriptive"`` with a note.
* The **Dasa-of-the-11th-lord** family (doc rules 41–54) is "11th lord in house N
  WITH the N-lord" → ``And(LordIn(11, N), LordsConjunct(11, N))``. The extra
  conjunction distinguishes them from the bare ``LordIn(11, N)`` placements.
* Rules needing predicates not yet in the algebra — Vaiseshikamsa / Navamsa-
  dispositor / multi-varga overlays, planet **strength / eclipse / "defeated in
  war"** gates, functional **friendship-between-lords** gates, affliction-grade
  aggregates, **Dasa timing** (Phase-F), and **numeric co-born counts** — go in as
  ``kind="descriptive"`` with a ``TODO(predicate)`` note.
* The **ear-affliction / black-magic health cluster** (doc rules 32–36) is a
  bodily-affliction read off the 11th/3rd with NO matching H11 signification key
  (ear/throat is an H3 matter) — kept descriptive rather than mis-routed.
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


_MOVABLE_SIGNS: Final[frozenset[int]] = frozenset({1, 4, 7, 10})  # cardinal/chara signs
_KENDRA_TRIKONA: Final[frozenset[int]] = frozenset({1, 4, 7, 10, 5, 9})


def _lord_of(house: int, chart: RamanChart) -> str:
    return SIGN_LORDS[((chart.asc_sign - 1) + (house - 1)) % 12 + 1]


# ── local leaf predicates ─────────────────────────────────────────────────────

class _LagnaInSigns(C.Condition):
    def __init__(self, signs: frozenset[int]) -> None:
        self.signs = signs

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return ctx.chart.asc_sign in self.signs


class _ClassAspectsHouse(C.Condition):
    """Some natural planet of `klass` casts a whole-sign drishti on whole-sign `house`."""
    def __init__(self, house: int, klass: str) -> None:
        self.house, self.klass = house, klass

    def evaluate(self, ctx: C.EvalContext) -> bool:
        group = NATURAL_MALEFICS if self.klass == "malefic" else NATURAL_BENEFICS
        return any(name in group and drishti.aspects_house(name, self.house, ctx.chart)
                   for name in ctx.chart.planets)


class _ClassAspectsLord(C.Condition):
    """Some natural planet of `klass` casts a whole-sign drishti on the lord of `house`."""
    def __init__(self, house: int, klass: str) -> None:
        self.house, self.klass = house, klass

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lord_of(self.house, ctx.chart)
        if lord not in ctx.chart.planets:
            return False
        group = NATURAL_MALEFICS if self.klass == "malefic" else NATURAL_BENEFICS
        return any(name != lord and name in group
                   and drishti.aspects_planet(name, lord, ctx.chart)
                   for name in ctx.chart.planets)


class _AspectedByClass(C.Condition):
    """`target` planet is aspected by some natural planet of `klass`."""
    def __init__(self, target: str, klass: str) -> None:
        self.target, self.klass = target, klass

    def evaluate(self, ctx: C.EvalContext) -> bool:
        if self.target not in ctx.chart.planets:
            return False
        group = NATURAL_MALEFICS if self.klass == "malefic" else NATURAL_BENEFICS
        return any(name != self.target and name in group
                   and drishti.aspects_planet(name, self.target, ctx.chart)
                   for name in ctx.chart.planets)


class _LordConjunctClass(C.Condition):
    """The lord of `house` shares a whole-sign house with a natural planet of `klass`."""
    def __init__(self, house: int, klass: str) -> None:
        self.house, self.klass = house, klass

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lord_of(self.house, ctx.chart)
        p = ctx.chart.planets.get(lord)
        if p is None:
            return False
        group = NATURAL_MALEFICS if self.klass == "malefic" else NATURAL_BENEFICS
        return any(name != lord and name in group and q.rasi_house == p.rasi_house
                   for name, q in ctx.chart.planets.items())


class _LordInClass(C.Condition):
    """The lord of `house` occupies a whole-sign house whose number is in `houses`."""
    def __init__(self, house: int, houses: frozenset[int]) -> None:
        self.house, self.houses = house, houses

    def evaluate(self, ctx: C.EvalContext) -> bool:
        p = ctx.chart.planets.get(_lord_of(self.house, ctx.chart))
        return p is not None and p.rasi_house in self.houses


class _LordAspectsHouse(C.Condition):
    """The lord of `from_house` casts a whole-sign drishti on whole-sign `target_house`."""
    def __init__(self, from_house: int, target_house: int) -> None:
        self.from_house, self.target_house = from_house, target_house

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lord_of(self.from_house, ctx.chart)
        return lord in ctx.chart.planets and drishti.aspects_house(
            lord, self.target_house, ctx.chart)


class _HouseHemmedByClass(C.Condition):
    """Subhakartari/Papakartari on a HOUSE: both the 10th-sign and the 12th-sign
    neighbours of whole-sign `house` (i.e. the houses immediately before and after
    it) hold a natural planet of `klass`. Backs Raman's "11th flanked on both sides
    by benefics" (HTJAH-II:14348) and "3rd & 11th hemmed between malefics"
    (HTJAH-II:14403)."""
    def __init__(self, house: int, klass: str) -> None:
        self.house, self.klass = house, klass

    def evaluate(self, ctx: C.EvalContext) -> bool:
        group = NATURAL_MALEFICS if self.klass == "malefic" else NATURAL_BENEFICS
        prev_house = ((self.house - 2) % 12) + 1
        next_house = (self.house % 12) + 1
        seen = {prev_house: False, next_house: False}
        for name, p in ctx.chart.planets.items():
            if name in group and p.rasi_house in seen:
                seen[p.rasi_house] = True
        return all(seen.values())


class _JupiterOwnsHouse(C.Condition):
    """Jupiter is the D1 lord of whole-sign `house` for this Lagna."""
    def __init__(self, house: int) -> None:
        self.house = house

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return _lord_of(self.house, ctx.chart) == "Jupiter"


class _LordInKendraFromMoon(C.Condition):
    """The lord of `house` is in a kendra (1/4/7/10) counted from the Moon."""
    def __init__(self, house: int) -> None:
        self.house = house

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return C.InHouseFrom(_lord_of(self.house, ctx.chart), "MOON", 1).evaluate(ctx) \
            or C.InHouseFrom(_lord_of(self.house, ctx.chart), "MOON", 4).evaluate(ctx) \
            or C.InHouseFrom(_lord_of(self.house, ctx.chart), "MOON", 7).evaluate(ctx) \
            or C.InHouseFrom(_lord_of(self.house, ctx.chart), "MOON", 10).evaluate(ctx)


class _LordsRelated(C.Condition):
    """Lords of houses `h1` and `h2` are "related": conjunction, mutual aspect, or
    parivartana. Backs Raman's recurring "11th lord related to the Nth lord"
    phrasing (doc rules 42, 43). Identity (one planet lords both) → True."""
    def __init__(self, h1: int, h2: int) -> None:
        self.h1, self.h2 = h1, h2

    def evaluate(self, ctx: C.EvalContext) -> bool:
        l1, l2 = _lord_of(self.h1, ctx.chart), _lord_of(self.h2, ctx.chart)
        if l1 == l2:
            return True
        if C.LordsConjunct(self.h1, self.h2).evaluate(ctx):
            return True
        if drishti.mutual_aspect(l1, l2, ctx.chart):
            return True
        return C.Parivartana(self.h1, self.h2).evaluate(ctx)


def _lord_in_own_house(house: int) -> C.Condition:
    """The lord of `house` occupies that same house (in its own sign)."""
    return C.LordIn(house, house)


# ── RULES ─────────────────────────────────────────────────────────────────────

RULES: Final[tuple[RuleRecord, ...]] = (
    # ===== A. Gains / wealth — general (HTJAH-II:14355–14438) =====
    RuleRecord(
        id="H11.C.1", house=11, signification="gains", group="combination", kind="evaluable",
        condition=C.CountInHouse(11, 1, "benefic"),
        fortified="a benefic in the 11th Bhava → acquires wealth through honest and noble means",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14357)),
    RuleRecord(
        id="H11.C.2", house=11, signification="gains", group="combination", kind="evaluable",
        condition=C.CountInHouse(11, 1, "malefic"),
        fortified=None,
        afflicted="malefics in the 11th Bhava → resorts to unfair and unscrupulous methods of "
                  "earning",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 14358)),
    RuleRecord(
        id="H11.C.3", house=11, signification="gains", group="combination", kind="evaluable",
        condition=C.And(C.CountInHouse(11, 1, "benefic"), C.CountInHouse(11, 1, "malefic")),
        fortified="both benefics and malefics in the 11th → sometimes unjust, sometimes just means "
                  "of earning",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 14360)),
    RuleRecord(
        id="H11.C.4", house=11, signification="gains", group="combination", kind="descriptive",
        condition=None,
        fortified="fortified planets in the 11th → fortunate conveyances, bungalows and all "
                  "comforts; a noble beautiful wife; fond of clothes, food and enjoyments. "
                  "TODO(predicate: planet strength gate)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14362)),
    RuleRecord(
        id="H11.C.5", house=11, signification="gains", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="the 11th occupied by a weak planet — eclipsed, depressed, defeated in planetary "
                  "war, or in inimical vargas → even one born affluent loses everything and wanders "
                  "without self-respect. TODO(predicate: weakness/eclipse/planetary-war gate)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 14367)),
    RuleRecord(
        id="H11.C.6", house=11, signification="gains", group="combination", kind="descriptive",
        condition=None,
        fortified="the Lagna, 2nd and 11th lords mutually friendly → earnings used for honourable "
                  "ends (legitimate expenses and charity). TODO(predicate: functional-friendship "
                  "between three lords)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14388)),
    RuleRecord(
        id="H11.C.7", house=11, signification="gains", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="the 2nd and 11th lords afflicted and inimical to the Lagna lord → money "
                  "squandered on wine and women. TODO(predicate: affliction + lord-enmity gate)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 14390)),
    RuleRecord(
        id="H11.C.8", house=11, signification="gains", group="combination", kind="evaluable",
        condition=C.Or(_LordInClass(11, _KENDRA_TRIKONA), C.CountInHouse(11, 1, "malefic")),
        fortified="the 11th lord well placed in a kendra or trikona from the Ascendant, OR malefics "
                  "strong in the 11th → the native is immensely wealthy",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14392)),
    RuleRecord(
        id="H11.C.9", house=11, signification="gains", group="combination", kind="evaluable",
        condition=C.And(_LordInClass(1, frozenset({1, 4, 7, 10})), C.LordIn(10, 4), C.LordIn(9, 11)),
        fortified="Lagna lord in a quadrant + 10th lord in the 4th + 9th lord in the 11th → "
                  "Rajayoga; long-lived, even a ruler",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14409)),
    RuleRecord(
        id="H11.C.10", house=11, signification="gains", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Moon", 11), C.InRashiHouse("Saturn", 11)),
        fortified="the Moon and Saturn joining the 11th house → can become a ruler even if born in "
                  "humble circumstances",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14412)),
    RuleRecord(
        id="H11.C.11", house=11, signification="gains", group="combination", kind="evaluable",
        condition=C.And(
            _JupiterOwnsHouse(11),
            C.Or(_LordInKendraFromMoon(2), _LordInKendraFromMoon(9), _LordInKendraFromMoon(11))),
        fortified="the 2nd, 9th or 11th lord in a kendra from the Moon AND Jupiter owning the 11th → "
                  "similar (ruler) results",
        afflicted=None,
        frame="MOON", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14414)),
    RuleRecord(
        id="H11.C.12", house=11, signification="gains", group="combination", kind="descriptive",
        condition=None,
        fortified="the lord of the Navamsa occupied by the Lagna lord in a kendra/trikona from the "
                  "Lagna or exalted, OR the 11th house in strength → the native is happy after his "
                  "30th year. TODO(predicate: Navamsa-dispositor-of-lord overlay, house-strength gate)",
        afflicted=None,
        frame="LAGNA", varga="D9", polarity="benefic", source=Citation("HTJAH-II", 14420)),
    RuleRecord(
        id="H11.C.13", house=11, signification="gains", group="combination", kind="evaluable",
        condition=C.And(_lord_in_own_house(1), _lord_in_own_house(2), _lord_in_own_house(11)),
        fortified="the lords of the Lagna, the 2nd and the 11th each in their own houses → confer "
                  "much wealth",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14423)),
    RuleRecord(
        id="H11.C.14", house=11, signification="gains", group="combination", kind="evaluable",
        condition=C.Or(C.And(C.LordIn(2, 1), C.LordIn(11, 1)),
                       C.And(C.LordIn(2, 11), C.LordIn(11, 11))),
        fortified="the friendly 2nd and 11th lords together in the Ascendant, OR both in the 11th "
                  "house (in strength) → fabulous wealth (the Lagna+2nd+11th-lords-in-a-trine/"
                  "quadrant variant is deferred — TODO(predicate: three-lords-same-class gate))",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14424)),
    RuleRecord(
        id="H11.C.15", house=11, signification="gains", group="combination", kind="evaluable",
        condition=C.Or(C.Parivartana(2, 11), C.And(C.LordIn(1, 2), C.LordIn(2, 11)), C.LordIn(11, 1)),
        fortified="the 2nd & 11th lords exchanging houses, OR the Lagna lord in the 2nd with the 2nd "
                  "lord in the 11th, OR the 11th lord in the Lagna → acquires much property",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14431)),
    RuleRecord(
        id="H11.C.16", house=11, signification="gains", group="combination", kind="descriptive",
        condition=None,
        fortified="the 1st, 2nd, 9th and 11th attaining their exalted Navamsa or Vaiseshikamsa "
                  "(own moolatrikona / exaltation / same varga three or more times) → becomes a "
                  "millionaire. TODO(predicate: Vaiseshikamsa / multi-varga rank overlay)",
        afflicted=None,
        frame="LAGNA", varga="D9", polarity="benefic", source=Citation("HTJAH-II", 14436)),

    # ===== B. Gains — timing / loss qualifiers (HTJAH-II:15158–15187) =====
    RuleRecord(
        id="H11.C.17", house=11, signification="gains", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="the Dasa of a weak or depressed planet (among the 11th-influencers) → loss of "
                  "labha / gains. TODO(predicate: weakness gate + Dasa timing)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 15158)),
    RuleRecord(
        id="H11.C.18", house=11, signification="gains", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="in the major/sub-period of an 11th-influencer that is afflicted by malefics, "
                  "combust, depressed, eclipsed, or with inimical planets → loss of the 11th-Bhava "
                  "significations. TODO(predicate: affliction-grade gate + Dasa timing)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 15171)),
    RuleRecord(
        id="H11.C.19", house=11, signification="gains", group="combination", kind="evaluable",
        condition=C.Or(C.Parivartana(2, 5), C.Parivartana(2, 11)),
        fortified="the lords of the 2nd & 5th, OR the 2nd & 11th, having mutually exchanged places "
                  "→ gains in their Dasas/Bhuktis",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 15176)),
    RuleRecord(
        id="H11.C.20", house=11, signification="gains", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(5, 5), C.LordIn(9, 9)),
        fortified="the lords of the 5th & 9th occupying the 5th & 9th respectively → gains predicted "
                  "in their periods",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 15179)),
    RuleRecord(
        id="H11.C.21", house=11, signification="gains", group="combination", kind="evaluable",
        condition=C.LordsConjunct(11, 12),
        fortified=None,
        afflicted="the 11th lord associated with the 12th lord → loss expected during their mutual "
                  "periods",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 15182)),
    RuleRecord(
        id="H11.C.22", house=11, signification="gains", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(1, 8), C.LordIn(4, 8), C.LordIn(9, 8)),
        fortified=None,
        afflicted="the Lagna, 4th & 9th lords in the 8th house → financial stress in their "
                  "major/minor periods",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 15183)),
    RuleRecord(
        id="H11.C.23", house=11, signification="gains", group="combination", kind="evaluable",
        condition=C.Or(C.LordIn(5, 8), C.LordIn(8, 5)),
        fortified=None,
        afflicted="the 5th lord in the 8th, OR the 8th lord in the 5th → losses can occur",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 15185)),

    # ===== C. Source-of-gains by planet in the 11th (HTJAH-II:14373–14386) =====
    # Condition for each is InRashiHouse(<planet>, 11) — IDENTICAL to the per-planet
    # placements (H11.P.<planet>, tagged "gains"), whose result text already names
    # the income source. Encoding evaluable here would double-count, so descriptive.
    RuleRecord(
        id="H11.C.24", house=11, signification="gains", group="combination", kind="descriptive",
        condition=None,
        fortified="Sun in the 11th → source of gains is a fortune received as an inheritance. "
                  "(Condition Sun-in-11th already scored by placement H11.P.Sun under `gains`.)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14374)),
    RuleRecord(
        id="H11.C.25", house=11, signification="gains", group="combination", kind="descriptive",
        condition=None,
        fortified="Moon in the 11th → gains via mother, sea-products, pearls, milk, farms, fruit "
                  "orchards and breweries. (Already scored by placement H11.P.Moon.)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14375)),
    RuleRecord(
        id="H11.C.26", house=11, signification="gains", group="combination", kind="descriptive",
        condition=None,
        fortified="Mars in the 11th → gains via factories, litigation, lands, rentals and "
                  "self-exertion. (Already scored by placement H11.P.Mars.)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14377)),
    RuleRecord(
        id="H11.C.27", house=11, signification="gains", group="combination", kind="descriptive",
        condition=None,
        fortified="Mercury in the 11th → gains via teaching, writing, friends or uncles. "
                  "(Already scored by placement H11.P.Mercury.)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14382)),
    RuleRecord(
        id="H11.C.28", house=11, signification="gains", group="combination", kind="descriptive",
        condition=None,
        fortified="Jupiter in the 11th → gains via knowledge (scientific/religious/literary) and "
                  "well-placed sons. (Already scored by placement H11.P.Jupiter.)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14383)),
    RuleRecord(
        id="H11.C.29", house=11, signification="gains", group="combination", kind="descriptive",
        condition=None,
        fortified="Venus in the 11th → gains via dance, drama, cinema, fine arts, music and women. "
                  "(Already scored by placement H11.P.Venus.)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14384)),
    RuleRecord(
        id="H11.C.30", house=11, signification="gains", group="combination", kind="descriptive",
        condition=None,
        fortified="Saturn in the 11th → gains via industries, labour and agriculture. "
                  "(Already scored by placement H11.P.Saturn.)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14386)),

    # ===== D. Friends / social influence / afflictions (HTJAH-II:14348–14408) =====
    RuleRecord(
        id="H11.C.31", house=11, signification="elder_siblings", group="combination",
        kind="evaluable",
        condition=C.Or(_HouseHemmedByClass(11, "benefic"),
                       C.Or(C.CountInHouse(11, 1, "benefic"), _ClassAspectsHouse(11, "benefic"))),
        fortified="the 11th flanked on both sides by benefics, or otherwise favourably disposed → "
                  "a powerful elder brother; fabulous wealth through the mother",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14348)),
    RuleRecord(
        id="H11.C.32", house=11, signification="gains", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="Mars in the 11th + a movable-sign Lagna aspected by the 6th lord → physical "
                  "ailments and fever from spells and black-magic. Kept descriptive: an ear/black-"
                  "magic health output with no matching H11 signification key (ear/throat is an H3 "
                  "matter). Predicates exist: And(InRashiHouse('Mars',11), _LagnaInSigns(movable), "
                  "_LordAspectsHouse(6, 1)). TODO(signification: no H11 health-affliction key)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 14397)),
    RuleRecord(
        id="H11.C.33", house=11, signification="gains", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="malefics aspecting the 11th, 5th, 9th & 3rd without any benefic aspect → "
                  "ear-troubles and deafness. Kept descriptive: ear-affliction has no H11 sig key "
                  "(ear/throat is an H3 matter). TODO(signification: no H11 health-affliction key)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 14400)),
    RuleRecord(
        id="H11.C.34", house=11, signification="gains", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="heavy afflictions + the 3rd & 11th hemmed between malefics (papakartari) → may "
                  "become stone-deaf. Kept descriptive: ear-affliction has no H11 sig key; the "
                  "papakartari leg is _HouseHemmedByClass(11,'malefic') ∧ _HouseHemmedByClass(3,"
                  "'malefic') but routing has no target. TODO(signification: no H11 health key)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 14402)),
    RuleRecord(
        id="H11.C.35", house=11, signification="gains", group="combination", kind="descriptive",
        condition=None,
        fortified="a feeble benefic aspect to the deaf-making affliction above → only slight "
                  "deafness. Kept descriptive: ear-affliction has no H11 sig key. "
                  "TODO(predicate: feeble-aspect grade; signification: no H11 health key)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 14404)),
    RuleRecord(
        id="H11.C.36", house=11, signification="gains", group="combination", kind="descriptive",
        condition=None,
        fortified="both benefic and malefic aspects on the 11th & 3rd → irritating ear-ailments "
                  "but not deafness. Kept descriptive: ear-affliction has no H11 sig key. "
                  "TODO(signification: no H11 health-affliction key)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 14405)),

    # ===== E. Elder siblings / co-borns (HTJAH-II:14744–14759) =====
    RuleRecord(
        id="H11.C.37", house=11, signification="elder_siblings", group="combination",
        kind="evaluable",
        condition=C.Or(C.CountInHouse(11, 1, "benefic"), _ClassAspectsHouse(11, "benefic")),
        fortified="benefic aspects and associations on the 11th house → gives elder brothers and "
                  "ensures their happiness and long life",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14745)),
    RuleRecord(
        id="H11.C.38", house=11, signification="elder_siblings", group="combination",
        kind="evaluable",
        condition=C.And(
            C.Or(C.CountInHouse(11, 1, "malefic"), _ClassAspectsHouse(11, "malefic")),
            C.Or(_LordConjunctClass(11, "malefic"), _ClassAspectsLord(11, "malefic"))),
        fortified=None,
        afflicted="malefic aspects and associations on BOTH the 11th house and the 11th lord → "
                  "deny elder brothers, or give them short lives, or mar their prosperity",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 14747)),
    RuleRecord(
        id="H11.C.39", house=11, signification="elder_siblings", group="combination",
        kind="evaluable",
        condition=C.And(C.Or(C.LordIn(11, 6), C.LordIn(11, 8), C.LordIn(11, 12)),
                        _AspectedByClass("Mars", "malefic")),
        fortified=None,
        afflicted="the 11th lord in the 6th/8th/12th AND the karaka Mars afflicted → may have no "
                  "elder brother, or lose him by death",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 14749)),
    RuleRecord(
        id="H11.C.40", house=11, signification="elder_siblings", group="combination",
        kind="descriptive",
        condition=None,
        fortified="(one theory) the number of planets taken together in the 11th and 12th houses → "
                  "the number of elder co-borns — subject to qualification; students should test it "
                  "for themselves. TODO(predicate: numeric count output, not a boolean gate)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 14755)),

    # ===== F. Fulfilment of ambitions — Dasa of the 11th lord (HTJAH-II:14615–14736) =====
    # Each is "11th lord in house N WITH the N-lord" → And(LordIn(11,N), LordsConjunct(11,N)).
    # The added conjunction distinguishes these from the bare LordIn(11,N) placements.
    RuleRecord(
        id="H11.C.41", house=11, signification="gains", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(11, 1), C.LordsConjunct(11, 1)),
        fortified="the 11th lord in the Ascendant with the Lagna lord → a happy and prosperous "
                  "life (in the lord's major period)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14615)),
    RuleRecord(
        id="H11.C.42", house=11, signification="gains", group="combination", kind="evaluable",
        condition=_LordsRelated(11, 10),
        fortified="the 11th lord related to the 10th lord → a successful career; merit recognised; "
                  "many distinctions",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14617)),
    RuleRecord(
        id="H11.C.43", house=11, signification="gains", group="combination", kind="evaluable",
        condition=_LordsRelated(11, 2),
        fortified="the 11th lord related to the 2nd house/lord → business fares well, huge profits",
        afflicted="if afflicted → may lose an elder brother, or an elder brother suffers troubles "
                  "and bad health",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14619)),
    RuleRecord(
        id="H11.C.44", house=11, signification="gains", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(11, 2), C.LordsConjunct(11, 2)),
        fortified="the 11th lord in the 2nd with the 2nd lord → earns large sums (Mars+Sun → "
                  "dentist/throat-specialist prosperity; with the 9th & 2nd lords in exaltation/own "
                  "vargas → millionaire). The 11th lord in the 6/8/12 from Navamsa Lagna → only "
                  "moderate results. TODO(predicate: Navamsa 6/8/12 overlay for the moderate qualifier)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14624)),
    RuleRecord(
        id="H11.C.45", house=11, signification="elder_siblings", group="combination",
        kind="evaluable",
        condition=C.And(C.LordIn(11, 3), C.LordsConjunct(11, 3)),
        fortified="the 11th lord in the 3rd with the 3rd lord → both elder & younger co-borns; "
                  "brothers taken as business partners → much wealth; writing ability",
        afflicted="if malefics afflict the 11th lord → the brother incurs losses; obstacles from "
                  "competitors",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14631)),
    RuleRecord(
        id="H11.C.46", house=11, signification="gains", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(11, 4), C.LordsConjunct(11, 4)),
        fortified="the 11th lord in the 4th with the 4th lord → fortunate in the mother; excellent "
                  "education, fame, awards; earns via lands/vehicles/houses; domestic harmony",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14638)),
    RuleRecord(
        id="H11.C.47", house=11, signification="gains", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(11, 5), C.LordsConjunct(11, 5)),
        fortified="the 11th lord in the 5th with the 5th lord → fast spiritual sadhana; excellent "
                  "children; earns via investment",
        afflicted="malefics here → death of a child or intense anguish on account of progeny "
                  "(minimised if the 11th lord is fortified in the Navamsa)",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14650)),
    RuleRecord(
        id="H11.C.48", house=11, signification="gains", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(11, 6), C.LordsConjunct(11, 6)),
        fortified="the 11th lord in the 6th with the 6th lord → succeeds as a lawyer & through "
                  "litigation; healthy; ill-wishers can't harm; good earnings; a maternal uncle's "
                  "business may fall in his favour",
        afflicted="if afflicted → leg troubles; medical and legal expenses",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14660)),
    RuleRecord(
        id="H11.C.49", house=11, signification="gains", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(11, 7), C.LordsConjunct(11, 7)),
        fortified="the 11th lord in the 7th with the 7th lord → a rich wife; strong Sun → ambassador "
                  "abroad; powerful influential friends; successful partnerships",
        afflicted="malefics → both spouses earn by questionable means; strong Lagna lord but weak "
                  "7th → the wife may desert",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14669)),
    RuleRecord(
        id="H11.C.50", house=11, signification="gains", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(11, 8), C.LordsConjunct(11, 8)),
        fortified=None,
        afflicted="the 11th lord joining the 8th lord in the 8th → pecuniary losses, mounting "
                  "debts; business fails; mental aberration; succeeds only in small manual-labour "
                  "ventures; warped morals; bodily weakness and pain",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 14678)),
    RuleRecord(
        id="H11.C.51", house=11, signification="gains", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(11, 9), C.LordsConjunct(11, 9)),
        fortified="the 11th lord in the 9th with the 9th lord → exalted/aristocratic father & "
                  "background; continues & extends the family business; moves with rulers; "
                  "religious; foreign collaboration brings distinction and money",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14690)),
    RuleRecord(
        id="H11.C.52", house=11, signification="gains", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(11, 10), C.LordsConjunct(11, 10)),
        fortified="the 11th lord in the 10th with the 10th lord → a highly successful, distinguished "
                  "career; more than one occupation",
        afflicted="malefics afflicting the 10th → powerful and rich but unscrupulous; heavy "
                  "affliction → monstrous nature, loss of wealth and power",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14699)),
    RuleRecord(
        id="H11.C.53", house=11, signification="elder_siblings", group="combination",
        kind="evaluable",
        condition=C.LordIn(11, 11),
        fortified="the 11th lord in the 11th → succeeds without effort; fair dealings, goodwill; a "
                  "dutiful son; money spent only legitimately/charity; a FAMOUS elder brother; "
                  "business keyed to the lord's nature (Jupiter→books/publishing/religion; "
                  "Saturn→industries/print/oil/quarries; Venus→women/hotels/films/art; "
                  "Mercury→writing/teaching/research; Mars→drugs/lands/metals/sports; "
                  "Sun→photography/gold/banking/stock; Moon→farming/dairy/wines/pearls/fish)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14709)),
    RuleRecord(
        id="H11.C.54", house=11, signification="gains", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(11, 12), C.LordsConjunct(11, 12)),
        fortified=None,
        afflicted="the 11th lord in the 12th with the 12th lord → losses through varied "
                  "expenditure; malefics → wealth squandered; the elder brother's troubled phase/"
                  "loss. The 11th lord in the 6/8/12 from Navamsa Lagna → runs into debts. "
                  "TODO(predicate: Navamsa 6/8/12 overlay for the debt qualifier)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 14731)),
)
