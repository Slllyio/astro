# Stage-2 validation worksheet — H7 (house_07_kalatra)

Worked charts from HTJAH-II. All `verdict_review: DRAFT` (inert until you confirm).
Reply with confirmations/corrections (sig + ordinal). `DECODE-MISMATCH` = my cast Lagna
disagrees with the stated Lagna → birth-decode needs a second look before confirming.

| # | Chart | Birth | castLagna/stated | sig / DRAFT | engine | status | conf | cite |
|---|---|---|---|---|---|---|---|---|
| 1 | Chart 13 | 1918-10-16T14:00 tz5.17 13,77.583 | Cp/Cp | marital_happiness / **favourable** | favourable | OK | 0.6 | HTJAH-II:1687 |
| 2 | Chart 14 | 1957-11-03T10:20 tz5.5 13,77.5 | Sg/Sg | spouse / **afflicted** | favourable | OK | 0.6 | HTJAH-II:1741 |
| 3 | Chart 15 | 1941-12-08T01:20 tz5.5 13,77.583 | Vi/Vi | marital_happiness / **mixed** | afflicted | OK | 0.6 | HTJAH-II:1782 |
| 4 | Chart 16 | 1953-02-25T06:54 tz5.5 8.483,76.983 | Aq/Aq | marital_happiness / **mixed** | mixed | OK | 0.55 | HTJAH-II:1826 |
| 5 | Chart 17 | 1948-08-14T00:07 tz5.5 13,77.583 | Ta/Ta | spouse / **afflicted** | mixed | OK | 0.6 | HTJAH-II:1869 |
| 6 | Chart 18 | 1947-04-02T07:02 tz5.5 26.383,78.067 | Ar/Ar | spouse / **mixed** | mixed | OK | 0.6 | HTJAH-II:1918 |
| 7 | Chart 19 | 1938-03-16T21:30 tz5.5 12.3,76.7 | Li/Li | coverture / **mixed** | afflicted | OK | 0.55 | HTJAH-II:1976 |
| 8 | Chart 20 | 1893-04-07T09:31 tz5.06 20.933,75.917 | Ta/Ge | spouse / **mixed** | mixed | DECODE-MISMATCH | 0.5 | HTJAH-II:2002 |
| 9 | Chart 21 | 1954-10-07T22:00 tz5.5 12.3,76.7 | Ta/Ta | coverture / **afflicted** | mixed | OK | 0.65 | HTJAH-II:2054 |
| 10 | Chart 22 | 1939-11-22T22:10 tz5.5 12.15,77.15 | Cn/Cn | coverture / **afflicted** | favourable | OK | 0.6 | HTJAH-II:2118 |
| 11 | Chart 23 | 1937-03-16T18:45 tz5.5 28.85,78.817 | Vi/Vi | coverture / **afflicted** | mixed | OK | 0.6 | HTJAH-II:2173 |
| 12 | Chart 24 | 1755-11-02T20:00 tz2 46.5,30 | Ge/Ge | coverture / **afflicted** | afflicted | OK | 0.45 | HTJAH-II:2233 |
| 13 | Chart 25 | 1953-02-02T00:43 tz5.5 12.3,76.7 | Li/Li | coverture / **afflicted** | afflicted | OK | 0.45 | HTJAH-II:2280 |
| 14 | Chart 26 | 1871-10-10T14:00 tz-0.17 51.45,-2.583 | Sg/Sg | spouse / **afflicted** | afflicted | OK | 0.55 | HTJAH-II:2446 |
| 15 | Chart 27 | 1886-04-06T18:30 tz5.23 17.5,78.5 | Li/Li | spouse / **afflicted** | favourable | OK | 0.5 | HTJAH-II:2498 |
| 16 | Chart 28 | 1894-06-23T22:00 tz0 51.5,-0.083 | Cp/Cp | spouse / **mixed** | mixed | OK | 0.5 | HTJAH-II:2642 |
| 17 | Chart 29 | 1938-09-10T09:00 tz5.5 13,77.583 | Li/Li | spouse / **mixed** | afflicted | OK | 0.55 | HTJAH-II:2686 |
| 18 | Chart 30 | 1897-01-23T12:00 tz0.38 20.633,5.733 | Ar/Ar | spouse / **mixed** | afflicted | OK | 0.45 | HTJAH-II:2733 |
| 19 | Chart 32 | 1953-07-24T13:30 tz5.5 13.083,80.25 | Li/Li | spouse / **mixed** | mixed | OK | 0.55 | HTJAH-II:2834 |

**Extractor notes:** Source: docs/raman_saab/methodology/house_07_kalatra.md "Example-Chart Insights" (charts 13-32). Valid _H7 fine-sig keys read from app/raman_saab/doctrine/significations.py lines 351-398: spouse, marital_happiness, virility, coverture, wealth_through_marriage, partnership.

Scope/extraction: charts 1-12 skipped (already done). Extracted 20 candidates (13-32) but the schema cap is ~18; I kept the priority bands the prompt called out (widowhood/coverture 21-25, profligacy 26-27, cross-community 28-32) plus 13-20 worked charts. Chart 31 was DROPPED for a corrupt time and a corrupt longitude in the same line; see below. All 20 minus Chart 31 = 19 charts returned (one over the soft cap; Chart 31 dropped brings it to 19 — if a hard 18 cap is enforced, drop Chart 30 next, lowest-confidence cross-community with non-Indian place).

Signification routing rationale: widowhood/spouse-death charts (19,21-25) -> coverture (duration of married life / widowhood, the dedicated key, source _c2(2047)). Two-wives/clandestine/profligacy/cross-community charts -> spouse (its rule_tags cover spouse + character/chastity scope). Quality-of-marriage-without-loss charts (13,15,16) -> marital_happiness. No chart in this band cleanly mapped to virility, wealth_through_marriage, or partnership as the SINGLE most relevant key (Ch.27 venereal disease was secondary to the profligacy/character verdict, so routed to spouse).

Lagna derivation: every chart's Lagna derived from the stated 7th-house sign as the opposite sign (lagna = ((7th_sign-1+6)%12)+1). Ch.14 had Lagna stated directly (Sagittarius=9). Ch.19 cross-checked: 7th lord Mars in own sign in 7th + "Venus exalted in 6th" -> 6th must be Pisces -> Lagna Libra(7), 7th Aries. Ch.20 cross-checked: "Venus exalted in 10th" -> 10th Pisces -> Lagna Gemini(3) (the "7th Gemini" in the text is the from-Moon 7th, not the Lagna 7th).

AM/PM handled: evening births converted to 24h — Ch.23 18:45, Ch.24 ~20:00, Ch.27 ~18:30, Ch.21 22:00, Ch.22 22:10, Ch.28 22:00. Midnight-ish: Ch.17 00:07, Ch.25 00:43.

Timezone notes: IST=5.5. LMT charts use longitude/15: Ch.13 (77E35)->5.17, Ch.20 (75E55)->5.06, Ch.24 (30E)->2.0, Ch.26 (2W35)->-0.17, Ch.27 (78E30)->5.23, Ch.28 (0W5)->~0.0, Ch.30 (5E44)->0.38, Ch.32 is IST. Ch.26 longitude 2W35 is WEST -> negative (-2.583).

OCR / data-quality flags:
- Chart 25: latitude printed as "72N78/76E42" is corrupt (78 arc-minutes is impossible; 72N is arctic, inconsistent with 76E42 = southern-India longitude). Charts 19 and 21 are BOTH printed at "12N18/76E42", the same longitude — Chart 25 (also 76E42) almost certainly shares 12N18, garbled to "72N78". I used lat 12.30 (12N18) as a best-effort inference and lowered confidence to 0.45. Also the date "7/2-2-1953" is a dual-date notation; I took 2-2-1953.
- Chart 31 (22/23-11-1902, "5:76 am" LMT, 23N6/72E40): the time "5:76" is uninterpretable (76 minutes) AND it sits with otherwise-OK place data; per the rules I would set birth_dt="" but with a corrupt minute the cast-Lagna verification is unreliable, so I DROPPED it rather than emit a misleading birth_dt. Place (23.10N, 72.667E ~ Ahmedabad) and 7th Aries -> Lagna Libra(7) are recoverable if a human resolves the minute (likely 5:16 am). Verdict was "high-caste Hindu married a Parsee widow with children" -> spouse / mixed.
- Chart 23 pagination caveat (noted in the .md at lines 528-533): the "wife died in 1970" sentence at HTJAH-II:2191 belongs to CHART 22 (wife-death), not Chart 23 (a woman's chart ending in widowhood). I attributed wife-death to Ch.22 and widowhood to Ch.23 accordingly.

Charts with NO positional data in this band: none — every worked chart 13-32 prints a place (lat/lon), so none were skipped for missing coordinates. The only drop was Chart 31 (corrupt time, see above).

Confidence calibration: 0.6-0.65 for clear loss/widowhood verdicts with full Indian birth data and clean Lagna derivation (21,22,23,13,14,15,17,18,19); 0.5-0.55 for cross-community/profligacy where the verdict ordinal sits between mixed and afflicted, or non-Indian LMT places; 0.45 for charts with OCR-corrupt or approximate data (24 ~20:00, 25 corrupt lat, 30 approx noon foreign place).
