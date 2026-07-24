"""House 10 (Karma — profession / status / authority) — "Important Combinations".

Encodes the combination rule-atoms of the "Important Combinations" tables in
``docs/raman_saab/methodology/house_10_karma.md`` (HTJAH-II:9685-14230).

Encoding policy (honest, atom by atom — mirrors H2/H3/H7/H8):

* Existing predicates compose directly. "Kind of profession" rules route to the
  fine ``profession_*`` significations (NOT ``career``) so they never double-count
  the ``career`` placement layer (lord_in_12 / planets_in_10th).
* Rules needing predicates not yet in the algebra — the **Navamsa-dispositor of the
  10th lord** routing (rules 5-11), the **Jaimini Atmakaraka / Karakamsa** overlay
  (15-25, 42; Stage-5 KARAKAMSA origin), the per-planet **trade catalogues** and
  **sign-by-sign career map** (12-14; lookups, not booleans), planet
  strength/weak/afflicted gates, and the **dasa-phala** rise/fall verdicts (Phase-F)
  — go in as ``kind="descriptive"`` with a ``TODO(predicate)`` note.
* OUT OF SCOPE here: the Varahamihira 32-Rajayoga enumeration and the vargottama-
  aspect-count Rajayogas (descriptive pointers) — structural Rajayogas are encoded.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine import drishti
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation
from app.raman_saab.primitives.dignity import dignity
from app.raman_saab.primitives.functional_nature import (
    NATURAL_BENEFICS, NATURAL_MALEFICS)


_KENDRAS: Final[tuple[int, ...]] = (1, 4, 7, 10)


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


class _DignityInKendrasAtLeast(C.Condition):
    """At least `n` planets sit in a kendra (1/4/7/10) with a D1 dignity in `states`
    (e.g. exalted or own-sign) — the "planets exalted/own in quadrants" Rajayoga."""
    def __init__(self, n: int, states: set[str]) -> None:
        self.n, self.states = n, states

    def evaluate(self, ctx: C.EvalContext) -> bool:
        count = sum(1 for name, p in ctx.chart.planets.items()
                    if p.rasi_house in _KENDRAS
                    and C.HasDignity(name, self.states).evaluate(ctx))
        return count >= self.n


class _AllKendrasHaveClass(C.Condition):
    """Every kendra (1/4/7/10) holds at least one planet of `klass`
    ("benefics/malefics in all four quadrants")."""
    def __init__(self, klass: str) -> None:
        self.klass = klass

    def evaluate(self, ctx: C.EvalContext) -> bool:
        group = NATURAL_MALEFICS if self.klass == "malefic" else NATURAL_BENEFICS
        return all(any(name in group and p.rasi_house == h
                       for name, p in ctx.chart.planets.items())
                   for h in _KENDRAS)


class _HouseInfluencedByClass(C.Condition):
    """A natural planet of `klass` OCCUPIES OR ASPECTS whole-sign `house` (from the Lagna) — the
    benefic/malefic house-influence used to judge whether the 10th (Karma) is fortified by benefics
    or afflicted by malefics (HTJAH-II:11064 'benefics in the 10th -> noble; malefics -> evil'; the
    aspect arm per Raman's standard 'the 10th aspected by a benefic' readings, e.g. :9617/:11241).
    Placement-based, so it fires on a Track-B chart with no Shadbala. With `exclude_debil` a
    DEBILITATED benefic is not counted as a fortifier (a light strength gate — bphs-reviewer flag:
    Raman does not let a debilitated significator fortify, HTJAH-II:10177-10178; combustion is the
    other weakener but is not computable on a Track-B stated-positions chart, so it is documented
    rather than gated here)."""
    def __init__(self, house: int, klass: str, exclude_debil: bool = False) -> None:
        self.house = house
        self.exclude_debil = exclude_debil
        self.group = NATURAL_MALEFICS if klass == "malefic" else NATURAL_BENEFICS

    def evaluate(self, ctx: C.EvalContext) -> bool:
        ch = ctx.chart
        for name, p in ch.planets.items():
            if name not in self.group:
                continue
            if self.exclude_debil and dignity(name, ch) == "debil":
                continue
            if p.rasi_house == self.house or drishti.aspects_house(name, self.house, ch):
                return True
        return False


# ── RULES ─────────────────────────────────────────────────────────────────────

RULES: Final[tuple[RuleRecord, ...]] = (
    # ===== A. Nature of profession (anchors) — fine profession_* significations =====
    RuleRecord(
        id="H10.C.1", house=10, signification="profession_learned", group="combination",
        kind="evaluable", condition=C.InRashiHouse("Mercury", 10),
        fortified="Mercury in the 10th → the best gift for an author/writer; with Jupiter or "
                  "Venus influencing → a poet, or an author on spiritual/literary subjects",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9685)),
    RuleRecord(
        id="H10.C.4", house=10, signification="profession_learned", group="combination",
        kind="evaluable", condition=C.And(C.InRashiHouse("Sun", 10), C.InRashiHouse("Rahu", 10)),
        fortified="Sun and Rahu together in the 10th (apt signs) → a medical career (Sun rules "
                  "cardiology)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 11478)),
    RuleRecord(
        id="H10.C.43", house=10, signification="profession_trade", group="combination",
        kind="evaluable", condition=C.And(C.InRashiHouse("Mars", 10), C.InRashiHouse("Venus", 10)),
        fortified="Mars and Venus in the 10th → a trader in foreign lands",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9847)),
    RuleRecord(
        id="H10.C.5", house=10, signification="career", group="combination", kind="descriptive",
        condition=None,
        fortified="the KIND of livelihood is read from the Navamsa-dispositor of the 10th lord "
                  "(Sun→medicine/gold/diplomacy, Moon→ships/agriculture, Mars→metals/fire/military, "
                  "Mercury→writer/artist/astrologer, Jupiter→judge/teacher/banker, Venus→gems/"
                  "textiles/show-business, Saturn→labour/mining), the per-planet trade catalogues, "
                  "the sign-class on the 10th, and the sign-by-sign career map. "
                  "TODO(predicate: Navamsa-dispositor-of-lord + trade/sign lookups)",
        afflicted=None,
        frame="LAGNA", varga="D9", polarity="neutral", source=Citation("HTJAH-II", 10249)),

    # ===== B. Jaimini Atmakaraka / Karakamsa overlay (descriptive — needs AK) =====
    RuleRecord(
        id="H10.C.15", house=10, signification="career", group="combination", kind="descriptive",
        condition=None,
        fortified="Karakamsa (Jaimini) profession overlay: Sun-with-Atmakaraka → statesman; "
                  "Sun-AK aspected by Jupiter→temple, Saturn→vile work, Rahu→foreign concerns; "
                  "Sun-AK with Venus→secretary to women, Mars→local-body head, Mercury→judiciary; "
                  "Moon/Venus-with-AK→journalist/writer; Mars-in-Karakamsa→electrical/mechanical; "
                  "Jupiter-in-Karakamsa→priesthood. AK = 7-karaka strict (NO Rahu/Ketu, per "
                  "CLAUDE.md). TODO(predicate: Atmakaraka / Karakamsa origin — Stage-5)",
        afflicted=None,
        frame="KARAKA", varga="D9", polarity="neutral", source=Citation("HTJAH-II", 10969)),

    # ===== D. Royal / government favour & political power (Rajayoga) — status_honour =====
    RuleRecord(
        id="H10.C.26", house=10, signification="status_honour", group="combination",
        kind="evaluable", condition=_DignityInKendrasAtLeast(3, {"exalt", "own", "moolatrikona"}),
        fortified="three or more planets exalted or in own sign in the quadrants → a widely-known "
                  "ruler (five or more → even an ordinary man comes to rule)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 13261)),
    RuleRecord(
        id="H10.C.31", house=10, signification="status_honour", group="combination",
        kind="evaluable", condition=_AllKendrasHaveClass("benefic"),
        fortified="benefics in all four quadrants → powerful intellect, fame, wealth, recognition",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 11057)),
    RuleRecord(
        id="H10.C.32", house=10, signification="status_honour", group="combination",
        kind="evaluable", condition=_AllKendrasHaveClass("malefic"),
        fortified=None,
        afflicted="malefics in all the kendras → notoriety, crime, hypocrisy, poverty",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 11060)),
    RuleRecord(
        id="H10.C.33", house=10, signification="status_honour", group="combination",
        kind="evaluable", condition=C.CountInHouse(10, 1, "benefic"),
        fortified="benefics in the 10th (from Lagna or Moon) → a noble-minded native",
        afflicted="malefics in the 10th → addicted to evil deeds",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 11064)),
    RuleRecord(
        id="H10.C.27", house=10, signification="status_honour", group="combination",
        kind="descriptive", condition=None,
        fortified="the classical Rajayoga banks — Varahamihira's 32 royalty yogas (exalted "
                  "Mars/Saturn/Jupiter/Sun with one in Lagna; Moon-in-Cancer variants), "
                  "Phaladeepika's {2nd/9th/11th}-lord-in-kendra-from-Moon, the 44 vargottama-"
                  "aspect Rajayogas, and the positional king-yogas. TODO(predicate: multi-planet "
                  "exaltation/vargottama-aspect-count enumeration)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 13275)),

    # ===== E. Dishonour / loss of position (Rajayoga-bhanga) — status_honour =====
    RuleRecord(
        id="H10.C.35", house=10, signification="status_honour", group="combination",
        kind="evaluable",
        condition=C.And(C.Conjunct("Mars", "Saturn"),
                        C.Or(C.InRashiHouse("Mars", 1), C.InRashiHouse("Mars", 7),
                             C.InRashiHouse("Mars", 8), C.InRashiHouse("Mars", 10))),
        fortified=None,
        afflicted="Mars and Saturn joining in the Lagna, 7th, 8th or 10th (unrelieved) → "
                  "aggressive, intolerant, fanatical, ruthless",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 13441)),
    RuleRecord(
        id="H10.C.36", house=10, signification="status_honour", group="combination",
        kind="evaluable", condition=C.InRashiHouse("Saturn", 10),
        fortified=None,
        afflicted="Saturn in the 10th (a politically-oriented chart) → initial success but "
                  "eventual defeat and humiliation; destroys Rajayogas",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 14020)),

    # ===== G. Sanyasa / asceticism — career =====
    RuleRecord(
        id="H10.C.46", house=10, signification="career", group="combination", kind="evaluable",
        condition=C.CountInHouse(10, 4),
        fortified="four planets in the 10th → a renunciate (if combusted by the Sun → pious but "
                  "no actual renunciation)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 11032)),
    RuleRecord(
        id="H10.C.44", house=10, signification="career", group="combination", kind="descriptive",
        condition=None,
        fortified="three strong planets (own/exalt/benefic-varga) in the 10th with a fortified "
                  "10th lord → an ascetic; five planets incl. the 10th lord in a kendra/trine → "
                  "a Jeevanmukta; Moon in Saturn's decanate aspected by Saturn → renunciation. "
                  "TODO(predicate: planet strength/varga gate, decanate)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 11025)),

    # ===== H. Vice / affliction in the 10th — status_honour =====
    RuleRecord(
        id="H10.C.52", house=10, signification="status_honour", group="combination",
        kind="evaluable", condition=C.And(C.InRashiHouse("Moon", 10), _AspectedByClass("Moon", "malefic")),
        fortified=None,
        afflicted="an afflicted Moon in the 10th → a gambler, violent",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 11009)),
    RuleRecord(
        id="H10.C.54", house=10, signification="status_honour", group="combination",
        kind="evaluable", condition=C.And(C.LordIn(2, 10), C.LordIn(7, 10)),
        fortified=None,
        afflicted="the 2nd and 7th lords among the planets in the 10th → lustful",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 11028)),
    RuleRecord(
        id="H10.C.54a", house=10, signification="status_honour", group="combination", kind="evaluable",
        condition=C.LordIn(10, 7),
        fortified=None,
        afflicted="a (weak) 10th lord in the 7th house → the native is of evil conduct "
                  "(strength gate kept in text). Routed to `status_honour` (a conduct/dishonour "
                  "verdict), NOT `career`, so it does not re-score the H10.L.7 placement",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 11027)),

    # ===== I. Neechabhanga Rajayoga (rise from nothing) — status_honour =====
    RuleRecord(
        id="H10.C.55", house=10, signification="status_honour", group="combination",
        kind="evaluable",
        condition=C.And(C.CountInHouse(10, 1, "benefic"), C.CountInHouse(11, 1, "benefic"),
                        C.CountInHouse(3, 1, "benefic")),
        fortified="benefics in the 10th, 11th and 3rd → Rajayoga",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14211)),
    RuleRecord(
        id="H10.C.56", house=10, signification="status_honour", group="combination",
        kind="descriptive", condition=None,
        fortified="Neechabhanga Rajayogas: a debilitated planet whose dispositor/exaltation-lord "
                  "is in a kendra from the Moon/Lagna, or a planet neecha in Rasi but exalted in "
                  "Amsa, raises the native to power. TODO(predicate: neechabhanga-in-kendra, "
                  "Rasi-debil + Amsa-exalt)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 14214)),

    # ===== C. Rise/fall dasa-phala (Phase-F) — descriptive =====
    RuleRecord(
        id="H10.C.60", house=10, signification="career", group="combination", kind="descriptive",
        condition=None,
        fortified="the 10th-lord-in-house rise/fall verdicts (HTJAH-II:10043-10224) and the "
                  "accession/loss timing (kingdom won in the Dasa of a planet in the Lagna/10th "
                  "or the strongest planet; lost in the period of a planet in an inimical sign or "
                  "the 7th from its own sign) are dasa-phala. TODO(predicate: Dasa timing — Phase-F)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 13313)),

    # ===== D. Benefic-influenced, malefic-free 10th -> favourable career =====
    # HTJAH-II:10181-10191 contrasts the benefic-influenced 10th (distinction, eminence, prosperity)
    # with the afflicted 10th (poverty, loss of position); :11064 'benefics in the 10th -> noble';
    # and :3231-3233 gives the exact structure the rule computes — a significator 'in association
    # with or aspected by a benefic and free of malefic aspects'. This is the placement-based
    # FAVOURABLE-career signal that fires WITHOUT Shadbala (so it reaches Track-B charts, where the
    # strength pillars are absent and the career verdict otherwise abstains). The malefic-free guard
    # is load-bearing: a raja/mahapurusha yoga does NOT lift an afflicted 10th (Hitler/Tilak/Gandhi
    # have raja yogas but afflicted careers via malefics ON the 10th). bphs-doctrine-reviewer
    # VALIDATED direction+magnitude (KEEP), with documented edges: (a) the debilitated-benefic case
    # is gated out (exclude_debil, per HTJAH-II:10177-10178); combustion is not computable on Track-B
    # and is left documented; (b) natural (not functional) benefic/malefic classification is used —
    # consistent with the project's fixed NATURAL sets — so a functionally-malefic benefic on the
    # 10th could over-count (accepted limit); (c) a waning Moon / a nodal 7th-aspect are the residual
    # edges. Empirically over-fire-clean: across the golden career charts this holds ONLY on
    # favourable careers (7/0/0), and it does NOT name/claim the Subhakartari hemming yoga (which is
    # the distinct 2nd+12th-flanking configuration, HTJAH-II:18736).
    RuleRecord(
        id="H10.C.61", house=10, signification="career", group="combination", kind="evaluable",
        condition=C.And(_HouseInfluencedByClass(10, "benefic", exclude_debil=True),
                        C.Not(_HouseInfluencedByClass(10, "malefic"))),
        fortified="the 10th (Karma) fortified by an undebilitated benefic — occupying or aspecting "
                  "it — AND free of any malefic occupation or aspect: distinction, eminence and a "
                  "prosperous career",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 10181)),
)
