# Golden validation worksheet — DRAFT → CONFIRMED (user pass #1)

**What this is:** the 19 DRAFT goldens from `tests/fixtures/raman_goldens.jsonl`, laid out for
your validation. For each House-1 chart: Raman's verbatim conclusion, the auto-extracted draft
ordinal, and the independent doctrine-reviewer's suggestion (with corpus lines for quick lookup in
`data/knowledge_library/sources/how_to_judge_a_horoscope_raman/chapter_001_full-text-unsplit.md`).

**How to validate:** for each row, pick the ordinal you (as domain authority) read from Raman's
prose, then either (a) tell me the calls and I apply them + flip `verdict_review` to CONFIRMED, or
(b) edit the JSONL directly. A record only asserts in Track B once CONFIRMED — until then it is
inert. **Convention locked by the review: `insufficient-evidence` = ABSENT testimony only; explicit
negative testimony = `afflicted`, explicit positive = `favourable`.**

## House-1 (self) verdicts — 12 charts

| # | Chart | Raman's conclusion (verbatim gist) | Draft | Reviewer suggests | Corpus | Your call |
|---|---|---|---|---|---|---|
| 1 | chart_33 | "all three 1st-house factors unfortunately disposed… not an entity… lacks self-confidence, nervous, weak-minded" | insufficient | **afflicted** (HIGH) | 2249–2262 | ☐ |
| 2 | chart_20 | "all three factors unfavourably disposed… unimaginative, miserly, mean, undignified" | insufficient | **afflicted** (HIGH) | 1995–2010 | ☐ |
| 3 | chart_29 | "very good combination… handsome… generous… well-off businessman" (lone negative: "much pride") | insufficient | **favourable** (HIGH) | 2167–2183 | ☐ |
| 4 | chart_10 | "saturnine features… not quite healthy, weak constitution" | insufficient | **mixed** (MED) | 1197–1214 | ☐ |
| 5 | chart_31 | "Lagna hemmed by Saturn & Mars, does not fortify… strides in career BUT lacks happiness" | favourable | **mixed** (MED — career is H10, self testimony is weak Lagna + unhappiness) | 2209–2232 | ☐ |
| 6 | chart_35 | "fortunate but self-made… Jupiter in Lagna a strong antidote… forceful, imposing, attractive" | mixed | **favourable** (MED — Jupiter antidote; "unsteady career" is H10) | 2272–2289 | ☐ |
| 7 | chart_24 | "first house factors fairly well disposed… attractive… dignified… now well-to-do" ("chequered career" = H10) | mixed | favourable *or keep mixed* (LOW) | 2080–2092 | ☐ |
| 8 | chart_18 | "unassuming, forgiving, self-reliant; fortunes subject to much change; defamation case but acquitted" | afflicted | afflicted *or mixed* (LOW — your call) | 1958–1974 | ☐ |
| 9 | chart_17 | "handsome… high distinction in legal line; not happy re children (H5); always worried" | favourable | favourable (uncontested; prose mixes domains) | — | ☐ |
| 10 | chart_15 | "self-made, very high position after struggle; worried, wavering, pessimistic mind" | favourable | favourable (uncontested) | 1903–1918 | ☐ |
| 11 | chart_09 | "of a respectable family but an ordinary man; absolutely no travels" | insufficient | insufficient (uncontested — genuinely neutral testimony) | — | ☐ |
| 12 | chart_12 | "health fairly good but occasional complaints; lacks self-confidence; ill-health in Jupiter Dasha" | mixed | mixed (uncontested) | — | ☐ |

## House-8 records — 7 charts (NO ordinal validation needed now)

These carry exact `expected_longevity` pins and assert only after Phase E (longevity engine).
Verdicts stay literal "DRAFT" deliberately (the longevity guard owns the death call). Validate
only the **birth data / dates** if you wish:

| Chart | Pin | Note |
|---|---|---|
| HTJAH-II.chart_33 | 86y 2m 20d (Pindayu) | tz fixed to IST +5.5; Lagna fixed to Aquarius (HTJAH-II:4253) |
| HTJAH-II.chart_34 | 68y 10m 5d (Amsayu) | actual death 70y 3m 15d — we pin the METHOD output, per audit |
| HTJAH-II.chart_35 | death 1966-02-07 (Rahu/Sun) | Poornayu; unit-count tie-break chart |
| chart_74 Gandhi | death 1948-01-30 | Jupiter Dasa, Sun Bhukti |
| chart_73 Lincoln | death 1865-04-14 | lon/tz corrected to Western (book OCR dropped "W") |
| chart_75 JFK | death 1963-11-22 | Saturn Bhukti, Jupiter Dasa |
| chart_78 Hitler | death 1945-04-30 | Rahu Dasa, Moon Bhukti |

## Also flagged for your eye (data, not verdicts)
- **chart_29 OCR:** "Long. 0 5h. E." read as 5h(time) → 75°E, tz 5.0 LMT — reproduces Raman's
  Scorpio Lagna, but the printed string is garbled (provenance-noted in the record).
- **One-sign Lagna boundary:** chart_35 (HTJAH-I) fresh-casts Pisces vs printed Aquarius — within
  the sandhi audit-log path (TOB rounding); kept at Raman's printed value.
