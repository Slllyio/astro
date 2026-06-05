"""House 11 (Labha / Aya Bhava — gains/income) RuleRecords.

Lord of the 11th in the 12 Houses — baseline placement combinations for the
11th-house significations (gains, elder brothers, friends, acquisitions).

Source span: HTJAH-II:14258–14340 (lord-in-house block).  The verbatim-warning
applies: "These results are very general and must not be applied directly without
weighing other factors." (HTJAH-II:14344–14345).

Karaka for gains = Jupiter (Dhanakaraka, HTJAH-II:15155).
Karaka for elder brothers = Mars (HTJAH-II:14742–14744).
NOTE: the 11th lord carries the worst-functional-malefic flag in Raman's scheme;
that flag is captured in the polarity field as "malefic" for houses where Raman
explicitly marks an affliction reversal risk, and "neutral" / "benefic" where the
fortified result dominates.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    RuleRecord(
        id="H11.L.1", house=11, signification="gains", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(11, 1),
        fortified="born in a rich family (very rich to well-to-do per lord's strength); earns much wealth",
        afflicted="loses an elder brother early in life",
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-II", 14258)),
    RuleRecord(
        id="H11.L.2", house=11, signification="gains", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(11, 2),
        fortified="lives with elder brothers; earns via commercial concerns and banking; "
                  "good profits in business with friends — benefics give harmonious relations",
        afflicted="malefics → domestic bickerings; heavy losses on account of friends",
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-II", 14267)),
    RuleRecord(
        id="H11.L.3", house=11, signification="gains", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(11, 3),
        fortified="concert-singer or musician earning thereby; gain through brothers; "
                  "many friends and helpful neighbours",
        afflicted="afflictions give contrary results",
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-II", 14274)),
    RuleRecord(
        id="H11.L.4", house=11, signification="gains", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(11, 4),
        fortified="profits through landed estates, rentals, products of earth; "
                  "cultured distinguished mother; renowned for learning; comfort, all joys, devoted charming wife",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-II", 14279)),
    RuleRecord(
        id="H11.L.5", house=11, signification="gains", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(11, 5),
        fortified="many children who rise well; gains through speculation; "
                  "if benefic → pious, observes vows enhancing prosperity",
        afflicted="if afflicted → a gambler indulging in foolish ventures",
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-II", 14286)),
    RuleRecord(
        id="H11.L.6", house=11, signification="gains", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(11, 6),
        fortified="gains through maternal relatives, litigation, running nursing-homes",
        afflicted="if afflicted → thrives on setting person against person, others' quarrels, "
                  "anti-social activity; malefics → loss through similar sources",
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-II", 14293)),
    RuleRecord(
        id="H11.L.7", house=11, signification="gains", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(11, 7),
        fortified="if fortified → marries only once, a rich and influential woman; "
                  "prospers in foreign countries",
        afflicted="marries more than once; if afflicted → liaisons with women of ill-repute, "
                  "trading in flesh, immoral activities",
        frame="LAGNA", varga="D1", polarity="neutral",
        source=Citation("HTJAH-II", 14302)),
    RuleRecord(
        id="H11.L.8", house=11, signification="gains", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(11, 8),
        fortified="rich at birth",
        afflicted="though rich at birth, suffers many calamities and loses much money; "
                  "depredations of thieves, cheats and swindlers; if in malefic constellation → forced to beg",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 14309)),
    RuleRecord(
        id="H11.L.9", house=11, signification="gains", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(11, 9),
        fortified="inherits a large paternal fortune; very lucky; many houses, conveyances, luxury; "
                  "religious-minded, charitable, sets up charitable institutions",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-II", 14315)),
    RuleRecord(
        id="H11.L.10", house=11, signification="gains", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(11, 10),
        fortified="prospers in business, good profits; elder brother helps in business; "
                  "earns prize-money for original contributions",
        afflicted="foul means if the planet is malefic",
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-II", 14322)),
    RuleRecord(
        id="H11.L.11", house=11, signification="gains", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(11, 11),
        fortified="many friends and elder brothers who help throughout life; "
                  "happy life with wife, home, children and all comforts",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-II", 14330)),
    RuleRecord(
        id="H11.L.12", house=11, signification="gains", group="lord_in_house",
        kind="evaluable", condition=C.LordIn(11, 12),
        fortified=None,
        afflicted="losses in business; ailing elder brother and heavy expenditure on his illness, "
                  "possibly death of elder brother; pays fines and penalties frequently; "
                  "burdened with domestic responsibilities",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-II", 14335)),

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
