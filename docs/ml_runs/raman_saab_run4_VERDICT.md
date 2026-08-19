# raman_saab RUN 4 — "Raman as Practiced" — VERDICT

**Date**: 2026-07-03
**Modules**: `app/medini/ml/raman_saab/{chart_bundle,raman_method,fidelity,run4_potency}.py`
**Corpus**: `death_corpus_run3.parquet` — N = 2,091 timed (Rodden AA/A) charts with own-death dates
**Pre-registration**: `docs/raman_saab/RUN4_PREREG.md` + `run4_gate.toml` (weights sha-frozen before evaluation)
**Fidelity prior**: `docs/raman_saab/FIDELITY_REPORT.md` (PARTIAL)
**Run id**: `2026-07-03T-run4-raman-frame-n2091`

## Question

Runs 1–3 refuted textbook *marginals*. Run 4 asked the stronger, fairer
question: does **Raman's method as he actually practiced it** — encoded as a
gated, graded composite (qualitative longevity class → conjunction-ranked
maraka hierarchy across four reference frames → dasha/bhukti fatal potency
scaled by weakness, nakshatra-transfer, occupancy, dasha-sandhi — vetoed by
the longevity band), calibrated ONLY against his own published verdicts and
run in **his own ayanamsa** — concentrate fatal potency on real death
moments at population scale?

## What made this run different (and maximally charitable)

1. **Fidelity gate first.** The encoder was tested against six golden cases
   from *Notable Horoscopes* (his printed positions, verbatim verdicts).
   His printed Moons reproduce his stated death dashas 4/4 — including
   "as soon as Rahu Dasa commenced" (Tilak) landing at MD-fraction 0.02 and
   Einstein's Jupiter at 0.01. Every encoder mechanism cites a verbatim
   passage (the nakshatra-transfer, Saturn-ayushkaraka-maraka,
   8H-occupant-aspected-by-maraka, malefic-in-12th, Chandra and navamsa
   frames, Shaw's longevity marks).
2. **His zodiac.** Under the repo's Lahiri ayanamsa only 2/5 of his stated
   death dashas reproduce (~1.5-year dasha shift); the population run
   converted every chart to Raman's ayanamsa by the exact per-JD delta.
3. **Calibration firewall.** Weights were tuned on the golden set only,
   then sha-frozen in the prereg before the population was touched.

Fidelity outcome carried as prior: **PARTIAL** — mechanisms encode
faithfully, but even on his own showcase charts the composite concentrated
death-window potency only modestly (median 21st percentile of lived windows
vs 50% chance; Einstein 73rd).

## Results (all pre-registered primaries; Bonferroni α = 0.01/3)

Preflight (shuffled person↔death-age pairing): P1 z = 0.30, P2 z = 1.16 —
**collapses cleanly, no leakage**.

| Primary | Result | Threshold | Verdict |
|---|---|---|---|
| P1 — death potency above own 90th-pct null | RR = **1.0045** (183 obs vs 182.2 exp), z = 0.06, p = 0.47 | RR ≥ 1.25 | **null** |
| P2 — mean percentile of death potency in own null | **0.5062** (se 0.0063), z = 0.98, p = 0.16 | ≥ 0.53 | **null** |
| P3 — longevity band κ vs observed band | **κ = 0.0145** (null sd 0.019), p = 0.23 | κ ≥ 0.05 | **null** |

Band confusion (P3): predicted-MADHYAYU and predicted-PURNAYU rows are
nearly proportional across observed bands — the encoder's band assignment
carries no lifespan information (matching run 3's ayurdaya κ = 0.016).

The smoke run's suggestive numbers (N = 300: P2 = 0.530, κ = 0.085)
evaporated at full N — small-sample noise, and the prereg pre-committed to
not interpreting them.

## Verdict

**REFUTED** (single corpus, N = 2,091 ≥ pre-registered power floor 1,500).
`raman.composite.as_practiced_v1` → `refuted` in the ratchet ledger.

The golden-set concentration (21st percentile median) did **not**
generalize: out of sample, the composite places real deaths at the 50.6th
percentile of each person's own potency distribution — chance. This is the
cleanest possible reading of the calibration firewall: the modest fidelity
signal was residue of tuning on six charts, not a transferable regularity.

## Scope and honesty

- This refutes **the encoded composite at its demonstrated fidelity level**
  (PARTIAL). The un-encodable remainder of "intuition" is unfalsifiable by
  construction — stated in the prereg §2, not retro-fitted.
- Single corpus. The pre-declared Wayback replication stratum (prereg §5)
  had not completed at evaluation time; if it completes, the frozen
  pipeline may run once on it as a replication read-out.
- Transit multipliers were excluded from primaries (frame consistency);
  the dasha-sandhi term was included.

## The run-family arc (runs 1–4)

| Run | Operationalization | N | Verdict |
|---|---|---|---|
| 1 | fixed-lord dasha marginals (Saturn/malefics/nodes) | 82,589 | refuted |
| 2 | house-based maraka lords (2L/7L/8L, timed charts) | 4,586 | refuted |
| 3 | Triple-Lock conjunction + numeric ayurdaya | 2,091 | refuted |
| 4 | **Raman-as-practiced graded composite, fidelity-gated, his ayanamsa** | 2,091 | **refuted** |

Four escalating operationalizations — from crude marginals to a
fidelity-verified reconstruction of the practitioner's own composite in his
own zodiac — all null. Per the ratchet's kill criterion (3 consecutive
refuted verdicts halt a family), the **longevity/death-timing family is now
HALTED**: no further death-timing runs without a qualitatively new
hypothesis AND a new data modality (e.g. the Wayback replication corpus for
G2, or rectified birth-times).

## Reproduce

```
python -m app.medini.etl.fetch_astrocrm --out data/holos
python -m app.medini.ml.raman_saab.build_run3_corpus
python -m app.medini.ml.raman_saab.fidelity --report docs/raman_saab/FIDELITY_REPORT.md
python -m app.medini.ml.raman_saab.run4_potency --corpus data/raman_saab/death_corpus_run3.parquet
```
