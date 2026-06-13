# Stage-2 validation worksheet — H10 (house_10_karma)

Worked charts from HTJAH-II. All `verdict_review: DRAFT` (inert until you confirm).
Reply with confirmations/corrections (sig + ordinal). `DECODE-MISMATCH` = my cast Lagna
disagrees with the stated Lagna → birth-decode needs a second look before confirming.

| # | Chart | Birth | castLagna/stated | sig / DRAFT | engine | status | conf | cite |
|---|---|---|---|---|---|---|---|---|
| 1 | Chart 114 | 1889-11-14T23:03 tz5.4667 25.4167,82 | Cn/Cn | profession_learned / **favourable** | favourable | OK | 0.55 | HTJAH-II:9693 |
| 2 | Chart 126 | 1912-08-08T19:35 tz5.5 13,77.5 | Aq/Aq | profession_learned / **favourable** | favourable | OK | 0.65 | HTJAH-II:10714 |
| - | Chart 164 | — | — | profession_trade / favourable | — | SKIP(no birth/place) | — | HTJAH-II:12186 |
| 3 | Chart 195 | 1884-06-04T10:18 tz5.1089 12,76.6333 | Cn/Cn | profession_authority / **favourable** | favourable | OK | 0.65 | HTJAH-II:13336 |
| 4 | Chart 198 | 1889-11-14T23:03 tz5.4667 25.4167,82 | Cn/Cn | profession_authority / **mixed** | afflicted | OK | 0.6 | HTJAH-II:13503 |
| 5 | Chart 203 | 1769-08-15T10:28 tz0.5778 41.9167,8.6667 | Li/Li | status_honour / **mixed** | mixed | OK | 0.5 | HTJAH-II:13808 |
| 6 | Chart 204 | 1883-07-29T14:00 tz1.0667 41,16 | Sc/Sc | status_honour / **mixed** | mixed | OK | 0.45 | HTJAH-II:13892 |
| 7 | Chart 208 | 1722-02-08T02:15 tz5.1722 13,77.5833 | Sc/Li | status_honour / **favourable** | afflicted | DECODE-MISMATCH | 0.5 | HTJAH-II:14172 |

**Extractor notes:** Source: docs/raman_saab/methodology/house_10_karma.md "Example-Chart Insights" (HTJAH-II, charts 114-208). Valid _H10 fine sig keys from app/raman_saab/doctrine/significations.py: career, profession_authority, profession_trade, profession_learned, profession_labour, status_honour.

INCLUSION RULE APPLIED: Only charts that PRINT explicit lat/lon coordinates qualified as Track-B goldens. Of ~95 worked charts (114-208), only 8 distinct chart-entries print coordinates. Extracted all 8 (under the ~18 cap). The vast majority of charts (118-194 etc.) print a date only (sometimes a time) with NO place/coordinates, so they were skipped per instructions.

NAMED FIGURES WITH TZ BUT NO PRINTED COORDINATES (skipped per "do not invent" rule): Chart 196 King George VI (3:05am GMT, no coords), 197 Subhas Chandra Bose (~noon LMT, no coords), 199 Truman (4:26pm LMT, no coords), 200 Morarji Desai (noon LMT, no coords), 201 Queen Elizabeth II (1:40pm GMT, no coords), 202 Tippu Sultan (8am LMT, no coords), 205 Nixon (9:30pm PST, no coords), 206 Indira Gandhi (11:13pm IST, no coords), 207 Zulfikar Ali Bhutto (4:29pm LMT, no coords). These have famous birthplaces but the text gives no lat/lon, so they cannot be coordinate-pinned without fabrication.

DUPLICATE NOTE: Chart 114 and Chart 198 are the SAME birth data (Nehru); the doc explicitly says Chart 114 "(=Chart 198, Nehru)". Both kept as separate candidates because the book treats them as two distinct worked entries with different emphases: 114 = profession-determination method (intellectual/legal political output -> profession_learned, favourable rise to PM); 198 = Rajayoga political figure (-> profession_authority, mixed: great status but vacillating/weak administrator). The orchestrator may dedupe by birth_dt if desired.

LAGNA DERIVATIONS:
- Chart 114/198 (Nehru): Cancer Lagna stated explicitly -> 4.
- Chart 126: only the 10th-house sign is stated ("Scorpio in 10th"); whole-sign back-count of 9 signs gives Lagna = Aquarius = 11 (Aquarius asc puts Scorpio on the 10th). Solid.
- Chart 164: NO Lagna and NO 10th-sign stated; it is a mislabeled header (carries Chart 169's journalist verdict) with no time printed -> birth_dt="" and stated_lagna_sign=0; confidence 0.4.
- Chart 195: "exalted Jupiter in Lagna" -> Jupiter exalts in Cancer -> Lagna = Cancer = 4.
- Chart 203 (Napoleon): no sign stated directly; derived from "Moon (10th lord)" + "Moon-Saturn parivartana" with "Saturn exactly in 10th" -> 10th sign = Cancer -> Lagna = Libra = 7. DERIVED (not stated); flag for human check (some external sources give Napoleon a Scorpio Vedic Lagna). Lower confidence.
- Chart 204 (Mussolini-type, anonymized): derived from "10th-lord Sun" -> 10th sign = Leo -> Lagna = Scorpio = 8. DERIVED; lower confidence.
- Chart 208 (Hyder Ali): derived from "debilitated Moon" (=Scorpio) among "6 planets in 2nd" -> 2nd sign = Scorpio -> Lagna = Libra = 7. DERIVED; moderate.

COORDINATE/TZ PARSING:
- 25N25 82E -> 25.4167, 82.0; LMT tz=82/15=5.4667 (114/198).
- 13N 77E30 -> 13.0, 77.5; printed IST -> tz=5.5 (126).
- 18N13 73E52 -> 18.2167, 73.8667; no time printed; India 1929 -> tz=5.5 (IST) used as best guess (164).
- 12N 76E38 -> 12.0, 76.6333; LMT tz=76.6333/15=5.1089 (195).
- 41N55 8E40 -> 41.9167, 8.6667 (Ajaccio, Corsica = Napoleon, consistent); LMT tz=8.6667/15=0.5778 (203).
- 41N 16E -> 41.0, 16.0 (southern Italy); LMT tz=16/15=1.0667 (204).
- 13N 77E35 -> 13.0, 77.5833; LMT tz=77.5833/15=5.1722 (208).

TIME -> 24h conversions verified: 11:03pm=23:03; 7:35pm=19:35; 10:18am=10:18; ~10:28am=10:28; 2pm=14:00; 2:15am=02:15.

CALENDAR NOTE: Chart 208 (Hyder Ali) and Chart 202 (Tippu Sultan, skipped) are marked "NS" (New Style/Gregorian) in the text -> 1722-02-08 / 1751 are already Gregorian; no Julian conversion needed.

OCR/SOURCE QUIRKS noted in doc itself: Chart 196 mislabeled "George IV" (corrected to VI by doc author); Chart 199 names wrong predecessor ("Theodore" vs Franklin Roosevelt); Chart 164 carries Chart 169's verdict. None affect the 8 extracted coordinate-charts except 164 (whose verdict is borrowed, hence low confidence).

SIGNIFICATION ROUTING RATIONALE: career-status charts split between profession_authority (kingship/government/political office: 114-as-PM via 198, 195, 198), status_honour (rise/fall of position, empire-founding, Rajayoga/Rajabhanga: 203, 204, 208), profession_learned (intellectual/astrology/legal-counsel avocation: 114, 126), profession_trade (Mercurial communication/journalism: 164). profession_labour was not the dominant theme in any coordinate-printing chart.
