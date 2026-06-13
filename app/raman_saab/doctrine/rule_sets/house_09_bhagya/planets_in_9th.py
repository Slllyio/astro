"""Bhagya / Dharma / Pitru Bhava (father / fortune / dharma / travel) — Planets-in-the-house RuleRecords.

Moved verbatim from the former flat ``house_09_bhagya.py`` (Stage-4 split)."""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
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
