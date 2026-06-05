"""House 10 (Karma / Rajya Bhava — career/profession) RuleRecords.

Lord of the 10th in the 12 Houses — faithful transcription of B.V. Raman's
*How to Judge a Horoscope*, Vol. II (HTJAH-II), from the "Lord of the 10th in
the 12 Houses" section. "Fortified" = well-placed / benefic-aspected / NOT in
6/8/12 from Navamsa Lagna; "Afflicted" = malefic/Rahu, debilitated, eclipsed,
inimical, or in 6/8/12 Navamsa (per the methodology header at HTJAH-II:9456).

Source span: HTJAH-II:9456-9575.
Karaka: Sun, Mercury, Jupiter, Saturn (multi-karaka house).
Special varga: D10 Dasamsa (career); D9 Navamsa used as overlay throughout.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    RuleRecord(
        id="H10.L.1", house=10, signification="career", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(10, 1),
        fortified="rises by perseverance; self-employed / independent profession; Lagna and "
                  "10th lord together → famous pioneer, founds public institution",
        afflicted="weak Lagna and 10th lord → modest attainment; little distinction",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9459)),
    RuleRecord(
        id="H10.L.2", house=10, signification="career", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(10, 2),
        fortified="fortunate, much money; may develop family trade; prospers in "
                  "catering / restaurants",
        afflicted="malefics → losses, winds up family business",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9467)),
    RuleRecord(
        id="H10.L.3", house=10, signification="career", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(10, 3),
        fortified="speaker or writer of celebrity; brothers aid career",
        afflicted="10th lord in 6/8/12 navamsa or unfriendly star → slow, obstacle-ridden "
                  "rise; afflicted 3rd lord → rivalry between brothers, reversals",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9474)),
    RuleRecord(
        id="H10.L.4", house=10, signification="career", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(10, 4),
        fortified="lucky, learned, famous for learning and generosity; royal favour; "
                  "agriculture / immovable property; 4th+9th+10th related → political "
                  "head of government",
        afflicted="depressed / eclipsed / inimical / afflicted → loses lands, life of "
                  "servitude; with 8th lord in malefic shashtyamsa same result",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9484)),
    RuleRecord(
        id="H10.L.5", house=10, signification="career", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(10, 5),
        fortified="shines as broker / speculation; benefics with it → pious simple life, "
                  "head of orphanage or remand home",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9501)),
    RuleRecord(
        id="H10.L.6", house=10, signification="career", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(10, 6),
        fortified="judiciary / prisons / hospitals; benefic aspect → post of authority "
                  "and esteem",
        afflicted="Saturn aspect → lifelong low-paying job; Rahu or afflicted malefics → "
                  "disgrace, criminal exposure, imprisonment",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 9508)),
    RuleRecord(
        id="H10.L.7", house=10, signification="career", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(10, 7),
        fortified="mature wife who assists work; foreign diplomatic travel; skilled "
                  "negotiator; profits via partnership",
        afflicted="malefics → debased sexual habits, every vice",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9517)),
    RuleRecord(
        id="H10.L.8", house=10, signification="career", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(10, 8),
        fortified="high office but only for a short time; Jupiter aspect or association → "
                  "mystic / spiritual teacher",
        afflicted="malefic influence → criminal propensities and offences; Saturn → "
                  "undertaker / burning-ghat work",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 9525)),
    RuleRecord(
        id="H10.L.9", house=10, signification="career", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(10, 9),
        fortified="spiritual stalwart; Jupiter aspect → beacon to seekers; both benefics "
                  "and malefics aspect → fortunate, hereditary preacher / teacher / "
                  "healer; father's great influence on career",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9537)),
    RuleRecord(
        id="H10.L.10", house=10, signification="career", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(10, 10),
        fortified="strong → highly successful, respect and honour in career",
        afflicted="weak or afflicted → no self-respect, cringing, dependent, fickle; "
                  "in 6/8/12 navamsa → routine career; 3 planets conjoin → ascetic",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9546)),
    RuleRecord(
        id="H10.L.11", house=10, signification="career", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(10, 11),
        fortified="immense riches, fortunate, meritorious deeds, employs hundreds, "
                  "high honour, many friends",
        afflicted="11th afflicted → friends turn enemies, hardship",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9556)),
    RuleRecord(
        id="H10.L.12", house=10, signification="career", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(10, 12),
        fortified="beneficial → spiritual seeker; works in a far-off place",
        afflicted="lacks comforts, difficulties; malefics → separated from family, "
                  "wanders, smuggling; Rahu → cheat / criminal, sorrow to family",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 9564)),

    # — planets in the 10th house (HTJAH-II:9813-9908) —
    RuleRecord(
        id="H10.P.Sun", house=10, signification="career", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Sun", 10),
        fortified="successful, strong, happy; sons, vehicles, fame, intelligence, money, "
                  "power; government service; ancestral wealth; fond of music; personal "
                  "magnetism",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9815)),
    RuleRecord(
        id="H10.P.Moon", house=10, signification="career", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Moon", 10),
        fortified="religious, wealthy, intelligent, bold; succeeds; corn, ornaments, women; "
                  "skilled in arts; helpful, virtuous; Jupiter conjunct → learned in ancient "
                  "subjects and astrology; Saturn aspect → dispassionate thinker, earns via "
                  "printing/selling books, trustee of religious institutions",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9828)),
    RuleRecord(
        id="H10.P.Mars", house=10, signification="career", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Mars", 10),
        fortified="earns much money; Mercury conjunct → skilled scientist/technician "
                  "patronised by rulers; Jupiter conjunct → head of low-class people; "
                  "Venus conjunct → trader in foreign lands",
        afflicted="may become a cruel ruler; bold/rash in governing; Saturn conjunct → "
                  "daring but no progeny",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9841)),
    RuleRecord(
        id="H10.P.Mercury", house=10, signification="career", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Mercury", 10),
        fortified="happy, straightforward; scholar in many subjects; seeks knowledge and "
                  "fame; successful; deep in astronomy and mathematics; Venus conjunct → "
                  "charming wife, wealth; Jupiter conjunct → in government circles",
        afflicted="defective eyesight; Jupiter conjunct → unhappy, childless; "
                  "Saturn conjunct → copyist/proofreader toil, penury",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9850)),
    RuleRecord(
        id="H10.P.Jupiter", house=10, signification="career", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Jupiter", 10),
        fortified="high government official; rich, virtuous, steadfast in spiritual life, "
                  "wise, guided by high principles; Venus conjunct → esteemed by government, "
                  "protects learned and Brahmins; Mars aspect → heads research/academic/"
                  "educational institutes",
        afflicted="Rahu conjunct → mischief-maker",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9860)),
    RuleRecord(
        id="H10.P.Venus", house=10, signification="career", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Venus", 10),
        fortified="earns through houses/buildings; influential, many women working for him; "
                  "social, friendly, renowned; Saturn conjunct → profits from cosmetics/"
                  "women's articles, healing powers, skilled trader, respects divine people",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9873)),
    RuleRecord(
        id="H10.P.Saturn", house=10, signification="career", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Saturn", 10),
        fortified="ruler/minister; agriculturist; brave, rich, famous; dispassionate; works "
                  "for downtrodden; judge; visits shrines, later ascetic",
        afflicted="career marked by sudden elevations and depressions; 8th lord conjunct in "
                  "malefic navamsa → tyrannical superior officer",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9881)),
    RuleRecord(
        id="H10.P.Rahu", house=10, signification="career", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Rahu", 10),
        fortified="skilled artist, flair for poetry/literature; travels widely, learned, "
                  "famous; business; bold, adventurous",
        afflicted="lusts after widows; limited issues; commits sins",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 9894)),
    RuleRecord(
        id="H10.P.Ketu", house=10, signification="career", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Ketu", 10),
        fortified="if beneficially disposed → happy, religious, well-read in scriptures, "
                  "pilgrim-visits",
        afflicted="vile deeds, impure resolves; many obstacles; strong and bold but very "
                  "clever in deceit",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 9900)),
)
