---
title: "The Certified Cohort — design & governance for a fresh real-outcome laboratory"
kind: plan
topic: validation
measured: false
updated: 2026-07-24
words: 2193
tags: [raman-saab, plan, validation]
---
# The Certified Cohort — design & governance for a fresh real-outcome laboratory

*Design document, 2026-07-24. Nothing is collected until this design is reviewed, the governance
and legal pieces are actually stood up, and the operator signs off. This is the artifact to
critique, not a built system.*

> This is the "rigorous version" that `REAL_OUTCOME_GENERALIZATION.md → What a rigorous version
> needs (a research program, not a clause)` named and deferred. The astrobank program measured the
> engine against 22,177 pre-existing charts and found the generalization axis null — but that null
> keeps two honest escape hatches open: **the birth times were poor** (the medini charts were
> 100% default-time) and **the sample was selected on the outcome** (celebrities). This program
> closes both at the source. Its job is *evidential closure*, not the promise of a discovery: the
> mechanism finding (median chart carries 19 afflicted + 31 favourable significations) predicts a
> null even under perfect data. A clean dataset makes whichever result we get — null or signal —
> uncontestable. Per the Prime Directive's last clause: *measure honestly, report both.*

---

## 1. What this is, and what it is not

**Is:** a standing, self-collected, birth-certificate-certified cohort of consenting people, whose
frozen-engine charts are computed at intake and whose life histories are captured through a broad,
hypothesis-blind inventory. Matched-discordant-pair analyses run against whichever outcome domain
accrues enough certified cases to be powered. Outcome-agnostic at intake; hypothesis-specific,
pre-registered, at analysis.

**Is not:** (a) a predictor or a reading service — subjects receive no chart interpretation that
could bias what they report; (b) an engine-tuning input — the same firewall that governs the
astrobank lab applies: **no constant, threshold, rule, or mapping in the engine is ever tuned from
this data**; (c) a claim to general-population inference — a volunteer cohort is self-selected (see
§4), so findings speak to internal validity, not universality.

## 2. Locked design decisions

| # | decision | value | rationale |
|---|---|---|---|
| D1 | Acquisition | **Fresh certified self-collection** | The only path that yields real, minute-accurate birth times we control — the one thing the astrobank corpus never had. |
| D2 | Ambition | **Standing laboratory** | Build the pipeline once; let domains activate for analysis as they cross their power threshold. |
| D3 | Intake target | **Outcome-agnostic ("whatever we can extract")** | A broad neutral inventory, not one pre-chosen outcome. Keeps intake hypothesis-blind and lets the data decide which domains power up. |
| D4 | Primary inference | **Matched discordant pairs** | Holds era + geography + sex constant *by construction* — the two confounds that killed G1 (cohort composition) and G2 (geography) vanish. Also the *fairest* test: it asks the differential question (§5). |
| D5 | Cohort scope | **Living first, deceased arm as phase 2** | Living self-report cannot include one's own death, so death/longevity + the suicide/8th confirmatory are deferred to a phase-2 deceased arm (next-of-kin / obituary), which carries its own consent track (§7.4). |
| D6 | Instrument | **The ratchet-frozen engine, unchanged** | The chart judgment is already the audited, pre-registered instrument. Only intake, certification, and the inventory are new. |

## 3. Threat model — the failure modes this design must defeat

Each is a mistake the prior programs actually made, turned into a requirement.

1. **Poor birth times** → certified, tiered, minute-accurate times from uploaded certificates (§6).
2. **Selection on the outcome** → enrollment is on birth data alone; outcome status is captured
   *after* enrollment, never a condition of it.
3. **Era confound (slow planets encode birth decade)** → controlled *structurally* by matching on
   birth era, not by regression.
4. **Coarse event dates** → the inventory captures day-precision dates with document proof where
   possible; year-only events are flagged and excluded from timing analyses.
5. **Ghost / immortal-time exposure** → living-cohort exposure windows are capped at the intake
   date; no window runs past last-known-status.
6. **p-hacking** → per-domain pre-registration (direction, mapping, statistic, threshold) committed
   before that domain's data is unblinded; the astrobank sham-gate, permutation-null, and BH
   machinery reused verbatim.
7. **Ascertainment / demand bias** — *the single biggest threat to any self-collected design*, §4.

## 4. The ascertainment problem, and why self-selection is survivable

The instinct is that astrology-interested volunteers are a fatally biased sample. The precise truth
is more forgiving and more demanding at once:

- **Self-selection threatens generalizability, not internal validity.** Belief cannot cause a natal
  chart — the chart was fixed at birth, before the subject ever heard of this study. For a
  within-pair *chart → outcome* test, a confounder would have to correlate with both the chart and
  the outcome; belief correlates with neither. A believer-heavy sample can still cleanly answer
  "does the more-afflicted chart, within a matched pair, carry the outcome." What we forfeit is the
  right to say "this generalizes to all humans." That is an acceptable price.
- **Ascertainment bias IS fatal and must be engineered out.** If a subject knows their chart and
  knows which outcome we test, self-report can drift to fit; lives that "matched" may preferentially
  enroll. Three non-negotiable defenses:
  1. **Hypothesis-blind inventory** — a broad, neutral life-events questionnaire that never reveals
     which house, karaka, or claim is under test. No chart interpretation is shown to the subject.
  2. **Documentable-outcome preference** — proof upload (decree, diagnosis date, record) is
     solicited for every material event; self-report is accepted but *tiered below* proof (§6.2),
     and timing analyses restrict to proof-tier events.
  3. **Pre-registered mapping** — the category→house→direction mapping is frozen and reviewed
     before a domain is unblinded, so no post-hoc fishing is possible.

## 5. The matched-discordant-pair protocol (primary analysis)

For an outcome `O` mapped (pre-registered) to house `H`, direction `dir`, and a continuous
engine-derived affliction score `s_H`:

1. **Pairing.** Form discordant pairs — one subject with `O`, one without — matched on the
   **confounds, not the chart**: birth era band, birth geography band (lat/lon), sex, and any
   base-rate covariate the domain requires (e.g. religion/region for divorce base rates). Matching
   holds era + geography + sex fixed; within a pair the two subjects still differ in birth *time*,
   hence in ascendant, house cusps, dasha state, and therefore in `s_H`. **That residual is the
   variable under test.** (Match on confounds only — matching on the chart itself would erase the
   signal we are trying to detect.)
2. **Statistic.** Conditional logistic regression of `O` on `s_H` across matched sets (equivalently
   a Wilcoxon signed-rank / sign test on within-pair `s_H` differences), one-sided in `dir`.
   Reported as effect size + person-clustered bootstrap CI.
3. **The fairness of it.** The flexibility census says every chart carries both poles, so any
   *absolute* test ("has an afflicted 8th") is diluted toward null because nearly everyone qualifies.
   The matched design escapes part of that by testing the *relative* rank: of two people identical
   in era/place/sex, does the one with the **more** afflicted `H` carry `O`? This is the sharpest
   honest question the doctrine can be asked. If it loses here, the null is total; if it wins here,
   the effect is real.
4. **Gates (reused from astrobank, unchanged):** a sham mapping must test null before any real
   domain is read; off-target specificity (the mapped house must out-rank the other eleven);
   within-stratum permutation null; BH q=0.10 across the domain family; minimum-effect threshold.
5. **Pre-registration.** Every domain's `(mapping, dir, statistic, matching keys, power threshold)`
   is committed to a dated pre-registration file before that domain's outcomes are unblinded.

**Flagship domain-in-waiting (first to pre-register): marriage / divorce.** Registry-documentable,
strong base rates, and it delivers a direct, uncontestable test of *Kuja dosha* — the tradition's
most famous marriage claim, which the astrobank raw-geometry test already found null (OR 1.09) and
which a certified matched-pair design would settle beyond appeal.

## 6. Certification & the data model

### 6.1 Two-store privacy architecture (built before any record is collected)

- **Identity vault** (restricted access): legal name, full birth date/time, certificate image,
  contact, consent record. Keyed by a random `subject_id`. Certificate images are encrypted at rest
  and, under data minimization, **purged after the birth time is extracted and tier-rated** unless
  the subject consents to retention for re-audit.
- **Analysis store** (working data, no direct PII): `subject_id`, frozen-engine chart features,
  matching covariates (era band, geo band, sex), and the tiered life-events inventory. No name, no
  contact, no raw certificate.
- **Withdrawal** = delete the vault row and purge the analysis row by `subject_id`. Retention,
  access logging, and breach response are specified in the governance annex (§7).

### 6.2 Certification tiers (mirroring Rodden ratings)

| tier | meaning | source |
|---|---|---|
| **AA** | time extracted from the uploaded birth certificate / hospital record | primary document |
| **A**  | documented but secondary (baby book, official record citing the time) | secondary document |
| **B**  | from memory / family report, no document | self-report |
| — (excluded) | no time, or round-hour/noon default | not usable for chart-level tests |

Jurisdiction reality: some registries record birth time (e.g. much of India, many US states),
others do not (e.g. UK certificates generally omit it). Subjects from no-time jurisdictions fall to
tier B or supply a hospital record for AA. Chart-level analyses are run at **AA primary**, with A/B
as a pre-registered sensitivity ladder — exactly as the astrobank tiers were used.

### 6.3 The hypothesis-blind life inventory

Broad, neutral, dated, domain-tagged, proof-solicited — and deliberately *not* organized around any
house or claim. Domains (living cohort): family & marital (marriages, divorces, separations, dates),
children & fertility, health (major diagnoses + dates), legal (incarceration, bankruptcy), education
& career (milestones, dates), residence/migration, notable accidents. Each event carries: type,
date + precision, and an optional proof upload that sets its evidence tier. The inventory is
reviewed to ensure no wording telegraphs the mapping under test.

## 7. Governance & privacy (load-bearing, prior to collection)

1. **Informed consent** — plain-language purpose, data collected, storage, retention, withdrawal
   rights, and the explicit statement that no personalized astrological reading is provided.
2. **Data minimization** — collect only what a matched-pair analysis needs; purge certificate
   images post-verification by default.
3. **PII isolation** — the two-store split (§6.1); analysis is never run over raw PII.
4. **Deceased-arm consent track (phase 2)** — decedent research follows a distinct model
   (next-of-kin authorization and/or public-record/obituary sourcing); it is *not* covered by the
   living-cohort consent and gets its own governance review before phase 2 opens.
5. **Ethics review** — an IRB-equivalent review is completed before any results are published
   externally.
6. **Engine firewall** — results here are a monitoring axis only; no engine parameter is tuned from
   them, ever. Any engine change they might *motivate* still goes cite → bphs-doctrine-reviewer →
   zero-golden-regression, identical to the astrobank governance.
7. **Security** — encryption at rest and in transit, access logging on the vault, documented breach
   response. Specific hosting/security posture is an open item (§9).

## 8. Power model — when a domain "activates"

Sample size is set by the smallest effect we're willing to bet exists. Order-of-magnitude discordant
pairs needed for 80% power (one-sided α=.05):

| target effect (within-pair) | ~pairs needed | interpretation |
|---|---|---|
| AUC ≈ 0.60 | ~150 | a "you could almost feel it" effect |
| AUC ≈ 0.55 | ~600 | a real but modest effect |
| AUC ≈ 0.53 | ~1,700 | the size of the surviving suicide thread |

Because everything measured so far is null and the one live thread sits at ~0.52–0.53, the honest
posture is to **power for small effects** — thousands of certified pairs per domain. A domain is
declared "activated" (its pre-registered analysis runs, once) only when it crosses its committed
pair-count threshold at AA tier; until then its status is "accruing," reported but unread.

## 9. Phasing & open items

**Phase 0 (now):** this design; then the marriage/divorce pre-registration file + a consent/privacy
annex + legal/ethics sign-off. No collection yet.
**Phase 1:** living-cohort intake MVP — consent flow, certificate upload + verification + tiering,
frozen-engine chart at intake, hypothesis-blind inventory, two-store persistence.
**Phase 2:** the matched-pair analysis engine (outcome-agnostic; reuses sham/permutation/BH/
specificity machinery), provable on synthetic data before real data exists.
**Phase 3:** first domain activation (marriage/divorce) once powered; result appended to
`REAL_OUTCOME_GENERALIZATION.md` regardless of outcome.
**Phase 4:** the deceased arm — reopens longevity + the suicide/8th confirmatory under its own
governance.

**Open items requiring decisions before Phase 1:** recruitment channel (who submits, and how we
reach a sample large and diverse enough to form matched pairs); jurisdiction mix for birth-time
availability; hosting & security posture for PII; the legal/ethics review path; and whether
certificate images are retained (re-auditability) or purged (minimization) by default.

## 10. What is reused vs genuinely new

- **Reused, unchanged:** the frozen engine and its house/affliction scoring; the pre-registration
  discipline; the sham gate, permutation null, off-target specificity matrix, BH correction; the
  generalization-ratchet governance; the engine firewall.
- **Genuinely new:** consented certificate-based intake; the certification/verification/tiering
  pipeline; the hypothesis-blind life inventory; the two-store privacy architecture; the
  matched-discordant-pair analysis layer.

The scientific machinery already exists and is battle-tested. This program's real work is a
**consented, hypothesis-blind, certification-tiered data pipeline** feeding it clean input — the one
thing every prior real-outcome test lacked.
