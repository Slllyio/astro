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

## Addendum 16 (2026-10-30): variants G1 and N1, fixed before any G1 or N1 number exists

User decision 2026-10-30 ("Headline + pre-register both", on the harshness diagnosis
`HARSHNESS_DIAGNOSIS_2026-10-30.md`). Both variants come from the Kanpur trace (10 Oct 1989,
15:15 IST), a chart outside the goldens. Their in-pool firing counts were already seen in the
diagnosis: the fertility gate decided 12 confirmed rows (9 afflicted, 1 mixed, 2 favourable in
Raman's words), and H7.C.82 fires on the nodes alone on no confirmed row. No variant number
exists yet.

**G1 (one variant, no second version). The fertility gate moves the verdict one step, never decides it.**
Today `_fertility_gate` sets children/progeny to `afflicted` when both sphutas fail their
odd/even test, or when one fails and Arm A or Arm B corroborates. Under G1 the same arms fire
on the same conditions, but each moves the verdict at most **one step toward afflicted**:
favourable to mixed, mixed to afflicted, afflicted unchanged. The `FERTILITY_GATE` flag and the
metadata are unchanged.

Basis:
- Raman's worked Chart 88: a Beeja in an even sign is judged "strong" on its other testimony
  (HTJAH-I:5529-5551).
- Chart 89: a Kshetra in an odd sign is judged "fertile → birth of children", fewer in number
  (HTJAH-I:5553-5582).
- So the parity test alone is co-testimony. It is not a decision. The relief clauses
  (HTJAH-I:5524-5527) are not encoded, so the gate cannot tell a relieved point from an
  unrelieved one.
- Moving one step is the same discipline the Navamsa follows (NAVAMSA_ONE_STEP).

Switch: `house_template.G1_FERTILITY_ONE_STEP` (default False).

**N1 (one variant, no second version). The nodal axis counts as one affliction in H7.C.82.**
Today `_SeventhBesiegedByMalefics` counts distinct natural malefics occupying or aspecting the
7th, so Ketu in the 7th plus Rahu's 7th aspect from the 1st (or the reverse) makes "two".
Under N1, Rahu and Ketu together count as one, whenever either afflicts the 7th. Every other
part of the condition is unchanged: the threshold of two, and the full-benefic relief.

Basis:
- The two nodes are always opposite, so one placement always brings the other's aspect. They
  are one testimony.
- The rule's cited classic case is Saturn + Mars (HTJAH-II:562), and its worked firings are
  Saturn + Mars and Mars + Ketu.

Switch: `house_7 combinations.NODE_AXIS_AS_ONE` (default False).

**Decision rule** (the same as M1 and Y1). For each variant alone:

- (a) Pool rule: real errors do not rise overall or in any book; within one does not fall; and
  exact rises or real errors fall.
- (b) Hold-out 3, scored once, against its sealed V0: real errors do not rise and within one
  does not fall. Hold-out 3 is scored only for a variant that passes (a).
- (c) An engine-blind doctrine review of the change, with the result going to the user.

A variant that fails is reported and held behind its switch. It is not adjusted.

If both pass (a), each goes to (b) on its own, and then the pair goes together. Because
hold-out 3 is scored once, the scoring order is fixed now: G1, then N1, then the pair, all in
one run, with V0 read from the sealed file.

If (a) passes but N1 changes no pool row, the pool cannot test it, and the hold-out decides.

## Addendum 17 (2026-10-30): G1 and N1 measured

**Correction to Addendum 16 (wording only, no number involved).** The N1 switch lives at
`doctrine/rule_sets/house_07_kalatra/combinations.NODE_AXIS_AS_ONE`. The last sentence of
Addendum 16 ("if (a) passes but N1 changes no pool row, the hold-out decides") cannot apply. A
variant that changes no row has no gain, so it cannot pass (a). It is not used.

**Pool, V0 → G1** (exact / within one / real errors):

| Scope | V0 | G1 |
|---|---|---|
| all | 260 / 349 / 40 | **251 / 351 / 38** |
| HTJAH-I | 54 / 70 / 13 | 50 / 70 / 13 |
| HTJAH-II | 65 / 90 / 5 | unchanged |
| NH | 141 / 189 / 22 | 136 / 191 / 20 |

**G1 passes rule (a).** Real errors do not rise in any book, within one rises, and real errors
fall overall. Thirteen rows move, all H5 children, afflicted → mixed:
- **Ten Raman calls afflicted.** They lose their exact match: HTJAH-I h5_04, h5_08, h5_09,
  h5_12, h5_18 and NH chart_37, 18, 20, 31, 22.
- **HTJAH-I.h5_13**, which Raman calls mixed, becomes exact.
- **NH.chart_67 and chart_48**, which Raman calls favourable, stop being real errors.

This is the B1-type trade: 9 exact for 2 real errors. In the ten afflicted rows the gate had
been carrying a denial that Raman reached from the house, its lord and the karaka, not from the
sphutas. So G1 exposes that the placement reading of the 5th is too lenient there.

**Hold-out 3, scored once** (`score_holdout … G1`, V0 from the sealed file, SHA as in
Addendum 11):
- G1 changes **none** of the 28 rows. The fixture's one children row is untouched. Result:
  8 / 19 / 9 of 28. Rule (b) holds only vacuously; the hold-out says nothing about G1.
- The current engine was also run as a control and matches G1 row for row.
- Side finding: it differs from the sealed V0 on one row. HPA.chart_35.8 H9 fortune moves from
  favourable to mixed (Raman afflicted). That move comes from the Addendum 15 citation repairs,
  which rerouted H9.C.35 to fortune. It is the first out-of-sample reading of those repairs:
  real errors 10 → 9, within one 18 → 19.
- Hold-out 3 has now been read once. The next variant needs a new sealed set.

**Rule (c), the doctrine review of G1, is pending.** It needs the printed HTJAH-I:5510-5611 on
the user's PC. Folder access to that corpus was refused in this session.

**N1** changes no pool row: 260 / 349 / 40 throughout. So it fails (a) as written. It was not
scored on hold-out 3, and it stays held behind its switch. Its case rests on Kanpur-like charts,
and the only scored firings of H7.C.82 involve Saturn or Mars.

**Status:** G1 and N1 are both held behind their switches (default False) until the user
decides. My recommendation is to keep G1 off until the review reads the sphuta passage itself.
The pool trade is real, but the hold-out cannot confirm it, and the cleaner fix is to encode the
relief clauses Raman prints, which this variant does not do.

## Addendum 18 (2026-10-30): variant G2, Raman's printed sphuta test, fixed before any G2 number exists

User go-ahead 2026-10-30 ("go ahead", on the offer to read the sphuta passage and review G1).
The passage HTJAH-I:5496-5633 was read verbatim from the corpus on the user's PC
(`how_to_judge_a_horoscope_raman/chapter_001_full-text-unsplit.md`). No G2 number exists yet.

**What the text says.**
- The test (5521-5527): Beeja strong in an odd sign and odd Navamsa, "aspected by or associated
  with benefics"; Kshetra the same in even sign and Navamsa. "Evil and impotent planets should
  not aspect these sensitive points, nor should evil planets occupy the 5th from" them; neither
  "should fall in a malefic sign"; "Rahu should never join" them.
- Chart 88 (male, 8-8-1912 19:35 IST, Bangalore; the same nativity as goldens HTJAH-I.chart_10):
  Beeja in Cancer, an EVEN sign, is judged strong: occupied by the Sun, a benefic sign, aspected
  by Jupiter and Saturn, Jupiter in the 5th from it, odd Navamsa (5543-5551).
- Chart 89 (female, 16-10-1918 14:20 IST; the same nativity as HTJAH-I.chart_12): Kshetra in
  Sagittarius, an ODD sign, is judged fertile: benefic sign, aspected by Jupiter, even Navamsa
  (5574-5577). For both: "the fertility cannot be in a pronounced manner … the number of
  children cannot be very large" (5577-5580).
- Chart 90 (sterile): Beeja in an even and malefic sign in Rasi and Amsa (Capricorn), aspected by
  Saturn (5602-5605).
- 5508-5509: weak Beeja with strong Kshetra means children late, not none.

**Finding on the shipped gate (rule (c) of Addendum 16, for G1 as well).** The shipped test
reads parity only, in both Rasi and Navamsa. Cast as printed, it reads Chart 88's Beeja WEAK
(Cancer) and Chart 89's Kshetra WEAK (Sagittarius), the two points Raman judges fertile. So the
shipped gate contradicts two of Raman's three worked sphuta charts. G1 keeps that test and only
softens its effect; it does not repair it.

**G2 (one variant, no second version). A sphuta point is strong exactly when Raman's printed
conditions hold.** For each point P (Beeja: odd parity wanted; Kshetra: even), with signs and
aspects whole-sign as everywhere in the engine, natural benefics Jupiter, Venus, Mercury, Moon,
natural malefics Sun, Mars, Saturn, Rahu, Ketu:

- Bars (any one makes P weak):
  1. P's Rasi sign is ruled by a natural malefic (Aries, Leo, Scorpio, Capricorn, Aquarius) (5526).
  2. Rahu occupies P's Rasi sign (5526-5527).
  3. A natural malefic occupies the 5th sign from P (5525).
  4. A natural malefic aspects P's sign and no natural benefic occupies or aspects it (5524-5525;
     Chart 88 is strong under Saturn's aspect because Jupiter also aspects).
- Requirements (all needed for P strong, when no bar applies):
  5. A natural benefic occupies or aspects P's Rasi sign (5521-5524).
  6. P has the wanted parity in its Rasi sign OR in its Navamsa sign (Charts 88 and 89 hold
     one of the two and are judged fertile).

The gate itself is unchanged: both points weak → afflicted; one weak → afflicted only on Arm A
or Arm B. The Saptamsa guard reads the same strong flags. Nothing reads the chart's sex, which
the engine does not have; that limit stays and is recorded.

Switch: `primitives.sphutas.G2_PRINTED_SPHUTA_TEST` (default False).

**Decision rule.**
- (a) The pool rule of Addendum 16, unchanged.
- (b) Worked charts: G2 must read Chart 88's Beeja strong, Chart 89's Kshetra strong, and Chart
  90's Beeja weak (from its printed longitudes, Sun 53°, Jupiter 192°, Venus 26°). Checked before
  the pool run; a failure stops the variant.
- (c) An engine-blind doctrine review of the G2 specification against the verbatim text.
- Hold-out 3 is spent (Addendum 17). There is no sealed out-of-sample set for G2, and that is
  reported with the result. Shipping is the user's decision.

## Addendum 19 (2026-10-30): G2 measured

**(b) Worked charts, checked first (cast with the Raman ayanamsa):**

| Raman's chart | Raman's verdict | Shipped (parity only) | G2 |
|---|---|---|---|
| 88, Beeja in Cancer (even), Navamsa odd, aspected by Jupiter | strong | weak | **strong** |
| 89, Kshetra in Sagittarius (odd), Navamsa Scorpio, aspected by Jupiter | fertile | weak | **fertile** |
| 90, Beeja 271° = Capricorn, a malefic sign | sterile | weak | **weak** |

G2 passes (b). The shipped test fails two of the three. Pinned in
`tests/raman_saab/primitives/test_sphutas.py::TestPrintedSphutaTest`.

**(a) Pool, V0 → G2** (exact / within one / real errors):

| Scope | V0 | G2 |
|---|---|---|
| all | 260 / 349 / 40 | **263 / 353 / 36** |
| HTJAH-I | 54 / 70 / 13 | 53 / 70 / 13 |
| HTJAH-II | 65 / 90 / 5 | unchanged |
| NH | 141 / 189 / 22 | **145 / 193 / 18** |

G2 passes (a): real errors rise in no book, within one rises, exact rises and real errors fall.
Five rows move, all H5 children:
- NH.chart_67 and chart_48, Raman favourable: afflicted → favourable (two inversions removed).
- NH.chart_57 and chart_52, Raman afflicted: favourable → afflicted (two inversions removed).
- HTJAH-I.h5_11 (Chart 101, five abortions, no surviving issue), Raman afflicted:
  afflicted → mixed. Its Raman reading is about survival of issue, not the sphutas.

This is unlike G1: G2 gains in BOTH directions, so it is not a softening.

**(c) Engine-blind review** (reviewer saw only the verbatim text and the three rule specs):
- Shipped parity-only test: UNSOUND, it inverts Charts 88 and 89.
- G1: UNSOUND, same trigger.
- G2: SOUND WITH CAVEATS. It reproduces all three worked charts from the printed facts, but the
  only negative case (90) fails every test, so the bars are thinly discriminated. Caveats the
  reviewer named, none of which G2 encodes (one variant, no second version):
  1. Mercury is an "impotent" planet with Saturn (5524), so Mercury should not rescue a point.
  2. Raman also reads the Navamsa: aspects there, and the 5th from the point in the Navamsa (88).
  3. A debilitated benefic does not rescue (90: "Jupiter neecha in Beeja Sthana").
  4. The majority-malefic-saptavarga denial (5607) is not encoded.
  5. When only the Navamsa parity holds, Raman says fertility is "not pronounced": a tempering,
     which G2 reads as plain strong.
  6. The gate's override is stronger than Raman's "simple rule … in the majority of cases"
     (5514-5515); and Raman reads one point per native by sex, which the engine has no input for.
  These are the ingredients of any later variant (G3), pre-registered separately.

**Hold-out:** none. Hold-out 3 is spent, so G2 has no out-of-sample check.

**Kanpur (the chart that started this):** unchanged under G2. Its Beeja is Cancer with a
Capricorn Navamsa (parity fails in both); its Kshetra in Libra has Rahu in the 5th from it. By
Raman's own printed test both points are weak, so the Kanpur children denial is faithful.

**Status:** G2 held behind `sphutas.G2_PRINTED_SPHUTA_TEST` (default False) for the user's
decision. Recommendation: ship G2 and drop G1.

## Addendum 20 (2026-10-30): G2 shipped, G1 dropped

User decision on the decision card: "Ship G2, drop G1".
- `sphutas.G2_PRINTED_SPHUTA_TEST` now defaults to True. The baseline is re-based 260/349/40 →
  **263/353/36** with lineage in `golden_accuracy_baseline.json`. The four former inversions
  (NH.chart_67, 48, 57, 52 H5 children) leave `real_errors`.
- G1 stays in the code, switched off for the record, and is not a candidate any more.
- `fidelity_variants.py` now measures from the shipped engine; the `PARITY` token restores the
  old parity-only test for comparison.
- The reviewer's caveats (Addendum 19, items 1-6) are open work for any later G3, which needs
  its own pre-registration and a sealed set with several H5 children rows and full degrees.

**Measured after shipping, reported for honesty (not a decision input; the user had already
decided).** G2 is more faithful on Raman's charts but HARSHER on ordinary ones:
- Across the 346 castable golden charts, 41 children verdicts moved: 30 toward afflicted, 11 away.
- On 600 random births (the harshness-diagnosis sampler, seed 20261030), both points weak rises
  313 → 438 (52% → 73%), and children afflicted rises 512 → 544 (85% → 91%).
- The cause is that Raman's printed test is strict per point: a malefic sign alone bars 5 of 12
  signs, and a benefic contact is required. Read from one chart for both sexes and fed into a
  decisive denial, it denies most charts. That is the reviewer's caveat 6 (the override and the
  missing sex input), not the point test itself. It is the next thing to fix, pre-registered on
  its own.

## Addendum 24 (2026-10-30): H9.A.18 repair, and speech variants S1 and S2, fixed before any S1 or S2 number exists

Numbered 24 because the audit thread holds 21-23.

**H9.A.18 (a rule repair, not a variant).** `_SunMoonTrineToMarsSaturn` required each luminary
to be in trine to Mars OR Saturn. Raman prints (HTJAH-II:7452-7453, read on the PC 2026-10-30):
"If the Sun and Moon be in trine to Mars and Saturn, the child will be abandoned by both
parents." The condition now requires both. Expected: no scored row moves (the rule fired on 19
goldens, 2 under the printed reading); the doctrine snapshot changes at the predicate level
only. Found on the Vaishali check, where the loose reading denied a father the family says is
well.

**Why speech.** On the Vaishali check (speech delay, confirmed by the family) the engine read
speech "mixed". Raman's own text was searched on the PC for every speech, Vak, dumb and stammer
line, and for Mercury near speech or intellect. Two findings bear on the engine:

1. HPA-19:150-151 prints a speech rule the engine does not encode: "Defective speech should be
   predicted if malefics are with the lord of the second or aspect it." HTJAH-I:2469 (the
   stricter stammer rule, already H2.C.25) is the only speech affliction encoded from Raman's
   Parashari books.
2. The engine's speech karaka is Jupiter, cited to HTJAH-I:2316, a line that names the 2nd
   house's significations and no karaka. Raman's one planet-to-speech statement is HPA-6:167-169:
   "Mercury — good and eloquent speech". In HTJAH-I Mercury is "the planet of intelligence"
   (4794, 14421, 15482) and "rules buddhi" (13852); Jupiter is the Dhana-karaka (2754). The
   comment in `significations.py` citing HTJAH-I:2734 for Mercury and speech is wrong: that
   line is about the eyes in Chart 39.

**S1 (fixed now).** A new evaluable rule on H2 speech, afflicted branch only: a natural malefic
(Sun, Mars, Saturn, Rahu, Ketu), other than the 2nd lord itself, occupies the 2nd lord's sign or
aspects the 2nd lord by Raman's drishti (nodes by the 7th only). Source HPA-19:150. Measured by
adding the rule at run time; the shipped engine is untouched.

**S2 (fixed now).** The speech karaka is Mercury instead of Jupiter; nothing else changes.

**Decision rule.** Unchanged (`passes()`): real errors may not rise in any book, within-one may
not fall, and exact must rise or real errors fall. Reported for each: pool figure, the three
scored speech rows (NH.chart_25, chart_26, chart_33; Raman says favourable on all three; V0
reads mixed, mixed, afflicted), and S1's firing rate on the goldens.

**Predictions, written before measuring.** S1 fires on most charts (five malefics, two contact
channels); on the three scored rows, all favourable in Raman, it can only hurt or do nothing, so
S1 is expected to FAIL the rule and, if it fires on more than half the charts, to be a candidate
for a descriptive record rather than an evaluable one. S2: no prediction of direction; the
pool has only three speech rows, so neither result can carry much weight. No hold-out exists
for either; any ship decision is the user's.

## Addendum 25 (2026-10-30): H9.A.18 repair, S1 and S2 measured

| | exact | within one | real errors |
|---|---|---|---|
| V0 (after the H9.A.18 repair) | 263 | 353 | 36 |
| S1 | 263 | 353 | 36 |
| S2 | 263 | 354 | 35 |
| S1+S2 | 263 | 354 | 35 |

- **H9.A.18 repair**: pool unchanged, as predicted. The doctrine snapshot moved at the predicate
  level only: 26 golden charts stop firing H9.A.18, no verdict changes (re-frozen with a note).
- **S1**: no scored row moves; it fires on 213 of 346 castable goldens (62%), as predicted. It
  FAILS the decision rule (nothing improves). Held. Firing on six charts in ten makes it a
  non-discriminating indication on its own; if encoded at all, it belongs as a descriptive
  record, which is a separate decision.
- **S2**: PASSES. One row moves, NH.chart_33 H2/speech, Raman favourable: afflicted → mixed
  (an inversion becomes a one-step miss). No book worsens. The pool holds only three speech
  rows, so this is thin evidence; the stronger case for S2 is the citation itself (the
  shipped Jupiter karaka is cited to a line that names no karaka; Mercury is Raman's printed
  speech planet at HPA-6:167-169).
- **Vaishali** (the real chart that prompted this; not part of the decision): speech reads
  mixed under V0, S1 and S2 alone, and afflicted only under S1+S2. Recorded, not used.

Status: S2 waits for an engine-blind review and the user's decision. S1 held.

## Addendum 26 (2026-10-30): engine-blind review of the H9.A.18 repair, S1 and S2

- **H9.A.18 repair: SOUND WITH CAVEATS.** The "both luminaries in trine to both malefics"
  reading is the printed one; a pair-to-pair reading reduces to the same check, and the old
  any-of reading had no textual basis. Caveats: the same sign is not counted as a trine (now
  stated in the docstring); the sentence is about abandonment by both parents, so the H4
  mother matter lacks its mirror rule, and the rule must not feed death or longevity scoring.
- **S2: SOUND WITH CAVEATS.** The Jupiter citation (HTJAH-I:2316) names no karaka, and the
  HTJAH-I:2734 comment is about eyesight, so both are unsound. Mercury is the planet Raman's
  text supports (HPA-6:167-169; HTJAH-I:13852). Caveats: Raman never uses the word "karaka" for
  Mercury and speech, so the entry should cite HPA-6 as a planetary signification; dropping
  Jupiter is an interpretive choice that must be recorded. The reviewer also flagged that the
  H2 "vision" entry cites 2734 for Jupiter as Netra-Karaka, which that line does not say.
- **S1: SOUND WITH CAVEATS; holding it is reasonable.** One malefic suffices; "it" most
  naturally means the lord. Leaving out the waning Moon and an afflicted Mercury as malefics
  is a narrowing that would need its own citation.

## Addendum 27 (2026-10-30): S2 shipped

User decision 2026-10-30 ("Ship Mercury for speech"). `significations.py`: the H2 speech
signification's primary karaka is Mercury, cited `HPA-6:168`, with no secondary karaka (as
measured). The wrong HTJAH-I:2734 comment is replaced. Pool 263/354/35; baseline re-based,
NH.chart_33 H2/speech removed from `real_errors`.

What moved on the 346 castable goldens (doctrine snapshot, re-frozen with a note):
- H2 speech: 130 verdicts change, 79 worse and 51 better (favourable 177 → 153, mixed 127 →
  145, afflicted 42 → 48).
- H2 headline rollup: 75 change, all worse (favourable 166 → 114, afflicted 54 → 82). The
  rollup does not mask an afflicted sub-matter, so a weak Mercury now pulls the 2nd house down.
  No scored H2 row other than speech moved. This harshness is a consequence to watch; any
  change to how the rollup weighs speech needs its own pre-registration.

Still open: the H4 mother mirror of H9.A.18; the H2 vision entry's karaka citation
(HTJAH-I:2734 does not name Jupiter as Netra-Karaka); S1 held.

## Addendum 21 (2026-10-30): hold-out 3 re-sealed, one birth time corrected from the page scan, still unread

The user supplied page scans of *Hindu Predictive Astrology* (310 jp2 images; ch.35 is scans
0280-0286, book page = scan number - 15). The scans are a slightly different edition from the
archive.org text in the corpus: 20 practical horoscopes instead of 21 (the text's No. 11, male,
29 July 1850, Bangalore, is absent, so the numbering shifts by one after No. 10). The other
charts' birth data agree, and the scans confirm the three uncertain digits recorded in the
extraction (77°25' E for Nos. 2, 5 and 6; 12° N for the text's No. 17; 75°30' E for the
text's No. 18).

One correction: the text's **No. 5** (female, 12 June 1909, 77°25' E, 13° N) reads "4-25 p.m.";
the scan (0282, book p.267) prints **"4-25 a.m."**. Cast at 04:25 LMT, the chart matches every
sign Raman printed (Ascendant, Sun and Rahu in Taurus); at 16:25 the Ascendant is Scorpio, which
is why the chart had failed the sign check and was scored from its printed signs. User decision
2026-10-30 ("Fix it and re-seal, unread"): the time is corrected in `r3_hpa_merged.json`
(recorded in the chart's `fill_notes`) and the hold-out rebuilt with
`build_holdout --stamp 2026-10-30`.

Checks, none of which read a verdict: rebuilding from the old extraction reproduced the old
fixture byte for byte; in the new fixture the only change is that HPA.chart_35.5 is now cast
from its birth data (no stated positions) and every record's `review_note` stamp; no label
changed (still 28 rows, 19 afflicted, 9 favourable). Five charts are now used from their printed
signs (35.3, 35.4, 35.6 Lagna; 35.10, 35.17 Venus; 35.17's cast Venus is 0.3° into Virgo and the
scan still prints Leo). The V0 verdicts are rewritten, unread, with the CURRENT engine (the
rule-defect repairs of Addendum 15 shipped after the first seal, so V0 is again the shipped
engine): `docs/raman_saab/holdout3_v0_verdicts_sealed.json`,
SHA-256 `103509cafe094f2bb1dfcb746249469d17ad0e3c9f70ef87983eb150fb35bc19`. This supersedes the
Addendum 11 hash. Side note, no action: for Henry Ford (text No. 14, scan No. 13) the scan prints
3 p.m. where the text prints 2 p.m.; Ford is scored from HTJAH-II's own data, not from HPA.

## Addendum 22 (2026-10-30): hold-out 4 from the page scans of *Three Hundred Important Combinations*, fixed before any hold-out 4 verdict exists

User instruction 2026-10-30 ("go ahead": find more unused Raman worked charts on the PC). The
user's scans of 3HC (350 jp2 pages, `300_important_combinations_b.v._raman_jp2.zip`) cover the
20 charts that hold-out 1 (Addendum 1) had to reject although they carry Raman conclusions: 12
whose printed dasa balance disagrees with our cast (19, 24, 32, 60, 66, 84, 104, 124, 128, 134,
135, 141), one with no readable balance (13), and seven with missing or garbled birth data or
diagrams (44, 46, 78, 80, 85, 99, 107). The OCR text had scrambled their Rasi diagrams.

**Positions.** Two independent readers transcribed each chart's birth line, dasa balance and
Rasi diagram from the scans; the two readings agree on all twenty (differences were spelling of
abbreviations only), each with nine grahas once and one Lagna. Every chart is scored from
**Raman's printed signs** (the stated-positions path of `build_holdout`, `deg` unset), the rule
already used for HPA charts whose cast misses a printed sign: where our ephemeris and Raman's
own printed chart disagree, Raman's printed chart is what he judged. Mandi, printed in three
diagrams, is not a graha and is not used. The dasa balance is recorded but not used to accept or
reject, because no cast is used.

**Conclusions.** The original engine-blind 3HC extraction (`3hc_a/b/c.json`, from the OCR text)
is paired with a second engine-blind extraction made from the page images
(`r4_3hc_scan_conclusions.json`). Only a (house, signification, verdict) given identically by
both is scored; a disagreement is dropped as contested and listed. The builder's usual dedupe
against goldens and hold-outs 1-3 applies.

**Sealing.** V0 verdicts (the shipped engine, HEAD at sealing) are written unread and their
SHA-256 recorded in Addendum 23. Hold-out 4 is scored once, under the same rules as
hold-out 3, for the next pre-registered variant; hold-outs 3 and 4 may be reported together and
separately. Nothing here changes the engine or the 389-row pool.

## Addendum 23 (2026-10-30): hold-out 4 sealed

Positions: `holdout_extractions/r4_3hc_scan_positions_a.json` and `_b.json` (two readers, all
twenty Rasi diagrams agree). Conclusions: `r4_3hc_scan_conclusions.json` (page-scan extractor)
paired with the original `3hc_a/b/c.json`; merged as `3hc_r4_scan_merged.json`. 29 conclusions
were given identically by both; dropped as not identical (mapping differences, no direction
contradicted): chart 13 H12 moksha vs H9 dharma, chart 44 H10 profession_authority vs
status_honour (chart 44 is left with none), chart 46 H10 career and chart 134 H8 death (given by
one extractor only). Chart 84's printed signs equal a golden chart's (the same native), so it is
dropped by the dedupe. `build_holdout._EARLIER` now also lists hold-out 3.

Fixture `tests/fixtures/raman_holdout4_sealed.jsonl`: 18 natives, 18 records, **28 scored rows**
(19 favourable, 8 afflicted, 1 mixed), all from Raman's printed signs. V0 verdicts written,
unread, to `docs/raman_saab/holdout4_v0_verdicts_sealed.json`,
SHA-256 `223b8ae34d3f392eb452be2a5e7a4a3a66951dabb2d385bd0f4416842cc4d6d9`.
Limit: positions are signs only (no degrees), so degree-dependent rules (combustion, exact
aspects, avasthas) read every graha at 15°, as for every printed-signs chart before.

## Addendum 28 (2026-10-30): reconciling the two branches

This branch and the fertility branch (`claude/project-thread-yj2a5g`) both wrote addenda on
2026-10-30. Theirs are 16-20; this branch's were renumbered 21-23 when the two were merged.
Two facts the merged record must state plainly:
- **Hold-out 3 is spent.** The fertility branch read it once at 05:53 (Addendum 17, against the
  Addendum 11 seal). The re-seal in Addendum 21 came at 06:11, after that read, so its words
  "still unread" were wrong when written. The corrected birth time stands as a data fix; the set
  gives no further out-of-sample test.
- **Hold-out 4's V0 predates G2** (Addendum 20). Any later score on hold-out 4 must say so, or
  re-run V0 with the current engine at scoring time and report both. Hold-out 4 has signs only
  (no degrees), so it cannot test G2 or any sphuta-based fertility variant.
User decision 2026-10-30: hold-out 4 stays sealed until a further fix is ready to be tested
together with R5 in one reading.

## Addendum 34 (2026-10-31): label re-review of the 35 real errors with matched controls, and variant BS1 (borrowed buckets carry placements only), both fixed before any outcome

User request 2026-10-31 ("FIX ALL THESE", of the 35 pool real errors in `ERROR_STUDY_2026-10-30.md`).
Numbered 34 because the other branch (`claude/project-thread-1ztlhb`) has used 29-33. Hold-outs
are not read or touched here; Addendum 33 on that branch governs hold-outs 4 and 5.

**Admitted position.** These 35 rows have been studied repeatedly; the ceiling check found that
logic fitted to the pool does not carry out of sample. Nothing below is a per-row patch. Part A
re-checks the answer key in BOTH directions; part B fixes a design defect found while reading the
rules that fire on these rows, and is measured on all 389 rows.

### Part A. Label re-review (protocol fixed before any reviewer output is read)

Rows: the 35 pool real errors plus 35 controls drawn at random (seed 20261031) from the 263 exact
matches, stratified by book in the same proportions (NH 17, HTJAH-I 13, HTJAH-II 5). The 70 rows
are shuffled and split into two packets. Four reviewers, two per packet, each engine-blind:
they see only the chart name, house, matter and Raman's cited passage (60 lines of context each
side, with the full book text available), never the gold label, the engine verdict, or which
group a row is in. Each returns favourable / mixed / afflicted / none, with Raman's words.

Outcome per row, the same rule for errors and controls:
- both reviewers give the same label, different from gold, confidence medium or high → proposed
  relabel;
- both give `none` → proposed removal from the scored pool (back to DRAFT; Raman states no
  conclusion on that matter);
- the reviewers disagree and neither agrees with gold → held for a third engine-blind reader;
- otherwise the gold label stands.
Reported: proposed changes in each group separately. Changes are proposals for the user; none is
applied without sign-off. If the error group yields changes and the control group does not, the
report says plainly that a one-sided review can still flatter the score.

### Part B. Variant BS1: a borrowed rule bucket contributes only house placements

**The defect.** Each sub-matter judges the fired rules whose `signification` tag is in its
`rule_tags`. In H4 the shared tag is a pure bridge (`mother_home`), holding only the lord-in-house
and planet-in-house rules, so every H4 matter shares the general placements and keeps its own
combinations. The module docstrings state that this is the intended design elsewhere too ("so it
aggregates the shared placements AND its own combos", `house_05_putra/combinations.py`). But in
eleven houses the shared tag is another matter's own bucket, so that matter's specific
combinations leak into every sibling matter. Examples: Raman's poverty and debt combinations
(HTJAH-II:16373-16424, tagged `loss_moksha`) vote on moksha, the left eye and imprisonment; the
Dhana yogas and the Dwirdwadasa wealth rule (tagged `wealth`) vote on speech and eyesight;
the gains combinations vote on elder brothers. A combination's printed result is about its own
matter ("one will be poor", HTJAH-II:16410), not about its neighbours'.

**BS1 (fixed now).** In `_bucket_fired`, when a fired rule's tag is another matter's own key in
the same house (a borrowed bucket), the rule counts only if its group is `lord_in_house` or
`planet_in_house`. A matter's own bucket, and any pure bridge bucket that is no matter's key
(`mother_home`), count in full as now. Uniform across all twelve houses, no exemptions. Flag
`house_template.BS1_BORROWED_PLACEMENTS_ONLY`, default off.

**Decision rule.** Unchanged: `fidelity_variants.passes()` against V0 = the engine at bd8c28a3
(263/354/35). Reported: figure by book, every row that moves.

**Predictions, written before measuring.** Only sub-matters that borrow a bucket can move (on the
pool: H1 body/health, H2 speech/vision, H3 courage, H6 sub-matters, H7 spouse/partnership, H8
death, H9 father/dharma/long journeys, H10 profession and status, H11 elder siblings/acquisitions,
H12 all but loss_moksha). Removing borrowed combinations removes votes on both sides, so the
direction is uncertain. H9 father (24 rows) and H8 death (15) are the largest groups and the most
likely to cost exact matches. A FAIL is quite possible. A pass is in-sample evidence only.
