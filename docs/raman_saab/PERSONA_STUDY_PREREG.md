# Pre-registration — the persona study (blinded feedback from documented lives)

**Written and committed BEFORE any chart is cast, any answer is collected, or any score is
computed.** Deviations from this document are recorded as deviations in the results, never
edited away.

---

## 0. What this study is, and what it is not

The feedback instrument (`app/raman_saab/feedback_instrument.py`) and its scorer have been
built and shipped, and have never been exercised on more than eight hand-made rows. This
study fills them from documented biographies of public figures, blind, and reports what comes
out.

**It is:**
1. an end-to-end exercise of the feedback loop — questions, HTTP validation, storage, scorer,
   scorecard — intended to find defects before real readers meet them;
2. an exploratory, out-of-sample **consistency check** against the project's already-closed
   real-outcome null.

**It is not** a test of whether the engine predicts lives. That question is settled at
n=22,177 charts and 47k dated events, sham-gated at exactly 0.500
(`REAL_OUTCOME_GENERALIZATION.md`). This study is roughly a thousandth of that size. Its
pre-registered expectation is a null, and a null here **corroborates** the existing finding
rather than adding to it.

**Interpretation rule, fixed in advance.** A result at chance is reported as consistent with
the closed null. A result far from chance is reported as **a flag to hunt contamination or
selection**, not as a discovery, and the first hypotheses examined will be blinding failure
and roster composition — in that order.

---

## 1. Primary endpoint and decision rule

**Primary:** Part C forced-choice hit rate against the persona's own chart, exact two-sided
binomial against **p = 0.5**.

The null is 0.5 *by construction*, not by estimation: each Part C item pairs the chart's own
reading of a signification with its exact inverse, both unlabelled, option order shuffled by a
chart-derived seed, and the answer key never leaves the server. There is no base rate to
estimate and no saturation trap.

Target size 24 personas × 12 items = **288 items**. Power, computed with the scorer's own
exact binomial:

| true rate | power at α=.05 |
|---|---|
| 0.55 | 0.40 |
| 0.58 | 0.78 |
| 0.60 | 0.93 |

Significance begins at **162/288 = 0.562**, a +6.2 point deviation. **That threshold sits
almost exactly on this project's own measured noise floor** (|AUC−0.5| p95 = 0.061 across
1,209 unmatched cells in `FAILURE_ATLAS.md`). The study can therefore only see effects larger
than the field's own noise, and **a null here is correspondingly weak evidence of absence.**
This limitation is stated in the results, not buried.

**Secondary, reported but never pooled into the primary:**
- inverted channels (`H3_courage`, `H12_incarceration`) — a separate pool, read backwards;
- rarity-weighted forced choice (weight = 1 − band_share);
- Part A life facts — **counts only, no rate, no p-value**. `_score_life` has no null and none
  is computable: children read afflicted on ~76% of ordinary charts, so a "hit" there is not a
  hit. Any percentage quoted from Part A would be a misreading.
- the dated spine and event-vs-house measurements, each against its own computed null.

---

## 2. Controls — the part that decides whether the primary means anything

### 2a. Cross-chart falsification (the decisive control)

The most productive control in the existing programme; it is what killed the +0.208
death-window signal. Each persona's Part C questions are generated from their **own** chart, so
answers are not transferable question-by-question. They are transferable **at the
signification level**: an answer means "my life on signification *S* reads as pole *P*", and
`instrument_key` decodes which option was which pole.

- **Matched arm** — persona A's poles against A's own chart.
- **Mismatched arm** — persona A's poles against each of the other 23 charts, pooled.
- **Statistic** — matched minus mismatched, tested by permutation over persona↔chart
  assignments.

Measured feasibility, on three real charts before writing this: **every chart judges all 56
significations, so transfer is 12/12 in every direction tested** — the control arm is
24 × 12 × 23 = **6,624 comparisons** against 288 matched ones. Between-chart verdict agreement
ranged **8% to 50%**, so the mismatched arm's own null is neither 0.5 nor stable, and a
control scoring against a single donor would be dominated by which donor it drew. Pooling over
all donors and testing the contrast is the only construction those numbers support.

Under "the chart carries no person-specific information", matched − mismatched = 0.

### 2b. Coin-flip arm — the sham gate

A deterministic seeded random answerer over the same 24 instruments. **Must return 0.5 within
its confidence interval. No other number in this study may be read until it does.** A
coin-flip arm away from 0.5 means a pipeline defect, and the run stops and is fixed.

### 2c. Contaminated arm — demonstrating the mechanism

The same 24 personas answered by an agent that **is** shown the chart's reading first.
Expected to score high. If the blind arm lands at chance and the contaminated arm well above
it, the study has demonstrated the *curation asymmetry*
(`WHY_THE_ENGINE_FAILS_ON_REAL_CHARTS.md:154-164`) inside our own harness — which is the
single most useful thing it can produce.

---

## 3. Blinding

- The persona agent receives only the person's name, a biography brief, and the instrument
  **payload** — which by construction carries no verdict, `band_share`, `signification`, or
  `inverted_warning`, and is pinned so by `test_the_answer_key_is_not_in_the_response`.
- Answers are written to disk and **SHA-256 hashed before any answer key is computed for that
  chart**, so the ordering makes the blind real for the operator as well as the agent.
- Submissions are posted with `context="before_reading"`.

**Residual risk, stated rather than waved away:** a persona subagent has tools and could in
principle cast the chart itself. Contamination of that kind raises the matched arm *and* leaves
the mismatched arm alone — the same signature as a real effect — so it is caught by per-persona
inspection against the coin-flip distribution, not by the pooled number. This is a genuine
limitation of the design and is reported as one.

---

## 4. Roster

### Selection rule (mechanical, fixed here)

Candidates are listed below **in order, by stratum**. Each is resolved through
`tools/raman_saab/persona_birthdata.py`. The **first four per stratum that pass the admission
gate** enter the study. Every candidate that fails is **recorded as dropped, with its reason**,
and is never silently replaced by a later name being promoted out of order.

### Admission gate

1. **Rodden AA or A** — birth certificate/civil record, or from the person or family. B, C, DD,
   X are refused. The rating is recorded per person and results are split by it.
2. **A birth time is stated, and it is not a noon default.** A date alone is refused, and so
   is a time of `12:00` — see Deviation 1.
3. **The birthplace was on standard time at that date** — the offset must be a whole
   quarter-hour. `zoneinfo` answers pre-standard-time dates with the *zone's* local mean time,
   which belongs to the reference city rather than the birth city (1879 Ulm returns Berlin's
   +00:53:28 against Ulm's own +00:39:58 — about 3.5° of ascendant). This drops births before
   their country adopted standard time, **Einstein and Kahlo among them**, and is the reason
   the roster skews to the twentieth century.
4. **Coordinates resolve** through OpenStreetMap.

### Reference date

The chart is built with `on=` anchored **inside the documented life**: the person's **40th
birthday**, falling back to the **midpoint of their documented adult life** where they did not
reach 40. Read as of today, a historical chart has an empty timeline — no running period, no
decades — and every timing measurement would be vacuous. Part C's verdicts do not depend on
`on` at all, so the anchor costs the primary endpoint nothing and buys the secondary ones their
validity.

### Strata

Six, four each. They reuse the outcome taxonomy already locked in
`tools/raman_saab/astrobank/mapping/category_house_map.csv` rather than inventing new ones. A
roster of only successful people would agree with the engine by base rate alone — half of
these strata are catastrophes for exactly that reason.

| # | stratum | maps to | note |
|---|---|---|---|
| 1 | long life, broad success | H8_LONGLIFE | the base case |
| 2 | early or violent death | H8_SHORTLIFE | forces the afflicted pole |
| 3 | imprisonment or legal ruin | H12_PRISON | a **proven INVERTED** channel — scored separately |
| 4 | chronic illness or disability | H6 | health answers that are not "fine" |
| 5 | childlessness or family rupture | H5_CHILDLESS, H7_DIVORCED | the 76%-afflicted trap made visible |
| 6 | wealth to ruin, or ruin to wealth | H2_BANKRUPT | direction, not level |

**Fame is never an outcome here.** `category_house_map.csv` pre-registers `VOC_ACTOR` and
`FAMOUS_TOP5` as `status=rejected` — "fame-selected corpus cannot test career favourability via
vocation membership" — and this study does not test career favourability against eminence.

### Candidate list, in order

1. **Long life, broad success:** Queen Elizabeth II · Katharine Hepburn · Jimmy Carter ·
   George Burns · Bob Hope · Clint Eastwood · Sean Connery · Charlie Chaplin
2. **Early or violent death:** Marilyn Monroe · James Dean · John F. Kennedy ·
   Martin Luther King · Janis Joplin · Jimi Hendrix · Bruce Lee · Princess Diana
3. **Imprisonment or legal ruin:** Nelson Mandela · Al Capone · Bernie Madoff ·
   Mike Tyson · O. J. Simpson · Martha Stewart · Jean Genet · Patty Hearst
4. **Chronic illness or disability:** Stephen Hawking · Ray Charles · Stevie Wonder ·
   Christopher Reeve · Michael J. Fox · Helen Keller · Frida Kahlo · Franklin D. Roosevelt
5. **Childlessness or family rupture:** Elizabeth Taylor · Marlene Dietrich · Greta Garbo ·
   Oprah Winfrey · Dolly Parton · Coco Chanel · Mia Farrow · Jack Nicholson
6. **Wealth to ruin, or ruin to wealth:** Walt Disney · Willie Nelson · Elvis Presley ·
   MC Hammer · Donald Trump · Larry King · Judy Garland · Burt Reynolds

A person who fits two strata is used in the **earlier-numbered** one only, and is skipped in
the later. No person appears twice.

**Privacy.** Every name is a public figure, and every fact used is from published biography.
This matches existing practice in `FAILURE_ATLAS.md`, which names public figures from the
public AstroDatabank corpus. No private individual appears. A31 (periods of low mood or
anxiety) is recorded as **informational and never scored**, because the engine's mind screen is
present-or-absent and ships its own caution that it is not a diagnosis.

---

## 5. Limitations, fixed in advance

1. **Celebrity selection** is the last open confound in the existing programme
   (`REAL_OUTCOME_GENERALIZATION.md:345-347`), and this study *doubles down* on that
   population. It cannot close that hatch and does not try.
2. **The respondent is a language model reading a biography, not the person.** It will answer
   from the famous, salient facts, which are the extreme ones. This biases toward strong poles.
   The cross-chart control absorbs that bias; it does not remove it.
3. **n = 24**, powered only past the field's own noise floor (§1).
4. **Blinding is procedural**, with the residual risk named in §3.

## 6. Deviations

Recorded here as they happen. Each names what changed, when relative to data collection, and
why.

### Deviation 1 — noon defaults excluded (amended BEFORE any answer was collected)

The gate as first written asked only that a birth time be *stated*. Running it over the
candidate list surfaced a time of exactly `12:00` (Martin Luther King, Rodden A), which is the
classic noon default — the value a record carries when the hour is unknown, not a claim about
the hour.

This project's own locked methodology already excludes it at every quality tier:
`tools/raman_saab/astrobank/_names.py` classifies a `12:00` prefix as `noon_default`, and
`quality_tier` returns `None` for it — "Noon-default/unknown times are excluded outright"
(`astrobank/METHODOLOGY.md:33-36`). §4's gate was modelled on that scheme and should have
carried the rule; omitting it was an oversight, not a choice.

The gate now refuses `12:00`. This is a **tightening**, applied before any answer existed, and
it is mechanical rather than discretionary. Under the standing rule — first four per stratum
that pass, in registered order — the next registered name in that stratum takes the place.

Round-hour and quarter-hour times are **kept**, not excluded, since they are real claims about
the hour; each person's time precision is recorded and the results are split by it.

## 7. Governance

Committed before any data is collected. The results document reports every arm, every drop,
every deviation, and leads with what the study cannot show. Nothing in this study touches the
verdict path, and the golden ratchet is asserted byte-identical (259/293 · 283/293 · 10)
alongside the results.
