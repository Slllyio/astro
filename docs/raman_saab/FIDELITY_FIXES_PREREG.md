---
title: "Fidelity fixes R1-R6: pre-registration (2026-10-24)"
kind: prereg
topic: validation
measured: false
updated: 2026-10-24
tags: [raman-saab, judge-mechanism, prereg, holdout]
---
# Fidelity fixes R1-R6: pre-registration

Committed BEFORE any of the measurements below exist. The user asked (2026-10-24) to implement
every recommendation in `WHY_273_OF_396.md`. This file fixes, in advance, exactly what each fix
is, what it is measured on, and what result lets it ship, so the outcome cannot steer the method.

Baseline (V0): the engine at commit ae0eac0. 273/396 exact, 363/396 within one, 33 real errors.

## The one decision rule (every engine variant)

A variant ships only if ALL hold on the confirmed pool:

1. real errors (ordinal distance 2) do not rise, overall or in any single book;
2. within-one does not fall;
3. exact rises, or real errors fall (at least one strict gain).

No variant gets a second, adjusted version after its numbers are seen. A coding error that makes
the code differ from the text below may be fixed, and the fix is recorded here with the reason.
Variants are measured one at a time against V0, then the passing ones together; the package must
also pass the rule.

## R6. Sealed hold-out (built first)

Source: Raman charts that are NOT in the golden fixture: the example nativities of
*Three Hundred Important Combinations* (complete edition) and the illustrated horoscopes of
*Ashtakavarga System of Prediction* ch. 16. Extraction is engine-blind: four agents that may not
run or read the engine, the judge, the doctrine rules or the fixtures, applying the confirmation
rule (conclusions only, never observations; "mixed" only when Raman names both poles). Brief:
`docs/raman_saab/HOLDOUT_BRIEF.md`.

Birth data is accepted only when the cast chart agrees with Raman's printed Lagna sign where he
states one, and with the printed dasa balance (planet must match; years within 1). Charts whose
birth data equals a golden chart's are dropped. The V0 verdicts on the hold-out are written to a
file whose SHA-256 is committed, without being looked at. The hold-out is scored ONCE, after all
shipping decisions on R1-R5 are final. It cannot change any of them. If the shipped package does
worse than V0 on the hold-out (more real errors, or lower exact), that is reported to the user with
a recommendation to revert, and nothing is tuned in response.

## R1. Raman-grammar lord and karaka condition

`raman_condition(planet, chart, matter_house)`:

- WEAK if any hard sign: uncancelled debility, or combust (not the Sun).
- Otherwise collect signs. Weak signs: placed in the 6th, 8th or 12th counted from the matter's
  house (HTJAH-I:5799ff "occupying the 12th from the 5th has rendered the 5th house weak");
  joined or aspected by a natural malefic (Sun, Mars, Saturn, Rahu, Ketu) with no joining or
  aspect by Jupiter or Venus (HTJAH-I:8434, :2532). Strong signs: exalted, own sign or
  moolatrikona (HTJAH-I:474, :497); joined or aspected by Jupiter or Venus with no malefic
  contact (HTJAH-I:2338).
- Weak signs only -> weak. Strong signs only -> strong. Both or neither -> the existing reading
  (Shadbala where it exists, else positional dignity).
- Matter house is counted from the frame's own Lagna (Lagna or Moon).

Gate 1, before any verdict is measured: on the rows where Raman's own passage calls the lord
(or karaka) strong or weak (the frozen word-miner `tools/raman_saab/raman_strength_words.py`),
R1 must agree with Raman more often than the current pillar does. Current: lord 128 of 194,
karaka 133 of 201. Both must improve. Gate 2: the decision rule.

Double counting: in clause 2 the pillars decide and rule counts only gate entry, so reading
contacts into the pillar does not weigh them twice there. This is stated so the review can
check it.

## R2. Re-scope the ten contra-heavy rules from their citations

Rules (fixed now): H11.C.2, H2.C.69, H5.C.1, H1.N.66, H2.C.26, H7.C.1, H3.C.8, H1.C.28b,
H7.KD.1, H9.B.23 with H9.B.24. They were chosen by how often they fire against Raman on the
pool, which is selection on outcome, so the REMEDY must come from the citation alone. An
engine-blind reviewer (told nothing about firing rates or verdicts) reads each rule and its
cited sentence and returns one of: KEEP; RE-SCOPE (to a named signification the sentence is
about); DESCRIPTIVE (a general dictum Raman reasons past, no verdict vote); NARROW (the condition
claims more than the sentence; give the text-faithful condition). Every decision the reviewer
makes is implemented as a package; no picking among them after measurement.

## R3. One meaning for "mixed"

R3a, labels. "Mixed" means Raman's conclusion names both poles as operative for the matter in
this life. Two independent engine-blind reviewers re-read every confirmed row labelled mixed
and every confirmed row whose prose carries a contrast word (but, however, though, yet, while,
although, despite). A label changes only when both reviewers agree on the same new label. Rows
the reviewers split on keep their adjudicated label and are listed. The re-labelled pool is the
pool every engine variant below is measured on, and its V0 figure is re-based with lineage.

R3b, engine (cast charts). When the frame decision (after the navamsa step) is still "mixed" on
a chart with strength pillars, break the tie by the preponderance of fired testimony: more
distinct benefic rules than malefic -> favourable; more malefic -> afflicted; equal -> mixed.
Citation: HTJAH-II:1673-1676, "There is a preponderance of benefic influences on the 7th house
... The native has a happy married life."

## R4. Stated-position charts

The same tie-break as R3b, applied only where both pillars are unknown. This reverses the effect
of the 2026-08-30 sparse-contradiction exception (P2) in exactly one respect: P2 stops the
navamsa from moving a contradicted mixed; R4 lets the rasi testimony itself decide it. P2's own
reason ("with no measured rasi strength and contradicted testimony there is nothing for it to
confirm") is about the navamsa, not about the testimony; R4 is measured on its own.

## R5. Raman's own reasons on the 21 no-fire rows

For each confirmed row where no rule fired, read the cited passage. Where Raman gives a GENERAL
principle (one that would apply to any chart) as his reason, encode it as a rule with that
citation. Chart-specific reasons, and reasons already encoded but not firing, are recorded and
not forced. Before shipping, each new rule's firing rate over all golden charts is reported
(playbook step 3a). The new rules are measured as one package under the decision rule.

## Honesty note

All of R1-R5 are measured on a pool that has been studied for months, and R2 and R5 were chosen
from that pool. A pass is evidence, not proof. The hold-out is the test.

## Addendum 1 (2026-10-24): hold-out sealed, R1 gate 1, two recorded fixes

**R6 sealed.** Four engine-blind extractions (`docs/raman_saab/holdout_extractions/`): 3HC
charts 2-143 gave 130 conclusions; the Ashtakavarga chapter prints only bindu tables and gave
none. After the acceptance checks: 27 natives, 28 records, **36 scored rows** (23 favourable,
13 afflicted) in `tests/fixtures/raman_holdout_sealed.jsonl`. Rejected: 34 charts share a birth
date with a golden chart, 13 disagree with the printed dasa balance, 10 lack a date, time or
coordinates. V0 verdicts on the hold-out were written, not read, to
`docs/raman_saab/holdout_v0_verdicts_sealed.json`,
SHA-256 `99ee148ce3a1b8839090e48576492abbdcd183ff5ec6a30d4780807c921b547b`.
Limits: 36 rows is small (one row is 2.8 points); where Raman names no Lagna, only the Moon is
verified (through the dasa balance), not the Lagna.

Two builder fixes, both made before any hold-out verdict existed: the dasa-balance parser
stripped a trailing "s" from planet names ("Venus" became "venu"), rejecting good charts; and
where no time basis is printed the builder now assumes LMT, Raman's default in this book, and
the dasa-balance check still decides acceptance.

**R1 gate 1: FAILED.** Agreement with Raman's own strong/weak words, R1 vs the current pillar:
lord 111 vs 128 of 194; karaka 106 vs 133 of 201. R1 cannot ship. Its verdict numbers are
measured for the record only. One coding fix: the frame-sign helper raised on stated-position
charts with no Moon; it now falls back to the Lagna.
