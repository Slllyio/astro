"""House 6 (Ari / Roga / Shatru / Rina Bhava) — "Important Combinations".

Encodes the combination rule-atoms of the "Important Combinations" tables in
``docs/raman_saab/methodology/house_06_ari.md`` (HTJAH-I:6072-6111 for the
disease / debts / enemies / litigation atoms, plus the death-in-battle and
death-in-a-dual-fight Navamsha atoms at 6098-6100).

Encoding policy (honest, atom by atom — mirrors H4/H5/H7/H8/H10):

* Existing condition-algebra predicates compose directly (``InRashiHouse``,
  ``LordIn``, ``Conjunct``, ``Aspects``, ``Parivartana``, ``CountInHouse``,
  ``MutualAspect``). Lord-conjunct-lord / lord-conjunct-planet / planet-with-
  house-lord / class-aspects patterns reuse the H5/H8 local leaves.
* The 6th is a DUSTHANA: for the *enemies* axis Raman INVERTS the usual valence —
  "If evil planets aspect or occupy the 6th, the native will have few enemies; if
  good planets … the number of enemies will increase" (HTJAH-I:6072-6073). That
  inversion is owned by the placement/aggregation engine (`is_dusthana_inversion`,
  Engine Note 2); the enemy-COUNT combos here route to ``enemies`` and carry the
  inverted polarity in the record (benefic = fewer enemies).
* Fine sig routing (significations.py _H6): disease atoms → ``enemies_disease``
  (the disease-bearing aggregate) except lingering/always-suffering/incurable →
  ``disease_chronic``; money-loss/auction → ``debts``; enemy/relative/friend
  count and litigation/imprisonment → ``enemies``; the Mars-in-6th-afflicted
  accident reading → ``accidents``.
* Rules needing predicates not yet in the algebra — **Mandi/Gulika** longitude,
  the **cruel-Navamsha** overlay, the **planet-weak**/"evil lord" strength gate,
  **dasha year-timing** (Phase-F), and **derived-frame "evil lord"/"benefic's
  house"** qualifiers — go in as ``kind="descriptive"`` with a ``TODO(predicate)``
  note.

No rule double-counts a placement already fired by ``planets_in_6th``
(``InRashiHouse(planet, 6)``) or ``lord_in_house`` (``LordIn(6, n)``) within the
SAME signification: every combo either uses a compound condition the flat layer
does not carry, or routes to a distinct fine matter (accidents / debts / enemies /
disease_chronic). The lone bare-disjunction atom (evil 6th-lord in 1/8/10 → boils)
is kept ``descriptive`` precisely because its ungated condition would otherwise
equal the L.1/L.8/L.10 placements under the same ``enemies_disease`` matter.
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
    """Lord of whole-sign house `house` (1..12) counted from the Lagna."""
    return SIGN_LORDS[((chart.asc_sign - 1) + (house - 1)) % 12 + 1]


# ── local leaf predicates (conditions.py intentionally untouched) ─────────────

class _ClassAspectsHouse(C.Condition):
    """Some natural planet of `klass` casts a whole-sign drishti on whole-sign `house`."""
    def __init__(self, house: int, klass: str) -> None:
        self.house, self.klass = house, klass

    def evaluate(self, ctx: C.EvalContext) -> bool:
        group = NATURAL_MALEFICS if self.klass == "malefic" else NATURAL_BENEFICS
        return any(name in group and drishti.aspects_house(name, self.house, ctx.chart)
                   for name in ctx.chart.planets)


class _LordConjunctPlanet(C.Condition):
    """The lord of `house` shares a house with `planet` (identity → False)."""
    def __init__(self, house: int, planet: str) -> None:
        self.house, self.planet = house, planet

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lord_of(self.house, ctx.chart)
        if lord == self.planet:
            return False
        return C.Conjunct(lord, self.planet).evaluate(ctx)


class _LordConjunctAnyOf(C.Condition):
    """The lord of `house` shares a house with at least one of `planets` (skips
    identity — a planet is never "with" itself)."""
    def __init__(self, house: int, planets: tuple[str, ...]) -> None:
        self.house, self.planets = house, planets

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lord_of(self.house, ctx.chart)
        return any(lord != p and C.Conjunct(lord, p).evaluate(ctx) for p in self.planets)


class _PlanetAspectsLord(C.Condition):
    """`planet` casts a whole-sign drishti on the lord of `house` (identity → False)."""
    def __init__(self, planet: str, house: int) -> None:
        self.planet, self.house = planet, house

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lord_of(self.house, ctx.chart)
        return lord != self.planet and drishti.aspects_planet(self.planet, lord, ctx.chart)


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


class _LordAspectedByPlanet(C.Condition):
    """The lord of `h_target` is aspected by the lord of `h_aspecter` (identity → False)."""
    def __init__(self, h_target: int, h_aspecter: int) -> None:
        self.h_target, self.h_aspecter = h_target, h_aspecter

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lt = _lord_of(self.h_target, ctx.chart)
        la = _lord_of(self.h_aspecter, ctx.chart)
        return lt != la and drishti.aspects_planet(la, lt, ctx.chart)


class _LordInHouseClass(C.Condition):
    """The lord of `house` sits in a house of class `klass`
    ∈ {kendra,trikona,dusthana,upachaya,maraka}."""
    def __init__(self, house: int, klass: str) -> None:
        self.house, self.klass = house, klass

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return C.InHouseClass(_lord_of(self.house, ctx.chart), self.klass).evaluate(ctx)


class _PlanetWithHouseLord(C.Condition):
    """`planet` shares a house with the lord of house `house` (identity → False)."""
    def __init__(self, planet: str, house: int) -> None:
        self.planet, self.house = planet, house

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _lord_of(self.house, ctx.chart)
        if lord == self.planet:
            return False
        return C.Conjunct(self.planet, lord).evaluate(ctx)


class _MoonConjunctAnyOfInHouses(C.Condition):
    """The Moon shares a house with at least one of `planets` AND the Moon occupies
    one of `houses` (Raman's "Moon joins Saturn/Rahu/Ketu in the 6th/8th/12th"),
    AND the Moon is aspected by the lord of `aspecter_house` (the Lagnadhipati).
    A single compound leaf so the three clauses share the Moon's resolved position."""
    def __init__(self, planets: tuple[str, ...], houses: tuple[int, ...],
                 aspecter_house: int) -> None:
        self.planets, self.houses, self.aspecter_house = planets, houses, aspecter_house

    def evaluate(self, ctx: C.EvalContext) -> bool:
        moon = ctx.chart.planets.get("Moon")
        if moon is None or moon.rasi_house not in self.houses:
            return False
        joins = any(p != "Moon" and C.Conjunct("Moon", p).evaluate(ctx) for p in self.planets)
        if not joins:
            return False
        lord = _lord_of(self.aspecter_house, ctx.chart)
        return lord == "Moon" or drishti.aspects_planet(lord, "Moon", ctx.chart)


class _LordsJoinKendraWith(C.Condition):
    """The lords of `h1` and `h2` BOTH occupy a kendra (1/4/7/10) AND both share that
    kendra with `planet` (Raman's "lords of Lagna and 6th join a Kendra with Saturn").
    A node passed as `planet` (Rahu/Ketu) is matched by conjunction like any body."""
    _KENDRAS: Final[frozenset[int]] = frozenset({1, 4, 7, 10})

    def __init__(self, h1: int, h2: int, planet: str) -> None:
        self.h1, self.h2, self.planet = h1, h2, planet

    def evaluate(self, ctx: C.EvalContext) -> bool:
        l1, l2 = _lord_of(self.h1, ctx.chart), _lord_of(self.h2, ctx.chart)
        pl = ctx.chart.planets.get(self.planet)
        p1, p2 = ctx.chart.planets.get(l1), ctx.chart.planets.get(l2)
        if pl is None or p1 is None or p2 is None:
            return False
        if pl.rasi_house not in self._KENDRAS:
            return False
        return (p1.rasi_house == pl.rasi_house and p2.rasi_house == pl.rasi_house
                and l1 != self.planet and l2 != self.planet)


# ── RULES ─────────────────────────────────────────────────────────────────────

RULES: Final[tuple[RuleRecord, ...]] = (
    # ===== A. Disease / illness (HTJAH-I:6072-6094) =====
    # Rule 1 — EVIL 6th lord in Lagna/8th/10th → boils. DESCRIPTIVE: the doctrine
    # gates this on the "evil lord" (functional-malefic / ill-disposed / weak 6th
    # lord), a predicate the algebra does not yet carry. Encoding only the ungated
    # core Or(LordIn(6,1), LordIn(6,8), LordIn(6,10)) would (a) fake the missing
    # "evil lord" strength gate and (b) duplicate the L.1 / L.8 / L.10 placements
    # exactly, all already routed to enemies_disease — a same-signification
    # double-count. So it is surfaced narratively, not boolean-scored.
    RuleRecord(
        id="H6.C.1", house=6, signification="enemies_disease", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="the EVIL (functional-malefic / weak / ill-disposed) lord of the 6th in "
                  "Lagna, the 8th or the 10th → the native suffers from boils. "
                  "TODO(predicate: 'evil 6th-lord' functional-nature + strength gate; ungated "
                  "this would double-count the L.1/L.8/L.10 placements under enemies_disease)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6073)),
    # Rule 2 — 6th lord in 6th/8th with a co-occupant → boils localised by the
    # co-planet (head / face / front / nose / eyes / armpits). Rasi-core fires; the
    # organ-by-co-planet refinement is kept in the text.
    RuleRecord(
        id="H6.C.2", house=6, signification="enemies_disease", group="combination", kind="evaluable",
        condition=C.And(
            C.Or(C.LordIn(6, 6), C.LordIn(6, 8)),
            C.Or(_LordConjunctPlanet(6, "Sun"), _LordConjunctPlanet(6, "Moon"),
                 _LordConjunctPlanet(6, "Mars"), _LordConjunctPlanet(6, "Mercury"),
                 _LordConjunctPlanet(6, "Jupiter"), _LordConjunctPlanet(6, "Venus"),
                 _LordConjunctPlanet(6, "Saturn"), _LordConjunctPlanet(6, "Rahu"),
                 _LordConjunctPlanet(6, "Ketu"))),
        fortified=None,
        afflicted="6th lord in the 6th or 8th joining the Sun / Moon / Mars-or-Mercury / "
                  "Jupiter / Venus / Saturn-Rahu-Ketu → boils in the head / face / front / "
                  "nose / eyes / armpits respectively",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6074)),
    # Rule 3 — 6th & 8th lords in the 7th & 8th respectively → piles.
    RuleRecord(
        id="H6.C.3", house=6, signification="enemies_disease", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(6, 7), C.LordIn(8, 8)),
        fortified=None,
        afflicted="lords of the 6th and 8th occupying the 7th and the 8th respectively → piles",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6077)),
    # Rule 4 — a planet joining the 6th lord in the Ascendant → disease by co-planet
    # (high fevers / watery-glandular swelling-or-ulcer / bilious / consumption /
    # sexual / nervous / carbuncle-or-spleen). Needs the 6th lord IN Lagna AND a
    # co-occupant — distinct from the bare LordIn(6,1) placement.
    RuleRecord(
        id="H6.C.4", house=6, signification="enemies_disease", group="combination", kind="evaluable",
        condition=C.And(
            C.LordIn(6, 1),
            C.Or(_LordConjunctPlanet(6, "Sun"), _LordConjunctPlanet(6, "Moon"),
                 _LordConjunctPlanet(6, "Mars"), _LordConjunctPlanet(6, "Mercury"),
                 _LordConjunctPlanet(6, "Jupiter"), _LordConjunctPlanet(6, "Venus"),
                 _LordConjunctPlanet(6, "Saturn"))),
        fortified=None,
        afflicted="the Sun / Moon / Mars / Mercury / Jupiter / Venus / Saturn joining the 6th "
                  "lord in the ascendant → high fevers / watery or glandular swelling or ulcer / "
                  "bilious complaints / consumption / sexual troubles / nervous diseases / "
                  "carbuncle or spleen trouble respectively",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6078)),
    # Rule 5 — evil planets in the 6th, OR the 6th lord with Saturn or Rahu → the
    # native suffers always. Chronic/perpetual → disease_chronic. The "many evil
    # planets in 6th" branch uses CountInHouse(6,2,"malefic") (≥2 malefics), distinct
    # from any single InRashiHouse(planet,6) placement.
    RuleRecord(
        id="H6.C.5", house=6, signification="disease_chronic", group="combination", kind="evaluable",
        condition=C.Or(C.CountInHouse(6, 2, "malefic"),
                       _LordConjunctAnyOf(6, ("Saturn", "Rahu"))),
        fortified=None,
        afflicted="evil planets in the 6th, or the 6th lord joining Saturn or Rahu → the native "
                  "suffers (from disease) always",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6080)),
    # Rule 6 — Mars in 6th AND 6th lord in 8th → severe fever (6th & 12th years).
    # Dasha-year timing deferred to the text.
    RuleRecord(
        id="H6.C.6", house=6, signification="enemies_disease", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Mars", 6), C.LordIn(6, 8)),
        fortified=None,
        afflicted="Mars in the 6th and the 6th lord in the 8th → severe fever in the 6th and "
                  "12th years (TODO(predicate: Phase-F dasha-year timing))",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6081)),
    # Rule 7 — Moon and Jupiter in the 6th → leprosy (20th year).
    RuleRecord(
        id="H6.C.7", house=6, signification="disease_chronic", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Moon", 6), C.InRashiHouse("Jupiter", 6)),
        fortified=None,
        afflicted="the Moon and Jupiter in the 6th → contracts leprosy in the 20th year "
                  "(TODO(predicate: Phase-F dasha-year timing))",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6083)),
    # Rule 8 — Rahu in 6th AND Lagna-lord in 8th → watery diseases (26th year).
    RuleRecord(
        id="H6.C.8", house=6, signification="enemies_disease", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Rahu", 6), C.LordIn(1, 8)),
        fortified=None,
        afflicted="Rahu in the 6th and the lord of Lagna in the 8th → watery diseases in the "
                  "26th year (TODO(predicate: Phase-F dasha-year timing))",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6083)),
    # Rule 9 — Parivarthana of 6th & 12th lords → colic (30th year). The 6th↔12th
    # exchange is a recurring disease/debt trigger; this record owns the colic
    # reading, rule 15 owns the money-loss reading (distinct sig).
    RuleRecord(
        id="H6.C.9", house=6, signification="enemies_disease", group="combination", kind="evaluable",
        condition=C.Parivartana(6, 12),
        fortified=None,
        afflicted="Parivarthana (mutual exchange) between the lords of the 6th and the 12th → "
                  "colic in the 30th year (TODO(predicate: Phase-F dasha-year timing))",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6084)),
    # Rule 10 — Lagna-lord in Lagna with the 8th lord → rheumatic affections.
    RuleRecord(
        id="H6.C.10", house=6, signification="enemies_disease", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(1, 1), C.LordsConjunct(1, 8)),
        fortified=None,
        afflicted="the lord of Lagna in Lagna together with the lord of the 8th → rheumatic "
                  "affections",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6085)),
    # Rule 11 — Saturn in 6th with 8th lord AND 12th lord in Lagna → fear from wild
    # animals. (The 8th lord may itself be Saturn; the leaf skips that identity, so
    # this fires when Saturn occupies the 6th and the 8th lord is co-present there.)
    RuleRecord(
        id="H6.C.11", house=6, signification="enemies_disease", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Saturn", 6), _PlanetWithHouseLord("Saturn", 8),
                        C.LordIn(12, 1)),
        fortified=None,
        afflicted="Saturn in the 6th with the lord of the 8th, and the lord of the 12th in "
                  "Lagna → fear from wild animals",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6086)),
    # Rule 12 — Sun in 6th/8th AND Moon in the 12th FROM the Sun → danger through
    # water (5th/9th year). Frame mixes Lagna (Sun house) + Sun (Moon's frame).
    RuleRecord(
        id="H6.C.12", house=6, signification="enemies_disease", group="combination", kind="evaluable",
        condition=C.And(C.Or(C.InRashiHouse("Sun", 6), C.InRashiHouse("Sun", 8)),
                        C.InHouseFrom("Moon", "Sun", 12)),
        fortified=None,
        afflicted="the Sun in the 6th or 8th and the Moon in the 12th from the Sun → danger "
                  "through water in the 5th or 9th year (TODO(predicate: Phase-F dasha-year "
                  "timing))",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6088)),
    # Rule 12a — Moon in the 6th with Mars → jaundiced constitution. Compound (Moon
    # in 6th AND Mars co-present), distinct from the bare InRashiHouse("Moon",6)
    # placement.
    RuleRecord(
        id="H6.C.12a", house=6, signification="enemies_disease", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Moon", 6), C.Conjunct("Moon", "Mars")),
        fortified=None,
        afflicted="the Moon in the 6th with Mars → a jaundiced constitution",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6091)),
    # Rule 13 — Saturn OR Mars in 6th aspected by Rahu or the Sun, Lagna-lord weak →
    # lingering disease. Lingering → disease_chronic. The Lagna-lord-weak strength
    # gate is deferred; the rasi-core (Saturn/Mars in 6th aspected by Rahu/Sun) fires.
    # NOTE (reviewer): "ascendant lord weak" is a load-bearing AND-clause in the
    # source, not a timing overlay; firing the ungated core over-fires when the Lagna
    # lord is strong. Retained evaluable per the module's stated encoding policy and
    # the H5 precedent (structural core fires, strength gate noted as TODO); a future
    # pass may demote to descriptive once the strength predicate lands.
    RuleRecord(
        id="H6.C.13", house=6, signification="disease_chronic", group="combination", kind="evaluable",
        condition=C.Or(
            C.And(C.InRashiHouse("Saturn", 6),
                  C.Or(C.Aspects("Rahu", "Saturn"), C.Aspects("Sun", "Saturn"))),
            C.And(C.InRashiHouse("Mars", 6),
                  C.Or(C.Aspects("Rahu", "Mars"), C.Aspects("Sun", "Mars")))),
        fortified=None,
        afflicted="Saturn or Mars in the 6th aspected by Rahu or the Sun (with a weak Lagna "
                  "lord) → lingering disease (TODO(predicate: Lagna-lord-weak strength gate))",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6091)),
    # Rule 14 — Saturn WITH Mandi in the 6th, aspected by Sun/Mars/Rahu → heart or
    # lung disease. Needs the Mandi/Gulika longitude → descriptive.
    RuleRecord(
        id="H6.C.14", house=6, signification="enemies_disease", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="Saturn with Mandi (Gulika) in the 6th, receiving the aspect of the Sun, "
                  "Mars or Rahu → heart or lung diseases. TODO(predicate: Mandi/Gulika "
                  "longitude)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6093)),

    # ===== B. Debts / money loss (HTJAH-I:6089-6090, 6110-6111) — sig debts =====
    # Rule 15 — Parivarthana of 6th & 12th lords → loss of money (31st/40th year).
    # Same exchange as rule 9, but routed to the DEBTS matter (distinct sig → not a
    # double-count of the colic reading).
    RuleRecord(
        id="H6.C.15", house=6, signification="debts", group="combination", kind="evaluable",
        condition=C.Parivartana(6, 12),
        fortified=None,
        afflicted="Parivarthana between the lords of the 6th and the 12th → loss of money in "
                  "the 31st or 40th year (TODO(predicate: Phase-F dasha-year timing))",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6089)),
    # Rule 16 — 6th lord in 6th with Mars, aspected by Rahu or Ketu → loses estates
    # by auction.
    RuleRecord(
        id="H6.C.16", house=6, signification="debts", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(6, 6), _LordConjunctPlanet(6, "Mars"),
                        C.Or(_PlanetAspectsLord("Rahu", 6), _PlanetAspectsLord("Ketu", 6))),
        fortified=None,
        afflicted="the 6th lord in the 6th with Mars, aspected by Rahu or Ketu → loses his "
                  "estates by auction",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6110)),

    # ===== C. Enemies / relatives / friends (HTJAH-I:6090-6109) — sig enemies =====
    # Rule 17 — 6th lord in 6th with Jupiter AND 12th lord in Lagna → the Sun becomes
    # an enemy.
    RuleRecord(
        id="H6.C.17", house=6, signification="enemies", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(6, 6), _LordConjunctPlanet(6, "Jupiter"), C.LordIn(12, 1)),
        fortified=None,
        afflicted="the 6th lord in the 6th with Jupiter and the 12th lord in Lagna → the Sun "
                  "(i.e. one's own kinsmen / superiors) becomes an enemy",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6090)),
    # Rule 18 — 6th lord in a Kendra aspected by evil planets, OR many evil planets
    # in the 6th → vexed by enemies.
    RuleRecord(
        id="H6.C.18", house=6, signification="enemies", group="combination", kind="evaluable",
        condition=C.Or(C.And(_LordInHouseClass(6, "kendra"), _ClassAspectsLord(6, "malefic")),
                       C.CountInHouse(6, 2, "malefic")),
        fortified=None,
        afflicted="the 6th lord in a Kendra aspected by evil planets, or many evil planets in "
                  "the 6th → the person will be vexed by enemies",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6104)),
    # Rule 19 — 6th lord in a benefic's house aspected by good planets → many
    # friends. "Benefic's house" (sign owned by a natural benefic) is approximated
    # by the good-aspect testimony; the dispositor-benefic gate is deferred. Kept
    # descriptive to flag the missing "house of a benefic" qualifier.
    RuleRecord(
        id="H6.C.19", house=6, signification="enemies", group="combination", kind="descriptive",
        condition=None,
        fortified="the 6th lord in the house (sign) of a benefic planet and aspected by good "
                  "planets → he will have many friends (few enemies). TODO(predicate: "
                  "dispositor-of-lord natural nature)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 6105)),
    # Rule 20 — Lagna-lord in 6th aspected by 6th lord, OR both (Lagna-lord & 6th
    # lord) in Lagna or in the 4th → constantly troubled and vexed by relatives.
    RuleRecord(
        id="H6.C.20", house=6, signification="enemies", group="combination", kind="evaluable",
        condition=C.Or(
            C.And(C.LordIn(1, 6), _LordAspectedByPlanet(1, 6)),
            C.And(C.LordIn(1, 1), C.LordIn(6, 1)),
            C.And(C.LordIn(1, 4), C.LordIn(6, 4))),
        fortified=None,
        afflicted="the lord of Lagna in the 6th aspected by the 6th lord, or both the Lagna "
                  "lord and the 6th lord together in Lagna or in the 4th → constantly troubled "
                  "and vexed by relatives",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6106)),
    # Rule 21 — Jupiter or Venus in Lagna with the 6th lord, aspected by Saturn,
    # Rahu or Mars → put to difficulties by relatives.
    RuleRecord(
        id="H6.C.21", house=6, signification="enemies", group="combination", kind="evaluable",
        condition=C.And(
            C.Or(_PlanetWithHouseLord("Jupiter", 6), _PlanetWithHouseLord("Venus", 6)),
            C.Or(C.InRashiHouse("Jupiter", 1), C.InRashiHouse("Venus", 1)),
            C.Or(_ClassAspectsLord(6, "malefic"),
                 _PlanetAspectsLord("Saturn", 6), _PlanetAspectsLord("Rahu", 6),
                 _PlanetAspectsLord("Mars", 6))),
        fortified=None,
        afflicted="Jupiter or Venus in Lagna with the 6th lord, aspected by Saturn, Rahu or "
                  "Mars → put to difficulties by relatives",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6108)),
    # Rule 22 — 9th lord in the 6th, aspected by the 6th lord → suffers from thieves
    # and fire.
    RuleRecord(
        id="H6.C.22", house=6, signification="enemies", group="combination", kind="evaluable",
        condition=C.And(C.LordIn(9, 6), _LordAspectedByPlanet(9, 6)),
        fortified=None,
        afflicted="the 9th lord occupying the 6th, aspected by the 6th lord → suffers from "
                  "thieves and fire",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6109)),

    # ===== D. Litigation / imprisonment / death-in-battle (HTJAH-I:6096-6100) =====
    # Rule 23 — lords of Lagna and 6th join a Kendra with Saturn → confined
    # (imprisoned).
    RuleRecord(
        id="H6.C.23", house=6, signification="enemies", group="combination", kind="evaluable",
        condition=_LordsJoinKendraWith(1, 6, "Saturn"),
        fortified=None,
        afflicted="the lords of Lagna and the 6th joining a Kendra with Saturn → the person "
                  "will be confined (imprisoned)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6096)),
    # Rule 24 — same, but with Rahu or Ketu → placed in irons.
    RuleRecord(
        id="H6.C.24", house=6, signification="enemies", group="combination", kind="evaluable",
        condition=C.Or(_LordsJoinKendraWith(1, 6, "Rahu"),
                       _LordsJoinKendraWith(1, 6, "Ketu")),
        fortified=None,
        afflicted="the lords of Lagna and the 6th joining a Kendra with Rahu or Ketu → placed "
                  "in irons",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6097)),
    # Rule 25 — Moon (aspected by Lagna-lord) joins Saturn/Rahu/Ketu in the 6th, 8th
    # or 12th → tragic end.
    RuleRecord(
        id="H6.C.25", house=6, signification="enemies", group="combination", kind="evaluable",
        condition=_MoonConjunctAnyOfInHouses(
            ("Saturn", "Rahu", "Ketu"), (6, 8, 12), 1),
        fortified=None,
        afflicted="the Moon (aspected by the Lagna lord) joining Saturn, Rahu or Ketu in the "
                  "6th, 8th or 12th → a tragic end",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6097)),
    # Rule 26 — 6th/8th lord or Mars joins the 3rd lord with Saturn & Rahu in a cruel
    # Navamsha → death in battle. The cruel-Navamsha overlay is deferred → descriptive.
    RuleRecord(
        id="H6.C.26", house=6, signification="enemies", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="the 6th or 8th lord, or Mars, joining the 3rd lord with Saturn and Rahu in "
                  "a cruel Navamsha → death in battle. TODO(predicate: cruel-Navamsha overlay)",
        frame="LAGNA", varga="D9", polarity="malefic", source=Citation("HTJAH-I", 6098)),
    # Rule 27 — Parivarthana OR mutual aspect of Mars and the Sun, in Rashi or in
    # Navamsha → death in a dual fight. The Rashi branch (sign-exchange or mutual
    # aspect of Mars & Sun) is evaluable; the Navamsha branch is noted in the text.
    RuleRecord(
        id="H6.C.27", house=6, signification="enemies", group="combination", kind="evaluable",
        condition=C.Or(C.Exchange("Mars", "Sun"), C.MutualAspect("Mars", "Sun")),
        fortified=None,
        afflicted="Parivarthana or mutual aspect between Mars and the Sun, in the Rashi (or in "
                  "the Navamsha) → death in a dual fight (TODO(predicate: Navamsha Mars-Sun "
                  "exchange/aspect branch))",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6099)),

    # ===== E. Mars-in-6th afflicted accident reading (HTJAH-I:6127) — sig accidents =====
    # The planet-in-6th flat layer carries InRashiHouse("Mars",6) under enemies_disease
    # anchored at the Mars header line 6126; this combo routes the *afflicted* Mars-in-6th
    # (Mars joined by a malefic) to the distinct ACCIDENTS matter and anchors at the
    # "Mars afflicted: accidents..." clause (6127), so it neither double-counts the
    # placement nor shares its citation line.
    RuleRecord(
        id="H6.C.28", house=6, signification="accidents", group="combination", kind="evaluable",
        condition=C.And(C.InRashiHouse("Mars", 6),
                        C.Or(C.Conjunct("Mars", "Saturn"), C.Conjunct("Mars", "Rahu"),
                             C.Conjunct("Mars", "Ketu"))),
        fortified=None,
        afflicted="Mars afflicted in the 6th (with Saturn → operation/animal injury; with Rahu "
                  "→ suicide; with Ketu → poisoning) → accidents, losses and bodily injury",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 6127)),
)
