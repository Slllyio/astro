"""House 8 (Ayur / Randhra / Mrityu Bhava) — Planets-in-the-8th RuleRecords.

Encodes the "Planets in the 8th House" table from ``house_08_ayur.md``
(HTJAH-II:3483–3578), carrying the real corpus ``Citation``. Moved verbatim
from the former flat ``house_08_ayur.py`` during the Stage-4 subpackage split.

General: "The 8th house rules suffering and afflictions here cause chronic or
incurable bodily or mental diseases." ``HTJAH-II:3580-3581``.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    # — Planets in the 8th House (HTJAH-II:3483–3578) —
    RuleRecord(
        id="H8.P.Sun", house=8, signification="longevity", group="planet_in_house",
        # 2026-10-28 rule-defect review (docs/raman_saab/research/rule_defects_review2_2026-10-28.json): descriptive, cite 3485.
        kind="descriptive", condition=C.InRashiHouse("Sun", 8),
        # SPLIT. The affliction scope runs 3485-3491 and ends at the configuration sentence;
        # 'He will have limited progeny, mostly male' (3492-3493) then stands unconditioned.
        general="limited progeny, mostly male",
        fortified="the Sun in the 8th in exaltation -> lives long, charming and an eloquent "
                  "speaker; (a configuration) with the 8th or 11th lord -> sudden speculation "
                  "gain",
        afflicted="the Sun afflicted -> troubled with sores in the face and head, disgruntled "
                  "in life, weak eyes, penury and an uneventful life; (a configuration) Sun in "
                  "the 8th with the Moon or Rahu in the 12th and Saturn in a trine -> dental "
                  "trouble",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3485)),
    RuleRecord(
        id="H8.P.Moon", house=8, signification="longevity", group="planet_in_house",
        # 2026-10-28 rule-defect review (docs/raman_saab/research/rule_defects_review2_2026-10-28.json): descriptive, cite 3505.
        kind="descriptive", condition=C.InRashiHouse("Moon", 8),
        # SENTIMENT-SPLIT. Zero openers of either kind; one unconditioned block cut so that
        # its only pleasant clause (3502-3503) went to fortified. Restores 'apprehensive',
        # 'amusement', 'large-hearted' and 'excessive perspiration', all dropped.
        general="subject to mental aberration; apprehensive, suffers from psychological "
                "complexes; capricious and unhealthy; may lose his mother in infancy or "
                "boyhood; slender build and weak eyesight; acquires possessions easily through "
                "legacies or inheritance; fond of fighting and amusement and large-hearted; "
                "suffers from excessive perspiration",
        fortified=None,
        afflicted="(a conjunction, not an affliction) Mars and Saturn conjoining -> the "
                  "eyesight is afflicted",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3505)),
    RuleRecord(
        id="H8.P.Mars", house=8, signification="longevity", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Mars", 8),
        # Relocated 2026-09-01: Raman states this flatly for the placement, so it is
        # his GENERAL reading, not a strength branch. Text copied verbatim — this
        # section was ruled unconditioned by the planet_in_house sweep's review, and
        # the mirror also fixes a rendering bug (a lone `afflicted` slot renders
        # NOTHING on a strong-lord chart, because `_branch` returns 'fortified').
        general="short-lived unless alleviators present; loss of spouse; few children; "
                "extramarital relations, hates relatives, blood complaints (piles); "
                "Mars-8th + fixed Lagna + Venus-9th + Moon-7th + Jupiter as 2nd lord "
                "→ life of servitude",
        fortified="short-lived unless alleviators present; loss of spouse; few children; "
                  "extramarital relations, hates relatives, blood complaints (piles); "
                  "Mars-8th + fixed Lagna + Venus-9th + Moon-7th + Jupiter as 2nd lord "
                  "→ life of servitude",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3510)),
    RuleRecord(
        id="H8.P.Mercury", house=8, signification="longevity", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Mercury", 8),
        # Relocated 2026-09-01: Raman states this flatly for the placement, so it is
        # his GENERAL reading, not a strength branch. Text copied verbatim — this
        # section was ruled unconditioned by the planet_in_house sweep's review, and
        # the mirror also fixes a rendering bug (a lone `afflicted` slot renders
        # NOTHING on a strong-lord chart, because `_branch` returns 'fortified').
        general="good qualities, well-bred, courteous; inherits and earns much wealth; "
                "learned, famous; long life though weak constitution",
        fortified="good qualities, well-bred, courteous; inherits and earns much wealth; "
                  "learned, famous; long life though weak constitution",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 3523)),
    RuleRecord(
        id="H8.P.Jupiter", house=8, signification="longevity", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Jupiter", 8),
        # SENTIMENT-SPLIT. Raman's opening sentence IS the split line: 'The native will be
        # UNHAPPY BUT GENEROUS HEARTED' (3531). Restores 'dirty habits'. The debility clause
        # is a debility+configuration branch, not an affliction.
        general="unhappy but generous-hearted; lives long; difficulty in speech; may do "
                "ignoble deeds but pretend to be noble; may have liaisons with widows; dirty "
                "habits and colitis; a painless death",
        fortified=None,
        afflicted="(a debility plus configuration, not an affliction) Jupiter debilitated with "
                  "the Moon in the 4th -> a menial, always ordered about",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 3531)),
    RuleRecord(
        id="H8.P.Venus", house=8, signification="longevity", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Venus", 8),
        # SPLIT. Note the old afflicted slot served a FAVOURABLE outcome ('emotional
        # disappointment -> piety') under an afflicted heading. The retained clause is a
        # debility + malefic-aspect condition (3545-3548) - affliction in substance though
        # Raman does not use the word; kept, and labelled as such.
        general="the position gives many blessings: much wealth, a life of comfort and all its "
                "conveniences; the mother may suffer danger; the native may meet with "
                "emotional disappointments early in life and, as a consequence, resort to a "
                "life of piety in later life",
        fortified="Venus exalted in the 8th -> gains much wealth",
        afflicted="Venus debilitated in Rasi or in a saturnine Navamsa and aspected by Saturn "
                  "(affliction in substance, though Raman does not use the word) -> "
                  "subordination and a life of drudgery along with his mother",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 3539)),
    RuleRecord(
        id="H8.P.Saturn", house=8, signification="longevity", group="planet_in_house",
        # 2026-10-28 rule-defect review (docs/raman_saab/research/rule_defects_review2_2026-10-28.json): benefic.
        kind="evaluable", condition=C.InRashiHouse("Saturn", 8),
        # SPLIT, with a sentiment-split nested inside it: 'good longevity BUT many
        # responsibilities' is one sentence that was cut across both slots.
        general="good longevity but many responsibilities in life; discharges his duties "
                "through sheer perseverance against many odds; defective eyes; very few "
                "children; a paunch; inclined to seek the company of women outside his caste; "
                "predisposed to asthma, consumption and lung disorders",
        fortified=None,
        afflicted="Saturn afflicted by malefic planets -> his children cause him pain and "
                  "grief, and the native will be dishonest and cruel; (configurations) with "
                  "Mars and Rahu in Lagna and Gulika in a trine -> generative-organ disease; "
                  "with the Moon -> flatulence and spleen",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 3550)),
    RuleRecord(
        id="H8.P.Rahu", house=8, signification="longevity", group="planet_in_house",
        # 2026-10-28 rule-defect review (docs/raman_saab/research/rule_defects_review2_2026-10-28.json): descriptive.
        kind="descriptive", condition=C.InRashiHouse("Rahu", 8),
        # Relocated 2026-09-01: Raman states this flatly for the placement, so it is
        # his GENERAL reading, not a strength branch. Text copied verbatim — this
        # section was ruled unconditioned by the planet_in_house sweep's review, and
        # the mirror also fixes a rendering bug (a lone `afflicted` slot renders
        # NOTHING on a strong-lord chart, because `_branch` returns 'fortified').
        general="public censure, humiliation; many ailments; vicious, quarrelsome, "
                "unscrupulous; Moon with malefic + Rahu in 8th/12th/5th → mental "
                "disorders",
        fortified="public censure, humiliation; many ailments; vicious, quarrelsome, "
                  "unscrupulous; Moon with malefic + Rahu in 8th/12th/5th → mental "
                  "disorders",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3568)),
    RuleRecord(
        id="H8.P.Ketu", house=8, signification="longevity", group="planet_in_house",
        # 2026-10-28 rule-defect review (docs/raman_saab/research/rule_defects_review2_2026-10-28.json): descriptive, cite 3575.
        kind="descriptive", condition=C.InRashiHouse("Ketu", 8),
        fortified="aspected by benefic → much wealth, long life",
        afflicted="covets others' wealth and women; excretory-system disease; profligacy "
                  "diseases",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3575)),
)
