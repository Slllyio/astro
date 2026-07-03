---
date: 2026-07-03
type: pre-registration (committed BEFORE the population evaluation)
run: raman_saab RUN 4 — "Raman as practiced" (fidelity-gated graded scorer)
corpus: data/raman_saab/death_corpus_run3.parquet (N = 2,091 timed, Rodden AA/A)
gate: docs/raman_saab/run4_gate.toml (hashes pinned there)
fidelity: docs/raman_saab/FIDELITY_REPORT.md (PARTIAL — see §2)
---

# RUN-4 Pre-registration — Raman-as-Practiced Fatal Potency

## 1. Hypothesis (NEW vs runs 1–3; lifts the family halt for this run only)

Runs 1–3 refuted **textbook marginals**: fixed-lord dasha sets (run 1,
N=82,589), house-based maraka-lord sets (run 2, N=4,586), and the Triple-Lock
conjunction with numeric ayurdaya (run 3, N=2,091). Deep reading of Raman's
worked cases (*Notable Horoscopes*, full text) shows he does not decide by
those marginals: his practiced method is a **gated, graded synthesis** —
longevity class first, marakas by a conjunction-ranked relationship hierarchy
across multiple reference frames, dasha/bhukti fatal potency scaled by
weakness / nakshatra-transfer / occupancy, all vetoed by the longevity band.

Run 4 tests **that composite**, encoded in `raman_method.py` and calibrated
ONLY against his own published verdicts (the fidelity golden set). This is a
different operationalization class from runs 1–3 (graded, fidelity-verified,
chart-conditional), pre-declared here as a new hypothesis.

## 2. Fidelity status carried as prior (calibration CLOSED)

The encoder reproduces Raman's readings only partially
(`FIDELITY_REPORT.md`): dasha anchors 4/4 on his printed positions; named
killers in top-4 for 3/4 Tier-A charts; longevity band correct where he
states one (1/1); but death-window potency concentrates only modestly even on
his own showcase charts (median 21st percentile of lived windows vs 50%
chance; Einstein 73%). Interpretation guardrail: **run 4 asks whether even
this modest concentration generalizes out of sample.** A null here refutes
the encoded composite at its demonstrated fidelity level — not "Raman's
intuition" in the abstract; that residue is unfalsifiable by construction and
we say so now rather than after the result.

Weights are FROZEN at `raman_method.py` sha256
`459ff1dfeba8a17bd2a94524657e276069fdfd234c99ff595931654b15a4fa41`
(pinned in run4_gate.toml). Any post-commit weight change voids the run.

## 3. Frame: Raman ayanamsa (justified divergence from the repo Lahiri lock)

The fidelity gate proved the point empirically: under Lahiri, only 2/5 of
Raman's stated death dashas reproduce; under his own positions/ayanamsa, 4/4
(with his two "as soon as the Dasa commenced" cases landing at MD-fraction
0.01–0.02). Testing his method in a zodiac ~1.4° away from his own shifts
every dasha boundary by ~1.5 years and would be a straw man. The population
cast is therefore converted Lahiri→Raman by the exact per-JD ayanamsa delta
(tropical frame is mode-invariant). The repo's production Lahiri lock
(doctrine-decisions.md) is untouched — this is a research-run parameter.

**Transits are excluded from the primaries** (ingress tables are
Lahiri-built; mixing frames would be inconsistent). The dasha-sandhi term
(pure dasha arithmetic) is included. Transit multipliers may be reported as
a pre-declared secondary only.

## 4. Design

Per person: fatal potency at the true death moment vs at the **shared 1,000
ages** drawn (seed 20260703) from the corpus' empirical age-at-death
distribution — the shuffled-age null of runs 1/3, controlling dasha-length
and age-at-death confounds simultaneously. Potency evaluation is
`PotencyModel.potency(md, ad, age, md_frac)` — per-person precomputation,
pure lookups per moment.

### Primaries (Bonferroni α = 0.01/3 each; thresholds in run4_gate.toml)

| # | Statistic | Null | Pass threshold |
|---|---|---|---|
| P1 | Top-decile exceedance: death potency strictly above the person's own 90th percentile of null potencies; per-person null p_i computed exactly from the sample (ties included) | Poisson-binomial | RR ≥ 1.25 AND p < α |
| P2 | Mean mid-rank percentile of death potency in the person's own null distribution | mean = 0.5 exactly; per-person variance estimated from the sample (se ≈ 0.0063 at N = 2,091, so the threshold sits ≈ 4.8σ from the null — refutable) | mean ≥ 0.53 AND p < α |
| P3 | Cohen's κ, encoder longevity band vs observed `band_of_age` | empirical (500 draws of observed bands from the sampled ages) | κ ≥ 0.05 AND p < α |

### Preflight (hard gate, runs before the confirmatory read-out)

Shuffled-pairing collapse: re-pair every person with another person's death
age — P1 and P2 must land within |z| ≤ 3. Failure = leakage; stop.

### Verdict rules

- **provisional** — any primary passes its threshold AND its α (single
  corpus; G2 replication unmet, so `validated` is unreachable here).
- **refuted** — all three primaries fail at N ≥ 1,500 (power note above).
- Smoke run (300 persons) validates machinery only; its numbers are not
  interpreted.

### Robustness (reported, non-gating)

Rodden-class strata (AA vs A); hemisphere strata; the exposure-null column
is NOT computed (known length-biased, run-1 lesson).

## 5. Replication extension (pre-declared, conditional)

A Wayback/ADB timed corpus is being scraped in the background. IF it
completes and yields ≥ 1,000 additional non-overlapping timed persons, the
same frozen pipeline runs once on it as a replication stratum; pooled
verdict per the ratchet's G2 language. If it does not complete, run 4 stands
as single-corpus.

## 6. Outputs

`data/ml_runs/raman_saab/run4/main_run.json`, ledger block in
`docs/raman_saab/RATCHET_LEDGER.json` (run4 section, additive),
`docs/ml_runs/raman_saab_run4_VERDICT.md`, findings table §7f in
`docs/death_timing_findings.md`.
