# Stage-2 validation worksheet — H9 (house_09_bhagya)

Worked charts from HTJAH-II. All `verdict_review: DRAFT` (inert until you confirm).
Reply with confirmations/corrections (sig + ordinal). `DECODE-MISMATCH` = my cast Lagna
disagrees with the stated Lagna → birth-decode needs a second look before confirming.

| # | Chart | Birth | castLagna/stated | sig / DRAFT | engine | status | conf | cite |
|---|---|---|---|---|---|---|---|---|
| - | Chart 85 | — | — | father / afflicted | — | SKIP(no birth/place) | — | HTJAH-II:223 |
| - | Chart 86 | — | — | father / mixed | — | SKIP(no birth/place) | — | HTJAH-II:224 |
| - | Chart 87 | — | — | father / afflicted | — | SKIP(no birth/place) | — | HTJAH-II:225 |
| - | Chart 88 | — | — | father / afflicted | — | SKIP(no birth/place) | — | HTJAH-II:226 |
| - | Chart 89 | — | — | father / afflicted | — | SKIP(no birth/place) | — | HTJAH-II:227 |
| - | Chart 90 | — | — | father / afflicted | — | SKIP(no birth/place) | — | HTJAH-II:228 |
| - | Chart 91 | — | — | father / favourable | — | SKIP(no birth/place) | — | HTJAH-II:229 |
| - | Chart 92 | — | — | father / favourable | — | SKIP(no birth/place) | — | HTJAH-II:231 |
| - | Chart 93 | — | — | father / mixed | — | SKIP(no birth/place) | — | HTJAH-II:232 |
| - | Chart 94 | — | — | father / favourable | — | SKIP(no birth/place) | — | HTJAH-II:233 |
| - | Chart 95 | — | — | father / favourable | — | SKIP(no birth/place) | — | HTJAH-II:234 |
| - | Chart 96 | — | — | father / mixed | — | SKIP(no birth/place) | — | HTJAH-II:235 |
| - | Chart 97 | — | — | father / afflicted | — | SKIP(no birth/place) | — | HTJAH-II:236 |
| - | Chart 98 | — | — | fortune / favourable | — | SKIP(no birth/place) | — | HTJAH-II:238 |
| - | Chart 99 | — | — | fortune / favourable | — | SKIP(no birth/place) | — | HTJAH-II:239 |
| - | Chart 100 | — | — | long_journeys / favourable | — | SKIP(no birth/place) | — | HTJAH-II:240 |
| - | Chart 101 | — | — | long_journeys / favourable | — | SKIP(no birth/place) | — | HTJAH-II:241 |
| - | Chart 102 | — | — | long_journeys / favourable | — | SKIP(no birth/place) | — | HTJAH-II:242 |
| - | Chart 103 | — | — | long_journeys / favourable | — | SKIP(no birth/place) | — | HTJAH-II:243 |
| - | Chart 104 | — | — | long_journeys / favourable | — | SKIP(no birth/place) | — | HTJAH-II:244 |
| - | Chart 105 | — | — | long_journeys / favourable | — | SKIP(no birth/place) | — | HTJAH-II:245 |
| - | Chart 106 | — | — | long_journeys / mixed | — | SKIP(no birth/place) | — | HTJAH-II:246 |
| - | Chart 107 | — | — | long_journeys / mixed | — | SKIP(no birth/place) | — | HTJAH-II:247 |
| - | Chart 108 | — | — | long_journeys / favourable | — | SKIP(no birth/place) | — | HTJAH-II:248 |
| - | Chart 109 | — | — | long_journeys / favourable | — | SKIP(no birth/place) | — | HTJAH-II:249 |
| - | Chart 110 | — | — | long_journeys / favourable | — | SKIP(no birth/place) | — | HTJAH-II:250 |
| - | Chart 111 | — | — | long_journeys / favourable | — | SKIP(no birth/place) | — | HTJAH-II:251 |
| - | Chart 112 | — | — | long_journeys / favourable | — | SKIP(no birth/place) | — | HTJAH-II:252 |
| - | Chart 113 | — | — | dharma / favourable | — | SKIP(no birth/place) | — | HTJAH-II:253 |

**Extractor notes:** CRITICAL DATA-AVAILABILITY FINDING — no birth data is extractable for ANY H9 chart from the available source. The task said to READ docs/raman_saab/methodology/house_09_bhagya.md "Example-Chart Insights" section. That table (lines 221-253) gives ONLY: chart number, a compressed combination summary, a verdict-of-matter, reasoning, and the HTJAH-II citation range. It prints NO DOB, NO birth time, NO place name, and NO lat/lon for any chart. I verified this with a regex sweep over the whole file (no date/time/coordinate/IST/LMT/AM-PM tokens appear anywhere except the citation line numbers). The raw HTJAH-II book corpus that those `HTJAH-II:<line>` numbers index into (and which DID carry printed birth data for the already-extracted H7 charts) is NOT checked into this repo — I searched all .txt/.pdf/.json/.jsonl outside node_modules/.venv/site-packages and found no line-numbered book text and no "Concerning the Ninth House" source. The only PDFs present are the Lal Kitab tmp and the Geo-Astrological engine PDF (unrelated). For comparison, the confirmed H7 goldens (HTJAH-II.chart_01..12) all carry full {dt,tz,lat,lon,lagna} — that data came from the raw book text the curator read directly, not from the methodology MD.

CONSEQUENCE for Track-B eligibility: per the task rule "Only include charts with a place (lat/lon) at minimum — charts with no positional data at all can't become Track-B goldens, skip them and mention in notes," NONE of charts 85-113 currently qualify, because none print a place. I did NOT invent any birth_dt/tz/lat/lon (all set to ""/0 as instructed). These rows are therefore best-effort DRAFT candidates capturing signification + verdict-ordinal + prose + citation only; they need the raw HTJAH-II text (or external birth-data lookup) before they can be cast/verified. Confidence is held at 0.40-0.45 throughout to reflect the missing astronomy and the death-timing ambiguity below.

stated_lagna_sign: derived where the combination text pins it via stated 9th-house sign and/or a self-consistent lord (e.g. 86 Leo via exalted-Sun-in-9th=Aries→Lagna Leo; 90 Capricorn via 9th=Virgo + Lagna-lord Saturn; 97 Sagittarius via 9th=Leo + Lagna-lord Jupiter; 104 Aquarius via Saturn ruling both Lagna and 12th; 105 Leo via Sun in 12th-Cancer; 111 Capricorn via Saturn exalted in 10th-Libra). Left 0 where the text gives no unique sign anchor (85, 91, 92, 98, 102, 107, 109, 113) or is internally contradictory (107: "Lagna-lord Venus in 9th-bhava Aquarius" is not Venus-ruled, so unresolved). These were NOT casting-verified (no birth data to cast).

Charts SKIPPED (method-note rows, not standalone charts): "86-91 synthesis" (line 230) and "96 & 97 note" (line 237) are cross-chart method commentary with no chart of their own — excluded.

Signification routing: charts 85-97 -> father (pitru-longevity readings, karaka Sun); 98-99 -> fortune (Raman's "fortune in homeland", bhagya/Jupiter); 100-112 -> long_journeys (foreign travel/residence, no classical karaka per HTJAH-II:7658-7659); 113 -> dharma (pilgrimage/acts of piety, karaka Jupiter). All four keys (father, fortune, dharma, higher_learning, long_journeys) are valid _H9 keys in significations.py.

Verdict-ordinal caveats (death-timing charts are the soft spots a human should re-judge): 86 mixed (royal/eminent father = good, but early death = bad); 91 favourable and 92 favourable read as the "father long-lived / not deprived early" side; 93 mixed (weak careerless father, moderate longevity); 96 mixed (diminished vitality, death stated but no native-age given). 106/107 marked mixed because foreign residence was "forced / no return possible" — the long_journeys matter manifested but with adverse colouring; all other travel charts are clean favourable (the indicated journey/residence/prosperity occurred). No genuine insufficient-evidence rows.

No OCR issues in the MD itself (it is clean prose), but chart 102 is flagged in-source as "9th lord material parse-degraded" (from the original book OCR) — its Lagna could not be pinned.
