# Stage-2 validation worksheet — H11 (house_11_labha)

Worked charts from HTJAH-II. All `verdict_review: DRAFT` (inert until you confirm).
Reply with confirmations/corrections (sig + ordinal). `DECODE-MISMATCH` = my cast Lagna
disagrees with the stated Lagna → birth-decode needs a second look before confirming.

| # | Chart | Birth | castLagna/stated | sig / DRAFT | engine | status | conf | cite |
|---|---|---|---|---|---|---|---|---|
| 1 | Chart 210 | 1937-08-16T08:31 tz5.5 13,77.583 | Vi/Vi | elder_siblings / **afflicted** | favourable | OK | 0.6 | HTJAH-II:14804 |
| 2 | Chart 211 | 1940-05-21T07:50 tz5.5 13,77.583 | Ge/Ge | elder_siblings / **mixed** | afflicted | OK | 0.6 | HTJAH-II:14835 |
| 3 | Chart 212 | 1946-09-29T11:58 tz5.5 13,77.583 | Sg/Sg | elder_siblings / **mixed** | mixed | OK | 0.6 | HTJAH-II:14908 |
| 4 | Chart 213 | 1974-01-06T12:40 tz5.5 13,77.583 | Ar/Ar | elder_siblings / **mixed** | mixed | OK | 0.5 | HTJAH-II:14988 |
| 5 | Chart 214 | 1943-12-30T21:19 tz5.0167 27.6,75.25 | Le/Le | elder_siblings / **favourable** | mixed | OK | 0.55 | HTJAH-II:15034 |
| 6 | Chart 215 | 1953-02-26T21:20 tz5.5 13,77.583 | Vi/Vi | elder_siblings / **favourable** | mixed | OK | 0.6 | HTJAH-II:15083 |
| 7 | Chart 216 | 1925-05-12T07:30 tz5.5 13.067,80.283 | Ta/Ta | elder_siblings / **afflicted** | afflicted | OK | 0.6 | HTJAH-II:15131 |
| 8 | Chart 217 | 1922-10-28T20:40 tz5.5 9.917,78.117 | Ta/Ta | gains / **favourable** | favourable | OK | 0.6 | HTJAH-II:15242 |
| 9 | Chart 218 | 1904-04-18T17:57 tz5.5333 25.3,83 | Li/Li | gains / **favourable** | afflicted | OK | 0.6 | HTJAH-II:15288 |
| 10 | Chart 219 | 1863-07-30T14:00 tz-5.5389 42.083,-83.083 | Sc/Sc | gains / **favourable** | favourable | OK | 0.55 | HTJAH-II:15331 |
| 11 | Chart 220 | 1893-04-07T09:31 tz5.0611 20.933,75.917 | Ta/Ge | gains / **favourable** | favourable | DECODE-MISMATCH | 0.6 | HTJAH-II:15390 |
| 12 | Chart 223 | 1939-06-03T22:30 tz5.5 24.85,67.067 | Sg/Sg | gains / **favourable** | afflicted | OK | 0.6 | HTJAH-II:15559 |
| 13 | Chart 225 | 1892-10-16T07:12 tz5.0667 13,76 | Li/Li | acquisitions / **favourable** | mixed | OK | 0.55 | HTJAH-II:15654 |
| 14 | Chart 227 | 1926-04-21T01:40 tz0 51.5,-0.083 | Cp/Cp | acquisitions / **favourable** | mixed | OK | 0.6 | HTJAH-II:15776 |
| 15 | Chart 228 | 1953-02-20T01:10 tz5.5 12.333,75.65 | Sc/Sc | gains / **favourable** | favourable | OK | 0.5 | HTJAH-II:15833 |
| 16 | Chart 229 | 1917-11-19T23:12 tz5.5 25.45,81.85 | Cn/Cn | gains / **favourable** | favourable | OK | 0.6 | HTJAH-II:15890 |
| 17 | Chart 230 | 1894-06-23T22:00 tz0 51.5,-0.083 | Cp/Cp | gains / **mixed** | afflicted | OK | 0.55 | HTJAH-II:15956 |
| 18 | Chart 232 | 1933-09-29T22:15 tz5.5 10.833,78.7 | Ta/Ta | gains / **mixed** | afflicted | OK | 0.6 | HTJAH-II:16087 |

**Extractor notes:** Source of truth: HTJAH-II raw text at data/knowledge_library/sources/how_to_judge_horoscope_raman2/chapter_001_full-text-unsplit.md (line numbering matches the HTJAH-II:<line> citations exactly; verified line 15155 = the Jupiter/Dhanakaraka karaka sentence). Valid _H11 fine sig keys per significations.py are exactly: gains, elder_siblings, friends, acquisitions. I routed Brothers charts -> elder_siblings; financial/industrial gains -> gains; "post of honour / trusteeship / titular rulership" charts (225, 227) -> acquisitions (Raman's own gains-scope: "acquisition of a post of honour, trusteeship... and inheritance of properties", HTJAH-II:15151-15154). I did NOT use "friends" — no worked chart's verdict is about friends.

Lagna derivation: For every chart Raman names the Lagna-frame 11th-house sign in clean prose, so I derived lagna_sign = ((eleventh_sign + 1) % 12) + 1 (11th house is 10 signs after Lagna). Cross-checked against the named 11th-lord planet and against explicit Lagna-lord statements in the text (e.g. 214 "Lagna lord the Sun"=Leo; 219 "Lagna lord Mars in the 10th"=Scorpio; 221/223/224 "Jupiter is also the Lagna lord"=Sagittarius; 225 "Lagna lord Venus in parivartana with 11th lord Sun"=Libra; 227 "Mars exalted in Lagna"+"Lagna lord Saturn"=Capricorn; 229 "Cancer being the Ascendant"=Cancer; 231 "malefic for Sagittarius Ascendant"=Sagittarius). All 18 cross-checks were internally consistent.
- Chart 213: Lagna NOT stated in clean prose; derived as Aries (11th lord Saturn -> 11th = Aquarius; karaka Mars "in own sign in a quadrant from Lagna" only fits Lagna=Aries with Mars in Aries). Confidence lowered to 0.5.

SKIPPED charts:
- Chart 209 (29-4-1948, 9-48 a.m. IST, 12N52, 74E53): a METHOD FIXTURE for timing-factor identification, not a co-born/gains verdict ("Mars, Saturn, Jupiter, Mercury, Sun, Rahu, Venus produce 11th results par excellence"; native started his own business in Jupiter-AD/Rahu-MD). Its Lagna sign is NOT stated in clean prose and the rasi diagram OCR is too garbled to trust (would force stated_lagna_sign=0, breaking the orchestrator's cast-Lagna verification). Excluded to keep the goldens verifiable; full birth data is otherwise present if you want it later.
- Charts 221, 222, 224, 226, 231: dropped only to honour the ~18 cap (all have clean place data and clear verdicts). 226 in particular has OCR-destroyed latitude ("9 N E a a aa a 78 E 37" at line 15677-78) — longitude 78E37 is clean but latitude minutes are lost (~9N00, likely Madurai-region), so it was the weakest data-quality candidate. 222's verdict text contains a self-referential OCR error ("could not come anywhere near the financial level of Chart Nos 221 and 222" — a chart cannot rank below itself; editorial reading is 221/229).

OCR / parsing notes that affected included charts:
- Chart 228: printed time "19-10 a.m." is impossible for a.m.; combined with the dual civil date "19/20-2-1953" (an after-midnight birth), this is an OCR corruption of "1-10 a.m." I set birth_dt=1953-02-20T01:10 (the later of the 19/20 night). Year also printed garbled as "7253" -> 1953 (confirmed by "Born ... at 12 N 20, 75 E 39" and by the chart sequence). Confidence 0.5.
- Chart 221: printed date "30/31-7-1896 at 4-30 a.m." -> after-midnight birth, civil date 1896-07-31 used in birth_dt (dropped from the final 18 for the cap, but noted for completeness).
- Chart 230: also dual-date-free 23-6-1894 10 p.m. LMT at London (51N30, 0W05) -> tz=0 (LMT at Greenwich ≈ GMT).
- LMT births: tz computed as longitude/15. 214 (75E15 ->+5.0167), 218 (83E0 ->+5.5333), 219 (83W5 -> -5.5389, Western longitude negative — Detroit-area, lon -83.083), 220 (75E55 ->+5.0611), 221 (73E ->+4.8667), 222 (79E36 ->+5.3067), 225 ("D.M.T." = local/LMT, 76E ->+5.0667).
- Coordinate conversions use N/E positive, W negative; arc-minutes/60 (e.g. 13N04 -> 13.067; 80E17 -> 80.283; 0W05 -> -0.083).

Verdict-ordinal mapping rationale: Brothers charts that confer at least one surviving elder co-born but with a death/limitation = "mixed" (211, 212, 213); outright denial = "afflicted" (210, 216); clean presence of co-borns = "favourable" (214, 215). All "Gains" charts with a clear wealth/industrial/inheritance outcome = "favourable". The three "Loss or Gain" reversal fixtures (230, 232; 231 not included) = "mixed" by design — strong gains-yoga delivered then withdrawn via the combust/eclipsed 11th-lord-as-functional-malefic reversal pattern the methodology doc flags (Engine Note 2).

All 18 emitted charts have full date+time+place. None required birth_dt="" or stated_lagna_sign=0.
