"""Vyaya Bhava (loss / expenditure / moksha) — Planets-in-the-house RuleRecords.

Moved verbatim from the former flat ``house_12_vyaya.py`` (Stage-4 split)."""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    # — Planets in the 12th House (HTJAH-II:16601–16656) —
    RuleRecord(
        id="H12.P.Sun", house=12, signification="loss_moksha",
        group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Sun", 12),
        # HTJAH-II:16603-16607. "He will, HOWEVER, be energetic and have sons" is the
        # closing clause of Raman's unconditioned paragraph, joined by a contrastive — not a
        # condition — so it was a sentiment-split. The appended clause IS genuinely
        # affliction-conditioned, and it is the only such clause in the whole H10/H11/H12
        # planet set: "The native's wealth is spent on fines or will be confiscated by the
        # Government when the AFFLICTED Sun occupies the 12th" (HTJAH-II:16310-16311, ~290
        # lines before the cited spine).
        general="may take to an immoral life and engage himself in vile occupations; not "
                "quite successful in life, may feel neglected by all; suffers the loss of "
                "some limb and weak eyesight; will, however, be energetic and have sons",
        fortified="may take to an immoral life and engage himself in vile occupations; not "
                  "quite successful in life, may feel neglected by all; suffers the loss of "
                  "some limb and weak eyesight; will, however, be energetic and have sons",
        afflicted="the Sun afflicted in the 12th → wealth spent on fines or confiscated by "
                  "the Government (HTJAH-II:16310-16311)",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 16603)),
    RuleRecord(
        id="H12.P.Moon", house=12, signification="loss_moksha",
        group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Moon", 12),
        fortified=None,
        afflicted="some deformity; narrow-minded, hard-hearted, mischievous; obscure "
                  "life in solitude; weak eyesight; waning Moon + Saturn → sloth and "
                  "lethargy",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 16609)),
    RuleRecord(
        id="H12.P.Mars", house=12, signification="loss_moksha",
        group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Mars", 12),
        fortified=None,
        afflicted="may lose wife; selfish, hateful, heat-diseases; liable to deception "
                  "and money-loss; expensive litigation; Mars+Saturn in 12th and 2nd with "
                  "Moon in Lagna and Sun in 7th → leucoderma; Mars aspected by Sun → "
                  "danger from fire or wicked people; malefics in 7th and 8th + Mars in "
                  "12th → second wife while first alive; injures the right eye",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 16615)),
    RuleRecord(
        id="H12.P.Mercury", house=12, signification="loss_moksha",
        group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Mercury", 12),
        fortified=None,
        afflicted="capricious, wayward; extra-marital relations; penury; perverted "
                  "thinking → unhappiness; few children; reckless share and trade "
                  "investment; family litigation dwindles wealth",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 16625)),
    RuleRecord(
        id="H12.P.Jupiter", house=12, signification="loss_moksha",
        group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Jupiter", 12),
        # HTJAH-II:16629-16632 has no conditional, and the `fortified` clause is ALSO
        # unconditioned — "Jupiter in the 12th makes one honest and pay taxes and tolls
        # properly" (16370-16371). Raman gives two unconditioned and opposed readings for the
        # same placement in two passages; the encoder resolved the tension by valence-slotting
        # them, an interpretation Raman did not authorise. Both are now stated as his.
        general="may deride religion and be evil-minded; commits fearful deeds and leads a "
                "lascivious life; later on he repents and reforms himself; always anxious "
                "about his vehicles, ornaments and clothes; makes one honest and pay taxes "
                "and tolls properly (HTJAH-II:16370-16371)",
        fortified="may deride religion and be evil-minded; commits fearful deeds and leads a "
                  "lascivious life; later on he repents and reforms himself; always anxious "
                  "about his vehicles, ornaments and clothes; makes one honest and pay taxes "
                  "and tolls properly (HTJAH-II:16370-16371)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-II", 16629)),
    RuleRecord(
        id="H12.P.Venus", house=12, signification="loss_moksha",
        group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Venus", 12),
        # HTJAH-II:16634-16642. `fortified` holds a GENUINE dignity branch — "If Venus is
        # exalted, contrary results will happen" (16641-16642) — one of only two correct
        # fortified slots across the H10/H11/H12 planet tables; kept. ("(favourable)" is the
        # encoder's gloss on Raman's bare "contrary results"; retained as a reasonable read of
        # the uniformly negative paragraph it reverses.) Everything in `afflicted` is
        # unconditioned, INCLUDING the appended clause, which at 16316-16317 reads flatly
        # "Venus causes loss of money through women of ill-fame, scandals or black-mail" with
        # no affliction qualifier.
        general="desertion by relatives; hankering after comforts without success, and penury "
                "make his life miserable; indulges in lying and associates with low women; "
                "poor eyesight; causes loss of money through women of ill-fame, scandals or "
                "blackmail (HTJAH-II:16316-16317)",
        fortified="Venus exalted → contrary (favourable) results",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 16634)),
    RuleRecord(
        id="H12.P.Saturn", house=12, signification="loss_moksha",
        group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Saturn", 12),
        fortified=None,
        afflicted="dull-headed, loses all money; squint eyes, deformed limb; many "
                  "enemies, trade losses; pessimist; commits sins in secret; "
                  "Saturn+Rahu → heavy expenses on deaths and calamities; "
                  "Saturn+Mars → expenditure on co-borns",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 16644)),
    RuleRecord(
        id="H12.P.Rahu", house=12, signification="loss_moksha",
        group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Rahu", 12),
        # HTJAH-II:16649-16652. "The native will be prosperous, immoral, but of a helpful
        # nature" is ONE clause torn into three pieces across a comma — "prosperous" and
        # "helpful nature" to fortified, "immoral" to afflicted. The purest sentiment-split in
        # the H10/H11/H12 set. The father-dies-early clause is a CONFIGURATION (16650-16652).
        general="prosperous, immoral, but of a helpful nature; will have eye troubles",
        fortified="prosperous, immoral, but of a helpful nature; will have eye troubles",
        afflicted="(a configuration, not an affliction) the Sun in the 7th, Mars in the 10th "
                  "and Rahu in the 12th → the father dies early",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 16649)),
    RuleRecord(
        id="H12.P.Ketu", house=12, signification="loss_moksha",
        group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Ketu", 12),
        # ★ CROSS-FRAME TRANSFER REMOVED 2026-09-01. This slot read "Ketu in 12th from
        # karakamsa → Kaivalya / Final Emancipation". The sentence is Raman's, verbatim, at
        # HTJAH-II:16527 — but its frame is the KARAKAMSA (the Atmakaraka's navamsa sign),
        # while this record's condition is `InRashiHouse("Ketu", 12)` with `frame="LAGNA"`.
        # As encoded it promised Final Emancipation to every chart with Ketu in the 12th from
        # the ASCENDANT, a claim Raman makes nowhere. Not a fabrication — the words exist —
        # but a miscitation with a doctrinal consequence, and the same shape as the H10.L.1
        # defect: a real idiom generalised onto a placement it was never granted to. Re-home
        # it to a karakamsa-framed rule if it is wanted; do not restore it here.
        #
        # HTJAH-II:16654-16656 is three unconditioned sentences and carries no branch.
        general="restless and wandering mind; leaves his country of birth; the lower classes "
                "will befriend him; all his inherited property may be lost",
        fortified="restless and wandering mind; leaves his country of birth; the lower "
                  "classes will befriend him; all his inherited property may be lost",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 16654)),
)
