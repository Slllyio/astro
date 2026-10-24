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

## Addendum 2 (2026-10-24): R2 to R4 measured; R5 fixed before measurement

| Variant | Exact | Within one | Real errors | HTJAH-I | HTJAH-II | NH | Ships? |
|---|---|---|---|---|---|---|---|
| V0 | 273 | 363 | 33 | 13 | 3 | 17 | baseline |
| R1 | 238 | 338 | 58 | 12 | 11 | 35 | no (also failed gate 1) |
| R2 package | 274 | 362 | 34 | 13 | 4 | 17 | no: +1 real error, -1 within one |
| R3b | 276 | 348 | 48 | 15 | 10 | 23 | no |
| R4 | 280 | 362 | 34 | 13 | 3 | 18 | no: +1 real error, -1 within one |
| R3b + R4 | 283 | 347 | 49 | 15 | 10 | 24 | no |

R2: the engine-blind reviewer returned KEEP for H2.C.69 (citation moved 2800 to 2802), H5.C.1,
H2.C.26, H7.C.1; RE-SCOPE for H11.C.2 (to a new `means_of_gain` matter, mixed case excluded)
and H1.N.66 (to H6 enemies); DESCRIPTIVE for H7.KD.1; NARROW for H3.C.8 (no D9-exaltation arm),
H1.C.28b (two or more functional malefics) and H9.B.23/24 (exclude a dignified malefic,
HTJAH-II:7468-7470). The package changed 8 rows: 3 new hits (HTJAH-II chart_11 and chart_12
marriage, NH chart_13 self), 1 hit lost (HTJAH-II h7_06), and 1 new inversion: HTJAH-II h11_08
gains, which the engine had right only because H11.C.2's malefic vote routed it through the
contradiction clause; without that vote, weak pillars plus maraka pressure read afflicted.
Held as `docs/raman_saab/held_patches/R2_rule_rescope_2026-10-24.patch` with the review.

**R5 specification (fixed now, before any R5 number).** The 21 rows with no polarity rule
miss 7 times, 5 of them inversions, all through clause 5. Raman's reason in each is the same
general factor, stated for every house: "the strength, aspects, conjunctions and location of
the lord of the house" (HTJAH-I:474) and "the good or bad nature of the aspects to which a lord
... is subjected plays no mean part" (HTJAH-I:499-500); worked as "the lord and the Karaka are
considerably afflicted. Hence the native lost his mother very early" (HTJAH-I:5228-5229). One
rule per house h in 1, 2, 3, 4, 5, 7, 9, 10, 11 (the dusthanas are excluded: an afflicted
dusthana lord is read the other way), tagged with that house's broad matter (self, wealth,
siblings, mother, children, spouse, father, career, gains), polarity malefic, firing when
EITHER (a) the house lord is joined or aspected by two or more natural malefics and by neither
Jupiter nor Venus, OR (b) the house lord and the matter's primary karaka are each joined or
aspected by at least one natural malefic and neither is joined or aspected by Jupiter or Venus.
Natural malefics: Sun, Mars, Saturn, Rahu, Ketu (the locked convention). Firing rate over all
golden charts is reported before the decision.

## Addendum 3 (2026-10-24): R5 measured

Firing rate over the 346 golden charts: 71 to 123 charts per house rule (21% to 36%). One
coding reading recorded: where the lord IS the karaka, arm (b) is switched off, since "the lord
and the Karaka" are then one factor and arm (b) would fire on a single malefic contact.

| Variant | Exact | Within one | Real errors | HTJAH-I | HTJAH-II | NH | Ships? |
|---|---|---|---|---|---|---|---|
| R5 | 269 | 362 | 34 | 11 | 5 | 18 | no |

R5 fixed four inversions exactly as intended (HTJAH-I h5_10 and h5_15, NH chart_55 self,
NH chart_57 children) and created five: HTJAH-II h11_15 and x224 gains, NH chart_25 speech,
NH chart_51 and chart_69 career, all charts where Raman reads the matter favourably despite the
lord's malefic contacts. This is the disposition-prereg result again from a different
direction: in Raman's own conclusions a malefic-afflicted lord decides the matter about as often
as he reasons past it, and nothing the engine reads separates the two. Held as
`docs/raman_saab/held_patches/R5_general_lord_affliction_2026-10-24.patch`.
