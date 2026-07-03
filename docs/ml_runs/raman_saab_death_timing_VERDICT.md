# raman_saab Death-Timing — VERDICT

> **Run 2 addendum (2026-07-03, timed-birth corpus):** the house-based maraka
> rules — the part of the doctrine run 1 could not test — were validated on
> **N = 4,586 Rodden AA/A/B timed charts** scraped from Astro-Databank via the
> Wayback Machine (real birth times, ADB timezone offsets, real lagnas).
> **Every rule is null:** maraka-lords (2H/7H) dasha RR = 0.99 MD / 0.96 AD;
> 8th-lord RR = 0.99/0.96; union RR = 0.99/0.97; Saturn-as-maraka (1,625
> eligible charts) RR = 0.94/0.95 — all under the same permutation
> (shuffled-age) null, all far from the G1 threshold of 1.20. Natal 8H
> longevity tests (births ≤ 1900, right-truncation-guarded): all null; the
> weak Rahu/Venus trends seen at the N≈2,100 checkpoint regressed to nothing
> at full N, as multiple-comparison noise does. Run 1's fixed-lord rules
> **replicate their null** on this independent corpus (RR 0.98–1.03) —
> completing the cross-corpus (G2) axis for the dasha-karaka refutations.
> Ratchet: the chart rules sit at `candidate (underpowered)` because
> N = 4,586 is just under the pre-registered 5,000 power bar; the corpus
> scrape's tail is still appending deceased entries and the statuses flip to
> `refuted` when N crosses 5,000. Engine audit (2026-07-02): dasha timelines
> match the production engine to 0.0 days on 500 random charts; null
> calibration z ~ N(0,1); planted 5% effect recovered at true size
> (RR 1.171, p=1.5e-4) at N=1,500 — the nulls are powered, not blind.
> Full numbers: `data/ml_runs/raman_saab/maraka_validation.json`.

**Date**: 2026-07-02
**Module**: `app/medini/ml/raman_saab/` (population_validate + ratchet)
**Corpus**: Wikidata death corpus, N = 82,589 persons (day-precision birth +
death dates + birthplace coordinates), scraped by
`app/medini/etl/wikidata_death_corpus.py`
**Run id**: `2026-07-02T-wikidata-n82589`

## Question being tested

> Do B. V. Raman's death-timing (Vimshottari **dasha**) rules — Saturn as
> ayushkaraka, malefic periods, nodal periods — show death **enriched** during
> the flagged lords' Mahadasha/Antardasha across the population, beyond what
> the dasha-length structure and the age-at-death distribution already explain?

Only house-independent (dasha) rules are testable: Wikidata has no birth times,
so ascendant/house-based maraka rules (2nd/7th lords, 8th-house occupancy) are
out of reach (see `docs/death_timing_findings.md` §6).

## Methodology

For each person, compute the Vimshottari MD/AD lord active **at death** (Lahiri
sidereal Moon via Swiss Ephemeris Moshier; MD/AD from the repo's locked
`DASHA_LORDS`). For a rule flagging lord-set S, count deaths whose death-lord ∈
S (observed O) vs the null-expected E; RR = O/E. O is Poisson-binomial, giving
an exact z and one-sided p.

**Two nulls:**

- **Exposure null (descriptive, length-biased):** E = Σ lifespan-fraction under
  S. Endpoint length-bias — the death dasha is only partially lived but scores a
  full hit — inflating RR for long dashas.
- **Permutation null (PRIMARY):** evaluate each person's own dasha timeline at
  ages drawn from the population's empirical age-at-death distribution. Controls
  the length-bias **and** the age confound. This is the population form of the
  repo's `stage_d_preflight.check_shuffled_times_collapse`.

## Results (permutation null, primary)

| Rule | level | RR | z | p (1-sided) | verdict |
|---|---|---:|---:|---:|---|
| `saturn_dasha` (Saturn) | MD | **0.973** | −4.03 | 1.00 | null (wrong dir) |
| `saturn_dasha` | AD | 1.007 | 0.90 | 0.18 | null |
| `saturn_dasha` | MD-or-AD | 0.987 | −2.56 | 1.00 | null |
| `mars_saturn_dasha` | MD | 0.974 | −4.32 | 1.00 | null |
| `malefic_dasha` (Su/Ma/Sa/Ra/Ke) | MD | 0.989 | −3.09 | 1.00 | null |
| `benefic_dasha_protective` (deplete) | MD | 1.010 | +3.09 | 1.00 | null (wrong dir) |
| `rahu_ketu_dasha` | MD | 1.004 | 0.57 | 0.28 | null |

Every rule lands in RR ∈ [0.97, 1.01] — squarely the "null at population scale"
band. **No rule clears G1** (enrich RR ≥ 1.20 / deplete RR ≤ 0.83). Per-lord MD
RRs span only 0.973 (Saturn) to 1.021 (Ketu); the largest |z| is Saturn at
−4.03 — a ~3% deviation in the *anti*-doctrinal direction, i.e. not support.

## The headline finding: a confound caught, not a signal found

Under the **exposure** null, Saturn Mahadasha looked strongly enriched at death:

> Saturn MD, exposure null: **RR = 1.090, z = 12.05, p = 9.3e-34**

Under the **permutation** null it disappears:

> Saturn MD, permutation null: **RR = 0.973, z = −4.03** (null / slightly depleted)

The entire "signal" was the **endpoint length-bias**: Saturn's 19-year
Mahadasha is long, so people are disproportionately *caught mid-Saturn-MD at
death* relative to how much Saturn MD contributes to lifespan exposure. The
same artifact made all long dashas (Venus 20y, Jupiter 16y, Mercury 17y) look
"enriched" and short ones (Sun 6y, Mars 7y, Ketu 7y) look "depleted" under the
exposure null — a pattern with no doctrinal meaning. This is a textbook
instance of the "looks like signal, controls reveal confound" failure mode
catalogued in `docs/round9_lessons_learned.md` §1.

## Robustness

- **Birth-time sensitivity** (unknown in corpus; swept 00/06/12/18h local):
  Saturn MD RR = 0.973–0.982 across all hours (z −2.7 to −4.0). Verdict is
  stable to the unknown birth time.
- **Age-stratified** (deaths age 55–85, N = 55,000): Saturn MD RR = 0.960
  (z −4.88), malefic MD RR = 0.963 (z −8.18). Still null/anti-doctrinal — the
  result is not an age-clustering artifact.

## Verdict

**NULL.** All five candidate death-timing dasha rules are **refuted** at high
power (N = 82,589) under the confound-controlled permutation null. B. V. Raman's
dasha-level death-timing doctrine does not predict death timing at population
scale once dasha-length and age are controlled.

This is consistent with — and extends — the project's prior evidence: Round-11's
population RR null, and `framework_validation_v1_VERDICT.md`'s **Death → 8H lift
= 1.00**. It is the first test of the *dasha-timing* (rather than natal-house)
form of the death doctrine at this scale, and it too is null.

## Ratchet outcome

Per `docs/raman_saab/DOCTRINE_RATCHET_PLAN.md`, all five rules move
`candidate → refuted` (single-corpus, high-power). Ledger:
`docs/raman_saab/RATCHET_LEDGER.json`.

| rule | status |
|---|---|
| raman.karaka.saturn_dasha | refuted |
| raman.karaka.mars_saturn_dasha | refuted |
| raman.malefic_dasha | refuted |
| raman.benefic_dasha_protective | refuted |
| raman.karaka.rahu_ketu_dasha | refuted |

## Caveats & scope

- **Single corpus.** Per the ratchet, refutation here is single-corpus (Wikidata).
  Cross-corpus replication (G2) would harden it; the direction (null) is
  unlikely to reverse given the effect sizes.
- **Dasha-only.** House/lord maraka rules (the richer part of Raman's longevity
  method) are **untested** — they need birth times. They remain `candidate`
  (blocked on data), not refuted. A birth-time-rated corpus (e.g. AstroDatabank
  Rodden-rated) would unlock them.
- **Ayurdaya bands** (Alpayu/Madhyayu/Purnayu) are not yet implemented (also
  need ascendant-dependent pairs); listed as future work in
  `death_timing_findings.md` §4.

## Reproduce

```
python -m app.medini.etl.wikidata_death_corpus --out app/medini/data/raman_saab/death_corpus.parquet
python -m app.medini.ml.raman_saab.cli --corpus app/medini/data/raman_saab/death_corpus.parquet --run-id <id>
```
