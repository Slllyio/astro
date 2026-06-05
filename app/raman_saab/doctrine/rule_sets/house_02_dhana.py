"""House 2 (Dhana — wealth) RuleRecords.

Encoding of the "Lord of the 2nd in the 12 Houses" table from
`methodology/house_02_dhana.md`, distilled verbatim from B.V. Raman,
*How to Judge a Horoscope* Vol I, §V (HTJAH-I:2314–3321).

Each of the 12 records covers one placement (n = 1..12) with fortified
and afflicted readings as given. Polarity follows the dominant nature of
the fortified result (malefic when even the positive reading is corrupt;
benefic when clearly auspicious; neutral otherwise).

Source span: HTJAH-I:2325–2421.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    RuleRecord(
        id="H2.L.1", house=2, signification="wealth", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(2, 1),
        fortified="wealthy by own effort, intelligence and learning; inheritance if 9th lord or Sun touches the combination",
        afflicted="hates his own family, lacks polite manners, passionate, subservient, time-serving",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 2325)),
    RuleRecord(
        id="H2.L.2", house=2, signification="wealth", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(2, 2),
        fortified="riches without effort if 1st and 2nd lords have exchanged; exaltation/own-disposition yields Yoga-Karaka-grade fortune through business",
        afflicted="proud; may marry twice or thrice per 7th-house strength; may be childless; affliction causes poor food, family/children's diseases, marital discord",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 2332)),
    RuleRecord(
        id="H2.L.3", house=2, signification="wealth", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(2, 3),
        fortified="benefited by sisters; gains by fine arts (music, dancing); propitiates Kshudra Devatas",
        afflicted="brave and intelligent but depraved character, atheistic, addicted to luxuries, turns miser later",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 2347)),
    RuleRecord(
        id="H2.L.4", house=2, signification="wealth", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(2, 4),
        fortified="earns as automobile dealer/agent, agriculturist, landlord or commission agent; benefited by maternal relations",
        afflicted="spends on own happiness, highly frugal; losses if 4th lord afflicted",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 2355)),
    RuleRecord(
        id="H2.L.5", house=2, signification="wealth", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(2, 5),
        fortified="unexpected wealth via lotteries, crosswords, favour of rulers",
        afflicted="hates family, sensual, will not spend even on children, lacks manners and etiquette",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 2362)),
    RuleRecord(
        id="H2.L.6", house=2, signification="wealth", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(2, 6),
        fortified="amasses wealth by black-marketing, deceit, creating misunderstandings and questionable dealings",
        afflicted="involved in such troubles and sentenced for breach of trust, forgery or perjury; income and expenditure from enemies; anus/thigh disease",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 2368)),
    RuleRecord(
        id="H2.L.7", house=2, signification="wealth", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(2, 7),
        fortified="influx of wealth via foreign sources or foreign business; if sign/navamsa/star of 2nd lord is feminine, benefit via women",
        afflicted="laxity of morals in both spouses; wastes money on sensual gratification; likely to become a healer",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 2380)),
    RuleRecord(
        id="H2.L.8", house=2, signification="wealth", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(2, 8),
        fortified="influx and loss of wealth — hardly any earnings; inherited or accumulated wealth disappears",
        afflicted="little or no happiness from spouse; misunderstandings with elder brothers; gets landed properties",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 2388)),
    RuleRecord(
        id="H2.L.9", house=2, signification="wealth", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(2, 9),
        fortified="good inheritance if 9th lord is in Lagna; benefits per sign/nakshatra of 2nd lord; much wealth and happiness",
        afflicted="ill-health in young age, healthy afterwards",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 2395)),
    RuleRecord(
        id="H2.L.10", house=2, signification="wealth", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(2, 10),
        fortified="takes to many useful avocations — business, agriculture, philosophical lectures — benefiting financially",
        afflicted="respect from elders, learned, wealthy by own exertion; powerful afflictions cause loss from those same sources",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 2402)),
    RuleRecord(
        id="H2.L.11", house=2, signification="wealth", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(2, 11),
        fortified="earns by lending money, banking or running a boarding house",
        afflicted="bad health in childhood; earns considerable wealth but becomes unscrupulous",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 2410)),
    RuleRecord(
        id="H2.L.12", house=2, signification="wealth", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(2, 12),
        fortified="income through ecclesiastical sources; becomes a respectable man, likely a government servant",
        afflicted="deprived of happiness of elder brother; loses money on the ecclesiastical account if 2nd lord afflicted",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 2417)),

    # — Planets in the 2nd House (HTJAH-I:2538–2578) —
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
