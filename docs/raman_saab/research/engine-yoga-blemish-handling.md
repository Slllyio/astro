---
title: "How the engine handles a strong positive with one small negative (yoga + blemish)"
kind: analysis
topic: judge-mechanism
measured: true
updated: 2026-10-24
---
# A strong positive with one small negative: what the engine does today

**Question.** A chart has a good combination (a yoga, or benefic rules) for a matter, plus one
small negative. How does the Raman engine turn that into a verdict, and where does it go wrong
against Raman's labels?

**Method.** I exported the committed engine (`git archive HEAD`, commit 0472732, so the
uncommitted R2 patch is *not* included) and re-ran every scored row through the harness's own
`build_chart` and `judge_signification`. A mirror of `_decide` labelled which clause fired, and
each later layer was replayed in order to see which one moved the verdict. Asserts confirmed the
replay matches the engine on every row. The figures reproduce the published ones exactly:

| Set | Rows | Exact | Within one | Real errors |
|---|---|---|---|---|
| Golden pool | 389 | 275 | 351 | 38 |
| Hold-out 1 (3HC) | 36 | 23 | 28 | 8 |
| Hold-out 2 (NH 1-15, HTJAH) | 134 | 55 | 98 | 36 |

Both hold-outs were already scored and spent; using them for diagnosis is allowed now, but
nothing below may be tuned against them. Scripts and the per-row dump are in
`/tmp/claude-0/-home-claude/0462ad3d-edef-5079-8a7a-8785976d2ea4/scratchpad/blemish/`
(`dump.py`, `analyse.py`, `a2.py`, `cf.py`, `rows.json`). No file under `app/` or `tests/` was changed.

---

## 1. The mechanism today, in one paragraph

Rule evidence reaches the verdict as **two yes/no flags**: did any benefic rule fire, and did
any malefic rule fire. The amount, the strength and the target of either side are never read.
`_decide` clause 2 (`house_template.py:590`, `if L.fired_benefic and L.fired_malefic:`) treats
**one** malefic exactly like ten. Once both sides have fired, the evidence is thrown away and the
matter is settled by things that are not the evidence at all: the lord and karaka Shadbala
pillars, then the navamsa. Yogas are not part of that weighing. They act afterwards, in
`_yoga_modulate` (`:1377`), and they can only move a verdict that is still "mixed". A dhana or
raja yoga's lift is **cancelled outright by any fired malefic** (`:1427`,
`elif "dhana" in kinds and not lead.fired_malefic`, and the same test for raja). So the answer to
"positive yoga + one small negative" is: the small negative turns the matter into a
contradiction, the yoga is disqualified, and the verdict comes from Shadbala or the D9.

### The path a "positive + one negative" row takes

1. **Clause 1 / 1.5** (karaka veto; dusthana matters) catch a few rows. Not the topic here.
2. **Clause 2, the contradiction clause.** Entered whenever both polarities fired.
   - No pillars (a stated-position chart, no Shadbala) → **mixed by construction**. The P2
     exception in `_navamsa_modulate` then stops the D9 from moving it.
   - 3 weak pillars → afflicted. 2 strong pillars → favourable, unless the D9 "weakens" or the
     lord is combust or debilitated (B1). Either of those exceptions drops the row to mixed.
   - Otherwise (pillars split) → mixed.
3. **`_navamsa_modulate`** turns a contradiction-mixed into **afflicted** when the D9 "weakens",
   and into favourable when it "confirms". The one-sided-rasi guard does not apply, because both
   sides fired.
4. **`_yoga_modulate`** only looks at a remaining "mixed". Arishta yogas are blocked when both
   sides fired. Dhana yogas, and raja yogas that pass the vitality test, are blocked whenever
   **any** malefic fired.
5. **Late floors and gates** (H11 dhana floor, powerful dhana-kendra floor, blemishless Venus,
   yogakaraka in the Lagna) are the only places where a positive overrides a negative. Each is
   scoped to one house or matter.

Without the small negative, the same chart usually lands in clause 5 (both pillars strong, no
malefic): a **decisive favourable** that the D9 is not allowed to move. One extra malefic rule
moves the row from "decisive favourable" to "whatever the navamsa says". That cliff is the core
of the problem.

---

## 2. Q1: Raman favourable (or mixed), engine more negative

| | Pool | HO1 | HO2 | All |
|---|---|---|---|---|
| Engine more negative than Raman | 60 (17 real) | 9 (5) | 53 (18) | **122 (40)** |
| ...of which both polarities fired | 36 | 4 | 35 | **75** |
| ...with at most 2 malefic rules | 18 | 2 | 20 | **40** |
| ...with exactly 1 malefic rule | 7 | 1 | 12 | **20** |
| ...where benefic rules outnumber malefic | 12 | 2 | 20 | **34** |
| malefic-only (no positive present) | 16 | 3 | 16 | 35 |
| benefic-only | 8 | 1 | 2 | 11 |

So **75 of the 122 over-negative misses (61%)** are rows where the positive was present and the
engine still went negative or mixed. **40** are the narrow "positive + one or two negatives" shape,
and **20** have exactly one negative.

**Which clause produced them (the 75):**

| Clause | Rows |
|---|---|
| 2, pillars split → mixed (D9 may then drop it) | 30 |
| 2, no pillars (stated chart) → mixed, frozen | 26 |
| 2, pillars strong but the D9 weakens → mixed → D9 → afflicted | 14 |
| 2, pillars strong but B1 (lord combust or debilitated) → mixed | 4 |
| 2, pillars strong → favourable, then a late gate demoted it | 1 |

71 of the 75 were settled inside `_decide`. The late gates moved only 4 (saptamsa 3,
fertility 1), so the late gates are not the cause.

Raman → engine on the 75: favourable→mixed 52, favourable→afflicted 16, mixed→afflicted 7.

**The inversions come through the navamsa.** Of the 16 favourable→afflicted inversions among
contradiction rows, **15 had D9 = "weakens"**: 10 through "pillars strong but the D9 weakens", 5
through "split, then the D9 drops it". Seven of those 15 have only one or two malefic rules. In
other words, the small negative does not afflict the matter by itself. It **opens the door** that
lets a D9 proxy decide, and the D9 proxy is what inverts. Examples:

- `HTJAH-I.h5_16 H5/children`: benefic H5.L.2 and H5.C.1, one malefic H5.C.10. Both pillars
  strong, D9 weakens → **afflicted**. Raman: **favourable**.
- `NH.chart_1 H4/mother` (HO2): benefic H4.L.4 and H4.P.Jupiter, one malefic H4.P.Sun. Both
  pillars strong, D9 weakens → **afflicted**. Raman: **favourable**.
- `NH.chart_12 H4/education` (HO2): five benefic rules (H4.L.1, H4.P.Mercury, H4.P.Venus,
  H4.C.31, H4.C.32), one malefic H4.C.49. D9 weakens → **afflicted**. Raman: **favourable**.
- `3HC.chart_17 H1/self` (HO1): benefic H1.C.33 and H1.C.30, one malefic H1.C.37 → **afflicted**.
  Raman: **favourable**.

**The non-answers come through "no pillars".** On the 42 contradiction rows the engine leaves
"mixed" because no pillars exist, Raman is favourable 25, afflicted 13 and mixed 4. On the 34 it
leaves "mixed" from split pillars: favourable 23, afflicted 5, mixed 6. **The engine's
contradiction-mixed is right about 13% of the time.** When the engine says mixed after both
sides fired, Raman most often meant favourable.

### The yoga is disqualified by the blemish

**22 rows** reach `_yoga_modulate` as "mixed" with a routed dhana yoga, or a vital raja yoga,
that would have lifted them, and are held back only because a malefic rule fired. Raman's
labels: favourable 18 (two of those still reach favourable through the H11 dhana floor), afflicted 4.

- `NH.chart_62 H2/wealth`: Y.DHANA.CHAIN routed to wealth. The only malefic is H2.C.69, the
  chart-wide Dwirdwadasa dictum, which WHY_273 already lists as over-firing. Engine **mixed**,
  Raman **favourable**.
- `3HC.chart_65 H2/wealth` (HO1): Y.DHANA.CHAIN and Y.DHANA.122. One malefic, H2.C.43. Engine
  **mixed**, Raman **favourable**.
- `NH.chart_33 H10/career` and `NH.chart_11 H10/career` (HO2): Y.RAJA.KT, vital. One malefic,
  H10.P.Rahu. Engine **mixed**, Raman **favourable** on both.
- `NH.chart_6 H10/status_honour` (HO2): Y.RAJA.KT. One malefic, H10.C.33m. **mixed** vs
  **favourable**.

3 of the 4 Raman-afflicted rows in this set are **H9 father** rows (NH chart_17, chart_19,
NH chart_11 in HO2). They are there only because `yoga_routes._FORTUNE_CAREER` routes the raja
yogas to H9 `father`, which is a father's-longevity matter. The 4th is HTJAH-I chart_44 wealth.
Whether a raja yoga should reach the father's life at all is a routing question for a citation
review. It is not a weighting question.

More widely, **27** rows where Raman says favourable and the engine does not carry a routed
dhana or raja yoga. And on the 108 Raman-favourable rows the engine misses as mixed or afflicted,
there are **413** detected raja and dhana yoga instances that are routed to no matter at all
(381 raja, 32 dhana). They are reported but carry no weight.

---

## 3. Q2: Raman afflicted, engine favourable or mixed, with a malefic present

| | Pool | HO1 | HO2 | All |
|---|---|---|---|---|
| Raman afflicted, engine favourable or mixed | 40 (21 fav) | 4 (3) | 14 (9) | 58 (33) |
| ...with at least one malefic fired | 28 (9 fav) | 4 (3) | 8 (3) | **40 (15 fav)** |

How the malefic was discounted (the 40):

| Clause → verdict | Rows |
|---|---|
| 2, no pillars → mixed | 13 |
| **2, pillars strong → favourable** | **11** |
| 2, split → mixed | 5 |
| 8, borderline → mixed | 3 |
| 2, split → favourable (D9 confirms) | 3 |
| 2, B1 → mixed | 2 |
| other (6, 1.5 + catastrophic gate, 3 + longevity span) | 3 |

Number of malefic rules on those rows: 1 → 12, 2 → 8, 3 → 10, 4 or more → 10. So the engine
discounts a negative **not because it is small** but because two Shadbala pillars read "strong",
which they do for 89% of lords (WHY_273 §3). A malefic that Raman calls decisive loses to a
Shadbala pass exactly as a blemish does. Examples:

- `HTJAH-I.chart_42 H2/wealth`: one malefic, H2.C.69 (Dwirdwadasa). Pillars strong →
  **favourable**. Raman: **afflicted** ("Mars in 2nd; Jupiter (3L+12L) aspects the 2nd, both
  bad; 2nd lord Saturn in 3rd...").
- `NH.chart_52 H5/children`: one malefic, H5.C.39 (the Putrakaraka affliction family).
  Split → favourable. Raman: **afflicted** ("These afflictions rendered the native issueless").
- `HTJAH-I.x68 H4/mother`: one malefic, H4.C.48 → **favourable**. Raman: **afflicted**.
- `3HC.chart_133 H6/disease_chronic` (HO1): one malefic, H6.C.2 → **favourable**. Raman:
  **afflicted**.

Raman also states the yoga-failure case outright, in the opposite direction:
`3HC.chart_143 H10` reads "The Raja Yoga formed in the 10th house has been rendered infructuous"
(the engine agrees, afflicted, through the D9 route), and `3HC.chart_127 H10` reads "the yoga is
present in toto. Yet the subject is neither a king nor a big personality" (the engine says
favourable on a single H10.L.6 malefic). The engine has no representation of a yoga being
**spoiled**. Only Kemadruma has its cancellation folded in.

---

## 4. Q3: what is the negative's weight proportional to?

**In code: nothing. It is a presence flag, not even a vote count.** `_decide`,
`_navamsa_modulate` and `_yoga_modulate` test only `bool(fired_malefic)`. Rules carry no weight
field (`RuleRecord` has polarity only). A count is read in just three places, all of them
narrow demotion gates: the catastrophic gate (3 or more malefics for incarceration, left eye and
accidents), `_malefic_occupancy_gate` (2 or more cruel malefics occupying the house and the lord
not strong, favourable → mixed) and `_marital_bond_gate` (2 or more cruel malefics in the 8th
from the Moon). Things that are **not** read when weighing a negative:

- **The afflictor's strength.** Not read. Some rule conditions build in their own exemptions,
  for example H3.C.9 "exempted when..." and R2's proposed "dignified malefic" exclusion for
  H9.B.23/24.
- **A benefic aspect on the afflictor.** Not read by the judge. Only individual rule or yoga
  conditions include it, for example Nishturabhashi cancelled by Jupiter's aspect.
- **Whether it touches the lord, the karaka or the house.** Read only indirectly: through the
  karaka veto (clause 1), through B1 (a combust or debilitated lord blocks the strong-pillar
  lift), and through the 13-rule `_DECISIVE_AFFLICTION_RULE_IDS` list (`:165`). Every other
  malefic weighs the same.

The engine already has the **seed of a weight scale**, but uses it in only two lists:
`_DECISIVE_AFFLICTION_RULE_IDS` (13 rules that afflict even against strong pillars) and
`_MANNER_RULE_IDS` (`:144`, five rules that may corroborate but never confirm alone). Everything
else sits on one undifferentiated middle tier.

**Does the data say the negative's identity matters? Yes.** On all 275 rows where both sides
fired:

| Single malefic rule, by kind | Rows | Raman favourable | Raman afflicted |
|---|---|---|---|
| planet-in-house (a malefic occupant) | 19 | **16** | 2 |
| lord-in-house | 12 | 8 | 4 |
| combination | 40 | 19 | **14** |
| navamsa qualifier | 3 | 3 | 0 |

A lone malefic *occupant* is a blemish Raman reasons past 84% of the time. The engine already
gets 12 of those 19 right. Lone *combinations* split, and the Raman-afflicted ones are mostly
lord- or karaka-targeted. On the 32 Raman-afflicted "blemish-shape" rows (1-2 malefics,
benefics ≥ malefics), the deciding negatives are H5.C.39/40/41 (Putrakaraka and 5th-lord
afflictions), H9.A.13 (Sun afflicted by Saturn or Rahu), H9.L.12 (9th lord in the 12th),
H7.C.86, H4.C.18a and H3.C.9/10. On the Raman-favourable side the commonest negatives are general
dicta and chart-wide conditions: H1.N.66, H2.C.69, H1.C.28b, H9.B.23/24, H10.C.33m.

**Neither existing extreme works.** On those 129 blemish-shape rows, *ignoring* the negatives
entirely (re-running `_decide` with `fired_malefic=()`) raises exact from 72 to 76 but **raises
real errors from 16 to 39**: 16 of the 18 Raman-afflicted rows the engine currently gets right
become inversions. Counting rules (R3b and R4, which break ties by benefic count against malefic
count) was already pre-registered and failed, raising inversions (FIDELITY_FIXES_PREREG Addenda
2 and 4). The count does carry *some* information (Raman favourable 70% when benefics outnumber,
39% when malefics do), but a count cannot tell a decisive lord affliction from a background
dictum. **The information is in what the negative strikes, not in how many negatives there are.**

---

## 5. Q4: yoga-bhanga and cancellation in code

| Mechanism | Exists? | Gates the yoga → house verdict? |
|---|---|---|
| Kemadruma bhanga (3HC:2182-2185) | yes: `Y.KEMADRUMA` fires only `And(_Kemadruma, Not(_KemadrumaBhanga))` | yes, because the yoga simply doesn't fire |
| Nishturabhashi, cancelled by Jupiter's aspect (3HCC:10205) | yes, inside the condition | unrouted, so it never affects a verdict |
| Neecha-bhanga | yes (`primitives/bhangas.neecha_bhanga`); also Y.RAJA_250 Neechabhanga Raja | feeds **planet strength** (`_qualitative_strong`, `_effective_strength`, `_lord_hard_afflicted`), not yogas |
| Raja-yoga vitality (HTJAH-I:641-645, 12°) | yes: `yogas.raja_yoga_vital` | yes, but only `Y.RAJA.KT` can pass. Every other raja yoga is "noted" |
| **Raja Yoga Bhanga 298/299, Rajabhrashta** (3HCC:10246, :10213) | detected as kind `other` | **no.** Unrouted, so they never cancel the raja yoga they defeat. Rajabhrashta's own effect text says "when stronger than the Raja yogas, defeats them" |
| Yoga spoiled by affliction or weakness of its **causing planets** | **no** general mechanism | no. The only stand-in is the blanket `not lead.fired_malefic`, which tests the *matter's* rules, not the yoga's planets |
| Parivartana direction (an exchange can transmit affliction as well as relief) | coded but both arms OFF | n/a |

So the one place a cancellation should act, a raja yoga met by its own bhanga, is not wired.
Meanwhile a malefic that has nothing to do with the yoga's planets (H2.C.69 is chart-wide;
H10.C.33m is "malefics in the 10th from Lagna or Moon") cancels the yoga in full.

---

## 6. Where a better rule would plug in (design points, not thresholds)

None of these is a proposal to tune a threshold to the goldens. Each would need to be assigned
from Raman's citations by an engine-blind reviewer, pre-registered, and tested on a **fresh**
sealed hold-out (both current hold-outs are spent).

1. **A per-rule evidence tier, attached in `_bucket_fired` (`:1119`) and read at clause 2
   (`:590`).** Generalise the two lists that already exist (`_DECISIVE_AFFLICTION_RULE_IDS` /
   `_MANNER_RULE_IDS`) into three tiers set by each rule's citation: *decisive* (strikes the
   lord or karaka of the matter, or Raman reasons "this denies"), *ordinary*, and *blemish*
   (background dicta and chart-wide conditions Raman states and then reasons past: H7.KD.1,
   which Raman himself calls "misunderstood and misapplied", H2.C.69, H1.N.66, H1.C.28b, lone
   occupants). A blemish-tier malefic would **not open the contradiction clause**. It would be
   recorded, and would lower `degree` in `_compute_degree` (`:733`) instead of changing the
   verdict. That is Raman's "favourable, with a qualification".
2. **`_navamsa_modulate` (`:481`).** When the only malefic testimony is blemish-tier, the D9
   should not be allowed to turn a contradiction-mixed into afflicted. 15 of the 16
   favourable→afflicted inversions on contradiction rows pass through this step. This sits
   beside the existing one-sided-rasi and P2 guards, with the same reasoning: the navamsa is
   co-testimony, not a tie-breaker for a contradiction that is really a blemish.
3. **`_yoga_modulate` (`:1377`, the `not lead.fired_malefic` tests).** Replace the blanket
   veto with Raman's own two questions: is the yoga **cancelled** (wire Y.RAJA_YOGA_BHANGA and
   Rajabhrashta as gates on the raja lift, and test affliction to the yoga's *causing planets*),
   and is the matter carrying **decisive** affliction (the tier from point 1)? A blemish on the
   house would no longer disqualify a yoga that is intact. Separately, have a citation review
   check whether raja yogas belong on the H9 `father` route in `yoga_routes._FORTUNE_CAREER`.

**Expected reach (diagnostic upper bounds, not forecasts):** 39 over-negative rows across all
three sets that have the blemish shape (one or two malefic rules, benefics at least as many),
8 of them real errors. 22 rows where a
yoga is blocked only by a malefic being present. 15 navamsa-driven inversions. On the other side,
11 Raman-afflicted rows currently lifted by a "strong pillar" pass, which a decisive tier would
hold down. The ignore-the-negatives counterfactual (real errors 16 → 39) is the warning: tiering
must be decided by what the citation says the negative strikes, or it will simply trade misses
for inversions.

---

## Appendix: every row in the two error sets (golden pool, HO1, HO2)

Each line: key, set, Raman/engine labels, the `_decide` clause, any later layer that moved the
verdict, the lead-frame pillars and D9 status, the fired rule IDs on each side, and any routed
dhana or raja yoga.

### pool: Raman favourable/mixed, engine more negative, BOTH polarities fired

- `HTJAH-I.chart_17 H1/self` [pool] Raman **favourable** / engine **afflicted** — clause `2-contra-strong-but-D9-weakens`, layers -; lord Jupiter strong=True hard=False, karaka Sun strong=True, D9 weakens; benefic(5): H1.L.9, H1.C.33, H1.C.34, H1.C.30, H1.C.31; malefic(2): H1.P.Ketu, H1.C.1c
- `HTJAH-I.chart_53 H3/siblings` [pool] Raman **favourable** / engine **mixed** — clause `2-contra-split`, layers -; lord Mercury strong=False hard=False, karaka Mars strong=True, D9 neutral; benefic(2): H3.C.1, H3.C.8; malefic(2): H3.C.10, H3.C.34
- `HTJAH-I.chart_54 H3/siblings` [pool] Raman **favourable** / engine **mixed** — clause `2-contra-strong-but-B1`, layers -; lord Venus strong=True hard=True, karaka Mars strong=True, D9 neutral; benefic(4): H3.L.9, H3.C.5, H3.C.7, H3.C.8; malefic(4): H3.P.Ketu, H3.C.9, H3.C.10, H3.C.35
- `HTJAH-I.chart_46 H2/wealth` [pool] Raman **favourable** / engine **mixed** — clause `2-contra-split`, layers -; lord Venus strong=True hard=False, karaka Jupiter strong=False, D9 neutral; benefic(2): H2.C.40, H2.C.65; malefic(3): H2.P.Saturn, H2.C.69, H2.C.70
- `HTJAH-I.h4_05 H4/vehicles` [pool] Raman **favourable** / engine **mixed** — clause `2-contra-split`, layers -; lord Sun strong=True hard=False, karaka Venus strong=False, D9 neutral; benefic(2): H4.P.Moon, H4.C.45; malefic(1): H4.P.Saturn
- `HTJAH-I.h5_13 H5/children` [pool] Raman **mixed** / engine **afflicted** — clause `2-contra-strong`, layers ['fertility_gate']; lord Saturn strong=True hard=False, karaka Jupiter strong=True, D9 confirms; benefic(1): H5.C.1; malefic(3): H5.L.6, H5.P.Ketu, H5.C.39
- `HTJAH-I.h5_16 H5/children` [pool] Raman **favourable** / engine **afflicted** — clause `2-contra-strong-but-D9-weakens`, layers -; lord Mercury strong=True hard=False, karaka Jupiter strong=True, D9 weakens; benefic(2): H5.L.2, H5.C.1; malefic(1): H5.C.10
- `HTJAH-II.h7_07 H7/spouse` [pool] Raman **mixed** / engine **afflicted** — clause `2-contra-strong-but-D9-weakens`, layers -; lord Mars strong=True hard=False, karaka Venus strong=True, D9 weakens; benefic(2): H7.L.7, H7.C.7; malefic(3): H7.P.Mars, H7.KD.1, H7.C.86
- `HTJAH-II.h11_02 H11/elder_siblings` [pool] Raman **mixed** / engine **afflicted** — clause `2-contra-strong-but-D9-weakens`, layers -; lord Mercury strong=True hard=True, karaka Jupiter strong=True, D9 weakens; benefic(9): H11.L.1, H11.P.Jupiter, H11.P.Saturn, H11.C.1, H11.C.4, H11.C.8, H11.C.15, H11.C.31, H11.C.37; malefic(4): H11.C.2, H11.C.5, H11.C.21, H11.C.38
- `HTJAH-II.h12_01 H12/moksha` [pool] Raman **favourable** / engine **afflicted** — clause `2-contra-strong-but-D9-weakens`, layers -; lord Moon strong=True hard=False, karaka Saturn strong=True, D9 weakens; benefic(1): H12.L.8; malefic(2): H12.C.C5, H12.C.E3
- `HTJAH-II.h12_17 H12/moksha` [pool] Raman **favourable** / engine **mixed** — clause `2-contra-strong-but-B1`, layers -; lord Mercury strong=True hard=True, karaka Saturn strong=True, D9 neutral; benefic(2): H12.C.F4, H12.C.I3; malefic(5): H12.L.2, H12.P.Sun, H12.P.Moon, H12.C.C5, H12.C.E3
- `HTJAH-II.h12_18 H12/moksha` [pool] Raman **favourable** / engine **mixed** — clause `2-contra-strong-but-B1`, layers -; lord Mercury strong=True hard=True, karaka Saturn strong=True, D9 neutral; benefic(1): H12.C.F4; malefic(4): H12.L.1, H12.P.Saturn, H12.C.C5, H12.C.E3
- `HTJAH-II.h9_07 H9/father` [pool] Raman **mixed** / engine **afflicted** — clause `2-contra-split`, layers -; lord Mercury strong=False hard=True, karaka Sun strong=True, D9 weakens; benefic(2): H9.L.10, H9.B.31; malefic(4): H9.A.5, H9.A.20, H9.B.23, H9.B.24; routed +yoga: Y.RAJA.KT, Y.RAJA.910X
- `HTJAH-II.h9_09 H9/father` [pool] Raman **mixed** / engine **afflicted** — clause `2-contra-strong-but-D9-weakens`, layers -; lord Saturn strong=True hard=False, karaka Sun strong=True, D9 weakens; benefic(2): H9.B.29, H9.B.30; malefic(1): H9.A.13; routed +yoga: Y.RAJA.KT
- `HTJAH-II.h9_14 H9/fortune` [pool] Raman **favourable** / engine **mixed** — clause `2-contra-split`, layers -; lord Sun strong=True hard=False, karaka Jupiter strong=False, D9 neutral; benefic(2): H9.P.Jupiter, H9.B.21; malefic(5): H9.L.6, H9.P.Ketu, H9.B.22, H9.B.23, H9.B.24; routed +yoga: Y.RAJA.KT
- `NH.chart_33 H2/speech` [pool] Raman **favourable** / engine **afflicted** — clause `2-contra-split`, layers -; lord Mercury strong=False hard=False, karaka Jupiter strong=True, D9 weakens; benefic(2): H2.C.16, H2.C.32; malefic(4): H2.L.8, H2.C.64, H2.C.69, H2.C.70
- `NH.chart_37 H10/status_honour` [pool] Raman **favourable** / engine **mixed** — clause `2-contra-split`, layers -; lord Mercury strong=False hard=False, karaka Sun strong=True, D9 neutral; benefic(1): H10.C.56; malefic(3): H10.P.Saturn, H10.C.33m, H10.C.36
- `NH.chart_43 H1/self` [pool] Raman **favourable** / engine **mixed** — clause `2-contra-strong-but-B1`, layers -; lord Jupiter strong=True hard=True, karaka Sun strong=True, D9 neutral; benefic(2): H1.P.Jupiter, H1.C.29; malefic(2): H1.P.Mars, H1.C.1b
- `NH.chart_57 H1/body` [pool] Raman **favourable** / engine **afflicted** — clause `2-contra-strong-but-D9-weakens`, layers -; lord Moon strong=True hard=False, karaka Sun strong=True, D9 weakens; benefic(4): H1.L.10, H1.C.33, H1.C.34, H1.C.30; malefic(6): H1.P.Mars, H1.P.Saturn, H1.P.Rahu, H1.C.28, H1.N.66, H1.C.37
- `NH.chart_65 H2/wealth` [pool] Raman **favourable** / engine **afflicted** — clause `2-contra-strong-but-D9-weakens`, layers -; lord Moon strong=True hard=False, karaka Jupiter strong=True, D9 weakens; benefic(2): H2.C.65a, H2.C.66; malefic(2): H2.C.26, H2.C.43
- `NH.chart_18 H2/wealth` [pool, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Mercury strong=None hard=False, karaka Jupiter strong=None, D9 neutral; benefic(2): H2.P.Moon, H2.C.65a; malefic(2): H2.L.8, H2.C.26
- `NH.chart_23 H10/career` [pool, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-split`, layers -; lord Mars strong=None hard=False, karaka Sun strong=True, D9 neutral; benefic(2): H10.P.Sun, H10.P.Mercury; malefic(1): H10.L.12
- `NH.chart_27 H5/children` [pool, sparse] Raman **favourable** / engine **afflicted** — clause `2-contra-split`, layers ['saptamsa_gate']; lord Mercury strong=None hard=False, karaka Jupiter strong=True, D9 neutral; benefic(1): H5.C.1; malefic(3): H5.P.Ketu, H5.C.9, H5.C.39
- `NH.chart_29 H1/self` [pool, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Venus strong=None hard=False, karaka Sun strong=None, D9 neutral; benefic(3): H1.C.33, H1.C.34, H1.C.30; malefic(2): H1.L.8, H1.C.26a
- `NH.chart_30 H1/self` [pool, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Moon strong=None hard=False, karaka Sun strong=None, D9 neutral; benefic(6): H1.L.9, H1.P.Venus, H1.C.34, H1.N.56, H1.C.30, H1.C.31; malefic(3): H1.C.1a, H1.C.28b, H1.N.66
- `NH.chart_38 H2/wealth` [pool, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Jupiter strong=None hard=False, karaka Jupiter strong=None, D9 confirms; benefic(2): H2.C.6, H2.C.40; malefic(2): H2.C.43, H2.C.62; routed +yoga: Y.DHANA.CHAIN
- `NH.chart_49 H3/courage` [pool, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-split`, layers -; lord Saturn strong=None hard=True, karaka Mars strong=True, D9 neutral; benefic(4): H3.C.1, H3.C.7, H3.C.8, H3.C.30; malefic(6): H3.C.9, H3.C.10, H3.C.19, H3.C.34, H3.C.35, H3.C.39
- `NH.chart_56 H2/wealth` [pool, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Jupiter strong=None hard=False, karaka Jupiter strong=None, D9 confirms; benefic(2): H2.C.6, H2.C.65a; malefic(2): H2.C.26, H2.C.70
- `NH.chart_74 H5/children` [pool, sparse] Raman **favourable** / engine **afflicted** — clause `2-contra-nopillars`, layers ['saptamsa_gate']; lord Venus strong=None hard=True, karaka Jupiter strong=None, D9 weakens; benefic(3): H5.L.9, H5.P.Moon, H5.C.1; malefic(2): H5.P.Ketu, H5.C.9
- `NH.chart_16 H2/wealth` [pool, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Jupiter strong=None hard=False, karaka Jupiter strong=None, D9 neutral; benefic(3): H2.P.Mercury, H2.C.5, H2.C.6; malefic(3): H2.L.6, H2.P.Sun, H2.C.69
- `NH.chart_19 H2/wealth` [pool, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-split`, layers -; lord Mars strong=True hard=True, karaka Jupiter strong=None, D9 neutral; benefic(8): H2.P.Moon, H2.P.Mercury, H2.P.Jupiter, H2.C.5, H2.C.40, H2.C.47, H2.C.65, H2.C.66; malefic(7): H2.P.Sun, H2.P.Saturn, H2.C.1, H2.C.26, H2.C.28, H2.C.62, H2.C.69; routed +yoga: Y.VISHNU
- `NH.chart_48 H9/dharma` [pool, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Mars strong=None hard=False, karaka Jupiter strong=None, D9 weakens; benefic(1): H9.B.31; malefic(1): H9.L.12; routed +yoga: Y.RAJA.KT
- `HTJAH-II.x231 H11/gains` [pool] Raman **mixed** / engine **afflicted** — clause `2-contra-strong-but-D9-weakens`, layers -; lord Venus strong=True hard=False, karaka Jupiter strong=True, D9 weakens; benefic(4): H11.L.9, H11.C.8, H11.C.42, H11.C.43; malefic(1): H11.C.22
- `NH.chart_5 H1/self` [pool, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-split`, layers -; lord Moon strong=None hard=False, karaka Sun strong=True, D9 neutral; benefic(2): H1.C.33, H1.C.30; malefic(3): H1.L.12, H1.N.66, H1.M.G3
- `NH.chart_13 H1/self` [pool, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Sun strong=None hard=False, karaka Sun strong=None, D9 weakens; benefic(4): H1.L.4, H1.C.33, H1.N.44, H1.C.30; malefic(1): H1.N.66
- `NH.chart_14 H1/body` [pool, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Venus strong=None hard=False, karaka Sun strong=None, D9 confirms; benefic(2): H1.C.34, H1.C.30; malefic(2): H1.L.7, H1.N.66

### pool: Raman afflicted, engine favourable/mixed, malefic present

- `HTJAH-I.chart_20 H1/self` [pool] Raman **afflicted** / engine **mixed** — clause `2-contra-strong-but-B1`, layers -; lord Moon strong=True hard=True, karaka Sun strong=True, D9 neutral; benefic(4): H1.P.Mercury, H1.C.33, H1.C.34, H1.C.29; malefic(2): H1.C.28b, H1.M.G3
- `HTJAH-I.chart_31 H1/self` [pool] Raman **afflicted** / engine **favourable** — clause `2-contra-strong`, layers -; lord Jupiter strong=True hard=False, karaka Sun strong=True, D9 neutral; benefic(2): H1.L.3, H1.C.33; malefic(3): H1.C.26a, H1.C.26b, H1.N.66
- `HTJAH-II.chart_73 H8/death` [pool] Raman **afflicted** / engine **mixed** — clause `8-borderline`, layers -; lord Sun strong=True hard=False, karaka Saturn strong=True, D9 confirms; benefic(0): -; malefic(4): H8.C.21, H8.D.4, H8.D.5, H8.C.33
- `HTJAH-I.chart_60 H3/siblings` [pool] Raman **afflicted** / engine **favourable** — clause `2-contra-strong`, layers -; lord Mercury strong=True hard=False, karaka Mars strong=True, D9 confirms; benefic(3): H3.C.1, H3.C.7, H3.C.8; malefic(3): H3.L.11, H3.C.14, H3.C.35
- `HTJAH-I.chart_42 H2/wealth` [pool] Raman **afflicted** / engine **favourable** — clause `2-contra-strong`, layers -; lord Saturn strong=True hard=False, karaka Jupiter strong=True, D9 neutral; benefic(3): H2.L.4, H2.C.40, H2.C.65a; malefic(1): H2.C.69
- `HTJAH-I.chart_44 H2/wealth` [pool] Raman **afflicted** / engine **mixed** — clause `2-contra-split`, layers -; lord Mercury strong=False hard=False, karaka Jupiter strong=True, D9 neutral; benefic(1): H2.C.48; malefic(2): H2.P.Sun, H2.C.70; routed +yoga: Y.DHANA.CHAIN, Y.LAKSHMI
- `HTJAH-I.chart_48 H2/wealth` [pool] Raman **afflicted** / engine **favourable** — clause `2-contra-strong`, layers -; lord Mercury strong=True hard=False, karaka Jupiter strong=True, D9 confirms; benefic(2): H2.P.Venus, H2.C.40; malefic(2): H2.C.69, H2.C.70
- `HTJAH-II.h7_11 H7/coverture` [pool] Raman **afflicted** / engine **mixed** — clause `6-weakpillar`, layers -; lord Jupiter strong=False hard=False, karaka Venus strong=True, D9 neutral; benefic(0): -; malefic(2): H7.K.2, H7.C.49
- `HTJAH-II.h12_05 H12/expenditure` [pool] Raman **afflicted** / engine **mixed** — clause `2-contra-strong-but-B1`, layers -; lord Saturn strong=True hard=True, karaka Saturn strong=True, D9 neutral; benefic(3): H12.C.A3, H12.C.A6, H12.C.A7; malefic(13): H12.L.11, H12.P.Sun, H12.P.Moon, H12.P.Mars, H12.P.Mercury, H12.C.A2, H12.C.A9, H12.C.A10, H12.C.A16, H12.C.A17, H12.C.A19, H12.C.C5, H12.C.E3
- `HTJAH-II.h9_12 H9/father` [pool] Raman **afflicted** / engine **favourable** — clause `2-contra-strong`, layers -; lord Mars strong=True hard=False, karaka Sun strong=True, D9 neutral; benefic(2): H9.P.Moon, H9.B.21; malefic(3): H9.A.13, H9.A.18, H9.A.20; routed +yoga: Y.RAJA.910A
- `HTJAH-I.h6_04 H6/disease_chronic` [pool] Raman **afflicted** / engine **favourable** — clause `2-contra-split`, layers -; lord Venus strong=True hard=True, karaka Saturn strong=False, D9 confirms; benefic(1): H6.P.Jupiter; malefic(1): H6.L.2
- `NH.chart_39 H8/death` [pool] Raman **afflicted** / engine **mixed** — clause `8-borderline`, layers -; lord Mars strong=True hard=False, karaka Saturn strong=True, D9 neutral; benefic(0): -; malefic(3): H8.C.21, H8.D.3, H8.D.5
- `NH.chart_54 H9/fortune` [pool] Raman **afflicted** / engine **mixed** — clause `2-contra-split`, layers -; lord Mars strong=True hard=False, karaka Jupiter strong=False, D9 neutral; benefic(1): H9.B.29; malefic(3): H9.P.Ketu, H9.B.23, H9.B.24
- `NH.chart_75 H1/self` [pool] Raman **afflicted** / engine **mixed** — clause `2-contra-split`, layers -; lord Mars strong=True hard=False, karaka Sun strong=False, D9 neutral; benefic(3): H1.L.3, H1.C.33, H1.C.34; malefic(3): H1.P.Mars, H1.P.Rahu, H1.C.28
- `NH.chart_30 H9/fortune` [pool, sparse] Raman **afflicted** / engine **favourable** — clause `2-contra-strong`, layers -; lord Jupiter strong=True hard=False, karaka Jupiter strong=True, D9 confirms; benefic(4): H9.L.9, H9.P.Moon, H9.P.Jupiter, H9.B.21; malefic(3): H9.P.Rahu, H9.B.23, H9.B.24; routed +yoga: Y.RAJA.KT, Y.VIPAREETA
- `NH.chart_38 H9/father` [pool, sparse] Raman **afflicted** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Moon strong=None hard=False, karaka Sun strong=None, D9 neutral; benefic(3): H9.P.Mercury, H9.B.21, H9.B.31; malefic(5): H9.P.Sun, H9.A.2, H9.A.13, H9.B.23, H9.B.24; routed +yoga: Y.RAJA.KT, Y.RAJA.910X, Y.RAJA.910A
- `NH.chart_46 H9/father` [pool, sparse] Raman **afflicted** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Mercury strong=None hard=False, karaka Sun strong=None, D9 neutral; benefic(2): H9.P.Moon, H9.B.21; malefic(5): H9.P.Ketu, H9.A.7, H9.A.13, H9.B.23, H9.B.24; routed +yoga: Y.RAJA.KT, Y.RAJA.910X
- `NH.chart_46 H4/education` [pool, sparse] Raman **afflicted** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Saturn strong=None hard=False, karaka Jupiter strong=None, D9 confirms; benefic(1): H4.C.40; malefic(1): H4.L.6
- `NH.chart_52 H5/children` [pool, sparse] Raman **afflicted** / engine **favourable** — clause `2-contra-split`, layers ['saptamsa_gate']; lord Mars strong=None hard=False, karaka Jupiter strong=True, D9 neutral; benefic(2): H5.L.2, H5.C.1; malefic(1): H5.C.39
- `NH.chart_59 H3/siblings` [pool, sparse] Raman **afflicted** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Mercury strong=None hard=True, karaka Mars strong=None, D9 neutral; benefic(2): H3.C.6, H3.C.8; malefic(2): H3.P.Mars, H3.C.9
- `NH.chart_64 H9/fortune` [pool, sparse] Raman **afflicted** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Mercury strong=None hard=False, karaka Jupiter strong=None, D9 neutral; benefic(1): H9.B.25; malefic(4): H9.P.Saturn, H9.P.Ketu, H9.B.23, H9.B.24
- `NH.chart_73 H4/mother` [pool, sparse] Raman **afflicted** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Mars strong=None hard=True, karaka Moon strong=None, D9 confirms; benefic(1): H4.L.10; malefic(2): H4.P.Saturn, H4.P.Rahu
- `NH.chart_73 H3/siblings` [pool, sparse] Raman **afflicted** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Jupiter strong=None hard=True, karaka Mars strong=None, D9 confirms; benefic(4): H3.L.10, H3.C.6, H3.C.7, H3.C.8; malefic(1): H3.C.10
- `NH.chart_16 H5/children` [pool, sparse] Raman **afflicted** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Jupiter strong=None hard=False, karaka Jupiter strong=None, D9 neutral; benefic(1): H5.C.2; malefic(2): H5.L.6, H5.P.Mars
- `NH.chart_17 H9/father` [pool, sparse] Raman **afflicted** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Venus strong=None hard=False, karaka Sun strong=None, D9 weakens; benefic(2): H9.P.Mercury, H9.B.21; malefic(4): H9.P.Sun, H9.A.2, H9.B.23, H9.B.24; routed +yoga: Y.RAJA.KT
- `NH.chart_19 H9/father` [pool, sparse] Raman **afflicted** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Mercury strong=None hard=False, karaka Sun strong=None, D9 confirms; benefic(2): H9.B.29, H9.B.30; malefic(6): H9.P.Rahu, H9.A.7, H9.A.13, H9.A.22, H9.B.23, H9.B.24; routed +yoga: Y.RAJA.KT
- `HTJAH-I.x67 H4/mother` [pool] Raman **afflicted** / engine **mixed** — clause `8-borderline`, layers -; lord Jupiter strong=True hard=False, karaka Moon strong=True, D9 neutral; benefic(0): -; malefic(3): H4.L.6, H4.C.1, H4.C.48
- `HTJAH-I.x68 H4/mother` [pool] Raman **afflicted** / engine **favourable** — clause `2-contra-strong`, layers -; lord Jupiter strong=True hard=False, karaka Moon strong=True, D9 confirms; benefic(1): H4.L.1; malefic(1): H4.C.48

### ho1: Raman favourable/mixed, engine more negative, BOTH polarities fired

- `3HC.chart_28 H2/wealth` [ho1] Raman **favourable** / engine **mixed** — clause `2-contra-split`, layers -; lord Mercury strong=False hard=False, karaka Jupiter strong=False, D9 neutral; benefic(4): H2.C.40, H2.C.51, H2.C.61, H2.C.66; malefic(2): H2.C.64, H2.C.69; routed +yoga: Y.DHANA.59, Y.LAKSHMI
- `3HC.chart_119 H10/status_honour` [ho1] Raman **favourable** / engine **afflicted** — clause `2-contra-strong-but-D9-weakens`, layers -; lord Mercury strong=True hard=True, karaka Sun strong=True, D9 weakens; benefic(1): H10.C.56; malefic(4): H10.P.Rahu, H10.C.33m, H10.C.36, H10.C.62
- `3HC.chart_121 H2/wealth` [ho1] Raman **favourable** / engine **afflicted** — clause `2-contra-strong-but-D9-weakens`, layers -; lord Moon strong=True hard=False, karaka Jupiter strong=True, D9 weakens; benefic(2): H2.C.40, H2.C.65; malefic(3): H2.C.43, H2.C.69, H2.C.70
- `3HC.chart_17 H1/self` [ho1] Raman **favourable** / engine **afflicted** — clause `2-contra-strong-but-D9-weakens`, layers -; lord Jupiter strong=True hard=False, karaka Sun strong=True, D9 weakens; benefic(2): H1.C.33, H1.C.30; malefic(1): H1.C.37

### ho1: Raman afflicted, engine favourable/mixed, malefic present

- `3HC.chart_58 H12/incarceration` [ho1] Raman **afflicted** / engine **mixed** — clause `1.5-dusthana`, layers ['catastrophic_gate']; lord Venus strong=True hard=False, karaka Saturn strong=True, D9 confirms; benefic(0): -; malefic(2): H12.L.4, H12.C.E3
- `3HC.chart_133 H6/disease_chronic` [ho1] Raman **afflicted** / engine **favourable** — clause `2-contra-strong`, layers -; lord Venus strong=True hard=False, karaka Saturn strong=True, D9 neutral; benefic(2): H6.P.Mercury, H6.P.Venus; malefic(1): H6.C.2
- `3HC.chart_127 H10/status_honour` [ho1] Raman **afflicted** / engine **favourable** — clause `2-contra-strong`, layers -; lord Mercury strong=True hard=False, karaka Sun strong=True, D9 neutral; benefic(2): H10.C.33, H10.C.61; malefic(1): H10.L.6
- `3HC.chart_96 H5/children` [ho1] Raman **afflicted** / engine **favourable** — clause `2-contra-strong`, layers -; lord Mars strong=True hard=False, karaka Jupiter strong=True, D9 neutral; benefic(2): H5.L.11, H5.C.1; malefic(5): H5.P.Saturn, H5.P.Ketu, H5.C.10, H5.C.14, H5.C.15

### ho2: Raman favourable/mixed, engine more negative, BOTH polarities fired

- `HTJAH-I.chart_63 H1/health` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-split`, layers -; lord Jupiter strong=True hard=False, karaka Sun strong=None, D9 neutral; benefic(2): H1.P.Venus, H1.C.30; malefic(5): H1.L.8, H1.P.Mars, H1.C.1b, H1.C.28b, H1.N.54
- `HTJAH-II.chart_A#2 H9/father` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-split`, layers -; lord Moon strong=None hard=False, karaka Sun strong=True, D9 neutral; benefic(4): H9.L.5, H9.P.Jupiter, H9.B.21, H9.B.31; malefic(2): H9.A.7, H9.A.13; routed +yoga: Y.RAJA.KT
- `HTJAH-II.chart_B H9/long_journeys` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Saturn strong=None hard=False, karaka Jupiter strong=None, D9 neutral; benefic(6): H9.L.5, H9.P.Moon, H9.B.21, H9.B.25, H9.B.30, H9.D.41; malefic(2): H9.B.23, H9.B.24; routed +yoga: Y.RAJA.KT
- `HTJAH-II.chart_B H12/expenditure` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-split`, layers -; lord Mars strong=True hard=False, karaka Saturn strong=None, D9 neutral; benefic(2): H12.C.A3, H12.C.A6; malefic(3): H12.C.A4, H12.C.A16, H12.C.C5
- `HTJAH-II.chart_B#2 H9/father` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Saturn strong=None hard=False, karaka Sun strong=None, D9 neutral; benefic(5): H9.L.5, H9.P.Moon, H9.B.21, H9.B.25, H9.B.30; malefic(4): H9.A.5, H9.A.13, H9.B.23, H9.B.24; routed +yoga: Y.RAJA.KT
- `NH.chart_1 H1/body` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-split`, layers -; lord Venus strong=None hard=False, karaka Sun strong=True, D9 neutral; benefic(3): H1.L.3, H1.C.34, H1.C.30; malefic(3): H1.P.Moon, H1.C.1c, H1.C.28b
- `NH.chart_1 H3/courage` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-split`, layers -; lord Moon strong=True hard=False, karaka Mars strong=None, D9 neutral; benefic(4): H3.C.5, H3.C.6, H3.C.7, H3.C.8; malefic(5): H3.P.Mars, H3.P.Rahu, H3.C.9, H3.C.10, H3.C.35
- `NH.chart_1 H9/dharma` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Saturn strong=None hard=False, karaka Jupiter strong=None, D9 confirms; benefic(1): H9.D.43; malefic(3): H9.P.Ketu, H9.B.23, H9.B.24; routed +yoga: Y.RAJA.KT
- `NH.chart_1 H4/mother` [ho2, sparse] Raman **favourable** / engine **afflicted** — clause `2-contra-strong-but-D9-weakens`, layers -; lord Sun strong=True hard=False, karaka Moon strong=True, D9 weakens; benefic(2): H4.L.4, H4.P.Jupiter; malefic(1): H4.P.Sun
- `NH.chart_1#2 H1/self` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-split`, layers -; lord Venus strong=None hard=False, karaka Sun strong=True, D9 neutral; benefic(3): H1.L.3, H1.C.34, H1.C.30; malefic(3): H1.P.Moon, H1.C.1c, H1.C.28b
- `NH.chart_1#2 H4/education` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-split`, layers -; lord Sun strong=True hard=False, karaka Jupiter strong=None, D9 neutral; benefic(3): H4.L.4, H4.P.Jupiter, H4.C.37; malefic(1): H4.P.Sun
- `NH.chart_1#3 H4/happiness` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-split`, layers -; lord Sun strong=True hard=False, karaka Jupiter strong=None, D9 neutral; benefic(3): H4.L.4, H4.P.Jupiter, H4.C.20; malefic(2): H4.P.Sun, H4.C.19
- `NH.chart_11 H10/career` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Mars strong=None hard=True, karaka Sun strong=None, D9 confirms; benefic(1): H10.C.64; malefic(1): H10.P.Rahu; routed +yoga: Y.RAJA.KT
- `NH.chart_12 H3/courage` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Saturn strong=None hard=False, karaka Mars strong=None, D9 confirms; benefic(2): H3.C.6, H3.C.30; malefic(2): H3.P.Mars, H3.C.9
- `NH.chart_12 H4/education` [ho2, sparse] Raman **favourable** / engine **afflicted** — clause `2-contra-strong-but-D9-weakens`, layers -; lord Jupiter strong=True hard=False, karaka Jupiter strong=True, D9 weakens; benefic(5): H4.L.1, H4.P.Mercury, H4.P.Venus, H4.C.31, H4.C.32; malefic(1): H4.C.49
- `NH.chart_12 H10/status_honour` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-split`, layers -; lord Mercury strong=None hard=False, karaka Sun strong=True, D9 neutral; benefic(2): H10.L.4, H10.C.56; malefic(1): H10.C.33m
- `NH.chart_15 H5/children` [ho2, sparse] Raman **mixed** / engine **afflicted** — clause `2-contra-split`, layers ['saptamsa_gate']; lord Saturn strong=True hard=False, karaka Jupiter strong=None, D9 neutral; benefic(1): H5.C.1; malefic(1): H5.P.Rahu
- `NH.chart_2 H1/body` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-split`, layers -; lord Moon strong=None hard=False, karaka Sun strong=True, D9 neutral; benefic(4): H1.L.4, H1.C.33, H1.C.34, H1.C.30; malefic(1): H1.N.66
- `NH.chart_2 H12/moksha` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Mercury strong=None hard=False, karaka Saturn strong=None, D9 weakens; benefic(1): H12.C.G3; malefic(4): H12.L.11, H12.P.Rahu, H12.C.F1, H12.C.F2
- `NH.chart_2#2 H1/self` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-split`, layers -; lord Moon strong=None hard=False, karaka Sun strong=True, D9 neutral; benefic(4): H1.L.4, H1.C.33, H1.C.34, H1.C.30; malefic(1): H1.N.66
- `NH.chart_3 H3/courage` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Mercury strong=None hard=False, karaka Mars strong=None, D9 neutral; benefic(3): H3.C.6, H3.C.7, H3.C.8; malefic(2): H3.P.Mars, H3.C.9
- `NH.chart_3 H4/education` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Moon strong=None hard=False, karaka Jupiter strong=None, D9 neutral; benefic(2): H4.P.Mercury, H4.C.32; malefic(1): H4.C.49
- `NH.chart_4 H1/body` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Venus strong=None hard=False, karaka Sun strong=None, D9 neutral; benefic(6): H1.L.2, H1.C.26c, H1.C.33, H1.C.34, H1.C.29, H1.C.30; malefic(3): H1.P.Sun, H1.C.28b, H1.N.66
- `NH.chart_4 H4/education` [ho2, sparse] Raman **favourable** / engine **afflicted** — clause `2-contra-split`, layers -; lord Saturn strong=None hard=False, karaka Jupiter strong=True, D9 weakens; benefic(2): H4.C.37, H4.C.40; malefic(1): H4.L.8
- `NH.chart_4 H10/status_honour` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Moon strong=None hard=False, karaka Sun strong=None, D9 weakens; benefic(4): H10.L.5, H10.P.Jupiter, H10.C.33, H10.C.56; malefic(2): H10.C.33m, H10.C.35; routed +yoga: Y.RAJA.KT
- `NH.chart_4#2 H1/self` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Venus strong=None hard=False, karaka Sun strong=None, D9 neutral; benefic(6): H1.L.2, H1.C.26c, H1.C.33, H1.C.34, H1.C.29, H1.C.30; malefic(3): H1.P.Sun, H1.C.28b, H1.N.66
- `NH.chart_6 H9/dharma` [ho2, sparse] Raman **favourable** / engine **afflicted** — clause `2-contra-split`, layers -; lord Venus strong=None hard=False, karaka Jupiter strong=True, D9 weakens; benefic(1): H9.B.31; malefic(3): H9.P.Ketu, H9.B.23, H9.B.24; routed +yoga: Y.RAJA.KT
- `NH.chart_6 H1/self` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Mercury strong=None hard=True, karaka Sun strong=None, D9 neutral; benefic(2): H1.L.4, H1.C.30; malefic(2): H1.C.1c, H1.N.66
- `NH.chart_6 H10/status_honour` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Mercury strong=None hard=True, karaka Sun strong=None, D9 neutral; benefic(2): H10.L.4, H10.C.33; malefic(1): H10.C.33m; routed +yoga: Y.RAJA.KT
- `NH.chart_7 H2/speech` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-split`, layers -; lord Saturn strong=True hard=False, karaka Jupiter strong=None, D9 neutral; benefic(6): H2.P.Venus, H2.C.9, H2.C.40, H2.C.60, H2.C.66, H2.C.72; malefic(4): H2.P.Rahu, H2.C.26, H2.C.29, H2.C.69
- `NH.chart_7#2 H1/body` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Jupiter strong=None hard=False, karaka Sun strong=None, D9 neutral; benefic(3): H1.P.Mercury, H1.C.26c, H1.C.29; malefic(3): H1.L.12, H1.C.26b, H1.C.28b
- `NH.chart_8 H2/speech` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Jupiter strong=None hard=False, karaka Jupiter strong=None, D9 weakens; benefic(4): H2.L.9, H2.C.6, H2.C.16, H2.C.40; malefic(1): H2.C.69
- `NH.chart_8 H1/self` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-split`, layers -; lord Saturn strong=None hard=False, karaka Sun strong=True, D9 neutral; benefic(3): H1.L.10, H1.C.33, H1.C.30; malefic(2): H1.N.66, H1.M.G3
- `NH.chart_9 H1/body` [ho2, sparse] Raman **favourable** / engine **afflicted** — clause `2-contra-split`, layers -; lord Moon strong=None hard=False, karaka Sun strong=True, D9 weakens; benefic(2): H1.C.33, H1.C.30; malefic(4): H1.L.12, H1.C.1a, H1.N.66, H1.M.G3
- `NH.chart_9 H12/moksha` [ho2, sparse] Raman **favourable** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Mercury strong=None hard=True, karaka Saturn strong=None, D9 confirms; benefic(2): H12.C.F4, H12.C.I3; malefic(4): H12.L.10, H12.P.Moon, H12.C.C9, H12.C.E3

### ho2: Raman afflicted, engine favourable/mixed, malefic present

- `HTJAH-I.chart_63#2 H2/vision` [ho2, sparse] Raman **afflicted** / engine **favourable** — clause `2-contra-strong`, layers -; lord Saturn strong=True hard=False, karaka Jupiter strong=True, D9 confirms; benefic(4): H2.C.5, H2.C.21, H2.C.32, H2.C.66; malefic(3): H2.P.Sun, H2.C.43, H2.C.69
- `NH.chart_11 H9/father` [ho2, sparse] Raman **afflicted** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Jupiter strong=None hard=True, karaka Sun strong=None, D9 neutral; benefic(2): H9.B.29, H9.B.30; malefic(4): H9.A.7, H9.A.13, H9.A.17, H9.A.20; routed +yoga: Y.RAJA.KT
- `NH.chart_4 H12/expenditure` [ho2, sparse] Raman **afflicted** / engine **mixed** — clause `2-contra-split`, layers -; lord Mercury strong=True hard=True, karaka Saturn strong=None, D9 neutral; benefic(3): H12.C.A3, H12.C.A6, H12.C.A7; malefic(4): H12.P.Mercury, H12.C.A10, H12.C.C5, H12.C.C9
- `NH.chart_7 H1/self` [ho2, sparse] Raman **afflicted** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Jupiter strong=None hard=False, karaka Sun strong=None, D9 neutral; benefic(3): H1.P.Mercury, H1.C.26c, H1.C.29; malefic(3): H1.L.12, H1.C.26b, H1.C.28b
- `NH.chart_7 H8/longevity` [ho2, sparse] Raman **afflicted** / engine **favourable** — clause `3-trackB`, layers ['longevity_span']; lord Moon strong=None hard=False, karaka Saturn strong=True, D9 neutral; benefic(0): -; malefic(1): H8.P.Ketu
- `NH.chart_7 H9/father` [ho2, sparse] Raman **afflicted** / engine **mixed** — clause `2-contra-nopillars`, layers -; lord Sun strong=None hard=False, karaka Sun strong=None, D9 neutral; benefic(3): H9.L.1, H9.P.Moon, H9.B.21; malefic(1): H9.A.13; routed +yoga: Y.RAJA.KT
- `NH.chart_8 H4/education` [ho2, sparse] Raman **afflicted** / engine **mixed** — clause `2-contra-split`, layers -; lord Venus strong=True hard=False, karaka Jupiter strong=None, D9 neutral; benefic(6): H4.L.4, H4.P.Venus, H4.C.31, H4.C.34, H4.C.40, H4.C.41; malefic(1): H4.P.Rahu
- `NH.chart_8#2 H4/mother` [ho2, sparse] Raman **afflicted** / engine **favourable** — clause `2-contra-split`, layers -; lord Venus strong=True hard=False, karaka Moon strong=None, D9 confirms; benefic(2): H4.L.4, H4.P.Venus; malefic(1): H4.P.Rahu
