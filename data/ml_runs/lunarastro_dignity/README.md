# Does Vedic dasha astrology leave a measurable footprint in real life events?

**A pre-registered, permutation-controlled audit on 17,912 dated life events.**

*Run: `lunarastro_dignity` · corpus: LunarAstro/Astro-Databank export · see
`SYNTHESIS.md` for the full 17-finding detail.*

---

## TL;DR

Across 17 findings and a 103-hypothesis FDR-corrected battery, **most classical
dasha-timing doctrine shows no detectable signal** on this corpus. Two things
survive honest, non-circular testing:

1. **The 7th-lord Mahadasha times marriage** — chart-specific, age-robust,
   replicated across all 6 disjoint sub-samples (lift ≈1.15, z=2.28, p≈0.01).
   *The* clean result. Corroborated independently by event-age (stronger 7th
   house → earlier marriage, ρ=−0.06, p=0.04).
2. **A benefic/malefic-period → event-class coincidence** — Jupiter periods
   coincide with auspicious-class events (relationship/family/career), Saturn
   with death. Statistically strong but *not* precise significator timing (see
   caveat 3).

Everything else — the dignity→benefit gradient, natural benefic/malefic nature,
domain "promise", D9 navamsa refinements, and the broad house-lord→class rules —
is either a **null** or an **artifact of how the data is labelled**.

3. **Why astrology *feels* accurate (Finding 12).** Tested the way a jyotishi
   actually reads a chart — the disjunctive union of significators (7th-lord
   *or* Venus *or* 2nd/11th-lord *or* aspecting planet…) across MD *and* AD —
   the classical dictums "hit" **76–90%** of real events. But that equals
   **chance** (lift ≈ 1.00): a ~5-of-9-planet set read over two dasha levels is
   running ~83% of the time by construction. The rules are near-unfalsifiable,
   which is precisely how the system can feel reliable for millennia while
   adding no skill over naming the same number of planets at random.

4. **The steelman also fails (Finding 13).** Tested as *convergence* — scoring
   each life-period by how many independent dictums agree (0–6) and predicting at
   the **peak**, the way an astrologer cross-infers — events do **not** cluster
   in high-confluence periods. Dose-response is flat (marriage: rate 11.1 at
   0 dictums vs 10.2 at 6), and the within-person peak percentile sits at **0.50
   = chance** for marriage, career, and death. Even astrology's best-practice
   method carries no timing signal here, because the one real factor is too weak
   and the rest are noise that dilute it.

5. **The verses, verbatim, still fail — and they settle an old dispute
   (Finding 14).** A verse-level sourcing pass (70 dictums with chapter/verse;
   `dictum_catalog_v2.md`) let us test Parashara's *actual* mechanism — the bhukti
   lord's position **counted from the dasha lord** (PD 20.29) — for the first
   time: null (lift 1.01, p=0.54). And it adjudicates a real schism: Phaladeepika
   says the 7th-lord's period *gives marriage*; BPHS says the 7th-lord is a
   *maraka* (killer). On 1,750 marriages and 2,695 deaths, the 7th-lord period
   lifts **neither** (0.95 and 0.98) — both classical schools are wrong here. The
   only surviving whisper is that a *well-dignified* benefic sub-period lifts
   events ~1.09× (p=0.14): faint, not significant, but the same *strength* signal
   Findings 8–10 found — suggesting whatever little is real is about planetary
   **dignity**, not which significator is named.

6. **Chasing that whisper to ground — pre-registered (Finding 15).** A two-stage,
   person-split, permutation-controlled test of the strength effect. The discovery
   half independently re-selected the **exact classical conjunction** — a benefic
   that is well-dignified *and* well-placed from both the Lagna *and* the dasha
   lord (the simpler "dignity alone" / "good house alone" versions are flat). The
   held-out half replicates it **in direction and size** (lift 1.08) but
   **cannot confirm it** (p=0.18) — the design is underpowered for an effect this
   small (80% power needs lift ≥1.21; the truth is ~1.1). Full-corpus one-sided
   p=0.03. **This is the honest terminus**: the dignity/strength effect is the
   single non-null survivor of the whole arc — real-but-tiny, the specific
   conjunction the texts prescribe, sitting right at the edge of what 17,912
   events can resolve. We can neither kill it nor claim it; it would take a corpus
   several times larger to settle.

## Corpus & method

| | |
|---|---|
| natives (sidereal D1 + Vimshottari) | 3,779 |
| dated events joined to active MD/AD | 17,912 |
| event classes | career, death, marriage, family, health, relationship, education, divorce, personal, other |
| nulls | chart-shuffle permutation (age-robust), measured dasha-exposure, FDR (Benjamini-Hochberg) |

**Core methodological discipline:** never trust a raw association. Each claim is
tested against a null that holds the confounds fixed — and multiple comparisons
are FDR-controlled.

## The findings, one line each

| # | Question | Verdict |
|---|---|---|
| 1 | Which lord runs ↔ which event class | Strong, sensible associations |
| 2 | Age/recording effect on outcome valence | Large — dominates valence |
| 3 | Dignity × life-stage → benefit (MD+AD pair, prime) | +0.21 gradient, **survives chart-shuffle** (p≈0.003) |
| 4 | Anatomy of that gradient | Carried by Jupiter/Mercury; **reverses for the Sun** |
| 5 | Robustness + split-half replication | Holds vs label-noise, event-clustering, disjoint halves |
| 6 | Natural benefic/malefic & 45 chart features | Benefic/malefic **flat**; nothing survives Bonferroni |
| 7 | Promise vs timing | **Valence ≈ event_class** → Findings 3–6 are a *class-coincidence*, not within-class outcome |
| 8 | Non-circular targets (timing + age) | **7th-lord times marriage**; chart strength → marriage age; longevity null |
| 9 | Marriage deep-dive + multiclass ceiling | It's the 7th-lord **MD** (not AD, not 2/11); house-lord→class directionally right but aggregate null |
| 10 | Does the Navamsa (D9) sharpen marriage timing? | **No** — D1 7th-lord stays strongest |
| 11 | 103-claim battery, FDR-corrected | 4 survive, all karaka-exposure → the benefic-period→class coincidence; marriage←7th-lord leads the age-robust family |
| 12 | Classical dictums tested the astrologer's way | Hit 76–90% — but **= chance** (lift ≈1.00); near-unfalsifiable by construction. Mangal Dosha → no divorce link |
| 13 | Convergence model (count agreeing dictums, predict at peak) | **Flat** — event rate independent of confluence; within-person peak percentile = 0.50. Even the steelman is null |
| 14 | Verses encoded verbatim, 2 schools separated, exposure-controlled | **Null** — PD 20.29 from-MD-lord frame lift 1.01 (p=0.54); "7L→marriage" lift **0.95**, "7L=maraka→death" lift 0.98 (both fail); only whisper = benefic-AD *strength* lift ~1.09 (p=0.14) |
| 15 | Pre-registered split-half confirmation of the strength whisper | **Inconclusive-but-alive** — out-of-sample lift **1.08** (p=0.18, underpowered: needed ≥1.21); full-corpus lift 1.11 (1-sided p=0.03). The single non-null survivor — real-but-tiny (~10%), the exact classical conjunction, at the edge of detectability |
| 15b | The whisper in practitioner metrics (SCCS rate ratio; C-index) | **Dissociates** — IRR 1.13 (CI 0.998–1.29) but C-index **0.503**: a faint rate shift with zero ability to *point at* the period. Death also lifts 1.11 (not auspicious-specific) |
| 15c | Astrology scored as a forecaster (proper scores vs age base-rate) | **Calibrated but empty** — log-skill −0.0005, ≈0 bits gained, ECE 0.0014: calibrated only because the forecast reduces to the actuarial age table |
| 16 | The transit trigger (Jupiter-trine, Rao double transit), alone & joint with dasha | **Null** — verse-faithful joint rule lift **1.002** (p=0.97); every trigger 0.91–1.05. The two-stage "double confirmation" adds nothing |
| 17 | BPHS 18.22–34 fixed-age marriage tables | **Null** — natives matching "marry at 5/9" yogas marry at mean age **29**, same as everyone; the tables encode the child-marriage customs of their era |

## Three caveats that shape every claim

1. **Valence is circular.** The Beneficial/Adverse label is ~deterministic from
   `event_class` (career 97% beneficial, death 0%), so "predict benefit" ≈
   "predict class". This is why the dignity findings, though real, mean *"good
   periods bring good-class events"* — not *"a given event turns out better"*.
2. **Single corpus.** Replication here is internal (split-half); a truly
   independent dataset is the outstanding gold-standard step — the confirmatory
   protocol is frozen in `replication_preregistration.md` (needs ≥ ~9,000
   auspicious first events to resolve IRR 1.10 at 80% power).
3. **The karaka survivors are not age-deconfounded** and are non-specific
   (Jupiter lifts several good classes; Venus fails to lift marriage), so they
   read as a benefic-period effect, not karaka-to-domain timing.

## Reproduce

All analyzers are deterministic Python modules under `app/medini/ml/` (+
`app/medini/etl/build_d9_charts.py`), each with a focused `tests/` file and a
markdown report in this directory. Rebuild any finding with, e.g.:

```bash
python -m app.medini.ml.dasha_hypothesis_battery --data-dir <run> --out <here> --k 1000
```

## Bottom line

Every pillar of the classical timing method has now been tested **on its own
terms**: single significators (null), the disjunctive dictums as astrologers
state them (hit 76–90% = exactly chance), convergence/weight-of-evidence
(flat), the verses verbatim including Parashara's from-the-dasha-lord mechanism
(null), the fixed-age tables (era custom, not law), and the dasha+transit
"double confirmation" — the heart of practice — at exposure-level chance
(joint-rule lift 1.002). Scored as a forecaster with proper scoring rules,
astrological timing is **calibrated but empty**: it reduces to the actuarial
age table, adding ≈0 bits.

Two residues survive. The **7th-lord Mahadasha → marriage** association
(lift ≈1.15) is real, modest, chart-specific, and age-robust — the one clean
positive. And a **strong-benefic sub-period rate whisper** (IRR 1.13, CI
grazing 1) persists at the edge of detectability, but confers **no ranking or
forecasting skill** (C-index 0.50, 0 bits) and is not auspicious-specific —
its confirmation or burial awaits the pre-registered external replication.

The map is now complete and falsifiable: on 17,912 dated events, Vedic dasha
timing does not predict *when* life events happen beyond a person's age —
and we know precisely where the two faint exceptions sit and what it would
take to settle them.
