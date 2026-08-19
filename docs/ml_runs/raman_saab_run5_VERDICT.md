# raman_saab RUN 5 — Audit-Corrected Encoder, Held-Out Fidelity — VERDICT

**Date**: 2026-07-03
**Modules**: `app/medini/ml/raman_saab/{golden_registry,raman_method_v2,fidelity_v2,calibrate_v2,run5_potency}.py`
**Corpus**: `death_corpus_run3.parquet` — N = 2,091 timed (Rodden AA/A) charts with own-death dates (same corpus + sha as runs 3–4)
**Pre-registration**: `docs/raman_saab/RUN5_PREREG.md` + `run5_gate.toml` (four sha pins, frozen before the held-out read-out)
**Fidelity prior**: `docs/raman_saab/FIDELITY_REPORT_V2.md` — held-out gate **HG1 PASS (0.123)**
**Run id**: `2026-07-03T-run5-raman-v2-heldout-n2091`

## Question

Run 4 refuted one operationalization of "Raman as practiced" — but a
three-agent audit found material defects that made it an unfair test of its
own hypothesis (degenerate longevity-band veto, navamsa-frame conjunctions
computed in radix houses, dead combustion/Shadbala wiring, nakshatra
transfer dropping the dispositor's weakness, and band cutoffs using the
exact 32/70 split HPA p.110 rejects verbatim). Run 5 asked the corrected
question: does a **verifiably faithful** encoder — one that reproduces
Raman's own verdicts on *unseen* charts from his own book — concentrate
fatal potency on real death moments at population scale?

## What made this run different

1. **Audit-corrected encoder (`raman_method_v2`).** Every audit defect
   fixed, plus previously-missing treatise machinery, each keyed to a
   citation: per-lagna kill/spare overrides (HPA Ch. XVII, all 12 lagnas),
   HTJAH p.212 placement-class ayurdaya (Raman's only systematic longevity
   algorithm), HPA-forced band edges 8/32/75/120, ordered
   occupant-2 > occupant-7 > lord-2 > lord-7 hierarchy, independent 8L,
   tara/star-of-death (Vipat/Pratyak/Naidhana), MD↔AD
   shashtashtaka/dwirdwadasa, node sign-dispositor transfer,
   weakness that actually consumes combustion and graded Shadbala.
2. **New data modality: the full *Notable Horoscopes* sweep.** 57
   transcribed cases with Raman's printed positions; an **objective OCR
   filter** (printed-Moon Vimshottari must reproduce his stated
   maha-dasha at death; label-blind ±15-day date repair by position fit)
   validated 48 (84%). Run 4 had 6 golden cases, all consumed by
   calibration.
3. **Held-out design with a STOP rule.** Seeded 50/50 split (seed
   20260704). Weights calibrated on 24 cases only (scripted coordinate
   descent, pinned coarse grid, doctrine ordering constraints as hard
   filters): calibration median death-window percentile 0.184 → 0.090.
   Shas frozen. The other 24 cases scored exactly once, post-freeze:

   | gate | value | rule | outcome |
   |---|---|---|---|
   | HG1 median death-window percentile | **0.123** | ≤ 0.35 proceed / ≥ 0.45 abort | **PASS** |
   | HG2 fraction below 50th pctile | 0.625 | ≥ 0.65 | miss (marginal) |
   | HG3 killer hit-rate (soft) | 0.62 | ≥ 0.70 | miss (reported) |

   This is the fidelity certificate run 4 never had: on 24 of Raman's own
   charts the encoder had **never seen**, real death windows sit at the
   12th percentile of each life's lived dasha windows (16/24 below the
   20th; several below the 5th). The encoder demonstrably "speaks Raman"
   out of book-sample.
4. **Pre-registered transit rule — outcome EXCLUDED.** The Raman-frame
   transit terms (sadesathi 3rd cycle, HPA p.127 composite point) changed
   the calibration median by −0.006, below the required +0.05 gain;
   `tr2.*` zeroed in the frozen weights.
5. Same maximally-charitable population machinery as run 4: Raman's own
   ayanamsa via exact per-JD conversion, shuffled-age permutation null,
   preflight leakage gate, Bonferroni α = 0.01/3.

## Results (all pre-registered primaries)

Preflight (shuffled person↔death-age pairing): P1 z = −1.08, P2 z = −0.20 —
**collapses cleanly, no leakage**. The smoke run (N = 300) was
machinery-only and showed nothing.

| Primary | Result | Threshold | Verdict |
|---|---|---|---|
| P1 — death potency above own 90th-pct null | RR = **0.9675** (176 obs vs 181.9 exp), z = −0.46, p = 0.68 | RR ≥ 1.25 | **null** |
| P2 — mean percentile of death potency in own null | **0.4950** (se 0.0063), z = −0.79, p = 0.78 | ≥ 0.53 | **null** |
| P3 — longevity band κ vs observed band | **κ = −0.0234** (null sd 0.015), p = 0.96 | κ ≥ 0.05 | **null** |

The v2 band classifier is no longer degenerate (all three predicted bands
27–37% of persons — the run-4 defect is fixed), yet its κ against real
lifespans is slightly *negative*. The held-out anti-pattern (0/5 on
Raman's explicitly-stated ayurdaya cases) foreshadowed exactly this and
was flagged as P3's interpretive caveat before the population run.

## Verdict

**REFUTED** (single corpus, N = 2,091 ≥ pre-registered floor 1,500).
`raman.composite.as_practiced_v2` → `refuted` in the ratchet ledger.

## The headline finding

Run 5 produced the cleanest dissociation this project has: an encoder that
**passes an honest out-of-sample fidelity test on the practitioner's own
casebook** (median 12th percentile on 24 unseen *Notable Horoscopes*
charts) transfers to 2,091 independently-timed real deaths at **exactly
chance** (49.5th percentile; top-decile RR 0.97; band κ −0.02). The
coherence the method exhibits is a property of the literature — the
casebook's charts, transcriptions, and verdicts form a self-consistent
corpus the encoder can learn and generalize *within* — not a property of
the population. "Overfitting to six calibration charts", run 4's most
charitable escape hatch, is now closed: the signal survives a held-out
half of the book and still vanishes the moment the charts stop coming
from the book.

## Scope and honesty

- This refutes the encoded composite at its demonstrated fidelity level
  (held-out PASS). The unfalsifiable "intuition residue" caveat (RUN4 §2)
  carries over verbatim — but its footprint shrinks with every mechanism
  encoded, and v2 encoded every mechanism the NH sweep surfaced.
- HG2/HG3 missed their soft marks (0.625 vs 0.65; 0.62 vs 0.70) — carried
  as prior, per prereg. The population nulls are far below any threshold
  regardless.
- Single corpus. The pre-declared Wayback/ADB replication stratum (prereg
  §5 of run 4, carried forward) may still complete; if it yields ≥ 1,000
  new timed persons the frozen pipeline runs once on it as a replication
  read-out.
- All findings are population-level statistical associations. Nothing
  here predicts, or should ever be phrased as predicting, any
  individual's death.

## The run-family arc (runs 1–5)

| Run | Operationalization | N | Verdict |
|---|---|---|---|
| 1 | fixed-lord dasha marginals (Saturn/malefics/nodes) | 82,589 | refuted |
| 2 | house-based maraka lords (2L/7L/8L, timed charts) | 4,586 | refuted |
| 3 | Triple-Lock conjunction + numeric ayurdaya | 2,091 | refuted |
| 4 | Raman-as-practiced graded composite (fidelity PARTIAL) | 2,091 | refuted |
| 5 | **audit-corrected v2, held-out fidelity PASS (0.123)** | 2,091 | **refuted** |

Five escalating operationalizations, the last one carrying an
out-of-sample fidelity certificate on the practitioner's own book — all
null. The **death-timing family is re-HALTED**, now with the strongest
possible closure: the remaining gap between "the method as written" and
"the method as practiced" has been squeezed to the unfalsifiable residue.
No further runs without a genuinely new data modality (the Wayback
replication corpus, or rectified birth-times).

## Reproduce

```
python -m app.medini.etl.fetch_astrocrm --out data/holos
python -m app.medini.ml.raman_saab.build_run3_corpus
python -m app.medini.ml.raman_saab.calibrate_v2                       # calibration half only
python -m app.medini.ml.raman_saab.fidelity_v2 --half held_out \
    --weights data/raman_saab/run5_weights.json --allow-heldout       # step F (post-freeze)
python -m app.medini.ml.raman_saab.run5_potency --smoke               # machinery check
python -m app.medini.ml.raman_saab.run5_potency                       # step G
```
