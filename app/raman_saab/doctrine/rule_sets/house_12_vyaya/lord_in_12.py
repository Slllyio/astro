"""Vyaya Bhava (loss / expenditure / moksha) — Lord-in-12-houses RuleRecords.

Moved verbatim from the former flat ``house_12_vyaya.py`` (Stage-4 split)."""
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

)
