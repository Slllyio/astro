"""House 10 (Karma — career/profession) — Planets-in-the-10th RuleRecords.

The "Planets in the 10th House" table (HTJAH-II:9813-9908). Moved verbatim
from the former flat ``house_10_karma.py`` during the Stage-4 split.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    RuleRecord(
        id="H10.P.Sun", house=10, signification="career", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Sun", 10),
        # Relocated 2026-09-01: Raman states this flatly for the placement, so it is
        # his GENERAL reading, not a strength branch. Text copied verbatim — this
        # section was ruled unconditioned by the planet_in_house sweep's review, and
        # the mirror also fixes a rendering bug (a lone `afflicted` slot renders
        # NOTHING on a strong-lord chart, because `_branch` returns 'fortified').
        general="successful, strong, happy; sons, vehicles, fame, intelligence, money, "
                "power; government service; ancestral wealth; fond of music; personal "
                "magnetism",
        fortified="successful, strong, happy; sons, vehicles, fame, intelligence, money, "
                  "power; government service; ancestral wealth; fond of music; personal "
                  "magnetism",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9815)),
    RuleRecord(
        id="H10.P.Moon", house=10, signification="career", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Moon", 10),
        # Relocated 2026-09-01: Raman states this flatly for the placement, so it is
        # his GENERAL reading, not a strength branch. Text copied verbatim — this
        # section was ruled unconditioned by the planet_in_house sweep's review, and
        # the mirror also fixes a rendering bug (a lone `afflicted` slot renders
        # NOTHING on a strong-lord chart, because `_branch` returns 'fortified').
        general="religious, wealthy, intelligent, bold; succeeds; corn, ornaments, women; "
                "skilled in arts; helpful, virtuous; Jupiter conjunct → learned in ancient "
                "subjects and astrology; Saturn aspect → dispassionate thinker, earns via "
                "printing/selling books, trustee of religious institutions",
        fortified="religious, wealthy, intelligent, bold; succeeds; corn, ornaments, women; "
                  "skilled in arts; helpful, virtuous; Jupiter conjunct → learned in ancient "
                  "subjects and astrology; Saturn aspect → dispassionate thinker, earns via "
                  "printing/selling books, trustee of religious institutions",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9828)),
    RuleRecord(
        id="H10.P.Mars", house=10, signification="career", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Mars", 10),
        # HTJAH-II:9841-9848. No affliction opener. 9841 ("Other combinations favouring the
        # native may become a cruel ruler") is OCR-garbled; on either parse it is a
        # strength/configuration condition, not an affliction. The conjunction clauses are
        # kept together and labelled, not swept into `general`.
        general="other combinations favouring - the native may become a cruel ruler; fond of "
                "praise and may take bold steps in governing; rash; earns much money",
        fortified="other combinations favouring - the native may become a cruel ruler; fond "
                  "of praise and may take bold steps in governing; rash; earns much money",
        afflicted="(conjunctions, not afflictions) with Mercury → skilled scientist or "
                  "technician patronised by rulers; with Jupiter → head of low-class people; "
                  "with Venus → trader in foreign lands; with Saturn → daring but no progeny",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9841)),
    RuleRecord(
        id="H10.P.Mercury", house=10, signification="career", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Mercury", 10),
        # HTJAH-II:9850-9858, no openers of either kind. Torn at two of Raman's own "but"s:
        # "He will have defective eyesight BUT profound knowledge in astronomy and
        # mathematics" (9853-9854), and "If Jupiter, he will be unhappy, and childless BUT
        # move in prominent circles of the government" (9855-9856) — each sentence split
        # across both slots by valence.
        general="happy and straightforward; a scholar in many subjects, engaged in acquiring "
                "more knowledge and fame; successful in all endeavours; defective eyesight "
                "but profound knowledge in astronomy and mathematics",
        fortified="happy and straightforward; a scholar in many subjects, engaged in "
                  "acquiring more knowledge and fame; successful in all endeavours; "
                  "defective eyesight but profound knowledge in astronomy and mathematics",
        afflicted="(conjunctions, not afflictions) with Venus → a charming wife and wealth; "
                  "with Jupiter → unhappy and childless, but moves in prominent circles of "
                  "the government; with Saturn → toil as a copyist or proofreader, penury",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9850)),
    RuleRecord(
        id="H10.P.Jupiter", house=10, signification="career", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Jupiter", 10),
        fortified="high government official; rich, virtuous, steadfast in spiritual life, "
                  "wise, guided by high principles; Venus conjunct → esteemed by government, "
                  "protects learned and Brahmins; Mars aspect → heads research/academic/"
                  "educational institutes",
        # The whole slot is one CONJUNCTION clause (9865-9870, "If he is with Rahu, he
        # becomes a mischief-maker"), not a strength condition — it must not be swept into
        # `general`, but nor may it stay unlabelled, because `_branch` fires it for a
        # strength-weak Jupiter in a chart with no Rahu involved at all.
        general="a high official in the government; rich, virtuous, steadfast in his "
                "spiritual or religious life, wise and happy, guided by high principles",
        afflicted="(a conjunction, not an affliction) with Rahu → a mischief-maker who "
                  "creates trouble for others at every step",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9860)),
    RuleRecord(
        id="H10.P.Venus", house=10, signification="career", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Venus", 10),
        # Relocated 2026-09-01: Raman states this flatly for the placement, so it is
        # his GENERAL reading, not a strength branch. Text copied verbatim — this
        # section was ruled unconditioned by the planet_in_house sweep's review, and
        # the mirror also fixes a rendering bug (a lone `afflicted` slot renders
        # NOTHING on a strong-lord chart, because `_branch` returns 'fortified').
        general="earns through houses/buildings; influential, many women working for him; "
                "social, friendly, renowned; Saturn conjunct → profits from cosmetics/"
                "women's articles, healing powers, skilled trader, respects divine people",
        fortified="earns through houses/buildings; influential, many women working for him; "
                  "social, friendly, renowned; Saturn conjunct → profits from cosmetics/"
                  "women's articles, healing powers, skilled trader, respects divine people",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 9873)),
    RuleRecord(
        id="H10.P.Saturn", house=10, signification="career", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Saturn", 10),
        fortified="ruler/minister; agriculturist; brave, rich, famous; dispassionate; works "
                  "for downtrodden; judge; visits shrines, later ascetic",
        # HTJAH-II:9881-9892. "His career will be marked by sudden elevations and
        # depressions" (9886-9887) is unconditioned, sitting in the same run of declaratives
        # as "becomes a ruler or minister". The retained clause is the nearest thing to an
        # affliction condition anywhere in the H10 table, but it is strictly a configuration
        # (8th-lord association + malefic navamsa), so it is labelled rather than asserted.
        general="his career will be marked by sudden elevations and depressions",
        afflicted="(a configuration, not an affliction) Saturn associated with the 8th lord "
                  "in a malefic Navamsa → suffers under a tyrannical superior officer",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 9881)),
    RuleRecord(
        id="H10.P.Rahu", house=10, signification="career", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Rahu", 10),
        # HTJAH-II:9894-9898 is a single unconditioned paragraph with ZERO conditionals of
        # any kind, cut in two by valence — including mid-sentence at 9897-9898, "Bold and
        # somewhat adventurous he commits many sins".
        general="tendency to lust after widows; a skilled artist with a flair for poetry and "
                "literature; travels widely and is learned; famous and engages himself in "
                "business; limited issues; bold and somewhat adventurous, commits many sins",
        fortified="tendency to lust after widows; a skilled artist with a flair for poetry "
                  "and literature; travels widely and is learned; famous and engages himself "
                  "in business; limited issues; bold and somewhat adventurous, commits many "
                  "sins",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 9894)),
    RuleRecord(
        id="H10.P.Ketu", house=10, signification="career", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Ketu", 10),
        fortified="if beneficially disposed → happy, religious, well-read in scriptures, "
                  "pilgrim-visits",
        # HTJAH-II:9900-9908. Raman gives exactly ONE fortification opener in the whole
        # 96-line table and it is here — "If beneficially disposed, the native will be happy,
        # religious, well read in the scriptures..." (9902-9903) — which the encoder used
        # correctly, and then dumped the base reading into `afflicted`. Also restores
        # "well-known" (9900-9901) and drops "in deceit", which is the encoder's gloss:
        # Raman writes only "He will be very clever." (9902).
        general="strong, bold and well-known; commits vile deeds and is impure in his "
                "resolves; faces many obstacles in all his undertakings; very clever",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 9900)),
)
