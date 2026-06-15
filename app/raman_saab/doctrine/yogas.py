"""The yoga layer — named load-bearing yogas Raman invokes in HTJAH worked charts.

Each ``YogaRecord`` cites a REAL on-disk corpus line (verified by the paired
test via :func:`app.raman_saab.doctrine.sources.verify`). Definitions come from
*Three Hundred Important Combinations* (tag ``3HC`` —
``data/knowledge_library/sources/three_hundred_combinations_raman``) and from
*How to Judge a Horoscope* Vol I (``HTJAH-I``). Doctrinal anchor: HTJAH-I
consideration #4 (HTJAH-I:480-482) — whether yogas alter the house influence.

Vipareeta Raja Yoga is encoded EXACTLY as Raman states it: dusthana lords
conjoined in a dusthana give prosperity (HTJAH-I:6302-6303 — "Financial
prosperity can be anticipated during the Dasha of the 6th lord in the 6th, if
he is joined by the lords of the 8th and 12th"; worked-chart usage
HTJAH-I:15864 — 6th lord in the 8th WITH the 12th lord "generates a Vipareeta
Raja-Yoga"). NO Phaladeepika isolation clauses are added.

Kemadruma folds its bhanga in: the record fires only while uncancelled.
Cancellation per 3HC:2182-2185 is exactly: planets in a kendra from birth
(Lagna) OR from the Moon, or the Moon in conjunction with a planet. The
benefic-drishti-on-Moon branch retained in
:mod:`app.raman_saab.primitives.bhangas` is EXTENDED doctrine from the
Phase-2 aspect backfill, NOT attributable to 3HC:2182-2185.

This module deliberately does NOT modify ``doctrine/conditions.py``; the extra
leaf predicates it needs are local ``Condition`` subclasses, and yoga-kind
checks are exposed via :func:`has_yoga` for the orchestrator to wire later.

Usage:
    from app.raman_saab.doctrine.yogas import YOGAS, detect_yogas, has_yoga
    fired = detect_yogas(chart)           # -> tuple[FiredYoga, ...]
    has_yoga(chart, "raja")               # -> bool
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Final, Literal, get_args

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.chart.model import RamanChart
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine import drishti
from app.raman_saab.doctrine.sources import Citation
from app.raman_saab.primitives import bhangas

logger = logging.getLogger(__name__)

YogaKind = Literal["raja", "dhana", "arishta", "lunar", "other"]
_YOGA_KINDS: Final[frozenset[str]] = frozenset(get_args(YogaKind))

_DUSTHANAS: Final[frozenset[int]] = frozenset({6, 8, 12})
_KENDRAS: Final[frozenset[int]] = frozenset({1, 4, 7, 10})
_TRIKONAS: Final[frozenset[int]] = frozenset({1, 5, 9})

# Sunapha/Anapha/Durudhara occupiers: "planets excepting the Sun" (3HC:1834-1835,
# enumerated at 3HC:1845-1846 as Mars, Mercury, Jupiter, Venus, Saturn — the Moon
# itself and the chaya-grahas never count).
_LUNAR_FLANK_PLANETS: Final[tuple[str, ...]] = (
    "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

# Adhi yoga benefics: "Soumyehi implying clearly only the benefics, viz.,
# Mercury, Jupiter and Venus" (3HC:2462-2463).
_ADHI_BENEFICS: Final[tuple[str, ...]] = ("Mercury", "Jupiter", "Venus")


def _house_lord(house: int, chart: RamanChart) -> str:
    """Lord of whole-sign house `house` (1..12) counted from the Lagna."""
    return SIGN_LORDS[((chart.asc_sign - 1) + (house - 1)) % 12 + 1]


# ── local leaf predicates (conditions.py is intentionally untouched) ─────────
class _DusthanaLordsConjoinedInDusthana(C.Condition):
    """Two (or more) DISTINCT dusthana lords (of 6/8/12) share a rasi house that
    is itself a dusthana — Raman's stated Vipareeta form (HTJAH-I:6302-6303,
    worked usage HTJAH-I:15864). No isolation clauses."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        seen: dict[int, set[str]] = {}
        for h in sorted(_DUSTHANAS):
            lord = _house_lord(h, chart)
            p = chart.planets.get(lord)
            if p is not None:
                seen.setdefault(p.rasi_house, set()).add(lord)
        return any(house in _DUSTHANAS and len(lords) >= 2
                   for house, lords in seen.items())


class _KendraTrikonaLordsConjoined(C.Condition):
    """A kendra (1/4/7/10) lord conjoined with a DISTINCT trikona (1/5/9) lord
    (HTJAH-I:622-623: Kendradhipati associated with Trikonadhipati -> Raja yoga)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        kendra_lords = {_house_lord(h, chart) for h in _KENDRAS}
        trikona_lords = {_house_lord(h, chart) for h in _TRIKONAS}
        for k in kendra_lords:
            pk = chart.planets.get(k)
            if pk is None:
                continue
            for t in trikona_lords:
                if t == k:
                    continue
                pt = chart.planets.get(t)
                if pt is not None and pt.rasi_house == pk.rasi_house:
                    return True
        return False


class _LordsMutualAspect(C.Condition):
    """The lords of houses `h1` and `h2` (distinct planets) fully aspect each
    other (HTJAH-I:634 for the 9th/10th lords)."""

    def __init__(self, h1: int, h2: int) -> None:
        self.h1, self.h2 = h1, h2

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        l1, l2 = _house_lord(self.h1, chart), _house_lord(self.h2, chart)
        if l1 == l2 or l1 not in chart.planets or l2 not in chart.planets:
            return False
        return drishti.mutual_aspect(l1, l2, chart)


class _Kemadruma(C.Condition):
    """Moon flanked by empty houses (3HC:2172-2174) — primitive in bhangas.py."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return bhangas.kemadruma(ctx.chart)


class _KemadrumaBhanga(C.Condition):
    """Kemadruma cancellation — primitive in bhangas.py. Encodes the
    3HC:2182-2185 branches (planet in a kendra from birth or from the Moon;
    Moon conjunct a planet) plus the EXTENDED benefic-drishti branch
    documented there as Phase-2 backfill, not 3HC."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return bhangas.kemadruma_bhanga(ctx.chart)


class _NthHouseSignOwnedBy(C.Condition):
    """The whole-sign `house` (1..12 from the Lagna) is a sign owned by `planet`. Backs the
    Dhana-Yoga clause '5th from the Ascendant happens to be a sign of Venus' (3HC:7632)."""

    def __init__(self, house: int, planet: str) -> None:
        self.house, self.planet = house, planet

    def evaluate(self, ctx: C.EvalContext) -> bool:
        sign = ((ctx.chart.asc_sign - 1) + (self.house - 1)) % 12 + 1
        return SIGN_LORDS[sign] == self.planet


# ── record forms ─────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class YogaRecord:
    id: str
    name: str
    kind: YogaKind
    condition: C.Condition
    effect: str
    source: Citation

    def fires(self, chart: RamanChart) -> bool:
        """Does this yoga hold for the chart?"""
        return self.condition.evaluate(C.EvalContext(chart))


@dataclass(frozen=True)
class FiredYoga:
    """An active yoga in a chart, surfaced with its citation."""
    id: str
    name: str
    kind: YogaKind
    effect: str
    source: Citation


def _kendra_from_moon(planet: str) -> C.Condition:
    return C.Or(*[C.InHouseFrom(planet, "MOON", n) for n in sorted(_KENDRAS)])


def _any_flank_in_house_from_moon(n: int) -> C.Condition:
    return C.Or(*[C.InHouseFrom(p, "MOON", n) for p in _LUNAR_FLANK_PLANETS])


# ── the encoded yogas ────────────────────────────────────────────────────────
YOGAS: tuple[YogaRecord, ...] = (
    # — lunar (Moon-centred) —
    YogaRecord(
        id="Y.GAJAKESARI", name="Gajakesari Yoga", kind="lunar",
        condition=_kendra_from_moon("Jupiter"),
        effect=("Many relations, polite and generous; builder of villages and "
                "towns or magistrate over them; lasting reputation even long "
                "after death."),
        source=Citation("3HC", 1589)),   # "If Jupiter is in a kendra from the Moon"
    YogaRecord(
        id="Y.SUNAPHA", name="Sunapha Yoga", kind="lunar",
        condition=_any_flank_in_house_from_moon(2),
        effect=("Self-earned property; ruler or his equal; intelligent, "
                "wealthy, good reputation."),
        source=Citation("3HC", 1834)),   # planets (excepting the Sun) in 2nd from Moon
    YogaRecord(
        id="Y.ANAPHA", name="Anapha Yoga", kind="lunar",
        condition=_any_flank_in_house_from_moon(12),
        effect=("Well-formed organs, majestic appearance, good reputation, "
                "polite, generous, self-respecting; renunciation in later life."),
        source=Citation("3HC", 1982)),   # planets in the 12th from the Moon
    YogaRecord(
        id="Y.DURUDHARA", name="Durudhara (Dhurdhura) Yoga", kind="lunar",
        condition=C.And(_any_flank_in_house_from_moon(2),
                        _any_flank_in_house_from_moon(12)),
        effect="Bountiful; blessed with much wealth and conveyances.",
        source=Citation("3HC", 2066)),   # planets on either side of the Moon
    YogaRecord(
        id="Y.CHANDRAMANGALA", name="Chandramangala Yoga", kind="lunar",
        # Definition: Mars conjoins the Moon (3HC:2272). Raman extends it to the
        # mutual aspect in a worked chart: "Here Mars and the Moon are mutually
        # aspecting. Hence Chandramangala Yoga is caused." (HTJAH-I:2908).
        condition=C.Or(C.Conjunct("Moon", "Mars"), C.MutualAspect("Moon", "Mars")),
        effect=("A powerful factor in stabilising one's financial worth "
                "(Raman's reading); classically: earnings through unscrupulous "
                "means."),
        source=Citation("3HC", 2272)),
    YogaRecord(
        id="Y.ADHI", name="Adhi Yoga", kind="lunar",
        # Full form: the benefics (Mercury, Jupiter, Venus — 3HC:2461-2463) all
        # situated in the 6th/7th/8th from the Moon, in any distribution
        # (3HC:2464-2466). HTJAH-I:15140 shows Raman grading partial forms.
        condition=C.And(*[
            C.Or(*[C.InHouseFrom(b, "MOON", n) for n in (6, 7, 8)])
            for b in _ADHI_BENEFICS]),
        effect=("Polite and trustworthy; enjoyable, happy life surrounded by "
                "luxuries and affluence; defeats enemies; healthy and "
                "long-lived. May be considered a Raja yoga or its equivalent."),
        source=Citation("3HC", 2442)),
    YogaRecord(
        id="Y.AMALA", name="Amala Yoga", kind="lunar",
        # "The 10th from the Moon or Lagna should be occupied by a benefic planet."
        condition=C.Or(C.ClassInHouseFrom("benefic", "MOON", {10}),
                       C.ClassInHouseFrom("benefic", "LAGNA", {10})),
        effect=("Lasting fame and reputation; spotless character; a prosperous "
                "life."),
        source=Citation("3HC", 3037)),

    # — arishta —
    YogaRecord(
        id="Y.KEMADRUMA", name="Kemadruma Yoga", kind="arishta",
        # No planets on either side of the Moon (3HC:2172-2174); the record
        # fires only while UNCANCELLED. Bhanga per 3HC:2182-2185 verbatim:
        # "if planets are [in] a kendra from birth or from the Moon or if the
        # Moon is in conjunction with a planet there is no Kemadruma". The
        # benefic-drishti-on-Moon branch inside kemadruma_bhanga is EXTENDED
        # doctrine (Phase-2 backfill), NOT from that line.
        condition=C.And(_Kemadruma(), C.Not(_KemadrumaBhanga())),
        effect=("Dirty, sorrowful, doing unrighteous deeds, poor, dependent, "
                "a rogue and a swindler."),
        source=Citation("3HC", 2172)),
    YogaRecord(
        id="Y.SAKATA", name="Sakata Yoga", kind="arishta",
        condition=C.Or(*[C.InHouseFrom("Moon", "Jupiter", n) for n in (6, 8, 12)]),
        effect=("Loses fortune and may regain it; ordinary and insignificant; "
                "poverty, privation and misery; stubborn, hated by relatives."),
        source=Citation("3HC", 2984)),   # Moon in 12th, 6th or 8th from Jupiter

    # — raja —
    YogaRecord(
        id="Y.RAJA.KT", name="Raja Yoga (kendra-trikona lords associated)",
        kind="raja",
        condition=_KendraTrikonaLordsConjoined(),
        effect=("Raja yoga: rise, political power, dignity — strongest when the "
                "9th and 10th lords combine (HTJAH-I:625-626)."),
        source=Citation("HTJAH-I", 622)),
    YogaRecord(
        id="Y.RAJA.910X",
        name="Raja Yoga (9th-10th lords exchanged or in each other's houses)",
        kind="raja",
        # HTJAH-I:630-632 prints THREE disjuncts: the 9th and 10th lords
        # exchanged; the 9th lord in the 10th; the 10th lord in the 9th.
        # Parivartana(9,10) true => LordIn(9,10) AND LordIn(10,9) (it is
        # exactly the two placements with distinct lords), so the Or of the
        # two LordIns already covers the exchange disjunct.
        condition=C.Or(C.LordIn(9, 10), C.LordIn(10, 9)),
        effect=("Each lord becomes a Raja yoga karaka; Raja yoga is caused "
                "(also when the 9th lord is in the 10th or the 10th in the 9th)."),
        source=Citation("HTJAH-I", 630)),
    YogaRecord(
        id="Y.RAJA.910A", name="Raja Yoga (9th-10th lords in mutual aspect)",
        kind="raja",
        condition=_LordsMutualAspect(9, 10),
        effect="The 9th and 10th lords fully aspecting each other confer Raja yoga.",
        source=Citation("HTJAH-I", 634)),
    YogaRecord(
        id="Y.VIPAREETA", name="Vipareeta Raja Yoga", kind="raja",
        # EXACTLY Raman's form: dusthana lords conjoined in a dusthana ->
        # prosperity (HTJAH-I:6302-6303; worked usage HTJAH-I:15864). No
        # Phaladeepika isolation clauses.
        condition=_DusthanaLordsConjoinedInDusthana(),
        effect=("Financial prosperity / Raja-yoga results during the periods of "
                "the dusthana lords so conjoined."),
        source=Citation("HTJAH-I", 6302)),

    # — dhana —
    YogaRecord(
        id="Y.DHANA.EXCH", name="Dhana Yoga (2nd-5th / 2nd-11th lords exchanged)",
        kind="dhana",
        condition=C.Or(C.Parivartana(2, 5), C.Parivartana(2, 11)),
        effect=("Financial prosperity in the periods and sub-periods of the "
                "lords so exchanged (corroborated at HTJAH-I:2447-2449: 2nd and "
                "11th lords interchanged make the person 'pretty rich')."),
        source=Citation("HTJAH-I", 2709)),
    YogaRecord(
        id="Y.DHANA.59", name="Dhana Yoga (5th and 9th lords in own houses)",
        kind="dhana",
        condition=C.And(C.LordIn(5, 5), C.LordIn(9, 9)),
        effect=("Financial prosperity in the periods of the 5th and 9th lords "
                "placed in the 5th and 9th respectively."),
        source=Citation("HTJAH-I", 2710)),
    YogaRecord(
        id="Y.DHANA.CHAIN", name="Dhana Yoga (1st-2nd-11th lord chain)",
        kind="dhana",
        # Reading note (HTJAH-I:2480-2481): "One acquires great wealth if lord
        # of Lagna is in the 2nd, the 2nd lord is in the 11th or 11th lord is
        # in Lagna." Ambiguous between a conjunctive chain (all three links,
        # the And reading some traditions use) and a disjunct list. The Or
        # reading is kept — it matches the printed English, where "or" joins
        # the final item of a plain list.
        condition=C.Or(C.LordIn(1, 2), C.LordIn(2, 11), C.LordIn(11, 1)),
        effect=("Acquires great wealth: lord of Lagna in the 2nd, the 2nd lord "
                "in the 11th, or the 11th lord in Lagna."),
        source=Citation("HTJAH-I", 2480)),

    # — dhana (3HC mining, B5 — additive coverage; the 1-2-11 cyclic chain and two
    #   specific 5th/11th-axis combinations Raman names; each feeds the H2/H11 dhana
    #   modulation + dhana-floor for real charts) —
    YogaRecord(
        id="Y.DHANA.BAHU", name="Bahudravyarjana Yoga (1-2-11 lord cyclic chain)",
        kind="dhana",
        # The CONJUNCTIVE chain (distinct from the disjunct Y.DHANA.CHAIN above): lagna lord
        # in the 2nd AND 2nd lord in the 11th AND 11th lord in the lagna -> earns much money.
        condition=C.And(C.LordIn(1, 2), C.LordIn(2, 11), C.LordIn(11, 1)),
        effect=("Earns much money and amasses good fortune (the lagna lord in the 2nd, "
                "the 2nd lord in the 11th, and the 11th lord in the lagna)."),
        source=Citation("3HC", 8184)),
    YogaRecord(
        id="Y.DHANA.122", name="Dhana Yoga (Venus-5th + Saturn-11th, a Venus 5th-sign)",
        kind="dhana",
        condition=C.And(_NthHouseSignOwnedBy(5, "Venus"),
                        C.InRashiHouse("Venus", 5), C.InRashiHouse("Saturn", 11)),
        effect=("Immense wealth: the 5th is a sign of Venus with Venus in the 5th and "
                "Saturn in the 11th."),
        source=Citation("3HC", 7632)),
    YogaRecord(
        id="Y.DHANA.125", name="Dhana Yoga (Sun own-5th + Moon & Jupiter 11th)",
        kind="dhana",
        condition=C.And(C.InRashiHouse("Sun", 5), C.HasDignity("Sun", {"own"}),
                        C.InRashiHouse("Moon", 11), C.InRashiHouse("Jupiter", 11)),
        effect=("Immense wealth: the Sun in the 5th identical with his own sign (Leo) "
                "and Jupiter and the Moon in the 11th (a Moon-Jupiter Gajakesari in gains)."),
        source=Citation("3HC", 7645)),
)


# ── detection API ────────────────────────────────────────────────────────────
def detect_yogas(chart: RamanChart) -> tuple[FiredYoga, ...]:
    """All encoded yogas active in `chart`, each carrying its corpus citation.

    A fresh ``EvalContext`` is shared across records so per-chart computations
    (functional nature, etc.) are memoised once.
    """
    ctx = C.EvalContext(chart)
    fired: list[FiredYoga] = []
    for rec in YOGAS:
        if rec.condition.evaluate(ctx):
            fired.append(FiredYoga(id=rec.id, name=rec.name, kind=rec.kind,
                                   effect=rec.effect, source=rec.source))
    logger.debug("detect_yogas: %d/%d fired", len(fired), len(YOGAS))
    return tuple(fired)


def has_yoga(chart: RamanChart, kind: YogaKind) -> bool:
    """True iff any encoded yoga of `kind` is active in `chart`. (Exposed here so
    conditions.py stays untouched; the orchestrator can wire IsRajaYoga/
    IsDhanaYoga/IsArishta predicates onto this later.)

    Raises ValueError when `kind` is not a member of the YogaKind Literal —
    the Literal is only a static hint, so the boundary is validated at runtime.
    """
    if kind not in _YOGA_KINDS:
        raise ValueError(
            f"unknown yoga kind {kind!r}; expected one of {sorted(_YOGA_KINDS)}")
    ctx = C.EvalContext(chart)
    return any(rec.kind == kind and rec.condition.evaluate(ctx) for rec in YOGAS)
