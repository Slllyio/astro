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

> **DATA-INTEGRITY CORRECTION (increments 6–8).** Earlier drafts of these increments
> called Vol 2 Ch XIII (charts 92/93/94) a "held-out cross-house" set. It is NOT — Ch XIII
> is the tuned `h9` calibration chapter, so those charts were in the training data. All
> "cross-house-confirmed" / "pooled (4th+9th)" claims below are retracted; the honest
> held-out set is **Ch VII 4th house only** (ch64/69/70/71/72/73/74). The fixes themselves
> were driven and validated by Ch VII held-out charts, so A.1/A.2 stand; only the framing
> was wrong. See `docs/raman_doctrine/validation/REPORT_ch13_vol2_9th_rederivation.md`.

Phase A.1 of 2.6. The **held-out Ch VII** set (7 charts) showed `_assess_bhava`
driving a **natural benefic** occupant to −0.70 whenever it happened to be a **functional
malefic** (a dusthāna/maraka lord): ch72 Venus (7/12 lord for Scorpio) and ch74 Venus
(3/8 lord for Pisces). Raman credits the natural benefic's presence outright — ch72 "the
fourth is **not blemished**", ch74 "**feebly blemished**" — because functional nature
governs the *results a planet gives as a lord*, not its blemishing weight as an occupant.

`_assess_bhava` now credits an occupant as benefic if it is functionally benefic
(`ben`, already handled — yogakāraka/functional benefic) **or** a natural benefic
(`nat_ben`). Only a planet malefic by **both** measures blemishes as an occupant. Scoped
to occupants (the evidenced site); aspects unchanged.

- **Held-out effect (Ch VII):** ch72 bhāva **−4 → −1** (within-one) and ch74 bhāva
  **−2 → 0** (exact). Ch VII within-one **39% → 50%**; bhāva per-factor within-one 3/7 → 5/7.
- **Zero tuned/anchor cost:** the token audit is blind to natural-vs-functional nature
  (corpus occupant tokens carry only a `benefic` flag), so tuned stays **79%** and the
  live-engine anchor is **byte-stable** — the tuned "weak" bhāvas are all blemished by
  *natural* malefics (`nat_ben` False), untouched. 237 doctrine tests pass; guarded by
  `TestNaturalBeneficBhavaOccupant` (credit for a natural-benefic functional malefic;
  penalty preserved for a natural malefic).
- **Still open (A.2 / B):** ch73 bhāva (−4) is the *neechabhanga-rescued aspect*
  under-credit (a different mechanism); and the kendra-offsets-affliction lord/kāraka
  over-credit (B, held-out ch64/70/71/72/73), the next candidate.

### Increment 7 — natural-benefic influence on a bhava: aspect + kartari (held-out-driven, DONE)

Phase A.2 of 2.6 — the aspect and hemming analogs of A.1. A.1 fixed the *occupant*; the
same principle (a **natural benefic influences a bhava benignly regardless of functional
lordship**) was still missing for aspects and papakartari/subhakartari. Two shared helpers
now carry it: `_natural_benefic` (paksha-based for the Moon) and `_bhava_benefic`
(= functionally benefic **or** naturally benefic), reused by the occupant (A.1), the
bhava-aspect branch of `_aspect_findings` (`dignity_aware`), and `_kartari`
(`natural_benefic_ok`, set only by the main `_assess_bhava` calls). Planet-facing aspects
and the reference/from-Moon bhava keep functional nature (unchanged).

- **Held-out effect (two fixes):**
  - **ch73 bhāva −4 → −3** — the 4th's Mercury aspect (natural benefic, 6th lord) flips
    −0.35 → +0.35 (Raman credits its neechabhanga). A partial lift — Raman's "fairly
    powerful" for a twice-aspected empty house out-reaches the additive model.
  - **ch70 bhāva −2 → 0 (exact)** — the "clean/empty under-score" was really a
    **false papakartari**: the 4th is hemmed by Mercury (natural benefic, 5th) on one side
    and Mars+Ketu on the other, so it is *not* papa (Raman: "moderately strong"). A.2
    suppresses the spurious −1.0.
- **Held-out Ch VII within-one 50% → 56%; bhāva mean Δ −1.25 → −0.43.**
- **Zero tuned/anchor cost:** the token audit stays **79%** (blind to natural-vs-functional
  nature), the live anchor byte-stable; natural malefics and node hemmers are unaffected
  (`_bhava_benefic` False). 241 tests pass; guarded by `TestNaturalBeneficBhavaOccupant`
  (aspect credited; false papakartari suppressed vs. functional papa).
- **Not closed:** ch73 (held-out) stays −3 (generous grading — Raman's "fairly powerful"
  for a twice-aspected empty house out-reaches the additive model). (The tuned ch94 also
  stays −4, its subhakartari blocked by Ketu in the 8th, but that is not a held-out miss.)
- **Next: B** — the kendra-offsets-affliction lord/kāraka over-credit (held-out
  ch64/70/71/72/73), the positive-saturation frontier, still open.

### Increment 8 — the lord/kāraka over-credit (B): NOT closable on current features (documented negative result)

B is the target Phase B's optimizer flagged (it lowered `pos_knee`/`kendra_trikona`) and the
one the held-out set most consistently misses: a kendra/dignity placement offsets stacked
malefic testimony where Raman grades the planet **afflicted** (held-out ch64/70/71/72/73,
Δ +2/+3). Two routes were tested against the anchor-as-hard-constraint and **both fail**:

1. **Blanket `pos_knee` / `kendra_trikona` reduction (the Phase-B direction, in isolation).**
   A sweep of `pos_knee ∈ {1.6..1.2} × kendra_trikona ∈ {1.2..0.8}` raised the scored set
   but **dropped the ch. IV anchor 8/8 → 5/8** the moment `pos_knee < 1.6`, and
   pulls the tuned audit to ≤77%. The anchor charts are legitimately strong *without* heavy
   malefic siege, so saturating their positives earlier mis-grades them. Phase B kept the
   anchor at 100% only by co-moving ~20 other params; the two knobs in isolation cannot.

2. **A targeted "malefic-siege" penalty (≥2 malefic aspects/conjunctions on the planet).**
   This does *not* separate the classes: the anchor's **ch14 kāraka (Sun)** has siege
   rasi = **2** and Raman grades it **moderate**; the held-out **ch70/ch72 kāraka (Moon)**
   have siege rasi = **2** and Raman grades them **afflicted**. Same feature value, opposite
   labels — and ch14's siege is *conjunctions* (stronger) vs ch70's *aspects*, yet graded
   higher. No threshold on siege / kendra / dignity separates the over-credited held-out
   kārakas from the correctly-graded anchor kārakas.

**Conclusion:** the over-credit is **not linearly/threshold separable on the features the
sign-reconstructed engine has**. Closing it needs information the additive point-scheme (and
the sign-only reconstruction) does not carry — degree-based aspect strength, the dispositor's
condition, or Raman's holistic benefic-vs-malefic weighing — not a re-weighting. This is the
expressiveness ceiling: Phase B plateaued at 58% for the same reason. **No engine change made**
(an anchor-breaking or non-separating change would be worse than the honest ceiling).

- **Options for a future pass (not done here):** (a) accept the additive ceiling (~50–56%
  held-out); (b) reconstruct with *degrees* (from birth data, not sign diagrams) to expose
  aspect-strength/dispositor features, then re-fit; (c) grow the held-out kāraka set further
  to search for a finer separating feature. Each is a distinct project.

### Increment 9 — Ashtakavarga bindu strength (DOCUMENTED NEGATIVE, no accuracy change)

Motivated by the "new terms, not re-weighting" conclusion above and the survey finding that
Raman's **own numeric strength tool, ashtakavarga**, was fully implemented
(`app/core/ashtakavarga.py`, sign-computable) but never read by the numeric strength scorer
(only by the DSL rule-predicate path). Wired two features into the live scorer: a bhāva's
**Sarvashtakavarga** total (`_sav_finding` in `_assess_bhava`) and a planet's own
**Bhinnashtakavarga** in its sign (`_bav_finding` in `_assess_planet`), each scored per bindu
above the chart's own average, sharing the exact `compute_ashtakavarga` call the rule path
uses.

**Result — it does not improve held-out agreement with Raman's strength verdicts.** Sweeping
the two weights against the 24/51 (47.1%) held-out baseline (all 168 charts / 51 scoreable
rows):

| feature | weight swept | held-out within-one |
|---|---|---|
| SAV (bhāva) | 0.02 → 0.14 | **strictly falls** 24 → 23 → 22 (bhāva 9 → 7) |
| BAV (planet) | 0.05, 0.10 | **neutral** (24) |

**Why:** the engine already over-scores on held-out — every factor's mean Δ is *positive*
(bhāva +0.56, lord +0.76, kāraka +1.19). Ashtakavarga is a *positive fortification* term, so
adding it additively deepens the over-credit rather than correcting it. Raman's own SAV/BAV,
added linearly, does not encode what his *strength verdicts* encode — corroborating increment
8's conclusion that the residual gap is **structural (holistic weighing / the over-credit),
not a missing linear feature**. A re-fit cannot rescue it: `fit_weights` sign-constrains a
fortification weight to ≥0, and positive AV hurts-or-neutral, so the optimizer converges the
AV weight to 0.

**Disposition:** kept **wired but dormant** (`_W["av_bindu"]=_W["bav_bindu"]=0.0`) — the bindu
count is measured and shown in the findings for display, and the machinery (cross-checked
against the rule path, guarded by `TestAshtakavargaFeature`) is available for a degree-era or
longevity-scoped use where it may weigh differently. Engine behaviour is byte-identical to the
pre-increment baseline (held-out 24/51, anchor 8/8). Measurement + dormant wiring only.

### Increment 11 — a lord at home in its own dusthāna is redeemed (fresh-held-out-driven, DONE)

The Tier-2 **blind** corpus (`unseen_scoreable.json`, charts the engine was never tuned on)
surfaced a concrete, recurring structural miss: **ch35** — the 8th lord Moon occupies its own
sign Cancer *in the 8th house* with exalted Jupiter; Raman grades it **"full and very
powerful"**, the engine graded it **weak** (Δ−7). The scorer applied a flat `dusthana = −1.0`
placement penalty (`_assess_planet`, `:862`) **and** the Phase-2.4 `dusthana_lord = −1.0`
functional-malefic penalty, so own-sign strength (+1.2) and the exalted-Jupiter conjunction
(+1.6) were dragged under by −2.0.

**Rule:** a lord occupying **the very house it rules**, in its own sign, is "at home" — the
dusthāna does not afflict it. Both the placement and the dusthāna-lordship penalties are
cancelled; the own-sign dignity finding stands. Scoped to `h == own_house` (`_assess_lord`
passes the judged house) so it fires only for a lord *in its own house*, not a lord merely
displaced into a coincidental dusthāna.

**The scope is load-bearing — it is what makes this a clean, not a regressing, change.** A
first, blanket "own-sign redeems any dusthāna" cut the held-out within-one **52.8 → 49.1%**
because it wrongly redeemed **ch103** (the 5th lord Saturn sits in the *6th* in own sign, yet
Raman still calls it **"afflicted"** — its affliction is aspect-driven, and it is *displaced*,
not at home). Restricting to `h == own_house` protects ch103 (h6 ≠ judged-5) while keeping the
ch35 gain.

**Result:** held-out within-one **52.8% (unchanged, no regression)**; anchor **byte-stable
8/8**; tuned floor + `fit_weights` self-check green (269 doctrine tests pass). On the fresh
blind set ch35's 8th lord moves **weak (−0.91) → fairly strong (+1.09)**, shrinking its miss
from Δ−7 to Δ−3 and lifting the fresh mean Δ **−0.50 → −0.21**. The coarse within-one metric
does not flip (Δ−3 is still a "miss"), but the engine is measurably more faithful to Raman on
the dusthāna-own-sign class at **zero cost** to every gate. Guarded by
`test_lord_at_home_in_own_dusthana_is_redeemed`.

### Increment 12 — neechabhāṅga-in-kendra strength: INERT under the positive cap (documented negative)

**Hypothesis (fresh-blind ch52):** the debilitated 8th lord Sun sits in the 10th (a kendra)
with its debility *cancelled* (neechabhāṅga); classically this is a **Neecha-Bhaṅga Rāja
Yoga**, a strength — Raman grades it **"fairly strong"**, the engine **"afflicted"** (Δ−5).
The engine already cancels the debility (+0.2 instead of −1.6) but does not upgrade the
cancellation to a yoga. A candidate weight `neechabhanga_kendra = 1.2` was added (fires only
when cancellation *is* detected AND the planet is in a kendra — so ch87's **raw** debilitation,
no cancellation, is untouched and stays correctly "afflicted").

**Result: no measurable effect.** ch52's 8th lord moved only −1.26 → −1.16 (still "weak"),
because its Rāśi positive stack is **already saturated by `_cap_positive`** (kendra +1.2 +
vargottama +1.2 sit past the `_POS_KNEE = 1.6` knee), so the extra +1.0 of raja-yoga credit is
absorbed. Held-out within-one unchanged (52.8%), fresh within-one unchanged (71.4%).

**Diagnosis:** ch52's low grade is driven by its **uncapped negative load** — malefic aspects
(Jupiter-as-functional-malefic, Ketu, Mars) plus the functional-malefic lordship penalty — not
by a missing dignity term. This is the **same holistic-weighing ceiling as increment 8**: once
the positive side is capped, only reducing the negatives moves the grade, and re-weighting the
negatives risks the held-out (the debilitation itself is *already* handled correctly). The
neechabhāṅga-in-kendra rule is faithful doctrine but cannot close the ch52 class on the current
(capped, additive) scorer. **Reverted** — no weight added; engine byte-identical to increment
11. Recorded as a negative, alongside increments 8 (kāraka over-credit) and 9 (ashtakavarga).

### Increment 13 — true-degree affliction (combustion + conjunction-orb): reduces but does NOT separate the over-credit (documented negative)

**Hypothesis (from the NH degree-accurate held-out).** The fresh *Notable Horoscopes* strength
test — charts reconstructed from Raman's **printed degrees**, the doctrine engine never tuned on
them — exposed a clean, systematic **+1.13-grade over-credit** on afflicted factors
(`REPORT_nh_strength.md`). The over-credit is proven non-separable on **sign-only** features
(increments 8, 12; Phase D.0; Phase-2 recalibration breaks the anchor). NH supplies the one thing
never tried against it: **true degrees**. Two degree-only terms were built and measured —
**combustion** (`planet_state.is_combust`, a phenomenon the sign engine is entirely blind to) and
a **malefic-conjunction orb multiplier** (tight orb → harder affliction). Both fire only when
degree resolution is present, so the stored-findings paths (anchor, tuned floor, `fit_weights`
self-check) are **byte-stable by construction** and stayed green throughout.

**Result — degrees carry *some* signal, but not enough, and the weight can't be calibrated.**
- **Combustion is directionally correct.** NH Buddha's 7th lord Saturn *is* combust and Raman
  calls it "afflicted"; the term moved it one grade the right way (Δ+4 → +3) and pulled the
  over-credit **mean** toward Raman on both held-out sets (NH +1.13 → +1.00; HTJAH held-out +0.49
  → +0.38) with **zero within-one regression** anywhere and longevity ρ unchanged.
- **But it does not SEPARATE the over-credit.** NH within-one stayed **46.7% at every combustion
  weight tried** (−0.7 … −1.6) — the misses are 2-4 grades off; combustion moves ~1. The
  pre-registered go/no-go ("NH within-one up") is **not met**.
- **The orb multiplier was inert.** NH within-one and mean were unchanged across
  `affliction_orb` 0 → 1.5, because the NH misses are **bhāva**-driven (house occupants/aspects),
  not the assessed lord's conjunctions. Dropped.
- **The weight is uncalibratable without ground truth.** Combustion necessarily changes any
  chart with a combust factor — e.g. Mainpuri's combust lagna-lord Mars drops fairly-good → weak
  at −1.6 — and there is no Raman verdict to say the new grade is better. Chasing the NH **mean**
  by a weight that shifts already-calibrated verdicts would be overfitting N=15.

**Disposition: reverted; engine byte-identical to increment 11.** Recorded as a negative
alongside increments 8, 9, 12. The definitive finding: a **bolt-on true-degree affliction feature
does not close the over-credit** — the sign-only strength engine is at its structural ceiling, and
further strength gains need the full real-birth degree engine (a separate, larger effort), not a
degree term grafted onto the sign scorer. The measurement stands on its own: **true degrees reduce
the over-credit magnitude but do not separate the grade.**

### Increment 14 — the real-birth degree engine: combustion helps, chalita & degree-dignity do not (DONE + two documented negatives)

Increment 13 concluded that further strength gains "need the full real-birth degree engine, not a
degree term grafted onto the sign scorer." Increment 14 builds that layer properly — a
`degree_resolved`-gated feature module (`degree_features.py`) that supplies bhāva-chalita placement,
degree-graded dignity, and orb-graded combustion to the numeric assessor, wired so every
sign-reconstructed chart (the ch. IV anchor, all HTJAH held-out) is **byte-identical**. It is
measured **blind** on a grown, degree-accurate held-out set (NH 15 → **32** rows; 17 fresh verdicts
extracted from the clean *Notable Horoscopes* text, three-agent + raw-text audited, pre-registered
map grading, nothing fit).

Blind ablation (NH degree pooled, N=32):

| config | within-one | mean Δ |
|---|---|---|
| sign baseline | 40.6% | +0.75 |
| bhāva-chalita only | **34.4%** | +0.50 |
| degree-dignity + moolatrikona only | 40.6% | +0.75 |
| **combustion only** | **43.8%** | +0.69 |

- **Combustion (DONE, default on).** The only feature that raises within-one (40.6 → **43.8%**),
  moving combust factors Raman grades afflicted the right way (Tippu's 8th Āyushkāraka Saturn
  Δ+2 → +1; Buddha's 7th lord Saturn Δ+4 → +3). Within-one-neutral on the original 15 (46.7 →
  46.7, bias +1.13 → +1.07) — consistent with increment 13 — so the gain surfaces only on a corpus
  broad enough to contain such factors.
- **Bhāva-chalita (documented negative, default off).** *Hurts* (40.6 → 34.4%): Raman grades
  strength by **whole-sign rāśi**, not Sripati cusps, so re-classing planets to their chalita bhāva
  moves them off the houses he judges. The dusthāna under-score is not a cusp artifact.
- **Degree-dignity + moolatrikona (documented negative, default off).** Inert: within a sign the
  Uccha depth spans ~0.83–1.0 and never crosses a grade boundary.

**Disposition: combustion kept (on); chalita + degree-dignity retained as default-off, reproducible
ablation levers.** The decisive lesson is now doctrinally grounded: the two levers that *should*
have rescued the ceiling — cusp-accurate placement and degree-accurate dignity — are exactly the
two that fail, because Raman's own method is whole-sign and sign-dignity based. Degree resolution
yields a real but modest combustion gain and confirms the ~53% sign ceiling is structural. Full
report: `validation/REPORT_degree_engine.md`.

### Increment 15 — learned combine (A2): synthesis hypothesis CONFIRMED as measurement; landing gate-blocked

The ML_RESEARCH track-A test of the ceiling's diagnosis. Keeping feature extraction
byte-identical and replacing only `_combine`/`_THRESH` with small interpretable models
(ordinal logistic; depth-3 tree) over (delta, frame) finding tokens: LOCO-CV over the 7
held-out chapters **63.5% within-one vs the live engine's 51.9% on identical rows** (N=52);
NH degree pool single-shot **62.5% vs 46.9%** (N=32, in no training fold). The tree's root
split is the hypothesized gate made visible: `sum_neg_rasi ≤ −1.22 → afflicted` regardless
of positional credits. The residual above the ceiling IS learnable — it is Raman's
non-linear weighing, not noise (a blinded frontier-LLM scorer on the same rows managed only
47.1% with zero real-vs-perturbed-twin gap, so generic astrological expertise does not
substitute for fitting HIS weighing).

**Disposition: NOT landed.** The pre-registered ch. IV anchor gate failed (ordinal 2/8,
tree 1/8) — confounded with representation shift (the anchor exists only in the audit's
typed-finding vocabulary), but the gate is the gate. Landing path: grid-extract the ch. IV
anchor charts, re-run the gate in engine representation, land only on 9/9. Engine
byte-identical to increment 14. Full data: `validation/ml_research/`; report:
`ML_RESEARCH.md`.

### Increment 15b — A2′ landing attempt: the frozen anchor has drifted from the live engine

Attempting to land the learned combine (increment 15) required evaluating the pre-registered
ch. IV anchor gate in engine representation. Investigation found the gate cannot validly gate a
live-engine model:

- The frozen anchor (`htjah_anchor_calibration.json`) is 8 hand-decoded typed-finding rows in a
  retired weight vocabulary (e.g. a `1.0` kendra delta the engine long ago moved to `1.2`), 1–3
  findings per row vs the engine's dense output.
- Casting the three anchor charts (HTJAH Nos. 12–14) from their real birth data in Raman's
  ayanamsa produces FAITHFUL charts — Chart 12's rāśi and navāṁśa match Raman's prose exactly
  (Saturn 8th-Leo; Saturn navāṁśa Taurus "with Jupiter in Venus's sign"; Sun vargottama) — yet the
  **live engine grades its own calibration anchor at 2/8 within-one**, under-crediting by 3–5
  grades (Chart 12 lord: engine "weak" vs Raman "fairly good"). `test_audit_anchor` reads 8/8 only
  because it runs the frozen findings through `validate_house.predict`, not `judge_house_doctrine`.

- **Decisive test:** scoring the anchor in engine representation on the faithful casts, **vs
  Raman**, the live engine is 2/8 and the learned combine is **0/8 -- it collapses to "afflicted"
  on every house-1 row**. The learned model's LOCO folds are dusthana-heavy held-out chapters; it
  overfits "dense negatives -> afflicted" and fails out-of-distribution on strong lagnas. The
  pre-registered gate did its job.

**Disposition:** the learned combine (increment 15) is a validated *in-distribution* measurement
(63.5% LOCO), NOT landed -- it does not generalize to house 1, and the gate correctly rejects it.
Two separate true findings: the frozen anchor test has drifted from the live engine (8/8 stale vs
2/8 live), AND the learned model is worse than the engine outside its training distribution.
Landing needs house-1 training rows + a grid-backed anchor re-baselined through the live engine.
Data: `validation/ml_research/a2prime_anchor_diagnostic.json`; full discussion in `ML_RESEARCH.md`.
Engine byte-identical (measurement only).

### Increment 16 — LIVE ch. IV anchor rebuilt (P0 of the engine overhaul); Chart 14 birth data repaired

The overhaul's measurement foundation. The frozen anchor gates only the old harness
(increment 15b); this increment builds the authoritative live-engine anchor:

- **Builder** `audit/builders/build_anchor_live_corpus.py`: Charts 12–14 cast from printed
  birth data in Raman's ayanamsa, HARD-GATED against 25 mechanical facts stated in his own
  ch. IV walkthrough prose (per-planet rasi/navamsa signs, houses, vargottama, hemming
  occupants). All three charts pass.
- **Chart 14 repair**: the printed "7-8-1878" cannot be right — no 1878 date puts Saturn+Rahu
  in Cancer as Raman states. A constrained ephemeris search over ALL his stated facts
  (Sun+Mercury+Saturn+Rahu in Cancer, Mars in Gemini, Scorpio lagna vargottama, Mars navamsa
  Taurus, Sun ≈18° from Saturn) uniquely selects **7-8-1887** — an OCR digit transposition
  (87↔78). Sun–Saturn casts to 15.9°.
- **The honest number: the live engine scores Raman's own calibration examples 1/8 within-one
  (mean Δ −3.75), every miss an UNDER-credit** — worse than 15b's 2/8 because the corrected
  Chart 14 exposes the bhāva confound: Raman counts Mars "in the 9th house (8th Rashi)" while
  whole-sign reads Gemini as the 8th from Scorpio → dusthāna penalties on a lord he grades
  "very strong" (Δ−7). The vargottama-lagna structural override still matches (very powerful ✓).
- **Guards**: `anchor_live_validate.py` (re-checks every expected sign at load — varga-math
  drift trips it) + `tests/doctrine/test_anchor_live.py` (RATCHET floor 1/8 + a per-row grade
  LEDGER any intentional change must update in the same commit). `test_audit_anchor.py`
  re-scoped to the harness representation it actually gates.

Measurement only; engine byte-identical. Every subsequent increment (17+: sutra strength,
rebalance) is dual-gated on THIS anchor plus the held-out corpora.

### Increment 17 — sutra-fed strength: the encoded doctrine finally feeds the grades (LANDED; largest single gain)

Root cause 1 (increment 16 context): all 1,359 encoded sutras fired into an unscored path.
This increment routes them into the factor verdicts under three disciplines
(`domains/sutra_strength.py`): NOVELTY (rules restating what the assessors already score
mechanically are dropped; only lord-of-X-in-Y, yogas/compounds, varga/AV/nakshatra/nodal
testimony contributes), DOCTRINE-FIXED WEIGHTS (polarity × the rule's own printed magnitude
class, valued in the assessor's units — nothing fit), and BOUNDED CONTRIBUTION (per-factor
±1.6 clamp, positives saturate through the existing `_cap_positive`). Corrective
planet-in-house sutras that CONTRADICT the mechanical occupant sign flip it (17b). The
strong-affliction gate (17c) is wired but dormant — no row trips it on any corpus.

Ladder (all gates green; OFF-path byte-identical, full suite):

| corpus | before | after |
|---|---|---|
| pooled held-out (N=53) | 52.8% | **54.7%** (Δ +0.49 → +0.32) |
| max HTJAH expansion (N=76) | 53.9% | **55.3%** |
| fresh blind (N=14) | 71.4% | 71.4% (unchanged) |
| NH degree-accurate (N=15) | 46.7% | **53.3%** |
| NH degree pooled (N=32) | 43.8% | **53.1%** (Δ +0.69 → +0.44) |
| live anchor | 1/8 | 1/8 (intra-band shuffles only; 13-bhava −5→−3, 12-lord −3→−4 — ch. IV
lord-in-dusthana sutras fire unfavorably, testimony Raman himself overrides: P3's case) |
| longevity ρ | +0.52 | +0.50 |

The house-1 chapter (ch. IV) participates only on the sutra path (`_HOUSE_CHAPTERS_SUTRA`)
so the default path stays byte-identical with flags off. The largest single accuracy gain in
the project's history, and it came from CONTENT, not weights — fourteen weight/feature
increments could not move what routing the doctrine's own rules did.

### Increment 18 — P3 rebalance, round 1: one landed, two doctrinally-real trades rejected

Mechanisms proposed from the live-anchor findings dump (each dual-gated on live anchor AND
pooled held-out AND NH pooled):

- **M-A, neechabhāṅga kendra-from-the-Moon (REJECTED — documented negative).** The textbook
  second leg, asserted by Raman twice in ch. IV (Chart 13's neecha Sun and Venus: "Raja-Yoga
  is caused"). Lifts the live anchor 1/8 → 2/8 (all three Chart-13 rows improve) but regresses
  NH pooled 53.1 → 50.0: Marie Antoinette's 5th-bhāva occupant gains a cancellation Raman does
  not grant. A trade, not a gain; any narrowing that keeps Chart 13 and excludes her would be
  corpus-fitting. Recorded in `_neechabhanga`'s docstring for revisit as the anchor corpus grows.
- **M-B, navāṁśa associations read by natural nature (REJECTED — documented negative).** Raman,
  Chart 12: functional-malefic Jupiter with Saturn "in the sign of a friend. Hence ... fairly
  good." Same trade shape: anchor 1/8 → 2/8, NH 53.1 → 50.0. The `natural_benefic_ok` lever on
  `_conjunction_findings` is retained for reproducibility; nav calls stay functional-natured.
- **M-C, vargottama dignity counted once (LANDED).** A vargottama planet was charged the same
  sign's dignity in BOTH frames (Chart 12's neecha-sign Sun: −1.6 twice) while also credited
  vargottama — Raman weighs the enemy sign once ("vargottama but in an enemy's sign →
  inclining towards good"). Fix: skip the navāṁśa dignity finding when sign1 == sign9. Effect:
  anchor mean Δ −3.75 → −3.62 (Chart 12 kāraka afflicted → weak), held-out 54.7% and NH 53.1%
  byte-unchanged. Zero-cost doctrinal correctness.

The recurring pattern is itself a finding: every mechanism that lifts the anchor's strong-lagna
under-credit spends the same rows' worth of NH over-credit — the two corpora sit on opposite
sides of the engine's calibration, and per-mechanism fixes inherit the recalibration report's
global trade unless (like M-C) they correct an outright double-count. The lever that breaks the
trade is CONTENT (increment 17), not weights; further anchor recovery likely needs the P2
encoding completion (more, finer rules) rather than more weight surgery.

### Increment 19 — P2 encoding completion: HPA finished (599 → 1,153 rules), compendium at 1,913

The engine-overhaul diagnosis named incomplete coverage as one of the three root causes: HPA had
~20 of 36 chapters un-swept, **including ch. XVI "Judgment of a Horoscope"** — the one chapter most
directly about strength synthesis. This increment closes that gap. The user supplied the full HPA
text; its `<pre>` body verified **byte-identical** to the pinned OCR (sha256 `4af231cc…`), so the
sweep ran against the canonical text with no provenance caveat and the 599 existing rules were
untouched.

Encoded in seven checkpointed batches (commit → tri-gate → suite → push per batch), each rule a
verbatim-quoted, gate-verified span — **never cherry-picked for accuracy**:

| batch | chapters | rules | notes |
|---|---|---:|---|
| 19a | XVI Judgment of a Horoscope | 46 | the highest strength-value chapter |
| 19b | XII Birth Verification, XIII Dasas & Bhukthies | 18 | |
| 19c | IX Hindu Casting, X Western Casting | 45 | method/definition only |
| 19d | I, II, IV, V, VI, VII | 156 | VII Planetary Strengths & Avasthas carries DSL antecedents |
| 19e | XXVII Prasna, XXVIII Unknown Birth Times, XXXI Mundane | 95 | 20 executable prasna/horary rules |
| 19f | XXXV Practical Horoscopes, XXXVI Drekkanas & Stellar | 78 | 36 drekkana + 27 nakshatra definitions |
| 19g | XXXII Muhurtha, XXXIII Annual/Varshaphal | 116 | electional + varshaphal |

**Grade impact: essentially nil, by policy.** Only rule_types {bhava_judgment, yoga, graha_effect}
are admitted to the sutra-fed strength path (ADMITTED_RULE_TYPES, increment 17). HPA's remaining
chapters are overwhelmingly method / definition / electional / prasna / dasha_timing / transit —
outside that whitelist — so the scored path stayed byte-stable across all seven merges: live anchor
1/8 (mean Δ −3.62), pooled held-out 54.7%, NH pooled 53.1% (Δ +0.41), full doctrine suite 299
passed at every checkpoint. The one measurable move was 19a: a few admitted ch. XVI rules shaved
the NH over-credit (mean Δ +0.44 → +0.41, exact 25.0 → 28.1%) with zero within-one movement —
drift-guard + summary re-pinned in that commit.

**Two runtime bugs the compile-only sweep gate could not catch** surfaced in batch 19g against the
whole-compendium evaluation test (which *evaluates* every rule against the printed-chart smoke set,
not just compiles it): 6 antecedents named the node `Kethu` (→ `Ketu`, KeyError at eval) and 7
`lagna_sign_is` antecedents passed a sign *list* where the op takes a single sign (→ wrapped each in
an `any()` of single-sign checks, TypeError at eval). Both fixed in the draft before the final merge;
the evaluation test is now part of the per-batch gate.

Coverage: all 36 HPA chapters swept except **XVII "Key-Planets for Each Sign"**, which stays
"partial" honestly — it carries one key-planet rule per sign (12/12 signs), so its per-sign doctrine
is complete but the chapter's prose remarks are not separately encoded. `three_hundred` remains
truncated at yoga 162 (no retrievable source, unchanged). Compendium now **1,913 rules across 10
books**; COMPENDIUM_STATUS / COVERAGE / SOURCES updated to match.

### Increment 20 — widening the admitted rule-types is inert (documented negative)

Increment 19 finished HPA encoding but left the grades unmoved *by policy*: only
`ADMITTED_RULE_TYPES = {bhava_judgment, yoga, graha_effect}` feed the sutra-strength scorer
(`sutra_strength.py`). The natural next question — does admitting the newly-abundant rule-types
(`functional_role`, `cancellation`, `strength`, `transit`, `dasha_timing`, …) into the scorer break
the ceiling? — was measured directly and answered **no**.

A diagnostic that admitted **every** rule-type and instrumented the live judge across the anchor +
pooled held-out + NH corpora counted how many fired rules would contribute *novel, factor-targeted*
testimony under each type. Result:

| rule_type | novel+targeted contributions | distinct rules | status |
|---|---:|---:|---|
| bhava_judgment | 133 | 51 | already admitted |
| graha_effect | 90 | 22 | already admitted |
| yoga | 33 | 5 | already admitted |
| **cancellation** | **3** | **1** | the only excluded type with *any* signal |
| functional_role / strength / transit / dasha_timing / electional / prasna / definition / method | **0** | 0 | contribute nothing |

The excluded types are inert not because of the gate but because of the **two disciplines upstream
of it**: the novelty filter drops rules whose antecedents restate what the mechanical assessor
already scores (e.g. `strength`/avastha rules built from `exalted`/`own_sign`/`combust` —
REDUNDANT_OPS), and `target_factor` drops rules that don't tie an atom to the judged house. The
rule-type gate is therefore **not** the bottleneck.

The one live candidate, **`+cancellation`, was run through the full tri-gate and is byte-identical to
baseline** (anchor 1/8, held-out 54.7% / Δ +0.17, NH 53.1% / Δ +0.41): its 3 contributions from a
single rule never cross a grade boundary. Engine untouched; recorded as a documented negative.

**What this establishes:** encoding more doctrine (increment 19) and admitting more of it into scoring
(this increment) are both spent levers — the strength engine's ~53–55% within-one ceiling and the
1/8 live anchor are held by the *holistic-weighing* residual (increments 8, 12, 13, 18's rejected
trades), not by coverage or by the rule-type whitelist. The remaining lever for the anchor's
strong-lagna under-credit is weight surgery, which the increment-18 trades showed spends NH
over-credit for every point of anchor gain. The honest position: the sign-only strength engine is at
its structural ceiling.

### Increment 22 — natal-scope firing filter: no horary / electional / past-life rule fires on a birth chart

A domain-expert review of the Mainpuri reading (increment 21's firing surface) caught a real category
error: rules from *Prasna Marga* (horary) and HPA's Muhurtha (electional) chapters were firing in the
**natal** judgment because their antecedents happen to be true of the birth chart. Verified on Mainpuri:
the 2nd-house reading fired *"Benefics in 3, 5, 7 and 11 of the Prasna chart: success in speculation"*
and the 4th fired *"When the Prasna Lagna falls in a fixed sign … the article was stolen by a near
relative"* — horary query rules with no natal meaning — plus two after-death "loka" **definition**
records. The pre-existing domain-candidate path surfaced 7 such rules; increment 21's chart-global pass
was already clean, but the per-house path was not.

**The fix.** In `judge_house_doctrine`'s fired loop, a rule is dropped unless it is
`natal_scope.in_natal_scope(...)` OR its rule_type is a genuine natal-timing type
(`dasha_timing` / `transit`, which the timing sub-verdict legitimately consumes). This catches the
subtle case the first cut missed: Muhurtha rules carry an election `timing` and so classify into the
`"timing"` bucket, so a bucket-based exemption would have let them through — the type-based exemption
does not. Result on Mainpuri: **out-of-scope firings 7 → 0**; the daśā/transit timing sub-verdict is
untouched.

**Grade-safe by construction.** The excluded types (electional/prasna/definition/method) are not in
`ADMITTED_RULE_TYPES` and were never scored, so every verdict is byte-identical (live anchor 1/8,
held-out 54.7%, NH 53.1% — all drift-guard pins hold; full suite 304 passed). This is pure reading
correctness. Pinned by `test_mainpuri_firing_audit.test_no_out_of_scope_rule_fires_on_natal_chart`.

**Still open (honest, from the same review).** Two further critiques are correct and *not* yet fixed:
(1) **Kemadruma has no bhaṅga** — only the raw yoga is encoded; the cancellation when a kendra from
lagna/Moon is occupied (Venus in the 1st, here) is not modelled, so the engine over-states it.
(2) **Balariṣṭa (infant-mortality) rules scatter across adult house readings** (9 houses on Mainpuri)
because they route by the dusthāna houses their antecedents name; they belong to the longevity context.
Both are encoding/routing refinements, scoped as follow-ups. The **House-11 "weak" verdict** the review
flags (exalted 11th-lord + rājayoga read down by the navāṁśa-debilitation) is not a bug but the
documented **synthesis ceiling** (increments 8/12/13/18) — the engine layers testimony where Raman
weighs it holistically.

### Increment 23 — Kemadruma-bhaṅga: a cancelled yoga no longer surfaces

The first of the two review follow-ups, now landed. Raman (HTJAH / *300 Combinations*): Kemadruma
"ceases to exist" when a planet other than the Sun/Moon occupies a kendra (1/4/7/10) from the Lagna or
the Moon (or the Moon is conjoined/aspected by a benefic). The raw yoga encodes only its *definition*
(no planet in the 2nd/12th from the Moon), so the engine printed the full "misery and poverty" text on
charts where the cancellation clearly holds. On Mainpuri, **Venus in the 1st is a kendra from both the
Lagna and the Moon → the bhaṅga holds**, yet both Kemadruma records (`hpa.xx.kemadruma`,
`three_hundred.y005.kemadruma`) were firing.

**Fix.** `_kemadruma_cancelled(chart)` tests the kendra-occupancy leg; `_is_cancelled_yoga(rule, chart)`
gates it in both firing paths (per-house loop and the chart-global pass). A cancelled yoga is dropped
before it surfaces. **Grade-safe:** the drift-guard confirms every held-out / NH / anchor number is
byte-identical (the `y005` yoga is scoring-admitted, but suppressing it moved no grade on any corpus;
full suite green). Reading-only correctness, pinned by
`test_mainpuri_firing_audit.test_kemadruma_bhanga_suppresses_the_yoga` and honoured as a legitimate
non-firing exception in the coverage test. Still open from the review: the Balariṣṭa (infant-mortality)
rules that scatter across adult house readings (a longevity-context routing refinement) and the
House-11 synthesis ceiling (structural, not a bug).

### Increment 21 — fire every applicable natal sutra (firing-coverage, grade-safe by construction)

A Mainpuri-chart diagnostic exposed a firing-coverage gap distinct from the scoring question: the
judge only makes a rule a candidate if its `domain` equals the house's single `HOUSE_DOMAIN` mapping
(or it lives in that house's HTJAH chapter). But `HOUSE_DOMAIN` maps 12 houses to 12 of the
compendium's 18 domains — the orphan domains **`general` (713 rules)** and **`mind_character` (159)**
map to NO house, so every rule tagged with them (present yogas, avasthas/balas, functional-role,
planet-in-sign character) could never fire. On Mainpuri, of **137** applicable (antecedent-true)
sutras, only **~87** natal-relevant ones surfaced; **all 114 natal-scope applicable rules should
fire, and ~27 never did.**

**The fix (`NATAL_FIRING_WIDEN`, default ON).** A new pure module `natal_scope.py` supplies the
doctrinal scope filter (`IN_SCOPE_RULE_TYPES` = bhava_judgment/yoga/graha_effect/strength/
functional_role/cancellation; the rest carry `OUT_OF_SCOPE_REASONS`) and house routing
(`referenced_houses`, skipping `frame:moon` atoms so Moon-frame yogas aren't mis-filed to a Rasi
house). `judge_house_doctrine` adds, as candidates, every in-scope rule that references the judged
house — from **any** book/domain — and a new `judge_chart_doctrine` fires the chart-global rules
(no house anchor: yogas, balas, planet-in-sign) **once**, deduped and disjoint from the house
verdicts. Result on Mainpuri: surfaced rules **101 → 135**, and **114/114 natal-scope applicable
sutras now fire**; the ~23 out-of-scope applicable rules (electional/prasna/dasha_timing/transit/
definition — meaningless for a birth) stay excluded by design.

**Grade-safe by construction — the key discipline.** Feeding the newly-fired rules into the numeric
grade was measured and **regresses every axis** (anchor Δ −3.62→−4.00, held-out 54.7→52.8%
Δ+0.17→+0.51, NH 53.1→50.0% Δ+0.41→+0.66) — the same over-credit lesson as increments 12/13/20. So
the widened candidates surface for **reading only**: only the original domain+chapter `scoring_ids`
reach `sutra_fired`, and the numeric verdicts stay **byte-identical** to the pre-increment path
(live anchor 1/8 Δ −3.62, held-out 54.7% Δ +0.17, NH 53.1% Δ +0.41 — all pins unchanged; full
doctrine suite green). The firing coverage (what the encoded doctrine engages for the interpreter)
and the scoring policy (what moves the verdict) are cleanly separated: the doctrine now *fires*
completely, while the grade stays under the audited increment-17 path. Pinned by
`tests/doctrine/test_mainpuri_firing_audit.py` (coverage, exclusion-by-design, once-firing).

### Increment 24 — synthesis_v2: a doctrine-derived non-linear scorer breaks the strength ceiling

The whole audit trail (increments 8/12/13/18/20, then the A2 ML experiment) converged on one
diagnosis: the ~53–55% within-one ceiling is held by the engine's **additive-linear** synthesis, not
by coverage or weights. Raman judges *conditionally* — a besieged planet is broken regardless of
credit; stacked affliction halts the house like a broken gear. A2 proved a fitted non-linear combine
beats the engine in-distribution (63.5% vs 51.9% LOCO) but **collapsed the ch. IV anchor to 0/8** and
was unlandable.

**synthesis_v2** (`app/medini/doctrine/domains/synthesis_v2.py`) encodes that non-linearity as
*doctrine*, not a fit, in a **standalone parallel scorer — the live engine is byte-untouched** (zero
drift risk). It takes each factor's engine grade as the base, then applies Raman's structural
overrides: **A** besiegement veto (papakartari → capped "weak"), **B** deep-affliction gate (summed
Rāśi negatives ≤ −2.45 → afflicted, ≤ −1.22 → weak — the two thresholds are the A2 tree's split,
declared as such), and a collinearity guard (combustion counted as the tight-orb case of
Sun-proximity, not a second penalty).

**Result (A+B, `synthesis_v2_validate`):** pooled HTJAH held-out **54.7 → 64.2%**, NH degree pool
**53.1 → 62.5%**, ch. IV anchor **held at parity (1/8)**. This matches the A2 in-distribution gain from
pure doctrine and, unlike the fitted model, does not sacrifice the anchor — the two-axis win no linear
trade reached. The ablation shows the strong-promise floor (P) is inert on sign charts and the dignity
floor (C) lifts the anchor 1→2 only by costing ~17 pts of held-out — a **documented negative** proving
the anchor's residual under-credit is a *feature-space* limit (the strength signal is in
yogas/degrees absent from the sign chart), not a synthesis failure. Full write-up:
`validation/REPORT_synthesis_v2.md`; pinned by `tests/doctrine/test_synthesis_v2.py` (7 gate/guard
units + a three-axis ratchet). synthesis_v2 stays a parallel scorer; promoting it to the live grade
path (with an anchor-ledger re-pin) is a separate, deliberately un-taken decision.

### Increment 25 — degree corpus grow2: the synthesis_v2 lead generalizes; the floors are refuted

The degree pool grew 32 → **50 rows** (18 new rows from 13 fresh nativities; all 27 unmined
degree-usable NH cases swept; 62 candidates → 18 through mechanical triage + a unanimous 3-agent
adversarial audit; verdict map unchanged; extraction frozen before scoring —
`corpora/nh_strength_grow2.json`). Results: (1) **synthesis_v2's lead holds on fully unseen degree
data** — 52.0% vs the live engine's 44.0% on N=50 (+8.0, vs +9.4 on the pinned N=32) — the
generalization the fitted A2 model failed; (2) **the strong-promise floor (P) is now refuted, not
just untested**: on degrees its precondition binds (13/50 factors reach a strong Rāśi grade) and it
COSTS 2 points (52.0 → 50.0) — Raman himself grades some strong-Rāśi factors down; (3) the dignity
floor (C) remains catastrophic (28.0%). A+B stands. Pinned N=32 numbers and all drift guards
byte-untouched. Full detail: `validation/REPORT_synthesis_v2.md`.

### Increment 26 — grow3 + the NH attribution audit: 5 bad gold rows removed, pools re-pinned

The grow3 second-verdict sweep (45 candidates → 11 shipped, `nh_strength_grow3.json`) surfaced a
misattribution in the EXISTING gold: the shipped gandhi H1 row belongs to the anonymous "Example for
Poverty" chart. A full attribution audit of all 50 shipped rows followed (phrase located in the full
text; chapter + Rāśi/Lagna frame checked): **5 bad gold rows removed** — 2 misattributions (gandhi H1,
einstein H9 — both section-bleed artifacts) and 3 frame errors (milton H5, sankara H8, nehru H4 — all
"In the Navamsa…" verdicts shipped as Rāśi-frame gold). Removed rows recorded in
`corpora/nh_strength_removed.json`; 45 rows verified sound. Re-pinned: NH base 15→12 (41.7%), default
pooled 32→**27** (live 51.9%, Δ+0.11 — the bias nearly vanishes on clean gold), full degree pool
N=**56**. synthesis_v2's lead on the corrected default pool WIDENS to **+11.1** (63.0 vs 51.9) and
holds at **+9.0** on the full pool (53.6 vs 44.6) — the removed rows were noise. Full detail:
`validation/REPORT_synthesis_v2.md` § grow3.

### Increment 27 — verdict map v2 + grow4: culled stems recovered, gold pinned per-row

The pre-registered verdict map was extended BLIND (fortified/affliction-freedom/placement/power/
destruction families, assignments from the map's own intensity ladder) and a negation bug fixed
("not well disposed" matched `well disposed` → two shipped rows corrected to weak). Gold is now
pinned per-row (`nh_gold_grade_pins.json` + `test_verdict_map_gold_pins`) so no future map edit can
re-grade shipped gold silently. The 46 map-v1 culls re-triaged: 17 shipped (`nh_strength_grow4.json`)
after the 3-agent audit (nero's Sun refuted 3/3 as daśā-scoped) — full degree pool **56 → 73 rows**,
finally strong-heavy. Decisive finding: **both scorers fail the strong-graded slice almost completely
(2/17)** — the ch. IV anchor's under-credit signature is now measured in held-out gold at scale, and
both pool mean-Δs turn negative. v2's lead holds (+6.9 full pool; +11.1 default) because the gates
keep winning the afflicted side; the strong side is a FEATURE gap (yogas/dispositor chains absent
from the Finding vocabulary), the next feature-side target. Full detail:
`validation/REPORT_synthesis_v2.md` § increment 27.
