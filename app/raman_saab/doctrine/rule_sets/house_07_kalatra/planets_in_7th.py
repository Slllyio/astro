"""House 7 (Kalatra — spouse/marriage) — Planets-in-the-7th RuleRecords.

The "Planets in the 7th House" table (HTJAH-II:512-611). Moved verbatim from the
former flat ``house_07_kalatra.py`` during the Stage-4 subpackage split.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
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
