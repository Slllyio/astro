# Stage-2 validation worksheet — H7 (Kalatra / marriage), batch 1

**12 worked charts from B.V. Raman, *How to Judge a Horoscope* Vol. II, Chapter XI.**
Drafted as `HTJAH-II.chart_01` … `chart_12` in `tests/fixtures/raman_goldens.jsonl`
(all `verdict_review: "DRAFT"` → currently **inert** to the ratchet).

**Your job:** for each row, confirm or correct **(a)** the signification and **(b)** the
ordinal verdict. Reply with the corrections (e.g. "chart_06 → spouse / mixed; chart_05 OK").
On your call I flip the row to `CONFIRMED`, which adds it to Track-B (ratchet denominator
37 → up to 49) and makes the H7 combination layer measurable.

- **Birth-decode is validated**: every chart's cast Lagna matches Raman's stated Lagna /
  7th-sign (0 mismatches — Track A green). Chart 8 corrected to a 7:35 **PM** birth.
- **"Engine now"** is the engine's *current* verdict for that signification — shown only so you
  can see where the engine already agrees vs where this chart will become a refinement target.
  It is NOT the claim; the **DRAFT** column is my reading of Raman's prose, which is what you validate.
- Ordinals: `favourable` | `mixed` | `afflicted` | `insufficient-evidence`.
- H7 significations available: `marital_happiness`, `spouse` (count/character), `virility`,
  `coverture` (widowhood/partner-death), `wealth_through_marriage`, `partnership`.

| Chart | Birth (DOB / time / place) | Lagna | Raman's verdict (prose) | DRAFT: sig / ordinal | Engine now | Conf | Cite | Your call |
|---|---|---|---|---|---|---|---|---|
| 01 | 16-08-1937 08:31 IST, 13N00 77E35 | Virgo | stable marriage, deep attachment (Jupiter↔Venus aspect holds it) | marital_happiness / **favourable** | favourable ✓ | 0.6 | II:999 | |
| 02 | 03-08-1942 07:23 IST, 13N00 77E35 | Leo | happy married life, good-looking conventional wife | marital_happiness / **favourable** | favourable ✓ | 0.6 | II:1109 | |
| 03 | 04-12-1953 05:17 IST, 13N00 77E35 | Scorpio | chaste, devoted wife (blemishless Venus karaka-cum-7th-lord) | marital_happiness / **favourable** | afflicted | 0.6 | II:1166 | |
| 04 | 20-11-1950 03:00 IST, 18N55 72E54 | Virgo | complete deprivation of marital happiness; separated 1974 | marital_happiness / **afflicted** | mixed | 0.6 | II:1244 | |
| 05 | 08-10-1935 11:30 IST, 13N10 76E10 | Sagittarius | violent clashes, miserable but not broken (Jupiter saves it) | marital_happiness / **mixed** | favourable | 0.55 | II:1297 | |
| 06 | 24-03-1883 06:00 LMT, 13N00 77E35 | Pisces | two marriages, both unhappy (Venus + 7th lord dual signs) | marital_happiness / **afflicted** | favourable | 0.5 | II:1343 | |
| 07 | 12-02-1856 12:21 LMT, 18N00 84E00 | Taurus | second marriage after death of first; both fairly happy | marital_happiness / **mixed** | mixed ✓ | 0.5 | II:1388 | |
| 08 | 08-08-1912 19:35 IST, 13N00 77E30 | Aquarius | one happy stable marriage; devoted chaste religious wife | marital_happiness / **favourable** | afflicted | 0.6 | II:1436 | |
| 09 | 03-11-1940 07:00 EST, 35N44 81W21 | Libra | stiff opposition; married 1961, separated 1964, never happy | marital_happiness / **afflicted** | mixed | 0.6 | II:1510 | |
| 10 | 13-03-1948 10:30 IST, 11N06 79E42 | Taurus | deserted by husband three days after marriage | marital_happiness / **afflicted** | afflicted ✓ | 0.6 | II:1539 | |
| 11 | 26-12-1953 23:47 IST, 10N23 78E55 | Virgo | happy marriage; strength of 7th lord and karaka | marital_happiness / **favourable** | favourable ✓ | 0.6 | II:1580 | |
| 12 | 21-05-1940 07:50 IST, 13N00 77E30 | Gemini | happy married life, devoted wife (benefic preponderance) | marital_happiness / **favourable** | favourable ✓ | 0.6 | II:1625 | |

**Open questions for you:**
1. **Chart 06** — verdict emphasises "TWO marriages" (a `spouse`-count matter) *and* "both unhappy"
   (a `marital_happiness` matter). I drafted it as `marital_happiness / afflicted`. Prefer
   `spouse / mixed` instead, or keep as drafted?
2. **Chart 07** — "second marriage after death of first; both fairly happy" — drafted `mixed`.
   Is the loss-of-first-partner a `coverture` claim you'd want pinned separately?
3. Any chart where you'd read the ordinal differently — note it and I'll correct + re-confirm.

**Next batches (on your go-ahead):** H7 charts 13–25 (loss/widowhood — `coverture`), then the
other new houses (H4/H5/H6/H8/H9/H10/H11/H12 worked charts). Same DRAFT → worksheet → confirm flow.
