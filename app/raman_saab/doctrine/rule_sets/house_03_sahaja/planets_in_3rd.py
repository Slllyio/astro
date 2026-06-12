"""House 3 (Sahaja / Bhratru Bhava) — the nine planets in the 3rd house.

Encodes the "Planets in the 3rd House" table from
`docs/raman_saab/methodology/house_03_sahaja.md`; each record cites the first
line of its planet's paragraph (HTJAH-I:3472-3517).
Moved verbatim from the former single-module `house_03_sahaja.py` (Stage-1 split).
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
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
