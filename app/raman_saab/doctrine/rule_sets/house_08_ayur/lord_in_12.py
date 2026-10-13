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
    # RE-SLOTTED 2026-09-02 after an engine-blind doctrine review returned REVERSAL.
    #
    # Raman writes three sentences here, on TWO different axes (HTJAH-II:2902-2914):
    #   (a) unconditioned  — "Penury and heavy debts will befall the native... Misfortune
    #       will follow him at every step."
    #   (b) STRENGTH-gated — "If the 8th lord is weak or placed in the 6th, 8th or 12th from
    #       Navamsa Lagna, the intensity of misfortune is reduced."
    #   (c) AFFLICTION-gated — "If the 8th lord is severely afflicted the native will suffer
    #       bodily complaints such as disease and disfiguration..."
    #
    # The slot named `afflicted` is selected by `_branch` on WEAK Shadbala, so it is a
    # STRENGTH label, not an affliction label. Filing (c) there was a name pun: it showed the
    # severe-affliction reading to charts chosen by a test that never looked at an afflicter,
    # while (b) — Raman's actual weak-lord sentence — sat in `fortified`, where it told
    # STRONG-lord charts "misfortune reduced when the 8th lord is weak", asserting of that
    # chart exactly what the branch had just measured to be false. Both branches were wrong.
    #
    # That weak != severely-afflicted is settled inside this same table, not inferred: at
    # HTJAH-II:3001-3009 Raman runs all three tiers over one entry — "in strength... If the
    # 8th lord is weak, he may have no serious troubles but may not also enjoy any luck... If
    # the 8th lord is afflicted, the native will fail in his undertakings" — giving weak and
    # afflicted different, non-nested outcomes. HTJAH-II:273-276 repeats it on the 7th lord.
    # And the engine's WEAK test IS Raman's own criterion (`is_powerful` -> the GBB-8:303
    # minimum-required table), so the mapping needs no interpretation.
    RuleRecord(
        id="H8.L.1", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.And(C.LordIn(8, 1), C.LordsConjunct(8, 1)),
        # Raman gives NO strong-lord sentence. The licensed reading is the unconditioned one
        # at full force: the only mitigation offered is conditioned on weakness, so its
        # absence leaves the misfortune undiminished.
        fortified="the 8th lord strong - penury, heavy debts and misfortune at every step, "
                  "undiminished",
        general="penury, heavy debts, misfortune at every step",
        afflicted="the 8th lord weak - the intensity of the misfortune is reduced",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 2902)),
    # (b)'s second disjunct, re-homed. A Navamsa PLACEMENT, not a strength test, so it can
    # never be reached by a branch — it needed a predicate, and could not have one until the
    # varga gate opened to name-addressed divisions (2026-09-02). This is the first rule in
    # the corpus to test a varga through the generic condition rather than a hand-rolled
    # local subclass.
    RuleRecord(
        id="H8.L.1a", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(8, 1), C.LordsConjunct(8, 1),
                        C.InVargaHouseFrom("LORD_OF:8", "LAGNA", {6, 8, 12}, varga="D9")),
        fortified=None,
        general="the 8th lord in the 6th, 8th or 12th from Navamsa Lagna - the intensity of "
                "the misfortune is reduced",
        afflicted=None,
        frame="LAGNA", varga="D9", polarity="neutral", source=Citation("HTJAH-II", 2904)),
    # (c) re-homed. A genuine Raman conclusion, so it must not be deleted with the slot it
    # was wrongly occupying — that would trade a false display for a missing one. Descriptive
    # until an 8th-lord affliction predicate exists (the shape is `_MaleficAfflictsLagnaLord`,
    # house_01_lagna/combinations_core.py:99, generalised off the Lagna lord).
    RuleRecord(
        id="H8.L.1b", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable",
        # "SEVERELY afflicted" -> the corpus's established severity convention: >= 2 of the
        # first-rate malefics contacting the lord. A bare boolean would fire on one mild
        # contact and assert a severity Raman did not.
        condition=C.And(C.LordIn(8, 1), C.LordsConjunct(8, 1),
                        C.AfflictedBy("LORD_OF:8", C.FIRST_RATE_MALEFICS, min_count=2)),
        fortified=None,
        general=None,
        afflicted="the 8th lord severely afflicted - disease and disfiguration, weak "
                  "constitution, no bodily comforts, the displeasure of superiors and "
                  "trouble from Government",
        # polarity NEUTRAL by design: a refinement of a parent that already votes for this
        # placement; it displays Raman's words without counting the placement twice.
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 2906)),
    RuleRecord(
        id="H8.L.2", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.And(C.LordIn(8, 2), C.LordsConjunct(8, 2)),
        # RE-SLOTTED 2026-09-02. The slot held ONLY the D9 placement clause
        # (HTJAH-II:2923-2925), and unlike H8.L.1 this entry has no "weak or" disjunct —
        # no strength term appears anywhere in it. So strength licenses no sentence here,
        # and there is not even the "undiminished when strong" inference H8.L.1 supports.
        fortified=None,
        general="eye and tooth trouble, putrid food, domestic discontent; wife "
                "estrangement or separation; severe illness if longevity is otherwise good",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 2916)),
    RuleRecord(
        id="H8.L.2a", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(8, 2), C.LordsConjunct(8, 2),
                        C.InVargaHouseFrom("LORD_OF:8", "LAGNA", {6, 8, 12}, varga="D9")),
        fortified=None,
        general="the 8th lord in the 6th, 8th or 12th from Navamsa Lagna - the intensity of "
                "the results is reduced in degree",
        afflicted=None,
        frame="LAGNA", varga="D9", polarity="neutral", source=Citation("HTJAH-II", 2923)),
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
    # RE-SLOTTED 2026-09-02, same review, same defect class as H8.L.1 — but this entry packed
    # FOUR distinct antecedents into three slots (HTJAH-II:2957-2976):
    #   (a) unconditioned  — children in trouble/crime, father misunderstandings, child falls
    #       sick; and (2968) the buddhisthana strand, nervous debility.
    #   (b) AFFLICTION-gated — "If the affliction is heavy, a child may die as soon as it is
    #       born or ... mental retardation."
    #   (c) PLACEMENT-gated  — "If the 8th lord is in the 6th, 12th or 8th from Navamsa Lagna,
    #       the evil results are greatly mitigated."   <- no strength term AT ALL, unlike
    #       H8.L.1's "weak or", so it cannot be resolved the same way.
    #   (d) STRENGTH-gated   — "But if fortified in a kendra or trikona, the evil results are
    #       intensified."
    # plus a SEPARATE combination in its own paragraph (2972): the 9th lord conjoining the 8th
    # in the 5th with a debilitated Lagna lord.
    #
    # The worst display error in the file was (e)-as-branch: any chart with merely a weak 8th
    # lord — no 9th lord involved, Lagna lord in fine dignity — was told it had "no knowledge
    # or wealth, lustful, reviled". A missing rule masquerading as a branch.
    #
    # `afflicted` is now empty because Raman gives this entry NO weak-lord reading. That is
    # only safe since `_branch`/`fire_rules` stopped answering an empty strength slot with the
    # opposite pole (2026-09-02) — before that, emptying it would have shown a WEAK lord the
    # intensification reading, the exact opposite of nothing.
    RuleRecord(
        id="H8.L.5", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.And(C.LordIn(8, 5), C.LordsConjunct(8, 5)),
        fortified="the 8th lord fortified - the evil results are intensified",
        general="the children may get into trouble, commit some crime and invite situations "
                "affecting the native's reputation; or the native and his father develop "
                "misunderstandings; the child may fall sick; and since the 5th is the "
                "buddhisthana, nervous debility, breakdown or mental aberration",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 2957)),
    # (c) re-homed to the predicate it always needed.
    RuleRecord(
        id="H8.L.5a", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(8, 5), C.LordsConjunct(8, 5),
                        C.InVargaHouseFrom("LORD_OF:8", "LAGNA", {6, 8, 12}, varga="D9")),
        fortified=None,
        general="the 8th lord in the 6th, 12th or 8th from Navamsa Lagna - the evil results "
                "are greatly mitigated",
        afflicted=None,
        frame="LAGNA", varga="D9", polarity="neutral", source=Citation("HTJAH-II", 2965)),
    # (b) re-homed; descriptive for the same reason as H8.L.1b.
    RuleRecord(
        id="H8.L.5b", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(8, 5), C.LordsConjunct(8, 5),
                        C.AfflictedBy("LORD_OF:8", C.FIRST_RATE_MALEFICS, min_count=2)),
        fortified=None, general=None,
        afflicted="the affliction heavy - a child may die as soon as it is born, or cause "
                  "much grief through an incurable physical affliction or mental "
                  "retardation; the native may also suffer much bodily ill-health",
        # polarity NEUTRAL by design: a refinement of a parent that already votes for this
        # placement; it displays Raman's words without counting the placement twice.
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 2962)),
    # The separate paragraph at 2972, now its own rule with its own three-part antecedent.
    # Every clause is expressible today; nothing here needed new machinery.
    RuleRecord(
        id="H8.L.5c", house=8, signification="longevity", group="combination",
        kind="evaluable",
        condition=C.And(C.LordIn(8, 5), C.LordIn(9, 5), C.LordsConjunct(8, 9),
                        C.LordHasDignity(1, {"debil"})),
        fortified=None, general=None,
        afflicted="the 9th lord conjoining the 8th in the 5th with a debilitated Lagna lord "
                  "- neither knowledge nor wealth; hostile, lustful and ill-tempered; crafty, "
                  "reviles God and pious men, and is treated with contempt by wife and "
                  "children",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 2972)),
    RuleRecord(
        id="H8.L.6", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.And(C.LordIn(8, 6), C.LordsConjunct(8, 6)),
        # RE-SLOTTED 2026-09-02. The Rajayoga at HTJAH-II:2978-2980 is this entry's
        # UNCONDITIONED headline — its antecedent is the conjunction, which is already the
        # rule's `condition`. Filing it under `fortified` did not assert a falsehood; it
        # WITHHELD Raman's main reading from every weak-8th-lord chart, which shows only the
        # theft-and-police sentence. That inverts him.
        fortified=None,
        general="a Rajayoga - material affluence, fame and the acquisition of objects "
                "desired; but because the 6th is the house of disease the native may suffer "
                "ill-health; the maternal uncle may suffer much trouble",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 2978)),
    # HTJAH-II:2982-2988, re-homed off the strength slot. "If afflicted" is Raman's INFLUENCE
    # axis; the referent is the 8th lord (his subject throughout this table, explicit at 2934
    # and 3007, and named in the next sentence).
    #
    # The "kendra or trikona" tag stays PROSE and must NOT become a predicate — settled by a
    # second engine-blind review that surveyed ~160 kendra/trikona occurrences across both
    # volumes. Every one that names a frame names a RASI origin; the ~120 navamsa references
    # are always marked and always use bare ordinals, never the category words. Under D1 the
    # tag is unsatisfiable here (the entry stipulates the 8th lord in the 6th, which is
    # neither kendra nor trikona); under D9 it would be the only unmarked-navamsa reference
    # in the corpus. The economical reading is that it is Raman's IDIOM for "strong" —
    # licensed explicitly at HTJAH-II:7923, "in a kendra ... or is otherwise fortified" —
    # carried over mechanically from the near-identical sentence in the adjacent entry.
    RuleRecord(
        id="H8.L.6a", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable",
        # Raman writes a plain "If afflicted" here, not "severely" -- min_count stays 1.
        condition=C.And(C.LordIn(8, 6), C.LordsConjunct(8, 6),
                        C.AfflictedBy("LORD_OF:8")),
        fortified=None, general=None,
        afflicted="the 8th lord afflicted - loss of money through theft, and trouble through "
                  "the courts and the police; the evil intensified when the 8th lord is "
                  "strong (Raman's 'in a kendra or trikona' read as his idiom for "
                  "fortification, HTJAH-II:7923 - NOT encodable as a placement)",
        # polarity NEUTRAL by design: a refinement of a parent that already votes for this
        # placement; it displays Raman's words without counting the placement twice.
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 2986)),
    # MISSING from the corpus entirely until now (HTJAH-II:2989-2991).
    # The dignity proxy is PROVABLY unusable here: the 6th lord is in the 6th house by the
    # entry's premise, hence in its own sign, so LordHasDignity(6,{own,...}) is tautologically
    # TRUE on every firing chart. That is not a conservative under-approximation, it is a
    # constant. This needs a real Shadbala predicate, which `conditions.py` does not have.
    RuleRecord(
        id="H8.L.6b", house=8, signification="longevity", group="lord_in_house",
        kind="descriptive", condition=None,
        fortified="the 6th lord fortified - he overcomes all his troubles and emerges "
                  "victor; no attempt by ill-wishers or enemies to harm him will succeed. "
                  "TODO(predicate: Shadbala strength of the 6th lord - no IsPowerful "
                  "Condition exists; the dignity proxy is tautological here)",
        general=None, afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 2989)),
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
        # H8.L.9 WAS HERE, and is gone deliberately (2026-09-02). It was the worst case in
        # the file: NOT ONE of this entry's sentences is gated on the 8th lord's strength,
        # yet both strength slots were populated and `general` was empty. A strong-8th-lord
        # chart with malefics on the 8th lord was shown the INHERITANCE reading; a weak one
        # with benefics on it was shown the DISINHERITANCE reading — backwards in both
        # directions. Raman states no unconditioned reading for this entry, so the base
        # record had nothing legitimate to say and now does not exist; every sentence lives
        # in H8.L.9a..e below, each with its own antecedent and its own citation. Nothing was
        # lost. (It was also listed in `test_general_reading_slot.LEFT_ALONE` as a rule that
        # "really does give an afflicted reading" — true of the TEXT, false of the SLOT.)
        id="H8.L.9a", house=8, signification="longevity", group="lord_in_house",
        kind="descriptive", condition=None,
        fortified=None, general=None,
        afflicted="the 8th lord joining the 9th lord in the 9th WITH MALEFICS - the native "
                  "may lose his father's property, and misunderstandings with the father may "
                  "arise. TODO(predicate: malefic other than the 8th/9th lords in that "
                  "house - ClassInHouseFrom has no subject-exclusion set, so the two lords "
                  "the rule is about would count themselves)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3011)),
    RuleRecord(
        id="H8.L.9b", house=8, signification="longevity", group="lord_in_house",
        kind="descriptive", condition=None,
        fortified=None,
        general="the 8th lord conjoined with BENEFICS in the 9th with the 9th lord - the "
                "native acquires his father's property, and relations with the father will "
                "be harmonious. TODO(predicate: benefic other than the 8th/9th lords - same "
                "subject-exclusion gap as H8.L.9a)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 3015)),
    RuleRecord(
        id="H8.L.9c", house=8, signification="longevity", group="lord_in_house",
        kind="descriptive", condition=None,
        fortified=None, general=None,
        afflicted="the Sun, natural significator of the father, afflicted - the father may "
                  "die during the period of the 9th lord. TODO(predicate: generalised "
                  "planet-affliction; also a dasha-timing claim, outside the atemporal "
                  "EvalContext)",
        frame="KARAKA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3013)),
    RuleRecord(
        id="H8.L.9d", house=8, signification="longevity", group="lord_in_house",
        kind="descriptive", condition=None,
        fortified=None, general=None,
        afflicted="the NINTH lord weak - the native suffers all kinds of hardships, misery "
                  "and unhappiness; friends and kinsmen may desert him while superiors find "
                  "fault with him. TODO(predicate: Shadbala weakness of the 9th lord - the "
                  "dignity proxy is provably TAUTOLOGICALLY FALSE here, the 9th lord being "
                  "in its own house and so its own sign by the entry's premise)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3017)),
    # The one clause of this entry the opened varga gate makes encodable today.
    RuleRecord(
        id="H8.L.9e", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(8, 9), C.LordsConjunct(8, 9),
                        C.InVargaHouseFrom("LORD_OF:8", "LAGNA", {6, 8, 12}, varga="D9")),
        fortified=None,
        general="the 8th lord in the 6th, 8th or 12th from Navamsa Lagna - the evil results "
                "will be greatly reduced",
        afflicted=None,
        frame="LAGNA", varga="D9", polarity="neutral", source=Citation("HTJAH-II", 3023)),
    RuleRecord(
        id="H8.L.10", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable", condition=C.And(C.LordIn(8, 10), C.LordsConjunct(8, 10)),
        # RE-SLOTTED 2026-09-02. `fortified` was ALSO mis-gated, which the first pass missed:
        # HTJAH-II:3038-3040 reads "The 8th lord in the 10th may ALSO confer unexpected
        # gains..." — restating the PLACEMENT as its antecedent, with no strength term. It is
        # unconditioned, so it was being withheld from every weak-lord chart for no doctrinal
        # reason. Merged into `general`.
        fortified=None,
        general="slow advancement in career, with obstacles and impediments; in the "
                "appropriate period he may be superseded by his subordinates and his merit "
                "go unnoticed; he may resort to deceit and unrighteous means, his thinking "
                "clouded and his actions inviting the wrath of the government or the law, "
                "and he may suffer poverty; it may also confer unexpected gains through the "
                "death of superiors or elders",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3027)),
    # HTJAH-II:3034-3036, re-homed. The old slot silently dropped HALF the antecedent: Raman
    # requires the 2nd lord to be afflicted AND to join the 8th lord. Even with an affliction
    # predicate, the encoded sentence was a strictly weaker claim than his.
    RuleRecord(
        id="H8.L.10a", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(8, 10), C.LordsConjunct(8, 10),
                        C.LordsConjunct(8, 2), C.AfflictedBy("LORD_OF:2")),
        fortified=None, general=None,
        afflicted="the 2nd lord ALSO AFFLICTED AND JOINING the 8th lord - his reputation may "
                  "suffer through involvement in huge debts and inability to repay them",
        # polarity NEUTRAL by design: a refinement of a parent that already votes for this
        # placement; it displays Raman's words without counting the placement twice.
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 3034)),
    RuleRecord(
        id="H8.L.10b", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(8, 10), C.LordsConjunct(8, 10),
                        C.InVargaHouseFrom("LORD_OF:8", "LAGNA", {6, 8, 12}, varga="D9")),
        fortified=None,
        general="the 8th lord in the 6th, 8th or 12th from Navamsa Lagna - the intensity of "
                "the evil is greatly reduced",
        afflicted=None,
        frame="LAGNA", varga="D9", polarity="neutral", source=Citation("HTJAH-II", 3036)),
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
        # RE-SLOTTED 2026-09-02. The Rajayoga (HTJAH-II:3053-3054) is the entry's
        # unconditioned base and was misfiled in `fortified`, leaving `general` empty. The old
        # `afflicted` welded together two DIFFERENT antecedents — "If benefics join" (a
        # conjunction) and "If afflicted by malefics" (an influence) — neither a strength test.
        fortified=None,
        general="a Rajayoga",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3053)),
    RuleRecord(
        id="H8.L.12a", house=8, signification="longevity", group="lord_in_house",
        kind="descriptive", condition=None,
        fortified=None, general=None,
        afflicted="BENEFICS JOINING the 8th lord - unfavourable results may be expected: "
                  "treachery of friends resulting in many problems and grief, unexpected "
                  "expenditure and pecuniary losses. TODO(predicate: benefic other than the "
                  "8th/12th lords joining - the ClassInHouseFrom subject-exclusion gap)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3055)),
    # HTJAH-II:3061-3065 is a SEPARATE COMBINATION, and Raman says so himself: he RE-OPENS
    # the antecedent as "If the 8th lord is in the 12th house", DROPPING "with the 12th lord".
    # That matters, because under the conjunction the 12th lord is in the 12th by
    # construction, and the 12th is neither trine nor quadrant — so as previously encoded the
    # clause was UNSATISFIABLE, a display promise that could never be met. Freed of the
    # conjunction it is live, and needs no new machinery. It is also one place where the
    # 2026-09-01 conjunction-narrowing of this file genuinely does not apply.
    RuleRecord(
        id="H8.L.12b", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(8, 12),
                        C.Or(C.InHouseClass("LORD_OF:12", "kendra"),
                             C.InHouseClass("LORD_OF:12", "trikona"))),
        fortified=None,
        general="the 8th lord in the 12th with the 12th lord favourably placed in a trine or "
                "quadrant - the native gains in religious learning and piety, and some post "
                "or seat of authority may be thrust upon him",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 3061)),
    RuleRecord(
        id="H8.L.12c", house=8, signification="longevity", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(8, 12), C.LordsConjunct(8, 12),
                        C.AfflictedBy("LORD_OF:8")),
        fortified=None, general=None,
        afflicted="the 8th lord AFFLICTED BY MALEFICS - the native may resort to vicious acts "
                  "clandestinely: rape, adultery, counterfeiting of money and smuggling "
                  "(Raman's own caution at HTJAH-II:3073-3074: criminal-act predictions "
                  "require further qualification)",
        # polarity NEUTRAL by design: a refinement of a parent that already votes for this
        # placement; it displays Raman's words without counting the placement twice.
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 3065)),
)
