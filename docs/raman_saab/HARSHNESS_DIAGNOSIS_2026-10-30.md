# Why the engine reads the Kanpur 4th, 5th, 7th and 10th as afflicted: a diagnosis

Date: 2026-10-30. User request: "find causes why it is too harsh … deep analysis and
introspection of engine should be done with utmost accuracy."

Scope and limits:
- **Diagnosis only.** No verdict, rule or threshold was changed.
- **Hold-out 3 stays sealed.**
- **Two kinds of numbers.** Golden figures are in-sample: the 389 confirmed conclusions the
  judge was built on. Random-chart figures describe the engine's behaviour, not accuracy.
- **Reproduce:** `python -m tools.raman_saab.harshness_mechanisms --population 1000`.

## 1. The Kanpur trace (10 Oct 1989, 15:15 IST)

Each sub-matter was replayed through `judge_signification` one step at a time. Each line below
shows the first verdict and every step that changed it.

| House | Headline | Matters | The one afflicted matter | The step that made it afflicted |
|---|---|---|---|---|
| 4th | afflicted | 5 of 6 favourable | property | clause 6: the karaka Mars is weak and a **maraka is active**. **No malefic rule fired at all**; the only rule is benefic (H4.L.10). |
| 5th | afflicted | 2 of 3 favourable | children | The clauses gave **favourable** (two strong pillars). The **fertility gate** then overrode it to afflicted, because the Beeja (Cancer) and Kshetra (Libra) sphutas both fail the odd/even test. |
| 7th | afflicted | 2 favourable, 3 mixed, 1 afflicted | marital happiness | The clauses gave **favourable**. The **decisive rule H7.C.82** ("two or more malefics afflicting the 7th") then made it afflicted. The two malefics are **Ketu in the 7th and Rahu's 7th aspect from the Lagna**: one nodal axis counted as two malefics. |
| 10th | afflicted | 4 favourable, 1 mixed, 1 afflicted | trade | The karaka Mercury has **6.86 rupas against Raman's bar of 7.0**, so he counts as "weak" though exalted. That makes the matter mixed, and the Navamsa (Mercury debilitated there) moves it one step to afflicted. |

Every headline follows the rollup rule: the worst sub-matter wins (`house_template._rollup`).
In all four houses one afflicted matter decides the headline.

## 2. The five mechanisms, measured

### M-A. The headline rule is never scored against Raman

The ratchet scores **sub-matters** (`test_goldens._signification_verdict`). The house headline,
the word the reader sees first, is never compared with Raman. So I scored it here against the
same 389 conclusions:

| What is compared with Raman's conclusion | Exact | Within one | Real errors | Says "afflicted" |
|---|---|---|---|---|
| the matter itself (the scored figure) | 260 | 349 | **40** | 141 |
| the house headline (worst matter) | 210 | 309 | **80** | 214 |
| majority of the house's matters | 191 | 319 | 70 | 82 |
| median of the house's matters | 194 | 315 | 74 | 76 |

Raman himself says "afflicted" in 168 of the 389.

- **The headline doubles the real errors** (40 to 80) and calls "afflicted" 214 times against
  Raman's 168.
- **Neither simple alternative rule does better on exact matches.** So the honest fix is not a
  different single word. It is to lead each house with its matters, for example "favourable in
  5 of 6 matters; property afflicted". That changes no scored verdict.

**On ordinary charts** (1,000 random births, Indian cities, 1950-2005), the share of charts
whose headline is afflicted:

| House | Headline afflicted | Afflicted although most of its matters are favourable |
|---|---|---|
| 4th | 52% | 18% |
| 5th | 85% | 30% |
| 7th | 63% | 13% |
| 10th | 64% | 31% |
| 3rd | 69% | 27% |
| 8th | 69% | 30% |

So the engine heads two careers in three, and five 5th houses in six, "afflicted". Kanpur is
typical, not an outlier.

### M-B. The fertility gate denies on a test Raman's own worked charts do not follow

`_fertility_gate` makes children **afflicted, overriding any other verdict**, when both the Beeja
and the Kshetra sphuta fail their odd/even test (HTJAH-I:5521-5524). Three problems, each from
Raman's own text as summarised in `methodology/house_05_putra.md`:

1. **Raman's worked Chart 88 contradicts the parity-only test.** Its Beeja falls in Cancer, an
   even sign (the same sign as Kanpur's Beeja). Raman still judges "**Beeja is strong**",
   because the point holds the Sun, sits in a benefic sign, is aspected by Jupiter, and is odd
   in the Navamsa (HTJAH-I:5529-5551). In his Chart 89 the Kshetra falls in an odd sign, and he
   judges it "fertile → birth of children" (HTJAH-I:5553-5582). The engine's parity-only test
   reads both points as weak.
2. **The relief clauses are left out, but the denial is kept.** The code says so itself: the
   aspect, malefic-sign and Rahu clauses (HTJAH-I:5524-5527) "are deferred". Leaving out the
   clauses that can rescue a point, while keeping a decisive denial, makes the gate one-sided.
3. **Raman reads one point per native: Beeja for a man, Kshetra for a woman.** The methodology
   card says "Route by chart sex". The engine has no sex input, so it requires both points to
   fail.

**How often it fires.** Both points fail in **52% of random charts**. That is simply the odds:
each point passes about 28% of the time. The gate changed the verdict in 32% of random charts.

**On Raman's charts.** Of the 12 confirmed rows where it decided an afflicted reading, Raman
says afflicted 9 times, mixed once and favourable twice. But the children pool is 26 afflicted
rows out of 34, because Raman's denial chapter supplies most of them. A gate that says
"afflicted" half the time will look right on such a pool. Raman's favourable children charts
fare badly: of his 8 non-afflicted children rows, the engine reads 7 as afflicted.

### M-C. One nodal axis counted as two malefics (H7.C.82)

H7.C.82 is one of the decisive rules: it overrides a favourable preponderance. Its condition
counts **distinct natural malefics** that occupy or aspect the 7th. Rahu and Ketu are always
opposite, and the Raman engine counts the nodes' 7th aspect (locked 2026-10-13). So **a node in
the 7th always brings the other node's aspect with it.** The single axis satisfies "two or more
malefics" by itself.

The rule's own record cites Saturn + Mars as the classic case (HTJAH-II:562), and Mars + Ketu.

- **On Raman's charts:** no confirmed golden row fires it on the nodes alone. All 6 of its
  scored firings involve another malefic, and all 6 are Raman-afflicted, so the rule is sound
  there.
- **On random charts:** it fires on the nodes alone in 3% of charts. Kanpur is one of them.
  That firing has no support in any of Raman's charts.

### M-D. Maraka pressure deciding non-death matters

Clause 6 makes a matter afflicted when one pillar is weak and a maraka is active, even when no
malefic rule fired.
- **On Raman's charts**, where it decided an afflicted reading, Raman agrees 7 times in 14, and
  5 of the 14 are matters he calls favourable.
- **On random charts** it decides about 8% of all matters.

This is the known M1 question. The pre-registered M1 variant was measured on 2026-10-28 and
**held**, because real errors in Notable Horoscopes rose 22 to 24 (FIDELITY_FIXES_PREREG
Addendum 12). Kanpur's property is this case. Nothing new to decide here unless you want M1
revisited.

### M-E. The strength cliff

Pillars are strong or weak by a hard cutoff at Raman's Shadbala bars. Mercury at 6.86 rupas
against 7.0 is "weak", though exalted. The engine already admits that the bars are reference
values on a continuum (GBB-1:38-60), and `_marginal_karaka_gate` softens the cliff, but **only
for marriage**. Kanpur's trade matter falls on the cliff.

The Navamsa push that followed is legitimate. It is within the one-step rule, and on Raman's
charts it agrees 21 times in 27 where it decided an afflicted reading.

## 3. What I recommend, in order

1. **Show each house by its matters, not by the worst one.** This is a presentation change
   only: keep the matter verdicts and the full data, and replace the single headline word with
   the count and the afflicted matters named. It cannot move the 260/389 figure, and it removes
   a headline that doubles the real errors. Under the report-completeness rule, adding the
   breakdown is always allowed; dropping or replacing the headline word is your call.
2. **Pre-register a fertility-gate variant.** Two options, measured the usual way:
   - deny only when a sphuta also fails the relief clauses Raman prints (HTJAH-I:5524-5527);
   - or let both-weak lower the verdict one step instead of deciding it.

   The reading must reproduce Raman's Charts 88-90 as he wrote them.
3. **Pre-register an H7.C.82 variant** that counts the nodal axis as one affliction. The pool
   cost is expected to be nil, because no scored row fires on the nodes alone. The doctrine
   question goes to an engine-blind reviewer first.
4. **M-D and M-E stay as they are.** M1 was measured and held. A general marginal band was
   tried before and clipped a correct NH.chart_54 H10, so a new version needs its own
   pre-registration.

Hold-out 3 is sealed for the next pre-registered variant. Spending it on (2) or (3) is your
decision.
