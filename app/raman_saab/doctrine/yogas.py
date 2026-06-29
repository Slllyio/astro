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
)
# DEFERRED HPA-20 yogas (over-fire under the current primitives; documented limits):
#   Y.SHANKHA (HPA-20:77), Y.KAHALA (HPA-20:151) — hinge on a holistic "powerful lord" the
#     Shadbala is_powerful proxy reads too liberally (Shankha 102/164, Kahala 48/164). Re-attempt
#     once an effective-strength (combust/dignity-adjusted) measure exists (DOCTRINE_BACKLOG B1).
#   Y.LAKSHMI (HPA-20:190) — even the strict dignity arm (9th-lord exalt/moolatrikona) fires
#     16/164; its discriminating form needs lagna-lord involvement the geometry can't isolate
#     (matches the prior B5 finding). Re-attempt with B1.


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
