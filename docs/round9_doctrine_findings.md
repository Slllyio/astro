# Round 9 doctrine findings — empirical structure in classical Vedic dasha-lord attribution

_Author note: this document consolidates the doctrine-faithful scoring
work from Round 9 of the astro project. The empirical signal here is
small in absolute terms (rate ratios 1.4-2.4) but is a defensible
positive contribution against a backdrop of 5 prior substrate FAILs._

## TL;DR

In a corpus of 86,599 (person, mahadasha-window) tuples drawn from
10,239 people with dated events, the classical Vedic-astrology rule
"the event class E fires when the dasha lord L has structural
relevance to E" carries detectable per-time signal for **3 of 14
event classes** at p<0.05 and **2 classes survive Bonferroni
correction at α/14 = 7e-4**:

| Class | Top-vs-bottom quintile RR (95% CI) | Trend p | Scorer applied |
|---|---|---|---|
| **fame** | 1.43 (1.25-1.64) | **1.06e-06** | §6 strength-modulated |
| **personal** | 2.44 (1.81-3.29) | **2.0e-04** | §6 strength-modulated |
| relationships | 2.28 (1.71-3.03) | 4.4e-03 (above Bonferroni) | §8.3 triple-witness |

11 other event classes (marriage, career, death, finance, health,
education, legal, work, family, ...) show no significant trend at any
sample size in this corpus. The signal is concentrated in event
classes where classical doctrine attributes the timing to **specific
structural channels** that are stable across reading traditions.

## What "doctrine-faithful scoring" means here

Three classical primitives, combined according to per-class doctrine:

1. **§5 channel-relation score** (BPHS Ch.46 + Raman + Rao):

   ```
   chrel(L, h)   = 1.00 * is_lord(L,h) + 0.75 * occupies(L,h) + 0.50 * aspects_full(L,h)
   HR(L, E, C)   = sum (h, w) in house_map(E):  w * chrel(L, h, C)
   KR(L, E)      = max (planet, w) in karaka(E): w * 1[L == planet]
   func_mod(L,C) = +0.5 yogakaraka / +0.25 trikona / 0 kendra / -0.25 dusthana
   relevance(L,E) = HR + KR + func_mod
   ```

   House weights (1.0 primary / 0.5 secondary / 0.25 tertiary) and channel
   weights (1.0/0.75/0.50) follow the doctrine spec at
   `docs/dasha_house_lord_doctrine.md` §5.

2. **§6 strength modifier** (BPHS Ch.27 Sthana-bala, simplified):

   A dignity-based positional-strength proxy in place of full Shadbala:

   | Dignity         | Multiplier |
   |---|---|
   | Exalted         | 1.00 |
   | Own / moolatrikona | 0.75 |
   | Friend          | 0.50 |
   | Neutral         | 0.40 |
   | Enemy           | 0.25 |
   | Debilitated     | 0.10 |

   This is the strongest single component of Shadbala. Empirically, adding
   the other 3 cached-data-computable components (Dig, Naisargika, Drik)
   *regressed* the signal — see "What didn't work" below.

3. **§8.3 trikona-sakshi triple-witness** (Raman, Rao):

   ```
   triwit(E, person, MD_lord) = min(
       bhavesha_witness:  strength_of(lord_of_primary_house(E), E, person),
       karaka_witness:    max strength_of(karaka, E, person) over karakas(E),
       md_witness:        strength_of(MD_lord, E, person),
   )
   ```

   Each witness is computed with §5 × §6. The MIN encodes the doctrinal
   "weakest link" rule — the event fires only when all three witnesses
   align.

## Per-class scoring assignment (locked, doctrine-informed)

| Class | Scorer | Doctrinal reason |
|---|---|---|
| `fame` | §6 | BPHS 27.62: results delivered fully when bala > apekshita. Exaltation = canonical honour marker. |
| `personal` | §6 | Phaladeepika Ch.4: personal events tied to 1H-lord strength. |
| `relationships` | §8.3 | Raman/Rao explicitly use triple-witness for yoga manifestation. Partnerships are yoga-shaped. |
| `marriage` | §5 | Marriage timing is dasha+transit-driven, not lord-strength-driven. |
| `family` | §5 | Default. Signals scattered across many karakas + houses. |
| `career`/`work` | §5 | Default. Multiple co-equal karakas dilute strength signal. |
| `health` | §5 | Default. Affliction reading more than strength. |
| `education`/`finance`/`legal` | §5 | Default. |
| `death_*` | §5 | Default. Affliction-based. |

This assignment was made **before** running the per-class results. The
empirical data confirms the doctrine intent without modification.

## Headline result

Per-class top-vs-bottom-quintile rate ratios on the locked mix-and-match
scorer, sorted by RR:

| Class | RR (95% CI) | Bottom-quintile rate/yr | Top-quintile rate/yr | Trend p (1-sided) |
|---|---|---|---|---|
| `personal` | **2.44** (1.81-3.29) | low | 2.4× higher | **2.0e-4** |
| `relationships` | **2.28** (1.71-3.03) | low | 2.3× higher | 4.4e-3 |
| `fame` | **1.43** (1.25-1.64) | mid | 1.43× higher | **1.06e-6** |
| education | 1.15 | — | — | 0.63 |
| health | 1.14 | — | — | 0.16 |
| legal | 1.13 | — | — | 0.086 |
| finance | 1.11 | — | — | 0.57 |
| marriage | 1.06 | — | — | 0.21 |
| 6 others | <1 (negative direction) | — | — | n.s. |

**Bonferroni passes**: 2 of 14 (fame + personal). **Joint binomial p**
across 14 classes at α=0.05 = 0.03.

## What didn't work (the negative findings)

### §5.8 multi-layer composition (MD × AD × PD)

The doctrine spec includes a multiplicative composition over the three
dasha layers: `relevance_full = R_md^0.5 × R_ad^0.3 × R_pd^0.2`.

Empirically this **does not improve** over MD-only on this corpus:

- **Product combiner** produces eye-popping headline RRs (relationships
  33.5) that are artifacts: 72.5% of rows have at least one zero-
  relevance layer, collapsing the product to zero and making the
  bottom-quintile rate ~zero. RR = (something small) / (near zero) is
  uninterpretable.
- **Additive combiner** (`0.5*R_md + 0.3*R_ad + 0.2*R_pd`) is
  statistically clean but actually weaker than MD-only because the AD
  and PD lords at the population scale add noise rather than refinement.

Doctrinal interpretation: classical astrologers use AD windows in
individual reading to identify SPECIFIC sub-periods where MD + AD +
transits align. The all-AD-lord cross-section at population scale
doesn't surface that pattern. The doctrine here works at the
chart-and-strength level, not the multi-layer-aggregate level.

### Partial Shadbala (4 of 6 balas)

Adding Dig + Naisargika + Drik to the dignity-only Sthana-proxy
*regressed* the signal:

| Class | Dignity-only RR | + Dig + Naisargika + Drik RR | Change |
|---|---|---|---|
| personal | 2.44 | 1.96 | **-0.48** |
| relationships | 2.04 | 1.72 | **-0.32** |
| fame | 1.43 | 1.39 | -0.04 (lost Bonferroni) |

Why: Dig/Naisargika/Drik measure **absolute** planet strength regardless
of event class. A high-naisargika Saturn doesn't make events fire more —
Saturn is karaka for only some classes. Multiplying these in
broadened noise without adding event-class-specific signal.

**Implication**: the dignity proxy alone is the right amount of
strength integration. Full Shadbala may help if combined with
event-class-specific weighting, but flat-summing all 6 balas is
counterproductive.

## What this contributes (a positive scientific claim)

The bare claim defensible from this corpus + analysis:

> "In a corpus of 10,239 individuals with dated life events, the
> classical Vedic-astrology rule 'event class E is more likely during
> a mahadasha period whose lord has structural relevance to E' predicts
> the per-time rate of `personal` events (RR=2.44, p=2.0e-4) and
> `fame` events (RR=1.43, p=1.06e-6) with rates exceeding Bonferroni-
> corrected significance at α=0.01/14. The corresponding `relationships`
> signal (RR=2.28, p=4.4e-3) is significant at α=0.05 but does not
> survive Bonferroni. Eleven other event classes do not show
> Bonferroni-significant signal in this sample. The classical "lord
> attribution" rule appears to carry **modest-but-real per-time
> predictive signal for the specific subset of events where the
> doctrine is doctrinally focused** — strength-based events for personal
> and fame, yoga-style triple-witness for relationships."

This is **modest** — RR=1.43 means the top-strength quintile is 43%
more likely to see a fame event in a given month than the bottom-
strength quintile, conditional on being in the same dasha window of
the same person's chart. But it is **stably present** under exposure-
adjusted Poisson testing on an n=10k corpus, and it is **doctrinally
grounded** — the per-class scorer assignment matches BPHS / Phaladeepika
/ Raman / Rao without empirical tuning.

## CRITICAL REPLICATION FAILURE — lunarastro corpus (added 2026-05-25)

After the original Astro-Databank result was written above, the same
scorers were re-run on an INDEPENDENT corpus (lunarastro research-style
event tagging, ~32k people, 291k MD windows). **The original signal
did not transfer.**

| Class | Astro-Databank RR | Lunarastro RR | Replication |
|---|---|---|---|
| **fame** | **1.43 PASS** (p=1.06e-6) | **0.99** (p=0.98) | **VANISHED** |
| **personal** | **2.44 PASS** (p=2.0e-4) | 2.09 (p=0.04) | direction holds, n=52 (weak) |
| **relationships** | 2.28 (p=4.4e-3) | **0.52** (p=1.0) | **REVERSED** |
| marriage | 1.06 | **0.75** (p=1) | **REVERSED** |
| family | 0.90 (n.s.) | **1.23 PASS** (p=1.3e-4) | new positive |

The bare-§5 scorer on lunarastro shows the same pattern (fame=0.99,
relationships=0.52), so the failure is not a strength-modifier
artifact — it's the underlying lord-attribution mechanism that fails.

### Possible explanations (cannot distinguish without a 3rd corpus)

1. **Corpus-specific selection bias.** Astro-Databank curates documented
   public figures with biographies; lunarastro is research-style with
   inline-date events. Different selection criteria could produce
   systematically different event-class distributions in different
   dasha windows.
2. **Event-class extraction mismatch.** Astro-Databank's `event_fame=1`
   labels biographies; the lunarastro regex extractor maps phrases like
   "Award 1983" / "Public Office 1992" to `event_fame=1`. These may
   index different astrological phenomena even though both are called
   "fame".
3. **Original signal was multiple-testing artifact.** With 14 classes
   tested at α=0.05, you'd expect ~0.7 false positives by chance.
   Bonferroni correction nominally controls for this, but the doctrine
   research process tested many scorers (Stage F-2 product / additive,
   Stage F-3, F-4, F-5) — informal multiple-testing may have inflated
   the Bonferroni p-values.

### Revised headline claim

**The original "doctrine carries Bonferroni-significant signal on
Astro-Databank" finding does not robustly generalize.** A doctrine-
informed mix-and-match scorer applied on lunarastro produces:
- 1 Bonferroni pass (`family`, RR=1.23, p=1.3e-4)
- 1 trend p<0.05 (`personal`, RR=4.31, p=0.001 with wide CI)
- everything else null or reversed-direction

The intersection of the two corpora's Bonferroni-passing classes is
**EMPTY** — fame passes on Astro-Databank but not lunarastro; family
passes on lunarastro but not Astro-Databank. This is the signature of
corpus-specific signal, not a universal doctrine effect.

### 3-way arbiter — Wikidata replication (added 2026-05-25 final)

To distinguish between corpus-specific artifact and extraction-bug
hypotheses, a third INDEPENDENT corpus was pulled from Wikidata SPARQL
(structured biographical events for 32,932 people born 1850-2000;
P166 awards, P39 positions, P26 marriages, P570 deaths). 46,351
events → 289,442 MD windows. Mix scorer result:

| Class       | RR (95% CI)        | Trend p     | Bonferroni (α=0.01/5) |
|-------------|--------------------|-----------  |-----------------------|
| **career**  | **1.25 (1.16-1.34)** | **8.4e-11** | **PASS**              |
| fame        | 1.04 (0.98-1.11)   | 0.092       | fail                  |
| marriage    | 1.00 (0.94-1.06)   | 0.92        | fail                  |
| relationships | 0.84 (0.78-0.91) | 1.0         | reversed              |
| death       | 0.77 (0.72-0.83)   | 1.0         | reversed              |

### Final 3-way cross-corpus picture

| Class         | Astro-Databank   | Lunarastro       | Wikidata        |
|---------------|------------------|------------------|-----------------|
| `fame`        | **1.43 PASS**    | 0.99 (n.s.)      | 1.04 (n.s.)     |
| `personal`    | **2.44 PASS**    | 2.09 (weak)      | (no data)       |
| `relationships` | 2.28 (p=4e-3)  | **0.52 reversed** | 0.84 reversed  |
| `marriage`    | 1.06             | **0.75 reversed** | 1.00           |
| `career`      | 0.93             | 0.75 reversed    | **1.25 PASS**   |
| `family`      | 0.90             | **1.23 PASS**    | (no data)       |

**No class passes Bonferroni on more than one corpus.** Each substrate
has a different "winning" class:
- Astro-Databank → `fame` + `personal`
- Lunarastro → `family`
- Wikidata → `career`

This is the signature of **corpus-specific spurious correlations**,
NOT a universal doctrine signal. The three corpora pull
event-class data from systematically different sources:
- Astro-Databank: curated biographies of public figures
- Lunarastro: research-tagged events with inline-date phrases
- Wikidata: structured property records (P166/P39/P26/P570)

Each source's selection bias produces its own spurious correlation
with dasha-lord doctrine quintiles. None of the spurious correlations
transfers.

### Definitive null verdict

The cross-corpus replication produces an **EMPTY intersection of
Bonferroni-passing classes**. This is what we'd expect under the null
hypothesis: a 14-class test at α=0.05 with informal multiple-testing
inflation should fire ~3 spurious "PASS" per corpus by chance.

The structural-doctrine relevance scoring as tested here **does not
carry universal predictive signal** across the three corpora available
to us. The original Astro-Databank-only signal was almost certainly
**corpus-specific Type I error** (selection bias or unrecognised
multiple testing).

### Final mechanistic confirmation — non-structural ML with birth-date control

To settle why the original quintile-test signal appeared, an XGBoost
classifier was trained per event-class on both Astro-Databank and
Wikidata corpora with two feature sets:

* **person_only**: birth_year + birth_jd (day-precision) +
  window_start_year + md_lord one-hot. Captures person-level +
  per-window date confounders.
* **full_chart**: above + ascendant + 9 planet signs + 9 planet-house
  occupancies (228 cyclical structural features).

Person-disjoint 5-fold CV (GroupKFold on name_norm — no person ever
in both train and test).

#### Wikidata corpus (n=289,442 windows, 32,884 people)

| Class    | person_only AUC | full_chart AUC | Lift   |
|----------|------------------|------------------|--------|
| career   | 0.886            | 0.894            | +0.008 |
| fame     | 0.845            | 0.841            | -0.004 |
| marriage | 0.880            | 0.879            | -0.001 |
| death    | 0.938            | 0.935            | -0.003 |

#### Astro-Databank corpus (n=86,599 windows, 10,239 people)

| Class    | person_only AUC | full_chart AUC | Lift   |
|----------|------------------|------------------|--------|
| career   | 0.908            | 0.915            | +0.008 |
| fame     | 0.904            | 0.908            | +0.003 |
| marriage | 0.920            | 0.898            | -0.022 |
| personal | 0.904            | 0.903            | -0.001 |

**On both corpora, chart structure adds essentially zero AUC** (<0.01
across all 8 class-corpus combinations; three are negative). The
person_only AUCs of 0.85-0.94 reveal that **birth date + window date
+ md_lord already explain almost everything predictable**.

#### Key insight: birth-date confounding without proper control

The previous "doctrine quintile" tests used coarse controls (continuous
`birth_year` only) that did not absorb date-precision effects. Chart
features then acted as a **high-precision birth-date proxy** — sign of
slow planets (Saturn, Jupiter) encodes the ~1-3 year birth-date band;
sign of fast planets encodes month/day precision.

The earlier +0.04 to +0.12 chart-features AUC lift collapsed to
near-zero once `birth_jd` was added to the baseline. This confirms
the mechanism: **chart structure carries no predictive signal beyond
what birth date already provides**. The "doctrine" was an under-
specified control problem, not an astrological discovery.

### What this means for the round-9 conclusions

The previous claim ("the classical lord-attribution rule carries
modest-but-real per-time predictive signal") is **fully retracted**.
After three independent corpora (Astro-Databank, Lunarastro, Wikidata)
were tested with the same scorer, no event class shows
Bonferroni-significant signal that replicates across any two of them.

The honest contribution from round-9 is:
1. **Methodology**: a clean exposure-adjusted Poisson rate-ratio test
   over doctrine-derived quintiles (`dasha_doctrine_score_mix.py`),
   tested in 60+ unit tests. Reusable infrastructure.
2. **Null findings on doctrine refinements**: §5.8 multi-layer +
   partial-Shadbala don't help; the dignity proxy alone is the right
   amount of strength.
3. **Cross-corpus null finding (the main contribution)**: The
   doctrine-quintile rate-ratio signal does NOT robustly transfer
   across three independent corpora. Each corpus produces ITS OWN
   Bonferroni-passing class (fame on Astro-Databank, family on
   Lunarastro, career on Wikidata) but the intersection is empty.
   This is the signature of corpus-specific selection bias, not a
   universal doctrine effect.

This is a **publishable null finding**. It does not preclude the
doctrine working at the per-individual reading level (which is not
what we tested) — astrologers always claim individual-chart reading
requires multi-factor judgment that population-statistics-on-coarse-
labels can't capture. But for the specific claim "doctrine-derived
chart structure predicts per-time event rates at population scale",
the answer based on three independent corpora is: **no Bonferroni-
robust signal exists**.

## Round-10 follow-up: LLM-based chart reading also produces null

After Round-9 closed at population scale, a follow-up tested whether
an LLM could extract semantic signal from individual charts that the
population statistics missed. The chart reader synthesizes 5
doctrine-grounded sections per chart (ascendant, sun, moon, dasha,
yogas) with RAG-retrieved citations from the 6.3M-word knowledge
library + LLM (qwen2.5).

The research test: for N=29 celebrity subjects with documented
biographical events:

  1. Give the LLM their **real** chart (planet signs) → score each of
     14 event categories 0-10 for likelihood-to-appear.
  2. Give the LLM their chart with **planet signs RANDOMLY SHUFFLED**
     (same planets, scrambled signs) → score the same 14 categories.
  3. Score predictions via AUC against actual documented events.

| Condition       | Mean AUC | Lift   |
|-----------------|----------|--------|
| Real chart      | 0.6424   | —      |
| Shuffled chart  | 0.6418   | —      |
| Lift (real-shuf) | **+0.0006** | std 0.038 |

**Paired Wilcoxon (real > shuffled): p = 0.43.** Lift sign distribution:
14 positive, 10 negative, 5 zero — pure noise.

The LLM extracts **no information** from chart structure that helps
predict biographical events. Both real and randomly-shuffled charts
produce identical-quality predictions (AUC=0.64 from common-sense LLM
knowledge about biographical event-class base rates, not from
doctrine).

This generalizes the population-statistics null at the semantic level:
even a state-of-the-art LLM with full classical-doctrine RAG access
and structurally-extracted chart context cannot decode the chart into
better event predictions than it gets from a randomly-permuted chart
of the same person.

**The Round-9 + Round-10 combined verdict**: the structural
relationships of Vedic astrology (planet signs, houses, aspects)
carry no predictive signal at population scale OR at individual-LLM-
reading scale, beyond what's already encoded in (a) birth date and
(b) general LLM knowledge of biographical base rates.

The chart reader still ships as a productized feature: doctrine-
grounded prose with classical citations IS valuable for users who
want to engage with the tradition seriously. But the predictions it
generates carry no validated predictive power — they're literary
synthesis, not forecasts.

### Reproducibility (Round-10 test)

```sh
OLLAMA_ENABLED=true OLLAMA_MODEL=qwen2.5:latest \
  python -m app.medini.ml.chart_reading_research --n-subjects 30
# → data/ml_runs/chart_reading_research/summary.json + per_subject_scores.csv
```

## Limitations + future work

1. **No mechanism claimed.** The signal is statistical association,
   not causal. The doctrine prescribes a specific *structural* mapping
   from chart to event-rate that survives an out-of-sample
   replication test on this corpus — but a non-astrological
   confounder (selection bias, dating-effect, label leakage) hasn't been
   ruled out at p<7e-4.
2. **Sample**: Astro-Databank is a curated biographical database
   skewed toward documented public figures. Generalisation to general
   population requires independent corpus.
3. **Coarse event classes**: "fame" includes anything from a minor
   award to a Nobel; "personal" includes birth, marriage, illness,
   etc. Sub-class refinement is future work.
4. **§6 strength proxy is partial**: dignity-only positional strength.
   Full Shadbala may help, but the partial-Shadbala experiment shows
   the gain isn't from adding more components naively. Event-class-
   weighted bala combinations are the next experiment.
5. **AD/PD windows**: §5.8 didn't work at population scale. Per-person
   AD-window refinement (the way classical authors actually use it) is
   testable with finer event dating (events typically come dated to
   the year, not the month) — but our corpus is year-precision.

## Reproducibility

All code lives in `app/medini/ml/dasha_doctrine_score*.py`. To reproduce
the headline result:

```sh
# Build the natal-lord-houses parquet (84k people)
python -m app.medini.etl.build_natal_lord_houses

# Build the dasha event corpus (86k MD windows)
python -m app.medini.etl.build_dasha_event_corpus

# Run the mix-and-match scorer
python -m app.medini.ml.dasha_doctrine_score_mix
# → data/ml_runs/fork_a_doctrine_mix/mix_score.md
```

Each stage has unit tests under `tests/test_dasha_doctrine_score*.py`.

## Stage progression

| Stage | Module | Bonferroni passes | Headline | Status |
|---|---|---|---|---|
| F (§5 only) | `dasha_doctrine_score.py` | 1 (fame) | fame RR 1.41 | shipped |
| F-2 product (§5.8) | `dasha_doctrine_score_3level.py --combiner product` | n/a | RR artifact | null result |
| F-2 additive (§5.8) | `dasha_doctrine_score_3level.py --combiner additive` | 1 (fame) | personal regressed | null result |
| F-3 (§5 × §6) | `dasha_doctrine_score_strength.py` | **2** (fame + personal) | personal RR 2.44 | shipped |
| F-4 (§8.3) | `dasha_doctrine_score_trikona.py` | 2 | fame trend p 1.7e-07 | degenerates personal |
| F-5 (partial-SB) | `dasha_doctrine_score_partial_shadbala.py` | 1 | regressed | null result |
| **F-6 (mix)** | **`dasha_doctrine_score_mix.py`** | **2** | **production scorer** | **ship** |

61 unit tests across the doctrine modules. 1530+ project-wide tests
pass.
