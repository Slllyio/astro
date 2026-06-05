"""House 3 (Sahaja — siblings/courage) RuleRecords.

Encodes the "Lord of the 3rd in the 12 Houses" table from
`methodology/house_03_sahaja.md`, each row as an evaluable `RuleRecord`
carrying the first HTJAH-I line cited in that row.

Karaka = Mars (Bhratru-Karaka); lord-in-house rules use frame="LAGNA", varga="D1".
Source span: HTJAH-I:3337-3413 (lord-in-house table).
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

    # — Planets in the 3rd House (HTJAH-I:3472-3517) —
    RuleRecord(
        id="H3.P.Sun", house=3, signification="siblings", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Sun", 3),
        fortified="courageous; resourceful, restive, successful mind; Sun in 3rd is 'one of the "
                  "strong points in a horoscope'; with Mercury → highly intelligent; with Jupiter "
                  "→ spiritually strong",
        afflicted="bad for brothers; discredit through letters; if afflicted → ill effects on "
                  "co-borns",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 3472)),
    RuleRecord(
        id="H3.P.Moon", house=3, signification="siblings", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Moon", 3),
        fortified="active-minded; fair wife; good knowledge; fond of travelling; changes in "
                  "occupation; attached to children",
        afflicted="if waning → cruel, miserable, impious, unscrupulous; if afflicted → "
                  "unfavourable for peace of mind; subordinate to wife",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3476)),
    RuleRecord(
        id="H3.P.Mars", house=3, signification="siblings", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Mars", 3),
        fortified="brave; reckless and pioneering; evil effects largely modified if the 3rd is "
                  "Capricorn, Aries or Scorpio",
        afflicted="bad for brothers/sisters; danger and accidents by journeys; unprincipled; "
                  "possible ear defects/deafness; if house further afflicted → suicidal thoughts "
                  "or violent tendencies",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 3481)),
    RuleRecord(
        id="H3.P.Mercury", house=3, signification="siblings", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Mercury", 3),
        fortified="does good for others; sharp mind; fond of reading and study; persistent; "
                  "tactful/diplomatic; success in trade/speculation; a number of brothers and "
                  "sisters; gain through 3rd-house affairs",
        afflicted="if afflicted → inclined to nervous breakdown",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 3488)),
    RuleRecord(
        id="H3.P.Jupiter", house=3, signification="siblings", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Jupiter", 3),
        fortified="'a good position'; optimistic, philosophical mind; many good brothers; adapts "
                  "to conventionalities",
        afflicted="becomes a miser; does not love family or children; body heated, ill-health; "
                  "if afflicted → ungrateful, few friends, misses opportunities",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 3495)),
    RuleRecord(
        id="H3.P.Venus", house=3, signification="siblings", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Venus", 3),
        fortified="good mental quality; delight in singing, music, dancing and fine arts; "
                  "brothers will be good",
        afflicted="poor health and low vitality; not financially successful; if afflicted → "
                  "miserly, mean, poor, highly sensual, scandal-prone; little happiness from "
                  "children",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3500)),
    RuleRecord(
        id="H3.P.Saturn", house=3, signification="siblings", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Saturn", 3),
        fortified="brave, courageous, wealthy; honoured by rulers; may head local "
                  "boards/municipalities; protects many; success only after disappointments; "
                  "mind improves with age",
        afflicted="loss of or sorrow through brothers; eccentric, cruel; mind tends to "
                  "gloom/anxiety; if afflicted → despondency may run into mental affliction",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 3505)),
    RuleRecord(
        id="H3.P.Rahu", house=3, signification="siblings", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Rahu", 3),
        fortified="brave for outward appearance; sudden and unexpected news",
        afflicted="generally bad for brothers; may incur severe criticism for his views and ideas",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 3512)),
    RuleRecord(
        id="H3.P.Ketu", house=3, signification="siblings", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Ketu", 3),
        fortified="strong and adventurous",
        afflicted="disturbs the mind with hallucinations; funky disposition",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 3517)),
)
