"""Labha / Aya Bhava (gains / friends / elder-siblings) — Lord-in-12-houses RuleRecords.

Moved verbatim from the former flat ``house_11_labha.py`` (Stage-4 split)."""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    RuleRecord(
        id="H11.L.1", house=11, signification="gains", group="lord_in_house",
        # 2026-10-13 House-11 sweep (1/12 correct): 14259-14264 is a strong / middling /
        # weak ladder. Outer tiers in the strength slots (each carrying the unconditioned
        # sentences, since only one slot is shown); the middle tier -> H11.L.1a.
        kind="evaluable", condition=C.LordIn(11, 1),
        fortified="earns much wealth; loses an elder brother early in life; the 11th lord "
                  "in Lagna strong - born in a very rich family",
        general="born in a rich family; earns much wealth; loses an elder brother early in "
                "life",
        afflicted="earns much wealth; loses an elder brother early in life; the 11th lord "
                  "in Lagna weak - born in a well-to-do family",
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-II", 14258)),
    RuleRecord(
        id="H11.L.1a", house=11, signification="gains", group="lord_in_house",
        kind="descriptive",
        condition=None,
        general="the 11th lord in Lagna middling in strength - born in a fairly rich "
                "family. TODO(predicate: PARKED by research 2026-10-13 -- Raman prints no "
                "middle strength level (GBB-8:303 is one bar); his 'middling' is a tally of "
                "mixed testimony across Rasi and Navamsa, not a Shadbala band. Do NOT build "
                "a Shadbala band for it; see DOCTRINE_BACKLOG 'Middle and upper strength "
                "levels')",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 14259)),
    RuleRecord(
        id="H11.L.2", house=11, signification="gains", group="lord_in_house",
        # 2026-10-13 House-11 sweep (1/12 correct): 'Benefics there' / 'if malefics join'
        # (14268-14272) are occupancy tests -> H11.L.2a/b, conjunction only, never counting
        # the lord itself.
        kind="evaluable", condition=C.LordIn(11, 2),
        fortified="lives with his elder brothers; earns through commercial concerns and "
                  "banking business; business with friends brings good profits",
        afflicted=None,
        general="lives with his elder brothers; earns through commercial concerns and "
                "banking business; business with friends brings good profits",
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-II", 14267)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H11.L.2a", house=11, signification="gains", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(11, 2), C.JoinedBy("LORD_OF:11", C.FIRM_BENEFICS)),
        general="benefics with the 11th lord in the 2nd - harmonious relations",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 14268)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H11.L.2b", house=11, signification="gains", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(11, 2), C.JoinedBy("LORD_OF:11", C.NATURAL_MALEFICS)),
        general="malefics with the 11th lord in the 2nd - domestic bickerings but common "
                "residence; the native may suffer heavy losses on account of friends",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 14268)),
    RuleRecord(
        id="H11.L.3", house=11, signification="gains", group="lord_in_house",
        # 2026-10-13 House-11 sweep (1/12 correct): 'Afflictions give contrary results'
        # (14277) -> H11.L.3a.
        kind="evaluable", condition=C.LordIn(11, 3),
        fortified="a concert-singer or musician and earns thereby; gain through brothers; "
                  "many friends and helpful neighbours",
        afflicted=None,
        general="a concert-singer or musician and earns thereby; gain through brothers; "
                "many friends and helpful neighbours",
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-II", 14274)),
    # Raman does not say whose affliction; the entry's subject, the 11th lord, is tested.
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H11.L.3a", house=11, signification="gains", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(11, 3), C.AfflictedBy("LORD_OF:11")),
        general="the 11th lord in the 3rd afflicted - afflictions give contrary results",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 14277)),
    RuleRecord(
        id="H11.L.4", house=11, signification="gains", group="lord_in_house",
        # 2026-10-13 House-11 sweep (1/12 correct): wholly unconditioned; it was labelled a
        # strength reading.
        kind="evaluable", condition=C.LordIn(11, 4),
        fortified="profits through landed estates, rentals and products of the earth; the "
                  "mother a cultured and distinguished lady; renowned for learning and "
                  "scholarship of various subjects; lives in comfort and enjoys all joys in "
                  "life; a devoted and charming wife",
        afflicted=None,
        general="profits through landed estates, rentals and products of the earth; the "
                "mother a cultured and distinguished lady; renowned for learning and "
                "scholarship of various subjects; lives in comfort and enjoys all joys in "
                "life; a devoted and charming wife",
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-II", 14279)),
    RuleRecord(
        id="H11.L.5", house=11, signification="gains", group="lord_in_house",
        # 2026-10-13 House-11 sweep (1/12 correct): 'afflicted' (14288) and 'beneficially
        # disposed' (14289) are set against each other -> H11.L.5a/b.
        kind="evaluable", condition=C.LordIn(11, 5),
        fortified="many children who will come up well in life; indulges in speculation and "
                  "gains much money",
        afflicted=None,
        general="many children who will come up well in life; indulges in speculation and "
                "gains much money",
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-II", 14286)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H11.L.5a", house=11, signification="gains", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(11, 5), C.AfflictedBy("LORD_OF:11")),
        general="the 11th lord afflicted - a gambler, indulging in foolish ventures",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 14288)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H11.L.5b", house=11, signification="gains", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(11, 5), C.InfluencedBy("LORD_OF:11")),
        general="the 11th lord beneficially disposed - pious, observes many resolves and "
                "vows which enhance his prosperity",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 14289)),
    RuleRecord(
        id="H11.L.6", house=11, signification="gains", group="lord_in_house",
        # 2026-10-13 House-11 sweep (1/12 correct): two affliction clauses (14294, 14297)
        # with opposite-leaning outcomes -> H11.L.6a/b, kept as Raman wrote them, not
        # reconciled.
        kind="evaluable", condition=C.LordIn(11, 6),
        fortified="gains money through maternal relatives, litigation and running "
                  "nursing-homes",
        afflicted=None,
        general="gains money through maternal relatives, litigation and running "
                "nursing-homes",
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-II", 14293)),
    # Same predicate as H11.L.6b, opposite-leaning outcome, as Raman wrote them; not
    # reconciled. Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H11.L.6a", house=11, signification="gains", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(11, 6), C.AfflictedBy("LORD_OF:11")),
        general="the 11th lord afflicted in the 6th - thrives on setting person against "
                "person, involves himself in other people's quarrels and anti-social "
                "activity",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 14294)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H11.L.6b", house=11, signification="gains", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(11, 6), C.AfflictedBy("LORD_OF:11")),
        general="malefics afflicting the 11th lord - the native may lose through similar "
                "sources",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 14297)),
    RuleRecord(
        id="H11.L.7", house=11, signification="gains", group="lord_in_house",
        # 2026-10-13 House-11 sweep (1/12 correct): 'If there are afflictions to the 11th
        # lord' (14303) -> H11.L.7a. The fortified clause (14305) is genuinely strength-
        # gated and stays.
        kind="evaluable", condition=C.LordIn(11, 7),
        fortified="if fortified → marries only once, a rich and influential woman; "
                  "prospers in foreign countries",
        general="marries more than once; prospers in foreign countries",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-II", 14302)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H11.L.7a", house=11, signification="gains", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(11, 7), C.AfflictedBy("LORD_OF:11")),
        general="afflictions to the 11th lord - liaisons with women of ill-repute; trading "
                "in flesh and similar immoral activities",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 14303)),
    RuleRecord(
        id="H11.L.8", house=11, signification="gains", group="lord_in_house",
        # 2026-10-13 House-11 sweep (1/12 correct): 'a malefic constellation' (14311) is a
        # nakshatra placement, undefined in the entry -> H11.L.8a.
        kind="evaluable", condition=C.LordIn(11, 8),
        general="though rich at birth, suffers many calamities and loses much of his "
                "money; suffers from the depredations of thieves, cheats and swindlers",
        fortified="though rich at birth, suffers many calamities and loses much of his "
                  "money; suffers from the depredations of thieves, cheats and swindlers",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 14309)),
    RuleRecord(
        id="H11.L.8a", house=11, signification="gains", group="lord_in_house",
        kind="descriptive",
        condition=None,
        general="the 11th lord in the 8th occupying a malefic constellation - forced to eke "
                "out his living by begging. TODO(predicate: 'malefic constellation' is "
                "undefined in the entry - a malefic-ruled nakshatra, or the 3/5/7 taras of "
                "the Satyacharya note; not chosen)",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 14311)),
    RuleRecord(
        id="H11.L.9", house=11, signification="gains", group="lord_in_house",
        # 2026-10-13 House-11 sweep (1/12 correct): wholly unconditioned; 'disseminates
        # religious literature' restored.
        kind="evaluable", condition=C.LordIn(11, 9),
        fortified="inherits a large paternal fortune and is very lucky in life; many "
                  "houses, conveyances and every other kind of luxury; religious-minded and "
                  "disseminates religious literature; charitable, sets up charitable "
                  "institutions",
        afflicted=None,
        general="inherits a large paternal fortune and is very lucky in life; many houses, "
                "conveyances and every other kind of luxury; religious-minded and "
                "disseminates religious literature; charitable, sets up charitable "
                "institutions",
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-II", 14315)),
    RuleRecord(
        id="H11.L.10", house=11, signification="gains", group="lord_in_house",
        # 2026-10-13 House-11 sweep (1/12 correct): 'Depending upon the benefic or malefic
        # nature of the planet' (14327) is planet identity, expressible by sign ->
        # H11.L.10a/b.
        kind="evaluable", condition=C.LordIn(11, 10),
        fortified="prospers very well in his business and makes good profits; the elder "
                  "brother helps him in his business; earns some prize-money for original "
                  "contributions to the subject of his study or profession",
        afflicted=None,
        general="prospers very well in his business and makes good profits; the elder "
                "brother helps him in his business; earns some prize-money for original "
                "contributions to the subject of his study or profession",
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-II", 14322)),
    # With the lord in the 10th its sign fixes the Lagna and so the lord: Saturn, Mars or
    # the Sun in signs 4, 7, 9, 10, 12. Neutral: refines a parent that already votes for
    # this placement.
    RuleRecord(
        id="H11.L.10a", house=11, signification="gains", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(11, 10), C.Or(C.InSign("LORD_OF:11", 4), C.InSign("LORD_OF:11", 7), C.InSign("LORD_OF:11", 9), C.InSign("LORD_OF:11", 10), C.InSign("LORD_OF:11", 12))),
        general="the 11th lord in the 10th a malefic planet - earns through foul means",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 14327)),
    # Jupiter or Venus only (signs 1, 6, 8, 11); a Moon or Mercury lord (signs 2, 3, 5) does
    # not fire, since Raman counts them benefic only conditionally. Neutral: refines a
    # parent that already votes for this placement.
    RuleRecord(
        id="H11.L.10b", house=11, signification="gains", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(11, 10), C.Or(C.InSign("LORD_OF:11", 1), C.InSign("LORD_OF:11", 6), C.InSign("LORD_OF:11", 8), C.InSign("LORD_OF:11", 11))),
        general="the 11th lord in the 10th a benefic planet - earns through fair means",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 14327)),
    RuleRecord(
        id="H11.L.11", house=11, signification="gains", group="lord_in_house",
        # 2026-10-13 House-11 sweep (1/12 correct): wholly unconditioned; it was labelled a
        # strength reading.
        kind="evaluable", condition=C.LordIn(11, 11),
        fortified="many friends and elder brothers who help throughout life; "
                  "happy life with wife, home, children and all comforts",
        afflicted=None,
        general="many friends and elder brothers who may help him throughout life; a happy "
                "life with the blessings of wife, home, children and comforts",
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-II", 14330)),
    RuleRecord(
        id="H11.L.12", house=11, signification="gains", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(11, 12),
        general="losses in business; ailing elder brother and heavy expenditure on his "
                "illness, possibly death of elder brother; pays fines and penalties "
                "frequently; burdened with domestic responsibilities",
        fortified="losses in business; ailing elder brother and heavy expenditure on his "
                  "illness, possibly death of elder brother; pays fines and penalties "
                  "frequently; burdened with domestic responsibilities",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 14335)),
    # Section-level (Satyacharya, quoted by Raman), not a refinement of one placement. Taras
    # count cyclically, matching the HTJAH-I:1142 TaraOf precedent.
    RuleRecord(
        id="H11.L.S1", house=11, signification="gains", group="lord_in_house",
        kind="evaluable",
        condition=C.TaraOf("LORD_OF:11", {3, 5, 7}),
        general="the 11th lord in an evil constellation, the 3rd, 5th or 7th from that "
                "occupied by the Moon (Satyacharya) - the native suffers penury and misery",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 14346)),
    RuleRecord(
        id="H11.L.S2", house=11, signification="gains", group="lord_in_house",
        kind="descriptive",
        condition=None,
        general="benefics in the 11th house augment the significations of the Bhava while "
                "malefics diminish them both qualitatively and quantitatively. TODO(a "
                "magnitude modifier on the other readings, not a reading in itself)",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 14351)),

)
