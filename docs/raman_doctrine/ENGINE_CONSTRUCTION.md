---
title: How the Engine Was Built — the patient, house-by-house construction
tags: [moc, raman-doctrine, engine, architecture]
updated: 2026-07-13
---

# How the Engine Was Built

*The validation reports ([`FULL_REPORT.md`](FULL_REPORT.md), [`VALIDATION_SUMMARY.md`](VALIDATION_SUMMARY.md))
answer "how well does it do?". This one answers "how was it actually coded?" — the architecture of the
engine itself, how Raman's method became executable code **one house at a time**, and how 1,913 classical
rules were encoded by hand across ten source books. The per-increment ledger is
[`HOUSE_SCHEME_AUDIT.md`](HOUSE_SCHEME_AUDIT.md); this is the map that makes it readable.*

---

## 1. Three layers

The engine is three layers stacked, each independently testable:

```
  BIRTH DATA / SIGN DIAGRAMS
        │
        ▼
  ①  CHART LAYER          ephemeris → RamanChart (Rāśi + 16 vargas, in Raman's ayanāṁśa)
        │                 app/core/ephemeris_engine.py · app/medini/doctrine/raman_chart.py
        ▼
  ②  DOCTRINE LAYER       judge each house the way Raman does, and fire the encoded sūtras
        │                 app/medini/doctrine/domains/house_judgment.py (1,684 lines)
        │                 app/medini/doctrine/engine/{predicates,evaluate}.py (the rule DSL)
        │                 data/raman_doctrine/compendium/*.jsonl (1,913 encoded rules)
        ▼
  ③  VALIDATION LAYER     score the doctrine layer against Raman's own printed verdicts
                          app/medini/doctrine/validation/*.py
```

The craft is almost all in layer ②. It has two halves that were built in parallel and then joined:
the **house-judgment scheme** (Raman's procedure, turned into a scorer) and the **rule compendium**
(his atomic statements, turned into data). They stayed separate for a long time — until increment 17
finally wired the compendium into the scores (see §5).

---

## 2. The house-judgment scheme — Raman's own method as code

Raman does not judge a house with one number. In *How to Judge a Horoscope* he judges it from several
independent lines of testimony and synthesises them. The engine mirrors that structure exactly.

### 2.1 The per-house constants (encoded verbatim from his chapters)

Each house carries four hand-encoded facts, taken from the opening lines of its HTJAH chapter
(`house_judgment.py:56–100`):

| # | signification (ch. opening) | **kāraka** (natural indicator) | its Sanskrit name | HTJAH chapter |
|---|---|---|---|---|
| 1 | body, health, temperament, longevity | Sun | Thanukāraka | ch. IV |
| 2 | family, speech, food, wealth | Jupiter | Dhanakāraka | ch. V |
| 3 | siblings, courage, communication | Mars | Bhrātrukāraka | ch. VI |
| 4 | mother, home, lands, education | Moon | Mātrukāraka | ch. VII |
| 5 | children, intelligence, pūrva-puṇya | Jupiter | Putrakāraka | ch. VIII |
| 6 | enemies, disease, debts, litigation | Mars, Saturn | Śatrukāraka | ch. IX |
| 7 | spouse, marriage, partnerships | Venus | Kalatrakāraka | ch. XI |
| 8 | longevity & death, obstacles, occult | Saturn | Āyuṣkāraka | ch. XII |
| 9 | father, fortune, dharma, preceptor | Jupiter, Sun | Pitṛkāraka | ch. XIII |
| 10 | profession, status, karma, authority | Sun, Mercury, Jupiter, Saturn | Karmakāraka | ch. XIV |
| 11 | gains, elder siblings, desires | Jupiter | Lābhakāraka | ch. XV |
| 12 | loss, expenditure, mokṣa | Saturn, Ketu | Vyayakāraka | ch. XVI |

Two houses take **multiple kārakas** because Raman names more than one significator (the 10th has
four — his four "karmic" planets). The engine grades each and takes the strongest.

### 2.2 The three graded factors

For any house, the engine produces three `FactorVerdict`s, each judged on the same criteria but from a
different vantage:

- **Bhāva** — the house *as a place*: who occupies it, who aspects it, is it hemmed between malefics
  (`_assess_bhava`, `house_judgment.py:1088`).
- **Lord** — the *ruler* of the house, judged as a planet: its dignity, placement, aspects,
  conjunctions, combustion (`_assess_lord` → `_assess_planet`, `:1182` / `:1001`).
- **Kāraka** — the *natural significator* from the table above, judged the same way (`_assess_karaka`,
  `:1187`).

### 2.3 Raman's six influence factors

Beyond the three graded factors, Raman lists (HTJAH p. 44) the ways a planet can **influence** a
house. The engine encodes all six (`_influence_factors`, `:1298`; `FACTOR_DESCRIPTIONS`, `:392`):

> **(a)** lord of the house · **(b)** aspects the house · **(c)** posited in the house ·
> **(d)** aspects the lord · **(e)** in association with the lord · **(f)** lord of the house *from the
> Moon* (the Chandra-Lagna view — the engine's `chandra` sub-verdict).

A planet satisfying more of these ranks higher as an "influencer," which drives both the written
conclusion and the timing sub-verdict (a period lord that influences the house *activates* it).

### 2.4 Functional roles — the gate before every judgment

The single most important thing the engine computes before it judges anything is whether a planet is a
**friend or an enemy for this particular ascendant** (`app/core/functional_roles.py`, BPHS Ch. 3).
This is a per-chart question, not a per-planet property:

> Saturn is the **yogakāraka** (best planet) for a Taurus or Libra ascendant, but a **functional
> malefic** for Cancer or Leo. Same planet, opposite disposition.

Each visible planet gets its roles — **yogakāraka** (rules one kendra + one trikoṇa), **māraka** (rules
2nd/7th), **badhakeśa** (obstruction lord, by ascendant modality), **functional benefic/malefic** — and
every aspect, conjunction and lordship reads off this table first. Getting this layer right is what lets
the engine say "this malefic aspect actually *helps* here," which is central to Raman's judgments.

### 2.5 From findings to a grade

Each assessor emits a list of **`Finding`s** — `(text, delta, frame, criterion)` — one per piece of
testimony, e.g. `("exalted", +1.6, "Rasi", "dignity")` or `("placed in the 8th (dusthāna)", −1.0,
"Rasi", "placement")`. The ten criteria: `dignity, placement, lordship, aspect, conjunction, kartari,
vargottama, combustion, ashtakavarga, sutra`.

The weights are Raman's decoded testimony, not fitted parameters
(`_DIGNITY_W`/`_W`, `house_judgment.py:488`):

```
_DIGNITY_W = exalted +1.6 · own +1.2 · friendly +0.8 · inimical −0.8 · debilitated −1.6
_W         = kendra/trikona +1.2 · vargottama +1.2 · dusthana −1.0 · dusthana-lord −1.0 · …
```

Findings flow through `_combine` (`:829`) — which blends the Rāśi and Navāṁśa frames and saturates
stacked positives — then `_verdict_label` bins the score onto the **9-grade scale**
(`VERDICT_SCALE`, `:541`): *afflicted · weak · moderate · moderately good · fairly good · fairly strong
· fairly powerful · very strong · very powerful*.

> The whole synthesis was later replaced (kept, not fitted) by the gated scorer `synthesis_v2` —
> see [`FULL_REPORT.md`](FULL_REPORT.md) §4 and [`REPORT_synthesis_v2.md`](validation/REPORT_synthesis_v2.md).
> This section is the *feature front-end* both scorers share.

---

## 3. The doctrine compendium — 1,913 rules, encoded by hand

The second half of layer ② is a database of Raman's (and allied classics') atomic statements. Every
rule is one JSON record with a **verbatim, hash-verified quote** and a **machine-evaluable antecedent**.

### 3.1 The ten source books

| rules | book | what it is |
|---:|---|---|
| 1,153 | **hpa** | Hindu Predictive Astrology (Raman) |
| 351 | **htjah_vol1** | How to Judge a Horoscope, Vol I |
| 185 | **htjah_vol2** | How to Judge a Horoscope, Vol II |
| 147 | **three_hundred** | 300 Important Combinations (Raman) |
| 24 | **jaimini_studies** | Studies in Jaimini Astrology |
| 12 | **graha_bhava_balas** | planetary/house strengths |
| 12 | **manual_hindu_astrology** | A Manual of Hindu Astrology (Raman) |
| 10 + 10 | **prasna_marga** (2 parts) | the classical praśna text |
| 9 | **muhurtha** | electional astrology |
| **1,913** | **— total —** | across 10 books |

### 3.2 What one encoded rule looks like

A single record (`raman.htjah_vol1.ch1.fifth_afflicted_children_suffer`):

```json
{
  "id": "raman.htjah_vol1.ch1.fifth_afflicted_children_suffer",
  "book": "htjah_vol1", "page": 2, "rule_type": "bhava_judgment", "domain": "children",
  "quote": "Take a horoscope in which the fifth house is afflicted by unfavourable
            conjunctions and aspects. The subject will have no children …",
  "quote_sha256": "e590d0…", "quote_verified": true,
  "antecedent": { "op": "any", "args": [
      { "op": "planet_in_house",      "planet": "malefic", "house": 5 },
      { "op": "planet_aspects_house", "planet": "malefic", "house": 5 } ] },
  "consequent": { "polarity": "unfavorable", "magnitude": "strong",
                  "text": "No children, or all or most children die." },
  "computability": "partial", "inputs_required": ["planet_houses", "aspects"]
}
```

Three parts do the work:

1. **The verbatim quote + its SHA-256.** Nothing is paraphrased. The hash is re-checked so a rule can
   never silently drift from Raman's actual words. `quote_verified: true` means it was matched against
   the pinned source text.
2. **The antecedent** — a small tree of operators (`planet_in_house`, `planet_aspects_house`,
   `lord_of_house_in_house`, `any`/`all`, `yoga_present`, `dignity_is`, …) that the engine evaluates
   against a real chart (`engine/predicates.py`). `computability` records whether it is `full`,
   `partial`, or `manual` (prose that can't be mechanised).
3. **The consequent** — the signed effect: `polarity` (favorable/unfavorable), `magnitude`
   (strong/moderate/slight), the outcome text, and any `timing`.

### 3.3 The extraction pipeline (`sweep`)

Rules were not typed by hand into code — they were **swept** from the source books through a gated
pipeline: an extractor agent proposes draft rules per chapter → `sweep.py` verifies each one's quote
against the pinned, SHA-pinned source text, compiles its antecedent, checks its schema, then merges.
A rule that fails any gate is rejected, not fixed up. Coverage manifests
([`COVERAGE.md`](COVERAGE.md), [`COMPENDIUM_STATUS.md`](COMPENDIUM_STATUS.md)) update mechanically, so
"what's encoded" is always a computed fact, not a claim.

---

## 4. The patience: one house at a time

The engine was **not** written in one pass. It was grown house by house, each deepening calibrated
against Raman's own worked charts and guarded so it could not disturb the houses already settled. That
discipline is the whole reason the numbers are trustworthy. A few representative moments from the
30+ increment ledger ([`HOUSE_SCHEME_AUDIT.md`](HOUSE_SCHEME_AUDIT.md)):

- **Increment 2.4 — the dusthāna lord.** On Chart 64, Raman calls a planet afflicted because *it owns*
  the 6th, not merely because of where it sits. So "a 6/8/12 lord is a functional malefic *to itself*"
  became a rule — but scoped so the ascendant lord and an own-sign lord at home are exempt (Chart 35's
  8th lord in its own sign is "full and very powerful", not afflicted).
- **Increment 2.6 A.1/A.2 — the natural benefic.** A natural benefic (Jupiter, Venus) in or aspecting a
  house is *not* a blemish even when it is a functional malefic for that ascendant. This one change,
  read straight from Charts 70–74, moved the 4th-house held-out from **39% to 56%** with **zero cost**
  to the already-settled houses.
- **Increments 34–35 — the fine exceptions.** A debilitated planet whose debilitation is *cancelled*
  (neechabhāṅga) in a kendra is treated as strong; a dusthāna lord *in its own sign* keeps its dignity.
  Each is one worked chart, encoded, then guarded by a test.
- **House 1 was frozen on purpose.** The ascendant has special rules (vargottama-lagna, first-house
  reading order); its reviewed output is kept byte-stable so later increments can't quietly change it,
  and it is validated separately as the calibration **anchor**.

Every one of these is pinned by a test in `tests/doctrine/`, so a later change that would undo a
patiently-won calibration trips a red test in the same commit. The two anchors — the frozen
hand-decoded one and the live grid-backed one — exist precisely so drift between "what we calibrated"
and "what the engine now does" can never hide.

---

## 5. Joining the two halves (increment 17)

For a long time the compendium and the scorer ran side by side but **the encoded rules never touched
the strength grades** — they fed only the written reading. A three-agent survey found this was the
single biggest missed opportunity: "we encoded the doctrine and then didn't use it to judge."

Increment 17 fixed it. `sutra_strength.py` classifies each *fired, novel* rule (excluding
timing/definition/electional and anything the additive path already covers), routes it to the right
factor (bhāva/lord/kāraka), and injects it as a `Finding` with a doctrine-derived weight, clamped per
factor so no single rule can dominate. This was **the largest single accuracy gain** of the whole
effort: held-out **52.8 → 54.7%**, NH pooled **43.8 → 53.1%**. Later, `natal_scope.py` (increment 21)
widened which rules are even *eligible* to fire on a birth chart, closing an orphan-domain gap where
872 rules could never reach any house.

---

## 6. Where to read the code

| you want | file |
|---|---|
| the house scheme, assessors, weights, 9-grade scale | `app/medini/doctrine/domains/house_judgment.py` |
| the gated scorer that replaced the additive synthesis | `app/medini/doctrine/domains/synthesis_v2.py` |
| functional benefic/malefic/yogakāraka per ascendant | `app/core/functional_roles.py` |
| the rule DSL (operators + evaluator) | `app/medini/doctrine/engine/{predicates,evaluate}.py` |
| routing fired rules into the grades | `app/medini/doctrine/domains/{sutra_strength,natal_scope}.py` |
| the 1,913 encoded rules | `data/raman_doctrine/compendium/*.jsonl` |
| the chart layer (ephemeris + reconstruction) | `app/core/ephemeris_engine.py` · `app/medini/doctrine/raman_chart.py` · `validation/reconstruct.py` |
| the patient increment history | [`HOUSE_SCHEME_AUDIT.md`](HOUSE_SCHEME_AUDIT.md) |
| how well it all does | [`FULL_REPORT.md`](FULL_REPORT.md) · [`VALIDATION_SUMMARY.md`](VALIDATION_SUMMARY.md) |

---

*The engine is, in the end, Raman's own procedure made executable: judge each house from its bhāva, its
lord, and its kāraka; read every planet's disposition relative to the ascendant first; weigh the
testimony the way his chapters describe; and never let a new refinement quietly undo an old one.*
