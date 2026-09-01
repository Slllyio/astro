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
        # HTJAH-II:14453-14455: "clever and rich BUT lustful, will acquire landed
        # Properties" — one sentence, split at the "but". (The gains tail is from Raman's
        # sources-of-gain list at 14377-14381, ~80 lines earlier than the cited spine.)
        general="eloquent and forceful speaker, clever and rich but lustful; acquires landed "
                "properties and wields considerable influence in top circles; income "
                "augmented through factories, litigation, lands and rentals and through "
                "self-exertion",
        fortified="eloquent and forceful speaker, clever and rich but lustful; acquires "
                  "landed properties and wields considerable influence in top circles; "
                  "income augmented through factories, litigation, lands and rentals and "
                  "through self-exertion",
        afflicted=None,
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
        # HTJAH-II:14469-14472: "He will be OF A WANDERING NATURE, will make immense
        # profits..." — the opening clause was cut off its own sentence into `afflicted`.
        general="of a wandering nature; makes immense profits, possessing all kinds of "
                "comforts and luxuries; has a weakness for women and longs for their "
                "company; popular, having many friends; earnings increase through dance, "
                "drama, cinema, fine arts, music and women",
        fortified="of a wandering nature; makes immense profits, possessing all kinds of "
                  "comforts and luxuries; has a weakness for women and longs for their "
                  "company; popular, having many friends; earnings increase through dance, "
                  "drama, cinema, fine arts, music and women",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-II", 14469)),
    RuleRecord(
        id="H11.P.Saturn", house=11, signification="gains", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Saturn", 11),
        # HTJAH-II:14474-14478: "He will have FEW FRIENDS, will be fond of enjoyment and
        # will earn through Government sources." — the middle of a three-part sentence was
        # pulled out into `afflicted`.
        general="earns through employing many men and women; few friends; fond of enjoyment; "
                "earns through Government sources; long and healthy life; involved in "
                "politics, commanding great respect; wealth through industries, labour and "
                "agriculture",
        fortified="earns through employing many men and women; few friends; fond of "
                  "enjoyment; earns through Government sources; long and healthy life; "
                  "involved in politics, commanding great respect; wealth through "
                  "industries, labour and agriculture",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-II", 14474)),
    RuleRecord(
        id="H11.P.Rahu", house=11, signification="gains", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Rahu", 11),
        # HTJAH-II:14480-14484 is ONE sentence; two of its clauses were pulled into
        # `afflicted` from the middle of it.
        general="distinguishes himself in the army or navy; famous, wealthy and learned; few "
                "children; suffers from ear afflictions; earns much wealth in foreign "
                "countries",
        fortified="distinguishes himself in the army or navy; famous, wealthy and learned; "
                  "few children; suffers from ear afflictions; earns much wealth in foreign "
                  "countries",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-II", 14480)),
    RuleRecord(
        id="H11.P.Ketu", house=11, signification="gains", group="planet_in_house",
        kind="evaluable", condition=C.InRashiHouse("Ketu", 11),
        # HTJAH-II:14486-14492. "The native will have the habit of hoarding" is Raman's
        # OPENING sentence for Ketu here, unconditioned — not an afflicted variant.
        general="habit of hoarding; may get a monetary windfall through speculation such as "
                "lottery, horse-racing and the stock exchange; noble and possessed of many "
                "good qualities of head and heart; succeeds in all his ventures; "
                "participates in charitable and similar works of beneficence",
        fortified="habit of hoarding; may get a monetary windfall through speculation such "
                  "as lottery, horse-racing and the stock exchange; noble and possessed of "
                  "many good qualities of head and heart; succeeds in all his ventures; "
                  "participates in charitable and similar works of beneficence",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-II", 14486)),
)
