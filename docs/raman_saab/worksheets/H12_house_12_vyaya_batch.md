# Stage-2 validation worksheet — H12 (house_12_vyaya)

Worked charts from HTJAH-II. All `verdict_review: DRAFT` (inert until you confirm).
Reply with confirmations/corrections (sig + ordinal). `DECODE-MISMATCH` = my cast Lagna
disagrees with the stated Lagna → birth-decode needs a second look before confirming.

| # | Chart | Birth | castLagna/stated | sig / DRAFT | engine | status | conf | cite |
|---|---|---|---|---|---|---|---|---|
| 1 | Chart 234 | 1896-02-29T13:00 tz4.866 20.6,72.983 | Ge/? | moksha / **mixed** | afflicted | UNVERIFIED | 0.5 | HTJAH-II:16890 |
| 2 | Chart 239 | 1893-04-07T09:31 tz5.061 20.933,75.917 | Ta/? | expenditure / **mixed** | favourable | UNVERIFIED | 0.5 | HTJAH-II:17048 |
| 3 | Chart 240 | 1948-11-25T19:28 tz5.5 13.333,74.8 | Ge/? | expenditure / **favourable** | favourable | UNVERIFIED | 0.55 | HTJAH-II:17087 |
| 4 | Chart 242 | 1901-06-06T00:00 tz7.517 -7.25,112.75 | Aq/? | expenditure / **mixed** | afflicted | UNVERIFIED | 0.45 | HTJAH-II:17143 |
| 5 | Chart 243 | 1934-02-15T09:15 tz5.5 12.3,76.65 | Pi/? | expenditure / **afflicted** | mixed | UNVERIFIED | 0.6 | HTJAH-II:17170 |
| 6 | Chart 244 | 1928-01-05T17:26 tz5.5 27.45,68.133 | Ge/? | incarceration / **afflicted** | favourable | UNVERIFIED | 0.6 | HTJAH-II:17211 |
| 7 | Chart 245 | 1738-07-04T07:46 tz-0.006 51.5,-0.083 | Le/? | expenditure / **mixed** | favourable | UNVERIFIED | 0.55 | HTJAH-II:17243 |
| 8 | Chart 246 | 1887-08-07T13:21 tz5.134 11,77.017 | Sc/? | expenditure / **mixed** | afflicted | UNVERIFIED | 0.5 | HTJAH-II:17251 |
| 9 | Chart 247 | 1869-10-02T07:45 tz4.654 21.617,69.817 | Li/? | incarceration / **afflicted** | mixed | UNVERIFIED | 0.55 | HTJAH-II:17291 |
| 10 | Chart 248 | 1883-05-28T21:25 tz4.926 18.383,73.883 | Sg/? | incarceration / **afflicted** | mixed | UNVERIFIED | 0.6 | HTJAH-II:17321 |
| 11 | Chart 249 | 1889-11-14T23:03 tz5.467 25.417,82 | Cn/Cn | incarceration / **afflicted** | afflicted | OK | 0.65 | HTJAH-II:17349 |
| 12 | Chart 250 | 1910-05-19T08:29 tz5.5 18.517,73.867 | Ge/? | incarceration / **afflicted** | afflicted | UNVERIFIED | 0.6 | HTJAH-II:17378 |
| 13 | Chart 251 | 1883-03-24T18:00 tz5.172 13,77.583 | Vi/? | left_eye / **afflicted** | afflicted | UNVERIFIED | 0.6 | HTJAH-II:17420 |
| 14 | Chart 252 | 1608-12-09T06:30 tz-0.006 51.517,-0.083 | Sc/? | left_eye / **afflicted** | afflicted | UNVERIFIED | 0.55 | HTJAH-II:17447 |
| 15 | Chart 253 | 1947-08-01T22:10 tz5.5 14.817,74.25 | Pi/? | left_eye / **afflicted** | afflicted | UNVERIFIED | 0.55 | HTJAH-II:17482 |
| 16 | Chart 254 | 1951-08-02T13:35 tz5.5 13,77.5 | Sc/? | left_eye / **afflicted** | favourable | UNVERIFIED | 0.55 | HTJAH-II:17507 |
| 17 | Chart 257 | 1917-11-13T08:30 tz5.5 12.967,77.583 | Sc/? | moksha / **favourable** | mixed | UNVERIFIED | 0.65 | HTJAH-II:17587 |
| 18 | Chart 258 | 1892-10-16T07:12 tz5.067 13,76 | Li/? | moksha / **favourable** | mixed | UNVERIFIED | 0.65 | HTJAH-II:17627 |

**Extractor notes:** Source: docs/raman_saab/methodology/house_12_vyaya.md "Example-Chart Insights" (charts 233-258), cross-checked against the raw HTJAH-II text at data/knowledge_library/sources/how_to_judge_horoscope_raman2/chapter_001_full-text-unsplit.md. Valid _H12 fine keys confirmed in app/raman_saab/doctrine/significations.py: loss_moksha, expenditure, foreign_residence, moksha, incarceration, left_eye. (No clean key exists for sayana-sukha/bed-comforts; those charts routed to the nearest valid key.)

SECTION HAS 26 WORKED CHARTS (233-258), all with full birth data (date+time+place). Capped output at 18 with a deliberate domain balance: incarceration (244,247,248,249,250), eyes/left_eye (251,252,253,254), expenditure (239,240,242,243,245,246), moksha/renunciation (234,257,258).

CHARTS OMITTED to stay within ~18 (all have valid birth data; can be added if more goldens wanted):
- Chart 233 (12-2-1856 12:21 LMT, 18N 84E, line 16571): Moon-in-12 karaka dictum; verdict is about MOTHER (4th-house fortune), not a true 12th-house outcome -> poor fit, would have been loss_moksha/favourable conf 0.4.
- Chart 235 (30-4-1896 04:08 LMT, 23N45 91E30, line 16925): great mystic + spiritual celibacy -> moksha/favourable conf 0.6. Strong but moksha already well-represented.
- Chart 236 (21-2-1879 05:00 LMT, 13N5 80E2, line 16957): wife died, never remarried, deeply spiritual; core matter is DENIAL OF BED-COMFORTS (sayana-sukha) which has no valid _H12 key -> would map to moksha/mixed conf 0.5.
- Chart 237 (8-4-1919 19:00 GMT, 19S40 30E00, line 16966): staunch Christian missionary (voluntary renunciatory service) -> moksha/favourable conf 0.55. Note tz=0 (GMT) and SOUTHERN latitude (-19.667).
- Chart 238 (10-10-1917 22:21 LMT, 27N30 77E43, line 17016): celibate spiritually-evolved mass leader -> moksha/favourable conf 0.6.
- Chart 241 (1-4-1898 01:23 LMT, 13N20 74E49, line 17117): moksha-karaka Rahu in 12th; selfless philanthropist -> expenditure/favourable conf 0.55. Date printed ambiguously as "30/1-4/5-1898"; resolved to 1-4-1898.
- Chart 255 (24-7-1933 01:40 IST, 21N9 79E9, line 17535): spiritual aspirant taking to austerity/sadhana -> moksha/favourable conf 0.55. Date "23/24-7-1933" resolved to 24th.
- Chart 256 (19-9-1936 10:50 IST, 10N30 78E45, line 17563): full-time sadhaka -> moksha/favourable conf 0.6.

LAGNA: Only Chart 249 states its Lagna explicitly ("Ascendant Cancer" at source line 17357 area) -> stated_lagna_sign=4. All other example-chart blocks give only lord-based hints (e.g. "Lagna lord Mars/Venus/Mercury") that do not pin a single sign, and the OCR rasi-diagram grids are too garbled to read Lagna position reliably, so stated_lagna_sign=0 for the rest. The orchestrator should cast from birth data; Lagna verification will only be possible for Chart 249 here.

LMT TZ: computed as longitude/15. Examples: 245 & 252 at 0W05 -> tz -0.006; 247 at 69E49 -> 4.654; 248 at 73E53 -> 4.926; 246 at 77E1 -> 5.134; 251 at 77E35 -> 5.172; 258 at 76E -> 5.067; 242 at 112E45 -> 7.517; 234 at 72E59 -> 4.866; 239 at 75E55 -> 5.061; 249 at 82E -> 5.467. IST charts -> 5.5; Chart 237 G.M.T. -> 0.

AM/PM CARE TAKEN: evening/PM births correctly converted to 24h -> 234 13:00, 238 22:21, 240 19:28, 243 (a.m.) 09:15, 244 17:26, 246 13:21, 248 21:25, 249 23:03, 251 18:00, 253 22:10, 254 13:35. Chart 242 "about midnight" -> 00:00.

OCR / DATA CAVEATS:
- Chart 252 birth date is "9-12-1608 (O.S.)" = Old Style / Julian calendar; recorded the printed date as 1608-12-09. Whoever casts it must decide Julian-vs-Gregorian handling (engine uses GREG_CAL by convention) -> ~10-day proleptic shift possible; flagged.
- Charts with slash-dates: 236 "20/21-2-1879" (used 21st, the post-midnight 5 a.m. date); 241 "30/1-4/5-1898" (resolved 1-4-1898 for the 1:23 a.m. time); 255 "23/24-7-1933" (used 24th). These are genuinely ambiguous in the source.
- No chart in this section lacked positional data, so none were skipped for that reason.
- The methodology md's Example-Chart Insights cite the ANALYSIS-START line (e.g. 16571 for 233); citation_line values use those analysis-start lines, which differ slightly from the in-prose verdict-line ranges also given in the md.
