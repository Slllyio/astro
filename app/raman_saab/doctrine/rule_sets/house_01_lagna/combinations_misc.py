"""House 1 — miscellaneous Important Combinations (the Group-2 *remainder* batch).

Encodes ONLY the combinations from HTJAH-I:1086-1150 that are not the canonical
home of any other house_01_lagna submodule (one-owner-per-corpus-rule policy):

    #22  travels (movable-sign ascendant/lord)              — descriptive
    #23  happy all life (Lagna lord Vargottama+exalted...)  — descriptive
    #24  happy beginning+middle (benefics 1/11/12 + lord)   — descriptive
    #25  happy beginning (lord strong / Jupiter in Lagna)   — descriptive
    #29  happy after 20th (Lagna/11th lord in 2nd)          — evaluable
    #30  happy after 30th (those lords in Kendras)          — evaluable
    #31  happy after 16th (Lagna lord in 9th)               — evaluable
    #35  evil intensified (weak Lagnadhipati in Tara 3/5/7) — descriptive
    #36  favourable lessened (strong Lagnadhipati in Tara)  — descriptive
    #37  benefic results decrease (blemished dispositor)    — descriptive

Canonical owners of the records that USED to be duplicated here (removed in the
unification pass):

    #13-#19  constitution.py        (H1.B.13 .. H1.B.19)  — Sushka/watery physique
    #32-#34  combinations_core.py   (H1.C.32 .. H1.C.34)  — the fortunate ladder
    #38/#39  navamsa_qualifiers.py  (H1.N.38 / H1.N.39)   — Lagnadhipati weak / D9-12th
    #67      navamsa_qualifiers.py  (H1.N.67)             — two-of-three well disposed

Source span: HTJAH-I:1117-1149 (timing/qualifying combinations).
Corpus: data/knowledge_library/sources/how_to_judge_a_horoscope_raman/
         chapter_001_full-text-unsplit.md

Usage:
    python -m app.raman_saab.doctrine.rule_sets.house_01_lagna.combinations_misc
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine.conditions import CountInHouse, LordIn, Or
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (

    # ── #22 — Ascendant / lord / navamsa-ascendant / its lord in movable sign → travels ──────
    # HTJAH-I:1117-1119: "If the ascendant, its lord, ascendant in Navamsha, or its lord is in
    # a movable sign the subject travels in distant lands with profit to himself."
    # Requires sign-modality predicate (movable = Aries/Cancer/Libra/Capricorn) not yet
    # available as a Condition. Descriptive.
    RuleRecord(
        id="H1.C.22", house=1, signification="self", group="combination", kind="descriptive",
        condition=None,
        fortified="travels in distant lands with profit (ascendant/lord/navamsa-ascendant/its "
                  "lord in a movable sign: Aries/Cancer/Libra/Capricorn)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 1117)),

    # ── #23 — Lord of Lagna Vargottama + exalted + friendly Drekkana + good aspects → happy
    #          all his life ────────────────────────────────────────────────────────────────────
    # HTJAH-I:1119-1120: "He will be happy all his life if lord of Lagna is in Vargottama, in
    # exaltation, in a friendly Drekkana, and joined or aspected by good planets."
    # Requires testing these properties on a variable lord (Vargottama(lord), HasDignity(lord,
    # {"exalt"}), Drekkana check). No planet-agnostic predicate for "lord of lagna is X".
    # Descriptive.
    RuleRecord(
        id="H1.C.23", house=1, signification="self", group="combination", kind="descriptive",
        condition=None,
        fortified="happy all his life (Lagna lord Vargottama + exalted + friendly Drekkana + "
                  "aspected/joined by good planets)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 1119)),

    # ── #24 — Benefics in 1st, 11th, 12th AND strong lord in Trikona → happy beginning & middle
    # HTJAH-I:1120-1122: "If benefices stay in the 1st, 11th and 12th houses and the strong lord
    # is in Trikona he will be happy in the beginning and middle."
    # "Strong lord in trikona" requires testing strength of a variable lord — no predicate.
    # Descriptive.
    RuleRecord(
        id="H1.C.24", house=1, signification="self", group="combination", kind="descriptive",
        condition=None,
        fortified="happy in the beginning and middle of life (benefics in 1st/11th/12th AND "
                  "strong Lagna lord in trikona)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 1120)),

    # ── #25 — Lord of Lagna strong OR Jupiter in Lagna → happy in the beginning ──────────────
    # HTJAH-I:1122: "If lord of Lagna is strong or Jupiter is in Lagna he will be happy in the
    # beginning."
    # "Lord of Lagna strong" requires a strength predicate (Shadbala aggregate) not yet
    # available. Descriptive to cover both branches.
    RuleRecord(
        id="H1.C.25", house=1, signification="self", group="combination", kind="descriptive",
        condition=None,
        fortified="happy in the beginning of life (Lagna lord strong; OR Jupiter in Lagna)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 1122)),

    # ── #29 — Asc-lord / navamsa-lord of Lagna-lord / 11th-lord in 2nd → happy after 20th year
    # HTJAH-I:1131-1133: "If the ascendant lord, or the lord of the Navamsha occupied by the
    # lord of the Lagna, or the lord of the 11th occupy the second house the person becomes happy
    # after his 20th year."
    # Branches: LordIn(1,2) and LordIn(11,2) are evaluable; the navamsa branch requires a
    # navamsa-lord predicate not available — encode the D1 branches evaluably.
    RuleRecord(
        id="H1.C.29", house=1, signification="self", group="combination", kind="evaluable",
        condition=Or(LordIn(1, 2), LordIn(11, 2)),
        fortified="happy after the 20th year (Lagna lord or 11th lord in 2nd)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 1131)),

    # ── #30 — Same lords in Kendras → happy after the 30th year ──────────────────────────────
    # HTJAH-I:1133-1134: "The position of the above lords in Kendras makes the person happy
    # after the 30th year."
    # "Above lords" = Lagna lord, lord of navamsa held by Lagna-lord, and 11th lord.
    # Encode the D1 kendra branches for Lagna-lord and 11th-lord evaluably.
    RuleRecord(
        id="H1.C.30", house=1, signification="self", group="combination", kind="evaluable",
        condition=Or(
            LordIn(1, 1), LordIn(1, 4), LordIn(1, 7), LordIn(1, 10),
            LordIn(11, 1), LordIn(11, 4), LordIn(11, 7), LordIn(11, 10),
        ),
        fortified="happy after the 30th year (Lagna lord or 11th lord in a Kendra)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 1133)),

    # ── #31 — Lagna lord occupies the 9th → happy after the 16th year ────────────────────────
    # HTJAH-I:1134-1135: "Occupation of the 9th house by Lagna lord is conducive for happiness
    # after the 16th year."
    RuleRecord(
        id="H1.C.31", house=1, signification="self", group="combination", kind="evaluable",
        condition=LordIn(1, 9),
        fortified="happy after the 16th year (Lagna lord in the 9th)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 1134)),

    # ── #35 — Lagnadhipati weak + in 3rd/5th/7th star from Janma Nakshatra → evil intensified
    # HTJAH-I:1142-1145: "when Lagnadhipati is not strong and well disposed, but occupies the
    # 3rd (vipat), 5th (pratyak) and 7th (naidhana) constellations from Janma Nakshatra …
    # the evil indications would be intensified."
    # TODO(predicate: TaraOf) — requires computing the Tara (3rd/5th/7th nakshatra from the
    # radical Moon's star). Descriptive until TaraOf predicate is implemented.
    RuleRecord(
        id="H1.C.35", house=1, signification="self", group="combination", kind="descriptive",
        condition=None,  # TODO(predicate: TaraOf) — needs TaraOf(planet, moon_nak, [3,5,7])
        fortified=None,
        afflicted="evil indications intensified (Lagnadhipati weak AND occupies 3rd vipat / "
                  "5th pratyak / 7th naidhana constellation from Janma Nakshatra)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 1142)),

    # ── #36 — Lagnadhipati strong + in same 3rd/5th/7th star → favourable indications lessened
    # HTJAH-I:1145-1146: "Conversely when Lagnadhipati is strong but occupies the above
    # constellational positions, there will be a lessening of the favourable indications."
    # TODO(predicate: TaraOf) — descriptive until TaraOf predicate is implemented.
    RuleRecord(
        id="H1.C.36", house=1, signification="self", group="combination", kind="descriptive",
        condition=None,  # TODO(predicate: TaraOf) — needs TaraOf(planet, moon_nak, [3,5,7])
        fortified="favourable indications lessened (Lagnadhipati strong but in 3rd/5th/7th "
                  "Tara constellation from Janma Nakshatra)",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 1145)),

    # ── #37 — Lagnadhipati strong BUT dispositor blemished → benefic results decrease ─────────
    # HTJAH-I:1146-1148: "Even when Lagnadhipati is strong but the lord of sign occupied by
    # Lagnadhipati is blemished, the benefice results decrease and the malefic effects are
    # augmented."
    # "Blemished" dispositor requires a Shadbala-strength or compound-dignity predicate not yet
    # available. Descriptive.
    RuleRecord(
        id="H1.C.37", house=1, signification="self", group="combination", kind="descriptive",
        condition=None,
        fortified=None,
        afflicted="benefic results decrease and malefic effects augmented (Lagnadhipati strong "
                  "but its dispositor — lord of the sign it occupies — is blemished)",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 1146)),
)
