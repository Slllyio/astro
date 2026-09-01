"""House 2 (Dhana — wealth) lord-in-12-houses RuleRecords.

Encoding of the "Lord of the 2nd in the 12 Houses" table from
`methodology/house_02_dhana.md`, distilled verbatim from B.V. Raman,
*How to Judge a Horoscope* Vol I, §V (HTJAH-I:2325–2421).

Source span: HTJAH-I:2325–2421.

SLOT MAPPING CORRECTED 2026-09-01 after an engine-blind doctrine review. Raman writes each
placement here as a GENERAL, unconditioned reading followed by one conditioned on
FORTIFICATION ("When the 2nd lord in the 3rd is well fortified", "When well-fortified"), and
he closes the table at 2423 saying so: "These combinations are AGAIN of general application" —
"again" back-referencing his design statement at 1003-1007. The general paragraph had been
filed under `afflicted`, so `_branch` showed a weak-lord chart his BASE reading under an
"afflicted" heading. It now sits in `general`; `afflicted` keeps ONLY the clauses Raman really
does condition on affliction (2360, 2373-2378, 2408, 2420-2421).

Three things in this module are misfiled but are NOT general readings, and are deliberately
left where they are pending their own review:
  * H2.L.4's affliction is of the **4TH lord**, not the 2nd (2360) — a predicate testing this
    rule's own house lord would fire it on the wrong thing.
  * H2.L.8's **STRONG** branch is ADVERSE (2392-2393, "hardly any earnings, but inherited or
    accumulated wealth will disappear"). Any renderer that presents `fortified` as the good
    reading mis-presents this one.
  * H2.L.2's `fortified` "riches without effort if 1st and 2nd lords have exchanged" is real
    Raman but from HTJAH-I:2506, a dasha-timing list OUTSIDE this table, and is conditioned on
    a parivarthana, not on fortification.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    RuleRecord(
        id="H2.L.1", house=2, signification="wealth", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(2, 1),
        fortified="wealthy by own effort, intelligence and learning; inheritance if 9th lord or Sun touches the combination",
        # HTJAH-I:2325-2326, unconditioned. The old slot ALSO dropped Raman's leading
        # "becomes no doubt wealthy", which inverts the sentence's balance; restored.
        general="becomes no doubt wealthy, but hates his own family, lacks polite manners, "
                "and becomes passionate, subservient and time-serving",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 2325)),
    RuleRecord(
        id="H2.L.2", house=2, signification="wealth", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(2, 2),
        fortified="riches without effort if 1st and 2nd lords have exchanged; exaltation/own-disposition yields Yoga-Karaka-grade fortune through business",
        # HTJAH-I:2332-2333 general; 2342-2345 genuinely afflicted ("Depending upon the
        # nature of the aspects cast on the 2nd lord by malefic planets..."; "An affliction
        # to the 2nd lord may also express itself in the shape of..."). The
        # twice-or-thrice clause is a 7TH-HOUSE strength branch and stays inside Raman's
        # own sentence rather than becoming a discriminator.
        general="becomes proud; may marry twice or thrice depending upon the strength of the "
                "7th house; may become childless",
        afflicted="malefic aspects on the 2nd lord - losses; an affliction may also show as "
                  "not getting nutritious and delicious food, or family and children "
                  "suffering constant diseases, or want of cordial relations with the "
                  "life-partner",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 2332)),
    RuleRecord(
        id="H2.L.3", house=2, signification="wealth", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(2, 3),
        fortified="benefited by sisters; gains by fine arts (music, dancing); propitiates Kshudra Devatas",
        # HTJAH-I:2347-2349, unconditioned; the fortified paragraph opens "When the 2nd
        # lord in the 3rd is well fortified" (2351).
        general="brave, intelligent, but of depraved character; atheistic tendencies rampant "
                "and addicted to luxuries; later in life turns out to be a miser",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 2347)),
    RuleRecord(
        id="H2.L.4", house=2, signification="wealth", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(2, 4),
        fortified="earns as automobile dealer/agent, agriculturist, landlord or commission agent; benefited by maternal relations",
        # HTJAH-I:2355-2360. The general half is unconditioned; the affliction Raman names
        # is of the **4th** lord ("There will be losses on this account if the 4th lord is
        # afflicted", 2360), NOT the 2nd — flagged in the module docstring.
        general="the results of the lord in the 3rd apply in addition; spends money for his "
                "own happiness; highly frugal in dealing with money",
        afflicted="the 4TH lord afflicted - losses on the maternal-relations account",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 2355)),
    RuleRecord(
        id="H2.L.5", house=2, signification="wealth", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(2, 5),
        fortified="unexpected wealth via lotteries, crosswords, favour of rulers",
        # HTJAH-I:2362-2363, unconditioned; the fortified paragraph opens at 2365.
        general="hating family, sensual, not spending money even on children, he lacks "
                "manners and etiquette",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 2362)),
    RuleRecord(
        id="H2.L.6", house=2, signification="wealth", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(2, 6),
        fortified="amasses wealth by black-marketing, deceit, creating misunderstandings and questionable dealings",
        # HTJAH-I:2368-2378. General at 2368-2369; genuinely afflicted at 2373+2377,
        # Raman's own "If afflicted, he will be involved in these troubles and sentenced...".
        general="income and expenditure from enemies; suffers from defects or diseases in "
                "the anus and thighs",
        afflicted="the 2nd lord afflicted - involved in these troubles and sentenced for such "
                  "crimes as breach of trust, forgeries and perjuries",
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 2368)),
    RuleRecord(
        id="H2.L.7", house=2, signification="wealth", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(2, 7),
        fortified="influx of wealth via foreign sources or foreign business; if sign/navamsa/star of 2nd lord is feminine, benefit via women",
        # HTJAH-I:2380-2381, unconditioned. The fortified clause is a CONFIGURATION plus
        # strength compound (2nd lord conjunct the 7th lord AND strong, 2383), and the
        # feminine-sign clause (2385-2386) is pure configuration with no strength element.
        general="likely to become a healer; laxity of morals will mark both husband and "
                "wife; wastes much money on the gratification of the senses",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 2380)),
    RuleRecord(
        id="H2.L.8", house=2, signification="wealth", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(2, 8),
        fortified="influx and loss of wealth — hardly any earnings; inherited or accumulated wealth disappears",
        # HTJAH-I:2388-2389, unconditioned. NOTE the `fortified` branch is Raman's STRONG
        # branch and is ADVERSE (2392-2393) — see the module docstring.
        general="very little or no happiness from wife or husband; misunderstandings with "
                "elder brothers; gets landed properties",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-I", 2388)),
    RuleRecord(
        id="H2.L.9", house=2, signification="wealth", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(2, 9),
        # HTJAH-I:2395-2396 is ONE unconditioned sentence that the encoder cut in two:
        # "will possess lot of wealth and become happy" to `fortified`, "ill-health in young
        # age" to `afflicted`. Reunited, with "Skilful" — dropped entirely by the old
        # encoding — restored. The fortified branch is compound: well fortified AND the 9th
        # lord in Lagna (2398).
        general="skilful; ill-health in young age but healthy afterwards; will possess a lot "
                "of wealth and become happy",
        fortified="the 2nd lord well fortified and the 9th lord in Lagna - good inheritance, "
                  "and benefits through different sources according to the sign and "
                  "Nakshatra held by the 2nd lord",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-I", 2395)),
    RuleRecord(
        id="H2.L.10", house=2, signification="wealth", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(2, 10),
        # HTJAH-I:2402-2408. BOTH paragraphs are unconditioned — the second (the avocations
        # sentence, currently in `fortified`) carries no opener — so both are general. Only
        # "Powerful afflictions will cause loss from the very same sources" (2408) is
        # conditioned.
        general="respect from elders and superiors, learned, wealthy, and earns by his own "
                "exertions; takes to a number of useful avocations - business, agriculture, "
                "or philosophical lectures and dissertations - and benefits financially; "
                "the constellation and sign held by the 2nd lord determine the exact nature "
                "and sources of earnings",
        fortified="respect from elders and superiors, learned, wealthy, and earns by his own "
                  "exertions; takes to a number of useful avocations - business, "
                  "agriculture, or philosophical lectures and dissertations - and benefits "
                  "financially",
        afflicted="powerful afflictions - loss from the very same sources",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 2402)),
    RuleRecord(
        id="H2.L.11", house=2, signification="wealth", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(2, 11),
        fortified="earns by lending money, banking or running a boarding house",
        # HTJAH-I:2410-2411, unconditioned; the fortified paragraph opens "When
        # well-fortified" (2413).
        general="health will be bad during childhood; earns considerable wealth but becomes "
                "unscrupulous",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 2410)),
    RuleRecord(
        id="H2.L.12", house=2, signification="wealth", group="lord_in_house", kind="evaluable",
        condition=C.LordIn(2, 12),
        # HTJAH-I:2417-2421. The 2417-2418 sentence was torn across both slots, and the
        # ecclesiastical-income sentence (2420) is unconditioned but sat in `fortified`.
        # Only "If the second lord is afflicted, he will lose money on this account"
        # (2420-2421) is a real afflicted clause.
        general="becomes a respectable man; in all probability a government servant; "
                "deprived of the happiness of an elder brother; the income will be through "
                "ecclesiastical sources",
        fortified="becomes a respectable man; in all probability a government servant; "
                  "deprived of the happiness of an elder brother; the income will be "
                  "through ecclesiastical sources",
        afflicted="the 2nd lord afflicted - loses money on the ecclesiastical account",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-I", 2417)),
)
