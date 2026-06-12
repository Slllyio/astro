"""House 1 (Tanu Bhava / Lagna) — the nine planets in the 1st house.

Source span: HTJAH-I:1499-1562; each record cites the first line of its planet's
paragraph. Moved verbatim from the former single-module `house_01_lagna.py`
(Stage-1 split).
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    RuleRecord(
        id="H1.P.Sun", house=1, signification="self", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Sun", 1),
        fortified="strong moral nature, righteous, ambition and love of power; good health and "
                  "vitality; cheerful, optimistic, popular; adds respect and lofty motives to "
                  "the personality",
        afflicted="if with Saturn or Mars: scars, hot constitution, impure blood, itches, "
                  "fevers, inflammations, eye affections",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 1499)),
    RuleRecord(
        id="H1.P.Moon", house=1, signification="self", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Moon", 1),
        fortified="fanciful, romantic, moderate eater; restless but easy-going; changeable "
                  "fortune; idealist, great traveller/explorer; sociable; succeeds in "
                  "mass-contact professions",
        afflicted="with Saturn: mind always worried; with Mars: menstrual disorders (women); "
                  "with Rahu: hysterical tendencies; with Jupiter: mind elevated",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 1505)),
    RuleRecord(
        id="H1.P.Mars", house=1, signification="self", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Mars", 1),
        fortified="hot constitution, courage, self-confidence, enterprise, practical ability, "
                  "love of liberty; handsome; aspects should be carefully examined",
        afflicted="reckless, rash; body has scars; domestic life unhappy; prone to accidents; "
                  "cuts and burns likely",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 1511)),
    RuleRecord(
        id="H1.P.Mercury", house=1, signification="self", group="planet_in_house",
        kind="evaluable",
        condition=C.InRashiHouse("Mercury", 1),
        fortified="humorous, quick wit, mental ingenuity, well-read (especially occult), "
                  "adaptable, intellectual; in good aspect to Venus: musical and talented",
        afflicted="with Rahu or Ketu in Lagna: much nervous trouble",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 1519)),
    RuleRecord(
        id="H1.P.Jupiter", house=1, signification="self", group="planet_in_house",
        kind="evaluable",
        condition=C.InRashiHouse("Jupiter", 1),
        fortified="magnetic personality, optimistic, jovial, pleasant manners; more sons if 5th "
                  "unafflicted; lawyers/professors/writers/theologians; influential leader",
        afflicted="self-indulgence/gluttony affects health; with Rahu: sins committed, body "
                  "corpulent; diseases from impure blood",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 1525)),
    RuleRecord(
        id="H1.P.Venus", house=1, signification="self", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Venus", 1),
        fortified="fortunate (more so if Capricorn or Aquarius ascending); amiable, cheerful, "
                  "emotional; art appreciation; fond of music/drama/singing; admired by opposite "
                  "sex; magnetic personality; early marriage possible",
        afflicted="discord in married life",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 1532)),
    RuleRecord(
        id="H1.P.Saturn", house=1, signification="self", group="planet_in_house",
        kind="evaluable",
        condition=C.InRashiHouse("Saturn", 1),
        fortified="if unafflicted: consideration for others' welfare; self-confident, morally "
                  "stable; calm, grave, serious; progress slow but certain",
        afflicted="copies foreign customs; body weak and emaciated; aversion for responsibility; "
                  "inactive habits; loss through negligence; misfortunes in early life; same "
                  "results if ascendant merely aspected by Saturn",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 1541)),
    RuleRecord(
        id="H1.P.Rahu", house=1, signification="self", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Rahu", 1),
        fortified=None,
        afflicted="health generally unsatisfactory (needs non-medical treatment); inclines to "
                  "occult; wilful; hypocritical super-consciousness; odd and eccentric; usually "
                  "bad for marriage; partakes of Saturn's characteristics",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 1553)),
    RuleRecord(
        id="H1.P.Ketu", house=1, signification="self", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Ketu", 1),
        fortified=None,
        afflicted="psychic powers likely; weak constitution, emaciated figure; instability and "
                  "deceitfulness; morbid imagination, strange appetites, excitability, wandering "
                  "disposition; married life unhappy unless other favourable configurations",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 1559)),
)
