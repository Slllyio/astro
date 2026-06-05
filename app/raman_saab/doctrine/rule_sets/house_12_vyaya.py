"""House 12 (Vyaya — loss/expenditure/moksha) RuleRecords.

Lord of the 12th in the 12 houses, encoded from B.V. Raman,
*How to Judge a Horoscope* Vol II, "Concerning the Twelfth House".
Signification: loss, expenditure, foreign residence, imprisonment, sayana-sukha,
moksha / Final Emancipation.  Karaka: Saturn (loss/sorrow/after-life/renunciation);
Ketu (kaivalya/moksha, from karakamsa).

Source span: HTJAH-II:16129–16243 (lord-in-house table).
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    RuleRecord(
        id="H12.L.1", house=12, signification="loss_moksha",
        group="lord_in_house", kind="evaluable",
        condition=C.LordIn(12, 1),
        fortified="handsome, sweet-tongued; if 6th lord joins 12th lord in Lagna → long life",
        afflicted="weak constitution, feeble-minded; imprisonment and living abroad; "
                  "if 8th afflicted → short-lived; Lagna↔12th lord exchange → miser, "
                  "hated, devoid of intelligence",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 16129)),
    RuleRecord(
        id="H12.L.2", house=12, signification="loss_moksha",
        group="lord_in_house", kind="evaluable",
        condition=C.LordIn(12, 2),
        fortified="if 12th lord benefic and dignified → evils greatly reduced, "
                  "financial stability, tactful speaker",
        afflicted="financial losses, debts, nefarious activity, untimely meals, "
                  "poor eyesight, disharmonious family; if ill-disposed → gossip and quarrelling",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 16138)),
    RuleRecord(
        id="H12.L.3", house=12, signification="loss_moksha",
        group="lord_in_house", kind="evaluable",
        condition=C.LordIn(12, 3),
        fortified=None,
        afflicted="timid, quiet, loss of a brother, shabby dress; malefic affliction → "
                  "ear-ailments; spends much on younger brothers; unsuccessful writer; "
                  "commonplace job, low earnings; joins 2nd lord aspected by Jupiter/9th lord "
                  "→ more than one wife (mitigated)",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 16152)),
    RuleRecord(
        id="H12.L.4", house=12, signification="loss_moksha",
        group="lord_in_house", kind="evaluable",
        condition=C.LordIn(12, 4),
        fortified="if 12th lord well-placed → adverse indications largely mitigated; "
                  "if Venus strong → may own a (troublesome) conveyance",
        afflicted="early death of mother, mental restlessness, worry, enmity of relatives, "
                  "living abroad, landlord harassment, ordinary residence",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 16161)),
    RuleRecord(
        id="H12.L.5", house=12, signification="loss_moksha",
        group="lord_in_house", kind="evaluable",
        condition=C.LordIn(12, 5),
        fortified="religious-minded, may undertake pilgrimages",
        afflicted="difficulty and unhappiness re progeny, weak-minded, mental aberrations, "
                  "feels miserable, fails in agriculture (pests/disease)",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 16169)),
    RuleRecord(
        id="H12.L.6", house=12, signification="loss_moksha",
        group="lord_in_house", kind="evaluable",
        condition=C.LordIn(12, 6),
        fortified="happy, prosperous, long-lived, healthy handsome physique, vanquishes enemies; "
                  "litigation ends to his advantage",
        afflicted="if malefics afflict 12th lord → unscrupulous, sinful, ill-tempered, "
                  "hates mother, unhappy via children; womanising brings distress",
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-II", 16176)),
    RuleRecord(
        id="H12.L.7", house=12, signification="loss_moksha",
        group="lord_in_house", kind="evaluable",
        condition=C.LordIn(12, 7),
        fortified=None,
        afflicted="wife from poor family, unhappy marriage may end in separation; "
                  "weak health, phlegmatic troubles, without learning or property; "
                  "later takes to asceticism",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 16189)),
    RuleRecord(
        id="H12.L.8", house=12, signification="loss_moksha",
        group="lord_in_house", kind="evaluable",
        condition=C.LordIn(12, 8),
        fortified="rich and celebrated, luxurious life, many servants; gain through deaths "
                  "and legacy; occult interest, devoted to Vishnu, righteous, famous, good qualities",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-II", 16194)),
    RuleRecord(
        id="H12.L.9", house=12, signification="loss_moksha",
        group="lord_in_house", kind="evaluable",
        condition=C.LordIn(12, 9),
        fortified="residence abroad and prosperity, acquires foreign property; "
                  "honest, generous, large-hearted",
        afflicted="may lack spiritual leanings; dislikes wife, friends and preceptor; "
                  "loses father early",
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-II", 16201)),
    RuleRecord(
        id="H12.L.10", house=12, signification="loss_moksha",
        group="lord_in_house", kind="evaluable",
        condition=C.LordIn(12, 10),
        fortified="spends on agriculture and makes profit",
        afflicted="hard-working, tedious journeys; jailor/doctor/works in cemetery; "
                  "no happiness or comfort from sons",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 16207)),
    RuleRecord(
        id="H12.L.11", house=12, signification="loss_moksha",
        group="lord_in_house", kind="evaluable",
        condition=C.LordIn(12, 11),
        fortified="earns well trading in pearls, rubies and precious stones",
        afflicted="business but little profit; few friends, many enemies; "
                  "troubled by extravagant or invalid brothers; funds dwindle",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 16214)),
    RuleRecord(
        id="H12.L.12", house=12, signification="loss_moksha",
        group="lord_in_house", kind="evaluable",
        condition=C.LordIn(12, 12),
        fortified="spends much on religious and righteous purposes, good eyesight, "
                  "enjoys couch-pleasures, engaged in agriculture; benefic 12th lord → "
                  "generally favourable",
        afflicted="if malefics afflict 12th lord → restless, always roaming about",
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-II", 16224)),

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
