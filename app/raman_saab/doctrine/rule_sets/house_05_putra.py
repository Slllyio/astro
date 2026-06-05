"""House 5 (Putra — children/intellect) RuleRecords.

Lord-of-the-5th in the 12 houses, encoded from B.V. Raman,
*How to Judge a Horoscope*, Vol. I, Chapter VIII "The Fifth House."
Each record is one row of Raman's placement table (HTJAH-I:5112–5171)
with Raman's fortified/afflicted scaling caveat (HTJAH-I:5173–5175):
"general results … have to be used with great care paying particular
attention to the benefic, malefic, or moderating nature of the lord."

Primary signification: "children" (the dominant matter of the 5th;
intellect, poorvapunya, speculation are secondaries judged in sub-matter
routing from the same pillar).

Source span: HTJAH-I:5010–5981.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    RuleRecord(
        id="H5.L.1", house=5, signification="children", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(5, 1),
        fortified="commands servants; Judge / Magistrate / Minister empowered to punish; "
                  "earns grace of God; few children; gives happiness to others",
        afflicted="no issues; invokes kshudra-devatas; evil-minded; leader of a gang of "
                  "deceitful persons; tale-bearer with a sting",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 5112)),
    RuleRecord(
        id="H5.L.2", house=5, signification="children", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(5, 2),
        fortified="beautiful wife and well-behaving children; gains from Government/King; "
                  "becomes learned and a good astrologer",
        afflicted="poor; loss of money via Government displeasure; cannot maintain family; "
                  "family troubles; becomes a priest in a Siva temple",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5119)),
    RuleRecord(
        id="H5.L.3", house=5, signification="children", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(5, 3),
        fortified="many good children and brothers",
        afflicted="loss of children; misunderstandings with brothers; continuous occupational "
                  "troubles; stingy, a tale-bearer",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 5125)),
    RuleRecord(
        id="H5.L.4", house=5, signification="children", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(5, 4),
        fortified="a few sons (one lives by agriculture); mother lives long; "
                  "may advise a ruler or be his preceptor",
        afflicted="lord afflicted — death of children; lord moderate — daughters and no sons",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 5129)),
    RuleRecord(
        id="H5.L.5", house=5, signification="children", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(5, 5),
        fortified="number of sons; becomes great in his own line; expert in Mantra Shastra; "
                  "befriends the powerful; expert in mathematics or head of a religious institution",
        afflicted="children will die; will not keep his word; wavering mentality; cruel",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5137)),
    RuleRecord(
        id="H5.L.6", house=5, signification="children", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(5, 6),
        fortified="maternal uncle becomes famous; enmity with his own son",
        afflicted="no issues born; may adopt one from maternal uncle's line",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5143)),
    RuleRecord(
        id="H5.L.7", house=5, signification="children", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(5, 7),
        fortified="son lives abroad and attains distinction, wealth and fame; or many issues; "
                  "renowned, learned, prosperous, devoted to master, charming personality",
        afflicted="loss of children, one of whom dies abroad after attaining name and fame",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5147)),
    RuleRecord(
        id="H5.L.8", house=5, signification="children", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(5, 8),
        fortified="no specific benefit noted",
        afflicted="paternal property lost to debts; extinction of family; lung trouble; "
                  "peevish, unhappy but not poor",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5153)),
    RuleRecord(
        id="H5.L.9", house=5, signification="children", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(5, 9),
        fortified="teacher or preceptor; renovates ancient temples, wells, choultries, gardens; "
                  "a son distinguished as orator or author",
        afflicted="earns divine wrath leading to destruction of fortune",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5156)),
    RuleRecord(
        id="H5.L.10", house=5, signification="children", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(5, 10),
        fortified="Raja Yoga; landed property; goodwill of rulers; builds temples, performs "
                  "sacrifices; a son becomes a gem of the family; Sun-aspected may join the "
                  "intelligence department",
        afflicted="faces the wrath of rulers; contrary results",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5160)),
    RuleRecord(
        id="H5.L.11", house=5, signification="children", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(5, 11),
        fortified="benefits through sons; success in all undertakings; rich, learned, helpful; "
                  "many sons; becomes an author",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5166)),
    RuleRecord(
        id="H5.L.12", house=5, signification="children", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(5, 12),
        fortified="quest for the Ultimate Reality; non-attachment; spiritual; wanders; "
                  "ultimately attains Moksha",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 5169)),

    # — Planets in the 5th House (HTJAH-I:5232–5295) —
    RuleRecord(
        id="H5.P.Sun", house=5, signification="children", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Sun", 5),
        fortified=None,
        afflicted="deprived of children, riches, happiness; short life; heart disease; "
                  "roams forests; a mountaineer; difficult child-birth; afflicted → loss "
                  "through speculation, trouble with cousins",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5232)),
    RuleRecord(
        id="H5.P.Moon", house=5, signification="children", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Moon", 5),
        fortified="clarity of mind; happiness from children; lands, gems, precious stones; "
                  "chance to serve the State; straightforward, truthful, learned, god-fearing, "
                  "no enemies; speculation; one child becomes famous",
        afflicted="joins/aspected by malefics → loss through children and loose sex relations; "
                  "Mars affliction → intrigues, loose sex relations",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5236)),
    RuleRecord(
        id="H5.P.Mars", house=5, signification="children", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Mars", 5),
        fortified="strengthened → gains via lands, chemicals, factories; rash speculation",
        afflicted="miserable re wife, friends, children; disturbed thoughts; rash, weak-minded, "
                  "back-biter; colic; misfortune through children; over-attached to sex → loss "
                  "of health; dangerous child-birth (female chart); affliction → ruin and disgrace "
                  "through opposite sex",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5241)),
    RuleRecord(
        id="H5.P.Mercury", house=5, signification="children", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Mercury", 5),
        fortified="learned and happy; number of children; adviser or minister; highly intelligent; "
                  "learned in Mantrasastras; Jupiter-aspected → gain via speculation and authorship",
        afflicted="too much sex → low vitality; afflicted → anxiety and worry through children; "
                  "Mars-afflicted → scandal in love affairs, emotion over reason",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5244)),
    RuleRecord(
        id="H5.P.Jupiter", house=5, signification="children", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Jupiter", 5),
        fortified="learned in logic, law, mantrasastra; highly intelligent; preceptor or adviser "
                  "to a king; great discrimination; good friends, vehicles, decorous manners; "
                  "many children; god-fearing; happy; strengthened → life smooth",
        afflicted="afflicted → troubles per the afflicting planet's nature",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5248)),
    RuleRecord(
        id="H5.P.Venus", house=5, signification="children", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Venus", 5),
        fortified="poetic; many friends and beautiful children; happiness through offspring; wise, "
                  "discriminating; acquires wealth; respected by State; more female children; success "
                  "in speculation; well-fortified → gains via females and attachments to actresses "
                  "or singers",
        afflicted="afflicted → loss of health via over-indulgence; with Rahu → homosexual "
                  "tendencies; with Ketu → platonic love",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5252)),
    RuleRecord(
        id="H5.P.Saturn", house=5, signification="children", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Saturn", 5),
        fortified="strengthened by Jupiter → gains in mines",
        afflicted="evil-minded and stupid; sickly, weak; poor, hated; sorrows through children; "
                  "variable unsteady fortune; hypocritical; quarrels with friends or relatives; "
                  "domestic sorrow; Mars-afflicted → unnatural attachments (especially to elders), "
                  "loss of children, danger of drowning, heart trouble",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5258)),
    RuleRecord(
        id="H5.P.Rahu", house=5, signification="children", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Rahu", 5),
        fortified=None,
        afflicted="colic; mistaken by others, unfriended; loses a number of children; "
                  "hard-hearted, unconventional; heart trouble; affliction is a very bad "
                  "combination → scandal through children; with Venus → homosexual tendencies",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5262)),
    RuleRecord(
        id="H5.P.Ketu", house=5, signification="children", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Ketu", 5),
        fortified=None,
        afflicted="loss of children; stomach trouble; strange experiences in emotions and feelings; "
                  "later inclination to spirituality; afflicted → criminal tendencies, lacks shame, "
                  "vindictive; lacks the human touch toward one or two of the issues; with Venus → "
                  "platonic love; Mars the afflicter → many dangers, family extinguished",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5265)),
)
