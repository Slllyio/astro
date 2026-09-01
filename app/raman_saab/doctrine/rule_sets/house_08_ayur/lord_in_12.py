"""House 8 (Ayur / Randhra / Mrityu Bhava — longevity/death) — Lord-in-12 RuleRecords.

Each entry encodes one row of the "Lord of the 8th in the 12 Houses" table from the
methodology doc ``house_08_ayur.md`` (HTJAH-II:2902-3069), carrying the real corpus
``Citation``. Moved verbatim from the former flat ``house_08_ayur.py`` during the
Stage-4 subpackage split (field-by-field preserved).

CONDITIONS NARROWED 2026-09-01 (user-signed; the golden baseline was re-based DOWN for it).
Raman conditions eleven of these twelve readings on the 8th lord being WITH that house's own
lord — "in conjunction with the 2nd lord in the 2nd house" (2916), "joins the 4th lord in the
4th house" (2940), "placed in the 7th house with the 7th lord" (2993), "combines with the 11th
lord in the 11th house" (3042), and so on through the section. The encoded condition was the
bare `LordIn(8, N)`, which fires on the placement alone.

Measured over the 346 golden charts before the change: the bare condition fires 345 times, the
conjunction-required condition 64 — so **81% of firings were on placements Raman's sentence
does not cover**. The 8th entry is excluded: "if the lord of the 8th house occupies the 8th
house IN STRENGTH" is a strength condition, not a conjunction.

THE COST, RECORDED HONESTLY. The narrowing changed exactly ONE scored row and fixed none:
HTJAH-II.chart_73 — LINCOLN, assassinated — H8/death went favourable where Raman says
afflicted, so exact fell 287 -> 286 and inversions rose 34 -> 35. The diagnosis is the reason
the change shipped anyway: the engine had been reaching Raman's verdict on Lincoln through
H8.L.1 firing on the bare placement (Mercury, the 8th lord, in the 1st) while Saturn, the 1st
lord, is NOT conjunct it. Raman would not have applied that rule to that chart. The old number
was right for the wrong reason, and preserving it would have been exactly the overfitting the
Prime Directive forbids ("overfitting to worked examples is not accuracy"). What the narrowing
exposes is that Lincoln's afflicted-death verdict rested entirely on a mis-encoded predicate —
a real gap in the H8 doctrine, now visible instead of masked.

A further refinement is NOT encoded and is left for its own measured pass: Raman adds a
second condition to some entries (the 9th wants the conjunction "with malefics", 3010; the
12th distinguishes benefics joining the 8th lord, 3053-3055).
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    # — Lord of the 8th in the 12 Houses (HTJAH-II:2902–3069) —
    RuleRecord(
        id="H8.L.1", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.And(C.LordIn(8, 1), C.LordsConjunct(8, 1)),
        fortified="misfortune reduced when 8th lord is weak or placed in 6/8/12 of Navamsa-Lagna",
        general="penury, heavy debts, misfortune at every step",
        afflicted="the 8th lord severely afflicted - disease and disfiguration, weak "
                  "constitution, no bodily comforts, the displeasure of superiors and "
                  "trouble from Government",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 2902)),
    RuleRecord(
        id="H8.L.2", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.And(C.LordIn(8, 2), C.LordsConjunct(8, 2)),
        fortified="evil reduced if 8th lord falls in 6/8/12 of Navamsa-Lagna",
        general="eye and tooth trouble, putrid food, domestic discontent; wife "
                "estrangement or separation; severe illness if longevity is otherwise good",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 2916)),
    RuleRecord(
        id="H8.L.3", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.And(C.LordIn(8, 3), C.LordsConjunct(8, 3)),
        fortified="conjunction with 6th/12th lords → monetary windfall via writing or a co-born",
        general="deafness or ear trouble, quarrels with siblings, fears, hallucinations, "
                "debts",
        afflicted="malefics afflicting - the troubles become unbearable",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 2927)),
    RuleRecord(
        id="H8.L.4", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.And(C.LordIn(8, 4), C.LordsConjunct(8, 4)),
        fortified=None,
        general="mental peace shattered; domestic bickerings and financial problems; the "
                "mother's health may suffer; problems regarding house, land and conveyance",
        afflicted="the affliction heavy - land and immovable property slip from his hands, "
                  "conveyances lost or destroyed, pets sicken and die; malefics furthering "
                  "the affliction force him to seek his fortune abroad, where he meets "
                  "troubles and losses",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 2940)),
    RuleRecord(
        id="H8.L.5", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.And(C.LordIn(8, 5), C.LordsConjunct(8, 5)),
        fortified="mitigated if 8th lord is in 6/12/8 of Navamsa-Lagna; fortified in "
                  "kendra/trikona → evil intensified",
        general="children get into crime or sickness; nervous breakdown "
                "(5th = buddhisthana)",
        afflicted="the affliction heavy - a child may die at birth or be retarded; and the "
                  "9th and 8th lords in the 5th with a debilitated Lagna-lord → no knowledge "
                  "or wealth, lustful, reviled",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 2957)),
    RuleRecord(
        id="H8.L.6", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.And(C.LordIn(8, 6), C.LordsConjunct(8, 6)),
        fortified="Rajayoga — affluence, fame, desired objects",
        general="ill-health (6th = disease); the maternal uncle suffers",
        afflicted="the 8th lord afflicted - theft, court and police trouble, intensified "
                  "when it falls in a kendra or trikona",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 2978)),
    RuleRecord(
        id="H8.L.7", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.And(C.LordIn(8, 7), C.LordsConjunct(8, 7)),
        fortified="if 7th and 8th lords both strong → diplomatic foreign missions, distinction",
        general="curtails longevity; the wife's ill-health",
        afflicted="the 8th lord afflicted - the native's own disease, and ill-health while "
                  "abroad",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 2993)),
    RuleRecord(
        id="H8.L.8", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(8, 8),
        fortified="long life, happiness; lands, conveyance, power and position by past-life merit",
        afflicted="if weak → no serious trouble but no luck; father may die or face crisis; "
                  "if afflicted → failure, prompted to wrong acts",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 3001)),
    RuleRecord(
        id="H8.L.9", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.And(C.LordIn(8, 9), C.LordsConjunct(8, 9)),
        fortified="with benefics → inherits father's property; harmony with father",
        afflicted="with malefics → loses father's property; if Sun afflicted, father dies in "
                  "9th-lord period; weak 9th lord → hardship, deserted by kin",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 3011)),
    RuleRecord(
        id="H8.L.10", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.And(C.LordIn(8, 10), C.LordsConjunct(8, 10)),
        fortified="may confer unexpected gains via death of superiors or elders",
        general="slow career, superseded by subordinates, deceit, the wrath of government "
                "or the law, poverty",
        afflicted="the 2nd lord also afflicted - reputation ruined by debts",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3027)),
    RuleRecord(
        id="H8.L.11", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.And(C.LordIn(8, 11), C.LordsConjunct(8, 11)),
        fortified="benefic influence → friends and elder brother help overcome troubles",
        general="trouble to close friends; elder brother's hard time, strained relations "
                "or misconduct; business losses, debts",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 3042)),
    RuleRecord(
        id="H8.L.12", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.And(C.LordIn(8, 12), C.LordsConjunct(8, 12)),
        fortified="Rajayoga; if 12th lord in trine/quadrant → religious learning, piety, "
                  "post of authority",
        afflicted="benefics joining → treachery of friends, grief, unexpected loss; "
                  "malefic-afflicted → rape, adultery, counterfeiting, smuggling",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3053)),
)
