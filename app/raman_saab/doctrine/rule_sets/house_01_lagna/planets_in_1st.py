"""House 1 (Tanu Bhava / Lagna) — the nine planets in the 1st house.

Source span: HTJAH-I:1499-1562; each record cites the first line of its planet's
paragraph. Moved verbatim from the former single-module `house_01_lagna.py`
(Stage-1 split).
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    RuleRecord(
        id="H1.P.Sun", house=1, signification="self", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Sun", 1),
        # HTJAH-I:1499-1503, no opener of either strength kind. The `afflicted` slot is
        # entirely a CONJUNCTION clause (1502) — kept and labelled, not swept into `general`.
        general="strong moral nature, righteous-minded, ambition and love of power; well "
                "supported by good health and vitality; cheerfulness and an optimistic "
                "temperament ensure popularity; adds respect to the personality and gives "
                "lofty motives",
        fortified="strong moral nature, righteous-minded, ambition and love of power; well "
                  "supported by good health and vitality; cheerfulness and an optimistic "
                  "temperament ensure popularity; adds respect to the personality and gives "
                  "lofty motives",
        afflicted="(a conjunction, not an affliction) with Saturn or Mars → scars and a hot "
                  "constitution, impure blood, itches all over the body, fevers, "
                  "inflammations, eye affections",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 1499)),
    RuleRecord(
        id="H1.P.Moon", house=1, signification="self", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Moon", 1),
        # DIRECTION INVERSION FIXED 2026-09-01. All four clauses in the old `afflicted`
        # slot are CONJUNCTION conditions (HTJAH-I:1507-1511), not afflictions — and one of
        # them is POSITIVE: Raman writes "and with Jupiter, the mind is elevated". Rendering
        # a fortifying conjunction under an "afflicted" heading tells the reader the exact
        # opposite of his sentence. The base reading, which was in `fortified`, is
        # unconditioned. Raman states the axis himself at 1480-1481: a planet's effects "by
        # house position, as given below, are subjected to modification" by aspect and
        # conjunction — configuration, not strength.
        general="fanciful and romantic, a moderate eater; considerable restlessness tempered "
                "by an easy-going disposition; the fortune is generally changing; an "
                "idealist, a great traveller and explorer; sociability a strong feature; "
                "successful in professions that bring him into contact with the masses",
        fortified="fanciful and romantic, a moderate eater; considerable restlessness "
                  "tempered by an easy-going disposition; the fortune is generally changing; "
                  "an idealist, a great traveller and explorer; sociability a strong feature; "
                  "successful in professions that bring him into contact with the masses",
        afflicted="(conjunctions, not afflictions - Raman's polarity preserved) with Saturn: "
                  "the mind will always be worried; with Mars: menstrual disorders in a "
                  "woman's chart; with Rahu: hysterical tendencies; with Jupiter: the mind "
                  "is ELEVATED",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 1505)),
    RuleRecord(
        id="H1.P.Mars", house=1, signification="self", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Mars", 1),
        # HTJAH-I:1511-1517, zero conditionals. One paragraph cut across both slots by
        # sentiment, mid-sequence: "He becomes reckless of danger scorning defeat. This gives
        # somewhat of a rash nature. The body will have scars and the appearance will be
        # handsome." (1513-1514) — "scars" to afflicted, "handsome" to fortified.
        general="a hot constitution, courage, self-confidence and enterprise; practical "
                "ability and love of liberty and independence; reckless of danger, scorning "
                "defeat, somewhat rash; the body will have scars and the appearance will be "
                "handsome; domestic life unhappy unless there are other favourable "
                "combinations; abuse of physical resources may lead to ill-health; proneness "
                "to accidents; the aspects should be carefully examined; danger of cuts and "
                "burns",
        fortified="a hot constitution, courage, self-confidence and enterprise; practical "
                  "ability and love of liberty and independence; reckless of danger, scorning "
                  "defeat, somewhat rash; the body will have scars and the appearance will be "
                  "handsome; domestic life unhappy unless there are other favourable "
                  "combinations; abuse of physical resources may lead to ill-health; "
                  "proneness to accidents; the aspects should be carefully examined; danger "
                  "of cuts and burns",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 1511)),
    RuleRecord(
        id="H1.P.Mercury", house=1, signification="self", group="planet_in_house",
        kind="evaluable",
        condition=C.InRashiHouse("Mercury", 1),
        # HTJAH-I:1519-1523. Both conditional clauses are ASPECT/CONJUNCTION conditions
        # (1521, 1522-1523); the base reading sat in `fortified`.
        general="humorous; quickness of wit and mental ingenuity strongly marked; well-read, "
                "particularly in occult studies; adaptability a striking feature; makes the "
                "man intellectual",
        fortified="humorous; quickness of wit and mental ingenuity strongly marked; "
                  "well-read, particularly in occult studies; adaptability a striking "
                  "feature; makes the man intellectual; and (an aspect, not fortification) "
                  "in good aspect to Venus → musical and talented",
        afflicted="(a conjunction, not an affliction) Rahu or Ketu also in Lagna → much "
                  "nervous trouble",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 1519)),
    RuleRecord(
        id="H1.P.Jupiter", house=1, signification="self", group="planet_in_house",
        kind="evaluable",
        condition=C.InRashiHouse("Jupiter", 1),
        # HTJAH-I:1525-1530. The only conditional is a CONJUNCTION ("If with Rahu, sins will
        # be committed", 1527-1528); "more sons if the 5th house is not affected" is an
        # other-house condition. The self-indulgence and impure-blood clauses are
        # unconditioned. "Body will be inclined towards corpulence" (1528) is UNDETERMINED —
        # a fresh sentence right after the Rahu clause, so it is left where the encoder put
        # it rather than moved on a guess.
        general="a magnetic personality; an optimistic spirit, jovial disposition and "
                "pleasant manners; more sons if the 5th house is not affected; "
                "self-indulgence, especially in regard to gluttony, will affect health; "
                "lawyers, professors, writers and theologians come under this planet; "
                "becomes an influential leader; diseases may result from impure blood",
        fortified="a magnetic personality; an optimistic spirit, jovial disposition and "
                  "pleasant manners; more sons if the 5th house is not affected; "
                  "self-indulgence, especially in regard to gluttony, will affect health; "
                  "lawyers, professors, writers and theologians come under this planet; "
                  "becomes an influential leader; diseases may result from impure blood",
        afflicted="(a conjunction, not an affliction) with Rahu → sins will be committed; "
                  "(UNDETERMINED whether the condition carries) the body inclined towards "
                  "corpulence",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 1525)),
    RuleRecord(
        id="H1.P.Venus", house=1, signification="self", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Venus", 1),
        # HTJAH-I:1532-1539. The ONE genuine affliction opener in the whole House-1 section
        # — "If afflicted, it indicates discord in married life" (1538-1539) — is correctly
        # slotted and untouched. Only the unconditioned base reading moves, and the encoder's
        # dropped clauses ("craving for pleasure", "passions pronounced", "fondness for
        # scents and flowers", 1534-1536) are restored.
        general="fortunate, more so if the ascendant happens to be Capricorn or Aquarius; "
                "amiable, cheerful and emotional; appreciation of art; fond of music, drama "
                "and singing; there will be a craving for pleasure and the passions will be "
                "pronounced; fondness for scents and flowers; admired by the opposite sex; a "
                "magnetic personality; early marriage possible",
        fortified="fortunate, more so if the ascendant happens to be Capricorn or Aquarius; "
                  "amiable, cheerful and emotional; appreciation of art; fond of music, drama "
                  "and singing; there will be a craving for pleasure and the passions will be "
                  "pronounced; fondness for scents and flowers; admired by the opposite sex; "
                  "a magnetic personality; early marriage possible",
        afflicted="Venus afflicted → discord in married life",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 1532)),
    RuleRecord(
        id="H1.P.Saturn", house=1, signification="self", group="planet_in_house",
        kind="evaluable",
        condition=C.InRashiHouse("Saturn", 1),
        # HTJAH-I:1541-1551. The one fortification opener in the section is here, and it is
        # a NEGATED AFFLICTION: "BUT, if Saturn is not afflicted, there will be much
        # consideration for the welfare of others" (1541-1542). Raman's "But" contrasts that
        # branch AGAINST the base reading, which proves "copies foreign customs" is the base,
        # not an affliction. "Calm, grave and serious" is likewise general — he gives it
        # unconditioned in his own worked Aquarius example at 1488-1489 — so gating it behind
        # fortification was wrong. "Self-confidence / moral stability" (1544) is UNDETERMINED
        # (separated from the not-afflicted clause by a page break) and stays in `fortified`.
        general="foreign customs will be easily copied and imitated; the disposition is calm, "
                "grave and serious; the body will be weak and emaciated; progress in any "
                "venture will be slow but certain; some aversion for responsibility; this "
                "position makes habits inactive; loss through negligence and lack of "
                "opportunity are possible; misfortunes are likely in the early part of life; "
                "the same results are noticed if the ascendant is merely aspected by Saturn",
        fortified="Saturn NOT afflicted → much consideration for the welfare of others; "
                  "self-confidence is normally justified and moral stability will be marked",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 1541)),
    RuleRecord(
        id="H1.P.Rahu", house=1, signification="self", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Rahu", 1),
        fortified=None,
        afflicted="health generally unsatisfactory (needs non-medical treatment); inclines to "
                  "occult; wilful; hypocritical super-consciousness; odd and eccentric; usually "
                  "bad for marriage; partakes of Saturn's characteristics",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 1553)),
    RuleRecord(
        id="H1.P.Ketu", house=1, signification="self", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Ketu", 1),
        fortified=None,
        afflicted="psychic powers likely; weak constitution, emaciated figure; instability and "
                  "deceitfulness; morbid imagination, strange appetites, excitability, wandering "
                  "disposition; married life unhappy unless other favourable configurations",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 1559)),
)
