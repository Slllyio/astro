"""House 10 (Karma — career/profession) — Lord-in-12-houses RuleRecords.

The "Lord of the 10th in the 12 Houses" table (HTJAH-II:9456-9575). Moved
verbatim from the former flat ``house_10_karma.py`` during the Stage-4 split.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    RuleRecord(
        id="H10.L.1", house=10, signification="career", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-10 sweep (0/12 correct): the Lagna-lord conjunction (9462-9465)
        # welded onto every strong-lord chart; a label did not change who saw it ->
        # H10.L.1a.
        condition=C.LordIn(10, 1),
        # UNSOURCED, REMOVED 2026-09-01. This slot read "weak Lagna and 10th lord →
        # modest attainment; little distinction". A dedicated provenance audit read
        # HTJAH-II:9456-9465 in full and searched BOTH volumes: "modest" and "little
        # distinction" appear nowhere, and the cited paragraph is four unconditioned
        # favourable sentences containing no conditional clause at all. The forensic
        # signature is a cross-house formula transfer: Raman DOES use a
        # strong/middling/weak ladder for a lord in Lagna, but only for the 4th lord
        # (HTJAH-I:4151) and the 11th (HTJAH-II:14259) — never the 10th. The encoder
        # generalised a real idiom onto a placement where Raman withholds it.
        #
        # The `fortified` text on this record IS sourced, verbatim and completely, so the
        # rule is repaired rather than deleted: deleting it would discard genuine doctrine
        # to punish an invented sentence, and demoting it to `kind="descriptive"` would
        # stop it firing and take the sourced reading down with the invented one. The same
        # audit checked 185 rules across all 12 packages and both volumes and found this to
        # be the ONLY fabrication (0.5%); its adversarial arm, targeted at this defect's own
        # phrasing, found zero others.
        # HTJAH-II:9459-9465. The base is unconditioned; the pioneer/institution clause is
        # conditioned on the Lagna lord and 10th lord COMBINING in the 1st ('When the Lagna
        # and 10th lord combine in the first house...'). Folded into `fortified` it showed
        # on any strong-lord chart - and, because `_branch` also defaults to `fortified`
        # when Shadbala is absent, on every sparse chart too. Now labelled as the
        # configuration it is.
        general="rises in life by sheer dint of perseverance; self-employed, or pursues a "
                "profession of independence",
        fortified="rises in life by sheer dint of perseverance; self-employed, or pursues a "
                  "profession of independence",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9459)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H10.L.1a", house=10, signification="career", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(10, 1), C.LordsConjunct(1, 10)),
        general="the Lagna lord and the 10th lord combining in the 1st - very famous and a "
                "pioneer in his field of work; founds a public institution and engages in "
                "social projects",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9462)),
    RuleRecord(
        id="H10.L.2", house=10, signification="career", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-10 sweep (0/12 correct): unconditioned text was only in
        # fortified; 9470 is gated on affliction of the 10th HOUSE -> H10.L.2a. 'rises well
        # in life' restored.
        condition=C.LordIn(10, 2),
        fortified="fortunate; rises well in life and makes a lot of money; may engage in "
                  "the family trade and develop it; prospers in catering and restaurant "
                  "businesses",
        afflicted=None,
        general="fortunate; rises well in life and makes a lot of money; may engage in the "
                "family trade and develop it; prospers in catering and restaurant "
                "businesses",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9467)),
    RuleRecord(
        id="H10.L.2a", house=10, signification="career", group="lord_in_house",
        # 2026-10-13: promoted from descriptive once HouseAfflictedBy existed (a natural
        # malefic occupies or aspects the house; its own lord excluded). Neutral: refines a
        # parent placement.
        kind="evaluable",
        condition=C.And(C.LordIn(10, 2), C.HouseAfflictedBy(10)),
        general="malefics afflicting the 10th house - suffers losses and is responsible for "
                "winding up the family business",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9470)),
    RuleRecord(
        id="H10.L.3", house=10, signification="career", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-10 sweep (0/12 correct): 'if the 10th lord is well-placed' (9476)
        # is postposed and governs only the speaker/writer sentence. Navamsa/star/3rd-lord
        # clauses -> H10.L.3a-c.
        condition=C.LordIn(10, 3),
        fortified="may have to travel constantly on short journeys; a speaker or writer of "
                  "celebrity; brothers may be instrumental to some extent in advancing his "
                  "career",
        afflicted=None,
        general="may have to travel constantly on short journeys; brothers may be "
                "instrumental to some extent in advancing his career",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9474)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H10.L.3a", house=10, signification="career", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(10, 3), C.InVargaHouseFrom("LORD_OF:10", "LAGNA", {6, 8, 12}, varga="D9")),
        general="the 10th lord in the 6th, 8th or 12th from the Navamsa Lagna - rise in "
                "life slow and beset with obstacles",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9477)),
    RuleRecord(
        id="H10.L.3b", house=10, signification="career", group="lord_in_house",
        kind="descriptive",
        condition=None,
        general="the 10th lord in an unfriendly constellation in the 3rd - rise in life "
                "slow and beset with obstacles. TODO(predicate: PARKED by research "
                "2026-10-13 -- NOT planetary friendship: on Raman's only worked use (Indira "
                "Gandhi, HTJAH-II:14087) natural and Saturn-side compound friendship both "
                "FAIL. Surviving readings: tara 3/5/7 from Janma (HTJAH-I:1142; NH:8376 "
                "'Atimitra (very friendly) star'), the star lord's compound view, or the "
                "star lord's functional nature. Reviews split; re-open on a second worked "
                "chart that separates them)",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9478)),
    # Only the Navamsa half of the shared antecedent is encodable (see H10.L.3b). Neutral:
    # refines a parent that already votes for this placement.
    RuleRecord(
        id="H10.L.3c", house=10, signification="career", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(10, 3), C.InVargaHouseFrom("LORD_OF:10", "LAGNA", {6, 8, 12}, varga="D9"), C.AfflictedBy("LORD_OF:3")),
        general="the 10th lord so placed and the 3rd lord also afflicted - rivalry between "
                "brothers may lead to reversals and obstacles in the career",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9480)),
    RuleRecord(
        id="H10.L.4", house=10, signification="career", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-10 sweep (0/12 correct): no sentence is gated on weakness; the
        # dignity/combustion/affliction clause (9495), the D60 clause (9497) and the
        # 4th/9th/10th-lord combination (9489) -> H10.L.4a-c.
        condition=C.LordIn(10, 4),
        fortified="a lucky man, highly learned in various subjects; famous both for his "
                  "learning and generosity; respected wherever he goes and receives royal "
                  "favour; may engage in agricultural pursuits or dealings with immovable "
                  "properties",
        afflicted=None,
        general="a lucky man, highly learned in various subjects; famous both for his "
                "learning and generosity; may engage in agricultural pursuits or dealings "
                "with immovable properties",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9484)),
    # 'depressed' = positional debility (Raman gives no Neecha-Bhanga caveat here);
    # 'eclipsed' = Combust; 'inimical sign' = enemy dignity. Neutral: refines a parent that
    # already votes for this placement.
    RuleRecord(
        id="H10.L.4a", house=10, signification="career", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(10, 4), C.Or(C.LordHasDignity(10, {"debil", "enemy"}), C.Combust("LORD_OF:10"), C.AfflictedBy("LORD_OF:10"))),
        general="the 10th lord depressed, eclipsed, in an inimical sign or afflicted by "
                "malefics - loses his lands and is forced to take to a life of servitude",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9495)),
    RuleRecord(
        id="H10.L.4b", house=10, signification="career", group="lord_in_house",
        kind="descriptive",
        condition=None,
        general="the 10th lord conjoining the 8th lord in the 4th in a malefic shashtyamsa "
                "- loses his lands and is forced into servitude. TODO(predicate: "
                "malefic-shashtyamsa (D60) class - BLOCKED on source attribution, see "
                "DOCTRINE_BACKLOG 'D60 named-class doctrine')",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9497)),
    RuleRecord(
        id="H10.L.4c", house=10, signification="career", group="lord_in_house",
        kind="descriptive",
        condition=None,
        general="the 4th, 9th and 10th lords beneficially disposed and related to one "
                "another - wields great political authority as a president or head of a "
                "government. TODO(predicate: a three-way relation among three lords, each "
                "beneficially disposed)",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9489)),
    RuleRecord(
        id="H10.L.5", house=10, signification="career", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-10 sweep (0/12 correct): two conditioned clauses were folded into
        # fortified -> H10.L.5a/b.
        condition=C.LordIn(10, 5),
        # HTJAH-II:9501-9506. Base unconditioned. TWO conditioned clauses were folded in:
        # 'If benefics join the lord of the 10th in the 5th house' and the orphanage clause,
        # which Raman gates on a NAVAMSA placement ('if the 10th lord occupies the 6th, 8th
        # or 12th Navamsa') - the second condition was dropped entirely by the encoding.
        general="shines well as a broker and engages in speculation and similar business",
        fortified="shines well as a broker and engages in speculation and similar business",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9501)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H10.L.5a", house=10, signification="career", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(10, 5), C.JoinedBy("LORD_OF:10", C.FIRM_BENEFICS)),
        general="benefics joining the 10th lord in the 5th - a simple and pious life, "
                "engaged in prayers and pious activities",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9502)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H10.L.5b", house=10, signification="career", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(10, 5), C.InVargaHouseFrom("LORD_OF:10", "LAGNA", {6, 8, 12}, varga="D9")),
        general="the 10th lord in the 6th, 8th or 12th Navamsa - may become the head of an "
                "orphanage or remand home",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9504)),
    RuleRecord(
        id="H10.L.6", house=10, signification="career", group="lord_in_house", kind="descriptive",
        # 2026-10-28 rule-defect review (docs/raman_saab/research/rule_defects_review2_2026-10-28.json): descriptive, cite 9508.
        # 2026-10-13 House-10 sweep (0/12 correct): Saturn's aspect, benefic aspects and
        # Rahu/afflicted malefics joining (9509-9515) -> H10.L.6a-d.
        condition=C.LordIn(10, 6),
        fortified="an occupation bearing on judiciary, prisons or hospitals",
        afflicted=None,
        general="an occupation bearing on judiciary, prisons or hospitals",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 9508)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H10.L.6a", house=10, signification="career", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(10, 6), C.Aspects("Saturn", "LORD_OF:10")),
        general="Saturn aspecting the 10th lord - may have to work all his life in a "
                "low-paying job with not much prospects",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9509)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H10.L.6b", house=10, signification="career", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(10, 6), C.Or(C.Aspects("Jupiter", "LORD_OF:10"), C.Aspects("Venus", "LORD_OF:10"))),
        general="benefics aspecting the 10th lord - holds a post of authority and is held "
                "in high esteem for his character",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9511)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H10.L.6c", house=10, signification="career", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(10, 6), C.Conjunct("Rahu", "LORD_OF:10")),
        general="Rahu with the 10th lord - may suffer disgrace in his career, be exposed to "
                "criminal action and face imprisonment",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9513)),
    RuleRecord(
        id="H10.L.6d", house=10, signification="career", group="lord_in_house",
        kind="descriptive",
        condition=None,
        general="afflicted malefics with the 10th lord - may suffer disgrace in his career, "
                "be exposed to criminal action and face imprisonment. TODO(predicate: "
                "conjunction with a malefic that is itself afflicted)",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9513)),
    RuleRecord(
        id="H10.L.7", house=10, signification="career", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-10 sweep (0/12 correct): 'If malefics afflict the 10th lord'
        # (9521) -> H10.L.7a.
        condition=C.LordIn(10, 7),
        fortified="a mature wife who assists him in his work; travels abroad on diplomatic "
                  "missions; well known for his skill in talking and achieving objectives; "
                  "profits through partnerships and co-operative ventures",
        afflicted=None,
        general="a mature wife who assists him in his work; travels abroad on diplomatic "
                "missions; well known for his skill in talking and achieving objectives; "
                "profits through partnerships and co-operative ventures",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9517)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H10.L.7a", house=10, signification="career", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(10, 7), C.AfflictedBy("LORD_OF:10")),
        general="malefics afflicting the 10th lord - debased in sexual habits and indulges "
                "in every kind of vice",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9521)),
    RuleRecord(
        id="H10.L.8", house=10, signification="career", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-10 sweep (0/12 correct): 9525 restored; malefic affliction,
        # Jupiter and Saturn clauses -> H10.L.8a-c.
        condition=C.LordIn(10, 8),
        fortified="many breaks in career; occupies a high office in his field but only for "
                  "a short time",
        afflicted=None,
        general="many breaks in career",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 9525)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H10.L.8a", house=10, signification="career", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(10, 8), C.AfflictedBy("LORD_OF:10")),
        general="a malefic afflicting the 10th lord - criminal propensities, commits "
                "offences",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9527)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H10.L.8b", house=10, signification="career", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(10, 8), C.InfluencedBy("LORD_OF:10", {"Jupiter"})),
        general="Jupiter influencing the 10th lord by aspect or association in the 8th - "
                "becomes a mystic or spiritual teacher",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9532)),
    # 'Saturn here' read as Saturn in the 8th, which covers both Saturn-as-10th-lord and
    # Saturn alongside it. Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H10.L.8c", house=10, signification="career", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(10, 8), C.InRashiHouse("Saturn", 8)),
        general="Saturn here - an undertaker, or otherwise employed in burning ghats, "
                "graveyards, etc.",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9534)),
    RuleRecord(
        id="H10.L.9", house=10, signification="career", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-10 sweep (0/12 correct): the Jupiter-aspect claim had been shown
        # to every chart. Aspect clauses -> H10.L.9a/b. 9543-9544 restored.
        condition=C.LordIn(10, 9),
        fortified="a spiritual stalwart; follows a hereditary profession or that of a "
                  "preacher, teacher or healer; the father has a great influence on him; a "
                  "dutiful son who does many charitable deeds",
        afflicted=None,
        general="a spiritual stalwart; follows a hereditary profession or that of a "
                "preacher, teacher or healer; the father has a great influence on him; a "
                "dutiful son who does many charitable deeds",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9537)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H10.L.9a", house=10, signification="career", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(10, 9), C.Aspects("Jupiter", "LORD_OF:10")),
        general="Jupiter aspecting the 10th lord - a beacon light to spiritual seekers",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9538)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H10.L.9b", house=10, signification="career", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(10, 9), C.Or(C.Aspects("Jupiter", "LORD_OF:10"), C.Aspects("Venus", "LORD_OF:10")), C.Or(C.Aspects("Sun", "LORD_OF:10"), C.Aspects("Mars", "LORD_OF:10"), C.Aspects("Saturn", "LORD_OF:10"), C.Aspects("Rahu", "LORD_OF:10"), C.Aspects("Ketu", "LORD_OF:10"))),
        general="both benefics and malefics aspecting the 10th lord - generally fortunate "
                "and well-to-do",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9539)),
    # H10.L.10 REMOVED: 2026-10-13 House-10 sweep. Raman gives NO unconditioned sentence for
    # the 10th lord in the 10th (9546-9554): every clause is gated on strength, weak-and-
    # afflicted, a Navamsa placement or three conjoining planets. A fortified-only base
    # record leaked 'highly successful' to weak and Shadbala-less charts via _branch's
    # fortified default. It was neutral. Content: H10.L.10a-d.
    RuleRecord(
        id="H10.L.10a", house=10, signification="career", group="lord_in_house",
        # 2026-10-13: promoted from descriptive once IsStrong/IsWeak existed (effective
        # strength: Shadbala bar plus combustion/debility overrides). Neutral: refines a
        # parent placement.
        kind="evaluable",
        condition=C.And(C.LordIn(10, 10), C.IsStrong("LORD_OF:10")),
        general="the 10th lord strongly disposed in the 10th - can be highly successful in "
                "his profession and command respect and honour",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9546)),
    RuleRecord(
        id="H10.L.10b", house=10, signification="career", group="lord_in_house",
        # 2026-10-13: promoted from descriptive once IsStrong/IsWeak existed (effective
        # strength: Shadbala bar plus combustion/debility overrides). Neutral: refines a
        # parent placement.
        kind="evaluable",
        condition=C.And(C.LordIn(10, 10), C.IsWeak("LORD_OF:10"), C.AfflictedBy("LORD_OF:10")),
        general="the 10th lord weak and afflicted - no self-respect, cringing for favours; "
                "dependent all his life; fickle-minded",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9548)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H10.L.10c", house=10, signification="career", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(10, 10), C.InVargaHouseFrom("LORD_OF:10", "LAGNA", {6, 8, 12}, varga="D9")),
        general="the 10th lord in the 6th, 8th or 12th from the Navamsa - career routine "
                "and ordinary",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9550)),
    # At least four planets in the 10th (the lord plus three); CountInHouse counts the
    # nodes. Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H10.L.10d", house=10, signification="career", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(10, 10), C.CountInHouse(10, 4)),
        general="three other planets conjoining the 10th lord in the 10th - becomes an "
                "ascetic",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9552)),
    RuleRecord(
        id="H10.L.11", house=10, signification="career", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-10 sweep (0/12 correct): 9560 is gated on affliction of the 11th
        # HOUSE -> H10.L.11a.
        condition=C.LordIn(10, 11),
        fortified="earns immense riches; fortunate in every respect, engages in meritorious "
                  "deeds; gives employment to hundreds of persons; endowed with a high "
                  "sense of honour; many friends",
        afflicted=None,
        general="earns immense riches; fortunate in every respect, engages in meritorious "
                "deeds; gives employment to hundreds of persons; endowed with a high sense "
                "of honour; many friends",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9556)),
    RuleRecord(
        id="H10.L.11a", house=10, signification="career", group="lord_in_house",
        # 2026-10-13: promoted from descriptive once HouseAfflictedBy existed (a natural
        # malefic occupies or aspects the house; its own lord excluded). Neutral: refines a
        # parent placement.
        kind="evaluable",
        condition=C.And(C.LordIn(10, 11), C.HouseAfflictedBy(11)),
        general="the 11th house under affliction - friends turn enemies and cause every "
                "sort of hardship and worry",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9560)),
    RuleRecord(
        id="H10.L.12", house=10, signification="career", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-10 sweep (0/12 correct): 'If beneficially disposed' (9569) is set
        # against 'if malefics afflict' -> benefic influence, not strength. Clauses ->
        # H10.L.12a-d.
        condition=C.LordIn(10, 12),
        general="works in a far-off place, lacking comforts and facing many difficulties "
                "in life",
        fortified="works in a far-off place, lacking comforts and facing many difficulties "
                  "in life",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 9564)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H10.L.12a", house=10, signification="career", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(10, 12), C.InfluencedBy("LORD_OF:10")),
        general="the 10th lord beneficially disposed - becomes a spiritual seeker",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9569)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H10.L.12b", house=10, signification="career", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(10, 12), C.AfflictedBy("LORD_OF:10")),
        general="malefics afflicting the 10th lord - separated from his family, wanders "
                "about without success",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9570)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H10.L.12c", house=10, signification="career", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(10, 12), C.AfflictedBy("LORD_OF:10", {"Rahu"})),
        general="Rahu afflicting the 10th lord - a cheat and a criminal; causes sorrow to "
                "his family and relatives",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9573)),
    RuleRecord(
        id="H10.L.12d", house=10, signification="career", group="lord_in_house",
        kind="descriptive",
        condition=None,
        general="[sic] indulges in smuggling and other nefarious activities. TODO(source: a "
                "comma splice at 9572-9573 leaves the antecedent unresolvable - it may "
                "belong to H10.L.12b, to H10.L.12c, or stand alone; parked rather than "
                "asserted on every chart)",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9572)),
)
