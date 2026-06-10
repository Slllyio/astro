# Does Vedic dasha astrology leave a measurable footprint in real life events?

**A pre-registered, permutation-controlled audit on 17,912 dated life events.**

*Run: `lunarastro_dignity` · corpus: LunarAstro/Astro-Databank export · see
`SYNTHESIS.md` for the full 11-finding detail.*

---

## TL;DR

Across 11 findings and a 103-hypothesis FDR-corrected battery, **most classical
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

## Three caveats that shape every claim

1. **Valence is circular.** The Beneficial/Adverse label is ~deterministic from
   `event_class` (career 97% beneficial, death 0%), so "predict benefit" ≈
   "predict class". This is why the dignity findings, though real, mean *"good
   periods bring good-class events"* — not *"a given event turns out better"*.
2. **Single corpus.** Replication here is internal (split-half); a truly
   independent dataset is the outstanding gold-standard step.
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

A genuine, modest, **chart-specific** signal exists — the 7th-lord Mahadasha
times marriage — and it survives every control we threw at it. The grander
edifice of dasha significator timing, dignity-determined fortune, and varga
refinement does **not** leave a footprint distinguishable from chance and data
labelling on this corpus. That is a useful, falsifiable map of where the
signal is.
