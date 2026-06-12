"""House 1 — Moon/mind rules (Chandra-Lagna dispositions and mental indications).

Raman's governing instruction: "The mental disposition should always be judged by
reference to the Moon and his disposition." (HTJAH-I:1231)

All rules carry frame="MOON" and group="moon_mind".  Signification is "self" at
Stage 1 (coarse); the "mind" re-tag lands in Stage 1c.

Source span: HTJAH-I:1231-1240 (general Moon/mind doctrine) + per-sign mental
tendency paragraphs HTJAH-I:1242-1465.

Rule-id convention: H1.M.<tag>
  MD   — master-doctrine (introductory instruction)
  G1   — General rule 1 (disease/accident: planets configured with Moon)
  G2   — General rule 2 (violent/sudden death: Sun+Moon+Lagna all multi-afflicted)
  G3   — General rule 3 (distortions/lameness: nodes in angles with luminaries)
  S01-S12 — per-sign mental-tendency delineations (Aries..Pisces)

Kind breakdown:
  - MD, G1, S01-S12: descriptive (narrative outcomes surfaced by placement)
  - G2, G3: evaluable (boolean conditions encodable with existing predicates)

G7 ambiguity note: G3 requires Rahu AND Ketu both in {1,4,7,10} WITH the angles
being specifically Aries/Taurus/Scorpio/Capricorn (signs 1,2,8,10).  The existing
predicate set has no SignIsAngle-class predicate, so this is encoded with
InSign("Rahu"/"Ketu", ...) disjunction + InSign("Sun"/"Moon", ...) requirement.
The corpus text (line 1238-1240) is unambiguous about the four signs; the
condition tree therefore tests that BOTH nodes are in those four signs AND at
least one luminary shares one of them.  See ambiguity note in StructuredOutput.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine import drishti
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation

# Signs that Raman calls "angles" for the G3 node rule:
# Aries=1, Taurus=2, Scorpio=8, Capricorn=10  (HTJAH-I:1239)
_NODE_ANGLE_SIGNS: tuple[int, ...] = (1, 2, 8, 10)


def _node_in_angles(planet: str) -> C.Condition:
    """Planet (Rahu or Ketu) occupies one of the four node-angle signs."""
    return C.Or(*[C.InSign(planet, s) for s in _NODE_ANGLE_SIGNS])


def _luminary_in_angles() -> C.Condition:
    """At least one luminary (Sun or Moon) is in one of the four node-angle signs."""
    sun_in = C.Or(*[C.InSign("Sun", s) for s in _NODE_ANGLE_SIGNS])
    moon_in = C.Or(*[C.InSign("Moon", s) for s in _NODE_ANGLE_SIGNS])
    return C.Or(sun_in, moon_in)


# G2: Sun + Moon + Lagna all afflicted by ≥2 malefics.
# "Afflicted" here means a malefic CONJOINS or casts true Vedic drishti — computed
# via the canonical drishti engine (whole-sign aspects, with Mars 4/8, Saturn 3/10,
# Jupiter 5/9, nodes 7th-only per the Raman Saab lock), NOT a hand-rolled house-set
# proxy.  Conjunction (same rasi-house / same sign) is added explicitly because
# drishti.aspects_house counts dist-1 as occupancy, not aspect.
# The available malefic afflicters are Sun, Mars, Saturn, Rahu, Ketu.
# "Lagna afflicted" = ≥2 malefics afflict house 1; "Sun/Moon afflicted" = ≥2
# malefics afflict the Sun / Moon (conjunction counted in either case).
_MALEFICS = ("Sun", "Mars", "Saturn", "Rahu", "Ketu")


class _AfflictsPlanet(C.Condition):
    """`afflicter` conjoins (same sign) OR casts a true whole-sign drishti on
    `target` — the Raman drishti engine (Mars 4/8, Saturn 3/10, Jupiter 5/9,
    nodes 7th-only).  None-safe: a missing planet on a sparse chart -> False."""

    def __init__(self, afflicter: str, target: str) -> None:
        self.afflicter = afflicter
        self.target = target

    def evaluate(self, ctx: C.EvalContext) -> bool:
        a = ctx.chart.planets.get(self.afflicter)
        t = ctx.chart.planets.get(self.target)
        if a is None or t is None or self.afflicter == self.target:
            return False
        if a.rasi_house == t.rasi_house:          # conjunction
            return True
        return drishti.aspects_planet(self.afflicter, self.target, ctx.chart)


class _AfflictsLagna(C.Condition):
    """`afflicter` occupies house 1 (conjunction with the Lagna) OR casts a true
    whole-sign drishti on house 1 via the Raman drishti engine.  Replaces the old
    {1,4,7,8}-house-set proxy (which mis-modelled Saturn's 3/10 and Jupiter's 5/9
    and wrongly fired on house 8 for non-special planets).  None-safe."""

    def __init__(self, afflicter: str) -> None:
        self.afflicter = afflicter

    def evaluate(self, ctx: C.EvalContext) -> bool:
        a = ctx.chart.planets.get(self.afflicter)
        if a is None:
            return False
        if a.rasi_house == 1:                       # in the Lagna = conjunction
            return True
        return drishti.aspects_house(self.afflicter, 1, ctx.chart)


def _aspects_moon(planet: str) -> C.Condition:
    return _AfflictsPlanet(planet, "Moon")


def _aspects_sun(planet: str) -> C.Condition:
    return _AfflictsPlanet(planet, "Sun")


def _aspects_lagna(planet: str) -> C.Condition:
    return _AfflictsLagna(planet)


_g2_moon_afflicted = C.AtLeastN(2, [_aspects_moon(p) for p in _MALEFICS])
_g2_sun_afflicted = C.AtLeastN(2, [_aspects_sun(p) for p in _MALEFICS])
_g2_lagna_afflicted = C.AtLeastN(2, [_aspects_lagna(p) for p in _MALEFICS])


RULES: Final[tuple[RuleRecord, ...]] = (

    # ── Master-doctrine rule ───────────────────────────────────────────────────
    RuleRecord(
        id="H1.M.MD", house=1, signification="self", group="moon_mind",
        kind="descriptive", condition=None,
        fortified="mental disposition determined by reference to the Moon and his "
                  "disposition; the Moon-sign and planets configured with the Moon "
                  "are the primary indicators of mind",
        afflicted=None,
        frame="MOON", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 1231)),

    # ── General Moon-frame rules ───────────────────────────────────────────────
    RuleRecord(
        id="H1.M.G1", house=1, signification="self", group="moon_mind",
        kind="descriptive", condition=None,
        fortified="health and accident tendency read from planets rising/setting "
                  "and those configured with the Moon",
        afflicted="liability to diseases and accidents — planets afflicting the Moon "
                  "or rising/setting at birth indicate bodily vulnerability",
        frame="MOON", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 1236)),

    RuleRecord(
        # The CONDITION encodes the affliction (Sun+Moon+Lagna each hit by >=2
        # malefics), so this rule only ever fires in the malefic case. fortified=None
        # (mirrors the H1.C.26a/27/28 pattern) so rule_firing._branch surfaces the
        # AFFLICTED text — never a misleading "no violent death" claim.
        id="H1.M.G2", house=1, signification="self", group="moon_mind",
        kind="evaluable",
        condition=C.And(_g2_sun_afflicted, _g2_moon_afflicted, _g2_lagna_afflicted),
        fortified=None,
        afflicted="liability to accidents and violent or sudden death — Sun, Moon, "
                  "and ascendant are all afflicted by more than one malefic",
        frame="MOON", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 1237)),

    RuleRecord(
        # The CONDITION encodes the affliction (both nodes in angles WITH a
        # luminary), so this rule only ever fires in the malefic case.
        # fortified=None so the AFFLICTED text surfaces, never "no bodily distortion".
        id="H1.M.G3", house=1, signification="self", group="moon_mind",
        kind="evaluable",
        condition=C.And(
            _node_in_angles("Rahu"),
            _node_in_angles("Ketu"),
            _luminary_in_angles(),
        ),
        fortified=None,
        afflicted="body afflicted with distortions, lameness, or even paralysis — "
                  "Rahu and Ketu in angles (Aries/Taurus/Scorpio/Capricorn) with "
                  "the Sun and the Moon",
        frame="MOON", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 1238)),

    # ── Per-sign mental-tendency delineations (MOON frame, descriptive) ───────
    # Condition: Moon in that sign (InHouseFrom("Moon","MOON",1) is trivially True;
    # the discriminating predicate is InSign("Moon", sign_number)).
    RuleRecord(
        id="H1.M.S01", house=1, signification="self", group="moon_mind",
        kind="evaluable",
        condition=C.InSign("Moon", 1),
        fortified="independent thinking, courageous and sensitive",
        afflicted=None,
        frame="MOON", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 1244)),

    RuleRecord(
        id="H1.M.S02", house=1, signification="self", group="moon_mind",
        kind="evaluable",
        condition=C.InSign("Moon", 2),
        fortified="obstinate, proud and ambitious; easily accessible to adulation "
                  "but affectionate and loving; sometimes unreasonable, prejudiced "
                  "and stubborn",
        afflicted=None,
        frame="MOON", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 1260)),

    RuleRecord(
        id="H1.M.S03", house=1, signification="self", group="moon_mind",
        kind="evaluable",
        condition=C.InSign("Moon", 3),
        fortified="wavering mind; fond of writing and reading; ingenious and "
                  "quick-witted; vivacious and inconsistent; nervous and restless",
        afflicted=None,
        frame="MOON", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 1278)),

    RuleRecord(
        id="H1.M.S04", house=1, signification="self", group="moon_mind",
        kind="evaluable",
        condition=C.InSign("Moon", 4),
        fortified="extremely sensitive, inquisitive, nervous and restless; "
                  "interested in music and dexterous",
        afflicted=None,
        frame="MOON", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 1296)),

    RuleRecord(
        id="H1.M.S05", house=1, signification="self", group="moon_mind",
        kind="evaluable",
        condition=C.InSign("Moon", 5),
        fortified="ambitious and avaricious; warm-hearted; liking for art, "
                  "literature and music; cheerful and un-impulsive",
        afflicted=None,
        frame="MOON", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 1312)),

    RuleRecord(
        id="H1.M.S06", house=1, signification="self", group="moon_mind",
        kind="evaluable",
        condition=C.InSign("Moon", 6),
        fortified="impulsive, emotional and fond of learning; love of music and "
                  "fine arts; lacks self-confidence; methodical and ingenious with "
                  "active mind",
        afflicted=None,
        frame="MOON", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 1330)),

    RuleRecord(
        id="H1.M.S07", house=1, signification="self", group="moon_mind",
        kind="evaluable",
        condition=C.InSign("Moon", 7),
        fortified="idealistic, quick-witted, vindictive, forceful and positive",
        afflicted=None,
        frame="MOON", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 1347)),

    RuleRecord(
        id="H1.M.S08", house=1, signification="self", group="moon_mind",
        kind="evaluable",
        condition=C.InSign("Moon", 8),
        fortified="sarcastic and impulsive; interested in occult forms of study; "
                  "possesses a subtle mind, hard to influence",
        afflicted=None,
        frame="MOON", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 1369)),

    RuleRecord(
        id="H1.M.S09", house=1, signification="self", group="moon_mind",
        kind="evaluable",
        condition=C.InSign("Moon", 9),
        fortified="inclination for philosophy and occult studies; humane and "
                  "somewhat impulsive; generally active and enterprising",
        afflicted=None,
        frame="MOON", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 1389)),

    RuleRecord(
        id="H1.M.S10", house=1, signification="self", group="moon_mind",
        kind="evaluable",
        condition=C.InSign("Moon", 10),
        fortified="stoical to miseries of life; possessed of sympathy, generosity "
                  "and philanthropy; self-willed, strong in purpose, secretive and "
                  "vindictive; cunning and determined",
        afflicted=None,
        frame="MOON", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 1407)),

    RuleRecord(
        id="H1.M.S11", house=1, signification="self", group="moon_mind",
        kind="evaluable",
        condition=C.InSign("Moon", 11),
        fortified="great teachers, writers and lecturers (if sign free from "
                  "affliction); reserved; peevish when provoked; generous-hearted; "
                  "highly sympathetic; intelligent with good memory",
        afflicted=None,
        frame="MOON", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 1428)),

    RuleRecord(
        id="H1.M.S12", house=1, signification="self", group="moon_mind",
        kind="evaluable",
        condition=C.InSign("Moon", 12),
        fortified="stubborn, psychically receptive, highly religious, stoical, "
                  "bigoted and God-fearing",
        afflicted=None,
        frame="MOON", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 1452)),
)
