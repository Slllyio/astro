"""House 1 — per-sign affliction sub-rules S1-S9.

Raman embeds discrete "if afflicted / if evil planets / if Saturn-or-Mars so placed"
clauses inside the per-sign delineations (HTJAH-I:1242-1465).  Each rule fires
**only** for the named rising sign and modifies the base sign description.

Condition shape:  And(<lagna in sign S>, <the affliction predicate>)

The ``LagnaInSign`` predicate is a tiny local Condition subclass — there is no
equivalent in conditions.py for checking the ascendant sign directly.  It reads
``ctx.chart.asc_sign`` which is always populated (never None).

Sign numbers (whole-sign, 1=Aries … 12=Pisces):
    1 Aries   3 Gemini   6 Virgo   10 Capricorn   11 Aquarius

Source span: HTJAH-I:1254-1436  (per-sign delineation affliction clauses).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.conditions import Condition, EvalContext
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


# ── tiny local predicate: ascendant falls in sign `sign` (1..12) ─────────────

@dataclass(frozen=True)
class LagnaInSign(Condition):
    """Ascendant sign equals `sign` (1=Aries … 12=Pisces).

    Reads ``ctx.chart.asc_sign`` — always an int, never absent.
    Not added to conditions.py: it is a sign-specific guard used only inside
    this module's per-sign affliction encodings.
    """
    sign: int

    def evaluate(self, ctx: EvalContext) -> bool:
        return ctx.chart.asc_sign == self.sign


# ── helper: "sign afflicted" = at least one natural malefic in the 1st house ─
# Raman's usage of "if [sign] is afflicted" in per-sign delineations means
# malefic occupation of (or aspect on) the ascendant.  The evaluable encoding
# uses the tractable, well-defined half: at least one natural malefic in the
# 1st whole-sign house.  Aspecting malefics are a descriptive qualifier noted
# in the `afflicted` field.

def _sign_afflicted() -> Condition:
    """At least one natural malefic (Sun, Mars, Saturn, Rahu, Ketu) in the 1st."""
    return C.CountInHouse(house=1, n=1, klass="malefic")


# ── Mars NOT in own sign (Aries=1, Scorpio=8) ────────────────────────────────

_MARS_OWN_SIGNS: frozenset[int] = frozenset({1, 8})


@dataclass(frozen=True)
class _MarsNotInOwnSign(Condition):
    """Mars occupies any sign other than his own (Aries / Scorpio)."""

    def evaluate(self, ctx: EvalContext) -> bool:
        m = ctx.chart.planets.get("Mars")
        return m is not None and m.sign not in _MARS_OWN_SIGNS


# ── rule set ──────────────────────────────────────────────────────────────────

RULES: Final[tuple[RuleRecord, ...]] = (

    # S1 — Aries: sign afflicted → head diseases
    # "If Aries is afflicted they suffer from diseases pertaining to the head."
    # HTJAH-I:1254-1255
    RuleRecord(
        id="H1.S.1", house=1, signification="self", group="sign_affliction",
        kind="evaluable",
        condition=C.And(
            LagnaInSign(1),
            _sign_afflicted(),
        ),
        fortified="",
        afflicted="diseases pertaining to the head when Aries is afflicted",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 1254)),

    # S2 — Aries: Saturn and Moon both in Aries → mental affliction / derangement
    # "Mental affliction and derangement are also likely if Saturn and the Moon are in Aries."
    # HTJAH-I:1255-1256
    RuleRecord(
        id="H1.S.2", house=1, signification="self", group="sign_affliction",
        kind="evaluable",
        condition=C.And(
            LagnaInSign(1),
            C.InRashiHouse("Saturn", 1),
            C.InRashiHouse("Moon", 1),
        ),
        fortified="",
        afflicted="mental affliction and derangement are likely when Saturn and the Moon "
                  "both occupy Aries",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 1255)),

    # S3 — Gemini: evil planets in Gemini → trickery and deceit
    # "If evil planets are in Gemini, trickery and deceit will characterise their nature."
    # HTJAH-I:1288-1289
    RuleRecord(
        id="H1.S.3", house=1, signification="self", group="sign_affliction",
        kind="evaluable",
        condition=C.And(
            LagnaInSign(3),
            _sign_afflicted(),
        ),
        fortified="",
        afflicted="trickery and deceit characterise the nature when evil planets occupy Gemini",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 1288)),

    # S4 — Virgo: sign afflicted → chest weak (otherwise prominent)
    # "Their chest will be prominent and when afflicted, weak also."
    # HTJAH-I:1334-1335
    # The CONDITION gates on _sign_afflicted() (a malefic in the 1st), so this rule
    # only fires in the AFFLICTED case. fortified=None so "chest weak" surfaces, not
    # the unconditional "chest prominent" (the prominent reading is the base Virgo
    # delineation, carried by H1.M.S06 / the per-sign narrative — not this affliction
    # sub-rule).
    RuleRecord(
        id="H1.S.4", house=1, signification="self", group="sign_affliction",
        kind="evaluable",
        condition=C.And(
            LagnaInSign(6),
            _sign_afflicted(),
        ),
        fortified=None,
        afflicted="chest weak when the sign (Virgo) is afflicted",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 1334)),

    # S5 — Virgo: sign afflicted → liable to nervous breakdowns and paralysis
    # "They are liable to suffer from nervous breakdowns and paralysis when the sign is afflicted."
    # HTJAH-I:1341-1342
    RuleRecord(
        id="H1.S.5", house=1, signification="self", group="sign_affliction",
        kind="evaluable",
        condition=C.And(
            LagnaInSign(6),
            _sign_afflicted(),
        ),
        fortified="",
        afflicted="liable to nervous breakdowns and paralysis when Virgo is afflicted",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 1341)),

    # S6 — Capricorn: Saturn afflicted → vindictive and somewhat bigoted
    # "They become vindictive when Saturn is afflicted and may become somewhat bigoted."
    # HTJAH-I:1417
    # "Saturn afflicted" = combust, debilitated, or hemmed by malefics.
    RuleRecord(
        id="H1.S.6", house=1, signification="self", group="sign_affliction",
        kind="evaluable",
        condition=C.And(
            LagnaInSign(10),
            C.Or(
                C.Combust("Saturn"),
                C.HasDignity("Saturn", {"debil"}),
                C.HemmedBy("Saturn", "malefic"),
            ),
        ),
        fortified="",
        afflicted="become vindictive and somewhat bigoted when Saturn (lagna lord) is afflicted "
                  "(combust, debilitated, or hemmed by malefics)",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 1417)),

    # S7 — Capricorn: Mars not in own sign → lack confidence, funky/nervous/weak-minded
    # "If Mars occupies any sign other than his own they lack confidence, become funky,
    #  nervous and weak-minded."
    # HTJAH-I:1420
    RuleRecord(
        id="H1.S.7", house=1, signification="self", group="sign_affliction",
        kind="evaluable",
        condition=C.And(
            LagnaInSign(10),
            _MarsNotInOwnSign(),
        ),
        fortified="",
        afflicted="lack confidence; become funky, nervous and weak-minded when Mars does not "
                  "occupy his own sign (Aries or Scorpio)",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 1420)),

    # S8 — Aquarius: sign NOT free from afflictions → fails as great teacher/writer/lecturer
    # "Aquarius being a philosophical sign, people born in it become great teachers, writers,
    #  and lecturers, provided the sign is free from afflictions."
    # HTJAH-I:1428-1429
    RuleRecord(
        id="H1.S.8", house=1, signification="self", group="sign_affliction",
        kind="evaluable",
        condition=C.And(
            LagnaInSign(11),
            _sign_afflicted(),
        ),
        fortified="",
        afflicted="fails to become a great teacher, writer or lecturer — the gift is "
                  "conditional on Aquarius being free from afflictions",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 1428)),

    # S9 — Aquarius: Saturn in the 4th → chest weak, tendency towards stooping
    # "If Saturn is in the 4th, the chest will be weak with a tendency towards stooping."
    # HTJAH-I:1435-1436
    RuleRecord(
        id="H1.S.9", house=1, signification="self", group="sign_affliction",
        kind="evaluable",
        condition=C.And(
            LagnaInSign(11),
            C.InRashiHouse("Saturn", 4),
        ),
        fortified="",
        afflicted="chest weak with a tendency towards stooping when Saturn occupies the 4th "
                  "from Aquarius lagna",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 1435)),
)
