# Phase-3 — DRAFT golden validation worksheet

Generated 2026-06-25 (Item 3), regenerated after the Section-A validation pass.
Confirming a DRAFT = set `verdict_review: "CONFIRMED"` in
`tests/fixtures/raman_goldens.jsonl`; it then enters the Track-B ratchet. A DRAFT
the engine already matches becomes a CORRECT verdict (ratchet numerator + denominator
both +1); a DRAFT the engine misses adds to the denominator only.

> **Update 2026-06-25:** the original 10-row Section A was validated against Raman's
> text and **9 confirmed** (h7_01/06/12/13/14, h9_01, h12_14, h6_02/05) — ratchet
> 90/130 → **99/139**. `h12_13` left HELD (below). **25 DRAFTs remain** (1 held +
> 7 H8 placeholders + 17 engine-mismatch).

## A. Ready to confirm — engine already matches (1 DRAFT: the held one)

The 9 validated rows are now CONFIRMED. Only `h12_13` remains — previously HELD,
left as-is pending a fresh decision.

| # | id | house/sig | recorded verdict | engine | held? | Raman's reasoning (verdict_prose) | citations |
|---|----|-----------|------------------|--------|-------|-----------------------------------|-----------|
| 1 | h12_13 | H12/left_eye | **afflicted** | afflicted | ⚠️ HELD | First suffered night-blindness, then lost vision completely. | HTJAH-II:17420 |

## B. H8 death/longevity — BLOCKED on the Phase-E longevity engine (7 placeholders)

The death-house has **0 confirmed goldens**, and these **cannot be confirmed by text
validation** — they are deliberately Phase-E-gated:
- Each record's prose ends *"Asserts only after Phase E longevity engine."*
- The judge sets `LONGEVITY_GUARD` for every `longevity`/`death` signification and
  `_clamp_longevity` (house_template.py:392) **defers an afflicted/death verdict to the
  Phase-E sub-engine → `insufficient-evidence`**. The engine intentionally does NOT emit a
  real death/longevity verdict, so there is nothing faithful to confirm against.
- chart_33/34 assert specific ayurdaya year-counts (Pindayu 86y, Amsayu 68y) that need the
  alpa/madhya/purna span computation; chart_35/73/74/75/78 (Lincoln/Gandhi/JFK/Hitler) need
  death-dasha + maraka timing.

**To open the death house, raman_saab needs a Phase-E longevity engine** (ayurdaya span +
maraka-dasha timing). NB: the death-timing/longevity work on the sibling branches
(`feat/death-timing-predictor`, `data/vedastro-corpus`) is the empirical analogue of exactly
this missing machinery — a candidate to port/adapt. The `engine says` column below is the
clamped fallback, **not** a real longevity reading.

| id | name | sig | engine says | citations |
|----|------|-----|-------------|-----------|
| chart_33 | Chart 33 ayur (Pindayu = 86y 2m 20d; Aquarius Lagna 9d42') | H8/longevity | mixed | HTJAH-II:4105, HTJAH-II:4249-4260 |
| chart_34 | Chart 34 ayur (Amsayu 68y 10m 5d; actual death 15-4-1950 at 70y 3m 15d) | H8/longevity | mixed | HTJAH-II:4332, HTJAH-II:4435-4441 |
| chart_35 | Chart 35 ayur (Poornayu; died 7-2-1966 Rahu Dasa Sun Bhukti; Sagittarius Lagna) | H8/death | afflicted | HTJAH-II:4661, HTJAH-II:4844-4855 |
| chart_74 | Chart 74 (Gandhi - assassinated by a fanatic) | H8/death | mixed | HTJAH-II:6777-6819 |
| chart_73 | Chart 73 (Lincoln - assassinated, shot) | H8/death | favourable | HTJAH-II:6711-6775 |
| chart_75 | Chart 75 (Kennedy/JFK - US President shot dead) | H8/death | afflicted | HTJAH-II:6821-6869 |
| chart_78 | Chart 78 (Hitler - believed suicide) | H8/death | favourable | HTJAH-II:6959-6993 |

## C. Engine mismatch — VALIDATED as genuine engine misses (16 remaining; h7_09 FIXED)

> **Increment 1 (2026-06-25):** `h7_09` (over-lenient coverture/vaidhavya) **fixed + confirmed**
> via the decisive rule `H7.C.84` (7th-lord-in-8th + node/Saturn aggravator → spouse death).
> **Increment 2:** `h7_10` fixed + confirmed via `H7.C.85` (Mars-in-8th + debilitated 7th lord →
> spouse death). Ratchet 99/139 → **101/141**. **14 mismatches remain** (7 over-lenient + 7
> over-harsh; h5_14 held). The remaining coverture/vaidhavya miss `h7_11` is engine=mixed (8th-
> from-Moon affliction — a Chandra-frame signature, its own increment).

**Validated 2026-06-25 against Raman's text (corpus reads).** Every recorded DRAFT
verdict is CORRECT per Raman — the engine misses each one, so NONE is confirmable now
(confirming would lower accuracy). No "wrong-DRAFT" quick wins exist here. The split:
- **Over-LENIENT (10)** — engine reads favourable/mixed where Raman is afflicted/mixed:
  h7_02, h7_04, h7_05, h7_09, h7_10, h7_11, h7_15, h7_16, h7_19, h5_18. The dominant
  failure: the engine **under-reads marriage afflictions** — esp. coverture/vaidhavya
  (spouse-death) charts h7_09/10/11 read favourable/mixed though Raman reads the spouse
  dead. The V2 favour-preponderance is over-lifting afflicted marriage verdicts.
- **Over-HARSH (7)** — engine reads afflicted where Raman is mixed/favourable:
  h7_03, h7_07, h7_17, h7_18, h5_13, h5_14, h5_15. Mostly "unconventional but not ruined"
  marriages (married outside caste/religion, remarried after widowhood = mixed) that the
  engine's decisive/nodal affliction over-reads as full afflicted.

These are the precise B2/B3/B4 + H5 engine-calibration spec. They are NOT bulk-fixable —
each needs a faithful, cited, doctrine-reviewed, zero-regression increment (the project's
demonstrated discipline). Raman's exact reasoning per chart:

| id | house/sig | recorded | engine | Raman's reasoning |
|----|-----------|----------|--------|-------------------|
| h5_13 | H5/children | mixed | afflicted | Birth of children not denied (5th lord aspected by Jupiter, PutraKaraka free of affliction); only one daughter born at the start of Ketu Dasha, living, no ot... |
| h5_14 | H5/children | mixed | afflicted | 5th house fairly well disposed but 5th lord and PutraKaraka both considerably afflicted; the native has only one daughter (miscarriages/premature births sugg... |
| h5_15 | H5/children | favourable | mixed | 5th house fairly well disposed; counting gives about 9 children — the native had 8 issues, out of which one died. |
| h5_18 | H5/children | mixed | favourable | Birth of a number of children and loss of all but one; about 10 children born, out of which only one daughter survives. |
| h7_02 | H7/spouse | afflicted | favourable | Husband was already married to another at the time; Rahu with 7th lord made him immoral. |
| h7_03 | H7/marital_happiness | mixed | afflicted | Rigid, headstrong partner; tensions and quarrels but no separation or divorce. |
| h7_04 | H7/marital_happiness | mixed | favourable | Generally happy marriage with domestic bickerings. |
| h7_05 | H7/spouse | afflicted | favourable | Two wives; a clandestine marriage before the regular one, the wife leaving on learning of the secret. |
| h7_07 | H7/coverture | mixed | afflicted | Two marriages, the second after the death of the first husband. |
| h7_09 | H7/coverture | afflicted | favourable | Early widowhood — husband drowned ten months after marriage, in Venus Bhukti of Rahu Dasa. |
| h7_10 | H7/coverture | afflicted | favourable | Death of the wife — debilitated/eclipsed 7th lord with Mars in the 8th. |
| h7_11 | H7/coverture | afflicted | mixed | A good husband, then widowed exactly a year after marriage (Ketu Bhukti, Rahu Dasa). |
| h7_15 | H7/spouse | afflicted | favourable | Disliked his wife; a profligate who contracted venereal disease — both 7th lord and Venus heavily afflicted. |
| h7_16 | H7/spouse | mixed | favourable | A duke of British royalty married a commoner divorcee, abdicating the throne — 8th (marital bond) afflicted in Rasi and Navamsa. |
| h7_17 | H7/spouse | mixed | afflicted | A Hindu married a Christian colleague — Ketu in 7th, Rahu afflicting Venus, papakartari to 8th-from-Moon. |
| h7_18 | H7/spouse | mixed | afflicted | Married a foreigner — Jupiter (9th lord) influence on karaka/7th lord Venus, with 8th afflicted in Rasi and Navamsa. |
| h7_19 | H7/spouse | mixed | favourable | A Brahmin married a Christian youth — all malefics in the 8th plus Saturn's aspect on the 7th-from-Moon. |
