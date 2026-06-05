"""House 9 (Bhagya / Dharma / Pitru Bhava) RuleRecords.

Lord of the 9th in the 12 houses, encoded from
`methodology/house_09_bhagya.md`. Each entry is one row of the
"Lord of the 9th in the 12 Houses" table with the corresponding
`HTJAH-II` corpus citation (Vol II, work tag **HTJAH-II**).

Signification = "fortune" (the primary bhagya matter);
father-specific sub-matter and dharma/travel combos are
encoded in separate groups.  Karaka: Jupiter (fortune/dharma),
Sun (father/pitrukaraka).

Source span: HTJAH-II:7301-7394 (lord-in-house table).
Full chapter: HTJAH-II:7283-9426.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    # — 9th lord in the 12 houses (HTJAH-II:7301-7394) —
    RuleRecord(
        id="H9.L.1", house=9, signification="fortune", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(9, 1),
        fortified="self-made man; earns much through own efforts; with Lagna-lord + benefic = "
                  "fortune, riches, happiness",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7301)),
    RuleRecord(
        id="H9.L.2", house=9, signification="fortune", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(9, 2),
        fortified="father rich and influential; native acquires wealth from father",
        afflicted="malefics influencing → ruin/destroy paternal property",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7310)),
    RuleRecord(
        id="H9.L.3", house=9, signification="fortune", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(9, 3),
        fortified="fortune through writing, speeches, oratory; advances via co-borns; "
                  "father of moderate means",
        afflicted="malefics → trouble through irrational/obscene writings; forced to sell "
                  "paternal property",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7316)),
    RuleRecord(
        id="H9.L.4", house=9, signification="fortune", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(9, 4),
        fortified="vast landed property, bungalows; gains via estate/land; rich fortunate mother; "
                  "inherits father's immovables",
        afflicted="hard-hearted father / parental disharmony; early-life misery; "
                  "Rahu → mother divorcee/separated",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7326)),
    RuleRecord(
        id="H9.L.5", house=9, signification="fortune", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(9, 5),
        fortified="prosperous and famous father; sons very fortunate, enjoy success and distinction",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7336)),
    RuleRecord(
        id="H9.L.6", house=9, signification="fortune", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(9, 6),
        fortified="benefics flanking → wealth via father's legal wins, compensation, costs",
        afflicted="sickly father with chronic disease; malefics → fortune frustrated by "
                  "litigation/debts of father",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7340)),
    RuleRecord(
        id="H9.L.7", house=9, signification="fortune", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(9, 7),
        fortified="goes abroad and prospers; father prospers abroad; noble lucky wife; "
                  "ascetic yogas → spiritual fulfilment abroad",
        afflicted="asubhayogas → father dies abroad",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7352)),
    RuleRecord(
        id="H9.L.8", house=9, signification="fortune", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(9, 8),
        fortified="benefics → inherits substantial paternal property",
        afflicted="loses father early; malefics → severe poverty/heavy responsibility; "
                  "abandons traditions, damages religious trusts",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7359)),
    RuleRecord(
        id="H9.L.9", house=9, signification="fortune", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(9, 9),
        fortified="long-lived prosperous father; native religious, charitable; travels abroad, "
                  "earns money and distinction",
        afflicted="malefics, OR 9th lord in 6/8/12 from Navamsa Lagna → father dies early",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7367)),
    RuleRecord(
        id="H9.L.10", house=9, signification="fortune", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(9, 10),
        fortified="very famous and powerful; generous; posts of authority; great wealth, comfort, "
                  "luxury; righteous law-abiding livelihood",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7374)),
    RuleRecord(
        id="H9.L.11", house=9, signification="fortune", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(9, 11),
        fortified="exceedingly rich; powerful influential friends; well-known well-placed father",
        afflicted="unfaithful friends destroy wealth via selfish scheming and fraud",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7380)),
    RuleRecord(
        id="H9.L.12", house=9, signification="fortune", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(9, 12),
        fortified="religious and noble",
        afflicted="poor background; suffers, works hard, success may not come; always in want; "
                  "father dies early leaving native penniless",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7389)),

    # — Planets in the 9th House (HTJAH-II:7513-7603) —
    RuleRecord(
        id="H9.P.Sun", house=9, signification="fortune", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Sun", 9),
        fortified="dutiful son; spiritual; ambitious, enterprising; ordinary health",
        afflicted="changes faith; hostile to father/elders/preceptors; little patrimony; "
                  "Moon+Sun → eye troubles; Venus+Sun → sickness/ailments",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7513)),
    RuleRecord(
        id="H9.P.Moon", house=9, signification="fortune", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Moon", 9),
        fortified="fortunate, prosperous; many sons, friends, kinsmen; principled, generous; "
                  "builds charitable institutions; good immovables; foreign travel",
        afflicted="Saturn/Mars/Mercury aspect → ruler (mixed); Moon+Mars → fatal injury to "
                  "mother; Venus+Moon → immoral life, leagued with step-mother; Saturn here → "
                  "much suffering",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7522)),
    RuleRecord(
        id="H9.P.Mars", house=9, signification="fortune", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Mars", 9),
        fortified="wields authority, affluent; children, happy; generous, famous for good "
                  "qualities; Jupiter/Mercury → learned in religion/spiritual lore; Venus → "
                  "proficiency in law",
        afflicted="not dutiful son; Saturn → addiction to other women, wicked, self-seeking, "
                  "stubborn; Venus → two wives, foreign residence",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7536)),
    RuleRecord(
        id="H9.P.Mercury", house=9, signification="fortune", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Mercury", 9),
        fortified="much education and wealth; great scholar; theosophy/metaphysics; scientific "
                  "mind; friendly relations with father; Venus → music and pleasure; "
                  "Jupiter → wit and wisdom, lectures abroad on invitation",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7546)),
    RuleRecord(
        id="H9.P.Jupiter", house=9, signification="fortune", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Jupiter", 9),
        fortified="exponent of law/philosophy; benefic-aspected → much immovable property; "
                  "fond of brothers; conservative, principled; foreign lecturer/preacher; "
                  "Moon+Mars → great military leader; Saturn (benefic aspect) → austerity, "
                  "strives for divine communion",
        afflicted="Sun+Venus → characterless",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7554)),
    RuleRecord(
        id="H9.P.Venus", house=9, signification="fortune", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Venus", 9),
        fortified="born fortunate; fame, learning, children, wife, every happiness; "
                  "Sun → suave/polished speech; Saturn → diplomat/govt service, balanced views",
        afflicted="Sun → physical complaints; Sun+Moon → quarrels with women, money loss; "
                  "Sun+Saturn → criminal tendencies, possible conviction, libertine",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7566)),
    RuleRecord(
        id="H9.P.Saturn", house=9, signification="fortune", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Saturn", 9),
        fortified="valour on battlefield; thrifty; may found charitable institutions",
        afflicted="lonely life, may not marry; somewhat irreligious; Sun → conflicts with "
                  "father and children, stomach growths/lumps; Mercury → untruthful, deceitful, "
                  "though wealthy",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7579)),
    RuleRecord(
        id="H9.P.Rahu", house=9, signification="fortune", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Rahu", 9),
        fortified="may become famous and wealthy",
        afflicted="nagging domineering wife; impolite, miserly; emaciation; loose morals; "
                  "hates father, reviles God/religion",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7588)),
    RuleRecord(
        id="H9.P.Ketu", house=9, signification="fortune", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Ketu", 9),
        fortified="eloquent; valorous; frugal-saves; good wife and children",
        afflicted="short-tempered; scandalises others; pompous, haughty, arrogant; treats "
                  "parents badly; short-sighted",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7594)),
)
