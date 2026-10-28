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

## Addendum 4 (2026-10-24): R3a applied, every variant re-measured, hold-out scored

**R3a.** The two reviewers agreed with each other on 92 of 102 rows. They agreed with the
existing label on 69, agreed on a different label on 23, and split on 10 (kept as adjudicated).
Of the 23: 15 "mixed" rows were really one-sided conclusions (8 afflicted, 7 favourable), one
"afflicted" row was two-sided (HTJAH-II h9_02: an exalted royal father, lost very early), and 7
rows hold no good-or-bad conclusion at all (two wives both alive, married a foreigner, Einstein's
attitude to money), so both reviewers chose "unclear" and those rows were demoted to DRAFT,
unscored. Recorded reading: the brief offered "unclear" as a label, and a row two reviewers
independently find conclusion-free fails the confirmation rule, so demotion is the faithful act.

Re-labelled pool, V0: **275/389 exact (70.7%), 351/389 within one (90.2%), 38 real errors.**

| Variant (re-labelled pool) | Exact | Within one | Real errors | Ships? |
|---|---|---|---|---|
| V0 | 275 | 351 | 38 | baseline |
| R2 package | 277 | 350 | 39 | no |
| R3b | 280 | 335 | 54 | no |
| R4 | 284 | 350 | 39 | no |
| R5 | 271 | 350 | 39 | no |

No engine variant passes on either pool. The engine is unchanged.

**Hold-out (scored once).** The engine's verdicts on the hold-out reproduce the sealed hash
exactly (`99ee148c...`), so this is the pre-registered V0 reading:

| Pool | Exact | Within one | Real errors |
|---|---|---|---|
| Golden pool (in-sample) | 275/389 = 70.7% | 351/389 = 90.2% | 38 (9.8%) |
| Sealed hold-out (unseen) | 23/36 = 63.9% | 28/36 = 77.8% | 8 (22.2%) |

With 36 rows the hold-out exact figure has a 95% interval of roughly 47% to 79%, so it is
consistent with a modest in-sample advantage, and its inversion rate is more than double the
pool's. Read honestly: the pool figure carries some fitting from months of gates tuned on it, and
the true out-of-sample inversion rate is likely nearer one in five than one in ten. Per-row
record: `docs/raman_saab/holdout_score_2026-10-24.json`. The hold-out is now SPENT for these
variants; any future fix needs fresh unseen charts for its own test.

**User decision (2026-10-24):** R2 is HELD until more unseen charts exist ("Hold until more
unseen charts"). R4 and R5 stay held on the same footing. Next step: a second sealed hold-out
from Raman's other books, built with the same engine-blind brief and acceptance checks.

## Addendum 5 (2026-10-24): hold-out 2 protocol, fixed before any chart is extracted

Source: charts never used in the golden corpus or hold-out 1: Notable Horoscopes Nos. 1, 2, 3,
4, 6, 7, 8, 9, 11, 12, 15 and 50 (skipped by the old extractor because their positions did not
parse), and How to Judge a Horoscope Vol I and II charts whose birth date is in neither fixture.
Same engine-blind brief plus `HOLDOUT_BRIEF2_ADDENDUM.md` (stated positions for charts without
birth data). Acceptance: cast charts must match the printed dasa balance (planet, years within
1) and any printed Lagna; stated-position charts need all nine grahas and the Lagna sign, and are
dropped if their positions equal a golden chart's.

Decision rule on hold-out 2, each held variant (R2, R4, R5) scored once against V0: it ships only
if real errors do not rise, within-one does not fall, and exact rises or real errors fall. A
variant that also passed this on hold-out 2 still goes to the user before shipping, because it
failed the pool rule. Hold-out 1 is not reused.

## Addendum 6 (2026-10-24): two extraction findings, fixed before the hold-out 2 fixture or any verdict exists

1. **Vol II was extracted twice.** The HTJAH-I unsplit corpus file also carries Vol II from about
   line 7865, so the "HTJAH-I second half" extractor and the HTJAH-II extractor independently
   read the same 40 Vol II charts. Both were engine-blind. They agreed on 32 (house,
   signification, verdict) conclusions and contradicted each other on none; the other 17 were
   named by only one extractor (mostly signification-key naming, e.g. `career` vs
   `profession_authority`). Following the standing rule that a contested label never enters the
   scored pool, **only conclusions both extractors gave identically are scored**, and a chart is
   dropped when the two disagree on its birth data (Nos. 178, 205). Merge log:
   `holdout_extractions/r2_htjah2_merge_log.txt`. `r2_htjah1b.json` is therefore not fed to the
   builder except for its closing illustrations A and B, which the other extractor did not reach
   (single extraction, kept under the same footing as the NH and Vol I files).
2. **Pre-Gregorian and BC dates** (NH Nos. 1-9 print Julian dates) are routed to Raman's printed
   positions instead of the ephemeris cast, which is Gregorian; `build_holdout._birth` returns
   "pre-Gregorian date" for years before 1583.
3. **Prose dasa balances.** The first build rejected 23 Vol II charts as "no readable dasa
   balance" because the parser read only the short form ("Venus 2-1-15"), while Vol II prints
   "Balance of Venus Dasa at birth: 2 years 1 month and 15 days". The parser now reads both
   (`_printed_balance_any`; OCR 'O' read as zero). That first build's verdict file was deleted
   unread (only its hash was printed); hold-out 1 still rebuilds byte-identically.
4. **Hold-out 2 sealed.** 26 natives, 40 records, 134 scored rows (94 favourable, 33 afflicted,
   7 mixed) from NH, HTJAH Vol I and Vol II. Thirteen cast charts were rejected because they
   disagree with the printed dasa balance, one for a Lagna mismatch, and NH No. 50 as a golden
   chart. Fixture sha256 `4690276ba5f6fc77b25653d8e8db1f390f9a0af021875940fbea66ecfc0c4b0a`; V0 verdict file sha256
   `9ab344410ddc1f7252cf29fafe83e82e869f005ce886e43301293750228cd065` (not read before scoring).
   It is scored exactly once for V0, R2, R4 and R5 under the Addendum 5 rule.

## Addendum 7 (2026-10-24): hold-out 2 scored once

V0 55/134 exact, 98 within one, 36 real (verdict hash matched the sealed file). R2 58/98/36 passes;
R4 64/94/40 fails; R5 55/100/34 passes. Both passing variants go to the user, per Addendum 5.
Write-up: `HOLDOUT2_RESULTS_2026-10-24.md`.

## Addendum 8 (2026-10-24): user decision, R2 shipped

The user chose "Ship R2 only". R2 is applied to `app/` (patch kept in `held_patches/` for the
record). Pool re-based with lineage: 277/389 exact, 350/389 within one, 39 real errors (new pinned
error HTJAH-II.h11_08 H11/gains). R5 stays held; R4 is dropped. Knock-on updates, all deliberate:
rule-liveness baseline 899 -> 898 evaluable (H7.KD.1 descriptive), the `means_of_gain` topic phrase
in the feedback instrument and report glossary, four tests that pinned H7.KD.1 firing or its
maintainer note, the Track-B evidence snapshots, and the doctrine snapshot (1072 moves on unscored
rows; summary in its note).

## Addendum 9 (2026-10-24): user decision, Navamsa one-step rule

Not pre-registered: it follows from the doctrine research in `NAVAMSA_STEP_FINDINGS_2026-10-24.md`
(Raman lets the Navamsa change degree, not direction; the clause-2 flip had no citation). The user
chose to encode it. Pool 277/350/39 -> 269/354/35, four pinned real errors fixed, none new. Both
hold-outs were already spent, so their figures (22/30/6 and 57/100/34) describe the change and do
not test it. Doctrine snapshot: 1541 verdict moves on the corpus, 1518 of them afflicted -> mixed.

## Addendum 10 (2026-10-28): hold-out 3 and variant M1, fixed before any M1 number or hold-out 3 chart exists

**Hold-out 3 source.** *Hindu Predictive Astrology* ch. 35 ("Practical Horoscopes", 21 natives
with birth data, printed sign positions and short remarks) and ch. 14 Horoscope Nos. 1-3. No HPA
chart has been used in the golden pool or either earlier hold-out. Natives whose birth date is
already in any fixture are skipped (285 dates; Nos. 35.1 Mussolini and 14.3 are among them).
Extraction: two independent engine-blind agents, same brief (`HOLDOUT_BRIEF.md`) plus
`HOLDOUT_BRIEF3_ADDENDUM.md`; only conclusions the two give identically (house, matter and
verdict) are scored, as for HTJAH-II in hold-out 2. Acceptance: HPA prints no dasa balance, so a
cast chart is accepted only if all nine grahas and the Lagna fall in the signs Raman prints;
otherwise (or with no coordinates) the chart is used from its printed signs as a stated-position
chart, as NH Nos. 1-15 were. The V0 verdicts are written to a file whose SHA-256 is recorded
here, unread, before M1 is applied to `app/`. Hold-out 3 is scored once.
Disclosure: while scoping the source I read the remarks of ch. 35 Nos. 1-5. None of that text
was used in designing M1.

**Diagnosis that motivated M1** (decision-path trace of every scored row, pool plus the two
spent hold-outs, 559 rows). Sixteen rows are decided by clause 6 on "a weak pillar plus maraka
pressure" with no malefic rule fired at all: 8 are matters Raman calls favourable (all real
errors), 6 afflicted, 2 mixed. The matters are career, authority, gains, elder siblings, spouse,
children, intellect, mother, self, hearing. `maraka_active` is true whenever the matter's lord or
karaka is a maraka of the native, and Raman's maraka doctrine is death-determination doctrine
("Primary Determinants of death ... the 2nd and 7th are houses of death", HTJAH-I:776-814). B3
and its 2026-08-29 extension already removed maraka's verdict-driving effect from marital
happiness, speech, vision and family on exactly this ground; the reviewer's words then were "the
maraka chapter is death-determination doctrine, full stop".

**M1 (one variant, no second version).** `MARAKA_NON_DEATH_GUARD` is set for every
signification except `death`, `longevity` (already under `LONGEVITY_GUARD`) and `wealth` (the
poverty block, HTJAH-I:2526-2528, makes maraka association a wealth operator). Nothing else
changes: `maraka_active` is still recorded, the karaka veto and every fired rule keep full force.
Expected side effect, accepted in advance: where maraka pressure was the only evidence, a matter
may now read insufficient-evidence, which scores as distance 2.

**Decision rule.** M1 is recommended to the user only if (a) it passes the one decision rule on
the pool (real errors do not rise overall or in any book; within-one does not fall; exact rises
or real errors fall), and (b) on hold-out 3, scored once, real errors do not rise and within-one
does not fall against V0. Passing (a) and (b) still goes to the user, after an engine-blind
doctrine review of the change. Failing either is reported and M1 is held; it is not adjusted.

## Addendum 11 (2026-10-28): hold-out 3 sealed

Extractions `holdout_extractions/r3_hpa_a.json`, `r3_hpa_b.json`; 33 conclusions given identically
by both, none contradicted; merged as `r3_hpa_merged.json` with two mechanical fills recorded in
each chart's `fill_notes` (Ketu opposite the printed Rahu for 35.10; Bangalore coordinates for
14.2, place printed without coordinates). Fixture `tests/fixtures/raman_holdout3_sealed.jsonl`:
15 natives, 16 records, **28 scored rows** (19 afflicted, 9 favourable). Six charts whose cast
missed a printed sign (five Lagnas, two Venus) are used from their printed signs; 35.7, 35.12 and
14.1 are rejected (incomplete data). V0 verdicts written, unread, to
`docs/raman_saab/holdout3_v0_verdicts_sealed.json`,
SHA-256 `c9543269443dffed95fcbdb57a7eb496113c31bd1da08bd34994742678a3bc08`.

## Addendum 12 (2026-10-28): M1 measured on the pool, FAILS rule (a), held

Pool, V0 -> M1: exact 262 -> 262, within one 349 -> 350, real errors 40 -> 39. By book: HTJAH-I
13 -> 12, HTJAH-II 5 -> 3, but **NH 22 -> 24**, so real errors rise in one book and M1 fails the
one decision rule. Twelve rows move. Gains: HTJAH-I.h5_15 children, HTJAH-II.h11_08 gains,
HTJAH-I.x75 mother (all afflicted -> favourable, Raman favourable). New real errors:
NH.chart_35 H7 virility (afflicted -> insufficient-evidence: maraka was the only evidence) and
NH.chart_54 H10 career (afflicted -> favourable, Raman afflicted). Also HTJAH-I.chart_57 H3
ear_throat and NH.chart_36 H7 spouse fall to insufficient-evidence, the side effect predicted in
Addendum 10. M1 stays in code behind `MARAKA_GUARD_ALL_NON_DEATH = False` and is not adjusted.
Hold-out 3 was NOT scored for M1: a variant that fails the pool rule cannot ship, so the only
fresh set is kept sealed for the next pre-registered variant.

## Addendum 13 (2026-10-28): variant Y1 (a blemish does not open the contradiction), fixed before the tiers or any Y1 number exist

User decision 2026-10-28: start the yoga-flaw fix (`YOGA_BLEMISH_PROPOSAL_2026-10-24.md`) as the
next pre-registered change, tested on the sealed hold-out 3.

**Tiers.** Every rule that lands in a matter's malefic bucket on any fixture chart (379 rules:
363 malefic by polarity, 16 neutral promoted by the functional-malefic overlay; selection by
firing only, no verdict read) is graded by four engine-blind agents, about 95 rules each, from
its cited passage: `decisive`, `ordinary`, `blemish`, or `unsupported`. Brief:
`docs/raman_saab/research/TIER_BRIEF.md`. The grades are stored as data in the engine; a rule
with no grade, or graded `unsupported` or `decisive`, behaves exactly as today in Y1. The
`decisive` and `unsupported` grades are recorded for later work only.

**Y1 (one variant, no second version).** For a matter that is NOT an inherent-affliction matter
(`AFFLICTION_MATTER`: 6th, 8th death, 12th incarceration and left eye), when at least one benefic
rule fired, the malefic rules graded `blemish` are removed from the ledger's malefic set before
the verdict clauses run. They are kept on the ledger as their own `fired_blemish` list and flagged
`BLEMISH_ONLY` when they were the only malefics, so every renderer still shows them. When no
benefic fired, a blemish counts as an ordinary malefic, unchanged. Consequence: a good matter
with only blemish-grade negatives no longer goes through the contradiction clause (and so the
Navamsa can no longer turn it), and a yoga lift that required "no malefic fired" now ignores
blemishes. Nothing else changes. Switch: `house_template.Y1_BLEMISH_TIER` (default False).

**Decision rule.** Same as M1: (a) the one decision rule on the pool (real errors do not rise
overall or in any book; within-one does not fall; exact rises or real errors fall); (b) hold-out
3 scored once, V0 against Y1: real errors do not rise and within-one does not fall; (c) an
engine-blind doctrine review of the tier table before anything ships, which goes to the user.
Hold-out 3 is scored only if (a) passes.

## Addendum 14 (2026-10-28): Y1 measured on the pool, FAILS, held

Tiers from the four engine-blind reviews (379 rules): 106 decisive, 168 ordinary, 100 blemish,
5 unsupported; per-rule quotes in `research/malefic_tiers_review_2026-10-28.json`, table in
`doctrine/malefic_tiers.py`. Pool, V0 -> Y1: exact 262 -> 263, within one 349 -> 345, **real
errors 40 -> 44** (NH 22 -> 25, HTJAH-I 13 -> 14). Fails rules 1 and 2. Thirteen rows move: six
mixed -> favourable that Raman calls favourable, but also NH.chart_42 and chart_53 H1 self
favourable -> afflicted (with the blemish set aside the contradiction closes and the weak-pillar
clause decides), and HTJAH-I.chart_10 H1 and NH.chart_46 H4 education mixed -> favourable where
Raman says afflicted. Y1 stays behind `Y1_BLEMISH_TIER = False`, not adjusted; hold-out 3 is not
scored and stays sealed.

Side findings of the review, for citation-first repair (none measured, none applied): 5 rules
graded `unsupported` (H3.C.31, H7.L.8, H7.P.Sun, H8.L.1, H8.L.12); rules whose `text` is
Raman's favourable or mitigating clause but whose polarity is malefic (H1.L.8, H1.P.Saturn,
H2.P.Rahu, H3.L.11, H10.P.Ketu, H12.L.4, H12.P.Venus); routing problems (H12.C.J11 is the right
eye, filed under left_eye; H9.C.35 and H9.D.40 cite passages silent on their matter; several
H8.L/H8.P rules tagged `longevity` cite passages about other matters); one rule note contradicted
by its own citation (H4.C.18, HTJAH-I:4224); and several one-line citation offsets.

## Addendum 15 (2026-10-28): citation repair of the rules flagged by the tier review (user decision: "fix the rule defects"), HELD for sign-off

A second engine-blind reviewer re-checked the 36 flagged rules (`research/rule_defects_2026-10-28.json`
-> `research/rule_defects_review2_2026-10-28.json`): 18 descriptive, 11 keep, 3 citation-line only,
2 benefic (H3.L.11 HTJAH-I:3351; H8.P.Saturn "Saturn in the 8th house gives good longevity",
HTJAH-II:3550), 2 reroute (H9.C.35 -> fortune; H4.P.Mars NOT applied: its `mother_home` key is a
deliberate tag shared by mother and happiness, and the reviewer had been given only signification
keys). Applied as `held_patches/RULE_DEFECTS_2026-10-28.patch`.

Pool, before -> after: exact 262 -> 260, within one 349 -> 349, real errors 40 -> 40 (no book
changes in real errors). Four rows move: HTJAH-II.h12_11 and NH.chart_59 incarceration afflicted
-> mixed (H12.L.4, now descriptive, was carrying them; Raman afflicted), HTJAH-II.h9_17
long_journeys favourable -> mixed (rerouted H9.C.35 now reaches it through the shared fortune
tag; Raman favourable), NH.chart_14 body mixed -> favourable (H1.L.7 descriptive; Raman
favourable). This is a faithfulness correction, not a tuning variant: each rule now says what
its passage says, and the strict figure falls by two. Shipping it re-bases the ratchet, so it is
the user's decision.
