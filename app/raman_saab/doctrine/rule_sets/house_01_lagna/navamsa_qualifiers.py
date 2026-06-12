"""House 1 — navamsa qualifier rules (#38-#67, HTJAH-I:1709-1789).

The *lord-with-lord + D9-reversal* block: Lagnadhipati conjunct the Nth-house
lord in house N (evaluable), each followed by a D9-reversal qualifier whose
condition requires a dynamically-resolved planet name (G13 gap → descriptive).

Predicate notes
---------------
* LordsConjunct(1, N) — same-rasi conjunction of the D1 lords of houses 1 & N.
* LordIn(1, N)        — lord of house 1 sits in whole-sign house N (D1).
  Together these faithfully encode "Lagnadhipati in the Nth with the Nth lord".
* InVargaHouseFrom / VargaDignity accept a *planet name* as their first
  argument; "LORD_OF:n" is valid only as the *origin* parameter.  Because the
  lord of house 1 is chart-dependent, all conditions that would need
  `InVargaHouseFrom("LORD_OF:1", ...)` or `VargaDignity("LORD_OF:1", ...)`
  as the *subject planet* cannot be expressed with the current predicate
  algebra → kind="descriptive" + TODO comment (G13).

Rule-id scheme: H1.N.<seq>  (N = navamsa_qualifier group, seq is sequential).
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation

RULES: Final[tuple[RuleRecord, ...]] = (

    # ── #38 — Lagnadhipati weak / debilitated / combust ──────────────────────
    # G13: HasDignity and Combust both require a static planet name; the lord of
    # house 1 is chart-dependent. No predicate covers "debil OR combust for
    # dynamically-resolved lord". → descriptive.
    # TODO(G13): encode when a LAGNADHIPATI_WEAK(or_combust) predicate exists.
    RuleRecord(
        id="H1.N.38", house=1, signification="self", group="navamsa_qualifier",
        kind="descriptive",
        condition=None,
        fortified="",
        afflicted="lord of Lagna weak, debilitated or combust → native sickly, "
                  "grotesque in appearance, evil-minded, poor, infamous, serves others",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 1709)),

    # ── #39 — Lord of Lagna in 12th in the Navamsha ──────────────────────────
    # G13: InVargaHouseFrom takes a planet name as subject; the lord of house 1
    # is chart-dependent. → descriptive.
    # TODO(G13): encode as InVargaHouseFrom("LORD_OF:1", "LAGNA", {12}, "D9")
    # once the predicate accepts LORD_OF origins as the subject.
    RuleRecord(
        id="H1.N.39", house=1, signification="self", group="navamsa_qualifier",
        kind="descriptive",
        condition=None,
        fortified="",
        afflicted="lord of Lagna in 12th in Navamsha → always roaming, suffers in "
                  "mind and body",
        frame="LAGNA", varga="D9", polarity="malefic",
        source=Citation("HTJAH-I", 1711)),

    # ── #40 — Lagnadhipati in 2nd with 2nd lord (base) ───────────────────────
    RuleRecord(
        id="H1.N.40", house=1, signification="self", group="navamsa_qualifier",
        kind="evaluable",
        condition=C.And(C.LordIn(1, 2), C.LordsConjunct(1, 2)),
        fortified="acquisition of wealth, silver/gold ware, precious metals and "
                  "stones; succeeds in all attempts; family expands; peaceful, happy time",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 1714)),

    # ── #41 — Qualifier to #40: Lagnadhipati in 6/8/12 in D9 from 2nd lord ──
    # G13: InVargaHouseFrom requires the subject planet by name; LORD_OF:1
    # (Lagnadhipati) is chart-dependent. → descriptive.
    # TODO(G13): encode as InVargaHouseFrom("LORD_OF:1", "LORD_OF:2", {6,8,12}, "D9")
    # once the predicate algebra supports LORD_OF origins as the subject.
    RuleRecord(
        id="H1.N.41", house=1, signification="self", group="navamsa_qualifier",
        kind="descriptive",
        condition=None,
        fortified="",
        afflicted="Lagnadhipati in 6th/8th/12th in Navamsha from sign held by 2nd "
                  "lord → lessening of the #40 effects",
        frame="LAGNA", varga="D9", polarity="malefic",
        source=Citation("HTJAH-I", 1717)),

    # ── #42 — Lagnadhipati in 3rd with 3rd lord, fortified (base) ────────────
    RuleRecord(
        id="H1.N.42", house=1, signification="self", group="navamsa_qualifier",
        kind="evaluable",
        condition=C.And(C.LordIn(1, 3), C.LordsConjunct(1, 3)),
        fortified="birth/prosperity of brothers, mental peace, connection with "
                  "pleasure-loving persons of both sexes",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 1720)),

    # ── #43 — Qualifier to #42: Lagnadhipati in 6/8/12 from 3rd lord in D9 ──
    # G13: same LORD_OF:1 subject-planet gap. → descriptive.
    # TODO(G13): InVargaHouseFrom("LORD_OF:1", "LORD_OF:3", {6,8,12}, "D9")
    RuleRecord(
        id="H1.N.43", house=1, signification="self", group="navamsa_qualifier",
        kind="descriptive",
        condition=None,
        fortified="",
        afflicted="Lagnadhipati in 6th/8th/12th from 3rd lord in Navamsha → "
                  "enmity with brothers or sorrow to them",
        frame="LAGNA", varga="D9", polarity="malefic",
        source=Citation("HTJAH-I", 1725)),

    # ── #44 — Lagnadhipati fortified in 4th with 4th lord (base) ─────────────
    RuleRecord(
        id="H1.N.44", house=1, signification="self", group="navamsa_qualifier",
        kind="evaluable",
        condition=C.And(C.LordIn(1, 4), C.LordsConjunct(1, 4)),
        fortified="vehicles, valuable clothes, cattle, houses and lands, new "
                  "houses, respect from friends/relatives, acquaintance with learned men, "
                  "new friendships",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 1728)),

    # ── #45 — Qualifier to #44: Lagnadhipati in 6/8/12 in D9 from 4th lord ──
    # G13: LORD_OF:1 as subject planet. → descriptive.
    # TODO(G13): InVargaHouseFrom("LORD_OF:1", "LORD_OF:4", {6,8,12}, "D9")
    RuleRecord(
        id="H1.N.45", house=1, signification="self", group="navamsa_qualifier",
        kind="descriptive",
        condition=None,
        fortified="",
        afflicted="Lagnadhipati in 6th/8th/12th in Navamsha from 4th lord → "
                  "enmity with mother/relatives, accident, legal troubles",
        frame="LAGNA", varga="D9", polarity="malefic",
        source=Citation("HTJAH-I", 1731)),

    # ── #46 — Lagnadhipati in 5th with 5th lord, well-fortified (base) ───────
    RuleRecord(
        id="H1.N.46", house=1, signification="self", group="navamsa_qualifier",
        kind="evaluable",
        condition=C.And(C.LordIn(1, 5), C.LordsConjunct(1, 5)),
        fortified="grace of ruler/Government, mental peace, community leader, "
                  "Ambassador/Minister/high official, birth of a son, political prosperity",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 1735)),

    # ── #47 — Qualifier to #46: Lagna-lord in 6/8/12 from 5th lord in D9 ────
    # G13: LORD_OF:1 as subject planet. → descriptive.
    # TODO(G13): InVargaHouseFrom("LORD_OF:1", "LORD_OF:5", {6,8,12}, "D9")
    RuleRecord(
        id="H1.N.47", house=1, signification="self", group="navamsa_qualifier",
        kind="descriptive",
        condition=None,
        fortified="",
        afflicted="Lagna-lord in 6th/8th/12th from 5th lord in Navamsha → "
                  "reverses in political or official career",
        frame="LAGNA", varga="D9", polarity="malefic",
        source=Citation("HTJAH-I", 1739)),

    # ── #48 — Lagnadhipati in 6th with 6th lord (base) ───────────────────────
    RuleRecord(
        id="H1.N.48", house=1, signification="self", group="navamsa_qualifier",
        kind="evaluable",
        condition=C.And(C.LordIn(1, 6), C.LordsConjunct(1, 6)),
        fortified="",
        afflicted="physical ailments, wounds, enmity with rulers, failure, legal "
                  "troubles, poverty, weapon-wounds, physical distress",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 1743)),

    # ── #49 — Reversal: 6th lord debilitated AND Lagna-lord exalted in D9 ────
    # G13: VargaDignity accepts a planet name; both LORD_OF:1 and LORD_OF:6 are
    # chart-dependent. → descriptive.
    # TODO(G13): And(VargaDignity("LORD_OF:6","D9",{"debil"}),
    #                VargaDignity("LORD_OF:1","D9",{"exalt"}))
    RuleRecord(
        id="H1.N.49", house=1, signification="self", group="navamsa_qualifier",
        kind="descriptive",
        condition=None,
        fortified="in Navamsha 6th lord debilitated AND Lagna-lord exalted → "
                  "enters Army, vanquishes enemies, succeeds in litigation",
        afflicted=None,
        frame="LAGNA", varga="D9", polarity="benefic",
        source=Citation("HTJAH-I", 1745)),

    # ── #50 — Qualifier to #48/#49: Lagna-lord in 6/8/12 in D9 from 6th lord ─
    # G13: LORD_OF:1 as subject planet. → descriptive.
    # TODO(G13): InVargaHouseFrom("LORD_OF:1", "LORD_OF:6", {6,8,12}, "D9")
    RuleRecord(
        id="H1.N.50", house=1, signification="self", group="navamsa_qualifier",
        kind="descriptive",
        condition=None,
        fortified="",
        afflicted="Lagna-lord in 6th/8th/12th in Navamsha from 6th lord → "
                  "favourable results minimised, unfavourable will not predominate",
        frame="LAGNA", varga="D9", polarity="neutral",
        source=Citation("HTJAH-I", 1748)),

    # ── #51 — Lagnadhipati in 7th conjunct 7th lord (base) ───────────────────
    RuleRecord(
        id="H1.N.51", house=1, signification="self", group="navamsa_qualifier",
        kind="evaluable",
        condition=C.And(C.LordIn(1, 7), C.LordsConjunct(1, 7)),
        fortified="pilgrimage; if unmarried, marriage; movable 7th = distant "
                  "journeys, fixed = own country, common = foreign countries",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 1751)),

    # ── #52 — Qualifier: Lagnadhipati weaker than 7th lord ───────────────────
    # G13: Shadbala comparison between dynamically-resolved lords requires a
    # STRONGER_THAN / WEAKER_THAN predicate not yet implemented. → descriptive.
    # TODO(G13): encode when a comparative-strength predicate exists.
    RuleRecord(
        id="H1.N.52", house=1, signification="self", group="navamsa_qualifier",
        kind="descriptive",
        condition=None,
        fortified="",
        afflicted="Lagnadhipati weaker than 7th lord → journeys prove profitless",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 1754)),

    # ── #53 — Qualifier: Lagna-lord in 6/8/12 from 7th lord in D9 ───────────
    # G13: LORD_OF:1 as subject planet. → descriptive.
    # TODO(G13): InVargaHouseFrom("LORD_OF:1", "LORD_OF:7", {6,8,12}, "D9")
    RuleRecord(
        id="H1.N.53", house=1, signification="self", group="navamsa_qualifier",
        kind="descriptive",
        condition=None,
        fortified="",
        afflicted="Lagna-lord in 6th/8th/12th from 7th lord in Navamsha → "
                  "deprived of livelihood, defamed, misunderstandings with wife, "
                  "business loss, general deterioration",
        frame="LAGNA", varga="D9", polarity="malefic",
        source=Citation("HTJAH-I", 1755)),

    # ── #54 — Lagnadhipati joins 8th lord in the 8th (base) ──────────────────
    RuleRecord(
        id="H1.N.54", house=1, signification="self", group="navamsa_qualifier",
        kind="evaluable",
        condition=C.And(C.LordIn(1, 8), C.LordsConjunct(1, 8)),
        fortified="",
        afflicted="misery, poverty, sinful life, debts, evil thoughts",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 1759)),

    # ── #55 — Qualifier: 8th lord rendered weak ──────────────────────────────
    # G13: "lord rendered weak" requires a strength/debility predicate on a
    # dynamically-resolved lord. → descriptive.
    # TODO(G13): encode when LAGNADHIPATI_WEAK / lord-strength predicate exists.
    RuleRecord(
        id="H1.N.55", house=1, signification="self", group="navamsa_qualifier",
        kind="descriptive",
        condition=None,
        fortified="",
        afflicted="8th lord rendered weak → evil minimised, but sinful life "
                  "pursued clandestinely",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 1761)),

    # ── #56 — Lagnadhipati joins 9th lord in the 9th (base) ──────────────────
    RuleRecord(
        id="H1.N.56", house=1, signification="self", group="navamsa_qualifier",
        kind="evaluable",
        condition=C.And(C.LordIn(1, 9), C.LordsConjunct(1, 9)),
        fortified="father happy in Lagna-lord's Dasha, righteous acts, devotion "
                  "to parents and elders",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 1764)),

    # ── #57 — Reversal in adverse Navamsha (9th-lord conjunction) ────────────
    # G13: "adverse Navamsha positions" is unspecified (no single predicate). →
    # descriptive.
    # TODO(G13): clarify which of the 6/8/12 navamsha conditions Raman intends.
    RuleRecord(
        id="H1.N.57", house=1, signification="self", group="navamsa_qualifier",
        kind="descriptive",
        condition=None,
        fortified="",
        afflicted="adverse Navamsha positions → atheistic tendencies, litigation "
                  "over ancestral property",
        frame="LAGNA", varga="D9", polarity="malefic",
        source=Citation("HTJAH-I", 1766)),

    # ── #58 — Amplifier: either lord (1st/9th) exalted ───────────────────────
    # G13: HasDignity requires a static planet name; LORD_OF:1 and LORD_OF:9
    # are chart-dependent. → descriptive.
    # TODO(G13): Or(HasDignity("LORD_OF:1",{"exalt"}), HasDignity("LORD_OF:9",{"exalt"}))
    RuleRecord(
        id="H1.N.58", house=1, signification="self", group="navamsa_qualifier",
        kind="descriptive",
        condition=None,
        fortified="either the 1st or 9th lord exalted → influx of wealth, "
                  "expenditure on desirable and deserving causes",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 1767)),

    # ── #59 — Lagnadhipati joins 10th lord in the 10th (base) ────────────────
    RuleRecord(
        id="H1.N.59", house=1, signification="self", group="navamsa_qualifier",
        kind="evaluable",
        condition=C.And(C.LordIn(1, 10), C.LordsConjunct(1, 10)),
        fortified="religious sacrifices, good administrative/political job, "
                  "theistic, wields considerable influence in high circles",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 1770)),

    # ── #60 — Reversal in adverse Navamsha (10th-lord conjunction) ───────────
    # G13: "adverse in Navamsha" unspecified. → descriptive.
    # TODO(G13): clarify exact 6/8/12 navamsha predicate per Raman's intent.
    RuleRecord(
        id="H1.N.60", house=1, signification="self", group="navamsa_qualifier",
        kind="descriptive",
        condition=None,
        fortified="",
        afflicted="adverse Navamsha → loss of respect, victim of slander, "
                  "sinful acts",
        frame="LAGNA", varga="D9", polarity="malefic",
        source=Citation("HTJAH-I", 1772)),

    # ── #61 — Lagnadhipati joins 11th lord in the 11th (base) ────────────────
    RuleRecord(
        id="H1.N.61", house=1, signification="self", group="navamsa_qualifier",
        kind="evaluable",
        condition=C.And(C.LordIn(1, 11), C.LordsConjunct(1, 11)),
        fortified="much gain from trade, elder brother happy and benefits native",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 1776)),

    # ── #62 — Reversal in adverse Navamsha (11th-lord conjunction) ───────────
    # G13: "adverse in Navamsha" unspecified. → descriptive.
    # TODO(G13): clarify exact 6/8/12 navamsha predicate per Raman's intent.
    RuleRecord(
        id="H1.N.62", house=1, signification="self", group="navamsa_qualifier",
        kind="descriptive",
        condition=None,
        fortified="",
        afflicted="adverse Navamsha → gains less, misunderstandings with elder "
                  "brother",
        frame="LAGNA", varga="D9", polarity="malefic",
        source=Citation("HTJAH-I", 1778)),

    # ── #63 — Lagnadhipati joins 12th lord in the 12th (base) ────────────────
    RuleRecord(
        id="H1.N.63", house=1, signification="self", group="navamsa_qualifier",
        kind="evaluable",
        condition=C.And(C.LordIn(1, 12), C.LordsConjunct(1, 12)),
        fortified="",
        afflicted="loses ancestral property, poverty, roams in exile, financial "
                  "difficulties",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 1785)),

    # ── #64 — Qualifier: Lagnadhipati in his own Navamsha ────────────────────
    # G13: Vargottama("LORD_OF:1") — Vargottama takes a planet name, not a
    # LORD_OF origin. → descriptive.
    # TODO(G13): Vargottama("LORD_OF:1") once the predicate accepts LORD_OF origins.
    RuleRecord(
        id="H1.N.64", house=1, signification="self", group="navamsa_qualifier",
        kind="descriptive",
        condition=None,
        fortified="Lagnadhipati in own Navamsha → slight benefit / earns money "
                  "in foreign countries",
        afflicted=None,
        frame="LAGNA", varga="D9", polarity="benefic",
        source=Citation("HTJAH-I", 1786)),

    # ── #65 — Amplifier: lord of Navamsha sign held by Lagnadhipati exalted in
    #          a Chara Rashi ─────────────────────────────────────────────────
    # G13: multi-step — requires (a) finding the D9 sign of LORD_OF:1,
    # (b) finding the lord of that D9 sign, (c) checking if that planet is
    # exalted in a Chara (movable) rashi. No existing predicate chain covers
    # this. → descriptive.
    # TODO(G13): needs a NAVAMSHA_DISPOSITOR_EXALT_IN_CHARA predicate.
    RuleRecord(
        id="H1.N.65", house=1, signification="self", group="navamsa_qualifier",
        kind="descriptive",
        condition=None,
        fortified="lord of Navamsha sign held by Lagnadhipati exalted in a Chara "
                  "Rashi → considerable amassing of fortune",
        afflicted=None,
        frame="LAGNA", varga="D9", polarity="benefic",
        source=Citation("HTJAH-I", 1788)),

    # ── #66 — Diagnostic: contact between lords of 1st and 6th ───────────────
    # The full condition is "aspect OR association" between the lords — but
    # MutualAspect and Aspects require static planet names, not LORD_OF origins.
    # LordsConjunct(1,6) covers the association half; the aspect half is G13.
    # Encoding as descriptive to capture Raman's full intent without truncating
    # the OR.
    # TODO(G13): Or(LordsConjunct(1,6), <aspect between LORD_OF:1 and LORD_OF:6>)
    # once an AspectsBetweenLords(h1, h2) predicate exists.
    RuleRecord(
        id="H1.N.66", house=1, signification="self", group="navamsa_qualifier",
        kind="descriptive",
        condition=None,
        fortified="no contact (aspect or association) between lords of 1st and "
                  "6th → health protective; violation implicates illness/defamation",
        afflicted="contact between lords of 1st and 6th (aspect or association) "
                  "→ health suffers; defamation risk (Chart 18 case: Lagna-lord "
                  "aspected by Mars/6th-lord)",
        frame="LAGNA", varga="D1", polarity="malefic",
        source=Citation("HTJAH-I", 1972)),

    # ── #67 — Integration: at least two of {Lagna, Sun, Moon} well disposed ──
    # G13: "well disposed" is a multi-factor holistic judgment (strength, dignity,
    # aspects) with no single predicate. → descriptive.
    # TODO(G13): encode when a WELL_DISPOSED(lagna_or_planet) predicate exists.
    RuleRecord(
        id="H1.N.67", house=1, signification="self", group="navamsa_qualifier",
        kind="descriptive",
        condition=None,
        fortified="at least two of {Lagna, Sun, Moon} well disposed → steady "
                  "fortune assured",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic",
        source=Citation("HTJAH-I", 2111)),
)
