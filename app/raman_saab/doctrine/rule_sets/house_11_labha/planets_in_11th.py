"""Labha / Aya Bhava (gains / friends / elder-siblings) — Planets-in-the-house RuleRecords.

Moved verbatim from the former flat ``house_11_labha.py`` (Stage-4 split)."""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    # — Planets in the 11th House (HTJAH-II:14442–14492) —
    RuleRecord(
        id="H11.P.Sun", house=11, signification="gains", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Sun", 11),
        fortified="long life; wealthy; wife, children, many servants; royal/governmental favours; "
                  "success without much effort; sagacious and principled; gains via inheritance",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-II", 14442)),
    RuleRecord(
        id="H11.P.Moon", house=11, signification="gains", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Moon", 11),
        fortified="noble, generous; riches, wife, children; introspective, quiet; famous; "
                  "good profits in business; vast lands; helped by the fair sex; "
                  "gains via mother, sea-products, pearls, milk, farms, fruit orchards, breweries",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-II", 14447)),
    RuleRecord(
        id="H11.P.Mars", house=11, signification="gains", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Mars", 11),
        fortified="eloquent forceful speaker; clever and rich; acquires landed properties; "
                  "wields influence in top circles; gains via factories, litigation, lands, "
                  "rentals and self-exertion",
        afflicted="lustful tendencies",
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-II", 14453)),
    RuleRecord(
        id="H11.P.Mercury", house=11, signification="gains", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Mercury", 11),
        fortified="learned in many sciences; keen sharp intellect; wealthy, truthful, happy; "
                  "many faithful servants; prospers in engineering; "
                  "gains via teaching, writing, friends or uncles",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-II", 14459)),
    RuleRecord(
        id="H11.P.Jupiter", house=11, signification="gains", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Jupiter", 11),
        fortified="long-lived; bold and wealthy; piercing intellect; renowned; fond of music; "
                  "accumulates riches; many friends; limited issues; "
                  "gains via knowledge (scientific/religious/literary) and well-placed sons",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-II", 14464)),
    RuleRecord(
        id="H11.P.Venus", house=11, signification="gains", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Venus", 11),
        fortified="immense profits, all comforts and luxuries; popular, many friends; "
                  "gains via dance, drama, cinema, fine arts, music and women",
        afflicted="wandering nature; weakness for women, longs for their company",
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-II", 14469)),
    RuleRecord(
        id="H11.P.Saturn", house=11, signification="gains", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Saturn", 11),
        fortified="earns by employing many men and women; fond of enjoyment; earns through "
                  "Government sources; long healthy life; involved in politics, great respect; "
                  "gains via industries, labour and agriculture",
        afflicted="few friends",
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-II", 14474)),
    RuleRecord(
        id="H11.P.Rahu", house=11, signification="gains", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Rahu", 11),
        fortified="distinguishes himself in army or navy; famous, wealthy, learned; "
                  "earns much wealth in foreign countries",
        afflicted="few children; ear afflictions",
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-II", 14480)),
    RuleRecord(
        id="H11.P.Ketu", house=11, signification="gains", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Ketu", 11),
        fortified="monetary windfall via speculation (lottery, horse-racing, stock exchange); "
                  "noble, good qualities; succeeds in all ventures; charitable",
        afflicted="habit of hoarding",
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-II", 14486)),
)
