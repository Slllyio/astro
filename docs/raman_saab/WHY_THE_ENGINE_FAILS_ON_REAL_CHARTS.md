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


> Per-case atlas — WHERE it fails, house by house, with named lives: [FAILURE_ATLAS.md](FAILURE_ATLAS.md)
