---
title: "Raman Saab golden-harness schema (`tests/fixtures/raman_goldens.jsonl`)"
kind: spec
topic: validation
measured: false
updated: 2026-07-24
words: 1455
tags: [raman-saab, spec, validation]
---
# Raman Saab golden-harness schema (`tests/fixtures/raman_goldens.jsonl`)

The golden corpus is the **accuracy ratchet** for the deterministic "Raman Saab"
engine (a replica of B.V. Raman *How to Judge a Horoscope* Vols I & II). Each line
is one self-contained JSON object pinning the engine against Raman's own published
verdicts. The harness in `tests/raman_saab/test_goldens.py` loads this file once and
runs a 3-tier check (astronomy / doctrine / evidence snapshot) over it.

This file is **JSON Lines** (`.jsonl`): one JSON object per line, UTF-8, `\n`
terminated. Blank lines and lines whose first non-whitespace character is `#`
(a comment line) are ignored by the loader. Comments are how we keep a worked
example beside its machine record without breaking the parser.

> **Doctrinal note.** A golden is a *claim about Raman's text*, never about the
> engine's current output. The `verdict_review` gate (below) is what keeps an
> un-reviewed machine guess out of the asserting path. A `self_test` record is the
> one exception — it is a synthetic regression anchor, explicitly **not** a doctrine
> claim, and is labelled as such.

---

## Per-line fields

| Field | Type | Required | Meaning |
|---|---|---|---|
| `id` | string | yes | Stable unique id, e.g. `"HTJAH-I.chart_08"`, `"H7.rule.B23a"`, `"self_test.aries_jupiter_h1"`. Used in snapshot keys and failure messages. |
| `book` | `"HTJAH-I"` \| `"HTJAH-II"` | yes | Which volume the case is drawn from (Vol I = houses 1–6, Vol II = houses 7–12). `self_test` records use the nearest volume by house. |
| `name` | string | yes | Human label, e.g. `"Chart 8 (Tiger native)"` or `"self-test: Aries Lagna, Jupiter in 1st"`. |
| `case_type` | enum | yes | One of `worked_example` \| `rule_level` \| `doctrine_statement` \| `self_test` (see below). |
| `birth` | object \| null | yes | `{dt, tz, lat, lon}` or `null`. Any sub-field may be `null` (most worked charts lack a printed birth time). See **birth**. |
| `lagna_sign` | int(1–12) \| null | yes | Rashi index of the rising sign (Aries=1 … Pisces=12). `null` when the case is purely rule-level/doctrine and no Lagna is fixed. |
| `stated_positions` | object | yes | `{Planet: {sign\|lon, bhava, position_source}}`. The book's printed placements (Track-B input). May be `{}` for a pure `doctrine_statement`. See **stated_positions**. |
| `expected_verdicts` | object | yes | `{"H<n>": {signification, verdict, verdict_prose, verdict_review}}`. The asserted per-signification verdicts. May be `{}` for a pure `doctrine_statement`. See **expected_verdicts**. |
| `expected_longevity` | null \| object | yes | `null`, or `{"years":int,"months":int,"days":int}`, or `{"death_date":"YYYY-MM-DD"}`. The Phase-E longevity overlay consumes this; today it is captured only. |
| `track_eligibility` | array of `"A"`\|`"B"`\|`"3"` | yes | Which tiers may run this record. `"A"`=astronomy (needs full birth), `"B"`=doctrine, `"3"`=evidence snapshot. |
| `confidence` | float 0..1 | yes | Curator's confidence the record faithfully captures Raman's verdict. Informational; the tuner may weight by it. |
| `citations` | array of string | yes | Source pointers, `"<work>:<line>"` form, e.g. `["HTJAH-I:1068"]`. At least one for non-`self_test` records. |
| `_note` | string | no | Optional provenance/curation note (e.g. an OCR-correction explanation: dropped `W` hemisphere, a degrees-as-hours longitude, a corrected ayanamsa-cusp Lagna). Ignored by the harness; kept for human traceability. |

### `case_type`

| Value | What it pins | Track-B asserted? |
|---|---|---|
| `worked_example` | A full numbered chart from the book + Raman's prose verdict on one or more houses. | Only when every cited verdict is `CONFIRMED`. |
| `rule_level` | A single combination/rule (a `RuleRecord.condition`) and the verdict it should produce on a *minimal synthesised chart*. The chart is built by `condition_solver`. | Only when `CONFIRMED`. |
| `doctrine_statement` | A prose doctrine claim with no chart (e.g. "AK can never be Rahu/Ketu"). Captured for traceability; usually has empty `stated_positions`/`expected_verdicts`. | No (no chart to judge). |
| `self_test` | A **synthetic** chart whose `judge_house` verdict is deterministic, used to prove Track-B catches regressions. **NOT a doctrine claim.** | Yes — always `CONFIRMED`. |

### `birth`

```json
"birth": {"dt": "1901-07-15T13:25:00", "tz": 5.5, "lat": 12.97, "lon": 77.59}
```

* `dt` — ISO-8601 local datetime, or `null` if the book omits a birth time.
* `tz` — float hours offset from UTC (e.g. `5.5`), or `null`.
* `lat`, `lon` — decimal degrees (N/E positive), or `null`.

A record qualifies for **Track A** only when `birth` is present *and* all four of
`dt`/`tz`/`lat`/`lon` are non-null *and* `track_eligibility` contains `"A"`. Most
worked charts in the book give only the planetary table, not a time — so Track-A
cases are deliberately rare. That is fine: Track B is the north star.

### `stated_positions`

```json
"stated_positions": {
  "Jupiter": {"lon": 5.0,  "bhava": 1, "position_source": "synthetic_minimal"},
  "Saturn":  {"sign": 7,   "bhava": 7, "position_source": "sign_midpoint"}
}
```

Each planet entry supplies **either** `lon` (decimal degrees 0–360) **or** `sign`
(rashi 1–12), plus the `bhava` Raman assigns it, plus a `position_source` provenance
tag:

| `position_source` | Meaning | How `lon` is derived for the chart |
|---|---|---|
| `printed_degree` | The book printed an exact degree. | Use the printed `lon` verbatim. |
| `sign_midpoint` | Only a sign was printed; degree unknown. | Place at sign midpoint: `lon = (sign-1)*30 + 15`. |
| `synthetic_minimal` | Synthesised by `condition_solver` for a `rule_level` case. | Use the solver's chosen `lon`. |
| `fresh_cast` | Position comes from an ephemeris cast of `birth`, not the table. | Ignore `stated_positions`; `cast_chart(birth)` supplies positions. |

`from_stated_positions` requires a `lon`, so the loader materialises one from
`sign` via the midpoint rule when only `sign` is given. `bhava` is taken as printed
(Raman frequently uses a Bhava/Chalita placement different from the rashi house).

### `expected_verdicts`

Keyed by house tag `"H1".."H12"`. Each value:

```json
"H1": {
  "signification": "self",
  "verdict": "favourable",
  "verdict_prose": "...born to greatness, of fine physique...",
  "verdict_review": "CONFIRMED"
}
```

* `signification` — the sub-matter key (must match a `Signification.key` for that
  house in `app/raman_saab/doctrine/significations.py`; e.g. H4 `mother`, H7 `spouse`).
* `verdict` — the asserted ordinal: `favourable` \| `mixed` \| `afflicted` \|
  `insufficient-evidence` \| `DRAFT`.
* `verdict_prose` — the exact Raman sentence(s) the verdict is read from (kept so a
  human can re-judge). Drives the keyword lexicon (see extractor docs).
* `verdict_review` — `DRAFT` \| `CONFIRMED`. **This is the assertion gate.** Only
  `CONFIRMED` verdicts are asserted in Track B; `DRAFT` rows are skipped (the engine
  is allowed to disagree with an un-reviewed machine guess) and merely counted by a
  reporting test.

A verdict literal of `"DRAFT"` (as opposed to a real ordinal with
`verdict_review:"DRAFT"`) is also treated as un-reviewed and skipped — both
phrasings mean "not yet human-confirmed".

### `expected_longevity`

`null` for the vast majority. When Raman states a span or a death date:

```json
"expected_longevity": {"years": 71, "months": 2, "days": 0}
"expected_longevity": {"death_date": "1936-12-31"}
```

Captured now; consumed by the Phase-E longevity sub-engine later. The harness only
validates the *shape* today.

### `track_eligibility`

Array drawn from `{"A","B","3"}`. A record runs in a tier only if that tier's
letter is present **and** the tier's other preconditions hold (Track A also needs a
full `birth`; Track B also needs ≥1 `CONFIRMED` verdict). Typical values:

* `["B","3"]` — a from-table worked example with no birth time (the common case).
* `["A","B","3"]` — a rare chart with a full birth time, pinned both astronomically
  and doctrinally.
* `["B"]` — a `rule_level` synthesised chart (no real ephemeris to snapshot stably).

---

## Validation rules (enforced by the schema-guard test)

1. Every line parses as JSON (after comment/blank stripping).
2. All required fields present with the declared types.
3. `case_type` ∈ the four enum values.
4. `lagna_sign` ∈ `1..12` or `null`.
5. Every `stated_positions[*]` has exactly one of `lon`/`sign`, a `bhava`, and a
   valid `position_source`.
6. Every `expected_verdicts["H<n>"]` has `1 ≤ n ≤ 12`, a `verdict` ∈ the allowed
   set (incl. `DRAFT`), and `verdict_review` ∈ `{DRAFT, CONFIRMED}`.
7. `track_eligibility` ⊆ `{"A","B","3"}`, non-empty.
8. `confidence` ∈ `[0,1]`.
9. `expected_longevity` is `null`, or a `{years,months,days}` int-triple, or a
   `{death_date}` ISO date.
10. A `self_test` record must have `verdict_review == "CONFIRMED"` on every verdict
    (it is a regression anchor and must always assert).
11. **Case-type structural invariants (schema guard #5).** A `doctrine_statement`
    record carries no chart to judge, so it must have **empty** `stated_positions`
    **and** empty `expected_verdicts` (it pins a prose claim only). A `rule_level`
    record synthesises a minimal chart for a single combination, so it may pin **at
    most one** `expected_verdicts` house (`len(expected_verdicts) <= 1`).

---

## Worked-line example (also lives, commented, in the fixture)

```json
{"id":"HTJAH-I.chart_08","book":"HTJAH-I","name":"Chart 8 (greatness via strong Navamsa Lagna)","case_type":"worked_example","birth":null,"lagna_sign":7,"stated_positions":{"Venus":{"sign":2,"bhava":8,"position_source":"sign_midpoint"}},"expected_verdicts":{"H1":{"signification":"self","verdict":"favourable","verdict_prose":"born to greatness; Lagna lord in 8th redeemed by strong Navamsa Lagna","verdict_review":"DRAFT"}},"expected_longevity":null,"track_eligibility":["B","3"],"confidence":0.55,"citations":["HTJAH-I:1068"]}
```

This row is `DRAFT`, so Track B **skips** it (the engine may legitimately disagree
until a human confirms the reading). It is counted by the DRAFT/CONFIRMED reporting
test. Promotion to `CONFIRMED` is the Phase-B extraction workflow's job.
