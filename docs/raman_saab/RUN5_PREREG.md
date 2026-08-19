---
date: 2026-07-03
type: pre-registration (committed BEFORE the held-out read-out and the population run)
run: raman_saab RUN 5 — audit-corrected encoder, held-out fidelity design
corpus: data/raman_saab/death_corpus_run3.parquet (N = 2,091; same as runs 3-4)
gate: docs/raman_saab/run5_gate.toml (four sha pins)
calibration: docs/raman_saab/FIDELITY_REPORT_V2.md (held-out NOT scored)
---

# RUN-5 Pre-registration

## 0. Why this run is permitted (the run-4 family halt)

Run 4's verdict halted the death-timing family absent "a qualitatively new
hypothesis AND a new data modality". Both conditions are met, and the halt
override was explicitly directed by the project owner ("check the encoding
once again … then try again"):

1. **The three-agent audit invalidates run 4 as a fair test of its own
   hypothesis.** Verified defects: the longevity-band classifier was
   degenerate (ALPAYU predicted 1.4%; MADHYAYU/PURNAYU rows of the run-4
   confusion matrix near-identical — the method's core veto did almost
   nothing); navamsa-frame conjunctions were computed in radix houses;
   combustion and graded Shadbala were wired but never consumed; the
   nakshatra transfer dropped the dispositor's weakness (doctrinally the
   reason it kills); and the band cutoffs used the exact 32/70 split that
   HPA p.110 REJECTS verbatim (correct: 8/32/75/120). Run 4's ledger entry
   stands — it refuted THAT encoder. Run 5 tests a materially different
   operationalization (`raman_method_v2.py`), with previously-missing
   treatise machinery (per-lagna kill/spare table, HPA Ch. XVII; ordered
   occupant/lord hierarchy; independent 8L; 12L-conjunction; Sun in the
   kendra-lord promotion) and NH-case mechanisms (tara/star-of-death,
   MD↔AD shashtashtaka/dwirdwadasa, node sign-dispositor transfer).
2. **New data modality**: the NH full sweep yields 48 validated golden cases
   with Raman's printed positions (run 4 had 6, all consumed by
   calibration). This enables the **held-out design**: weights calibrated on
   a seeded half, validated once on the unseen half, with a STOP rule that
   can kill the run before the population is spent.

## 1. Golden registry, validation, split

`nh_golden_cases_v2.json` (sha pinned in the gate TOML): 57 cases;
objective OCR validation = printed-Moon Vimshottari timeline must reproduce
Raman's stated MD at death (AD recorded as a flag — run 4 proved his own
arithmetic can differ from his printed Moon at AD granularity); label-blind
date repair by position-fit (±15 days, ≥6/8 planets within 1.5°, ≥2-planet
gain). 48 valid → seeded 50/50 split (seed 20260704).

**Calibration half (24)**: akbar, buddha, chaitanya, george_vi, golwalkar, hyderali, kasturi, lincoln, marie_antoinette, milton, nanak, nero, nizam, omar, ramana, sc_bose, shivaji, sivananda, tagore, tennyson, thyagaraja, tippu, vivekananda, wadiyar.

**Held-out half (24)**: alexander, ashutosh, augustus, aurangzeb, aurobindo, crdas, einstein, fdr, gandhi, godse, goethe, havelock_ellis, jesus, marx, mussolini, narasimha_bharathi, nehru, rajendra_prasad, ramanuja, sankara, sayaji_rao, suryanarain_rao, tilak, victoria.

## 2. Calibration (CLOSED before this freeze)

Scripted coordinate descent (`calibrate_v2.py`; pinned coarse grid, two
passes, ORDERING_CONSTRAINTS as hard filters), objective lexicographic
(median death-window percentile, killer hit-rate, mean percentile),
calibration half only. Result: median 0.184 → 0.090, killers 0.57. Weights
frozen at `run5_weights.json` (sha pinned).

**Transit inclusion rule — outcome: EXCLUDED.** Pre-registered rule: the
Raman-frame transit terms enter the primaries iff they improve the
calibration median by ≥ 0.05 without lowering the killer hit-rate. Measured
gain: −0.006. `tr2.*` zeroed in the frozen weights; transits are a
non-gating secondary in the verdict only.

## 3. Held-out fidelity gate (step F — scored ONCE, after this freeze)

| Gate | Statistic | Rule |
|---|---|---|
| HG1 | median death-window percentile, held-out half | ≤ 0.35 → proceed; **≥ 0.45 → ABORT ("fidelity refuted, population unspent")**; between → PARTIAL (proceed if HG2 passes, carrying the prior) |
| HG2 | fraction of held-out cases below the 50th percentile | ≥ 0.65 |
| HG3 | killer hit-rate (named ∈ top-4) | ≥ 0.70, soft/reported |

## 4. Population evaluation (step G — only if the held-out gate proceeds)

Identical machinery to run 4 (`run5_potency.py` = run-4 harness + v2 model):
Lahiri cast → exact per-JD delta → Raman-frame bundles → PotencyModelV2;
shared 1,000 shuffled ages (seed 20260705); preflight shuffled-pairing
|z| ≤ 3 hard gate; smoke (300) machinery-only.

Primaries unchanged from run 4 (Bonferroni α = 0.01/3): P1 top-decile
exceedance RR ≥ 1.25; P2 mean mid-rank percentile ≥ 0.53; P3 band κ ≥ 0.05
— with `band_of_age_v2` (32/75 edges, HPA-forced), so P3's κ is
definitionally identical to run 4 but **not numerically comparable**
(different band marginals). Band-degeneracy soft flag: any predicted band
< 2% of persons → P3 reported as non-informative. Verdict rules: any
primary passing at α → `provisional` (single corpus; G2 unreachable); all
three failing at N ≥ 1,500 → `refuted`.

## 5. Honesty notes

- The calibration median (0.090) is optimistic by construction; the
  held-out read-out is the honest fidelity number.
- ~10 new tunables vs 24 calibration cases: mitigated by the coarse pinned
  grid, hard doctrine-ordering constraints, and the held-out audit — but
  residual overfitting risk is real and is exactly what HG1/HG2 measure.
- OCR corruption invisible to the Moon filter remains possible on non-Moon
  positions (the ±2° cross-flags are recorded per case).
- A null at population scale after a PASSING held-out gate would be the
  most informative outcome this family has produced: an encoder that
  demonstrably speaks Raman on his own out-of-sample charts, failing to
  generalize beyond his book. The unfalsifiable "intuition residue" caveat
  from RUN4 §2 carries over verbatim.
