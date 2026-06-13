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
        fortified="energetic and has sons",
        afflicted="immoral life, vile occupations; not successful, feels neglected; "
                  "loss of some limb, weak eyesight; afflicted Sun → wealth spent on "
                  "fines or confiscated by Government",
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
        fortified="makes one honest, pays taxes and tolls properly",
        afflicted="derides religion, evil-minded; commits fearful deeds, lascivious "
                  "life; later repents and reforms; anxious about vehicles, ornaments "
                  "and clothes",
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-II", 16629)),
    RuleRecord(
        id="H12.P.Venus", house=12, signification="loss_moksha",
        group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Venus", 12),
        fortified="Venus exalted → contrary (favourable) results",
        afflicted="desertion by relatives; hankering after comforts without success; "
                  "penury, misery; lying with low women; poor eyesight; loss via women "
                  "of ill-fame, scandals and blackmail",
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
        fortified="prosperous, helpful nature",
        afflicted="immoral; eye-troubles; Sun in 7th + Mars in 10th + Rahu in 12th → "
                  "father dies early",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 16649)),
    RuleRecord(
        id="H12.P.Ketu", house=12, signification="loss_moksha",
        group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Ketu", 12),
        fortified="Ketu in 12th from karakamsa → Kaivalya / Final Emancipation",
        afflicted="restless, wandering mind; leaves country of birth; befriended by "
                  "lower classes; inherited property lost",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 16654)),
)
