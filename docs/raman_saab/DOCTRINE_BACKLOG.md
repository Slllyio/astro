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

## B3 — Non-death-marital maraka guard  `judge-mechanism`  (Phase 2c)
**Doctrine.** Kuja-Dosha / maraka pressure is about the *death* of the spouse (HTJAH-II:2579
"the death of the husband/wife will occur"), NOT marital *happiness*. The 7th is a maraka
house, so Venus-the-karaka lands in the maraka set and clause-6 over-afflicts a barely-weak
Venus on the happiness sub-matter.
**Plan.** Suppress `maraka_drives` for the `marital_happiness` signification (a non-death
matter), mirroring the LONGEVITY_GUARD pattern. Pairs with B2 to fix chart_03/08.
**Note.** The Kuja-Dosha *cancellation* (sign exemptions Gemini/Virgo, Cancer/Capricorn, …;
Leo/Aquarius wholly exempt; Mars+Jupiter/Moon conjunction) is **already encoded** in
`_KujaDosha` (HTJAH-II:2593-2601) — so this is NOT a missing-cancellation gap.

## B4 — Blemishless-/Yogakaraka-Venus marriage override  `new-rule`
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

**ch.XVI (Illustrated Horoscopes).** The preamble states Illustrated No. 1's Sun Ashtakavarga
cell-by-cell, raw AND reduced (ASP-16:40-51): raw checksums to 48 and ALL SIX printed reduced
cells reproduce under `trikona_shodhana` exactly (`test_asp_illustrated.py`) — the third
independent printed-book validation of the subtract reading. The remaining ~8 nativities
(Roosevelt, Marx, Ford, Mussolini, Tagore, Stalin-era dates...) carry printed longitudes,
per-planet AV figure strings, Sarvashtakavarga rows and SODYA PINDA tables — fixture gold, but
the OCR of the longitude/figure strings is too damaged to extract responsibly (Roosevelt's
month digit corrupted, Moon's longitude lost). RE-EXTRACT BY VISION from the source PDF
(uploads/…89c0f204…pdf, PDF pages 84-90) in a fresh session; several charts likely overlap
existing NH goldens (Tagore, Ford) — flag for the golden track, do not confirm unilaterally.

**ch.XV (Miscellaneous), classified per the content-scope rule (a live tag does not admit
out-of-scope content — the AFB-horary precedent):**
- Rules 1-19 (ASP-15:21-168): ELECTIONAL — choosing times/directions for journeys, marriage,
  studies, factories, conception via Sun/Moon/Mercury/Venus bindu-transits. Category (b),
  MUHURTHA firewall — deliberately NOT encoded.
- Rahu Ashtakavarga (ASP-15:~240-260): Raman presents a variant Rahu AV with bindus, while
  noting "no Kakshya has been assigned to him". The first-edition preface says such
  controversial matters (Rahu/Lagna AVs) were deliberately avoided in the main exposition;
  the repo's 7-graha chayagraha lock stands. NOT encoded — recorded as a Raman-presented
  variant, not Raman doctrine.
- Rahu's 12-places-from-Moon transit results (ASP-15:263-271): benefic at (3), (6), (11) —
  CORROBORATES transits.py's existing Rahu Gochara set {3,6,11} exactly. No change needed;
  noted as an ASP confirmation of the encoded table.
