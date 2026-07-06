# House Point-Scheme Audit Ledger

Per-house held-out audits of the **strength point-scheme** in
`app/medini/doctrine/domains/house_judgment.py`
(`_DIGNITY_W`, `_W`, `_THRESH`, the optimistic/additive `_combine`, and
`_verdict_label`), measured against Raman's own worked per-factor verdicts in
*How to Judge a Horoscope*.

**Policy — tuning is DEFERRED.** Each house is audited in isolation and its
insights recorded here. A **single consolidation pass runs only after all twelve
houses are done**, tuning the weights *jointly* so that no already-reviewed house
regresses (in particular ch. IV must stay 9/9 and the approved house-1 output must
hold). Do not re-tune per house.

Each house audit is a **comprehensive**, cited, feature-level corpus read from the
prose (not the OCR grids) — *every* factor-verdict a chapter states clearly, not
just the tidiest — scored by the *live* scheme (constants imported, not copied).
Corpora themselves are fair-use excerpts kept in the working scratchpad, not
committed; only the distilled insights and the split assignment live here.

---

## Held-out validation protocol (PRE-REGISTERED)

To keep the final consolidation claim honest — *not* a circular in-sample fit —
a fraction of the evidence is reserved and **never used to derive or tune**
anything. Declared here **before** the consolidation, by a mechanical rule so it
cannot be cherry-picked:

- **Anchor (train, fixed):** ch. IV Charts 12–14 — the scheme was decoded to fit
  these; they stay the 9/9 calibration anchor and are never held out.
- **HOLDOUT (test, never tuned):** from ch. V onward, every worked chart whose
  **number is divisible by 3** — Charts 42, 45, 48, 51, 54, 57, 60, 63, …
- **TRAIN (tuning insights):** every other ch. V+ chart — 40, 41, 43, 44, 46,
  47, 49, 50, 52, 53, 55, 56, 58, 59, 61, 62, …

The consolidation may look at TRAIN rows only when choosing weights; the HOLDOUT
match rate is computed **once**, at the end, as the real generalisation number.
Each corpus row is tagged `split: train|holdout` accordingly.

---

## Scheme snapshot under audit

_Recorded so the consolidation knows exactly what these audits measured._

```
_DIGNITY_W = exalted +1.6, own +1.2, friendly +0.8, neutral 0.0,
             inimical -0.8, debilitated -1.6   (debil+neechabhanga -> +0.2)
_W        = dusthana -1.0, kendra_trikona +1.2, vargottama +1.2,
            neechabhanga +0.2, kartari_subha +1.0, kartari_papa -1.0,
            aspect +0.7, conjunct +0.7, conjunct_exalted +1.6,
            bhava_aspect_mul 0.5
combine   = BHAVA additive across vargas; PLANET optimistic max(rasi,nav)+0.3*min
_THRESH   = 2.4 very powerful | 1.75 very strong | 1.25 fairly powerful |
            0.9 fairly strong | 0.55 fairly good | 0.25 moderately good |
            -0.6 moderate | -1.6 weak | (else) afflicted   (9-grade scale)
```

---

## House 1 — ch. IV — CALIBRATION BASIS (not a held-out test)

- **Corpus:** Charts 12–14 (3 charts, 9 factor-verdicts).
- **Result:** 9/9 within one grade — the scheme was *decoded to fit these*, so
  this is the calibration set, not independent evidence.
- **Load-bearing decisions decoded here:**
  - Navāṁśa is **co-equal** with the Rāśi, not a half-modifier (Chart 12 Saturn:
    bad on every Rāśi count yet "fairly good" because the Navāṁśa redeems it).
  - A **planet** strong in *either* varga is strong → optimistic
    `max+0.3·min`; the **bhāva** is additive across vargas.
  - **Vargottama** is top-tier (a vargottama Lagna → "very powerful", an override).
  - Neechabhaṅga cancels debility (→ +0.2); exalted-conjunction and kartari are big.
  - Empty + unaspected Lagna → **"moderate"** (Chart 12). *(Note the tension with
    House 2 / Chart 43 below.)*

---

## House 2 — ch. V — HELD-OUT AUDIT

- **Corpus (comprehensive):** Charts 40, 41, 42, 43, 44, 45, 46, 48
  (**19 factor-verdicts**).
- **Result:** **OVERALL 14/19 within one grade** (5 exact) ·
  **TRAIN 8/11 · HOLDOUT 6/8** (holdout charts 42, 45, 48).
- **The held-out set independently reproduces the dominant pattern:** its only
  two misses are **45-Lord (+3)** and **48-Lord (+4)** — both the
  placement+dignity+conjunction **stacking over-score**. So the fix, when made,
  is validatable on data it was not derived from.
- **Report artifact:** ch5-scheme-audit (per-chart table + diagnosis; built on the
  original 14-row cut).

### Divergence patterns (the signal for consolidation)

1. **The Lord over-scores when placement + dignity + associations stack** — the
   scheme adds a good *house* and good *dignity* as two independent positives with
   **no ceiling**, so a well-placed dignified lord shoots to the top grade.
   - *Chart 43:* Mars in the 9th (trikoṇa +1.2) **and** in his own sign (+1.2) →
     "very powerful"; Raman **"moderately good"** (Δ +5, the worst row).
   - *Chart 40:* own-sign + benefic conjunction + benefic aspect → "very powerful";
     Raman **"strong"**.

2. **The optimistic Rāśi/Navāṁśa combine can rescue a Rāśi-afflicted lord too far**
   — right for Chart 12 (Saturn), but overshoots when the Rāśi carries several
   malefic associations.
   - *Chart 45:* Venus joined by **three** malefics (Sun, Moon, Rahu) in the Rāśi →
     still "fairly powerful"; Raman **"feebly strong"** (Δ +3).

3. **Empty-house baseline vs Raman's own spread** — an empty, unaspected house
   scores the neutral centre ("moderate"). Chart 43's empty 2nd is
   **"fairly strong"** (Δ −3) — *yet* Chart 12's equally empty Lagna is
   **"moderate"**. Raman's own verdicts for the same configuration span two
   grades, so no single threshold fits both. **Partly his inconsistency, not the
   scheme's** — flag, don't chase.

### Tuning hypotheses (candidates for the consolidation pass — NOT applied)

- **Diminishing return on stacked positives**: make placement + dignity
  sub-additive (a cap, or a soft-max), so "good house + own sign" ≈ one strong
  positive, not two. Directly addresses patterns 1.
- **Temper the optimistic combine under heavy Rāśi affliction**: e.g. reduce the
  Navāṁśa rescue when the Rāśi has ≥2 malefic associations. Addresses pattern 2.
- **Leave the empty-house baseline at "moderate"**: matches Chart 12; Chart 43 is
  within Raman's own noise.
- Every candidate must be re-validated **jointly** on ch. IV (stay 9/9) **and**
  ch. V (improve Lord past 2/5) before adoption.

---

## House 3 — ch. VI — HELD-OUT AUDIT

- **Corpus (comprehensive):** Charts 52, 53, 58, 61, 62 (**10 factor-verdicts**)
  + 2 rows set aside as *un-modeled* (below). Ch. VI's verdicts are
  coarser/comparative ("good", "well disposed", "not sufficiently strong").
- **Result:** **OVERALL 7/10 within one grade** (2 exact). **HOLDOUT 0** — ch.
  VI's ÷3 charts (54, 57, 60, 63) carry only coarse or un-modeled verdicts, so
  they yielded no clean held-out rows; ch. VI contributes to TRAIN, and the
  global holdout is fed by ch. V (and later houses).
- Ch. VI's remaining combinations are mostly **backlog** (need lord-to-planet
  binding, sign parity, or planet gender) — the 26 encoded ch6 rules already
  cover the systematic lord-in-house + planets-in-3rd content; chapter-reading
  wired (`HOUSE_CHAPTERS[3]`).

### Divergence patterns — these REINFORCE the House-2 findings

1. **Lord over-scores when placement + dignity + associations stack** (again, the
   dominant pattern):
   - *Chart 61:* Mars in a kendra (+1.2) **and** own sign (+1.2) → "very
     powerful"; Raman **"not sufficiently strong"** (Δ **+6**, worst row so far).
   - *Chart 53:* Venus in the 7th (+1.2) + neechabhaṅga (+0.2) + **exalted**
     Mercury conjunct (+1.6) + Jupiter aspect (+0.7) → "very powerful"; Raman
     **"well disposed"** (Δ +4).

2. **Empty-house baseline** — *Chart 52:* empty, unaspected 3rd → scheme
   "moderate"; Raman **"fairly strong"** (Δ −3). **Second data point** (with
   Chart 43) for "empty + unaspected → fairly strong" — so this is now a
   *pattern*, not noise, and it argues for a small positive baseline on a clean
   house (still to be reconciled with Chart 12's "moderate").

### NEW — factors the scheme cannot see (set aside, not counted)

- **Combustion** (*Chart 59:* Venus own-sign-in-9th but **combust → "powerless"**;
  *Chart 62* Mars). The scheme has no combustion penalty — a genuine missing
  input, not a weight error.
- **Mandi / upagraha** (*Chart 60:* the 3rd occupied by **Mandi**, outside the
  nine grahas the scheme scores).

---

## House 4 — ch. VII — HELD-OUT AUDIT

- **Corpus (comprehensive):** Charts 65–71 (**12 factor-verdicts**). ch7 already
  has 32 encoded rules (lord4-in-house ×12, planets-in-4th ×9, parivartana +
  mother-death yogas). Chapter-reading wired (`HOUSE_CHAPTERS[4]`).
- **Result:** **OVERALL 8/12 within one grade** (1 exact) · **TRAIN 5/7 ·
  HOLDOUT 3/5** (holdout charts 66, 69).

### Divergence patterns

1. **Empty / light-house UNDER-score — now the biggest recurring signal.** Raman
   repeatedly calls a clean or lightly-aspected 4th house **"moderately strong"**
   (Charts 65, 69, 70), which the scheme centres a grade or two lower. With Charts
   43 and 52 that is **five** instances of "clean house rated higher than the
   scheme". **BUT** this is entangled with a **mapping choice**: I map Raman's
   "moderately strong" → *fairly good*. Map it one notch lower (→ *moderately
   good*) and ch7 rises **8/12 → 10/12** — most light-house rows come within one.
   So the divergence is *real in direction* (clean houses read higher for Raman)
   but its *magnitude is mapping-sensitive*; the robust fix is a small positive
   baseline for a clean house, not a big one.

2. **Placement over-score on an afflicted lord** (mapping-independent) — *Chart
   65:* Moon in a kendra (+1.2) but conjunct a functional-malefic → scheme
   "moderately good"; Raman **"considerably afflicted"** (Δ +2). Same family as
   the Lord stacking pattern: good placement over-rewards a genuinely afflicted
   planet.

3. **NEW — Papakartari over-penalises the BHĀVA** (mapping-independent, holdout) —
   *Chart 66:* the 4th is hemmed between malefics (papakartari) yet Raman rates it
   **"moderately strong"**; the scheme's `kartari_papa = -1.0` alone sinks it to
   "weak" (Δ −3). Suggests kartari should weigh **less on the bhāva** than on a
   planet, or be softened when a benefic also occupies.

---

## House 5 — ch. VIII — HELD-OUT AUDIT

- **Corpus (comprehensive):** Charts 91–98 (**17 factor-verdicts**). ch8 has 39
  encoded rules (lord5-in-house ×12, planets-in-5th ×9, many progeny yogas).
  Chapter-reading wired (`HOUSE_CHAPTERS[5]`).
- **Result:** **OVERALL 13/17 within one grade — 9 EXACT** · **TRAIN 10/13 ·
  HOLDOUT 3/4.** ch. VIII's charts are mostly childless (heavily afflicted)
  natives, and the scheme grades **afflicted factors excellently** (9 exact).
- **The decisive confirmation:** *every one of the 4 misses is the placement /
  dignity over-score* —
  - *Chart 98-Lord:* Saturn in trikoṇa **and** own sign → "very powerful"; Raman
    **"weakened"** (Δ **+7**, worst in the whole audit).
  - *Chart 95-Lord:* Venus in a kendra + benefic conjunction → "very strong";
    Raman **"rendered neutral"** (Δ +5).
  - *Chart 91-Karaka:* Jupiter in trikoṇa + benefic conjunction but papakartari →
    "fairly strong"; Raman **"blemished"** (Δ +4).
  - *Chart 96-Karaka (holdout):* Jupiter own + benefic conjunction → "very
    strong"; Raman **"moderately benefic"** (Δ +3).
- **Refined diagnosis:** the scheme lets a planet reach "very strong / very
  powerful" from **placement + dignity + a benefic conjunction alone**. Raman
  reserves the top grades; his "good" planets sit around *fairly good / fairly
  strong*. The fix is a **ceiling / diminishing return on stacked positives**,
  and it must NOT touch the negative side (the 9 exact afflicted-factor matches
  show the scheme already reads affliction correctly).

---

## House 6 — ch. IX — NOT POINT-SCHEME-AUDITABLE (structural finding)

- Chapter-reading wired (`HOUSE_CHAPTERS[6]` = ch9; 34 rules already encoded —
  lord6-in-house ×12, planets-in-6th ×9, disease/enemy yogas). The Mainpuri
  house-6 reading works (Aries on the 6th, Satrukāraka Mars & Saturn).
- **But ch. IX yields no held-out audit rows.** The 6th is a **dusthāna**, and
  Raman judges it entirely for **disease identification and timing** — *which*
  ailment, via the 6th/8th lords, their conjunctions, combustion and transits —
  **never grading the bhāva / lord / kāraka on the strength scale.** A scan of
  all ~16 worked charts (109–124) found **zero** "the 6th house is
  moderately-strong / weak" verdicts (e.g. Chart 113: "the 6th lord Mars, the
  Rogakāraka, is in the 11th with malefics… the native is suffering from myopia").
- **Implication:** the strength point-scheme has no ground truth to validate
  against in ch. IX, so house 6 contributes **nothing** to the tuning corpus. The
  same likely holds for the other dusthānas — **house 8** (longevity/death:
  ayurdāya, mārakas) and **house 12** (loss/mokṣa) — which are judged for their
  own events, not bhāva strength. Combined tally therefore stays at houses 2–5.

---

## House 7 — ch. XI (Vol. II) — HELD-OUT AUDIT

- **Chapter is in Volume TWO** (houses 7–12 → ch. XI–XVI). Two structural facts
  surfaced here:
  1. The compendium already ships a comprehensive **`htjah_vol2.jsonl`** (185
     rules, ch11–16); ch. XI alone has **34 marriage rules** (lord7-in-house ×12,
     planets-in-7th ×9, plus the marriage/impotence/adultery combinations). No
     new hand-encoding was needed — the earlier duplicates I drafted were dropped.
  2. The engine's chapter-map scan was **hard-coded to `htjah_vol1`**, so for
     houses 7–12 the map pulled nothing. **Fixed** (`HOUSE_CHAPTERS[7] =
     ("ch11","11")` + the scan now spans both htjah volumes). The lock is
     `test_house7_reads_cross_domain_ch11_from_vol2`: the career-tagged
     `ch11.lord7_in_10` sutra reaches the 7th house *only* via the vol-two scan.
- **Corpus (comprehensive):** ch. XI worked Charts 1–16, **43 factor-verdicts**
  (Bhāva / Lord / Kāraka), each cited verbatim; ÷3 chart-number holdout.
- **Result:** **OVERALL 33/43 within one grade (21 EXACT, 77%)** · **TRAIN 25/32
  (56% exact) · HOLDOUT 8/11 (73%).** As a **kendra**, the 7th *is* fully
  auditable (unlike dusthāna house 6). Mean Δ **+0.53** — a systematic
  over-scoring bias, and every large miss is on the positive side.

### Divergence patterns — a textbook REINFORCEMENT of the #1 fix

1. **Positive-side stacking over-score — ALL 8 of the >1 misses.** A planet in a
   kendra/trikoṇa **plus** dignity **plus** an aspect/conjunction/vargottama blows
   past the 2.4 ceiling to "very strong / very powerful" where Raman grades it
   mid-scale:
   - *Chart 15-Kāraka:* Venus in the 5th (trikoṇa +1.2) + two benefic aspects
     (Moon, Jupiter +1.4) → "very powerful"; Raman just places it (Δ **+3**).
   - *Chart 16-Lord:* Sun in a quadrant (+1.2) + **vargottama** (+1.2) = exactly
     the 2.4 ceiling → "very powerful"; Raman **"strongly placed"** (Δ +3).
   - *Chart 2-Lord:* Saturn kendra (+1.2) + friendly (+0.8) + **subhakartari**
     (+1.0) → "very powerful"; Raman **"well placed"** (Δ +3).
   - Plus 1-Kāraka +2, 3-Lord +2, 4-Kāraka +2, 7-Lord +2, 8-Kāraka +2.
   - *Legit counter-example (kept honest):* Chart 16-Kāraka Venus **exalted +
     vargottama** genuinely earns "very strong" (Δ +1) — stacking is only wrong
     when the parts are individually modest, exactly what a soft-cap preserves.

2. **The negative side is right, again.** Every afflicted / dusthāna / debilitated
   factor matched or came within one — 4-Bhāva "afflicted" exact, 9-Bhāva/Lord/
   Kāraka all exact-or-1, 15-Bhāva "weak" exact, 10-Lord debilitated exact. The
   two ceiling-fix families (positive stacking) never touch these.

3. **Clean-house baseline — five more data points, consistent direction.** Charts
   7, 10, 11, 13 have empty/unaspected 7ths that the scheme scores **0 →
   "moderate"** while Raman calls them "free of affliction / blemish-free / happy"
   — mildly positive. Small positive baseline, as before (not counted as misses
   here; mapped conservatively to "moderate").

### NEW signals

- **Fortification-by-aspect UNDER-scored on the bhāva** (both >1 unders):
  *Chart 12-Bhāva* — a clean 7th "**quite fortified**" by three benefic aspects
  scores only "moderately good" because `bhava_aspect_mul = 0.5` halves each
  (Δ −2). Argues the half-weight is too aggressive when several benefics pile onto
  an empty house — same family as the clean-house baseline.
- **Parivartana (sign exchange) is an unmodelled input** — *Chart 11-Lord*
  Jupiter⇄Venus exchange makes Raman call the lord "strong" (Δ −2); the scheme has
  no exchange bonus. A missing low-level factor, like combustion/upagraha.

---

## Houses 8–12 — pending

_One held-out audit per house as each is deepened; append the corpus size, the
within-one rate, the per-factor split, and the divergence patterns here.
Expect houses 8 & 12 (dusthānas) to be non-auditable like house 6._

---

## Consolidation — TODO (after House 12)

Tune the shared weights/thresholds/combine **once**, driven by the accumulated
patterns above, under the hard constraint that **no already-approved house
regresses** (ch. IV 9/9; house-1 verdicts byte-stable). Re-run every house's
held-out audit and record the before/after match rates here.

**Combined held-out audit so far (houses 2–5 + 7, comprehensive corpora):**
- **OVERALL 75/101 within one grade (~74%).**
- **HOLDOUT 20/28 (~71%)** — reserved, never used to derive anything. Its failures
  are all named patterns: 45-Lord, 48-Lord, 96-Karaka, 15-Kāraka, 16-Lord
  (stacking), 66-Bhāva (papakartari), 69-Bhāva & 12-Bhāva (light/clean-house). The
  reserved data independently points at the same fixes, so the consolidation's
  before/after can be quoted on data it never saw.
- House 6 (dusthāna) contributed none; houses 8 & 12 expected likewise.

**Running tally of the dominant signals (houses 2–5, 7):**
- **Planet (Lord/Kāraka) over-scoring by good placement / dignity / stacked
  positives — OVERWHELMING: confirmed ~17×** (houses 2–5: Charts 43 +5, 61 +6,
  53 +4, 40 +3, 65 +2, 91-Kāraka +4, 95 +5, 98 +7, 96-Kāraka +3; **house 7: 15
  +3, 16-Lord +3, 2-Lord +3, 1-Kāraka +2, 3-Lord +2, 4-Kāraka +2, 7-Lord +2,
  8-Kāraka +2**). The scheme lets a planet reach "very strong / very powerful"
  from placement + dignity + a benefic conjunction/vargottama **alone**; Raman
  reserves the top grades. **THE #1 fix**: a ceiling / diminishing return on
  stacked positives, applied only to the positive side (the negative side is
  already right — ch. VIII's 9 exact afflicted matches and house 7's exact
  afflicted/dusthāna rows both prove it). House-7 Chart-16-Kāraka (exalted +
  vargottama = genuinely "very strong") shows the cap must spare *individually*
  strong parts — a **soft** cap, not a hard clip.
- **Clean / light house UNDER-scored** — Raman rates empty-or-lightly-aspected
  houses higher than the scheme's neutral "moderate" — now **~10×** (houses 2–5:
  43, 52, 65, 69, 70; house 7: 7, 10, 11, 13 clean 7ths + **Chart 12** fortified-
  by-aspect). Fix: a small positive baseline on a clean house, and reconsider the
  `bhava_aspect_mul = 0.5` halving that under-credits multi-benefic fortification.
  *Caveat:* magnitude is mapping-sensitive; direction is robust, so keep it small.
- **Papakartari too harsh on the BHĀVA** — Chart 66: `kartari_papa = -1.0` sinks
  a Raman-"moderately strong" house to "weak". Weigh kartari less on the bhāva.
- **Optimistic combine over-rescues a Rāśi-afflicted planet** — Charts 45, 62.
- **Missing inputs (not weight bugs):** combustion penalty; upagrahas (Mandi/
  Gulika); **parivartana / sign-exchange bonus** (house-7 Chart 11). Candidates
  for new low-level factors before/alongside the tune.
