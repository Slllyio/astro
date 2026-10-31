"""House 7 (Kalatra — spouse/marriage) — Lord-in-12-houses RuleRecords.

The "Lord of the 7th in the 12 Houses" table (HTJAH-II:235-340). Moved verbatim
from the former flat ``house_07_kalatra.py`` during the Stage-4 subpackage split.
"""
from __future__ import annotations

from typing import Final

from app.raman_saab.doctrine import conditions as C
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation


RULES: Final[tuple[RuleRecord, ...]] = (
    # — 7th lord in the 12 houses (HTJAH-II:235-340) —
    RuleRecord(
        id="H7.L.1", house=7, signification="spouse", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-7 sweep (0/12 correct): 235-239 is unconditioned; both afflicted-
        # slot clauses are AFFLICTION tests (H7.L.1a, and H7.L.1b with Venus). Dropped words
        # restored.
        condition=C.LordIn(7, 1),
        fortified="the native may marry someone he has known since childhood or one who has "
                  "been brought up in the same house; the wife or husband will be a stable "
                  "and mature person; he will be intelligent and capable of weighing the "
                  "pros and cons",
        afflicted=None,
        general="the native may marry someone he has known since childhood or one who has "
                "been brought up in the same house; the wife or husband will be a stable "
                "and mature person; he will be intelligent and capable of weighing the pros "
                "and cons",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 235)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H7.L.1a", house=7, signification="spouse", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(7, 1), C.AfflictedBy("LORD_OF:7")),
        general="afflictions to the 7th lord may entail constant travelling",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 239)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H7.L.1b", house=7, signification="spouse", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(7, 1), C.AfflictedBy("LORD_OF:7"), C.AfflictedBy("Venus")),
        general="the 7th lord and Venus both afflicted - the native may be sensual and seek "
                "clandestine relationship with the opposite sex",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 240)),
    RuleRecord(
        id="H7.L.2", house=7, signification="wealth_through_marriage", group="lord_in_house",
        # 2026-10-13 House-7 sweep (0/12 correct): 'If afflicted' (245) is an affliction
        # test (H7.L.2a); the dual-sign clause (248) and the maraka-Dasa clause (250) are
        # parked (H7.L.2b/c).
        kind="evaluable", condition=C.LordIn(7, 2),
        fortified="the native will get wealth from women or through marriage; the person "
                  "will have a wavering mind and will always be inclined sensually",
        afflicted=None,
        general="the native will get wealth from women or through marriage; the person will "
                "have a wavering mind and will always be inclined sensually",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 244)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H7.L.2a", house=7, signification="wealth_through_marriage", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(7, 2), C.AfflictedBy("LORD_OF:7")),
        general="the 7th lord afflicted - one may earn money through despicable means as "
                "trading in flesh, women, not excluding his wife; he may eat food offered "
                "at death-ceremonies (shraddha) and wander about seeking such food",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 245)),
    RuleRecord(
        id="H7.L.2b", house=7, signification="wealth_through_marriage", group="lord_in_house",
        # 2026-10-13: promoted from descriptive once HouseAfflictedBy existed (a natural
        # malefic occupies or aspects the house; its own lord excluded). Neutral: refines a
        # parent placement.
        kind="evaluable",
        condition=C.And(C.LordIn(7, 2), C.Or(C.InSign("LORD_OF:7", 3), C.InSign("LORD_OF:7", 6), C.InSign("LORD_OF:7", 9), C.InSign("LORD_OF:7", 12)), C.HouseAfflictedBy(2)),
        general="the second house a dual sign and afflicted - more than one marriage is "
                "likely",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 248)),
    RuleRecord(
        id="H7.L.2c", house=7, signification="wealth_through_marriage", group="lord_in_house",
        kind="descriptive",
        condition=None,
        general="a maraka Dasa running - the native may die during the period of the "
                "seventh lord. TODO(timing: a dasha condition, outside the atemporal "
                "EvalContext)",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 250)),
    RuleRecord(
        id="H7.L.3", house=7, signification="spouse", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-7 sweep (0/12 correct): 'Female issues survive' (257) has no
        # antecedent of its own and changes topic; read as unconditioned (a judgment call).
        # Affliction clauses -> H7.L.3a.
        condition=C.LordIn(7, 3),
        # "female issues survive" follows the AFFLICTION clause at HTJAH-II:257, not the
        # base — misattributed to `fortified` by the original encoding. Moved to `general`
        # with the base reading, since the base sentence ("This disposition gives lucky
        # brothers who may live abroad", 254) is unconditioned.
        general="lucky brothers who may live abroad; female issues survive",
        fortified="lucky brothers who may live abroad; female issues survive",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 254)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H7.L.3a", house=7, signification="spouse", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(7, 3), C.AfflictedBy("LORD_OF:7")),
        general="the 7th lord afflicted - the native may indulge in adultery with a "
                "brother's or sister's married partner; affliction also gives misfortunes "
                "to co-borns",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 255)),
    RuleRecord(
        id="H7.L.4", house=7, signification="spouse", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-7 sweep (0/12 correct): plain and severe affliction tiers (262,
        # 264) -> H7.L.4a/b.
        condition=C.LordIn(7, 4),
        fortified="a lucky and happy married partner with many children and comforts; the "
                  "native may have the benefit of high academic qualification and own many "
                  "vehicles",
        afflicted=None,
        general="a lucky and happy married partner with many children and comforts; the "
                "native may have the benefit of high academic qualification and own many "
                "vehicles",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 259)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H7.L.4a", house=7, signification="spouse", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(7, 4), C.AfflictedBy("LORD_OF:7")),
        general="the 7th lord afflicted - domestic harmony may be spoilt through an "
                "immature and mean partner; the native may run into endless problems on "
                "account of his conveyances",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 262)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H7.L.4b", house=7, signification="spouse", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(7, 4), C.AfflictedBy("LORD_OF:7", {"Rahu", "Ketu"}), C.AfflictedBy("LORD_OF:7", {"Sun", "Mars", "Saturn"})),
        general="the 7th lord severely afflicted by the nodes and other malefics - the "
                "native's wife's character becomes questionable",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 264)),
    RuleRecord(
        id="H7.L.5", house=7, signification="spouse", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-7 sweep (0/12 correct): 273 'If the 7th lord is weak' is the ONLY
        # plain weakness clause in the section and stays in the weak slot. Severe affliction
        # (274) and the affliction-plus-benefic tier (275) -> H7.L.5a/b.
        condition=C.LordIn(7, 5),
        fortified="an early marriage; the partner may hail from an affluent and well-to-do "
                  "family; the wife or husband will be mature and an advantage to the "
                  "native; trouble to one's office superiors through foreign sources is "
                  "likely; the native will possess good character",
        afflicted="the 7th lord weak - there may be no children",
        general="an early marriage; the partner may hail from an affluent and well-to-do "
                "family; the wife or husband will be mature and an advantage to the native; "
                "trouble to one's office superiors through foreign sources is likely; the "
                "native will possess good character",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 271)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H7.L.5a", house=7, signification="spouse", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(7, 5), C.AfflictedBy("LORD_OF:7", C.FIRST_RATE_MALEFICS, min_count=2)),
        general="the 7th lord severely afflicted - one may get issues through the "
                "adulterous conduct of the wife",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 274)),
    # Raman gives this as an alternative to H7.L.5a; both can fire together (two first-rate
    # malefics plus a benefic) and he does not say which prevails. Neutral: refines a parent
    # that already votes for this placement.
    RuleRecord(
        id="H7.L.5b", house=7, signification="spouse", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(7, 5), C.AfflictedBy("LORD_OF:7"), C.InfluencedBy("LORD_OF:7")),
        general="both afflictions and benefic influences on the 7th lord - the native may "
                "get only female progeny",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 275)),
    RuleRecord(
        id="H7.L.6", house=7, signification="spouse", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-7 sweep (0/12 correct): all four conditioned clauses (283-289)
        # turn on Venus or affliction, none on the 7th lord's strength -> H7.L.6a-c (Venus
        # has no strength predicate).
        condition=C.LordIn(7, 6),
        fortified="two marriages with both partners living; may marry a cousin (uncle's daughter)",
        afflicted=None,
        general="the native may have two marriages with both partners living; one may marry "
                "a cousin such as an uncle's daughter",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 281)),
    RuleRecord(
        id="H7.L.6a", house=7, signification="spouse", group="lord_in_house",
        # 2026-10-13: promoted once IllDisposed existed (disposition reads clearly bad);
        # 'badly afflicted' reuses H7.L.5a's severity test. Neutral: refines a parent.
        kind="evaluable",
        condition=C.And(C.LordIn(7, 6), C.AfflictedBy("LORD_OF:7", C.FIRST_RATE_MALEFICS, min_count=2), C.IllDisposed("Venus")),
        general="the 7th lord badly afflicted and the karaka Venus also ill-disposed - one "
                "may suffer from impotency and many other diseases; the native's wife may "
                "be sickly and jealous by nature, denying the husband happiness from "
                "marriage",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 283)),
    RuleRecord(
        id="H7.L.6b", house=7, signification="spouse", group="lord_in_house",
        kind="descriptive",
        condition=None,
        general="Venus well placed but the 7th lord afflicted - the native may suffer from "
                "piles. TODO(predicate: 'well placed' for the named planet Venus)",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 286)),
    RuleRecord(
        id="H7.L.6c", house=7, signification="spouse", group="lord_in_house",
        # 2026-10-13: promoted from descriptive once IsStrong/IsWeak existed (effective
        # strength: Shadbala bar plus combustion/debility overrides). Neutral: refines a
        # parent placement.
        kind="evaluable",
        condition=C.And(C.LordIn(7, 6), C.IsWeak("Venus"), C.Not(C.AfflictedBy("Venus"))),
        general="Venus weak but not afflicted - one may desert or lose one's married "
                "partner through some indiscreet act",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 288)),
    RuleRecord(
        id="H7.L.7", house=7, signification="spouse", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-7 sweep (0/12 correct): 'If weak and afflicted' (295) needs BOTH
        # halves. A weak-slot record conditioned on affliction would still show to a STRONG
        # afflicted lord (fire_rules falls through to the weak text when the other slots are
        # empty), so it is parked as H7.L.7a until a Shadbala Condition exists.
        condition=C.LordIn(7, 7),
        fortified="charming, magnetic personality; women flock to him; just, honourable spouse of good family",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 291)),
    RuleRecord(
        id="H7.L.7a", house=7, signification="spouse", group="lord_in_house",
        # 2026-10-13: promoted from descriptive once IsStrong/IsWeak existed (effective
        # strength: Shadbala bar plus combustion/debility overrides). Neutral: refines a
        # parent placement.
        kind="evaluable",
        condition=C.And(C.LordIn(7, 7), C.IsWeak("LORD_OF:7"), C.AfflictedBy("LORD_OF:7")),
        general="the 7th lord weak and afflicted - a lonely life devoid of marriage and "
                "friends, and loss through marriage negotiations",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 295)),
    RuleRecord(
        id="H7.L.8", house=7, signification="spouse", group="lord_in_house", kind="descriptive",
        # 2026-10-28 rule-defect review (docs/raman_saab/research/rule_defects_review2_2026-10-28.json): descriptive.
        # 2026-10-13 House-7 sweep (0/12 correct): affliction clauses (300-305) -> H7.L.8a.
        condition=C.LordIn(7, 8),
        fortified="marriage with relatives or a rich partner",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 298)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H7.L.8a", house=7, signification="spouse", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(7, 8), C.AfflictedBy("LORD_OF:7")),
        general="the 7th lord afflicted - the early death of the partner, while the native "
                "may die in distant lands; a sickly and ill-tempered wife or husband, "
                "leading to estrangement and separation",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 300)),
    RuleRecord(
        id="H7.L.9", house=7, signification="spouse", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-7 sweep (0/12 correct): affliction clauses (310-312) -> H7.L.9a.
        condition=C.LordIn(7, 9),
        fortified="father may live abroad; native makes fortune in foreign lands; accomplished, righteous wife",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 307)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H7.L.9a", house=7, signification="spouse", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(7, 9), C.AfflictedBy("LORD_OF:7")),
        general="the 7th lord afflicted - the father may die early; the married partner may "
                "drag the native from the right (Dharmic) course of life, and he may waste "
                "his wealth and suffer penury",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 310)),
    RuleRecord(
        id="H7.L.10", house=7, signification="spouse", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-7 sweep (0/12 correct): affliction clauses (318-321) -> H7.L.10a.
        condition=C.LordIn(7, 10),
        fortified="the native may flourish in a profession abroad or his career may involve "
                  "constant travelling; one will get a devoted and faithful wife or "
                  "husband; the wife may also be employed and contribute to the native's "
                  "income, or she may help in the advancement of the native's career",
        afflicted=None,
        general="the native may flourish in a profession abroad or his career may involve "
                "constant travelling; one will get a devoted and faithful wife or husband; "
                "the wife may also be employed and contribute to the native's income, or "
                "she may help in the advancement of the native's career",
        frame="LAGNA", varga="D1", polarity="benefic", source=Citation("HTJAH-II", 314)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H7.L.10a", house=7, signification="spouse", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(7, 10), C.AfflictedBy("LORD_OF:7")),
        general="the 7th lord afflicted - the wife will be avaricious and over-ambitious "
                "but without sufficient capacity; consequently the native's career may "
                "suffer and deteriorate",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 318)),
    RuleRecord(
        id="H7.L.11", house=7, signification="spouse", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-7 sweep (0/12 correct): 'beneficially disposed' (324) is set
        # against 'If afflicted' (326), so read as benefic influence (contestable) ->
        # H7.L.11a/b.
        condition=C.LordIn(7, 11),
        fortified="there may be more than one marriage or the native may associate with "
                  "many women",
        afflicted=None,
        general="there may be more than one marriage or the native may associate with many "
                "women",
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 323)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H7.L.11a", house=7, signification="spouse", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(7, 11), C.InfluencedBy("LORD_OF:7")),
        general="the 7th lord beneficially disposed - the wife may hail from a rich "
                "background or bring in much wealth",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 324)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H7.L.11b", house=7, signification="spouse", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(7, 11), C.AfflictedBy("LORD_OF:7")),
        general="the 7th lord afflicted - the native may marry more than once, but one wife "
                "may outlive him",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 326)),
    RuleRecord(
        id="H7.L.12", house=7, signification="spouse", group="lord_in_house", kind="evaluable",
        # 2026-10-13 House-7 sweep (0/12 correct): plain affliction (331), severe affliction
        # (333, 'But' makes it exclude the plain tier) and Venus+lord weakness (336) ->
        # H7.L.12a-c.
        condition=C.LordIn(7, 12),
        # ★ UNSOURCED AND INVERTED, REMOVED 2026-09-01. The slot read "possible spiritual
        # turn when both karaka and lord are STRONG". HTJAH-II:329-340 contains no spiritual
        # turn at all, and the only karaka+lord clause in it is the OPPOSITE condition with an
        # opposite outcome: "If both karaka and the 7th lord are WEAK, the native may only
        # dream of women but never marry" (336-337) — which the `afflicted` slot already
        # carries correctly. So the encoding asserted a favourable result on a strength
        # condition Raman states negatively. Found by the condition-fidelity audit while
        # reading the section in full; the earlier text sweep missed it because H7.L.12 was
        # not an at-risk record by the both-slots rule.
        general="there may be more than one marriage in the native's life; he may marry a "
                "second time clandestinely while the first wife is still alive; the "
                "native's wife may hail from a servant's family; he will be close-fisted "
                "and generally poor",
        fortified="there may be more than one marriage in the native's life; he may marry a "
                  "second time clandestinely while the first wife is still alive; the "
                  "native's wife may hail from a servant's family; he will be close-fisted "
                  "and generally poor",
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="malefic", source=Citation("HTJAH-II", 329)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H7.L.12a", house=7, signification="spouse", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(7, 12), C.AfflictedBy("LORD_OF:7"), C.Not(C.AfflictedBy("LORD_OF:7", C.FIRST_RATE_MALEFICS, min_count=2))),
        general="the 7th lord afflicted - he may marry a second time after losing the first "
                "wife by death or separation",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 331)),
    # Neutral: refines a parent that already votes for this placement.
    RuleRecord(
        id="H7.L.12b", house=7, signification="spouse", group="lord_in_house",
        kind="evaluable",
        condition=C.And(C.LordIn(7, 12), C.AfflictedBy("LORD_OF:7", C.FIRST_RATE_MALEFICS, min_count=2)),
        general="the affliction severe - the wife or husband may die or separate soon after "
                "marriage and there may be no second marriage; death may occur while "
                "travelling or abroad",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 333)),
    RuleRecord(
        id="H7.L.12c", house=7, signification="spouse", group="lord_in_house",
        # 2026-10-13: promoted from descriptive once IsStrong/IsWeak existed (effective
        # strength: Shadbala bar plus combustion/debility overrides). Neutral: refines a
        # parent placement.
        kind="evaluable",
        condition=C.And(C.LordIn(7, 12), C.IsWeak("Venus"), C.IsWeak("LORD_OF:7")),
        general="both the karaka Venus and the 7th lord weak - the native may only dream of "
                "women but never marry",
        fortified=None,
        afflicted=None,
        frame="LAGNA", varga="D1", polarity="neutral", source=Citation("HTJAH-II", 336)),
)
