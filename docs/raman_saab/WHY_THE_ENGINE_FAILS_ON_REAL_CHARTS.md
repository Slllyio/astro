---
title: "Root-cause analysis — WHY the engine fails on real-life charts"
kind: analysis
topic: validation
measured: true
updated: 2026-07-24
words: 1759
tags: [raman-saab, analysis, validation]
---
# Root-cause analysis — WHY the engine fails on real-life charts (2026-07-24)

> The astrobank program returned null on real outcomes. "The doctrine doesn't generalize" is only
> the LAST acceptable explanation — this document records the systematic elimination of every
> mechanical alternative, each with direct evidence. The chain was dug until only one link remained.

## The suspects, each tested and eliminated

### 1. "The charts are cast wrong" (data / tz / LMT / houses) — ELIMINATED, external answer key
The wayback records embed **AstroDatabank's own computed placements** (Sun/Moon/Asc sign+degree)
for 23,741 charts — an external answer key covering the entire pipeline (date, time, tz convention,
coordinates, house math). Audit on 1,500 tier-A/B charts through OUR pipeline (sidereal→tropical):

- **Sun sign: 100.0% match. Moon sign: 99.9%. Ascendant sign: 96.7%, median degree error 0.5°**
  (the 3.3% misses are cusp-proximity; only 0.7% are >30° — stray data errors).

The charts are right. The failure is not astronomy, not tz, not birth data.

### 2. "We asked the wrong question" — CORRECTED, then still null
The cohort-AUC question was provably wrong (near-constant verdict instrument on ordinary charts;
rare-conditional dilution — see REAL_OUTCOME_GENERALIZATION.md Stage 6). The corrected questions —
each classical combination as its own conditional claim (91 tests), the doctrinal death-window
instrument, and the full engine-vs-reality matrix (16,450 persons × 56 significations × 23 reality
features) — all still return null. Diagonal specificity 0.0197 vs off-diagonal 0.0164.

### 3. "The verdict synthesis (`_decide`) destroys the signal" — BYPASSED, still null
The raw doctrinal evidence stream itself — the balance of malefic-vs-benefic rules firing per
signification, before any synthesis — was tested directly against the paired outcomes:

| outcome | raw-evidence AUC |
|---|---|
| childless vs prolific | 0.485 (wrong direction) |
| divorced vs long-married | 0.496 |
| bankrupt vs wealthy | 0.408 (wrong direction) |
| prison | 0.518 |
| suicide | 0.536 (the persistent thread) |

The rules' collective firing does not distinguish the outcomes. Nothing for a better synthesis to
recover: **the failure is upstream of `_decide`.**

### 4. "The rules are out-of-domain on ordinary charts" (regime shift) — NONE EXISTS
Fire rates of the 112 outcome-linked evaluable rules, Raman's curated golden charts vs 16,450 real
charts: **malefic rules 0.061 vs 0.065; benefic 0.111 vs 0.111.** The rules behave identically on
book charts and on humanity. (The verdict layer's over-affliction on ordinary charts — children 76%
afflicted — is therefore a synthesis-weighting property, and irrelevant anyway per #3.)

### 5. "The test machinery is biased" — CONTROLS VALID BOTH WAYS
The sham mapping returned AUC 0.500 exactly (no fake negatives are being manufactured), and the
cross-chart age-aligned null CAUGHT the one fake positive (death-window containment: own-chart
0.323 vs other-people's-charts 0.324). The machinery neither hides signal nor invents it.

## The one remaining link — the actual root cause

The engine's 89% golden fidelity means: **given a chart, the engine reliably predicts what B.V.
Raman would say about it.** That skill is real, externally validated (#1), and unchanged on real
charts (#4). The astrobank program then measured the second link — between *what Raman would say*
and *what actually happens* — on 16,450 real lives, 22 reality features, 91 classical conditionals,
and dated death timing. That link tests null everywhere.

**The engine does not fail at its job. Its job — faithfully reproducing Raman's system — is done
and proven. What fails to appear is the doctrine's claimed correspondence with reality.** The
chain is: engine → Raman (strong, 89%) → reality (null, n=16,450). The broken link is the second
one, and no amount of engine improvement can mend it, because the engine's target IS the first link.

## What survives (the honest residue)

1. **Suicide ↔ afflicted 8th (death-manner)** — the ONE channel that behaves as doctrine predicts,
   found independently by three designs (cohort AUC 0.535 perm p=.005; specificity rank 1/56 in the
   matrix; raw-evidence 0.536). Small, uncorrected-for-selection, but persistent. The single
   candidate for a dedicated confirmatory pre-registration on an independent corpus slice.
2. **The population over-affliction finding** (children 76%/incarceration 65%/death 72% afflicted on
   random people) — a real engine property, invisible to the golden corpus, now quantified. Relevant
   if the engine is ever used to read ordinary charts for people (calibration lead; golden-ratchet
   sovereignty governs any change).
3. **The infrastructure** — a verified-correct casting pipeline (96.7% external agreement), a 22k
   feature store, and the paired engine-vs-reality matrix, all reusable for any future hypothesis at
   query cost.

## Method note

Every elimination above used direct evidence, not argument: an external answer key (#1),
pre-registered re-tests (#2), an instrument bypass (#3), a measured distribution comparison (#4),
and dual-direction controls (#5). This is the Prime Directive's "measure honestly" applied to the
question "why did it fail" — the answer is not a guess.

---

# LEVEL 2 (2026-07-24) — why the DOCTRINE itself fails: the measured mechanism

Level 1 located the broken link (Raman → reality). This level answers the deeper question: **why
does a system that feels overwhelmingly true to its practitioners — and validated itself for Raman
on his own cases — predict nothing?** Four classical defenses are closed empirically, and then the
mechanism itself is measured.

## The four defenses, each closed with data already in hand

1. **"Birth times need rectification; recorded times aren't true times."** Closed twice over:
   (a) minute-precision birth-certificate charts (tier A) test IDENTICALLY null to round-hour ones
   (mean AUC 0.500 vs 0.496); (b) the Stage-10 direct tests used **time-insensitive features** —
   the Moon's sign holds for ~2.2 days, Saturn's aspect on it for months, Mars-from-Moon for days —
   features immune to any plausible birth-time error *and* to every ascendant/house question. They
   null too (OR 1.13, 1.09, 0.92). No rectification argument survives features that don't depend on
   the birth time. (Rectification as practiced — adjusting the time until the chart fits the life —
   is the flexibility mechanism below, formalized.)
2. **"The chart works as a WHOLE; single factors can't capture it."** The engine's verdict IS the
   whole-chart synthesis — three pillars, yogas, vargas, aspects, exactly Raman's integration — and
   it nulls. ML models given every ledger feature at once null. The 56×23 diagonal test nulls. The
   holistic reading was tested *as a whole* and in parts; the defense is closed unless "holism"
   means something no encoding could contain — which is unfalsifiable, i.e., not a claim.
3. **"The chart only PROMISES; the dasha DELIVERS — static labels miss the timing."** Timing was
   tested on its own terms: within-chart control dates against significator windows and maraka
   periods, at MD and AD level, with the span-anchored death_window. Null, with the one apparent
   positive exposed as pure age-structure (chart-specific excess −0.001).
4. **"Celebrities are an unrepresentative population."** All primary contrasts are within-corpus
   (divorced celebrities vs long-married celebrities — same selection process on both sides), the
   sham stayed exactly null, and strata controlled era/geography.

## The mechanism, measured: unbounded explanatory flexibility

Across 22,177 real charts, judged on all 56 significations by Raman's own integrated method:

- the **median chart simultaneously carries 19 afflicted AND 31 favourable significations**;
- **98.5%** of charts hold at least 5 of each; **86.8%** hold at least 10 of each;
- **97.1%** of humanity has, at every moment, BOTH an afflicted house and a favourable house
  available in the same chart.

This single measurement explains both halves of the paradox:

- **Why the system always *feels* true:** whatever happens in a life — divorce, riches,
  childlessness, prison, early death — a supporting indication exists in essentially *every*
  chart. A retrospective reading can never fail. Raman, reading the biography of a man he knew to
  be childless, had an afflicted indication available 76% of the time by our census — and where
  the 5th was clean, the doctrine supplies sanctioned alternates (Beeja/Kshetra, the karaka, the
  7th from the 5th, the navamsa…). The reading always lands. The conviction is sincere, and
  structurally guaranteed.
- **Why it can never predict:** the same abundance means the indications are not *differential*.
  An indication present in nearly everyone distinguishes no one. Prediction requires the sign to
  be present when the outcome is coming and absent when it is not — and that difference, measured
  every way the doctrine itself would choose, is zero.

The Failure Atlas's "saturation" finding was not a bug in our engine after all — it is the
doctrine's own architecture surfacing: rules generous enough to explain any life are exactly the
rules that cannot predict one.

## The curation asymmetry (why Raman's books validate at 89% while reality nulls)

Three already-established numbers combine into the answer: (a) the rules fire at IDENTICAL rates
on Raman's book charts and on random humanity (0.061 vs 0.065 — his charts are not astronomically
special); (b) the engine predicts his verdicts from his charts at 89% (his verdict process was
consistent and rule-shaped); (c) those same verdicts null against reality at scale. The resolution:
**his books are a gallery of agreement** — nativities selected, among the flexible abundance of
indications, precisely because doctrine and known biography could be shown aligning. The charts
where they clash (the statistical majority, per our nulls) could not become clean worked examples.
This is not an accusation of dishonesty; it is what sincere practice under unbounded flexibility
produces automatically — every practitioner's case file fills itself with confirmations.

## What still glimmers (recorded, not claimed)

The faint structure clusters in ONE region and nowhere else: death-manner and the afflicted mind.
Suicide → afflicted 8th replicated in effect size on held-out data (0.535 → 0.528, p=.062,
underpowered); Saturn on the Moon carries what little there is (OR 1.13) while Mars carries
exactly nothing (OR 1.00 — the specificity doctrine predicts); the waning Moon amplifies (OR 1.23,
p=.08). All below threshold, all pre-registered, all honestly unresolved. If the tradition retains
a grain of differential truth anywhere in this corpus, it is here — small, dark, and unconfirmed.

## The complete answer, in three sentences

The engine does not fail: it reproduces Raman at 89%, on verified-correct charts, with rules firing
exactly as they do in his books. The doctrine fails to predict because its indications are
non-differential by construction — present in abundance in every chart, they can explain
everything and therefore foresee nothing — and its historical validation was the curated residue of
that same flexibility. What survives is one small, twice-seen, never-confirmed thread at the 8th
house and the darkened Moon, and an instrument that now, uniquely among its kind, tells the truth
about itself.


> Per-case atlas — WHERE it fails, house by house, with named lives: [FAILURE_ATLAS.md](FAILURE_ATLAS.md)
