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
from app.raman_saab.primitives.dignity import dignity

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


# ── HPA-20 named-yoga leaf predicates (lords resolved at evaluate time) ───────
class _LordDignityInHouses(C.Condition):
    """The lord of `house` has a dignity in `states` AND (if `in_houses` given) occupies one."""

    def __init__(self, house: int, states: frozenset[str],
                 in_houses: frozenset[int] = frozenset()) -> None:
        self.house, self.states, self.in_houses = house, states, in_houses

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.primitives.dignity import dignity
        lord = _house_lord(self.house, ctx.chart)
        p = ctx.chart.planets.get(lord)
        if p is None or dignity(lord, ctx.chart) not in self.states:
            return False
        return (not self.in_houses) or p.rasi_house in self.in_houses


class _LordInHouses(C.Condition):
    """The lord of `house` occupies one of `in_houses` (whole-sign, from the Lagna)."""

    def __init__(self, house: int, in_houses: frozenset[int]) -> None:
        self.house, self.in_houses = house, in_houses

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _house_lord(self.house, ctx.chart)
        p = ctx.chart.planets.get(lord)
        return p is not None and p.rasi_house in self.in_houses


class _LordAspectedBy(C.Condition):
    """`aspector` casts a graha-aspect on the lord of `house`."""

    def __init__(self, house: int, aspector: str) -> None:
        self.house, self.aspector = house, aspector

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _house_lord(self.house, ctx.chart)
        return (lord in ctx.chart.planets
                and drishti.aspects_planet(self.aspector, lord, ctx.chart))


class _DispositorOfNthLordIs(C.Condition):
    """The dispositor of the `house`-lord — the lord of the sign that lord occupies — is
    `planet`. Backs Asatyavadi: 'the lord of the house occupied by the lord of the 2nd is
    Saturn' (HPA-20:225)."""

    def __init__(self, house: int, planet: str) -> None:
        self.house, self.planet = house, planet

    def evaluate(self, ctx: C.EvalContext) -> bool:
        p = ctx.chart.planets.get(_house_lord(self.house, ctx.chart))
        return p is not None and SIGN_LORDS[p.sign] == self.planet


class _PlanetSignModality(C.Condition):
    """`planet` occupies a sign of the given modality — movable / fixed / common (chara /
    sthira / dvisvabhava). Backs Kusuma's 'Venus in a fixed sign' (HPA-20:200)."""

    def __init__(self, planet: str, modality: str) -> None:
        self.planet, self.modality = planet, modality

    def evaluate(self, ctx: C.EvalContext) -> bool:
        p = ctx.chart.planets.get(self.planet)
        return p is not None and ("movable", "fixed", "common")[(p.sign - 1) % 3] == self.modality


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


class _Panchamahapurusha(C.Condition):
    """One of the five Mahapurusha yogas: the planet occupies a KENDRA (1/4/7/10 from the Lagna)
    that is identical with its OWN sign or EXALTATION sign (3HC:3434-3435, Hamsa: 'Jupiter should
    occupy a Kendra which should be his own house or exaltation sign'; the same form for the other
    four). Moolatrikona counts as own-sign occupancy."""

    def __init__(self, planet: str) -> None:
        self.planet = planet

    def evaluate(self, ctx: C.EvalContext) -> bool:
        p = ctx.chart.planets.get(self.planet)
        if p is None or p.rasi_house not in _KENDRAS:
            return False
        return dignity(self.planet, ctx.chart) in ("own", "moolatrikona", "exalt")


_SEVEN_VISIBLE: Final[tuple[str, ...]] = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
_NABHASA_BENEFICS: Final[frozenset[str]] = frozenset({"Jupiter", "Venus", "Mercury", "Moon"})
_NABHASA_MALEFICS: Final[frozenset[str]] = frozenset({"Sun", "Mars", "Saturn"})


def _seven_present(chart: RamanChart) -> list[str]:
    return [p for p in _SEVEN_VISIBLE if p in chart.planets]


class _SunFlank(C.Condition):
    """A planet OTHER than the Moon occupies the `n`-th house from the Sun (Sun-flank yogas: Vesi
    2nd, Vasi 12th) — the solar analogue of Sunapha/Anapha (3HC:3252-3388)."""

    def __init__(self, n: int) -> None:
        self.n = n

    def evaluate(self, ctx: C.EvalContext) -> bool:
        sun = ctx.chart.planets.get("Sun")
        if sun is None:
            return False
        target = ((sun.rasi_house - 1 + self.n - 1) % 12) + 1
        return any(nm not in ("Sun", "Moon", "Rahu", "Ketu") and p.rasi_house == target
                   for nm, p in ctx.chart.planets.items())


class _AsrayaModality(C.Condition):
    """All seven visible planets occupy signs of a SINGLE modality — movable (Rajju) / fixed (Musala)
    / common (Nala) (3HC:7088 'all the planets exclusively occupy movable, fixed or common signs')."""

    def __init__(self, modality: str) -> None:
        self.modality = modality

    def evaluate(self, ctx: C.EvalContext) -> bool:
        ps = _seven_present(ctx.chart)
        return len(ps) == 7 and all(
            ("movable", "fixed", "common")[(ctx.chart.planets[p].sign - 1) % 3] == self.modality
            for p in ps)


class _SankhyaSignCount(C.Condition):
    """The seven visible planets (nodes excepted) occupy exactly `n` distinct signs (the Sankhya
    count yogas: 7=Veena, 6=Damini, 5=Pasa, 4=Kedara, 3=Sula, 2=Yuga, 1=Gola; 3HC:6498-6868)."""

    def __init__(self, n: int) -> None:
        self.n = n

    def evaluate(self, ctx: C.EvalContext) -> bool:
        ps = _seven_present(ctx.chart)
        return len(ps) == 7 and len({ctx.chart.planets[p].sign for p in ps}) == self.n


class _DalaKendra(C.Condition):
    """The kendra-occupants are exclusively benefic (Mala) or exclusively malefic (Sarpa), with at
    least two of them there (3HC:3194 Mala 'benefics in kendras'; 3HC:7177 Sarpa 'malefics in
    kendras')."""

    def __init__(self, group: str) -> None:
        self.group = group

    def evaluate(self, ctx: C.EvalContext) -> bool:
        occ = [p for p in _seven_present(ctx.chart) if ctx.chart.planets[p].rasi_house in _KENDRAS]
        grp = _NABHASA_BENEFICS if self.group == "benefic" else _NABHASA_MALEFICS
        return len(occ) >= 2 and all(p in grp for p in occ)


class _AllSevenInHouses(C.Condition):
    """All seven visible planets are confined to the given set of houses (the Akriti shape yogas:
    contiguous blocks Yupa/Ishu/Sakti/Danda; odd-house Chakra; even-house Samudra; kendra Kamala;
    trine Sringhataka; etc.; 3HC:5761-6450)."""

    def __init__(self, houses: tuple[int, ...]) -> None:
        self.houses = frozenset(houses)

    def evaluate(self, ctx: C.EvalContext) -> bool:
        ps = _seven_present(ctx.chart)
        return len(ps) == 7 and all(ctx.chart.planets[p].rasi_house in self.houses for p in ps)


class _ShapeByClass(C.Condition):
    """Benefics confined to `benefic_houses` AND malefics to `malefic_houses` (Akriti Vajra: benefics
    in 1+7, malefics in 4+10; Yava: the reverse; 3HC:6172-6174). All seven planets must be present."""

    def __init__(self, benefic_houses: tuple[int, ...], malefic_houses: tuple[int, ...]) -> None:
        self.bh, self.mh = frozenset(benefic_houses), frozenset(malefic_houses)

    def evaluate(self, ctx: C.EvalContext) -> bool:
        ps = _seven_present(ctx.chart)
        if len(ps) != 7:
            return False
        for p in ps:
            allowed = self.bh if p in _NABHASA_BENEFICS else self.mh
            if ctx.chart.planets[p].rasi_house not in allowed:
                return False
        return True


def _contig(start: int, n: int = 7) -> tuple[int, ...]:
    """`n` contiguous houses starting at `start` (1-based, wrapping)."""
    return tuple(((start - 1 + i) % 12) + 1 for i in range(n))


class _AnchoredArc(C.Condition):
    """All seven planets confined to the n-contiguous-house arc from `start`, AND the arc is FULLY
    SPANNED (a planet in `start` and a planet in the last house) so it is EXACTLY n houses long and
    anchored — the precise Akriti contiguous form (Nava/Kuta/Chatra/Chapa, Ardha-Chandra). Without
    the anchor a loose 'all in a 7-house window' over-fires on ~40% of charts."""

    def __init__(self, start: int, n: int = 7) -> None:
        self.start = start
        self.houses = frozenset(_contig(start, n))
        self.last = ((start - 1 + n - 1) % 12) + 1

    def evaluate(self, ctx: C.EvalContext) -> bool:
        ps = _seven_present(ctx.chart)
        if len(ps) != 7:
            return False
        rh = {ctx.chart.planets[p].rasi_house for p in ps}
        return rh <= self.houses and self.start in rh and self.last in rh


_NAT_BENEFICS: Final[tuple[str, ...]] = ("Jupiter", "Venus", "Mercury")


class _Conjunct(C.Condition):
    """Two planets share a rasi house (conjunction)."""

    def __init__(self, a: str, b: str) -> None:
        self.a, self.b = a, b

    def evaluate(self, ctx: C.EvalContext) -> bool:
        pa, pb = ctx.chart.planets.get(self.a), ctx.chart.planets.get(self.b)
        return pa is not None and pb is not None and pa.rasi_house == pb.rasi_house


class _AllKendrasOccupied(C.Condition):
    """All four kendras (1/4/7/10) hold at least one planet (Chatussagara, 3HC:2613)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        occ = {p.rasi_house for p in ctx.chart.planets.values()}
        return all(k in occ for k in (1, 4, 7, 10))


class _BeneficsInUpachayas(C.Condition):
    """The natural benefics (Jupiter/Venus/Mercury) all occupy upachayas (3/6/10/11) reckoned from
    the Lagna OR all from the Moon (Vasumathi, 3HC:2708)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        if not all(b in chart.planets for b in _NAT_BENEFICS):
            return False
        moon = chart.planets.get("Moon")
        for ref in (chart.asc_sign, moon.rasi_house + chart.asc_sign - 1 if moon else None):
            if ref is None:
                continue
            base = ref if ref == chart.asc_sign else moon.rasi_house  # house-frame base
            upa = {((base - 1 + (u - 1)) % 12) + 1 for u in (3, 6, 10, 11)}
            if all(chart.planets[b].rasi_house in upa for b in _NAT_BENEFICS):
                return True
        return False


class _ParvataYoga(C.Condition):
    """Benefics disposed in the kendras (a benefic present and NO malefic in any kendra), and the 6th
    & 8th houses free of malefics (Parvata, 3HC:3170: 'benefics in kendras; 6th and 8th must be
    free')."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        malefics = ("Sun", "Mars", "Saturn", "Rahu", "Ketu")
        ben_in_kendra = any(chart.planets[b].rasi_house in (1, 4, 7, 10)
                            for b in _NABHASA_BENEFICS if b in chart.planets)
        no_malefic_kendra = not any(p.rasi_house in (1, 4, 7, 10)
                                    for n, p in chart.planets.items() if n in malefics)
        no_malefic_6_8 = not any(p.rasi_house in (6, 8)
                                 for n, p in chart.planets.items() if n in malefics)
        return ben_in_kendra and no_malefic_kendra and no_malefic_6_8


class _JayaYoga(C.Condition):
    """6th lord debilitated AND 10th lord exalted (Jaya, 3HC:5670)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        sixth, tenth = _house_lord(6, chart), _house_lord(10, chart)
        return (sixth in chart.planets and dignity(sixth, chart) == "debil"
                and tenth in chart.planets and dignity(tenth, chart) == "exalt")


class _DaridraYoga(C.Condition):
    """The 11th lord (the house of gains) occupies a dusthana — 6th, 8th or 12th — so gains are lost
    (Daridra / poverty yoga, 3HC:7289)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        p = ctx.chart.planets.get(_house_lord(11, ctx.chart))
        return p is not None and p.rasi_house in (6, 8, 12)


class _KendraFromLordOf(C.Condition):
    """`planet` sits in a kendra (1/4/7/10 whole-sign distance) counted FROM the lord of
    house `n` — the shape Brahma Yoga is built from (3HCH:1931)."""

    def __init__(self, planet: str, n: int) -> None:
        self.planet, self.n = planet, n

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _house_lord(self.n, ctx.chart)
        pp, pl = ctx.chart.planets.get(self.planet), ctx.chart.planets.get(lord)
        if pp is None or pl is None:
            return False
        dist = ((pp.rasi_house - pl.rasi_house) % 12) + 1
        return dist in _KENDRAS


class _LordOfHouseInHouseWith(C.Condition):
    """The lord of house `n` occupies whole-sign house `where`, conjoined (same house) with
    `companion` — Ravi Yoga's second clause (3HCH:1982)."""

    def __init__(self, n: int, where: int, companion: str) -> None:
        self.n, self.where, self.companion = n, where, companion

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = ctx.chart.planets.get(_house_lord(self.n, ctx.chart))
        comp = ctx.chart.planets.get(self.companion)
        return (lord is not None and comp is not None
                and lord.rasi_house == self.where
                and comp.rasi_house == self.where)


class _GauriNavamsaChain(C.Condition):
    """Gauri Yoga (3HCH:1637): the lord of the navamsa occupied by the 10th lord must join
    the 10th house, exalted, and conjoined with the lord of Lagna. One derived planet, three
    simultaneous demands — naturally rare, no strength proxy involved."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        chart = ctx.chart
        tenth_lord = chart.planets.get(_house_lord(10, chart))
        if tenth_lord is None:
            return False
        nav = getattr(tenth_lord, "navamsa_sign", None)
        y = chart.planets.get(SIGN_LORDS.get(nav)) if nav else None
        if y is None:
            return False
        if y.rasi_house != 10:
            return False
        if not C.HasDignity(y.name, "exalted").evaluate(ctx):
            return False
        lagna_lord = chart.planets.get(_house_lord(1, chart))
        return lagna_lord is not None and lagna_lord.rasi_house == y.rasi_house


class _LakshmiYoga(C.Condition):
    """Lakshmi Yoga per Raman's OWN 3HC wording (3HCH:1557), which resolves the comma-parse
    that deferred the HPA-20 form for months: the 9th lord "occupies own or exaltation sign
    IDENTICAL WITH a Kendra or Thrikona" — dignity AND placement, conjunctive — while the
    lord of Lagna is powerful.

    MEASURED before registering (2026-08-09, the deferral's own bar): geometric arm 26/225
    (11.6%) on the golden corpus; with the lagna-lord gate via `effective_strength` (the B1
    measure, band strong and not decisively weak) 12/225 (5.3%) — an order of magnitude
    tighter than the measured-common Shankha/Bheri pair (50%/38%)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.core.dignity import dignity_state
        from app.raman_saab.chart.constants import SIGN_LORDS
        from app.raman_saab.primitives.effective_strength import effective_strength
        chart = ctx.chart
        ninth_sign = ((chart.asc_sign - 1) + 8) % 12 + 1
        lord9 = chart.planets.get(SIGN_LORDS[ninth_sign])
        if lord9 is None:
            return False
        dig = dignity_state(lord9.name, lord9.sign)
        if dig not in ("own", "exalted", "moolatrikona"):
            return False
        if lord9.rasi_house not in {1, 4, 7, 10, 5, 9}:
            return False
        es = effective_strength(SIGN_LORDS[chart.asc_sign], chart)
        return getattr(es, "band", "") == "strong" and not getattr(es, "decisively_weak", False)


class _LordsAllInLagnaOrNeechamsa(C.Condition):
    """Netranasa Yoga (3HCC:5810): the lords of the 10th and 6th occupy Lagna with the 2nd
    lord — Raman's remark states it plainly, "the lords of the 2nd, 6th and 10th should all
    join the Lagna" — OR those lords stand in Neechamsa (debilitated navamsa)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.core.dignity import dignity_state
        chart = ctx.chart
        lords = [chart.planets.get(_house_lord(n, chart)) for n in (2, 6, 10)]
        if any(l is None for l in lords):
            return False
        if all(l.rasi_house == 1 for l in lords):
            return True
        pair = [chart.planets.get(_house_lord(n, chart)) for n in (10, 6)]
        return all(
            l is not None and getattr(l, "navamsa_sign", None)
            and dignity_state(l.name, l.navamsa_sign) == "debilitated"
            for l in pair)


class _NthLordInKendraAspectedByBenefic(C.Condition):
    """Sumukha's first arm (3HCC:5853, combination 166): the 2nd lord in a kendra, aspected
    by at least one natural benefic."""

    def __init__(self, n: int) -> None:
        self.n = n

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = _house_lord(self.n, ctx.chart)
        p = ctx.chart.planets.get(lord)
        if p is None or p.rasi_house not in _KENDRAS:
            return False
        from app.raman_saab.doctrine import drishti
        return any(b != lord and b in ctx.chart.planets
                   and drishti.aspects_planet(b, lord, ctx.chart)
                   for b in ("Jupiter", "Venus", "Mercury", "Moon"))


class _NthLordWithMaleficOrDebilitated(C.Condition):
    """Durmukha's 168 arm (3HCC:5878): the lord of house `n` joins an evil planet (same
    whole-sign house as a natural malefic) or stands debilitated."""

    def __init__(self, n: int) -> None:
        self.n = n

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.core.dignity import dignity_state
        lord = _house_lord(self.n, ctx.chart)
        p = ctx.chart.planets.get(lord)
        if p is None:
            return False
        if dignity_state(lord, p.sign) == "debilitated":
            return True
        return any(m != lord and (mp := ctx.chart.planets.get(m)) is not None
                   and mp.rasi_house == p.rasi_house
                   for m in ("Sun", "Mars", "Saturn", "Rahu", "Ketu"))


class _Sumukha167(C.Condition):
    """Sumukha's second printed arm (3HCC:5856, combination 167): the 2nd lord posited in a
    kendra which is his exaltation, own or friendly sign, AND the lord of that kendra sign
    attains Gopuramsa. Graduated 2026-08-09 when the varga-attainment primitive landed —
    rung 8 of Raman's GBB ladder, measured reachable for every planet over the shodasavarga
    (primitives/varga_attainment.py)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.core.dignity import dignity_state
        from app.raman_saab.chart.constants import SIGN_LORDS
        from app.raman_saab.primitives.relationships import naisargika
        from app.raman_saab.primitives.varga_attainment import attains_gopuramsa
        chart = ctx.chart
        lord2 = _house_lord(2, chart)
        p = chart.planets.get(lord2)
        if p is None or p.rasi_house not in _KENDRAS:
            return False
        dig = dignity_state(lord2, p.sign)
        friendly = naisargika(lord2, SIGN_LORDS[p.sign]) == "friend"
        if dig not in ("own", "exalted", "moolatrikona") and not friendly:
            return False
        kendra_lord = SIGN_LORDS[p.sign]
        return attains_gopuramsa(chart, kendra_lord)


class _MutualHouseExchange(C.Condition):
    """Parivartana between houses `a` and `b`: each lord stands in the other's house
    (whole-sign from Lagna) — Indra Yoga's spine (3HCH:1978)."""

    def __init__(self, a: int, b: int) -> None:
        self.a, self.b = a, b

    def evaluate(self, ctx: C.EvalContext) -> bool:
        la = ctx.chart.planets.get(_house_lord(self.a, ctx.chart))
        lb = ctx.chart.planets.get(_house_lord(self.b, ctx.chart))
        return (la is not None and lb is not None
                and la.rasi_house == self.b and lb.rasi_house == self.a)


class _MutualTrines(C.Condition):
    """Every pair of `planets` stands in trine (whole-sign distance 1/5/9) from each other —
    Trilochana Yoga (3HCH:2073)."""

    def __init__(self, planets: tuple[str, ...]) -> None:
        self.planets = planets

    def evaluate(self, ctx: C.EvalContext) -> bool:
        hs = []
        for name in self.planets:
            pl = ctx.chart.planets.get(name)
            if pl is None:
                return False
            hs.append(pl.rasi_house)
        return all(((hs[j] - hs[i]) % 12) + 1 in {1, 5, 9}
                   for i in range(len(hs)) for j in range(len(hs)) if i != j)


class _AllSevenInFifthFrom(C.Condition):
    """Kulavardhana (3HCH:2095): all seven planets in the 5th counted from `origin`
    ("Lagna", "Sun" or "Moon"). Nodes excluded, as everywhere Raman counts 'all planets'."""

    _SEVEN = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")

    def __init__(self, origin: str) -> None:
        self.origin = origin

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        if self.origin == "Lagna":
            seat = 1
        else:
            op = chart.planets.get(self.origin)
            if op is None:
                return False
            seat = op.rasi_house
        target = ((seat - 1) + 4) % 12 + 1
        return all((pl := chart.planets.get(n)) is not None and pl.rasi_house == target
                   for n in self._SEVEN)


class _VishnuChain(C.Condition):
    """Vishnu Yoga (3HCC:3495): the lord of the navamsa occupied by the 9th lord, AND the
    10th lord, join the 2nd house in conjunction with the 9th lord — three named planets
    together in the 2nd."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        chart = ctx.chart
        l9 = chart.planets.get(_house_lord(9, chart))
        l10 = chart.planets.get(_house_lord(10, chart))
        if l9 is None or l10 is None:
            return False
        nav = getattr(l9, "navamsa_sign", None)
        nd = chart.planets.get(SIGN_LORDS.get(nav)) if nav else None
        if nd is None:
            return False
        return l9.rasi_house == 2 and l10.rasi_house == 2 and nd.rasi_house == 2


class _GoYoga(C.Condition):
    """Go Yoga (3HCC:3787): STRONG Jupiter in his Moolatrikona with the 2nd lord, the lagna
    lord in exaltation. The strength gate rides `effective_strength` (the B1 measure) — the
    Lakshmi precedent, never the is_powerful proxy.

    DEFECT FIXED 2026-08-09: this condition originally tested
    ``dignity_state("Jupiter", sign) != "moolatrikona"`` — but ``dignity_state`` is
    sign-only and BY DESIGN never returns "moolatrikona" (the range is degree-dependent;
    see its docstring), so the gate ALWAYS refused and Y.GO was dead code whose
    liveness-never had been rationalized as rarity. The Moolatrikona test must be the
    longitude-aware ``is_moolatrikona`` (Jupiter: Sagittarius 0-10, lon 240-250)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.core.dignity import dignity_state, is_moolatrikona
        from app.raman_saab.chart.constants import SIGN_LORDS
        from app.raman_saab.primitives.effective_strength import effective_strength
        chart = ctx.chart
        jup = chart.planets.get("Jupiter")
        if jup is None or not is_moolatrikona("Jupiter", jup.lon):
            return False
        l2 = chart.planets.get(_house_lord(2, chart))
        if l2 is None or l2.rasi_house != jup.rasi_house:
            return False
        ll = chart.planets.get(SIGN_LORDS[chart.asc_sign])
        if ll is None or dignity_state(ll.name, ll.sign) != "exalted":
            return False
        es = effective_strength("Jupiter", chart)
        return getattr(es, "band", "") == "strong" and not getattr(es, "decisively_weak", False)


class _Vakchalana(C.Condition):
    """Vakchalana Yoga (3HCC:5991): a malefic owns the 2nd AND stands in a cruel navamsa
    (a navamsa sign owned by a malefic) AND the 2nd is devoid of benefic aspect or
    association."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        malefics = {"Sun", "Mars", "Saturn", "Rahu", "Ketu"}
        benefics = ("Jupiter", "Venus", "Mercury", "Moon")
        lord2 = _house_lord(2, chart)
        if lord2 not in malefics:
            return False
        p = chart.planets.get(lord2)
        nav = getattr(p, "navamsa_sign", None) if p else None
        if not nav or SIGN_LORDS[nav] not in malefics:
            return False
        occupants = [n for n, pl in chart.planets.items() if pl.rasi_house == 2]
        if any(b in occupants for b in benefics):
            return False
        return not any(drishti.aspects_house(b, 2, chart) for b in benefics
                       if b in chart.planets)


class _Vishaprayoga(C.Condition):
    """Vishaprayoga Yoga (3HCC:6003): the 2nd house joined AND aspected by malefics, and the
    2nd lord in a cruel navamsa aspected by a malefic."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        malefics = ("Sun", "Mars", "Saturn", "Rahu", "Ketu")
        if not any((pl := chart.planets.get(m)) is not None and pl.rasi_house == 2
                   for m in malefics):
            return False
        if not any(drishti.aspects_house(m, 2, chart) for m in malefics
                   if m in chart.planets):
            return False
        lord2 = _house_lord(2, chart)
        p = chart.planets.get(lord2)
        nav = getattr(p, "navamsa_sign", None) if p else None
        if not nav or SIGN_LORDS[nav] not in set(malefics):
            return False
        return any(m != lord2 and m in chart.planets
                   and drishti.aspects_planet(m, lord2, chart) for m in malefics)


class _Ekabhagini(C.Condition):
    """Ekabhagini Yoga (3HCC:6100): Mercury, the 3rd lord, and Mars join the 3rd house, the
    Moon, and Saturn RESPECTIVELY — a distributive triple."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        merc = chart.planets.get("Mercury")
        if merc is None or merc.rasi_house != 3:
            return False
        l3 = chart.planets.get(_house_lord(3, chart))
        moon = chart.planets.get("Moon")
        if l3 is None or moon is None or l3.rasi_house != moon.rasi_house:
            return False
        mars, sat = chart.planets.get("Mars"), chart.planets.get("Saturn")
        return mars is not None and sat is not None and mars.rasi_house == sat.rasi_house


class _DwadasaSahodara(C.Condition):
    """Dwadasa Sahodara Yoga (3HCC:6116): the 3rd lord in a kendra, and EXALTED Mars joins
    Jupiter in a trikona counted from the 3rd lord."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.core.dignity import dignity_state
        chart = ctx.chart
        l3 = chart.planets.get(_house_lord(3, chart))
        if l3 is None or l3.rasi_house not in _KENDRAS:
            return False
        mars, jup = chart.planets.get("Mars"), chart.planets.get("Jupiter")
        if mars is None or jup is None or mars.rasi_house != jup.rasi_house:
            return False
        if dignity_state("Mars", mars.sign) != "exalted":
            return False
        dist = ((mars.rasi_house - l3.rasi_house) % 12) + 1
        return dist in {1, 5, 9}


class _Parakrama(C.Condition):
    """Parakrama Yoga (3HCC:6194): the 3rd lord in a BENEFIC navamsa, aspected by (or
    conjoined with) benefic planets, and Mars in benefic signs."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        benefics = ("Jupiter", "Venus", "Mercury", "Moon")
        lord3 = _house_lord(3, chart)
        p3 = chart.planets.get(lord3)
        nav = getattr(p3, "navamsa_sign", None) if p3 else None
        if not nav or SIGN_LORDS[nav] not in set(benefics):
            return False
        touched = any(
            b != lord3 and (bp := chart.planets.get(b)) is not None
            and (bp.rasi_house == p3.rasi_house or drishti.aspects_planet(b, lord3, chart))
            for b in benefics)
        if not touched:
            return False
        mars = chart.planets.get("Mars")
        return mars is not None and SIGN_LORDS[mars.sign] in set(benefics)


class _Satkathadisravana(C.Condition):
    """Satkathadisravana Yoga (3HCC:6306): the 3rd house a benefic sign, aspected by
    benefics, and the 3rd lord in a benefic amsa."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        benefics = ("Jupiter", "Venus", "Mercury", "Moon")
        third_sign = ((chart.asc_sign - 1) + 2) % 12 + 1
        if SIGN_LORDS[third_sign] not in set(benefics):
            return False
        if not any(drishti.aspects_house(b, 3, chart) for b in benefics
                   if b in chart.planets):
            return False
        lord3 = _house_lord(3, chart)
        p3 = chart.planets.get(lord3)
        nav = getattr(p3, "navamsa_sign", None) if p3 else None
        return bool(nav) and SIGN_LORDS[nav] in set(benefics)


class _NthLordWithBeneficsInKendraTrikona(C.Condition):
    """Uttama Griha Yoga (3HCC:6320): the lord of house `n` joins benefics in a kendra or
    trikona — the lord conjoined with at least one benefic, standing in 1/4/7/10/5/9."""

    def __init__(self, n: int) -> None:
        self.n = n

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        lord = _house_lord(self.n, chart)
        p = chart.planets.get(lord)
        if p is None or p.rasi_house not in {1, 4, 7, 10, 5, 9}:
            return False
        return any(b != lord and (bp := chart.planets.get(b)) is not None
                   and bp.rasi_house == p.rasi_house
                   for b in ("Jupiter", "Venus", "Mercury", "Moon"))


class _FourPlanetConjunction4th10thSaturnMars(C.Condition):
    """Vichitra Saudha Prakara Yoga (3HCC:6358): the 4th and 10th lords conjoined, and the
    two together joining Saturn and Mars — Raman's own Remarks call it a four-planet
    conjunction."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        l4 = chart.planets.get(_house_lord(4, chart))
        l10 = chart.planets.get(_house_lord(10, chart))
        mars, sat = chart.planets.get("Mars"), chart.planets.get("Saturn")
        if any(x is None for x in (l4, l10, mars, sat)):
            return False
        seat = l4.rasi_house
        return all(x.rasi_house == seat for x in (l10, mars, sat))


_T5_BENEFICS = ("Jupiter", "Venus", "Mercury", "Moon")
_T5_MALEFICS = ("Sun", "Mars", "Saturn", "Rahu", "Ketu")


def _t5_afflicted(chart, planet_name: str) -> bool:
    """A malefic conjoins (same whole-sign house) or aspects ``planet_name``."""
    from app.raman_saab.doctrine import drishti
    target = chart.planets.get(planet_name)
    if target is None:
        return False
    for m in _T5_MALEFICS:
        if m == planet_name:
            continue
        mp = chart.planets.get(m)
        if mp is None:
            continue
        if mp.rasi_house == target.rasi_house:
            return True
        if drishti.aspects_planet(m, planet_name, chart):
            return True
    return False


class _AyatnaGriha189(C.Condition):
    """Ayatna Griha Prapta 189 (3HCC:6404): lords of Lagna and the 7th occupy Lagna or the
    4th, aspected by benefics — Raman's own Chart 87 counts ASSOCIATION as satisfying the
    benefic clause ("posited in the 4th in association with a benefic")."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        names = {SIGN_LORDS[chart.asc_sign], _house_lord(7, chart)}
        lords = [chart.planets.get(n) for n in names]
        if any(l is None or l.rasi_house not in {1, 4} for l in lords):
            return False
        for b in _T5_BENEFICS:
            if b in names or b not in chart.planets:
                continue
            bp = chart.planets[b]
            for l in lords:
                if bp.rasi_house == l.rasi_house or drishti.aspects_planet(b, l.name, chart):
                    return True
        return False


class _AyatnaGriha190(C.Condition):
    """Ayatna Griha Prapta 190 (3HCC:6406): 9th lord in a kendra, 4th lord in exaltation,
    Moolatrikona or own house. The Moolatrikona test is the longitude-aware
    ``is_moolatrikona`` (the Y.GO lesson: dignity_state never returns it)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.core.dignity import dignity_state, is_moolatrikona
        chart = ctx.chart
        l9 = chart.planets.get(_house_lord(9, chart))
        if l9 is None or l9.rasi_house not in _KENDRAS:
            return False
        l4 = chart.planets.get(_house_lord(4, chart))
        if l4 is None:
            return False
        return (dignity_state(l4.name, l4.sign) in ("exalted", "own")
                or is_moolatrikona(l4.name, l4.lon))


class _Grihanasa191(C.Condition):
    """Grihanasa 191 (3HCC:6435): the printed definition says "the 12th", but Raman's own
    Remarks correct it — "the 12th FROM THE 4TH and not from Lagna", i.e. the 3rd house.
    Encoded per the Remarks: 4th lord in the 3rd, aspected by a malefic."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        l4 = chart.planets.get(_house_lord(4, chart))
        if l4 is None or l4.rasi_house != 3:
            return False
        return any(m != l4.name and m in chart.planets
                   and drishti.aspects_planet(m, l4.name, chart) for m in _T5_MALEFICS)


class _Grihanasa192(C.Condition):
    """Grihanasa 192 (3HCC:6437): the lord of the navamsa occupied by the 4th lord is
    disposed in the 3rd (the same 12th-from-the-4th correction, stated in the Remarks:
    "either the lord of the 4th OR the lord of the navamsa occupied by the 4th is
    situated in the 3rd")."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        chart = ctx.chart
        l4 = chart.planets.get(_house_lord(4, chart))
        nav = getattr(l4, "navamsa_sign", None) if l4 else None
        nd = chart.planets.get(SIGN_LORDS.get(nav)) if nav else None
        return nd is not None and nd.rasi_house == 3


class _BandhuPujya193(C.Condition):
    """Bandhu Pujya 193 (3HCC:6459): the BENEFIC lord of the 4th aspected by another
    benefic, Mercury in Lagna. Raman's Remarks limit it to lagnas whose 4th lord is a
    natural benefic (Mesha, Mithuna, Kataka, Dhanus, Meena) — the natural-benefic check
    encodes exactly that."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        lord4 = _house_lord(4, chart)
        if lord4 not in set(_T5_BENEFICS):
            return False
        merc = chart.planets.get("Mercury")
        if merc is None or merc.rasi_house != 1:
            return False
        return any(b != lord4 and b in chart.planets
                   and drishti.aspects_planet(b, lord4, chart) for b in _T5_BENEFICS)


class _BandhuPujya194(C.Condition):
    """Bandhu Pujya 194 (3HCC:6462): the 4th house OR the 4th lord has the association or
    aspect of Jupiter (Raman's Gandhi remark applies both at once)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        jup = chart.planets.get("Jupiter")
        if jup is None:
            return False
        if jup.rasi_house == 4 or drishti.aspects_house("Jupiter", 4, chart):
            return True
        l4 = chart.planets.get(_house_lord(4, chart))
        if l4 is None or l4.name == "Jupiter":
            return False
        return (jup.rasi_house == l4.rasi_house
                or drishti.aspects_planet("Jupiter", l4.name, chart))


class _Matrugami(C.Condition):
    """Matrugami Yoga (3HCC:6666): the Moon or Venus in a kendra conjoined with or
    aspected by a malefic, AND an evil planet in the 4th house."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        if not any((mp := chart.planets.get(m)) is not None and mp.rasi_house == 4
                   for m in _T5_MALEFICS):
            return False
        for name in ("Moon", "Venus"):
            pl = chart.planets.get(name)
            if pl is not None and pl.rasi_house in _KENDRAS and _t5_afflicted(chart, name):
                return True
        return False


class _Kapata202(C.Condition):
    """Kapata 202 (3HCC:6711): a malefic in the 4th, and the 4th lord associated with,
    aspected by, or hemmed in between malefics (papakartari on the lord's house)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        if not any((mp := chart.planets.get(m)) is not None and mp.rasi_house == 4
                   for m in _T5_MALEFICS):
            return False
        lord4 = _house_lord(4, chart)
        l4 = chart.planets.get(lord4)
        if l4 is None:
            return False
        if _t5_afflicted(chart, lord4):
            return True
        prev_h = (l4.rasi_house - 2) % 12 + 1
        next_h = l4.rasi_house % 12 + 1
        def _malefic_in(h: int) -> bool:
            return any((mp := chart.planets.get(m)) is not None and mp.rasi_house == h
                       for m in _T5_MALEFICS)
        return _malefic_in(prev_h) and _malefic_in(next_h)


class _Kapata203(C.Condition):
    """Kapata 203 (3HCC:6715): Saturn, Mars, Rahu AND the malefic 10th lord all in the
    4th, the 10th lord aspected by malefics."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        for m in ("Saturn", "Mars", "Rahu"):
            mp = chart.planets.get(m)
            if mp is None or mp.rasi_house != 4:
                return False
        lord10 = _house_lord(10, chart)
        if lord10 not in set(_T5_MALEFICS):
            return False
        l10 = chart.planets.get(lord10)
        if l10 is None or l10.rasi_house != 4:
            return False
        return any(m != lord10 and m in chart.planets
                   and drishti.aspects_planet(m, lord10, chart) for m in _T5_MALEFICS)


class _MatruSatrutwa(C.Condition):
    """Matru Satrutwa Yoga (3HCC:6798): Mercury as lord of Lagna AND the 4th (Raman's
    Remarks: only Mithuna Lagna), joined with or aspected by a malefic."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        if chart.asc_sign != 3:
            return False
        return _t5_afflicted(chart, "Mercury")


class _Vahana209(C.Condition):
    """Vahana 209 (3HCC:6830): the lord of Lagna joins the 4th, 11th or the 9th."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        l1 = ctx.chart.planets.get(SIGN_LORDS[ctx.chart.asc_sign])
        return l1 is not None and l1.rasi_house in {4, 9, 11}


class _Vahana210(C.Condition):
    """Vahana 210 (3HCC:6832): the 4th lord exalted, and the lord of the exaltation sign
    (its dispositor) in a kendra or trikona."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.core.dignity import dignity_state
        from app.raman_saab.chart.constants import SIGN_LORDS
        chart = ctx.chart
        l4 = chart.planets.get(_house_lord(4, chart))
        if l4 is None or dignity_state(l4.name, l4.sign) != "exalted":
            return False
        disp = chart.planets.get(SIGN_LORDS[l4.sign])
        return disp is not None and disp.rasi_house in {1, 4, 7, 10, 5, 9}


def _t6_b1_strong(chart, planet: str) -> bool:
    """The B1 strength reading (Lakshmi/Go precedent): band strong AND not decisively weak."""
    from app.raman_saab.primitives.effective_strength import effective_strength
    es = effective_strength(planet, chart)
    return getattr(es, "band", "") == "strong" and not getattr(es, "decisively_weak", False)


class _Matrudeerghayur196(C.Condition):
    """Matrudeerghayur 196 (3HCC:6535): a benefic in the 4th, the 4th lord exalted, and the
    Moon STRONG — the strength clause rides B1 effective_strength."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.core.dignity import dignity_state
        chart = ctx.chart
        if not any((bp := chart.planets.get(b)) is not None and bp.rasi_house == 4
                   for b in _T5_BENEFICS):
            return False
        l4 = chart.planets.get(_house_lord(4, chart))
        if l4 is None or dignity_state(l4.name, l4.sign) != "exalted":
            return False
        return _t6_b1_strong(chart, "Moon")


class _Matrudeerghayur197(C.Condition):
    """Matrudeerghayur 197 (3HCC:6538): the lord of the navamsa occupied by the 4th lord is
    STRONG and stands in a kendra from Lagna AS WELL AS from Chandra Lagna."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        chart = ctx.chart
        l4 = chart.planets.get(_house_lord(4, chart))
        nav = getattr(l4, "navamsa_sign", None) if l4 else None
        nd = chart.planets.get(SIGN_LORDS.get(nav)) if nav else None
        moon = chart.planets.get("Moon")
        if nd is None or moon is None:
            return False
        if nd.rasi_house not in _KENDRAS:
            return False
        from_moon = ((nd.rasi_house - moon.rasi_house) % 12) + 1
        if from_moon not in {1, 4, 7, 10}:
            return False
        return _t6_b1_strong(chart, nd.name)


class _Matrunasa198(C.Condition):
    """Matrunasa 198 (3HCC:6554): the Moon hemmed in between (Papakartari), associated
    with, OR aspected by evil planets — Raman: "One of the three conditions must
    prevail". Papakartari = a malefic in each house adjacent to the Moon's."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        moon = chart.planets.get("Moon")
        if moon is None:
            return False
        if _t5_afflicted(chart, "Moon"):
            return True
        prev_h = (moon.rasi_house - 2) % 12 + 1
        next_h = moon.rasi_house % 12 + 1
        def _malefic_in(h: int) -> bool:
            return any((mp := chart.planets.get(m)) is not None and mp.rasi_house == h
                       for m in _T5_MALEFICS)
        return _malefic_in(prev_h) and _malefic_in(next_h)


class _Matrunasa199(C.Condition):
    """Matrunasa 199 (3HCC:6559), encoded to Raman's own worked procedure (charts 90/91):
    (a) the 4th lord occupies some navamsa; (b) that navamsa's lord occupies some navamsa;
    (c) THAT navamsa's lord stands, in the Rasi chart, in the 6th, 8th or 12th from Lagna.
    Chart 90 shows the self-dispositor collapse ("the third condition becomes merged with
    the 2nd") — the chain handles it without special-casing."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        chart = ctx.chart
        l4 = chart.planets.get(_house_lord(4, chart))
        nav1 = getattr(l4, "navamsa_sign", None) if l4 else None
        x = chart.planets.get(SIGN_LORDS.get(nav1)) if nav1 else None
        nav2 = getattr(x, "navamsa_sign", None) if x else None
        z = chart.planets.get(SIGN_LORDS.get(nav2)) if nav2 else None
        return z is not None and z.rasi_house in {6, 8, 12}


class _Nishkapata205(C.Condition):
    """Nishkapata 205 (3HCC:6767): the 4th occupied by a benefic, OR by a planet in
    exaltation, friendly or own house, OR the 4th a benefic sign. Raman's own remark
    ("very flexible... given for what they are worth") is on the record."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.core.dignity import dignity_state
        from app.raman_saab.chart.constants import SIGN_LORDS
        chart = ctx.chart
        # the benefic-sign arm is a lagna-only fact — without the planet guard it fires
        # on an EMPTY chart, which the detection contract forbids
        if not chart.planets:
            return False
        fourth_sign = ((chart.asc_sign - 1) + 3) % 12 + 1
        if SIGN_LORDS[fourth_sign] in set(_T5_BENEFICS):
            return True
        for name, pl in chart.planets.items():
            if pl.rasi_house != 4:
                continue
            if name in _T5_BENEFICS:
                return True
            if dignity_state(name, pl.sign) in ("exalted", "own", "friendly"):
                return True
        return False


class _MatruSneha(C.Condition):
    """Matru Sneha Yoga (3HCC:6812): the 1st and 4th houses share a lord (Mithuna and
    Dhanus, per Raman's Remarks), OR the two lords are natural or TEMPORAL (Tatkalika)
    friends, OR both lords are aspected by benefics. Mutuality is required for the
    friendship arms (Raman: "mutual friends or Tatkalika friends")."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.core.dignity import naisargika_relation, temporal_relation
        from app.raman_saab.chart.constants import SIGN_LORDS
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        n1, n4 = SIGN_LORDS[chart.asc_sign], _house_lord(4, chart)
        if n1 == n4:
            return True
        p1, p4 = chart.planets.get(n1), chart.planets.get(n4)
        if p1 is None or p4 is None:
            return False
        if (naisargika_relation(n1, n4) == "friend"
                and naisargika_relation(n4, n1) == "friend"):
            return True
        signs = {name: {"sign": pl.sign} for name, pl in chart.planets.items()}
        if (temporal_relation(signs, n1, n4) == "friend"
                and temporal_relation(signs, n4, n1) == "friend"):
            return True
        def _benefic_touched(lord_name: str, lord) -> bool:
            return any(b != lord_name and (bp := chart.planets.get(b)) is not None
                       and (bp.rasi_house == lord.rasi_house
                            or drishti.aspects_planet(b, lord_name, chart))
                       for b in _T5_BENEFICS)
        return _benefic_touched(n1, p1) and _benefic_touched(n4, p4)


class _Anapathya(C.Condition):
    """Anapathya Yoga (3HCC:6872): Jupiter and the lords of Lagna, the 7th and the 5th all
    WEAK. Weakness is B1 ``decisively_weak`` — the mirror of the Lakshmi/Go strong gate;
    Raman's modifying remark (strong Jupiter/5th lord softens the yoga) is carried by the
    conjunctive ALL-four requirement."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        from app.raman_saab.primitives.effective_strength import effective_strength
        chart = ctx.chart
        names = {"Jupiter", SIGN_LORDS[chart.asc_sign],
                 _house_lord(7, chart), _house_lord(5, chart)}
        for n in names:
            if n not in chart.planets:
                return False
            if not getattr(effective_strength(n, chart), "decisively_weak", False):
                return False
        return True


def _t7_papakartari(chart, house: int) -> bool:
    """A malefic in each whole-sign house adjacent to ``house``."""
    prev_h = (house - 2) % 12 + 1
    next_h = house % 12 + 1
    def _malefic_in(h: int) -> bool:
        return any((mp := chart.planets.get(m)) is not None and mp.rasi_house == h
                   for m in _T5_MALEFICS)
    return _malefic_in(prev_h) and _malefic_in(next_h)


class _Sarpasapa212(C.Condition):
    """Sarpasapa 212 (3HCC:6891), per Raman's Remarks disambiguation: EITHER Rahu in the
    5th aspected by Mars, OR the 5th sign being Aries/Scorpio (Kataka and Dhanus lagnas)
    with Rahu's association."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        rahu = chart.planets.get("Rahu")
        if rahu is None or rahu.rasi_house != 5:
            return False
        fifth_sign = ((chart.asc_sign - 1) + 4) % 12 + 1
        if fifth_sign in {1, 8}:
            return True
        return drishti.aspects_planet("Mars", "Rahu", chart)


class _Sarpasapa213(C.Condition):
    """Sarpasapa 213 (3HCC:6894): the 5th lord conjunct Rahu, Saturn in the 5th aspected
    by or associated with the Moon."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        l5 = chart.planets.get(_house_lord(5, chart))
        rahu = chart.planets.get("Rahu")
        if l5 is None or rahu is None or l5.rasi_house != rahu.rasi_house:
            return False
        sat, moon = chart.planets.get("Saturn"), chart.planets.get("Moon")
        if sat is None or moon is None or sat.rasi_house != 5:
            return False
        return (moon.rasi_house == 5
                or drishti.aspects_planet("Moon", "Saturn", chart))


class _Sarpasapa214(C.Condition):
    """Sarpasapa 214 (3HCC:6897): Jupiter (putrakaraka) with Mars, Rahu in Lagna, the 5th
    lord in a dusthana — AND Raman's own nullifier from the Remarks encoded: "if he
    [Jupiter] has sufficient Shadbala strength, the yoga becomes null and void" (his
    worked example: ~8 rupas -> defunct). The gate is NOT-B1-strong."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        jup, mars = chart.planets.get("Jupiter"), chart.planets.get("Mars")
        if jup is None or mars is None or jup.rasi_house != mars.rasi_house:
            return False
        rahu = chart.planets.get("Rahu")
        if rahu is None or rahu.rasi_house != 1:
            return False
        l5 = chart.planets.get(_house_lord(5, chart))
        if l5 is None or l5.rasi_house not in {6, 8, 12}:
            return False
        return not _t6_b1_strong(chart, "Jupiter")


class _Sarpasapa215(C.Condition):
    """Sarpasapa 215 (3HCC:6900): the 5th a sign of Mars, conjoined by Rahu, aspected by
    or associated with Mercury."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        fifth_sign = ((chart.asc_sign - 1) + 4) % 12 + 1
        if fifth_sign not in {1, 8}:
            return False
        rahu = chart.planets.get("Rahu")
        if rahu is None or rahu.rasi_house != 5:
            return False
        merc = chart.planets.get("Mercury")
        if merc is None:
            return False
        return (merc.rasi_house == 5
                or drishti.aspects_planet("Mercury", "Rahu", chart))


class _PitrusapaSutakshaya(C.Condition):
    """Pitrusapa Sutakshaya 216 (3HCC:7013), Raman's three-way disambiguation from the
    Remarks: the Sun in the 5th house AND (debilitated, OR in the amsas of Makara/Kumbha,
    OR hemmed in between malefics)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.core.dignity import dignity_state
        chart = ctx.chart
        sun = chart.planets.get("Sun")
        if sun is None or sun.rasi_house != 5:
            return False
        if dignity_state("Sun", sun.sign) == "debilitated":
            return True
        if getattr(sun, "navamsa_sign", None) in (10, 11):
            return True
        return _t7_papakartari(chart, 5)


class _MatrusapaSutakshaya(C.Condition):
    """Matrusapa Sutakshaya 217 (3HCC:7155): Parivartana between the 5th and 8th lords
    (8th lord in the 5th, 5th lord in the 8th), the Moon AND the 4th lord in the 6th.
    Raman: cannot operate for Simha/Kumbha (one planet owns both houses) — the geometry
    excludes them without a special case."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        l8 = chart.planets.get(_house_lord(8, chart))
        l5 = chart.planets.get(_house_lord(5, chart))
        if l8 is None or l5 is None or l8.rasi_house != 5 or l5.rasi_house != 8:
            return False
        moon = chart.planets.get("Moon")
        l4 = chart.planets.get(_house_lord(4, chart))
        return (moon is not None and l4 is not None
                and moon.rasi_house == 6 and l4.rasi_house == 6)


class _BhratrusapaSutakshaya(C.Condition):
    """Bhratrusapa Sutakshaya 218 (3HCC:7200): the lords of Lagna and the 5th in the 8th,
    the 3rd lord combining with Mars and Rahu in the 5th."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        chart = ctx.chart
        l1 = chart.planets.get(SIGN_LORDS[chart.asc_sign])
        l5 = chart.planets.get(_house_lord(5, chart))
        if l1 is None or l5 is None or l1.rasi_house != 8 or l5.rasi_house != 8:
            return False
        l3 = chart.planets.get(_house_lord(3, chart))
        mars, rahu = chart.planets.get("Mars"), chart.planets.get("Rahu")
        return all(x is not None and x.rasi_house == 5 for x in (l3, mars, rahu))


class _Pretasapa(C.Condition):
    """Pretasapa 219 (3HCC:7219): the Sun and Saturn in the 5th, WEAK Moon in the 7th,
    Rahu in Lagna, Jupiter in the 12th. "Weak" rides B1 ``decisively_weak`` — the same
    reading as Anapathya; Raman does not define the term here and B1 is the project's
    accepted weakness measure."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.primitives.effective_strength import effective_strength
        chart = ctx.chart
        pos = {"Sun": 5, "Saturn": 5, "Moon": 7, "Rahu": 1, "Jupiter": 12}
        for name, house in pos.items():
            pl = chart.planets.get(name)
            if pl is None or pl.rasi_house != house:
                return False
        return getattr(effective_strength("Moon", chart), "decisively_weak", False)


class _Bahuputra220(C.Condition):
    """Bahuputra 220 (3HCC:7285): Rahu in the 5th in a navamsa OTHER than Saturn's —
    Raman: the exception to the rule that Rahu in the 5th is harmful."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        rahu = ctx.chart.planets.get("Rahu")
        if rahu is None or rahu.rasi_house != 5:
            return False
        nav = getattr(rahu, "navamsa_sign", None)
        return nav is not None and SIGN_LORDS[nav] != "Saturn"


class _Bahuputra221(C.Condition):
    """Bahuputra 221 (3HCC:7288), per Raman's own untangling and Chart 100: some planet
    associates with the 7th lord; the lord of the navamsa THAT PLANET occupies stands in
    the 1st, 2nd or 5th house."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        chart = ctx.chart
        l7name = _house_lord(7, chart)
        l7 = chart.planets.get(l7name)
        if l7 is None:
            return False
        for name, pl in chart.planets.items():
            if name == l7name or pl.rasi_house != l7.rasi_house:
                continue
            nav = getattr(pl, "navamsa_sign", None)
            nd = chart.planets.get(SIGN_LORDS.get(nav)) if nav else None
            if nd is not None and nd.rasi_house in {1, 2, 5}:
                return True
        return False


class _Dattaputra222(C.Condition):
    """Dattaputra 222 (3HCC:7341): Mars AND Saturn in the 5th; the Lagna lord in a sign of
    Mercury, aspected by or associated with Mercury."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        mars, sat = chart.planets.get("Mars"), chart.planets.get("Saturn")
        if mars is None or sat is None or mars.rasi_house != 5 or sat.rasi_house != 5:
            return False
        l1name = SIGN_LORDS[chart.asc_sign]
        l1 = chart.planets.get(l1name)
        if l1 is None or l1.sign not in {3, 6}:
            return False
        if l1name == "Mercury":
            return True
        merc = chart.planets.get("Mercury")
        if merc is None:
            return False
        return (merc.rasi_house == l1.rasi_house
                or drishti.aspects_planet("Mercury", l1name, chart))


class _Dattaputra223(C.Condition):
    """Dattaputra 223 (3HCC:7345): the 7th lord in the 11th, the 5th lord joining a
    benefic, the 5th occupied by Mars or Saturn — Chart 101's shape."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        l7 = chart.planets.get(_house_lord(7, chart))
        if l7 is None or l7.rasi_house != 11:
            return False
        l5name = _house_lord(5, chart)
        l5 = chart.planets.get(l5name)
        if l5 is None:
            return False
        if not any(b != l5name and (bp := chart.planets.get(b)) is not None
                   and bp.rasi_house == l5.rasi_house for b in _T5_BENEFICS):
            return False
        return any((mp := chart.planets.get(m)) is not None and mp.rasi_house == 5
                   for m in ("Mars", "Saturn"))


class _Aputra(C.Condition):
    """Aputra 224 (3HCC:7388): the 5th lord in a dusthana. The printed Remarks read
    "Dusthanas are the 5th, 8th and 12th" — an OCR garble of the classical 6/8/12 (the
    5th lord IN the 5th is own-house, the opposite of a dusthana; Raman's own 214 spells
    the same trio as 6th/8th/12th). Encoded 6/8/12."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        l5 = ctx.chart.planets.get(_house_lord(5, ctx.chart))
        return l5 is not None and l5.rasi_house in {6, 8, 12}


class _Ekaputra(C.Condition):
    """Ekaputra 225 (3HCC:7423): the 5th lord in a kendra or trikona. Broad as printed —
    Raman's own Remarks caution that these 5th-house yogas "cannot be applied verbatim"."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        l5 = ctx.chart.planets.get(_house_lord(5, ctx.chart))
        return l5 is not None and l5.rasi_house in {1, 4, 7, 10, 5, 9}


class _KalanirdesatPutra227(C.Condition):
    """Kalanirdesat Putra 227 (3HCC:7466): Jupiter in the 5th, the 5th lord in
    conjunction with Venus. When Venus IS the 5th lord (Mithuna/Makara lagnas) the
    conjunction clause is degenerate — treated as unsatisfied (strict under-fire, never
    a generous over-fire)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        jup = chart.planets.get("Jupiter")
        if jup is None or jup.rasi_house != 5:
            return False
        l5name = _house_lord(5, chart)
        l5 = chart.planets.get(l5name)
        ven = chart.planets.get("Venus")
        if l5 is None or ven is None or l5name == "Venus":
            return False
        return l5.rasi_house == ven.rasi_house


class _KalanirdesatPutra228(C.Condition):
    """Kalanirdesat Putra 228 (3HCC:7468): Jupiter in the 9th, Venus in the 9th from
    Jupiter (Raman's own simplification: the 5th from Lagna) in conjunction with the
    Lagna lord."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        chart = ctx.chart
        jup = chart.planets.get("Jupiter")
        if jup is None or jup.rasi_house != 9:
            return False
        ven = chart.planets.get("Venus")
        if ven is None or ((ven.rasi_house - jup.rasi_house) % 12) + 1 != 9:
            return False
        # Venus-lagna charts (Vrishabha/Thula) make the Venus-conjunct-Lagna-lord clause
        # degenerate — unsatisfied, same strict rule as 227.
        l1name = SIGN_LORDS[chart.asc_sign]
        if l1name == "Venus":
            return False
        l1 = chart.planets.get(l1name)
        return l1 is not None and l1.rasi_house == ven.rasi_house


class _KalanirdesatPutranasa229(C.Condition):
    """Kalanirdesat Putranasa 229 (3HCC:7487): Rahu in the 5th, the 5th lord conjunct a
    malefic, Jupiter debilitated — Raman: all three factors of the house of children
    (house, lord, karaka) afflicted at once."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.core.dignity import dignity_state
        chart = ctx.chart
        rahu = chart.planets.get("Rahu")
        if rahu is None or rahu.rasi_house != 5:
            return False
        jup = chart.planets.get("Jupiter")
        if jup is None or dignity_state("Jupiter", jup.sign) != "debilitated":
            return False
        l5name = _house_lord(5, chart)
        l5 = chart.planets.get(l5name)
        if l5 is None:
            return False
        return any(m != l5name and (mp := chart.planets.get(m)) is not None
                   and mp.rasi_house == l5.rasi_house for m in _T5_MALEFICS)


class _KalanirdesatPutranasa230(C.Condition):
    """Kalanirdesat Putranasa 230 (3HCC:7494): malefics in the 5th from Jupiter AND from
    Lagna."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        jup = chart.planets.get("Jupiter")
        if jup is None:
            return False
        fifth_from_jup = ((jup.rasi_house - 1) + 4) % 12 + 1
        def _malefic_in(h: int) -> bool:
            return any((mp := chart.planets.get(m)) is not None and mp.rasi_house == h
                       for m in _T5_MALEFICS)
        return _malefic_in(5) and _malefic_in(fifth_from_jup)


class _Buddhimaturya(C.Condition):
    """Buddhimaturya 231 (3HCC:7544): the printed definition (a BENEFIC 5th lord aspected
    by another benefic or in a benefic sign) Or Raman's own Remarks extension for the five
    lagnas the definition excludes ("the yoga may be deemed present in case the 5th
    house... is occupied by benefics and the 5th lord is in association with" the
    benefics) — both his, both encoded."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        l5name = _house_lord(5, chart)
        l5 = chart.planets.get(l5name)
        if l5 is None:
            return False
        if l5name in set(_T5_BENEFICS):
            if SIGN_LORDS[l5.sign] in set(_T5_BENEFICS):
                return True
            if any(b != l5name and b in chart.planets
                   and drishti.aspects_planet(b, l5name, chart) for b in _T5_BENEFICS):
                return True
        occupied = any((bp := chart.planets.get(b)) is not None and bp.rasi_house == 5
                       for b in _T5_BENEFICS)
        conj = any(b != l5name and (bp := chart.planets.get(b)) is not None
                   and bp.rasi_house == l5.rasi_house for b in _T5_BENEFICS)
        return occupied and conj


class _Theevrabuddhi(C.Condition):
    """Theevrabuddhi 232 (3HCC:7625), encoded to Raman's own CORRECTION: the lord of the
    navamsa occupied by the 5th lord aspected by (or, per his extension, conjoined with) a
    benefic. The definition's second clause — that the 5th lord himself be a benefic — is
    the clause Raman explicitly rejects ("the suggestion... is not warranted... irrespective
    of his being a natural malefic or natural benefic"), and it is deliberately absent."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        l5 = chart.planets.get(_house_lord(5, chart))
        nav = getattr(l5, "navamsa_sign", None) if l5 else None
        ndname = SIGN_LORDS.get(nav) if nav else None
        nd = chart.planets.get(ndname) if ndname else None
        if nd is None:
            return False
        return any(b != ndname and (bp := chart.planets.get(b)) is not None
                   and (bp.rasi_house == nd.rasi_house
                        or drishti.aspects_planet(b, ndname, chart))
                   for b in _T5_BENEFICS)


class _BuddhiJada(C.Condition):
    """Buddhi Jada 233 (3HCC:7657): the Lagna lord conjoined with or aspected by evil
    planets, Saturn in the 5th, and the Lagna lord aspected by Saturn."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        sat = chart.planets.get("Saturn")
        if sat is None or sat.rasi_house != 5:
            return False
        l1name = SIGN_LORDS[chart.asc_sign]
        if not _t5_afflicted(chart, l1name):
            return False
        return (l1name != "Saturn"
                and drishti.aspects_planet("Saturn", l1name, chart))


class _PutraSukha(C.Condition):
    """Putra Sukha 235 (3HCC:7787): Jupiter AND Venus in the 5th, or Mercury in the 5th,
    or the 5th a benefic sign occupied by benefics."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        chart = ctx.chart
        def _in5(name: str) -> bool:
            pl = chart.planets.get(name)
            return pl is not None and pl.rasi_house == 5
        if _in5("Jupiter") and _in5("Venus"):
            return True
        if _in5("Mercury"):
            return True
        fifth_sign = ((chart.asc_sign - 1) + 4) % 12 + 1
        return (SIGN_LORDS[fifth_sign] in set(_T5_BENEFICS)
                and any(_in5(b) for b in _T5_BENEFICS))


class _Jara(C.Condition):
    """Jara 236 (3HCC:7805): the 10th occupied by the lords of the 10th, 2nd and 7th —
    NARROWED per Raman's own Remarks, which refuse the sages' bare form: "unless the 7th
    lord happens to be Mars or Venus... it is not advisable to conclude". Raman wins over
    the source he quotes; the narrowing is part of the yoga."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        if _house_lord(7, chart) not in ("Mars", "Venus"):
            return False
        for h in (10, 2, 7):
            lord = chart.planets.get(_house_lord(h, chart))
            if lord is None or lord.rasi_house != 10:
                return False
        return True


class _Jarajaputra(C.Condition):
    """Jarajaputra 237 (3HCC:7848): POWERFUL lords of the 5th and 7th joined with the
    lord of the 6th, aspected by benefics. "Powerful" rides B1 effective_strength on both
    lords (the Lakshmi/Go precedent, patched-gate fire test per the Y.GO discipline)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        n5, n7, n6 = (_house_lord(5, chart), _house_lord(7, chart),
                      _house_lord(6, chart))
        l5, l7, l6 = (chart.planets.get(n5), chart.planets.get(n7),
                      chart.planets.get(n6))
        if any(x is None for x in (l5, l7, l6)):
            return False
        if not (l5.rasi_house == l6.rasi_house and l7.rasi_house == l6.rasi_house):
            return False
        touched = any(b not in {n5, n6, n7} and b in chart.planets
                      and (chart.planets[b].rasi_house == l6.rasi_house
                           or drishti.aspects_house(b, l6.rasi_house, chart))
                      for b in _T5_BENEFICS)
        if not touched:
            return False
        return _t6_b1_strong(chart, n5) and _t6_b1_strong(chart, n7)


class _BahuStree(C.Condition):
    """Bahu Stree 238 (3HCC:7866): the lords of Lagna and the 7th in conjunction or in
    MUTUAL aspect (Chart 110's reading), Or the variant Raman reports in the Remarks (9th
    lord in the 7th, 7th lord in the 4th, the Lagna lord or 11th lord in a kendra)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        n1, n7 = SIGN_LORDS[chart.asc_sign], _house_lord(7, chart)
        l1, l7 = chart.planets.get(n1), chart.planets.get(n7)
        if l1 is not None and l7 is not None and n1 != n7:
            if l1.rasi_house == l7.rasi_house:
                return True
            if (drishti.aspects_planet(n1, n7, chart)
                    and drishti.aspects_planet(n7, n1, chart)):
                return True
        l9 = chart.planets.get(_house_lord(9, chart))
        if l9 is None or l9.rasi_house != 7:
            return False
        if l7 is None or l7.rasi_house != 4:
            return False
        l11 = chart.planets.get(_house_lord(11, chart))
        return ((l1 is not None and l1.rasi_house in _KENDRAS)
                or (l11 is not None and l11.rasi_house in _KENDRAS))


class _Satkalatra(C.Condition):
    """Satkalatra 239 (3HCC:7917): the 7th lord or Venus joined with or aspected by
    Jupiter or Mercury."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        targets = {_house_lord(7, chart), "Venus"}
        for tname in targets:
            tp = chart.planets.get(tname)
            if tp is None:
                continue
            for b in ("Jupiter", "Mercury"):
                if b == tname:
                    continue
                bp = chart.planets.get(b)
                if bp is None:
                    continue
                if bp.rasi_house == tp.rasi_house or drishti.aspects_planet(b, tname, chart):
                    return True
        return False


class _BhagaChumbana(C.Condition):
    """Bhaga Chumbana 240 (3HCC:7981): the 7th lord in the 4th conjunct Venus, Or the
    Remarks' own alternative (the Lagna lord debilitated in Rasi or in Navamsa)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.core.dignity import dignity_state
        from app.raman_saab.chart.constants import SIGN_LORDS
        chart = ctx.chart
        n7 = _house_lord(7, chart)
        l7 = chart.planets.get(n7)
        ven = chart.planets.get("Venus")
        if (l7 is not None and ven is not None and n7 != "Venus"
                and l7.rasi_house == 4 and ven.rasi_house == 4):
            return True
        l1 = chart.planets.get(SIGN_LORDS[chart.asc_sign])
        if l1 is None:
            return False
        if dignity_state(l1.name, l1.sign) == "debilitated":
            return True
        nav = getattr(l1, "navamsa_sign", None)
        return nav is not None and dignity_state(l1.name, nav) == "debilitated"


class _Bhagya(C.Condition):
    """Bhagya 241 (3HCC:7989): a STRONG benefic in Lagna, the 3rd or the 5th,
    simultaneously aspecting the 9th. The whole-sign drishti table carries Raman's own
    observation naturally (only Jupiter reaches the 9th from Lagna or the 5th; any
    benefic reaches it from the 3rd); strength rides B1."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        for b in _T5_BENEFICS:
            bp = chart.planets.get(b)
            if bp is None or bp.rasi_house not in {1, 3, 5}:
                continue
            if not drishti.aspects_house(b, 9, chart):
                continue
            if _t6_b1_strong(chart, b):
                return True
        return False


class _JananatpurvamPitruMarana(C.Condition):
    """Jananatpurvam Pitru Marana 242 (3HCC:8018): the Sun in 6/8/12, the 8th lord in the
    9th, the 12th lord in Lagna, the 6th lord in the 5th — Raman: "the ENTIRE yoga, and
    not a part of it, should be present" (Chart 113 holds it in toto)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        sun = chart.planets.get("Sun")
        if sun is None or sun.rasi_house not in {6, 8, 12}:
            return False
        for house, target in ((8, 9), (12, 1), (6, 5)):
            lord = chart.planets.get(_house_lord(house, chart))
            if lord is None or lord.rasi_house != target:
                return False
        return True


class _Dhatrutwa(C.Condition):
    """Dhatrutwa 243 (3HCC:8044): the 9th lord exalted, aspected by a benefic, and the
    9th occupied by a benefic."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.core.dignity import dignity_state
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        l9name = _house_lord(9, chart)
        l9 = chart.planets.get(l9name)
        if l9 is None or dignity_state(l9name, l9.sign) != "exalted":
            return False
        if not any(b != l9name and b in chart.planets
                   and drishti.aspects_planet(b, l9name, chart) for b in _T5_BENEFICS):
            return False
        return any((bp := chart.planets.get(b)) is not None and bp.rasi_house == 9
                   for b in _T5_BENEFICS)


class _Apakeerti(C.Condition):
    """Apakeerti 244 (3HCC:8126): the Sun AND Saturn in the 10th, both in malefic amsas
    OR aspected by malefics. Raman's converse is preserved: their mere presence,
    unaspected and in benefic navamsas, does NOT constitute the yoga."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        sun, sat = chart.planets.get("Sun"), chart.planets.get("Saturn")
        if sun is None or sat is None or sun.rasi_house != 10 or sat.rasi_house != 10:
            return False
        malefics = set(_T5_MALEFICS)
        def _cruel_amsa(pl) -> bool:
            nav = getattr(pl, "navamsa_sign", None)
            return nav is not None and SIGN_LORDS[nav] in malefics
        if _cruel_amsa(sun) and _cruel_amsa(sat):
            return True
        return any(m not in ("Sun", "Saturn") and m in chart.planets
                   and (drishti.aspects_planet(m, "Sun", chart)
                        or drishti.aspects_planet(m, "Saturn", chart))
                   for m in _T5_MALEFICS)


class _Raja245(C.Condition):
    """Raja 245 (3HCC:8154): three or more planets exalted or in own house occupying
    kendras — WITH Raman's own practice extension ("in actual practice... need not
    necessarily be in kendras. Even trikonas will do")."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.core.dignity import dignity_state
        chart = ctx.chart
        count = 0
        for name in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
            pl = chart.planets.get(name)
            if pl is None or pl.rasi_house not in {1, 4, 7, 10, 5, 9}:
                continue
            if dignity_state(name, pl.sign) in ("exalted", "own"):
                count += 1
        return count >= 3


class _Raja246(C.Condition):
    """Raja 246 (3HCC:8157), operationalized by Raman's own Remarks: a debilitated planet
    "of bright rays, i.e., free from combustion; or retrograde", occupying a house that
    is not a dusthana (6/8/12). Chart 116: Venus neecha in the 10th, bright AND
    retrograde."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.core.dignity import dignity_state
        chart = ctx.chart
        for name in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
            pl = chart.planets.get(name)
            if pl is None or pl.rasi_house in {6, 8, 12}:
                continue
            if dignity_state(name, pl.sign) != "debilitated":
                continue
            bright = getattr(pl, "combust_fraction", 0.0) == 0.0
            if bright or getattr(pl, "retrograde", False):
                return True
        return False


class _Raja247(C.Condition):
    """Raja 247 (3HCC:8168): two or more planets possessing Digbala, per Raman's own
    mapping in the Remarks: Mercury and Jupiter in Lagna, the Sun and Mars in the 10th,
    Saturn in the 7th, the Moon and Venus in the 4th."""

    _DIGBALA = {"Mercury": 1, "Jupiter": 1, "Sun": 10, "Mars": 10,
                "Saturn": 7, "Moon": 4, "Venus": 4}

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        count = sum(1 for name, house in self._DIGBALA.items()
                    if (pl := chart.planets.get(name)) is not None
                    and pl.rasi_house == house)
        return count >= 2


class _Raja249(C.Condition):
    """Raja 249 (3HCC:8315): the Moon in Lagna, Jupiter in the 4th, Venus in the 10th,
    Saturn exalted or in own house (Chart 118 holds it in toto)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.core.dignity import dignity_state
        chart = ctx.chart
        for name, house in (("Moon", 1), ("Jupiter", 4), ("Venus", 10)):
            pl = chart.planets.get(name)
            if pl is None or pl.rasi_house != house:
                return False
        sat = chart.planets.get("Saturn")
        return sat is not None and dignity_state("Saturn", sat.sign) in ("exalted", "own")


class _Raja250(C.Condition):
    """Neechabhanga Raja 250 (3HCC:8318): for a debilitated planet, the LORD of its sign
    or the planet EXALTED in that sign (thaduchchanatha — the contested term, resolved by
    Raman via Prof. B. Suryanarain Rao and applied so in Chart 119) stands in a kendra
    from the Moon or from Lagna. The definition carries both readings with "or"; both
    arms are encoded."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.core.dignity import EXALTATION, dignity_state
        from app.raman_saab.chart.constants import SIGN_LORDS
        chart = ctx.chart
        moon = chart.planets.get("Moon")
        exalted_in = {sign: name for name, sign in EXALTATION.items()}
        def _in_kendra_from(pl, seat_house: int) -> bool:
            return ((pl.rasi_house - seat_house) % 12) + 1 in {1, 4, 7, 10}
        for name in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
            pl = chart.planets.get(name)
            if pl is None or dignity_state(name, pl.sign) != "debilitated":
                continue
            cands = {SIGN_LORDS[pl.sign], exalted_in.get(pl.sign)}
            for cand in cands:
                if not cand or cand == name:
                    continue
                cp = chart.planets.get(cand)
                if cp is None:
                    continue
                if cp.rasi_house in {1, 4, 7, 10}:
                    return True
                if moon is not None and _in_kendra_from(cp, moon.rasi_house):
                    return True
        return False


_CHARA_SIGNS = {1, 4, 7, 10}
_STHIRA_SIGNS = {2, 5, 8, 11}


class _Raja251(C.Condition):
    """Raja 251 (3HCC:8416): the Moon in a kendra OTHER than Lagna, aspected by Jupiter,
    and "otherwise powerful" — the strength clause rides B1."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        moon = chart.planets.get("Moon")
        if moon is None or moon.rasi_house not in {4, 7, 10}:
            return False
        if not drishti.aspects_planet("Jupiter", "Moon", chart):
            return False
        return _t6_b1_strong(chart, "Moon")


class _Raja252(C.Condition):
    """Raja 252 (3HCC:8419): planets in debilitated rasis occupy EXALTED navamsas.
    Chart 122's reading is total ("ALL the neecha planets in Rasi are exalted in Amsa")
    — at least one debilitated planet, and every one of them exalted in amsa."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.core.dignity import EXALTATION, dignity_state
        chart = ctx.chart
        neecha = [pl for name, pl in chart.planets.items()
                  if name in EXALTATION
                  and dignity_state(name, pl.sign) == "debilitated"]
        if not neecha:
            return False
        return all(getattr(pl, "navamsa_sign", None) == EXALTATION[pl.name]
                   for pl in neecha)


class _Raja253(C.Condition):
    """Raja 253 (3HCC:8421): Jupiter in Lagna aspected by the 9th lord; Mercury in a
    kendra aspected by the 11th lord — with Raman's own Chart 123 relaxation: when
    Mercury IS the 11th lord, that clause is satisfied by self-lordship."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        jup = chart.planets.get("Jupiter")
        if jup is None or jup.rasi_house != 1:
            return False
        l9name = _house_lord(9, chart)
        # Chart 123's principle applied to both clauses: self-lordship satisfies.
        if l9name != "Jupiter" and not drishti.aspects_planet(l9name, "Jupiter", chart):
            return False
        merc = chart.planets.get("Mercury")
        if merc is None or merc.rasi_house not in _KENDRAS:
            return False
        l11name = _house_lord(11, chart)
        if l11name == "Mercury":
            return True
        return drishti.aspects_planet(l11name, "Mercury", chart)


class _Raja254(C.Condition):
    """Raja 254 (3HCC:8548): Saturn in Thula (exaltation) or Kumbha (Moolatrikona,
    SIGN-level per Raman's own Remark "Saturn must occupy either Thula or Kumbha"),
    standing in a kendra or trikona, aspected by the 10th lord."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        sat = chart.planets.get("Saturn")
        if sat is None or sat.sign not in {7, 11}:
            return False
        if sat.rasi_house not in {1, 4, 7, 10, 5, 9}:
            return False
        l10name = _house_lord(10, chart)
        if l10name == "Saturn":
            return False
        return drishti.aspects_planet(l10name, "Saturn", chart)


class _Raja255(C.Condition):
    """Raja 255 (3HCC:8555): the Moon joining Mars in the 2nd or 3rd, Rahu in the 5th."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        moon, mars = chart.planets.get("Moon"), chart.planets.get("Mars")
        if (moon is None or mars is None or moon.rasi_house != mars.rasi_house
                or moon.rasi_house not in {2, 3}):
            return False
        rahu = chart.planets.get("Rahu")
        return rahu is not None and rahu.rasi_house == 5


class _Raja257(C.Condition):
    """Raja 257 (3HCC:8560): a fixed-sign Lagna whose lord occupies the 10th, Jupiter in
    the 5th from Lagna and the Moon in a kendra from Jupiter (Gajakesari implied, as
    Raman notes)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        chart = ctx.chart
        if chart.asc_sign not in _STHIRA_SIGNS:
            return False
        jup = chart.planets.get("Jupiter")
        if jup is None or jup.rasi_house != 5:
            return False
        moon = chart.planets.get("Moon")
        if moon is None or ((moon.rasi_house - jup.rasi_house) % 12) + 1 not in {1, 4, 7, 10}:
            return False
        l1 = chart.planets.get(SIGN_LORDS[chart.asc_sign])
        return l1 is not None and l1.rasi_house == 10


class _Raja258(C.Condition):
    """Raja 258 (3HCC:8563): the lord of the navamsa occupied by the Moon in a quadrant
    or trine from Lagna or from Mercury. Raman's own remark — "quite a common
    combination" — is on the record."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        chart = ctx.chart
        moon = chart.planets.get("Moon")
        nav = getattr(moon, "navamsa_sign", None) if moon else None
        nd = chart.planets.get(SIGN_LORDS.get(nav)) if nav else None
        if nd is None:
            return False
        if nd.rasi_house in {1, 4, 7, 10, 5, 9}:
            return True
        merc = chart.planets.get("Mercury")
        if merc is None:
            return False
        return ((nd.rasi_house - merc.rasi_house) % 12) + 1 in {1, 4, 7, 10, 5, 9}


class _Raja259(C.Condition):
    """Raja 259 (3HCC:8723): Taurus Lagna with the Moon in it; Saturn, the Sun and
    Jupiter in the 10th, 4th and 7th. From Sambhu Hora Prakasha, with Raman's own
    skeptical gloss recorded in the effect."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        if chart.asc_sign != 2:
            return False
        for name, house in (("Moon", 1), ("Saturn", 10), ("Sun", 4), ("Jupiter", 7)):
            pl = chart.planets.get(name)
            if pl is None or pl.rasi_house != house:
                return False
        return True


class _Raja260(C.Condition):
    """Raja 260 (3HCC:8743): a movable-sign Lagna whose lord occupies a movable sign; the
    lord of the navamsa held by a debilitated planet in a kendra or trikona from Lagna
    (Chart 128: Makara Lagna, Saturn in Thula, Jupiter neecha, dispositor Saturn)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.core.dignity import dignity_state
        from app.raman_saab.chart.constants import SIGN_LORDS
        chart = ctx.chart
        if chart.asc_sign not in _CHARA_SIGNS:
            return False
        l1 = chart.planets.get(SIGN_LORDS[chart.asc_sign])
        if l1 is None or l1.sign not in _CHARA_SIGNS:
            return False
        for name, pl in chart.planets.items():
            if name in ("Rahu", "Ketu"):
                continue
            if dignity_state(name, pl.sign) != "debilitated":
                continue
            nav = getattr(pl, "navamsa_sign", None)
            nd = chart.planets.get(SIGN_LORDS.get(nav)) if nav else None
            if nd is not None and nd.rasi_house in {1, 4, 7, 10, 5, 9}:
                return True
        return False


class _Raja261(C.Condition):
    """Raja 261 (3HCC:8748): the Lagna lord joined with a debilitated planet; Rahu and
    Saturn in the 10th, aspected by the 9th lord (Chart 129 holds it completely)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.core.dignity import dignity_state
        from app.raman_saab.chart.constants import SIGN_LORDS
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        rahu, sat = chart.planets.get("Rahu"), chart.planets.get("Saturn")
        if rahu is None or sat is None or rahu.rasi_house != 10 or sat.rasi_house != 10:
            return False
        l9name = _house_lord(9, chart)
        if l9name not in chart.planets or not drishti.aspects_house(l9name, 10, chart):
            return False
        l1name = SIGN_LORDS[chart.asc_sign]
        l1 = chart.planets.get(l1name)
        if l1 is None:
            return False
        return any(name != l1name and name not in ("Rahu", "Ketu")
                   and pl.rasi_house == l1.rasi_house
                   and dignity_state(name, pl.sign) == "debilitated"
                   for name, pl in chart.planets.items())


class _Raja262(C.Condition):
    """Raja 262 (3HCC:8828): at least one of the lords of the 11th, 9th and 2nd in a
    kendra from the Moon, Jupiter owning the 2nd, 5th or 11th (Kumbha, Simha, Vrishabha
    or Vrischika lagnas, as Raman spells out)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        if not any(_house_lord(h, chart) == "Jupiter" for h in (2, 5, 11)):
            return False
        moon = chart.planets.get("Moon")
        if moon is None:
            return False
        for h in (11, 9, 2):
            lord = chart.planets.get(_house_lord(h, chart))
            if lord is None:
                continue
            if ((lord.rasi_house - moon.rasi_house) % 12) + 1 in {1, 4, 7, 10}:
                return True
        return False


class _Raja263(C.Condition):
    """Raja 263 (3HCC:8829): Jupiter, Mercury, Venus or the Moon in the 9th, free from
    combustion, aspected by or associated with FRIENDLY planets (naisargika friends of
    the occupant)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.core.dignity import naisargika_relation
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        for b in ("Jupiter", "Mercury", "Venus", "Moon"):
            bp = chart.planets.get(b)
            if bp is None or bp.rasi_house != 9:
                continue
            if getattr(bp, "combust_fraction", 0.0) > 0.0:
                continue
            for name, pl in chart.planets.items():
                if name == b or name in ("Rahu", "Ketu"):
                    continue
                if naisargika_relation(b, name) != "friend":
                    continue
                if pl.rasi_house == bp.rasi_house or drishti.aspects_planet(name, b, chart):
                    return True
        return False


class _Vrana(C.Condition):
    """Vrana 265 (3HCC:8914): the 6th lord, being a malefic, in Lagna, the 8th or the
    10th — with Raman's own exception encoded: Scorpio is excepted ("the 6th lord happens
    to be Lagnadhipathi himself")."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        if chart.asc_sign == 8:
            return False
        l6name = _house_lord(6, chart)
        if l6name not in set(_T5_MALEFICS):
            return False
        l6 = chart.planets.get(l6name)
        return l6 is not None and l6.rasi_house in {1, 8, 10}


class _Sisnavyadhi(C.Condition):
    """Sisnavyadhi 266 (3HCC:8987): Mercury in Lagna in association with the lords of the
    6th and the 8th. Self-lordship (Mercury owning the 6th or 8th) satisfies its clause —
    the Chart 123 precedent, and Chart 132's own loose bhava reading supports it."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        merc = chart.planets.get("Mercury")
        if merc is None or merc.rasi_house != 1:
            return False
        for h in (6, 8):
            lord = _house_lord(h, chart)
            if lord == "Mercury":
                continue
            pl = chart.planets.get(lord)
            if pl is None or pl.rasi_house != 1:
                return False
        return True


class _Kalatrashanda(C.Condition):
    """Kalatrashanda 267 (3HCC:9026): the 7th lord in the 6th with Venus. Venus as the
    7th lord itself is the degenerate case — strict-unsatisfied (the 227 rule). Raman's
    own I-have-not-tested caveat is recorded in the effect."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        n7 = _house_lord(7, chart)
        if n7 == "Venus":
            return False
        l7 = chart.planets.get(n7)
        ven = chart.planets.get("Venus")
        return (l7 is not None and ven is not None
                and l7.rasi_house == 6 and ven.rasi_house == 6)


class _Kushtaroga268(C.Condition):
    """Kushtaroga 268 (3HCC:9044): the Lagna lord with Mars and Mercury together in the
    4th or the 12th (the set collapses naturally when the Lagna lord IS Mars or
    Mercury)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        chart = ctx.chart
        names = {SIGN_LORDS[chart.asc_sign], "Mars", "Mercury"}
        planets = [chart.planets.get(n) for n in names]
        if any(pl is None for pl in planets):
            return False
        houses = {pl.rasi_house for pl in planets}
        return len(houses) == 1 and houses.pop() in {4, 12}


class _Kushtaroga269(C.Condition):
    """Kushtaroga 269 (3HCC:9046): Jupiter in the 6th in association with Saturn and the
    Moon — all three in the 6th."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        chart = ctx.chart
        return all((pl := chart.planets.get(n)) is not None and pl.rasi_house == 6
                   for n in ("Jupiter", "Saturn", "Moon"))


class _Bandhana(C.Condition):
    """Bandhana 271 (3HCC:9302): the lords of Lagna and the 6th in a kendra or trikona
    with Saturn, Rahu or Ketu — both lords seated in kendra/trikona houses, at least one
    of the three shadow-heavy malefics conjunct either lord. Raman's note (Saturn as
    Lagna lord lessens or neutralizes the evil) is recorded in the effect, not gated."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        chart = ctx.chart
        names = {SIGN_LORDS[chart.asc_sign], _house_lord(6, chart)}
        lords = [chart.planets.get(n) for n in names]
        if any(l is None or l.rasi_house not in {1, 4, 7, 10, 5, 9} for l in lords):
            return False
        return any(m not in names and (mp := chart.planets.get(m)) is not None
                   and any(mp.rasi_house == l.rasi_house for l in lords)
                   for m in ("Saturn", "Rahu", "Ketu"))


class _Durmarana(C.Condition):
    """Durmarana 274 (3HCC:9387): the Moon, aspected by the Lagna lord, in 6/8/12 in
    association with Saturn or Rahu. The definition's third associate — Mandi — is an
    OR-arm deliberately omitted pending the Gulika scope ruling (omission only
    under-fires); recorded here so the arm is restored when Gulika lands."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        moon = chart.planets.get("Moon")
        if moon is None or moon.rasi_house not in {6, 8, 12}:
            return False
        l1name = SIGN_LORDS[chart.asc_sign]
        if l1name != "Moon" and not drishti.aspects_planet(l1name, "Moon", chart):
            return False
        return any((mp := chart.planets.get(m)) is not None
                   and mp.rasi_house == moon.rasi_house for m in ("Saturn", "Rahu"))


class _Peenasaroga(C.Condition):
    """Peenasaroga 278 (3HCC:9495): the Moon in the 6th, Saturn in the 8th, a malefic in
    the 12th, and the Lagna lord in a malefic (cruel) navamsa."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.chart.constants import SIGN_LORDS
        chart = ctx.chart
        moon, sat = chart.planets.get("Moon"), chart.planets.get("Saturn")
        if moon is None or sat is None or moon.rasi_house != 6 or sat.rasi_house != 8:
            return False
        if not any(m != "Saturn" and (mp := chart.planets.get(m)) is not None
                   and mp.rasi_house == 12 for m in _T5_MALEFICS):
            return False
        l1 = chart.planets.get(SIGN_LORDS[chart.asc_sign])
        nav = getattr(l1, "navamsa_sign", None) if l1 else None
        return nav is not None and SIGN_LORDS[nav] in set(_T5_MALEFICS)


class _SaturnOwnsJoinsOrAfflictsSecond(C.Condition):
    """Sraddhannabhuktha (3HCC:5963): Saturn owns the 2nd, OR joins the 2nd lord, OR the 2nd
    is aspected by a debilitated Saturn."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.core.dignity import dignity_state
        from app.raman_saab.doctrine import drishti
        chart = ctx.chart
        lord2 = _house_lord(2, chart)
        if lord2 == "Saturn":
            return True
        sat, l2 = chart.planets.get("Saturn"), chart.planets.get(lord2)
        if sat is None:
            return False
        if l2 is not None and sat.rasi_house == l2.rasi_house:
            return True
        return (dignity_state("Saturn", sat.sign) == "debilitated"
                and drishti.aspects_house("Saturn", 2, chart))


# ── the encoded yogas ────────────────────────────────────────────────────────
YOGAS: tuple[YogaRecord, ...] = (
    # — Pancha Mahapurusha (the five 'great men' yogas; Varahamihira, 3HC:3432-4060) —
    YogaRecord(
        id="Y.RUCHAKA", name="Ruchaka Yoga", kind="other",
        condition=_Panchamahapurusha("Mars"),
        effect=("Strong, valorous physique; a leader of men, a great commander, aggressive and "
                "famous; observes ancestral custom."),
        source=Citation("3HC", 3884)),
    YogaRecord(
        id="Y.BHADRA", name="Bhadra Yoga", kind="other",
        condition=_Panchamahapurusha("Mercury"),
        effect=("Highly intelligent and skilful in all undertakings; learned, eloquent, long-lived; "
                "lion-like physique."),
        source=Citation("3HC", 3973)),
    YogaRecord(
        id="Y.HAMSA", name="Hamsa Yoga", kind="other",
        condition=_Panchamahapurusha("Jupiter"),
        effect=("Handsome body, righteous disposition, pure mind; a man of sterling character and "
                "moral fibre, respected."),
        source=Citation("3HC", 3434)),
    YogaRecord(
        id="Y.MALAVYA", name="Malavya Yoga", kind="other",
        condition=_Panchamahapurusha("Venus"),
        effect=("Well-developed physique, strong-minded, wealthy; happy with children and wife; "
                "commands renown, learned and refined."),
        source=Citation("3HC", 3680)),
    YogaRecord(
        id="Y.SASA", name="Sasa Yoga", kind="other",
        condition=_Panchamahapurusha("Saturn"),
        effect=("Commands good servants; head of a town or a king; powerful, covetous of others' "
                "wealth, strong constitution."),
        source=Citation("3HC", 3737)),
    # — solar (Sun-flank) yogas: the analogue of Sunapha/Anapha/Durudhara from the Sun —
    YogaRecord(
        id="Y.VESI", name="Vesi Yoga", kind="other", condition=_SunFlank(2),
        effect=("Truthful, happy, balanced; (benefic Vesi) eloquent and well-known."),
        source=Citation("3HC", 3268)),
    YogaRecord(
        id="Y.VASI", name="Vasi Yoga", kind="other", condition=_SunFlank(12),
        effect=("Skilful, liberal, eloquent; favoured by the ruler."),
        source=Citation("3HC", 3388)),
    YogaRecord(
        id="Y.UBHAYACHARI", name="Ubhayachari Yoga", kind="other",
        condition=C.And(_SunFlank(2), _SunFlank(12)),
        effect=("A king or his equal; eloquent, strong-bodied, virtuous, enjoys comforts."),
        source=Citation("3HC", 3373)),
    # — Nabhasa: Asraya (3) — all seven planets in one modality —
    YogaRecord(
        id="Y.RAJJU", name="Rajju Yoga", kind="other", condition=_AsrayaModality("movable"),
        effect=("Fond of travel and wandering, charming, attached to worldly objects."),
        source=Citation("3HC", 7088)),
    YogaRecord(
        id="Y.MUSALA", name="Musala Yoga", kind="other", condition=_AsrayaModality("fixed"),
        effect=("Endowed with self-respect, wealth, wisdom; firm of determination, honoured."),
        source=Citation("3HC", 7088)),
    YogaRecord(
        id="Y.NALA", name="Nala Yoga", kind="other", condition=_AsrayaModality("common"),
        effect=("Resourceful and clever, but defective of limb; engaged in many works."),
        source=Citation("3HC", 7113)),
    # — Nabhasa: Dala (2) — kendras held purely by benefics / malefics —
    YogaRecord(
        id="Y.MALA", name="Mala (Srik) Yoga", kind="other", condition=_DalaKendra("benefic"),
        effect=("Ever happy, blessed with conveyances, comforts and the company of agreeable people."),
        source=Citation("3HC", 3194)),
    YogaRecord(
        id="Y.SARPA", name="Sarpa Yoga", kind="other", condition=_DalaKendra("malefic"),
        effect=("Crooked and miserable; lives in distress, dependent and poor."),
        source=Citation("3HC", 7177)),
    # — Nabhasa: Sankhya (7) — by the count of distinct signs the seven planets occupy —
    YogaRecord(id="Y.VEENA", name="Veena (Vallaki) Yoga", kind="other", condition=_SankhyaSignCount(7),
               effect="Fond of music, dance and the arts; wealthy, happy, a leader.",
               source=Citation("3HC", 6498)),
    YogaRecord(id="Y.DAMINI", name="Damini Yoga", kind="other", condition=_SankhyaSignCount(6),
               effect="Charitable, wealthy, famous; helps others and is renowned.",
               source=Citation("3HC", 6593)),
    YogaRecord(id="Y.PASA", name="Pasa Yoga", kind="other", condition=_SankhyaSignCount(5),
               effect="Skilful, talkative, with many dependents; liable to bondage/confinement.",
               source=Citation("3HC", 6732)),
    YogaRecord(id="Y.KEDARA", name="Kedara Yoga", kind="other", condition=_SankhyaSignCount(4),
               effect="An agriculturist, useful to many, truthful and happy.",
               source=Citation("3HC", 6868)),
    YogaRecord(id="Y.SULA", name="Sula Yoga", kind="other", condition=_SankhyaSignCount(3),
               effect="Sharp/aggressive, valorous but indigent; cruel-natured.",
               source=Citation("3HC", 6868)),
    YogaRecord(id="Y.YUGA", name="Yuga Yoga", kind="other", condition=_SankhyaSignCount(2),
               effect="A heretic or outcaste; poor and devoid of wealth.",
               source=Citation("3HC", 6868)),
    YogaRecord(id="Y.GOLA", name="Gola Yoga", kind="other", condition=_SankhyaSignCount(1),
               effect="Poor, dirty, devoid of learning, strength and comfort.",
               source=Citation("3HC", 6868)),
    # — Nabhasa: Akriti (the 4 contiguous-house forms; the 16 other Akriti shapes are a backlog) —
    YogaRecord(id="Y.YUPA", name="Yupa Yoga", kind="other", condition=_AllSevenInHouses((1, 2, 3, 4)),
               effect="Liberal, self-possessed, noted for charitable and sacrificial deeds.",
               source=Citation("3HC", 5761)),
    YogaRecord(id="Y.ISHU", name="Ishu (Sara) Yoga", kind="other",
               condition=_AllSevenInHouses((4, 5, 6, 7)),
               effect="A maker or seller of arrows; superintendent of a jail/camp.",
               source=Citation("3HC", 5761)),
    YogaRecord(id="Y.SAKTI", name="Sakti Yoga", kind="other",
               condition=_AllSevenInHouses((7, 8, 9, 10)),
               effect="Lazy and slothful, devoid of riches, generally disliked.",
               source=Citation("3HC", 5761)),
    YogaRecord(id="Y.DANDA", name="Danda Yoga", kind="other",
               condition=_AllSevenInHouses((10, 11, 12, 1)),
               effect="Lacks the happiness of wife and children; lonely, servile.",
               source=Citation("3HC", 5761)),
    # — Nabhasa: the 16 remaining Akriti shape-yogas (3HC:5955-6450) — all seven planets confined
    #   to a named house-shape. Verdict-invariant (kind='other'). —
    YogaRecord(id="Y.NAVA", name="Nava (Nauka) Yoga", kind="other",
               condition=_AnchoredArc(1),
               effect="Gathers wealth (often by water/voyages); greedy, miserly.",
               source=Citation("3HC", 5955)),
    YogaRecord(id="Y.KUTA", name="Kuta Yoga", kind="other",
               condition=_AnchoredArc(4),
               effect="Deceitful and poor; a jailer or keeper of forts.",
               source=Citation("3HC", 5957)),
    YogaRecord(id="Y.CHATRA", name="Chatra Yoga", kind="other",
               condition=_AnchoredArc(7),
               effect="Helpful and wise; happy at the beginning and end of life.",
               source=Citation("3HC", 5959)),
    YogaRecord(id="Y.CHAPA", name="Chapa Yoga", kind="other",
               condition=_AnchoredArc(10),
               effect="Leads a comfortable life delighting in good deeds.",
               source=Citation("3HC", 5961)),
    YogaRecord(id="Y.ARDHACHANDRA", name="Ardha-Chandra Yoga", kind="other",
               condition=C.Or(*[_AnchoredArc(s) for s in (2, 3, 5, 6, 8, 9, 11, 12)]),
               effect="Fair-featured and happy throughout life; a commander, favoured by the ruler.",
               source=Citation("3HC", 6008)),
    YogaRecord(id="Y.CHAKRA", name="Chakra Yoga", kind="other",
               condition=_AllSevenInHouses((1, 3, 5, 7, 9, 11)),
               effect="A king or his equal; commands respect, earns and spends well.",
               source=Citation("3HC", 6025)),
    YogaRecord(id="Y.SAMUDRA", name="Samudra Yoga", kind="other",
               condition=_AllSevenInHouses((2, 4, 6, 8, 10, 12)),
               effect="Wealthy and well-supplied; enjoys many pleasures.",
               source=Citation("3HC", 6450)),
    YogaRecord(id="Y.GADA", name="Gada Yoga", kind="other",
               condition=C.Or(*[_AllSevenInHouses(p) for p in ((1, 4), (4, 7), (7, 10), (10, 1))]),
               effect="Highly religious and wealthy; performs sacrifices.",
               source=Citation("3HC", 6047)),
    YogaRecord(id="Y.SAKATA_AKRITI", name="Sakata Yoga (Akriti)", kind="other",
               condition=_AllSevenInHouses((1, 7)),
               effect="Poor and unhappy in domestic life.",
               source=Citation("3HC", 6049)),
    YogaRecord(id="Y.VIHAGA", name="Vihaga Yoga", kind="other",
               condition=_AllSevenInHouses((4, 10)),
               effect="A vagrant; quarrelsome and mean.",
               source=Citation("3HC", 6051)),
    YogaRecord(id="Y.VAJRA", name="Vajra Yoga", kind="other",
               condition=_ShapeByClass((1, 7), (4, 10)),
               effect="Brave and valorous; happy at the beginning and end of life.",
               source=Citation("3HC", 6172)),
    YogaRecord(id="Y.YAVA", name="Yava Yoga", kind="other",
               condition=_ShapeByClass((4, 10), (1, 7)),
               effect="Charitable and observant of vows; happy in middle life.",
               source=Citation("3HC", 6174)),
    YogaRecord(id="Y.SRINGHATAKA", name="Sringhataka Yoga", kind="other",
               condition=_AllSevenInHouses((1, 5, 9)),
               effect="Happy and devoted to god; loving spouse, conquers enemies.",
               source=Citation("3HC", 6260)),
    YogaRecord(id="Y.HALA", name="Hala Yoga", kind="other",
               condition=C.Or(*[_AllSevenInHouses(t) for t in ((2, 6, 10), (3, 7, 11), (4, 8, 12))]),
               effect="An agriculturist; eats much, often poor or servile.",
               source=Citation("3HC", 6262)),
    YogaRecord(id="Y.KAMALA", name="Kamala Yoga", kind="other",
               condition=_AllSevenInHouses((1, 4, 7, 10)),
               effect="Wealthy, virtuous, famous and long-lived; of many good deeds.",
               source=Citation("3HC", 6365)),
    YogaRecord(id="Y.VAPEE", name="Vapee Yoga", kind="other",
               condition=C.Or(_AllSevenInHouses((2, 5, 8, 11)), _AllSevenInHouses((3, 6, 9, 12))),
               effect="Accumulates and conserves wealth; frugal, enjoys steady fortune.",
               source=Citation("3HC", 6367)),
    # — named Raja / Dhana yogas (3HC; reported, kind='other') —
    YogaRecord(id="Y.BUDHA_ADITYA", name="Budha-Aditya Yoga", kind="other",
               condition=_Conjunct("Sun", "Mercury"),
               effect="Highly intelligent and skilful in all undertakings; learned, of good repute.",
               source=Citation("3HC", 4061)),
    YogaRecord(id="Y.CHATUSSAGARA", name="Chatussagara Yoga", kind="other",
               condition=_AllKendrasOccupied(),
               effect="Good reputation, equal to a ruler, long-lived; fame to the four oceans.",
               source=Citation("3HC", 2613)),
    YogaRecord(id="Y.VASUMATHI", name="Vasumathi Yoga", kind="other",
               condition=_BeneficsInUpachayas(),
               effect="Never wanting; always commands plenty of wealth.",
               source=Citation("3HC", 2708)),
    YogaRecord(id="Y.PARVATA", name="Parvata Yoga", kind="other",
               condition=_ParvataYoga(),
               effect="Wealthy, prosperous, liberal, charitable, humorous; head of a town.",
               source=Citation("3HC", 3170)),
    YogaRecord(id="Y.JAYA", name="Jaya Yoga", kind="other",
               condition=_JayaYoga(),
               effect="Ever successful, happy and long-lived; victorious over enemies.",
               source=Citation("3HC", 5670)),
    YogaRecord(id="Y.DARIDRA", name="Daridra Yoga", kind="other",
               condition=_DaridraYoga(),
               effect="Contracts heavy debts and is very poor; the gains-lord is lost in a dusthana.",
               source=Citation("3HC", 7289)),
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
    # — HPA Ch.20 named raja/virtue yogas (additive fidelity; cited verbatim) —
    YogaRecord(
        id="Y.CHAMARA", name="Chamara Yoga", kind="raja",
        # Raman: "lord of the ascendant exalted in a quadrant with the aspect of Jupiter;
        # OR two benefics in the ascendant/7th/10th." Only the STRICT first arm is encoded
        # (exalted-lagna-lord + Jupiter aspect). The "two benefics in 1/7/10" arm is OMITTED
        # — it over-fires (35/164); a documented limit.
        condition=C.And(_LordDignityInHouses(1, frozenset({"exalt"}), _KENDRAS),
                        _LordAspectedBy(1, "Jupiter")),
        effect=("Greatly respected by kings and the aristocracy; good conversationalist, "
                "profound scholar; long-lived (over 70 years)."),
        source=Citation("HPA-20", 65)),
    YogaRecord(
        id="Y.SREENATHA", name="Sreenatha Yoga", kind="raja",
        # "the exalted lord of the 7th occupies the 10th AND the lord of the 10th combines
        # with the lord of the 9th."
        condition=C.And(_LordDignityInHouses(7, frozenset({"exalt"}), frozenset({10})),
                        C.LordsConjunct(9, 10)),
        effect="Great respect and reputation, honourable living, much wealth, fine surroundings.",
        source=Citation("HPA-20", 90)),
    YogaRecord(
        id="Y.KHADGA", name="Khadga Yoga", kind="raja",
        # "Lord of the 2nd in the 9th, and the lord of the 9th in the 2nd [a 2-9 exchange],
        # and the lord of ascendant in a quadrant or a trine."
        condition=C.And(C.Parivartana(2, 9), _LordInHouses(1, _KENDRAS | _TRIKONAS)),
        effect="Religiously inclined; courageous, strong, of penetrating intelligence.",
        source=Citation("HPA-20", 184)),
    # — HPA Ch.20, the remaining purely-geometric named yogas (no 'powerful lord' proxy;
    #   each encodes Raman's printed geometry verbatim, so it is faithful by construction) —
    # NOTE: Matsya (HPA-20:116) is DEFERRED — the OCR text ("malefics in the 4th and [8th]")
    #   reads as a malefic in each of 1/4/5/8/9, which is UNSATISFIABLE (only 5 malefics exist and
    #   Rahu/Ketu are physically opposite, but no two of those houses are opposite). Other classical
    #   editions read "benefics in the 4th"; the definition needs cross-verification (3HC has a
    #   Matsya entry) before encoding. Never ship a rule that can never fire.
    YogaRecord(
        id="Y.SARADA", name="Sarada Yoga", kind="other",
        # HPA-20:106-114, three disjuncts printed as "...; or...; or...":
        #   (1) Jupiter in a trine (5/9) from the Moon AND Mars in a trine from Mercury;
        #   (2) Jupiter in the 11th from Mercury;
        #   (3) the 10th lord in the 5th, Mercury in a quadrant, and the Sun in his own sign.
        condition=C.Or(
            C.And(C.Or(C.InHouseFrom("Jupiter", "MOON", 5), C.InHouseFrom("Jupiter", "MOON", 9)),
                  C.Or(C.InHouseFrom("Mars", "Mercury", 5), C.InHouseFrom("Mars", "Mercury", 9))),
            C.InHouseFrom("Jupiter", "Mercury", 11),
            C.And(_LordInHouses(10, frozenset({5})),
                  C.InHouseClass("Mercury", "kendra"),
                  C.HasDignity("Sun", {"own", "moolatrikona"}))),
        effect=("Respector of preceptors and religiously inclined; praised by royalty and the "
                "aristocracy, a saintly disposition, a patron of the fine arts and sciences."),
        source=Citation("HPA-20", 106)),
    YogaRecord(
        id="Y.KUSUMA", name="Kusuma Yoga", kind="raja",
        # HPA-20:200-202: "Venus in a fixed sign, in a quadrant, a weak Moon in a trine and the
        # Sun in the 10th house." 'Weak Moon' is read as a waning (Krishna-paksha) Moon — the
        # standard sense of lunar weakness — placed in a trikona (5/9).
        condition=C.And(_PlanetSignModality("Venus", "fixed"),
                        C.InHouseClass("Venus", "kendra"),
                        C.InHouseClass("Moon", "trikona"), C.MoonPhase("waning"),
                        C.InRashiHouse("Sun", 10)),
        effect=("Extremely liberal, war-like, possessed of an unsullied reputation and good "
                "enjoyment."),
        source=Citation("HPA-20", 200)),
    # — HPA Ch.20 BAD YOGAS (arishta / character defect), also purely geometric —
    YogaRecord(
        id="Y.BRIHADBIJA", name="Brihadbija Yoga", kind="arishta",
        # HPA-20:216-219: "Rahu with Mars and Saturn in the ascendant; OR the lord of the
        # ascendant in the 8th with Rahu and malefics." Arm B needs Rahu PLUS another malefic
        # in the 8th (>=2 malefics there, Rahu being one) with the lagna lord.
        condition=C.Or(
            C.And(C.InRashiHouse("Rahu", 1), C.InRashiHouse("Mars", 1),
                  C.InRashiHouse("Saturn", 1)),
            C.And(_LordInHouses(1, frozenset({8})), C.InRashiHouse("Rahu", 8),
                  C.CountInHouse(8, 2, "malefic"))),
        effect=("Swelling of the testicles and venereal complaints."),
        source=Citation("HPA-20", 216)),
    YogaRecord(
        id="Y.ASATYAVADI", name="Asatyavadi Yoga", kind="other",
        # HPA-20:225-226: "If the lord of the house occupied by the lord of the 2nd is Saturn."
        # I.e. the dispositor of the 2nd lord is Saturn. Base rate ~1/6 (Saturn rules 2 of the 12
        # signs) — a common condition by construction, exactly as Raman states it, NOT a mis-encode.
        condition=_DispositorOfNthLordIs(2, "Saturn"),
        effect=("Always loving falsehood and indulging in fraudulent schemes."),
        source=Citation("HPA-20", 225)),
    # — first 3HC tranche against the clean copies (2026-08-08). Selection governed by the
    # deferral precedent above: nothing strength-gated, nothing measured-common, nothing whose
    # parse Raman leaves ambiguous. Skips recorded below the registry. —
    YogaRecord(
        id="Y.MATSYA", name="Matsya Yoga", kind="other",
        # 3HCH:1814: "Malefics should be disposed in Lagna and the 9th; the fifth house should
        # contain both malefics and benefics; and the fourth and 8th should be occupied by
        # malefics." Pure occupancy, six clauses, all whole-sign.
        condition=C.And(
            C.CountInHouse(1, 1, "malefic"), C.CountInHouse(9, 1, "malefic"),
            C.CountInHouse(5, 1, "malefic"), C.CountInHouse(5, 1, "benefic"),
            C.CountInHouse(4, 1, "malefic"), C.CountInHouse(8, 1, "malefic")),
        effect=("A clever prophet, an ocean of kindness, intelligent, well-behaving, famous "
                "and learned."),
        source=Citation("3HCH", 1814)),
    YogaRecord(
        id="Y.RAVI", name="Ravi Yoga", kind="other",
        # 3HCH:1982: "The Sun should join the 10th and the lord of the 10th must be in the 3rd
        # in conjunction with Saturn."
        condition=C.And(
            C.InRashiHouse("Sun", 10),
            _LordOfHouseInHouseWith(10, 3, "Saturn")),
        effect=("Respected by rulers, well-versed in sciences, famous after the fifteenth "
                "year, highly passionate, simple in food, lotus-eyed."),
        source=Citation("3HCH", 1982)),
    YogaRecord(
        id="Y.GAURI", name="Gauri Yoga", kind="other",
        condition=_GauriNavamsaChain(),
        effect=("Belongs to a respectable family, owns lands, charitable, performs religious "
                "rites; sons of good character; praised by all."),
        source=Citation("3HCH", 1637)),
    YogaRecord(
        id="Y.BRAHMA", name="Brahma Yoga", kind="other",
        # 3HCH:1931: "Jupiter and Venus are in Kendras respectively from the lords of the 9th
        # and 11th, and Mercury is in a similar position from the lord of either Lagna or the
        # 10th." All natural benefics involved — Raman remarks so himself.
        condition=C.And(
            _KendraFromLordOf("Jupiter", 9),
            _KendraFromLordOf("Venus", 11),
            C.Or(_KendraFromLordOf("Mercury", 1), _KendraFromLordOf("Mercury", 10))),
        effect=("Luxurious living; respected by the learned; highly learned, long-lived, "
                "charitable and bent on good deeds."),
        source=Citation("3HCH", 1931)),
    YogaRecord(
        id="Y.NISHTURABHASHI", name="Nishturabhashi Yoga", kind="other",
        # 3HCC:10205 — the FIRST yoga encoded from the complete edition (163-300): "The Moon
        # must be in conjunction with Saturn." Raman neutralises it under Jupiter aspect in the
        # same passage; the Not() arm is his cancellation, not an invention.
        condition=C.And(C.Conjunct("Moon", "Saturn"),
                        C.Not(C.Aspects("Jupiter", "Moon"))),
        effect=("Harsh in speech."),
        source=Citation("3HCC", 10205)),
    # — tranche 2 (2026-08-09): Lakshmi unlocked by measurement; a far-half block on the 2nd
    # house (speech/face/eyes) and the Andha pair. Skips recorded below. —
    YogaRecord(
        id="Y.LAKSHMI", name="Lakshmi Yoga", kind="dhana",
        condition=_LakshmiYoga(),
        effect=("Wealthy, noble, learned; high integrity and reputation, handsome; a good "
                "ruler enjoying the pleasures and comforts of life."),
        source=Citation("3HCH", 1557)),
    YogaRecord(
        id="Y.MOOKA", name="Mooka Yoga", kind="other",
        # 3HCC:5801: "The 2nd lord should join the 8th with Jupiter."
        condition=_LordOfHouseInHouseWith(2, 8, "Jupiter"),
        effect=("The person becomes dumb."),
        source=Citation("3HCC", 5801)),
    YogaRecord(
        id="Y.NETRANASA", name="Netranasa Yoga", kind="other",
        condition=_LordsAllInLagnaOrNeechamsa(),
        effect=("Loses eyesight owing to the displeasure of the rulers."),
        source=Citation("3HCC", 5810)),
    YogaRecord(
        id="Y.SUMUKHA", name="Sumukha Yoga", kind="other",
        # combination 166 (2nd lord in a kendra aspected by benefics, OR benefics in the 2nd)
        # PLUS combination 167 (graduated 2026-08-09: the Gopuramsa primitive now exists —
        # 2nd lord in a dignified/friendly kendra whose sign-lord attains rung 8).
        condition=C.Or(_NthLordInKendraAspectedByBenefic(2),
                       C.CountInHouse(2, 1, "benefic"),
                       _Sumukha167()),
        effect=("An attractive and smiling face."),
        source=Citation("3HCC", 5853)),
    YogaRecord(
        id="Y.DURMUKHA", name="Durmukha Yoga", kind="other",
        # combination 168 only: malefics occupy the 2nd AND its lord joins an evil planet or
        # is debilitated. Combination 169 needs Gulika — unmodelled; skipped below.
        condition=C.And(C.CountInHouse(2, 1, "malefic"),
                        _NthLordWithMaleficOrDebilitated(2)),
        effect=("An ugly or repulsive face; angry and irritable."),
        source=Citation("3HCC", 5878)),
    YogaRecord(
        id="Y.SRADDHANNABHUKTHA", name="Sraddhannabhuktha Yoga", kind="other",
        condition=_SaturnOwnsJoinsOrAfflictsSecond(),
        effect=("Gets food offered at obsequial rites."),
        source=Citation("3HCC", 5963)),
    YogaRecord(
        id="Y.ANDHA", name="Andha Yoga", kind="other",
        # both printed forms (3HCC:9829): 288 — the Sun rising in Lagna with Rahu, malefics in
        # the trikonas; 289 — Mars, Moon, Saturn, Sun in the 2nd, 6th, 12th, 8th respectively.
        condition=C.Or(
            C.And(C.InRashiHouse("Sun", 1), C.InRashiHouse("Rahu", 1),
                  C.CountInHouse(5, 1, "malefic"), C.CountInHouse(9, 1, "malefic")),
            C.And(C.InRashiHouse("Mars", 2), C.InRashiHouse("Moon", 6),
                  C.InRashiHouse("Saturn", 12), C.InRashiHouse("Sun", 8))),
        effect=("Born stone-blind."),
        source=Citation("3HCC", 9829)),
    # — tranche 3 (2026-08-09). NOTE the editions NUMBER these differently (Vishnu is 62 in
    # the complete ed., 64 in the truncated scans; Go 67 vs 69; Indra 64 vs 66) — citations
    # are by LINE in the edition actually quoted, which is what the source lock freezes. —
    YogaRecord(
        id="Y.INDRA", name="Indra Yoga", kind="raja",
        # 3HCH:1978: "the lords of the 5th and 11th interchange their houses and the Moon is
        # in the 5th."
        condition=C.And(_MutualHouseExchange(5, 11), C.InRashiHouse("Moon", 5)),
        effect=("Highly courageous, lasting fame, a king of kings, good enjoyments."),
        source=Citation("3HCH", 1978)),
    YogaRecord(
        id="Y.TRILOCHANA", name="Trilochana Yoga", kind="other",
        # 3HCH:2073: "The Sun, the Moon and Mars should be in trines from each other."
        condition=_MutualTrines(("Sun", "Moon", "Mars")),
        effect=("Great wealth, a terror to his enemies, highly intelligent, good longevity."),
        source=Citation("3HCH", 2073)),
    YogaRecord(
        id="Y.KULAVARDHANA", name="Kulavardhana Yoga", kind="other",
        # 3HCH:2095: "All planets should be in the 5th from Lagna, the Sun and the Moon" —
        # three variants, one per reference point, per Raman's remark.
        condition=C.Or(_AllSevenInFifthFrom("Lagna"), _AllSevenInFifthFrom("Sun"),
                       _AllSevenInFifthFrom("Moon")),
        effect=("Unbroken line of successors; wealthy, healthy and long-lived."),
        source=Citation("3HCH", 2095)),
    YogaRecord(
        id="Y.VISHNU", name="Vishnu Yoga", kind="dhana",
        condition=_VishnuChain(),
        effect=("Leads an enjoyable life; wealthy, famous, learned in many arts."),
        source=Citation("3HCC", 3495)),
    YogaRecord(
        id="Y.GO", name="Go Yoga", kind="other",
        condition=_GoYoga(),
        effect=("Hails from a respectable family; wealthy, of good conduct."),
        source=Citation("3HCC", 3787)),
    YogaRecord(
        id="Y.VAKCHALANA", name="Vakchalana Yoga", kind="other",
        condition=_Vakchalana(),
        effect=("A stammerer."),
        source=Citation("3HCC", 5991)),
    YogaRecord(
        id="Y.VISHAPRAYOGA", name="Vishaprayoga Yoga", kind="other",
        condition=_Vishaprayoga(),
        effect=("Subjected to poisoning."),
        source=Citation("3HCC", 6003)),
    # — tranche 4 (2026-08-09): the 3rd/4th-house block, complete-edition citations. —
    YogaRecord(
        id="Y.EKABHAGINI", name="Ekabhagini Yoga", kind="other",
        condition=_Ekabhagini(),
        effect=("Has only one sister."),
        source=Citation("3HCC", 6100)),
    YogaRecord(
        id="Y.DWADASA_SAHODARA", name="Dwadasa Sahodara Yoga", kind="other",
        condition=_DwadasaSahodara(),
        effect=("The third of twelve siblings — Raman's own remark: the yoga is typical "
                "inasmuch as it is rare."),
        source=Citation("3HCC", 6116)),
    YogaRecord(
        id="Y.PARAKRAMA", name="Parakrama Yoga", kind="other",
        condition=_Parakrama(),
        effect=("Possesses much courage."),
        source=Citation("3HCC", 6194)),
    YogaRecord(
        id="Y.SATKATHADISRAVANA", name="Satkathadisravana Yoga", kind="other",
        condition=_Satkathadisravana(),
        effect=("Interested in high-class literature and religious discourse."),
        source=Citation("3HCC", 6306)),
    YogaRecord(
        id="Y.UTTAMA_GRIHA", name="Uttama Griha Yoga", kind="other",
        condition=_NthLordWithBeneficsInKendraTrikona(4),
        effect=("Possesses good houses."),
        source=Citation("3HCC", 6320)),
    YogaRecord(
        id="Y.VICHITRA_SAUDHA", name="Vichitra Saudha Prakara Yoga", kind="other",
        condition=_FourPlanetConjunction4th10thSaturnMars(),
        effect=("Acquires innumerable mansions."),
        source=Citation("3HCC", 6358)),
    # — tranche 5 (2026-08-09): the 4th-house/mother block (189-210, the mechanical
    #   dozen). Paired combos with IDENTICAL printed results merge as Or-arms (the
    #   Sumukha-166/167 precedent); Bandhu Pujya 193/194 stay separate because Raman's
    #   Remarks distinguish their results (respected vs loved). —
    YogaRecord(
        id="Y.AYATNA_GRIHA", name="Ayatna Griha Prapta Yoga", kind="other",
        # 189 @3HCC:6404 Or 190 @3HCC:6406 — same printed result.
        condition=C.Or(_AyatnaGriha189(), _AyatnaGriha190()),
        effect=("Acquires substantial house property with hardly any effort."),
        source=Citation("3HCC", 6404)),
    YogaRecord(
        id="Y.GRIHANASA", name="Grihanasa Yoga", kind="other",
        # 191 @3HCC:6435 Or 192 @3HCC:6437 — both re-read per Raman's Remarks: the
        # "12th" is the 12th FROM THE 4TH, i.e. the 3rd house.
        condition=C.Or(_Grihanasa191(), _Grihanasa192()),
        effect=("Loses the house property."),
        source=Citation("3HCC", 6435)),
    YogaRecord(
        id="Y.BANDHU_PUJYA_193", name="Bandhu Pujya Yoga", kind="other",
        condition=_BandhuPujya193(),
        effect=("Respected by relatives and friends."),
        source=Citation("3HCC", 6459)),
    YogaRecord(
        id="Y.BANDHU_PUJYA_194", name="Bandhu Pujya Yoga", kind="other",
        condition=_BandhuPujya194(),
        effect=("Loved by relatives and friends."),
        source=Citation("3HCC", 6462)),
    YogaRecord(
        id="Y.MATRUGAMI", name="Matrugami Yoga", kind="other",
        condition=_Matrugami(),
        effect=("Raman's printed verdict: guilty of adultery with the mother — he "
                "extends 'mother' to women held in equal esteem."),
        source=Citation("3HCC", 6666)),
    YogaRecord(
        id="Y.KAPATA", name="Kapata Yoga", kind="other",
        # 202 @3HCC:6711 Or 203 @3HCC:6715 — same printed result (hypocrisy); 204 needs
        # Mandi/Gulika and stays in the Gulika queue below.
        condition=C.Or(_Kapata202(), _Kapata203()),
        effect=("Becomes a hypocrite — Raman: common in the charts of diplomats, "
                "'diplomacy always implies dignified hypocrisy'."),
        source=Citation("3HCC", 6711)),
    YogaRecord(
        id="Y.MATRU_SATRUTWA", name="Matru Satrutwa Yoga", kind="other",
        condition=_MatruSatrutwa(),
        effect=("Hates his mother."),
        source=Citation("3HCC", 6798)),
    YogaRecord(
        id="Y.VAHANA", name="Vahana Yoga", kind="other",
        # 209 @3HCC:6830 Or 210 @3HCC:6832 — same printed result.
        condition=C.Or(_Vahana209(), _Vahana210()),
        effect=("Acquires material comforts and conveyances."),
        source=Citation("3HCC", 6830)),
    # — tranche 6 (2026-08-09): clearing the queued bars — the strength-gated pair, the
    #   Matrunasa pair, Nishkapata-205, Matru Sneha, Anapathya. —
    YogaRecord(
        id="Y.MATRUDEERGHAYUR", name="Matrudeerghayur Yoga", kind="other",
        # 196 @3HCC:6535 Or 197 @3HCC:6538 — same printed result.
        condition=C.Or(_Matrudeerghayur196(), _Matrudeerghayur197()),
        effect=("The native's mother lives long."),
        source=Citation("3HCC", 6535)),
    YogaRecord(
        id="Y.MATRUNASA", name="Matrunasa Yoga", kind="other",
        # 198 @3HCC:6554 Or 199 @3HCC:6559 — same printed result.
        condition=C.Or(_Matrunasa198(), _Matrunasa199()),
        effect=("Early death of the mother — Raman grades it: all three afflictions of "
                "198 at once kill immediately after birth; Jupiter's aspect delays."),
        source=Citation("3HCC", 6554)),
    YogaRecord(
        id="Y.NISHKAPATA", name="Nishkapata Yoga", kind="other",
        # 205 @3HCC:6767 alone — 206 defers on the amsa-ladder question (see skip note).
        condition=_Nishkapata205(),
        effect=("Pure-hearted; hates secrecy and hypocrisy."),
        source=Citation("3HCC", 6767)),
    YogaRecord(
        id="Y.MATRU_SNEHA", name="Matru Sneha Yoga", kind="other",
        condition=_MatruSneha(),
        effect=("Cordial relations prevail between mother and son."),
        source=Citation("3HCC", 6812)),
    YogaRecord(
        id="Y.ANAPATHYA", name="Anapathya Yoga", kind="other",
        condition=_Anapathya(),
        effect=("Remains without issues."),
        source=Citation("3HCC", 6872)),
    # — tranche 7 (2026-08-09): the sapa (curse) block + Bahuputra, 212-221. —
    YogaRecord(
        id="Y.SARPASAPA", name="Sarpasapa Yoga", kind="arishta",
        # 212 @6891 Or 213 @6894 Or 214 @6897 Or 215 @6900 — one printed result; Raman's
        # common factor: "affliction of the 5th bhava, karaka or the lord of children by
        # Rahu". 214 carries his own Shadbala nullifier from the Remarks.
        condition=C.Or(_Sarpasapa212(), _Sarpasapa213(), _Sarpasapa214(), _Sarpasapa215()),
        effect=("Death of children attributed to the curse of serpents."),
        source=Citation("3HCC", 6891)),
    YogaRecord(
        id="Y.PITRUSAPA_SUTAKSHAYA", name="Pitrusapa Sutakshaya Yoga", kind="arishta",
        condition=_PitrusapaSutakshaya(),
        effect=("Loses issues on account of the father's wrath."),
        source=Citation("3HCC", 7013)),
    YogaRecord(
        id="Y.MATRUSAPA_SUTAKSHAYA", name="Matrusapa Sutakshaya Yoga", kind="arishta",
        condition=_MatrusapaSutakshaya(),
        effect=("Loss of children attributed to the mother's curse."),
        source=Citation("3HCC", 7155)),
    YogaRecord(
        id="Y.BHRATRUSAPA_SUTAKSHAYA", name="Bhratrusapa Sutakshaya Yoga", kind="arishta",
        condition=_BhratrusapaSutakshaya(),
        effect=("Death of children attributed to curses from brothers."),
        source=Citation("3HCC", 7200)),
    YogaRecord(
        id="Y.PRETASAPA", name="Pretasapa Yoga", kind="arishta",
        condition=_Pretasapa(),
        effect=("Death of children attributed to the curses of the departed (Pretas)."),
        source=Citation("3HCC", 7219)),
    YogaRecord(
        id="Y.BAHUPUTRA", name="Bahuputra Yoga", kind="other",
        # 220 @7285 Or 221 @7288 — same printed result.
        condition=C.Or(_Bahuputra220(), _Bahuputra221()),
        effect=("Has a large number of children."),
        source=Citation("3HCC", 7285)),
    # — tranche 8 (2026-08-09): the progeny block, 222-230 (226 deferred). —
    YogaRecord(
        id="Y.DATTAPUTRA", name="Dattaputra Yoga", kind="other",
        # 222 @7341 Or 223 @7345 — same printed result.
        condition=C.Or(_Dattaputra222(), _Dattaputra223()),
        effect=("Has adopted children."),
        source=Citation("3HCC", 7341)),
    YogaRecord(
        id="Y.APUTRA", name="Aputra Yoga", kind="other",
        condition=_Aputra(),
        effect=("Has no issues — Raman: a very general combination, never to be applied "
                "without a thorough examination of the 5th house."),
        source=Citation("3HCC", 7388)),
    YogaRecord(
        id="Y.EKAPUTRA", name="Ekaputra Yoga", kind="other",
        condition=_Ekaputra(),
        effect=("Has only one son."),
        source=Citation("3HCC", 7423)),
    YogaRecord(
        id="Y.KALANIRDESAT_PUTRA", name="Kalanirdesat Putra Yoga", kind="other",
        # 227 @7466 Or 228 @7468 — one printed result (the son's timing differs by arm:
        # 32nd/33rd year for 227, the 40th for 228, both CONDITIONAL on the directional
        # influences per Raman's Remarks).
        condition=C.Or(_KalanirdesatPutra227(), _KalanirdesatPutra228()),
        effect=("Raman assigns a season for the birth of a son (the 32nd/33rd year by "
                "227, the 40th by 228) — conditional, per his own Remarks, on the "
                "appropriate Dasa and Bhukthi operating."),
        source=Citation("3HCC", 7466)),
    YogaRecord(
        id="Y.KALANIRDESAT_PUTRANASA", name="Kalanirdesat Putranasa Yoga", kind="arishta",
        # 229 @7487 Or 230 @7494 — one printed result; Raman notes 229 in practice has
        # shown still-births or loss within the first year, 230 a few dying and a few
        # surviving.
        condition=C.Or(_KalanirdesatPutranasa229(), _KalanirdesatPutranasa230()),
        effect=("Loss of issues — Raman assigns the 32nd year (229) and the 32nd or 40th "
                "(230), and records that 229 in his own collection has shown the severer "
                "form."),
        source=Citation("3HCC", 7487)),
    # — tranche 9 (2026-08-09): the buddhi + marriage block, 231-240 (234 deferred). —
    YogaRecord(
        id="Y.BUDDHIMATURYA", name="Buddhimaturya Yoga", kind="other",
        condition=_Buddhimaturya(),
        effect=("A person of great intelligence and character."),
        source=Citation("3HCC", 7544)),
    YogaRecord(
        id="Y.THEEVRABUDDHI", name="Theevrabuddhi Yoga", kind="other",
        condition=_Theevrabuddhi(),
        effect=("Precociously intelligent — Raman: usually found in the horoscopes of "
                "geniuses."),
        source=Citation("3HCC", 7625)),
    YogaRecord(
        id="Y.BUDDHI_JADA", name="Buddhi Jada Yoga", kind="other",
        condition=_BuddhiJada(),
        effect=("Dullness of intellect."),
        source=Citation("3HCC", 7657)),
    YogaRecord(
        id="Y.PUTRA_SUKHA", name="Putra Sukha Yoga", kind="other",
        condition=_PutraSukha(),
        effect=("Happiness on account of children."),
        source=Citation("3HCC", 7787)),
    YogaRecord(
        id="Y.JARA", name="Jara Yoga", kind="other",
        condition=_Jara(),
        effect=("Extra-marital attachments — encoded WITH Raman's own narrowing (the "
                "7th lord must be Mars or Venus) without which he refuses the "
                "conclusion."),
        source=Citation("3HCC", 7805)),
    YogaRecord(
        id="Y.JARAJAPUTRA", name="Jarajaputra Yoga", kind="other",
        condition=_Jarajaputra(),
        effect=("Raman's printed verdict on the 5th/6th/7th-lord conjunction: issues "
                "not of the native's own line."),
        source=Citation("3HCC", 7848)),
    YogaRecord(
        id="Y.BAHU_STREE", name="Bahu Stree Yoga", kind="other",
        condition=_BahuStree(),
        effect=("Intimacy with a number of women — Raman's own practical reading of "
                "'any number of wives'."),
        source=Citation("3HCC", 7866)),
    YogaRecord(
        id="Y.SATKALATRA", name="Satkalatra Yoga", kind="other",
        condition=_Satkalatra(),
        effect=("The spouse is noble and virtuous."),
        source=Citation("3HCC", 7917)),
    YogaRecord(
        id="Y.BHAGA_CHUMBANA", name="Bhaga Chumbana Yoga", kind="other",
        condition=_BhagaChumbana(),
        effect=("Raman's printed verdict: indulges in intimate caressing of the "
                "partner."),
        source=Citation("3HCC", 7981)),
    # — tranche 10 (2026-08-09): fortune + the Raja group opening, 241-250 (248 deferred). —
    YogaRecord(
        id="Y.BHAGYA", name="Bhagya Yoga", kind="dhana",
        condition=_Bhagya(),
        effect=("Extremely fortunate, pleasure-loving and rich."),
        source=Citation("3HCC", 7989)),
    YogaRecord(
        id="Y.JANANATPURVAM_PITRU_MARANA", name="Jananatpurvam Pitru Marana Yoga",
        kind="other",
        condition=_JananatpurvamPitruMarana(),
        effect=("Born a posthumous child."),
        source=Citation("3HCC", 8018)),
    YogaRecord(
        id="Y.DHATRUTWA", name="Dhatrutwa Yoga", kind="other",
        condition=_Dhatrutwa(),
        effect=("An embodiment of generosity — Raman reserves the yoga for the "
                "sincerely humanitarian."),
        source=Citation("3HCC", 8044)),
    YogaRecord(
        id="Y.APAKEERTI", name="Apakeerti Yoga", kind="other",
        condition=_Apakeerti(),
        effect=("Suffers a bad reputation."),
        source=Citation("3HCC", 8126)),
    YogaRecord(
        id="Y.RAJA_245", name="Raja Yoga", kind="raja",
        condition=_Raja245(),
        effect=("Becomes a famous ruler."),
        source=Citation("3HCC", 8154)),
    YogaRecord(
        id="Y.RAJA_246", name="Raja Yoga", kind="raja",
        condition=_Raja246(),
        effect=("Attains a position equal to a ruler, with the insignia of royalty."),
        source=Citation("3HCC", 8157)),
    YogaRecord(
        id="Y.RAJA_247", name="Raja Yoga", kind="raja",
        condition=_Raja247(),
        effect=("Though born in an ordinary family, rises to rule."),
        source=Citation("3HCC", 8168)),
    YogaRecord(
        id="Y.RAJA_249", name="Raja Yoga", kind="raja",
        condition=_Raja249(),
        effect=("Becomes a ruler or an equal to one."),
        source=Citation("3HCC", 8315)),
    YogaRecord(
        id="Y.RAJA_250", name="Neechabhanga Raja Yoga", kind="raja",
        condition=_Raja250(),
        effect=("Becomes a ruler or an equal to one — elevation from ordinary birth, "
                "per Raman functioning much like the other Raja yogas."),
        source=Citation("3HCC", 8318)),
    # — tranche 11 (2026-08-10): the Raja group completes, 251-263 (256 deferred). —
    YogaRecord(
        id="Y.RAJA_251", name="Raja Yoga", kind="raja",
        condition=_Raja251(),
        effect=("A ruler or an equal in wealth, power and influence."),
        source=Citation("3HCC", 8416)),
    YogaRecord(
        id="Y.RAJA_252", name="Raja Yoga", kind="raja",
        condition=_Raja252(),
        effect=("A ruler or an equal in wealth, power and influence."),
        source=Citation("3HCC", 8419)),
    YogaRecord(
        id="Y.RAJA_253", name="Raja Yoga", kind="raja",
        condition=_Raja253(),
        effect=("A ruler or an equal in wealth, power and influence."),
        source=Citation("3HCC", 8421)),
    YogaRecord(
        id="Y.RAJA_254", name="Raja Yoga", kind="raja",
        condition=_Raja254(),
        effect=("Becomes a ruler or an equal to one."),
        source=Citation("3HCC", 8548)),
    YogaRecord(
        id="Y.RAJA_255", name="Raja Yoga", kind="raja",
        condition=_Raja255(),
        effect=("Becomes a ruler or an equal to one — though Raman records that in the "
                "dozen charts of his own collection the yoga proved nominal."),
        source=Citation("3HCC", 8555)),
    YogaRecord(
        id="Y.RAJA_257", name="Raja Yoga", kind="raja",
        condition=_Raja257(),
        effect=("Becomes a ruler or an equal to one — Gajakesari plus Jupiter's aspect "
                "on Lagna, as Raman reads it."),
        source=Citation("3HCC", 8560)),
    YogaRecord(
        id="Y.RAJA_258", name="Raja Yoga", kind="raja",
        condition=_Raja258(),
        effect=("Becomes a ruler or an equal to one — Raman's own caveat: not a "
                "powerful Raja yoga, quite a common combination."),
        source=Citation("3HCC", 8563)),
    YogaRecord(
        id="Y.RAJA_259", name="Raja Yoga", kind="raja",
        condition=_Raja259(),
        effect=("Becomes a commander or an equal to a ruler — from Sambhu Hora "
                "Prakasha; Raman muses a democratic tyrant may be born under it."),
        source=Citation("3HCC", 8723)),
    YogaRecord(
        id="Y.RAJA_260", name="Raja Yoga", kind="raja",
        condition=_Raja260(),
        effect=("Becomes a ruler or an equal to one."),
        source=Citation("3HCC", 8743)),
    YogaRecord(
        id="Y.RAJA_261", name="Raja Yoga", kind="raja",
        condition=_Raja261(),
        effect=("Becomes a ruler or an equal to one — Raman suspects the double evils "
                "cancel mutually, and asks his readers for tested charts."),
        source=Citation("3HCC", 8748)),
    YogaRecord(
        id="Y.RAJA_262", name="Raja Yoga", kind="raja",
        condition=_Raja262(),
        effect=("A great man or a respected ruler."),
        source=Citation("3HCC", 8828)),
    YogaRecord(
        id="Y.RAJA_263", name="Raja Yoga", kind="raja",
        condition=_Raja263(),
        effect=("A great man or a respected ruler."),
        source=Citation("3HCC", 8829)),
    # — tranche 12 (2026-08-11): the Arishta chapter's mechanical half, 265-278. —
    YogaRecord(
        id="Y.VRANA", name="Vrana Yoga", kind="arishta",
        condition=_Vrana(),
        effect=("Raman's printed verdict: suffers from malignant disease — he cautions "
                "a literal application is not recommended, and the planet involved "
                "locates the seat."),
        source=Citation("3HCC", 8914)),
    YogaRecord(
        id="Y.SISNAVYADHI", name="Sisnavyadhi Yoga", kind="arishta",
        condition=_Sisnavyadhi(),
        effect=("Suffers from diseases of the sexual organs."),
        source=Citation("3HCC", 8987)),
    YogaRecord(
        id="Y.KALATRASHANDA", name="Kalatrashanda Yoga", kind="arishta",
        condition=_Kalatrashanda(),
        effect=("Raman's printed verdict on the spouse's frigidity — with his own "
                "caveat that he has not tested the yoga and cannot endorse its "
                "applicability."),
        source=Citation("3HCC", 9026)),
    YogaRecord(
        id="Y.KUSHTAROGA", name="Kushtaroga Yoga", kind="arishta",
        # 268 @9044 Or 269 @9046 — same printed result.
        condition=C.Or(_Kushtaroga268(), _Kushtaroga269()),
        effect=("Raman's printed verdict: suffers from leprosy — to be applied only "
                "with the 6th bhava carefully weighed, per his own caution."),
        source=Citation("3HCC", 9044)),
    YogaRecord(
        id="Y.BANDHANA", name="Bandhana Yoga", kind="arishta",
        condition=_Bandhana(),
        effect=("Incarceration — Raman: Saturn as Lagna lord lessens or neutralizes "
                "the evil, and benefic aspects lessen it."),
        source=Citation("3HCC", 9302)),
    YogaRecord(
        id="Y.DURMARANA", name="Durmarana Yoga", kind="arishta",
        condition=_Durmarana(),
        effect=("Raman's printed verdict: an unnatural manner of death is indicated."),
        source=Citation("3HCC", 9387)),
    YogaRecord(
        id="Y.PEENASAROGA", name="Peenasaroga Yoga", kind="arishta",
        condition=_Peenasaroga(),
        effect=("Suffers from disease of the nose (inflammation of the Schneiderian "
                "membrane)."),
        source=Citation("3HCC", 9495)),
)

# ── first-tranche skips (2026-08-08), each with the reason, so the next encoder does not
# re-tread. MAHABHAGYA (3HCH:1490): needs the native's GENDER and day/night birth — gender is
# not modelled on RamanChart, and a gender-blind approximation is the silent approximation the
# Prime Directive forbids. PUSHKALA (3HCH:1527): "house of an intimate friend" (compound
# relations) plus two strength gates in one sentence. SANKHA (3HCH:1735) and BHERI
# (3HCH:1776): the SAME yogas as the measured-deferred HPA-20 pair above (50%/38% fire rates
# on the golden corpus — common by construction; the 3HC wording changes nothing about the
# base rate). BHARATHI (3HCH:1678): "the lords of the navamsas occupied by the lords of the
# 2nd, 5th and 11th should be exalted" — ALL-three vs ANY-one is undisambiguated and the
# readings differ by orders of magnitude (the Lakshmi precedent exactly).
#
# Tranche-2 skips (2026-08-09): DURMUKHA-169 needs Gulika (not computed); PARANNABHOJANA
# (172) has its definition split across a page-break chart figure in the complete-edition
# OCR — needs the manual audit before its clauses can be trusted. LAKSHMI GRADUATED tranche
# 2 (26/225 geometric, 12/225 gated, 5.3%); SUMUKHA-167 GRADUATED tranche 3 when the
# varga-attainment primitive landed.
#
# Tranche-3 skips (2026-08-09): SARPAGANDA (174) needs Mandi/Gulika — parked pending a
# scope ruling (the only Raman-citable computation is in his Prasna Marga translation, which
# is walled-horary; using its mechanics for a natal yoga is a decision, not a default).
# SODARANASA (178): "occupy the 8th (3rd, 5th or 7th) house" — the parenthetical is
# OCR-garbled and the candidate readings differ materially; manual audit first.
# Tranche-12 skips (2026-08-11) — the Arishta chapter is D60-HEAVY, and the SHASHTIAMSA
# PRIMITIVE is now the highest-value single unlock in the queue (it gates 195, 201, 234,
# 248, 264, 272, 273, 275, 276, 277 — ten combos — plus the Mandi overlaps):
#   GALAKARNA (264): Mandi AND Preta-Puriha shashtiamsa — the double bar.
#   KSHAYAROGA (270): Mandi in a kendra — the Gulika queue.
#   KARASCHEDA (272): Raman's own Remark REFUSES the bare Saturn-9/Jupiter-3 form ("the
#     mere presence... cannot make one lose one's limbs") and requires heavy affliction
#     in cruel shashtiamsas — encoding bare would over-fire against his explicit word.
#   SIRACHCHEDA (273): Sun/Saturn joined with Rahu IN a cruel shashtiamsa (the same-D60
#     reading Raman quotes from the original with his footnote).
#   YUDDHE MARANA (275): "cruel amsas" ambiguous (navamsa vs shashtiamsa) + Mandi.
#   SANGHATAKA MARANA (276/277): "evil sub-divisions" / "evil amsas" — same ambiguity.
#   The D60 build has its source named by Raman himself in 264's Remark: "For details
#   about shashtiamsas, see my book A MANUAL OF HINDU ASTROLOGY" — the MANUAL tag is on
#   disk and registered. Bar: build the D60 table from the Manual, with the cruel/benign
#   classification cited to it, and a reachability measurement (the varga_attainment
#   precedent).
# Tranche-11 skip (2026-08-10): RAJA-256 (10th lord in the 9th in exalted/friendly
# navamsa "having attained Uttamamsa"). ITS OWN REMARK SETTLES THE COUNT: "If a planet is
# in its own varga three times, it is said to be in Uttamamsa" — so with 234's Gopura=4,
# the 3HC ladder is confirmed as the Uttama-3/Gopura-4 (shadvarga-style) ladder, NOT the
# GBB table (Parvatha-3/Gopuram-8) in primitives/varga_attainment.py. What remains open is
# the VARGA SET the count runs over (234's worked example counts rasi/drekkana/
# chaturthamsa/saptamsa — chaturthamsa is not a shadvarga member). Bar: fix the set from
# the texts, then 206/234/256 all unlock together and Sumukha-167's GBB-based arm gets
# audited against its own source.
# Tranche-10 skip (2026-08-09): RAJA-248 (Kumbha lagna, Venus in it, four planets exalted
# "without occupying evil navamsas or shastiamsas") carries the D60 clause as a NEGATIVE
# filter on an AND — omitting it would fire where Raman would not (his own Remark: in evil
# navamsas/shashtiamsas "the yoga does not function and the native may become a tyrant").
# Over-firing is the bad direction; parked on the same D60 bar as 195/201/234.
# Tranche-9 skip (2026-08-09): THRIKALAGNANA (234) needs the SHASHTIAMSA (D60) —
# Mrudwamsa is its 19th part in odd signs / 42nd in even — which is unmodelled (same bar
# as 195/201). Its second arm carries MATERIAL EVIDENCE for the 206 ladder question:
# Raman here defines Gopuramsa as own-varga FOUR times, worked over rasi/drekkana/
# chaturthamsa/saptamsa ("Suppose Jupiter is in the first degree of Dhanus... having
# attained his Swavarga four times") — 3HC's ladder is therefore NOT the GBB table
# (Gopuramsam at count 8) that primitives/varga_attainment.py encodes, and the two
# Gopuramsa-consuming sites (Sumukha-167 via attains_gopuramsa, and any future 206/234
# encoding) now face a measured identity question: which ladder does WHICH Raman text
# mean. Settle before touching either; the varga-set he counts over (chaturthamsa is not
# a shadvarga member) is part of the same audit.
# Tranche-8 skip (2026-08-09): SUPUTRA (226) requires Jupiter as 5th lord (Simha/
# Vrischika only, per Raman) AND "the Sun occupies a favourable position" — the text never
# defines "favourable" (dignity? kendra/trikona? benefic vargas?), and Raman's Remarks
# muse about benefic vargas without fixing a criterion. Bar: a doctrine reading that
# settles what Raman means by the Sun's favourable position, with a citation.
# Tranche-7 note (2026-08-09): PITRUSAPA-216's Remarks list three FURTHER variant
# dispositions ("The following dispositions of planets also constitute Yoga No. 216"):
# (a) Sun as 5th lord in a trine hemmed/aspected by malefics (Mesha only), (b) Jupiter in
# Leo + 5th lord with the Sun + malefics in the 5th and Lagna, (c) Mars as 9th lord with
# the 5th lord + malefics in Lagna and the trikonas. Queued as Or-arm extensions — the
# definition's three arms are encoded; the variants await their own fire/silent pairs.
# Tranche-6 note (2026-08-09): NISHKAPATA-206 defers on a LADDER-IDENTITY question, not a
# missing primitive. Its "occupy Parvata or Uttamamsa" names amsa-attainment rungs, but
# Raman's own GBB table (encoded verbatim in primitives/varga_attainment.py) has
# Parvathamsa at count 3 and NO "Uttamamsa" rung at all — while the BPHS shadvarga ladder
# names Uttama at 3 and Paravata at 6. Which ladder 3HC-206 means is a doctrine reading,
# and encoding the wrong one would misattribute Raman. Bar: settle the ladder identity
# from the 3HC text or GBB cross-reference, then map the two titles to counts.
# Tranche-5 skips (2026-08-09), each with its bar:
#   KAPATA-204 needs Mandi/Gulika -> the Gulika queue (scope ruling pending, user's call).
#   BANDHUBHISTHYAKTHA (195) and SAHODAREESANGAMA (201) carry an evil/cruel-SHASHTIAMSA
#     (D60) arm — the varga is unmodelled; Raman himself cautions on 195 ("much reliance
#     cannot be placed... very general nature"). Bar: a D60 primitive, built and measured.
#   MATRUDEERGHAYUR (196/197) and ANAPATHYA (211) are STRENGTH-gated ("strong Moon",
#     "weak" Jupiter/lords) — encoding needs the deliberate B1 effective_strength
#     treatment (Lakshmi/Go precedent) plus a patched-gate fire test; queued, not grey.
#   MATRUNASA (198/199): 198 needs Papakartari on the Moon (encodable next tranche);
#     199's double navamsa chain has Raman's worked examples (charts 90/91) as its spec.
#   NISHKAPATA (205/206): 206 turns on Parvata/Uttamamsa — varga_attainment's ladder is
#     built, so the bar is only mapping Raman's amsa titles to counts; queued.
#   MATRU SNEHA (208) needs TATKALIKA (temporal) friendship — dignity_state_compound
#     models it; queued pending a fixture design that exercises both friendship layers.
# Tranche-4 skips: SAPTHASANKHYA SAHODARA (181) and the YUDDHAT pair (184/185) read on
# from clauses the page-break OCR interleaves with chart figures; YUDDHA PRAVEENA (183) is a
# navamsa-of-navamsa double chain whose antecedent ("the planet who owns the navamsa in
# which...") is ambiguous in the printed sentence — manual audit before encoding.
#
# BHOJANA SOUKHYA (170) and ANNADANA (171) are now a MEASURED deferral, the sharpest kind:
# both demand the 2nd lord in VAISESHIKAMSA — rung 12 of Raman's GBB amsa ladder — and a
# 0.05-degree longitude scan over the engine's shodasavarga shows rung 12 is unreachable for
# most planets under EVERY counting basis measured (own-sign: only Mars; own+exalted+moola:
# only Sun and Mars). Raman's worked example demonstrates the count on the saptavarga, where
# twelve is arithmetically impossible. Encoding any reading would either be dead code or a
# silent redefinition of his count. Full record: primitives/varga_attainment.py, which
# deliberately does not export a vaiseshikamsa predicate.
# DEFERRED HPA-20 yogas — RE-ATTEMPTED 2026-08-03 with the B1 effective-strength measure and
# still deferred, now for a MEASURED reason. The original deferral blamed the is_powerful proxy
# ("re-attempt once an effective-strength measure exists"); the re-attempt disproves that
# diagnosis. Fire rates on the full 225-chart golden corpus, old proxy -> effective gate
# (band=="strong" AND not decisively_weak, i.e. strictly tighter):
#   Y.SHANKHA (HPA-20:77)  126/225 (56%) -> 113/225 (50%)
#   Y.KAHALA  (HPA-20:151)  76/225 (34%) ->  67/225 (30%)
#   Y.BHERI   (HPA-20:96)   94/225 (42%) ->  85/225 (38%)
# The gate is NOT the discriminator: the geometric conditions themselves are common by
# construction (a mutual-kendra pair holds ~1/3 of the time; a lord in a movable sign ~1/3), so
# no strength refinement can make these rare. They stay deferred until a fundamentally more
# specific reading of Raman's text emerges — not until a better strength measure does.
#   Y.LAKSHMI (HPA-20:190) — the strict arm is genuinely rare (7/225 geometric, 3/225 gated),
#     but its rarity rests on ONE resolution of the sentence's comma-parse ("Lord of the 9th in
#     a quadrant, moolathrikona or in deep exaltation or lord of lagna in conjunction with 9th
#     lord" — kendra AND dignity? or kendra OR dignity?). Raman does not disambiguate, the two
#     readings differ by an order of magnitude in fire rate, and registering one would be
#     choosing doctrine for him. Deferred on parse ambiguity, not on strength.
#     UPDATE 2026-08-08: Raman's OWN 3HC wording resolves the parse — "the lord of the 9th
#     occupies own or exaltation sign IDENTICAL WITH a Kendra or Thrikona" (3HCH:1557):
#     dignity AND placement, conjunctive, unambiguous. What remains before encoding is only
#     the fire-rate measurement on the golden corpus with the lagna-lord strength gate — the
#     same measurement discipline the SHANKHA/KAHALA/BHERI re-attempt used.


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
