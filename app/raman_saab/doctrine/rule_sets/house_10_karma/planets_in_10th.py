"""House 10 (Karma — career/profession) — Planets-in-the-10th RuleRecords.

The "Planets in the 10th House" table (HTJAH-II:9813-9908). Moved verbatim
from the former flat ``house_10_karma.py`` during the Stage-4 split.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
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
