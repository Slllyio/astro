"""Ari / Roga Bhava (enemies / disease / debts / accidents) — Lord-in-12-houses RuleRecords.

Moved verbatim from the former flat ``house_06_ari.py`` (Stage-4 split)."""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    RuleRecord(
        id="H6.L.1", house=6, signification="enemies_disease", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(6, 1),
        fortified="joins army as soldier or commander, or becomes Minister of War / prison official; "
                  "lives in maternal uncle's house",
        # Slot CORRECT (6001-6002 grades soldier-vs-Commander explicitly BY strength -- the
        # clearest strength statement in the section). But the branch tests only WEAK, while
        # Raman requires "weak AND otherwise afflicted", so the antecedent is stated inline.
        afflicted="the 6th lord weak and otherwise afflicted - becomes a robber, thief, or "
                  "leader of a criminal gang",
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 6001)),
    RuleRecord(
        id="H6.L.2", house=6, signification="enemies_disease", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(6, 2),
        # "Conjoined with or aspected by benefices" (6007) is a discrete EVENT that Shadbala
        # does not measure -- the H8.L.12 idiom, already ruled REVERSAL. A strong-6th-lord
        # chart with no benefic association was told it has defective vision and stammering.
        fortified=None,
        # Kept, with the half of the antecedent the encoding had dropped restored. The
        # Dasha/Bhukti timing is NOT a defect: the guard line allows timed indications in the
        # classical idiom, and the text names its own timing.
        afflicted="the 6th lord weak and otherwise ill-disposed in the 2nd - loss of wife in "
                  "the Dasha or Bhukti of the malefic lord",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6007)),
    RuleRecord(
        id="H6.L.3", house=6, signification="enemies_disease", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(6, 3),
        # Slot CORRECT (6013 "The sixth lord fortified confers..."). Restores "befriending
        # the native's brother", dropped by the old text -- it changes the MECHANISM: the
        # uncle acts THROUGH the brother.
        fortified="enmity with brothers; or the maternal uncle, befriending the native's "
                  "brother, works against the native's interests; or the native's brother "
                  "suffers frequent ill-health",
        afflicted="the 6th lord weak and afflicted - no younger brothers",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6013)),
    RuleRecord(
        id="H6.L.4", house=6, signification="enemies_disease", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(6, 4),
        fortified="lives in a dilapidated building; breaks in education; discards mother; "
                  "maternal uncles are land cultivators",
        # Slot CORRECT: "Well fortified, lives in a dilapidated building" (6018) is Raman's
        # own gating -- negative content in `fortified` is right in this house, because the
        # 6th signifies enemies and disease and a strong 6th lord strengthens them.
        afflicted="the 6th lord weak and afflicted - quarrels with mother; ancestral property "
                  "in debts; works as a menial, miserable life; troublesome home and domestic "
                  "affairs and trouble through servants",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6018)),
    RuleRecord(
        id="H6.L.5", house=6, signification="enemies_disease", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(6, 5),
        # HTJAH-I:6024-6025 has ZERO antecedent anywhere -- two flat declaratives. Wrong not
        # because the content is negative (see H6.L.4) but because Raman attaches no condition
        # to it. A chart the engine has just measured WEAK was shown this under a FORTIFIED
        # heading, asserting a strength the chart cannot establish.
        fortified=None,
        general="sickly children; the native is adopted by his maternal uncle and becomes "
                "fortunate",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6024)),
    RuleRecord(
        id="H6.L.6", house=6, signification="enemies_disease", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(6, 6),
        fortified=None,
        general="increase of cousins; the maternal uncle becomes famed",
        # The clause named TWO conditions, neither of them the 6th lord's strength: a
        # conjunction, and the LAGNA lord's weakness. As encoded, "incurable disease" was
        # asserted on any weak-6th-lord chart with no Lagna lord involved at all.
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 6027)),
    RuleRecord(
        id="H6.L.7", house=6, signification="enemies_disease", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(6, 7),
        # ALL THREE `fortified` sentences are unconditioned -- Raman flags the first
        # "Generally" himself (6031) -- and all three `afflicted` sentences are gated on
        # something the strength branch cannot test. Zero correctly-slotted content.
        # Restores "brother's", dropped from Raman's three-way cousin list, and the sentence
        # at 6037 that was never encoded at all.
        fortified=None,
        general="generally marries the mother's, brother's or father's sister's daughter; the "
                "maternal uncle lives in a far-off place or foreign country; the wife's "
                "character will be doubtful; there will also be troubles with disrespectable "
                "women",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6031)),
    RuleRecord(
        id="H6.L.8", house=6, signification="enemies_disease", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(6, 8),
        fortified="Madhyayu (middle life)",
        afflicted="plenty of debts; loathsome diseases; chases other women; takes pleasure in "
                  "inflicting pain",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6039)),
    RuleRecord(
        id="H6.L.9", house=6, signification="enemies_disease", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(6, 9),
        # The fortified condition is POSTPOSED ("Father becomes a judge, if the sixth lord is
        # well fortified", 6045) and closes its own sentence, so unlike H6.L.4's fronted
        # "Well fortified," it does not govern the three sentences that follow.
        fortified="father becomes a judge",
        general="the maternal uncle becomes highly fortunate; there will be misunderstandings "
                "between the native and his father; benefits from Gnatis or cousins",
        # The "(moderate)" tier is split off below. Welded here it produced the H5.L.4
        # contradiction: one reader told he is destitute and sinful AND a working tradesman.
        # "and engaged in unrighteous deeds" (6048) restored.
        afflicted="poverty, sinful acts, misfortunes through relatives, ungrateful towards "
                  "preceptors, engaged in unrighteous deeds",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6045)),
    RuleRecord(
        id="H6.L.10", house=6, signification="enemies_disease", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(6, 10),
        fortified="sinful and destructive nature; poses as orthodox/pious but really unscrupulous "
                  "in religion",
        afflicted="(lord weak) dismissal; formidable enemies; low life or begging",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6051)),
    RuleRecord(
        id="H6.L.11", house=6, signification="enemies_disease", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(6, 11),
        # The outer arms are CONTESTED, not reversed, and are kept. "If benefice / If malefic"
        # most naturally means benefic/malefic ASSOCIATION -- Raman glosses that vocabulary
        # nine lines later, "the modifications due to benefice and malefic associations,
        # aspects" (6064) -- which is not a Shadbala test. But Drik Bala IS benefic/malefic
        # aspect strength and is folded into the Shadbala total, so the association axis sits
        # partially (and non-isolably) inside `is_powerful`. That is a genuine partial defence
        # of these two arms; it does not extend to conjunction, which Drik Bala does not
        # measure. The MIDDLE tier is certainly wrong and is split off below.
        fortified="the 6th lord with benefic association - the eldest brother will be a judge",
        afflicted="the 6th lord with malefic association - poor and wretched life; suffering "
                  "on account of convictions",
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 6055)),
    RuleRecord(
        id="H6.L.12", house=6, signification="enemies_disease", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(6, 12),
        fortified="difficulty and sorrow through destructive nature; causes harm to others",
        afflicted="miserable, hard and wretched existence",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6059)),

    # ---- clauses re-homed out of strength slots by the 2026-09-03 House-6 sweep ----------
    RuleRecord(
        id="H6.L.2a", house=6, signification="enemies_disease", group="lord_in_house",
        # 2026-10-13: polarity set neutral -- a refinement of a parent that already votes
        # for this placement (it predated the neutral rule; promoting siblings to live rules
        # exposed it).
        kind="descriptive", condition=None,
        fortified="the 6th lord CONJOINED WITH or ASPECTED BY benefics - untold suffering in "
                  "family life and deep sorrows, loss of money through enemies, defective "
                  "vision, uneven teeth and stammering. TODO(predicate: there is no "
                  "benefic-class analogue to AfflictedBy in conditions.py)",
        general=None, afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 6007)),
    RuleRecord(
        id="H6.L.2b", house=6, signification="enemies_disease", group="lord_in_house",
        # 2026-10-13: polarity set neutral -- a refinement of a parent that already votes
        # for this placement (it predated the neutral rule; promoting siblings to live rules
        # exposed it).
        # 2026-10-13: promoted from descriptive once IsStrong/IsWeak existed (effective
        # strength: Shadbala bar plus combustion/debility overrides). Neutral: refines a
        # parent placement.
        kind="evaluable", condition=C.And(C.LordIn(6, 2), C.IsWeak("Venus")),
        fortified=None, general="Venus weak - the native will be a celibate and poverty "
                                "stricken, just able to get a morsel of food when hungry",
        afflicted=None,
        frame="KARAKA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 6010)),
    RuleRecord(
        id="H6.L.6a", house=6, signification="enemies_disease", group="lord_in_house",
        # 2026-10-13: polarity set neutral -- a refinement of a parent that already votes
        # for this placement (it predated the neutral rule; promoting siblings to live rules
        # exposed it).
        # 2026-10-13: promoted from descriptive once IsStrong/IsWeak existed (effective
        # strength: Shadbala bar plus combustion/debility overrides). Neutral: refines a
        # parent placement.
        kind="evaluable", condition=C.And(C.LordIn(6, 6), C.LordsConjunct(6, 1), C.IsWeak("LORD_OF:1")),
        fortified=None, general="the 6th lord in conjunction with a weak Lagna lord - an "
                                "incurable disease, and increase of enmity with kith and "
                                "kin",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 6027)),
    RuleRecord(
        id="H6.L.7a", house=6, signification="enemies_disease", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(6, 7), C.AfflictedBy("LORD_OF:6")),
        fortified=None, general=None,
        afflicted="the 6th lord afflicted - he will either divorce his wife early in life or "
                  "she will die",
        # polarity NEUTRAL by design: a refinement of a parent that already votes for this
        # placement; it displays Raman's words without counting the placement twice.
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 6033)),
    RuleRecord(
        id="H6.L.7b", house=6, signification="enemies_disease", group="lord_in_house",
        # 2026-10-13: polarity set neutral -- a refinement of a parent that already votes
        # for this placement (it predated the neutral rule; promoting siblings to live rules
        # exposed it).
        kind="descriptive", condition=None,
        fortified=None, general=None,
        afflicted="the Rashi AND Navamsha involved both hermaphrodite - a sickly or barren "
                  "wife. TODO(predicate: a hermaphrodite sign-class test across D1 and D9; the "
                  "varga half is expressible via VargaDignity/varga_sign_by_name, the sign "
                  "class is not yet a Condition)",
        frame="LAGNA", varga="D9", polarity="neutral", source=Citation("HTJAH-I", 6034)),
    RuleRecord(
        id="H6.L.7c", house=6, signification="enemies_disease", group="lord_in_house",
        # 2026-10-13: polarity set neutral -- a refinement of a parent that already votes
        # for this placement (it predated the neutral rule; promoting siblings to live rules
        # exposed it).
        kind="descriptive", condition=None,
        fortified=None, general=None,
        afflicted="the LAGNA LORD joining the 6th lord IN THE 7th, which is a hermaphrodite "
                  "sign - the native will be a eunuch and unable to perform the sexual act. "
                  "TODO(predicate: a THREE-part antecedent. The old encoding reduced it to "
                  "'the 6th lord is weak' and asserted this on one-sixth of Raman's stated "
                  "evidence)",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 6035)),
    RuleRecord(
        id="H6.L.9a", house=6, signification="enemies_disease", group="lord_in_house",
        kind="descriptive", condition=None,
        fortified=None,
        general="the 6th lord MODERATE - becomes a mason, timber merchant or stone cutter. "
                "TODO(predicate: the MIDDLE band of the strength continuum; is_powerful is "
                "binary against GBB-8:303 and cannot express it)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 6048)),
    RuleRecord(
        id="H6.L.11a", house=6, signification="enemies_disease", group="lord_in_house",
        kind="descriptive", condition=None,
        fortified=None,
        general="the 6th lord ORDINARY - an elder brother becomes a judge for some time but "
                "loses his job. TODO(predicate: the middle tier of Raman's benefic / ordinary "
                "/ malefic ASSOCIATION continuum, glossed by him at HTJAH-I:6064)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 6055)),
)
