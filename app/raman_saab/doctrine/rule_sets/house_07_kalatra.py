"""House 7 (Kalatra — spouse/marriage) RuleRecords.

The TEMPLATE for house-by-house rule encoding (Phase 2). Each entry is one
combination from `methodology/house_07_kalatra.md`, encoded as a `RuleRecord`
with a `Condition` tree (evaluable) + the real corpus `Citation` the methodology
cites. Karaka = Venus; from-Venus rules carry frame="KARAKA".

Source span: HTJAH-II:198-2883. Karaka Venus, judged as a Lagna (HTJAH-II:225).
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


def _venus(houses: set[int]) -> C.Condition:
    return C.ClassInHouseFrom("malefic", "Venus", houses)


RULES: Final[tuple[RuleRecord, ...]] = (
    # — from-Karaka (Venus) combinations —
    RuleRecord(
        id="H7.K.1", house=7, signification="virility", group="from_karaka", kind="evaluable",
        condition=C.Or(C.InHouseFrom("Saturn", "Venus", 6), C.InHouseFrom("Saturn", "Venus", 8)),
        fortified="normal virility / potency",
        afflicted="impotency — Saturn in the 6th or 8th from Venus",
        frame="KARAKA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 430)),
    RuleRecord(
        id="H7.K.2", house=7, signification="coverture", group="from_karaka", kind="evaluable",
        condition=_venus({4, 8, 12}),
        fortified="long-lived partner",
        afflicted="wife dies soon — malefics in the 4th/8th/12th from Venus",
        frame="KARAKA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 368)),
    RuleRecord(
        id="H7.K.3", house=7, signification="marital_happiness", group="from_karaka", kind="evaluable",
        condition=_venus({7}),
        fortified="harmonious marriage",
        afflicted="unhappy marriage — malefics in the 7th from Venus",
        frame="KARAKA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 376)),

    # — 7th lord in the 12 houses (HTJAH-II:235-340) —
    RuleRecord(
        id="H7.L.1", house=7, signification="spouse", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(7, 1),
        fortified="marries someone known since childhood; stable, mature, intelligent spouse",
        afflicted="if the 7th lord is afflicted — constant travelling; with Venus afflicted, "
                  "clandestine relations",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 235)),
    RuleRecord(
        id="H7.L.2", house=7, signification="wealth_through_marriage", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(7, 2),
        fortified="wealth from women / through marriage",
        afflicted="money by despicable means; in a dual sign with affliction, more than one "
                  "marriage; maraka Dasa may kill in the 7th-lord period",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 244)),
)
