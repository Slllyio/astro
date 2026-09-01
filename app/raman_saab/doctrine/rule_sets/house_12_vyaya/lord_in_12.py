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
        general="financial losses, debts, nefarious activity, untimely meals, poor "
                "eyesight, disharmonious family",
        afflicted="the 12th lord ill-disposed → gossip and quarrelling",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 16138)),
    RuleRecord(
        id="H12.L.3", house=12, signification="loss_moksha",
        group="lord_in_house", kind="evaluable",
        condition=C.LordIn(12, 3),
        fortified=None,
        general="timid and quiet; loss of a brother is shown; shabbily dressed; may have "
                "to spend much money on younger brothers; unsuccessful as a writer; may work "
                "in some commonplace job and earn very little",
        afflicted="malefics afflicting → ear-ailments; and (a configuration, not an "
                  "affliction) the 12th lord joining the 2nd lord in the 3rd aspected by "
                  "Jupiter or the 9th lord → more than one wife",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 16152)),
    RuleRecord(
        id="H12.L.4", house=12, signification="loss_moksha",
        group="lord_in_house", kind="evaluable",
        condition=C.LordIn(12, 4),
        fortified="if 12th lord well-placed → adverse indications largely mitigated; "
                  "if Venus strong → may own a (troublesome) conveyance",
        general="early death of mother, mental restlessness, worry, enmity of relatives, "
                "living abroad, landlord harassment, ordinary residence",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 16161)),
    RuleRecord(
        id="H12.L.5", house=12, signification="loss_moksha",
        group="lord_in_house", kind="evaluable",
        condition=C.LordIn(12, 5),
        general="either difficulty to beget progeny or unhappiness from children; "
                "religious-minded and may undertake pilgrimages; weak-minded and suffering "
                "mental aberrations, he feels he is miserable; does not succeed in "
                "agriculture, his crops suffering from pests and disease",
        fortified="either difficulty to beget progeny or unhappiness from children; "
                  "religious-minded and may undertake pilgrimages; weak-minded and suffering "
                  "mental aberrations, he feels he is miserable; does not succeed in "
                  "agriculture, his crops suffering from pests and disease",
        afflicted=None,
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
        general="the wife may come from a poor family; married life unhappy and may end "
                "in separation; later takes to asceticism; weak in health and suffering "
                "phlegmatic troubles, without learning or property",
        fortified="the wife may come from a poor family; married life unhappy and may end "
                  "in separation; later takes to asceticism; weak in health and suffering "
                  "phlegmatic troubles, without learning or property",
        afflicted=None,
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
        general="residence abroad and prosperity, and may acquire much property in "
                "foreign lands; honest, generous and large-hearted, he may not have any "
                "spiritual leanings; not liking his wife, friends and preceptor, and "
                "interested in physical culture, he loses his father early in life",
        fortified="residence abroad and prosperity, and may acquire much property in "
                  "foreign lands; honest, generous and large-hearted, he may not have any "
                  "spiritual leanings; not liking his wife, friends and preceptor, and "
                  "interested in physical culture, he loses his father early in life",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-II", 16201)),
    RuleRecord(
        id="H12.L.10", house=12, signification="loss_moksha",
        group="lord_in_house", kind="evaluable",
        condition=C.LordIn(12, 10),
        general="hard-working and undertaking tedious journeys for his occupation, he "
                "will be a jailor, doctor, or work in the cemetery and such places; spends "
                "money on agricultural pursuits, in which he makes profits; derives no "
                "happiness or physical comfort from his sons",
        fortified="hard-working and undertaking tedious journeys for his occupation, he "
                  "will be a jailor, doctor, or work in the cemetery and such places; spends "
                  "money on agricultural pursuits, in which he makes profits; derives no "
                  "happiness or physical comfort from his sons",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 16207)),
    RuleRecord(
        id="H12.L.11", house=12, signification="loss_moksha",
        group="lord_in_house", kind="evaluable",
        condition=C.LordIn(12, 11),
        general="engages in business but does not make much profit; few friends but many "
                "enemies; troubled by extravagant brothers, some of whom may be invalids, "
                "his funds may dwindle on that account; earns well by trading in pearls, "
                "rubies and other precious stones",
        fortified="engages in business but does not make much profit; few friends but many "
                  "enemies; troubled by extravagant brothers, some of whom may be invalids, "
                  "his funds may dwindle on that account; earns well by trading in pearls, "
                  "rubies and other precious stones",
        afflicted=None,
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
