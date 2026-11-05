"""Ari / Roga Bhava (enemies / disease / debts / accidents) — Planets-in-the-house RuleRecords.

Moved verbatim from the former flat ``house_06_ari.py`` (Stage-4 split)."""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    # — Planets in the 6th House (HTJAH-I:6115–6157) —
    RuleRecord(
        id="H6.P.Sun", house=6, signification="enemies_disease", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Sun", 6),
        # ★ CROSS-HOUSE TRANSPLANT REMOVED 2026-09-01. This slot ended with "with Mercury →
        # handles Govt trouble well". Raman makes no such statement about Mercury joining the
        # Sun in the SIXTH — not at the cited 6115-6118, not in the 6th-house modifier
        # paragraph (6159-6185), not in the pre-table combinations (6072-6111). The sentence
        # exists at HTJAH-I:8218-8219, inside the paragraph headed "These results are
        # modified by the aspects and associations received by the planet in the 7TH HOUSE".
        # It is a seventh-house reading grafted onto a sixth-house placement. The SAME
        # sentence was independently found grafted onto H3.P.Sun (with its subject reassigned
        # there as well), so this is one passage transplanted twice.
        # SPLIT. HTJAH-I:6115-6118 + 6163-6170. Raman labels branches inline here, so the
        # afflicted clauses are genuine and stay; only the unconditioned lead moves.
        general="the person becomes a good politician, famous and successful; not very good "
                "for health",
        fortified="the Sun fortified -> administrative ability, few enemies, wealthy",
        afflicted="the Sun afflicted -> a long and troublesome illness; affliction by Saturn "
                  "-> heart trouble and chest pain, unless relieved by Jupiter's aspect",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6115)),
    RuleRecord(
        id="H6.P.Moon", house=6, signification="enemies_disease", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Moon", 6),
        # SPLIT. 6124 ('success as a caterer') is unconditioned and sat in fortified. The
        # FIXED-SIGN clause is a sign-modality condition, not an affliction; its neighbour
        # ('common sign AFFLICTED -> lung danger') is genuinely affliction-conditioned.
        general="indicates Balarishta, or much ill-health during early childhood; ability and "
                "success in subordinate positions; success as a caterer; (a sign modality, not "
                "an affliction) in a fixed sign -> stone in the bladder, submissive to women, "
                "stomach troubles",
        fortified="the Moon fortified, that is well disposed -> the ill-health of childhood is "
                  "moderated",
        afflicted="affliction by Mars and Saturn -> curious incurable diseases and revengeful "
                  "enemies; afflicted in a common sign -> danger to the lungs; (a conjunction) "
                  "with Rahu or Ketu -> mental derangement",
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-I", 6120)),
    RuleRecord(
        id="H6.P.Mars", house=6, signification="enemies_disease", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Mars", 6),
        # SPLIT. 'He will have worries from near relatives' is unconditioned and sat in the
        # afflicted slot; the conjunction clauses are kept and labelled.
        general="highly passionate, victorious and successful as a ruler or politician; "
                "worries from near relatives",
        fortified="Mars well-disposed is an asset",
        afflicted="Mars afflicted -> accidents, losses and troubles through employees; if "
                  "Saturn is the afflicting planet -> death by operation or animal injury; if "
                  "Rahu afflicts -> suicide; if Ketu -> poisoning; Saturn afflicting Mars -> "
                  "litigation with brothers and cousins",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6126)),
    RuleRecord(
        id="H6.P.Mercury", house=6, signification="enemies_disease", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Mercury", 6),
        # LEAVE the afflicted slot (6175-6177 is genuine). Mirror defect only: the base
        # reading sat in fortified, and 'lazy, harsh in speech' was dropped from Raman's
        # sentence 'The person will be lazy, harsh in speech, but nevertheless, a terror to
        # his enemies' (6135-6136) - restored.
        general="lazy and harsh in speech, but nevertheless a terror to his enemies; sharp "
                "intellect; quarrelsome and showy yet respected; interrupted education; a "
                "tendency to poor health",
        fortified="Mercury fortified -> the intellect tells; and (a conjunction, not "
                  "fortification) with Jupiter -> spiritual gains",
        afflicted="Mercury afflicted -> mental troubles and nervous breakdown; afflicted by "
                  "Mars and Rahu, or Saturn and Rahu -> insanity through excitement, and "
                  "servant troubles; afflicted by Rahu, Ketu or Saturn -> despondency and "
                  "abnormal behaviour",
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 6131)),
    RuleRecord(
        id="H6.P.Jupiter", house=6, signification="enemies_disease", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Jupiter", 6),
        # SENTIMENT-SPLIT. 6138-6139 is ONE unconditioned comma-list - 'Inactive, suffers
        # disrespect, indulges in black magic, feared by enemies, unlucky, dyspeptic,
        # health generally good' - cut by valence, two items to fortified and five to
        # afflicted. Raman gives Jupiter-in-6th NO fortification branch anywhere.
        general="inactive, suffers disrespect, indulges in black magic, feared by enemies, "
                "unlucky, dyspeptic, health generally good",
        fortified=None,
        afflicted="Jupiter afflicted -> health suffers through over-indulgence; hardships and "
                  "intemperance in food habits",
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 6138)),
    RuleRecord(
        id="H6.P.Venus", house=6, signification="enemies_disease", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Venus", 6),
        # SENTIMENT-SPLIT. 6141 is ONE unconditioned list - 'No enemies, corrupted by young
        # women, favourable for getting favours from women' - items 1 and 3 to fortified,
        # item 2 to afflicted. Restores 'fond of other women' (6142), dropped.
        general="no enemies; corrupted by young women; favourable for getting favours from "
                "women",
        fortified="Venus well placed -> success in nursing, films or drama",
        afflicted="Venus afflicted -> health affected by too much sexual indulgence, fond of "
                  "other women and licentious; urinary and sexual troubles",
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 6141)),
    RuleRecord(
        id="H6.P.Saturn", house=6, signification="enemies_disease", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Saturn", 6),
        # LEAVE the afflicted slot (6179-6180 is genuine). Mirror defect only: 6145's
        # unconditioned list - 'quarrelsome, obstinate, voracious eater, foeless,
        # courageous' - sat entire in fortified, negatives included.
        general="quarrelsome and obstinate, a voracious eater, foeless and courageous",
        fortified="Saturn well-aspected -> gains through contract, mining and masonry",
        afflicted="Saturn afflicted -> sickness through privation or neglect, and subordinate "
                  "troubles; if Mars is the afflicting planet -> dangerous illness and "
                  "operations; if Rahu afflicts -> hysteria; incurable or undiagnosable "
                  "psychic conditions",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6145)),
    RuleRecord(
        id="H6.P.Rahu", house=6, signification="enemies_disease", group="planet_in_house",
        # 2026-10-28 rule-defect review (docs/raman_saab/research/rule_defects_review2_2026-10-28.json): cite, cite 6181.
        kind="evaluable", condition=C.InRashiHouse("Rahu", 6),
        # SENTIMENT-SPLIT. 6150 is ONE unconditioned sentence - 'Long-lived and wealthy,
        # troubled by enemies, ghosts and diseases in private parts' - cut in half. Raman
        # gives Rahu-in-6th no fortification branch. Restores his relief rider 'unless
        # there is relief by benefic associations or aspects' (6183), which was dropped.
        general="long-lived and wealthy, troubled by enemies, ghosts and diseases in the "
                "private parts; many cousins; puzzling sickness; a scandalous private life; "
                "between Rahu and Ketu, the latter's position is to be preferred in the 6th",
        fortified=None,
        afflicted="Rahu's affliction -> huge debts, unexpected enmities and incurable "
                  "diseases, unless there is relief by benefic associations or aspects; (a "
                  "conjunction) the Moon and Saturn joining Rahu -> mental derangement and a "
                  "psychological misfit",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6181)),
    RuleRecord(
        id="H6.P.Ketu", house=6, signification="enemies_disease", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Ketu", 6),
        # ★ INVERSION FIXED 2026-09-01. HTJAH-I:6155-6157 contains ZERO conditionals, and
        # Raman explicitly insists the negative holds DESPITE the good: "The best position
        # for Ketu to occupy in a horoscope. The person will have fame and authority. He will
        # be foeless. NEVERTHELESS his moral character will be loose. The position also
        # confers intuitive and occult powers." Conditioning "moral character loose" on
        # affliction means a fortified chart never sees it — the precise inverse of what
        # "Nevertheless" asserts.
        general="the best position for Ketu to occupy in a horoscope; the person will have "
                "fame and authority; he will be foeless; nevertheless his moral character "
                "will be loose; the position also confers intuitive and occult powers",
        fortified="the best position for Ketu to occupy in a horoscope; the person will have "
                  "fame and authority; he will be foeless; nevertheless his moral character "
                  "will be loose; the position also confers intuitive and occult powers",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 6155)),
)
