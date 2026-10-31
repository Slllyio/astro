# Reason coding: results (2026-10-31)

Pre-registration: `REASON_CODING_PREREG_2026-10-31.md` (+ Addendum 1, the coefficient models the
user asked for). Pool only (389 conclusions, 237 charts). No engine change. Hold-outs 4 and 5
not read. Data in `reason_coding/`; models: `python -m tools.raman_saab.reason_models`.

Eight blind coders recorded every factor Raman states for each conclusion (2,011 factors).
Raman gives reasons in the passage for 347 of the 389. Four matchers then marked each factor
covered / opposed / absent against the engine's fired rules and ledger flags.

**Reliability.** A fifth coder independently re-coded 20% of charts (67 matters). Factor-type
overlap: mean Jaccard 0.75, above the 0.5 bar, so the factor lists are reliable. Agreement on
which single factor is "decisive" is only 47%, so anything resting on the decisive flag below
is weak.

## Finding 1. Raman's verdict is close to a tally of the reasons he states

An ordinal logistic model on his own coded factors (signed count per factor type, plus the
decisive one) recovers his verdict on charts it has not seen (leave-one-chart-out):

| | exact (of 347) | real errors | log-loss |
|---|---|---|---|
| L2 ordinal model on Raman's coded reasons | **291 (84%)** | 23 | 0.45 |
| Boosted trees (depth 2) on the same | 290 | 23 | 0.54 |
| Class frequencies | - | - | 0.94 |
| Shipped engine on the same rows | about 68% | | |

The coefficients are all positive and similar in size: about 0.6 to 1.05 per stated factor, for
every factor type, with every 95% interval above zero except karaka-as-decisive. **In effect
Raman adds up his favourable and adverse reasons, and a reason he leans on counts about double.**
No factor type dominates. Boosted trees find no interactions worth more than the linear tally.
(These features come from his text, so this describes his reasoning; it is not a predictor.)

## Finding 2. The engine sees under a third of the reasons Raman uses

Of the 2,011 stated factors, the engine covers 580 (29%), opposes 207 (10%), and has nothing
for 1,224 (61%).

| Factor type | Times Raman cites it | As decisive | Covered | Opposed | Absent |
|---|---|---|---|---|---|
| other (specific planet readings, e.g. "Mercury in Lagna aspected by Saturn: solid intellect") | 225 | 33 | 13% | 6% | 81% |
| reading from the Moon / karaka / another house as Lagna | 175 | 18 | 9% | 3% | **88%** |
| karaka | 175 | 22 | 59% | **28%** | 13% |
| lord's associations (conjunctions, aspects, combustion) | 160 | 25 | 33% | 21% | 46% |
| dasa / timing | 159 | 11 | 0% | 0% | 100% |
| named yogas | 154 | **54** | 18% | 2% | **80%** |
| aspects on the house | 152 | 16 | 25% | 5% | 70% |
| Navamsa | 145 | 7 | 20% | 10% | 70% |
| occupants of the house | 140 | 27 | 69% | 11% | 20% |
| lord's house placement | 134 | 15 | 62% | 18% | 20% |
| known life facts | 94 | 0 | 0% | 0% | 100% |
| Rahu / Ketu | 93 | 16 | 32% | 13% | 55% |
| lord's dignity | 62 | 8 | 45% | 21% | 34% |
| hemming | 53 | 1 | 38% | 13% | 49% |
| 6th/8th/12th lords | 42 | 7 | 17% | 12% | 71% |

## Finding 3. There is no single missing factor

Ranking (pre-registered): conclusions where the decisive factor is absent or opposed and the
engine is wrong. Named yogas 10, other 7, lord associations 6, other frames 4, dasa 4, Navamsa
3, everything else 1-2. The list is flat. Also, the engine is right about as often when the
decisive factor is covered (66%) as when it is absent (70%). The engine's misses come from
**breadth**: it counts a different, narrower set of evidence than Raman does, and then combines
it with a cascade instead of a tally.

## What this means

- The way Raman combines evidence is simple: a signed tally. The engine's clause cascade is the
  wrong combiner (this also explains why the plain rule count beat it out of sample).
- The evidence is what the engine lacks. The largest computable gaps are readings from the Moon
  and karaka as Lagna, named yogas applied to the matter, aspects on the house, the Navamsa, and
  lord associations; the karaka is often read the opposite way from Raman.
- About 13% of Raman's factors (dasa timing, known life facts) cannot come from a birth chart at
  all. That sets a hard ceiling on any chart-only judge, probably somewhere in the high 80s.

Recommended next step (for the user to decide): build a **tally judge**. For each matter, compute
the factor types Raman checks from the chart alone (lord house, dignity and associations,
occupants, aspects, karaka, Navamsa, Moon and karaka frames, hemming, 6/8/12 lords, named yogas,
nodes), each signed by Raman's own rules, and add them up with one shared weight. Pre-register,
develop on the pool and hold-outs 1-3, and test once on hold-outs 4 and 5.
