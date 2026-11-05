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
        # Relocated 2026-09-01: Raman states this flatly for the placement, so it is
        # his GENERAL reading, not a strength branch. Text copied verbatim — this
        # section was ruled unconditioned by the planet_in_house sweep's review, and
        # the mirror also fixes a rendering bug (a lone `afflicted` slot renders
        # NOTHING on a strong-lord chart, because `_branch` returns 'fortified').
        general="not favourable; losses by offending authorities; diseased face; money only by industrious effort; stubborn and peevish; nature of income depends on the sign",
        fortified="not favourable; losses by offending authorities; diseased face; money only by industrious effort; stubborn and peevish; nature of income depends on the sign",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 2540)),
    RuleRecord(
        id="H2.P.Moon", house=2, signification="wealth", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Moon", 2),
        # HTJAH-I:2544-2547, no openers of either kind. 2545-2546 is one sentence split.
        general="a large family and much happiness; money also obtained through females; the "
                "financial position somewhat variable; a fair complexion; per Dhundiraja: "
                "reserved and not much sociable, squint-eyed and much admired",
        fortified="a large family and much happiness; money also obtained through females; "
                  "the financial position somewhat variable; a fair complexion; per "
                  "Dhundiraja: reserved and not much sociable, squint-eyed and much admired",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 2544)),
    RuleRecord(
        id="H2.P.Mars", house=2, signification="wealth", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Mars", 2),
        # HTJAH-I:2549-2551. "Good earning powers but usually miserly." (2549) cut at the
        # "but". Raman OPENS the entry "Becomes quarrelsome" and CLOSES it "pick up quarrels
        # with all", both unconditioned — the negatives are his base reading, not a variant.
        general="becomes quarrelsome; good earning powers but usually miserly; much money is "
                "accumulated; a good conversationalist; befriends evil-minded persons, is "
                "unsympathetic and picks up quarrels with all",
        fortified="becomes quarrelsome; good earning powers but usually miserly; much money "
                  "is accumulated; a good conversationalist; befriends evil-minded persons, "
                  "is unsympathetic and picks up quarrels with all",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 2549)),
    RuleRecord(
        id="H2.P.Mercury", house=2, signification="wealth", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Mercury", 2),
        # Relocated 2026-09-01: Raman states this flatly for the placement, so it is
        # his GENERAL reading, not a strength branch. Text copied verbatim — this
        # section was ruled unconditioned by the planet_in_house sweep's review, and
        # the mirror also fixes a rendering bug (a lone `afflicted` slot renders
        # NOTHING on a strong-lord chart, because `_branch` returns 'fortified').
        general="learned in religious and philosophical lore; gain by lecturing, business and commerce; rich, intelligent, thrifty; spends on charity",
        fortified="learned in religious and philosophical lore; gain by lecturing, business and commerce; rich, intelligent, thrifty; spends on charity",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 2553)),
    RuleRecord(
        id="H2.P.Jupiter", house=2, signification="wealth", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Jupiter", 2),
        # Relocated 2026-09-01: Raman states this flatly for the placement, so it is
        # his GENERAL reading, not a strength branch. Text copied verbatim — this
        # section was ruled unconditioned by the planet_in_house sweep's review, and
        # the mirror also fixes a rendering bug (a lone `afflicted` slot renders
        # NOTHING on a strong-lord chart, because `_branch` returns 'fortified').
        general="poet, writer, astrologer or scientist; accumulates fortune; good wife and family; non-quarrelsome; money via things indicated by Jupiter's signs",
        fortified="poet, writer, astrologer or scientist; accumulates fortune; good wife and family; non-quarrelsome; money via things indicated by Jupiter's signs",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 2557)),
    RuleRecord(
        id="H2.P.Venus", house=2, signification="wealth", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Venus", 2),
        # Relocated 2026-09-01: Raman states this flatly for the placement, so it is
        # his GENERAL reading, not a strength branch. Text copied verbatim — this
        # section was ruled unconditioned by the planet_in_house sweep's review, and
        # the mirror also fixes a rendering bug (a lone `afflicted` slot renders
        # NOTHING on a strong-lord chart, because `_branch` returns 'fortified').
        general="large family; money comes readily by favours; good food and conveyances; handsome; good spouse; health and wealth in large measure",
        fortified="large family; money comes readily by favours; good food and conveyances; handsome; good spouse; health and wealth in large measure",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 2563)),
    RuleRecord(
        id="H2.P.Saturn", house=2, signification="wealth", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Saturn", 2),
        # HTJAH-I:2567-2571. The sign exception was MIS-SCOPED: detached into `fortified` it
        # read as cancelling the WHOLE malefic entry, where Raman scopes it to the
        # uphill-earning clause alone — "Saturn, UNLESS the second is Libra, Capricorn or
        # Aquarius, tends to make earning an uphill struggle" (2567-2568). Harsh speech,
        # unsocial habits, unhappy family life and unpopularity are not exempted. It now
        # travels with its own sentence. Restores "sorrowful and roaming about aimlessly...
        # seldom takes advantage of them" (2568-2570), dropped by the old encoding.
        general="unless the 2nd is Libra, Capricorn or Aquarius, earning tends to be an "
                "uphill struggle, much work with little gain; harsh speech, unsocial, "
                "sorrowful and roaming about aimlessly; comes across many opportunities but "
                "seldom takes advantage of them; unhappy in family life; gains by dealing "
                "with metals, storage, mines and labour; unpopular",
        fortified="unless the 2nd is Libra, Capricorn or Aquarius, earning tends to be an "
                  "uphill struggle, much work with little gain; harsh speech, unsocial, "
                  "sorrowful and roaming about aimlessly; comes across many opportunities but "
                  "seldom takes advantage of them; unhappy in family life; gains by dealing "
                  "with metals, storage, mines and labour; unpopular",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 2567)),
    RuleRecord(
        id="H2.P.Rahu", house=2, signification="wealth", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Rahu", 2),
        # HTJAH-I:2573-2575. The `afflicted` slot was Raman's opening unconditioned run.
        # "Money is gained through friends and business" (2575) is UNDETERMINED — a fresh
        # sentence after the Jupiter clause — so it stays in `fortified` rather than being
        # moved on a guess.
        general="peevish, diseased face, friction in family life, danger to eye-sight; "
                "financial affairs uncertain unless other favourable combinations occur",
        fortified="peevish, diseased face, friction in family life, danger to eye-sight; "
                  "financial affairs uncertain unless other favourable combinations occur; "
                  "money is gained through friends and business",
        afflicted="(an aspect, not an affliction) Jupiter aspecting the 2nd house → earnings "
                  "will be good",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 2573)),
    RuleRecord(
        id="H2.P.Ketu", house=2, signification="wealth", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Ketu", 2),
        # HTJAH-I:2577-2578: four flat sentences; the one positive was lifted into
        # `fortified` purely by sentiment.
        general="bad speaker; loss through fraud and deception; there will be liability in "
                "financial affairs; success in spiritualism, navigation, mystical arts, "
                "hospitals and the like may be expected",
        fortified="bad speaker; loss through fraud and deception; there will be liability in "
                  "financial affairs; success in spiritualism, navigation, mystical arts, "
                  "hospitals and the like may be expected",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 2577)),
)
