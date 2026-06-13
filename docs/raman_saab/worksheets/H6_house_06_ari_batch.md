# Stage-2 validation worksheet — H6 (house_06_ari)

Worked charts from HTJAH-I. All `verdict_review: DRAFT` (inert until you confirm).
Reply with confirmations/corrections (sig + ordinal). `DECODE-MISMATCH` = my cast Lagna
disagrees with the stated Lagna → birth-decode needs a second look before confirming.

| # | Chart | Birth | castLagna/stated | sig / DRAFT | engine | status | conf | cite |
|---|---|---|---|---|---|---|---|---|

**Extractor notes:** NO House-6 worked chart qualifies as a Track-B golden under the stated rule ("only include charts with a place (lat/lon) at minimum; do NOT invent data"). The source `docs/raman_saab/methodology/house_06_ari.md` "Example-Chart Insights" section (charts 109-123) prints ONLY a birth DATE in parentheses for each chart — no birth time, no place, and no coordinates anywhere. A regex over the entire file for any positional/time token (N/S/E/W degrees, Lat./Long., LMT, GMT, hrs, a.m./p.m.) returned ZERO matches. The richer place/time data that some CONFIRMED goldens carry (e.g. the Lincoln/Gandhi/JFK/Hitler H8 charts, chart_29's "Long. 0 5h. E.") was sourced from the book's full printed birth lines, which are NOT in the local corpus: `data/knowledge_library/sources/how_to_judge_a_horoscope_raman/` contains only `chapter_001_full-text-unsplit.md` (Chapter I / Lagna), not Chapter IX (the 6th house). So there is no available source from which to read lat/lon for these charts without fabricating it.

Cross-chapter check: chart 121 (16-3-1908) shares a date with house_04 Chart 82 and house_10 Chart 169, and chart 122 (23-7-1856) shares a date with house_10 Chart 130 — but the chart descriptions DIFFER (different people/charts on the same calendar day), so the shared dates do NOT let me identify a birthplace, and none of those entries print a place either. Two charts are clearly anonymized/withheld and would be skipped even if places existed: Chart 117 ("data withheld; Gemini Lagna") has no date at all, and Chart 123 ("ex-bank cashier") has no date.

To save a future pass, here is the per-chart routing I worked out (all DRAFT, all need lat/lon from the actual book before they can become goldens). Signification keys are the VALID _H6 fine keys (enemies_disease, accidents, debts, enemies, disease_chronic):
- Chart 109 (28-1-1919): typhoid/pneumonia/TB -> disease_chronic, afflicted. Lagna not stated. cite ~L463.
- Chart 110 (2/3-9-1921): TB -> death -> disease_chronic, afflicted. Lagna not stated. cite ~L470.
- Chart 111 (26-7-1914): TB + 5x imprisonment -> disease_chronic (or enemies), afflicted. Lagna not stated. cite ~L472.
- Chart 112 (15-6-1912): myopia -> disease_chronic, afflicted. Lagna not stated. cite ~L480.
- Chart 113 (7-10-1893): serious smallpox -> disease_chronic, afflicted. Lagna not stated. cite ~L484.
- Chart 114 (9-9-1911): multiple diseases (liver/spleen/spermatorrhoea/hydrocele) -> disease_chronic, afflicted. Mercury=Lagna lord (Gemini/Virgo). cite ~L489.
- Chart 115 (19-5-1916): typhoid + bronchitis -> disease_chronic, afflicted. Venus=Lagna AND 6th lord (so Lagna Taurus[2] or Libra[7], ambiguous). cite ~L497.
- Chart 116 (4/5-5-1895): fatal appendicitis -> disease_chronic, afflicted. 6th lord Sun => Lagna Pisces (1st=Pisces makes 6th=Leo, Sun-ruled) -> stated_lagna_sign=12 plausible but NOT explicitly stated; treat as 0 until confirmed. cite ~L501.
- Chart 117 (NO date; Gemini Lagna stated): leprosy -> disease_chronic, afflicted. stated_lagna_sign=3 (Gemini). SKIP (no date, no place). cite ~L509.
- Chart 118 (23-8-1879, lady): paralysis of limbs/arms -> disease_chronic, afflicted. Lagna not stated. cite ~L517.
- Chart 119 (12-4-1912): facial paralysis -> disease_chronic, afflicted. Mars=6th lord in Lagna (Aries[1] or Scorpio[8], ambiguous). cite ~L524.
- Chart 120 (10/19-7-1902): huge debts (Rahu Dasha) -> debts, afflicted. Mercury=Lagna lord with Mars+Sun in Lagna (Gemini[3] or Virgo[6], ambiguous). cite ~L529.
- Chart 121 (16-3-1908): political conviction/imprisonment -> enemies, afflicted. Venus=Lagna&6th lord (Taurus[2] or Libra[7]). cite ~L535.
- Chart 122 (23-7-1856): long imprisonment for sedition (Bandhana Yoga) -> enemies, afflicted. Moon=Lagna lord => Lagna Cancer, stated_lagna_sign=4. cite ~L540.
- Chart 123 (NO date; ex-bank cashier): "eternally involved in debts" -> debts, afflicted. Mercury=Lagna lord (Gemini[3] or Virgo[6]). SKIP (no date, no place). cite ~L545.

Verdict-ordinal note: every House-6 worked chart in this chapter illustrates a misfortune (disease, debt, or imprisonment/enemies) that actually fructified, so the DRAFT ordinal is "afflicted" for all of them — there are no favourable/mixed examples in this dusthana chapter, which is itself a useful regression signal but makes ordinal-discrimination confidence low.

Recommendation: to extract these as real Track-B goldens, obtain the Chapter IX full text of HTJAH-I (with the printed planetary tables and any birth lines) into data/knowledge_library/sources/how_to_judge_a_horoscope_raman/, OR follow the precedent of the existing snapshots and create birth=null, Track-B/3-only worked_example goldens (the schema explicitly supports birth=null for from-table charts) — in which case lat/lon are not required and ~13 of these (109-116, 118-122) become extractable from the planetary descriptions. The current task's lat/lon-minimum constraint cannot be met from the available material without fabrication.
