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

## House 8 — ch. XII (Vol. II) — NOT POINT-SCHEME-AUDITABLE (structural finding)

- Chapter-reading wired (`HOUSE_CHAPTERS[8]` = ch12; **34 rules already encoded**
  in htjah_vol2 — lord8-in-house ×12, planets-in-8th ×9, longevity/nature-of-death
  combinations). Guard: `test_house8_reads_ch12`. The Mainpuri house-8 reading
  runs (Gemini on the 8th, Āyuṣkāraka Saturn); 3 ch12 rules fire.
- **But ch. XII yields no held-out audit rows — the same shape as house 6.** The
  8th is a **dusthāna**, and Raman judges it entirely for **longevity and the
  timing / nature of death**, never grading the bhāva / lord / kāraka on the
  strength scale. The chapter's machinery is lifespan arithmetic, not strength:
  - **Length-of-life groups** — Bālāriṣṭa (<8y), Alpāyu (8–32), Madhyāyu (32–75),
    Pūrṇāyu (75–120) — fixed by ~20 named Bālāriṣṭa combinations, then
  - **Āyurdāya computation** — Piṇḍa / Aṁśa / Jaimini arcs of longevity (Chart 33:
    "total longevity 86 years 2 months 20 days"), then
  - **Māraka death-timing** — primary/secondary/tertiary death-dealers (2nd & 7th
    lords foremost) fixing the year (Chart 34: "died 15-4-1950, per Aṁśāyurdāya").
  - All 3 worked charts (33–35) are longevity/death cases; **zero** "the 8th house
    is fairly-strong / weak" verdicts. ("If the 8th lord is strong, the Lagna lord
    can kill in his period" is a *māraka* rule, not a bhāva-strength grade.)
- **Implication:** as with house 6, the strength point-scheme has no ground truth
  in ch. XII, so house 8 contributes **nothing** to the tuning corpus. Two of the
  three dusthānas (6, 8) are now confirmed non-auditable; **house 12**
  (loss/mokṣa) is the last expected one.

---

## House 9 — ch. XIII (Vol. II) — HELD-OUT AUDIT

- Chapter-reading wired (`HOUSE_CHAPTERS[9]` = ch13; **30 rules already encoded**
  in htjah_vol2). Guard: `test_house9_reads_ch13`. The 9th is a **trikoṇa**, so
  fully auditable.
- **Corpus (comprehensive):** ch. XIII worked Charts 86–97, **23 factor-verdicts**
  (Bhāva / 9th-lord / Pitrukāraka), each cited verbatim; ÷3 chart-number holdout.
- **Result:** **OVERALL 12/23 within one grade (3 exact, 52%)** · **TRAIN 4/14 ·
  HOLDOUT 8/9.** Mean Δ **+1.13 — by far the strongest over-scoring bias of any
  house so far** (house 7 was +0.53). 9 of the 11 misses are over-scores.
  *(The TRAIN/HOLDOUT flip is small-n noise: the exalted-but-afflicted karakas
  that the scheme most over-scores happened to fall in TRAIN charts 86/88/92/94;
  the ÷3 holdout charts 87/90/93/96 are mostly afflicted or clean and matched
  well. The signal is the pattern, not the split.)*

### Why house 9 is the sharpest confirmation of the #1 fix

ch. XIII is dominated by **father-longevity cases where the Pitrukāraka Sun (and
the 9th lord) is exalted or well-placed BUT afflicted** — papakartari, a nodal
constellation, or a dusthāna. Raman grades these **low** (the father dies early);
the scheme sees the dignity/placement bonus and grades them **high**. Exaltation
(+1.6) is the single biggest positive and recurs constantly here, so the stacking
over-score is amplified:

- *Chart 94-Kāraka:* Sun in the 9th (trikoṇa) + neechabhaṅga + subhakartari +
  benefic aspect → "very powerful"; Raman **"not very welcome but protected"**
  (Δ **+5**, the worst row in the entire audit).
- *Chart 92-Kāraka:* Sun in a kendra + **three** benefic co-tenants → "very
  powerful"; Raman **"well placed with slight afflictions"** (Δ +4).
- *Chart 88-Lord & 88-Kāraka:* exalted Mercury / Sun in the 9th, eclipsed by the
  nodes → "fairly powerful / fairly strong"; Raman **"exalted but eclipsed / not
  desirable"** (Δ +3 each).
- *Charts 86, 91, 96* — same family (exalted-or-kendra karaka, papakartari or
  Rahu, over-scored +3).
- **Negative side still holds:** the plainly-afflicted factors match or come
  within one (87-Lord/Kāraka, 89-Bhāva/Kāraka, 90, 93-Lord, 97) — the exact
  matches are all afflicted/dusthāna rows.

### Sharpened diagnosis for the consolidation

1. The **positive-side soft cap (#1)** is confirmed a further **9×**, now most
   visibly on **exaltation**: a single exalted planet in a good house reaches the
   ceiling before any affliction is weighed.
2. **An affliction that Raman treats as decisive is under-weighted next to
   dignity.** Papakartari (−1.0), a nodal/eclipse constellation (unmodelled), and
   "exalted-yet-in-a-dusthāna" do not, in the scheme, veto the +1.6 exaltation —
   but for Raman they do (the father dies). The cap should let a strong affliction
   **cancel** the dignity bonus, not merely subtract from it. (Consistent with the
   Chart-66 papakartari finding; here it is the dominant lever.)
3. **Bhāva occupant-scoring ignores dignity — under-scores neechabhaṅga Rājayoga.**
   *Chart 95-Bhāva:* a 9th with a debilitated-but-neechabhaṅga Jupiter reads
   "moderate"; Raman **"quite strong"** (Δ −3), because a bhāva occupant counts
   only ±0.7 by benefic/malefic, never its dignity. Two under-scores (92, 95) are
   this shape — the clean/fortified-house baseline, seen from the occupant side.

---

## House 10 — ch. XIV (Vol. II) — NOT POINT-SCHEME-AUDITABLE (structural finding — a NEW kind)

- Chapter-reading wired (`HOUSE_CHAPTERS[10]` = ch14; **30 rules already encoded**
  in htjah_vol2). Guard: `test_house10_reads_ch14`. The Mainpuri house-10 reading
  runs; 3 ch14 rules fire.
- **But ch. XIV yields no held-out strength rows — and NOT for the dusthāna
  reason.** The 10th is a **kendra**, so I expected it auditable. It is not,
  because of *what Raman judges the 10th FOR*: **identifying the nature / type of
  profession**, never grading the bhāva / lord / kāraka on the afflicted↔powerful
  scale. A full scan of ch. XIV (charts 114–132) found:
  - **0** "Karmakāraka" gradings and **0** "the 10th house/lord is strong / weak /
    afflicted / fairly …" verdicts (vs one *per chart* in ch. XI & XIII);
  - **105** profession-type phrases — the charts conclude on the *kind* of career:
    "a military emperor" (115), "a teacher" (117), "an accounts officer" (119),
    "a great educationist / mathematician / jurist" (120), "an income-tax
    official" (123), "an actor" (131).
  - The method is **determinant-selection**: pick the strongest of {10th lord,
    its occupant, the Navāṁśa-lord of the 10th, reckoned from the strongest of
    Lagna / Moon / Sun}, by **shaḍvarga** strength, then read *that planet's*
    nature (Jupiter → intellectual, Venus → aesthetic, Mars → military, Mercury →
    writing/trade, Saturn → labour). Strength is used **comparatively** (to pick
    the determinant), never as a bhāva-quality verdict.
- **The methodological lesson:** auditability is **not** predicted by dignity
  class (kendra vs dusthāna) — it is predicted by *what Raman judges the house
  FOR*. Three non-auditable houses, three different reasons: **6** disease-events,
  **8** longevity/death-events, **10** profession-type identification. Only houses
  whose chapter grades the bhāva/lord/kāraka on the strength scale (1–5, 7, 9)
  feed the tuning corpus.
- **Implication:** house 10 contributes **nothing** to the tuning corpus. Combined
  tally stays at houses 2–5, 7, 9. House 11 (gains) remains to be checked; house
  12 (dusthāna) is expected non-auditable.

---

## House 11 — ch. XV (Vol. II) — HELD-OUT AUDIT

- Chapter-reading wired (`HOUSE_CHAPTERS[11]` = ch15; **29 rules already encoded**
  in htjah_vol2). Guard: `test_house11_reads_ch15`.
- **AUDITABLE — auditability was genuinely open and had to be checked** (house 10
  taught that dignity class does not predict it). ch. XV is a **hybrid like ch.
  XIII**: 23 per-chart "The Eleventh House:" + 23 "The Eleventh Lord:" strength
  headings (vs 2 in the non-auditable ch. XIV), grading the 11th house and lord on
  the strength scale — in service of **elder-sibling survival** and **Dhana
  yogas**. (0 "Labhakāraka" gradings, so Bhāva + Lord only, no kāraka row. The
  chapter's opening *gains-type* passage — "if Saturn → industries, if Venus →
  films …" — mirrors ch. XIV, but the worked charts 210–232 do grade strength.)
- **Corpus:** ch. XV worked Charts 210–218, **16 factor-verdicts** (Bhāva /
  11th-lord), each cited verbatim; ÷3 holdout.
- **Result:** **OVERALL 12/16 within one grade (10 EXACT, 75%)** · **TRAIN 7/11 ·
  HOLDOUT 5/5 (100%).** Mean Δ **+0.50** — the familiar over-scoring bias; 3 of 4
  misses are over-scores.

### Divergence patterns — same signal, exaltation again to the fore

1. **Positive-side stacking, most visibly on exaltation / Navāṁśa dignity** (all 3
   over-misses — reinforcing the sharpened house-9 finding):
   - *Chart 211-Lord:* Mars in the Lagna (kendra) + **Navāṁśa exaltation** →
     "very powerful"; Raman grades it barely adequate, "allowing one elder co-born
     to survive" (Δ **+4**).
   - *Chart 218-Lord:* Sun **exalted** in a kendra → "very powerful"; Raman just
     "well placed" (Δ +3).
   - *Chart 215-Lord:* Moon own-sign, Saturn-afflicted, but a Navāṁśa
     exalted-Mars conjunction (+1.6) → "fairly good"; Raman "moderate" (Δ +2).
   - *Legit-strong control:* Chart 212-Lord Venus (own-sign moolatrikoṇa with
     benefics) = "very strong" both ways (Δ 0) — the soft cap must spare it.
2. **Fortified house dragged by one occupant + halved aspects** (the lone
   under-miss): *Chart 217-Bhāva* — an 11th "**strongly disposed**" (aspected by
   Saturn + exalted Mercury) reads "moderate" because a Ketu occupant is −0.7 and
   the two benefic aspects are halved by `bhava_aspect_mul` (Δ −3). Same family as
   the clean/fortified-house baseline.
3. **Negative side exact, again** — every empty/afflicted/debilitated factor is
   exact or within one (10 exact: 210, 211-Bhāva, 213, 214, 215-Bhāva, 216, 218-
   Bhāva …). The holdout is a clean **5/5**.

---

## House 12 — ch. XVI (Vol. II) — NOT POINT-SCHEME-AUDITABLE (structural finding)

- Chapter-reading wired (`HOUSE_CHAPTERS[12]` = ch16; **28 rules already encoded**
  in htjah_vol2). Guard: `test_house12_reads_ch16`. The Mainpuri house-12 reading
  runs; a ch16 rule fires.
- **Confirmed non-auditable — a dusthāna, judged for loss and mokṣa events, not
  bhāva strength.** A full scan of ch. XVI (charts 233–258) found **2** "The
  Twelfth House:" headings and **~4** strength-verdict phrases, versus **41**
  loss/mokṣa-event phrases. The chapter judges:
  - **Loss / expenditure / affliction** (planet-in-12th effects: "loss of some
    limb", "weak eye-sight", "loses all his money", penury, disease);
  - **Mokṣa / liberation** — combinations for Kaivalya and *jeevanmukta*, which
    Raman himself flags as **unverifiable**: *"There is no way of verifying
    predictions bearing on the state of the soul after it shakes off the physical
    body."*
  - The **Bhāvārtha-Ratnākara dictum** — a house is fortunate if *its* kāraka sits
    in the 12th (Chart 233: Moon-in-12th → fortunate re: the mother).
  - It carries the "(a)–(f) factors governing / Time of Fructification" timing
    structure, but that times loss/mokṣa events; it never grades the 12th
    bhāva/lord/kāraka on the afflicted↔powerful scale.
- **Implication:** house 12 contributes **nothing** to the tuning corpus.

---

## THE TWELVE-HOUSE WALK IS COMPLETE

Every house now reads its own HTJAH chapter via `HOUSE_CHAPTERS` (house 1 stays
absent so its reviewed output is byte-stable). The audit map:

| Auditable (feeds the tuning corpus) | Non-auditable (structural finding) |
|---|---|
| 1 (ch. IV — calibration anchor) | **6** (ch. IX — disease events) |
| 2 (ch. V), 3 (ch. VI), 4 (ch. VII), 5 (ch. VIII) | **8** (ch. XII — longevity/death) |
| 7 (ch. XI), 9 (ch. XIII), 11 (ch. XV) | **10** (ch. XIV — profession-*type*) |
| | **12** (ch. XVI — loss/mokṣa events) |

**The load-bearing lesson (house 10):** auditability is predicted by *what Raman
judges the house FOR*, not by dignity class. The 6th/8th/12th dusthānas judge
disease/death/loss **events**; the 10th (a kendra!) reads career **type**; only the
seven strength-graded houses feed the corpus. Guards
`test_house{3..12}_reads_ch{6..16}` (+ the cross-volume lock) hold all twelve
wirings; 208 doctrine tests pass; house-1 verdicts byte-stable throughout.

**→ The deferred CONSOLIDATION is now the next step** (below).

---

## Consolidation — DONE (v1: the positive soft-cap)

All twelve houses are wired; the seven strength-graded corpora are collected. The
consolidation tunes the shared scheme **once**, under the hard constraint that
**no already-approved house regresses** (ch. IV anchor stays 9/9; house-1 verdicts
byte-stable).

### What was changed (one localized edit to `_combine`)

The audit's single overwhelming, over-determined signal (~29×) was **positive-side
stacking**: a factor reaching "very strong / very powerful" from placement +
dignity + a benefic conjunction/vargottama summed additively, where Raman reserves
the top grades. The fix is **diminishing returns on stacked positives**, applied to
the **positive side only** (the negative side already matched Raman everywhere):

```
_POS_KNEE = 1.6   # = the exaltation weight: "one strong dignity's worth"
_POS_SLOPE = 0.1  # positives past the knee compound only weakly
_cap_positive(pos) = pos if pos <= 1.6 else 1.6 + (pos - 1.6) * 0.1
```

`_combine` now sums each varga frame's **positive** deltas, soft-caps that sum, and
adds the (linear) negative deltas — then blends Rāśi/Navāṁśa as before (BHĀVA
additive, PLANET optimistic `max+0.3·min`). The knee is deliberately set so **no
mid-range verdict, no ch. IV anchor factor, and the approved house-1 output all
stay put** — only the over-stacked positives compress. Weights, thresholds, and the
combine topology are otherwise unchanged. Deeper fixes flagged in the audit
(clean-house baseline, kartari re-scope, affliction-cancels-dignity, missing inputs
combustion/upagraha/parivartana/nodal) are **not** in v1 — they need the houses-2–5
corpora (ephemeral) or new low-level factors, and several are the source of the few
residual under-scores; a v2 can take them up.

### Before → after (re-run on the LIVE tuned engine)

| corpus | before (within-one) | after |
|---|---|---|
| house 7 (ch. XI, 43) | 77% (Δ̄ +0.53) | **86% (Δ̄ +0.16)** |
| house 9 (ch. XIII, 23) | 52% (Δ̄ +1.13) | **74% (Δ̄ +0.26)** |
| house 11 (ch. XV, 16) | 75% (Δ̄ +0.50) | 75% (Δ̄ **+0.06**) |
| **pooled (82)** | **70%**, over>1 **20** | **80%**, over>1 **7** |
| **HOLDOUT (÷3, 25)** | **84%** | **93%, 0 over-scores** |
| ch. IV anchor (Charts 12–14) | 9/9 | **9/9 (held)** |
| house-1 Mainpuri | vp / fg / fs | **vp / fg / fs (byte-stable)** |

The systematic over-scoring bias is **gone** (mean Δ +0.70 → +0.16; the errors are
now balanced, 7 over / 9 under, not 20 / 5). The reserved holdout — never used to
derive anything — improved most (84% → **93%**, zero remaining over-scores), so the
gain is genuine generalisation, not in-sample fit. The cost is **+4 new
under-scores** (genuinely-strong factors nudged one grade low — the price of the
soft cap; they are within the residual-under-score family flagged above). **208
doctrine tests pass; house-1 byte-stable.**

*Scope note (honest):* the before/after is measured on the corpora regenerable this
session — houses **7, 9, 11** (the ch. XI/XIII/XV builders) + the ch. IV anchor +
the house-1 guard. Houses **2–5**' corpora were scratchpad-only and lost to a
container reset; they are **not** re-measured here. But their documented divergences
(43 +5, 61 +6, 53 +4, 40 +3, 91/95/98 …) are the *same* positive-stacking family the
cap targets, so the fix applies to them by construction; the 93% holdout is the
defensible generalisation number.

### v2 exploration — the weight-tuning space is exhausted; further gains need FEATURES

After v1 I reconstructed a fresh **house-2 corpus** (ch. V, Charts 40–48, 22 rows)
— a house **not used to derive v1** — and tested the remaining candidate weight
fixes on the pooled set (h2 + h7 + h9 + h11 = 104 rows). Findings:

- **v1 generalises without bias to the unseen house.** House 2 under the live v1
  engine: mean Δ **+0.00**, errors balanced (5 over / 4 under) — the systematic
  over-scoring is gone here too, not just on the tuning corpora. Its lower absolute
  within-one (59%) is **variance, not bias**.
- **The clean-house baseline is NET-NEUTRAL and cannot be tuned.** Adding a positive
  baseline to empty/lightly-aspected bhāvas moves the pooled within-one by **at most
  +1 row** (76% → 77% at B≈0.3–0.5) and *regresses* past B≈0.5. Reason, now proven
  on data: Raman's own clean-house verdicts are **contradictory across houses** —
  "moderate" for the empty 7th/9th/11th (h7 Ch7/10/11/13, h11 Ch213/216/218) but
  "fairly strong" for the empty 2nd/4th (h2 Ch43/45, h4 Ch65/69/70). No single
  scalar satisfies both; the ledger's earlier "keep it small / direction robust,
  magnitude mapping-sensitive" caveat is confirmed — the honest magnitude is ~zero.
- **The residual misses are high-variance STRUCTURAL cases the weight vocabulary
  cannot express**, not mis-calibrations: a bhāva with **dignified / Rajayoga
  occupants** (h2 Ch40 own-Mars + neechabhaṅga-Moon + exalted-aspect → "very
  strong", read weak, Δ −6; Ch41 three-planet Rajayoga, Δ −4) — the ±0.7
  occupant scoring is blind to occupant dignity; plus **combustion**, **Mandi /
  upagrahas** (ch. VI Charts 59/60/62), **parivartana**, and **nodal/eclipse
  constellations**. Only ~2 corpus rows even cite occupant dignity, so no single
  one is worth a bespoke weight.

**Verdict: v1 (the positive soft-cap) is the correct stopping point for a
weight-and-combine consolidation.** The point-scheme's tunable surface is now fit
to Raman as well as it can be — mean Δ ≈ 0 everywhere, holdout 93%. Closing the
remaining gap requires **new low-level inputs** (occupant-dignity in `_assess_bhava`,
a combustion penalty, upagraha occupancy, a parivartana bonus, a nodal-constellation
affliction) — a *feature-modelling* project (call it v3), distinct from tuning, and
larger. It is scoped in the "missing inputs" bullet of the running tally below.
*(No engine change in v2 — this is a validated negative result that fixes the
stopping point.)*

---

### Pre-consolidation record (the "before")

Tune driven by the accumulated patterns below; re-run every house's held-out audit
and record before/after above.

**Combined held-out audit — FINAL pre-consolidation (houses 2–5 + 7 + 9 + 11):**
- **OVERALL 99/140 within one grade (~71%).**
- **HOLDOUT 33/42 (~79%)** — reserved, never used to derive anything. Its failures
  are all named patterns: 45-Lord, 48-Lord, 96-Karaka, 15-Kāraka, 16-Lord,
  94(h9)-Kāraka (stacking), 66-Bhāva (papakartari), 69-Bhāva & 12-Bhāva & 95(h9)-
  Bhāva & 217(h11)-Bhāva (light/clean/fortified-house). House 11's holdout is a
  clean 5/5. The reserved data independently points at the same fixes.
- **House 9 dropped the average** (52% within-one): ch. XIII is an adversarial
  corpus for the scheme — mostly exalted-but-afflicted father-charts, exactly the
  cases the #1 fix targets. It is the sharpest single-house confirmation, not an
  outlier. Houses 7 (77%) and 11 (75%) bracket the typical rate.
- **Four houses confirmed non-auditable:** 6 (disease-events), 8 (longevity/death),
  10 (profession-*type* — a kendra, yet non-auditable), **12 (loss/mokṣa events)**.
  Auditability tracks *what Raman judges the house for*, not its dignity class. The
  seven strength-graded houses (2–5, 7, 9, 11) are the whole corpus; the walk is
  **complete** and this combined number is **final** pre-consolidation.

**Running tally of the dominant signals (houses 2–5, 7, 9, 11):**
- **Planet (Lord/Kāraka) over-scoring by good placement / dignity / stacked
  positives — OVERWHELMING: confirmed ~29×** (houses 2–5: Charts 43 +5, 61 +6,
  53 +4, 40 +3, 65 +2, 91-Kāraka +4, 95 +5, 98 +7, 96-Kāraka +3; house 7: 15 +3,
  16-Lord +3, 2-Lord +3, 1-Kāraka +2, 3-Lord +2, 4-Kāraka +2, 7-Lord +2, 8-Kāraka
  +2; house 9: 94-Kāraka +5, 92-Kāraka +4, 86/88-Lord/88-Kāraka/91/96 +3;
  **house 11: 211-Lord +4, 218-Lord +3, 215-Lord +2**).
  The scheme lets a planet reach "very strong / very powerful" from placement +
  dignity + a benefic conjunction/vargottama **alone**; Raman reserves the top
  grades. **THE #1 fix**: a ceiling / diminishing return on stacked positives,
  applied only to the positive side (the negative side is already right — ch. VIII
  and house-9's exact afflicted/dusthāna rows prove it). House-7 Chart-16-Kāraka
  (exalted + vargottama = genuinely "very strong") shows the cap must spare
  *individually* strong parts — a **soft** cap, not a hard clip.
- **Exaltation is the most over-credited positive** (house 9, sharpened): +1.6
  reaches the ceiling on its own, so an "exalted but papakartari / nodal /
  dusthāna" factor — which Raman grades LOW — reads high. The cap should let a
  strong affliction **cancel** the dignity bonus, not merely subtract from it.
- **Clean / light / neechabhaṅga / fortified-by-aspect house UNDER-scored** —
  Raman rates empty, lightly-aspected, Rājayoga-occupied, or benefic-aspected
  houses higher than the scheme's neutral "moderate" — now **~14×** (houses 2–5:
  43, 52, 65, 69, 70; house 7: 7, 10, 11, 13 + Chart 12; house 9: 92, 95;
  house 11: 217-Bhāva). Fix: a small positive baseline on a clean
  house; reconsider `bhava_aspect_mul = 0.5`; and let a bhāva **occupant's
  dignity** count (a debilitated-but-neechabhaṅga or exalted occupant, not just
  its ±0.7 benefic/malefic sign).
- **Papakartari too harsh on the BHĀVA but too soft on the PLANET** — Chart 66
  (bhāva sunk to "weak"); yet on a planet (house 9) papakartari −1.0 fails to
  overcome a +1.6 exaltation Raman treats as vetoed. Kartari needs re-scoping per
  factor type.
- **Optimistic combine over-rescues a Rāśi-afflicted planet** — Charts 45, 62.
- **Missing inputs (not weight bugs):** combustion penalty; upagrahas (Mandi/
  Gulika); **parivartana / sign-exchange bonus** (house-7 Chart 11); **nodal /
  eclipse ("eclipsed") constellation affliction** (house-9 Charts 88, 94).
  Candidates for new low-level factors before/alongside the tune.

---

## Interpretation layer — `app/medini/doctrine/interpret.py`

The point-scheme this ledger audits produces *structured* verdicts, not prose. A
thin LLM layer now renders those verdicts as a reading — **grounded**, so it
interprets the doctrine rather than casting its own.

- `build_grounding(HouseJudgment)` — pure, key-free serialization of one house's
  executed judgment into the only evidence the model is allowed to read: the
  headline (Lagna+lord+kāraka **synthesis**, kept distinct from the raw
  sutra-polarity blend), the three testimonies with their **signed findings**,
  the **verbatim** fired sūtras (keyed by rule id), the named combinations and the
  dasa they fructify in, the Chandra-Lagna (from-Moon) view, and the first-house
  testimony.
- `interpret_house` / `interpret_chart` (+ `interpret_*_of_chart` convenience) —
  call Claude (`claude-opus-4-8`, adaptive thinking, streamed) under a system
  prompt whose one rule is grounding: every claim must trace to a verdict label, a
  listed finding, a quoted sūtra, a combination, or a dasa window; no placement,
  aspect, or prediction the engine never derived. Standard SDK auth
  (`ANTHROPIC_API_KEY`); no credential is sourced from anywhere else.
- Tests (`TestInterpretGrounding`, key-free) pin the anti-hallucination contract:
  the packet carries the three testimonies + headline, findings/sūtras stay
  verbatim and traceable to fired rule ids, and the whole-chart compaction bounds
  each testimony to its strongest findings.

### Cost architecture — accurate *and* cheap (no trade)

Feeding the LLM every house's full packet is ~48K input tokens; the earlier
whole-chart compaction dropped to ~4.6K but was *lossy* (top-3 findings, no
sutras/timing). The waste was redundancy, not detail: the chart's ≤9 planets fill
36 lord/karaka slots (Jupiter 6x, Mars/Saturn 4x each), and a planet's findings are
the same wherever it rules.

- `build_chart_grounding` emits each planet **once** into a `planets` dossier (all
  findings kept) and has each house reference its lord/karaka by name. Result on
  Mainpuri: **48K -> ~19K tokens, fully lossless** (verified: the dossier is a
  superset of every per-house lord/karaka finding). The remaining bulk is genuine
  per-house content (77 unique verbatim sutras, bhava findings), not repetition.
- `interpret_chart` is **hybrid + cached + structured**: one `messages.parse` on the
  cheap tier (`claude-haiku-4-5`) returns all twelve grounded readings as a
  `ChartReadings` schema; one Opus (`claude-opus-4-8`) streamed call writes the
  whole-chart synthesis. The static system prompt and the planet dossier carry
  `cache_control:{"type":"ephemeral"}`, so re-runs read the shared prefix cheaply.
  `count_tokens` reports the packet size before sending. Rough: ~$0.02 (Haiku
  readings) + Opus synthesis per chart, less on cached re-runs.
- `resolve_current_dasha(chart, birth_jd, target_jd)` walks the Vimshottari sequence
  (reusing `calculate_vimshottari_mahadasha` + `_maha_sequence`/`_antardasha_spans`)
  to the period running at a date, returning MD/AD + calendar windows. The engine
  never infers this from a date — the resolved `{"md":..,"ad":..}` is fed into
  `judge_all_houses_doctrine(dasha=...)` so every reading is time-anchored. Mainpuri
  (born 1989-10-12) at 2026-07-06 -> **Mercury / Mercury** MD-AD.

Follow-up (**v3, sequenced**): the engine's *verdicts* still carry the ledger's
known gaps (11th-house afflicted-vs-Rajayoga, exaltation over-credit); those are the
next phase — feature-modeled and re-audited — after this pipeline lands.

---

## Phase 2 — engine-verdict accuracy

### Increment 1 — occupant dignity in the bhava (DONE)

The bhava scored an occupant purely by its ±0.7 benefic/malefic nature, blind to its
**dignity** — so Mainpuri's 11th (Sun + Mars + **exalted** Mercury) read three stacked
malefics and graded **afflicted**, missing the rajayoga the exalted occupant makes.
This is the ledger's own flagged gap ("let a bhava occupant's dignity count ... an
exalted occupant, not just its ±0.7").

`_assess_bhava` now mirrors the exalted-companion credit already in
`_conjunction_findings`: an **exalted** occupant is credited `conjunct_exalted`
(+1.6) in place of a bare −0.7; an **own-sign** occupant adds +1.2; a **debilitated**
occupant adds −1.6 (or +0.2 if neechabhanga). Friendly/neutral occupants — too common,
low signal — stay on nature alone, to keep the change narrow.

- **Effect (Mainpuri):** exactly one house moves — the **11th bhava afflicted ->
  moderate** (headline weak -> moderate), matching Raman's rajayoga reading. Lord and
  karaka verdicts are untouched (only `_assess_bhava` changed); house-1 stays *very
  powerful* (vargottama override); all other bhavas unchanged (no other house has an
  exalted/own/debilitated occupant).
- **Regression:** 220 doctrine tests pass, incl. house-1 byte-stability and the two
  new guards (`test_exalted_occupant_credited_not_bare_malefic`,
  `test_friendly_or_neutral_occupant_stays_on_nature`). The ch.IV anchor is
  untouched — it calibrates house-1 (override) and lord/karaka charts, neither of
  which this feature reaches.

Remaining Phase-2 gaps (next increments, each its own audited commit): exaltation
**over-credit** on an afflicted factor (the cap should let a strong affliction cancel
the +1.6, e.g. exalted-but-papakartari); papakartari re-scoped per factor type;
combustion penalty; upagraha (Mandi/Gulika) occupancy; parivartana / sign-exchange
bonus; nodal / eclipse constellation affliction.

### Increment 2 — exaltation over-credit, examined (DONE, as a blend fix)

Reconstructed the audit corpora (ch. IV anchor + h2/h7/h9/h11, 104 rows) and
committed them under `docs/raman_doctrine/audit/` so they survive resets. Baselined
the post-2.1 scheme: anchor 8/8 within-one; corpus 79/104 within-one, over>1=12,
under>1=13, mean +0.13.

Inspecting the 12 over-predictions (`validate_house.py -v`) split the "exaltation
over-credit" into two mechanisms:

1. **Phantom-frame rescue (fixable, real bug).** Chart 9/89 — Sun *exalted* but
   dusthana + papakartari + malefic conjunction/aspect — sums to −1.8 in the Rasi
   (correctly afflicted), yet scored −0.54 ("moderate"). The optimistic PLANET blend
   `max()+0.3·min()` took the EMPTY Navamsa frame as a 0 and let it rescue the
   afflicted Rasi. Fix: blend only across frames that carry findings; an un-assessed
   varga is "no testimony", not "neutral strength". **Result: within-one 79→81,
   exact 44→52, over>1 12→10, under>1 flat at 13, mean +0.13→−0.02, anchor still
   8/8.** Over dropped with under unchanged — a real fix, not the zero-sum frontier.
   No Mainpuri rendered verdict changes (the live engine always assigns a Navamsa
   D9-dignity finding, so the phantom-empty frame never arises there; the fix is
   latent-correctness + corpus fit). Guarded by
   `test_unassessed_frame_does_not_rescue_affliction` and the raised audit floor (81).

2. **Stacked positives (the v2-exhausted frontier).** The remaining 10 over-rows
   (e.g. 9/92, 9/94, 2/43, 11/211) are kendra + dignity + benefic conjunctions
   saturating just under the ceiling. over>1=10 vs under>1=13 is near-symmetric —
   damping the positive cap would only trade over for under (confirming the v2
   negative result). Closing this needs new FEATURES (combustion, upagraha,
   parivartana, nodal constellation), not a cap tweak — the next Phase-2 increments.

### Increment 3 — bhāva-aspect dignity + audit-honesty sync (DONE)

The residual mispredictions (audit `-v`) showed the worst misses are BHĀVA
under-predictions where an occupant's or aspecting planet's **dignity** is unseen —
worst of all chart 40's 2nd bhāva (d=−6): "own-sign Mars + neechabhaṅga Moon +
exalted-Jupiter aspect", which Raman calls "very strong". Two gaps behind it:

1. **Engine (new feature): bhāva-aspect dignity.** `_assess_bhava`/`_aspect_findings`
   now credit an **exalted** planet aspecting a house like an exalted companion
   (`conjunct_exalted × bhava_aspect_mul`), whatever its functional nature — the same
   dignity-over-nature logic as the occupant (2.1) and conjunction credits.
   Blast radius on Mainpuri is one house: **5th bhāva `weak → moderate`** (exalted
   Mercury aspects it). 224 tests pass; `test_exalted_aspect_on_bhava_is_credited`.
2. **Audit honesty:** the harness still scored occupants flat ±0.7 — stale vs the 2.1
   engine — so the audit *under-reported* the engine's real accuracy. `delta_of` now
   models occupant dignity (2.1) and aspect dignity (2.3), and chart 40's occupant/
   aspect dignities are encoded from Raman's own note. Result: chart 40's 2nd bhāva
   **d=−6 → −2**; within-one holds at 81, anchor 8/8, under-count unchanged.

The features now fire correctly; chart 40 stops two grades short of "very strong"
only because the positive soft-cap holds the score near 1.0. Combustion was
**rejected** for this increment: it appears in ~1 corpus row (chart 45's Venus+Sun)
and has high blast radius on Mainpuri (Mercury+Mars are combust in the 11th → would
undo the 2.1 gain). The remaining frontier is positive-cap saturation, bounded on
both sides (over>1=10 stacked positives; the "very strong" tail of under>1) — a
structural saturation change, not more features, is what moves it next.

### Increment 4 — dusthāna-lordship penalty (held-out-driven, DONE)

The **held-out** validation (Vol 1 Ch. VII, `docs/raman_doctrine/validation/`) surfaced
the gap the tuned corpora could not: `_assess_planet` scored a planet's placement /
dignity / aspects / conjunctions but never penalised it for **being a functional
malefic by dusthāna lordship** (Raman, Chart 64: "the Moon owns the 6th and hence
afflicted"). `_planet_nature` already knew a dusthāna lord is a functional malefic —
but only for how it afflicts *others*, never itself.

`_assess_planet` now adds a `dusthana_lord` finding (−1.0) when the planet owns a
dusthāna (6/8/12) from the Lagna — the **Lagna lord exempt** (its ascendant lordship
redeems a coincidental dusthāna ownership; this also keeps house-1 byte-stable, since
Mainpuri's Mars owns Scorpio-1 AND Aries-6).

- **Held-out effect:** the one true dusthāna case (ch64 kāraka Moon, owns 6th) improved
  **+3 → +2**; mean Δ +1.1 → +1.0; **no held-out row regressed**; 233 tests pass. It
  does NOT fully close ch64 — the +1.2 kendra-placement credit (Moon in the 4th) still
  props the kāraka to "moderate"; closing it needs the companion **kendra-over-credit**
  fix (the v2 positive-saturation frontier).
- **Blast radius (Mainpuri):** 4 houses whose lord/kāraka owns 8/12 (H7/8/11/12). Note
  the **dignity interaction**: exalted Mercury owns the 8th → now "weak"; a flat −1.0
  may over-penalise a strongly-dignified dusthāna lord. No held-out evidence yet either
  way — flagged for calibration when the gold set grows (+ Navāṁśa).
- The token audit harness is blind to this feature (corpus rows don't encode lordship),
  so the **held-out set is its judge**. As the gold set grows it is also Phase B's test.

### Increment 5 — mild frame cannot rescue a deeply-afflicted one (held-out-driven, DONE)

The full-verdict held-out set (Ch VII) exposed the next over-credit: the optimistic
cross-varga blend `hi + 0.3·lo` rescued a **deeply-afflicted** frame via a **mild**
opposite one. Chart 71 kāraka Moon: Rāśi **−1.34** (afflicted — kendra +1.2, dusthāna
−1.0, then Ketu/Saturn/Rahu), Navāṁśa **+0.8** (Moon merely "friendly", one finding) →
blend `0.8 + 0.3·(−1.34) = +0.4` = "moderately good". Raman: **afflicted**. The optimism
was calibrated on a *strong* Navāṁśa rescue (Chart 12 exaltation), not a mild one.

`_combine` now withholds the 30% discount from a **deeply-afflicted** weaker frame
(`lo < _AFFLICT_FLOOR = −1.0`, i.e. worse than one full malefic) when the rescuer is
itself **mild** (`hi < _RESCUE_KNEE = 1.2`), applying `_RESCUE_W_WEAK = 0.9` instead.
Gated on affliction **depth** so a *mild* affliction is still rescued as before —
Mainpuri's house-1 Mars (lo −0.6) is untouched, keeping the anchor byte-stable.

- **Effect:** ch71 kāraka **+3 → +2** (moderately good → moderate, score +0.4 → −0.41);
  held-out mean Δ +1.22 → +1.11. **Zero regression:** the branch almost never fires in
  the token corpora, so tuned stays 89/112 within-one, anchor 8/8, house-1 byte-stable;
  234 tests pass. Auditable (unlike 2.4) since it lives in `_combine`.
- **Honest limit:** it does not cross ch71 into within-one. An ungated version (any
  affliction, w 0.9) did move held-out 4→5/9 **but shifted house-1's mildly-afflicted
  Mars** — over-reaching for N=9. So 2.5 is the *conservative, principled* fix; fully
  closing the kāraka gap needs more held-out N to calibrate the magnitude.
- **Still open:** ch70 lord/kāraka (+3) is a *different* mechanism — the kendra +1.2
  over-credits **in the Rāśi itself** (rasi +0.23 where Raman sees affliction), the
  positive-saturation frontier; and the clean/empty-house under-score (ch70 bhāva −2).

### Increment 6 — natural-benefic occupant is not blemished by functional-malefic status (held-out-driven, DONE)

Phase A.1 of 2.6, the cleaner of the two cross-house-confirmed bhāva gaps. The widened
held-out set (Ch VII → 7 charts + Vol 2 Ch XIII 9th house) showed `_assess_bhava`
driving a **natural benefic** occupant to −0.70 whenever it happened to be a **functional
malefic** (a dusthāna/maraka lord): ch72 Venus (7/12 lord for Scorpio) and ch74 Venus
(3/8 lord for Pisces). Raman credits the natural benefic's presence outright — ch72 "the
fourth is **not blemished**", ch74 "**feebly blemished**" — because functional nature
governs the *results a planet gives as a lord*, not its blemishing weight as an occupant.

`_assess_bhava` now credits an occupant as benefic if it is functionally benefic
(`ben`, already handled — yogakāraka/functional benefic) **or** a natural benefic
(`nat_ben`). Only a planet malefic by **both** measures blemishes as an occupant. Scoped
to occupants (the evidenced site); aspects unchanged.

- **Held-out effect:** ch72 bhāva **−4 → −1** (within-one) and ch74 bhāva **−2 → 0**
  (exact). Pooled (4th + 9th) within-one **35% → 45%**; Ch VII within-one **39% → 50%**;
  bhāva per-factor within-one 3/8 → 5/8.
- **Zero tuned/anchor cost:** the token audit is blind to natural-vs-functional nature
  (corpus occupant tokens carry only a `benefic` flag), so tuned stays **79%** and the
  live-engine anchor is **byte-stable** — the tuned "weak" bhāvas are all blemished by
  *natural* malefics (`nat_ben` False), untouched. 237 doctrine tests pass; guarded by
  `TestNaturalBeneficBhavaOccupant` (credit for a natural-benefic functional malefic;
  penalty preserved for a natural malefic).
- **Still open (A.2 / B):** ch73 & ch94 bhāva (−4) are the *neechabhanga-rescued aspect*
  under-credit (a different mechanism); and the kendra-offsets-affliction lord/kāraka
  over-credit (B) — cross-house-confirmed (ch64/70/71/72/73/93), the next candidate.
