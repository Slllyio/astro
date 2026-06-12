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
        afflicted="earns livelihood by self-exertion; vindictive, lean & tall, brave, sickly, "
                  "serving others",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3337)),
    RuleRecord(
        id="H3.L.2", house=3, signification="siblings", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(3, 2),
        fortified="results mitigated only by other favourable combinations in the chart",
        afflicted="unscrupulous; preys on others' women and wealth; mean deeds; devoid of "
                  "happiness; likely to lose younger brothers",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 3343)),
    RuleRecord(
        id="H3.L.3", house=3, signification="siblings", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(3, 3),
        fortified="brave; surrounded by friends and relatives; good children; wealthy, happy, "
                  "contented; in 3rd/6th/11th → many younger brothers",
        afflicted="if 3rd lord is Mars → loses all younger brothers; Saturn similarly; "
                  "Sun here kills elder brothers",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3348)),
    RuleRecord(
        id="H3.L.4", house=3, signification="siblings", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(3, 4),
        fortified="rich and learned; happy life; if well-fortified and Lagna+9th lords weak → "
                  "brothers survive him; step-brothers if 9th lord strong",
        afflicted="wife cruel-hearted and mean; Mars weak → loses lands, lives in others' "
                  "houses (minimised if 3rd is beneficially disposed)",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3356)),
    RuleRecord(
        id="H3.L.5", house=3, signification="siblings", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(3, 5),
        fortified="highly benefited by brothers; large-scale agriculture; adopted by a rich "
                  "family; shines in government service; financially well off",
        afflicted="little pleasure from children; friction in domestic life",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 3364)),
    RuleRecord(
        id="H3.L.6", house=3, signification="siblings", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(3, 6),
        fortified="younger brother joins Army; one brother becomes a successful physician; "
                  "if 6th lord also in 3rd → sportsman/athlete; becomes rich",
        afflicted="hates brothers and relatives; difficulty through them; maternal relatives "
                  "suffer; accepts illegal gratifications; both 6th and 3rd afflicted → "
                  "diseases, enemies, deceitful",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3371)),
    RuleRecord(
        id="H3.L.7", house=3, signification="siblings", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(3, 7),
        fortified="cordial feelings between brothers; if 7th lord in Lagna → a brother settles "
                  "abroad and helps native",
        afflicted="displeasure of rulers; vicissitudes; suffering in childhood; unfortunate "
                  "union; danger while travelling",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3379)),
    RuleRecord(
        id="H3.L.8", house=3, signification="siblings", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(3, 8),
        fortified="no specifically favourable variant given for this placement",
        afflicted="serious or dangerous disease and loss of younger brother; criminal case or "
                  "false accusation; trouble via death and bequests; unfortunate marriage; "
                  "rough career",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 3388)),
    RuleRecord(
        id="H3.L.9", house=3, signification="siblings", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(3, 9),
        fortified="brother inherits ancestral property; native benefited by brother; fortune "
                  "improves after marriage",
        afflicted="misunderstandings with father; father untrustworthy",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 3394)),
    RuleRecord(
        id="H3.L.10", house=3, signification="siblings", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(3, 10),
        fortified="native rich, happy, intelligent; all brothers shine and help him; gain from "
                  "journeys connected with profession",
        afflicted="quarrelsome and faithless wife",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 3399)),
    RuleRecord(
        id="H3.L.11", house=3, signification="siblings", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(3, 11),
        fortified="a number of younger brothers when 3rd lord is in 3rd, 6th or 11th",
        afflicted="not a very good combination; earnings with effort; vindictive; "
                  "unattractive or emaciated body; subservient and dependent; frequent illness",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 3351)),
    RuleRecord(
        id="H3.L.12", house=3, signification="siblings", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(3, 12),
        fortified="gets fortune from marriage",
        afflicted="sorrow through relatives; seclusion; great ups and downs; unscrupulous "
                  "father; youngest brother a tyrant → native becomes poor on his account",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 3409)),
)
