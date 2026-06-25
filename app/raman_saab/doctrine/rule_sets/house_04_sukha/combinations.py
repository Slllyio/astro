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
        condition=C.And(C.InRashiHouse("Moon", 4), _ConjunctAnyMalefic("Moon")),
        fortified=None,
        afflicted="the Moon (Matru-Karaka) in the 4th conjoined by an evil planet → the mother's "
                  "longevity is killed; early death of the mother",
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
                  "royalty; lord-of-Lagna & 4th-lord friendly & beneficial → wins mother's "
                  "affection; 4th lord with Mars favourably → army commission. "
                  "TODO(predicate: strength gate, lord-friendship)",
        afflicted="4th lord neecha with the Sun → loses lands by Government order; many evil "
                  "planets in the 4th + 4th lord in an enemy's house → a great sinner; weak "
                  "Lagna-lord in a watery 4th → drowning. TODO(predicate: weak/debil + lord gates)",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 4219)),

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
    RuleRecord(
        id="H4.C.42", house=4, signification="vehicles", group="combination", kind="descriptive",
        condition=None,
        fortified="lords of the 4th & 9th associated in the Lagna or 7th, OR the 4th lord "
                  "conjunct the Moon, OR Venus-as-4th-lord (Aquarius/Cancer Lagna) in 11/10/9 → "
                  "possession of a vehicle. TODO(predicate: lords-associated-in-house, lord-conjunct)",
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
)
