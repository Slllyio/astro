# Cast fidelity sweep, 2026-10-25

Read-only audit. Nothing in the engine, the goldens or the baseline was changed.

## Summary

Every scored golden chart that is cast from birth data (199 records with at least one CONFIRMED verdict: NH 27, HTJAH-I 81, HTJAH-II 91) was cast exactly as the harness does (`tests/raman_saab/test_goldens.py::build_chart`, Raman ayanamsa, mean node) and compared with what Raman printed for that chart.

| Check available | Charts | What was compared |
|---|---|---|
| Printed degrees (NH "Planetary Positions") | 27 | every printed body and the Lagna, to the arc-minute |
| Dasa balance at birth (HTJAH I/II) | 123 | the Moon longitude implied by Raman's printed balance |
| Sign level only | 49 | Lagna and placements stated in Raman's prose, where he states any |

The balance is a precise check. Across the 252 charts (scored or not) where it could be read, the implied Moon matches the cast to a median of 0.05 deg (p75 0.36 deg), and in 20 NH charts it matches Raman's own printed Moon to 0.0 deg. It has two blind spots. A Moon wrong by about 120 deg (a 9-day slip) can land in another nakshatra of the same lord. And Raman's balance itself is sometimes misprinted: three charts below have a balance that contradicts his own prose.

**13 MISFITS.** Eight are certain, two are probable on independent evidence, and three rest on the balance alone:

| # | Golden | Record | Proposed | Evidence | Residuals at proposal |
|---|---|---|---|---|---|
| 1 | NH.chart_26 Karl Marx | 1818-05-15 02:00 | **1818-05-05 02:00** | printed Sun/Moon/Lagna; history (born 5 May 1818, Trier) agrees; "15th" is a misprint | Moon 2.7, Sun 0.24, Lagna 0.33 deg |
| 2 | NH.chart_36 Swami Vivekananda | 1863-01-12 18:33 | **1863-01-12 06:33** | printed Lagna 267 31 (Sagittarius) and every body; history (sunrise birth, Sagittarius rising) agrees. The record's Cancer Lagna is the p.m. misprint | all bodies 0.0, Lagna 0.09 deg |
| 3 | NH.chart_67 Dhana-yoga example | 1896-01-30 04:30 | **1896-01-31 04:30** | printed "30th/31st January ... 4-30 a.m."; Sun off 1.0 deg and Moon 12.6 deg on the 30th; HTJAH-II.chart_35 (same native) is already recorded as the 31st | Moon 2.1, Sun 0.04, Lagna 0.9 deg |
| 4 | HTJAH-I.chart_53 | 1880-08-24 20:44, tz 5.3333, lon 80.0 | **1890-08-24 20:44, tz 5.1722, lon 77.5833** | OCR "18*0". Prose: Rahu in 3rd Taurus, Venus debilitated in 7th with exalted Mercury, Mars in 9th own sign. 1890 meets all of it, 1880 none. Same birth moment as HTJAH-I.chart_43 (1890). Printed longitude is 5h 10m 20s (77 35 E) | prose features all met |
| 5 | HTJAH-I.chart_15 | 1891-06-09 03:34 | **1891-06-10 03:34** | printed "9/10-6-1891 at 3-34 a.m."; balance Saturn 15-6-6 | balance Moon 1.2 deg (11.5 now) |
| 6 | HTJAH-I.h6_11 (Chart 120) | 1902-07-19 03:45 | **1902-07-10 03:45** | printed "1019-7-1902" means 10/9 (Raman also writes 25/24, 3/2, 29/28). Prose: Sun and Mercury with Mars in Gemini Lagna, Venus in 12th. True on the 10th, false on the 19th (Sun in Cancer, Venus in Lagna) | balance Moon 0.3 deg |
| 7 | HTJAH-I.h4_03 (Chart 77, Dublin, G. B. Shaw) | 1856-07-26 00:00 | **1856-07-27 00:00** (midnight closing the 26th) | balance Moon 6-6-18; prose: Jupiter is "lord of the 11th from Chandra Lagna", which needs the Moon in Taurus (it is in Aries at the record's time) | balance Moon 0.2 deg |
| 8 | HTJAH-II.h12_14 (Chart 252, John Milton) | 1608-12-09 06:30 | **1608-12-19 06:30** (Gregorian for 9 Dec O.S.) | Raman prints "(O.S.)" but the engine casts Gregorian. Balance fits; prose has 12th lord Venus with Saturn (Capricorn); NH No. 16 prints Sun 251 48, Moon 42 18, Lagna 226 18 | balance 0.5; vs NH-16: Moon 0.7, Sun 0.9, Lagna 4.3 deg (0.2 at 06:08) |
| 9 | NH.chart_25 Lord Tennyson | 1809-08-06 23:45 | **1809-08-05 23:41** (about midnight 5/6 Aug) | printed Moon 53 45 and prose "Lagna is occupied by the Moon" (Taurus); the record puts the Moon in Gemini. History says 6 Aug, which fits only if he was born just after midnight 5/6. Raman's own balance (Rahu 6-1-26) fits neither date, so his figures are internally inconsistent | Moon 0.3, Sun 0.5, Lagna 0.2 deg |
| 10 | NH.chart_62 Ramakrishna Dalmia | 1893-04-07 09:31 | **1893-04-07 09:43** | printed Lagna 60 49 and prose "Gemini Lagna rising"; the record casts Taurus 27.8. Every body matches to 0.0 deg, so this is Raman's Lagna arithmetic, a 12-minute equivalent | Moon 0.08, Sun 0.02, Lagna 0.12 deg |
| 11 | HTJAH-I.chart_29 | 1903-03-18 00:00 | 1903-03-19 00:00 (prints "12 a.m.", read as midnight ending the 18th) | balance only (Saturn 8-11-3); the Moon moves Libra -> Scorpio; Lagna Scorpio either way | balance 0.1 deg (12.4 now) |
| 12 | HTJAH-II.h12_04 (Chart 242, Sukarno) | 1901-06-06 00:00 | 1901-06-07 00:00 ("about midnight" ending the 6th) | balance only; same signs either way (Aquarius Lagna, Moon in 12th) | balance 0.1 deg (13.0 now) |
| 13 | HTJAH-I.chart_18 | 1896-08-12 01:52 | 1896-08-13 01:52 (Hindu day: 1:52 a.m. "of the 12th") | balance only: Moon dasa needs a Moon nakshatra (Hasta), and on the 12th the Moon is in Uttara Phalguni; prose is silent on the Moon | balance 4.0 deg (10.7 now). Lowest confidence |

**Scoring impact** (harness `_signification_verdict` on the 30 confirmed rows of these 13 charts, record cast vs proposed cast): exact **26 -> 19**, within one **30 -> 25**, real errors **0 -> 5**. The wrong casts were scoring well:

- **Vivekananda:** the Cancer-Lagna chart matches all 5 of Raman's verdicts. Raman's own Sagittarius chart matches 2, with 3 inversions: H7 spouse, H9 father and H10 profession all turn favourable -> afflicted.
- **Dhana-yoga example:** H5 children turns favourable -> afflicted (an inversion). H7 and H11 each move one step.
- **Dalmia:** H7 marital happiness turns afflicted -> favourable (an inversion). H2 becomes an exact hit.
- **Marx:** H2 moves exact -> one step out.
- **HTJAH-I.chart_53:** H3 moves one step out -> exact.
- **Sukarno:** H12 moves exact -> one step out.
- **The other seven** (Tennyson, Shaw, Milton, HTJAH-I.chart_15, chart_18, chart_29, h6_11): no verdict changes.

Correcting these charts lowers the figures. By the project's own rule (measure honestly, never protect the number) that is the measurement becoming truthful.

**Anomalies that are not birth-data errors** (cast confirmed by other printed evidence):

- **Misprinted balances.** HTJAH-II.h7_14, h7_17 and h9_07 have balances that contradict Raman's prose placement of the Moon, and the prose agrees with the cast.
- **Print or OCR slips in NH degrees.**
  - Narasimha Bharathi: Lagna printed "92 50" for 192 50.
  - Gaekwar: Moon 220 30 printed, though the balance agrees with the cast's 228.5.
  - Einstein: Saturn 333 30 printed for 343 30.
  - Suddhananda: Ketu printed as 19 for 109.
  - Ramakrishna: Rahu and Ketu printed swapped.
- **HTJAH-I.chart_58** was re-timed by an hour before this sweep. It has no balance, and Raman's "Saturn in a Kendra" holds in neither cast. It is listed, not re-opened.

Note on `lagna_sign`: in these records it agrees with the cast in every scored chart because it was filled in from the cast, so it is not an independent check (Vivekananda's record says 4, Cancer, where Raman printed Sagittarius).

## Method

1. **Cast.** The harness file was loaded by path (the `importlib` pattern of `tools/raman_saab/procedure_reader_measure.py`) and `_birth_from` / `build_chart` were used. Bulk comparisons and the candidate search used the same swisseph calls as `app/raman_saab/chart/adapter.py::cast_chart` (`houses_ex` with "O" and `FLG_SIDEREAL`, `SIDM_RAMAN`, `MEAN_NODE`). Verdicts came from the harness's own `build_chart` and `_signification_verdict`.
2. **Printed data.**
   - **NH:** the "Planetary Positions" paragraph after each "No. N.-" header, with manual reads where OCR broke the parse (Vivekananda's "Plarutary Positions", degree-only entries such as "Lagna 55 deg").
   - **HTJAH I/II:** the "Chart No. N.- Born ..." header that matches the record's chart number and printed date, and the "Balance of X Dasa at birth" line between that header and the next one. Charts that are re-printed in both volumes share balances by printed date.
   - **Balance to Moon:** elapsed fraction of the nakshatra = 1 - balance / dasa years. Of the lord's three nakshatras, the one nearest the cast is used.
   - **Placements in prose:** placement phrases in the record's cited lines ("X is in <sign>", "exalted/debilitated X", "Lagna is <sign>"). Every conflict was read by hand.
3. **Flag rules (as specified).**
   - Moon differs by more than 6 deg (printed degree, or implied by the balance).
   - Jupiter, Saturn or the nodes differ by more than 3 deg; the Sun by more than 3 deg was added as a date-slip check.
   - The printed or prose Lagna sign differs.
   - A stated sign placement differs.

   A flag counts as a MISFIT only after reading the text: a printed slip or misprint that the rest of Raman's data contradicts is listed as an anomaly instead.
4. **Candidate search.**
   - **Moves tried:** day offsets of -3..+3 and +/-10/20/30 days, AM/PM (+/-12 h), and minute shifts of +/-90 in 2-minute steps.
   - **Score minimised:** Moon error + 3 x Sun error + Lagna error / 2, with a 5-point penalty for the wrong Lagna sign.
   - **Accepted candidates:** only the simplest edit consistent with the printed text (double date, "midnight", O.S., OCR digit).
5. **Limits.**
   - **Sign-only charts (49):** nothing finer than the signs can be checked, and many prose passages never state a placement.
   - **Blind spot of the balance check:** it cannot see a Moon displaced by a multiple of 120 deg. HTJAH does not print the Sun, so a 9- or 18-day slip in a balance-only chart could go unseen unless the prose names a placement.
6. **Out of scope.** Unscored charts were swept too, but are not reported here.

## Full table (199 scored charts)

Moon column: printed or balance-implied / cast (difference, deg); for sign-only charts, the cast sign. Lagna column: printed / cast. For NH, the extra column gives the Sun, Jupiter, Saturn and Rahu differences in deg.

| Golden | Record dt | Check | Moon printed / cast (diff) | Lagna printed / cast | Extra | Status | Note |
|---|---|---|---|---|---|---|---|
| HTJAH-I.chart_10 | 1912-08-08T19:35 | balance | 55.0 / 55.1 (0.0) | -- / Aq 9.7 | bal Mars 6-1-6 | fit |  |
| HTJAH-I.chart_12 | 1918-10-16T14:20 | balance | 311.3 / 311.2 (0.1) | -- / Cp 26.8 | bal Rahu 11-8-20 | fit |  |
| HTJAH-I.chart_15 | 1891-06-09T03:34 | balance | 95.8 / 84.3 (11.5) | -- / Ar 28.3 | bal Saturn 15-6-6 | **MISFIT** |  |
| HTJAH-I.chart_17 | 1864-03-09T11:15 | balance | 341.7 / 343.6 (1.9) | -- / Ta 22.3 | bal Saturn 7-0-22 | fit | header OCR'd as "Chart No. 11"; balance Saturn 7-0-22 fits |
| HTJAH-I.chart_18 | 1896-08-12T01:52 | balance | 165.3 / 154.6 (10.7) | -- / Ge 4.0 | bal Moon 6-0-14 | **MISFIT** |  |
| HTJAH-I.chart_20 | 1909-07-29T06:42 | balance | 234.7 / 235.1 (0.4) | -- / Cn 26.7 | bal Mercury 6-8-27 | fit |  |
| HTJAH-I.chart_24 | 1898-08-29T05:30 | balance | 279.9 / 280.3 (0.4) | -- / Le 10.1 | bal Sun 0-0-18 | fit |  |
| HTJAH-I.chart_29 | 1903-03-18T00:00 | balance | 220.4 / 208.0 (12.4) | -- / Sc 27.4 | bal Saturn 8-11-3 | **MISFIT** |  |
| HTJAH-I.chart_31 | 1903-10-21T10:43 | balance | 191.5 / 193.0 (1.6) | -- / Sg 12.1 | bal Rahu 11-6-11 | fit |  |
| HTJAH-I.chart_33 | 1910-10-31T13:41 | sign | -- / Vi 26.9 | -- / Aq 2.4 |  | fit |  |
| HTJAH-I.chart_35 | 1903-05-28T00:32 | sign | -- / Ta 26.0 | -- / Aq 18.2 |  | fit |  |
| HTJAH-II.chart_33 | 1912-08-08T19:35 | balance | 55.0 / 55.1 (0.0) | -- / Aq 9.7 | bal Mars 6-1-6 | fit |  |
| HTJAH-II.chart_34 | 1879-12-30T01:00 | balance | 89.9 / 89.8 (0.0) | -- / Li 2.3 | bal Jupiter 4-1-20 | fit |  |
| HTJAH-II.chart_35 | 1896-01-31T04:30 | balance | 116.0 / 118.1 (2.1) | -- / Sg 15.6 | bal Mercury 5-1-6 | fit | same native as NH.chart_67, already correctly recorded as 31 Jan |
| HTJAH-II.chart_74 | 1869-10-02T07:45 | balance | 120.2 / 119.7 (0.5) | -- / Li 13.6 | bal Ketu 6-10-28 | fit |  |
| HTJAH-II.chart_73 | 1809-02-12T07:32 | balance | 275.3 / 277.7 (2.4) | -- / Aq 17.4 | bal Sun 2-1-6 | fit |  |
| HTJAH-II.chart_75 | 1917-05-29T15:00 | balance | 146.0 / 145.9 (0.1) | -- / Vi 28.8 | bal Venus 1-0-0 | fit |  |
| HTJAH-II.chart_78 | 1889-04-20T18:30 | balance | 255.8 / 255.8 (0.0) | -- / Li 5.9 | bal Venus 16-4-6 | fit |  |
| HTJAH-I.chart_52 | 1856-02-12T12:21 | balance | 18.5 / 22.2 (3.7) | -- / Ta 15.5 | bal Venus 12-3-9 | fit |  |
| HTJAH-I.chart_53 | 1880-08-24T20:44 | sign | -- / Ar 6.7 | -- / Pi 26.4 |  | **MISFIT** |  |
| HTJAH-I.chart_54 | 1887-08-07T13:35 | balance | 333.2 / 332.9 (0.3) | -- / Sc 15.9 | bal Jupiter 0-2-12 | fit |  |
| HTJAH-I.chart_55 | 1889-09-10T06:00 | balance | 330.8 / 332.5 (1.7) | -- / Le 28.5 | bal Jupiter 3-0-6 | fit |  |
| HTJAH-I.chart_56 | 1895-06-01T23:42 | balance | 156.6 / 158.5 (1.9) | -- / Aq 9.9 | bal Sun 1-6-13 | fit |  |
| HTJAH-I.chart_57 | 1864-03-09T11:27 | balance | 341.7 / 343.7 (2.0) | -- / Ta 25.2 | bal Saturn 7-0-22 | fit |  |
| HTJAH-I.chart_58 | 1901-08-28T17:30 | sign | -- / Cp 25.9 | -- / Aq 0.9 |  | anomaly | record re-timed 16:30->17:30 before this sweep (lagna_sign note); no balance printed; "Saturn in a Kendra from Lagna" not met in either cast (unresolved, pre-existing) |
| HTJAH-I.chart_59 | 1928-07-09T08:50 | sign | -- / Pi 7.6 | -- / Le 3.1 |  | fit |  |
| HTJAH-I.chart_60 | 1896-10-21T06:00 | sign | -- / Ar 0.2 | -- / Li 9.0 |  | fit |  |
| HTJAH-I.chart_61 | 1880-12-29T10:10 | balance | 223.4 / 223.4 (0.1) | -- / Aq 13.7 | bal Saturn 4-7-9 | fit |  |
| HTJAH-I.chart_62 | 1889-08-24T17:41 | sign | -- / Cn 16.9 | -- / Aq 0.8 |  | fit | prose: Mars debilitated in 6th with waning Moon (Cancer); cast agrees |
| HTJAH-I.chart_38 | 1893-10-21T04:01 | sign | -- / Aq 11.0 | -- / Vi 8.9 |  | fit |  |
| HTJAH-I.chart_39 | 1883-03-24T06:00 | balance | 165.3 / 165.3 (0.0) | -- / Pi 10.6 | bal Moon 6-0-0 | fit |  |
| HTJAH-I.chart_40 | 1895-12-14T03:05 | balance | 213.9 / 213.9 (0.0) | -- / Li 6.2 | bal Saturn 18-2-18 | fit |  |
| HTJAH-I.chart_41 | 1900-02-04T04:00 | sign | -- / Pi 17.7 | -- / Sg 11.7 |  | fit | "Saturn in Gemini" is the Navamsa position |
| HTJAH-I.chart_42 | 1909-07-03T21:01 | balance | 260.4 / 261.8 (1.4) | -- / Cp 29.3 | bal Venus 9-4-20 | fit |  |
| HTJAH-I.chart_43 | 1890-08-24T20:44 | sign | -- / Sc 24.3 | -- / Pi 25.7 |  | fit |  |
| HTJAH-I.chart_44 | 1888-09-30T04:35 | sign | -- / Cn 4.8 | -- / Le 28.3 |  | fit |  |
| HTJAH-I.chart_45 | 1898-01-22T22:07 | sign | -- / Cp 17.1 | -- / Vi 12.8 |  | fit |  |
| HTJAH-I.chart_46 | 1891-01-30T18:39 | sign | -- / Vi 19.9 | -- / Cn 29.4 |  | fit |  |
| HTJAH-I.chart_48 | 1887-10-21T03:10 | sign | -- / Sg 1.1 | -- / Le 27.0 |  | fit |  |
| HTJAH-I.chart_49 | 1912-08-08T19:35 | balance | 55.0 / 55.1 (0.0) | -- / Aq 9.7 | bal Mars 6-1-6 | fit |  |
| HTJAH-I.chart_50 | 1883-04-15T13:30 | balance | 102.0 / 106.0 (4.0) | -- / Le 1.0 | bal Saturn 6-7-24 | fit |  |
| HTJAH-I.chart_51 | 1887-08-07T13:30 | balance | 333.2 / 332.8 (0.3) | -- / Sc 14.8 | bal Jupiter 0-2-12 | fit |  |
| HTJAH-II.chart_02 | 1942-08-03T07:23 | balance | 8.4 / 8.4 (0.0) | -- / Le 5.9 | bal Ketu 2-7-0 | fit |  |
| HTJAH-II.chart_03 | 1953-12-04T05:17 | balance | 201.6 / 201.5 (0.0) | -- / Sc 2.9 | bal Jupiter 14-1-20 | fit |  |
| HTJAH-II.chart_04 | 1950-11-20T03:00 | balance | 349.3 / 343.3 (6.0) | -- / Vi 11.8 | bal Mercury 13-7-6 | anomaly | 6.0 deg, at threshold; prose (Moon in 7th, Pisces) agrees with cast |
| HTJAH-II.chart_05 | 1935-10-08T11:30 | balance | 297.2 / 297.2 (0.0) | -- / Sg 5.1 | bal Mars 4-11-20 | fit |  |
| HTJAH-II.chart_06 | 1883-03-24T06:00 | balance | 165.3 / 165.3 (0.0) | -- / Pi 10.6 | bal Moon 6-0-0 | fit |  |
| HTJAH-II.chart_07 | 1856-02-12T12:21 | balance | 18.5 / 22.2 (3.7) | -- / Ta 15.5 | bal Venus 12-3-9 | fit |  |
| HTJAH-II.chart_08 | 1912-08-08T19:35 | balance | 55.0 / 55.1 (0.0) | -- / Aq 9.6 | bal Mars 6-1-6 | fit |  |
| HTJAH-II.chart_09 | 1940-11-03T07:00 | sign | -- / Sg 8.2 | -- / Li 20.6 |  | fit |  |
| HTJAH-II.chart_10 | 1948-03-13T10:30 | balance | 357.0 / 357.0 (0.0) | -- / Ta 10.1 | bal Mercury 3-9-27 | fit | balance Mercury 3-9-27 fits to 0.0 |
| HTJAH-II.chart_11 | 1953-12-26T23:47 | sign | -- / Le 26.8 | -- / Vi 6.3 |  | fit |  |
| HTJAH-II.chart_12 | 1940-05-21T07:50 | balance | 212.0 / 212.1 (0.0) | -- / Ge 5.5 | bal Jupiter 1-6-22 | fit |  |
| HTJAH-I.h4_01 | 1912-08-08T19:35 | balance | 55.0 / 55.1 (0.0) | -- / Aq 9.7 | bal Mars 6-1-6 | fit |  |
| HTJAH-I.h4_02 | 1856-02-12T12:21 | balance | 18.5 / 22.2 (3.7) | -- / Ta 15.5 | bal Venus 12-3-9 | fit |  |
| HTJAH-I.h4_03 | 1856-07-26T00:00 | balance | 44.6 / 30.7 (13.9) | -- / Ta 17.0 | bal Moon 6-6-18 | **MISFIT** |  |
| HTJAH-I.h4_04 | 1902-11-23T05:16 | balance | 137.4 / 137.4 (0.0) | -- / Li 24.2 | bal Venus 13-11-12 | fit |  |
| HTJAH-I.h4_05 | 1912-08-08T19:35 | balance | 55.0 / 55.1 (0.0) | -- / Aq 9.7 | bal Mars 6-1-6 | fit |  |
| HTJAH-I.h5_01 | 1903-10-30T21:30 | balance | 310.4 / 310.4 (0.0) | -- / Ge 16.4 | bal Rahu 12-11-24 | fit |  |
| HTJAH-I.h5_02 | 1912-09-30T17:15 | sign | -- / Ta 3.0 | -- / Aq 25.0 |  | fit |  |
| HTJAH-I.h5_04 | 1888-07-16T23:06 | sign | -- / Li 7.0 | -- / Pi 23.8 |  | fit |  |
| HTJAH-I.h5_05 | 1914-06-02T07:05 | sign | -- / Le 25.7 | -- / Ge 5.6 |  | fit |  |
| HTJAH-I.h5_06 | 1913-03-28T20:35 | sign | -- / Sg 5.6 | -- / Li 8.8 |  | fit |  |
| HTJAH-I.h5_07 | 1914-12-25T02:30 | sign | -- / Pi 16.8 | -- / Li 5.6 |  | fit |  |
| HTJAH-I.h5_08 | 1901-05-24T13:36 | sign | -- / Le 1.0 | -- / Vi 4.4 |  | fit |  |
| HTJAH-I.h5_09 | 1892-04-12T12:45 | balance | 182.4 / 182.7 (0.3) | -- / Cn 13.1 | bal Mars 2-3-2 | fit |  |
| HTJAH-I.h5_10 | 1897-06-03T05:30 | sign | -- / Ge 19.2 | -- / Ta 21.5 |  | fit |  |
| HTJAH-I.h5_11 | 1891-05-06T17:10 | sign | -- / Ar 1.3 | -- / Li 8.8 |  | fit |  |
| HTJAH-I.h5_12 | 1880-12-29T10:10 | balance | 223.4 / 223.4 (0.1) | -- / Aq 13.7 | bal Saturn 4-7-9 | fit |  |
| HTJAH-I.h5_13 | 1906-12-06T01:10 | sign | -- / Cn 14.4 | -- / Vi 6.7 |  | fit |  |
| HTJAH-I.h5_14 | 1907-04-11T18:50 | sign | -- / Pi 14.4 | -- / Li 3.2 |  | fit |  |
| HTJAH-I.h5_15 | 1906-01-06T17:24 | sign | -- / Ta 6.4 | -- / Ge 23.3 |  | fit |  |
| HTJAH-I.h5_16 | 1902-05-30T03:19 | sign | -- / Aq 9.5 | -- / Ar 11.2 |  | fit |  |
| HTJAH-I.h5_18 | 1905-01-29T05:00 | sign | -- / Li 29.7 | -- / Sg 20.0 |  | fit |  |
| HTJAH-II.h7_01 | 1918-10-16T14:00 | balance | 311.3 / 311.2 (0.1) | -- / Cp 26.7 | bal Rahu 11-8-20 | fit |  |
| HTJAH-II.h7_02 | 1957-11-03T10:20 | balance | 329.7 / 329.7 (0.0) | -- / Sg 14.1 | bal Jupiter 4-4-17 | fit |  |
| HTJAH-II.h7_03 | 1941-12-08T01:20 | balance | 97.4 / 97.4 (0.1) | -- / Vi 9.7 | bal Saturn 13-2-22 | fit |  |
| HTJAH-II.h7_04 | 1953-02-25T06:54 | balance | 93.9 / 93.9 (0.0) | -- / Aq 18.1 | bal Saturn 18-2-0 | fit |  |
| HTJAH-II.h7_05 | 1948-08-14T00:07 | balance | 232.8 / 232.6 (0.2) | -- / Ta 4.2 | bal Mercury 9-2-5 | fit |  |
| HTJAH-II.h7_07 | 1938-03-16T21:30 | balance | 159.6 / 159.5 (0.1) | -- / Li 17.9 | bal Sun 0-1-29 | fit |  |
| HTJAH-II.h7_09 | 1954-10-07T22:00 | balance | 291.0 / 291.2 (0.3) | -- / Ta 24.6 | bal Moon 1-9-13 | fit |  |
| HTJAH-II.h7_10 | 1939-11-22T22:10 | balance | 348.4 / 348.5 (0.1) | -- / Cn 8.7 | bal Mercury 14-8-29 | fit |  |
| HTJAH-II.h7_11 | 1937-03-16T18:45 | sign | -- / Ar 25.2 | -- / Vi 9.6 |  | fit |  |
| HTJAH-II.h7_12 | 1755-11-02T20:00 | balance | 182.0 / 181.4 (0.6) | -- / Ge 18.9 | bal Mars 2-5-9 | fit |  |
| HTJAH-II.h7_13 | 1953-02-02T00:43 | balance | 143.9 / 141.3 (2.5) | -- / Li 23.7 | bal Venus 4-2-12 | fit |  |
| HTJAH-II.h7_14 | 1871-10-10T14:00 | balance | 189.8 / 129.8 (60.0) | -- / Sg 25.4 | bal Rahu 13-8-13 | anomaly | balance misprint: prose puts Moon in Leo (cast agrees) |
| HTJAH-II.h7_15 | 1886-04-06T18:30 | balance | 18.8 / 18.9 (0.1) | -- / Li 0.5 | bal Venus 11-9-9 | fit |  |
| HTJAH-II.h7_16 | 1894-06-23T22:00 | balance | 313.0 / 313.0 (0.0) | -- / Cp 12.4 | bal Rahu 9-5-12 | fit |  |
| HTJAH-II.h7_17 | 1938-09-10T09:00 | balance | 343.2 / 328.8 (14.4) | -- / Li 6.5 | bal Saturn 5-0-0 | anomaly | balance misprint: prose puts Moon in Aquarius (7th from Moon = Leo); cast agrees |
| HTJAH-II.h10_01 | 1889-11-14T23:03 | balance | 109.3 / 109.3 (0.0) | -- / Cn 24.4 | bal Mercury 13-7-0 | fit |  |
| HTJAH-II.h10_02 | 1912-08-08T19:35 | balance | 55.0 / 55.1 (0.0) | -- / Aq 9.6 | bal Mars 6-1-6 | fit |  |
| HTJAH-II.h10_03 | 1884-06-04T10:18 | balance | 182.9 / 182.9 (0.0) | -- / Cn 27.7 | bal Mars 1-11-16 | fit |  |
| HTJAH-II.h10_04 | 1889-11-14T23:03 | balance | 109.3 / 109.3 (0.0) | -- / Cn 24.4 | bal Mercury 13-7-6 | fit |  |
| HTJAH-II.h10_05 | 1769-08-15T10:28 | balance | 276.6 / 279.2 (2.6) | -- / Li 5.1 | bal Sun 1-6-6 | fit |  |
| HTJAH-II.h10_06 | 1883-07-29T14:00 | balance | 48.3 / 48.3 (0.1) | -- / Sc 1.7 | bal Moon 3-8-26 | fit |  |
| HTJAH-II.h11_01 | 1937-08-16T08:31 | balance | 235.3 / 233.2 (2.0) | -- / Vi 5.4 | bal Mercury 6-0-8 | fit |  |
| HTJAH-II.h11_02 | 1940-05-21T07:50 | balance | 212.0 / 212.1 (0.0) | -- / Ge 5.6 | bal Jupiter 1-6-22 | fit |  |
| HTJAH-II.h11_03 | 1946-09-29T11:58 | balance | 208.8 / 208.8 (0.0) | -- / Sg 4.9 | bal Jupiter 5-5-0 | fit |  |
| HTJAH-II.h11_04 | 1974-01-06T12:40 | balance | 52.1 / 52.1 (0.1) | -- / Ar 2.6 | bal Moon 0-11-16 | fit |  |
| HTJAH-II.h11_05 | 1943-12-30T21:19 | balance | 305.0 / 304.7 (0.2) | -- / Le 10.1 | bal Mars 0-10-19 | fit |  |
| HTJAH-II.h11_06 | 1953-02-26T21:20 | balance | 113.8 / 113.0 (0.8) | -- / Vi 29.2 | bal Mercury 7-10-26 | fit |  |
| HTJAH-II.h11_07 | 1925-05-12T07:30 | balance | 257.5 / 257.5 (0.0) | -- / Ta 25.0 | bal Venus 13-9-9 | fit |  |
| HTJAH-II.h11_08 | 1922-10-28T20:40 | balance | 295.0 / 295.2 (0.2) | -- / Ta 25.8 | bal Mars 6-1-17 | fit |  |
| HTJAH-II.h11_09 | 1904-04-18T17:57 | balance | 37.7 / 37.8 (0.1) | -- / Li 1.8 | bal Sun 1-0-13 | fit |  |
| HTJAH-II.h11_10 | 1863-07-30T14:00 | sign | -- / Cp 20.1 | -- / Sc 2.3 |  | fit |  |
| HTJAH-II.h11_12 | 1939-06-03T22:30 | balance | 249.0 / 249.0 (0.0) | -- / Sg 29.4 | bal Ketu 2-3-0 | fit |  |
| HTJAH-II.h11_13 | 1892-10-16T07:12 | balance | 131.9 / 130.4 (1.5) | -- / Li 20.9 | bal Ketu 0-9-0 | fit |  |
| HTJAH-II.h11_14 | 1926-04-21T01:40 | balance | 110.7 / 110.7 (0.0) | -- / Cp 0.1 | bal Mercury 11-9-23 | fit |  |
| HTJAH-II.h11_15 | 1953-02-20T01:10 | balance | 27.2 / 27.8 (0.6) | -- / Sc 15.2 | bal Sun 5-9-4 | fit |  |
| HTJAH-II.h11_16 | 1917-11-19T23:12 | balance | 277.1 / 277.0 (0.0) | -- / Cn 29.0 | bal Sun 1-3-25 | fit |  |
| HTJAH-II.h11_17 | 1894-06-23T22:00 | balance | 313.0 / 313.0 (0.0) | -- / Cp 12.4 | bal Rahu 9-5-12 | fit |  |
| HTJAH-II.h11_18 | 1933-09-29T22:15 | balance | 294.3 / 294.3 (0.0) | -- / Ta 22.4 | bal Mars 6-5-18 | fit |  |
| HTJAH-II.h12_01 | 1896-02-29T13:00 | balance | 146.4 / 146.6 (0.1) | -- / Ge 11.8 | bal Venus 0-4-6 | fit |  |
| HTJAH-II.h12_03 | 1948-11-25T19:28 | balance | 153.8 / 153.8 (0.0) | -- / Ge 3.3 | bal Sun 2-9-12 | fit |  |
| HTJAH-II.h12_04 | 1901-06-06T00:00 | balance | 283.9 / 270.9 (13.0) | -- / Aq 21.9 | bal Moon 7-0-27 | **MISFIT** |  |
| HTJAH-II.h12_05 | 1934-02-15T09:15 | balance | 319.6 / 319.6 (0.0) | -- / Pi 17.4 | bal Rahu 0-5-28 | fit |  |
| HTJAH-II.h12_06 | 1928-01-05T17:26 | balance | 59.4 / 59.3 (0.0) | -- / Ge 12.2 | bal Mars 3-9-27 | fit |  |
| HTJAH-II.h12_08 | 1887-08-07T13:21 | balance | 332.8 / 332.8 (0.0) | -- / Sc 12.7 | bal Jupiter 0-8-5 | fit |  |
| HTJAH-II.h12_09 | 1869-10-02T07:45 | balance | 120.2 / 119.7 (0.5) | -- / Li 13.6 | bal Ketu 6-10-28 | fit |  |
| HTJAH-II.h12_10 | 1883-05-28T21:25 | balance | 304.5 / 304.4 (0.0) | -- / Sg 27.0 | bal Mars 1-1-26 | fit |  |
| HTJAH-II.h12_11 | 1889-11-14T23:03 | balance | 109.3 / 109.3 (0.0) | -- / Cn 24.4 | bal Mercury 13-7-6 | fit |  |
| HTJAH-II.h12_12 | 1910-05-19T08:29 | balance | 160.7 / 160.4 (0.3) | -- / Ge 11.5 | bal Moon 9-5-16 | fit |  |
| HTJAH-II.h12_13 | 1883-03-24T18:00 | balance | 165.3 / 171.2 (5.9) | -- / Vi 10.9 | bal Moon 6-0-0 | fit |  |
| HTJAH-II.h12_14 | 1608-12-09T06:30 | balance | 282.3 / 262.4 (19.9) | -- / Sc 13.3 | bal Moon 8-3-9 | **MISFIT** |  |
| HTJAH-II.h12_15 | 1947-08-01T22:10 | sign | -- / Cp 12.7 | -- / Pi 12.9 |  | fit |  |
| HTJAH-II.h12_16 | 1951-08-02T13:35 | balance | 100.7 / 100.7 (0.0) | -- / Sc 4.8 | bal Saturn 8-5-14 | fit |  |
| HTJAH-II.h12_17 | 1917-11-13T08:30 | balance | 189.8 / 189.7 (0.1) | -- / Sc 28.3 | bal Rahu 13-9-7 | fit |  |
| HTJAH-II.h12_18 | 1892-10-16T07:12 | balance | 130.0 / 130.4 (0.4) | -- / Li 20.9 | bal Ketu 1-9-0 | fit |  |
| HTJAH-I.h4_06 | 1912-08-08T19:35 | balance | 55.0 / 55.1 (0.0) | -- / Aq 9.7 | bal Mars 6-1-6 | fit |  |
| HTJAH-II.h9_01 | 1883-03-24T06:00 | balance | 165.3 / 165.3 (0.0) | -- / Pi 10.6 | bal Moon 6-0-0 | fit |  |
| HTJAH-II.h9_03 | 1877-04-23T22:25 | balance | 144.4 / 144.3 (0.0) | -- / Sc 15.6 | bal Venus 3-5-12 | fit |  |
| HTJAH-II.h9_04 | 1950-10-06T14:18 | balance | 106.3 / 104.2 (2.1) | -- / Cp 6.9 | bal Saturn 0-7-0 | fit |  |
| HTJAH-II.h9_05 | 1947-05-02T19:20 | balance | 168.6 / 168.5 (0.1) | -- / Sc 1.8 | bal Moon 3-6-23 | fit |  |
| HTJAH-II.h9_06 | 1951-10-29T12:48 | balance | 176.7 / 176.7 (0.1) | -- / Cp 19.7 | bal Mars 5-3-0 | fit |  |
| HTJAH-II.h9_07 | 1949-08-01T12:42 | balance | 220.9 / 193.9 (27.0) | -- / Li 13.5 | bal Saturn 8-3-3 | anomaly | balance misprint: prose "Moon occupies Lagna" (Libra); cast agrees |
| HTJAH-II.h9_08 | 1938-01-31T00:23 | balance | 279.8 / 279.9 (0.1) | -- / Li 18.8 | bal Sun 0-1-0 | fit |  |
| HTJAH-II.h9_09 | 1912-08-08T19:35 | balance | 55.0 / 55.1 (0.0) | -- / Aq 3.1 | bal Mars 6-1-6 | fit |  |
| HTJAH-II.h9_10 | 1949-10-24T15:33 | balance | 224.4 / 224.4 (0.0) | -- / Aq 27.2 | bal Saturn 3-3-18 | fit |  |
| HTJAH-II.h9_11 | 1925-05-12T07:30 | balance | 257.5 / 257.5 (0.0) | -- / Ta 25.0 | bal Venus 13-9-9 | fit |  |
| HTJAH-II.h9_12 | 1958-08-04T06:40 | balance | 339.2 / 339.1 (0.1) | -- / Cn 26.2 | bal Saturn 10-7-25 | fit |  |
| HTJAH-II.h9_13 | 1954-12-12T07:30 | balance | 86.3 / 85.9 (0.4) | -- / Sg 12.6 | bal Jupiter 8-5-23 | fit |  |
| HTJAH-II.h9_14 | 1925-05-12T07:30 | balance | 257.5 / 257.5 (0.0) | -- / Ta 25.0 | bal Venus 13-9-9 | fit |  |
| HTJAH-II.h9_15 | 1889-11-14T23:03 | balance | 109.3 / 109.3 (0.0) | -- / Cn 24.4 | bal Mercury 13-7-6 | fit |  |
| HTJAH-II.h9_17 | 1942-08-03T07:23 | balance | 8.4 / 8.4 (0.0) | -- / Le 5.9 | bal Ketu 2-7-0 | fit |  |
| HTJAH-II.h9_18 | 1912-08-08T19:35 | balance | 55.0 / 55.1 (0.0) | -- / Aq 9.7 | bal Mars 6-1-6 | fit |  |
| HTJAH-I.h6_01 | 1919-01-28T15:58 | sign | -- / Sg 3.2 | -- / Ge 28.9 |  | fit |  |
| HTJAH-I.h6_02 | 1921-09-03T03:10 | balance | 155.1 / 149.1 (5.9) | -- / Cn 0.7 | bal Sun 2-2-16 | fit |  |
| HTJAH-I.h6_03 | 1914-07-26T17:24 | sign | -- / Le 25.1 | -- / Sg 14.0 |  | fit |  |
| HTJAH-I.h6_04 | 1912-06-15T05:23 | balance | 58.4 / 58.5 (0.1) | -- / Ge 8.4 | bal Mars 4-3-29 | fit |  |
| HTJAH-I.h6_05 | 1893-10-07T08:35 | sign | -- / Le 20.5 | -- / Sc 0.5 |  | fit |  |
| HTJAH-I.h6_06 | 1911-09-09T23:18 | balance | 337.9 / 337.9 (0.0) | -- / Ge 2.9 | bal Saturn 12-5-27 | fit |  |
| HTJAH-I.h6_07 | 1916-05-19T06:10 | sign | -- / Sc 26.4 | -- / Ta 18.2 |  | fit |  |
| HTJAH-I.h6_08 | 1895-05-05T04:00 | sign | -- / Vi 0.2 | -- / Pi 24.2 |  | fit |  |
| HTJAH-I.h6_09 | 1879-08-23T12:10 | sign | -- / Li 21.2 | -- / Sc 10.2 |  | fit |  |
| HTJAH-I.h6_11 | 1902-07-19T03:45 | balance | 264.8 / 254.4 (10.4) | -- / Ge 9.4 | bal Venus 2-9-27 | **MISFIT** |  |
| HTJAH-I.h6_12 | 1908-03-16T10:56 | sign | -- / Le 13.0 | -- / Ta 17.5 |  | fit | Chart 121 prints no balance; prose (lords of Chandra Lagna and 6th, Sun+Saturn, conjoined in the 8th from Leo Moon) agrees with cast |
| HTJAH-I.h6_13 | 1856-07-23T06:24 | balance | 349.3 / 349.2 (0.1) | -- / Cn 20.2 | bal Mercury 13-8-14 | fit |  |
| NH.chart_25 | 1809-08-06T23:45 | degree | 53.8 / 65.3 (11.6) | Ta 25.0 / Ta 27.5 | Su 0.5; Ju 0.3; Sa 0.3; Ra 0.3 | **MISFIT** |  |
| NH.chart_26 | 1818-05-15T02:00 | degree | 24.1 / 142.9 (118.8) | Aq 2.9 / Aq 23.0 | Su 9.4; Ju 0.3; Sa 0.7; Ra 0.5 | **MISFIT** |  |
| NH.chart_28 | 1836-02-18T06:23 | degree | 323.2 / 323.5 (0.2) | Aq 4.9 / Aq 4.6 | Su 0.0; Ju 0.0; Sa 0.0; Ra 180.0 | anomaly | printed Rahu/Ketu swapped (214/34 vs 34/214); all else 0.0-1.0 deg: print error, not birth data |
| NH.chart_32 | 1858-03-11T21:00 | degree | 283.8 / 283.7 (0.0) | Cn 2.8 / Li 12.9 | Su 0.0; Ju 0.0; Sa 0.0; Ra 0.0 | anomaly | printed Lagna 92 50 is a dropped "1" (192 50); prose "lord of Lagna Venus is exalted" = Libra; cast agrees |
| NH.chart_33 | 1858-11-30T16:25 | degree | 170.0 / 170.5 (0.5) | Ta 2.0 / Ta 6.0 | Su 0.5; Ju 0.6; Sa 0.6 | fit |  |
| NH.chart_34 | 1859-02-02T08:30 | degree | 285.1 / 285.1 (0.0) | Aq 7.1 / Aq 15.4 | Su 0.0; Ju 0.0; Sa 0.0; Ra 0.1 | fit | Lagna 8.3 deg off, same sign |
| NH.chart_35 | 1861-05-07T02:51 | degree | 352.0 / 352.0 (0.0) | Pi 6.1 / Pi 6.1 | Su 0.0; Ju 0.0; Sa 0.4; Ra 0.0 | fit |  |
| NH.chart_36 | 1863-01-12T18:33 | degree | 168.9 / 175.5 (6.6) | Sg 27.5 / Cn 15.1 | Su 0.5; Ju 0.0; Sa 0.0; Ra 0.0 | **MISFIT** |  |
| NH.chart_37 | 1863-03-12T02:03 | degree | 220.5 / 228.5 (8.0) | Sg 18.7 / Sg 18.4 | Su 0.8; Ju 1.1; Sa 0.0; Ra 0.1 | anomaly | printed Moon 220 30 vs balance-implied 228.5 = cast: OCR/print digit |
| NH.chart_39 | 1864-06-29T03:55 | degree | 16.3 / 16.4 (0.0) | Ta 26.7 / Ta 26.6 | Su 0.0; Ju 0.0; Sa 0.0; Ra 0.0 | fit |  |
| NH.chart_42 | 1870-11-05T06:49 | degree | 345.8 / 346.0 (0.2) | Sc 0.2 / Sc 0.3 | Su 0.0; Ju 0.5; Sa 0.0; Ra 0.1 | fit |  |
| NH.chart_43 | 1872-08-15T05:17 | degree | 247.0 / 247.1 (0.1) | Cn 26.7 / Cn 26.5 | Su 0.0; Ju 0.0; Sa 0.1; Ra 0.0 | fit |  |
| NH.chart_45 | 1879-03-14T11:30 | degree | 233.8 / 233.8 (0.0) | Ge 21.8 / Ge 20.9 | Su 0.0; Ju 0.0; Sa 10.0; Ra 0.0 | anomaly | printed Saturn 333 30 vs cast 343.5, every other body 0.0: print digit |
| NH.chart_47 | 1882-01-30T20:00 | degree | 75.1 / 75.1 (0.0) | Le 23.5 / Le 23.5 | Su 0.0; Ju 0.0; Sa 0.0; Ra 0.0 | fit |  |
| NH.chart_51 | 1884-05-08T16:26 | degree | 194.4 / 194.6 (0.1) | Vi 28.2 / Vi 28.2 | Su 0.0; Ju 0.0; Sa 0.0; Ra 0.0 | fit |  |
| NH.chart_53 | 1884-12-03T08:45 | degree | 55.5 / 55.4 (0.0) | Sg 20.2 / Sg 20.1 | Su 0.2; Ju 0.0; Sa 0.0; Ra 0.0 | fit |  |
| NH.chart_54 | 1885-10-06T01:36 | degree | 140.2 / 140.2 (0.0) | Cn 22.1 / Cn 22.0 | Su 0.0; Ju 0.0; Sa 0.0; Ra 0.0 | fit |  |
| NH.chart_55 | 1886-04-06T18:36 | degree | 19.2 / 19.2 (0.0) | Li 1.8 / Li 1.9 | Su 0.0; Ju 0.0; Sa 0.0; Ra 0.0 | fit |  |
| NH.chart_57 | 1887-09-08T04:16 | degree | 24.2 / 24.2 (0.0) | Cn 29.0 / Cn 29.7 | Su 0.0; Ju 0.0; Sa 0.0; Ra 0.0 | fit |  |
| NH.chart_61 | 1892-12-04T04:09 | degree | 53.0 / 53.0 (0.0) | Li 14.6 / Li 14.5 | Su 0.0; Ju 0.0; Sa 0.0; Ra 0.1 | fit |  |
| NH.chart_62 | 1893-04-07T09:31 | degree | 241.2 / 241.2 (0.0) | Ge 0.8 / Ta 27.8 | Su 0.0; Ju 0.0; Sa 0.0; Ra 0.0 | **MISFIT** |  |
| NH.chart_63 | 1894-02-25T04:30 | degree | 196.4 / 196.9 (0.5) | Cp 14.1 / Cp 12.4 | Su 0.0; Ju 0.0; Sa 0.0; Ra 0.0 | fit |  |
| NH.chart_65 | 1897-09-20T06:21 | degree | 76.5 / 76.6 (0.1) | Vi 16.0 / Vi 13.5 | Su 0.0; Ju 0.1; Sa 0.0; Ra 0.0 | fit |  |
| NH.chart_67 | 1896-01-30T04:30 | degree | 116.0 / 103.4 (12.6) |  | Su 1.0; Ju 0.1; Sa 0.0; Ra 0.8 | **MISFIT** |  |
| NH.chart_69 | 1897-05-12T10:19 | degree | 149.8 / 149.8 (0.0) | Cn 5.8 / Cn 5.8 | Su 0.0; Ju 0.0; Sa 0.0; Ra 0.0 | anomaly | printed Ketu 19 12 for 109 12: OCR |
| NH.chart_71 | 1906-02-19T04:34 | degree | 254.5 / 254.4 (0.1) | Cp 4.9 / Cp 1.4 | Su 0.1; Ju 0.0; Sa 0.0; Ra 0.0 | fit | Lagna 3.6 deg off, same sign |
| NH.chart_75 | 1920-02-11T22:18 | degree | 210.3 / 210.3 (0.0) | Li 0.6 / Li 1.6 | Su 0.0; Ju 0.1; Sa 0.0; Ra 0.0 | fit |  |
| HTJAH-II.x224 | 1901-03-22T01:29 | balance | 357.9 / 357.8 (0.0) | -- / Sg 3.3 | bal Mercury 2-8-26 | fit |  |
| HTJAH-II.x231 | 1919-07-18T18:17 | balance | 338.5 / 338.5 (0.0) | -- / Sg 25.9 | bal Saturn 11-6-24 | fit |  |
| HTJAH-I.x13 | 1935-11-02T05:20 | balance | 262.6 / 262.5 (0.0) | -- / Li 8.2 | bal Venus 6-1-24 | fit |  |
| HTJAH-I.x65 | 1914-11-16T16:54 | sign | -- / Li 15.6 | -- / Ar 29.3 |  | fit |  |
| HTJAH-I.x67 | 1900-02-19T10:24 | sign | -- / Vi 29.5 | -- / Ar 21.4 |  | fit |  |
| HTJAH-I.x68 | 1896-10-13T07:56 | sign | -- / Sg 23.2 | -- / Li 29.7 |  | fit |  |
| HTJAH-I.x69 | 1909-02-10T11:33 | sign | -- / Vi 23.2 | -- / Ar 21.9 |  | fit |  |
| HTJAH-I.x71 | 1886-07-05T22:32 | sign | -- / Le 14.9 | -- / Aq 28.0 |  | fit |  |
| HTJAH-I.x72 | 1910-04-10T20:38 | sign | -- / Ar 9.2 | -- / Sc 0.9 |  | fit |  |
| HTJAH-I.x73 | 1891-01-05T12:30 | sign | -- / Li 15.5 | -- / Ar 6.9 |  | fit |  |
| HTJAH-I.x75 | 1895-07-17T11:42 | sign | -- / Ar 28.2 | -- / Vi 29.4 |  | fit |  |
| HTJAH-I.x79 | 1749-08-28T12:04 | balance | 323.0 / 323.0 (0.0) | -- / Li 29.5 | bal Jupiter 12-4-24 | fit |  |
| HTJAH-I.x80 | 1856-09-07T16:00 | sign | -- / Sc 22.1 | -- / Cp 19.6 |  | fit |  |
| HTJAH-I.x93 | 1903-06-03T19:00 | sign | -- / Vi 3.6 | -- / Sg 0.7 |  | fit |  |
| HTJAH-II.x226 | 1914-05-26T19:28 | balance | 60.2 / 60.1 (0.1) | -- / Sc 27.1 | bal Mars 3-4-15 | fit |  |