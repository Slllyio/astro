"""House 1 (Tanu Bhava / Lagna) — lord of the 1st in the 12 houses.

Encoded from the methodology table in `docs/raman_saab/methodology/house_01_lagna.md`
(section "Lord of the 1st in the 12 Houses"). Each row cites a HTJAH-I span;
`source.line` is set to the FIRST line of that span, which is the first line of
Raman's text for that placement.

SLOT MAPPING CORRECTED 2026-09-01 after an engine-blind doctrine review. Raman writes each
placement in two paragraphs: a GENERAL, unconditioned reading, then one conditioned on
FORTIFICATION -- "If the Lagnadhipati is well disposed" (1000), "Well disposed." (1012),
"When Lagnadhipati is well disposed" (1019), "If the 4th lord is favourably disposed" (1026),
"If fortified:" (1035), "When the lord is fortified" (1043), "If well disposed" (1054), "If
the lord is strong" (1059), "Provided the lord is well disposed" (1065). That is NINE
fortification openers and ZERO affliction openers: in HTJAH-I:997-1082 Raman gives no
afflicted reading for these placements at all. He states the design himself at
HTJAH-I:1003-1007 -- "the combination is of general application... The same rules apply to
all Bhava."

This module previously read that general paragraph as the afflicted pole, so `_branch` showed
a weak-lord chart Raman's BASE reading under an "afflicted" heading. On H1.L.3 and H1.L.9
that meant presenting a blessing ("highly courageous, fortunate... intelligent, happy";
"generally fortunate... good orator... and rich") as an affliction. The general text now sits
in the `general` slot added for it and `afflicted` is None -- EXCEPT on H1.L.1, whose old
slot text ended with a genuine afflicted clause Raman gives at HTJAH-I:1088-1089; that clause
is preserved.

The old note claimed his "general rule (HTJAH-I:1003-1007) that evil aspect/weakness inverts
or worsens the base reading". 1003-1007 says the results should be INTERPRETED by taking
strength into account; it does not say weakness inverts the base reading, and no such
inversion is printed anywhere in this section.

Source span: HTJAH-I:997-1082. Karaka = Sun (Thanu Karaka).
Moved verbatim from the former single-module `house_01_lagna.py` (Stage-1 split).
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    RuleRecord(
        id="H1.L.1", house=1, signification="self", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-1 sweep: the old afflicted text (HTJAH-I:1088-1089) is gated on
        # 'evil combinations' -- an AFFLICTION test from the Other Important Combinations
        # section, not the Lagna lord's weakness. Re-homed to H1.L.1a.
        condition=C.LordIn(1, 1),
        fortified="becomes famous in his own community and country",
        general="lives by own exertion, independent spirit, two wives or one married and "
                "one illegal",
        # HTJAH-I:1088-1089 verbatim: "If the ascendant lord is posited in the Lagna subject
        # to evil combinations, the native will not be physically happy." A real afflicted
        # reading Raman does give for this placement, so it is kept.
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 997)),
    # 'Evil combinations' read as malefic contact, per Raman's own gloss at
    # HTJAH-I:1005-1006 ('in Lagna and aspected by evil planets'). Neutral: refines a parent
    # that already votes for this placement.
    RuleRecord(
        id="H1.L.1a", house=1, signification="self", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(1, 1), C.AfflictedBy("LORD_OF:1")),
        general="the ascendant lord in the Lagna subject to evil combinations - the native "
                "will not be physically happy",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 1088)),
    RuleRecord(
        id="H1.L.2", house=1, signification="self", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(1, 2),
        fortified="gladly discharges duties to kith and kin; ambitious, prominent eyes, blessed "
                  "with forethought",
        general="more of gains but teased or worried by enemies; good character, "
                "respectable, generous-hearted",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 1009)),
    RuleRecord(
        id="H1.L.3", house=1, signification="self", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(1, 3),
        fortified="rise in life brought about by brothers; may become famous as musician or "
                  "mathematician",
        general="highly courageous, fortunate, respectable, two wives, intelligent, happy",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 1015)),
    RuleRecord(
        id="H1.L.4", house=1, signification="self", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-1 sweep: HTJAH-I:1026 opens 'If the 4th lord is favourably
        # disposed' -- a DIFFERENT planet from the branch subject (the Lagna lord). Re-homed
        # to H1.L.4a.
        condition=C.LordIn(1, 4),
        fortified=None,
        general="happiness from parents, many brothers, materialistic, well-built, "
                "fair-looking, well-behaved",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 1023)),
    RuleRecord(
        id="H1.L.4a", house=1, signification="self", group="lord_in_house",
        kind="descriptive",
        condition=None,
        general=None,
        fortified="the 4th lord favourably disposed - the person will acquire considerable "
                  "landed properties, specially through maternal sources; rich, happy, "
                  "famous, and commands a number of conveyances. TODO(predicate: strength "
                  "of LORD_OF:4 with LordIn(1, 4) - no strength Condition exists for "
                  "another house's lord)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 1026)),
    RuleRecord(
        id="H1.L.5", house=1, signification="self", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(1, 5),
        fortified="in good graces of rulers/powerful parties; absorbed into trade or diplomatic "
                  "services; propitiates deities per 5th-lord indications",
        # Unconditioned like the rest; it merely READS grim, which is exactly why the
        # mis-mapping stayed invisible here and showed itself only on L.3 and L.9.
        general="first child does not survive, not much happiness from children, "
                "short-tempered, subservient, serving others",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 1030)),
    RuleRecord(
        id="H1.L.6", house=1, signification="self", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(1, 6),
        fortified="joins the army, becomes Commander/Commander-in-Chief (if lord's Dasha "
                  "operates), or head of medical/health services, expert physician/surgeon",
        general="the results of the lord in the 3rd, plus debts - liquidated when the "
                "Lagnadhipati's Dasha comes",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 1039)),
    RuleRecord(
        id="H1.L.7", house=1, signification="self", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(1, 7),
        fortified="spends most time in foreign countries, leads a licentious life; or a puppet "
                  "of parents-in-law",
        general="the wife does not live, or more than one marriage; later detached from "
                "worldly affairs and tries an ascetic life; much travelling; rich or poor "
                "according to other factors",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 1048)),
    RuleRecord(
        id="H1.L.8", house=1, signification="self", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(1, 8),
        fortified="takes pride in helping others, many friends, religiously inclined, peaceful "
                  "and sudden end",
        general="learned, gambling tendencies, interested in occultism, mean character",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 1057)),
    RuleRecord(
        id="H1.L.9", house=1, signification="self", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(1, 9),
        fortified="inherits good ancestral/paternal property; father famous, philanthropic, "
                  "god-fearing",
        general="generally fortunate, protector of others, religious (if a Hindu, a "
                "worshipper of Vishnu), good orator, happiness on account of wife and "
                "children, and rich",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 1062)),
    RuleRecord(
        id="H1.L.10", house=1, signification="self", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(1, 10),
        # HTJAH-I:1068-1070 is ONE unconditioned sentence; the encoder split it in two and
        # filed half under "afflicted". Raman gives no conditioned reading here at all, so
        # `fortified` carries the same text (the H5.L.11 / H9.L.1 convention) and the fired
        # prose is never empty.
        general="in addition to the results of the 4th house: professional success, honoured "
                "by eminent men, a research scholar or specialisation in the branch of "
                "knowledge or profession represented by the lords of Lagna and the 10th",
        fortified="in addition to the results of the 4th house: professional success, "
                  "honoured by eminent men, a research scholar or specialisation in the "
                  "branch of knowledge or profession represented by the lords of Lagna and "
                  "the 10th",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 1068)),
    RuleRecord(
        id="H1.L.11", house=1, signification="self", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(1, 11),
        # HTJAH-I:1072-1076 -- BOTH paragraphs are unconditioned (the second carries no
        # "if well disposed" marker), so neither of them is a strength branch.
        general="in addition to the results of the 2nd house: always gains in business if a "
                "businessman, and no financial straits; owes his prosperity to his elder "
                "brother, and earns enormous business profits consistent with the other "
                "planets joining the combination",
        fortified="in addition to the results of the 2nd house: always gains in business if "
                  "a businessman, and no financial straits; owes his prosperity to his elder "
                  "brother, and earns enormous business profits consistent with the other "
                  "planets joining the combination",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 1072)),
    RuleRecord(
        id="H1.L.12", house=1, signification="self", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(1, 12),
        # HTJAH-I:1078-1082 -- both paragraphs unconditioned, as in L.11.
        general="the same results as the 8th, plus many losses, visiting holy places and no "
                "success in business enterprises; spends inherited riches on charities and "
                "other deserving causes; emotionally balanced, dedicates himself to the "
                "public weal",
        fortified="the same results as the 8th, plus many losses, visiting holy places and "
                  "no success in business enterprises; spends inherited riches on charities "
                  "and other deserving causes; emotionally balanced, dedicates himself to "
                  "the public weal",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 1078)),
)
