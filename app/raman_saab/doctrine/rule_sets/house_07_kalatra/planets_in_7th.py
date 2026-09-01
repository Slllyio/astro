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
        # ★ UNSOURCED CLAUSE REMOVED 2026-09-01: "may gain through partnerships". It is at
        # neither the cited HTJAH-II:532-536 nor anywhere else for Mars in the 7th. Every
        # occurrence of "partnership" in the source was checked; the nearest real text is
        # line 560 — the VENUS entry, "He is successful in partnership with those of the
        # opposite sex" — a Raman idiom transferred one planet sideways, onto a placement
        # where he concludes the OPPOSITE: "He will be intelligent, tactless, stubborn,
        # peevish and UNSUCCESSFUL" (535-536). Same shape as the H10.L.1 fabrication.
        #
        # The rest of 532-536 is unconditioned, and "He will be intelligent" was lifted out
        # of the middle of that list into `fortified`; restored.
        general="hen-pecked by his wife and submissive to women; married life with clashes "
                "and tensions, or two wives; rash and given to speculation; intelligent, "
                "tactless, stubborn, peevish and unsuccessful",
        fortified="hen-pecked by his wife and submissive to women; married life with clashes "
                  "and tensions, or two wives; rash and given to speculation; intelligent, "
                  "tactless, stubborn, peevish and unsuccessful",
        # MISCITED: "unaspected by benefics -> frequent quarrels" is Raman's, but at
        # HTJAH-II:2558-2559, not 532. It is also a CONFIGURATION (benefic aspect), not an
        # affliction. Kept, relabelled, and its real line named — with the caveat that 2558
        # sits inside a two-horoscope COMPATIBILITY discussion ("Some General Observations",
        # 2543ff), so the frame wants checking before the citation is formally moved.
        afflicted="(a configuration, not an affliction; HTJAH-II:2558-2559, not the cited "
                  "line) Mars in the 7th unaspected by benefics → frequent quarrels leading "
                  "to misunderstandings",
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
                  "superior to father; good sons; native devoted to his wife "
                  "(HTJAH-II:367-368, not the cited line)",
        afflicted=None,
        # MISCITED fragment noted inline rather than by moving the Citation: the record's
        # spine is correctly at 547-553, but "the native will be devoted to his wife" is at
        # HTJAH-II:367-368 ("If Jupiter occupies the 7th house, the native will be devoted to
        # his wife"). Naming the real line in the text keeps a reader who follows the
        # citation from concluding the clause was invented.
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
