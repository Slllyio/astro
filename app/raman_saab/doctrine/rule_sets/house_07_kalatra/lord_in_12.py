"""House 7 (Kalatra — spouse/marriage) — Lord-in-12-houses RuleRecords.

The "Lord of the 7th in the 12 Houses" table (HTJAH-II:235-340). Moved verbatim
from the former flat ``house_07_kalatra.py`` during the Stage-4 subpackage split.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
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
    RuleRecord(
        id="H7.L.3", house=7, signification="spouse", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(7, 3),
        fortified="lucky brothers who may live abroad; female issues survive",
        afflicted="adultery with a brother's or sister's married partner; misfortunes to co-borns",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 254)),
    RuleRecord(
        id="H7.L.4", house=7, signification="spouse", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(7, 4),
        fortified="lucky, happy partner; many children and comforts; high academic qualification; many vehicles",
        afflicted="domestic harmony spoilt by an immature or mean partner; endless conveyance problems; "
                  "severe node and malefic affliction renders wife's character questionable",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 259)),
    RuleRecord(
        id="H7.L.5", house=7, signification="spouse", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(7, 5),
        fortified="early marriage; partner from affluent family; mature, advantageous spouse; good character",
        afflicted="weak 7th lord denies children; severe affliction → issue through wife's adultery; "
                  "afflictions with benefics → only female progeny; trouble to office superiors via foreign sources",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 271)),
    RuleRecord(
        id="H7.L.6", house=7, signification="spouse", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(7, 6),
        fortified="two marriages with both partners living; may marry a cousin (uncle's daughter)",
        afflicted="badly afflicted with ill Venus → impotency and many diseases; sickly jealous wife; "
                  "Venus well-placed but 7th lord afflicted → piles; Venus weak but not afflicted → "
                  "deserts or loses partner by indiscretion",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 281)),
    RuleRecord(
        id="H7.L.7", house=7, signification="spouse", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(7, 7),
        fortified="charming, magnetic personality; women flock to him; just, honourable spouse of good family",
        afflicted="weak and afflicted → lonely life devoid of marriage and friends; loss through marriage negotiations",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 291)),
    RuleRecord(
        id="H7.L.8", house=7, signification="spouse", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(7, 8),
        fortified="marriage with relatives or a rich partner",
        afflicted="early death of partner; native may die in distant lands; sickly, ill-tempered spouse "
                  "leading to estrangement or separation",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 298)),
    RuleRecord(
        id="H7.L.9", house=7, signification="spouse", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(7, 9),
        fortified="father may live abroad; native makes fortune in foreign lands; accomplished, righteous wife",
        afflicted="father may die early; partner drags native from Dharmic path; wastes wealth, suffers penury",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 307)),
    RuleRecord(
        id="H7.L.10", house=7, signification="spouse", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(7, 10),
        fortified="flourishing profession abroad or constant travel; devoted faithful spouse who may be "
                  "employed and aid native's income and career",
        afflicted="avaricious, over-ambitious wife without capacity; native's career suffers and deteriorates",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 314)),
    RuleRecord(
        id="H7.L.11", house=7, signification="spouse", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(7, 11),
        fortified="more than one marriage or associates with many women; wife from rich background or brings wealth",
        afflicted="marries more than once but one wife outlives him",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 323)),
    RuleRecord(
        id="H7.L.12", house=7, signification="spouse", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(7, 12),
        fortified="more than one marriage; possible spiritual turn when both karaka and lord are strong",
        afflicted="second marriage clandestine while first alive, or after losing first; severe affliction "
                  "→ partner dies or separates soon, no second marriage; death while travelling or abroad; "
                  "both karaka and 7th lord weak → only dreams of women, never marries; wife from servant "
                  "family; close-fisted and poor",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 329)),
)
