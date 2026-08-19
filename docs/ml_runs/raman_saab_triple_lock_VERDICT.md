# raman_saab Run 3 — Triple Lock VERDICT

**Date**: 2026-07-03
**Module**: `app/medini/ml/raman_saab/triple_lock.py` (+ `run3_gate.py`)
**Pre-registration**: `docs/raman_saab/RUN3_PREREG.md` (committed before the
evaluation; code SHA `faea72d…`, corpus sha256 `45c7cd38…`)
**Corpus**: ASTROCRM/Astro-Databank timed births — **N = 2,091** (1,836
Rodden AA + 255 A) with birth time, coordinates, tz offset, and a full-date
own-death event. Built by `build_run3_corpus.py`.
**Run id**: `2026-07-03-triple-lock-adb-astrocrm-n2091`

## Question being tested

Runs 1–2 refuted the *marginals* of B. V. Raman's death-timing doctrine (run 1:
fixed-karaka dasha rules, N=82,589 Wikidata; run 2: house-based maraka-lord
dasha rules, N=4,586 ADB). The standing doctrinal defense of those nulls is
that the factors must **concur**. Run 3 tests exactly that — the conjunctional
claim, plus the two legs never before tested:

> Death occurs when **(1) a maraka dasha** operates (MD or AD lord among the
> lords of the 2nd/7th from lagna) **∧ (2) a gochara trigger** is live (Sade
> Sati | Saturn in natal 8H | Jupiter–Saturn double transit on 8H) **∧ (3)**
> the age lies in the chart's promised **ayurdaya band** (three-pairs
> Alpayu/Madhyayu/Purnayu).

## Methodology

Per the pre-registration: primary permutation/shuffled-age null (one
fixed-seed 1,000-age sample shared across persons and legs, so the joint null
probability inherits all between-leg dependence); Poisson-binomial exact z /
one-sided p; 4 primary tests, Bonferroni α = 0.0025; thresholds legs RR ≥ 1.20,
conjunction RR ≥ 1.50; refutable-power rule ≥ 0.90 per test. Transits from
±0.5-day sign-ingress tables (property-tested vs direct ephemeris); T3
double-transit semantics pinned to the production `compute_gochara` by a
200-case parity test; ayurdaya per pins P1–P12 (incl. true sunrise-anchored
Hora Lagna). Preflight (shuffled person↔death-age pairing) passed: every
primary |z| ≤ 3 (joint RR 1.021, z 0.22).

## Results (primary, permutation null)

| test | RR | z | p (1-sided) | threshold | power | verdict |
|---|---:|---:|---:|---|---:|---|
| leg1_maraka (md_or_ad) | 0.978 | −0.88 | 0.81 | ≥1.20 | 1.000 | **refuted** |
| leg2_gochara (T1\|T2\|T3) | 1.020 | +0.72 | 0.24 | ≥1.20 | 1.000 | **refuted** |
| leg3_ayurdaya (band match) | 1.033 | +1.20 | 0.12 | ≥1.20 | 1.000 | **refuted** |
| **triple_lock (1∧2∧3)** | **0.992** | **−0.09** | **0.54** | ≥1.50 | 0.995 | **refuted** |

The conjunction sits at chance to the third decimal: observed 442 joint-lock
deaths vs 445.8 expected under the shuffled-age null.

Secondary rows (descriptive): all within RR [0.87, 1.10]; the most extreme,
`leg2_and_leg3` (RR 1.099, p 0.039), is a secondary at 15× the Bonferroni α
and shrinks under jitter. **Ayurdaya band accuracy = 33.8% vs 33.3% chance;
Cohen's κ = 0.016** — the three-pairs method carries no information about
observed death ages. (It also mis-bands its own author: the method votes
ALPAYU for B. V. Raman's chart; he died at 86 — recorded in the golden test,
not patched.)

## Robustness (pre-declared)

- **Birth-time jitter ±15 min** (Rodden-A precision, 2 seeds): 13–14% of
  persons flip ascendant/maraka-set/band, yet joint RR stays 0.952 / 0.964.
- **Degenerate fixed-hour sweep** (00/06/12/18h): joint RR 0.930–1.050 —
  real birth times neither create nor hide a signal.
- **Strata**: Rodden AA (n=1,836) RR 0.996; Rodden A (n=255) RR 0.965;
  northern hemisphere RR 0.968. South (n=52) under the pre-set 100 floor.

## Verdict

**NULL — all four pre-registered tests refuted at adequate power.** The
conjunctional "Triple Lock" form of Raman's death-timing doctrine performs
exactly at chance on 2,091 Rodden-rated timed charts, as do each of its three
legs individually — including the two legs (gochara triggers, ayurdaya bands)
tested here for the first time. With runs 1–3 together, the doctrine's death
timing has now failed at population scale in its house-independent marginal,
house-based marginal, and conjunctional forms, across three independently
assembled corpora (Wikidata, ADB-Wayback, ADB-ASTROCRM) totalling ~89k
persons. The "factors must concur" defense is now itself refuted.

## Ratchet

Ledger block `2026-07-03-triple-lock-adb-astrocrm-n2091` appended to
`docs/raman_saab/RATCHET_LEDGER.json`:

| rule | status | power |
|---|---|---|
| raman.triple_lock.leg1_maraka | refuted | 1.000 |
| raman.triple_lock.leg2_gochara | refuted | 1.000 |
| raman.triple_lock.leg3_ayurdaya | refuted | 1.000 |
| raman.triple_lock.triple_lock | refuted | 0.995 |

Kill-criterion note: run 3 was pre-registered as a distinct hypothesis (the
conjunction + two untested legs), so this block does not violate the
3-refutations halt — but with the conjunctional form now null, the
**longevity family halts** absent a genuinely new mechanism. The remaining
pre-registered variants (P5 samasaptaka sensitivity, P7 Madhyayu-fallback,
BPHS Ch.43 Pindayu family) are catalogued as `candidate`, not scheduled.

## Caveats

- Single corpus per the ratchet (though the three runs jointly cover three
  corpora and both marginal + conjunctional forms).
- The Wayback N-booster scrape (run-2 corpus rebuild) continues in the
  background; if it completes, a same-pins replication extension on the union
  corpus is pre-declared in RUN3_PREREG §2 — reported separately, never pooled.
- Ayurdaya was operationalized as the three-pairs method (P1); the Parashari
  Pindayu family is untested (out of scope, pinned).

## Reproduce

```
python -m app.medini.etl.fetch_astrocrm
python -m app.medini.ml.raman_saab.build_run3_corpus
python -m app.medini.ml.raman_saab.triple_lock --corpus data/raman_saab/death_corpus_run3.parquet --out data/ml_runs/raman_saab/run3
python -m app.medini.ml.raman_saab.run3_gate --run-id <id>
```
