"""House 2 (Dhana — wealth) planets-in-2nd-house RuleRecords.

Encoding of the "Planets in the 2nd House" section from
`methodology/house_02_dhana.md`, distilled verbatim from B.V. Raman,
*How to Judge a Horoscope* Vol I, §V (HTJAH-I:2538–2578).

Source span: HTJAH-I:2538–2578.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    RuleRecord(
        id="H2.P.Sun", house=2, signification="wealth", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Sun", 2),
        fortified=None,
        afflicted="not favourable; losses by offending authorities; diseased face; money only by industrious effort; stubborn and peevish; nature of income depends on the sign",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 2540)),
    RuleRecord(
        id="H2.P.Moon", house=2, signification="wealth", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Moon", 2),
        fortified="large family and much happiness; money through females; fair complexion; per Dhundiraja: reserved, not sociable, squint-eyed but much admired",
        afflicted="variable financial position",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 2544)),
    RuleRecord(
        id="H2.P.Mars", house=2, signification="wealth", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Mars", 2),
        fortified="good earning power; accumulates much money; good conversationalist",
        afflicted="quarrelsome, miserly, befriends evil-minded persons, unsympathetic, picks quarrels with all",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 2549)),
    RuleRecord(
        id="H2.P.Mercury", house=2, signification="wealth", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Mercury", 2),
        fortified="learned in religious and philosophical lore; gain by lecturing, business and commerce; rich, intelligent, thrifty; spends on charity",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 2553)),
    RuleRecord(
        id="H2.P.Jupiter", house=2, signification="wealth", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Jupiter", 2),
        fortified="poet, writer, astrologer or scientist; accumulates fortune; good wife and family; non-quarrelsome; money via things indicated by Jupiter's signs",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 2557)),
    RuleRecord(
        id="H2.P.Venus", house=2, signification="wealth", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Venus", 2),
        fortified="large family; money comes readily by favours; good food and conveyances; handsome; good spouse; health and wealth in large measure",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 2563)),
    RuleRecord(
        id="H2.P.Saturn", house=2, signification="wealth", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Saturn", 2),
        fortified="gains by dealing with metals, mines, storage and labour; exception: if the 2nd is Libra, Capricorn or Aquarius the uphill-earning burden is cancelled",
        afflicted="earning an uphill struggle (much work, little gain); harsh speech, unsocial, unhappy family life; unpopular",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 2567)),
    RuleRecord(
        id="H2.P.Rahu", house=2, signification="wealth", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Rahu", 2),
        fortified="if Jupiter aspects the 2nd → good earnings; money through friends and business",
        afflicted="peevish, diseased face, friction in family life, danger to eye-sight; uncertain finances",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 2573)),
    RuleRecord(
        id="H2.P.Ketu", house=2, signification="wealth", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Ketu", 2),
        fortified="success in spiritualism, navigation, mystical arts and hospitals",
        afflicted="bad speaker; loss through fraud and deception; financial liability",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 2577)),
)
