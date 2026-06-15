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

## B2 — Marginal-strength band  `threshold`  (Phase 2b)
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

## B5 — Yoga additions  `new-rule`
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

## B6 — HPA/HTJAH house rules  `new-rule`
- Mars in the 7th → clashes/tensions, possibly two wives (HTJAH-I:8170) — feeds H7.
- 4th lord in the 12th → loss of ancestral property (HPA-19:247) — feeds H4 property.
- 7th-lord & Venus in common/dual signs → ≥2 marriages (HTJAH-II:484; HTJAH-I:8138) — H7.
- Planet results vary by avastha/disposition, not mere occupancy (HPA-19:47; HPA-7 the 10
  avasthas) — a longer-horizon `shadbala`/metadata item, deferred.

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
- Mine more worked charts from HTJAH-I/II early chapters (full birth lines) via the existing
  DRAFT→worksheet→CONFIRMED pipeline.
- **Notable Horoscopes** is only 2 of ~50 chapters present — an *acquisition* gap; the full
  edition would add ~48 fully-worked goldens. Flag for the user to source.
