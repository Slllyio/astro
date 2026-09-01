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
        # RELOCATE-WHOLE. HTJAH-II:514-520 has zero openers of either kind; the whole
        # afflicted slot reproduced that paragraph. The fortified slot is three CONJUNCTION
        # clauses (594-599), kept and labelled. Restores 'fond of travelling'.
        general="fair, with thinning hair; few friends and difficulty getting along with "
                "people; marriage delayed and troubled; fond of travelling, with loose morals; "
                "likes foreign things; the wife's character questionable, with risk of loss "
                "and disgrace through women; incurs Government displeasure and humiliation; "
                "deformed",
        fortified="(conjunctions, not fortification) with Mercury -> highly intelligent, and "
                  "tactfully deals with troubles accruing from Government or other sources; "
                  "with Jupiter -> the partner may be a highly evolved spiritual soul; with a "
                  "fortified Venus -> marriage marked by spiritual harmony",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 514)),
    RuleRecord(
        id="H7.P.Moon", house=7, signification="spouse", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Moon", 7),
        # SENTIMENT-SPLIT, twice. 'Wife will be good-looking BUT the native will seek other
        # women' and 'NARROW-MINDED BUT SOCIABLE, he will be energetic and successful' were
        # each cut at their hinge. The waning-Moon clause is a PHASE branch, not an
        # affliction. Raman's real fortified result is 'hails from a good family' (526-527),
        # which the old text replaced with a vaguer 'improves prospects'.
        general="passionate and easily roused to jealousy; the mother may die while the native "
                "is young; the wife good-looking but the native seeks other women; narrow- "
                "minded but sociable; energetic and successful in life; pain in the groins; "
                "stingy",
        fortified="the Moon waxing or otherwise strong -> hails from a good family",
        afflicted="(a lunar phase and a conjunction, not afflictions) the Moon waning -> "
                  "always quarrelling with his enemies; with Rahu -> an intolerable life and "
                  "trouble from supernatural sources; with Jupiter -> a smooth, happy married "
                  "life",
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
        # LEAVE the afflicted slot - 543-544 is genuine ('Diplomatic but IF AFFLICTED, the
        # native will be cunning and deceitful'). Mirror defect only.
        general="virtuous and genial; dresses well; knowledge of law; skilled in business and "
                "trade; writing ability and early success; early marriage to a rich woman; "
                "learned in mathematics, astrology and astronomy; religious and diplomatic; a "
                "good physique and looks",
        fortified="virtuous and genial; dresses well; knowledge of law; skilled in business "
                  "and trade; writing ability and early success; early marriage to a rich "
                  "woman; learned in mathematics, astrology and astronomy; religious and "
                  "diplomatic; a good physique and looks",
        afflicted="Mercury afflicted -> cunning and deceitful",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 538)),
    RuleRecord(
        id="H7.P.Jupiter", house=7, signification="spouse", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Jupiter", 7),
        # MISCITED fragment noted inline rather than by moving the Citation: the record's
        # spine is correctly at 547-553, but "the native will be devoted to his wife" is at
        # HTJAH-II:367-368 ("If Jupiter occupies the 7th house, the native will be devoted to
        # his wife"). Naming the real line in the text keeps a reader who follows the
        # citation from concluding the clause was invented.
        # Relocated 2026-09-01: Raman states this flatly for the placement, so it is
        # his GENERAL reading, not a strength branch. Text copied verbatim — this
        # section was ruled unconditioned by the planet_in_house sweep's review, and
        # the mirror also fixes a rendering bug (a lone `afflicted` slot renders
        # NOTHING on a strong-lord chart, because `_branch` returns 'fortified').
        general="diplomatic, kind; virtuous, good-looking, chaste wife; good education and gains "
                "via marriage; sensitive; speculative mind; good agriculturist; pilgrimages; "
                "superior to father; good sons; native devoted to his wife "
                "(HTJAH-II:367-368, not the cited line)",
        fortified="diplomatic, kind; virtuous, good-looking, chaste wife; good education and gains "
                  "via marriage; sensitive; speculative mind; good agriculturist; pilgrimages; "
                  "superior to father; good sons; native devoted to his wife "
                  "(HTJAH-II:367-368, not the cited line)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 547)),
    RuleRecord(
        id="H7.P.Venus", house=7, signification="spouse", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Venus", 7),
        # SENTIMENT-SPLIT running through Raman's FIRST sentence (555): 'Fond of
        # quarrelling, sensuous and passionate, the native has unhealthy habits, AND a
        # happy marriage and devoted wife.' Only the Sun-affliction clause (630-632) is a
        # genuine afflicted reading; the Mars/Jupiter/Saturn clauses are configurations.
        general="fond of quarrelling, sensuous and passionate; unhealthy habits; a happy "
                "marriage and a devoted wife; fond of pleasure and drink; suave and charming "
                "with winning manners; a magnetic personality; danger of loss of virility "
                "through disease or excesses; successful in partnership with those of the "
                "opposite sex",
        fortified="with Mars, if fortified -> the partner loving, passionate and faithful; "
                  "with Saturn, if fortified -> success on the stage or cinema; "
                  "(configurations) with Jupiter -> good children and a healthy wife; with "
                  "Mars -> gambling and dens of pleasure",
        afflicted="Venus afflicted by the Sun -> the marriage lacks physical attraction, the "
                  "couple assuming indifferent attitudes",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 555)),
    RuleRecord(
        id="H7.P.Saturn", house=7, signification="spouse", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Saturn", 7),
        # SENTIMENT-SPLIT: the whole entry (562-571), a single alternating list, was cut
        # down the middle. Restores Raman's hedge 'provided of course there are other
        # afflictions' on the Mars clause (638-640), which the old encoding dropped.
        general="under the wife's control; the wife ugly or hunch-backed; more than one "
                "marriage, or marriage with a widow, divorcee or one advanced in age; "
                "diplomatic and enterprising; residence abroad, a stable marriage and "
                "political success; honour and distinction in foreign lands; colic pains and "
                "deafness",
        fortified="Saturn strong in his own constellation -> the partner later becomes pious "
                  "and devoted; (a configuration) with a strong Moon -> marriage with a widow",
        afflicted="if Mars afflicts -> courts may intervene, or violence such as suicide or "
                  "murder may destroy the marriage, provided of course there are other "
                  "afflictions",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 562)),
    RuleRecord(
        id="H7.P.Rahu", house=7, signification="spouse", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Rahu", 7),
        # Relocated 2026-09-01: Raman states this flatly for the placement, so it is
        # his GENERAL reading, not a strength branch. Text copied verbatim — this
        # section was ruled unconditioned by the planet_in_house sweep's review, and
        # the mirror also fixes a rendering bug (a lone `afflicted` slot renders
        # NOTHING on a strong-lord chart, because `_branch` returns 'fortified').
        general="brings ill-repute to family (if female native); unconventional, heterodox; "
                "affairs with outcaste women or foreigners; wife suffers womb disorders; rich "
                "food, luxurious habits; diabetes; trouble from ghosts or the supernatural",
        fortified="brings ill-repute to family (if female native); unconventional, heterodox; "
                  "affairs with outcaste women or foreigners; wife suffers womb disorders; rich "
                  "food, luxurious habits; diabetes; trouble from ghosts or the supernatural",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 573)),
    RuleRecord(
        id="H7.P.Ketu", house=7, signification="spouse", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Ketu", 7),
        # Relocated 2026-09-01: Raman states this flatly for the placement, so it is
        # his GENERAL reading, not a strength branch. Text copied verbatim — this
        # section was ruled unconditioned by the planet_in_house sweep's review, and
        # the mirror also fixes a rendering bug (a lone `afflicted` slot renders
        # NOTHING on a strong-lord chart, because `_branch` returns 'fortified').
        general="unhappy marriage; shrewish or sickly wife; passionate, sinful; lusts after "
                "widows; cancer in abdomen or uterus (if female native); humiliation; loss "
                "of virility",
        fortified="unhappy marriage; shrewish or sickly wife; passionate, sinful; lusts after "
                  "widows; cancer in abdomen or uterus (if female native); humiliation; loss "
                  "of virility",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 579)),
)
