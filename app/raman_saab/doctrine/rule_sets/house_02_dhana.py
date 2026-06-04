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
)
