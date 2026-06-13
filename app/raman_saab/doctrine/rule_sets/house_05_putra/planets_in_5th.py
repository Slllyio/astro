"""House 5 (Putra) — Planets-in-the-5th RuleRecords (HTJAH-I:5232-5295).

Moved verbatim from the former flat ``house_05_putra.py`` (Stage-4 split)."""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
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
