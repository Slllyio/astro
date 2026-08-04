---
title: "An Engine and a Verdict: encoding B. V. Raman's Vedic astrology faithfully, then testing it against 22,000 real lives"
kind: record
topic: doctrine
measured: true
updated: 2026-08-03
words: 2101
tags: [raman-saab, record, doctrine]
---
# An Engine and a Verdict: encoding B. V. Raman's Vedic astrology faithfully, then testing it against 22,000 real lives

*The capstone record of the raman_saab program — 2026-07-24.*

---

## Abstract

We built the most faithful digital encoding of Sri B. V. Raman's Parashari-natal system in
existence — 845 doctrine rules and 72 yogas, each carrying a verbatim citation to his texts, an
integrated house-judgment engine, numeric Ayurdaya longevity, Vimshottari/maraka timing — and
verified it two ways: against Raman's own published verdicts (**259/293 = 88.4% exact,
283/293 = 96.6% within one ordinal step**, with the ceiling proven un-improvable by five
independent methods) and against external astronomy
(ascendants agree with AstroDatabank's published placements at 96.7%, median error 0.5°). We then
did what the system's own author demanded — Raman: *"the purely mathematical methods... must be
applied to thousands of horoscopes"* (HTJAH-II:3937-3943) — and tested the encoded doctrine
against **22,177 Rodden-rated real charts with 47,466 dated life events**, under a pre-registered,
sham-gated, doctrine-reviewed protocol. The result is a convergent null: house verdicts, raw rule
evidence, all 91 outcome-linked classical conditionals, dasha and maraka timing, and the doctrine's
own primitives tested directly on chart geometry (Kuja dosha vs divorce; Saturn-afflicted Moon vs
suicide) show no chart-specific correspondence with real outcomes. The mechanism of the paradox —
a system that feels overwhelmingly true yet predicts nothing — was then measured: **the median
chart simultaneously carries 19 afflicted and 31 favourable significations**, indications abundant
enough to explain any life retrospectively and therefore non-differential prospectively. A second,
methodologically independent program — the medini machine-learning pipeline, which threw a
193-feature "Vedic tensor" and a composite astrologer's-lens framework at the same charts across
twelve rounds — reached the same null, and its three apparent survivors were then put through a
pre-registered *Survivors' Gauntlet*: all three fell (a marriage "signal" that was a birth-place
confound; a career "signal" that was a cohort-composition artifact; and the suicide thread, which
weakened rather than confirmed on a third, enlarged sample — 0.535 → 0.528 → 0.515). Every claim
below is reproducible from committed code and pre-registrations.

---

## Part I — The instrument

**Goal (the Prime Directive):** encode Raman's system with maximal fidelity — every rule cited to
his texts (*How to Judge a Horoscope* I/II, *Hindu Predictive Astrology*, *Three Hundred
Combinations*, *Graha and Bhava Balas*, *Notable Horoscopes*), verified against his worked
nativities, never against engine self-output.

**Architecture highlights.**
- 845 `RuleRecord`s + 72 `YogaRecord`s, each with `Citation(work, line)` resolved against the
  on-disk corpus by CI (a fabricated citation cannot survive).
- The three-pillar house judge (`judge_house`): bhava, lord, karaka — with Shadbala strength,
  navamsa confirmation, decisive-rule mechanics, yogas, and Raman's own exception structure.
- Numeric Ayurdaya (Pindayu/Amsayu + haranas) validated to the day against Raman's Charts 33/34;
  Vimshottari to pratyantar level; maraka death-windows; Gochara with Vedha.
- **The golden ratchet:** 293 confirmed verdicts extracted from Raman's books; accuracy may never
  regress; every re-base is a human, reasoned act recorded in a lineage log.

**Fidelity result: 259/293 = 88.4% exact, 283/293 = 96.6% within one ordinal step.** (Was
261/293 = 89.1% exact / 281/293 = 95.9% within-1 until 2026-08-03, when enabling the B1
dominant-factor guard deliberately traded 2 strict matches for 2 fewer favourable↔afflicted
inversions — real errors 12 → 10. See `DOCTRINE_BACKLOG` B1.) The ceiling
was then *proven*: the placement-discriminator harvest is exhausted (a systematic scan of every
miss-signification found no clean rule left), the karaka frames over-fire, a bounded threshold
tuner finds no improving configuration (holdout-locked, twice, on 5× data), the residual misses
share no citable pattern, and machine-learned judges trained on the same evidence lose to the
hand-tuned engine by 12–29 points of holdout accuracy. The remaining 11% is Raman's contextual
weighing — irreducible without overfitting to his examples, which the directive forbids.

**Astronomy verified externally:** for 1,500 charts, our pipeline agrees with AstroDatabank's own
published placements — Sun 100%, Moon 99.9%, ascendant 96.7% (median 0.5°).

## Part II — The laboratory

The AstroDatabank corpus (local, gitignored): 61,583-person master taxonomy + auxiliary sources,
resolved to 64,644 celebrity records through mojibake repair, name-convention normalization,
deterministic conflict ranking, and quality tiers (A = AA-rated + minute-precision; noon-default
births excluded outright). Spot-check gates caught and fixed two real ingestion bugs (wrong-source
times displacing canonical ones — Einstein restored to his certificate's 11:30). Events: 47,466
dated life events joined on corpus-unique names; contradiction quarantine applied.

**Protocol (pre-registered before any scoring):** a doctrine-reviewed category→house mapping
(bphs-reviewer verified every citation; three tempting mappings *rejected* for
selection-on-the-dependent-variable); a sham mapping that must test null before any real result is
read; off-target specificity matrices; within-stratum permutation nulls; BH correction;
minimum-effect thresholds; governance locking astrobank results out of engine tuning forever.

The verdict feature-store: all 12 houses × all significations judged for 22,177 charts (67 ms per
chart, 3.9 minutes total), byte-identical on recast — every downstream question became a query.

## Part III — The results

| test family | headline | verdict |
|---|---|---|
| Sham (expatriate→children) | AUC 0.500 (0.473–0.525) | pipeline valid — nulls are real |
| House verdicts vs 9 outcome cohorts | AUCs 0.475–0.535 | null; prison & military INVERTED |
| Full engine-vs-reality matrix (56 sigs × 23 features, 16,450 people) | diagonal 0.0197 vs off-diagonal 0.0164 | no matched-signification structure |
| Raw rule evidence (bypassing the judge) | childless 0.485, wealth 0.408 | null upstream of synthesis |
| 91 classical conditionals (each combination as its own claim) | 0 survive BH | the combinations do not validate |
| Dasha timing (within-chart control dates; the valid instrument: primary-maraka AD, coverage 0.34) | lift −0.007 (n=2,377 deaths) | null; the one apparent hit (span-anchored windows, +0.208) was pure age-structure: cross-chart containment identical (−0.001 excess) |
| Ayurdaya capacity vs realized span | AUC 0.502 | null |
| **Direct doctrine tests (Stage 10, pre-registered):** Kuja dosha vs divorce; Saturn-Moon vs suicide | OR 1.09 (p=.18); OR 1.13 (p=.16) | null on raw chart geometry — immune to every engine-layer critique |
| **Confirmatory: suicide → afflicted 8th (held-out n=218)** | AUC 0.528 vs predicted 0.53; p=.062 | direction + effect size replicated; NOT confirmed (underpowered; needs ~500 cases) |

Excuses eliminated with data: birth-time noise (tier-A ≡ tier-B ≡ null; time-insensitive features
null too), holism (the full synthesis IS holistic and nulls; ML on all features nulls), timing-
context (tested on its own terms), population selection (within-corpus contrasts; exact-null sham),
regime shift (rules fire at 0.061 on Raman's charts vs 0.065 on humanity — identical).

## Part IV — The second witness: the medini ML program and the Survivors' Gauntlet

The astrobank program tested Raman's *encoded doctrine* directly. Running beside it, an independent
effort — the **medini** pipeline — asked whether *machine learning* could find in the same charts
what the doctrine could not. It built a 193-feature "Vedic tensor" (planetary dignities, house
occupancies, yoga flags, dasha state) and a composite "astrologer's-lens framework" of
multi-condition AND-gate verdicts, and ran twelve rounds of population-scale prediction. Its
headline was the same null, and taught the same lesson from the other side: the strongest apparent
result — death-age AUC 0.81 — **collapsed to 0.50–0.61 the moment it was stratified by birth era**,
because slow-planet longitudes silently encode the birth decade and the corpus's death dates are
bounded by scrape year. What looked like astrology was a calendar.

Between the two programs, twelve-plus rounds left exactly **three positives that outlived their
first tests**. An independent ML audit (`docs/medini/ML_AUDIT_2026-07-24.md`) found the pipeline's
recurring leaks — row-level splits on multi-row-per-person corpora, era-truncation in the death
regressor, name-as-key joins — and defined exactly what a clean re-run must fix. Each survivor was
then re-tested under a pre-registered maximum-rigor protocol, directions and success criteria
locked before computation:

| lane | exploratory claim | clean re-run | result |
|---|---|---|---|
| **G2** — WD marriage chart-lift | +0.043 AUC over a cyclic-date baseline ("REAL SIGNAL") | added a **geography** arm; all 32,932 charts are default-time, so chart columns only re-encode birth *place* | **falls** — geography alone worth +0.107; charts add −0.0026 with lat/lon present (CI excludes 0) |
| **G1** — framework career→10H | lift **1.37** on 11,753 events ("first project-wide positive signal") | same machinery on both arms; each event vs the **same person** at year-shifted control dates | **falls** — paired lift **1.000** (CI 1.000–1.000); **0 of 11,626** events changed label at any control date |
| **G3** — suicide → afflicted 8th | 0.535 exploratory, 0.528 held-out (p=.062) | enlarged never-tested sample (+29 fresh casts, n=247) | **weakens** — 0.515, p=.198; fading across three looks |

The two falls are instructive because each is a *named* artifact, not a mere failure to replicate.
**G1's** verdict label was proven date-invariant by construction: `reading_composer` derives it from
the natal bhava alone, while transit and dasha context only set a *separate* `gochara_triggered`
flag (`reading_composer.py:142`) — so the "event" and "control" readings are identical for a person
on every date, and the 1.37 was entirely cohort composition (career-cohort people carry a natal 10H
strong-rate 1.41× the population, driven by the corpus's 77% Wikidata mix). **G2's** +0.043
replicated exactly and then dissolved into birth-place documentation bias. Different program,
different tools, same verdict: **no chart-specific correspondence with real outcomes survives an
honest control.**

## Part V — The mechanism

Why does a system that feels true to millions predict nothing? Measured, not argued:

> Across 22,177 charts judged by Raman's complete method, the **median chart carries 19 afflicted
> and 31 favourable significations at once**; 98.5% of charts hold ≥5 of each; **97.1% of humanity
> has both an afflicted and a favourable house available at every moment.**

Whatever happens in a life, a supporting indication already exists in essentially every chart — so
every retrospective reading lands, and sincere conviction is structurally guaranteed. But an
indication present in nearly everyone distinguishes no one — so prospective prediction is
impossible. The same architecture produces both the felt truth and the measured null.

And the curation asymmetry closes the loop: Raman's book charts are astronomically ordinary (rule
fire-rates identical to the population), his verdicts are 89% rule-predictable, yet those verdicts
null against reality — **his books are a gallery of agreement**, the automatic residue of sincere
practice under unbounded flexibility.

## Part VI — What stands at the end

1. **The scholarly instrument.** A verified, ratcheted encoding of Raman's system that answers
   "what would Raman say about this chart" at 89% — of genuine value to the study of the tradition,
   and preserved exactly.
2. **The self-honest overlay.** The population-calibration layer makes every reading disclose its
   own information content ("this reading is shared by 72% of humanity"; "this channel is proven
   inverted") — to our knowledge the only astrology engine that tells the truth about itself as it
   speaks.
3. **The laboratory.** 22k verified charts, the failure atlas, the paired engine-reality matrix,
   and pre-registered machinery that turns any future hypothesis into an afternoon's query.
4. **The Survivors' Gauntlet.** Across both programs, the only three findings that ever outlived
   their first test were re-run under pre-registered maximum rigor — and all three fell (two to
   named artifacts, one to a weakening trend). The null is not the absence of a signal we failed to
   find; it is a signal we chased down three times and watched dissolve.
5. **The open thread.** Suicide and the afflicted 8th — now thrice seen and *fading* (0.535 → 0.528
   → 0.515), never confirmed, honestly parked with its pre-registered study
   (`confirmatory_study.py`) awaiting a genuinely large independent sample that does not yet exist.
6. **The verdicts, side by side, never averaged:**

> **Fidelity to Raman: 88.4% exact / 96.6% within one ordinal step — proven and ceilinged.**
> *(The ceiling is permanent — five independent methods proved it un-improvable. Where the line
> falls BETWEEN "exact" and "within one step" is a deliberate, recorded trade: on 2026-08-03 the
> B1 dominant-factor guard gave up 2 strict matches to remove 2 favourable↔afflicted inversions.
> The number moved; the ceiling did not.)*
> **Correspondence with reality: null everywhere tested, by two methodologically independent
> programs, by the doctrine's own preferred questions, with every apparent survivor chased down and
> with controls honest in both directions.**

## Provenance

Canonical detail: `REAL_OUTCOME_GENERALIZATION.md` (results, including the three Gauntlet lanes),
`WHY_THE_ENGINE_FAILS_ON_REAL_CHARTS.md` (root cause, two levels), `FAILURE_ATLAS.md` (per-case),
`tools/raman_saab/astrobank/METHODOLOGY.md` + `CONFIRMATORY_PREREG.md` + `GAUNTLET_PREREG.md`
(protocol, pre-registrations), `docs/medini/ML_AUDIT_2026-07-24.md` (the second program's leak
audit) with the clean re-runs in `app/medini/ml/gauntlet_g1_career.py` and `gauntlet_g2_marriage.py`,
and the golden-ratchet lineage in `tests/fixtures/golden_accuracy_baseline.json`. All results
reproduce from committed code; the corpus stays local. The Prime Directive's last clause — *measure
honestly, report both* — is the sentence this document exists to obey.
