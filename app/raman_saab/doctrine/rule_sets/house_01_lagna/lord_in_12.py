"""House 1 (Tanu Bhava / Lagna) — lord of the 1st in the 12 houses.

Encoded from the methodology table in `docs/raman_saab/methodology/house_01_lagna.md`
(section "Lord of the 1st in the 12 Houses"). Each row cites a HTJAH-I span;
`source.line` is set to the FIRST line of that span, which is the first line of
Raman's text for that placement. Fortified vs. afflicted readings follow his
general rule (HTJAH-I:1003-1007) that evil aspect/weakness inverts or worsens the
base reading; where the methodology records no separate afflicted clause the
afflicted field is None.

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
        condition=C.LordIn(1, 1),
        fortified="becomes famous in his own community and country",
        afflicted="lives by own exertion, independent spirit, two wives or one married + one "
                  "illegal; subject to evil combinations, not physically happy",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 997)),
    RuleRecord(
        id="H1.L.2", house=1, signification="self", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(1, 2),
        fortified="gladly discharges duties to kith and kin; ambitious, prominent eyes, blessed "
                  "with forethought",
        afflicted="more of gains but teased/worried by enemies; good character, respectable, "
                  "generous-hearted",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 1009)),
    RuleRecord(
        id="H1.L.3", house=1, signification="self", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(1, 3),
        fortified="rise in life brought about by brothers; may become famous as musician or "
                  "mathematician",
        afflicted="highly courageous, fortunate, respectable, two wives, intelligent, happy",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 1015)),
    RuleRecord(
        id="H1.L.4", house=1, signification="self", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(1, 4),
        fortified="acquires considerable landed property (especially maternal), rich, happy, "
                  "famous, many conveyances",
        afflicted="happiness from parents, many brothers, materialistic, well-built, "
                  "fair-looking, well-behaved",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 1023)),
    RuleRecord(
        id="H1.L.5", house=1, signification="self", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(1, 5),
        fortified="in good graces of rulers/powerful parties; absorbed into trade or diplomatic "
                  "services; propitiates deities per 5th-lord indications",
        afflicted="first child does not survive, not much happiness from children, "
                  "short-tempered, subservient, serving others",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 1030)),
    RuleRecord(
        id="H1.L.6", house=1, signification="self", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(1, 6),
        fortified="joins the army, becomes Commander/Commander-in-Chief (if lord's Dasha "
                  "operates), or head of medical/health services, expert physician/surgeon",
        afflicted="results of lord-in-3rd plus debts (liquidated in Lagna-lord's Dasha)",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 1039)),
    RuleRecord(
        id="H1.L.7", house=1, signification="self", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(1, 7),
        fortified="spends most time in foreign countries, leads a licentious life; or a puppet "
                  "of parents-in-law",
        afflicted="wife does not live / more than one marriage; later detached, tries ascetic "
                  "life; much travelling; rich or poor per other factors",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 1048)),
    RuleRecord(
        id="H1.L.8", house=1, signification="self", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(1, 8),
        fortified="takes pride in helping others, many friends, religiously inclined, peaceful "
                  "and sudden end",
        afflicted="learned, gambling tendencies, interested in occultism, mean character",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 1057)),
    RuleRecord(
        id="H1.L.9", house=1, signification="self", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(1, 9),
        fortified="inherits good ancestral/paternal property; father famous, philanthropic, "
                  "god-fearing",
        afflicted="generally fortunate, protector of others, religious (if Hindu, worshipper of "
                  "Vishnu), good orator, happiness from wife and children, rich",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 1062)),
    RuleRecord(
        id="H1.L.10", house=1, signification="self", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(1, 10),
        fortified="professional success, honoured by eminent men, research scholar / "
                  "specialisation in field of Lagna and 10th lords",
        afflicted="results of the 4th house plus professional success",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 1068)),
    RuleRecord(
        id="H1.L.11", house=1, signification="self", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(1, 11),
        fortified="owes prosperity to elder brother; earns enormous business profits per other "
                  "planets",
        afflicted="results of the 2nd house plus always gains in business; no financial straits",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 1072)),
    RuleRecord(
        id="H1.L.12", house=1, signification="self", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(1, 12),
        fortified="spends inherited riches on charities/deserving causes; emotionally balanced; "
                  "dedicates self to public weal",
        afflicted="same results as the 8th, plus many losses, visiting holy places, no success "
                  "in business",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 1078)),
)
