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
        # 2026-10-13 House-12 sweep (5/12 correct): nothing in this entry depends on the
        # 12th lord's strength: a sign test (16131), the 6th-lord combination (16132), an
        # 8th-HOUSE affliction (16133) and an exchange (16135) -> H12.L.1a-d.
        group="lord_in_house", kind="evaluable",
        condition=C.LordIn(12, 1),
        # HTJAH-II:16129-16136, completed 2026-09-01. Raman's opening is one 'however' pair
        # - 'The native will have a weak constitution and will be feeble-minded. He will,
        # HOWEVER, be handsome and sweet-tongued.' - which had been split across both slots.
        # Reunited. Restores 'If the sign is common, the native will generally be travelling
        # about' (16131), dropped entirely by the old encoding.
        #
        # Only the 8th-house clause is genuinely affliction-conditioned. The 6th-lord and
        # exchange clauses are CONFIGURATIONS and are labelled as such. 'This also indicates
        # imprisonment and living abroad' (16134) stays where the encoder put it and is
        # marked UNDETERMINED: the referent of 'This' is ambiguous between the preceding
        # 8th-house-afflicted clause and the placement generally, and the text will not
        # settle it.
        general="a weak constitution and feeble-minded; he will, however, be handsome and "
                "sweet-tongued",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 16129)),
    # With the lord in Lagna, 'the sign' is the lord's own sign. Neutral: refines a parent
    # that already votes for this placement.
    RuleRecord(
        id="H12.L.1a", house=12, signification="loss_moksha", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(12, 1), C.Or(C.InSign("LORD_OF:12", 3), C.InSign("LORD_OF:12", 6), C.InSign("LORD_OF:12", 9), C.InSign("LORD_OF:12", 12))),
        general="the sign being common - the native will generally be travelling about",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 16131)),
    # H12.L.1c (8th house afflicted -> short-lived) overrides this, but cannot yet be
    # tested; until a house-affliction predicate exists 1b fires either way. Neutral:
    # refines a parent that already votes for this placement.
    RuleRecord(
        id="H12.L.1b", house=12, signification="loss_moksha", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(12, 1), C.LordIn(6, 1)),
        general="the 6th lord joining the 12th lord in Lagna - the native will live long",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 16132)),
    RuleRecord(
        id="H12.L.1c", house=12, signification="loss_moksha", group="lord_in_house",
        # 2026-10-13: promoted from descriptive once HouseAfflictedBy existed (a natural
        # malefic occupies or aspects the house; its own lord excluded). Neutral: refines a
        # parent placement.
        kind="evaluable",
        condition=C.And(C.LordIn(12, 1), C.LordIn(6, 1), C.HouseAfflictedBy(8)),
        general="the 6th lord joining the 12th lord in Lagna but the 8th house afflicted - "
                "he will be short-lived; this also indicates imprisonment and living abroad "
                "[referent of 'This' ambiguous]",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 16133)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H12.L.1d", house=12, signification="loss_moksha", group="lord_in_house",
        kind="evaluable",
        condition=C.Parivartana(1, 12),
        general="the Lagna and 12th lords exchanging signs - the native will be a miser, "
                "hated by all and devoid of intelligence",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 16135)),
    RuleRecord(
        id="H12.L.2", house=12, signification="loss_moksha",
        # 2026-10-13 House-12 sweep (5/12 correct): 'a benefic and in dignity' (16146) is
        # planet identity plus dignity, which strength does not imply -> H12.L.2a. 'If ill-
        # disposed' (16149) stays in the weak slot: Raman treats weakness as one form of
        # ill-disposition (HTJAH-I:6009 'weak and otherwise ill-disposed') -- MEDIUM
        # confidence.
        group="lord_in_house", kind="evaluable",
        condition=C.LordIn(12, 2),
        fortified=None,
        general="financial losses, debts, nefarious activity, untimely meals, poor "
                "eyesight, disharmonious family",
        afflicted="the 12th lord ill-disposed → gossip and quarrelling",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 16138)),
    RuleRecord(
        id="H12.L.2a", house=12, signification="loss_moksha", group="lord_in_house",
        kind="descriptive",
        condition=None,
        general="the twelfth lord a benefic and in dignity - these evil indications will be "
                "greatly reduced and the native will have financial stability; he will be a "
                "tactful speaker. TODO(predicate: by enumeration, a Jupiter/Venus 12th lord "
                "in the 2nd can never be in exaltation, own sign or moolatrikona; it fires "
                "only if friendly signs count AND the Moon or Mercury count as benefics - "
                "both conditional in Raman, so parked)",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 16146)),
    RuleRecord(
        id="H12.L.3", house=12, signification="loss_moksha",
        # 2026-10-13 House-12 sweep (5/12 correct): 'If malefics afflict' (16153) and the
        # 2nd-lord combination (16157) -> H12.L.3a/b.
        group="lord_in_house", kind="evaluable",
        condition=C.LordIn(12, 3),
        fortified=None,
        general="timid and quiet; loss of a brother is shown; shabbily dressed; may have "
                "to spend much money on younger brothers; unsuccessful as a writer; may work "
                "in some commonplace job and earn very little",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 16152)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H12.L.3a", house=12, signification="loss_moksha", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(12, 3), C.AfflictedBy("LORD_OF:12")),
        general="malefics afflicting - he may develop ear-ailments",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 16153)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H12.L.3b", house=12, signification="loss_moksha", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(12, 3), C.LordIn(2, 3), C.Or(C.Aspects("Jupiter", "LORD_OF:12"), C.Aspects("LORD_OF:9", "LORD_OF:12"))),
        general="the 12th lord joining the 2nd lord in the 3rd and aspected by Jupiter or "
                "the 9th lord - one may have more than one wife",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 16157)),
    RuleRecord(
        id="H12.L.4", house=12, signification="loss_moksha",
        # 2026-10-28 rule-defect review (docs/raman_saab/research/rule_defects_review2_2026-10-28.json): descriptive.
        # 2026-10-13 House-12 sweep (5/12 correct): 'well placed' (16164) is strength and
        # stays; the Venus clause (16166) is another planet's strength -> H12.L.4a.
        group="lord_in_house", kind="descriptive",
        condition=C.LordIn(12, 4),
        fortified="the twelfth lord well placed - these adverse indications get mitigated "
                  "to a large extent",
        general="early death of mother, mental restlessness, worry, enmity of relatives, "
                "living abroad, landlord harassment, ordinary residence",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 16161)),
    RuleRecord(
        id="H12.L.4a", house=12, signification="loss_moksha", group="lord_in_house",
        # 2026-10-13: promoted from descriptive once IsStrong/IsWeak existed (effective
        # strength: Shadbala bar plus combustion/debility overrides). Neutral: refines a
        # parent placement.
        kind="evaluable",
        condition=C.And(C.LordIn(12, 4), C.IsStrong("Venus")),
        general="Venus strong - the native may own his own conveyance but it will always "
                "give trouble",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 16166)),
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
        # 2026-10-13 House-12 sweep (5/12 correct): the unconditioned reading was only in
        # fortified, so weak-lord charts saw the affliction reading instead. 'If malefics
        # afflict' (16184) -> H12.L.6a. Dropped words restored.
        group="lord_in_house", kind="evaluable",
        condition=C.LordIn(12, 6),
        fortified="happy, prosperous, long-lived, healthy handsome physique, vanquishes enemies; "
                  "litigation ends to his advantage",
        afflicted=None,
        general="the native will be happy and prosperous, live long, enjoy many comforts, "
                "possess a healthy and handsome physique and vanquish his enemies; he may "
                "become involved in litigation which may come to an end to his advantage",
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-II", 16176)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H12.L.6a", house=12, signification="loss_moksha", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(12, 6), C.AfflictedBy("LORD_OF:12")),
        general="malefics afflicting the 12th lord - unscrupulous, sinful and ill-tempered, "
                "hating his mother, unhappy on account of his own children; womanising will "
                "land him in distress",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 16184)),
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
        # 2026-10-13 House-12 sweep (5/12 correct): wholly unconditioned and labelled a
        # strength reading; dropped words restored.
        group="lord_in_house", kind="evaluable",
        condition=C.LordIn(12, 8),
        fortified="rich and celebrated, luxurious life, many servants; gain through deaths "
                  "and legacy; occult interest, devoted to Vishnu, righteous, famous, good qualities",
        afflicted=None,
        general="the native will be rich and celebrated, will enjoy a luxurious life with "
                "many servants waiting on him; gain through deaths and legacy; interested "
                "in occult subjects and devoted to Lord Vishnu, he will be righteous, "
                "famous and a gentle speaker, endowed with many good qualities of head and "
                "heart",
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
        # 2026-10-13 House-12 sweep (5/12 correct): 'If malefics afflict' (16227) and the
        # closing 'If the twelfth lord is a benefic' (16231) -> H12.L.12a/b.
        group="lord_in_house", kind="evaluable",
        condition=C.LordIn(12, 12),
        fortified="the native spends much on religious and righteous purposes; he will have "
                  "good eyesight and enjoy pleasures of the couch; he will be engaged in "
                  "agriculture",
        afflicted=None,
        general="the native spends much on religious and righteous purposes; he will have "
                "good eyesight and enjoy pleasures of the couch; he will be engaged in "
                "agriculture",
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-II", 16224)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H12.L.12a", house=12, signification="loss_moksha", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(12, 12), C.AfflictedBy("LORD_OF:12")),
        general="malefics afflicting the twelfth lord - restless and always roaming about",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 16227)),
    # Jupiter or Venus in its own sign in the 12th (signs 2, 7, 9, 12); a Moon or Mercury
    # lord does not fire, as they are benefic only conditionally. Neutral: refines a parent
    # that already votes for this placement.
    RuleRecord(
        id="H12.L.12b", house=12, signification="loss_moksha", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(12, 12), C.Or(C.InSign("LORD_OF:12", 2), C.InSign("LORD_OF:12", 7), C.InSign("LORD_OF:12", 9), C.InSign("LORD_OF:12", 12))),
        general="the twelfth lord a benefic occupying the twelfth house - generally "
                "favourable results",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 16231)),
    # Section-level: its subject is the LAGNA lord, dropped corpus-wide until now; parked
    # here beside the text it closes, and may move to House 1.
    RuleRecord(
        id="H12.L.S1", house=12, signification="loss_moksha", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(1, 12), C.Not(C.ClassInHouseFrom("benefic", "LAGNA", {1, 4, 5, 7, 9, 10}))),
        general="the Lagna lord in the 12th and the trines or quadrants not occupied by "
                "benefics - a man of mediocre or poor means leading a monotonous life",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 16240)),

)
