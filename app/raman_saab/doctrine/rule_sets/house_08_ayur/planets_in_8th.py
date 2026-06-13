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
        kind="evaluable", condition=C.InRashiHouse("Sun", 8),
        fortified="exalted → long life, charming, eloquent; with 8th or 11th lord → "
                  "sudden speculation gain",
        afflicted="face/head sores, weak eyes, penury; limited (mostly male) progeny; "
                  "Sun-8th + Moon/Rahu-12th + Saturn-trine → dental trouble",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3483)),
    RuleRecord(
        id="H8.P.Moon", house=8, signification="longevity", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Moon", 8),
        fortified="acquires possessions easily through legacies or inheritance",
        afflicted="mental aberration, psychological complexes, capricious, unhealthy; "
                  "may lose mother in infancy; slender build, weak eyesight; fond of "
                  "fighting; with Mars+Saturn conjunct → eyesight afflicted",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3498)),
    RuleRecord(
        id="H8.P.Mars", house=8, signification="longevity", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Mars", 8),
        fortified=None,
        afflicted="short-lived unless alleviators present; loss of spouse; few children; "
                  "extramarital relations, hates relatives, blood complaints (piles); "
                  "Mars-8th + fixed Lagna + Venus-9th + Moon-7th + Jupiter as 2nd lord "
                  "→ life of servitude",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3510)),
    RuleRecord(
        id="H8.P.Mercury", house=8, signification="longevity", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Mercury", 8),
        fortified="good qualities, well-bred, courteous; inherits and earns much wealth; "
                  "learned, famous; long life though weak constitution",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 3523)),
    RuleRecord(
        id="H8.P.Jupiter", house=8, signification="longevity", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Jupiter", 8),
        fortified="long life; generous; painless death",
        afflicted="unhappy; speech difficulty; ignoble deeds under noble pretence; "
                  "widow liaisons; colitis; debilitated + Moon-4th → a menial, always "
                  "ordered about",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 3531)),
    RuleRecord(
        id="H8.P.Venus", house=8, signification="longevity", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Venus", 8),
        fortified="much wealth, life of comfort and conveniences; exalted → great wealth",
        afflicted="mother in danger; early emotional disappointment → piety later; "
                  "debilitated/saturnine-Navamsa + Saturn aspect → subordination, "
                  "drudgery with mother",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 3539)),
    RuleRecord(
        id="H8.P.Saturn", house=8, signification="longevity", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Saturn", 8),
        fortified="good longevity; perseveres against odds",
        afflicted="many responsibilities; defective eyes; few children; paunch; women "
                  "outside caste; asthma/consumption/lung disease; afflicted → children "
                  "cause grief, dishonest and cruel; with Mars + Rahu-Lagna + "
                  "Gulika-trine → generative-organ disease; with Moon → flatulence, spleen",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 3550)),
    RuleRecord(
        id="H8.P.Rahu", house=8, signification="longevity", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Rahu", 8),
        fortified=None,
        afflicted="public censure, humiliation; many ailments; vicious, quarrelsome, "
                  "unscrupulous; Moon with malefic + Rahu in 8th/12th/5th → mental "
                  "disorders",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3568)),
    RuleRecord(
        id="H8.P.Ketu", house=8, signification="longevity", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Ketu", 8),
        fortified="aspected by benefic → much wealth, long life",
        afflicted="covets others' wealth and women; excretory-system disease; profligacy "
                  "diseases",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 3574)),
)
