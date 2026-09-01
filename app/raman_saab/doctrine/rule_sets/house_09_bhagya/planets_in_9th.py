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
        # SPLIT - the one correctly-conditioned entry in the H9 table, contaminated by two
        # unconditioned sentences (7519-7520) themselves cut in half: 'The health will be
        # ordinary AND the native gets little patrimony'.
        general="the health will be ordinary and the native gets little patrimony; ambitious "
                "and enterprising",
        fortified="the Sun NOT afflicted -> a dutiful son, having regard for spiritual "
                  "pursuits",
        afflicted="the Sun afflicted -> may change his faith; displays hostile feelings "
                  "towards his father, lacking respect for elders and spiritual preceptors; "
                  "(configurations) Moon with Sun -> eye troubles; Venus with Sun -> sickness",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7513)),
    RuleRecord(
        id="H9.P.Moon", house=9, signification="fortune", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Moon", 9),
        # ★ INTERPOLATION REMOVED 2026-09-01. The old slot read "Saturn/Mars/Mercury aspect
        # → ruler (MIXED)". Raman's text is unambiguously favourable and carries no hedge:
        # "If Saturn, Mars and Mercury aspect the Moon, the native will become a ruler"
        # (HTJAH-II:7524-7525). The "(mixed)" qualifier is the encoder's, and filing a plain
        # favourable result under an "afflicted" heading inverts its direction.
        #
        # All four clauses here are CONJUNCTION or ASPECT conditions, not afflictions —
        # HTJAH-II:7522-7534 contains zero openers of either strength kind — so the slot is
        # relabelled rather than swept into `general`. The base reading, unconditioned, was
        # sitting in `fortified`.
        general="fortunate and prosperous; many sons, friends and kinsmen; principled and "
                "generous-minded; may build charitable institutions; acquires good immovable "
                "property and visits foreign countries",
        fortified="fortunate and prosperous; many sons, friends and kinsmen; principled and "
                  "generous-minded; may build charitable institutions; acquires good "
                  "immovable property and visits foreign countries",
        afflicted="(aspects and conjunctions, not afflictions) Saturn, Mars and Mercury "
                  "aspecting the Moon → the native becomes a RULER; Moon with Mars → fatal "
                  "injury to the mother; Venus with the Moon → immoral life, leagued with a "
                  "step-mother; Saturn here → much suffering",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7522)),
    RuleRecord(
        id="H9.P.Mars", house=9, signification="fortune", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Mars", 9),
        # SENTIMENT-SPLIT, twice. 'He will NOT BE A DUTIFUL SON BUT OTHERWISE GENEROUS and
        # famous for his good qualities' (7537-7538) was cut across both slots; and Raman's
        # configuration clause 'Venus here gives two wives and foreign residence, IT ALSO
        # GIVES the native proficiency in law' (7540-7541) was cut in half, its two halves
        # landing under opposite conditions. Rejoined. Restores 'impetuous' (7544).
        general="wields authority and is affluent; has children and is happy; not a dutiful "
                "son, but otherwise generous and famous for his good qualities",
        fortified=None,
        afflicted="(conjunctions, not afflictions) with Jupiter or Mercury -> learned in "
                  "religion and spiritual lore; with Venus -> two wives and foreign residence, "
                  "and also proficiency in law; Saturn with Mars -> addiction to other women, "
                  "wicked, self-seeking, stubborn and impetuous",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 7536)),
    RuleRecord(
        id="H9.P.Mercury", house=9, signification="fortune", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Mercury", 9),
        # Relocated 2026-09-01: Raman states this flatly for the placement, so it is
        # his GENERAL reading, not a strength branch. Text copied verbatim — this
        # section was ruled unconditioned by the planet_in_house sweep's review, and
        # the mirror also fixes a rendering bug (a lone `afflicted` slot renders
        # NOTHING on a strong-lord chart, because `_branch` returns 'fortified').
        general="much education and wealth; great scholar; theosophy/metaphysics; scientific "
                "mind; friendly relations with father; Venus → music and pleasure; "
                "Jupiter → wit and wisdom, lectures abroad on invitation",
        fortified="much education and wealth; great scholar; theosophy/metaphysics; scientific "
                  "mind; friendly relations with father; Venus → music and pleasure; "
                  "Jupiter → wit and wisdom, lectures abroad on invitation",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7546)),
    RuleRecord(
        id="H9.P.Jupiter", house=9, signification="fortune", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Jupiter", 9),
        # The whole afflicted slot is ONE configuration (7558-7559, 'if the Sun and Venus
        # join Jupiter'). The benefic-aspect clause in fortified is genuine and stays.
        general="may become an exponent of law, philosophy and the like; fond of his brothers; "
                "may visit foreign lands as a lecturer or preacher; conservative and "
                "principled",
        fortified="Jupiter aspected by benefic planets -> acquires much immovable property; "
                  "(configurations) with the Moon and Mars -> a great military leader; "
                  "Saturn's benefic aspect -> austerity and striving for divine communion",
        afflicted="(a conjunction, not an affliction) the Sun and Venus joining Jupiter -> "
                  "characterless",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7554)),
    RuleRecord(
        id="H9.P.Venus", house=9, signification="fortune", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Venus", 9),
        # Configuration-only afflicted slot. Raman's clause 'The Sun with Venus makes one
        # suave and polished in speech BUT one may suffer from many physical complaints'
        # (7568-7569) had its halves in opposite slots; rejoined here.
        general="born fortunate and endowed with fame, learning, children, wife and generally "
                "every kind of happiness",
        fortified="(configurations, not fortification) the Sun with Venus -> suave and "
                  "polished in speech, but may suffer from many physical complaints; Venus "
                  "with Saturn -> a diplomat or in government service, with balanced views",
        afflicted="(conjunctions, not afflictions) Venus with the Sun and Moon -> quarrels "
                  "with women and loss of money; the Sun, Saturn and Venus together -> "
                  "criminal tendencies, possible conviction, a libertine",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 7566)),
    RuleRecord(
        id="H9.P.Saturn", house=9, signification="fortune", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Saturn", 9),
        # SENTIMENT-SPLIT. 'THRIFTY IN DOMESTIC LIFE, SOMEWHAT IRRELIGIOUS, he may become a
        # founder of charitable institutions' (7584-7586) is one sentence of three clauses,
        # split two-to-fortified and one-to-afflicted; and 7579-7580 was split the same way.
        general="leads a lonely life and may not marry; well known for his valour on the "
                "battle field; thrifty in domestic life, somewhat irreligious, he may become a "
                "founder of charitable institutions",
        fortified=None,
        afflicted="(conjunctions, not afflictions) the Sun with Saturn -> conflicts with "
                  "father and children, and stomach growths or lumps; Mercury with Saturn -> "
                  "untruthful and deceitful although wealthy",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7579)),
    RuleRecord(
        id="H9.P.Rahu", house=9, signification="fortune", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Rahu", 9),
        # SENTIMENT-SPLIT. Raman's own adversative 'BUT he may become famous and acquire
        # much wealth' (7591-7592) was used as the slot boundary.
        general="a nagging and domineering wife; impolite and miserly; suffering from "
                "emaciation and generally inclined to be of loose morals; hates his father and "
                "reviles God and religion; but he may become famous and acquire much wealth",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7588)),
    RuleRecord(
        id="H9.P.Ketu", house=9, signification="fortune", group="planet_in_house", kind="evaluable",
        condition=C.InRashiHouse("Ketu", 9),
        # SENTIMENT-SPLIT, the most flagrant of the twenty in this batch: all four of
        # Raman's sentences hinge on an internal 'but' or 'however', and EVERY one of those
        # hinges became the fortified/afflicted boundary.
        general="short-tempered and may get upset over trifles; eloquent, but employs this "
                "ability to scandalise others; fond of pomp and show, haughty and arrogant, he "
                "will however be valorous; often treating his parents badly and generally "
                "hostile towards them, he will be short-sighted but save much money through "
                "frugal living; he will have a good wife and children",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 7594)),
)
