---
title: "Raman doctrine → engine improvement backlog"
kind: record
topic: doctrine
measured: false
updated: 2026-08-04
words: 7546
tags: [raman-saab, record, doctrine]
---
# Raman doctrine → engine improvement backlog

Source: the Phase-1 doctrine-extraction sweep over the prioritized B.V. Raman corpus
(GBB, HTJAH-I, HTJAH-II, HPA, 3HC). Companion to `doctrine_compendium.md` (the full
per-book digests with quotes). Every item carries the corpus citation it rests on.

Channels: `judge-mechanism` (house_template._decide), `shadbala` (primitives/shadbala),
`threshold` (MIN_REQUIRED / marginal handling), `new-rule` (RuleRecord / yoga detector),
`cancellation` (bhanga), `golden` (validation array).

Engine state at sweep time: ratchet **87/130**; uses 3/13 Raman books; the hard tail is
H3 chart_59/60 (siblings) and H7 chart_03/08 (marriage over-harsh).

---

## Recommended Phase-2 order (accuracy-per-effort, lowest-risk first)

| # | Item | Channel | Targets | Effort | Risk | Key citation |
|---|---|---|---|---|---|---|
| **B1** | **Three-factor comparative weighing** | judge-mechanism | H3 chart_59/60; general | high | med | HTJAH-I:3713/3788/3815/2760/2111 |
| **B2** | **Marginal-strength band** (near MIN_REQUIRED) | threshold | H7 chart_03/08 (Venus 5.37); general | med | low | GBB-1:38-60 |
| **B3** | **Non-death-marital maraka guard** | judge-mechanism | H7 chart_03/08 | low | low | HTJAH-II:2579 (Kuja=death, distinct from happiness) |
| **B4** | **Blemishless-/Yogakaraka-Venus marriage override** | new-rule | H7 chart_03/08 | med | med | HTJAH-II:1207, 368, 1474 |
| **B5** | **Yoga additions** (HPA 16 + 3HC Dhana/Lakshmi/Adhi/Nabhasa) | new-rule | H1/H2/H9/H10/H11; chart health | low–med each | low | HPA-20:65-229; 3HC:7632/8184/4256/2442 |
| **B6** | **HPA/HTJAH house rules** (Mars-in-7th, 4th-lord-in-12, dual-sign multiplicity) | new-rule | H4/H7 | low | low | HPA-19:247; HTJAH-I:8170; HTJAH-II:484 |

---

## B1 — Three-factor comparative weighing  `judge-mechanism`  (Phase 2a)
**Doctrine.** Raman weighs the three factors {Bhava, Lord, Karaka} *comparatively* — the
strongest dominates, and conversely a weak/combust dominant factor drags the matter down
even when another factor is strong. The engine currently treats the three pillars as
independent booleans (preponderance count), never *comparing* them.
- **HTJAH-I:3713** "Of the three elements, the third lord is more powerful than the third house or Mars." → strongest factor decides (chart_54, already correct).
- **HTJAH-I:3788** "Though the Karaka Mars is well disposed, the fact of the ruler of the third becoming combust and hence powerless, renders the third house weak. This stands against his having any brothers." → **chart_59 verbatim**: a combust/weak LORD denies the matter despite a strong karaka.
- **HTJAH-I:3815** "Though Jupiter is well-disposed... the Karaka and the third house are subject to affliction. The native has no brothers." → **chart_60 verbatim**: house+karaka afflicted → denied even with a good lord.
- **HTJAH-I:2760** "all the three factors... strong and well-fortified → immense wealth"; **HTJAH-I:2111** "a steady flow of fortune is assured if at least two of the three are well disposed."
- **HTJAH-I:13961** "the reckoning made from the strongest of these three centers gives good results."

**Engine note.** chart_59's lord is **combust** (Raman reads it weak) yet the Shadbala
pillar reads it strong — so comparative weighing must fold *combustion/placement* into the
factor's effective strength, not just total Shadbala. This is the same Shadbala-vs-placement
divergence the dusthana/fertility fixes addressed.
**Plan.** Extend `_decide` so that, when the pillars conflict, the *effective* strength of
each factor (Shadbala adjusted for combustion / debilitation-uncancelled / dusthana) is
compared; a decisively-weak dominant factor denies, a decisively-strong one carries. Guard
hard against regressing chart_54 and the broad ratchet. Shared judge → user sign-off.

**Status 2026-08-03 — BUILT, MEASURED, and ENABLED (user-signed-off).**
`house_template.B1_DOMINANT_FACTOR_GUARD` (default **True** since 2026-08-03) blocks clause 2's strong-pillar
FAVOUR lift when the LORD is hard-afflicted — combust or debilitation-uncancelled, the two
afflictions Raman reads as making a planet powerless in itself (HTJAH-I:3788). Dusthana
placement is deliberately excluded: Raman's dusthana readings are matter-specific (a strong
dusthana lord *feeds* an affliction, clause 1.5), so folding it in double-counts.
`primitives/effective_strength.py` supplies the facts; `_lord_hard_afflicted` reads them.

Measured A/B on the golden corpus — it splits the two ratchets:

| metric | guard OFF | guard ON |
|---|---|---|
| strict exact | 261/293 = 0.891 | **259/293 = 0.884 — SHIPPED** |
| within-1 ordinal | 281/293 = 0.959 | **283/293 = 0.966 — SHIPPED** |
| real errors (dist>=2) | 12 | **10 — SHIPPED** |

Both golden baselines were re-based in the enabling commit (the human-bump rule requires the
re-base and the change that earns it to land together). This is the **first deliberate DOWNWARD
strict re-base** in the project's lineage — accepted because a favourable<->afflicted INVERSION is
a worse doctrinal failure than a favourable/mixed boundary call, and the ordinal headline improves.

Per-chart: **+2 exact** (chart_18 H1, chart_52 H3 — both favourable→mixed, matching Raman),
**2 real errors downgraded to off-by-one** (chart_20 H1, h12_05 H12), **−4 exact**
(chart_54 H3, NH.chart_43 H1, h12_17 + h12_18 H12/moksha).

Two observations for whoever revisits this:
- chart_52 H3 improves while chart_54 H3 regresses — same matter, opposite directions — so a
  blanket lord-guard is not the whole of Raman's comparative weighing.
- **Half the regressions are H12/moksha**, and H12 is an atlas-proven INVERTED channel. Scoping
  the guard away from inverted channels would likely win on both metrics — but that is fitting
  to the goldens, which the MEASURED TRUTH lock warns is not accuracy. Deliberate call, not a
  silent tweak.
  - **SCOPING MEASURED AND CLOSED 2026-08-03 — the speculation above was WRONG.** A/B via the
    new `B1_GUARD_EXEMPT_HOUSES` knob (empty by default, read live, human-set only): exempting
    H12 (or H3+H12, the atlas set) gives exact 259→261 but within-1 283→282 and **real-errors
    10→11** — h12_05 H12/expenditure un-softens back to a favourable↔afflicted inversion. It
    does NOT win on both metrics; it trades back the exact failure category the guard was
    enabled to fix. Neither variant dominates, and the enablement decision already ranked fewer
    inversions above strict exact — so the guard stays UNSCOPED and the knob stays empty, kept
    only so a future re-measurement is a one-line experiment.

The tuner cannot find this: `tune_thresholds --holdout-lock` converges at iteration 0 (fit
0.907, holdout 0.841, no improving neighbour) because B1 is a *comparison*, not a weight, and
no swept knob expresses "the dominant factor decides".

## B2 — Marginal-strength band  `threshold`  (Phase 2b) — ✅ SHIPPED 2026-06-27
**Status.** `_marginal_karaka_gate` (house_template.py): a MARRIAGE verdict afflicted PURELY by a
marginally-weak Venus karaka (within 0.2 rupa of MIN_REQUIRED) + a STRONG lord + NO real malefic
re-decides treating the karaka as not-decisively-weak (GBB-8:303-312 bars are reference values,
GBB-1:38-60 continuity). Scoped to marriage (general form clips chart_54 H10); with/without-gate
diff changes exactly 1 confirmed verdict (chart_08 H7 afflicted→favourable, a dist-2 real-error
resolved); 0 regressions; reviewer SOUND-WITH-CAVEAT (KEEP/FLAG: n=1 + 0.2 band + 2-level lift,
re-examine if a 2nd marriage golden enters the band). Ratchet 206/240 → 207/240, real-errors 14→13.
**Doctrine.** GBB-1:38-60 — strength scales continuously (0 at bhava-sandhi → full at
madhya); there is no hard cliff. The engine's `MIN_REQUIRED` is a hard cutoff, so Venus at
5.37 vs the 5.5 bar reads "decisively weak" and trips clause-6/maraka on chart_03/08.
**Plan.** Introduce a *borderline band* (e.g. within ~0.3 rupa of MIN_REQUIRED → "marginal,"
neither decisively strong nor decisively weak), so a marginally-weak karaka doesn't drive a
decisive affliction. Re-examine via `tools/raman_saab/tune_thresholds.py` (do not hand-set).
**Note.** paksha-bala is ALREADY in the stack (`kala.py:81`, GBB-5:215-223) — the Venus gap
is threshold handling, not a missing bala.

## B3 — Non-death-marital maraka guard  `judge-mechanism`  (Phase 2c)  — ✅ SHIPPED 2026-08-17
**Status.** `MARAKA_NON_DEATH_GUARD`: `_build_frame_ledger` flags `marital_happiness`;
`_decide` suppresses only maraka's verdict-driving effect under it (karaka veto, fired
malefics, every other clause keep force; the ledger still records `maraka_active`;
spouse/coverture/death/longevity unflagged). Companion: `_marginal_karaka_gate`'s trigger
widened {afflicted}→{afflicted, mixed} (same strict conditions) because the maraka/cliff
artefact B2 was built to lift no longer forms as 'afflicted' — chart_08's confirmed
favourable preserved through the mixed route. Anti-double-move added per doctrine-review
HIGH: a 'mixed' produced by the `_marital_bond_gate` demote (HTJAH-II:2664/2877) is never
re-lifted (`bond_demoted` mirror of `blem_lifted`).
**Measured.** Canonical ratchet banner byte-identical: exact 259/293, within-1 283/293,
real-errors 10. Full A/B over all 450 H7 sig-verdicts on 225 goldens: exactly 5 flips, all
on rows with NO confirmed expectation (guard-invisible): h4_04 mh favourable→
insufficient-evidence; chart_35 / NH.chart_43 / NH.chart_65 mh afflicted→
insufficient-evidence; h7_12 mh afflicted→favourable (widowhood chart — death≠happiness
under this very doctrine; eyeball h7_12's prose on the corpus machine). On evidence-empty
ledgers the old artefact now surfaces as insufficient-evidence (not mixed) — arguably more
honest; recorded per the reviewer's MEDIUM.
**Corpus-machine follow-ups (content verification impossible on the cloud machine):**
(1) HTJAH-II:2579 verbatim — death-of-spouse reading; RECONCILE with H7.KD.1 which cites
the same line for a marital_happiness affliction (possible pre-existing sig
mis-assignment); (2) h7_12 prose vs the new favourable happiness reading; (3)
HTJAH-II:1436 (chart_08) spot-check of the mixed-trigger gate route.
### (original)
**Doctrine.** Kuja-Dosha / maraka pressure is about the *death* of the spouse (HTJAH-II:2579
"the death of the husband/wife will occur"), NOT marital *happiness*. The 7th is a maraka
house, so Venus-the-karaka lands in the maraka set and clause-6 over-afflicts a barely-weak
Venus on the happiness sub-matter.
**Plan.** Suppress `maraka_drives` for the `marital_happiness` signification (a non-death
matter), mirroring the LONGEVITY_GUARD pattern. Pairs with B2 to fix chart_03/08.
**Note.** The Kuja-Dosha *cancellation* (sign exemptions Gemini/Virgo, Cancer/Capricorn, …;
Leo/Aquarius wholly exempt; Mars+Jupiter/Moon conjunction) is **already encoded** in
`_KujaDosha` (HTJAH-II:2593-2601) — so this is NOT a missing-cancellation gap.

## B4 — Blemishless-/Yogakaraka-Venus marriage override  `new-rule`  — arm 2 ✅ SHIPPED 2026-08-17 (arm 1 shipped 2026-06-15)
**Status.** `H7.C.87`: benefic `marital_happiness` testimony — `IsYogaKaraka("Venus")` AND
Venus in a fixed sign {Taurus, Leo, Scorpio, Aquarius} → "fixity of affections"
(HTJAH-II:1474). Venus is Yogakaraka only for Capricorn/Aquarius lagnas (HTJAH-I:606
kendra+trikona sense — the conservative, under-firing reading of "Yogakaraka"). Fires on
20/225 goldens, changes 0 confirmed verdicts (incl. firing WITHOUT flipping the h7_16
troubled-marriage golden — the right stress case surviving). Doctrine-review
KEEP-WITH-FLAG: the record re-frames the backlog's "override of the dual-sign stigma" as
the karaka-QUALITY testimony itself (unconditional benefic, not conditioned on dual-sign
context) — **corpus-machine follow-up**: verify HTJAH-II:1474 verbatim for (a) the
technical vs loose "Yogakaraka" sense, (b) whether the statement is conditional on the
multiplicity context, (c) whether its subject is constancy/happiness or number of
marriages.
### (original)
**Doctrine.** HTJAH-II:1207/368 — a *blemishless* Venus (exalted/own/good-vargas,
unafflicted) as karaka+7th-lord aspecting the 7th → chaste devoted wife (favourable).
HTJAH-II:1474 — a *Yogakaraka* Venus in a fixed sign overrides the dual-sign multiplicity
stigma ("fixity of affections"). A positive karaka-quality gate the engine lacks.
**Plan.** A `marital_happiness` benefic rule: blemishless/Yogakaraka Venus → favourable
(complements B2/B3 for the chart_03/08 over-harsh).

## B5 — Yoga additions  `new-rule`  (partly done 2026-06-15)
**Done (coverage):** added 3 cited 3HC Dhana yogas to the detector — Y.DHANA.BAHU (Bahudravyarjana
1-2-11 cyclic chain, 3HC:8184), Y.DHANA.122 (Venus-5th + Saturn-11th in a Venus 5th-sign,
3HC:7632), Y.DHANA.125 (Sun own-5th + Moon&Jupiter-11th, 3HC:7645). They fire on **0 of the 130
goldens** (ratchet unchanged at 89) — pure additive fidelity for real charts via the H2/H11 dhana
modulation + dhana-floor. **Deliberately NOT added** (un-faithful or noisy): Lakshmi (#72) — its
faithful form needs "lagna-lord powerful" (Shadbala), and the geometry-only form over-fires (17/130);
the Sun-based Vesi/Vasi/Ubhayachari — near-universal (~85/130), inert (kind=other), snapshot noise.
**HPA named yogas — partly done 2026-06-27 (Phase 1A):** added 3 as additive fidelity (cited HPA-20,
reviewer-KEEP, zero-regression) — **Y.CHAMARA** (HPA-20:65, strict arm), **Y.SREENATHA** (HPA-20:90),
**Y.KHADGA** (HPA-20:184). Deferred (over-fire under the is_powerful proxy → need B1 effective-strength):
Shankha (102/164), Kahala (48/164), Lakshmi (strict dignity arm 16/164). Rejected as noise: Sun-based
Vasi/Vesi/Obhayachari. Un-mined: Sarada, Matsya, Mridanga, Konrma, Kusimia, Daridra, Rajju.

**RE-ATTEMPT CLOSED 2026-08-03 (negative, measured).** The B1 effective-strength measure now
exists and was applied to all four deferred yogas on the full 225-chart corpus. It does NOT
rescue them: Shankha 126→113/225 (50%), Kahala 76→67/225 (30%), Bheri 94→85/225 (38%) under the
strictly tighter gate (band=="strong" AND not decisively_weak). The original diagnosis was wrong
— the proxy was never the problem; the GEOMETRY is common by construction (mutual kendras ~1/3
base rate, movable-sign lords ~1/3), so no strength refinement can make these rare. Lakshmi's
strict arm IS rare (7/225 geometric, 3/225 gated) but only under one resolution of the
sentence's comma-parse, which Raman does not disambiguate and whose readings differ by an order
of magnitude — registering one would be choosing doctrine for him. All four stay deferred; the
unblocking condition is now "a more specific reading of Raman's text", not a better strength
measure. Scan: yoga_refire (session scratch, 2026-08-03); full numbers in yogas.py's deferral
note.

### (original)
Add to the yoga detector / rule sets (each cited; mostly low-risk, additive):
- **3HC Dhana yogas** (H2/H11 wealth): #122 Venus-5th+Saturn-11th (3HC:7632); #125 Sun-5th-own
  + Moon/Jupiter-11th (3HC:7645); Bahudravyarjana #133 lagna→2nd→11th→lagna lord chain
  (3HC:8184). Lakshmi #72 (3HC:4256, H9/H11). Adhi #7 (3HC:2442 — already present as Y.ADHI).
- **3HC Nabhasa** (chart health): Rajju/Musala/Nala (3HC:7083), Srik/Sarpa (3HC:7175),
  Harsha/Sarala/Vimala (3HC:7320 — the Vipareeta family; Y.VIPAREETA exists, audit overlap).
- **HPA named yogas** (HPA-20): Chamara, Shankha, Sreenatha, Bheri, Sarada, Kesari, Kahala,
  Mridanga, Khadga, Lakshmi, Kusimia, Konrma (raja/wealth/virtue, H1/H9/H10); Sun-based
  Vasi/Vesi/Obhayachari (mirror of lunar Sunapha/Anapha/Durudhura); Daridra (poverty),
  Rajju (foreign). Wire kind-scoped like the existing dhana/raja/arishta modulation.

## B6 — HPA/HTJAH house rules  `new-rule`  ✅ RESOLVED-BY-AUDIT 2026-06-25
**Settled:** all three proposed rules are ALREADY encoded; adding them would double-count
(the judge dedups by `rule.id`, not by placement). bphs-doctrine-reviewer pass confirmed,
HIGH confidence on B6.1/B6.2, MEDIUM on B6.3. Coverage pinned by
`tests/raman_saab/doctrine/test_b6_house_rules_coverage.py` so the rules can't silently
regress nor be re-added as duplicates. ZERO engine change → ratchet unchanged (89/130).
- **B6.1** Mars-in-7th → clashes/tensions/two wives (HTJAH-I:8170) — **COVERED** by
  `H7.P.Mars` (planets_in_7th.py:35, HTJAH-II:532 — the SAME dictum, near-verbatim), with the
  placement partitioned into `coverture` (`H7.C.60`) and `marital_happiness` (`H7.KD.1`).
- **B6.2** 4th-lord-in-12 → loss of ancestral property (HPA-19:247) — **COVERED** by
  `H4.C.3` (combinations.py:116, HTJAH-I:4208, sig `property`) + `H4.L.12` (lord_in_12.py:84,
  HTJAH-I:4187). HPA is Raman's own condensation of the same HTJAH-I lines.
- **B6.3** dual-sign 7th & Venus → ≥2 marriages (HTJAH-II:484; HTJAH-I:8138) — **PARTIALLY
  COVERED**: `H7.C.38` (combinations.py:392) already scores the **7th-SIGN**-dual + Venus-dual
  signature from the SAME source (HTJAH-II:484). The reviewer FLAGGED the **7th-LORD**-in-dual-
  sign as a *genuinely distinct* but deliberately deferred refinement — encoding it now would
  inflate the over-harsh H7 marriage tail (the very thing B2/B3/B4 relieve) and needs the
  unencoded Jupiter↔Venus holding-factor exception first. Kept text-only, as the code already
  does. (HTJAH-I:8138 could not be verified on disk — confirm against a primary source before
  treating it as an independent testimony.)
- Planet results vary by avastha/disposition, not mere occupancy (HPA-19:47; HPA-7 the 10
  avasthas) — a longer-horizon `shadbala`/metadata item, **still deferred**.

### B6-adjacent observation — `H4.C.3` / `H4.L.12` same-placement double-fire  ✅ RESOLVED 2026-06-25
Surfaced during the B6.2 audit: the H4 `property` verdict (which aggregates the `property` and
`mother_home` rule_tags, significations.py:251) has TWO evaluable rules firing on the single
`LordIn(4,12)` placement — `H4.C.3` (sig `property`, HTJAH-I:4208) and `H4.L.12` (sig
`mother_home`, HTJAH-I:4187). They are two distinct corpus lines that happen to overlap on one
placement; the codebase elsewhere prevents this by making the overlapping rule `descriptive`
(cf. H4.C.30, H7.C.67's note). Whether this is a true double-count to collapse, or an acceptable
two-testimony overlap, is a verdict-affecting judgment for the user — deferred (it can move H4
`property` goldens; needs its own regression analysis + sign-off).
**Measured 2026-06-25:** making `H4.C.3` descriptive is **zero golden regression** — the
double-count is currently *inert* (no golden verdict depends on it), confirmed by running the
full harness with H4.C.3 disabled (only the B6.2 coverage assertion changed; all goldens held,
TrackB=131). So there is no ratchet cost or benefit today; the decision is purely the design call
above (combos-stack-on-bridge vs the H7 "no re-score" policy). Recommendation: align with the H7
policy (make `H4.C.3` descriptive, citation preserved) *before* Phase-3 adds H4-property goldens,
so the inflation can't bake a wrong verdict into a new golden.
**Applied 2026-06-25 (user-delegated):** `H4.C.3` is now `kind="descriptive"` (citation preserved,
ownership note added) — EVERY arm of its Or is already scored into `property` by the mother_home
bridge (H4.L.6/8/12, H4.P.Mars/Saturn), so the property-loss testimony survives via the bridge while
the double-count is removed. Zero golden regression (ratchet held 99/139, no snapshot drift — the
double-count was inert at the evidence level too). The B6.2 coverage test was updated to assert the
property loss flows through H4.L.12 and that H4.C.3 no longer fires.

## B7 — Reconcile the Venus/Saturn combustion doctrine  `threshold`  ✅ RESOLVED 2026-06-15
**Settled:** removed the non-Raman 0.85 Venus/Saturn exemption; `_combust_graded` now uses one
0.5 half-combust bar for all planets, matching H3.C.39. Zero golden regression (the exemption
only affected the karaka-intact triple-veto, and no golden sits in the 0.5–0.85 band with the
combined debil+maraka condition). Chart 59's powerless 0.79 Venus (HTJAH-I:3788) is the warrant.
Below is the original analysis, kept for provenance.

### (original)
**Origin.** bphs-doctrine-reviewer flag on H3.C.39 (Phase-2a). The engine carries TWO
Venus-combustion thresholds: `_combust_graded` uses 0.85 for Venus/Saturn (a NOVEL heuristic
explicitly "NOT cited to Raman", wired only into the `_karaka_intact` triple-veto), while
H3.C.39's `_ThirdLordSubstantiallyCombust` uses a flat 0.5. Chart_59's Venus is 0.79 — Raman
calls it "powerless" (HTJAH-I:3788), so the 0.5 bar is the more faithful one.
**Status.** No runtime collision (separate paths). But the project should pick ONE
Venus-combustion doctrine. Decision is the user's (it touches the karaka-intact veto, which
has its own blast radius): keep both (documented), lower the `_combust_graded` Venus/Saturn
exemption toward Raman's reading, or unify on a single combustion model. Deferred pending
user sign-off; H3.C.39 ships as-is (faithful, zero-regression).

## Golden expansion  `golden`  (Phase 3)
**Assessed 2026-06-25 (Item 3).** The fixture already holds **131 CONFIRMED** verdicts (the
ratchet) **+ 34 DRAFT verdicts awaiting user validation** — so the nearest Phase-3 lever is
VALIDATING the existing DRAFTs, not mining new charts. Worksheet:
`docs/raman_saab/worksheets/PHASE3_draft_validation.md`. Breakdown:
- **Ready to confirm (10)** — the engine already matches the recorded DRAFT verdict, so
  confirming the ones the user validates moves the ratchet 90/130 → up to 100/140:
  h7_01, h7_06, h7_12, h7_13, h7_14, h9_01, h12_14, h6_02, h6_05 (+ h12_13, currently HELD).
- **H8 death/longevity** — **DEATH MANNER OPENED 2026-06-25** (user-directed "do H8 like the other
  houses"). The death *manner* is read directly from the 8th-house affliction apparatus, like any
  dusthana house — NOT a Phase-E subsystem. Two-part judge change: narrowed `LONGEVITY_GUARD` to the
  `longevity` SPAN sig only; flagged `death` as an `AFFLICTION_MATTER` (a fired malefic on the 8th
  confirms the affliction; pillar strength can't rescue death — mirrors H6/H12). bphs-doctrine-reviewer
  VALIDATED (HIGH; HTJAH-II combos #1-2, Phaladeepika Ch.14). **5 death goldens confirmed = afflicted**
  (chart_73 Lincoln, chart_74 Gandhi, chart_75 JFK, chart_78 Hitler, chart_35 Poornayu-natural-via-maraka)
  → ratchet +5, H8 now 5/5. **Only the 2 LONGEVITY-SPAN charts remain** (`chart_33` Pindayu 86y,
  `chart_34` Amsayu 70y) — left DRAFT: the numeric span genuinely needs the ayurdaya engine (reviewer
  INSUFFICIENT-EVIDENCE; 8th-strength ≠ span class, proven by in-corpus charts 59/61). That span build
  is the one true Phase-E remnant below.
- **Engine mismatch (17)** — **VALIDATED 2026-06-25** against Raman's text: every recorded DRAFT
  verdict is CORRECT, the engine misses each, so NONE is confirmable (no wrong-DRAFT quick wins).
  Split: **10 over-lenient** (engine favourable/mixed where Raman afflicted/mixed — esp. the
  coverture/vaidhavya spouse-death charts h7_09/10/11 the V2 favour-preponderance over-lifts) +
  **7 over-harsh** (engine afflicted where Raman mixed — "unconventional but not ruined" marriages
  h7_17/18/19 the nodal/decisive affliction over-reads). This is the precise B2/B3/B4 + H5
  calibration spec (per-chart reasoning in `worksheets/PHASE3_draft_validation.md` §C). Each needs
  a faithful, cited, doctrine-reviewed, zero-regression increment — not a bulk pass.
- New-chart mining (HTJAH-I/II early chapters, full birth lines) via the existing
  DRAFT→worksheet→CONFIRMED pipeline remains available once the DRAFT backlog is cleared.
- **Notable Horoscopes** is only 2 of ~50 chapters present — an *acquisition* gap; the full
  edition would add ~48 fully-worked goldens. Flag for the user to source.

## Phase E — longevity SPAN engine  `shadbala`/`new-mechanism`  (narrowed 2026-06-25)
**Update:** the H8 death *manner* is now judged like any house (5/5 confirmed) — Phase E is no longer
needed for the death house in general, **only for the numeric life-SPAN** (`chart_33` Pindayu 86y,
`chart_34` Amsayu 70y, still DRAFT). The `longevity` sig keeps deferring. Remaining scope for the span: 
- **Already present** (partial infra to build on): `app/raman_saab/primitives/balarishta.py`
  (infant-mortality / early-death yogas), the `house_08_ayur/` rule sets (combinations, lord_in_12,
  planets_in_8th), and the maraka flags in the judge (`maraka_active`, `LONGEVITY_GUARD`).
- **Missing** (the build): (1) the classical **ayurdaya span computation** — Pindayu / Amsayu /
  Nisargayu year-counts with the haranas (Chakrapatha, Krurodaya, etc.) → the alpa/madhya/purna
  span class; (2) **maraka-dasha death-timing** — selecting the killing Dasa/Bhukti from the 2nd/7th
  lords + Saturn + the assembled marakas; (3) a verdict path that, once the span class is fixed,
  releases the `LONGEVITY_GUARD` to emit a real death/longevity verdict.
- **Death-timing branch relationship:** `feat/death-timing-predictor` / `data/vedastro-corpus` built
  an **empirical** longevity model (MortalityModel ECDF, alpa/madhya/purna *brackets* by age,
  composite×bracket risk) — it shares the bracket taxonomy and the maraka/significator concepts but
  is **statistical, not classical ayurdaya**. So it is a strong *reference* (bracket boundaries, the
  maraka head-to-head results, the Saturn-transit trigger) and a candidate to wrap as a secondary
  empirical lever, but the classical span computation must be built natively. **Major effort** — its
  own phase, not a single increment.

## Documented limits register  (confirmed misses the engine cannot faithfully reach today)
These are CONFIRMED goldens the engine misses; each is a deliberate limit, not a bug to hack:
- **chart_60** — H3 siblings *afflicted*, engine *favourable*. The lord (Jupiter) is well-disposed but
  the house + karaka are afflicted (HTJAH-I:3815, "no brothers"); the preponderance favours the good
  lord. The B1 three-factor comparative-weighing case — a faithful fix needs the general B1 mechanism
  and risks regressing chart_54 (also malefic-aspected 3rd that KEEPS brothers on a strong lord).
- **chart_52** — H3 siblings *mixed*, engine *favourable*. House good but lord Moon weak (6 born, 3
  died); contestable "favourable/mixed" golden (confidence 0.45). Same B1 comparative-weighing family.
- **chart_08** — H7 marital_happiness *favourable*, engine *afflicted*. Over-harsh: a separation/besiege
  rule fires, but Raman reads it favourable; the blemishless-Venus floor correctly does NOT rescue it
  (its Venus has Mars on it → not blemishless). Softening the decisive rule risks regression.
- **h12_13 / h5_14** — HELD DRAFTs (engine matches but deliberately not confirmed pending a fresh call).
- **chart_17** — H1 self *favourable*, engine *afflicted* (dist 2). ADDED 2026-08-22; this and
  chart_31 were the only two current dist-2 misses with NO prior register entry. Diagnosed, not
  guessed: the deciding frame is the **MOON** frame (lagna is the alternate), and in it all three
  pillars are strong (lord Jupiter strong, karaka Sun strong, bhava-bala strong, lord NOT
  hard-afflicted) with fired evidence **benefic-dominant 5:2**. No decisive-affliction rule fires;
  the arishta yoga drop correctly does NOT apply (its `not (fired_benefic and fired_malefic)`
  guard blocks it — both polarities fired). The verdict is `borderline_shifted=True` with
  **`navamsa_status='weakens'` and no yoga metadata**, so a borderline mixed was dropped to
  afflicted by the **D9 navamsa modulation** — against benefic-dominant rasi evidence and three
  strong pillars. Raman's prose is favourable-with-worry ("self-reliant, endurance and energy;
  high distinction in the legal line" — the negatives he names, "not happy regarding children",
  are H5 matters, not H1). Whether a navamsa drop should be able to outvote a benefic-dominant,
  all-pillars-strong rasi ledger is a real doctrinal question and NOT attempted here.
- **chart_31** — H1 self *afflicted*, engine *favourable* (dist 2). ADDED 2026-08-22. The mirror
  of chart_17 and why no single directional fix serves both: lagna frame, all three pillars
  strong, evidence an even 2:2, `navamsa_status='neutral'`, `borderline_shifted=False` — the
  engine reaches favourable by ordinary preponderance with nothing anomalous in the machinery.
  Raman reads afflicted on "lack of happiness" (stated twice) despite granting good build, honesty
  and a "clear quick mind". This is the `self`-as-wellbeing vs `self`-as-body/character boundary;
  the engine reads the latter. Likely not mechanically separable without an outcome layer.
The B1 comparative-weighing mechanism (backlog B1) is the single lever that would address chart_52 +
chart_60; it is high-risk (med) and was deliberately narrowed into the H3.C.39 combust-lord rule rather
than attempted wholesale. Deferred pending a careful, chart_54-guarded design.

---

## Layer-C cited-fix sweep (2026-06-25) — shipped + documented limits

The faithfulness program (graded `degree` + within-1 ordinal metric + cited fixes) reached its clean
ceiling. **Shipped (+4, all on GENERAL dicta, user-validated, doctrine-reviewed, over-fire-scanned):**

| Rule | Fixes | Cited dictum | Pattern |
|---|---|---|---|
| H9.A.20a | h9_13 | HTJAH-II:7916 "afflictions to the Sun → early death of father" | Sun-Pitrukaraka dusthana + papakartari (decisive) |
| H5.C.38 | h5_01, h5_07 | HTJAH-I:5619 "Jupiter… Papakarthari + malefic Rashi → blemished" | PutraKaraka papakartari + malefic-rashi (decisive) |
| H4.C.18a | h4_01 | HTJAH-I:4224 "Moon in 4th joined by evil planets → kills mother early" | Moon-Matrukaraka in 4th conjunct-malefic (decisive) |

Ratchet: **106/146 → 110/146 exact (0.753); 126/146 → 130/146 within-1 ordinal (0.890).**

**Documented limits — the irreducible real-error tail (do NOT force; each would overfit).**
The shipped fixes all rested on a GENERAL Raman dictum. The remainder do not — they are n=1
chart-conclusion-only readings or comparative-weighing/over-harsh cases where the favourable twin carries
MORE surface affliction. Forcing them violates the main goal (faithful, not golden-tuned):

- **chart_60 (H3 siblings), chart_52** — comparative-weighing limit. The favourable twin `chart_54` has 5
  malefics on/aspecting the 3rd (vs chart_60's 2); any "3rd/karaka afflicted" signature over-fires on
  chart_54. Only a chart_54-guarded narrow aspect-rule could help; deferred (backlog B1).
- **h12_05 (H12 expenditure)** — n=1, cite HTJAH-II:17170 is Chart-243's HEADER (no general dictum). The
  only discriminator vs the favourable twin `h12_03` (also 12th-lord-conjunct-node, Venus+Ketu) is the
  lord's nature (malefic Saturn vs benefic Venus) — an empirically-found twin-sparing gate = overfit risk.
- **h6_04 (H6 disease_chronic / eye)** — n=1, cite HTJAH-I:6664 is Chart-130's myopia CONCLUSION (6th lord
  in 2nd + 2nd-lord Moon in 12th with Saturn). Encoding this multi-factor configuration memorises one chart.
- **h11_01 (H11 elder_siblings)** — n=1, cite HTJAH-II:14804 is the Chart-210 CONCLUSION; a debilitated
  11th lord + aspect-affliction with no general dictum.
- **h11_09 (H11 gains, over-harsh fav→afflicted)** — the engine over-weights an afflicted karaka (Jupiter in
  dusthana + conj Ketu) and under-weights a strong 2nd/7th/9th/11th-lords-in-kendra dhana-yoga. Fixing needs
  a yoga-relief that risks regressing genuinely-afflicted gains; deferred.
- **h5_05 / h5_12 (H5 children)** — FIXED 2026-06-25 (Phase-2). The `_fertility_gate` one-weak-sphuta
  refinement denies on a corroborating affliction: Arm A (>=2 malefic 5th-rules = "5th house spoilt",
  h5_12) or Arm B (weak karaka pillar + Jupiter malefic-afflicted = "baneful PutraKaraka", h5_05). +2,
  zero over-fire; spares h5_16 via the `karaka_strong is False` AND. bphs-doctrine-reviewer SOUND.
- **h5_10 (H5 children)** — STILL a limit. Raman: "the lord is weak and the Karaka powerless"
  (HTJAH-I:5804), but the engine reads ALL pillars strong + 0 malefic rules — a pillar-layer strength
  DISAGREEMENT, not a gate gap. The gate must not invent an affliction the engine cannot see. Revisit only
  if the Shadbala/dignity strength reads are reconciled.
- **h5_16 / chart_08 (over-harsh fav→engine-afflicted)** — softening these un-afflicts genuine cases or
  needs the forbidden navamsa/CONTRA_PILLAR retune. Documented limits. (The Phase-2 gate explicitly SPARES
  h5_16 — does not make it worse.)
- **chart_09/17/20/31 (H1 self)** — holistic whole-chart prose with no single cited combination.
- **h9_02 (H9 father)** — INVESTIGATED + confirmed limit 2026-06-26. The clean candidate "Sun-in-9th +
  9th-house papakartari (malefics in 8th & 10th)" does NOT fire (9th-house is not hemmed that way); the
  affliction is Raman's COMPOUND "papakartari to 9th house/lord/karaka PLUS karaka-in-house" reading
  (HTJAH-II:7929) that no single predicate reproduces. 3 malefic father-rules already fire but strong
  pillars (exalted Sun, vargottama Jupiter, Mars in own kendra) override — a confluence case, not a
  missed cited rule.
- **chart_44 (H2 wealth)** — INVESTIGATED + confirmed limit 2026-06-26. The 2nd lord IS papakartari'd,
  but the over-fire scan shows "2nd-lord-papakartari" fires on chart_40/41/46 — all FAVOURABLE wealth
  twins. chart_44's poverty is the compound confluence (Dwirdwadasa from the Moon + Sun aspected by
  Saturn + 2nd-lord-with-malefic-turned-Venus + papakartari TOGETHER, HTJAH-I:2827-2848); the single
  papakartari signature over-fires on 3 favourable charts.

**Honest ceiling: ~77% exact / ~90% within-1 (114/148, 134/148 at 2026-06-26; the AYURDAYA longevity engine resolved the chart_33/34 span goldens); the within-1 figure is the
fairer headline and is at the projected ordinal ceiling.** The 20 distance-1 boundary near-hits are
subjective favourable-vs-mixed calls (handled by the graded `degree`), not errors. The two most-promising
remaining over-lenient cases (h9_02, chart_44) were empirically re-tested and both confirm as limits —
every faithful general-dictum / 2+-chart mechanism has been mined. Further rule-grinding overfits.

---

## H7-marriage (+H5) DRAFT backlog — validated 2026-06-26, awaiting engine work

bphs-doctrine-reviewer adjudicated all 16 remaining non-empty DRAFT goldens against Raman's
TEXT. **All 16 DRAFT labels are correct per Raman.** Progress: h12_13 (engine-match) CONFIRMED;
**h7_02 / h7_05 / h7_15 FIXED + CONFIRMED 2026-06-26** via the decisive **H7.C.86** (afflicted
7th lord -> vitiated spouse) — the 3 HIGH-confidence mode-B reversals. **12 validated DRAFTs
remain** (the mode-A benefic-relief lift + the residual mode-B 8th-marital-bond rule), kept DRAFT
per the project pattern (confirm engine-matches; DRAFT-until-fixed for mismatches). Confirming the
remaining 12 now would re-base the ratchet DOWN for zero engine benefit; BUILD the mechanisms,
then confirm.

**Two engine failure modes (the agent's diagnosis):**

**(A) Over-weights affliction, ignores Raman's stated benefic RELIEF -> engine wrongly `afflicted`
(correct = `mixed`):**
| golden | sig | Raman (correct) | engine | the relief the engine drops | conf |
|---|---|---|---|---|---|
| h5_13 | children | mixed | afflicted | "birth of children is not denied" (Jupiter unafflicted) HTJAH-I:5876 | HIGH |
| h5_14 | children | mixed | afflicted | "5th house is fairly well disposed" HTJAH-I:5889 | HIGH |
| h7_03 | marital_happiness | mixed | afflicted | "rule out... separation or divorce" (Venus+Jupiter) HTJAH-II:1818 | HIGH |
| h7_07 | coverture | mixed | afflicted | remarriage after the first husband's death HTJAH-II:1996 | MED |
| h7_17 | spouse | mixed | afflicted | realized (inter-faith) marriage, not destroyed HTJAH-II:2726 | MED |
| h7_18 | spouse | mixed | afflicted | "Jupiter... on karaka and 7th lord Venus" HTJAH-II:2768 | MED |

**(B) Over-weights a clean 7th-lord, misses the heavily-afflicted 8th / marital-bond / Navamsa ->
engine wrongly `favourable` (correct = `mixed`/`afflicted`):**
| golden | sig | Raman (correct) | engine | what the engine misses | conf |
|---|---|---|---|---|---|
| h7_02 | spouse | afflicted | favourable | both 7th-lords afflicted by Rahu; immoral spouse HTJAH-II:1773 | HIGH |
| h7_05 | spouse | afflicted | favourable | two wives; clandestine marriage; wife left HTJAH-II:1906 | HIGH |
| h7_15 | spouse | afflicted | favourable | 7th-lord+Venus much afflicted; profligate, VD HTJAH-II:2528 | HIGH |
| h7_04 | marital_happiness | mixed | favourable | "domestic bickerings" (Rahu-7th, Mars-Venus) HTJAH-II:1864 | MED |
| ~~h7_16~~ | spouse | mixed | ~~favourable~~ **FIXED** | 8th-from-Moon afflicted -- _marital_bond_gate 2026-06-26 | MED |
| ~~h7_19~~ | spouse | mixed | ~~favourable~~ **FIXED** | 8th-from-Moon afflicted -- _marital_bond_gate | MED |

**Also:** h5_15 (children, favourable — engine `mixed`, the single child-death over-weighted) and
h5_18 (children, mixed — engine `favourable`, "spoiling of the 5th house" missed).

**Status (2026-06-26): 5 of 15 fixed** (h7_02/05/15 via H7.C.86; h7_16/19 via the marital-bond gate).
**10 remain** — all MODE-A `afflicted`-should-be-`mixed` benefic-relief misses (h5_13/14, h7_03/07/17/18),
plus h7_04 (the lone weak mode-B, 1 malefic in 8th-from-Moon), h5_15/h5_18, and h7_11 (coverture).

### Mode-A path (diagnosed 2026-06-26) — a benefic-RELIEF LIFT (afflicted -> mixed), regression-aware
The mode-A reliefs are heterogeneous and the fix touches rules already shipped, so it needs careful,
dedicated work (NOT a tail-of-session rush). Per-target why-afflicted:
- **h5_13** (children): reads afflicted via the **fertility-gate Arm A (>=2 malefics)** I shipped — but
  Raman = mixed ("birth not denied", Jupiter unafflicted). **Arm A over-fires here** (the H5 over-fire
  scan only checked CONFIRMED goldens; h5_13 was DRAFT). FIX: gate Arm A with "karaka Jupiter NOT clean"
  (a clean/unafflicted karaka -> the affliction is tempered to mixed, not denied). Must NOT regress h5_12
  (Jupiter afflicted there -> stays afflicted). Verify h5_12/06/07 unchanged.
- **h5_14** (children): fertility-gate (nben=3, nmal=1) -> afflicted; Raman mixed ("5th house fairly well
  disposed"). Same karaka/bhava-relief family as h5_13.
- **h7_03** (marital_happiness): 1 malefic, 0 benefic-RULE -> afflicted; Raman = mixed ("Venus+Jupiter
  rule out separation"). The relief is a benefic INFLUENCE not captured as a rule -> needs a marital
  benefic-relief detector (unafflicted Jupiter/Venus on the 7th house/lord/karaka -> lift afflicted->mixed).
- **h7_07** (coverture): 4 malefics -> afflicted; Raman mixed (remarriage after the spouse's death) -- a
  recovery signature, harder; possibly leave as a documented near-hit.
- **h7_17 / h7_18** (spouse): the "unconventional-but-realized inter-faith marriage" pair -- afflicted
  configuration but a realized marriage; the inverse of the marital-bond demote (lift afflicted->mixed
  when the 7th LORD is clean and the marriage is realized). h7_18 reads afflicted with nmal=0/nben=0
  (investigate the source -- navamsa/maraka).
All are dist-1 near-hits (already within-1).

### Mode-A is a DOCUMENTED LIMIT — empirically proven not mechanically separable (2026-06-26)
A benefic-relief lift was BUILT AND TESTED (a blemishless Jupiter/Venus on the 5th/7th house, lord, or
karaka -> lift afflicted->mixed). It does NOT discriminate, in BOTH families:
- **Children:** h5_13 (mixed) has NO detectable benefic-on-5th relief, while h5_04/h5_08/h5_09 (all
  AFFLICTED) DO. The real mixed-vs-afflicted axis is child SURVIVAL ("born and lived" h5_13 vs "born and
  died" h5_04/08/09) -- an outcome the natal config cannot express.
- **Marriage:** h7_17/h7_18 (mixed) have a Jupiter relief, but so do chart_09, h7_02, h7_05 (all
  AFFLICTED -- and h7_02/h7_05 were JUST confirmed afflicted via H7.C.86). A relief lift would REGRESS
  those shipped fixes. h7_03 (mixed) has no detectable relief at all. The axis is marriage REALIZED-but-
  flawed (mixed) vs DESTROYED/immoral (afflicted) -- again an outcome, not a separable natal predicate.
CONCLUSION: the 10 mode-A items are the subjective afflicted-vs-mixed boundary the within-1 ordinal
metric was built to honor (all dist-1 near-hits). Forcing a relief mechanism over-fires on genuinely-
afflicted charts and regresses the H5/H7 afflicted fixes. LEFT as within-1 limits; do NOT pursue a
relief lift. (If ever fixed, it would need a Dasa/outcome layer the rule-engine deliberately excludes.)

**Engine work implied (future):** (1) a marital benefic-RELIEF mechanism that lifts an afflicted
spouse/marital verdict to `mixed` when Raman's named reliefs are present (no separation/divorce,
remarriage, benefic on the karaka) — complements the existing blemishless-Venus floor; (2) an
8th-house / Navamsa MARITAL-BOND affliction rule so a clean 7th-lord with a heavily-afflicted 8th
reads `mixed`/`afflicted`, not `favourable` (the h7_02/05/15 hard reversals are the priority — a
profligate-with-VD spouse must not read favourable). The three HIGH-confidence reversals
(h7_02/05/15) are the cleanest fix targets. The four "Unconventional Marriages" charts
(h7_16/17/18/19) are MEDIUM (afflicted-but-realized marriage = mixed) — tighten the spouse rubric
first.

---

## Dasha / outcome-timing layer (2026-06-26) — built + documented limits

The Vimshottari timing layer (vimshottari.py: maraka_set, death_window, significator_dasha_windows;
wired metadata-only via house_template._event_timing; rendered via the re-routed proforma) is ADDITIVE
and validated (death-Mahadasha matches Raman on all 5 dated deaths; the death falls in a maraka period
all 5). Honest limits, NOT to be force-fixed:

- **Strongest-maraka / single-date prediction** — the death's Mahadasha is reliably a maraka, but WHICH
  of the (broad) maraka set actually strikes — and the to-the-day date — is the chart-specific
  "strongest-maraka + Saturn-transit final-signal" judgement Raman makes by hand (chart_35 invokes a
  Saturn transit). The engine returns a RANKED WINDOW SET, never a date. `death_window` predicts the
  natural-death (alloted-span) region; premature/violent deaths (Lincoln 56, JFK 46) strike a strong
  EARLIER maraka well below the ayurdaya span and are not isolated.
- **General event-timing — RESOLVED 2026-06-26** (was: partial). A critical audit found the layer was
  death-biased (death 12/12; non-death ~10-29%). FIXED by `vimshottari.timer_set(chart, house)` — Raman's
  universal "Time of Fructification" significator set (H-lord + H-karaka + occupants + aspecters +
  H-lord-aspecters/conjuncts + H-lord-from-Moon + node-via-dispositor), wired into `_event_timing` for
  EVERY matter. Non-death event-MD recognition: **12/13 (92%)** across gains/career/acquisition/travel.
  Remaining edge: **h10_05 Napoleon (Rahu)** — needs the deeper Kujavad-Ketu *constellation-chaining*
  (Rahu in Ketu's star -> Ketu gives Mars' results -> Mars+Sun = empire); the engine adds a node by its
  sign-DISPOSITOR but not yet by its CONSTELLATION-lord chain. Future lift, low priority.
- **Birth-time sensitivity** — a Bhukti boundary shifts months per few minutes of birth error: the
  Mahadasha claim is robust (all 5 deaths), the Bhukti only for precisely-timed births (Lincoln/Hitler
  exact). Hence the layer reports a window, not a date.
- **Timing ANNOTATES, never resolves** the mode-A outcome ambiguity (born-and-lived vs born-and-died):
  the natal verdict is unchanged; timing only adds "when the significators/marakas are active".

## ASP ch.XV + ch.XVI mining record (2026-08-03) — so no future session re-mines blind

**ch.XVI (Illustrated Horoscopes) — CLOSED, whole-pipeline validated on 9 nativities, 63/63
printed Sodya Pindas exact.** The preamble states Illustrated No. 1's Sun Ashtakavarga cell-by-
cell, raw AND reduced (ASP-16:40-51): raw checksums to 48 and ALL SIX printed reduced cells
reproduce under `trikona_shodhana` exactly. Vision-re-extracted (PDF pp.84-87) all 12 remaining
nativities' printed longitudes + Sodya Pindas; ran the full pipeline (BAV -> Trikona ->
Ekadhipatya -> Rasi+Graha Gunakara -> Sodya Pinda) against each. Result (`test_asp_illustrated.py`):
- **9 nativities, 63 pindas, EXACT**: "An Eminent Indian", Roosevelt, Marx, Havelock Ellis,
  Sankaracharya of Govardhan Mutt, Wodiyar, Nehru, Mussolini, Narasimha Bharathi. This
  definitively settles the earlier ASP-14 Standard-Horoscope delta (Sun 182 printed vs 191
  computed): the rules are right, that one printed table was a hand-computation slip.
- **Windsor and Golwalkar, 6/7 exact, Venus off by +3 and +10 respectively** — re-verified
  2026-08-03 against a clean, fully-legible re-scan (positions cross-checked self-consistent via
  the printed table's own Rasi+Graha=Sodya arithmetic). Same deltas both times the chart was
  read independently -> CONFIRMED as isolated Venus-cell slips in Raman's own printed tables,
  the same error class as ASP-14, not a transcription or engine defect. Not encoded as exact
  fixtures (only 7/7 matches are); recorded here as closed with a known, bounded, reproducible
  delta.
- **Ford, 0/7 total mismatch — genuinely OPEN, re-classified.** Originally suspected as an OCR/
  vision transcription failure. Re-read on a clean scan (Sun 106°34', Moon 209°12', Mars
  127°35', Mercury 102°32', Jupiter 179°56', Venus 151°44', Saturn 160°32', Rahu 223°5', Asc
  211°52', ayanamsa 20°30' — ASP-16, book p.163) gave IDENTICAL positions to the first read, and
  the resulting raw Bhinnashtakavarga totals check out EXACTLY against the canonical checksums
  (Sun 48, Moon 49, Mars 39, Mercury 54, Jupiter 56, Venus 52, Saturn 39) — so the positions and
  the engine's raw-BAV stage are provably correct for this chart. The divergence therefore
  enters somewhere in Raman's own reduction (Trikona/Ekadhipatya) or Gunakara arithmetic for
  this one nativity, compounding across all 7 planets rather than one isolated cell — unlike
  every other slip found in this book, which was always a single planet. Not pursued further
  (no clean cited-fix pattern, per B1's precedent for not reverse-engineering a book's own
  errors); flagged for the golden track separately, since Ford may overlap an existing NH
  golden and any cross-check there should go through that discipline, not this one.

**ch.XV (Miscellaneous), classified per the content-scope rule (a live tag does not admit
out-of-scope content — the AFB-horary precedent):**
- Rules 1-22 (ASP-15:21-183): ELECTIONAL — choosing times/directions for journeys, marriage,
  studies, factories, conception via Sun/Moon/Mercury/Venus bindu-transits. (Corrected
  2026-08-03 from "1-19 / :21-168": rules 20-22 — Saturn-direction siting, least-SAV-rising
  treatment timing, >30-bindu-SAV-rising elections — are electional too.) Category (b),
  MUHURTHA firewall — deliberately NOT encoded at mining time; RELEASED to the electional
  subsystem by the same-day firewall lift (next record).
- Rahu Ashtakavarga (ASP-15:~240-260): Raman presents a variant Rahu AV with bindus, while
  noting "no Kakshya has been assigned to him". The first-edition preface says such
  controversial matters (Rahu/Lagna AVs) were deliberately avoided in the main exposition;
  the repo's 7-graha chayagraha lock stands. NOT encoded — recorded as a Raman-presented
  variant, not Raman doctrine.
- Rahu's 12-places-from-Moon transit results (ASP-15:263-271): benefic at (3), (6), (11) —
  CORROBORATES transits.py's existing Rahu Gochara set {3,6,11} exactly. No change needed;
  noted as an ASP confirmation of the encoded table.

## PRASNA + MUHURTHA firewall LIFT (2026-08-03) — user decision, binding scope rules

**Decision.** The user (via AskUserQuestion, 2026-08-03) explicitly chose to lift the horary
(PRASNA) and electional (MUHURTHA) divergence firewalls, alongside approving a report-only
medical read-out section. JAIMINI and VARSHA remain firewalled; Prasna Marga vols remain
unregistered. This overturns the "strictly Parashari-natal" project scope deliberately and
on the record — do not silently revert, and do not silently widen further.

**Standing scope rules (binding on all future sessions):**
1. Horary and electional are SEPARATE SUBSYSTEMS — `app/raman_saab/horary/` and
   `app/raman_saab/electional/`. They may import natal primitives; natal verdict code
   (judges, proforma, house_template, synthesis feeding verdicts) must NEVER import them.
   This extends the VERDICT-AUTHORITY invariant: the natal ratchet is untouchable by
   anything these subsystems compute.
2. The lift releases the content-scope quarantine on horary/electional chapters inside
   LIVE books — HPA-27 (Prasna Sastra), AFB-11 (horary), ASP-15 rules 1-22 — FOR THOSE
   SUBSYSTEMS ONLY. Natal rules still never cite them (the AFB-horary precedent stands
   for natal scope).
3. Subsystem outputs carry the Measured-Truth framing: "what Raman's method says", never a
   validated prediction. The horary judge excludes death/lifespan/serious-illness/self-harm
   queries IN CODE (the /ai-interpret precedent).
4. Doctrine-first still governs: every rule cites `PRASNA-<ch>:<line>` / `MUHURTHA-<ch>:<line>`
   verbatim; where Raman's text omits a technique the pasted plan wished for, the technique
   is NOT encoded (measured example: "Tyajyam" does not appear in the ingested Muhurtha text).

**Corpus actions taken (same day).** `muhurtha_raman` ingested for the FIRST time (its dir
had been empty since registration — the registered archive item `bwb_P9-EAH-659` is
access-restricted/401; the ETL entry was repointed to the open DLI scan
`in.ernet.dli.2015.128092`; 16 chapters, gaps in chapter numbering are OCR heading artifacts).
`prasna_tantra_raman` re-ingested COMPLETE from its existing identifier (the old ETL filename
had a spacing mismatch — "B. V. Raman" vs the served "B.V.Raman" — which is why only 5
partial chapters ever landed; the same 5 chapter files now carry the full text; the odd
`chapter_049` label is an OCR-artifact heading for the main Bhava-Prasna body and is
cosmetically wrong but citation-stable). Zero pre-existing citations targeted either tag
(grep-verified), so no line numbers shifted under anyone. Both registry entries flipped to
`live` with provenance comments.

**Citable anchors located (for the build phases):** Tajika yoga definitions
PRASNA-4:1068-1330 (Ithasala incl. Muthaseela + Vartamana/complete grades, Easarapha,
Naktha, Yamaya, Kamboola incl. quality grades); Deeptamsa orb table PRASNA-2:258-270
(Sun 15, Moon 12, Mars 7(8?—verify at encode time vs print), Mercury 7, Jupiter 9, Venus 7,
Saturn 9; aspects themselves have no orb); significator scheme (lagna lord = querent,
karyesa = house lord) PRASNA-2/49. Muhurtha: Tarabala/Chandrabala ~MUHURTHA-2 (raw ~881-1063),
Raja/Agni/Chora Panchaka (raw ~944-1037), Rahu Kalam weekday table (raw ~7318 — locate
post-split chapter at encode time), Durmuhurtha (index -> pp.31-32).

**Known dependency, decision PARKED for Phase 3:** Saham FORMULAS are not in Prasna Tantra —
Raman himself defers Tajika machinery to his Varshaphal (PRASNA-2:288-291), and the formula
table (Punya/Guru/Kirti/Mitra/Raja... with day/night variants and the +30° no-lagna-between
rule) sits in `varshaphal_raman` ch.7 — still firewalled. Encoding sahams therefore requires
EITHER a separate user decision to lift VARSHA (scoped to the saham/yoga-definition
chapters) OR leaving sahams out of the horary package. Punyasaham APPLICATION rules
(PRASNA-3, PRASNA-49) are citable either way. ASK THE USER AT PHASE 3, not before.

**RESOLVED same day — VARSHA LIFTED (user decision via AskUserQuestion, 2026-08-03,
Phase 3).** `varshaphal_raman` flipped to `live` with the same walled-subsystem scope.
JAIMINI is now the ONLY firewalled book. Phase 3 built `app/raman_saab/horary/`:
- `tajika_aspects.py` — the printed Deeptamsa table (PRASNA-2:262-264), the speed order
  (PRASNA-4:1085-1088), Ithasala/Poorna (stanzas 54-55), Easarapha (56), Naktha (57),
  Yamaya (60), Kamboola (61). **Orb rule = the SMALLER of the two deeptamsas** — fixed by
  VARSHA-7:43-47's own micro-example ("Guru's 9 and Sukra's 7 -> within 7 degrees"), since
  PRASNA-4's worked figure is OCR-damaged at the digit. Applying/separating resolved in the
  directed separation space (sep = slower−faster mod 360, strictly decreasing).
- `sahams.py` — the TEN sahams Raman prints (VARSHA-7:84-171) with day/night swaps, the
  +30 no-lagna-between rule, saham lords (VARSHA-7:190-192), and the worked Punya
  arithmetic (105°21'+285°9'=30°30') pinned. "Vidya"/"Karya" sahams (the pasted plan's
  wish-list) are NOT in Raman's table -> NOT encoded. Mitra's printed formula adds VENUS in
  place of the lagna term (encoded exactly); its Night line is OCR-mangled and the
  every-other-saham day/night-swap pattern is applied — recorded, not silently corrected.
- `prasna_judge.py` — Karyasiddhi: the four full-success configurations (PRASNA-49:107-116),
  Karyesa = query-house lord (:119-126), the 25/50/75/100% ladder (:137-190). Planet-planet
  checks use tajika orbs; planet-HOUSE checks are sign-granular (the book's charts are rasi
  diagrams). Death/lifespan/serious-illness/self-harm topics REFUSED IN CODE. Every verdict
  carries the Measured-Truth disclaimer.
Source-lock re-locked add-only (3 PRASNA chapters + VARSHA-7). Walled both directions by
test. HPA-27/AFB-11 remain citable-but-uncited (no rule needs them yet).

## JAIMINI lift (2026-08-04) — the last firewall falls

User decision (AskUserQuestion, the karmic-evolution chapter, items 6-16 arc):
`studies_jaimini_raman` flips live for a WALLED karmic-evolution layer — the same pattern
as PRASNA/MUHURTHA/VARSHA. **No book remains firewalled.** What the firewall used to
enforce is now carried entirely by the content-scope rule + the walled-subsystem import
tests: natal verdict code imports none of the lifted layers; the 2026-07-24 merge
re-lock's concern (Jaimini doctrine leaking into natal verdicts) remains enforced — the
soul layer's free-text Jaimini references may now also resolve as real citations, but
NOTHING in the verdict path may cite JAIMINI. Corpus re-ingested complete (the ETL
filename mismatch fixed — the prasna precedent); karakamsa combinations live in JAIMINI-9.

## Coherence audit + interpretation guide (2026-08-03) — report v18/v19

User concern: "many sections saying the same things — how to interpret when taking features
or output of the engine." A full coherence audit (agent-run, results verified) mapped the
38 contract sections into 8 clusters and found the report already states precedence in
ELEVEN places — but only locally, inside the section that yields; nothing collected them.
Exactly ONE overlapping pair had no shipped statement: dashboard vs house-by-house (the
former grades ONE named signification via its dedicated reader; the latter grades the whole
bhava by its WEAKEST decided signification — different grain, not disagreement). That
derived rule (PREC-1) was doctrine-reviewed before shipping and is tagged project
governance, not Raman doctrine, in its own rule text.

Encoded as `app/raman_saab/interpretation_guide.py` (chart-independent constant): 12
precedence records + 4 parallel-lens records + the 5-axis table + the 5-step reading
order, rendered as report section v18 ("How to read this report", after the honesty
headline) and shipped machine-readable as the JSON `interpretation_guide` key with a
CLOSED relation vocabulary (governs/corroborates/different_grain/re_read_of/parallel) so
the LLM-grounding path branches deterministically. Where no rule exists the guide says
"parallel lenses — side by side, never averaged"; it never invents precedence.

The audit also found the ranked digest (insight_digest.py) was shipped in JSON + the
interactive page but NEVER rendered in markdown/standalone HTML — a REPORT COMPLETENESS
violation, repaired as v19 ("What matters most"). Full amendment notes:
docs/raman_saab/REPORT_TEMPLATE.md v18/v19.

## The deterministic synthesis layer (2026-08-03) — S1-S5, report v20

The user proposed a 10-phase synthesis architecture ("no prose generated directly from
calculations"). Inventory: ~half already existed; the rest was built as five phases, all
report-layer pure re-reads (PREC-10), the verdict-path wall extended by test. Three user
decisions bind the deviations from the proposal as pasted:
1. **Conflicts NARRATED, never hidden** (the proposal's "never expose unresolved
   contradictions" was rejected as conflicting with REPORT COMPLETENESS/Measured-Truth):
   `tension_narrator.py` composes one sentence per already-detected tension naming BOTH
   poles + the governing v18 rule; a test pins both poles' words in every sentence.
2. **Two doctrine tiers**: Raman-citable core + the MODERN_SYNTHESIS-bannered layer
   (NON_RAMAN_GROUPINGS matter edges; NON_RAMAN_THEMES keywords) — bannered on every use,
   never bare (the pitru precedent).
3. **No numeric evidence weights** (the proposal's fixed weight table): numeric weighting
   was already MEASURED NULL (the tuner's holdout-locked convergence at iteration 0) and
   Raman states no numeric rule (HTJAH-I:495) — his comparative weighing (B1) + the v18
   axes ARE the ranking. Do not re-litigate by re-building weights.
Built: `judgment_graph.py` (S1), `planet_biographies.py` + section v20 (S2),
`PlainReading.reconciliations` (S3), bannered groupings (S4), `Nichod.turning_points`
(S5). Known recorded limitation: `FiredYoga` carries no participant field, so yoga graph
edges are citation-only until that field exists (a future append-only lift).

**Graha chapters + Yoga deep-read (same day, user-requested):** the v20 section grew into
full per-graha chapters and v21 added the per-yoga study — see REPORT_TEMPLATE.md's
v20/v21 amendment note for the complete record. Doctrinal decisions binding here:
verbatim-by-frozen-line-range rendering (zero transcription risk; ranges under the source
lock), stated-absences-never-guesses (the 2 OCR-defeated MD-sign cells, the nodes'
HPA-22/vocation rows), NO invented yoga percentage (measured rupas only — the
measured-null lock), and only Raman-stated cancellations. The HPA-24 mining derivation
(anchor walk over 82 sub-period anchors with 9 OCR aliases, zero Vimshottari-order breaks)
is reproducible from the module's docstring.

**Pipeline WIRED end-to-end (same day, follow-up commit):** the graph decoupled from
life_chapters (period nodes/timer edges now from the first-pass timeline, with grades);
the second pass re-ordered to the diagram (objects → graph → conflicts → themes →
narrative); the narrative engine consumes the layers (census-dominant sentence in Your
Reading's opening beside the Shadbala line — two dominance measures, both said;
reconciliations composed in, not attached; the dominant graha's own MD chapter marked);
`raman_style.py` names the writer stage. Order enforced by consumption tests.

**Report punch-list corrections 1-2 (2026-08-04).** (1) Rectification confidence
re-measured as a bidirectional per-pillar minute RANGE (a full ±60-min scan) instead of a
4-fixed-offset flip check, plus the combined "every pillar holds together" window — no
doctrine change, a pure measurement-precision upgrade to an already-honest instrument.
Two implementation bugs fixed in the same pass (an ayanamsa mismatch between the base
chart and the probe casts that could report false sensitivity; an invalid-hour bug in the
old offset arithmetic near midnight, unreachable at ±5 min but live at ±60). (2) The
judgment graph is now a first-class section (v32) beside "Your Reading" on all three
surfaces — it was already used there (the dominant-planet census sentence); this closes
the gap that it was never actually SHOWN on markdown/standalone HTML, and was shown too
late (after Planet biographies) on the interactive page. Pure re-read both ways; no new
astrology, no verdict touched. See `docs/raman_saab/REPORT_TEMPLATE.md`'s v32 note for
the full technical record.

**v33 Aptitude/intelligence/work-style chapter + an interactive-page completeness gap
(2026-08-14).** The three trait axes the report never had as output fields shipped as
one appended chapter (pure re-read; `REPORT_TEMPLATE.md` v33 note carries the record,
including the corpus-machine follow-up: pinning Raman's master Moon-mind instruction
range near HTJAH-I:1231 before its verbatim block can render). While wiring the fourth
surface, a standing REPORT COMPLETENESS violation surfaced: the interactive page
(`app/medini/templates/report.html`) had never rendered `psych` (v27) — repaired in the
same commit — and STILL does not render `profession` (v23), `wealth` (v24), `marriage`
(v25), `children` (v26), `arishta` (v22), `karmic` (v30), `decades` (v28), or
`life_synthesis` (v29), all of which the markdown and standalone-HTML surfaces carry in
full. Rendering them is a mechanical repair, but folio placement on that page is a
product-layout call — per the completeness rule ("surface it and ask"), this is
recorded here for the USER to schedule rather than done unilaterally.

**Interactive-page completeness repair COMPLETED (2026-08-14, user-directed "implement and
do next").** All eight remaining chapters — `arishta` (v22), `profession` (v23), `wealth`
(v24), `marriage` (v25), `children` (v26), `decades` (v28), `life_synthesis` (v29),
`karmic` (v30) — now render on `app/medini/templates/report.html` with every field, via the
page's safe-DOM helpers. Folio placement: arishta/marriage/children/profession/wealth in
folio 7 (matters & longevity, before the v33 aptitude chapter), decades closing folio 8
(life-narrative), karmic in folio 10 (divisional & soul, between Soul and Pitru), full life
synthesis opening the close of folio 11 (insights). Corpus-quote fields render only when
non-empty (honest absence off the corpus machine). With this, every chapter the report
computes appears on all four surfaces; the REPORT COMPLETENESS gap recorded above is closed.

## Prediction unblock (2026-08-17) — user decision, binding guard-policy record

The user directed "unblock prediction part"; two decisions were then taken via explicit
question-and-answer and are binding until a doctrine review WITH user sign-off says otherwise:

1. **Q1 — scope: "Timed indications."** The guard boundary moved from *timing* to *idiom*.
   Classical timed-indication phrasing is now ALLOWED on every surface, including dates,
   ages, and dasha/bhukti attribution: "marriage is indicated during the Venus bhukti,
   2027–2028", "the 10th house is activated at par-excellence grade in this period",
   "at age 30 the Saturn bhukti turns classically sensitive for health." This is Raman's
   own published voice (his worked nativities date their indications throughout HTJAH).
   The DECREE voice stays refused everywhere: "you will marry", third-person
   `he/she/they will|shall <verb>`, `is going to`, `destined/certain/guaranteed/bound
   to/sure to`, `I predict`. Implementation: `_FORBIDDEN_RE` in
   `app/llm/report_explainer.py` — the 2026-07-28 dated-indication arms were removed,
   every decree arm kept, and a decree-dated-death arm retained.
2. **Q2 — the death wall: "Lift fully."** Maraka periods and the longevity span may now be
   STATED as timed indications on the grounded surfaces ("the maraka periods 2031–2034
   are classically sensitive", "the span reads at the purna band, around the 83rd year").
   **The assistant's recorded recommendation was to keep the death wall** (mortality
   statements are the one category where a mis-read costs the most and the engine's
   real-outcome generalization is measured NULL); **the user overrode it knowingly** —
   this line preserves that record. Correspondingly `_EXCLUDED_RE` in
   `app/llm/ai_interpret.py` dropped its death/lifespan/longevity/maraka tokens.

What did NOT move (kept without being asked, as safety/honesty floor):
- **Suicide/self-harm and serious/terminal-illness exclusions stay in code** on the walled
  panel (`_EXCLUDED_RE`, `TOPIC_DEFERRAL`, `AI_INTERP_SYSTEM`) — no register lifts them.
- **Decree-dated death stays refused on every surface**: "death around 2031", "will die",
  "dies by 60" trip both `_FORBIDDEN_RE` and a purpose-added decree-death arm in
  `_EXCLUDED_RE` (so the walled panel cannot decree either).
- **The Measured-Truth disclosure layer is untouched** (add-only law): every timed
  indication still ships alongside the calibration framing — the engine answers "what
  would Raman say", it is not a validated predictor.

Tests pinning the new policy: `tests/test_report_explainer.py`
(`test_timed_indications_now_pass` allowed-list; decree suites trimmed to decree-only) and
`tests/test_ai_interpret.py` (`test_lifted_indication_idiom_passes`;
`test_selfharm_illness_and_decree_death_are_caught`). CLAUDE.md's guard-line and
ai-interpret bullets were amended the same day to point here.

## Corpus-gated worklist from the chapter audit (2026-08-18) — what the waves deliberately did NOT encode

Waves 0-2 of `REPORT_CRITIQUE_2026-08-17.md` were executed on a machine where the
doctrine corpus is ABSENT. Every shipped addition is a re-read of already-computed state
citing only line numbers already recorded in the codebase. The items below were REFUSED
by the implementers because encoding them would have required minting a citation from
memory — the one thing the PRIME DIRECTIVE forbids. Each needs a corpus machine to pin
its exact range, after which it becomes a normal (mostly small) encoding task.

**Doctrine that needs a verified citation before it can be encoded**

1. **10th-from-the-Moon (and from the Sun) career derivation.** `primitives/career.py` is
   Lagna-only. Raman judges the 10th from Lagna, Moon and Sun and takes the strongest;
   the profession chapter therefore misses two of his three reference frames. Needs the
   HTJAH-II / HPA passage that states the three-frame rule.
2. **Anatomical mapping for Health: sign -> body region (Kalapurusha) and planet ->
   disease tables.** Grep confirms NO such table exists anywhere in `app/raman_saab`.
   The health section's own subtitle asks "which body areas does the chart mark" and it
   answers with house numbers. HPA carries both tables; the chapter+line ranges must be
   verified before encoding. **This is the single largest genuine content gap in the
   report** (audit's own words).
3. **Studies-in-Jaimini chara-dasha x karakamsa pairing.** The dated chara sequence and
   the karakamsa reading now both render (Wave 1/2), but the sentence that reads the
   karakamsa indications THROUGH the running chara period is not composed — the passage
   is unpinned. A navigational cross-reference was shipped instead.
4. **Spouse-description block** (7th sign nature, the 7th lord's navamsa, the D-9 spouse
   significator's temperament) and the **computed early/delayed marriage-timing lean**.
   The primitives exist; the descriptive passages (HTJAH-II 7th-house chapter) need their
   ranges verified before the block can quote or paraphrase them.
5. **Balance-of-dasha-at-birth citation.** The row now renders (Wave 2, foundation) as
   disclosed JD arithmetic with NO citation, because Raman's casting chapter / the
   Mainpuri proforma line is unpinned.
6. **Deeptadi precedence rule.** `state()` is priority-ordered (dignity-first) and the
   report now discloses secondary states, but HPA Ch.7 states no explicit precedence —
   the ordering is disclosed as the engine's own convention, uncited by design.
7. **Per-component Shadbala minima (GBB-8).** The "weakest component" pointer shipped as
   explicitly arithmetic-only ("no per-component minima are encoded"). GBB-8's component
   requirement table needs verification to make it a real per-component verdict.
8. **Moderating-factor clause citation.** The clause ("the affliction is qualified - ...")
   composes from ledger flags (parivartana_resilient / intact karaka / catastrophic-gate)
   and carries NO citation: Raman's "the affliction is considerably reduced by..." device
   has no recorded line. Framed as the judge's own disclosure until one is pinned.
9. **Psych affliction-to-the-mind screen** (Moon/Mercury under malefic aspect, 5th-house
   affliction). The critique marked it FOR CORPUS VERIFICATION; not implemented.
10. **Kemadruma-bhanga extended branch** — the benefic-drishti branch is labelled
    not-3HC in code; if Raman states it elsewhere, pin it and relabel.
11. **Missing significations** the audit found thin against Raman's chapter tables: H1
    appearance/character, H3 writing/neighbours, H2 food/sustenance, H5 speculation and
    upasana, H6 servants/subordinates, H12 bed-comforts. Each is an add-only row in
    `significations.py` + a rule bucket, but each needs its chapter-table citation.
12. **HPA-26 pinda -> longevity application** and the **ASP transit-multiplier via pinda**
    remain deliberately unwired (the reduced tables and Sodya Pinda themselves now render,
    Wave 1); both were already recorded as deferred pending corpus.

**USER decisions still open** (unchanged by the waves; recorded here so they are not lost):
Sun `MIN_REQUIRED` 5.0 (tuned) vs GBB-8:303's printed 6.5 — retune or relabel; whether
raja/dhana yoga-lean should be house-conditional in the preponderance ledger (doctrine
review); the Jaimini overlay's aspect scheme (rasi drishti vs graha drishti); the decade
timeline's whole-life mode default; and the Stage-9 holdout gate + the 90% bar vs the
proven 88.4% ceiling.

**Side effect to be aware of:** the two new digest head items (governing factor,
longevity foundation) shift the positions of later digest items, so `chart_feedback` rows
stored under older qids no longer align with the current digest. Harmless for new feedback;
historical rows should be treated as position-stale if they are ever re-analysed.


## Directional parivartana (2026-08-19) — OPEN, needs doctrine review + user sign-off

Found while citing the moderating-factor clause with the corpus mounted. NOT actioned:
this sits in the verdict path and would move the golden ratchet, so it is recorded rather
than changed.

`house_template._decide` credits `parivartana_resilient` as flat relief — a lord or karaka
in an exchange has a debilitation penalty bypassed (`house_template.py:1009-1020`,
"treat a debil-but-exchanged pillar as not-weak"), **regardless of the condition of the
exchange partner**.

Raman's own worked charts run BOTH ways:

- benign: "Jupiter and Venus have exchanged signs (parivartana), mutually benefiting each
  other" (HTJAH-I:8837)
- transmitting affliction: "the 8th and 10th lords have exchanged signs so that Saturn who
  is the 7th lord **also is afflicted by this parivartana**" (HTJAH-I:9119)
- explicitly undesirable: "Although the 7th lord Jupiter is strongly placed, his exchange
  of signs with 5th lord Saturn **is not desirable as it can deny marriage or progeny**"
  (HTJAH-I:9143)

On that showing an exchange TRANSMITS the partner's condition; it does not shield by
itself. A direction-aware rule would credit resilience only where the partner is itself
unafflicted, and would let an exchange with an afflicted or dusthana lord carry affliction
across instead.

**Why it was not changed here:** `parivartana_resilient` feeds `_decide`, so any change
moves the ratchet and needs the doctrine-review + user-sign-off path that B1-B4 went
through. The reporting side WAS corrected in the same commit — the moderating-factor clause
no longer implies Raman grants relief unconditionally and now names his counter-examples.

**If actioned**, expect movement on charts where a debilitated lord/karaka sits in an
exchange with an afflicted partner; measure exact/within-1/real-errors before and after and
report both axes side by side per MEASURED TRUTH.


### CLOSED 2026-08-21 — WILL NOT SHIP (user sign-off). Both flags stay off, permanently.

Implemented in `judges/house_template.py` on the `B1_DOMINANT_FACTOR_GUARD` pattern
(module-level, read LIVE, default OFF) and measured. Nothing is enabled; the golden ratchet
is byte-identical at the shipped values.

Two arms, because "an exchange transmits the partner's condition" can mean two things:

* **Arm A — `PARIVARTANA_DIRECTIONAL`** withholds the existing relief when the exchange
  partner is itself in trouble.
* **Arm B — `PARIVARTANA_TRANSMITS`** goes further: the lord itself counts hard-afflicted,
  which is literally what HTJAH-I:9119 says, and is the channel the B1 guard already reads.

And three readings of "partner in trouble" (`PARIVARTANA_PARTNER_TEST`), because Raman's two
counter-examples do NOT name the same mechanism: `condition` (partner combust /
debilitated-uncancelled / a maraka), `dusthana` (partner lords the 6th, 8th or 12th — the
mechanism at :9119, where the 8th lordship is what travels), and `either`. HTJAH-I:9143
("exchange … with 5th lord Saturn is not desirable") fits neither and is deliberately not
encoded: the 5th is no dusthana and Saturn is not described as afflicted there.

Measured over the 225 golden charts, 12,600 significations, both ratchet axes:

| variant | exact | within-1 | real errors | significations moved |
|---|---|---|---|---|
| baseline (shipped) | 259/293 | 283/293 | 10 | — |
| A / partner=condition | 259/293 | 283/293 | 10 | 0 (0.00%) |
| A / partner=dusthana | 259/293 | 283/293 | 10 | 0 (0.00%) |
| A / partner=either | 259/293 | 283/293 | 10 | 0 (0.00%) |
| B / partner=condition | 259/293 | 283/293 | 10 | 159 (1.26%) |
| B / partner=dusthana | 259/293 | 283/293 | 10 | 74 (0.59%) |
| B / partner=either | 259/293 | 283/293 | 10 | 162 (1.29%) |
| A+B (any reading) | 259/293 | 283/293 | 10 | same as B alone |

**Every variant leaves all three fidelity numbers exactly unchanged.**

**Arm A is a measured no-op — 0 of 12,600.** The reason is not that the rule is right; it is
that the relief it would qualify almost never fires. Across 225 charts, 93 carry at least
one exchange, but only **5** exchange members are debilitated-and-uncancelled — the shipped
relief's actual trigger — and none of those five has an afflicted partner. The backlog's
doctrinal criticism stands; its practical consequence is nil, and no golden can test it.

**Arm B moves 0.59%–1.29% of all output, always one step downward** (161 favourable→mixed,
1 favourable→afflicted at `either`). On the pinned corpus it is an exact wash: it FIXES
`HTJAH-II.h10_05 H10/status_honour` (favourable→mixed, Raman: mixed) and BREAKS
`HTJAH-II.h11_05 H11/elder_siblings` (favourable→mixed, Raman: favourable).

**Recommendation: do not enable either arm.** Arm A cannot be justified because it changes
nothing. Arm B is a real change to 1.29% of every reading, tightening favourable verdicts
toward mixed, bought with one golden fixed and one golden broken — no measured fidelity gain
on either axis. The B1 precedent does not apply: B1 was enabled because it cut real errors
(inversions) 12 → 10 at a known strict cost. Arm B cuts nothing. Enabling it would be a
purely doctrinal act, and the doctrine itself is split — :8837 has exchanges benefiting,
:9119 has one transmitting affliction, :9143 objects to an exchange on neither ground.

If a human wants it anyway, `dusthana` is the reading with the best textual warrant (it is
the mechanism :9119 actually describes) and the smallest blast radius (0.59%), and it moves
no golden at all.

Reproduce: `tests/raman_saab/judges/test_directional_parivartana.py` pins the helpers and
the flags-off no-op; the sweep is committed as
`tools/raman_saab/measure_directional_parivartana.py` and rebinds the three module flags
directly. (This paragraph previously pointed at a session scratchpad file,
`measure_parivartana_full.py`, which was never committed — corrected 2026-08-21.)

**DECISION 2026-08-21 — closed, will not ship.** The user signed off on the recommendation
above. `PARIVARTANA_DIRECTIONAL` and `PARIVARTANA_TRANSMITS` stay `False`, and the code stays
in place as the record of a measurement rather than as a rule awaiting a switch.

The reasoning is worth keeping short and blunt so it is not re-opened on a whim. Arm A is a
measured no-op — 0 of 12,600 significations — because the relief it would qualify almost never
fires: 93 of 225 charts carry an exchange, only 5 exchange members are debilitated-and-uncancelled,
and none of those five has an afflicted partner. There is nothing to enable. Arm B is a real
change to 1.29% of every reading, always one step downward, and it buys one pinned golden fixed
against one broken with no movement on either fidelity axis. The B1 precedent does not transfer:
B1 shipped because it cut inversions 12 -> 10 at a known strict cost, and arm B cuts nothing.

Enabling either would be a purely doctrinal act on a doctrine that is itself split —
HTJAH-I:8837 has exchanges mutually benefiting, :9119 has one transmitting affliction, and
:9143 objects to an exchange on neither ground. Where the texts disagree and the measurement is
silent, the engine keeps what it already encodes.


## Kemadruma bhanga attribution (2026-08-19) — OPEN, needs doctrine review + user sign-off

`bhangas.kemadruma_bhanga` cites 3HC:2182-2185 for its three cancellation branches. The
quoted Remark does not end there. The full passage runs to 3HC:2188:

> "Some authors say that if planets are m a kendra from birth or from the Moon or if the
> Moon is in conjunction with a planet there is no Kemadruma. Theie are yet other authors
> who say that these yogas arise from kendras and navamsas **but these observations are not
> generally acceptable.**"

Two problems:

1. Raman **attributes** the cancellation to "some authors" — he never asserts in his own
   voice that there is no Kemadruma in these cases. The engine cites the line as though he
   did.
2. His dismissal at :2188 is grammatically ambiguous. "these observations" attaches most
   immediately to the SECOND group ("kendras and navamsas"), but can be read as covering
   both reported opinions, since he is reporting throughout rather than endorsing.

**Not actioned:** `kemadruma_bhanga` feeds the yoga layer and therefore the verdict path, so
narrowing or dropping the branches moves the golden ratchet and needs the doctrine-review +
sign-off path. The DOCSTRING was corrected in the same commit — the anchor is now quoted in
full including the dismissal, and the attribution is stated.

**If actioned**, the question to settle first is scope: does :2188 dismiss the kendra/
conjunction cancellations too, or only the kendra-and-navamsa claim? A reviewer with the
printed page (the OCR is poor here — "Theie", "m" for "in") should decide before any code
moves. Expect movement on charts carrying an otherwise-formed Kemadruma.

**Settled in the same pass:** the extended benefic-drishti branch is NOT Raman's. The
backlog asked "if Raman states it elsewhere, pin it and relabel" — searching the mounted
3HC finds Kemadruma only at :2170-2266 and no such statement. The NOT-3HC label is correct
and stays.

### RESOLVED 2026-08-20 (Track 4b) — the text settles it; no code change proposed

The scope question does NOT need a reviewer with the printed page. It is answerable from
the mounted corpus, and the earlier pass missed the answer for a mechanical reason: it
searched for "Kemadruma", and the two decisive passages are OCR'd as **"Kemadiuma"** and
**"Kemidiumi s"**. A spelling-tolerant search finds exactly six mentions in the whole book —
:2170, :2173, :2185, :2255, :2263, :2266 — and the last three were never read.

Immediately after the Remarks, Raman applies the cancellation **in his own voice, on worked
charts, in both directions**:

> 3HC:2263-2268 — "Here you will see that Kemadruma is present because the houses on either
> side of the Moon are vacant. But there is distinct cancellation of the Kemadruma because
> (a) the kendras from the Moon are occupied and (b) kendras from the Lagna are also
> occupied."

> 3HC:2255-2261 — the converse, on Chart No. 8: "The above is a typically Kemadruma Yoga
> horoscope. No planets are placed on either side of Chandra and no planets are to be found
> in kendras either from Lagna or from the Moon."

A man does not demonstrate a cancellation twice, once each way, and mean it to be "not
generally acceptable". **:2187-2188 attaches to the SECOND reported group only** ("yet other
authors … these yogas arise from kendras and navamsas"). Branches (a) and (b) are Raman's
own applied doctrine, not merely "some authors", and the attribution defect is a citation
fix, not a behaviour question.

(The two passages describe charts with opposite kendra occupancy and no chart header stands
between them, so :2263 discusses a chart the OCR did not carry. Which chart it is does not
affect the reading: both statements assert the same rule.)

**Two further findings, both measured over the 225 golden charts / 12,600 significations:**

| reading | bhanga fires | exact | within-1 | real errors | significations moved |
|---|---|---|---|---|---|
| R1 as measured — (a)(b)(c)+extended | 63/63 | 259/293 | 283/293 | 10 | — |
| R2 drop (c) conjunction | 63/63 | 259/293 | 283/293 | 10 | 0 |
| R3 drop extended drishti | 63/63 | 259/293 | 283/293 | 10 | 0 |
| R4 keep only what Raman works | 63/63 | 259/293 | 283/293 | 10 | 0 |
| R5 maximal dismissal — no bhanga | 0/63 | 259/293 | 283/293 | 10 | 0 |

1. **Branch (c) is provably dead**, not merely unused. `_in_kendra_from` scores the same
   rasi-house as distance 1, the 1st is a kendra, and the Sun is not excluded from branch
   (b) — so every conjunction (c) can see, (b) has already seen. The docstring's claim that
   (c) earned its keep through the Sun was wrong and is corrected. The extended
   benefic-drishti branch is different: it is NOT provably redundant (Jupiter in the 5th or
   9th from the Moon aspects it from outside every kendra) but never once supplies a
   cancellation (a)/(b) had not already made across these 225 charts.

2. **The whole question is currently inert in the verdict path.** Even R5 — cancel nothing,
   so Kemadruma stands on all 63 charts that form it — moves **zero significations** and
   leaves all three fidelity numbers untouched. It does change the yoga layer visibly:
   `Y.KEMADRUMA` fires on 63/63 instead of 0/63, which reaches the Yogas section, the
   Arishta chapter's kemadruma note, and the preponderance ledger (an arishta yoga leans
   adverse). So the stake is a REPORT claim, not a verdict.

**Recommendation: change no behaviour.** The doctrine came out in favour of what is already
encoded. What was actually wrong was the citation and two claims in the docstring, and those
are fixed in this commit. The one live question left for a human was cosmetic-but-honest:
branch (c) is dead code kept "for textual fidelity" — keep it as a mirror of the quoted line,
or delete it as provably unreachable? Either is defensible; it cannot change a reading.

**CLOSED 2026-08-21 — branch (c) DELETED on user sign-off.** The shipped reading is now
**(a)(b)+extended**; the table above records the measurement as it stood, so R1 names the
configuration measured, not the one shipped. Deletion moved nothing, exactly as R2 predicted:
259/293 · 283/293 · 10 real errors, 0 significations moved. `bhangas.kemadruma_bhanga`
quotes the line in full in its docstring, which is where fidelity to the text belongs — an
`if` that cannot fire records nothing a reader can check. The extended benefic-drishti branch
STAYS (it is not provably redundant) and keeps its NOT-3HC label; a test now builds the chart
only it can cancel — Moon in the 2nd, Jupiter in the 6th — so deleting it would fail loudly
rather than silently.

## Chara dasa x Karakamsa pairing (2026-08-19) — NOT ENCODABLE from the mounted text

The audit wanted the sentence that reads the karakamsa indications THROUGH the running
chara period. It cannot be composed from what is mounted, and the reason is the import, not
the doctrine:

* the JAIMINI import is PARTIAL — 6 chapters (4, 5, 6, 9, 11, 49), and chapter 5 is 48
  lines of OCR junk;
* "karakamsa" appears **only** in chapter 9 (the Summary), at :797-838, where Raman lists
  what the karakamsa reveals (appearance via its lord, character and mind, pre-disposition
  to troubles, education, profession) — a topic index, not a timing rule;
* chapter 4 is the Chara Dasa chapter and mentions karakamsa **zero times**.

So the pairing is either in a chapter that did not import or is not stated. The
navigational cross-reference that shipped instead remains the correct surface. A session
with a complete Studies-in-Jaimini scan should look for an article pairing the two before
re-opening this.


## Thin significations (2026-08-19) — CLOSED, measured, and closed AGAINST adding them

The audit's six thin significations were checked twice with the corpus mounted. Detail and
anchors live in the `doctrine/significations.py` module docstring; the summary:

* **Four of six ARE Raman's** (H1 character/environment, H2 food/literary gift,
  H3 writings/neighbours, H5 fame-and-position/discriminating-power) — HPA-19:64-67,
  :114-117, :190-193, :300-303.
* **Three are not his, in the bhava requested**: H5 speculation (absent), H5 upasana
  (worship is his 12th-house matter, HPA-19:785), H6 servants (absent), H12 bed-comforts
  (absent). BPHS/classical attributions, barred by the divergence firewall.
* **The four he does state were added and MEASURED, then reverted**: cross-layer agreement
  fell **0.475 → 0.439** and 62 tier-3 evidence snapshots churned. The scored golden
  ratchet did NOT move (259/293) because a new signification carries no golden expectation
  and is never scored — which is precisely why the ratchet alone was not a sufficient gate
  here, and the convergence test was.

**The doctrinal reason**: naming a matter is not giving rules to judge it. Raman lists
these in a definitional sentence and gives no combinations for them, so a signification
added here routes to no rule bucket and is decided by the polarity fallback — a verdict
manufactured from no evidence.

**To re-open**: the prerequisite is the RULE BUCKET, not the row. Find Raman's combinations
for the matter, encode those, and the signification follows. The audit's own phrasing ("an
add-only row + a rule bucket") had it right; only the row is cheap.


## H3.C.4 courage-favourable rule encoded (2026-08-22) — ✅ SHIPPED, two open caveats

**Trigger** (prioritization only, not justification — see below): a real-outcome study
(`docs/raman_saab/FAILURE_ATLAS.md`, AstroDatabank) found H3 `courage` reads AUC 0.480
against a "military service" indicator, labeled INVERTED. Per this project's own governance
(`tools/raman_saab/astrobank/METHODOLOGY.md`: "No engine constant, threshold, or rule may be
tuned from these results directly"), that finding is **not** the reason for this change — it
only motivated auditing H3's rule coverage, where a genuine, citation-backed gap turned out
to already exist independent of any real-outcome number.

**The gap**: `H3.C.4` (HTJAH-I:3421) — "3rd lord in a beneficial Nakshatra and Navamsha,
aspected by benefics, with Mars equally well disposed → a man of character and conviction,
brave and straightforward" — was `kind="descriptive", condition=None` since the rule set was
first written, the only rich *favourable* courage combination in the file (everything else
feeding courage is malefic-leaning "3rd lord with X" temperament atoms, or bridged in from
the `siblings` bucket).

**Encoding** (`house_03_sahaja/combinations.py`, four conjuncts, one per clause of Raman's
sentence, all reused from already-shipped primitives — no new invented threshold):
1. `_ThirdLordInBeneficialNakshatra` — 3rd lord's nakshatra ruled by a natural benefic
   (`primitives.nakshatra.nakshatra_lord`, the function `conditions.InStarOf` already uses).
2. `C.VargaDignity("LORD_OF:3", varga="D9", states={"exalt","own","friend"})` — beneficial
   Navamsha, the project's existing "beneficial" dignity-state set.
3. `_ThirdLordAspectedByBenefic` — Jupiter/Venus only, matching the identical-phrase
   precedent at `house_02_dhana/combinations.py:320` and `house_05_putra/combinations.py:228`.
4. `_NotDecisivelyWeak("Mars")` — `not effective_strength("Mars", chart).decisively_weak`,
   the shipped, golden-tuned B1 measure (this same file's `DOCTRINE_BACKLOG` B1 entry),
   deliberately NOT a stricter `is_powerful`-style gate (that shortcut is the one the B1
   module's own docstring records as over-firing Shankha/Kahala 102/164, 48/164).

**Measured**: full 293-chart golden corpus, before/after byte-identical — strict exact
259/293, within-1 283/293, real errors 10. The rule fired on exactly one golden
(HTJAH-I chart_61) as additional corroborating evidence for an already-correct
"courage: favourable" verdict; it changed zero verdicts anywhere in the corpus.
Evidence snapshot `HTJAH-I.chart_61.json` regenerated to include the new citation/fired-id.

**bphs-doctrine-reviewer verdict: SHIP-WITH-CAVEAT** (confidence MEDIUM). Two open caveats
recorded rather than silently resolved:
1. "Beneficial Nakshatra" has no formal BPHS anchor on disk (no gana/tara-from-Moon/named-list
   definition found in `data/knowledge_library/`) — nakshatra-lordship-by-nature is a
   *consistent*, not an *invented*, reading (it's the concept `InStarOf` already operationalizes
   elsewhere), but it is one plausible reading among others (a tara-from-Moon sense is the more
   common classical use of "auspicious star"). Revisit if a tara/gana-based source surfaces.
2. `decisively_weak=False` is a materially looser bar than the `{exalt,own,friend}` requirement
   the SAME sentence sets for the 3rd lord two clauses earlier — Raman's "equally well disposed"
   reads as parallel-positive, not merely "not ruined." Deliberate (matches the project's own
   anti-overfire precedent rather than risk a stricter gate over-firing), but asymmetric — a
   future tightening pass must re-run the golden ratchet before "fixing" this asymmetry, not
   assume tightening is free.

Not yet touched by this pass: the question of whether bridging courage's evidence through
the shared `rule_tags=("siblings","courage")` bucket is itself doctrinally correct
(HTJAH-I:3324 vs 3428 read as one combined reading or two) — deferred to a follow-up pass.


## H12.C.D6 "equal in strength" (2026-08-22) — INVESTIGATED and HELD, not shipped

**Attempted**: encode the last dead H12 combination, `H12.C.D6` (HTJAH-II:16444) — "rulers of
(2&12)/(5&9)/(6&12)/(3&11)/(4&10) equal in strength → criminal action (absent other
mitigation)" — using a new `_LordsEqualInStrength(house_a, house_b)` condition comparing two
D1 lords' total Shadbala rupas, `C.Or`-ed across the five cited house-pairs. "Equal" was read
as `abs(rupas_a - rupas_b) <= MARGINAL_BAND`, reusing the project's own shipped B2 constant
(0.2 rupas) rather than inventing a new number.

**Why it was held**: `MARGINAL_BAND` was tuned and golden-validated for a *different*
statistical question — one planet's total vs. its OWN fixed, planet-specific bar
(`MIN_REQUIRED`, 5.0-7.0 rupas) — not the spread between two independently-varying planets'
totals, which has different natural variance. Measured against the 209 Track-B golden
charts, the reused-tolerance version fired on **57/209 = 27%** of charts. The full 293-chart
ratchet stayed byte-identical (259/293 exact, 283/293 within-1, 10 real errors) throughout,
but that silence is NOT evidence of good calibration here: `incarceration` sits in
`house_template._DUSTHANA_AFFLICTION_KEYS`, so any single fired malefic with no benefic
contradiction already confirms "afflicted" — a 27%-firing rule can ride along on charts
already decided by other evidence and never be tested as the DECIDING factor on any golden.

**bphs-doctrine-reviewer verdict: INSUFFICIENT-EVIDENCE / HOLD-AS-DOCUMENTED-LIMIT.**
Back-of-envelope: rupas empirically span ~0-12 (`test_adapter.py`, `test_shadbala_compute.py`
pins); a uniform-spread estimate puts a single pair's P(|Δ|≤0.2) at roughly 3-4%, and only 7
grahas hold lordship across the 10 house-slots in play (a birthday-paradox-style crowding
effect across the 5 pairs) — ORing five such checks lands close to the observed 27% by
arithmetic alone, not because the combination is doctrinally common. The `C.Or` structure
itself is textually correct (Raman lists the pairs disjunctively); the defect is the
per-pair tolerance, reused from a context it was never validated for. DOCTRINE_BACKLOG's own
B2 entry already recorded once that widening that band beyond its original narrow scope
broke a golden (chart_54 H10) — this reuse repeated the same class of mistake without
re-testing against that precedent.

**Reverted**: `H12.C.D6` is back to `kind="descriptive", condition=None` (dead, as before),
its `afflicted=` text updated to record this investigation so a future session doesn't
re-attempt the same reuse. Confirmed the revert restores the byte-identical ratchet.

**To re-open** (per the reviewer's own conditions — either one, not a same-day constant
reuse):
1. Derive the pairwise "equal" tolerance empirically from this project's own chart corpus
   (e.g. the percentile spread of `|rupas_A - rupas_B|` per specific lord-pair across the
   golden/reference set) instead of reusing `MARGINAL_BAND`, then re-run the ratchet.
2. Build a test that isolates charts where this rule would be the SOLE fired evidence for
   `incarceration` (not merely corroborating alongside another malefic) and confirm it
   doesn't over-fire there — the ratchet's redundancy blindness means this has never
   actually been checked, for this rule or for how many of H12's other malefic rules ride
   the same confirmation mechanism.


## Dead-rule inventory (2026-08-22) — a systematic, citation-backed coverage gap

Measured across the whole rule corpus: **128 of 847 rules (15.1%) are dead** —
`kind="descriptive"` / `condition=None`, so they can never fire. By house:

| house | dead/total | | house | dead/total |
|---|---|---|---|---|
| H1 | 19/106 (17.9%) | | H7 | 6/73 (8.2%) |
| H2 | 19/92 (20.7%) | | H8 | 11/71 (15.5%) |
| H3 | 3/61 (4.9%) | | H9 | 7/73 (9.6%) |
| H4 | 6/50 (12.0%) | | H10 | 6/42 (14.3%) |
| H5 | 4/50 (8.0%) | | H11 | **21/75 (28.0%)** |
| H6 | 4/50 (8.0%) | | H12 | 22/104 (21.2%) |

**The load-bearing finding: many `TODO(predicate)` notes are STALE.** They were written when
the blocking primitive did not exist; the primitive was built later and nobody revisited the
rule. Confirmed present today: `primitives/maraka.py`, `primitives/arudha.py`,
`primitives/dispositor.py`, the `shadbala/` package. H2 alone has 4 Arudha-blocked rules
(C.39/40/46/68), 3 Maraka-blocked (C.41/42/43 — C.41 now encoded, below), 2 navamsa-dispositor
(C.33/34), 3 sign-modality (C.36/37/38, trivially computable), 1 Kalabala (C.35), 1 dispositor
(C.31). This is a real, doctrine-cited backlog independent of any real-outcome measurement,
and a future session should walk it house by house rather than trust the TODO text.

**Not a polarity story for H2** (checked, because it WAS the story for H3.C.4): H2 `wealth`'s
live rules are already balanced 25 benefic / 25 malefic / 12 neutral, and its dead rules are
proportionally balanced too (9/6/2). Encoding them would not systematically shift H2's
favourable/afflicted lean either way.


## H2.C.41 Lagna-lord-in-12 + Maraka (2026-08-22) — ✅ SHIPPED WITH CAVEAT, gate discharged

**Shipped**: the previously-dead `H2.C.41` (HTJAH-I:2526, POVERTY block) encoded as
`C.And(C.LordIn(1, 12), _LordTouchedByMaraka(1))`. The old `TODO(predicate): MarakaDetection`
was stale — `primitives/maraka.py` postdates the deferral.

**Doctrinal choice — PRIMARY maraka tier only.** `maraka_points()`'s all-tier set averages 5.5
of 7 grahas and would fire on ~all 19 Lagna-lord-in-12th goldens, rendering Raman's own explicit
"with/aspected by a Maraka" qualifier INERT — a reading that deletes a cited clause is worse
doctrine than a narrowing that preserves it. Secondary/tertiary hold benefics-conjunct-2/7-lords,
the 6th lord and the Shadbala-weakest planet (`00_method_overview.md:160`) — longevity-net
members, not "a Maraka planet" in a poverty rule. Primary averages 3.0 of 7. The local
inconsistency with `house_template._maraka_grahas` (all tiers) points the RIGHT way: B3 exists
precisely because the all-tier set over-afflicts non-death matters. HTJAH-I:783's within-primary
gradation ("associates kill hardest, lords least") is deliberately NOT modelled; #41's phrase
is bare.

**Measured.** Fires 14/209 Track-B goldens (6.7%). Full 293-chart ratchet byte-identical:
259/293 exact, 283/293 within-1, 10 real errors. Suite 605 passed. The primary tier is
Shadbala-independent, so Track-B and ephemeris charts behave identically (a point D6 lacked).

**Gate discharged — H2.C.29 double-count check.** The reviewer flagged that `H2.C.29`
(HTJAH-I:2475, `wealth`/malefic) also requires `C.LordIn(1, 12)`, so one placement could enter
the wealth ledger as two malefic testimonies — which would break the "one testimony among many,
preponderance contextualizes it" argument this ship rests on. **Measured: co-fire on 2/209
charts** (`HTJAH-I.h6_04`, `HTJAH-I.h6_12`) — 2 of C.41's 14 firings, 14%. Low, and the rules
are not substantively redundant: C.29 additionally requires evil planets in the 2nd AND
10th/11th-lord involvement, and reads "always in debt", a different combination and outcome
that merely shares one conjunct. Gate passes; ship stands.

**Caveat, recorded honestly — the ratchet CANNOT validate this rule.** Zero of the 14 firing
charts carries a scored H2 expectation. This is a plain coverage gap, NOT evidence-redundancy
(cf. H12.C.D6, where `incarceration`'s `_DUSTHANA_AFFLICTION_KEYS` membership caused the
blindness); `wealth` goes through normal preponderance weighing, so the ratchet WOULD be
sensitive if a scored chart existed. The B4 precedent (fires 20/225, changes 0 confirmed
verdicts) therefore does NOT cleanly extend: B4's basis included firing on `h7_16` WITHOUT
flipping it — a real stress case surviving. That element is absent here.

**Discrimination is weak, by arithmetic not by defect.** Lagna-lord-in-12th base rate is
19/209 = 9.1% (≈1/12); the maraka qualifier passes 74% of the time, so the rule is
~"Lagna-lord in 12th" minus a 26% haircut. With whole-sign drishti + Jupiter 5/9 + Mars 4/8 +
Saturn 3/10 + the locked Rahu/Ketu 5/9, ~3 primary marakas contacting one planet is near-certain.
Acceptable as a preponderance input; not a discriminating test.

**Corpus-machine follow-up**: HTJAH-I:2526 verbatim. All sourcing here is the repo's derived
methodology table (`house_02_dhana.md:135`), not Raman's printed line — verify (a) the exact
phrasing of "a Maraka planet" and whether Raman qualifies which maraka, (b) whether "extreme
poverty" is stated absolutely or conditioned on absence of mitigation like #44's Jupiter clause.

**Sibling rules NOT unblocked by this**: `H2.C.42` and `H2.C.43` cite the same maraka predicate
and remain descriptive; they need `Parivartana(1,6)`-with-maraka and a functional-nature-filtered
malefic set respectively. Encode only after this rule's corpus-machine follow-up is discharged.


## H7 marriage backlog re-checked (2026-08-22) — NO REMAINING WORK, closed

Picked up the "H7-marriage (+H5) DRAFT backlog" above expecting live rows to work. Re-reading it
against the current engine: **there are none.** Recorded so no future session re-opens it:

* **Mode-A (10 items)** is already closed as a DOCUMENTED LIMIT, by measurement, not opinion — a
  benefic-relief lift was built and tested and does not discriminate (the reliefs it keys on are
  present on genuinely-afflicted charts too, and enabling it would regress the shipped
  h7_02/05/15 fixes). The section's own verdict: "do NOT pursue a relief lift."
* **Mode-B** is fully shipped: h7_02/05/15 via `H7.C.86`, h7_16/19 via `_marital_bond_gate`.
* **Measured today**: of the engine's 10 remaining dist-2 errors, **zero are H7** (or any marriage
  signification). The marriage work genuinely landed.

The 10 current dist-2 errors are: H1 self ×3 (chart_09/17/31), H5 children ×2 (h5_10/h5_16), and
one each of H2 wealth (chart_44), H3 siblings (chart_60), H6 disease_chronic (h6_04), H9 father
(h9_02), H11 elder_siblings (h11_01). chart_44 and chart_60 were already registered limits;
chart_17 and chart_31 are newly registered above. **H1 `self` is now the largest single cluster
(3 of 10)** and is the natural next target for dedicated work — not H7.


## The 10 remaining dist-2 errors are ONE mechanism (2026-08-22) — measured, and already optimal

Profiled all 10 current dist-2 errors together (engine verdict, Raman's verdict, fired benefic /
malefic counts, and the three pillar-strength booleans). The result is far more concentrated than
the per-chart register entries suggest:

| chart | sig | engine | Raman | ben/mal | pillars L/K/B |
|---|---|---|---|---|---|
| chart_09 | self | favourable | insufficient-evidence | **1/4** | 1/1/1 |
| chart_31 | self | favourable | afflicted | 2/2 | 1/1/1 |
| chart_60 | siblings | favourable | afflicted | 3/3 | 1/1/1 |
| chart_44 | wealth | favourable | afflicted | **1/2** | 0/1/1 |
| h5_10 | children | favourable | afflicted | **0/0** | 1/1/1 |
| h11_01 | elder_siblings | favourable | afflicted | 2/0 | 1/1/1 |
| h9_02 | father | favourable | afflicted | 6/6 | 1/1/1 |
| h6_04 | disease_chronic | favourable | afflicted | 1/1 | 1/0/1 |
| chart_17 | self | afflicted | favourable | 5/2 | 1/1/1 |
| h5_16 | children | afflicted | favourable | 2/1 | 1/1/1 |

**8 of 10 are the engine reading favourable where Raman reads afflicted or abstains**; only 2 run
the other way. Nearly all carry all-three-pillars-strong.

**This is BY DESIGN, not a defect.** `_decide` clause 2 (`house_template.py:457-501`) deliberately
does NOT count fired-rule surplus — it weighs Raman's three strength PILLARS (lord, karaka,
Bhava-Bala) per the three-factors doctrine, thresholds `CONTRA_PILLAR_AFFLICT=3` /
`CONTRA_PILLAR_FAVOUR=2` ("Stage-3 calibration, user-signed-off V2"). So chart_09's 4:1 malefic
evidence is irrelevant by construction: 3 strong pillars ≥ 2 → favourable. Any apparent
"tie should read mixed" intuition is a red herring — counts never enter this clause.

**Threshold sweep — the current setting is already a local optimum.** The knobs are read live
specifically so a tuner can monkeypatch them; swept both:

| AFFLICT | FAVOUR | exact | within-1 | real errors |
|---|---|---|---|---|
| 2 | 2 | 256 | 282 | 11 |
| 2 | 3 | 252 | 283 | 10 |
| 2 | 4 | 234 | 285 | 8 |
| **3** | **2** | **259** | **283** | **10** ← current |
| 3 | 3 | 255 | 284 | 9 |
| 3 | 4 | 237 | 286 | 7 |

Raising FAVOUR trades strict accuracy for real errors at a poor rate: 2→3 costs **4 exact** to
save **1** real error (+1 within-1); 2→4 costs **22 exact** to save 3. Compare the B1 guard that
DID ship: −2 exact, **+2** within-1, −2 real errors — a genuinely two-sided gain. Nothing in this
sweep matches that shape. **Do not re-run this sweep; do not re-tune these knobs on this
evidence.** A real improvement here needs a NEW mechanism that separates these 8 charts from the
strong-pillar charts the engine currently gets right — not a threshold move, which trades one
error class for a larger one.

This supersedes the framing in the documented-limits register that B1 comparative-weighing is
"the single lever [for] chart_52 + chart_60": it is the lever for **8 of the 10** remaining
errors, which raises its value — and the sweep above shows the lever cannot be pulled by
threshold alone.


## Tier-3 bhava-rescue (2026-08-22) — gate MET, fix REFUTED twice, CLOSED

The FEEDBACK_UTILIZATION_PLAN Tier-3 item ("H3 over-affliction bhava-rescue", HTJAH-I:503-505,
gated on the wife's H3 as the n=2 counterexample) came due today: the wife's sibling facts
arrived (younger brother = very good relations → H3 siblings truth favourable; engine reads
afflicted — the same over-affliction shape as the anchor chart). **Condition (a) of the gate is
satisfied.** The fix itself was then investigated and is REFUTED, on two independent grounds:

**1. Refuted by the source's own conditions.** The verbatim passage (read today from
`knowledge_library/how_to_judge_a_horoscope_raman/chapter_001`, lines ~503-505): "But if in a
particular case, **the lord is badly placed**, and **the house itself has good conjunctions and
aspects** then evil results should not be predicted." Diagnosed both family charts against it:
father — H3 lord Saturn STRONG (house 2), H3 has ZERO occupants and ZERO benefic aspects;
mother — H3 lord Jupiter STRONG (house 5), H3 likewise empty of benefic conjunction/aspect.
Neither condition obtains on either chart. A faithful encoding of the citation **cannot fire on
the two charts it was pre-registered to fix.** Loosening the conditions until it does would be
citation-shopping — encoding the target, not the text.

**2. The actual mechanisms are load-bearing, by measurement.** What really produces the family
afflicted verdicts: father — the D9 `weakens` modulation dropping a contradiction-mixed to
afflicted (`_navamsa_modulate`; the SAME mechanism as registered golden miss chart_17, now two
independent counterexamples); mother — decisive rules H3.C.36/38/39. A/B on the goldens
(monkeypatch, nothing shipped): blocking the weakens-drop on contradiction-mixed alone costs
**exact 259→248 (−11)** for within-1 +1 and real-errors −1 (chart_17). Eleven goldens where
Raman HIMSELF reads afflicted depend on that drop. Decisively worse than any shippable trade
(B1 precedent: −2/+2/−2).

**Closure.** The family H3 misses are genuine documented limits of the chart_60 class: the
doctrine as encoded from Raman's own worked charts reads these configurations afflicted, and
the lives are favourable — the real-outcome generalization gap, not an implementation bug. The
n=2 pattern the gate was designed to detect is REAL; the pre-registered mechanism just does not
cover it, and no alternative mechanism survives the golden A/B. **Do not re-open without a
DIFFERENT verbatim citation whose conditions actually obtain on such charts.** Tier-1
(elicitation) is DONE; Tier-3 is CLOSED-REFUTED.


## H11 dead-rule sweep (2026-08-22) — pass 1 of the all-houses sweep: 2 shipped, 2 held, 17 correctly left

First house pass of the full dead-rule sweep (H11 first: worst dead-rate 21/75 = 28%, plus the
mother's confirmed elder_siblings miss). Full triage of all 21:

**Correctly descriptive, no action (13):** C.24-30 (seven source-of-gains flavour texts whose
conditions are ALREADY live as H11.P.* placement rules — kept descriptive precisely to avoid
double-counting); C.32-36 (five ear/health outputs with no H11 signification key — and the
"Thin significations" entry already closed AGAINST adding keys without rule buckets); C.40
(a co-born COUNT output, which the verdict engine cannot express, and which Raman himself
hedges — "students should test it for themselves").

**Genuinely still blocked (4):** C.12 (Navamsa-dispositor-of-lagna-lord multi-clause), C.16
(Vaiseshikamsa / multi-varga attainment — no such primitive in app/), C.17/C.18 (Dasa-timing
predicates — the rule engine is static-natal; no dasha context in EvalContext by design).

**✅ SHIPPED — H11.C.4** (HTJAH-II:14362, "fortified planets in the 11th"): encoded as any
11th-occupant with B1 `effective_strength` band "strong" AND not decisively-weak — per-planet-
vs-its-own-bar, the exact context B1 was tuned for. Reviewer: VALIDATED/SHIP, HIGH confidence —
Raman's "fortified" is a generic strength word (when he means dignity he names it, cf. the H12
`_LordHasDignity` precedent). Fires 62/209 (30%, blunt but placement-class-normal), and
**12 firing charts carry scored H11 expectations — the ratchet genuinely tested this rule**
(unlike H2.C.41's coverage-gap blindness) and stayed byte-identical. Designed behaviour, not a
gap: Rahu/Ketu (no Shadbala bar) and Track-B stated-position charts cannot fire it — "fortified"
is a strength claim such charts cannot substantiate.

**✅ SHIPPED WITH CAVEAT — H11.C.5** (HTJAH-II:14367, "weak planet in the 11th — eclipsed,
depressed, defeated in planetary war, or in inimical vargas"): encoded as any non-node
11th-occupant `decisively_weak` (weak band / combust="eclipsed" / debil-uncancelled=
"depressed" — the two facts B1 was literally built from). War-defeat carried indirectly (Yuddha
Bala depresses the Shadbala total). Fires 31/209 (15%), 4 scored firing charts, ratchet
unchanged. Caveats recorded: (a) the inimical-vargas leg is NOT modelled — disjunct-only, so
its absence causes only false negatives, disclosed in the rule text; pending a varga-dignity
predicate; (b) the weak-band leg reads Raman's em-dash list as examples of "weak" (head-noun
reading), a slight deliberate broadening.

**⛔ HELD (reverted same day) — H11.C.6 / H11.C.7** (HTJAH-II:14388/14390, friendly/inimical
lord-relationships): briefly encoded on NAISARGIKA relationships; the reviewer PROVED both
predicates unsatisfiable by enumerating all 12 lagnas (lordship fixed per lagna x naisargika
fixed per pair: no lagna yields three mutually-friendly 1/2/11 lords, none yields both 2nd+11th
lords natural enemies of the lagna lord — even one-directionally). An evaluable rule no chart
can satisfy is WORSE than a descriptive stub: it claims coverage the engine does not have. The
decisive doctrinal inference: Raman wrote these sentences about real nativities, so "friendly"/
"inimical" there cannot mean fixed natural friendship — it must be the chart-dependent COMPOUND
relation (naisargika x tatkalika), which exists in-repo as `dignity._compound_relation`
(private, already trusted by Sthana Bala) but is not exposed to the conditions algebra.
**Re-open path**: expose the compound relation as a condition, re-encode the PAIR together
(they are Raman's paired opposite sentences), measure firing + ratchet, re-review. Reverted to
descriptive with the proof noted in the rule file itself.

**New sweep lesson (added to the per-rule protocol):** for any predicate built ONLY from
lagna-fixed lordship and pair-fixed tables (naisargika, sign lords), CHECK SATISFIABILITY BY
ENUMERATION over the 12 lagnas before encoding — a 0% corpus firing rate on such a predicate is
a proof of impossibility, not a small-sample observation.

**H11 elder_siblings note (the mother's miss):** nothing in the dead inventory serves it — the
only dead elder_siblings rule (C.40) is a count-output. Her H11 miss remains a real-outcome
observation with no citation-backed engine gap behind it; per governance it stays a
prioritization signal only.


## H12 dead-rule sweep (2026-08-23) — pass 2: 3 shipped, 1 already-held, 18 correctly left

Second house pass (H12: 22 dead, second-worst rate; the mother's expenditure miss set the
order). Triage of all 22:

**Genuinely blocked (16):** the bulk of H12's dead inventory needs varga machinery the
conditions algebra does not carry — shashtyamsa/D60 class overlays (A23, B1, F3, I6-partial),
"benefic vargas" plural (A1, E2-half, F6), drekkana + vaiseshikamsa (B4), navamsa-dispositor-
of-house (A21, B1), karakamsa frame (G2), navamsa moolatrikona (F7 — EXCLUDED BY DESIGN,
`_VARGA_DIGNITY_STATES` deliberately omits it), comparative cross-planet strength (C4 — same
class as the held D6), multi-house affliction-grade aggregate (A5), amsa overlays (A22),
vague "beneficially disposed" gates (E1), and Dasa-free source reads needing verification
(B3's "(and variants)" compression). G1 (a single ultra-specific four-condition nativity)
is encodable but would assert one exact configuration — left descriptive as effort-vs-value.
D6 stays HELD (its own entry above).

**✅ SHIPPED — H12.C.C3** (HTJAH-II:16398, "a beggar is born"): the "Navamsa-debility overlay"
TODO was stale — `VargaDignity` covers it exactly (Sun D9-debil = Libra, Venus D9-debil =
Virgo, so "Venus in Virgo in Rasi AND Navamsa" is InSign+VargaDignity{debil} literally).
Reviewer: VALIDATED/SHIP, HIGH — printed text read verbatim, one-to-one transcription, no
dropped clause. Fires 2/209 (1%), zero scored-chart exposure, ratchet byte-identical.

**✅ SHIPPED WITH CAVEAT — H12.C.F1** (HTJAH-II:16491, Saturn/Mandi on 12th + 12th lord in
Vipat/Pratyak/Naidhana tara): the Tara TODO was stale — `TaraOf` has carried `LORD_OF:n`
support (its own docstring cites HTJAH-I:1142-1146); Mandi read from `chart.upagrahas`.
Reviewer: VALIDATED, HIGH — source parentheses ARE {3,5,7}; the 10% firing rate is the
predicate's own arithmetic (Saturn covers ~4/12 houses x 3/9 taras ≈ 11%), a severity
mismatch present in Raman's own text, accepted per the H2.C.41 preponderance reasoning.
Caveats: (i) Mandi leg absent on Track-B charts (no upagrahas) — disclosed in the rule text;
(ii) Mandi-ASPECT is unmodelled (occupancy only — Mandi is an upagraha point with no standard
drishti); both disjunct-only, false-negatives-only.

**✅ SHIPPED WITH CAVEAT — H12.C.F2** (HTJAH-II:16498, combust/debilitated malefic afflicting
the 12th): combust bar = the engine-wide B7 substantial threshold; debility bhanga-gated per
B1. Reviewer: VALIDATED, MEDIUM — "a state of eclipse" is read as combustion per Raman's own
usage in the SAME chapter (16381-16385 treats "eclipsed" and "combust" as one register) and
the H11.C.5 precedent; the alternative grahana reading (Sun/Moon under node-eclipse) is
unmodelled — concretely, a Sun-conjunct-Rahu afflicting the 12th will not fire (the Sun can
never be combust). Disjunct-only, false negatives only. Revisit if a corpus pass finds Raman
glossing "eclipse" with node language.

**Ratchet-blindness ledger for this pass** (per the cross-cutting entry below): only F2 was
genuinely ratchet-tested (one scored firing chart, HTJAH-II.h12_10, verdict unmoved); C3 and
F1 shipped on coverage-gap silence — their fidelity rests on the reviewer's verbatim source
reads, not on the ratchet. One tier-3 evidence snapshot regenerated (NH.chart_46 —
evidence-only, all six H12 verdicts identical).


## H1 dead-rule sweep (2026-08-23) — pass 3: 3 shipped (2 review-corrected), 1 reverted-by-measurement, 15 correctly left

Third house pass (H1: 19 dead; the golden corpus's largest error cluster and the mother's
health miss set the order). The most instructive pass so far — the ratchet caught a live
regression, and the reviewer corrected an encoding before it shipped wrong.

**Correctly left (15):** H1.M.G1/H1.M.MD (methodological prose, not predicates); H1.C.32
(vague "decent position"); H1.N.57/60/62 (vague "adverse Navamsha" summary rows); H1.C.23
(blocked: friendly-Drekkana class, no D3 in the algebra); H1.N.52 (comparative lord strength —
the held D6 class); H1.N.65 (navamsa-dispositor chain); H1.N.67 ("well disposed" holistic
gate); H1.C.22/24/25 (encodable but blunt/phase-output; deferred as effort-vs-value);
**H1.C.W33 — confirmed NOT a stale TODO**: its deferral note is a live design decision
(boolean malefic would double-count the chart-33 affliction the Sakata arishta already
carries) — and this pass PROVED that note right, see N.38 below.

**⛔ ENCODED AND REVERTED — H1.N.38** (HTJAH-I:1709, lord of Lagna weak/debilitated/combust →
sickly): the predicate is a faithful transcription ("weak, debilitated or combust" IS the B1
`decisively_weak` founding list) — and firing it as a context-free boolean malefic reproduced
EXACTLY the failure W33's deferral note predicted for this rule class: on chart_33 (lagna lord
neecha) it manufactured a benefic-vs-malefic contradiction that blocked the Y.SAKATA arishta
drop, flipping the golden's correct 'afflicted' to 'mixed'. **Measured: strict 259→258,
within-1 and real-errors unmoved — a pure one-sided loss.** Reverted; reviewer confirmed the
revert ("a change buying nothing on any axis cannot ship"). The working predicate class
(`_LagnaLordDecisivelyWeak`) is retained unused for promotion behind the same gate W33 names:
a lord-dignity-aware contradiction policy. THE RATCHET DID ITS JOB — first live catch of the
sweep.

**✅ SHIPPED (review-corrected) — H1.N.58** (HTJAH-I:1767, 1st/9th lord exalted → wealth
influx): first encoding was a standalone `Or(exalt-1st, exalt-9th)` firing 36/209 (17%). The
reviewer read the source paragraph and HELD it: "either of the lords" is scoped to the
paragraph's base configuration — Lagnadhipati JOINED WITH the 9th lord IN the 9th (:1764, the
base N.56 already encodes), per the file's own amplifier convention (N.50/N.53 =
And(base, qualifier)). Re-encoded with the gate: **fires 2/209 (1%)** — the rare event Raman
actually wrote, a 34-chart over-fire caught before shipping. Ratchet unchanged.

**✅ SHIPPED WITH CAVEAT — H1.N.66** (HTJAH-I:1972, contact between 1st and 6th lords →
health/defamation risk): `_LordsInContact(1,6)` — conjunction or aspect in EITHER direction.
Reviewer VALIDATED both scrutinized choices: identity→False (Raman's dictum is a two-place
relation; his worked Chart 18 is two planets; counting Taurus/Scorpio dual-lordship would
blanket-fire from the lagna alone) and either-direction aspect (the dictum is directionless;
restricting to the Chart-18 gloss's direction would encode the example, not the rule; and
mutual-only could fail Raman's own worked case under directional drishti). Fires 58/209
(28%) — honest arithmetic, accepted per the H2.C.41 preponderance class. Caveat: the
"health suffers" wording is signification-INFERRED (the printed lines support "fortunes
subject to much change" + defamation, not health verbatim).

**✅ SHIPPED WITH CAVEAT (review-corrected) — H1.C.37** (HTJAH-I:1146-1148, Lagnadhipati
strong but dispositor blemished): first encoding blemished on ALL of NATURAL_MALEFICS; the
reviewer flagged that the very precedent the docstring cited (B4 blemishless-Venus,
`_BLEMISH_MALEFICS`) EXCLUDES the Sun — the Sun blemishes only through combustion, which the
decisively-weak leg already carries. Corrected to Mars/Saturn/Rahu/Ketu touch + decisively-
weak dispositor. Fires 73/209 (35%, down from 37% — the Sun leg was precedent-inconsistent
surplus). Identity→False validated (a lord in own sign disposits itself; Raman's sentence is
about a DIFFERENT planet holding the lord's fate). Caveat: "blemished" is Raman-undefined at
this line; the encoding follows the project's settled register.

**Ratchet-blindness ledger:** H1 has the corpus's densest scored coverage (23 charts), so all
three shipped rules were GENUINELY ratchet-tested (6-9 scored firing charts each, no verdict
moved) — and N.38's regression was caught live. Snapshots regenerated twice (9 then 3,
verified evidence-only both times, zero verdict changes).


## H2 dead-rule sweep (2026-08-23) — pass 4: 5 shipped, 1 held-by-parity-proof, 12 left — AND THE SWEEP'S FIRST ACCURACY GAIN

Fourth house pass (H2's remaining 18 after C.41). **Strict ratchet 259/293 → 260/293** —
the first exact-accuracy gain since the ceiling was measured, earned by a dead rule whose
TODO went stale, and banked only after the reviewer's arithmetic proved it legitimate.

**Correctly left (12):** C.33/34 (navamsa-dispositor chain), C.35 (blocked by the SETTLED
"no per-component Shadbala minima exist" finding — "having Kalabala" has no bar), C.11
(absence-as-trigger, the N.66-note default-state concern), C.13 ("all good" vague), C.15
(encodable, deferred effort-vs-value), C.31 (multi-gate, deferred), C.42/C.43 (still gated
on the C.41 corpus-machine follow-up, per that entry's own condition), C.45 (deferred),
C.67 (routing note — already covered by H2.L.1-12), C.68 (vague composite outcome).

**✅ SHIPPED — the modality triplet H2.C.36/37/38** (HTJAH-I:2492-2496): 3rd lord in the 3rd
aspected by Jupiter/Venus, with the 3rd common/fixed/movable → wealth by thousands/hundreds/
within-two-hundred. The "SignModality" TODO was trivially computable all along. Reviewer:
VALIDATED×3, HIGH — source read verbatim, "its lord is situated there" = lord in the 3rd
confirmed, modality attaches to the house's sign, wealth routing explicit in the outcome
clause; Raman's own "naturally applies where movable signs ascend" remark is a consistency
note, correctly not encoded. Fires 0/1/0 of 209 (four-conjunct narrow rules, position-
dependent — NOT the lagna-fixed unsatisfiability class). The magnitude gradient survives
only in the fortified prose (RuleRecord carries no magnitude channel — framework limit).
Noted for a future precedent re-litigation: Jupiter/Venus-only for "benefics" is a corpus
precedent call; Raman names Mercury as a benefic 2nd-house resident two lines earlier.

**✅ SHIPPED WITH CAVEAT — H2.C.39** (HTJAH-I:2497, Saturn/Mars debilitated in the 11th
FROM ARUDHA LAGNA → good earnings): sign-from-AL confirmed verbatim; bhanga gate correctly
SKIPPED (debility is the TRIGGER of a benefic result here — a classical paradox rule — so
the guard that protects 'weak' readings points the wrong way; a bhanga'd planet satisfies
the rule more, not less). Fires 7/209, 2 scored charts, no verdict moved. **CAVEAT → NEW
AUDIT TICKET (arudha.py)**: Raman's own worked AL example (HTJAH-I:2518-2520, Aquarius
Lagna → Leo AL, kept in the 7th) does NOT apply the Jaimini same-sign/7th redirect that
`primitives/arudha.py:34-35` applies — for ~17% of charts (raw AL in 1st/7th) the code's AL
differs from Raman's. Per the Prime Directive (Raman wins) the primitive needs its own
review; C.39's fire-set is affected, C.40's provably is NOT (below).

**✅ SHIPPED — H2.C.40** (HTJAH-I:2498, AL in 11th/4th/5th/7th from Lagna → becomes rich):
**fixed golden chart_45 H2 wealth (mixed → favourable, Raman agrees) — strict 260/293, zero
new misses.** The 52% fire rate triggered full scrutiny and survived it: the reviewer
ENUMERATED the arithmetic — AL offset = 2·d mod 12 (d = lagna lord's offset) is ALWAYS
EVEN, so the attainable AL houses are {3,4,5,9,10,11} (after redirect), and Raman's four
named houses span exactly 3 of those 6 → ~50% is Raman's own arithmetic, the H12.C.F1
precedent class. Decisive robustness result: the fire-set is IDENTICAL under the code's
redirect convention and under Raman's own no-redirect construction (his set contains both
7 and 4, so the redirected case fires either way) — the chart_45 gain does not depend on
the open arudha.py question. Raman's own worked example is itself a C.40-firing chart.
Baseline bumped 259→260 in this change-set with the mechanism recorded in `_comment`.

**⛔ HELD BY PARITY PROOF — H2.C.46** (HTJAH-I:2535, AL in 6/8/12 → poverty): encoded and
reverted same day. The same enumeration proves it UNSATISFIABLE under BOTH conventions:
2·d mod 12 is always even; houses 6/8/12 sit at odd offsets and are unreachable. The
contradiction is INTERNAL TO THE SOURCE — Raman's poverty sentence cannot fire under his
own sign-based AL definition fourteen lines earlier (likely inherited from a tradition
computing Arudha differently, transcribed unreconciled). Per the H11.C.6 precedent, an
evaluable rule that cannot fire fakes coverage. Reverted to descriptive with the proof in
the rule text. C.40 does NOT revert with it — the pairing is superficial; the asymmetry is
arithmetic.

**Sweep protocol addendum (from the C.40/C.46 pair):** when a predicate is built on a
DERIVED point (Arudha, upagraha, sphuta), enumerate the derivation's reachable set first —
the same discipline as the lagna-fixed satisfiability check, one level up.


## H8-H3 dead-rule sweep finale (2026-08-23) — passes 5-12, closing the all-houses sweep

Final passes over the remaining eight houses (H8, H9, H10, H4, H5, H6, H7, H3 — 47 dead
rules). Full triage; six candidates encoded (verdicts below finalized after batch review).

**Correctly left, by blocking class:**
* Drekkana/D60/varga machinery absent: H8.C.21 (22nd drekkana), H8.C.22/C.27
  (navamsa-lagna-lord chains), H5.C.11 (drekkana dispositor), H4.C.47 (Gopura/shashtiamsa
  legs), H6.C.26 ("cruel Navamsha" 4-planet battle-death), H10.C.5/C.15 (navamsa-dispositor
  profession table, karakamsa overlay).
* Dasa-timing (Phase-F, no dasha context in EvalContext by design): H9.D.44/45/46,
  H10.C.60, H8.C.19-partial.
* Requires the FATHER'S chart (impossible from one nativity): H9.A.14, H9.A.16.
* Affliction-grade aggregates (no graded predicate): H8.C.4, H5.C.37.
* Deliberate dedups (refinements of already-scored placements, kept descriptive to avoid
  double-counting): H8.C.5, H8.C.6, H8.C.14, H4.C.3, H4.C.30, H5.C.8, H7.C.14 (promoted
  long ago into H7.C.86 branch (a)).
* Output-flavour / no verdict polarity: H8.C.20 (cause-by-planet table), H8.C.27 (place of
  death), H3.C.15/16/17 (co-born COUNT outputs — the whole of H3's remainder), H8.C.7
  (dual-polarity per-occupant flavour — does not fit one boolean; splitting would fork the
  rule id), H10.C.44 (ascetic counting), H9.A.10 (adoption, neutral), H9.A.12 ("beneficially
  disposed" vague), H4.C.24 (vague multi-clause), H4.C.26 ("strong 4th" house-strength gate),
  H7.C.81 (comparative-strength timing, the held D6 class), H10.C.27 (the 32-yoga royalty
  BANK — a yoga-file project, not one rule).
* **H7 deliberately untouched beyond the dedup note**: the marriage machinery is the
  project's densest-gated, most-scored surface with its backlog explicitly CLOSED; its
  remaining dead rules (C.5/C.8/C.31/C.35) include lagna-fixed blanket benefics (a benefic
  7th SIGN covers 7 of 12 lagnas → ~58% lagna-only fire) with real regression risk for no
  measured need. Recorded, not encoded.

**Encoded — all six SHIPPED (3 clean, 3 with caveats applied same-day):**

* **✅ H8.D.2** (HTJAH-II:3584, food-intake disease) — SHIP, exact three-conjunct
  transcription; the reviewer confirmed aspect-only on the Lagna leg is faithful ("aspected
  by", so a malefic IN the Lagna correctly does not fire). Fires 14/209. NH.chart_38's
  unpinned `death` manner moving insufficient-evidence → afflicted while its pinned
  `longevity` favourable stands is the established span-vs-manner dual reading.
* **✅ H10.C.56** (HTJAH-II:14214, Neechabhanga Rajayoga) — SHIP-WITH-CAVEAT. The
  broader-than-citation question was ruled FAITHFUL: the source introduces its list as
  "SOME important combinations" (non-exhaustive), `bhangas.py` anchors the 4-condition set
  as the standard doctrine Raman's method accepts, and a citation-trimmed fork would create
  two competing bhanga definitions in one engine. Caveat-fix applied: the separate
  `VargaDignity(D9,{exalt})` OR-branch was REMOVED as provably redundant (bhanga condition
  4 is the same test) — the docstring now states the unitary-doctrine reasoning instead of
  misdescribing the branch. Fires 80/209 (38%) — the doctrine's real breadth (any-of-7
  debil is ~40-50% of charts; Raman applies bhanga liberally in his own worked voice at
  14200), a weak testimony by construction; recorded for any future H10 re-weighing. Forms
  (1)/(4)/(5) of the citation remain unencoded (correct conservatism).
* **✅ H4.C.42** (HTJAH-I:4929, Vahana yoga) — SHIP, all three disjuncts parse-verified
  against the printed sentence; both identity→False guards ruled correct (Aquarius' Venus
  lords both 4 and 9 — "association of the lords" cannot be self-association; disjunct 3
  still covers those charts). Aquarius/Cancer → Venus-as-4th-lord derivations confirmed.
  Fires 22/209.
* **✅ H5.C.3** (HTJAH-I:5185, Jupiter as strong 5th lord) — SHIP-WITH-CAVEAT. Rasi core
  exact. Caveat-fix applied: the source's next sentence ("Birth of children is ALSO
  indicated when...") lists three INDEPENDENT combinations, not overlays — the rule text
  now says so explicitly, so a future encode makes them separate rules, never an And-gate
  here. Fires 0/209 (2/12-lagna × strength × aspect; satisfiable; liveness baseline
  consciously bumped 84→85).
* **✅ H6.C.1** (HTJAH-I:6073, evil 6th lord in 1/8/10) — SHIP-WITH-CAVEAT, and the caveat
  was decisive: the reviewer found Raman's own counter-citation for my `decisively_weak`
  arm — HTJAH-II:14229-14230, weak dusthana lords "if weak, produce Rajayoga" — weakness
  is classically FAVOURABLE for this signification. **The weak arm was DROPPED same-day**
  (fires 42→32/209); the surviving functional-malefic arm reads Raman's own per-lagna
  table (HTJAH-I:523-604) and is what keeps the rule from double-counting the ungated
  L.1/L.8/L.10 placements (double-count concern ruled adequately addressed — the gate is
  new testimony, not duplication). Weak arm re-addable only on explicit user ruling.
* **✅ H6.C.19** (HTJAH-I:6105, 6th lord in a benefic's sign → many friends) — SHIP;
  dispositor-∈-benefics is the standard "house of a benefic" reading; any-one-of
  Jupiter/Venus for "good planets" (plural) matches the corpus's loose class-plural usage.
  Fires 34/209.

Ratchet stable 260/293 · 283 · 10 through the whole finale; scored-house overlap
1/16/1/0/2/3 charts respectively — H10.C.56 was genuinely ratchet-tested on 16 scored
charts. 11 evidence snapshots regenerated (verdict changes: only the chart_38 dual-reading
above).

**THE ALL-HOUSES SWEEP IS COMPLETE.** Totals across all 12 houses: **19 rules shipped**
(H3.C.4; H2.C.41+36/37/38/39/40; H11.C.4/5; H12.C.C3/F1/F2; H1.N.58/66 + C.37; H8.D.2;
H10.C.56; H4.C.42; H5.C.3; H6.C.1/19 — counting the pair-corrected ships once), **6
held/reverted with a measured or proven reason** (H12.C.D6 tolerance-misuse; H11.C.6/7
naisargika-unsatisfiability; H1.N.38 chart_33 contradiction; H2.C.46 parity-proof; H6.C.1's
weak arm counter-citation), **1 golden chart fixed** (chart_45, strict 259→260 — the first
exact gain since the measured ceiling), **~78 dead rules correctly left** with their
blocking class named, and **3 standing audit tickets** (compound-relation exposure for
H11.C.6/7; arudha.py's Jaimini redirect vs Raman's worked example HTJAH-I:2518-2520; the
H2.C.41 corpus-machine verbatim check gating C.42/C.43).


## Cross-cutting: "ratchet unchanged" is NOT evidence of correctness (2026-08-22)

Three rules were encoded or attempted in one session; in **all three** the golden ratchet was
byte-identical, and in **none** did that silence carry evidential weight about correctness:

* `H3.C.4` — fired on 1 golden, corroborating an already-correct verdict. Ratchet blind
  because the rule never had to decide anything.
* `H12.C.D6` — fired on 27% of charts. Ratchet blind through **evidence redundancy**:
  `incarceration` sits in `_DUSTHANA_AFFLICTION_KEYS`, so any single fired malefic with no
  benefic contradiction already confirms "afflicted"; a badly-calibrated rule rides along
  invisibly. HELD on review.
* `H2.C.41` — fired on 14 charts. Ratchet blind through **coverage gap**: zero of those
  charts has a scored H2 expectation at all.

The ratchet is a strong guard against REGRESSION and remains sovereign for that purpose. It is
not, and was never designed as, a validator for newly-encoded rules. Any future dead-rule
encoding should measure (a) the firing rate, (b) whether any firing chart carries a scored
expectation for that house, and (c) co-fire against rules sharing a conjunct — before treating
a green ratchet as permission to ship.

## DRAFT golden pool fully adjudicated (2026-08-23) — 1 confirmed, 94 legitimate-mismatch backlog

All 95 remaining DRAFT verdicts were enumerated against the current engine. Exactly ONE is an
engine-match: **HTJAH-I.h5_15** (H5 children, favourable), reviewer CONFIRM/HIGH against
HTJAH-I:5906-5922 read verbatim (Chart No. 105: "5th house is unafflicted... fairly well
disposed"; the single infant death among ~9 counted / 8 born is a Navamsha-counting deduction in
Raman's own method, not an affliction verdict — the old "mixed" was exactly the over-weighting
the June backlog predicted). The engine's mixed→favourable movement pre-dates this adjudication
(D-7 confirm layer, PROGRESS_LOG "improves toward Raman's recorded verdict") — the engine moved
toward the text, not the label toward the engine. Ratchet: 260/293 → **261/294** exact,
283/293 → **284/294** within-1, real errors 10 (unchanged). The other 94 DRAFTs are the
legitimate mismatch backlog and stay DRAFT per the never-confirm-to-pad discipline; they are the
raw material for future mechanism work (the pillar-clause cluster chief among them), not for
label flips.

## Audit ticket DISCHARGED: H2.C.41 corpus-machine verbatim check → C.42/C.43 shipped (2026-08-23)

The H2 sweep's standing ticket (verify HTJAH-I:2526-2528 verbatim through the corpus machine
before encoding the gated siblings) was discharged after the corpus reconciliation made the
passage readable: all three poverty sentences read exactly as the rule prose claimed.
**H2.C.42** encoded as `Parivartana(1,6) AND (lord-1 OR lord-6 touched by primary maraka)` —
reviewer CONFIRM/HIGH (BPHS vol1 ch.42 v.3 corroborates; Raman's "either of these" broadens
BPHS's narrower attachment and Raman wins). Fires 1/211 (NH.chart_43). **H2.C.43** encoded as
`_MaleficNotOwning9or10InLagnaTouchedByMaraka` — reviewer REVISE→fixed same-day: the review
proved by enumeration that IF the counterpart node ever counted as a maraka, a node in the Lagna
would satisfy the maraka-touch qualifier on every chart (twin always in the 7th). The node-pair
guard was added as a **pinned invariant**; measurement then showed maraka.py already excludes
nodes from every tier (maraka.py:134), so the guard is defensive, not a live filter — fire rate
identical with and without (29/211, 4 scored-H2 overlaps, no verdict moved). Reviewer's two
side-questions settled: existential reading of "malefics" is correct (BPHS 42.8 generic plural);
nodes stay in the candidate-occupant set (the carve-out filters on ownership, and the house_11
node exclusion was a Shadbala-capability argument with no analogue here). Ratchet unchanged
261/294; liveness 739→741 evaluable, never-fired stays 85. H2's "left" count drops 12→10.

## Audit ticket DISCHARGED: arudha.py follows Raman, not the Jaimini 1st/7th redirect (2026-08-23)

Raman's own worked example (HTJAH-I:2521-2522: Aquarius Lagna, Saturn in Taurus → "the 4th from
Taurus, viz., Leo becomes Arudha Lagna") lands the AL in the **7th from Lagna and keeps it** —
strict Jaimini would redirect it to the 10th therefrom (Taurus), and `primitives/arudha.py` was
doing exactly that. The redirect was REMOVED: plain double-count, no exception, per the
definition sentence (HTJAH-I:2519-2521) and the Prime Directive (Raman wins). Consumer audit:
H2.C.39/C.40 verdict rules + report display only; the walled Jaimini subsystem does not consume
this primitive. Measured: Raman's example now reproduces (engine previously returned Taurus for
it); golden ratchet byte-identical (261/294, 284/294, 10); chart_45 still fires C.40. Parity
consequence recorded on C.40: the plain count reaches only ODD houses from Lagna, so of Raman's
four named houses {11,4,5,7} house 4 is now arithmetically unreachable (under the old redirect
it was house 7 — each formula kills exactly one). C.46's 6/8/12 unsatisfiability proof survives
under both formulas. Two tests that pinned the old exception were re-pinned to Raman's
arithmetic, including a new test reproducing the worked example verbatim.

**Review outcome (same day): VALIDATED/HIGH, with stronger evidence than dispatched.** The
reviewer found Raman keeps the plain count in FOUR independent passages covering BOTH exception
arms: the 7th-landing example above, the exception-free glossary definition (HTJAH-I:7187-7192,
generic per-house — the anchor for one formula across all 12 houses), Studies in Jaimini §19
(same definition + a second example), and decisively Studies in Jaimini **Ex. 48 (Hitler)**:
"lord of Lagna Sukra is in the 7th, and the 7th from the 7th, viz., Lagna itself will be Arudha
Lagna" — the SELF-landing case kept, where the exception would force Capricorn. So no flag is
needed for the walled Jaimini subsystem: Raman's own Jaimini book uses the plain count. The
exception's real home is **BPHS 29.4-5** (in-corpus, non-citable for natal verdicts), which on
Raman's own Aquarius configuration yields Taurus — exactly what the old code returned.

**Standing note before any Upapada-based verdict rule ships**: `upapada_lagna` has NO Raman
anchor (zero corpus hits in any Raman source — UL is defined only by BPHS ch.30 / KN Rao / Rath,
inside the ch.29 exception framework). Two open variants: (a) strict-classical UL would apply
the exception this fix removed; (b) Santhanam's BPHS 30.1-6 anchors UL to the 2nd house
("the bhava following the natal ascendant"), not the 12th the primitive uses (the Rao/Rath
reading). Today UL is display-only (special_points/synthesis); if a UL verdict rule is ever
proposed, resolve both variants through doctrine review first.

## Audit ticket DISCHARGED: compound_relation exposed, H11.C.6/C.7 re-encoded — both VALIDATED (2026-08-23)

The third and last standing ticket from the all-houses sweep. `dignity._compound_relation`
(naisargika x tatkalika via the standard ladder, previously private to Sthana Bala) is now
public as `dignity.compound_relation`, and the H11 pair whose naisargika encodings were proven
unsatisfiable over all 12 lagnas (2026-08-22) is re-encoded on it:

* **H11.C.6** = all three of the Lagna/2nd/11th lords pairwise MUTUALLY compound-friendly
  (identity pairs vacuous — Capricorn and Leo lagnas collapse to a two-planet test). Reviewer
  VALIDATED (MEDIUM-HIGH): mutual is the faithful reading of "the lords are friendly"; the one
  recorded LAXER variant — "friendly" = non-enemy both ways — is noted here per the review and
  re-opens only on new textual evidence. Fires 12/211, scored-H11 overlap on 2 goldens.
* **H11.C.7** = 2nd AND 11th lords each malefic-associated (conjunct/aspected, the codebase's
  standard "afflicted" floor) and compound-ENEMY one-way toward the Lagna lord, exactly as
  Raman's directional syntax reads ("inimical TO the Lagna lord"). Reviewer VALIDATED (HIGH):
  the neighbouring HTJAH-II:14367 sentence enumerates heavier weaknesses by name, proving bare
  "afflicted" here is the associational floor. Fires 17/211 with ZERO scored-H11 overlap —
  logged as a coverage-gap blindness mode per playbook rule 4: the ratchet cannot see this rule
  until a scored H11 chart fires it.

Satisfiability point for the record: the compound relation's temporal side is symmetric by
construction (whole-sign distances d and 14-d are in the friendly set together), so mutual
compound friendship needs only a friendly mutual placement plus no natural enmity — the
2026-08-22 unsatisfiability was purely a naisargika artifact, exactly as the hold note
predicted. Ratchet byte-identical (261/294, 284/294, 10); liveness 741→743, never-fired 85.
All three sweep audit tickets are now closed.

## H1-cluster mechanism design session (2026-08-23) — majority-loci affliction PROBED and REFUTED

The follow-up the threshold-sweep entry demanded: "a real improvement here needs a NEW mechanism
that separates these 8 charts from the strong-pillar charts the engine currently gets right."
A candidate was designed from the error charts' own printed reasoning and measured. It fails.
Recorded so the next session does not redesign it.

**The candidate (doctrine-anchored, not invented)**: per-locus CONTACT-affliction as an axis
separate from strength. Raman's own error-chart paragraphs weigh it exactly so — chart_60
(HTJAH-I:3802-3816): house (Mandi + Mars/Saturn aspects, Jupiter aspect "somewhat mitigates"
but "still the Bhava is not sufficiently strong") + lord (well-placed, D9-exalt, BUT Jupiter-
Ketu association + D9 Mars aspect) + karaka (good house BUT enemy sign + Sun + Saturn aspect)
→ "Though Jupiter is well-disposed... the Karaka and the third house are subject to affliction.
The native has no brothers." And h9_02 (HTJAH-II:7945-7985): "The Sun in exaltation with
Vargottama Jupiter... gave an exalted father — BUT the papakartari to the 9th house (from Rahu
and Mars), the 9th lord (from Saturn and Sun)..." — strength gave the QUALITY, contact gave the
VERDICT. Proposed clause: demote-only guard on the clause-2 FAVOUR lift when >=2 of the three
loci (bhava/lord/karaka) are contact-afflicted — the exact B1/navamsa-guard mold.

**The measurement (scratch probe, no engine change; all 294 confirmed Track-B verdicts)**:
four variants — {any-malefic-contact, hard-gates (>=2 distinct malefic contactors / papakartari
/ node-conjunction)} x {gross, net-of-benefic-contact}. NO variant separates:

| variant | threshold | errors caught (of 8) | correct favourables flagged |
|---|---|---|---|
| any-contact NET   | >=2 | 3 | 24 |
| any-contact GROSS | >=2 | 7 | 100 |
| any-contact GROSS | =3  | 3 | 38 |
| hard-gates NET    | >=2 | 0 | 9  |
| hard-gates GROSS  | >=2 | 1 | 31 |

The error charts sit at the SAME afflicted-loci counts as the correctly-favourable population —
the base-rate problem is structural, and it is the Measured-Truth mechanism operating inside
Raman's own corpus: malefic contact on a majority of loci is ordinary, therefore non-
differential. Raman's per-locus judgments in the very paragraphs above are finer than any
tally: WHICH malefic (functional nature), HOW (papakartari vs single aspect vs association),
mitigation weight ("somewhat mitigates" ≠ clears), D9 confirmation, enemy-sign placement,
Mandi/upagrahas (not modelled), and the Moon-reference check. His grading is the full reading,
not a countable proxy of it.

**Status: CLOSED-REFUTED** (same shape as the Tier-3 bhava-rescue: designed from citations,
killed by measurement — a success of the process). Together with the threshold sweep this
closes BOTH obvious mechanism families for the 10-error cluster. **Re-open path**: not a new
clause guess — systematic extraction of Raman's per-locus grading LANGUAGE from all worked
examples (the "sufficiently strong / not very good / quite afflicted" vocabulary) into a graded
per-locus dataset, then a mechanism designed against that dataset. That is golden-corpus work
(playbook rule 7), which is already the declared accuracy lever. Probe script preserved in the
session scratchpad; numbers above are the durable record.

## Workstream D DONE: parent-channel disclosure upgraded UNDER-POWERED → PURE-NOISE (2026-08-23)

The last deferred item from the real-people plan. The calibration table's H9_father/H4_mother
rows carried `*_died_early:UNDER-POWERED` (n=26/25) — a statement about the test, not the
engine — while the family data and the persona pilot both pointed at the father channel. The
legitimate route was taken end-to-end: (1) pre-registered mapping_version 3 in
`category_house_map.csv` (14 rows, 4 composite map_ids, supporting tier) using the childhood-
family tags as the powered proxy, with the SHARED-SOURCE confound (tags don't distinguish
parent — one measurement, two channels) and the prior ad-hoc null DISCLOSED in the registration
itself; (2) v2 results archived (`archive_mapping_v2/`); (3) full governed harness re-run —
sham gate PASSED, then H9_father AUC 0.511 (0.473-0.549) / H4_mother 0.506 (0.465-0.543) at
n=496 scored pairs: properly-powered NULL, replicating the ad-hoc result under sham-gated
governance; (4) failure atlas re-run → both channels classed PURE-NOISE at n≈570; calibration
table regenerated — rows now carry the powered class alongside the historical event rows, and
the reader-facing disclosure note upgrades automatically (`test_every_table_class_has_a_
reader_facing_note` green); (5) `update_baseline --confirm` → mapping_version 3, same 4 core
metrics (supporting tier never enters the ratchet), `test_astrobank_ratchet` green. FAILURE_
ATLAS.md carries the dated addendum. No verdict, threshold, or rule was touched — this is the
disclosure layer telling readers the truth at proper power, exactly what Workstream D was for.

## Golden corpus growth: the HTJAH extraction backlog, measured and opened (2026-08-23)

Prompted by the owner's question — "can't we increase the golden ratchet number, I think we
missed many examples." He was right, and the gap is now measured rather than estimated.

**The audit.** The two HTJAH volumes contain **502 worked-chart presentations** (a "Chart No. N"
followed by birth data); the golden corpus held **174** of them. That leaves **328 unextracted**,
and 136 "Conclusion" paragraphs — Raman's own graded judgments — sit on chart numbers the corpus
had never seen (81 in Vol I, 55 in Vol II). Corpus growth being the declared remaining accuracy
lever (playbook rule 7), this is the largest single piece of fidelity work still open.

**Why it was not simply automated before.** HTJAH prints birth DATA, not the printed longitudes
Notable Horoscopes gives, so records must be FRESH CAST out of OCR-damaged text. Observed
corruption in these very scans: `Born 24-3-7883` (mangled year), coordinates truncated by a line
break, `3/4-12-1953` (midnight-straddling date), unreadable zone markers. A mis-parsed birth line
produces a WRONG chart, and a wrong chart scored against Raman's verdict silently corrupts the
fidelity measurement.

**The gate that makes extraction safe.** Vol II prints, for most charts, *"Balance of <Lord> Dasa
at birth: N years, M months and D days"* — fixed by the Moon's longitude, therefore an independent
function of date, time and place. `tools/raman_saab/extract_htjah_goldens.py` parses the birth
line, casts, computes the Vimshottari balance, and emits ONLY when lord and duration reproduce
Raman's printed figure within tolerance. Worked proof: Chart No. 20 (HTJAH-II:2002) prints
"20 N 56, 75 E 55" and a Ketu balance of 6y 4m 4d; the parse lands the coordinates exactly and the
cast balance agrees to **3 days**. Failures are reported and skipped, never repaired by guesswork —
the 42 gate failures are scattered in magnitude (120d to 2289d) and direction, i.e. genuine OCR
damage rather than a systematic casting error.

**Batch 1 shipped: 57 charts.** Golden records 225 → 282. `expected_verdicts` deliberately EMPTY —
the tool extracts CHARTS; a verdict remains a doctrine judgment a reviewer makes by reading Raman,
and only CONFIRMED verdicts score. **The accuracy ratchet is therefore untouched at 261/294 by
construction**, which is the point: extraction can never inflate fidelity.

**The measured gain is liveness.** Dormant rules **85 → 71** — fourteen woke on the new nativities
(H11.C.22, H12.C.D5, H12.C.I5, H2.C.52, H2.C.63, H5.C.26, H5.C.29, H5.C.3, H6.C.16, H7.C.30,
H8.D.1, H8.K.28, H9.A.6, H9.B.27), plus one yoga (49 → 50). This is the empirical answer to "why
are rules dormant": for these fourteen it was CORPUS SIZE, not impossibility — including H5.C.3,
which the all-houses sweep shipped as a deliberate reviewer-validated dormant rule and which now
fires. It also retro-justifies that sweep decision: the honest hold was correct, and the corpus
caught up.

**What remains, in priority order.** (a) 105 charts parse cleanly but Vol I prints no dasha balance
to verify against — they need a different gate (Raman's stated Lagna sign, where the grid OCR
permits) before they can be trusted. (b) 118 fail to parse at all, dominated by line-break-truncated
longitudes and unreadable zone markers; a targeted OCR repair pass over the birth lines would
recover a large share. (c) The 57 shipped charts + the 136 known Conclusion paragraphs are now a
REVIEW queue: each verdict promoted DRAFT → CONFIRMED grows the ratchet's denominator honestly.
**That review is the only path that moves 261/294, and it must stay per-record against Raman's
text — never confirm to pad.**

## Raman's chart preparation vs a modern ephemeris — MEASURED (2026-08-23)

Raised by the owner mid-extraction: *"raman chart preparation is different from ephemeris."*
Correct, and it invalidated the gate the HTJAH extractor had been using. Now quantified.

**The instrument.** Two digitally-typeset PDFs of HTJAH Vol I and Vol II (Motilal, 12th ed.)
were supplied — real text layers, not the OCR'd scans in the vendored corpus. That made Raman's
PRINTED chart grids machine-readable for the first time: the planet names are text spans with
page coordinates and the grid rules are vector rectangles, so a South Indian 4x4 square can be
reconstructed geometrically and read cell by cell (`tools/raman_saab/htjah_grid.py`).

**Validation of the reading itself** (against Raman's prose, never the engine). Vol I Chart
No. 2 reconstructs to Lagna in Leo with Mercury, Jupiter and Mars; Sun and Ketu in Cancer; Venus
in Gemini; Saturn in Scorpio; Rahu in Capricorn. Raman writes of that chart: *"the combination
of Mars and Jupiter in the ascendant has produced a Raja yoga… Mars by himself is a yoga Karaka
as he is lord of the 4th and 9th."* From Leo, Mars (owning Aries and Scorpio) is lord of the 9th
and the 4th exactly. Both claims confirm the geometry independently.

**The finding, in two parts.**

1. **At SIGN level the modern cast reproduces Raman exactly.** For Chart No. 2, casting his
   printed birth line agrees with his printed grid on **8 of 8 grahas AND the Lagna**, under
   either plausible zone reading. This matters more than it sounds: the entire doctrine layer is
   whole-sign — drishti fires by sign membership, lordship is by sign, bhava is by sign — so the
   divergence does **not** reach the verdict logic. Fresh-cast golden records are sound as
   verdict inputs.

2. **Below sign level the Moon diverges, per chart, with no systematic bias.** Raman's printed
   Vimshottari balance implies a Moon longitude; comparing it against the cast Moon across
   **227 charts**: median **-0.010°**, mean **+0.161°**, stdev **1.248°**. 57% agree within 0.1°,
   68% within 0.25°, but **18% differ by more than a full degree**. A near-zero median across 227
   charts rules out an ayanamsa or ephemeris offset — there is nothing to calibrate. The scatter
   is per-chart: era table interpolation, rounded birth times, and occasional printed typos.

**Consequence — the dasha-balance gate was the wrong primary gate.** It was rejecting charts for
a Moon disagreement that is Raman-vs-modern-ephemeris noise rather than a parse error, which is
why it failed 74 of 108 gated PDF charts while the median |offset| was a hundredth of a degree.
It remains useful as a COARSE check (a wrong parse throws the balance by years, not months), but
the correct primary gate is **sign-level agreement with the printed grid** — which is also what
the golden schema always preferred: `printed_degree` / `sign_midpoint` positions are the primary
Track-B input and `fresh_cast` the fallback, and the corpus's strongest records already use
Raman's own printed figures.

**Where this leaves the extraction backlog.** The grid reader is committed EXPERIMENTAL: correct
where it locates a square, but it locates only 3 of 65 chart-bearing pages in the first 120,
because it refuses to extrapolate a missing rule (extrapolating shifts the cells and puts one
graha in two signs — a usable self-check, since that is astronomically impossible). Finishing it
is the highest-value next step on this thread: it would supply Raman's printed placements for
~600 charts across both volumes, gate them at sign level, and make the fresh-cast fallback
unnecessary. Until then the 57 already-ingested fresh-cast charts stand — they carry no verdicts,
so they cannot affect fidelity, and their sign-level placements are sound per finding (1).

## Golden corpus batch 2 (2026-08-23) — clean-edition harvest, dormancy 85 → 60 across the day

Owner directive: *"i want to increase the examples from raman sor books because it will give
engine more insights."* Two digitally-typeset PDFs (Vol I Motilal 12th ed., Vol II) were supplied
and harvested. What shipped, and what the evidence would not support:

**Shipped.** 60 further nativities, corpus **282 → 342** charts, deduped by BIRTH MOMENT rather
than chart number (the editions number differently, so the same nativity carries different
numbers in different sources — `existing_birth_keys`). Twelve DRAFT verdicts were added: 6 on new
records, 6 by enriching batch-1 records that had been extracted chart-only. DRAFT total 94 → 106.

**The gate was re-based from days to DEGREES**, and this was the substantive correction. The flat
30-day tolerance had been rejecting 74 of 108 gated charts, but the measurement showed why that
was wrong: the Raman-vs-modern Moon offset has median −0.010° and stdev 1.248°, so the rejections
were era table noise, not parse errors. Worse, a flat day limit is not scale-free — the same 1° of
Moon error surfaces as ~4 months inside a 6-year Sun dasha and ~1.5 years inside a 20-year Venus
one, so it silently applied a threshold three times stricter to Sun-dasha charts. The gate now
requires the dasha LORD to match (227/227 on Vol I — chance is 1 in 9) and the implied Moon
longitude to agree within **2.5°** (~2σ). Yield on Vol I alone: 209 of 227.

**Verdicts are read off Raman's own Conclusion paragraph** by the existing conservative
`classify_prose` lexicon, stored with the prose verbatim, and marked DRAFT — unscored, so
extraction still cannot inflate fidelity. House attribution comes from the running chapter
heading, with the observed OCR variants (`Twelth`, `Eleveath`, `Eieventh`, `Elevanth`) accepted;
a table-of-contents row is explicitly NOT a heading, a bug that had pinned Vol I's first charts to
the twelfth house. **H8 is deliberately given no verdict**: its primary key `longevity` is
deferred by LONGEVITY_GUARD, so a scored verdict there would measure the guard, not the doctrine.

**The measured gain is coverage.** Dormant rules **71 → 60** (11 more woke), yogas 50 → 52.
Cumulative across both batches today: corpus **225 → 342** charts, dormancy **85 → 60** — a 29%
cut in dead doctrine surface, bought purely by giving the rules more of Raman's own nativities.
**The verdict ratchet stayed at 261/294 throughout, by construction.**

**The honest ceiling, and it matters for planning.** Only 10 of the 60 new charts carry a
Conclusion paragraph at all. Both volumes hold 252 Conclusions between them, but ~240 attach to
charts the corpus ALREADY had — the original curation went after exactly the verdict-bearing
charts. **What remains unextracted is overwhelmingly chart-only material**: valuable for rule
liveness and astronomy coverage, but it cannot yield verdicts, and therefore cannot move
261/294. Further HTJAH harvesting should be costed on that basis.

**Where the remaining verdict-bearing material actually is** (measured over the vendored library):
Notable Horoscopes carries **868 printed degrees** across 71 birth lines in the prose-positions
format the corpus prefers and that `extract_nh_goldens.py` already handles — 60 records extracted
so far. The Astrological Magazine v75 (~50k lines, 489 printed degrees, 54 birth lines) is
essentially untouched. Either is a better next seam than more HTJAH grid work.

## Verdict-merge pass + Notable Horoscopes exhausted (2026-08-23) — DRAFT verdicts 106 → 136

Follow-up to batch 2, chasing the seam the batch-2 entry identified. Two findings.

**A block-boundary bug was suppressing 92% of the available verdicts.** Chart discussions were
bounded at the next MENTION of a chart number, but Raman cross-references charts constantly in
his prose ("...as in Chart No. 44"). Vol I has 754 mentions against only 364 real presentations,
and **270 of those 364 were being truncated before their Conclusion paragraph** — precisely where
the verdict lives. Bounding blocks at the next PRESENTATION instead (a chart number with "Born"
within three lines) took Conclusions captured from **10 to 130**, and available house-verdicts
from 37 to 63.

**Raman re-presents the same nativity across chapters** — up to ten times, 111 of 180 nativities
more than once — each time concluding on THAT chapter's house. Deduplicating by birth moment was
discarding those extra judgments. `merge_by_nativity` + `merged_verdicts` now group presentations
and collect one verdict per house; where two presentations disagree on a house the first is kept
and the collision recorded rather than averaged, because a disagreement is a reviewer's call.
Result: **26 existing records gained a DRAFT house-verdict (+26)**. Existing verdicts are never
overwritten — CONFIRMED ones are the ratchet's own ground truth.

**Notable Horoscopes is now exhausted as a chart source**: of its 74 parseable charts, 70 were
already goldens and the last 4 were ingested. NH remains the corpus's strongest material — its
records carry Raman's OWN printed longitudes (`position_source=printed_degree`, 224 verdicts
across 64 records, averaging 3.5 houses each), immune to the birth-data reconstruction HTJAH
records need. It simply has no more charts to give.

**Totals for the day.** Corpus **225 → 346** charts. DRAFT verdicts **94 → 136**. Dormant rules
**85 → 58** (a 32% cut in dead doctrine surface), yogas firing 49 → 52. **The verdict ratchet
never moved: 261/294 exact, 284/294 within-1, 10 inversions** — every batch carries DRAFT
verdicts only, and DRAFTs are unscored by construction.

**What is left, ranked.** (a) The 136 DRAFT verdicts are a review queue; promoting them per-record
against Raman's text is the only thing that moves 261/294, and it must stay per-record — never
confirm to pad. (b) The Astrological Magazine v75 is the last substantial untouched seam (~50k
lines, 489 printed degrees, 54 birth lines) and would need its own extractor. (c) HTJAH's
remaining unextracted charts are overwhelmingly chart-only and cannot yield verdicts.

## ★ AUDIT + CONFIRMATION-RULE AMENDMENT (2026-08-23) — the ratchet falls 88.8% → 85.9%, on purpose

A deep audit of the day's corpus work, prompted by the owner ("this is swaying a lot"). It found
one real bug of mine, one structural flaw in the project's own playbook, and it changed the
headline number for the first time in a downward direction. Binding record.

### The bug I introduced, and its blast radius

Batch 1 deduplicated by CHART NUMBER instead of by BIRTH MOMENT. The printings number charts
differently, so this leaked **19 duplicate records** (~14 nativities). The follow-up
"merge verdicts across presentations" pass then wrote the same DRAFT verdict onto every copy:
**14 duplicated matters, nine of which CONTRADICTED an already-CONFIRMED verdict** for that same
matter with a different ordinal (e.g. HTJAH-II.h9_11 CONFIRMED H9/father *favourable* vs my
x95/x99/h11_07 DRAFT *mixed*).

Nothing scored — DRAFTs are skipped — so **261/294 was never corrupted**, verified by direct
check: zero (nativity, house, signification) pairs carried two CONFIRMED verdicts. But confirming
those rows later would have counted one Raman judgment up to four times in one accuracy figure.
Repaired: 9 draft-shadows-confirmed dropped, 5 draft-only duplicates collapsed to a canonical
copy (the human-curated non-`.x` record wins). Duplicate records are KEPT as charts — they earned
real liveness coverage — only the duplicated verdicts were removed.
**Guard: `tests/raman_saab/test_golden_verdict_uniqueness.py` makes this unrepresentable.**

### The structural flaw: playbook rule 7 was a one-way gate

The rule said *"confirm engine-matches from DRAFTs (never confirm mismatches to pad)"*. The
parenthesis was right; the main clause was not. Under it a DRAFT could enter the scored pool ONLY
by agreeing with the engine — so the ratchet could climb and never fall, and genuine Raman
conclusions the engine gets WRONG stayed parked in DRAFT forever, invisible to the number. This
session demonstrated the mechanism live: h5_15 was confirmed in the morning after *searching the
DRAFTs for engine matches*. Legitimate per record, selection-on-agreement in aggregate.

Three pools measured, which is what exposed it: CONFIRMED **88.8%** exact; drafts parked *because*
the engine disagreed **1.3%**; drafts extracted **blind to the engine 29.6%**.

**AMENDED, user-signed (CLAUDE.md playbook rule 7): confirm whatever Raman actually CONCLUDED,
regardless of engine agreement. A confirmed miss is worth exactly as much as a confirmed hit.
Never confirm to pad; never withhold to protect the number.**

### The confirmable unit: CONCLUSION, never OBSERVATION

The distinction that makes the amendment safe. *"The native lost his mother very early"* is a
conclusion. *"The Lagna is weak, being occupied by debilitated Mars"* is a factor Raman is still
weighing — confirming it as a house verdict blames the engine for disagreeing with something that
was never a verdict. Measured: draft rows whose prose is factor-like score **0.0% exact**
(n=25) versus outcome-like at **30.0%** (n=20) — the factor rows are bad labels, not engine misses.

### First adjudication batch, engine-blind

A `bphs-doctrine-reviewer` read 16 sampled drafts against the printed text with the engine's
verdict explicitly excluded from its reasoning. Result: **11 CONFIRM, 3 REVISE (ordinal wrong),
2 REJECT** — 14/16 salvageable, a ~31% defect rate on the label. Twelve were applied (one ordinal
revised first: HTJAH-I.x71 H4 afflicted→**mixed**, because Raman credits the 4th house's strength
for the mother living to the native's 36th year and the karaka for her death — two-sided).
Rejected: HTJAH-I.x79 (wrong signification — Goethe's row is about *education*, not mother) and
NH.chart_13 (prose spliced across a footnote, inverting Raman: the Lagna is Vargottama and
**unafflicted**). Six of the confirmations are **real engine misses** the old rule excluded by
construction: Roosevelt's career NH:10155, the Gaekwar's children NH:8352, Bose's speech NH:7628,
plus the H7 pair HTJAH-II:1818/1864.

**Ratchet: 261/294 (88.8%) → 263/306 (85.9%) exact; 284/294 → 291/306 within-1; inversions
10 → 15.** +12 denominator, +2 numerator. Nothing regressed in the engine.

### Two systematic extractor defects, fixed with tests

1. **Signification mislabelling.** `house_from_chapter` blanket-mapped a house to its primary
   matter, but a Raman chapter can judge two: HTJAH-I ch.4 covers the mother AND education.
   Now `_signification_for` picks from the prose (`_SIG_HINTS`), and the chosen key is always one
   the house owns.
2. **Ordinal read off the factor clause.** Raman states factors first and the outcome last
   ("...but the lord and Karaka are afflicted. **Hence the native lost his mother very early**").
   `outcome_clause` now feeds only the outcome to the classifier. Re-running over stored drafts
   corrected 6 fields — four became `insufficient-evidence`, i.e. the fix is more conservative,
   refusing where a factor clause had been driving a spurious verdict.

Also found (pre-existing, not from today): **11 DRAFT rows name a signification that does not
exist** — NH extractor compound labels like `wealth/speech`, `death/maraka`, `self/body`. None are
CONFIRMED, so none are scored, but confirming one would silently score against nothing. Ratcheted
at 11, may only shrink; which matter Raman judged is for the reviewer reading the prose.

### What this means for the number, going forward

Only **12 of the 121-row DRAFT queue** are adjudicated. At the sampled defect and agreement rates
the honest figure lands near **70-75% exact on a ~380-verdict denominator**. **Expect it to keep
falling as review proceeds, and do not treat that as regression** — it is the same standard
already applied when real-outcome generalization was reported NULL rather than buried. The two
axes stay reported side by side, and neither is ever averaged with the other.

### Negative result: automated conclusion-vs-observation triage does NOT work (2026-08-23)

Before committing reviewer time to the remaining 109 DRAFT rows, the obvious cost-saver was
tested: use the `outcome_clause` marker set (hence / thus / the native / this gave / …) to triage
rows into "usable conclusion" vs "factor observation" mechanically, and only send the usable ones
to review. It was validated against the 14 rows an engine-blind reviewer had already adjudicated.

**It agreed with the reviewer on 3 of 14.** It rejected genuine conclusions wholesale, because
Raman states most outcomes as bare fact with no discourse marker at all — *"the Gaekwar was very
unfortunate in regard to his children as most of them died during his life-time"* carries no
"hence", and is unambiguously a conclusion. Marker presence simply does not track the distinction.

**Consequence: there is no cheap path. The distinction requires reading, per row.** The full queue
was therefore split into four disjoint slices and sent to four parallel `bphs-doctrine-reviewer`
agents under the engine-blind protocol. Do not re-attempt heuristic triage without new evidence;
this is the recorded refutation.

Note the narrower claim that survives: `outcome_clause` is still correct for what it actually does
in the extractor — choosing WHICH clause of a paragraph to hand the classifier once you already
know the paragraph is a conclusion. It is a clause selector, not a conclusion detector.

## ★★ FULL ADJUDICATION (2026-08-23) — the honest fidelity figure is 269/381 = 70.6%

The complete DRAFT queue, reviewed. This supersedes every earlier fidelity number in this file.

**Method.** All 94 adjudicable DRAFT rows were split into four disjoint slices and sent to four
parallel `bphs-doctrine-reviewer` agents. Each judged **blind to the engine** — engine verdicts
were deliberately withheld from the prompts — against the single question: *is this Raman's
CONCLUSION about the matter, or an OBSERVATION about one contributing factor?* Reviewers verified
every row in the printed source and returned a decisive quote with a line number.

**Outcome: 59 CONFIRM, 17 REVISE, 18 REJECT.** The 17 revisions corrected an ordinal, a
signification, or both, before confirming. Reject rate 19%.

**The figure: 263/306 → `269/381 = 70.6% exact`, `329/381 = 86.4% within-1`, `52 real errors`.**
Cumulative from the day's start: 261/294 = 88.8% → 70.6%. **Not one line of judge or doctrine
code changed.** The engine is exactly what it was this morning; the measurement stopped being
one-sided.

**What the rejects were** (these stay DRAFT, unscored, and must never be confirmed):
observations about a single factor mid-analysis ("the Lagna is weak, being occupied by
debilitated Mars"), and prose corrupted by splices. Three splice classes were found and are worth
fixing in the extractor: a **footnote splice** that inverted polarity (NH.chart_5 — the real text
says the Lagna is *unafflicted*), a **section-heading splice** that swallowed the next section's
title and drove the signification off it (HTJAH-I.x75 took "Education and Learning" while the
conclusion judged the mother), and a **two-passage splice** that dropped Raman's own hedge
(NH.chart_41 H10 omitted "Of course this is a general statement and may have exceptions").

**One row HELD, and the rule it establishes.** NH.chart_38 H9 was graded `afflicted` by one
reviewer and `mixed` by another, both reasoned. **A contested label never enters the scored
pool** — reviewer disagreement is evidence the label is genuinely contestable, and confirming it
would inject adjudication noise into the accuracy figure. Held unscored until resolved.

### The real error surface — 52 rows, and the old diagnosis does not describe it

| kind | n |
|---|---|
| engine favourable, Raman afflicted | 26 |
| engine afflicted, Raman favourable | 16 |
| **engine ABSTAINS** (insufficient-evidence, scored distance 2 by convention) | 9 |
| mixed-vs-abstain | 1 |

By house: H5 **9**, H4 **7**, H1/H2/H10 **6** each, H7/H9 5, H3 2, H8 3, H6/H11/H12 1.

**The standing "10 dist-2 errors are ONE mechanism (the pillar clause) at a proven local
optimum" finding is now STALE** — it characterised the selected pool. It has not been re-derived
against these 52 and must not be assumed to generalise. The nine ABSTENTIONS are a different
failure mode entirely (the engine declining to judge where Raman concluded), and they were
invisible while the pool only contained rows the engine had already graded. Any future mechanism
work starts by re-profiling these 52.

**What did NOT change, and is worth stating plainly.** The doctrine layer, the 847 cited rules,
the whole-sign conventions, and every reviewer-validated fix shipped today stand untouched. The
engine remains the most faithful encoding of Raman's system this project can build; we simply now
know what its fidelity actually is when measured without a thumb on the scale. Both axes remain
reported side by side: textbook fidelity **70.6% exact / 86.4% within-1**, real-outcome
generalization **NULL**.

## Re-profile of the 52 real errors (2026-08-23) — the one-mechanism diagnosis is REFUTED

Required by the full-adjudication entry above: the old finding ("the 10 remaining dist-2 errors
are ONE mechanism — the pillar-preponderance clause — at a proven local optimum") described the
selected pool and had to be re-derived against the true 52-row error surface. It does not survive.

### Where the errors actually come from

| origin in `_decide` | n |
|---|---|
| **clause 3** — Track-B fallback, NO pillars available, decided on rule polarity alone | **17** |
| **clause 2** — the pillar-preponderance contradiction (the old diagnosis) | **14** |
| clauses 4-8 — pillars known, no benefic/malefic contradiction | 12 |
| **abstention** — no polarised rule fired at all; engine returns insufficient-evidence | **9** |

**The pillar clause accounts for 14 of 52 (27%), not all of them.** The largest single bucket is
charts where the engine has *no strength information whatsoever*. Any future mechanism work must
start here, not from the superseded claim.

### The abstentions are a coverage gap, not a misjudgment

All nine are NH charts, and on every one **no benefic rule and no malefic rule fired** for that
matter (eight had only neutral-polarity rules fire; one had nothing). The engine is not grading
wrongly — it is silent, which clause 7 explicitly permits ("silence is a legitimate answer").
Two things were ruled out by measurement before concluding this:
- **Not a Shadbala-evaluability problem.** All 743 evaluable rules evaluate cleanly on a sparse NH
  chart, zero exceptions, firing 67 vs 70 on a comparable fresh-cast chart.
- **Not a routing bug.** 21 H4 rules carry `signification="mother_home"`, which is not an H4
  key — this looked like a defect and is NOT one: significations route by `Signification.rule_tags`,
  and `mother_home` is a deliberate bridge tag listed in mother/happiness/education/vehicles.
  Recorded so the next reader does not re-raise it.

The scoring convention counts an abstention as distance 2 ("a real miss, not a near-hit",
`_ordinal_distance`). That is deliberate and unchanged, but it means **9 of the 52 "real errors"
are silences rather than inversions** — a materially different failure, and it should be reported
as such rather than folded into the inversion count.

### Fidelity stratified by data completeness — report this, do not hide it

| corpus stratum | n | exact | within-1 | dist-2 |
|---|---|---|---|---|
| **full cast** (birth data → Shadbala available) | 283 | **76.3%** | 90.8% | 26 |
| **sparse** (Raman's printed positions, no birth time → no Shadbala) | 98 | **54.1%** | 73.5% | 26 |
| **COMBINED — the headline figure** | **381** | **70.6%** | **86.4%** | **52** |

Sparse charts are a quarter of the corpus but carry half the errors — roughly three times the
error rate. This is a structural handicap, not a doctrinal one: without a birth time there is no
Shadbala, so the three-pillar machinery cannot run and `_decide` falls through to clause 3, which
weighs rule polarity alone.

**The combined 70.6% remains THE number to quote.** The strata are published because they say
where the error concentrates and what would actually move it — NOT so that the flattering half can
be reported on its own. Quoting 76.3% without its denominator would repeat, in a new form, exactly
the selection problem this whole audit existed to remove.

### What this makes actionable, in order

1. **Clause 3 is the biggest lever (17 errors).** The Track-B fallback decides on rule polarity
   with no strength input at all. Raman himself judges these same book charts without computing
   Shadbala, so there is doctrine to encode here — his qualitative strength assessment (dignity,
   placement, aspect) is available on a sparse chart even when Shadbala is not.
2. **The 9 abstentions are a coverage question**, answerable per chart: which of Raman's stated
   factors produced his conclusion, and is that factor encoded as a polarised rule at all?
3. **The 14 pillar-clause errors** are the only part the old sweep table still describes, and its
   "proven local optimum" conclusion stands for them alone.

## Sparse-chart strength: positional dignity encoded, three arms REFUTED on review (2026-08-23)

First fix aimed at the re-profiled error surface. Target: clause 3, the Track-B fallback, which
was 17 of the 52 errors — the engine judging Raman's own printed book charts with the dignity
evidence thrown away.

**The gap.** `_strong()` read strength from Shadbala, which a `from_stated_positions` chart does
not have, so it returned None, both pillars were unknown, and `_decide` fell to clause 3 (rule
polarity alone). But Raman judges these very charts without Shadbala: "Considerations in Judging
a House" lists eight factors, none of which need it, and factor 5 is categorical — *"The
exaltations and debilitations of the house lords are equally important"* (HTJAH-I:474) — with the
consequence stated at HTJAH-I:497: *"If the strength of the lord is full or complete there will
be in general a good influence on the house."*

**Shipped (`_qualitative_strong`, used only when `shadbala_rupas is None`):** exalt / moolatrikona
/ own → strong; uncancelled debilitation → weak; **everything else → None**, still abstaining.

**Three arms were written and removed on review, each refuted by Raman working a chart the
opposite way.** Recorded so they are not re-proposed:

| proposed arm | refuted by |
|---|---|
| dusthana location → weak | HTJAH-I:2150 — a lagna lord **in the 12th**: "Lagnadhipati **gets strength** because he is aspected by Saturn, a Yoga Karaka" |
| friend + kendra → strong | HTJAH-I:2202 — "**moderate** in strength, because, though in a friendly sign, is in conjunction with Mars and Saturn" |
| enemy → weak (the symmetric temptation) | HTJAH-I:1948 — "in an **inimical sign** but since this happens to be a Kendra he **becomes strong**"; HTJAH-I:10402 makes an inimical sign a graded one-third deduction with exemptions, never a class |

Two further review corrections: the dusthana arm had **already** been rejected for these same
pillar semantics by `_lord_hard_afflicted`, and the first draft neither cited nor rebutted that
ruling. And the original rationale for excluding aspects was wrong — "plays no mean part"
(HTJAH-I:499) is litotes, and Raman directs the reader to "blend all the influences carefully"
(HTJAH-I:1497). The correct reason is non-double-counting: aspects already reach `_decide` via
`fired_benefic`/`fired_malefic`. Two citation line numbers were wrong (:493→:497, :472→:474) and
are fixed; `sources.passage` backs click-to-source, so a wrong number ships a wrong quote.

**Measured: NET ZERO.** 269/381 exact and 52 dist-2, unchanged; abstentions 9 → 8. The +2 exact /
−1 inversion the first draft measured was attributable to the two refuted arms — a clean
demonstration that a corpus gain is not evidence of fidelity. **Shipped anyway, deliberately**:
the justification is HTJAH-I:474 + :497 alone, and it stands at net zero. Net-negative would have
meant holding it and recording the number.

**Anchor `self_test.aries_jupiter_h1` re-pinned mixed → favourable.** Not a doctrine claim by
construction; its `mixed` recorded the old blindness (no pillars known, clause 2 could not run).
Reviewer-confirmed. The behavioural contract test `test_track_b_decides_on_polarity` needed NO
change and still passes — its chart has no categorical dignity — and two boundary tests now pin
the refuted arms so they cannot return by accident.

### Three tickets opened by this review, none acted on yet

1. **Clause 2 is one-way on sparse charts.** `_bhava_bala_for` returns None without
   `bhava_madhyas`, so a sparse chart has at most TWO knowable pillars, while
   `CONTRA_PILLAR_AFFLICT = 3` and `CONTRA_PILLAR_FAVOUR = 2`. The afflicted arm is
   **unreachable** while the favourable arm needs only both pillars, and the B1 guard is inert
   there too. Raman calls exaltation and debilitation "equally important"; an engine that can
   promote but never demote contradicts that. Proposed: `weak >= min(CONTRA_PILLAR_AFFLICT,
   len(known))` — a no-op when all three pillars are known. Needs its own measurement and review.
2. **BHAVA-RESCUE is structurally dead on Track-B.** HTJAH-I:503-505 is gated on
   `bhava_bala_strong is True`, always False without bhava madhyas — so the "badly placed →
   afflicted" half can fire where its rescue half cannot. The adjacent `bhava_ok` already treats
   None as permissive; this gate does not.
3. **★ The better-cited lever: combustion is discarded on every sparse chart.**
   `from_stated_positions` never populates `combust_fraction`, so it is silently 0.0 — though
   `combustion.combust_fraction` needs only the Sun's and the planet's longitude, both of which
   printed positions supply. HTJAH-I:3788 — *"the ruler of the third becoming combust and hence
   powerless"*, this project's strongest lord-weakness citation and the basis of the B1 guard —
   **is itself a printed book chart**. Take this next.

## Combustion on book charts — the data was never computed (2026-08-24)

Ticket 3 from the sparse-strength review, and the best-cited of the three. **Closed.**

**The defect.** `RamanChart.from_stated_positions` never ran a combustion pass, so
`combust_fraction` sat at its `0.0` default on every printed book chart — the engine read every
graha on every such chart as un-combust. The fresh-cast path (`chart/adapter.py`) has always run
that pass. Nothing about combustion needs a birth time: `combustion.combust_fraction` reads the
Sun's longitude and the planet's, both of which a printed chart supplies.

**Why it mattered more than an ordinary data gap.** Combustion is a factor Raman applies
CATEGORICALLY, and he applies it on exactly these charts. HTJAH-I:3780, **Chart No. 59**, of the
third lord: *"in the Rashi he is with an inimical planet Sun and has become combust. This makes
him weak in the chart."* That passage (at :3788) is the citation the **B1 dominant-factor guard**
is built on. So the engine held a rule derived from a printed book chart that it could not apply
to printed book charts.

**Two fixes, both closing that circle:**
1. `from_stated_positions` now runs the same combustion pass as the adapter. Result: **24 of 32**
   sparse golden charts carry at least one combust graha, where previously all were silently 0.0.
2. `_lord_hard_afflicted` no longer early-returns on `shadbala_rupas is None`. It reads
   `es.combust` and `es.debilitated_uncancelled`, neither of which needs Shadbala — only
   `rupas`/`band` do, and it reads neither. Result: B1 now reports on **18 of 98** sparse rows,
   where it previously returned None on all 98.

**Measured: NET ZERO again.** 269/381 exact, 52 dist-2, unchanged (abstentions 9 → 8 from the
dignity fallback in the preceding entry). The 18 rows where B1 now fires did not reach the
clause-2 favourable-lift branch it gates, so no verdict moved on this corpus. The ledger is
nonetheless correct where it was previously blank, and that ledger is surfaced to readers.

**Shipped on the same standard as the preceding entry:** the justification is HTJAH-I:3780 plus
the plain fact that the value was computable and discarded. A correctness fix that measures net
zero is still a correctness fix; net-NEGATIVE would have meant holding it.

**Contract test updated, with its sound half preserved.**
`test_b1_dominant_factor.py::test_track_b_chart_returns_none` asserted "No Shadbala -> no
judgement, rather than a default that would deny the matter". Its own fixture put Mercury 2° from
the Sun — genuinely combust — so returning None was not withholding judgement but discarding a
stated fact. It is now three tests: a combust book-chart lord reports True, an uncombust one
reports False (reporting must not mean flagging), and a graha ABSENT from the chart still returns
None — the sound half of the old contract, kept.

### Still open from that review

- **Clause 2 is one-way on sparse charts** (afflicted arm unreachable at two knowable pillars,
  `CONTRA_PILLAR_AFFLICT = 3`). Now more pointed than when filed: B1 fires on 18 sparse rows but
  gates only the favourable lift, so the demotion path it feeds is the one that cannot be
  reached. Proposed `weak >= min(CONTRA_PILLAR_AFFLICT, len(known))` — a no-op with all three
  pillars known. Needs its own measurement and review.
- **BHAVA-RESCUE is structurally dead on Track-B** (`bhava_bala_strong is True` never holds
  without bhava madhyas, while the adjacent `bhava_ok` already treats None as permissive).

## Two HOLDS on the sparse-chart thread (2026-08-24) — both would have been inventions

Continuing the error re-profile. Both remaining candidate fixes were measured, and both are held.
Recording the evidence so neither is re-proposed on intuition.

### HOLD 1 — the clause-2 symmetry fix is UNSATISFIABLE on this corpus

The review filed it as a real asymmetry, and it is one: a sparse chart has at most two knowable
pillars while `CONTRA_PILLAR_AFFLICT = 3`, so the afflicted arm cannot be reached while the
favourable arm (threshold 2) can. Raman calls exaltation and debilitation "equally important",
so an engine that can promote but never demote does contradict him. Proposed fix:
`weak >= min(CONTRA_PILLAR_AFFLICT, len(known))`.

**Measured before encoding, and it could never fire.** Across all 98 sparse scored rows:

| knowable pillars | rows |
|---|---|
| 0 | 63 |
| 1 | 29 |
| 2 | 6 |

and rows carrying **≥1 weak pillar: 1. Rows carrying ≥2 weak pillars: 0.** No sparse row reaching
clause 2 has a single weak pillar. Shipping the fix would add an unexercised code path for zero
measured effect — the H11.C.6/C.7 precedent (an evaluable rule that cannot fire fakes coverage)
applies directly. **Held.** Re-open if the weak side ever becomes populated — which requires
HOLD 2 to change, and it should not.

### HOLD 2 — neecha_bhanga cancels 83% of debilitations, and that is NOT a defect

Chasing why the weak side is empty: `_qualitative_strong` returns True 51 times and False 3
times across every graha on sparse charts. The cause is upstream — of 18 debilitated grahas,
**15 are cancelled by `neecha_bhanga`**. The rate is 83% on sparse charts and **83% on full-cast
charts too (85 of 103)**, so it is a global property, not a sparse artifact.

83% looked far too high: Neecha Bhanga Raja Yoga is classically a notable condition, and the
implementation ORs four conditions of which two accept a kendra **from Lagna OR from Moon** —
up to eight of twelve houses, tested against two different planets. Cancellation is close to the
default by construction. The module docstring also concedes the conditions are imported
Parashari/Phaladeepika doctrine, since "Raman references neecha-bhanga at HPA-33:308 but does not
enumerate the conditions".

**Then I read what Raman actually does, and he cancels freely.** HTJAH-I:1822: *"The Sun, lord of
11, is in Lagna in neecha or debility. Because the Sun gets neechabhanga or cancellation of
debility, Raja-Yoga is caused."* Fourteen lines later, in the SAME chart: *"Lord of Lagna Venus is
in the 12th in debilitation but there is cancellation of debility. Venus is with exalted Mercury
and hence good."* Two cancellations in one nativity — and the reason given for the second,
conjunction with an EXALTED planet, is not even among the four implemented conditions, i.e.
Raman's working set is *wider* than the engine's, not narrower. Again at HTJAH-I:1984 for a third
chart.

**So there is no doctrinal basis to tighten it, and tightening would be my invention.** This is
the same shape as the dusthana arm refuted hours earlier: a plausible-sounding structural
intuition ("that fires too often") with Raman's own text running the other way. **Held.**
Re-open only on a citation where Raman DECLINES a cancellation the engine grants.

### What these two holds establish about the sparse-chart error surface

The 26 dist-2 errors on sparse charts are **not** reachable by threshold or cancellation work.
The weak side of the pillar reading is structurally near-empty because Raman himself rarely
lets a debilitation stand, and the corpus bears that out. Anything that moves these rows has to
come from somewhere else — most plausibly a genuine three-valued strength band ("moderate in
strength" recurs at HTJAH-I:1868, :2198, :2202), which an `Optional[bool]` pillar cannot express
and which is a design change with its own doctrine review, not a threshold tweak.

## The pillar-threshold sweep, RE-DERIVED on the corrected corpus (2026-08-24)

The old sweep table was marked STALE by the full adjudication, with the instruction to re-derive
before acting on it. Done. Also profiled the 26 errors on charts that have COMPLETE data — the
ones where the engine misjudges with everything available, and therefore the purest signal.

### The 26 full-cast errors

| origin | n |
|---|---|
| clause 2 — pillar-preponderance contradiction | 14 |
| clauses 4-8 — only one polarity fired | 12 |

Direction: **15 favourable where Raman says afflicted**, 10 the reverse, 1 abstain-vs-graded.
By house: H1 6, H2 5, H5 5, H4 3, H9 2, then singletons. Concentration in H1/H2/H5 is unchanged
from the old profile.

**This partly rehabilitates the old "one mechanism" finding.** It described clause 2, and clause 2
is 14 of these 26 — so it was roughly right *about full-cast charts*, which is all its pool
contained. What it could not see was sparse charts, which the adjudication added and where the
mechanism is entirely different (clause 3, 17 errors). Both statements are now on the record.

### The sweep, re-run over all 381 scored verdicts

| AFFLICT | FAVOUR | exact | within-1 | real errors |
|---|---|---|---|---|
| 2 | 2 | 266 | 328 | 53 |
| 2 | 3 | 261 | 331 | 50 |
| 2 | 4 | 247 | 334 | 47 |
| **3** | **2** | **269** | **329** | **52** ← current |
| 3 | 3 | 264 | 332 | 49 |
| 3 | 4 | 250 | 335 | 46 |

**The current setting is still the exact-accuracy maximum.** But the TRADE has changed, and the
old conclusion should not be quoted as it stands. It recorded that raising FAVOUR "trades strict
accuracy for real errors at a poor rate: 2→3 costs 4 exact to save 1". On the corrected corpus
2→3 costs **5 exact to save 3 real errors** (and buys +3 within-1) — roughly 1.7:1, against the
old 4:1. That is still worse than the B1 guard which DID ship at 1:1, but it is no longer the
lopsided trade the old table described. The difference is not that the engine changed; it is that
the old ratio was measured on a pool selected for engine agreement.

**No change made, and deliberately so.** Moving CONTRA_PILLAR_FAVOUR from 2 to 3 because it
scores better here would be corpus-tuning — the precise thing `astrobank/METHODOLOGY.md` forbids
and the thing that produced two refuted arms in this same session. The knob means "how many of
Raman's three factors must be strong before a contradicted matter reads favourable", and 2-of-3
versus 3-of-3 is a **doctrinal** question about the three-factors method, answerable only from his
text. **Re-open path:** find whether Raman requires all three factors strong for a favourable
reading of a contradicted bhava, or accepts a majority. If the text says all three, FAVOUR=3
ships on that basis and the numbers are a consequence, not a justification. If it says majority,
the current setting is confirmed and this closes for good.

## HOLD 3 — the bhava-rescue gate mismatch is real but unexercised (2026-08-24)

Profiling the 12 no-contradiction full-cast errors surfaced a citation tension in the existing
BHAVA-RESCUE clause. Raman's sentence (HTJAH-I:503-505) gates the rescue on *"the house itself
has good conjunctions and aspects"* — which the code carries as `fired_benefic` — but the code
ADDITIONALLY requires a strong numeric Bhava Bala (`bhava_bala_strong is True`), which appears
nowhere in the sentence. The extra gate is also what makes the rescue structurally dead on
Track-B charts (ticket filed 2026-08-23), since Bhava Bala is never computable there.

**Prototyped the textual reading** (`is not False` instead of `is True`, i.e. the same permissive
idiom the adjacent `bhava_ok` already uses) **and measured per-row: ZERO of 381 scored verdicts
change.** The relaxed arm never fires differently anywhere on the corpus — the charts that would
need it don't reach clause 6 with the required shape (`not lord_strong` + benefic-only firing).

**Held, per the unexercised-change discipline** (H11.C.6/C.7, clause-2-symmetry precedents): an
unexercised gate relaxation adds unproven behaviour for zero measured effect, and unlike the
combustion fix it changes no stored data — only a branch that nothing takes. The citation tension
stands recorded; re-open when a golden (or a family real-outcome case) actually routes through
clause 6 with a weak lord, benefic testimony, and an unknown/weak Bhava Bala, so the change would
be measurable rather than speculative.

### The 12 no-contradiction errors, profiled

| pattern | n | reading |
|---|---|---|
| nothing fired, 3 strong pillars → favourable; Raman afflicted | 4 | pure coverage gap: Raman's afflicting factor is not encoded as a rule at all |
| benefic-only fired, 3 strong → favourable; Raman afflicted | 3 | same gap, one-sided testimony |
| benefic-only fired, 2 strong/1 weak → afflicted; Raman favourable | 3 | clause-6 shape; the rescue tension above is adjacent but measured inert |
| malefic-only fired → afflicted; Raman favourable | 2 | mirror coverage gap |

**Seven of twelve are coverage gaps, not judgment defects** — the engine never heard the evidence
Raman weighed. That folds them into the same programme as the 9 abstentions: per-chart source
reading to identify which of Raman's stated factors is missing as a rule, i.e. golden-corpus /
rule-encoding work, not judge work.

### The four nothing-fired charts, diagnosed — NH.chart_57 is the worked example (2026-08-24)

All four "nothing fired, three strong pillars → favourable, Raman afflicted" errors share one
mechanism, and chart_57 shows it exactly:

- **Raman's sentence**: "The 5th house is equally afflicted as the lord Mars is with Rahu and
  Saturn." His operative fact: the LORD is CONJUNCT two malefics.
- **The engine HOLDS that fact**: Mars (5th lord for Cancer lagna) sits in the Lagna in the same
  rasi as Rahu AND Saturn. Nothing is missing from the chart model.
- **No rule shape matches it**: the five afflicted-5th-lord rules are all narrower compounds —
  H5.C.9 needs papakartari, H5.C.10 needs the 5th house ALSO malefic-aspected (it is not, so
  C.10 correctly declines per its own citation), H5.C.14 needs Saturn in the 5th, H5.L.4 is the
  lord-in-4th table row. The bare fact has no rule.
- **The pillar apparatus cannot carry it either**: pillars measure BALA, and Mars's Shadbala
  reads strong. Contact-affliction and strength are different axes — the same finding the
  majority-loci probe (2026-08-23) hit from the other side.

The other three: h5_10 ("lord weak, Karaka powerless" — Raman grading pillars DOWN where
Shadbala grades them up), chart_55 ("affliction of Lagna lord by three malefics"), x73 ("lord and
Karaka moderately blemished"). Lord/karaka contact-affliction in every case.

**What this does and does not license.** It does NOT revive the refuted majority-loci tally —
that mechanism was measured non-differential across the corpus and stays dead. It sharpens the
already-filed design ticket instead: Raman's strength reading is **three-valued and blended**
("moderate in strength", "moderately blemished", "not sufficiently strong"), where contact
degrades a strong-bala planet toward the middle band. An `Optional[bool]` pillar cannot express
"strong bala, blemished by association". The three-valued band design is now motivated by BOTH
halves of the error surface (sparse: no bala at all; full-cast: bala contradicted by contact) and
is the single remaining mechanism-shaped lever. It requires a design session with its own
doctrine review — per-band definitions must come from Raman's grading vocabulary, not from
fitting these four charts.

## The pillar thresholds, doctrinally re-cited — FAVOUR confirmed, AFFLICT resolved (2026-08-24/25)

The re-derived sweep left one doctrinal question: does a contradicted bhava need ALL THREE of
Raman's factors strong to read favourable, or a majority? Settled from the text, engine-blind.

**FAVOUR=2 (majority) is VALIDATED — but on a different citation than proposed.** My candidate,
HTJAH-I:2113 ("at least two of the three factors"), was REJECTED by the reviewer as the proof:
its triad is Lagna/Sun/Moon — the body-mind-soul trinity (HTJAH-I:1870-1873) — and its consequent
is whole-life fortune, not a bhava verdict. The suspected over-generalisation was real. The true
authority is **HTJAH-I:5729-5730** (Chart No. 96, verified verbatim): *"Since the house and the
lord are considerably afflicted, the Karaka's moderately benefic disposition SHOULD BE IGNORED."*
Two pillars against one, both testimonies present, the dissenting third ordered discarded —
unanimity cannot survive that sentence. Applied favourably on worked charts across houses:
HTJAH-I:4856-4858 (Chart 80: karaka considerably afflicted, house+lord strong → "very high
official position"), :4619-4621, :8493-8518. Ten consistent negative cases; the one candidate
counterexample (Chart 68) is OCR-self-contradictory and unusable either way. All eight "all the
three factors" recurrences checked: every one descriptive sufficiency, none prescriptive
necessity. The knob is re-cited in `shadbala/total.py`; it no longer stands on the sweep.

**AFFLICT=3 vs the same passage — investigated, and the tension dissolves into the predicate.**
5729 condemns at TWO afflicted pillars, which reads like AFFLICT should be 2. Measured per-row:
lowering it flips exactly **3 scored verdicts, all three AWAY from Raman** (HTJAH-II.h11_08
favourable→afflicted where Raman says favourable — a new inversion; NH.chart_45 and NH.chart_47
mixed→afflicted where Raman says mixed). Meanwhile the condemnations Raman actually issues at two
afflicted pillars are UNREACHABLE by any threshold: on HTJAH-I Chart 73 ("the lord and Karaka are
moderately blemished" → mother lost) both condemned pillars read **bala-strong**. Raman's
"considerably/moderately afflicted" is contact-blemish severity; the pillar booleans are
bala-weakness. **Two different predicates wearing one word.** The knob stays 3 — not because the
text supports unanimity, but because at 2 the bala-boolean misfires on everything it can reach
while still missing everything Raman means.

**This is the third independent derivation of the same conclusion in two days.** The sparse-chart
profile (no bala at all), the nothing-fired diagnosis (bala strong, contact ignored), and now the
AFFLICT investigation (bala-weak ≠ Raman-afflicted) all terminate at the identical design gap:
**the engine needs a graded strength band that folds contact-blemish into the pillar reading**,
with band definitions taken from Raman's own vocabulary (feebly / moderately / fairly /
considerably / quite — the reviewer counted the grades). That design session is now the
single next piece of mechanism work, and nothing smaller will move the remaining error surface.

Two rendering notes from the review, filed for the report surfaces (no verdict impact): a 2-of-3
favourable verdict arguably owes the reader the dissenting pillar's specific denial (Raman always
confines it to its own signification — Chart 80 gets high office AND denied schooling); and the
knob docstring previously described both thresholds as pure sweep calibration, which is no longer
true of FAVOUR.

## ★★ THE GRADED STRENGTH BAND — design session run, countable form CLOSED-REFUTED (2026-08-25)

The design session three independent investigations demanded. Its outcome is a refutation, and
it is the most informative result of the whole error-surface programme. Binding on future work.

### What the session established first: the vocabulary is real

268 graded-state phrases harvested across HTJAH-I/II. They cluster into three operative bands
with a graded rim — retained here as the durable asset for any future attempt:

| band | Raman's words (with counts) |
|---|---|
| STRONG | well disposed (42), well fortified (29), very powerful (23), very strong (23), quite strong (19), considerably fortified, highly fortified |
| MIDDLE | fairly strong (18), moderately strong (7), "moderate in strength" (recurring), feebly strong (3), not sufficiently strong (3), slightly/somewhat/moderately blemished |
| AFFLICTED | considerably afflicted (26), heavily afflicted (24), badly afflicted (11), quite afflicted (6), very weak (4), powerless |

### The make-or-break measurement, run BEFORE any design: the band cannot be computed from counts

The band is only implementable if some countable contact measure on the pillar planets separates
the rows Raman reads afflicted from those he reads favourable, among rows the engine currently
reads favourable. Four pillar-blemish variants were measured (worst-of lord/karaka, net of
benefic mitigation), completing the eight begun by the majority-loci probe:

| variant | Raman-favourable (n=134) ≥+1 / ≥+2 | Raman-afflicted (n=27) ≥+1 / ≥+2 |
|---|---|---|
| natural nature, conj+aspect | 62% / 28% | 70% / 41% |
| natural nature, conjunction-only | 46% / 2% | 59% / 7% |
| functional nature (Raman's per-lagna printed table), conj+aspect | 43% / 8% | 52% / 15% |
| functional nature, conjunction-only | 29% / 3% | 30% / 4% |

**No variant separates.** The best relative differential (~1.5x) sits on base rates of 28-41%,
useless as a discriminant; the most faithful variant (functional, conjunction-only — the exact
shape of the error proses' "with Rahu and Saturn", counted with Raman's own printed per-lagna
lists) shows NOTHING (29% vs 30%). With the earlier loci-tally probe this makes **eight contact
measures refuted**: natural/functional x conjunction/aspect x pillar/loci.

### What this means, stated plainly

**Raman's per-chart strength grades are not a function of countable contact.** Blemished pillars
are just as common on the charts he reads favourable. Whatever selects "considerably afflicted"
on Chart 96 but "well fortified" on a chart with the same contact profile lives in information a
count does not carry: which specific configuration, which signification the afflictor touches,
the yoga context, the dasha story, and his own graded language per case. This is the MEASURED
TRUTH mechanism — indications abundant and non-differential — now demonstrated INSIDE the golden
corpus at pillar level, against Raman's own judgments.

**Consequently the 52-row error surface is NOT mechanism-shaped.** There is no clause, band,
threshold, or guard left to design; every countable form has been measured against the corpus and
none discriminates. What remains is per-chart doctrine work: for each error chart, read Raman's
stated reason, and where his sentence instantiates a general rule that exists in his text, encode
THAT rule with its citation (the chart_57 diagnosis is the worked template: the fact is held, the
rule shape is missing). Where his reasoning is irreducibly per-case, the chart goes to the
documented-limits register. That is golden-corpus/rule-encoding work — slow, per-chart, honest —
and it is the only path that remains open.

The three-valued-band ticket is CLOSED in its computable form. Re-open ONLY with a proposal whose
discriminant is measured to separate before any design begins — the burden of proof is now on the
proposer, and eight dead variants say the bar is high.

## Per-chart error programme, pass 1 (2026-08-29) — 2 rules recovered, 4 documented limits

First pass of the only remaining fidelity path (the graded-band refutation's conclusion): take
each error chart, read Raman's stated reason, encode the general rule where his text states one,
register the documented limit where it is irreducibly per-case. Processed: the four nothing-fired
charts.

**Recovered: H5.C.15 and H5.C.16 — two clauses of Raman's own printed list, never encoded.**
Tracing NH.chart_57 back to the children-die-early list (HTJAH-I:5190-5209) exposed that the rule
id sequence skips 15/16 and no rule anywhere carried these predicates, while every neighbouring
clause of the same list shipped long ago:

* **H5.C.15** (HTJAH-I:5200-5201): "when Rahu and lord of Lagna are associated with the 5th lord
  or occupy the 5th" → children die early. Encoded as the COLLECTIVE parse (both planets joined
  to the 5th lord, or both in the 5th) with "associated" = conjunction. Reviewer VALIDATED/HIGH,
  and strengthened the precedent: H2.C.62 and H11.C.21 already encode Raman's identical
  "associated with <lord>" as LordsConjunct, the wider conjunction-or-aspect reading being
  reserved for where he writes "aspect or association" (H1 _LordsInContact) — and in this very
  paragraph he writes "aspected by" four times when he means aspect. The mixed configuration
  (Rahu with the 5th lord while the lagna lord sits in the 5th) is a recorded floor, not covered.
* **H5.C.16** (HTJAH-I:5203-5204): "The family is extinguished when the lord of Lagna is in the
  5th, and Lagna and the Moon have evil associations." Lagna's evil association = malefic
  occupation (the sibling C.17 reads the same sentence-group's "the Lagna by a malefic"
  identically); the Moon's = malefic conjunction over exactly NATURAL_MALEFICS. VALIDATED/HIGH.

Hygiene from the review: C.11's descriptive text had bundled the Rahu+Lagna-lord fragment that is
actually 5200's first disjunct — trimmed, with a pointer to C.15. Re-open path recorded on both:
if a Raman worked nativity ever applies 5200/5203 through aspect-only contact, that is citable
grounds to widen "association".

Liveness 743 → 745, fired 685 → 687, never-fired stays 58 (C.15 fires on the wider 346-chart
corpus, outside the scored subset). Ratchet byte-identical at 269/381 — these ship on citation,
as always.

**Documented limits: all four nothing-fired charts.** None yields an encodable rule:

| chart | Raman's stated reason | why no rule can carry it |
|---|---|---|
| NH.chart_57 H5 | "lord Mars is with Rahu and Saturn" | his own list's nearest clause (5200) requires the LAGNA LORD joined too — Moon is in the 10th; the NH judgment is broader than his printed list |
| NH.chart_55 H1 | "affliction of Lagna lord by three malefics" | facts verified exactly (Mars asp, Rahu asp, Ketu conj on Venus) but NO general lagna-lord-afflicted combination is stated anywhere in the doctrine region — blended judgment |
| HTJAH-I.h5_10 H5 | "House feebly strong, lord weak, Karaka powerless" | pillar-grading language; the graded band that could carry it is CLOSED-REFUTED in countable form |
| HTJAH-I.x73 H4 | "lord and Karaka moderately blemished" | the predicate-mismatch specimen (bala-strong, contact-blemished); same refutation |

**Programme arithmetic, for planning.** Pass 1 processed 4 error charts: 0 fixed (the two
recovered rules fire on neither — they ship because the TEXT states them), 4 documented limits,
2 rules of pure doctrine-completion recovered as a by-product. The realistic value of the
remaining ~48-chart queue is exactly this shape: fidelity moves rarely; corpus completeness and
honest limit-registration are the steady yield.

## Per-chart programme pass 2 + the contested row closed (2026-08-29)

**NH.chart_38 H9 resolved by tiebreak: CONFIRMED mixed, ratchet 269/381 → 270/382.** The row was
held because two engine-blind reviewers split afflicted-vs-mixed. A third blind reading went
2-of-3 for mixed: the only father content in the whole Ford write-up (NH:8530-8532) is a
double-hedged mild negative — "not *quite* conducive to *happy* relations" — whose confirming
instance is vocational disagreement, with none of the loss/deprivation markers Raman uses when he
means affliction. Direction negative, magnitude below the afflicted band. The engine happens to
read mixed, so the row lands exact — legitimately, via three blind readings.

**Pass 2 rule-checks: both resolve as documented limits.**

* **HTJAH-II.h9_02** (papakartari to 9th house/lord/karaka overrode royal-father strength): the
  ninth-house doctrine region states only the generic "If afflicted, the father may die early"
  (HTJAH-II:310); no general hemmed-9th rule exists in the text, and H9.A.20a covers only the
  Sun-in-dusthana variant (h9_02's Sun is in the 9th itself). Raman's conclusion is the blended
  papakartari-on-all-three-loci judgment — the loci-tally that would carry it is CLOSED-REFUTED.
* **HTJAH-I.h6_04** (myopia via 6th lord in the 2nd + 2nd lord in the 12th with Saturn): no
  eye/vision rule is stated anywhere in the sixth-house doctrine region, and H6.L.2 (6th lord in
  the 2nd) carries a different printed result entirely (loss of wife). The vision chain is a
  per-chart signification-transfer reading. Documented limit.

Running tally of the programme: 6 error charts processed, 6 documented limits, 2 recovered rules
(C.15/C.16, firing on neither), 1 contested row honestly closed, fidelity +1 by tiebreak.

## Per-chart programme pass 3 — two clusters, one guard shipped, one REVERSAL held (2026-08-29)

Triage of the remaining 46-row queue found two same-direction clusters, and clusters beat
chart-by-chart: three speech errors and four children errors, all engine-over-afflicted.

### Speech cluster → B3 extension SHIPPED (+1 exact, −1 inversion; 271/382)

Benefic rules fire for speech on all three charts, yet the verdicts were afflicted — because the
2nd is a maraka sthana and `maraka_active` fires on set MEMBERSHIP of the matter's lord, while
the 2nd lord is a maraka determinant BY DEFINITION (HTJAH-I:779). Every 2nd-house matter carried
permanent maraka pressure by construction: the identical artifact B3 fixed for Venus/the 7th.
Reviewer VALIDATED extending `MARAKA_NON_DEATH_GUARD` to speech/vision/family as ONE CLASS (the
maraka chapter is death-determination doctrine, full stop; Laghu Parashari lists "Maraka effects"
as a separate 2nd-house signification, severable from the quality matters; guarding speech alone
would encode a distinction no source supports). `wealth` deliberately excluded — the poverty
block (HTJAH-I:2526-2528) makes maraka association a wealth operator, and those are fired rules
that keep force under the guard anyway. Row gained: NH.chart_26 (Marx — exalted yogakaraka Venus
in the 2nd, Raman favourable). The two residual speech rows are navamsa-weakens modulations of a
borderline mixed — legitimate machinery, left alone.

### ★ Children cluster → the FERTILITY GATE is doctrinally REVERSED but empirically load-bearing: HELD

The reviewer returned a full **REVERSAL** (HIGH) on the Beeja/Kshetra gate, every finding from
the printed text:

1. **The "O1" sign-off's premise is false.** The gate was justified by h5_08/h5_11 being read
   afflicted "purely on barren sphutas". Raman computes NO sphuta in either chart: Chart 98's
   printed drivers are lord/karaka Saturn-afflictions (HTJAH-I:5750-5768); Chart 101's are
   Saturn occupying and Mars aspecting the 5th-from-CHANDRA-LAGNA (HTJAH-I:5826-5842) — and
   that chart AFFIRMS birth while denying survival. The gate is a patch over un-scored
   Chandra-Lagna 5th testimony, wearing a sphuta citation.
2. **Parity-only denial inverts Raman's worked cases.** Both his strength examples FAIL parity
   and are rescued (Chart 88 "though an even sign... These indicate the strength of the Beeja",
   :5548-5551; Chart 89 "(though odd)... the Kshethra is fertile", :5574-5580). Parity alone
   yields at worst reduced quantity. The one printed denial (Chart 90, :5602-5605) needs the
   full stack — both-varga failure AND malefic sign AND malefic aspect AND afflicted sthana.
3. **The sphutas are sex-assigned across the COUPLE.** Beeja for a male chart, Kshetra for a
   female one (:5517-5520); every worked use is single-sphuta, sex-matched. Computing both from
   one chart is textually meaningless — Queen Victoria (nine children) was denied partly on HER
   chart's Beeja, the male seed belonging to Prince Albert's chart, while her sex-matched
   Kshetra is fully strong.

**Suspension was implemented and MEASURED: 270/382 → 259/382 exact, real errors 52 → 62.** The
reviewer's predicted +3/−2 was wrong about reach — the gate carries ~13 correct afflicted
verdicts across the H5 corpus. **HELD per the net-negative rule** (the same standard that held
the clause-2 fix): reverted.

**The honest state, recorded plainly: ~13 correct H5 verdicts currently rest on a mechanism
whose doctrinal justification is refuted.** They are right for the wrong reasons. This is the
corpus's largest known instance of the accidental-correctness class, and it must not be quietly
forgotten because the ratchet looks fine.

**The recovery path (sequenced, and the ONLY sanctioned route to suspension):**
1. Encode Raman's ACTUAL printed drivers for these charts — above all **Chandra-Lagna 5th-house
   occupancy/aspect testimony** (the stated mechanism of h5_11's "strongly blemished" and part
   of h5_08), which the engine does not currently score for H5 children. A cited coverage gap
   with a worked chart naming it: prime dead-rule-sweep-shape work.
2. Re-measure the suspension once that testimony carries the rows. If the corpus then holds,
   suspend the gate (reinstatement condition for any future sphuta work: sex-matched sphuta
   only — requires native sex on the chart model — under the full Chart-90 pattern with the
   :5548-5551 rescues checked).
3. Until then the gate stands, flagged here as refuted-but-load-bearing. The "O1" user sign-off
   should be considered void in principle (its factual premise failed), pending the recovery.

### Addendum to pass 3: the B3 extension cost a private family row, and the floor was lowered honestly

The pre-commit real-outcome guard blocked the commit: Avika's H2 speech (owner-confirmed
AFFLICTED — a child in speech therapy) had been within-1, and the guard lifted it to favourable,
dropping her static floor 5/5 → 4/5. Investigated before overriding: the previously-correct
'afflicted' was DELIVERED BY THE MARAKA TAUTOLOGY the review refuted — the same right-for-the-
wrong-reason class as the fertility gate, on one row instead of thirteen. Keeping a refuted
mechanism to preserve one matching outcome is the trap the audit exists to close, so the floor
was consciously lowered 5→4 in the same change, with the full note in `real_outcomes.json` and
the miss recorded. The recovery is the same as for the goldens: encode the chart's actual
afflicting testimony from cited rules; never re-widen the tautology. This is also a live datum
for the honesty ledger: the day's one fidelity "gain" (+1 golden, Marx) cost one real-outcome
row (Avika), which is exactly the two-axes trade-off the project promises to report and never
average.

### Fertility-gate recovery, step 1 MEASURED and insufficient (2026-08-29)

The sequenced recovery's first step — encode Chandra-Lagna 5th-house testimony and let it carry
the gate's rows — was probed before building, per the band-refutation discipline. Discriminant
over all scored H5 rows (net malefic-minus-benefic testimony on the 5th-from-Moon, occupancy
double-weighted):

| group | n | net ≥ +2 |
|---|---|---|
| gate-carried (Raman afflicted) | 15 | **6 (40%)** |
| other Raman-afflicted | 9 | 3 (33%) |
| other Raman-favourable | 8 | 1 (13%) |

Directionally right (h5_11's own mechanism is real) but far short of replacement: a demote-only
Chandra-corroboration gate at net ≥ +2 would recover ≤6 of the ~15 carried rows and clip a
favourable. **No single mechanism replaces the refuted gate** — its carrying capacity is
heterogeneous, one printed reason per chart. The recovery path is amended accordingly: the gate
stays (refuted-but-load-bearing, as recorded) until per-chart rule coverage accumulates through
the ordinary programme; the Chandra-Lagna testimony remains a real, citable factor (HTJAH-I:7093
"as from Moon, which cannot be ignored ... as he is strong" — note Raman gates it on the Moon's
own strength) for encoding as individual cited rules where charts name it, not as a blanket gate.


## WS2 CLOSE-OUT (2026-08-30) — the adjudication story is complete; the scored pool is now the whole corpus

Every adjudicable DRAFT in the golden corpus is resolved. Final movement: **271/382 → 277/397
exact (69.8%), 344/397 within-1 (86.6%), real errors 51 → 53.** Four moves, one commit:

1. **Splice re-extractions (+2).** NH.chart_13 H1 and NH.chart_5 H1 confirmed favourable per the
   prior engine-blind reviews that rejected their originals — a footnote splice had INVERTED both
   (the printed text reads unafflicted/fortified). The three splice classes (footnote /
   section-heading / two-passage) are now guarded in `extract_htjah_goldens._conclusion`, each
   pinned by a test reproducing the row it corrupted. NH.chart_32 H1 deliberately NOT re-applied:
   the reviewer's pointer ("sweet and gentle nature") states a trait, not a graded conclusion.
2. **Leftover queue (+17, the final batch).** The 15 insufficient-evidence drafts + 2 invalid-sig
   rows adjudicated engine-blind: 16 REVISE, 1 CONFIRM, 0 REJECT. Three matters moved to their
   true significations (HTJAH-II.chart_01 + h9_11 gains→elder_siblings; x63 mother→education —
   its source text sits in the HTJAH-I file despite the II id). Invalid-sig backlog 11 → 9
   (NH.chart_39 death/maraka → death; NH.chart_42 career/leadership → career, mixed).
3. **Duplicate collapse (−4).** The uniqueness guard caught four matters confirmed on two
   chapter-presentation records of one nativity — the exact bug class it was built for after the
   2026-08-23 audit. Each matter now scores once; shadow copies carry the new terminal-unscored
   `DUPLICATE` status (schema: `_REVIEWS` now {DRAFT, CONFIRMED, DUPLICATE, CONTESTED}).
4. **Tiebreak overturn (−1 exact, honest).** The 1937-08-16 nativity's H7 marital_happiness had
   an existing favourable confirmation quoting only the positive half of a two-sided conclusion
   (raman2:1041-1050: "temperamental clashes" AND "stable marriage with deep attachment", same
   operative verb on both). Third blind reading → 2-of-3 MIXED, scored on HTJAH-II.h11_01. The
   engine reads favourable there, so the resolution costs a point — recorded, not fudged.

**What "complete" means:** the scored pool is now every conclusion Raman reached in the three
books — hit or miss. Remaining DRAFTs are rejected observations, corrupt prose, or the
engine-mismatch backlog (Workstream 1's per-chart queue). The denominator can still grow from
NEW sources (Astrological Magazine, WS4) but no adjudication debt remains.

**WS3 shipped alongside:** `BirthData.sex` ("M"/"F"/None, validated, never guessed) +
golden-schema `birth.sex` support + paired tests. Pure capability — unlocks the sex-matched
Beeja/Kshetra sphuta test (the fertility-gate reinstatement condition) and HTJAH-I:486 factor 7.


## WS1 PASS 1a (2026-08-30) — the Chandra-Lagna 5th rule ships; the fertility-gate ledger re-profiled

**H5.C.39 SHIPPED** (bphs-doctrine-reviewer SHIP-WITH-AMENDMENTS, HIGH; amendments applied):
>= 2 distinct natural malefics occupying or aspecting the 5th FROM CHANDRA LAGNA -> strong
afflicted testimony for children — deliberately **NON-decisive**. The review's findings, all
banked:
- FIVE explicit printed citations (two of which this session had misfiled as "incidental
  fires"): Chart 101 HTJAH-I:5826-5829, Chart 98 :5750-5752, **Chart 108 :5956-5958** ("a clear
  case of the spoiling of the 5th house"), Goethe NH:5494-5497, **Wadiyar IV NH:11061-11064**
  (Raman's second influence there is MANDI, unmodelled — the engine counts Saturn's aspect;
  recorded in the rule comment).
- The >= 2 bar is Raman's own vocabulary gradient: one malefic aspect rates "nominally or
  feebly strong" (Chart 100, :5804-5806); two or more rate "strongly blemished" / "completely
  spoiled".
- DECISIVE was refused on three textual grounds (Victoria NH:6764-6770 is a printed
  counterexample; the CL testimony never stands alone even in condemned charts; the two mixed
  fires show restriction, not denial). The benefic-relief guard (HTJAH-I:5876-5878) FAILED
  enumeration — Jupiter aspects the CL 5th in condemned Charts 101/Shaw exactly as in Victoria
  — so the rule ships guardless and **Victoria is the documented limit**. Moon-strength gate
  REJECTED (HTJAH-I:7094 is a per-chart weighting remark; the gate rescues nothing in the fire
  set). Node drishti: 7th-only per the raman_saab lock (the design-time 5/9 scratch measurement
  was caught and re-run; chart_16/x93 correctly dropped out of the fire set).
- Movement: 277/397 -> 279/397 exact, 345 within-1, real errors 53 -> 52. Exactly two rows
  moved, both toward Raman: Gaekwar/chart_37 favourable->afflicted (dist-2 resolved),
  Bose/chart_68 mixed->afflicted. Zero regressions.
- **Fertility-gate ledger re-profiled**: C.39 now carries h5_11 on its cited mechanism (OUT of
  the gate's carry list). **CORRECTION 2026-08-30, same session**: this entry (and the d7bfaad
  commit message + baseline note) originally claimed h5_18 and chart_52 also left the carry
  list — FALSE. Neither was ever gate-carried; both were plain misses before and after C.39
  (h5_18 was later fixed by H5.C.40; chart_52 remains a miss). Only h5_11 moved. The ratchet
  numbers were correct throughout; the prose over-claimed.
  Suspension re-measured: net −12 (13 carried, 1 healed). THE GATE STAYS, refuted-but-load-
  bearing. Remaining carried rows and their printed drivers, for future passes: h5_04
  (lord+house "considerably afflicted"), h5_05 (PK baneful — Arm B's own chart), h5_08
  (Saturn-association on lord+karaka), h5_09 (PK + two first-rate malefics), h5_12 ("5th
  spoilt" — Arm A's own chart), h5_02, chart_19 (5th lord with Saturn + Mars aspects the 5th),
  chart_22 (Keetarasi lord + PK-in-5th with Rahu), chart_20/31/37/40/68 (gate-entangled via
  the one-weak arms).

**H2.C.71 Vakchalana Yoga SHIPPED** (bphs-doctrine-reviewer VALIDATED, HIGH, no amendments):
malefic 2nd lord in a cruel navamsa with the 2nd devoid of benefic aspect/association ->
stammerer (3HC:5991). Cruel-sign set {Ari, Leo, Sco, Cap, Aqu} anchored to Raman's own
HTJAH-I:1105-1107 parenthetical; Moon kept in the relief set (the H7.C.82 three-benefic
precedent was a judge-calibration decision, not doctrine — playbook rule 6). Fires 21/242,
ZERO scored speech overlap today: corroboration-only, recorded per the no-silent-caps rule.
**Re-open path**: if a confirmed speech verdict ever lands on a chart that escapes only
through a WANING-Moon touch on the 2nd, revisit with a phase-conditional Moon.

**1b — Avika H2 speech: DOCUMENTED LIMIT, floor stays 4.** Her chart correctly escapes both
cited speech mechanisms: HTJAH-I:2469 (H2.C.25) needs the 2nd lord debilitated or in the
2nd/8th with malefics — hers is EXALTED Mars in the 11th; Vakchalana needs the 2nd devoid of
benefic influence — her 2nd holds the Moon and receives Jupiter's drishti. Her real afflictions
(2nd lord with Ketu, vak-karaka Jupiter in the 8th, Mercury-Rahu in the 5th) match no rule
Raman states generally — Mercury-with-Rahu in his text is a SPECULATION-loss indicator
(HTJAH-I:4025), not speech. No mechanism invented; the miss stands recorded. Recovery
re-opens only if a citable general rule surfaces (Astrological Magazine sweep, WS4).


## WS1 PASS 2 (2026-08-30) — the contact-affliction twins + the span/manner separation; 282/397

Three reviewer-approved changes, each moving exactly one row toward Raman, zero regressions.
Cumulative from pass 1a: 277 -> 282 exact, real errors 53 -> 49.

**H5.C.40** (SHIP-WITH-AMENDMENTS, HIGH): PutraKaraka under the COMBINED contact of >= 2
first-rate malefics {Mars, Saturn, Rahu, Ketu} -> afflicted testimony, NON-decisive. Chart 99
HTJAH-I:5795-5799 verbatim; second citation Chart 95 :5701-5713; corroborated Shaw NH:7320-7323
(a genuine two-contact chart per :7302-7303), Marie Antoinette NH:5834-5836, Bose
NH:14001-14003. Reviewer findings banked: (a) Raman's "first-rate malefic" idiom INCLUDES the
Sun (HTJAH-I:5673, NH:10543, NH:18035) — the Sun's exclusion from the contact set is an
EMPIRICAL DOCUMENTED LIMIT (no printed PK condemnation names the Sun), not his vocabulary;
(b) no printed chart condemns on a single PK contact alone — the >= 2 gradient is his own
("moderately blemished" / "feebly weak" at one, "sorrow" at two, "most baneful" at three);
(c) chart_67's fire is directionally faithful but a MECHANISM MISMATCH (his stated driver is
the 5th-lord Mars), never a validation chart. Fixed h5_18 (favourable->afflicted, dist-2).

**H4.C.48** (SHIP-WITH-AMENDMENTS, HIGH): the exact H4 twin — Matru-Karaka Moon under >= 2
first-rate contacts. Chart 68 HTJAH-I:4550-4560 ("combined aspect of two first-rate malefic
... Matru-Karaka is considerably afflicted"; own-lordship does not sanitize, :4558-4559). The
reviewer read the ENTIRE 64-75 mother series: condemned at >= 2 (x67 :4529-4539, x70
:4595-4601, x71 :4616-4617), explicitly dismissed at one contact (x73 "moderately blemished",
x75 "feeble" — even an EXALTED Saturn's single aspect), and the two apparent single-contact
condemnations (x69, x72) carry printed independent drivers. **x74 is the printed
COUNTERBALANCE case** (:4673-4678): exalted Moon + Ketu + Mars fires the rule, Raman registers
the affliction then outweighs it (Jupiter aspect + navamsa) -> "feebly blemished" — exactly
what non-decisive testimony models; if x74 is ever confirmed mixed/favourable the fire is
expected. Thyagaraja (chart_23) upgraded: TWO of the engine's three contacts are in Raman's
own text (MK-with-Ketu NH:6060-6063; Saturn-aspects-Cancer :6071-6072). Fixed chart_23
(favourable->afflicted, dist-2).

**Clause-1.5 span/manner separation** (SHIP, VALIDATED, HIGH): a fired BENEFIC of the
`longevity` SPAN signification no longer vetoes the death-MANNER affliction confirmation.
The bug: Marie Antoinette's guillotine reading (H8.C.1 fired, Saturn occupies + Mars aspects
her 8th) was blocked by H8.L.8 ("8th lord in the 8th -> long life", HTJAH-II:3001) — a purna
span vetoing a violent manner, the exact conflation the H8-OPENED decision forbids. The
reviewer's proof text is her own chart: Raman counts the SAME Saturn-in-8th on the guillotine
side ("by virtue of the influence both Saturn and Mars prevailing on the 8th house ... her
graceful head fell", NH:5950-5952) — the asymmetry is doctrine, not corpus-fit. Process per
playbook rule 3, all three faithful forms MEASURED before shipping: fully sig-precise broke
11 correct H6/H12/H8 rows (malefic-side pooling is load-bearing — the 6th's afflictions
cross-speak by design); symmetric span-exclusion broke Lincoln/Hitler (their manner
confirmations ride malefic 8th-apparatus rules tagged longevity). Scope proven H8-only by
enumeration (no H6/H12 key pools the longevity tag; all 21 longevity rules are house=8).
**STANDING DEPENDENCY: the benefic-in-8th manner veto now routes exclusively through the
death-tagged H8.C.2 — if H8.C.2 is ever re-tagged, this exclusion must be revisited.**
Fixed chart_22 (favourable->afflicted, dist-2). New unit test pins the veto case.

**H8 queue remainder** (for later passes): chart_41 Gandhi (benefic Jupiter in the 8th fires
death-tagged H8.C.2, so clause 1.5 correctly defers — his fix needs the malefic-ASPECT-on-8th
testimony and/or the drekkana leg), chart_72 Godse + chart_22's second leg (Ayudha/Nigala
DREKKANA death-manner — H8.C.21 is a stale descriptive TODO; needs the named-drekkana
primitive: planet degree-band -> Parasari drekkana name table), chart_39 Ashutosh (8th-lord
maraka-timing conclusion; no aspect mechanism — may be a documented limit for the static
verdict).


## WS1 pass 3 (2026-08-30, in progress) — H2 speech pair diagnosed; H2.C.72 ships as corroboration

**H2.C.72 SHIPPED** (benefic occupying the 2nd -> speech fortified; NH:5655 Bose "Jupiter in
the 2nd house made Bose a clear, forceful and convincing speaker", NH:4777-4801 Tennyson
"poetic greatness ... Venus in the 2nd", + Marx per the B3 record). Zero scored movement —
recorded corroboration, same class as Vakchalana.

**Tennyson (chart_25) + J.C. Bose (chart_33) H2 speech: DOCUMENTED LIMITS, diagnosis precise
and measured.** Both engine-afflicted where Raman says favourable. Two hypotheses were
measured and REFUTED: (a) missing benefic speech testimony — C.72 now fires on both, no
movement; (b) wealth-rule pooling (speech.rule_tags=('wealth','speech')) — an in-memory probe
narrowing speech to its own tag changed NOTHING scored anywhere (282/397 identical; Tennyson
had zero malefic evidence and still read afflicted). The actual driver on both charts is the
weak-pillar + navamsa-weakens routing (Tennyson: karaka weak; Bose: lord weak; both
nav=weakens) — V2-guard machinery at its measured local optimum, which the north-star playbook
forbids tuning against two rows. Re-open path: a navamsa-authority design review for QUALITY
matters (speech/education-class), only with a pre-measured discriminant across all houses.


**NH.chart_13 (Guru Nanak) H1 self: DOCUMENTED LIMIT (sparse-input class).** Raman's verdict
rests on "The Lagna is Vargottama and even in the Navamsa, the Lagna is unafflicted"
(NH:3752-3755) — but NH prints NO ascendant degree for this chart ("Simha Lagna" only, from
the Gyani birth-details footnote), so the record carries lagna_sign alone and the engine's
materialized longitude cannot verify the Vargottama band (a fixed sign needs 13d20'-16d40').
The engine's afflicted comes from the lord-Sun's D9 debilitation driving nav=weakens on a
Track-B mixed — Raman reads the LAGNA'S OWN navamsa condition instead, which the stated
positions cannot reproduce. Re-open path: a Vargottama-Lagna self-fortification rule (cited
here + standard doctrine) becomes fireable only on charts whose asc DEGREE is printed; and/or
a stated_flags extension to the golden schema if more Vargottama-stated-but-degree-unprinted
rows accumulate (this is the first).


## WS1 pass 3 close (2026-08-30) — the named-drekkana primitive ships; 283/397

The stale H8.C.21 drekkana territory is unblocked. An evidence sweep reconstructed the
death-manner drekkana table cell-by-cell (HTJAH-II's printed table :3845-3871 is OCR-garbled;
Phaladeepika III.13 anchors it verbatim — reviewer verified the full Ayudha column
cell-for-cell; five cells worked-chart-anchored by printed longitudes). All three targets
reviewer-VALIDATED. Full per-cell evidence trail in `primitives/drekkana.py`.

Shipped: the primitive (+9 tests, midpoint sentinel — sign-only charts return None, never
phantom cells), H8.D.3 (8th lord in Ayudha -> violent manner; Godse NH:14735 verbatim),
H8.D.4 (Ayushkaraka Saturn in the Sarpa/Nigala/Pasa triad -> captivity/noose; Marie
NH:5944-5947). **Q5 amendment applied**: drekkana rules are CORROBORATION-TIER — Raman's
apparatus "gives the clue to the CAUSE of death" (HTJAH-II:3884-3886); in every worked
instance it is the "also" clause, and Savarkar (NH:10563-10570) is the printed
counter-instance (Jupiter in Ayudha, dasha-danger read, natural death). Implemented as
_DREKKANA_MANNER_RULE_IDS excluded from the clause-1.5 confirming set.

Movement: Godse (chart_72) insufficient-evidence -> afflicted; Ashutosh (chart_39)
favourable -> mixed (dist-2 -> dist-1; RECORDED mechanism-mismatch fire — his death
paragraph is timing/maraka, his death natural). 283/397 exact, 350/397 within-1, 47 real
errors. Zero regressions.

**Open items from this pass:**
- 22nd-drekkana counting convention UNRESOLVED (Raman's two worked examples disagree:
  HTJAH-I:10164-10166 exclusive vs Marie's derivation) — the rising-drekkana rules (incl.
  making H8.C.21 evaluable) wait on it; when resolved, RE-REVIEW D.4 as the junior partner
  of its passage (Raman's "also" syntax).
- Residual exposure, recorded: on a sparse benefic-free chart the Track-B malefic-only
  fallback can still land afflicted from a lone drekkana fire (Godse — where it happens to
  match Raman's own printed reasoning verbatim). Revisit with the 22nd-drekkana work.
- Gandhi (chart_41) still favourable: fires BOTH drekkana rules but his benefic-in-8th
  (H8.C.2) routes him out of confirmation. His own sentence ("Jupiter is in the 8th aspected
  powerfully by Mars — a maraka ... violent end", NH:6870) is a DEFEATED-PROTECTION
  statement — needs its own design + review, with the Victoria lesson in mind (no favourable
  death rows exist to counter-test a decisive form).
- Pakshi/Chatushpada cells retained as SECONDARY data; no verdict rule may consume them
  without fresh review.


## WS1 pass 4 (2026-08-30) — the 22nd-drekkana convention resolved; the Gandhi pair; 284/397

**THE 22ND-DREKKANA COUNTING CONVENTION: INCLUSIVE (+21), settled by derivation** (equivalently:
the same drekkana index in the 8th sign). Reviewer-VALIDATED after independently hand-recasting
the ascendants. Anchors: Lincoln (cast Aqu-2 -> Virgo-2, exactly HTJAH-II:6752-6753), HTJAH-II
Chart 69 (fresh-cast from its printed birth data, Leo-3 -> Pisces-3, exactly :6547), and Raman's
own structural identity "rises in the 8th Bhava, i.e., the 22nd drekkana" (:3687) — which ONLY
inclusive preserves for every lagna index. The Aquarius-27deg textbook example (+22, landing in
the NINTH sign against Raman's own gloss two sentences earlier) is the recorded off-by-one slip.
**Marie Antoinette reclassified ANOMALOUS**: the reviewer's recomputation supports her PRINTED
74deg01 lagna, from which no convention yields Raman's "first of Capricorn" — possibly the JP
first-of-8th shortcut; the derivation does not lean on her. JP's gloss corroborates 8th-house
PLACEMENT only (its literal "first" is refuted by both worked charts).

**Shipped on it** (all reviewer-approved): H8.C.21 EVALUABLE (the conjunctive suicide dictum
HTJAH-II:3684-3688, verbatim two legs; 26% fire rate ruled DOCTRINAL — "rates never justify a
change" — contained by corroboration tier, zero scored movement); H8.D.5 (the senior 22nd-class
rule; four-class union KEPT — Chart 69's Sarpa 22nd reads "the end was violent" with NO
captivity, refuting a triad/Ayudha prose split); D.4's re-review CLOSED (stands separate and
ungated — Raman stacks freestanding planet-in-cell testimonies and never declines one because
the 22nd is unnamed; its true evidence base honestly narrowed to ONE verbatim Ayushkaraka
instance, with Charts 66/67 re-attributed to the cell label).

**THE GANDHI PAIR** (chart_41 death favourable -> afflicted, the last NH batch-2 backlog miss
of its kind): H8.C.2 GUARDED — a benefic in the 8th protects only when free of Mars/Saturn
drishti; Gandhi's chart is the printed refutation of the bare form ("Jupiter is in the 8th
aspected powerfully by Mars — a maraka ... a violent end", NH:9184-9191); "beneficially
DISPOSED" (HTJAH-II:3880-3882) supports the holistic reading. Reviewer VALIDATED. H8.D.6 (the
vitiated configuration -> violent end) was DOCTRINE-CONTESTED and amended **MARS-REQUIRED**:
**Sankaracharya NH:2077-2087 is the pinned printed counter-instance** for a Saturn-alone arm
(his Jupiter-in-8th under Saturn's lone 3rd drishti reads "sublimation of the sex energy and a
spotless character", death analysis pure span) and Raman's own cause table reserves violence
for Mars (:3886-3891, "Mars by weapons ... Saturn through starvation"). Saturn alone WITHHOLDS
protection (C.2 guard) but ASSERTS nothing — the three-state design: protected -> C.2 benefic;
Mars-vitiated -> D.6 malefic; Saturn-only -> silence. D.6 stays confirm-capable (tier demotion
would undo the fix; his other manner testimony is corroboration-tier drekkana). Residual
out-of-pool exposure recorded: a lone Mars-aspected benefic-in-8th confirming by itself;
re-open on any printed chart with that configuration read as natural death.

Movement this pass: +1 exact (Gandhi), real errors 47 -> 46. Zero regressions. The Victoria
condition (no favourable death rows to counter-test) is permanent for this signification and
stands recorded on every death-manner rule.


## DESIGN TICKET (2026-08-30, accumulating) — cross-signification pooling + the sparse-chart navamsa lift

The same verdict-routing shape has now been diagnosed on THREE independent error clusters, each
time with the cited mechanism FIRING and the verdict unmoved:

1. **Tennyson/Bose H2 speech** (engine afflicted, Raman favourable): wealth-tagged rules pool
   into the speech frame; the driver measured as weak-pillar + navamsa-weakens routing (the
   sig-precision probe changed nothing anywhere).
2. **Hyder Ali chart_19 / h9_02 H9 father** (engine favourable, Raman afflicted): the father
   frame holds 6 malefics vs 2 pooled FORTUNE benefics (zero father-own benefics), sparse
   pillars route to mixed, and NAV-CONFIRMS lifts to favourable. The reverse polarity of #1.
3. **Marie Antoinette H8 death** (fixed): a pooled longevity benefic vetoed the manner
   confirmation — resolved narrowly (span/manner separation) because the H8-OPENED decision
   documents that axis; measurement showed both wider forms break H6/H12/Lincoln/Hitler.

The pattern: rule_tags pooling and the V2 navamsa machinery are LOAD-BEARING in some frames
and inverting in others, and every narrow fix measured so far whipsaws when widened. Per the
north-star playbook this is design work with a PRE-MEASURED DISCRIMINANT, not tuning: any
future pass must (a) enumerate, over ALL confirmed rows, where pooled cross-sig evidence
decides the verdict and in which direction; (b) enumerate where the navamsa lift/drop decides
a sparse-chart contradiction; (c) propose per-axis separations only where a DOCUMENTED
doctrinal axis exists (the span/manner precedent), with the three-form measurement discipline
(sig-precise / asymmetric / status-quo) applied to each. Until then: the affected rows stay
documented limits, and their cited mechanisms stay recorded as corroboration.


## WS1 pass 5 (2026-08-30) — H9 father mechanisms + the Princess Beatrice basis correction

**h9_02's BASIS CONVERTED fresh-cast -> stated_positions** (reviewer SHIP, HIGH — every position
multiply corroborated in the prose). The modern ephemeris puts Mars at Aries 18.0, a FULL SIGN
from Raman's printed chart (his prose thrice: Mars in the 10th with Venus, hemming the 9th
"between malefics Rahu and Mars"). Raman's afflicted verdict is CONSTITUTED by the Taurus Mars;
scoring the modern sky against it measures ephemeris divergence, not fidelity — the conversion
follows the prime directive ("pin accuracy on his own published worked nativities"). The
nativity is PRINCESS BEATRICE (b. 14-4-1857 London, Queen Victoria's youngest; her father
Prince Albert historically died Dec 1861, Raman prints Feb 1861 — the print governs this axis).
Caveat recorded: the sign-midpoint Moon lands Purvashadha where Raman states Moola.

**H9.A.21 SHIPPED** (reviewer SHIP, HIGH): the Pitrukaraka Sun in the 9th CONJUNCT THE 8TH
LORD with the 9th hemmed by papakartari -> father's longevity curtailed. Chart 86 verbatim
(HTJAH-II:7965-7967 + :7984-7988 "together with"); ALL THREE legs proven load-bearing by
enumeration (two-leg fires the mixed chart_38; sans-8th-lord fires the favourable h9_10).
The June-deferred mechanism, closed.

**H9.A.22 SHIPPED** (SHIP-WITH-AMENDMENTS, applied): Rahu in the 9th -> early death of the
father, Hyder Ali verbatim — re-anchored to NH:5311-5312 (the anchor guard caught the golden's
line number landing blank in the unsplit source). CONTRARY VOICE recorded in the rule:
HTJAH-II:7843 reads the same placement favourably for father-FAME; re-open if a
fortified-father golden with Rahu in the 9th appears.

**Scored movement: NONE — and that is the honest result.** Both target rows (h9_02, chart_19)
now carry their cited mechanism as fired testimony, but the verdicts are routed by the
sparse-pillar mixed + navamsa-confirms lift over cross-signification-pooled benefics (chart_19:
6 malefics vs 2 pooled FORTUNE benefics -> favourable). That routing is the subject of the
consolidated DESIGN TICKET above — mechanism coverage first, routing design with a
pre-measured discriminant later. 284/397 holds; zero regressions; suite 5723 green.


## DESIGN TICKET — ENUMERATION COMPLETE (2026-08-30). P1/P3 closed-refuted; P2 pending review + sign-off

The prescribed measurement ran: three probes over all 397 confirmed rows, per-row diffs.

**P1 — full signification-precise bucketing: CLOSED-REFUTED at scale.** 284 -> 252 exact
(-32), real errors 46 -> 68. 46 rows move AWAY vs 14 toward. The cross-signification pooling
is globally load-bearing: H12 incarceration/left_eye alone loses 12 rows, H6 loses 7, H8
death loses Lincoln+Hitler, and the favourable side of H9 father loses 6. Even a
father-scoped narrowing loses more than it gains (4-ish toward vs 8 away within the father
sig). Re-open ONLY with a per-matter documented axis (the span/manner precedent) — never as
a blanket, at any scope. **P3 (both probes): -34 exact, dominated by P1's damage — same
verdict.**

**P2 — the confirmation varga may not testify FIRST: THE SURVIVOR, pending.** Scope: pillars
ALL unknown (sparse chart) AND both polarities fired (genuine contradiction) -> the D9 does
not move the resulting mixed. Measured: 284 -> 280 exact, within-1 351 -> 356, dist>=2
inversions 46 -> 41 — the exact B1-trade shape the MEASURED TRUTH lock blessed ("a strict
miss one step out is a contestable boundary call; an inversion is the engine saying the
opposite of Raman"). Five inversions dissolve (chart_46 education, chart_73 siblings,
Hyder Ali father, chart_48 dharma, Guru Nanak self); four exact favourables become boundary
calls (chart_38 + chart_56 wealth, chart_17 father, chart_14 body). Doctrinal axis claimed:
D9 is the CONFIRMATION varga ("rasi = promise, varga = fruit") — with no measured promise and
contradicted testimony, D9-first authority inverts its documented role. Engine-blind review
dispatched (the four cost-rows' own passages are the critical check: if Raman himself credits
the navamsa on any of them, that cost is real fidelity, not a boundary call). **Ships only
with USER SIGN-OFF per the B1 precedent (strict down / within-1 up / inversions down).**


## P2 SHIPPED, USER-SIGNED (2026-08-30) — the sparse-contradiction nav-neutral rule; 280/397 exact, 356/397 within-1, 41 inversions

The design ticket's survivor is law. When ALL strength pillars are unknown AND both polarities
fired, the D9 no longer converts the mixed to a pole verdict. Full record in the baseline
lineage note; the review packet's two amendments were applied before sign-off (the chart_17
row is the afflicted-side cost, and the doctrinal citation is the verbatim HTJAH-I:979-980 —
the "rasi = promise, varga = fruit" phrasing was a project gloss, NOT Raman's sentence, and
is retired from this rationale). The Guru Nanak disclosure stands verbatim in the code
comment: his dissolved inversion was produced by a D9 proxy reading the OPPOSITE sign of
Raman's actual navamsa sentence.

Net effect of the WHOLE design-ticket arc (enumeration + P2): real errors 46 -> 41, within-1
88.4% -> 89.7%, strict 71.5% -> 70.5% (deliberate, user-signed). P1/P3 are closed-refuted
with per-row receipts (46-away vs 14-toward; the pooling is globally load-bearing). The
remaining 41-row surface is the per-chart programme's steady queue.


## WS1 pass 7 (2026-08-30) — THE ABSTENTION SWEEP; 286/397 exact, 362/397 within-1 (91.2%), 35 inversions

The 41-row surface's workable cluster was the seven ABSTENTIONS (nothing fired, Raman
concluded). Seven single-citation rules shipped, six rows resolved exactly, zero regressions —
the largest single-pass gain since the measured ceiling, banked only after the adversarial
batch review returned 7/7 VALIDATED (5 SHIP + 2 documentation amendments, applied). Full
per-rule record in the baseline lineage. Highlights that must not be lost:

- **The Nanak save**: the first review run died on a session limit with one finding in hand —
  Guru Nanak as a near-counter-instance to the Hitler dictum. Raman's own sentence resolves it
  ("Mars, a yogakaraka — have become benefics by ownership", NH:3776-3790, split by a footnote
  splice) and the YOGAKARAKA GUARD now encodes it: Nanak spared, Hitler (maraka Mars) fires.
  Watch item: Raman's logic is "benefics BY OWNERSHIP" generally; the guard covers only
  yogakaraka Mars (conservative; no printed lagna-lord-Mars instance exists).
- **Shivaji lands mixed BY DESIGN**: his passage is two-sided in print, both testimonies are
  encoded (C.49/C.50), and the user-signed sparse-contradiction rule holds the contradiction
  at mixed — the first row RESOLVED BY the P2 machinery rather than despite it.
- **C.88's enumeration proof**: the "general" mutual-enemy-lords form is extensionally
  IDENTICAL to Wadiyar's own Cancer-lagna Sun-Saturn configuration (the only satisfiable
  case) — generalization with zero over-reach, playbook rule 3d working as intended.
- **Honesty amendments banked**: C.63's >= 3-benefic bar is a CONSTRUCTED BOUND (one printed
  instance per side, Marx/Nehru; Marx's own affliction is lord-reasoned, NH:6561-6563 — the
  bar is bounded, not derived); C.51's Vargottama leg is INFERRED (Raman prints it for a
  Rajayoga effect), kept because it narrows firing.
- Corroborations found by the sweep: Nero (Saturn-in-10th, NH:2739-2741), Prophet Mahamud
  (hemmed 4th -> illiterate, NH:2818-2819). H9.C.36 carries a do-not-promote note (weak
  second leg, fine for non-decisive testimony only).

Remaining error surface: 35 rows, singleton-dominated (H5 7 incl. the gate class, H1 6, H2 5,
H7 5, H10 4, H4 4). The abstention class is EXHAUSTED except chart_31 H10 (Shaw career — his
"Mercury, Saturn and Jupiter contributed to literary greatness" names planets without a
configuration; documented limit pending a closer read).


## WS4 CLOSED-MEASURED (2026-08-30) — the Astrological Magazine v75 seam is unusable as vendored

The planned extractor was NOT built, on measurement: the vendored v75 extract (3 chapters,
~50k lines) contains NO Raman-authored chart verdicts. Chapter 7 (the bulk) is reader
correspondence and third-party articles (e.g. D. S. Rao and H. R. Shankar debating two
charts at ch7:1650-1700); every "Dr. B. V. RAMAN" hit is a book ADVERTISEMENT or event
notice (verified at ch7:4137, 5084, 7186, 9437, 19840, 25002, 28818, 30751); chapter 3 is a
reprinted Western author's first-person epochal-horoscope text; references to "the
editorial" exist but the editorials themselves are not in the extract. Under the amended
confirmation rule (only what RAMAN concluded is confirmable) the seam's "489 printed
degrees / 54 birth lines" belong to non-Raman voices, and the OCR is materially worse than
the books (Cyrillic bleed-through, mangled planet names). RE-OPEN PATH: a fuller/cleaner
v75 (or other volume) scan that contains Raman's own editorials or signed chart-analysis
columns, ingested with PER-ARTICLE authorship attribution — the extractor design (NH
prose-positions format) remains valid for that day.


## CL-2nd wealth convergence: REFUTED BY ENUMERATION (2026-08-30) — the C.39 pattern does not generalize to wealth

Probe: >= 2 (and every higher bar) natural malefics occupying/aspecting the 2nd from Chandra
Lagna, over all 33 confirmed H2 wealth rows. Result: FAVOURABLE wealth charts routinely carry
heavy CL-2nd convergence — chart_38 (4 malefics, favourable), chart_64 (4, favourable),
chart_32 (3, favourable), chart_40/46/67 (2 each, favourable) — while the poverty example
chart_73 sits at 5. A >= 5 bar would fire on one chart with two favourables one step below:
naked overfit, refused. CONCLUSION, recorded as doctrine-shape knowledge: the Chandra-Lagna
convergence idiom is REAL for children (H5.C.39, five citations) and does NOT transfer to
wealth — wealth is yoga-driven (Dhana yogas and the maraka-association poverty operators
override placement convergence), consistent with the existing poverty-block design.

**NH.chart_73 (An Example for Poverty) H2 wealth: DOCUMENTED LIMIT (irreducibly
comparative).** Raman's own summing-up is explicitly holistic: "Study the horoscope
carefully and you will find the whole structure is rotten" — lord of Lagna strengthless,
two debilitated planets in mutual aspect, 2nd lord with Rahu under evil aspects, lords of
8/12/6/11 all contributing (NH:14846-14860). Each factor alone appears in favourable charts;
the condemnation is the synthesis. The one candidate single form ("the mutual aspect of two
debilitated planets ... suggest poverty") remains available for a future pass IF a second
printed instance surfaces; encoding it from one synthesis-verdict chart would claim his
mechanism where he stated a gestalt.


## H10.C.64 + the abstention class CLOSED (2026-08-30); 287/397 exact, 363 within-1, 34 inversions

Shaw's career — the last engine abstention — resolved by H10.C.64 (Mercury associated with a
yogakaraka 10th lord -> gains and public favour through writing, NH:7296-7300 verbatim).
Reviewer VALIDATED/SHIP; the generalization is licensed by Raman's own "a yogakaraka for this
horoscope" phrasing plus Chengiz Khan (NH:3319-3325) as a second printed firing instance.
**Recorded caveat (reviewer's): this gain is self-fulfilling by construction — the rule was
extracted from the chart it resolves, so it proves COVERAGE, not correctness.** The reviewer
also had to triangulate Shaw's Taurus lagna from four prose legs because his printed Birth
Details block is OCR-lost in the vendored NH — a data-quality note for any future work on
that chart.

**THE ABSTENTION CLASS IS NOW FULLY CLOSED**: every row where the engine said nothing and
Raman concluded carries its cited mechanism. Seven abstentions at the start of the day; zero
now.

## H1 LAGNA-AFFLICTION COUNT: REFUTED BY ENUMERATION (2026-08-30) — do not re-derive

The Nizam (NH.chart_55, "the affliction of Lagna lord by three malefics") and Farouk
(NH.chart_75, "the focussing of the influences of the three first-rate malefics on Lagna")
share an idiom with the SHIPPED contact-affliction twins (H4.C.48 / H5.C.40), so both count
forms were measured over all 34 confirmed H1 self/body/health rows:
- **A — >= 3 first-rate malefics contacting the LAGNA LORD**: fires on chart_33 (afflicted),
  chart_55 (the target), chart_18 (mixed) — and on **NH.chart_30, which Raman reads
  FAVOURABLE**. A printed counter-instance.
- **B — >= 3 first-rate malefics influencing the LAGNA**: fires on chart_75 (the target) —
  and on **NH.chart_57 (Sivananda, favourable body) and NH.chart_69 (favourable self)**. Two
  printed counter-instances, one of them a chart whose Lagna carries FOUR such influences
  and which Raman still reads as conferring "a sturdy physical frame" (NH:11962).
Neither count separates at any bar; raising the bar to 4 would fire on Sivananda alone among
favourables and on neither target. **The contact-count idiom that works for the karakas
(PutraKaraka, Matru-Karaka) does NOT transfer to the Lagna/Lagna-lord** — consistent with
Raman's H1 practice of reading the self holistically (constitution, dignity, yogas) rather
than by malefic tally. The five H1 rows stay documented limits; re-open only with a
non-count discriminant read from the charts' own prose.


## CORPUS GROWTH — the 3HC seam SURVEYED, registered, and handed off (2026-08-30)

With WS4's magazine seam closed (no Raman-authored verdicts), the library was re-surveyed for
un-mined Raman-authored sources carrying worked charts. **"Three Hundred Important
Combinations" is the seam**: ~57-63 chart presentations, of which **28 birth dates are NEW to
the corpus** (which stands at 262 nativities). Ashtakavarga-System has 25 chart refs; Hindu
Predictive Astrology, Manual of Hindu Astrology, Graha-Bhava-Balas and Studies-in-Jaimini
carry ZERO "Chart No." presentations and are rule-text only.

**Scan choice, measured**: FOUR 3HC scans are vendored and they DISAGREE ON CONTENT, not just
quality — `_complete` reads chart 2's time as "2-30 pm" where `_raman` reads "11-50", and its
dates are visibly corrupt ("3l- Z- 19t0"). The `_raman` scan is registered. (The `_hocr` copy
is a 3k-line fragment.)

**The gate validates end to end.** 3HC prints "Balance of <lord> Dasa at birth" for most
charts — which is exactly this project's existing extraction gate. Proof: Chart 1 is Raman's
OWN nativity (8-8-1912, Bangalore; it is also HTJAH-I Chart 10/11) and a fresh cast gives a
Mars balance of **6y 1m 5d** against his printed **6-1-6** — one day. The gate also works in
the negative: chart 2's printed time yields a Venus balance of 4y4m18d against a printed
6-7-15, correctly refusing an OCR-damaged time rather than ingesting it.

**Shipped now** (both regression-checked; HTJAH-I still finds its 248 presentations / 72
verified, and the extractor's 33 tests pass): 3HC registered in `_BOOKS`, and a
**MERIDIEM-DESTROYED FALLBACK** — where OCR eats the a.m./p.m. marker ("7-35 fi.m.", "2-30
j).m."), the parser now emits BOTH readings as sibling candidates and lets the printed dasha
balance arbitrate. This is safe precisely here and nowhere else: a 12-hour error moves the
Moon ~6.6 deg, far outside the 2.5 deg tolerance, so at most one branch can survive. It is a
general improvement that will help any future scan.

**HANDOFF — what remains for a dedicated session** (bounded, diagnosed, not speculative):
1. **Multi-line birth assembly.** 3HC's scan breaks lines mid-datum far more aggressively than
   HTJAH ("Chart No. 6 .—Born on" with the date on the NEXT line; latitude routinely one line
   below the time). 25 of 63 candidates fail with "no parseable Born line" and 11 more with
   "no latitude" purely from line-breaking. Fix: assemble the presentation window before
   matching, rather than matching per-line.
2. **A different verdict anchor.** 3HC has NO "Conclusion.—" paragraphs (0 found) — its
   readings are "In Chart No. N ..." paragraphs placed with the YOGA, often far from the
   chart's own presentation. They do carry confirmable conclusions with outcomes ("the native
   was the ruler"; "a Joint Secretary in the Government of India and has been getting on very
   well"; "there is an element of destructiveness"). The extractor's house-from-chapter
   attribution also does not apply — 3HC is organised by YOGA, not by house, so the
   signification must be read from the reading's own words.
3. **Expect a yoga-flavoured corpus.** Many readings confirm a yoga's manifestation rather
   than grading a house matter; those are worth ingesting for RULE LIVENESS even where they
   yield no scored verdict.


## ★ FERTILITY GATE — THE RECOVERY PATH IS STRUCTURALLY BLOCKED (2026-08-30, measured)

**This supersedes the recovery path recorded in "pass 3" and in the comprehensive plan's
sub-item 1a. That path — "encode the charts' actual printed drivers, then re-measure the
suspension" — CANNOT succeed, and the reason is architectural, not a shortfall of coverage.**

The drivers WERE encoded. Across today's passes the gate-carried charts acquired their cited
mechanisms: H5.C.39 (Chandra-Lagna malefic convergence, five citations), H5.C.40 (PutraKaraka
double contact), and now H5.C.41 (5th-lord-from-the-Moon in a barren sign). These rules FIRE
on the carried charts — chart_20, chart_31, chart_68, h5_02, h5_05, h5_09, h5_18, chart_37,
chart_22 all carry one or more. **And the suspension economics did not move at all: still
−13 exact / +1, net −12, identical to the measurement before any of them existed.**

**Why.** Clause 2 of `_decide` resolves a benefic/malefic contradiction by counting STRENGTH
PILLARS, never evidence. Measured on the carried charts with the gate off:
- h5_04: **5 malefic rules vs 3 benefic, 3/3 pillars strong → favourable**
- h5_12: 2 malefic vs 2 benefic, 3/3 strong → favourable
- chart_31: **5 malefic vs 2 benefic, 2/2 strong → favourable**
No quantity of cited malefic testimony can reach these rows, because the clause that decides
them cannot hear testimony at all. The fertility gate works precisely and only because it is
a DECISIVE override that bypasses clause 2.

**So the honest re-characterisation of the debt** (an improvement on the "accidental
correctness" framing, which over-stated it): the gate is not producing right-for-coincidental
reasons. The RIGHT doctrine is now present and firing on these charts — it simply is not
heard by the clause that decides them. The gate is compensating for a clause-2 blind spot,
not for absent doctrine.

**Both exits are already closed by measurement, so the gate STAYS:**
1. *Make the H5 children rules decisive* — refused twice on printed counter-instances:
   Queen Victoria for C.39 (multi-malefic CL convergence, "prolific motherhood") and the
   Dhana-Yoga chart for C.40 (double-contact PK, "fairly well disposed"). Decisiveness would
   invert Raman on his own charts.
2. *Change clause 2* — the MEASURED TRUTH lock names the pillar-preponderance clause as the
   one mechanism behind the dist-2 errors AND as a proven local optimum; the design-ticket
   enumeration (2026-08-30) then whipsawed on both wider forms (P1 −32 exact, P3 −34).
**Re-open condition (unchanged in kind, but now precise): a printed Raman passage that makes
one of these H5 mechanisms decisive in his own voice — i.e. a chart where he condemns
children on that mechanism alone against strong house/lord/karaka — or a clause-2 redesign
carrying its own pre-measured discriminant. Neither exists today.**

## H5.C.41 — the barren-sign mechanism (2026-08-30); ships GUARDED, scoring ZERO

Wells's third leg, the one neither C.39 nor C.40 covered. TWO citations: the general
definition is Raman's own — "Cancer, Scorpio and Pisces are fruitful and Gemini, Leo and
Virgo are barren" (Hindu Predictive Astrology ch.5, a prime-directive natal source) — and the
application to children is his own frame: "Mercury, the 5th lord FROM THE MOON, is in a
barren sign" (H. G. Wells, NH:8937-8938). The LAGNA-frame variant was measured (10 fires, 8 afflicted / 2 favourable) and deliberately
NOT encoded — Raman names the Moon frame, and the reviewer's corpus sweep confirmed "barren
sign" occurs exactly ONCE in all of NH (Wells, Moon frame); HTJAH-II uses the classes only
for the 11th and 12th houses, never the 5th.

**★ THE REVIEW CAUGHT A TEXTUAL CONTRADICTION, AND THE FIX COST THE ENTIRE GAIN — banked
anyway.** Unguarded, C.41 fired 9/35 (8 afflicted, 1 favourable) and resolved NH.chart_57 for
+1. The reviewer PROVED, without running anything, that the favourable fire was not an
ordinary outweighed testimony: Raman states of chart 106/h5_16 both that Mercury is the 5th
lord FROM CHANDRA LAGNA and that he occupies that same 5th — which forces the CL-5th sign
into {Gemini, Virgo}, both barren — and then reads it the OPPOSITE way, "From Chandra Lagna,
the 5th house is well fortified by the presence of Mercury, the 5th lord" (HTJAH-I:5933-5934),
on the corpus's strongest fertility chart (13 children). The rule fired BY CONSTRUCTION on the
placement Raman calls fortified.
The cited fix — a lord occupying its own house fortifies it, so suppress when the CL-5th lord
sits in the CL-5th sign — is Raman's general principle, not an h5_16 epicycle. Measured
effect: fires drop 9 -> 6, now **6/6 all Raman-afflicted** (a clean separation), and the
+1 on chart_57 is GIVEN UP, because chart_57's CL-5th lord (Sun in Leo) is also in its own
house — its affliction is real but comes from elsewhere, so the unguarded rule had it right
by coincidence. **Net ratchet effect: ZERO. Shipped regardless**: cited coverage that fires
6/6 correctly beats a +1 bought by a fire Raman's own text refutes (playbook rule 4 — a corpus
gain is not evidence of fidelity; and the earlier defence "it's already a miss so this cannot
worsen it" was struck as the named evidence-redundancy blindness).
**KEETARASI deliberately not encoded — MY PREMISE WAS WRONG AND THE CORRECTION STRENGTHENS
THE DECISION.** I recorded that no general definition existed; Raman defines it in his own
hand: "Keeta Rasis.—These are insect signs. In the whole of the Zodiac, Vrischika (Scorpio) is
the only Keeta Rasi" (Graha and Bhava Balas ch.9 §130; corroborated Prasna Marga vol.2 ch.32).
So "both attested instances are Scorpio" is a NECESSITY, not a coincidence — and the
definition is a bhava-bala insect-sign taxonomy with zero fertility content. Raman applies the
class to three unrelated matters across two charts: children (Marie, NH:5835), physical
APPEARANCE (Marie again, NH:5819, "her thick eyebrows and the light russet hair"), and
IMPRISONMENT (Nehru, NH:12439-12441). Do not reopen on rediscovering the definition — the
definition IS the reason not to encode.
**Recorded at the constant**: HTJAH-II runs a WIDER fertile/barren scheme ("Libra, a fruitful
sign" :14888; "the twelfth house is a barren sign Aries" :18217) for the 11th/12th houses. The
encoded set is the strict HPA subset — right here, but any future 11th/12th reuse must adopt
HTJAH-II's wider set or silently under-fire.


## STALE-TODO AUDIT (2026-08-31) — 46 of 87 parked rules are now buildable

The full `TODO(predicate)` surface was audited against what has actually shipped. Of 87
distinct parked rules (99 grep hits): **46 STALE-NOW-BUILDABLE**, 15 PARTIAL, 4 STILL-BLOCKED,
22 DEFERRED-BY-DESIGN. The ranked table with per-rule blockers, unblocking primitives and
one-line predicate sketches is in the audit output; the headline findings:

- **`_resolve_planet` already resolves `"LORD_OF:n"`** as a subject for `VargaDignity`,
  `Vargottama`, `NeechaBhanga`, `TaraOf` and as an origin for `InHouseFrom`/`InVargaHouseFrom`.
  Every TODO naming "lord-aware varga dignity" is stale against a gap its own docstring says
  it closed.
- **306 of 346 golden records carry `birth`**, so `chart.upagrahas["Mandi"/"Gulika"]` and
  Shadbala are live on 88% of the corpus — five parked Mandi rules have a shipped precedent
  (`_SaturnOrMandiOn12th`).
- **`EvalContext` holds a chart and nothing else** — every "Phase-F dasha timing" TODO is the
  atemporal-verdict design boundary, NOT a missing primitive. 13 rules classified so.
- **The single highest-leverage genuine blocker is the D60 named-class table**
  (Ghora/Rakshasa/Kulaghna/Devaloka…), absent corpus-wide, capping 6 rules. That is new
  doctrine-import work, not a stale TODO.
- Recommended order (densest first): the H2 block (8 rules on a house carrying 5 dist-2
  errors, every blocker already local to the file), then H7/H10, then H4.C.24 (moves BOTH
  poles), then the Mandi sweep.

**H2.C.45 SHIPPED** — movable Lagna with Saturn or Ketu hemmed by malefics -> poverty
(HTJAH-I:2532 region). The "SignModality" blocker was gone twice over: `sign_attributes.
modality` ships AND this file already carried its own movable-sign constant. Fires 2/242;
zero ratchet change (no scored H2 row on either chart) — recorded coverage.

**H9.B.23's navamsa leg: BUILDABLE, IMPLEMENTED, MEASURED, HELD.** The audit called it the
clearest stale claim in the file set and it was right about the blocker — `VargaDignity(
"LORD_OF:9","D9",{"debil"})` compiles today and is verbatim faithful to Raman's "debilitated
(in sign or Navamsa)". Measured: the rule's fire rate climbs to 123/242 and NH.chart_57's
fortune INVERTS favourable -> afflicted against him (287 -> 286 exact, inversions 34 -> 35).
Held under the net-negative rule. Diagnosis recorded in the rule: his sentence is a
three-part severity conjunction ("debilitated ... / weak / in a malefic shashtyamsa"), and
adding one part as a bare OR-disjunct to an already-broad rule encodes his VOCABULARY without
his THRESHOLD. Re-open with the 'weak' gate (effective_strength) applied TOGETHER with the D9
leg, not beside it. **This is why the audit's rankings are a queue to measure, not a queue to
ship.**

## ASHTAKAVARGA — SURVEYED, AND ITS ONE TESTABLE RULE IS REFUTED (2026-08-31)

The Ashtakavarga System's "Chart No." references are BINDU DIAGRAMS (the Sun's ashtakavarga
etc.), not nativities — **no golden-corpus growth is available there**. The real gap is that
the engine COMPUTES ashtakavarga (`primitives/ashtakavarga.py` + `_pinda` + `_reduction`,
`bindus_in_house`) while **no doctrine rule consumes it**.

ASP does carry genuine interpretive bindu rules, and the one that targets a house on the
current error surface was measured: ch.5 #9, "The waning Moon in Lagna associated with 1, 2, 3
or no bindus ... there is also a likelihood of the mother's death." Only two confirmed H4
mother rows have the Moon in Lagna, and the rule fires **exactly backwards on both**: Shaw
(NH.chart_31) has 3 bindus and Raman reads his mother FAVOURABLE ("gave good longevity to his
mother"), while Thyagaraja (chart_23) has 6 bindus and is AFFLICTED. Not shipped.
Note the direct collision: Shaw is the very chart where Raman credits the Moon in Lagna
Vargottama for a powerful mother (H4.C.51, shipped 2026-08-30) — his own applied reading and
ASP's bindu warning point opposite ways on the same placement, and the applied reading is the
one with a printed verdict attached. **General lesson recorded: ASP's bindu thresholds are not
corroborated by Raman's own worked charts in this corpus; any future ashtakavarga rule must be
enumerated against the goldens before encoding, never taken from the manual on faith.**


## H2 STALE-TODO BATCH (2026-08-31) — four more rules un-deferred; zero scored movement

Working the audit's #1 recommendation (the H2 block: densest buildable set, on a house
carrying 5 dist-2 errors). Four rules moved descriptive -> evaluable, all firing, ratchet
unchanged at 287/397:

- **H2.C.13** family (HTJAH-I:2452-2453) — 2nd lord with benefics in a kendra, OR the 2nd
  house wholly benefic in association and aspect. Blocker "LordInHouseClass + benefic
  conjunction" was never real: a kendra test is `rasi_house in (1,4,7,10)` and the benefic set
  is a module constant. Fires 67/242. The "wholly benefic" leg returns False on an UNTOUCHED
  2nd rather than vacuously True — an untouched house is not "all good association", it is
  none.
- **H2.C.15** speech (HTJAH-I:2456-2458) — Jupiter in Lagna with Saturn in the 8th, or Jupiter
  in a kendra with the Lagna-lord or Mercury exalted. `C.LordHasDignity` was the whole
  blocker. Fires 7/242. These are Raman's 2nd and 3rd paths to the mathematician; C.14 was
  already carrying only the first.
- **H2.C.33 / H2.C.34** wealth (HTJAH-I:2482-2488) — the "NavamsaDispositor" pair.
  `dispositor.navamsa_lord_of` IS the named primitive, and Raman spells the construction out
  with his own worked example ("Aquarius is Lagna and Saturn occupies Taurus in Navamsha ...
  aspected by Venus, who is the lord of the Navamsha occupied by lord ascendant"). Fires 3
  and 13.

**Zero rows moved, and that is the expected shape**: these are benefic wealth/family/speech
rules, while H2's live errors need either benefic weight the routing cannot hear
(chart_25/chart_33 speech — diagnosed 2026-08-30 as weak-pillar + navamsa-weakens at the
measured local optimum) or malefic weight (chart_44), and chart_73 is the recorded gestalt
limit. Banked as COVERAGE: the doctrine is now encoded and firing rather than parked, which
is the point of the audit — not every un-deferral is a ratchet gain, and one that fires
correctly on 90 chart-instances while moving no scored row is still the engine knowing more
of what Raman wrote.

**Process note worth keeping**: a patch of mine asserted a "copy-paste bug" in C.13's
`fortified` text. There was none — I had misread interleaved `sed` output that spliced two
records. The anchored assertion caught it before the edit landed. Anchored patches earn their
keep on exactly this class of confident-but-wrong edit.


## H7 STALE-TODO BATCH (2026-08-31) — one shipped, two held; the audit is 3-for-7 on shipping

Continuing the audit queue into H7 (5 dist-2 errors). All three parked rules WERE buildable
exactly as the audit said — and only one survived measurement. Ratchet unchanged, 287/397.

**H7.C.5 SHIPPED** (HTJAH-II:364-366) — 7th lord and Venus in even signs, the 7th an even
sign, and the 5th and 7th lords neither combust nor otherwise weak -> a good wife and
children. The "combust+weak gate" was `C.Combust` plus
`effective_strength(...).decisively_weak`, both long shipped. Fires 17/242. The strength leg
is None-safe: on a sparse chart an UNKNOWN strength is not treated as weakness, so the rule
falls back to the combustion leg rather than silently asserting.

**H7.C.8 HELD, measured net-negative.** `C.Or(_SeventhSignIsBenefic(),
_VenusAsSeventhLordAspectedByBenefic())` is verbatim HTJAH-II:370-372 and compiles today —
but it fires **110/242 (45%)**, because seven of the twelve signs are benefic-owned, and it
lifts h7_06's spouse reading mixed -> favourable against Raman. Same shape as H9.B.23's hold:
a generic placement indication carries his VOCABULARY but not his WEIGHT — he offers "the 7th
house be a benefic sign" as one testimony among many, and as an unqualified benefic in a
pooled bucket (`spouse` pools `marital_happiness`) it out-votes specific afflictions. Re-open
only with a strength or blemishlessness qualifier, per the blemishless-Venus floor precedent.

**H7.C.35 STAYS DESCRIPTIVE — on doctrinal grounds that PRECEDE the measurement.** It is
buildable (two `LordHasDignity({"debil"})` plus navamsa lordship off `PlanetPos.navamsa_sign`)
and was encoded and measured (28/242). But "only one marriage is possible" / "the native will
marry only once" is a marriage-COUNT statement, not a judgment of the spouse or of marital
happiness. **Marrying once is neither favourable nor afflicted** — Raman reads single
marriages both ways elsewhere. Encoding a count as a benefic that lifts spouse QUALITY is the
category error the audit's own taxonomy defers (H3.C.15-17, H11.C.40: "numeric count output,
not a boolean gate"). Re-open only with a marriage-count signification to route it to.

**Running tally on the audit's 46 buildable rules: 7 attempted, 3 shipped (H2.C.45, the H2
C.13/C.15/C.33/C.34 four, H7.C.5), 3 held on measurement (H9.B.23 leg, H7.C.8), 1 refused on
doctrine (H7.C.35).** The pattern is now clear enough to state as guidance for whoever
continues: **the audit's "buildable" is a claim about the ALGEBRA, never about the DOCTRINE or
the weight.** Broad single-placement indications (a benefic sign, a lord's varga debility) are
the ones that fail — they are real sentences of Raman's that he weighs among many, and the
judge has no way to weigh them. Narrow multi-leg conjunctions (C.5's four legs, C.45's three)
are the ones that ship. Prefer the latter when picking the next batch.


## H10 SKIPPED WITH REASON + H4.C.24 SPLIT (2026-08-31)

**H10's two "buildable" rules cannot move any verdict, and the audit's ranking missed it.**
Both H10.C.15 and H10.C.44 carry `polarity="neutral"` and are CATALOGUES: C.15 maps
Atmakaraka/Karakamsa configurations to KINDS of profession ("Sun-AK aspected by Jupiter ->
temple, Saturn -> vile work, Rahu -> foreign concerns, Mercury -> judiciary"), and C.44 maps
configurations to ascetic/Jeevanmukta/renunciate. Neither says a career is GOOD or BAD, which
is the only thing a verdict is made of. The audit ranked them highly on error-surface
relevance (H10 carries 4 dist-2 errors) — but a neutral rule can only rescue an ABSTENTION,
and H10's three abstentions were already closed (C.62/C.63/C.64 on 2026-08-30). The three
remaining H10 errors are all wrong-DIRECTION rows, which no neutral catalogue can touch.
Skipped, not attempted. **Generalisable check for the next batch: read `polarity` before
reading the TODO — a neutral rule is a classifier, not a verdict.**

**H4.C.24 SPLIT into two scoped rules.** The record bundled SIX distinct sentences of Raman's
under one neutral polarity — royal favours, mother's affection, an army commission, loss of
lands, sinfulness, drowning — which is why it could never be made evaluable as a unit: the
outcomes carry different significations AND opposite poles. Two were extracted:
- **H4.C.52** (mother, benefic, fires 7/242): "He wins the affection of mother if lord of
  Lagna and the fourth are friendly, and are otherwise beneficially disposed"
  (HTJAH-I:4228-4229). Friendship reads `dignity.compound_relation` in BOTH directions —
  "are friendly" is mutual — and "otherwise beneficially disposed" is read conservatively as
  neither lord carrying a natural-malefic contact.
- **H4.C.53** (property, malefic, fires 1/242): "The person loses lands by royal or
  Government orders if the lord of the fourth is neecha with Sun" (HTJAH-I:4219-4220). Two
  legs, both his. Scoped to `property`, the matter the sentence is about, not the bundle's
  `happiness`.
What remains in C.24 is honestly still blocked: the royalty/army sentences want a strength
gate and have no status/career key on H4, and the sinner/drowning pair are life-event
readings with no signification to route to.

Zero ratchet movement from either (287/397 holds). **Tally: 9 of 46 attempted — 5 shipped,
3 held on measurement, 1 refused on doctrine, plus 2 skipped unattempted on the neutral-
polarity check.**

**A near-miss worth recording**: while reading C.24 I nearly reported its drowning summary as
a text bug ("weak Lagna-lord in a watery 4th" vs Raman's "the fourth lord is weak,
debilitated and joined by evil planets and LAGNA is in a watery sign"). It is not a bug —
HTJAH-I:4221-4223 contains TWO drowning sentences, and the record summarises the second one
("The person will be drowned if the weak lord of the Lagna is in the fourth, which should be
a watery sign"). This is the second time in two days that a confident "found a bug" reading
of these records was wrong on a closer read. **When a record's summary looks wrong, read the
FULL source paragraph before claiming it — Raman routinely states two near-identical
variants in consecutive sentences.**


## THE GENERAL-READING SLOT (2026-09-01) — Raman's base reading was being shown as an affliction

Opened by the owner's question: *"why is it always good or bad? Can't we use whatever Raman
has written — find out how."* The answer turned out to be an encoding defect, not a product
gap, and it was found by asking what the corpus contains rather than what the judge computes.

**The defect.** `RuleRecord` had exactly two result-text slots, `fortified` and `afflicted`.
But Raman's "Results of Lord of the Nth House Occupying Different Houses" sections are written
in TWO paragraphs of a different kind: a GENERAL, unconditioned reading, then one conditioned
on FORTIFICATION. An engine-blind `bphs-doctrine-reviewer` counted the openers in House 1 --
**nine fortification openers, zero affliction openers** (HTJAH-I:1000, 1012, 1019, 1026, 1035,
1043, 1054, 1059, 1065). He gives no afflicted reading for those placements at all, and says so
himself at HTJAH-I:1003-1007: *"the combination is of general application... The same rules
apply to all Bhava."*

With nowhere else to put it, the corpus had filed the general paragraph under `afflicted`.
`rule_firing._branch` picks the slot by the house-lord's Shadbala, so **a weak-lord chart was
shown Raman's BASE reading under an "afflicted" heading.** On H1.L.3 that is *"highly
courageous, fortunate, respectable, two wives, intelligent, happy"*; on H1.L.9 *"generally
fortunate, protector of others, religious... good orator... and rich"* — blessings presented
to the reader as afflictions. The defect stayed invisible for years because on H1.L.5 and
H1.L.7 the general reading happens to read grim (*"the first child does not survive"*, *"the
wife does not live"*), so nine of twelve rows looked plausible.

**The repair.** `RuleRecord.general` (optional, defaulted, read by NO judge code). The reviewer
ranked a third slot most faithful over the two fallbacks: Raman's doctrine here is genuinely
three-valued (base / modulated-up / modulated-down), and two slots cannot hold it without
either fabricating an afflicted reading he never gave or discarding the base reading he
insisted on. Surfaced by `house_general_readings()` in all four renderers.

**SCOPE WAS SET BY REVIEW, NOT BY SWEEP — this is the load-bearing part.** Two engine-blind
reviews classified all twelve source sections. A blanket application of the House-1 finding
would have destroyed real doctrine in more than half of them:

| Family | Houses | Action |
|---|---|---|
| general + fortified, NO afflicted branch | H1 | fixed (12 rules) |
| MIXED — general + fortified, plus some genuine afflicted clauses | H2, H3, H8, H11, H12 | H8/H11/H12 fixed per-rule; **H2/H3 OPEN** |
| general ONLY, encoder split one sentence by sentiment | H4 | **OPEN** (H4.L.1/2/4) |
| EXPLICIT-AFFLICTED — Raman does give an afflicted reading | H5, H6, H7, H9, H10 | untouched, pinned by test |

Shipped: **list A** (10 rules, whole slot relocated) H8.L.2, H8.L.11, H11.L.1, H11.L.12,
H12.L.4/5/7/9/10/11; **list B** (12 rules, slot SPLIT so the genuine afflicted clause
survives) H8.L.1/3/4/5/6/7/10, H10.L.12, H11.L.7/8, H12.L.2/3. 34 rules now carry a `general`
slot. `[ratchet]` 287/397 unchanged throughout — text moved between presentation slots;
`polarity` decides the verdict and `_branch` reads neither the new field nor any edited
condition.

**Caught by review, would have been damage:**
- **H1.L.1's slot ENDED with a genuine afflicted clause** (HTJAH-I:1088-1089, *"If the ascendant
  lord is posited in the Lagna subject to evil combinations, the native will not be physically
  happy"*). A whole-slot move would have deleted it. Preserved and pinned.
- **H11.L.8's `fortified` held "rich at birth"** — the opening subordinate clause of the single
  sentence *"The native though rich at birth suffers many calamities"*, cut mid-sentence.
- **H12.L.9's two slots split one sentence at its comma**: *"Honest, generous and large-hearted
  he may not have any spiritual leanings."*

### STILL OPEN — do not treat this arc as finished

1. **H2 and H3** (first review, MIXED): relocate the general readings but PRESERVE the genuine
   afflicted clauses at HTJAH-I:2360, 2373-2378, 2408, 2420-2421 (H2.L.6, H2.L.12) and
   HTJAH-I:3376-3377, 3397 (H3.L.6, H3.L.9).
2. **H4** (HTJAH-I:4145-4188) and **H9.L.12**: the *sentiment-split* variant — one unconditioned
   sentence cut across both slots (H4.L.2 *"highly fortunate, courageous, happy"* / *"sarcastic
   nature"*; H4.L.4 *"sensual"*). Same root cause, different shape.
3. **★ H10.L.1 — UNSOURCED TEXT, INVESTIGATE BEFORE ANYTHING ELSE.** Its `afflicted` reads
   *"weak Lagna and 10th lord → modest attainment; little distinction"*, and the reviewer could
   not find that statement at HTJAH-II:9459-9465 or anywhere in the tenth-lord section, which
   is wholly unconditioned and wholly favourable. It is neither Raman's general reading nor a
   genuine afflicted one and appears **encoder-supplied**. Deliberately NOT relocated: moving
   it would have laundered unsourced prose into the general slot. A test pins it untouched.
   If confirmed unsourced it must be deleted, not moved — and the same provenance question
   should then be asked of the rest of the corpus.
4. **Misfiled but NOT general readings** — conditioned on a CONFIGURATION or a middling-strength
   branch, so outside this defect and explicitly not to be swept up by it: H12.L.1 (Lagna/12th
   exchange → miser, HTJAH-II:16135-16136), H12.L.3 (2nd-lord + Jupiter/9th-lord aspect → more
   than one wife, 16157-16159), H10.L.10 (three planets conjoin → ascetic, 9552-9554), H6.L.9
   (Raman's third *"If moderate"* branch, 6048). H12.L.1's *"This also indicates imprisonment
   and living abroad"* (16134) is UNDETERMINED — the referent of "This" is ambiguous.
5. **A different fidelity gap, noted in passing by the reviewer:** Raman conditions most H8
   lord-in-house readings on the 8th lord *joining that house's own lord* (*"If the lord of the
   8th house joins the 4th lord in the 4th house"*, HTJAH-II:2940), while the encoded condition
   is the bare `C.LordIn(8, N)`. That is over-firing, and it is a CONDITION defect, not a slot
   defect — it would move the ratchet, so it needs measurement before any change.

## THE NON-GRADED LANE (2026-09-01) — what the corpus holds that a grade cannot carry

Measured over all 871 `RuleRecord`s: **611 (70%) carry non-graded content** — a kind, count,
attribute or circumstance rather than a verdict; ~175 are non-graded ONLY. Largest categories:
character (210), profession (163), a named disease or body part (144), aptitude (85), place
(80), counts (69), manner of death (45). Four independent chokepoints kept it off every
surface, all now closed:

1. **`SignificationVerdict.metadata` was computed and discarded.** The canonical chart produces
   **165 pairs and rendered exactly ONE** (`catastrophic_gate`): `report_html` read none, and
   `report_json._proforma_dict` dropped them before the interactive page could see them. Now
   rendered by `house_indications()` in all four surfaces.
2. **`house_longevity_pointer` made a promise the product did not keep** — it told the reader
   the 22nd-decanate detail "is carried in the Longevity chapter below", where only the
   drekkana LORD ever printed. `longevity_decanate_cause()` prints the class; the pointer is
   reworded to what is now true.
3. **97 `kind="descriptive"` rules never execute and reached no one.** `rules.fires()` and
   `rule_firing.fire_rules` both skip a `condition=None` rule, and nothing else read them —
   despite the class docstring promising each is "surfaced with its citation when a placement
   holds". `descriptive_house_rules()` surfaces them, framed as doctrine ON RECORD and
   explicitly *"not yet computed... listed, not applied to this chart"*, with a test pinning
   that wording: an unevaluated rule shown as a finding would be a false claim about the
   engine's own work.
4. **The chief-combination cap.** `per_sig=3` with `fired_neutral` ordered last. MEASURED
   before assuming: only **3 rows** are actually lost on the canonical chart, so the cap was
   never the main loss — the 97 were. `house_further_combinations()` shows the remainder;
   `house_chief_combinations` is deliberately NOT modified (3 call sites, 2 tests pin it).

**Two latent defects the new surfaces exposed, both silent until the data was finally rendered:**
- `EventWindow` labelled the birth Mahadasha from its NOMINAL start, which precedes birth by
  the elapsed balance — *"Mercury(maraka) 1978-1995"* on a 1990 birth. Astronomically right,
  but false as a reading. Clipped at the source in `significator_dasha_windows`. Note
  `test_no_pre_birth_activation_windows` was written to catch exactly this and was PASSING —
  the un-clipped window simply never reached the one surface it inspected. A vacuous pass is
  indistinguishable from a real one in a test report.
- Three logic glyphs in rule maintainer notes (`∧` in H11.C.34, `↔` in H12.L.1/H12.C.A18) had
  no entry in `render._REPL` and printed as `?` mojibake the moment those rules first reached
  a reader. `∨ ≠ ≤ ≥` added alongside them.

**Explicit non-goals, held to** (from the approved plan): `polarity` was NOT re-modelled (it
feeds `_bucket_fired` and the ratchet); NO rows were added to the significations table
(`significations.py:61-71` records the measured failure — ungraded rows dropped cross-layer
agreement 0.475 -> 0.439 and were reverted); `_decide` untouched.


## PROVENANCE AUDIT (2026-09-01) — one fabrication in 185 rules, and it is fixed

Triggered by a reviewer's aside that H10.L.1's `afflicted` text could not be found in Raman.
Because a citation is what this engine's whole credibility rests on, that got its own
engine-blind audit rather than a quiet fix.

**H10.L.1 — CONFIRMED ENCODER-SUPPLIED. Removed, not relocated.** Its slot read *"weak Lagna
and 10th lord -> modest attainment; little distinction"*. The auditor read HTJAH-II:9456-9465
in full and searched BOTH volumes: "modest" and "little distinction" appear nowhere, and the
cited paragraph is four unconditioned FAVOURABLE sentences with no conditional clause of any
kind. The forensic signature is a **cross-house formula transfer**: Raman does use a
strong/middling/weak ladder for a lord in Lagna -- but only for the 4th lord (HTJAH-I:4151)
and the 11th (HTJAH-II:14259), never the 10th. The encoder generalised a real Raman idiom onto
a placement where he withholds it, then translated a wealth ladder into a career register.
That is why it read plausible and survived.
The `fortified` half is sourced verbatim, so the rule was REPAIRED, not deleted: deletion
would discard genuine doctrine to punish an invented sentence, and demotion to
`kind="descriptive"` would stop it firing and take the sourced reading down with it. Both of
those would also move the ratchet; clearing the text slot does not, and did not.

**THE RATE: 185 rules verified across all 12 packages, both volumes, all three groups --
174 SOURCED, 9 PARAPHRASE-OK, 1 MISCITED, 1 UNSOURCED (0.5%), 10 UNVERIFIED.** The auditor ran
a second, adversarial arm aimed squarely at the defect's own phrasing (43 `weak`-token hits
across the whole tree, hand-checking every nearest sibling of H10.L.1) and found **zero
further fabrications** -- including in the two graded-ladder sentences the defect was probably
copied from. Read the rate honestly: Arm A cluster-sampled by SOURCE SECTION, so 185 rules are
only ~15 independent spans and ~7 of ~30 modules. `combinations_core.py`, `constitution.py`,
`moon_mind.py`, `sign_afflictions.py`, `navamsa_qualifiers.py`, `from_karaka.py` and ~200
`combination` rules were NOT sampled, and the `combination` modules are hand-composed from
prose rather than transcribed from a table -- the likeliest place to find more.

**H3.L.11 — MISCITED, corrected.** Cited HTJAH-I:3351, which sits inside the THIRD-house
paragraph and supports only its `fortified` half; the afflicted text is Raman verbatim at
3405-3407. The tell: every other row in that module cites monotonically increasing lines and
L.11 alone jumped backwards 54 lines.

**A method note worth keeping.** The auditor's explicit recommendation: **do NOT sweep for
"afflicted slots that look invented" with a lexical heuristic.** The phrasing that most
resembles the defect (`weak ... -> poor/modest/limited`) is Raman's own graded idiom in every
other instance, so a regex sweep would be ~98% false positives -- and a false accusation of
fabrication is as damaging as a missed one. The reliable unit is what Arm A used: read the
source section once, then match every row in the module against it.

**Three records carry honest encoder meta-text where Raman gives no favourable variant**
(H3.L.8 "no specifically favourable variant given for this placement"; H4.L.8 and H4.L.12 "no
specific benefit noted"). The auditor rated these NON-DOCTRINAL and correct behaviour -- they
disclose the gap instead of filling it, and are the direct contrast that makes H10.L.1 stand
out: three encoders met the same "Raman gives no reading here" situation and wrote a
disclosure; one wrote a reading. (H4.L.8/H4.L.12 have since been given Raman's own general
text, because the meta-text was DISPLAYING to readers as the strong-lord reading; the
disclosure survives as a code comment.)

## HOUSE 4 — the general-only section, an INVERSION, and a positive gloss (2026-09-01)

HTJAH-I:4149-4188 has **zero fortification openers and exactly one affliction opener**
(4181-4182, H4.L.10). Raman closes the section saying so: *"these combinations are very
general and they should not be applied verbatim. The good and bad nature of results... becomes
augmented or minimised according to the strength or weakness of the fourth lord"* (4190-4193).
Each placement is ONE unconditioned sentence, and the encoder had split most of them across
the two slots BY SENTIMENT -- cutting Raman mid-list, and in H4.L.4 filing his own final
adjective ("sensual") as if it were an affliction. All twelve now carry `general`.

*** H4.L.3 was INVERTED, not merely mis-slotted -- the most damaging single defect found in
this arc.** Its "very little immovable property, even loss of meagre possessions" comes from
the Satyacharya note at HTJAH-I:4193-4196, whose condition is the OPPOSITE of affliction:
*"when the fourth lord, SUBJECTED TO SUBHA VARGAS OR FAVOURABLE ASPECTS, is in the third, one
acquires very little of immovable property..."* Raman's entire point is that even a
WELL-DISPOSED 4th lord in the 3rd gives little property. Filed under `afflicted`, the encoding
taught the reverse of the sentence's reason for existing. Moved to `fortified`.

**H4.L.6's `fortified` held "active, prone to roaming"** -- a positive re-spin of Raman's *"He
will always be roaming about"*, with "active" appearing nowhere in the section. Raman gives no
favourable variant for this placement. Two reviewers disagreed on whether to call this a
fabrication or a loose paraphrase; the source was read directly and the disagreement is moot
either way, because the whole paragraph is general and the slot was wrong regardless.

**Not encoded, deliberately:** Raman's three-way modifier at 4196-4198 ("moderately afflicted
-> evil tempered; strongly afflicted -> intensification") is SECTION-WIDE, not per-placement.
And H4.L.1's genuine strength branch is strong/MIDDLING/weak -- the middling grade has no slot
and is named in the `general` text rather than silently folded into either branch.

### STILL OPEN after this arc — a full per-rule map exists, apply it next

An engine-blind review produced an exact fragment-level repair map for **House 2 (12 rules)
and House 3 (12 rules)**, plus **H9.L.12**, which is the lone sentiment-split in an otherwise
correctly-encoded House 9 (its paragraph at HTJAH-II:7389-7394 has no opener of either kind;
the encoder cut Raman at his own "but", filing "religious and noble" as fortified and "always
in want" as afflicted). Tallies from that map: H2 = 5 RELOCATE-WHOLE (L.1/3/5/7/8), 5 SPLIT
(L.2/4/6/10/12), 1 SENTIMENT-SPLIT (L.9). H3 = 4 RELOCATE-WHOLE (L.1/7/8/11), 2 SPLIT (L.6/9),
5 SENTIMENT-SPLIT (L.2/4/5/10/12), 1 LEAVE (L.3).

Three findings from that map that are NOT slot defects and must not be swept up:
- **H3.L.3's three sibling-death clauses are keyed on PLANET IDENTITY** (which planet happens
  to be the 3rd lord -- Mars/Saturn/Sun, HTJAH-I:3352-3354) with no affliction test anywhere.
  Firing them off an affliction predicate is wrong in BOTH directions.
- **H2.L.4's affliction is of the 4TH lord, not the 2nd** (HTJAH-I:2360). If the slot's
  predicate tests the rule's own house lord, it fires on the wrong thing.
- **H2.L.8's STRONG branch is ADVERSE** ("hardly any earnings, but inherited or accumulated
  wealth will disappear", 2392-2393). Any renderer that labels `fortified` as the good reading
  mis-presents this one.

Plus content dropped from the encoding entirely, relevant to the report-completeness lock:
H2.L.1's "becomes no doubt wealthy" (2325), H2.L.4's explicit carry-over "The above results
will apply in addition to the following" (2355), H2.L.9's "Skilful" (2395), H3.L.9's "Long
journeys. Sudden and unexpected changes in life." (3394-3395). And two provenance mismatches
(real Raman, wrong location): H2.L.2's `fortified` is sourced from 2506, a dasha-timing list
outside the lord-in-house table.


## INDICATION CORROBORATION (2026-09-01) — measured, and the answer is NULL

The non-graded lane has no ordinal to score against, so without a check of its own it would
have shipped unmeasured -- the one thing this project does not allow. `tools/raman_saab/
indication_corroboration.py` closes that gap by asking a narrow, falsifiable question: do
distinctive terms from an emitted indication appear in Raman's own `verdict_prose` for the
SAME chart and the SAME house? If the engine says the 10th indicates `judiciary` and his prose
for that chart says "a Judge", that is corroboration.

**★ THE RESULT: 284/8666 = 3.3% corroborated, against 2.7% (232/8541) on deliberately
MISASSIGNED prose. Lift +0.6%. VERDICT: NULL.** The real rate does not clearly exceed the
baseline, so what the matcher is measuring is shared astrological vocabulary, not
corroboration. The tool says so on its own face and refuses to present the raw 3.3% as a
result.

**The null arm is the whole point, and it is not optional.** A corroboration rate quoted alone
is uninterpretable: astrological prose shares so much vocabulary that any generous matcher
"corroborates" everything. Misassignment is deterministic (each chart's indications are scored
against the NEXT chart's prose), so the baseline is reproducible and cannot be reseeded into a
flattering value -- a test pins that. The matcher's own thresholds were set BEFORE any result
was looked at (a term is DISTINCTIVE at document-frequency <= 10% of prose docs; a row needs
two distinctive terms, or one rare term at <= 2%) and are reported alongside the number they
produced.

**This is the correct outcome, not a defect.** Raman's prose argues the GRADE far more often
than it names the KIND, so most indications have nothing in his commentary to match against.
The finding is consistent with the project's standing Measured-Truth position: the engine is a
faithful scholarly instrument, and every axis on which we can check it is reported honestly,
including the ones that come back null.

**How to read it beside the other two axes -- never averaged, never merged:**
- textbook fidelity (golden ratchet): 287/397 exact, 363/397 within-1, 34 inversions
- real-outcome generalization: NULL (astrobank, 22,177 charts)
- indication corroboration: **NULL** (this measure)

**What would change the verdict.** Not a looser matcher -- that would raise both arms
together. Only a genuinely sharper signal would: exact multi-word phrase matching against the
book text rather than term overlap; restricting to the categories where Raman does name kinds
(profession, manner of death, counts) rather than scoring all eleven; or growing the prose
denominator. Two caveats on the current run: 206 golden records carried both a castable birth
and per-house prose, and some `verdict_prose` is maintainer commentary rather than Raman's own
words, which dilutes both arms equally but shrinks the real signal more than the sham.


## SLOT-MAPPING ARC CLOSED (2026-09-01) — all twelve houses classified, 70 rules repaired

Houses 2, 3 and H9.L.12 are done, which finishes the `lord_in_house` sweep the general-slot
entry above opened. Final state of the classification, all of it from engine-blind review
against Raman's printed text, none of it swept:

| Family | Houses | Outcome |
|---|---|---|
| general + fortified, NO afflicted branch | H1, H4 | repaired (24 rules) |
| MIXED — general + fortified with some genuine afflicted clauses | H2, H3, H8, H11, H12 | repaired per rule |
| EXPLICIT-AFFLICTED — Raman does give an afflicted reading | H5, H6, H7, H9, H10 | untouched, pinned by test |

**70 rules now carry a `general` slot.** `[ratchet]` 287/397 unchanged through every commit of
the arc — the repair moves TEXT between presentation slots; `polarity` decides the verdict and
`_branch` reads neither the new field nor any edited condition.

House 2 closes with Raman's own confirmation at HTJAH-I:2423 — *"These combinations are AGAIN
of general application"* — whose "again" back-references the design statement at 1003-1007 and
settles the whole table.

**H9.L.12 was the lone exception in an otherwise correctly-encoded House 9.** Its paragraph
(HTJAH-II:7389-7394) carries no conditional opener of any kind, and the encoder cut it at
Raman's own "but": *"He will be religious and noble BUT ALWAYS IN WANT"* — first half filed as
fortified, second half plus the rest of the paragraph as afflicted. H9.L.1-11 use explicit
malefic/benefic openers and are untouched; a test pins that.

### Three things deliberately NOT repaired, because they are a different defect

Each is misfiled but is NOT a general reading, so relocating it would have been a second error
on top of the first. All three are annotated in place and need a CONDITION change, which would
move the ratchet and therefore needs measurement first:

1. **H3.L.3** — its three sibling-death clauses (HTJAH-I:3352-3354) are conditioned on PLANET
   IDENTITY: which planet happens to be the 3rd lord (Mars / Saturn / Sun). There is no
   affliction test in them at all, so firing them off an affliction predicate is wrong in BOTH
   directions — an afflicted non-Mars 3rd lord wrongly reads "loses all younger brothers", and
   an unafflicted Mars 3rd lord wrongly does not.
2. **H2.L.4** — the affliction Raman names is of the **4TH lord**, not the 2nd (2360).
3. **H3.L.4** — "When Mars is weak" is KARAKA strength (3361) and "if the 3rd house is
   beneficially disposed" is a HOUSE-disposition branch (3361-3362); neither is a 3rd-lord
   affliction.

Also standing, and worth a product decision rather than a code change: **H2.L.8's `fortified`
branch is ADVERSE** (HTJAH-I:2392-2393, "hardly any earnings, but inherited or accumulated
wealth will disappear"). Raman's strong branch really is the bad one here. Any renderer that
labels `fortified` as "the good reading" mis-presents it — which is now a live concern, since
the new `general` lane renders these slots to readers who did not previously see them.

### Content restored that the encoding had dropped entirely

Relevant to the report-completeness lock, since these were silently absent rather than hidden:
H2.L.1's *"becomes no doubt wealthy"* (2325, which inverted that sentence's balance by its
absence); H2.L.4's explicit carry-over *"The above results will apply in addition to the
following"* (2355); H2.L.9's *"Skilful"* (2395); H3.L.9's *"Long journeys. Sudden and
unexpected changes in life."* (3394-3395); and H3.L.9's *"father untrustworthy"*, which was
not merely dropped but mis-slotted — it is Raman's GENERAL reading, and only "misunderstandings
with his father" (3397) is affliction-conditioned.

### What remains open in this area

- **H2.L.2's `fortified`** is real Raman but sourced from HTJAH-I:2506, a dasha-timing list
  OUTSIDE the lord-in-house table, and is conditioned on a parivarthana rather than on
  fortification. Left in place; it needs its own decision, not a slot move.
- **The `planet_in_house` and `combination` groups were never swept for this defect.** The
  provenance audit noted the same general-vs-afflicted pattern is live in
  `house_04_sukha/planets_in_4th.py` (H4.P.Mars's one unconditioned sentence at 4250-4253 is
  split across both slots). ~200 `combination` rules and the `planet_in_house` modules remain
  unclassified. The reliable method is the one used throughout this arc: read the source
  section once, then match every row in the module against it — never a lexical sweep.


## THE planet_in_house SWEEP (2026-09-01) — the defect class closed, and three more transplants

Five engine-blind reviews covered every rule in the corpus that could carry the slot defect but
had not been examined: **96 rules with BOTH text slots filled, outside `lord_in_house`** — 79
`planet_in_house`, 12 `combination`, 3 `from_karaka`, 1 `navamsa_qualifier`, 1 `moon_mind`.
Each review did TWO jobs over one reading of the source: slot classification AND provenance.

**★ THE STRUCTURAL FINDING. The "Planets in the Nth House" tables are not built on a strength
axis at all.** Raman writes each planet as one flat, unconditioned paragraph, modified by
CONJUNCTION and ASPECT — he says so himself at HTJAH-I:1480-1481 ("its effects by house
position, as given below, are subjected to modification correspondingly"), and **the project's
own methodology docs already had it right**: their column is headed *"Effect | Aspect /
association modifiers"* (`methodology/house_01_lagna.md:243`, `house_02_dhana.md:187`). The
`.py` encoders collapsed that two-column table into the two-slot record BY SENTIMENT.

The opener census is decisive. House 2: **zero** fortification and **zero** affliction openers
across all nine planets. House 11: 53 lines of unbroken declarative prose with **not one
conditional of any kind**. Houses 10/11/12 together: **two** fortification openers in 231
lines, and exactly those two rules (H10.P.Ketu, H12.P.Venus) had a correctly-populated
`fortified` slot.

**The smoking gun for valence-driven slotting** is in House 10: the same conjunction pair lands
in opposite slots by how pleasant the outcome is — Mars+Jupiter ("head of low-class people") in
`fortified`, Mercury+Jupiter ("unhappy, childless") in `afflicted` — with identical grammar in
Raman. And the tearing is repeatedly MID-SENTENCE, at Raman's own hinge word: *"strong and
adventurous BUT funky"*, *"unhappy BUT generous hearted"*, *"clever and rich BUT lustful"*,
*"NEVERTHELESS his moral character will be loose"*, *"He will HOWEVER be valorous"*.

**Shipped: 78 of the 79 at-risk `planet_in_house` rules now carry a `general` slot.** The one
exception is H8.P.Ketu, ruled correctly encoded (both of Raman's openers explicit, both slots
tracking them). 150 rules corpus-wide now carry `general`. `[ratchet]` 287/397 unchanged
through every commit.

### The severe findings, handled separately from the bulk

- **★ TWO MORE CROSS-HOUSE TRANSPLANTS, both of the SAME sentence.** HTJAH-I:8218-8219 sits
  inside the paragraph headed *"These results are modified by the aspects and associations
  received by the planet in the 7TH HOUSE"*. It had been grafted onto **H3.P.Sun** (with its
  subject reassigned — Raman writes that the PARTNER may be a highly evolved spiritual soul,
  not that the native is spiritually strong) and onto **H6.P.Sun**. One passage, two
  placements, neither of which Raman grants it to.
- **★ A THIRD UNSOURCED CLAIM.** H7.P.Mars asserted *"may gain through partnerships"*. The
  nearest real text is line 560 — the VENUS entry — transferred one planet sideways onto a
  placement where Raman concludes the opposite: *"intelligent, tactless, stubborn, peevish and
  UNSUCCESSFUL"* (535-536).
- **★ A CROSS-FRAME TRANSFER.** H12.P.Ketu promised *"Kaivalya / Final Emancipation"* — Raman's
  words verbatim at HTJAH-II:16527, but framed on the **KARAKAMSA**, while the record's
  condition is Ketu in the 12th with `frame="LAGNA"`. As encoded it promised Final Emancipation
  to every chart with Ketu in the 12th from the Ascendant. **Removed, not relocated** —
  moving unsourced or misframed prose into `general` would launder it into a slot that asserts
  Raman said it.
- **★ THREE DIRECTION INVERSIONS.** H6.P.Ketu conditioned *"moral character loose"* on
  affliction when Raman's word is **"Nevertheless"** — he insists it holds DESPITE the good, so
  a fortified chart never saw it. H9.P.Moon filed *"the native will become a RULER"* under
  `afflicted` with an interpolated *"(mixed)"* hedge that is nowhere in Raman. H1.P.Moon filed
  *"with Jupiter, the mind is ELEVATED"* under `afflicted`.
- **★ THREE INVENTED POSITIVE COMPLEMENTS — the mirror of the hunted defect.** H7.K.1/K.2/K.3
  encode the affliction IN THE CONDITION, so they only ever fire in the malefic case, yet each
  carried an unsourced positive `fortified` string ("normal virility", "long-lived partner",
  "harmonious marriage") that `_branch` surfaces on a strong karaka. A chart with Saturn in the
  6th/8th from a strong Venus was shown *"normal virility"* — the inverse of Raman's flat
  sentence that the position CAUSES impotency. The corpus's own correct handling of this shape
  was already documented three files away at `moon_mind.py:147-151`.
- **H1.M.G1 turned a METHOD into a verdict.** HTJAH-I:1236 renders no judgement at all — "The
  liability to diseases and accidents is JUDGED FROM the planets rising or setting, and those
  CONFIGURATED with the Moon" — and the encoding cut it in two, substituting "afflicting" for
  "configurated" and adding "indicate bodily vulnerability".
- **H1.N.66's `fortified` half was the logical NEGATION of its own firing condition**, so
  whenever the rule fired its fortified text was false of that chart.

### ★ AN IMPORTANT NEGATIVE RESULT — why the group was reviewed and not transformed

**15 of the 17 scattered `combination` / `from_karaka` / `moon_mind` / `navamsa_qualifier`
rules came back LEAVE.** The slot defect is largely ABSENT there: those slots hold genuinely
conditioned prose, because `combination` rules are hand-composed from prose rather than
transcribed from a table. **No fabrication and no frame transfer was found in any of them** —
H8.C.7's Mandi/Navamsa frame, the likeliest candidate for the H12.P.Ketu error shape, is
encoded correctly. A blanket sweep would have destroyed real doctrine in 15 of 17 cases. House
3's planets module was likewise ruled the best-encoded of its batch (seven genuine affliction
openers, every one preserved by the encoder), so its repairs were surgical.

This is the third time in this arc that reviewing before sweeping prevented damage. It should
be treated as settled method: **read the source section once, then match every row in the
module against it — never a lexical sweep.**

### STILL OPEN

1. **Single-slot rules were out of scope and carry the same defect on the other side.** At
   least 15 were named in passing: H1.P.Rahu/Ketu, H2.P.Sun/Mercury/Jupiter/Venus,
   H7.P.Jupiter/Rahu/Ketu, H8.P.Mars/Mercury, H9.P.Mercury, H10.P.Sun/Moon/Venus,
   H12.P.Moon/Mars/Mercury/Saturn, H4.P.Rahu/Ketu, H5.P.Sun/Rahu/Ketu. Their unconditioned
   reading sits in a lone `fortified` or `afflicted`. Lower harm (nothing is INVERTED), same
   repair direction.
2. **★ H10.C.33 — a CONDITION/SLOT MISMATCH, not a text defect.** `condition=CountInHouse(10,
   1, "benefic")` means the rule can only fire when a BENEFIC is in the 10th, yet its
   `afflicted` slot asserts *"malefics in the 10th"*. The malefic half of Raman's sentence is
   reachable only on a chart that has a benefic in the 10th AND an afflicted 10th house. It
   needs its own predicate. **This would move the ratchet — measure first.**
3. **Cross-house and cross-lord conditions that `_branch` fires on the wrong evidence:**
   H11.C.47 ("Malefics HERE" means malefics in the 5th, not affliction of the 11th),
   H11.C.52 (both clauses condition on affliction of the **10th**), H11.C.49 (one clause is
   "strong Lagna lord BUT weak 7th house" — neither leg an affliction), H2.C.53 ("when the 7th
   lord has MARAKA POWER" — a lordship identity). All annotated in place; all are CONDITION
   work.
4. **H7.K.2's set semantics, UNDETERMINED.** Raman writes "malefics in the 4th, 8th AND 12th
   houses from Venus"; `ClassInHouseFrom` is an ANY-OF quantifier, so the rule fires on a
   single malefic in the 4th from Venus. Whether his "and" is conjunctive or distributive is
   not resolvable from the sentence, but the any-of reading is materially looser and will fire
   on a large majority of charts.
5. **Dropped content and under-citations**, both relevant to the report-completeness lock:
   ~25 clauses were noted as omitted from their entries across the four reviews, and the whole
   `planets_in_11th` family appends a "gains via..." tail drawn from Raman's sources-of-gain
   list at HTJAH-II:14373-14386, ~80 lines from each record's cited spine. Under-citation, not
   miscitation — the cited line is right for the record's spine.
6. **H11's real house-level fortified/weak pair is unencoded** (HTJAH-II:14362-14371,
   "Fortified planets in the 11th house confer..." / "If the 11th house be occupied by a weak
   planet..."). That is the doctrinally correct home for a strength split on the 11th, and the
   module has none.

### Provenance, cumulative

Across the two audits the corpus now has **~280 rules verified against Raman's printed text**.
Confirmed unsourced or misframed: **H10.L.1, H3.P.Sun, H6.P.Sun, H7.P.Mars, H12.P.Ketu, and
the three H7.K `fortified` complements** — eight in total, all now removed. Miscitations
corrected or annotated: H3.L.11, H4.C.24, H7.P.Jupiter, H7.P.Mars. The `combination` modules,
named by the first audit as the likeliest remaining risk, came back clean on their first look.


## H8 OVER-FIRING FIXED, AND WHAT IT EXPOSED (2026-09-01) — the first deliberate ratchet re-base since B1

**The defect.** Raman conditions ELEVEN of the twelve H8 lord-in-house readings on the 8th lord
being WITH that house's own lord, in his own words throughout HTJAH-II:2899-3069 — *"in
conjunction with the 2nd lord in the 2nd house"* (2916), *"combines with the lord of the 3rd in
the 3rd"* (2927), *"joins the 4th lord in the 4th house"* (2940), *"placed in the 7th house with
the 7th lord"* (2993), *"combines with the 11th lord in the 11th house"* (3042). The encoded
condition was the bare `LordIn(8, N)`.

**Measured before changing anything.** Over the 346 golden charts the bare condition fires 345
times; requiring the conjunction, 64. **81% of firings were on placements Raman's sentence does
not cover.** The 8th entry is the exception and was left alone — *"if the lord of the 8th house
occupies the 8th house IN STRENGTH"* is a strength condition, and `LordsConjunct(8,8)` is
identity-false by design.

**★ THE COST, AND WHY IT SHIPPED ANYWAY.** Narrowing changed exactly ONE scored row and fixed
none: **HTJAH-II.chart_73 — LINCOLN, assassinated by shooting** — H8/death went favourable
where Raman says afflicted. Exact 287 -> 286, within-1 363 -> 362, inversions 34 -> 35.

The diagnosis is the whole point. The engine had been reaching Raman's verdict on Lincoln
through **H8.L.1 firing on the bare placement** (Mercury, the 8th lord, in the 1st) while
Saturn, the 1st lord, is **not** conjunct it. **Raman would not have applied that rule to that
chart.** The old number was right for the wrong reason. Preserving it would have been exactly
what the Prime Directive forbids — *"overfitting to worked examples is not accuracy"* — so the
baseline was re-based DOWN deliberately, user-signed, with lineage in both fixtures. This is
the first deliberate strict-down re-base since the B1 dominant-factor guard (2026-08-03), and
unlike B1 it buys no measured improvement: it buys **predicate correctness**, which the ratchet
does not measure at all. That asymmetry is worth remembering — a faithful fix can be invisible
to, or negative on, every number the project tracks.

**★ WHAT THE NARROWING EXPOSED — a real gap, now visible instead of masked.** Lincoln's
H8/death ledger after the change: lord Sun **strong**, karaka Saturn **strong**, and the only
malefic rules firing are **H8.C.21, H8.D.4 and H8.D.5 — all three `_DREKKANA_MANNER_RULE_IDS`**,
which by the 2026-08-30 reviewer amendment name the MANNER of an affliction established by
other testimony and may never be the sole confirming malefic (Savarkar is the printed
counter-instance). The one other rule, H8.C.26, is neutral polarity. **So the H8 corpus holds
no orthodox non-manner testimony for Lincoln's death at all.** The verdict is favourable
because both pillars are strong and nothing that may confirm an affliction does.

That is not a judge defect. The manner/span separation is correct doctrine. It is a **corpus**
gap, and it was invisible while the over-firing rule was covering for it.

**Raman's own reasoning is on record** in the golden's `verdict_prose` and at HTJAH-II:6741-6790:
*"The 22nd Drekkana is an Ayudha Drekkana, being the 2nd of Virgo"* (the engine computes Virgo-2
— it agrees with him), *"The 8th lord Mercury is in a constellation of Rahu who, in turn, is in
association with the planet of violence, Mars"*, and a named combination he quotes and then
demonstrates: *"A combination in **Goutama Samhita** says that if the lord of the 8th is in the
Ascendant and the waning Moon is aspected by Mars, death will be due to a weapon. The 8th lord
Mercury is in the Ascendant and the waning Moon in the 12th house is aspected by Mars."*
(6757-6762).

**Candidate rule, measured, and under engine-blind review at time of writing.** Predicate
`And(LordIn(8,1), MoonPhase("waning"), Mars-aspects-Moon)`; all three primitives already ship.
Fires on **5 of 346 goldens (1.4%)**. Only TWO of the five carry a scored H8/death expectation
— and both are Abraham Lincoln, recorded independently in two books (HTJAH-II.chart_73 and
NH.chart_24), both `afflicted`, which is what the rule predicts. So it cannot flip a scored row
the wrong way. The open doctrinal question, put to the reviewer, is whether *"death will be due
to a weapon"* is orthodox affliction testimony or MANNER evidence like the drekkana rules — if
the latter, it must NOT be allowed to establish the affliction alone either, encoding it will
not recover Lincoln's row, and the honest conclusion is that the gap is real and unfilled.

**NOT proposed:** the Jataka Tatwa assassination combination Raman cites next (6766-6771,
"Saturn, Sun and Mars in the 10th, 7th and 4th respectively"). His own chart does not satisfy
its strict form — he has Mars *aspecting* the 4th and the Sun *aspecting* the 7th — so encoding
it would mean encoding his loosened reading rather than the stated combination.

**Rule-liveness floor 58 -> 59.** H8.L.3 now fires on no golden: no golden chart has the 8th
lord conjunct the 3rd lord in the 3rd. An honest coverage gap is better than a rule firing on
18 placements Raman's sentence does not cover.

**Still open in H8:** Raman adds a SECOND condition to some entries that is not encoded — the
9th wants the conjunction *"with malefics"* (3010), the 12th distinguishes benefics joining the
8th lord (3053-3055). Each needs its own measured pass.


### THE LINCOLN HUNT — CLOSED, and the gap is REAL (2026-09-01)

The candidate Goutama Samhita rule was reviewed engine-blind and came back
**DOCTRINE-CONTESTED**. The predicate was faithful; the proposed TIER was wrong. It is
shipped as **H8.C.33 at MANNER tier**, and it does **not** recover Lincoln — by design.

**Why the tier matters, in Raman's own taxonomy.** HTJAH-II:3591 heads the section "Nature of
Death"; at **3728-3731** he writes *"When these particular yogas are absent in a horoscope,
classical works refer to the lord of the 22nd drekkana to find out the cause of death"* — so
the weapon-yogas and the 22nd drekkana are **alternate instruments of ONE apparatus**. The
drekkana half is already corroboration-tier (the 2026-08-30 amendment), so letting the
weapon-yoga half confirm would make the tier depend on which instrument happened to fire. At
3884-3891 he assigns *"Mars by weapons"* explicitly under *"indicate the CAUSE of death"*.
Structural corroboration: in BOTH worked charts the combination sits in the Conclusion block,
after the four-pillar ledger, beside the 22nd drekkana — Lincoln (6757) and Gandhi (6810, the
sibling yoga "the waning Moon in the 11th").

Encoding it confirm-capable would have been **the same category error as the over-firing rule
the narrowing removed** — recovering the row through a rule that is not doing the doctrinal
work the verdict needs — and harder to spot, because the citation is genuine. `_MANNER_RULE_IDS`
(renamed from `_DREKKANA_MANNER_RULE_IDS`, now a misnomer) holds it. Measured after shipping:
Lincoln's H8/death stays favourable, all four fired malefics being manner-tier; ratchet
unmoved at 286/362/35.

**★ THE FINDING THAT MATTERS MOST, and it belongs with MEASURED TRUTH.** Raman's own
four-pillar ledger for Lincoln is FAVOURABLE on three of four pillars, in his own words:
*"The Eighth Lord: Mercury is **well placed** in the Ascendant with the 7th lord Sun"*
(6741-6742); *"Ayushkaraka: Saturn occupies Scorpio in the 10th house aspected by Jupiter in
own sign"* (6744-6745); the 8th itself *"aspected by Jupiter and exalted Venus"* (6711-6712).
**The engine computing lord Sun strong and karaka Saturn strong is AGREEING with Raman's
printed pillar reading — it is not misreading the chart.** His `afflicted` verdict rests on
manner + timing + the historical fact that the man was shot.

So this is not a corpus gap that one more rule can close, and it is not a judge defect either.
It is a limit of the four-pillar method as such: on Lincoln, Raman's own pillars say
favourable, and he overrides them with knowledge the pillars do not contain. Any future attempt
to "fix" this row should start from that sentence, not from a search for more testimony.

**Rejected, with reasons, so they are not re-proposed:**
- **The nakshatra chain** (*"The 8th lord Mercury is in a constellation of Rahu who, in turn,
  is in association with the planet of violence, Mars"*, 6753-6755): an observation about one
  contributing factor in one chart, not a stated dictum — exactly the unit the north-star
  playbook's confirmation rule excludes. Its own wording (*"the planet of violence"*) shows it
  is explaining the MANNER anyway, so it would change nothing even if encoded. (Aside:
  `InStarOf` takes a static lord name, so "the 8th lord in Rahu's star" is not expressible
  without a dynamic-lord form.)
- **The Saturn-Dasa / Mercury-Bhukti maraka reasoning** (6770-6775): timing, not natal
  affliction — and already encoded, in `primitives/vimshottari.py:331-334` (Saturn-in-10th
  Mrityu Yoga adds Saturn to the tertiary maraka set) and 324-326 (the from-Moon 2nd/7th/8th
  lords). Nothing to add.
- **The Jataka Tatwa assassination combination** (6766-6771): the strict form is not what Raman
  applied to this chart, and the loosened form is not what the text says. The reviewer put the
  objection better than the original proposal did — choosing the loosened form would be
  **reverse-engineering the predicate from the chart you want it to fire on**. Its outcome
  clause is manner anyway.

**One live candidate, NOT certified, for a future citation hunt.** The from-Moon pillar at
6747-6750 — *"Considered from the Moon: The 8th house is aspected by Saturn while the 8th lord
Sun occupies the 2nd house with Mercury"* — is the only line in the passage recording an
affliction to the 8th itself rather than a cause or a date, and **H8 currently has ZERO
`frame="MOON"` rules** (H1 has seventeen, H9 three). But Raman's stated H8 factor list is
*"(a) The House, (b) Its Lord, (c) Its Occupants and (d) The Karaka... The same considerations
must be judged from the Navamsa chart also"* (2890-2894) — **the from-Moon frame is not in it**
— and he states no general dictum of the form "the 8th from the Moon aspected by a malefic
afflicts the 8th". Encoding it needs its own general-voice citation, which the reviewer could
not find in the H8 chapter. The search should target Raman's from-Moon method statements
OUTSIDE that chapter (he concludes *"The 7th house from the Moon also suffers affliction"* at
1279-1280, so the frame is doctrinally live as affliction testimony elsewhere).

**One open design question, surfaced and explicitly NOT recommended.** Lincoln carries three to
four independent manner testimonies converging on the same instrument (22nd drekkana Ayudha,
Goutama Samhita weapon, Jataka Tatwa assassination, and via Mars the 3884-3891 cause table).
The Savarkar counter-instance that justified corroboration-tier is a SINGLE manner testimony
(Jupiter in Ayudha, natural death) and does not refute a rule keyed on convergence of three or
more. Whether a manner CONVERGENCE may confirm is a live doctrinal question — but there is **no
printed Raman dictum stating it**, and his H8 factor list gives no warrant. It must not be
slipped in as a threshold tweak; it is a separate INVESTIGATE with its own citation hunt and
its own engine-blind review.


## CONDITION-FIDELITY AUDIT (2026-09-01) — 132/132 BARE. H8 was an outlier, not the first case.

After the H8 over-firing fix, the obvious question was whether the other eleven
`lord_in_house` tables have the same defect. Nobody had checked — H8's was found by accident.
Every rule in those eleven modules is a bare `LordIn(N, k)`, so the whole question is whether
Raman states a bare placement or a richer predicate per entry.

**Three engine-blind reviews read all 132 remaining entries IN FULL** — not sampled, because
H8's defect ran across eleven of its twelve entries and a house carrying it in only three would
slip past first-entry sampling (which is exactly how my own H9 "lone exception" claim went
wrong; see below).

**★ RESULT: 132 BARE, 0 NARROWER, 0 UNDETERMINED. The bare `LordIn(N, k)` encoding is faithful
for Houses 1-7 and 9-12, and no condition should be narrowed.** Narrowing any of them would
SUPPRESS doctrine Raman states broadly — the opposite error from H8's, and just as damaging.

### Why H8 differs — the discriminator, worth keeping for any future audit of this shape

The reviews converged on four independent structural facts:

1. **Every other section closes by naming the placement as the base and strength as the
   modifier** — HTJAH-I:1003-1007 ("the combination is of general application"), 2423 ("again
   of general application"), 4190 ("very general... augmented or minimised according to the
   strength"), 5173 ("quite general... qualified or modified"), 6062 ("the general results
   likely to happen when the sixth lord is posited"), HTJAH-II:343 ("These results occur if the
   7th lord is placed in the different Bhavas"), 7396, 14344, 16230. **H8's section carries no
   such disclaimer, because its readings are not general — they are conjunction-specific.**
2. **Every qualifier elsewhere is SCALAR and unnamed** ("favourably disposed", "well aspected",
   "fortified", "beneficially"). H8's are DETERMINATE planets — *the 2nd lord*, *the 4th lord*,
   *the 7th lord* — a rare, checkable event (measured 64 of 345 firings).
3. **Every qualifier elsewhere has its complement pole stated**, and four entries (H5.L.1,
   H5.L.4, H6.L.9, H6.L.11) are explicit THREE-WAY partitions (fortified / moderate / afflicted),
   leaving no placement Raman declines to address. H8's conjunction has **no complement**: an
   8th lord in the 2nd *without* the 2nd lord is a configuration his sentence simply does not
   reach.
4. **The syntactic tell:** in H8 the conjunction is the grammatical subject of the entry's FIRST
   result-bearing sentence. Everywhere else that sentence is a flat declarative or a placement
   restatement, and every conjunction/aspect/sign clause sits in a LATER sentence with its own
   distinct outcome.

House 12 came closest without reaching it — two of its entries use the exact H8 idiom ("If the
6th lord joins the 12th lord in Lagna", 16132; "If the 12th lord joins the 2nd lord in the 3rd",
16157) — but both are late sentences with their own outcomes, after an unconditioned opening.
H9.L.1 is the sharpest illustration: "If the 9th lord combines with the Lagna lord in the first
house and associates with or is aspected by a benefic planet..." (7303) is H8-shaped, but it is
the SECOND sentence and carries a different outcome from the base.

### `tools/raman_saab/condition_delta.py` — the instrument, now permanent

The H8 measurement was improvised. It is now a harness that reports, in the order the questions
should be asked: COVERAGE (firings now vs proposed), EXPOSURE (how many changed charts carry a
scored expectation for that house), and IMPACT (which scored rows move, with golden / current /
proposed per row). It reports DIRECTION deliberately — the H8 change cost one exact match, and a
bare delta would have argued for reverting something that was right to ship. Restores the
swapped condition in a `finally`, with a test proving no leak even when a proposal raises.

### ★ FOUR TEXT DEFECTS the audit found in passing — including a correction to my own claim

Reading all 132 entries in full surfaced defects the earlier text sweep had missed, because
they were not "at-risk" records under its both-slots rule:

- **H7.L.12's `fortified` was UNSOURCED AND INVERTED.** It read *"possible spiritual turn when
  both karaka and lord are STRONG"*. HTJAH-II:329-340 contains no spiritual turn at all, and its
  only karaka+lord clause is the OPPOSITE condition with an opposite outcome: *"If both karaka
  and the 7th lord are WEAK, the native may only dream of women but never marry"* (336-337) —
  which the `afflicted` slot already carried correctly. Removed.
- **H7.L.3** attributed *"female issues survive"* to `fortified`; it follows the AFFLICTION
  clause at 257.
- **★ H9.L.6 and H9.L.8 — a CORRECTION TO THIS BACKLOG'S OWN EARLIER ENTRY.** The 2026-09-01
  slot-mapping work asserted, in a module comment, a commit message and a TEST, that H9.L.12 was
  *"the LONE exception in House 9"*. That was FALSE. H9.L.6 (7340, *"The ninth lord in the sixth
  house gives a sickly father afflicted with chronic diseases"*) and H9.L.8 (7359, *"The native
  may lose his father early in life"*) are also flat unconditioned bases with no benefic/malefic
  opener, and both had them filed under `afflicted`. Three entries needed repair, not one.
  **The error was made by sampling the entries that DO have explicit openers instead of reading
  every one — precisely the mistake this audit existed to catch, committed by the process that
  commissioned it.** The test that pinned the false claim has been corrected to assert the true
  state and to record why it was wrong, rather than quietly re-scoped.

### Still open from the audit (text-arm, not condition)

- **Conditioned outcomes folded into unconditioned arms.** `H10.L.1.fortified` ends "Lagna and
  10th lord together → famous pioneer, founds public institution" (HTJAH-II:9462), and
  `_branch` returns "fortified" by default INCLUDING whenever Shadbala is absent — so a chart
  with the 10th lord in Lagna and no conjunction still receives that text. Same shape in
  `H10.L.5.fortified` and `H12.L.1.fortified`. Most preserve the "if" in prose, which mitigates
  it; H10.L.1's does not.
- **`_branch`'s fortified-default on sparse charts.** `H10.L.10` has no unconditioned reading in
  Raman at all, so on a Track-B chart with no Shadbala a weak 10th lord receives the "highly
  successful" reading. A general property of the fallback, not specific to these modules, but
  worth its own decision.


### SINGLE-SLOT RELOCATION + ARM-FOLDING (2026-09-01) — the sweep's remainder, closed

**29 single-slot `planet_in_house` rules relocated.** They carried Raman's unconditioned base
reading in a lone `fortified` or `afflicted` slot — the same defect as the at-risk records, on
the other side. Out of scope for the main sweep, which took only both-slots records.

Done as a **pure, mechanical relocation**: the text was copied verbatim into `general` and
mirrored into `fortified`, nothing rewritten. Every one of these sections had already been
ruled unconditioned by the sweep's reviews (H2: "zero fortification openers and zero affliction
openers across all nine planets"; H11: "53 lines of unbroken declarative prose containing not
one conditional"; H1's nodes: "wholly unconditioned paragraphs... they belong in `general`"),
and hand-rewriting them would have introduced text no reviewer checked.

**`afflicted` was deliberately left None**, not mirrored. A first pass DID mirror into all
three slots and was reverted: filling `afflicted` would put Raman's unconditioned reading back
under an "afflicted" heading, which is the exact defect this whole arc removed. With it None,
`_branch` always returns "fortified" (rule_firing.py:48), so the reading renders on every chart
and never under a false label.

The mirror also fixes a **live rendering bug**: a rule with `fortified=None` and `afflicted=X`
renders NOTHING on a strong-lord chart, because `_branch` returns "fortified" and the text is
then None. Twelve of the 29 were in that state.

**107 of 108 `planet_in_house` rules now carry a `general` slot** — the one exception being
H8.P.Ketu, reviewed as correctly encoded.

**Arm-folding repaired in three `lord_in_house` records** (H10.L.1, H10.L.5, H12.L.1). Each had
a CONDITIONED outcome folded into the unconditioned `fortified` arm, so it displayed on any
strong-lord chart — and, because `_branch` also defaults to `fortified` when Shadbala is
absent, on every sparse chart too. H10.L.1's "Lagna and 10th lord together -> famous pioneer,
founds public institution" (HTJAH-II:9462) is the clearest case. Each is now labelled as the
configuration it is, with the base reading in `general`.

Two clauses that had been dropped entirely are restored: H10.L.5's navamsa gate on the
orphanage clause ("if the 10th lord occupies the 6th, 8th or 12th Navamsa", 9506) and
H12.L.1's "If the sign is common, the native will generally be travelling about" (16131).
H12.L.1's "This also indicates imprisonment and living abroad" (16134) is left where the
encoder put it and marked UNDETERMINED in place — the referent of "This" is ambiguous between
the preceding 8th-house-afflicted clause and the placement generally, and the text will not
settle it.

**A test was tightened rather than re-scoped.** `test_the_one_unsourced_slot_was_removed_not_relocated`
asserted `H10.L.1.general is None`, which was right when the unsourced text was cleared but
became wrong once the record legitimately gained a base reading. It now asserts the thing that
actually matters — that the invented words ("modest attainment", "little distinction") appear
in NO slot — with a note recording why the original assertion was replaced.

**Still open:** the four cross-house condition bugs (H10.C.33's unreachable malefic branch;
H11.C.47, H11.C.52 and H2.C.53 firing off the wrong lord's affliction), and `_branch`'s
fortified-default on sparse charts, which is a general property of the fallback and wants its
own decision rather than a patch.


### H10.C.33 SPLIT (2026-09-01) — an unreachable branch, and half a predicate

**The defect.** HTJAH-II:11064-11066 is ONE sentence with TWO distinct antecedents: *"Benefics
in the 10th from the Ascendant or the Moon make the native noble-minded WHILE MALEFICS make him
addicted to evil deeds."* Both halves were fused into a single record whose condition was
`CountInHouse(10, 1, "benefic")`. So the rule could only fire when a BENEFIC was in the 10th,
and **the branch meant to state the malefic case was gated behind the benefic case** — reachable
only on a chart that had a benefic in the 10th AND an afflicted 10th house.

Second defect in the same record: the condition tested only the LAGNA while Raman says *"from
the Ascendant OR the Moon"*, so half the doctrine was unreachable on that axis too.

**Measured before shipping**, with the new `condition_delta` harness:
- widening the benefic rule to include the from-Moon axis: **101 -> 158 of 346 goldens, and NO
  scored row changes verdict**;
- the new malefic rule H10.C.33m: fires **180/346**, touches **30 scored H10 rows**, and leaves
  the ratchet at **286/362/35 — non-decisive on every scored row it reaches**.

Both halves are broad (46% and 52%), which is inherent to Raman's sentence rather than a sign
of over-encoding — but note the H7.C.8 precedent, where a verbatim-faithful rule was HELD on
breadth grounds. The difference here is that this is not a new doctrine claim: it makes the
other half of an already-cited sentence reachable, and both changes were prescribed by name in
the engine-blind review that found the defect.

### The remaining three "condition bugs" are ONE structural question, not three fixes

H11.C.47, H11.C.52 and H2.C.53 were flagged as firing off the wrong evidence:
- **H11.C.47** — *"Malefics here"* (HTJAH-II:14650) means malefics in the **5th**, not affliction
  of the 11th;
- **H11.C.52** — both afflicted clauses condition on affliction of the **10th** (14699);
- **H2.C.53** — *"When the 7th lord has Maraka power"* (HTJAH-I:2663) is a **lordship identity**.

None of these is a defect in the rule's `condition`. Each is a BRANCH carrying its own
predicate that the two-slot record cannot express, so `_branch` selects it by the rule's own
house-lord Shadbala instead. That is the same shape as the H10.C.33 defect just fixed — and the
fix is the same shape too: give the clause its own rule.

**But that is a PATTERN decision, not three edits.** Branch-with-its-own-predicate is likely
widespread (the planet_in_house sweep alone annotated roughly two dozen "(a configuration, not
an affliction)" clauses), and converting them wholesale would add a large number of new rules,
each needing its own measurement and review. It should be decided deliberately — with a census
of how many branch clauses carry their own predicate, and a rule for when one earns its own
record — rather than fixed three at a time. All three currently name their real condition in
their prose, which mitigates the reader-facing harm; the machine-facing harm (firing on the
wrong evidence) remains.


### `_branch` NOW FALLS BACK TO `general` WHEN STRENGTH IS UNKNOWN (2026-09-01)

**The defect, measured.** `rule_firing._branch` picks `fortified` vs `afflicted` by the
bhava-lord's Shadbala. On a Track-B chart there is no Shadbala — **40 of the 346 goldens
(12%)** — and the old fallback returned "fortified" regardless.

Census of what that showed:
- **90 rules** where `general == fortified` → the fallback happened to show the right text;
- **★ 82 rules where `general != fortified`** → the reader was shown Raman's
  STRENGTH-CONDITIONED reading when his UNCONDITIONED one applies. H1.L.3 is the plain case:
  "rise in life brought about by brothers; may become famous as musician or mathematician" was
  displayed where "highly courageous, fortunate, respectable, two wives, intelligent, happy" is
  what Raman states for the placement itself;
- **64 rules** with no `general` at all → nothing better exists; old behaviour retained.

**This is the same defect class the general-slot work removed from the DATA, surfacing at the
JUDGE instead**: asserting a strength the chart cannot establish. And it could only be fixed
now — the `general` slot did not exist before this arc created it, so there was nothing to fall
back to.

`_branch` returns `"general"` when Shadbala is unavailable and the rule has one; `fire_rules`
resolves that to `rule.general`; `FiredRule.branch` gains a third legal value. Presentation
only — `_bucket_fired` buckets by `rule.polarity`, which no branch choice touches — and the
ratchet held at 286/397 across the change, as predicted.

### BRANCH-PREDICATE CENSUS (2026-09-01) — 28 candidates, not 134

The previous entry warned that "branch clause carrying its own predicate" might be a
corpus-wide pattern needing a design decision. Measured, it is much smaller.

134 evaluable rules have conditional language in their branch text, but that number is
misleading and splits three ways:
- **33 are strength-only** ("if afflicted", "when fortified") — that is exactly what the two
  slots exist to carry. NOT a defect.
- **21 name a NON-strength predicate**, plus **7 carrying both kinds** — the real candidate
  pool, **28 rules**.
- 31 unclear on a lexical scan.

And even within the 28, a scan cannot settle it, because some merely RESTATE the rule's own
condition. H1.C.1a reads "lord of the Lagna with the lord of the 6th, conjoined with or
aspected by a malefic" and its `condition` is already an `And(...)` encoding exactly that —
nothing unreachable, nothing firing on absent evidence. Only per-rule reading separates that
from a genuine extra predicate like H2.C.53's "if 7th lord has maraka power".

The 28: H1.C.1a/1b/1c, H1.B.17, H1.S.9, H2.L.2, H2.L.7, H2.C.9, H2.C.47, H2.C.48, H2.C.53,
H2.C.54, H3.L.4, H3.L.6, H3.L.11, H3.C.2, H3.C.6, H3.C.9, H3.C.31, H3.C.34, H4.P.Saturn,
H6.P.Sun, H6.P.Rahu, H7.L.1, H8.L.1, H8.L.2, H8.L.5, H11.C.47. Under engine-blind review at
time of writing, with the reviewer asked for a STATED PRINCIPLE for when a branch clause earns
its own record — not a case list — since the answer must still be right when applied beyond
these 28.


## BRANCH-PREDICATE AUDIT (2026-09-01) — a stated principle, and a systemic selector defect

The 28 candidates were reviewed engine-blind, with the reviewer asked for a PRINCIPLE rather
than a case list. Tally: **7 RESTATES, 3 SCOPE-NOTE, 18 EXTRA, 0 UNDETERMINED.**

### THE PRINCIPLE — binding for the remaining ~106 rules with conditional branch text

> **A branch clause earns its own `RuleRecord` if and only if it is a separate antecedent
> carrying its own consequent — "when C', then R'" where R' still asserts something about the
> native with the parent rule deleted. Otherwise it is a guard on the parent's condition, a
> branch-selector input, or a documentation note — never a record.**

Four tests, first failure decides:
1. **Consequent.** Delete the parent — does the clause still assert something? *"a sportsman,
   physical culturist or athlete"* yes; *"the intensity is reduced"*, *"minimised"*, *"unless
   relieved by Jupiter's aspect"* no. **This one test disposes of every navamsa-mitigation and
   every relief rider in the 28.**
2. **Antecedent-independence.** Can the clause hold where the parent's condition FAILS? Yes ->
   it must be its own record, because the parent can never reach those charts (H10.C.33's
   malefic half; H3.C.2's Saturn half).
3. **Satisfiability.** Can it co-hold with the parent? No -> source contradiction, descriptive
   only. H2.L.2 is the new instance: parivartana(1,2) puts the 2nd lord in house 1 while the
   parent requires it in house 2, so a conjoined rule would be dead -- the H2.C.46 shape.
4. **Non-vacuity / encodability.** Not true-by-construction, not biographical, expressible
   without inventing a threshold. "7th lord has Maraka power" fails (a) -- `maraka.py:122-133`
   makes the 7th lord a PRIMARY maraka on every chart, so a split rule would fire exactly as
   often as its parent, the H11.C.6 fake-coverage objection; "if a musician" fails (b);
   "otherwise well disposed" fails (c).

Corollary that decided most of the pool: **a clause whose subject is a strength test on the
rule's own house lord is never a record and never a guard -- it is `_branch`'s job.** And a
clause that INVERTS the parent's polarity ("quite the opposite results") passes test 1, while
one that merely SCALES it ("reduced in degree") does not.

### SHIPPED: the selector was asking the wrong planet, for 108 rules

The reviewer's highest-leverage finding, verified directly against the source before acting.
In the "Planets in the Nth House" tables Raman brands the branch on the **OCCUPANT**:

> *"The Sun.—The person becomes a good politician... **Sun afflicted:** Long and troublesome
> illness. **Sun fortified:** Good administrative ability, few enemies, wealthy"*
> (HTJAH-I:6115-6117)

Every one of the **108 evaluable `planet_in_house` rules** was branched on its HOUSE LORD. A
chart with a strong 6th lord and a combust, node-hemmed Sun was shown "administrative ability,
few enemies, wealthy" -- Raman's fortified reading, selected by a planet his sentence never
mentions. `_branch_subject` now reads the occupant off `InRashiHouse.planet` (all 108
conditions are that type, so coverage is total and no rule falls back silently).

**Measured before shipping: ratchet UNCHANGED at 286/397.** Branch selection is presentation --
`_bucket_fired` buckets by `rule.polarity` -- so this could only ever change WHICH of Raman's
readings is displayed, never a verdict. One rule fixes what would otherwise have been 84
splits.

A correct side effect: **node-occupant rules now fall back to `general`.** Rahu and Ketu carry
no Shadbala, so their strength is unassessable; branching on the occupant means those rules
yield Raman's unconditioned reading instead of a strength claim borrowed from the house lord.

### Still open — the 7 SPLIT candidates, and two inversions

**Split (7)**, each a separate antecedent with its own consequent, all expressible today:
H3.L.6 (6th lord also in the 3rd -> sportsman/athlete, = `Parivartana(3,6)`); H3.L.4 (three
sentences, none about the 3rd lord's strength); H4.P.Saturn twice (the Lagnadhipati/benefic
positive reading the parent lacks entirely, and the Mars/node affliction trio -- the latter
contingent on resolving its UNVERIFIED subject attribution); H6.P.Rahu (Moon+Saturn joining
Rahu); H7.L.1 (7th lord AND Venus afflicted -> clandestine relations); H8.L.5 (9th+8th lords in
the 5th with a debilitated Lagna lord).

**Plus H3.C.2 for coverage, not correctness:** *"Saturn will also give similar effects"*
(HTJAH-I:3353) is an unreachable second antecedent -- the H10.C.33 shape, differing only in
that the outcomes coincide.

**TWO SLOT INVERSIONS, and they are worse than mis-slotting.** H8.L.1 and H8.L.5 put Raman's
WEAK-lord relief in `fortified` -- *"If the 8th lord is WEAK or placed in the 6th, 8th or 12th
from Navamsa Lagna, the intensity of misfortune is reduced"* (HTJAH-II:2905) -- and `_branch`
shows `fortified` to STRONG-lord charts. **The relief is displayed to exactly the charts it does
not apply to, and withheld from the ones it does.** H2.L.8 is the already-known third instance.
These want the H2.L.8 treatment, and they are the next thing to do.

**One open reading question:** H2.C.54's navamsa clause -- the corpus renders *"worse if"* where
HTJAH-I:2674 reads *"These evil results should be anticipated IF..."*, i.e. a GATE, not an
intensifier. Under the gate reading the rule's whole afflicted payload is asserted on charts
Raman does not cover. The reviewer could not resolve the antecedent placement from the printed
text and left it open.


## VARGA DOCTRINE LANGUAGE (2026-09-02) — Gates 0-2: the gate opened, and immediately repaired a wrong reading

The milestone was deliberately NOT framed as "adding divisional charts". Three layers hide in
that phrase, and only the middle one was missing:

| Layer | Question | State |
|---|---|---|
| Computation | can the engine CAST D3/D7/D10/D12/D16/D30? | already yes — all 16 Shodashavarga |
| Doctrine language | can a Raman RULE say something happens in one? | **no — this milestone** |
| Synthesis | when/how strongly should a varga move a verdict? | **not solved; not attempted** |

### The measurement that set the scope

**Opening D10/D7/D12/D30 unlocks ZERO parked rules.** All 58 were classified by what they
actually need: 7 want D60 classes, 7 are dasha-timing, 4 navamsa-Lagna/dispositor, 3 drekkana,
1 "cruel navamsa", 1 parity — **none name D10, D7, D12 or D30.** So the payoff is expressive
capacity, not rule count, and it was scoped and reported that way rather than oversold. The
near-term unlock is the NAVAMSA predicates, which the same generalisation delivers.

Also measured, and it changes the roadmap: the golden extractor now yields 569 presentations,
206 verified, **5 new and 0 carrying a verdict.** Playbook rule 7 still names corpus growth as
the accuracy lever; that is out of date. The bottleneck has moved from corpus VOLUME to
doctrine REPRESENTATION and validation.

### Gate 0 — `tools/raman_saab/doctrine_snapshot.py`, and why the ratchet was not enough

The golden ratchet scores 397 rows and is blind to everything else: `_bucket_fired` buckets by
`rule.polarity` and never looks at the branch, so a change can hold 286/362/35 exactly while
altering what hundreds of charts SAY. The snapshot freezes three levels for every castable
golden — varga signs (primitive), fired rules with branch and text-hash (predicate), and
per-signification verdicts — and `--write` refuses to overwrite without a `--note`, so every
re-freeze is a recorded decision.

**It caught its own construction bug on the first run:** the verdict level came back empty on
all 346 charts because `getattr(hv, "significations", {})` silently defaulted a wrong attribute
name. A level that records nothing reads as "identical" forever. It now delegates to the golden
harness's own `evidence_snapshot` (so the tool and the tests cannot disagree about what a
verdict IS) and raises rather than writing a snapshot that cannot detect change.

### Gate 1 — the gate itself

`_SUPPORTED_VARGAS` went `{"D9"}` -> `{D1, D3, D7, D9, D10, D12, D16, D30}`. The chart layer
now owns a canonical `VARGA_NUMBERS` / `varga_sign_by_name`, and doctrine addresses a division
by NAME, never by harmonic number — the question a rule asks is "this planet's D10 sign per the
engine's canonical implementation", not "compute the tenth harmonic", and that distinction will
matter the first time a convention is audited (the published schemes for D30 and D60 differ).
**D1 is documented as the Rasi/radix, not a derived varga**, so a varga="D1" rule is never
reviewed as a varga rule.

D9 is NOT special-cased: `PlanetPos.navamsa_sign` is set to `varga.navamsa_sign(lon)` by both
constructors and `_VARGA_FN[9]` is that same function, so reading it through the named API is
identical by construction — pinned for every planet of every golden. One path beats a bridge
that could quietly diverge.

**Acceptance: primitive + predicate + report equality, all three IDENTICAL across 346 charts.**

**D60 is deliberately ABSENT, and the reason is stronger than "we did not find it":**

```
D60 named-class doctrine (Ghora / Rakshasa / Kulaghna / Devaloka ...)
STATUS: BLOCKED - source attribution
REASON: no citable Raman source identified. Checked HTJAH-I, HTJAH-II, HPA and GBB;
        GBB's 21 "Shashtiamsa" occurrences are the UNIT of Shadbala (1/60 rupa), an
        unrelated meaning that reads as a hit on a lexical sweep.
DO NOT SUBSTITUTE: a non-Raman classical source. Seven rules stay parked; that is the
        correct state, not a gap to close.
```

### ★ Gate 2 — TWO ROUTING DEFECTS, found by using the new capability

Repairing H8.L.1/H8.L.5 required emptying a strength slot, which exposed that `_branch` and
`fire_rules` answer an empty slot with **the opposite pole**:

- a STRONG subject with `fortified=None` was routed to the AFFLICTED text;
- a WEAK subject with `afflicted=None` was routed to the FORTIFIED text.

Both now prefer Raman's `general` slot, which is true of every chart. Measured over the corpus:
**650 rule-instances across 219 of 346 charts (63%) stopped being shown a strength-conditioned
reading the chart does not satisfy. 0 primitive changes, 0 verdict changes, ratchet unmoved.**

The sampled cases show the defect was worse than "wrong pole": `H9.P.Mars` and `H8.P.Moon`
carry `afflicted` slots annotated **"(conjunctions, not afflictions)"** — conjunction riders,
not affliction readings. A strong-Mars chart was shown "with Venus -> two wives and foreign
residence" INSTEAD OF Raman's base reading, "wields authority and is affluent; has children and
is happy".

### ★★ THE SLOT IS A STRENGTH LABEL, NOT AN AFFLICTION LABEL — reviewer REVERSAL x2

`_branch` selects `afflicted` on WEAK Shadbala (`is_powerful` -> the GBB-8:303 minimum-required
table). Filing Raman's affliction-gated sentences there was a **name pun**, and it made both
branches assert falsehoods about the chart being read.

That weak != severely-afflicted is settled INSIDE the same table, not inferred. At
**HTJAH-II:3001-3009** Raman runs three tiers over one entry: *"If the lord of the 8th house
occupies the 8th house **in strength**... If the 8th lord is **weak**, he may have no serious
troubles but may not also enjoy any luck... If the 8th lord is **afflicted**, the native will
fail in his undertakings."* Three antecedents, three non-nested outcomes. **HTJAH-II:273-276**
repeats it on the 7th lord, and its next clause — "both afflictions **and** benefic influences
on the 7th lord" — shows affliction is Raman's INFLUENCE axis, orthogonal to STRENGTH.

**Semantic snapshot — H8.L.1** (HTJAH-II:2902)
```
SOURCE    HTJAH-II:2902-2914, three sentences on TWO axes
BEFORE    fortified = "misfortune reduced when 8th lord is weak or in 6/8/12 of Navamsa-Lagna"
          afflicted = the severe-affliction reading
AFTER     fortified = "the 8th lord strong - ... undiminished"   (Raman writes no strong-lord
                      sentence; the only mitigation is gated on weakness, so its absence
                      leaves the misfortune undiminished)
          afflicted = "the 8th lord weak - the intensity of the misfortune is reduced"
          H8.L.1a   = the Navamsa disjunct, now a PREDICATE (evaluable, D9)
          H8.L.1b   = the severe-affliction clause, descriptive, TODO(affliction predicate)
RATIONALE both branches asserted an antecedent the branch had just measured false
EXPECTED  presentation only; 0 verdict movement
```

**Semantic snapshot — H8.L.5** (HTJAH-II:2957) — FOUR antecedents packed into three slots
```
BEFORE    fortified = mitigation (placement-gated) AND intensification (strength-gated),
                      two clauses pointing opposite ways in one sentence
          afflicted = the heavy-affliction clause AND a SEPARATE combination (2972)
AFTER     fortified = "the 8th lord fortified - the evil results are intensified"
          general   = restored, incl. the father-misunderstanding strand (2960) the old
                      text had dropped
          afflicted = None -- Raman gives this entry NO weak-lord reading
          H8.L.5a   = the Navamsa mitigation (2965), a PREDICATE. Placement-only: unlike
                      H8.L.1 there is no "weak or" disjunct, so it can never be reached by
                      a strength branch at all.
          H8.L.5b   = the heavy-affliction clause (2962), descriptive
          H8.L.5c   = the 2972 combination as its OWN rule
RATIONALE the worst display error in the file: any chart with merely a weak 8th lord -- no
          9th lord involved, Lagna lord in fine dignity -- was told it had "no knowledge or
          wealth, lustful, reviled". A missing rule masquerading as a branch.
EXPECTED  presentation only; 0 verdict movement
```

`afflicted=None` is only SAFE because of the routing fix above; before it, emptying the slot
would have shown a weak lord the intensification reading — the exact opposite of nothing.

### Satisfiability, because these rules fire on nothing

H8.L.1a / H8.L.5a / H8.L.5c fire on **ZERO of 346 goldens** — their parents already fire on
only 3 and 1, the H8 conditions having been narrowed in 2026-09-01 to Raman's actual
conjunction predicate, and these are strictly narrower still. A rule the ratchet never
exercises is exactly playbook rule 4's coverage-gap blindness, so each is **proved satisfiable
by explicit witness** (`test_h8_slot_reversal.py::TestSatisfiableByConstruction`) rather than
assumed. Liveness re-based 59 -> 62, consciously, with the reason recorded in the baseline.

### ★ OPEN — needs a USER decision, flagged by the reviewer at LOW confidence

**H8.L.5's "kendra or trikona" frame (HTJAH-II:2967).** *"But if fortified in a kendra
(quadrant) or trikona (trine), the evil results are intensified."* Under a **D1** reading the
placement half is satisfied BY CONSTRUCTION — the rule already places the 8th lord in the 5th,
and 5 is a trikona (`conditions.py:46`) — reducing the clause to pure strength. But the
parallel entry at **HTJAH-II:2986-2988** says the evil is intensified if the 8th lord is "in a
kendra or trikona" of an entry whose own condition places it **in the 6th** — neither a D1
kendra nor a D1 trikona, so under the D1 reading that sentence is unsatisfiable and vacuous.
The reading that keeps both meaningful is the **navamsa** frame, and 2967 opens with "But",
contrasting directly against the D9 sentence before it. Currently shipped as the strength half
only, with the kendra/trikona qualifier NOT encoded — the safe subset either way. It decides
whether the fortified slot is exact or over-firing.

### ★ OPEN — a sweep the reviewer identified but did not adjudicate

**H8.L.2, H8.L.6, H8.L.9, H8.L.10, H8.L.12 all park Navamsa-placement or affliction clauses in
strength slots** — the same defect class, visible on inspection (H8.L.2's `fortified` reads
"evil reduced if 8th lord falls in 6/8/12 of Navamsa-Lagna": placement-gated, in a strength
slot). Worth ONE reviewed sweep rather than five edits. The Navamsa halves are all now
expressible via `InVargaHouseFrom`, which is what the gate was opened for.

### What Gate 2 proves about the milestone

The first two rules in the corpus to reach a varga through the **generic, reviewable**
condition rather than a hand-rolled local subclass are H8.L.1a and H8.L.5a — and they exist
because opening the gate was what let a known-wrong reading be repaired instead of merely
described. That is a materially stronger milestone than "we added six varga types", and it was
the reason B1 was sequenced immediately after A1.


## ★ THE STRENGTH-SLOT DEFECT (2026-09-02) — corpus-wide, 7/7 REVERSAL where reviewed

Two more engine-blind reviews were dispatched after the H8.L.1/H8.L.5 reversal. Both came back
REVERSAL on everything they examined. **Across H8.L.2/6/9/10/12, ZERO of the ten populated
strength slots was gated on the 8th lord's strength** — the branch subject.

### The defect, stated once

`_branch` selects `afflicted` on WEAK Shadbala (`is_powerful` -> GBB-8:303). The slot is a
**STRENGTH label**. Any clause Raman gates on something else — an affliction, a conjunction, a
varga placement, another planet entirely — is untestable by that branch, so filing it there
shows the reading to charts selected by a test that never examined the stated antecedent.

Three shapes, in rising severity:

1. **Untestable antecedent in a strength slot** — H8.L.2's `fortified` held ONLY the D9
   placement clause (HTJAH-II:2923-2925), with no strength term anywhere in the entry.
2. **Unconditioned headline in `fortified`** — H8.L.6's Rajayoga (2978-2980), H8.L.10's "may
   ALSO confer unexpected gains" (3038-3040, which restates the PLACEMENT as its antecedent),
   H8.L.12's Rajayoga (3053-3054). Not a false assertion but a wrong **WITHHOLDING**: weak-lord
   charts never saw Raman's main reading for the entry. That inverts him.
3. **Another planet's condition in the 8th lord's slot** — H8.L.9's Sun and 9th lord, H8.L.10's
   2nd lord. H8.L.10's encoding also **silently dropped half its antecedent**: Raman requires
   the 2nd lord afflicted AND joining the 8th lord (3034-3036), so the encoded sentence was a
   strictly weaker claim than his.

### H8.L.9 was REMOVED, not repaired

Not one of that entry's sentences is gated on the 8th lord's strength, and Raman states no
unconditioned reading for it — so the base record had nothing legitimate to say. A strong-8th-
lord chart with malefics on the 8th lord was shown the INHERITANCE reading; a weak one with
benefics on it was shown the DISINHERITANCE reading. Backwards in both directions. Content now
lives in H8.L.9a..e, each with its own antecedent and citation. It was also listed in
`test_general_reading_slot.LEFT_ALONE` as a rule that "really does give an afflicted reading" —
true of the TEXT, false of the SLOT, which is the whole distinction.

### Material Raman states that the corpus never carried at all

Found by reading the source, not by auditing slots — a slot audit cannot see an absence:

- HTJAH-II:2989-2991 — the 6th lord fortified -> overcomes all troubles, enemies fail (H8.L.6b)
- HTJAH-II:3023-3025 — the D9 6/8/12 mitigation for the 9th-house entry (H8.L.9e)
- HTJAH-II:3036-3038 — the D9 6/8/12 mitigation for the 10th-house entry (H8.L.10b)

### ★ TWO UNSATISFIABILITY PROOFS, and what they decided

**H8.L.12b — Raman re-opens his own antecedent.** At 3061 he restarts with *"If the 8th lord is
in the 12th house"*, DROPPING *"with the 12th lord"*. Under the conjunction the 12th lord is in
the 12th by construction, and the 12th is neither trine nor quadrant, so the clause was
**unsatisfiable as encoded** — a display promise that could never be met. Freed of the
conjunction it fires on **15 goldens**. This is one place where the 2026-09-01 conjunction
narrowing of this file genuinely does not apply.

**The dignity proxy is a CONSTANT, not a conservative approximation, for two clauses.** H8.L.6's
6th lord is in the 6th house by the entry's premise, hence in its own sign, so
`LordHasDignity(6,{"own",...})` is tautologically TRUE on every firing chart; H8.L.9's 9th lord
is likewise in its own house, making `LordHasDignity(9,{"debil"})` tautologically FALSE. Neither
can stand in for Shadbala here. Both clauses ship descriptive.

### ★ THE KENDRA/TRIKONA FRAME — settled, and the answer is "do not encode it"

A dedicated review surveyed **~160 kendra/trikona/quadrant/trine occurrences across both
volumes**. Result:

- **Every occurrence that names a frame names a RASI origin** — "from Lagna", "from the
  Ascendant", numbered "(1, 4, 7, 10)", "from the Moon", or from a named planet. **Zero** pair
  the category words with a navamsa origin.
- Conversely the **~120 navamsa references are ALWAYS marked** ("in Navamsa", "from Navamsa
  Lagna") and **always use bare ordinals** — never the category words. That register split is
  the most consistent habit in the book and is what decides it.
- **The "But" argument is refuted.** HTJAH-II:2905 offers *"If the 8th lord is **weak or**
  placed in the 6th/8th/12th from Navamsa Lagna, the intensity is reduced"* — weakness and
  navamsa-dusthana as interchangeable alternatives for the SAME mitigation. So the "But" at 2967
  negates **weakness**, and its negation is **fortification**: a strength contrast, not a frame
  continuation.
- **HTJAH-II:7923 fixes the idiom**: *"If the 9th lord is in a kendra or the 11th house or
  aspects the 9th house **or is otherwise fortified**"* — kendra-occupation enumerated as a
  member of the class *fortified*.

**Verdict: D1 at MEDIUM — and MOOT for encoding at HIGH.** Both candidate frames agree the
operative content is *8th lord strong -> evil intensified*, which is exactly what H8.L.5 already
ships with no positional qualifier. **Do not add a kendra/trikona predicate on either frame**:
on D1 it is satisfied by construction (H8.L.5) or unsatisfiable (H8.L.6); on D9 it would be the
only unmarked-navamsa reference in the corpus. H8.L.6's tag is carried as PROSE, labelled as
idiom.

### The scale, measured — this is not an H8 problem

A lexical triage over all 776 evaluable rules (TRIAGE ONLY; it orders the queue, it never
adjudicates a slot):

| antecedent type parked in a strength slot | rules |
|---|---|
| placement / varga | 59 |
| conjunction | 44 |
| affliction | 43 |
| a different planet's condition | 15 |

**148 of 776 (19%), in all twelve houses** — H8 27, H2 20, H12 18, H9 16, H1/H7/H11 14 each.
The reviews landed on H8 because that is where we looked.

**The bounded sub-queue the opened varga gate unblocks: 9 rules** state a varga placement as an
antecedent in a strength slot WITHOUT encoding it (nine others already encode theirs correctly):
`H2.L.7, H2.C.57, H8.L.2 (fixed), H8.P.Venus, H9.L.9, H9.B.23, H9.B.29, H10.L.3, H10.P.Saturn`.
Two are already self-annotated as misfiled — H10.P.Saturn reads "(a configuration, not an
affliction)", H8.P.Venus "(affliction in substance, though Raman does not use the word)". Note
H9.B.23 also wants a **malefic shashtyamsa (D60)**, which stays BLOCKED on source attribution.

### Machinery gaps, ranked by how many split-offs they block

1. **No Shadbala `IsPowerful`/`IsWeak` Condition exists** in `conditions.py`. Blocks H8.L.6b and
   H8.L.9d, and the documented dignity proxy is provably unusable for both (above). This is the
   single highest-value predicate to build next.
2. **No generalised planet-affliction predicate** — `_MaleficAfflictsLagnaLord`
   (`house_01_lagna/combinations_core.py:99`) hardcodes the Lagna lord. Blocks six split-offs
   (H8.L.1b, H8.L.5b, H8.L.6a, H8.L.9c, H8.L.10a, H8.L.12c).
3. **`ClassInHouseFrom` has no subject-exclusion set** — it counts the very lords the rule is
   about inside its benefic/malefic quantifier, so "benefics joining the 8th lord" is satisfied
   by the 8th and 9th lords themselves whenever either is a benefic. Blocks H8.L.9a/9b/12a.
4. **`InVargaHouseFrom` — exists and is proven**, and unblocked three of the four missing D9
   mitigations immediately. This is what the varga gate was opened for.

### FIXED in passing: a condition that was silently always False

`InHouseClass.evaluate` read `chart.planets` directly, so a `"LORD_OF:n"` subject resolved to
`None` and the condition **returned False for every chart ever cast**. H8.L.12b would have been
a dead rule that looks alive. Every sibling condition already routed through `_resolve_planet`;
this one was simply inconsistent. Static names pass through unchanged, so no shipped rule
changed behaviour — pinned by a test.

### Measurement

**5 VERDICT changes** — the first verdict movement of the milestone: four degree-only
(mild -> strong on H8/longevity) and one grade change (HTJAH-II.x146 H8/death,
afflicted -> mixed). All trace to H8.L.12b, which fires on 15 charts. **The ratchet is UNMOVED
at 286/397 exact, 362/397 within-1, 35 inversions** — no moved verdict falls on a scored row.
Liveness `never_fired` UNCHANGED at 62: all four new evaluable rules fire.

Both gates therefore pass independently: doctrinally validated at HIGH confidence, and
empirically neutral. Had they conflicted, the citation would have won — that is the standing
rule, and the H8 re-base of 2026-09-01 is the precedent.

### Still open

- The **remaining 8 rules** of the varga sub-queue, and the wider 148-rule triage. One reviewed
  sweep per house, not per rule.
- **`RuleRecord.fortified` is annotated `str`** (`doctrine/rules.py:37`) while `afflicted` and
  `general` are `Optional[str]`, and eleven records now pass `fortified=None`. Runtime is fine
  (`fire_rules` tests truthiness); the annotation is simply wrong.
- **A polarity/display mismatch worth its own pass**: H8.L.6 carries `polarity="neutral"` and
  H8.L.12 `polarity="malefic"`, though both entries now open with an unconditioned Rajayoga in
  `general`. Slot moves cannot change a verdict (bucketing is on `polarity` alone), but a
  Rajayoga displayed under a malefic-bucketed record is visible to a reader.


## ★ THE UNBIASED BASE RATE (2026-09-03) — House 5 is 5/12, with ZERO inversions

House 8 came back 7 of 7 defective. **That number could not be extrapolated, because House 8 is
where a defect had already been found** — the same selected-pool error that produced the
"88.4% ceiling", which turned out to be a ceiling on a pool that could only admit agreements.
So House 5 was swept: chosen for volume, never examined by the strength-slot lens, and the
reviewer was told in the prompt that "all twelve are correctly encoded" would be a useful
answer. It was asked for a number, not for defects.

**Result: 5 of 12 correctly encoded (H5.L.2, L.3, L.5, L.6, L.7), and ZERO inversions.**

The reviewer supplied its own sensitivity, which is the honest way to read it:

| standard | figure |
|---|---|
| inversion-or-withholding only | 8 of 12 |
| **as reported** (every sentence in a slot whose test matches its own antecedent) | **5 of 12** |
| counting the table-wide axis question | 0 of 12 — *meaningless as a base rate* |

**House 5 is materially healthier than House 8, and its defects are a different, milder kind.**
H8's seven were INVERSIONS — readings asserting of a chart the opposite of what the branch had
just measured. House 5 has none. Its seven are: text dropped by sentiment, a third tier the
binary branch cannot express, an encoder-invented slot, three unconditioned readings misfiled,
and one folded combination. **Four of the seven repeat repairs this project had already shipped
elsewhere for the identical textual shape** — corroboration, not reviewer over-reach.

A caution the reviewer volunteered and which should be honoured: House 5 is itself
**pre-enriched** for one defect, because DOCTRINE_BACKLOG already listed H5.L.1 and H5.L.4 among
the four known three-way partitions. The other two are **H6.L.9 and H6.L.11 — inside a house
previously ruled "EXPLICIT-AFFLICTED, correctly encoded throughout"**. That ruling is now in
tension with a fact this backlog itself records. **Sweep House 6 next.**

### The seven repairs

- **H5.L.1** — *"will have foes"* (5114) was SILENTLY DROPPED. Raman lists it between "few
  children" and "gives happiness to others"; the encoding kept both flanking items and deleted
  the one in the middle. That is trimming by SENTIMENT, not by antecedent — a negative result
  removed from a favourable arm. Restored.
- **H5.L.4** — the slot welded two antecedents with different outcomes: *"The lord, afflicted,
  causes death of children"* (5134) and *"The lord, moderately strong, confers daughters and no
  sons"* (5134-5135). Under the binary branch both displayed together, telling one reader that
  children die AND that daughters are born.
- **H5.L.8 — an ENCODER-INVENTED slot.** `fortified` read *"no specific benefit noted"*, a
  phrase that appears in NEITHER volume. HTJAH-I:5153-5154 is four flat declaratives with no
  conditional clause anywhere. **Cleared, not relocated**, per the H10.L.1 precedent: moving
  unsourced prose into `general` would launder it into a slot asserting Raman said it. Every
  strong-5th-lord chart had been shown the editorial line INSTEAD of Raman's only reading.
- **H5.L.9** — no favourable opener exists; the base is flat and the gate appears only in the
  last sentence. Identical in shape to H9.L.6 and H9.L.8, repaired 2026-09-01.
- **H5.L.10** — *"If aspected by the Sun"* (5162) is a separate antecedent with its own
  outcome, folded into the fortification arm, so a strong 5th lord with no solar aspect
  anywhere was told it may join the intelligence department. Now H5.L.10a.
- **H5.L.11 / H5.L.12** — ungated entries labelled strength-conditioned. `fortified` is KEPT
  alongside `general` per the H1.L.10/11/12 precedent; the defect was the LABEL, not the
  display.

### ★ OPEN — DOCTRINE-CONTESTED, needs USER SIGN-OFF, and deliberately NOT acted on

> **MEASURED 2026-10-24 (DISPOSITION_PILLAR_PREREG.md): letting the influence axis vote in the
> verdict makes the engine LESS faithful to Raman (real errors 30 -> 38, or 44 with a house-influence
> pillar; a veto-only form changes nothing). Pre-registered, no variant passed, nothing shipped.
> The Shadbala-pillar convention stands on evidence now, not only by precedent.**

**HTJAH-I:5173-5175 closes this table by naming its own axis, and it is not Shadbala:**

> *"...paying particular attention to the **benefic, malefic, or moderating nature of the
> lord** qualified or modified otherwise **by the association or aspect of the other planets
> and lords**."*

Three tiers, on a NATURE-plus-ASSOCIATION axis. It maps exactly onto the three qualifiers Raman
actually uses — *favourably disposed* / *moderately good* / *afflicted* — and explains why L.1
and L.4 have a middle tier at all. HTJAH-II:7479-7481 glosses it independently (*"beneficially
disposed **by aspect or association**"*), and HTJAH-II:7906-7910 lists strength and
aspect/association as two separate inputs whose poles are *afflicted / beneficially disposed*.

**This was NOT counted as twelve defects, and must not be reported that way.** It is true of
Houses 1-7 and 9-12 identically; the project has a standing contrary convention adopted
deliberately (this backlog, "Every qualifier elsewhere is SCALAR and unnamed"); and unlike H8 it
does not INVERT — Shadbala is a lossy proxy for disposition, not its opposite. Overturning it is
a corpus-wide, user-signed decision touching all 132 lord-in-house rules, not a reviewer's
verdict on twelve records.

**Corroborating tell, in HTJAH-I this time:** at 5121 Raman writes *"Lord **weak and
afflicted**"* — a conjunction of two qualifiers, where every other entry says plain "afflicted".
He would not conjoin synonyms. The weak != afflicted distinction established from HTJAH-II holds
in this volume too.

## AfflictedBy — one shared predicate replacing ten hand-rolled variants

The rule sets had re-invented the affliction predicate **ten times, once per house**
(`_MaleficAfflictsLagnaLord`, `_AfflictsPlanet`, `_AfflictedBy`, `_LordAfflictedBy` and
siblings). Every variant agreed on the substance — same rasi house, or a true whole-sign
drishti — so the duplication bought nothing and left each house free to drift.

`conditions.AfflictedBy(planet, afflictors=None, min_count=1)` is the shared form. `planet`
accepts "LORD_OF:n", so a dynamic house lord resolves per chart.

**`min_count` carries DEGREE, and that matters doctrinally.** Raman distinguishes plain
affliction from *"severely afflicted"* (2906) and *"if the affliction is heavy"* (2962).
Encoding those as a bare boolean would fire them on one mild contact and assert a severity he
did not. The corpus already had a convention — `_PutraKarakaDoublyAfflicted` and its siblings
read ">= 2 of the FIRST-RATE malefics", Sun excluded — so severity REUSES it via
`FIRST_RATE_MALEFICS` rather than inventing a second scale.

Five H8 clauses converted descriptive -> evaluable: H8.L.1b and H8.L.5b at min_count=2 (Raman
says severely/heavy), H8.L.6a, H8.L.10a and H8.L.12c at min_count=1 (he says plain "afflicted").
Three of the five fire (1, 6, 3 of 346). H8.L.9c stays descriptive: its consequent is a
dasha-timing claim, outside the atemporal EvalContext.

## FIXED: a second condition that was silently always False

`Aspects` resolved neither end through `_resolve_planet`, and `drishti.aspects_planet` rejects
any name absent from `chart.planets` — so `Aspects("Sun", "LORD_OF:5")` returned False for every
chart ever cast. H5.L.10a would have been **dead on arrival**. This is the SECOND condition
found with this exact defect in two days (`InHouseClass` was the first), which makes it a
pattern worth a sweep: **any Condition that reads `chart.planets` directly instead of going
through `_resolve_planet` silently rejects a "LORD_OF:n" subject.**

## Measurement

3 VERDICT changes, all degree-only (moderate -> mild on H8/longevity), from the AfflictedBy
conversions. **Ratchet unmoved at 286/397 exact, 362/397 within-1, 35 inversions.** Liveness
never_fired 62 -> 65, consciously: H5.L.10a, H8.L.5b and H8.L.10a fire on no golden — each
proved satisfiable by explicit witness, because a rule the ratchet never exercises is exactly
playbook rule 4's coverage-gap blindness. Suite 6020 passed.

## What the two houses together now say about the programme

The corpus-wide lexical triage flagged 148 of 776 evaluable rules. **That number remains
triage, and the two sweeps show why it cannot be converted to a defect count by extrapolation:**
House 8 ran 7/7 and House 5 ran 7/12, but their defects are of DIFFERENT SEVERITY — H8
inverted, H5 did not. A programme justified on "148 broken rules" would be overclaiming; one
justified on "two houses examined, both carried real defects, the severity varies by house" is
what the evidence supports. Sweep House 6 next, on the specific tension named above.

## HOUSE 6 SWEEP + THE REFINEMENT-POLARITY RULE (2026-09-03)

**Base rate, three houses in:** H8 0/7 correct (the outlier — it was sampled BECAUSE a defect had
been seen there), **H5 5/12, H6 6/12** (both sampled for volume, not suspicion). In fairly-chosen
houses roughly half the lord-in-house rules have text in a slot whose test does not match its
stated antecedent. **Neither H5 nor H6 has a single inversion** — no slot teaches the opposite of
its sentence, which H8 did seven times.

**H6 refuted its pinned ruling.** "EXPLICIT-AFFLICTED, correctly encoded throughout" was reached
by counting openers, and an opener count cannot see unconditioned sentences sitting BETWEEN
openers, welded third tiers, or openers that name a conjunction or another planet. H6.L.7 had
zero correctly-slotted content. Both backlog-recorded three-way partitions are real, but they are
different axes: H6.L.9 is a STRENGTH continuum ("well fortified / moderate / afflicted"), H6.L.11
an ASSOCIATION continuum ("benefice / ordinary / malefic", glossed by Raman at HTJAH-I:6064).

**The trap was avoided, on the evidence.** In the 6th house a strong lord legitimately strengthens
enemies and disease, so negative text in `fortified` is NOT a defect signal there: H6.L.4's
"dilapidated building" and H6.L.10's "sinful and destructive nature" are gated on "Well
fortified" / "If fortified" verbatim and are correct. H6.L.5 was wrong not for being negative but
because Raman attaches no condition to it at all.

### ★ RULE: a re-homed refinement DISPLAYS but does not VOTE

Measured: H6.L.7a ("the 6th lord afflicted -> divorce or the wife dies", HTJAH-I:6033) shipped as
a malefic House-6 rule and flipped **13 charts' H6/accidents from mixed to afflicted** — a clause
about the WIFE moving the native's ACCIDENTS verdict, which Raman never said. It is also double
counting: the parent H6.L.7 already votes for the same placement. That is playbook rule 4's
"evidence-redundancy" blindness, invisible to the ratchet (which stayed at 286/362/35 throughout).

The reviews that motivated every re-homed record adjudicated **slot**, not polarity. So the six
re-homed affliction refinements — H8.L.1b, H8.L.5b, H8.L.6a, H8.L.10a, H8.L.12c, H6.L.7a — are
`polarity="neutral"`: they show Raman's words and cast no second vote. This reverted the three
degree-only H8/longevity changes the H8 refinements had caused. **SEPARATE combinations keep
their polarity** (H8.L.5c, H8.L.12b): they are Raman's own paragraphs with their own antecedents,
not refinements of a parent's placement.

**Open, for its own measured decision:** whether a refinement whose clause speaks to the house's
OWN signification (H8.L.1b: severe affliction -> "disease and disfiguration", a longevity matter)
should vote after all. It is defensible; it was not reviewed; the neutral default keeps every
shipped change inside what was reviewed.


## HOUSES 1-3 STRENGTH-SLOT SWEEP (2026-10-13)

**Base rates:** H1 10/12, H2 3/12, H3 7/12 correctly encoded. Running total across six fairly-sampled
houses (1, 2, 3, 5, 6 and the H8 outlier excluded): 31 of 60 correct (52%). **No inversions anywhere
outside H8.** Every defect was a clause gated on something the strength branch cannot test.

**Applied by tool, not by hand:** `tools/raman_saab/apply_slot_changes.py` edits each RuleRecord by id
through the AST and re-imports to verify. Two of its own bugs were caught by its refuse-to-write guard
before touching a file: chained new records, and AST columns being UTF-8 BYTES (an arrow in the old
text made the cut land two characters late and eat a comma). Both have regression tests.

**Net effect:** 826 presentation changes, **0 verdict changes** (every new record is neutral). Ratchet
286/397, 362/397, 35. Liveness 65 -> 67 (H2.L.4a, H2.L.9a; proved satisfiable).

### Findings worth keeping

- **H1.L.4's strength reading belonged to the 4th lord** ("If the 4th lord is favourably disposed",
  HTJAH-I:1026) -- the module docstring's "nine fortification openers" was really eight for the Lagna
  lord plus one for another planet. Opener-counting cannot see whose strength an opener names.
- **H2 was the worst fairly-sampled house (3/12)**, and two findings are about Raman's own text, not
  the encoding:
  - **H2.L.2f -- Raman contradicts himself.** HTJAH-I:2506 sits under "In the second" (2nd lord in
    the 2nd) but gates on "the 1st and 2nd lords have exchanged their houses", which puts the 2nd
    lord in the 1st. The antecedent cannot hold with its own heading. Kept, descriptive, never fired.
  - **H2.L.2c -- a general remark parked inside one entry.** "Exaltation, or disposition in Lagna,
    4th, 5th, 7th, 9th or 10th will make him a Yoga Karaka" (2339) cannot hold while the 2nd lord is
    in the 2nd. Encoded unscoped it would fire on about half of all charts; parked pending an
    overlap check against the H2 combinations.
- **Strength-plus-something clauses use the dignity proxy** (H2.L.4a, H2.L.7a, H2.L.9a): leaving the
  text `fortified`-only would show a strength-gated reading to a WEAK lord via `_branch`'s fallback.
  The proxy under-fires but never mislabels. Replace with a Shadbala Condition when one exists.
- **Planet identity is expressible exactly by sign** (H3.L.3a-c): Mars in the 3rd in Aries or Scorpio
  IS the 3rd lord in the 3rd. The old annotation said this needed a new predicate; it did not.
- **Old pins overturned, with reasons recorded in the tests:** `H2_SPLIT` and `H3_SPLIT` are now
  empty -- every "genuine afflicted clause" they pinned was gated on affliction, another planet or
  two houses, never on the lord being weak.


## HOUSES 4, 7, 9 STRENGTH-SLOT SWEEP (2026-10-13)

**Base rates:** H4 8/12, **H7 0/12, H9 1/12**. Both H7 and H9 had been pinned "ruled CORRECT" by an
earlier review -- the same pin House 5 carried before scoring 5/12. They turned out to be the worst
fairly-sampled houses of the sweep: nearly every conditional sentence in their tables is gated on
AFFLICTION or BENEFIC contact. In H7 Raman gives exactly ONE sentence gated on the lord's strength
alone (HTJAH-II:273, "If the 7th lord is weak, there may be no children"); in H9, none at all --
the section's only strength clause is the closing "very powerful" remark at 7398, a band above
`is_powerful`'s minimum, now parked as H9.L.S1. Running total, eight fairly-sampled houses (H8
excluded): 40 of 96 correct (42%). Still no inversions outside H8.

**Net effect:** 1652 presentation changes; 44 new records, all neutral; H9.L.2 removed. Ratchet
286/397, 362/397, 35. Liveness unchanged -- every new evaluable record fires on real charts.

### ★ Correction to "neutral = no vote" -- measured, and it matters

Neutral records never push a verdict towards favourable or afflicted. But whether ANY rule fired
decides whether a signification is judged at all (house_template clause 7: nothing fired ->
insufficient-evidence). Removing H9.L.2 (neutral, content-free: Raman gives nothing unconditional
for the 9th lord in the 2nd) changed ONE unscored chart: on HTJAH-II.x155 it had been the only rule
firing for H9 fortune/dharma/higher_learning/long_journeys, so its mere presence let the engine judge
those on strength pillars ("afflicted"). Without it they honestly read insufficient-evidence. A
verdict resting on a content-free rule is not Raman's; the abstention is the faithful state.
Adding neutral records could, in principle, do the reverse on charts where nothing else fires --
which is why every batch is measured against the doctrine snapshot, not assumed.

Also checked: the functional-nature overlay (`_bucket_fired`, HTJAH-I:523-604) promotes a NEUTRAL
rule to malefic when its subject is a functional malefic -- but `_rule_subject` only parses
planet-in-house ids (`H<h>.P.<Planet>`). No lord-in-house record, new or old, is ever promoted.

### Findings worth keeping

- **Six more LORD_OF traps** (HasDignity, IsYogaKaraka, MutualAspect, Exchange, HemmedBy,
  FunctionalNature), found because the H9 review had to route around HemmedBy. They hand the raw name
  to a helper instead of reading `chart.planets`, which the first guard could not see. The guard now
  requires `_resolve_planet` in ANY Condition that takes a subject planet. Zero live rules affected.
- **`InfluencedBy` + `FIRM_BENEFICS`** (Jupiter, Venus): benefic-contact clauses read true instead of
  `AfflictedBy(lord, {"Jupiter","Venus"})`. Moon and Mercury excluded -- conditional benefics in Raman.
- **"Weak AND afflicted" cannot be faked** (H7.L.7a): a weak-slot record conditioned on affliction
  would still show to a STRONG afflicted lord, because `fire_rules` falls through to the weak text
  when the other slots are empty. Parked until a Shadbala Condition exists. A reviewer proposed the
  trick; the code path refuted it.
- **H4.L.3's 2026-09-01 "fix" was half-right**: the Satyacharya note's condition is favourable, but it
  is subha VARGAS / benefic ASPECTS, not Shadbala, so `fortified` was the wrong home too.
- **H9.L.4a keeps Raman's misprint** ("may not have any domestic unhappiness" inside an affliction
  clause), flagged [sic], not silently corrected.
- **The marriage monograph hardcoded "of the 50 encoded"** -- stale long before this sweep took House 7
  to 84 evaluable rules. Now computed, and the unconditioned group is named "general", not "other".

### Open (polarity, out of slot-repair scope)

H7.L.8 and H7.L.12 are `malefic` parents whose `general` text is now mostly unconditioned and not
malefic. Polarity drives verdicts, so it is its own measured decision.


## ★ THE TWELVE-HOUSE STRENGTH-SLOT SWEEP IS COMPLETE (2026-10-13) — final tally and what it means

Every lord-in-house table (12 houses x 12 entries) has now been read against Raman's printed text by
an engine-blind reviewer, sentence by sentence, under one fixed question: *does each sentence sit in
a slot whose selection test matches its own stated antecedent?*

| House | correct | | House | correct |
|---|---|---|---|---|
| 1 | 10/12 | | 7 | **0/12** |
| 2 | 3/12 | | 8 | 0/7 (biased sample) |
| 3 | 7/12 | | 9 | **1/12** |
| 4 | 8/12 | | 10 | **0/12** |
| 5 | 5/12 | | 11 | **1/12** |
| 6 | 6/12 | | 12 | 5/12 |

**Fairly-sampled total (H8 excluded): 46 of 132 correct (35%).** The HTJAH-II houses (7, 9, 10, 11,
12) are far worse than the HTJAH-I houses (1-6): 7/60 against 39/72. The likely reason is visible in
the text: HTJAH-II's entries carry many more mid-entry conditionals, nearly all gated on affliction
or benefic influence -- which an encoder reading "afflicted" naturally filed in the slot of that
name.

**The defect, stated once for the record.** `_branch` selects the slot called `afflicted` on WEAK
Shadbala. It is a strength label. Raman keeps strength and affliction apart (HTJAH-II:3001-3009 runs
"in strength / weak / afflicted" as three tiers on one entry; HTJAH-I:5121 writes "weak AND
afflicted"). Every affliction-, conjunction-, aspect-, placement- or identity-gated sentence filed
there was shown to charts chosen by a test that never examined its antecedent.

**Inversions: only in House 8.** Nowhere else did a slot teach the opposite of its sentence. Outside
H8 the harm was showing a reading whose condition was never tested, withholding Raman's main reading
from weak-lord charts, or mislabelling an unconditioned reading as strength-conditioned.

### Net effect on the engine

- **Verdicts:** across all twelve houses, the only verdict changes the doctrine snapshot recorded
  were the ones already documented (HTJAH-II.x155's H9 abstention, plus the earlier H8.L.12b and H6
  polarity episodes). Every re-homed record is neutral. **Ratchet unmoved throughout: 286/397 exact,
  362/397 within-1, 35 inversions.**
- **Presentation:** thousands of rule-instances now show the sentence whose antecedent the chart
  actually satisfies.
- **Records removed** because Raman gives them no unconditioned reading: H8.L.9, H9.L.2, H10.L.10.
- **Missing doctrine recovered:** dozens of dropped clauses and dropped words, plus section-level
  sentences encoded nowhere (H9.L.S1/S2, H11.L.S1/S2, H12.L.S1 -- the last a Lagna-lord clause
  dropped corpus-wide).
- **Liveness 59 -> 69 over the arc**, every dormant record proved satisfiable by explicit chart.

### What the sweep could NOT encode -- the remaining queue, ranked by how much it unblocks

1. **A Shadbala strength Condition** (strong / weak for any lord or named planet). Blocks the most:
   every "weak AND afflicted" clause (H7.L.7a, H10.L.10b), every named-planet strength clause
   (Venus in H6/H7/H12, Mars in H3, the 9th lord in H3/H8), and several fortified-only clauses that
   would otherwise leak to weak charts (H10.L.10a). It also lets the dignity proxy retire.
2. **House (bhava) affliction.** Raman often afflicts the HOUSE, not the lord (H10.L.2a, H10.L.11a,
   H12.L.1c, H7.L.2b, H3.L.6b).
3. **Middle strength bands** -- every three-tier ladder (H4.L.1a, H11.L.1a, H6.L.9a, H5.L.4a).
4. **Yoga presence, nakshatra-lord friendship, sign/nakshatra gender, D60 classes** (the last
   BLOCKED on source attribution).

### Flagged, not acted on

- **Nodal drishti.** The `drishti`/`Aspects` code gives Rahu/Ketu 7th-only aspect, while CLAUDE.md
  locks "Rahu/Ketu drishti = Jupiter-style 5/9" -- though that lock also says "Not BV Raman (no nodal
  drishti)". The raman_saab engine appears deliberately Raman-faithful here; confirm with the user
  before touching either.
- **Parent polarity mismatches** (H7.L.8, H7.L.12 and similar): `malefic` parents whose `general` is
  now unconditioned and not malefic. Polarity drives verdicts, so it is its own measured decision.
- **Corpus-wide axis question** (House 5 review): Raman closes several tables naming a benefic /
  moderating / malefic NATURE-plus-ASSOCIATION axis, not Shadbala. The sweep kept the project's
  standing convention ("favourably disposed" = strength); overturning it is a user-signed decision.


## IsStrong / IsWeak (2026-10-13) — the strength check the sweep was waiting on

**What they are.** Raman's BINARY strength as a rule CONDITION, built on `effective_strength` (B1):
- `IsStrong(p)` = Shadbala meets the GBB-8:303 bar AND not combust AND not debilitated-uncancelled.
- `IsWeak(p)` = below the bar OR combust OR debilitated-uncancelled (`decisively_weak`).
- Unknown strength (Track-B charts, Rahu/Ketu) is never strong; only hard facts can make it weak.
- The B2 "marginal" band is neither -- it is a tuning band, not Raman's middle tier.

**Why not raw `is_powerful`.** Raman reads a combust ruler "powerless" even when well disposed
(HTJAH-I:3788), and gating on the raw number was tried before and over-fired (four HPA-20 yogas
deferred). Measured over the goldens: the raw bar calls a planet strong **198 times** where these
facts make it powerless.

**This is not the strength ontology the roadmap warned about.** No new vocabulary: it is the same
binary reading the engine already uses for slot selection, made available to conditions. Middle
tiers ("moderately strong", "middling") and the upper band ("very powerful") remain parked.

**What it unblocked.** 14 parked clauses went live (H1.L.4a, H3.L.4a-c, H6.L.2b, H6.L.6a, H7.L.6c,
H7.L.7a, H7.L.12c, H8.L.6b, H8.L.9d, H10.L.10a/b, H12.L.4a) and the dignity proxy was retired from
H2.L.4a/7a/9a. Strength goes INTO the condition and the text into `general` -- left in a strength
slot, `_branch` would test the rule's HOUSE lord with the raw number, the wrong planet for "Venus
weak". It also dissolved two tautologies a reviewer had proved: the dignity proxy is constantly
TRUE for a lord in its own house (H8.L.6b's 6th lord) and constantly FALSE for debility there
(H8.L.9d's 9th lord). Shadbala-with-overrides has no such blind spot.

**"Weak AND afflicted" is now exact** (H7.L.7a, H10.L.10b): `And(IsWeak(lord), AfflictedBy(lord))`.

### ★ A bug the promotion exposed, and the guard that now prevents it

Eleven re-homed records from the H6 and H8 sweeps had kept their parent's malefic/benefic polarity --
created before the "re-homed refinements are neutral" rule. Harmless while descriptive. Promoting
H6.L.6a to a live rule made it vote malefic and flip three H6/accidents verdicts. All eleven set
neutral; `test_rehomed_records_are_neutral.py` now fails if any re-homed record carries a vote,
with an explicit allowlist for the two genuine separate combinations (H8.L.5c, H8.L.12b).

**Net:** 115 presentation changes, **0 verdict changes**, ratchet 286/397, 362/397, 35. Liveness
unchanged at 69. H2.L.9a is proved satisfiable by a real cast chart (1950-01-03 06:00 IST,
Bangalore) since synthetic charts carry no Shadbala; H7.L.6c by debility alone.

### Flagged

- `effective_strength` counts ANY combustion (`combust > 0.0`) as powerless, while the `Combust`
  condition and the judge use a 0.5 orb fraction ("one threshold for the whole engine"). Two
  thresholds for one fact. Reused as-is here (reuse over a second definition); reconciling them is
  its own measured decision.
- `_branch` (slot selection) still uses raw `is_powerful`, so a combust lord with a high number can
  be shown its `fortified` text while `IsStrong` says it is not strong. Switching `_branch` to
  effective strength is presentation-only and would make the two agree; measure first.

## Nodal drishti -- RESOLVED 2026-10-13 (user: "follow Raman only, even for Rahu/Ketu aspects")

The Raman engine keeps **Rahu/Ketu = 7th aspect only**. Nothing in the engine changed; the
CLAUDE.md lock row was corrected because it claimed Raman gave the nodes NO aspect.

- Raman's aspect chapter (HPA-8) lists the 7th for all planets and the special aspects of Mars,
  Jupiter and Saturn; it never mentions the nodes.
- His worked judgments count the nodes' 7th repeatedly: HTJAH-I:2062 "Lagna is occupied by Ketu
  and aspected by Rahu. Lagna is therefore weak"; HTJAH-I:2221 (Jupiter with Rahu "aspected by ...
  Ketu"), 2720 (Ketu in the 2nd "aspected by Rahu"), 6092 ("aspected by Rahu or the Sun").
- No worked chart uses a nodal 5th or 9th. HTJAH-I:7107 "Rahu aspects Upapada" is in a Jaimini
  passage (sign aspects), a different system -- not evidence for Parashari node aspects.
- "No nodal drishti" would contradict Raman's own text, so it was rejected.
- `app/core/drishti_argala.py` (legacy engine; used by bhava_judge, gochara_engine,
  yoga_library) keeps 5/9. It is not Raman's engine; changing it is a separate decision.
- Guard: `test_drishti.py::test_ramans_ketu_lagna_aspected_by_rahu` (new) and the existing
  `test_nodes_cast_only_the_seventh_NOT_5_9`.

## HouseAfflictedBy (2026-10-13) -- house (bhava) affliction, queue item 2

**The condition.** A whole-sign house is afflicted when >= 1 natural malefic (Sun, Mars, Saturn,
Rahu, Ketu) OCCUPIES or ASPECTS it (nodes 7th only). `min_count` carries degree, as in `AfflictedBy`.
- One malefic suffices and the Sun counts: HTJAH-I:12018-12019 ("The 7th house is afflicted by the
  8th house aspect of Mars and occupation by Ketu"), I:11598, I:10392, II:3211.
- The house's OWN lord does not afflict it: HTJAH-I:2740-2741 ("This blemish is cancelled because
  Mars is in his own house"); HPA-8:64-67.
- Exception, also Raman's: an own lord debilitated WITHOUT cancellation and joined by a node loses
  the shield (HTJAH-II:2139-2161, Saturn aspecting his own 7th). Joined-by-one-node == aspected-by-
  the-other, so conjunction is the whole test. Kept to natural malefics; Raman's "rendered malefic"
  might also cover a benefic own lord -- deliberate under-fire.
- Benefic relief does NOT cancel the label (HTJAH-I:3769-3770, 8669, 11598): Raman weighs it
  separately.

**Base rate is high and that is Raman's threshold, not a bug.** Over 346 goldens (4152 house-slots)
a house is afflicted 64% of the time (57% without the Sun, 49% Mars+Saturn only, 27% with >= 2).
Mars and Saturn each reach four houses. This is the measured-truth mechanism again: classical
indications are abundant.

**Promoted (all neutral, text in `general`):** H7.L.2b (8 fires / 31 placements), H10.L.2a (20/35),
H10.L.11a (18/26), H12.L.1c (5/34; the "But" depends on the 6L+12L-in-Lagna clause, kept).
**H3.L.6b re-read by the doctrine review:** "the 6th and the 3rd are both afflicted" (HTJAH-I:3376)
means the LORDS -- the paragraph runs on lords and sets "afflicted" against "well disposed"
(medium confidence). Gated on `AfflictedBy("LORD_OF:3")` + `AfflictedBy("LORD_OF:6")`: 14/28.

**Net:** 65 presentation changes, 0 verdict changes, ratchet 286/397, 362/397, 35.

### Resolved same day: the Lagna lord (see below)

- **Does the LAGNA lord afflict?** (original open question) HTJAH-II:8368-8369 "Saturn does not afflict in the strict sense
  of the term being the Lagna lord" (also I:11598) says no; HTJAH-I:4405 ("good as lord of Lagna and
  bad as a natural malefic. The affliction is heavy") and I:5925 say it is both. Contested within
  Raman, so NOT adopted. Matters most for H12.L.1c (8th-house longevity).

### The Lagna lord does NOT afflict a house -- unless joined by a node (2026-10-13)

The user delegated the decision ("take decisions on well researched"). Two engine-blind
`bphs-doctrine-reviewer` agents read all of HTJAH-I/II and Notable Horoscopes independently and
**both** returned EXCLUDE, medium-high confidence.
- **Stated rule:** "ruler of Lagna is always the most benefic planet ... Saturn becomes the best
  planet ... though usually the worst malefic" (NH:15662-15665); "Saturn does not afflict in the
  strict sense of the term being the Lagna lord" (HTJAH-I:13193-13194 = II:8368-8369).
- **Practice:** 8-11 worked house cases read the malefic Lagna lord's occupation or aspect as relief
  or strength, e.g. "The house and lord are both powerfully disposed" (HTJAH-I:17133), "It is quite
  strong" (17153), "The aspect of the Sun on the 11th house prevents denial of elder co-borns"
  (16725). No house case reads it as plain affliction.
- **Mixed weighings** (HTJAH-I:4405 "good as lord of Lagna and bad as a natural malefic", 5925)
  attribute the heavy affliction elsewhere and never turn the house afflicted. Charts 8/64/93 are
  one native analysed three times; the later formal wording is "does not afflict".
- **Exception encoded:** joined by a node it afflicts again -- "Although Saturn as Lagna lord is a
  benefice, his association with Ketu ... renders him a malefic" (HTJAH-I:17253-17255); also
  I:17231 ("with a node, Ketu ... The 11th lord is blemished"). That is the overlap of both
  reviewers' proposed exceptions; broader triggers (any malefic aspect, 6th-lord association)
  rest on one chart each and would gut the rule, since most planets have some malefic contact.
- **Measured:** the Lagna lord was the sole afflicter in 188/3806 house-slots (4.9%). 4 firings
  dropped (H10.L.2a 1, H10.L.11a 3); 0 verdict changes; ratchet 286/397, 362/397, 35.
- **Scope:** `HouseAfflictedBy` only. `AfflictedBy` (planet affliction) still counts a malefic
  Lagna lord; whether the same principle should apply there is a separate measured decision.

## Middle and upper strength levels (2026-10-13) -- queue item 3: PARKED by research

Five sentences need a strength grade finer than strong/weak: "middling in strength" (H4.L.1a
HTJAH-I:4150, H11.L.1a HTJAH-II:14259), "moderate" (H6.L.9a I:6048), "moderately strong" (H5.L.4a
I:5134), "very powerful" (H9.L.S1 II:7398). Two independent engine-blind reviews (decision
delegated by the user; rule: adopt on agreement, keep parked on a split).

**Agreed (high confidence):**
- Raman prints NO multi-level scale. GBB-8:303-312 is one bar per planet; GBB-8:333-340 ranks
  planets; GBB-10:134-139 compares Ishta vs Kashta; GBB-3:462-467 Saptavargaja points are one
  Shadbala input, not levels. Nothing in HPA ch.7 or Three Hundred Combinations.
- His grade words are a tally of mixed testimony across Rasi and Navamsa (I:2039-2041, 2134-2137,
  2773-2778), NOT Shadbala. He calls a 4.58-rupa Sun "fairly powerful" (I:3924-3925) -- below his own
  5-rupa bar -- and the chart's strongest planet (9.59 rupas) only "fairly powerful" for aspects
  (I:3880-3890). Labels are unstable: Chart 22's Lagna is "powerful" at I:2039 and "fairly strong"
  at I:2044. A Shadbala band would contradict printed charts.
- The contrast terms in the target sentences run fortified <-> afflicted (I:6045-6049, 5129-5135):
  the corpus-wide NATURE/ASSOCIATION axis question already flagged, not the Shadbala axis.

**Split (so parked):**
- Middle grade as "neither strong nor weak": reviewer B allows it as a complement; reviewer A calls
  it an unstated inference. Measured: it would fire on 0-3 charts per sentence (Raman's bar is low;
  most lords clear it).
- "Very powerful": A would encode exalted/own/moolatrikona + Vargottama or own vargas majority, no
  affliction (I:11046, 11695, 17023, 17185); B: only the exact printed conjunctions as separately
  cited instances, or nothing. Also "very powerful" sometimes means maraka power (HPA-16:57-60).

**Done:** the five TODOs re-worded so nobody builds a Shadbala band for them. No output change.

**Flagged, not acted on:** reviewer A notes the engine's binary rule would grade the I:3924 Sun
(4.58 rupas) WEAK where Raman says "fairly powerful". It is one chart, in a passage that also calls
the Sun "fairly" strong on mixed testimony; worth a measured look at whether `IsWeak` on Shadbala
alone (without combustion/debility) contradicts other printed charts.

## Item 4 small predicates (2026-10-13)

Two engine-blind reviews per term; ship only on agreement.
- **H2.L.7b promoted** -- `InFeminineSign` (even sign, HPA-5:37-38) in D1 OR D9 for the 2nd lord in
  the 7th. Raman's sentence (HTJAH-I:2385) also names the constellation; no natal Raman book genders
  the nakshatras (the only list is Muhurtha ch.8:544 Yoni Kuta, a marriage-matching table and
  walled off from natal code), so that branch is omitted -- under-fires, never wrongly. 21 fires.
- **H10.L.3b parked** -- "unfriendly constellation" is NOT planetary friendship: on Raman's only
  worked use (Indira Gandhi, HTJAH-II:14087) natural and Saturn-side compound friendship both fail
  (both reviews). Survivors: tara 3/5/7 from Janma (HTJAH-I:1142; NH:8376 "Atimitra (very friendly)
  star"), the star lord's compound view, the star lord's functional nature. One reviewer chose tara,
  one parked.
- **H11.L.8a parked** -- "malefic constellation": a star ruled by a natural malefic (NH:15674-15678)
  and tara 3/5/7 (Satyacharya, HTJAH-II:14346) both fit Chart 230 (HTJAH-II:15960). Split.
- **H6.L.7b parked** -- no Raman book defines hermaphrodite SIGNS (planets only: HPA-6:135, GBB-3:665);
  he labels a sign by its own gender, not its lord's (HTJAH-I:5942). Both reviews.
- **H9.L.7a/b remain parked** -- they need Pravrajya / Asubha yogas encoded first (new yoga work from
  Three Hundred Combinations).

**Citation correction:** "NH:" anchors resolve into `notable_horoscopes_raman/chapter_001`, whose
line numbers differ from `Notable Horoscopes BV Raman.txt`. Two quotes were first cited by .txt
numbering: the Lagna-lord rule is NH:15662-15665 (not 26922-26926) and "Atimitra" is NH:8376 (not
14351). Fixed in code, tests and this file; the citation-anchor guard caught the second. Reviewers
must cite NH from the `.md` split.

**Net:** 21 presentation changes, 0 verdict changes, ratchet 286/397, 362/397, 35.

## Disposition axis -- stage 1 SHIPPED (2026-10-13): planet-in-house text picked by influence

The corpus-wide "nature-and-association axis" question, opened by the House 5 review and flagged
since. Decision delegated by the user ("take decisions on well researched").

**Research (two independent engine-blind reviews, concurring):** Raman's fortified / well
disposed / afflicted words are INFLUENCE, and "strong / weak" is a separate STRENGTH axis.
Definitions in his own words: "If the Moon is fortified, that is well aspected or conjoined"
(HTJAH-I:4283); "fortified, i.e., joined with or aspected by benefices" (I:2338); "strong and not
afflicted, by aspect or association, by malefic planets" (I:8434); "beneficially disposed by aspect
or association" (II:7480). Shadbala-only selection is contradicted by NH:14852-14854 ("Venus is the
strongest planet ... and even he is afflicted"). "Fortified" and "well disposed" are synonyms in
practice (II:1033 vs 1039).

**Three implementation rounds, each tested on Raman's worked charts:**
1. Netted score with rescues (dispositor, Jupiter relief, per-Lagna table): an adversarial review on
   12 charts found 2 agreements, 2 reversals. Rejected.
2. Revised with the reviewer's four cited changes: a FRESH 23-case holdout -- his "fortified" calls
   8/10, his "afflicted" calls 2/13. Pattern: when Raman calls a planet afflicted he names the
   malefic contact and does not net it ("fortification as well as affliction", NH:2843-2846).
3. **Two independent flags** (no netting): AFFLICTED = natural-malefic contact / combust (full orb,
   II:4067-4076) / hemmed without benefic relief; FORTIFIED = Jupiter/Venus, functional benefic or
   yogakaraka, dispositor or Lagna lord contact, exalted/own/moolatrikona, own nakshatra. A
   SECOND fresh holdout, 37 HTJAH-I cases: module "bad" 8/8 correct; "good" 5/7, the two
   opposites both from exempting the Lagna lord. Raman blames a malefic Lagna lord for afflicting a
   PLANET (HTJAH-I:5925-5937, 5641-5643) while also calling it "the most benefic" (NH:15662) --
   so for planets it now sets BOTH flags (mixed). That leaves 0 opposites on that holdout (the fix
   was informed by it; residual risk is on the fortified side).

**Display rule (rule_firing._branch, planet_in_house only):** one flag -> that text; both or
neither -> Raman's unconditioned `general` text (incomplete, never the wrong pole); no general
recorded -> strength still decides, as before. 3250 presentation changes, 0 verdict changes,
ratchet 286/397, 362/397, 35. Over the goldens' 1423 two-pole firings: 248 fortified, 171
afflicted, 872 mixed, 132 none.

**Deliberately not counted (contested in Raman):** natural benefics as afflicters when they own the
3rd/6th/8th/12th (NH:14854 vs NH:4727-4732); Jupiter "relieving" affliction as a net (I:6117 vs
NH:1335). Functional-benefic fortification for natural malefics is kept because it can only produce
"mixed", though Raman sets lordship aside when judging a karaka (I:5837, I:4761-4763).

**Stage 2, not started:** the lord-in-house tables (594 two-pole firings) mix "strong/weak" and
"afflicted/well disposed" qualifiers, mostly in Raman's surrounding sentence rather than the slot
text, so each record must first be tagged with its qualifier word (both reviews recommended
routing by the word). Combination rules rarely have two poles.

## Disposition axis -- stage 2 SHIPPED (2026-10-13): lord-in-house text picked by Raman's own word

58 lord-in-house rules have a text choice that matters (1520 firings over the goldens). Two
independent engine-blind reviews tagged every conditioned slot from HTJAH-I/II with the qualifier
Raman wrote; they agreed on 56/58. `doctrine/branch_axis.py` lists the 47 rules with agreed,
usable tags; `rule_firing._slot_holds` tests each slot on its axis -- INFLUENCE via
`disposition` (one flag), STRENGTH via effective strength (combust = powerless, HTJAH-I:3788),
BOTH ("weak and afflicted", HTJAH-I:5121) via both. One slot holding picks it; both or neither shows
the unconditioned text; with no unconditioned text a clear disposition picks the matching pole
before the old strength fallback (so an afflicted lord is never shown "well fortified").

Fortified slots: 37-38 influence, 7 strength. Afflicted slots: 15 influence, 5 strength, 4 "weak and
afflicted". Raman's lord-in-house tables are overwhelmingly on the INFLUENCE axis, as the House 5
review suspected; the old Shadbala-only selection fit only ~12 of ~81 conditioned slots.

**Left on the old selection (recorded in branch_axis.py):** H8.L.5 and H8.L.8 (reviews split),
H6.L.11 / H10.L.3 / H12.L.4 / H8.L.3-fortified (unclear in Raman), H8.L.7 (condition on two lords),
and fortified slots that merely repeat the unconditioned text (H7.L.6, H11.L.11, H12.L.6, H12.L.8).

**Net:** 1036 presentation changes, 0 verdict changes, ratchet 286/397, 362/397, 35. Overhead
measured at ~8% of a fire_rules pass.

### Found by the tagging, NOT acted on (data work, its own pass)
- **Afflicted sentences Raman wrote that were never encoded** (both reviews): H2.L.6 (2373-2378),
  H3.L.9 (3397), H7.L.5 (two: "severely afflicted", "both afflictions and benefic influences"),
  H7.L.6 (283-289), H8.L.1 ("severely afflicted", 2906), H8.L.5 (2962), H8.L.11 (3050), H10.L.4
  (9495-9497), H10.L.8 (9527), H11.L.7 (14303), H12.L.6 (16184). H12.L.2 lacks its fortified
  sentence (16146).
- **H8.L.1's fortified text ("strong -> undiminished") has no "strong" clause in Raman** -- an
  inference by the original encoding; its afflicted slot holds the "weak" sentence while Raman's
  real afflicted sentence is missing.
- **H11.L.7's fortified text contradicts its general text** ("marries only once" vs "more than once").
- Fortified slots that copy the unconditioned text (H7.L.5, H7.L.6, H11.L.11, H12.L.6, H12.L.8).

## "Missing sentences" pass (2026-10-14) -- mostly a false alarm, three real fixes

The stage-2 tagging reported 12 afflicted sentences Raman wrote but the records lacked. **Eleven
already existed** as child records from the twelve-house sweep (H2.L.6a, H3.L.9a, H7.L.5a/b,
H7.L.6a, H8.L.1b, H8.L.5b, H10.L.4a, H10.L.8a, H11.L.7a, H12.L.6a; H12.L.2's fortified side is
H12.L.2a) -- the taggers were given only the parent records. Lesson: a reviewer packet for a family
of records must include the children.

Real fixes:
- **H7.L.6a live** -- "If badly afflicted and the karaka Venus is also ill-disposed" (HTJAH-II:283).
  New `IllDisposed` condition = disposition reads clearly bad (Raman "deliberately does not say
  afflicted" of Venus there; "ill disposed" is an influence word per both reviews). "Badly
  afflicted" reuses H7.L.5a's severity test (>= 2 first-rate malefics). Fires on no golden; proved
  satisfiable by chart (test_missing_sentences.py); liveness 69 -> 70 consciously.
- **H8.L.1 fortified slot emptied** -- "the 8th lord strong - ... undiminished" was an encoding
  inference (Raman states the penury unconditionally, HTJAH-II:2902-2904). A past session wrote it
  deliberately as "the unconditioned reading at full force"; with the slot empty a strong lord falls
  back to `general`, which says exactly that without inventing a condition.
- **H8.L.11 afflicted restored** -- "Afflictions will aggravate the malefic results"
  (HTJAH-II:3050-3051); axis tag (influence, influence).

Not a defect: H11.L.7's "marries more than once" (general) vs "if fortified, marries only once" is
Raman's own conditional exception (HTJAH-II:14302-14304); only one is ever displayed.

Still parked: H7.L.6b ("Venus well placed" -- unclear word), H12.L.2a (enumeration proof).
**Net:** 0 presentation changes on the goldens, 0 verdict changes, ratchet 286/397, 362/397, 35.

## Ascetic and asubha yogas (2026-10-14) -- H9.L.7a and H9.L.7b live

HTJAH-II:7353-7357 (9th lord in the 7th): "If ascetic yogas are present in the chart, the native may
seek spiritual guidance and fulfilment abroad. If asubhayogas spoil the ninth lord, the father may
meet with his death abroad." Two independent engine-blind reviews.

**Ascetic yogas** (`doctrine/ascetic_yogas.py`). Raman's own stated list is HTJAH-II:11025-11053
(10th-house chapter). His many worked-chart Parivraja readings are loose and hedged ("a slight
adaptation of ... Brihat Jataka", NH:2388-2390; "some sort of", NH:3863-3864; "Strictly speaking
no Parivraja yoga", NH:6916-6917) and he cancels the planet-cluster pattern twice (NH:14603,
14860) -- both reviews: encode the stated rules, not the hedged readings. Encoded: four planets in
the 10th (minus his Sun-combustion exception), the Moon in a Saturn decanate / Saturn-or-Mars
navamsa aspected by Saturn, Saturn or the Lagna lord aspecting the Moon-sign lord (strict, no
identity), the Moon in the 9th unaspected. Not encoded: the strength-graded rules, "five planets
in a quadrant or trine" (ambiguous), Jupiter-in-9th "holy man". **Base rate: 35% of the goldens hold
at least one** (84 via the Moon-sign-lord rule) -- Raman's own threshold; the classical-abundance
mechanism again. Under-fires vs his readings of Buddha, Vivekananda, Sivananda.

**Asubhayoga.** Raman's glossary: "Asubhayoga -- A combination caused by evil planets"
(HTJAH-I:18681-18685). Reviewer A first said PARK (searched only the HTJAH-II index), reversed on
seeing the glossary. Encoded as the 9th lord joined or aspected by a natural malefic (HTJAH-I:8434)
or hemmed between malefics "with out any benefic influence" (HTJAH-II:975-977). Supporting
definition of affliction (papakartari / malefic aspect / conjunction) is at
three_hundred_combinations_complete:6567-6570 under combination 199 -- NOT in the registered 3HC
copy, which ends near combination 162 (flag: the registered copy is incomplete). Fires 27/38.

**Net:** 39 presentation changes (H9.L.7a 12, H9.L.7b 27), 0 verdict changes, ratchet 286/397,
362/397, 35. Liveness unchanged (both fire).

## MERGE OF main INTO claude/empirical-engine-lag-vrxsau (2026-10-14) -- committed WITH 12 KNOWN FAILURES

Branches split 2026-08-05 (main +168, this branch +202). Merged at user request to bring in the
complete Three Hundred Combinations (3HCC, main a71dfa9a) and everything else on main. Saved at the
user's instruction before the tail was fixed. **Golden ratchet held exactly: 286/397, 362/397, 35.**

Resolved: all 15 conflicted files. Report layer: every section of both branches kept (REPORT
COMPLETENESS); this branch's six sections renumbered v36-v41 (aptitude, themes, medical, feedback,
simple_summary, indications) and placed in main's `report_movements.MOVEMENTS` arc (feedback after
nichod by user request). Contract test now `_ORDER_V41`.

**Open -- fix next session (pytest tests/raman_saab: 12 failed / 7231 passed):**
1. test_book_registry::test_unsplit_books_match_the_registry
2. test_citation_anchors_land_on_text::test_no_anchor_resolves_to_blank
3. test_rule_liveness::test_yoga_liveness_does_not_regress (main added ~110 yogas; re-baseline)
4. test_source_lock::test_source_lock_matches_disk
5-6. test_yogas: Matrunasa-199 and Raja-263
7. test_detailed_report::...test_the_general_varga_anchors_agree_with_the_domain_table (D-27 cite)
8. test_doctrine_snapshot (main's yogas change presentations; check 0 verdict change, re-freeze)
9. test_sitting::TestTheHedgeCensus -- USER DECISION PENDING: main caps the "not a prediction"
   family at 8 per reading; with this branch's sections the Mainpuri report has 13. Raise the cap or
   consolidate wording.
10. test_theme_synthesis::...background_provenance_is_stated_and_honest
11-12. test_wave2_yogas_houses_preponderance: family map lacks main's new yogas; json new fields.
Also: the merged interactive page (report.html) passes a JS syntax check but has NOT been opened in
a browser. The digest now pins governing_factor/foundation first, salience orders the rest (merge
judgement call, review it).

**2026-10-21 follow-up (branch claude/merge-fix, on top of the NH re-anchor d004f1f5): 12 -> 4
failing (7231 -> 7239 passed). Golden ratchet unmoved: 286/397, 362/397, 35.**
- FIXED 1. 3HCC and 3HC-HOCR carry `never_split=True` in the ETL bundle (both pinned unsplit).
- FIXED 2. Five blank anchors re-read on the corpus: BPHS-27:163->164 (Drekkana Bala),
  BPHS-27:19->3609 (sloka 19, Drig Bala; "19" was the sloka number), BPHS-45:66->71 (Results
  sloka), BPHS-7:300->301 (table head), NH:2556->1505 ("natural Atmakaraka", the Sun). Each line
  checked identical in both local corpus copies (E:\astro and the varga worktree).
- FIXED 4. Source lock re-locked. Every raman_saab citation into the 5 files lands on identical
  text in both corpora. Phala/3HCC/3HC-HOCR: bytes unchanged; the diff was only this branch's
  front-matter-excluding body hash vs main's whole-file hash. BPHS-7 and HPA-11 DO differ between
  copies (E:\astro BPHS-7 is 883 lines, main locked 1028) -- the cited lines agree, the files do
  not. Which corpus copy is canonical is an open question.
- FIXED 5-6. Fixture bugs, not yoga bugs: Matrunasa-199 put Venus on the exact 10d00' navamsa
  cusp and only passed through the old `deg // (30/9)` off-by-one; Raja-263 put the Sun 5d from
  Jupiter and only read un-combust before stated charts got a combustion pass (c5706858).
- FIXED 9. Hedge census 13 -> 8 by trimming the SECOND hedge in five places where one section
  carried two (span honesty line, marriage separation caveat on all three surfaces, the
  longevity and maraka subtitles, and SYN_R9's doctrine text, whose simple_meaning already
  discloses the null). Cap unchanged at 8; every section still states its limits.
- FIXED 11-12. 113 main yogas added to YOGA_FAMILIES by their own `kind` (no new family).
- HELD 3 + 8 (DECISION NEEDED). The doctrine snapshot shows 78 VERDICT changes vs the freeze at
  2d65fe57 -- introduced by the merge itself (same 78 before any fix). Unscored houses/sub-matters
  only (ratchet held), but not zero, so neither the snapshot nor yoga liveness (20 -> 54
  never-fire, all main's new yogas) was re-frozen.
- HELD 7 + 10 (DECISION NEEDED). D-27/40/45/60 anchor: main moved varga_domains to the classical
  sloka (BPHS-7:96/100/102, PHALA:112 -- verified on the corpus); this branch's judge and two
  tests pin Raman's pointer HPA-11:195. The tests contradict each other; one side must change.
- NOT RUN: test_astrobank_ratchet skips (engine fingerprint changed; needs a feature-store
  rebuild). data/private was not mounted in the worktree.

**CLOSED 2026-10-21 (branch claude/merge-fix). pytest tests/raman_saab green. Golden ratchet
unmoved throughout: 286/397, 362/397, 35.**
- HELD 7 + 10 resolved by user decision B: D-27/40/45/60 cite the classical sloka
  (BPHS-7:96/100/102, PHALA:112); the judge and both tests follow varga_domains.
- HELD 3 + 8 resolved by user decision A: the 78 verdict moves were reviewed against Raman, not
  waved through. All 78 came from main's new yogas acting through the kind-only yoga step in
  house_template. Fixed: `doctrine/yoga_routes.py` gives each yoga the house its own text names
  (HTJAH-I:480-482). Bhagya -> H9 fortune plus its ownership clause (3HCC:8003-8010); progeny
  curses -> H5; wealth yogas -> H2 wealth / H11 gains+acquisitions; 3HC raja 245-263 shift nothing
  (3HCC:8580-8584 names "inherent vitality" but no test); disease/death arishtas report-only
  (user decision 3, 3HCC:8923-8924). 78 -> 13 diffs, all faithful, re-frozen with lineage;
  rule liveness re-based (yogas 72 -> 185, never 20 -> 54, all 34 new dormant ones merged 3HC).
  Full record: docs/raman_saab/MERGE_VERDICT_REVIEW_2026-10-21.md.
- Still open: decision C (canonical BPHS ch.7 copy); the vitality rule for pre-merge HTJAH raja
  yogas; H7 spouse yogas; `_rollup` masking an afflicted sub-matter; the real-outcome ratchet
  (needs a feature-store rebuild).

## ENGINE AUDIT FIXES (2026-10-23)

Source: the independent audit `raman-engine-audit-2026-10-23.md` (project files); the user asked
for every finding to be fixed and made the two judgement calls below on decision cards.

- **Citations.** H2.C.71 `3HC:5991` -> `3HCC:5991` (wrong edition); H2.C.72 `NH:5655` -> `NH:7628`
  (pre-re-OCR numbering); H4.C.48 `HTJAH-I:4550` -> `4551` and H4.C.49 `NH:4961` -> `4963` (blank
  lines); Kedara/Sula/Yuga/Gola off the shared `3HC:6868` heading onto their own definitions;
  `VARSHA-7:190` (blank) -> `174`. The anchor test now scans `Citation("WORK", n)` objects.
- **Golden labels.** HTJAH-I chart_09 H1 ("insufficient-evidence") demoted to DRAFT pending an
  engine-blind re-adjudication — Raman's text (HTJAH-I:1181-1188) reads unfavourable; stale
  "Phase E" notes removed from five H8 rows.
- **One-sided-rasi navamsa guard** (`_navamsa_modulate`). The D9 may not carry a mixed to the pole
  opposite every fired rule (HTJAH-I:975-980, the navamsa is co-testimony). Ratchet 286->284 /
  362->364 / 34->32. Corpus-wide it is the largest mover: ~520 unscored sub-matters, mostly
  favourable -> mixed (H12, H7, H4 heaviest). Re-open path: an engine-blind read of a sample of
  those moves against the text.
- **Rollup.** An afflicted sub-matter always reaches the house headline (was masked in ~8% of houses).
- **Raja vitality.** HTJAH-I:641-645 ("within 12° of each other") is the encodable vitality test
  the 3HC Remarks ask for; a raja yoga lifts a verdict only when it passes. Only the association
  yoga Y.RAJA.KT has a measurable pair; every other raja yoga, old or new, is noted. No scored change.
- **USER DECISION "Drop the pillar".** Bhava Bala no longer votes (`BHAVA_BALA_PILLAR_VOTES`); it is
  still computed and reported. The H11 dhana floor's "all pillars strong" is read over the voting
  pillars. Ratchet 284->276 / 364->366 / 32->30. New real error: HTJAH-I h5_15 H5 (flipped when the
  vote went); cleared: chart_44 H2, NH chart_54 H9, NH chart_75 H1.
- **USER DECISION "Raman's ayanamsa".** Raman-engine reports, CLI and API default to Raman's
  ayanamsa; the report header names the ayanamsa actually used (it said "Lahiri sidereal" always).
- **Report honesty.** A failed maraka check is reported as undetermined, never as "no maraka-tier
  lord"; every swallowed exception in `detailed_report` is logged.
- **Ratchet.** Re-based to 276/396, 366/396 with lineage; the 30 real errors are pinned by key
  (`real_errors`, `test_no_new_real_errors`). Doctrine snapshot re-frozen (2147 VERDICT lines, note
  in the file); cross-layer D9 baseline re-based (0.7294 -> 0.6693: part of the old agreement was
  the D9 manufacturing the verdict it was compared with).
- **Not done here:** the sealed hold-out of unseen Raman charts (needs extraction on the PC with the
  full book set); electional/prasna/BPHS 46+ citations were not checkable in the cloud copy.

## TIMING GAP CHECK -- all 16 fixes (2026-10-24, USER DECISION)

Source: `docs/raman_saab/research/engine-timing-gap-check.md`. The user approved all 16 fixes,
including fix 1, which revises the CLAUDE.md lock "Dasha/bhukti house-activation" (row updated
the same day). Every rule change carries its verbatim Raman citation in code. Golden ratchet
unchanged at **269/389 exact, 354 within one, 35 real errors**; `doctrine_snapshot --check`:
**IDENTICAL across 346 charts (primitive + predicate + verdict)**.

| # | Fix | Where |
|---|---|---|
| 1 | Timer set = Raman's printed per-house lists: karaka only for H3/H4/H5/H6/H7/H9 (Sun)/H12, lord-from-Moon from H2 on, H3 adds Mars's associates/aspecters | `primitives/vimshottari.py` (`TIMER_KARAKA`, `timer_roles`) |
| 2 | Node channels: dispositor, conjoined planet, nakshatra lord, Sanivad Rahu / Kujavad Ketu (recovers Napoleon h10_05 Rahu) | `vimshottari.timer_roles`, `nakshatra_lord_of`, `NODE_DICTUM` |
| 3 | Grade on the house's own set; allied 2/11, 9/12 as an `allied_via` note; MD lord's own bhukti = "same lord" | `vimshottari.period_tier`/`active_houses`, all tier consumers + 3 renderers |
| 4 | Star-lord layer (veto/boost note) and the 3rd/5th/7th-star trial | `raman_timing` period_lords, bhukti_relations |
| 5 | Lifespan gate | `vimshottari.lifespan_gate`; `raman_timing` period_lords, yoga_lords, maraka_order |
| 6 | Raman's bhukti relation (6/8, 2/12, 3/11, kendra, mutual aspect, 5/9 lords, Saturn-Venus, maraka from the major lord) | `raman_timing.bhukti_relation`; `SYN_R15_BHUKTI_RELATION` |
| 7 | Maraka order 5/4/3 inside primary; tertiary Saturn widened; delegation to a node; Amsa half of the Saturn signal; Saturn over 8th/12th lords' signs | `vimshottari.MarakaSet`, `death_weight_fn`, `delegated_marakas`; `MarakaSaturnConfluence.amsa_spans/signature`; `_chk_r9`; `raman_timing` saturn_8_12_lords |
| 8 | Sade-Sati rounds since birth, ruling-period strength, SAV > 30; the "no doctrine on record" notes corrected | `raman_timing` sade_sati_rounds; detailed_report, report_html, template |
| 9 | Vedha: Mercury 10th -> 7th as printed; no node rows; reverse Vedha; sentence fixed | `primitives/transits.py`; gochara and adverse tables in all renderers |
| 10 | Dasa gate + combination label on each transit window | `raman_timing` transit_dasa_gate |
| 11 | Saturn/Rahu over natal rasi and Navamsa signs; Mars-Saturn / Saturn-Rahu meetings on the Moon sign, 8th, 11th | `raman_timing` transit_natal_points, malefic_meetings |
| 12 | Marriage point: lords' sums + the practised bhava sum, Jupiter windows and aspects | `judges/marriage_timing.py` (third sphuta); `raman_timing` marriage_point |
| 13 | Sign-part activation | `raman_timing` sign_parts |
| 14 | av_pinda: transit Saturn in the natal ayanamsa; Raman's ASP-11:388-393 cited first | `doctrine/av_pinda_timing.py` |
| 15 | Antaras judged by position from MD/AD lords and role | `raman_timing` antaras |
| 16 | Sandhi for the AD lord and yoga lords | `_chk_r7`; `raman_timing` bhukti_relations, yoga_lords |

**Mercury 10th Vedha (fix 9).** The printed page (PDF p.264, book p.257, scanned at 400 dpi) and
the OCR (HPA-34:203, 207) both read the Mercury row "2-4-6-8-10-11 / 5-3-9-1-7-12", so the 10th
maps to the 7th. There is no sign of a misprint: 7 does not repeat in the row, and the classical 8
would put a Vedha point on one of Mercury's own good houses. Raman's worked example (Mercury in
the 11th obstructed by Saturn in the 12th) confirms the row's 11 -> 12 cell. Followed as printed.

**Not done faithfully, or done with a disclosed proxy:**
- `house_template._event_timing` still unions the 2/11, 9/12 aux houses for its event windows. This is timing metadata only, not a grade; it was left unchanged and needs its own decision.
- The Saturn-in-10th Mrityu-yoga maraka is kept, with "no citation located" noted in code.
- HTJAH-I:788 (iii), "lord of 3rd or 8th associated with 2nd or 7th lord": the 3rd and 8th lords are already secondary unconditionally, so set membership is unchanged.
- HPA-15:41-46 (2nd stronger than 7th) is recorded as a variant, not applied.
- Star-lord veto/boost, bhukti relations, sandhi, the lifespan gate and every transit table are report-only. None feeds a verdict, so the ratchet cannot measure them.
- Dasa "good/bad" in transit_dasa_gate and sade_sati_rounds uses the engine's `lord_quality` tag. "Does the Dasa warrant it" uses the engine's `death_window` ranking. Raman gives no mechanical test for either.
- The star trial treats "malefic" as a natural malefic (the project lock). Raman's wording does not say natural or functional.
- No orb is printed for natal points, so whole signs are used. The ~10 degree conjunction (NH:12265-12266) is applied only to the Mars-Saturn and Saturn-Rahu meetings.
- The natal-point scans cover the running bhukti and the next one only, to keep the table readable.
- Raman's Jupiter-transit observation (ASP-11:402-409) is recorded, not encoded. The rekha half of the pinda clock (ASP-11:410-430) stays omitted.
- Nodes still OBSTRUCT other planets' transits ("any other planet", HPA-34:159-160). Only their own Vedha rows were removed.
- Rectification scoring was remapped to the new grades (par excellence / ordinary / same lord -> both-lords score; limited / feeble -> one-lord score, HTJAH-I:1592-1594). Its tests pass, but no separate rectification accuracy benchmark exists to re-measure against.
