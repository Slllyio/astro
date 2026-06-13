# Stage-2 validation worksheet — H4 (house_04_sukha)

Worked charts from HTJAH-I. All `verdict_review: DRAFT` (inert until you confirm).
Reply with confirmations/corrections (sig + ordinal). `DECODE-MISMATCH` = my cast Lagna
disagrees with the stated Lagna → birth-decode needs a second look before confirming.

| # | Chart | Birth | castLagna/stated | sig / DRAFT | engine | status | conf | cite |
|---|---|---|---|---|---|---|---|---|
| 1 | Chart 64 | 1912-08-08T19:35 tz5.5 13,77.5833 | Aq/Aq | mother / **afflicted** | mixed | OK | 0.6 | HTJAH-I:4404 |
| 2 | Chart 76 | 1856-02-12T12:21 tz5.6 18,84 | Ta/Ta | education / **favourable** | favourable | OK | 0.55 | HTJAH-I:4743 |
| 3 | Chart 77 | 1856-07-26T00:00 tz-0.4178 53.0333,-6.2667 | Ta/Ta | education / **favourable** | favourable | OK | 0.5 | HTJAH-I:4775 |
| 4 | Chart 81 | 1902-11-23T05:16 tz4.8444 23.1,72.6667 | Li/Li | education / **favourable** | favourable | OK | 0.55 | HTJAH-I:4869 |
| 5 | Chart 85 | 1912-08-08T19:35 tz5.5 13,77.5833 | Aq/Aq | vehicles / **favourable** | mixed | OK | 0.55 | HTJAH-I:4975 |

**Extractor notes:** SOURCE & METHOD. Read docs/raman_saab/methodology/house_04_sukha.md "Example-Chart Insights" (charts 64-87) and the _H4 block of app/raman_saab/doctrine/significations.py (valid fine sig keys: mother, happiness, education, vehicles, property, home_comforts). The methodology doc prints DATES and (via the stated 4th-house sign) Lagnas, but it does NOT print birth TIMES or PLACES for these charts. Per "do not invent data," I only emitted charts whose place (lat/lon) is faithfully sourced from the book elsewhere in the repo: (a) the existing golden fixture tests/fixtures/raman_goldens.jsonl, or (b) a sibling methodology doc that reprints the SAME nativity with coords. That yields the 5 high-confidence charts above.

PLACE PROVENANCE for the 5 emitted charts:
- Chart 64 & Chart 85 (both 8-8-1912, Aquarius Lagna): same nativity as fixture HTJAH-I.chart_10 / HTJAH-II.chart_33 -> 1912-08-08T19:35 IST (7:35 pm), Bangalore 13.0N/77.5833E, tz 5.5. Chart 64's "Saturn+Moon in 4th, Venus(4th lord) afflicted" and Chart 85's "Lagna-lord Saturn in 4th; 4th lord Venus in 7th" both confirm Aquarius Lagna(11). EVENING birth (7:35 pm) -> 19:35.
- Chart 76 (12-2-1856): same nativity as fixture HTJAH-I.chart_52 and house_08_ayur Chart 61 ("12-2-1856, 12:21 pm LMT, 18N 84E"). Doc 4th=Leo -> Lagna Taurus(2). NOON birth 12:21 pm -> 12:21. tz LMT = 84/15 = 5.6.
- Chart 77 (26-7-1856, Dublin): house_08_ayur Chart 60 reprints "26-7-1856, ~midnight, 53N2 6W16". Doc 4th=Leo -> Lagna Taurus(2). Place is WESTERN (6W16) -> lon negative -0.4178 tz (LMT=lon/15). Time "~midnight" coded 00:00 (ambiguous; could be 23:xx of the 26th). lat 53N2=53.0333, lon 6W16=-6.2667.
- Chart 81 (23-11-1902): house_08_ayur Chart 63 and house_07_kalatra Chart 31 both reprint "23-11-1902, 5:16 am LMT, 23N6 72E40" (Ahmedabad). Doc 4th=Capricorn -> Lagna Libra(7); Saturn (4th lord = Yoga-Karaka) in 4th in own Capricorn confirms. EARLY-MORNING 5:16 am -> 05:16. tz LMT = 72.6667/15 = 4.8444.

CITATION LINES are the HTJAH-I line where each chart's analysis block opens (doc-listed ranges: Chart 64 4404-4463; Chart 76 4743-4773; Chart 77 4775-4795; Chart 81 4869-4885; Chart 85 4975-4978).

SIGNIFICATION/VERDICT routing:
- Chart 64 -> mother / afflicted (Matru-Karaka definitely afflicted, early death of mother).
- Charts 76, 77, 81 -> education / favourable (Education chapter; all three pillars well disposed; high learning, music/art critic, professor of Power-Engineering respectively).
- Chart 85 -> vehicles / favourable. Note: Chart 85's verdict grants BOTH a car (Venus Bhukti) AND a house (Mars Bhukti); I routed to "vehicles" because the car/Venus is led first and is the cleaner single match, but a human may prefer to split or re-key to "property". Either is defensible.

SKIPPED CHARTS (date + derivable Lagna present, but NO place printed anywhere in repo -> cannot become Track-B goldens; listed here so a human can supply externally-verified coords later). Format: Chart | date | doc 4th-sign -> derived Lagna | sig | draft verdict | HTJAH-I cite-start:
- Chart 65 | 16-11-1914 | Cancer -> Aries(1) | mother | afflicted ("mother lost very early"; death Rahu Dasa Venus Bhukti) | 4465
- Chart 66 | 25/26-8-1892 | Virgo -> Gemini(3) | mother | afflicted (longevity combos poor; death Rahu Dasa Jupiter Bhukti; lived to native's 13th yr via Moon-in-own-star) | 4488
- Chart 67 | 19-2-1900 | Cancer -> Aries(1) | mother | afflicted (karaka & lord very weak, poor longevity; death Jupiter Bhukti Rahu Dasa) | 4522
- Chart 68 | 13-10-1896 | Capricorn -> Libra(7) | mother | mixed (4th moderately strong, Matru-Karaka feebly strong, house considerably afflicted) | 4543
- Chart 69 | 10-2-1909 | Cancer -> Aries(1) | mother | afflicted (mother died at age 9, Rahu Dasa Rahu Bhukti; DOC HAZARD: the 16th-yr Moon-Saturn line at 4572 belongs to the preceding chart, NOT chart 69) | 4562
- Chart 70 | 25-9-1898 | Cancer -> Aries(1) | mother | afflicted (mother died native's 18th yr, Moon Dasa Sun Bhukti) | 4588
- Chart 71 | 5-7-1886 | Taurus -> Aquarius(11) | mother | mixed (mother lived to native's 36th yr on house+lord strength, but death Mars Dasa Saturn Bhukti; karaka considerably afflicted) | 4604
- Chart 72 | 10-4-1910 | Aquarius -> Scorpio(8) | mother | afflicted (mother died native aged 3, Venus Dasa Venus Bhukti) | 4632
- Chart 73 | 5-1-1891 | Cancer -> Aries(1) | mother | mixed/afflicted (house not much afflicted, lord/karaka moderately blemished; lost mother Saturn Dasa Venus Bhukti) | 4646
- Chart 74 | 21-7-1900 | Gemini -> Pisces(12) | mother | mixed (all three feebly blemished; mother died 1946 native aged 46 -> long-ish life, late loss) | 4660
- Chart 75 | 17-7-1895 | Sagittarius -> Virgo(6) | mother | favourable (4th quite strong; retained mother till age 52) | 4680
- Chart 78 | 30-11-1858 | Leo -> Taurus(2) | education | favourable (all three fortified; acknowledged distinction in Physics, extending to biology) | 4797
- Chart 79 | 28-8-1749 | Capricorn -> Libra(7) | education | favourable ("one of the greatest poets of Europe of the 18th century"; likely Goethe, Frankfurt -- but NO coords printed). OCR CAVEAT noted in doc: conclusion line 4837 misprints "Chart No 16"; the physical chart is 79. cite-start 4816
- Chart 80 | 7-9-1856 | Aries -> Capricorn(10) | education | mixed (Vidya-Karaka afflicted -> very ordinary school education, but strong house+lord gave knowledge of men/matters & high office) | 4845
- Chart 82 | 16-3-1908 | Leo -> Taurus(2) | education | mixed (only Vidya-Karaka strong -> school knowledge poor, English almost nil, but unique grasp of political/social/international problems via self-study) | 4887
- Chart 83 | 12-3-1863 | no 4th-sign printed (4th lord Jupiter in 11th; from Moon Saturn in 11th) -> Lagna indeterminable from doc | vehicles/property | favourable ("possessed many luxurious conveyances and mansions throughout life") | 4957
- Chart 84 | 30-7-1863 | no 4th-sign printed; "Mars (Griha-Karaka) is Lagnadhipati" -> Lagna Aries(1) or Scorpio(8); appears in house_11_labha as Chart 219 "automobile manufacturer" (likely Henry Ford, Michigan USA, Western) but NO coords | property/vehicles | favourable ("possession of innumerable houses and vehicles") | 4964
- Chart 86 | (NO DATE printed; "data line not separately printed; follows 85") | 4th=Virgo -> Lagna Gemini(3) | vehicles | afflicted (NEGATIVE example: "owned a car for a time but lost it along with a fine job"; useful regression fixture) | 4980
- Chart 87 | 28-8-1909 | Capricorn -> Libra(7) | property | afflicted ("a Police Jamedar on ~Rs.60/month -- none of the 4th-house benefits conferred"; intensely malefic house, Vahana-Karaka neecha, Griha-Karaka weak) | 4995

AMBIGUITIES / OCR ITEMS:
- Chart 77 time "~midnight" is the one materially ambiguous time among the 5 emitted (0:00 vs ~23:xx) -> confidence 0.50.
- Chart 85 sig is vehicles-vs-property contestable (verdict grants both car and house).
- Chart 64 vs 66 both have Saturn+Moon in the 4th but differ in outcome via the constellation (nakshatra-lord) rule -- doc notes Moon-in-own-star spared the mother in 66.
- Charts 64 & 85 share one nativity (8-8-1912) but judge DIFFERENT significations (mother vs vehicles) -- both kept as they are distinct golden claims on the same chart.
- 18 charts skipped for missing lat/lon (the doc prints no places). All have a derivable Lagna and a clear draft verdict above; a human with the book's birth tables (or external identification of the famous natives: Chart 79 Goethe, Chart 77 G.B. Shaw Dublin already coded, Chart 84 Henry Ford) can promote them to full Track-B goldens by supplying coords.
