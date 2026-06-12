"""House 1 — constitution rules #13-#19: Sushka (dry) and watery counterweights.

Source: HTJAH-I:1105-1114 (corpus on disk).
Methodology anchor: docs/raman_saab/methodology/house_01_lagna.md
§ "Constitution / Sushka (dry-planet) rules — consolidated".

Rules encoded
-------------
#13  H1.B.13  Sushka planet in Lagna → lean                           (evaluable)
#14  H1.B.14  Sushka rasi rising → emaciated                          (evaluable)
#15  H1.B.15  Lord of Lagna conjunct a Sushka planet → lean/emaciated (evaluable)
#16  H1.B.16  Watery rasi rising with good (benefic) planets → corpulent
                                                                        (evaluable)
#17  H1.B.17  Ascendant lord is a watery planet, strong & well-conjoined
              → stout                                                   (evaluable)
#18  H1.B.18  Lagna owned by a benefic AND lord of the Navamsha
              occupied by the Lagna-lord is in a watery sign → corpulent
                                                                        (evaluable)
#19  H1.B.19  Jupiter in Lagna, OR Jupiter aspects Lagna from a watery
              sign, OR Lagna is a watery sign with benefics → stout    (evaluable)

Counts: 7 evaluable, 0 descriptive-deferred.

Local Condition subclasses (plain functions SignIsSushka / SignIsWatery in
conditions.py accept an int, not an EvalContext; following the yogas.py
precedent, they are wrapped here rather than modifying conditions.py):

    _LagnaIsSushka                       — asc_sign in SUSHKA_SIGNS
    _LagnaIsWatery                       — asc_sign in WATERY_SIGNS
    _LagnaLordIsWatery                   — lord of Lagna is Moon or Venus
    _LagnaOwnedByBenefic                 — lord of Lagna is a natural benefic
    _LagnaLordConjunctSushkaPlanet       — lord of Lagna shares a rasi with any
                                           of Sun, Mars, Saturn (rule #15)
    _NavamshaLordOfLagnaLordIsWatery     — D9-sign lord of Lagna-lord is in a
                                           watery D1 sign (rule #18 D9 arm)
    _JupiterAspectsLagnaFromWaterySign   — Jupiter in watery sign AND aspects
                                           Lagna (rule #19 second arm)

No conditions.py, significations.py, house_template.py, goldens, baselines,
or snapshots were modified by this module.
"""
from __future__ import annotations

import logging
from typing import Final

from app.raman_saab.chart.constants import SIGN_LORDS
from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation
from app.raman_saab.primitives.functional_nature import NATURAL_BENEFICS

logger = logging.getLogger(__name__)

# ── corpus citation anchors ───────────────────────────────────────────────────
# Each line number is the first line of the relevant sentence in the corpus file
# data/knowledge_library/sources/how_to_judge_a_horoscope_raman/
#     chapter_001_full-text-unsplit.md
#
# line 1105: "If a Sushka (dry) planet occupies the Lagna the person will be lean."
_SRC_1105 = Citation("HTJAH-I", 1105)
# line 1106: "If the ascendant falls in any of the Sushka Rashis …"
_SRC_1106 = Citation("HTJAH-I", 1106)
# line 1107: "If the lord of the Lagna is in conjunction with Sushka planets …"
_SRC_1107 = Citation("HTJAH-I", 1107)
# line 1108: "He will be corpulent if ascendant be Cancer, Scorpio, or Pisces …"
_SRC_1108 = Citation("HTJAH-I", 1108)
# line 1109: "If the ascendant lord is a watery planet (Venus and the Moon) …"
_SRC_1109 = Citation("HTJAH-I", 1109)
# line 1110: "Corpulence can also be predicted if the Lagna is owned by a benefice …"
_SRC_1110 = Citation("HTJAH-I", 1110)
# line 1112: "If Jupiter occupies Lagna or if Jupiter aspects Lagna from a watery sign …"
_SRC_1112 = Citation("HTJAH-I", 1112)


# ── local Condition leaves ────────────────────────────────────────────────────

class _LagnaIsSushka(C.Condition):
    """The rising sign is a Sushka (dry) rasi — owned by Mars, Saturn or the Sun
    (HTJAH-I:1106-1107; set: conditions.SUSHKA_SIGNS = {1,5,8,10,11})."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return C.SignIsSushka(ctx.chart.asc_sign)


class _LagnaIsWatery(C.Condition):
    """The rising sign is a watery rasi — Cancer (4), Scorpio (8) or Pisces (12)
    (HTJAH-I:1108-1109; set: conditions.WATERY_SIGNS = {4,8,12})."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        return C.SignIsWatery(ctx.chart.asc_sign)


class _LagnaLordIsWatery(C.Condition):
    """The lord of the Lagna is a watery planet — Moon or Venus
    (HTJAH-I:1109-1110; set: conditions.WATERY_PLANETS = {Venus, Moon})."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = SIGN_LORDS[ctx.chart.asc_sign]
        return lord in C.WATERY_PLANETS


class _LagnaOwnedByBenefic(C.Condition):
    """The lord of the Lagna is a natural benefic — Jupiter, Venus, Mercury or Moon
    (HTJAH-I:1110-1112). Raman's 'benefice' here is the natural classification;
    no Lagna context is needed to resolve this."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lord = SIGN_LORDS[ctx.chart.asc_sign]
        return lord in NATURAL_BENEFICS


class _LagnaLordConjunctSushkaPlanet(C.Condition):
    """The lord of the Lagna is in CONJUNCTION with a Sushka planet (Sun, Mars,
    or Saturn) — rule #15 (HTJAH-I:1107-1108).

    This cannot be expressed with `LordsConjunct(1, X)` because the Sushka
    planets are named bodies, not house lords. We resolve the Lagna-lord and
    test whether a *distinct* Sushka body shares its sign.

    A planet cannot be conjunct itself: when the Lagna-lord IS a Sushka planet
    (e.g. Saturn lording Aquarius), Saturn alone in its sign is NOT "conjunction
    with Sushka planets" — that case is already covered by #13 (Sushka planet in
    the Lagna). #15 requires a SECOND, distinct Sushka co-tenant. The
    ``sushka == lagna_lord_name`` co-tenant is therefore skipped, so the rule
    fires only when another Sushka body genuinely joins the lord.
    Returns False if the Lagna-lord is absent (sparse Track-B charts)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lagna_lord_name = SIGN_LORDS[ctx.chart.asc_sign]
        lagna_lord_pos = ctx.chart.planets.get(lagna_lord_name)
        if lagna_lord_pos is None:
            return False
        lagna_lord_sign = lagna_lord_pos.sign
        for sushka in C.SUSHKA_PLANETS:
            if sushka == lagna_lord_name:
                continue  # the lord itself is not a distinct conjoining body
            sp = ctx.chart.planets.get(sushka)
            if sp is not None and sp.sign == lagna_lord_sign:
                return True
        return False


class _NavamshaLordOfLagnaLordIsWatery(C.Condition):
    """Lord of the Navamsha sign occupied by the Lagna-lord is placed in a
    watery D1 sign — rule #18 D9 arm (HTJAH-I:1110-1112).

    Algorithm:
      1. Identify the Lagna-lord's name from the D1 Lagna sign.
      2. Read its ``navamsa_sign`` (the D9 sign it occupies).
      3. Find the lord of that D9 sign (SIGN_LORDS[navamsa_sign]).
      4. Check whether THAT planet's D1 ``sign`` is watery.

    Raman: "the lord of the Navamsha occupied by the lord of Lagna occupies a
    watery sign" — 'occupies' refers to the D1 placement of the navamsha-sign
    lord, not a further varga hop.
    Returns False if either the Lagna-lord or the navamsha-sign-lord is absent
    (sparse Track-B charts)."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        lagna_lord_name = SIGN_LORDS[ctx.chart.asc_sign]
        lagna_lord_pos = ctx.chart.planets.get(lagna_lord_name)
        if lagna_lord_pos is None:
            return False
        nav_sign = lagna_lord_pos.navamsa_sign
        nav_sign_lord_name = SIGN_LORDS[nav_sign]
        nav_sign_lord_pos = ctx.chart.planets.get(nav_sign_lord_name)
        if nav_sign_lord_pos is None:
            return False
        return C.SignIsWatery(nav_sign_lord_pos.sign)


class _JupiterAspectsLagnaFromWaterySign(C.Condition):
    """Jupiter sits in a watery sign AND casts a whole-sign aspect on house 1
    — rule #19 second arm (HTJAH-I:1112-1114).

    Jupiter's drishti includes its special 5th, 7th and 9th aspects in addition
    to the standard 7th; `drishti.aspects_house` covers all of these."""

    def evaluate(self, ctx: C.EvalContext) -> bool:
        from app.raman_saab.doctrine import drishti as _drishti  # local import avoids circular
        jup = ctx.chart.planets.get("Jupiter")
        if jup is None:
            return False
        if not C.SignIsWatery(jup.sign):
            return False
        return _drishti.aspects_house("Jupiter", 1, ctx.chart)


# ── rule records #13-#19 ──────────────────────────────────────────────────────

RULES: Final[tuple[RuleRecord, ...]] = (
    # ── Rule #13 ─────────────────────────────────────────────────────────────
    # "If a Sushka (dry) planet occupies the Lagna the person will be lean.
    #  (Sushka planets are the Sun, Mars and Saturn)."  HTJAH-I:1105-1106.
    RuleRecord(
        id="H1.B.13",
        house=1,
        signification="self",
        group="constitution",
        kind="evaluable",
        condition=C.Or(
            C.InRashiHouse("Sun", 1),
            C.InRashiHouse("Mars", 1),
            C.InRashiHouse("Saturn", 1),
        ),
        fortified="lean physique — Sushka planet (Sun, Mars or Saturn) occupies the Lagna",
        afflicted=None,
        frame="LAGNA",
        varga="D1",
        # polarity=neutral: lean/stout describe physical BUILD, not fortune; these
        # physique rules must NOT count as house strength/affliction evidence in the
        # ledger (they ride along as descriptive constitution, not benefic/malefic).
        polarity="neutral",
        source=_SRC_1105,
    ),
    # ── Rule #14 ─────────────────────────────────────────────────────────────
    # "If the ascendant falls in any of the Sushka Rashis (signs owned by Mars,
    #  Saturn and the Sun) the body will be emanciated."  HTJAH-I:1106-1107.
    RuleRecord(
        id="H1.B.14",
        house=1,
        signification="self",
        group="constitution",
        kind="evaluable",
        condition=_LagnaIsSushka(),
        fortified="emaciated body — ascendant falls in a Sushka rasi "
                  "(Aries, Leo, Scorpio, Capricorn or Aquarius)",
        afflicted=None,
        frame="LAGNA",
        varga="D1",
        polarity="neutral",  # physique (build), not fortune — see #13
        source=_SRC_1106,
    ),
    # ── Rule #15 ─────────────────────────────────────────────────────────────
    # "If the lord of the Lagna is in conjunction with Sushka planets then also
    #  similar results will follow."  HTJAH-I:1107-1108.
    RuleRecord(
        id="H1.B.15",
        house=1,
        signification="self",
        group="constitution",
        kind="evaluable",
        condition=_LagnaLordConjunctSushkaPlanet(),
        fortified="lean / emaciated — lord of Lagna conjunct a Sushka planet "
                  "(Sun, Mars or Saturn)",
        afflicted=None,
        frame="LAGNA",
        varga="D1",
        polarity="neutral",  # physique (build), not fortune — see #13
        source=_SRC_1107,
    ),
    # ── Rule #16 ─────────────────────────────────────────────────────────────
    # "He will be corpulent if ascendant be Cancer, Scorpio, or Pisces with good
    #  planets."  HTJAH-I:1108-1109.  "Good planets" = natural benefics in
    #  house 1 (Jupiter, Venus, Mercury, Moon per Raman's usage throughout).
    RuleRecord(
        id="H1.B.16",
        house=1,
        signification="self",
        group="constitution",
        kind="evaluable",
        condition=C.And(
            _LagnaIsWatery(),
            C.Or(
                C.InRashiHouse("Jupiter", 1),
                C.InRashiHouse("Venus", 1),
                C.InRashiHouse("Mercury", 1),
                C.InRashiHouse("Moon", 1),
            ),
        ),
        fortified="corpulent — watery rasi (Cancer/Scorpio/Pisces) ascending "
                  "with a benefic planet in the Lagna",
        afflicted=None,
        frame="LAGNA",
        varga="D1",
        polarity="neutral",  # corpulence describes build, not fortune — see #13
        source=_SRC_1108,
    ),
    # ── Rule #17 ─────────────────────────────────────────────────────────────
    # "If the ascendant lord is a watery planet (Venus and the Moon), strong and
    #  well conjoined, the native becomes stout."  HTJAH-I:1109-1110.
    # Structural condition: Lagna-lord is Venus or Moon.  Strength / conjunction
    # quality is a modifier noted in the fortified text; Raman gives no discrete
    # boolean test for "strong and well-conjoined" in this passage.
    RuleRecord(
        id="H1.B.17",
        house=1,
        signification="self",
        group="constitution",
        kind="evaluable",
        condition=_LagnaLordIsWatery(),
        fortified="stout build — Lagna-lord is a watery planet (Venus or Moon); "
                  "effect strongest when the lord is strong and well-conjoined",
        afflicted=None,
        frame="LAGNA",
        varga="D1",
        polarity="neutral",  # stout build, not fortune — see #13
        source=_SRC_1109,
    ),
    # ── Rule #18 ─────────────────────────────────────────────────────────────
    # "Corpulence can also be predicted if the Lagna is owned by a benefice and
    #  if the lord of the Navamsha occupied by the lord of Lagna occupies a
    #  watery sign."  HTJAH-I:1110-1112.  Two-arm AND.
    RuleRecord(
        id="H1.B.18",
        house=1,
        signification="self",
        group="constitution",
        kind="evaluable",
        condition=C.And(
            _LagnaOwnedByBenefic(),
            _NavamshaLordOfLagnaLordIsWatery(),
        ),
        fortified="corpulence — Lagna owned by a natural benefic AND the D9-sign "
                  "lord of the Lagna-lord occupies a watery sign",
        afflicted=None,
        frame="LAGNA",
        varga="D9",
        polarity="neutral",  # corpulence describes build, not fortune — see #13
        source=_SRC_1110,
    ),
    # ── Rule #19 ─────────────────────────────────────────────────────────────
    # "If Jupiter occupies Lagna or if Jupiter aspects Lagna from a watery sign
    #  or if the Lagna happens to be a watery sign with benefices in it then
    #  also the body will be stout."  HTJAH-I:1112-1114.
    # Three disjunctive arms — any one suffices.
    RuleRecord(
        id="H1.B.19",
        house=1,
        signification="self",
        group="constitution",
        kind="evaluable",
        condition=C.Or(
            # Arm 1: Jupiter in Lagna
            C.InRashiHouse("Jupiter", 1),
            # Arm 2: Jupiter aspects Lagna from a watery sign
            _JupiterAspectsLagnaFromWaterySign(),
            # Arm 3: watery Lagna with benefic(s) in it
            C.And(
                _LagnaIsWatery(),
                C.Or(
                    C.InRashiHouse("Jupiter", 1),
                    C.InRashiHouse("Venus", 1),
                    C.InRashiHouse("Mercury", 1),
                    C.InRashiHouse("Moon", 1),
                ),
            ),
        ),
        fortified="stout body — Jupiter in Lagna; or Jupiter aspects Lagna from a "
                  "watery sign; or watery Lagna with benefic planet(s) inside",
        afflicted=None,
        frame="LAGNA",
        varga="D1",
        polarity="neutral",  # stout build, not fortune — see #13
        source=_SRC_1112,
    ),
)
