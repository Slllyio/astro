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
        # Relocated 2026-09-01: Raman states this flatly for the placement, so it is
        # his GENERAL reading, not a strength branch. Text copied verbatim — this
        # section was ruled unconditioned by the planet_in_house sweep's review, and
        # the mirror also fixes a rendering bug (a lone `afflicted` slot renders
        # NOTHING on a strong-lord chart, because `_branch` returns 'fortified').
        general="deprived of children, riches, happiness; short life; heart disease; "
                "roams forests; a mountaineer; difficult child-birth; afflicted → loss "
                "through speculation, trouble with cousins",
        fortified="deprived of children, riches, happiness; short life; heart disease; "
                  "roams forests; a mountaineer; difficult child-birth; afflicted → loss "
                  "through speculation, trouble with cousins",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5232)),
    RuleRecord(
        id="H5.P.Moon", house=5, signification="children", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Moon", 5),
        # LEAVE the afflicted slot - 5269-5273 gives four genuine affliction clauses.
        # fortified=None: Raman gives the Moon in the 5th NO fortification branch anywhere.
        # Adds the two affliction clauses that were unencoded (5271-5272).
        # LEAVE the afflicted slot - 5269-5273 gives four genuine affliction clauses.
        # fortified=None: Raman gives the Moon in the 5th NO fortification branch anywhere.
        # Adds the two affliction clauses that were unencoded (5271-5272).
        general="clarity of mind; happiness from children; lands, gems and precious stones; a "
                "chance to serve the State; straightforward, truthful, learned, god-fearing, "
                "with no enemies; gains by speculation; one child becomes famous; gentlemanly",
        fortified=None,
        afflicted="the Moon joining malefics or aspected by them -> loss through children and "
                  "loose sex relations; if the afflicting planet be Mars -> intrigues, loose "
                  "sex relations, and children die after some time; if the afflicting planet "
                  "is Saturn -> fear of brain derangement",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5236)),
    RuleRecord(
        id="H5.P.Mars", house=5, signification="children", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Mars", 5),
        # SPLIT. 5275-5276 ('trouble and danger through children'; 'inclination to rush
        # into rash speculations') is unconditioned - the sentence between it and the
        # strengthened-clause shows the strengthened branch does not extend that far, so
        # 'rash speculation' leaves fortified. 'Dangerous child-birth' is a GENDER
        # condition (5244), not an affliction.
        # SPLIT. 5275-5276 ('trouble and danger through children'; 'inclination to rush
        # into rash speculations') is unconditioned - the sentence between it and the
        # strengthened-clause shows the strengthened branch does not extend that far, so
        # 'rash speculation' leaves fortified. 'Dangerous child-birth' is a GENDER
        # condition (5244), not an affliction.
        general="miserable in regard to wife, friends and children; disturbed thoughts; rash, "
                "weak-minded and a back-biter; colic; misfortune through children; over- "
                "attached to sex, with loss of health; trouble and danger through children are "
                "shown; an inclination to rush into rash speculations; in a female chart, "
                "dangerous child-birth (a gender condition, not an affliction)",
        fortified="Mars strengthened -> gains through lands, chemicals and factories",
        afflicted="affliction of Mars -> danger of ruin and disgrace through the opposite sex",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5241)),
    RuleRecord(
        id="H5.P.Mercury", house=5, signification="children", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Mercury", 5),
        # SPLIT. 'Inclined to too much of sex pleasure and consequently lacking in
        # vitality' is unconditioned in the base entry and led the old afflicted slot.
        # The Jupiter clause is an ASPECT condition (5278).
        # SPLIT. 'Inclined to too much of sex pleasure and consequently lacking in
        # vitality' is unconditioned in the base entry and led the old afflicted slot.
        # The Jupiter clause is an ASPECT condition (5278).
        general="learned and happy; a number of children; an adviser or minister; highly "
                "intelligent; learned in the Mantrasastras; inclined to too much of sex "
                "pleasure and consequently lacking in vitality",
        fortified="(an aspect, not fortification) well aspected by Jupiter -> gain via "
                  "speculation and authorship",
        afflicted="Mercury afflicted -> anxiety and worry through children; afflicted by Mars "
                  "-> scandal in love affairs, emotion over reason",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5244)),
    RuleRecord(
        id="H5.P.Jupiter", house=5, signification="children", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Jupiter", 5),
        # LEAVE the afflicted slot (5280-5281, 'If afflicted'). Mirror defect only.
        # LEAVE the afflicted slot (5280-5281, 'If afflicted'). Mirror defect only.
        general="learned in logic, law and mantrasastra; highly intelligent; a preceptor or "
                "adviser to a king; great discrimination; good friends, vehicles and decorous "
                "manners; many children; god-fearing and happy",
        fortified="Jupiter strengthened -> life runs smooth",
        afflicted="Jupiter afflicted -> troubles according to the nature of the afflicting "
                  "planet",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5248)),
    RuleRecord(
        id="H5.P.Venus", house=5, signification="children", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Venus", 5),
        # LEAVE the first afflicted clause (5281-5285). Mirror defect on the base reading,
        # and the Rahu/Ketu clauses are CONJUNCTIONS stated inside Raman's Rahu and Ketu
        # paragraphs. Adds his three unencoded Venus affliction clauses (5283-5285).
        # LEAVE the first afflicted clause (5281-5285). Mirror defect on the base reading,
        # and the Rahu/Ketu clauses are CONJUNCTIONS stated inside Raman's Rahu and Ketu
        # paragraphs. Adds his three unencoded Venus affliction clauses (5283-5285).
        general="poetic; possesses a number of friends and beautiful children; happiness "
                "through offspring; wise and discriminating; acquires wealth; respected by the "
                "State; more female children; success in speculation",
        fortified="Venus well-fortified -> gains via females, and attachments to actresses or "
                  "singers",
        afflicted="Venus afflicted -> loss of health via over-indulgence; if Mars is the "
                  "afflicting planet -> indiscriminate bestowal of affection on children; Rahu "
                  "afflicting -> strange courtships; Saturn afflicting -> disappointments in "
                  "love affairs; (conjunctions, not afflictions) with Rahu -> homosexual "
                  "tendencies; with Ketu -> platonic love",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 5252)),
    RuleRecord(
        id="H5.P.Saturn", house=5, signification="children", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Saturn", 5),
        # SPLIT. The base list (5258-5260) is unconditioned; fortified and the
        # Mars-affliction clause were both already correct and are kept.
        # SPLIT. The base list (5258-5260) is unconditioned; fortified and the
        # Mars-affliction clause were both already correct and are kept.
        general="evil-minded and stupid; sickly and weak; poor and hated; sorrows through "
                "children; variable, unsteady fortune; hypocritical; quarrels with friends or "
                "relatives; domestic sorrow",
        fortified="Saturn's position strengthened by Jupiter -> gains in mines",
        afflicted="Saturn afflicted by Mars -> unnatural attachments (especially to elders), "
                  "loss of children, danger of drowning, heart trouble",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5258)),
    RuleRecord(
        id="H5.P.Rahu", house=5, signification="children", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Rahu", 5),
        # Relocated 2026-09-01: Raman states this flatly for the placement, so it is
        # his GENERAL reading, not a strength branch. Text copied verbatim — this
        # section was ruled unconditioned by the planet_in_house sweep's review, and
        # the mirror also fixes a rendering bug (a lone `afflicted` slot renders
        # NOTHING on a strong-lord chart, because `_branch` returns 'fortified').
        general="colic; mistaken by others, unfriended; loses a number of children; "
                "hard-hearted, unconventional; heart trouble; affliction is a very bad "
                "combination → scandal through children; with Venus → homosexual tendencies",
        fortified="colic; mistaken by others, unfriended; loses a number of children; "
                  "hard-hearted, unconventional; heart trouble; affliction is a very bad "
                  "combination → scandal through children; with Venus → homosexual tendencies",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5262)),
    RuleRecord(
        id="H5.P.Ketu", house=5, signification="children", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Ketu", 5),
        # Relocated 2026-09-01: Raman states this flatly for the placement, so it is
        # his GENERAL reading, not a strength branch. Text copied verbatim — this
        # section was ruled unconditioned by the planet_in_house sweep's review, and
        # the mirror also fixes a rendering bug (a lone `afflicted` slot renders
        # NOTHING on a strong-lord chart, because `_branch` returns 'fortified').
        general="loss of children; stomach trouble; strange experiences in emotions and feelings; "
                "later inclination to spirituality; afflicted → criminal tendencies, lacks shame, "
                "vindictive; lacks the human touch toward one or two of the issues; with Venus → "
                "platonic love; Mars the afflicter → many dangers, family extinguished",
        fortified="loss of children; stomach trouble; strange experiences in emotions and feelings; "
                  "later inclination to spirituality; afflicted → criminal tendencies, lacks shame, "
                  "vindictive; lacks the human touch toward one or two of the issues; with Venus → "
                  "platonic love; Mars the afflicter → many dangers, family extinguished",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 5265)),
)
