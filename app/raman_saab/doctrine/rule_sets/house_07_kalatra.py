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

    # — Planets in the 7th House (HTJAH-II:512-611) —
    RuleRecord(
        id="H7.P.Sun", house=7, signification="spouse", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Sun", 7),
        fortified="with Mercury → highly intelligent, handles Govt trouble well; with Jupiter → "
                  "spiritually evolved partner; with fortified Venus → spiritual harmony in marriage",
        afflicted="fair, thinning hair; few friends; delayed or troubled marriage; loose morals; "
                  "likes foreign things; wife's character questionable; risk of loss or disgrace via "
                  "women; Govt displeasure; deformed constitution",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 514)),
    RuleRecord(
        id="H7.P.Moon", house=7, signification="spouse", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Moon", 7),
        fortified="good-looking wife; sociable, energetic, successful native; waxing Moon improves "
                  "prospects; with Jupiter → smooth, happy married life",
        afflicted="passionate, jealous native; mother may die young; native seeks others despite "
                  "good-looking wife; narrow-minded; pain in groins; stingy; waning Moon → quarrels "
                  "with enemies; with Rahu → intolerable life and trouble from supernatural sources",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 522)),
    RuleRecord(
        id="H7.P.Mars", house=7, signification="spouse", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Mars", 7),
        fortified="intelligent, speculative; may gain through partnerships",
        afflicted="hen-pecked, submissive to women; clashes, tensions, or two wives; rash, tactless, "
                  "stubborn, peevish, unsuccessful; unaspected by benefics → frequent quarrels",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 532)),
    RuleRecord(
        id="H7.P.Mercury", house=7, signification="spouse", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Mercury", 7),
        fortified="virtuous, genial; dresses well; knowledge of law; skilled in business and trade; "
                  "writing ability and early success; early marriage to a rich woman; learned in "
                  "maths, astrology, astronomy; religious, diplomatic; good physique",
        afflicted="cunning and deceitful",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 538)),
    RuleRecord(
        id="H7.P.Jupiter", house=7, signification="spouse", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Jupiter", 7),
        fortified="diplomatic, kind; virtuous, good-looking, chaste wife; good education and gains "
                  "via marriage; sensitive; speculative mind; good agriculturist; pilgrimages; "
                  "superior to father; good sons; native devoted to his wife",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 547)),
    RuleRecord(
        id="H7.P.Venus", house=7, signification="spouse", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Venus", 7),
        fortified="happy marriage and devoted wife; suave, magnetic personality; success in "
                  "partnership with opposite sex; with Jupiter → good children and healthy wife; "
                  "with Saturn → patience, stability, skill in dance and drama",
        afflicted="fond of quarrelling, sensuous, passionate; unhealthy habits; danger of loss "
                  "of virility via disease or excess; with Mars → gambling and dens of pleasure; "
                  "with Sun afflicting → marriage lacks physical attraction",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 555)),
    RuleRecord(
        id="H7.P.Saturn", house=7, signification="spouse", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Saturn", 7),
        fortified="diplomatic, enterprising; residence and honour abroad; stable marriage; political "
                  "success; in own constellation → partner later pious; with strong Moon → marriage "
                  "with widow",
        afflicted="under wife's control; ugly or hunch-backed wife; more than one marriage or "
                  "marriage with widow, divorcee, or elderly person; colic pains, deafness; "
                  "with Mars → courts, violence, suicide, or murder",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 562)),
    RuleRecord(
        id="H7.P.Rahu", house=7, signification="spouse", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Rahu", 7),
        fortified=None,
        afflicted="brings ill-repute to family (if female native); unconventional, heterodox; "
                  "affairs with outcaste women or foreigners; wife suffers womb disorders; rich "
                  "food, luxurious habits; diabetes; trouble from ghosts or the supernatural",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 573)),
    RuleRecord(
        id="H7.P.Ketu", house=7, signification="spouse", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Ketu", 7),
        fortified=None,
        afflicted="unhappy marriage; shrewish or sickly wife; passionate, sinful; lusts after "
                  "widows; cancer in abdomen or uterus (if female native); humiliation; loss "
                  "of virility",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 579)),
)
