"""Bhagya / Dharma / Pitru Bhava (father / fortune / dharma / travel) — Lord-in-12-houses RuleRecords.

Moved verbatim from the former flat ``house_09_bhagya.py`` (Stage-4 split)."""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    # — 9th lord in the 12 houses (HTJAH-II:7301-7394) —
    RuleRecord(
        id="H9.L.1", house=9, signification="fortune", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-9 sweep (1/12 correct): 7301-7303 is unconditioned. The
        # conjunction-with-benefic clause (7303) sat in fortified with no general, so it
        # showed on EVERY chart -> H9.L.1a.
        condition=C.LordIn(9, 1),
        fortified=None,
        afflicted=None,
        general="the native becomes a self-made man; he earns much money through his own "
                "efforts",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7301)),
    # If the Lagna lord is itself Jupiter or Venus, the conjunction alone satisfies the
    # benefic contact; Raman seems to mean an additional benefic. Neutral: refines a parent
    # that already votes for this placement.
    RuleRecord(
        id="H9.L.1a", house=9, signification="fortune", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(9, 1), C.LordsConjunct(9, 1), C.InfluencedBy("LORD_OF:9")),
        general="the 9th lord combining with the Lagna lord in the 1st and associating with "
                "or aspected by a benefic planet - the native is fortunate with riches and "
                "happiness",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7303)),
    # H9.L.2 REMOVED: 2026-10-13 House-9 sweep. Raman gives NO unconditioned sentence for
    # the 9th lord in the 2nd: 7310-7312 is gated on 'beneficially' (benefic influence, as
    # he glosses it at 7480 and 7910) and 7312-7314 on malefic influence. With both clauses
    # re-homed the base record had nothing to say and would have rendered an empty reading.
    # It was neutral, so removing it moves no verdict. Content: H9.L.2a/b.
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H9.L.2a", house=9, signification="fortune", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(9, 2), C.InfluencedBy("LORD_OF:9")),
        general="the 9th lord placed in the 2nd beneficially - the native's father is a "
                "rich and influential man; the native acquires wealth from the father",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7310)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H9.L.2b", house=9, signification="fortune", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(9, 2), C.AfflictedBy("LORD_OF:9")),
        general="malefics influencing the 9th lord in the 2nd - ruin or destroy paternal "
                "property",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7312)),
    RuleRecord(
        id="H9.L.3", house=9, signification="fortune", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-9 sweep (1/12 correct): the opener only restates the placement;
        # the affliction clauses (7320-7324) -> H9.L.3a.
        condition=C.LordIn(9, 3),
        fortified=None,
        afflicted=None,
        general="the native makes his fortune through writing, speeches and oratorial "
                "abilities; the native's father will be a man of moderate means while the "
                "native advances his fortune through his co-borns",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7316)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H9.L.3a", house=9, signification="fortune", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(9, 3), C.AfflictedBy("LORD_OF:9")),
        general="malefics afflicting the 9th lord in the 3rd - the native may land in "
                "trouble through his writings, which may be irrational and even obscene "
                "depending upon the nature of affliction; he may be forced to sell his "
                "paternal property because of troubles arising from his writings",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7320)),
    RuleRecord(
        id="H9.L.4", house=9, signification="fortune", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-9 sweep (1/12 correct): unconditioned base restored; affliction
        # clauses -> H9.L.4a, Rahu -> H9.L.4b. 7330 was DROPPED and reads self-contradictory
        # as printed.
        condition=C.LordIn(9, 4),
        fortified=None,
        afflicted=None,
        general="vast landed properties and beautiful bungalows, or the native may earn "
                "through estate and land dealings; his mother will be a rich and fortunate "
                "woman; he will inherit his father's immovable properties",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7326)),
    # 7330 reads 'may not have any domestic unhappiness' inside an AFFLICTION clause --
    # almost certainly a misprint for 'happiness'. Kept as printed, flagged, not silently
    # corrected. Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H9.L.4a", house=9, signification="fortune", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(9, 4), C.AfflictedBy("LORD_OF:9")),
        general="the 9th lord afflicted in the 4th - the native may not have any domestic "
                "unhappiness [sic, as printed; almost certainly 'happiness']; his early "
                "life will be crossed by miseries due to a hard-hearted father or "
                "disharmony between parents",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7330)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H9.L.4b", house=9, signification="fortune", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(9, 4), C.AfflictedBy("LORD_OF:9", {"Rahu"})),
        general="Rahu afflicting - the mother may be a divorcee or living separately from "
                "his father",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7333)),
    RuleRecord(
        id="H9.L.5", house=9, signification="fortune", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-9 sweep (1/12 correct): wholly unconditioned; it was labelled as
        # a strength reading.
        condition=C.LordIn(9, 5),
        fortified=None,
        afflicted=None,
        general="a prosperous and famous father; the native's sons may also be very "
                "fortunate in life and enjoy success and distinction",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7336)),
    RuleRecord(
        id="H9.L.6", house=9, signification="fortune", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-9 sweep (1/12 correct): benefic hemming of the 6th (7341) ->
        # H9.L.6a; malefic affliction (7347) -> H9.L.6b. Neither is a strength test.
        condition=C.LordIn(9, 6),
        fortified=None,
        # HTJAH-II:7340 is a FLAT unconditioned base — "The ninth lord in the sixth house
        # gives a sickly father afflicted with chronic diseases" — with no benefic/malefic
        # opener. Only the malefic clause that follows is conditioned. (The father being
        # "afflicted with chronic diseases" describes the FATHER, not the 9th lord; that
        # wording is very likely what misled the original encoder.)
        general="a sickly father afflicted with chronic diseases",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7340)),
    # Benefics flanking the 6th = benefics in the 5th and 7th (whole sign). Uses the corpus
    # benefic class of ClassInHouseFrom. Neutral: refines a parent that already votes for
    # this placement.
    RuleRecord(
        id="H9.L.6a", house=9, signification="fortune", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(9, 6), C.ClassInHouseFrom("benefic", "LAGNA", {5}), C.ClassInHouseFrom("benefic", "LAGNA", {7})),
        general="benefics flanking the 6th - the native may gain wealth through the "
                "successful termination of the father's legal problems, and by way of "
                "compensation, costs, etc.",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7341)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H9.L.6b", house=9, signification="fortune", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(9, 6), C.AfflictedBy("LORD_OF:9")),
        general="malefics afflicting the 9th lord in the 6th - the native's attempts to "
                "make his fortune may be frustrated through litigation involving his father "
                "or debts contracted by him",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7347)),
    RuleRecord(
        id="H9.L.7", house=9, signification="fortune", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-9 sweep (1/12 correct): the yoga-gated clauses (7354, 7356) have
        # no predicate -> H9.L.7a/b.
        condition=C.LordIn(9, 7),
        fortified=None,
        afflicted=None,
        general="the native may go abroad and prosper there; his father may also prosper in "
                "foreign lands; he will get a noble and lucky wife",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7352)),
    RuleRecord(
        id="H9.L.7a", house=9, signification="fortune", group="lord_in_house",
        kind="descriptive",
        condition=None,
        general="ascetic yogas present in the chart - the native may seek spiritual "
                "guidance and fulfilment abroad. TODO(predicate: ascetic / Pravrajya yoga "
                "presence)",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7354)),
    RuleRecord(
        id="H9.L.7b", house=9, signification="fortune", group="lord_in_house",
        kind="descriptive",
        condition=None,
        general="asubhayogas spoiling the 9th lord - the father may meet with his death "
                "abroad. TODO(predicate: an asubha yoga involving the 9th lord; AfflictedBy "
                "would be an unnamed approximation)",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7356)),
    RuleRecord(
        id="H9.L.8", house=9, signification="fortune", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-9 sweep (1/12 correct): three clauses gated on affliction or
        # benefic contact -> H9.L.8a-c.
        condition=C.LordIn(9, 8),
        fortified=None,
        # HTJAH-II:7359 is likewise a FLAT unconditioned base — "The native may lose his
        # father early in life" — followed by two separately conditioned clauses ("If
        # malefics afflict the eighth house in such a case...", "Afflictions may cause...").
        general="the native may lose his father early in life",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7359)),
    # With the 9th lord in the 8th, malefic contact with the lord is exactly a malefic
    # occupying or aspecting the 8th (whole sign). Neutral: refines a parent that already
    # votes for this placement.
    RuleRecord(
        id="H9.L.8a", house=9, signification="fortune", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(9, 8), C.AfflictedBy("LORD_OF:9")),
        general="malefics afflicting the 8th house in such a case - he may suffer severe "
                "poverty and heavy responsibility due to the father's death",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7360)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H9.L.8b", house=9, signification="fortune", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(9, 8), C.InfluencedBy("LORD_OF:9")),
        general="benefics influencing the 9th lord - the native may inherit substantial "
                "paternal property",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7362)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H9.L.8c", house=9, signification="fortune", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(9, 8), C.AfflictedBy("LORD_OF:9")),
        general="afflictions - may cause the native to abandon traditions or damage "
                "religious institutions and trusts set up by the family",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7363)),
    RuleRecord(
        id="H9.L.9", house=9, signification="fortune", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-9 sweep (1/12 correct): 'afflicted by malefics OR in 6/8/12 from
        # Navamsa Lagna' (7370) -- neither arm is strength; both are now expressible ->
        # H9.L.9a.
        condition=C.LordIn(9, 9),
        fortified=None,
        afflicted=None,
        general="a long-lived and prosperous father; the native will be religiously "
                "inclined and be charitable; he will travel abroad and earn money and "
                "distinction thereby",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7367)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H9.L.9a", house=9, signification="fortune", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(9, 9), C.Or(C.AfflictedBy("LORD_OF:9"), C.InVargaHouseFrom("LORD_OF:9", "LAGNA", {6, 8, 12}, varga="D9"))),
        general="the 9th lord afflicted by malefics, or in the 6th, 8th or 12th from the "
                "Navamsa Lagna - the native's father will die early",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7370)),
    RuleRecord(
        id="H9.L.10", house=9, signification="fortune", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-9 sweep (1/12 correct): wholly unconditioned; it was labelled as
        # a strength reading.
        condition=C.LordIn(9, 10),
        fortified=None,
        afflicted=None,
        general="the native will become very famous and powerful; he will be generous and "
                "occupy posts of authority; he will earn much wealth and acquire every kind "
                "of comfort and luxury; his means of livelihood will be righteous and he "
                "will be a law abiding citizen",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7374)),
    RuleRecord(
        id="H9.L.11", house=9, signification="fortune", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-9 sweep (1/12 correct): 'If afflicted' (7385) -> H9.L.11a.
        condition=C.LordIn(9, 11),
        fortified=None,
        afflicted=None,
        general="the native will be exceedingly rich; he will have powerful and influential "
                "friends; his father will be a well-known and well-placed man",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7380)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H9.L.11a", house=9, signification="fortune", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(9, 11), C.AfflictedBy("LORD_OF:9")),
        general="the 9th lord afflicted - unfaithful friends will destroy the native's "
                "wealth through selfish scheming and fraud",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7385)),
    RuleRecord(
        id="H9.L.12", house=9, signification="fortune", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(9, 12),
        # SENTIMENT-SPLIT, corrected 2026-09-01. HTJAH-II:7389-7394 (= HTJAH-I:12581-12584)
        # is ONE paragraph with no conditional opener of any kind, and the encoder cut it at
        # Raman's own "but": "He will be religious and noble BUT ALWAYS IN WANT" — the first
        # half filed as fortified, the second half plus the rest of the paragraph as
        # afflicted.
        #
        # CORRECTION 2026-09-01: this comment originally called H9.L.12 "the LONE exception in
        # House 9". That was WRONG, and the condition-fidelity audit caught it by reading all
        # twelve entries in full. H9.L.6 (7340) and H9.L.8 (7359) also carry flat
        # unconditioned base readings — "gives a sickly father afflicted with chronic
        # diseases", "The native may lose his father early in life" — with no benefic/malefic
        # opener, and both had them filed under `afflicted`. Both are now repaired. The claim
        # below is retained, corrected, because the reasoning it rests on is still right for
        # the OTHER nine entries; only the word "lone" was false. It was reached by sampling
        # the entries with explicit openers rather than reading every one — the same
        # first-entry sampling error this audit was designed to avoid.
        #
        # The rest of the section (the nine entries other than L.6, L.8 and L.12) is
        # written with explicit malefic/benefic openers and was reviewed as correctly
        # encoded, so repairing this record does not disturb H9.L.1-11.
        general="the 9th lord in the 12th gives a poor background; the native will suffer "
                "much and will have to work very hard in life, and even then success may "
                "not come to him; he will be religious and noble but always in want; the "
                "father may die early, leaving the native penniless",
        fortified="the 9th lord in the 12th gives a poor background; the native will suffer "
                  "much and will have to work very hard in life, and even then success may "
                  "not come to him; he will be religious and noble but always in want; the "
                  "father may die early, leaving the native penniless",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7389)),
    RuleRecord(
        id="H9.L.S1", house=9, signification="fortune", group="lord_in_house",
        kind="descriptive",
        condition=None,
        general=None,
        fortified="the 9th lord very powerful - he becomes capable of conferring fortune "
                  "even if placed in a malefic house. TODO(predicate: a 'very powerful' "
                  "Shadbala band ABOVE is_powerful, scoped to the 9th lord in a malefic "
                  "house; section-level, applies to H9.L.6/8/12)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7398)),
    RuleRecord(
        id="H9.L.S2", house=9, signification="fortune", group="lord_in_house",
        kind="descriptive",
        condition=None,
        general="the 9th lord afflicted but the 9th house beneficially disposed - the "
                "intensity of the malefic results will be greatly reduced. TODO(predicate: "
                "benefic disposition of the 9th HOUSE; a section-level modifier of the "
                "malefic readings, not a reading itself)",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7400)),

)
