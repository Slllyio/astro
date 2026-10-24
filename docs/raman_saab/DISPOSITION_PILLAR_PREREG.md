---
title: "Disposition as a verdict pillar: pre-registration (2026-10-24)"
kind: prereg
topic: validation
measured: false
updated: 2026-10-24
tags: [raman-saab, judge-mechanism, prereg]
---
# Disposition as a verdict pillar: pre-registration

Written and committed BEFORE any number exists. The user asked to make the engine "truest to
Raman" (2026-10-24). This records exactly what will be measured and what result would justify
proposing a change, so the measurement cannot be steered by its outcome.

## The question

In his worked charts Raman judges each of the three factors (house, lord, karaka) by its
INFLUENCE: who joins it and who aspects it, benefic or malefic. Chart No. 100 (HTJAH-I:5799-5819)
is typical: "The 5th lord Mercury is in Lagna with a malefic Sun and aspected by another malefic
Saturn and hence afflicted ... the 5th house is feebly strong, the lord is weak and the Karaka
powerless." No Shadbala figure appears. The engine's lord and karaka pillars are read from
Shadbala (`house_template._strong`), and on that chart both read strong, no rule fires, and the
engine returns favourable where Raman wrote that children were a source of misery.

The INFLUENCE axis already exists as `doctrine/disposition.py` (two engine-blind reviews,
2026-10-13, Raman's own definitions at HTJAH-I:2338, :4283, :8434, HTJAH-II:7480). It drives only
which text a rule shows; it casts no vote in the verdict. DOCTRINE_BACKLOG ("OPEN -
DOCTRINE-CONTESTED") records that letting it vote is a corpus-wide decision needing user sign-off.

## Variants (fixed now; no others will be scored)

- **V0** the engine as shipped.
- **V1 influence decides a clear case.** Lord and karaka pillar = `disposition(...).reading`:
  "good" -> strong, "bad" -> weak. "mixed" or "none" keeps the Shadbala reading.
- **V2 afflicted veto only.** A lord whose disposition reads "bad" counts as hard-afflicted, the
  channel the B1 guard already reads (blocks a favourable lift, never forces afflicted).
- **V3 V1 plus the house factor.** The third pillar (empty since the Bhava Bala stopped voting)
  reads the HOUSE's influence: joined or aspected by a natural malefic and by neither Jupiter,
  Venus nor its own lord -> weak; joined or aspected by Jupiter, Venus or its own lord and by no
  natural malefic -> strong; otherwise no vote. The Lagna lord is exempt as an afflicter of a
  house, as in `conditions.HouseAfflictedBy`.

## Metrics

On the current CONFIRMED pool (396 rows): exact, within-one, real errors (distance 2), each also
split by book (HTJAH-I, HTJAH-II, NH). Plus the list of every row that changes.

## Decision rule

A variant becomes a candidate only if ALL hold:

1. real errors fall;
2. within-one does not fall;
3. real errors do not rise in any single book (a gain bought in one book at another's cost is
   fitting, not fidelity).

A candidate is then given, row by row, to an engine-blind reading against Raman's printed text.
Only after that does it go to the user, as B1 did, because it changes the shared judge. If no
variant passes, that is recorded here as the result and nothing ships.

## Honesty note

The pool is in-sample: earlier gates were tuned on these same rows. A pass here is evidence the
mechanism is closer to Raman, not proof. The sealed hold-out of new Raman charts (audit
2026-10-23) remains the real test and is still owed.
