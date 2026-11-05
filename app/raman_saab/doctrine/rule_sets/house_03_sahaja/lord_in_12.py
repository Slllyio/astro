"""House 3 (Sahaja / Bhratru Bhava) — lord of the 3rd in the 12 houses.

Encodes the "Lord of the 3rd in the 12 Houses" table from
`docs/raman_saab/methodology/house_03_sahaja.md`, each row as an evaluable
`RuleRecord` carrying the first HTJAH-I line cited in that row.

Karaka = Mars (Bhratru-Karaka); lord-in-house rules use frame="LAGNA", varga="D1".
Source span: HTJAH-I:3337-3413 (lord-in-house table).
Moved verbatim from the former single-module `house_03_sahaja.py` (Stage-1 split).
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    # — 3rd lord in the 12 houses (HTJAH-I:3337-3413) —
    RuleRecord(
        id="H3.L.1", house=3, signification="siblings", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(3, 1),
        fortified="expert in dancing, music, acting; livelihood via fine arts; earns name as actor",
        # HTJAH-I:3337-3338, unconditioned.
        general="earns his livelihood by self-exertion; vindictive, lean and tall of body, "
                "brave and courageous, always sickly and serving others",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3337)),
    RuleRecord(
        id="H3.L.2", house=3, signification="siblings", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(3, 2),
        # HTJAH-I:3343-3346 is one unconditioned paragraph; its "unless there are other
        # favourable combinations" is a qualifier INSIDE Raman's sentence, not a
        # fortification branch, and was lifted out to manufacture one. Restored in place.
        general="an unfavourable position, as it makes the subject rather unscrupulous "
                "unless there are other favourable combinations; he will make advances on "
                "the women and wealth of others; likes mean deeds and is generally devoid "
                "of happiness; likely to lose his younger brothers",
        fortified="an unfavourable position, as it makes the subject rather unscrupulous "
                  "unless there are other favourable combinations; he will make advances on "
                  "the women and wealth of others; likes mean deeds and is generally devoid "
                  "of happiness; likely to lose his younger brothers",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 3343)),
    RuleRecord(
        id="H3.L.3", house=3, signification="siblings", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-3 sweep: HTJAH-I:3348-3349 is unconditioned and sat in fortified.
        # The sibling-death clauses (3352-3354) are gated on WHICH planet is the 3rd lord --
        # expressible exactly by sign, now H3.L.3a-c.
        condition=C.LordIn(3, 3),
        fortified="the 3rd lord well-disposed in the 3rd, 6th or 11th - a number of younger "
                  "brothers",
        # NOT a general reading, and NOT relocated — but flagged. These three clauses
        # (HTJAH-I:3352-3354) are conditioned on PLANET IDENTITY: which planet happens to be
        # the 3rd lord (Mars / Saturn / Sun). There is no affliction test anywhere in them,
        # so firing them off an affliction predicate is wrong in BOTH directions — an
        # afflicted non-Mars 3rd lord wrongly reads "loses all younger brothers", and an
        # unafflicted Mars 3rd lord wrongly does not. Needs a configuration predicate, which
        # is a CONDITION change and would move the ratchet; see DOCTRINE_BACKLOG.
        afflicted=None,
        general="brave, surrounded by friends and relatives, blessed with good children, "
                "wealthy, happy and contented",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3348)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H3.L.3a", house=3, signification="siblings", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.InRashiHouse("Mars", 3), C.Or(C.InSign("Mars", 1), C.InSign("Mars", 8))),
        general="the 3rd lord being Mars and occupying the 3rd - generally the native will "
                "lose all his younger brothers",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3352)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H3.L.3b", house=3, signification="siblings", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.InRashiHouse("Saturn", 3), C.Or(C.InSign("Saturn", 10), C.InSign("Saturn", 11))),
        general="the 3rd lord being Saturn and occupying the 3rd - similar effects: the "
                "loss of younger brothers",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3353)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H3.L.3c", house=3, signification="siblings", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.InRashiHouse("Sun", 3), C.InSign("Sun", 5)),
        general="the Sun as 3rd lord occupying the 3rd - will kill elder brothers",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3353)),
    RuleRecord(
        id="H3.L.4", house=3, signification="siblings", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-3 sweep: no sentence is gated on the 3rd lord's strength ALONE --
        # 3359 conjoins the Lagna and 9th lords' weakness, 3360 the 9th lord, 3361 Mars. Re-
        # homed to H3.L.4a-c.
        condition=C.LordIn(3, 4),
        # HTJAH-I:3356-3357 is one sentence cut at Raman's own "But". The remaining
        # clauses are neither fortification nor affliction: the brothers-survive pair is
        # conditioned on the LAGNA and 9TH lords' strength (3359-3360), "When Mars is weak"
        # is KARAKA strength (3361), and "if the 3rd house is beneficially disposed" is a
        # HOUSE-disposition branch (3361-3362).
        general="life will be happy on the whole; he becomes rich and learned; but the wife "
                "will be cruel-hearted and mean",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3356)),
    RuleRecord(
        id="H3.L.4a", house=3, signification="siblings", group="lord_in_house",
        # 2026-10-13: promoted from descriptive once IsStrong/IsWeak existed (effective
        # strength: Shadbala bar plus combustion/debility overrides). Neutral: refines a
        # parent placement.
        kind="evaluable",
        condition=C.And(C.LordIn(3, 4), C.IsStrong("LORD_OF:3"), C.IsWeak("LORD_OF:1"), C.IsWeak("LORD_OF:9")),
        general="the lord of the 3rd well fortified in the 4th and the lords of Lagna and "
                "the 9th rendered weak - his brothers will survive him",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3359)),
    RuleRecord(
        id="H3.L.4b", house=3, signification="siblings", group="lord_in_house",
        # 2026-10-13: promoted from descriptive once IsStrong/IsWeak existed (effective
        # strength: Shadbala bar plus combustion/debility overrides). Neutral: refines a
        # parent placement.
        kind="evaluable",
        condition=C.And(C.LordIn(3, 4), C.IsStrong("LORD_OF:9")),
        general="the 9th lord strong - he will have step-brothers",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3360)),
    RuleRecord(
        id="H3.L.4c", house=3, signification="siblings", group="lord_in_house",
        # 2026-10-13: promoted from descriptive once IsStrong/IsWeak existed (effective
        # strength: Shadbala bar plus combustion/debility overrides). Neutral: refines a
        # parent placement.
        kind="evaluable",
        condition=C.And(C.LordIn(3, 4), C.IsWeak("Mars")),
        general="Mars weak - he will lose his lands and will have to live in others' "
                "houses; the evil results will be minimised if the 3rd house is "
                "beneficially disposed",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3361)),
    RuleRecord(
        id="H3.L.5", house=3, signification="siblings", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(3, 5),
        # HTJAH-I:3364-3365 is one unconditioned paragraph; "Financially well off in life"
        # sits between its two other sentences and was pulled out into `fortified`.
        # Restored in Raman's order. The real fortified paragraph opens at 3367.
        general="much pleasure will not be derived from children; financially well off in "
                "life; friction will prevail in the domestic life",
        fortified="the 3rd lord in the 5th, well disposed - highly benefited by his "
                  "brothers; large-scale agricultural operations, or adoption by a rich "
                  "family; shines well in Government service",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 3364)),
    RuleRecord(
        id="H3.L.6", house=3, signification="siblings", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-3 sweep: the sportsman clause (3375) has its own antecedent
        # (H3.L.6a); the affliction clause (3376) names two HOUSES (H3.L.6b). 'A number of
        # younger brothers' restored from the 3351 cross-reference.
        condition=C.LordIn(3, 6),
        # HTJAH-I:3371-3377. General at 3371-3372 (including "Becomes rich", which had been
        # pulled into `fortified`); genuinely afflicted at 3376-3377, "When the 6th and the
        # 3rd are both afflicted". The sportsman clause (3375) is CONFIGURATION-conditioned
        # (the 6th lord also joining the 3rd), not a fortification result.
        general="hates brothers and relatives and has difficulty through them; becomes rich; "
                "maternal relatives will suffer; accepts illegal gratifications",
        fortified="the 3rd lord in the 6th, well disposed - a younger brother joins the "
                  "Army; one of the brothers becomes a successful physician; a number of "
                  "younger brothers",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3371)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H3.L.6a", house=3, signification="siblings", group="lord_in_house",
        kind="evaluable",
        condition=C.Parivartana(3, 6),
        general="the 6th lord also joining the 3rd - the native becomes either a sportsman, "
                "physical culturist or an athlete",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3375)),
    RuleRecord(
        id="H3.L.6b", house=3, signification="siblings", group="lord_in_house",
        # 2026-10-13 review: 'the 6th and the 3rd' are the LORDS, not the houses -- the
        # paragraph (HTJAH-I:3374-3377) runs on lords and sets 'afflicted' against 'well
        # disposed', a lord's quality; bare ordinals for lords recur (HTJAH-II:9489-9490).
        # Medium confidence (elliptical wording).
        # 2026-10-13: promoted from descriptive once HouseAfflictedBy existed (a natural
        # malefic occupies or aspects the house; its own lord excluded). Neutral: refines a
        # parent placement.
        kind="evaluable",
        condition=C.And(C.LordIn(3, 6), C.AfflictedBy("LORD_OF:3"), C.AfflictedBy("LORD_OF:6")),
        general="when the 6th and the 3rd are both afflicted - he will suffer from "
                "diseases, be tormented by enemies, and will himself be deceitful",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3376)),
    RuleRecord(
        id="H3.L.7", house=3, signification="siblings", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-3 sweep: the 7th-lord-in-Lagna clause (3383) re-opens with its
        # own 'When' -- now H3.L.7a.
        condition=C.LordIn(3, 7),
        fortified="the 3rd lord in the 7th, well-fortified - cordial feelings between "
                  "brothers",
        # HTJAH-I:3379-3380, unconditioned. The abroad-brother clause in `fortified` is
        # conditioned on the 7TH LORD IN LAGNA (3383) — a configuration, not fortification.
        general="may incur the displeasure of rulers or authorities; many vicissitudes in "
                "life; much suffering in childhood; the union will be unfortunate; danger "
                "while travelling",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3379)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H3.L.7a", house=3, signification="siblings", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(3, 7), C.LordIn(7, 1)),
        general="the 7th lord in Lagna - one of the brothers will settle in a foreign "
                "country and will help the native",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3383)),
    RuleRecord(
        id="H3.L.8", house=3, signification="siblings", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(3, 8),
        # HTJAH-I:3388-3392. BOTH paragraphs are unconditioned — 3391's "When the 3rd lord
        # is in the 8th" merely restates the placement. `fortified` held the encoder's
        # disclosure "no specifically favourable variant given for this placement", correct
        # as a note but displaying to the reader AS the strong-lord reading; Raman gives no
        # favourable variant here, and that disclosure survives as this comment.
        general="involvement in a criminal case or false accusations; trouble on account of "
                "death or bequests; marriage unfortunate; the career will not be smooth; a "
                "victim of misfortune; suffers from a serious and dangerous disease and "
                "loses his younger brother",
        fortified="involvement in a criminal case or false accusations; trouble on account "
                  "of death or bequests; marriage unfortunate; the career will not be "
                  "smooth; a victim of misfortune; suffers from a serious and dangerous "
                  "disease and loses his younger brother",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 3388)),
    RuleRecord(
        id="H3.L.9", house=3, signification="siblings", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-3 sweep: 'When afflicted' (3397) is an AFFLICTION test, not
        # weakness -- now H3.L.9a. The stray 'fortune improves after marriage' left
        # fortified; it lives in general.
        condition=C.LordIn(3, 9),
        fortified="the 3rd lord in the 9th, favourably disposed - the native's brother will "
                  "inherit ancestral property; the native himself will be benefited by his "
                  "brother",
        # HTJAH-I:3394-3397. "Father untrustworthy" is Raman's GENERAL reading and must
        # leave `afflicted`; only "When afflicted, the person will have misunderstandings
        # with his father" (3397) is affliction-conditioned. "Long journeys. Sudden and
        # unexpected changes in life." had been dropped entirely; restored.
        general="fortune will improve after marriage; the father untrustworthy; long "
                "journeys; sudden and unexpected changes in life",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 3394)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H3.L.9a", house=3, signification="siblings", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(3, 9), C.AfflictedBy("LORD_OF:3")),
        general="the 3rd lord afflicted - the person will have misunderstandings with his "
                "father",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3397)),
    RuleRecord(
        id="H3.L.10", house=3, signification="siblings", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(3, 10),
        # HTJAH-I:3399-3403. Both paragraphs unconditioned; "A quarrelsome and faithless
        # wife" is the FIRST sentence of Raman's own paragraph, not an afflicted variant.
        general="a quarrelsome and faithless wife; the native will become rich, happy and "
                "intelligent; gain from journeys connected with his profession; all the "
                "brothers will shine well and be helpful to him in all ways",
        fortified="a quarrelsome and faithless wife; the native will become rich, happy and "
                  "intelligent; gain from journeys connected with his profession; all the "
                  "brothers will shine well and be helpful to him in all ways",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 3399)),
    RuleRecord(
        id="H3.L.11", house=3, signification="siblings", group="lord_in_house", kind="evaluable",
        # 2026-10-28 rule-defect review (docs/raman_saab/research/rule_defects_review2_2026-10-28.json): benefic, cite 3351.
        condition=C.LordIn(3, 11),
        fortified="a number of younger brothers when 3rd lord is in 3rd, 6th or 11th",
        # HTJAH-I:3405-3407, a single unconditioned paragraph. `fortified` here is genuine
        # Raman but from 3351, inside the THIRD-house paragraph ("The 3rd lord well-disposed
        # in the 3rd, 6th or 11th indicates a number of younger brothers") — a legitimate
        # cross-reference that does cover this placement, which is why the record's citation
        # was corrected to 3405 rather than the fortified half's 3351.
        general="not a very good combination; earnings with effort; becomes vindictive; the "
                "body unattractive and emaciated; subservient to or dependent upon others, "
                "and liable to frequent attacks of illness",
        afflicted=None,
        # Citation corrected 2026-09-01: was HTJAH-I:3351, which is inside the THIRD-house
        # paragraph ("The 3rd lord well-disposed in the 3rd, 6th or 11th indicates a number
        # of younger brothers") and supports only this record's `fortified` half. The
        # afflicted text is Raman verbatim at 3405-3407. A reader following the old citation
        # to check the affliction would land on a sentence about younger brothers and
        # reasonably conclude the affliction had been invented.
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 3351)),
    RuleRecord(
        id="H3.L.12", house=3, signification="siblings", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(3, 12),
        # HTJAH-I:3409-3413. Both paragraphs unconditioned; "gets fortune from marriage"
        # sits inside Raman's own opening list and was cut out into `fortified`.
        general="sorrow through relatives; gets fortune from marriage; seclusion; great ups "
                "and downs; an unscrupulous father; the youngest brother will be a tyrant, "
                "and the native becomes poor on account of him",
        fortified="sorrow through relatives; gets fortune from marriage; seclusion; great "
                  "ups and downs; an unscrupulous father; the youngest brother will be a "
                  "tyrant, and the native becomes poor on account of him",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 3409)),
)
