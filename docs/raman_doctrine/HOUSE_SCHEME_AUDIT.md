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

- **Corpus:** Charts 40, 41, 43, 44, 45, 46 (14 factor-verdicts).
- **Result:** **10–11 / 14 within one grade** (5 exact). Per factor:
  **Kāraka 4/4 · Bhāva 4/5 · Lord 2/5.** ("strong" phrase mapped
  conservatively → *fairly strong*; the looser reading → *very strong* lifts the
  total to 11/14.)
- **Report artifact:** ch5-scheme-audit (per-chart table + diagnosis).

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

- **Corpus:** Charts 52, 53, 61, 62 (8 factor-verdicts) + 2 rows set aside as
  *un-modeled* (see below). Ch. VI's verdicts are coarser/comparative ("good",
  "well disposed", "not sufficiently strong") than ch. V's graded scale.
- **Result:** **5 / 8 within one grade** (2 exact). Per factor:
  **Bhāva 3/4 · Lord 1/3 · Kāraka 1/1.**
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

## Houses 4–12 — pending

_One held-out audit per house as each is deepened; append the corpus size, the
within-one rate, the per-factor split, and the divergence patterns here._

---

## Consolidation — TODO (after House 12)

Tune the shared weights/thresholds/combine **once**, driven by the accumulated
patterns above, under the hard constraint that **no already-approved house
regresses** (ch. IV 9/9; house-1 verdicts byte-stable). Re-run every house's
held-out audit and record the before/after match rates here.

**Running tally of the dominant signals (houses 2–3):**
- **Lord over-scoring by stacked positives** — confirmed 4× (Chart 43 +5, 61 +6,
  53 +4, 40 +3). The single highest-value fix: a diminishing return / cap so
  "good house + own sign (+ exalted conjunction)" ≈ one strong positive, not two
  or three summed to the ceiling.
- **Empty + unaspected house → "fairly strong"** — confirmed 2× (Charts 43, 52).
  Argues for a small positive baseline on a clean house, reconciled with Chart 12
  ("moderate") — the truth is likely "moderately good", splitting the two.
- **Optimistic combine over-rescues a Rāśi-afflicted planet** — Charts 45, 62.
- **Missing inputs (not weight bugs):** combustion penalty; upagrahas (Mandi/
  Gulika). Candidates for new low-level factors before/alongside the tune.
