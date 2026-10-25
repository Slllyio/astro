# The procedure reader (2026-10-25)

`app/raman_saab/procedure/` reads a horoscope house by house the way Raman reads his worked charts
in *How to Judge a Horoscope*. It follows the synthesis in
`docs/raman_saab/RAMAN_READING_PROCEDURE_2026-10-25.md` (the "spec" below), and the per-chapter
extractions in `docs/raman_saab/research/raman-procedure-*.md`.

**It is a separate instrument.** It does not feed `house_template`, the scored judge, the golden
ratchet, the doctrine snapshot or the report sections, and none of them import it. A test
(`tests/raman_saab/test_procedure_reader.py::TestIndependence`) checks that no module outside the
package imports it.

Entry points:

```
from app.raman_saab.procedure import read_procedure
reading = read_procedure(chart)        # ProcedureReading; reading.to_dict() is JSON-safe
python -m app.raman_saab.procedure --date 1990-07-15 --time 12:00 --lat 12.97 --lon 77.59 --tz 5.5
```

## 1. What it does

**Stage 0** (spec 2), once per chart:
- the functional nature of every planet for the Lagna (`functional_nature`), and the yogakarakas;
- the stronger of the Lagna and the Moon. This is the engine's measure (`chart_overview`), shown
  but not used to re-weight anything, because Raman prints no re-weighting rule;
- the span of life (`ayurdaya.longevity`);
- the Mahadashas that can run within the span, with those beginning after it marked.

**Each matter** (spec 3) goes House, then Lord, then Karaka, then the view from the Moon, then the
Conclusion. A house can hold several matters: the 4th holds mother, education, vehicles, property
and happiness.

Inside each planet factor the sub-order is the one in spec 3.3:
1. position;
2. dignity (with neechabhanga, and with an exalted benefic aspecting, as cancellations, 4.6);
3. associates;
4. aspecters, with functional nature over natural nature (4.3);
5. hemming;
6. the star lord, read only for longevity and for the father (4.8);
7. the Navamsa.

The Navamsa moves a grade by one step at most and never reverses it (4.7). Every item is listed
with its weight and an `HTJAH:<line>` citation. Grades use Raman's ordinal words: afflicted,
blemished, moderate, fairly strong, strong.

**The conclusion** (spec 4.1, 4.2) counts two of three, with the tie-breaks for each matter:
- brothers and children: the lord outweighs the house;
- children: three outcomes;
- mother: the Moon decides whether she is lost early, and the house and lord decide how long she
  lives;
- education: two separate answers;
- father: the karaka decides;
- longevity: the Lagna lord against the 8th lord, then Saturn;
- gains: wealth yogas outrank the 11th house;
- elder brothers: the Lagna view and the Moon view must agree.

One benefic sets a floor (4.4), and a blemish shows as a quality or a shorter duration (4.5). The
sentence follows his formula, "[house]; [lord]; [karaka]. Hence ...". Every sentence passes
`_FORBIDDEN_RE`, which was not widened.

**Timing** (spec 5) uses the five selection rules:
1. **Good events** of a house use the house's influence set (`vimshottari.timer_roles`). For gains
   it also adds the 2nd house and the wealth-yoga planets.
2. **Rise and fall in rank** uses the planets that form the raja yoga, with the relation between
   the Mahadasha and Bhukti lords.
3. **A relative's death** uses marakas counted from that relative's house, from its lord and from
   its karaka. For the father it adds the 9th from the Moon. A planet in its own star is not
   proposed as the Mahadasha lord.
4. **Marriage** uses Raman's seven slots in his order, with Mahadashas outside the marriageable
   age struck out.
5. **The native's death** uses the span window, then marakas from the Lagna, the Moon, the Navamsa
   Lagna and the Navamsa Moon, plus Mahadashas delegated to the nodes.

Rules that apply to every kind of event:
- dasas outside the span are struck out;
- both lords must qualify;
- the bhukti lord carries the event;
- a node qualifies through its sign lord, its star lord, a conjoined planet, or Sanivad Rahu /
  Kujavad Ketu;
- transit comes last, as a note.

The engine's fructification tier is shown as a separately labelled field, because Raman never uses
those words in a chart.

## 2. Conventions (where Raman gives no mechanical rule)

Each one is named in the code as `basis="convention"`, and all of them are printed in every
reading.
- Each testimony counts as one step, and the net count gives the grade on the five-step scale.
- For a house, the Navamsa compares benefics against malefics in the same house counted from the
  Navamsa Lagna.
- A factor votes good at "fairly strong" or above and bad at "blemished" or below.
- Where Raman uses no karaka (the 9th for fortune, the 10th), the view from the Moon takes the
  third vote.
- The star lord counts good in its own star or a benefic's star. It counts bad in a node's star or
  in the star of the 6th, 8th or 12th lord.
- The marriageable window is ages 16 to 33.
- The wealth-yoga planets include the 2nd, 5th, 9th and 11th lords when they are associated with
  one another.
- When Saturn is weak it moves the longevity band down, mirroring the upward move Raman prints.
- The 6th is read with the forward template, although Raman reads it backwards from the disease
  he already knows.
- Death rules carry a maraka "strength" (the summed weights of the Mahadasha and Bhukti lords). It
  is reported, never used as a cutoff.

## 3. Pre-registration (written before any comparison was run)

**Verdicts.**
- **Rows.** Every CONFIRMED Track-B worked-example row of `tests/fixtures/raman_goldens.jsonl`,
  taken through the harness's own `_TRACK_B_RATCHET`, `confirmed_verdicts` and `build_chart`.
  Charts with birth data are cast with Raman's ayanamsa; the others come from their printed
  positions. That is 389 rows.
- **Matter.** `matters.SIGNIFICATION_MATTER` maps each row's signification to a matter. An
  unlisted key falls back to the house's first matter. The map was written before the run and will
  not be edited after it.
- **Score.** The reader's `conclusion.verdict` (favourable / mixed / afflicted) is scored with the
  harness's `_ordinal_distance`. The reader never abstains, so every row gets a graded verdict.
- **Reported:** exact, within one step, real errors (distance 2), and the confusion matrix. All of
  these are shown next to the engine's 269 / 354 / 35.
- **Prediction:** exact 210-250 of 389, within one 320-350, real errors 40-70. In other words, the
  reader will do *worse* than the tuned judge. It is a literal procedure with one-step-per-testimony
  conventions and no fitted thresholds.
- I expect the H6 rows to be weakest. The reader grades the 6th forward, where malefics are bad,
  while Raman reads the 6th from the known outcome.

**Timing.** The dated events below are printed by Raman (period lords quoted from his text). The
golden id gives the chart; birth data comes from the golden record.

| Kind | Events (golden id: Mahadasha / Bhukti) |
|---|---|
| native death | II.chart_35 Rahu/Sun; II.chart_73 Saturn/Mercury; II.chart_74 Jupiter/Sun; II.chart_75 Jupiter/Saturn; II.chart_78 Rahu/Moon; I.h6_02 Rahu/Saturn |
| mother's death | I.h4_01 Mars/Saturn (HTJAH:4404); I.x67 Rahu/Jupiter; I.x69 Rahu/Rahu; I.x71 Mars/Saturn; I.x72 Venus/Venus; I.x73 Saturn/Venus |
| father's death | II.h9_01 Saturn/Ketu (HTJAH:12766); h9_03 Venus/Mercury (13006); h9_04 Saturn/Jupiter (13031); h9_05 Mars/Mercury (13060); h9_06 Rahu/Saturn (13091); h9_07 Jupiter/Rahu (13117); h9_08 Jupiter/Mercury (13170); h9_09 Jupiter/Ketu (13194); h9_12 Mercury/Rahu (13312); h9_13 Saturn/Rahu (13329) |
| spouse's death | II.h7_09 Rahu/Venus; h7_11 Rahu/Ketu; h7_12 Saturn/Saturn; h7_13 Mars/Venus |
| good event | I.chart_38 Saturn/Venus (H2 wealth); I.chart_40 Ketu/Mercury (H2); I.h4_05 Jupiter/Venus (vehicle); I.h4_06 Jupiter/Mars (house); I.h5_13 Ketu MD (child); II.h11_14 Venus/Rahu; h11_15 Jupiter/Jupiter; h11_16 Jupiter/Sun; h11_17 Saturn/Rahu; h11_18 Mercury MD (gains); II.h9_15 Ketu/Rahu; h9_17 Sun/Jupiter; h9_18 Jupiter/Jupiter (9th house) |
| rank | II.h10_01 Rahu bhukti (Mahadasha not printed); II.h10_05 Rahu/Mars |
| bad event of a house (read with the house's influence set) | I.chart_39 Jupiter/Rahu (H2 eyes); I.chart_44 Ketu/Venus (H2 loss); I.chart_12 Jupiter MD (H1 health); I.h6_11 Rahu MD; I.h6_12 Sun and Moon MDs; I.h6_13 Sun and Moon MDs; II.h12_09 Rahu MD (prison) |
| marriage | none: no golden chart with birth data prints the marriage period, so the marriage rule is not measured |

Each event is measured with the timing rule of its kind on its matter.
- **Rule hit:** the printed Mahadasha/Bhukti pair, or the Mahadasha alone where only that is
  printed, is among the rule's candidate periods.
- **Base rate:** for each rule, the share of all bhukti periods in the rule's window that are
  candidates. A rule that proposes most periods hits by default.
- **Lift:** the hit rate divided by the mean base rate.
- **Death rules only:** the rank of the printed pair among the candidates by maraka strength,
  given as a percentile (0 means top-ranked).
- **Prediction:** for relative deaths, hits of 60-90% at base rates of 50-80%, so a lift of at
  most 1.3. For native deaths, at most half the printed pairs among the candidates, because the
  window is the computed span and that span is often wrong. For good events, hits of 50-80% at
  base rates of 40-70%. Strength rank no better than the median.
- **One run.** After it, only plain bug fixes are allowed, and each is listed below with its
  effect.

The run uses `tools/raman_saab/procedure_reader_measure.py`.

## 4. Results (written after the single run)

### 4.1 Verdicts

| | exact | within one | real errors (distance 2) |
|---|---|---|---|
| **reader, pre-registered run** | **147 / 389 (37.8%)** | **290 (74.6%)** | **99** |
| reader after bug fix 1 (below) | 147 / 389 (37.8%) | 292 (75.1%) | 97 |
| engine (judge), for reference | 269 / 389 (69.2%) | 354 (91.0%) | 35 |

**The prediction failed in the bad direction.** I expected 210-250 exact, 320-350 within one and
40-70 real errors. The run is below all three ranges. No `SIGNIFICATION_MATTER` key went unmapped.

The confusion matrix (Raman → reader, pre-registered run):

| Raman said | reader favourable | reader mixed | reader afflicted |
|---|---|---|---|
| favourable | 77 | 61 | 45 |
| mixed | 16 | 12 | 10 |
| afflicted | 54 | 56 | 58 |

Raman's favourable rows come out favourable 42% of the time and afflicted 25% of the time. His
afflicted rows come out afflicted 35% of the time and favourable 32% of the time. So the literal
procedure, run forward with one step per testimony, is close to indifferent to which way Raman
concluded.

Real errors by house: H1 2, H2 10, H3 11 (of 18), H4 7, H5 12, H6 9 (of 18), H7 11, H8 6, H9 9,
H10 14, H11 6, H12 2. H6 was the predicted weak spot, and it was: every H6 real error reads
favourable where Raman reads affliction. H3 and H10 were as bad, which I did not predict.

This is a measurement of the procedure *as encoded with these conventions*, not of Raman. The
spec's own caution (section 1 of the spec) is that his order of reasoning is retrodictive: he knows
the outcome and picks which testimonies to name. A forward reader that counts every testimony
equally does not reproduce that selection, and this run quantifies how much it matters. The
tuned judge, which weights evidence through the doctrine-cited pillars, stays far better.
**Nothing in the reader was adjusted toward the goldens after the run.**

### 4.2 Timing (Raman's printed dated events)

| Rule | events | printed period among candidates | printed period inside the window | mean base rate | lift | strength rank (0 = top) |
|---|---|---|---|---|---|---|
| native's death | 6 | 1 | 1 | 0.48 | 0.35 | 0.50 |
| relative's death (mother, father, spouse) | 20 | 20 | 20 | 0.81 | 1.24 | 0.40 |
| good event of a house | 13 | 11 | 12 | 0.66 | 1.29 | - |
| bad event, read with the house's influence set | 9 | 6 | 9 | 0.51 | 1.32 | - |
| rise and fall in rank | 2 | 0 | 2 | 0.20 | 0 | - |

- **Relative deaths hit 20 of 20, but the rule proposes 81% of all bhuktis in the window.** In five
  charts it proposes every bhukti, so the hits are mostly coverage. The maraka strength puts the
  printed pair at a mean percentile of 0.40, only slightly better than the chance value of 0.5.
  The best cases are h9_13 (top), h7_13 (0.06), h7_11 (0.07), h9_01 (0.10) and x69 (0.11). The
  worst are x72 (0.90), h7_12 (0.87) and h9_09 (0.76).
- **Native deaths: 1 of 6.** Five of the six printed deaths fall outside the window, because the
  rule searches only the computed span ± its band. JFK died at 46 against a computed span of 73,
  and Chart 35 died at 62 against 81. Raman's caveat (HTJAH:818-820) names exactly this. The one
  hit (Gandhi, Jupiter/Sun) is at the median strength.
- **Good events: 11 of 13**, at a base rate of 0.66.
  - h11_18 missed because the computed span (34 years) ends before the Mercury Mahadasha.
  - h9_18 (Jupiter/Jupiter, pilgrimage) missed because Jupiter is not in the 9th's influence set
    in Chart 113. Raman reads it through Jupiter's aspect from the 10th lord.
- **Bad events** (the same influence set): 6 of 9. Chart 12's Jupiter Mahadasha and Chart h6_12's
  Sun and Moon Mahadashas are missed.
- **Rank: 0 of 2.** In both charts the Rahu bhukti does not qualify, because Rahu's channels do not
  reach a raja-yoga planet.
- **Marriage** was not measured: no golden chart with birth data prints a marriage period.

**Lift is about 1.2-1.3 wherever the rule hits.** That matches the pre-registered "at most 1.3":
the selection rules, applied literally, leave most periods open. This agrees with the engine's
measured real-outcome null (CLAUDE.md, "Measured truth").

### 4.3 Bug fixes made after the run (the only changes)

1. **A planet could occupy no house at all.** `grade_house` applied the Bhava rule in one direction
   only (HTJAH:1945-1946). A planet in the house's sign but another Bhava was removed from the
   house. A planet in the neighbouring sign but this Bhava was never added. Such a planet therefore
   counted in neither house.
   - The fix counts it in its Bhava, still subject to the Bhava-sandhi rule.
   - Effect: exact 147 → 147, within one 290 → 292, real errors 99 → 97. Timing is unchanged,
     because timing uses the engine's `timer_roles`.

No other change was made after the numbers were seen.

### 4.4 Engine guards

- `tools.raman_saab.doctrine_snapshot --check` still reports IDENTICAL across 346 charts.
- The golden ratchet is unchanged (269 / 354 / 35); `test_goldens.py` passes.
- `tests/fixtures/golden_accuracy_baseline.json` was not touched.

## Round 2 (2026-10-25): fixes from the mismatch review

Written **before** any code change. Each of the 97 real-error rows of round 1 (after bug fix 1)
was read against Raman's printed text and given exactly one class:

- **A, reader bug**: the reader computes a fact Raman's text contradicts, or applies a cited rule
  beyond what the citation says.
- **B, missing Raman rule**: Raman's reasoning uses a general rule he states, with a quotable
  citation, that the reader lacks.
- **C, Raman's weighting**: left alone.
- **D, label or casting issue**: recorded only; the goldens are not edited.

A row is put in A or B only when one of the textual defects below is present on one of its three
voting factors *and* points the way Raman concluded. Where a defect is present but points the
other way, or two defects cancel, the row is classed by its main cause (usually C) and the fix will
still change it; such losses are reported, not avoided. **No fix is chart-specific and none was
chosen because a row would flip**: each is justified by the cited passages alone, and each applies
to all 389 rows.

### R2.1 The textual defects found

| id | class | defect | Raman's text |
|---|---|---|---|
| A1 | A | The father rule lets a *good* Sun overrule an afflicted 9th house and lord. Raman's sentence is about afflictions only. | HTJAH:13126-13127, "Afflictions to the pitruKaraka by association, aspect, placement or otherwise are very important in depriving a native of his father". The Sun decides when afflicted; otherwise the plain two-of-three tally (HTJAH:2111-2113) stands. |
| A2 | A | Neechabhanga is taken from the engine's four-clause primitive, which also cancels a debility when the dispositor joins or aspects the planet. Raman never gives that reason. | HTJAH:16178-16181 prints the cancellation as "the lord of this sign or the planet who gets exalted there is in Kendra from the Moon or Lagna" and "neecha (debilitated) in Rashi but gets exalted in Amsa". Every reason he gives in a worked chart is one of these (HTJAH:2037-2038, 8858-8859, 8888-8889, 8966-8967, 9133-9134). The reader gets its own check with these clauses only. Surfaced while checking Chart 90 (h9_06); it touches none of the 97 rows' voting factors. |
| A3 | A | "Inimical sign" uses the engine's compound (panchadha) relation. In every case where the cast sign matches Raman's and the two relations disagree, Raman's word follows the natural relation. | HTJAH:2930-2931 (Chart 48, Jupiter in Libra, "an inimical sign"; compound gives neutral), HTJAH:3811-3812 (Chart 60, Mars in Gemini, "the sign of an enemy"; compound gives neutral), HTJAH:3779 (Chart 59, Venus in Gemini, "a friendly sign"), HTJAH:1947 (Venus in Capricorn, "a friendly sign"). One counter-instance: HTJAH:1898 calls Mars in Gemini "friendly", which neither relation gives. Exaltation, own sign and debility stay positional. |
| A6 | A | Longevity compares the Lagna lord with the 8th lord. For Aries and Libra Lagnas they are one planet, so the comparison is degenerate and always reads "middle". | HTJAH:11415-11416 ("the 8th lord stronger than Lagna lord causing Alpayu") compares two lords. When they are the same planet the comparison does not apply, and the plain two-of-three tally (HTJAH:2111-2113) is used, in which Saturn, the karaka, is one of the three votes. |
| A8 | A | An unoccupied, unaspected house counts 0 (moderate). Raman grades exactly that configuration "fairly strong" or "good". | HTJAH:3669-3670 (Chart 52, "not occupied or aspected by any planets, benefice or malefic. Hence it is fairly strong"), HTJAH:2809-2810 (Chart 43, "not aspected by any planet—good or bad. Hence it is fairly strong"), HTJAH:1801-1802 ("Lagna is occupied by no planet. This is good"). It becomes +1, in the house and in the view from the Moon. No passage grades an empty house weak. |
| B1 | B | A lord in the 8th from its own house is not marked. | HTJAH:3826-3828 (Chart 61, the 3rd lord Mars "posited in a Kendra and own sign but his situation in the 8th from the 3rd and with the ruler of the 6th Moon renders him weak"); NH chart 64 ("lord of the 10th is placed in the 8th from the 10th"). -1 for the house's own lord; own sign does not cancel it (both instances are in own sign). Skipped where the lord already stands in a dusthana from the Lagna, which is counted once. |
| B2 | B | A natural benefic that owns the 6th from the Lagna counts as helping (or as nothing). Raman counts its contact as an affliction. | HTJAH:4405-4406 (Chart 64, "The affliction is heavy because of association with the Moon lord of the sixth"), HTJAH:4472-4473 ("The fourth lord Moon is in the seventh with Mercury lord of the third and sixth and hence blemished"), HTJAH:3827, HTJAH:2218-2220 ("even this aspect is not good because Venus is lord of 6 and 11"). -1 by occupation, association or aspect. Not applied to a planet that also owns the Lagna, the 5th or the 9th (HTJAH:575-578: the 9th lord is "decidedly more benefice"), nor to the house's own lord. Counter-instance: HTJAH:8930-8931 calls Venus as 6th and 11th lord "not very helpful" rather than harmful. |

Considered and **rejected** (C): a combustion cap (HTJAH:10409-10411 says a combust planet "becomes
practically useless", but Raman routinely passes over Mercury's combustion); changing the
yogakaraka weight (HTJAH:8565-8567 and 8748 against Charts 59 and 60); karaka-in-own-bhava for the
7th (HTJAH:9244-9248 says that dictum "is not quite valid"); reading occupancy by Bhava only or by
Rasi only (the text goes both ways: HTJAH:1945 against 2601-2602, 4082-4083 and 8878; recorded as an
open doctrine conflict, the round-1 rule stands); a "with no relief" reading of Chart 90's Sun
(HTJAH:13140), since Roosevelt (NH chart 47) counts conjunction with the Moon as a kendra from it,
so Chart 90 is a Raman inconsistency on that point. A Special Dhana Lagna (HTJAH:3258-3300) is a
stated rule but a separate method outside the house template; it is deferred, not built.

A4 (the mother tie-break when the Moon is good) was drafted and **dropped**: it touches none of the
97 rows and its textual basis (HTJAH:4392-4393) is a weighting call.

### R2.2 Classification of the 97 rows

| row | class | reason | citation |
|---|---|---|---|
| HTJAH-II.chart_33 H8 | C | Raman reads the span arithmetically (Pindayu 86y); the template has no arithmetic. B2 lowers Saturn further (a loss) | HTJAH:11415-11416 |
| HTJAH-II.chart_34 H8 | A | Libra Lagna: Venus is Lagna and 8th lord, so the lord comparison is degenerate (A6); Venus's sign relation (A3) | HTJAH:11415-11416 |
| HTJAH-II.chart_73 H8 | D | Lincoln: the label is the manner of death (assassination), not the span | - |
| HTJAH-I.chart_53 H3 | D | Birth year OCR-garbled ("18*0"); the cast puts Venus in Leo/6th where Raman has it in the 7th with exalted Mercury | - |
| HTJAH-I.chart_54 H3 | C | Raman's weighting of the 3rd; A3 lowers Mars further (a loss) | HTJAH:3690-3692 |
| HTJAH-I.chart_57 H3 | C | Raman counts ear/throat afflictions toward the 3rd; A3 raises the lord (a loss) | HTJAH:3725-3727 |
| HTJAH-I.chart_59 H3 | C | Raman weighs Venus's combustion over its vargottama | HTJAH:3779-3781 |
| HTJAH-I.chart_60 H3 | A | Mars in Gemini is "the sign of an enemy"; the reader reads it neutral (A3) | HTJAH:3811-3812 |
| HTJAH-I.chart_61 H3 | B | 3rd lord Mars in the 8th from the 3rd (B1) and with the 6th lord Moon (B2) | HTJAH:3826-3828 |
| HTJAH-I.chart_38 H2 | C | Occupancy by Rasi vs Bhava, an open doctrine conflict; Raman's weighting | HTJAH:2601-2602 |
| HTJAH-I.chart_41 H2 | C | Raman's weighting of the 2nd | - |
| HTJAH-I.chart_48 H2 | A | Jupiter in Libra is "an inimical sign"; the reader reads it neutral (A3) | HTJAH:2930-2931 |
| HTJAH-I.chart_50 H2 | B | Raman decides wealth by the Special Dhana Lagna, a stated rule outside the template (deferred, not built) | HTJAH:3295-3300 |
| HTJAH-II.chart_11 H7 | A | Empty 7th graded moderate (A8); Venus in Capricorn is a friendly sign (A3) | HTJAH:3669-3670, 1947 |
| HTJAH-I.h4_01 H4 | B | Chart 64: the Moon as 6th lord in the 4th makes the affliction heavy (B2); Venus's sign relation (A3) | HTJAH:4405-4406 |
| HTJAH-I.h5_08 H5 | C | Raman's weighting; A3 raises the lord (a loss) | - |
| HTJAH-I.h5_10 H5 | C | Raman's weighting; A8 raises the house (a loss) | - |
| HTJAH-I.h5_15 H5 | A | Empty 5th graded moderate (A8); lord's sign relation (A3) | HTJAH:3669-3670 |
| HTJAH-I.h5_18 H5 | C | Raman's weighting; A3 raises the lord (a loss) | - |
| HTJAH-II.h7_01 H7 | C | A3 raises and B1 lowers the lord; Raman's weighting decides | - |
| HTJAH-II.h7_10 H7 | C | Raman judges by a yoga (Jara/Bahukalatra type) | - |
| HTJAH-II.h7_14 H7 | B | The 7th lord is touched by Venus as 6th lord (B2) | HTJAH:4472-4473 |
| HTJAH-II.h7_15 H7 | C | Raman judges by a yoga and the maraka | - |
| HTJAH-II.h11_05 H11 | A | Lord and karaka read "inimical" by the compound relation only (A3) | HTJAH:2930-2931 |
| HTJAH-II.h11_06 H11 | C | Elder brothers: Raman's weighting | - |
| HTJAH-II.h11_15 H11 | A | 11th lord read "inimical" by the compound relation only (A3) | HTJAH:2930-2931 |
| HTJAH-II.h11_16 H11 | A | 11th lord read "inimical" by the compound relation only (A3) | HTJAH:2930-2931 |
| HTJAH-II.h9_06 H9 | A | Chart 90: a strong Sun rescues an afflicted 9th house and lord; the rule is about afflictions (A1) | HTJAH:13126-13127 |
| HTJAH-II.h9_12 H9 | A | The good-Sun rescue (A1); 9th lord in the 8th from the 9th (B1) | HTJAH:13126-13127 |
| HTJAH-I.h6_01 H6 | C | Raman reads the 6th in reverse (pre-registered weak spot) | - |
| HTJAH-I.h6_02 H6 | C | Raman reads the 6th in reverse | - |
| HTJAH-I.h6_07 H6 | C | Raman reads the 6th in reverse | - |
| HTJAH-I.h6_09 H6 | C | Raman reads the 6th in reverse | - |
| HTJAH-I.h6_11 H6 | C | Raman reads the 6th in reverse | - |
| HTJAH-I.h6_13 H6 | C | Raman reads the 6th in reverse | - |
| NH.chart_26 H10 | D | Marx: the cast Moon is in Leo; Raman has it in Aries with the Sun and Rahu, in parivartana with Mars | NH:6561-6576 |
| NH.chart_33 H2 | A | 2nd lord read "inimical" by the compound relation only (A3) | HTJAH:2930-2931 |
| NH.chart_34 H12 | B | The Moon as 6th lord touches the 12th, its lord and Saturn (B2) | HTJAH:4405-4406 |
| NH.chart_36 H6 | C | Raman reads the 6th in reverse | - |
| NH.chart_39 H9 | A | The good-Sun rescue of an afflicted house (A1) | HTJAH:13126-13127 |
| NH.chart_39 H8 | D | The label is about maraka timing, not the span | - |
| NH.chart_42 H2 | C | Raman judges wealth by yogas | - |
| NH.chart_42 H4 | D | The prose is about legal brilliance, not the mother | - |
| NH.chart_42 H10 | C | Career judged from yogas and planets in the 10th | - |
| NH.chart_45 H1 | C | Raman's weighting of the Lagna | - |
| NH.chart_45 H7 | C | Raman's weighting of the 7th | - |
| NH.chart_47 H9 | D | The prose is "Saturn, the planet of democracy in the 9th", not the father | - |
| NH.chart_51 H10 | C | Career judged from the 9th/10th raja yoga | - |
| NH.chart_51 H9 | D | The prose is about the 9th/10th exchange raja yoga, not the father | - |
| NH.chart_51 H2 | C | Wealth judged from yogas | - |
| NH.chart_54 H10 | C | Career judged from planets in the 10th; A8 raises the house (a loss) | - |
| NH.chart_54 H4 | D | The prose is about education, not the mother | - |
| NH.chart_55 H7 | C | Raman's weighting of the 7th | - |
| NH.chart_55 H6 | C | Raman reads the 6th in reverse | - |
| NH.chart_57 H7 | A | 7th lord Saturn in a natural enemy's sign read neutral (A3) | HTJAH:3811-3812 |
| NH.chart_62 H11 | C | Gains judged from wealth yogas | - |
| NH.chart_62 H7 | C | Raman's weighting of the 7th | - |
| NH.chart_65 H2 | C | A8 raises the house and A3 lowers the lord; Raman's weighting decides | - |
| NH.chart_69 H1 | C | Raman's weighting; A3 lowers the Sun (a loss) | - |
| NH.chart_69 H10 | C | Career judged from yogas | - |
| NH.chart_71 H3 | A | 3rd lord Jupiter in a natural enemy's sign read neutral (A3) | HTJAH:2930-2931 |
| NH.chart_71 H9 | A | 9th lord read "inimical" by the compound relation only (A3) | HTJAH:2930-2931 |
| NH.chart_71 H5 | C | Children read from Chandra Lagna; A3 lowers Jupiter (a loss) | - |
| NH.chart_18 H5 | C | Raman's weighting; A3 raises lord and karaka (a loss) | - |
| NH.chart_18 H10 | A | Empty 10th graded moderate (A8) | HTJAH:3669-3670 |
| NH.chart_20 H5 | C | Children: Raman's weighting | - |
| NH.chart_23 H10 | C | Career judged from yogas; A3 lowers the lord (a loss) | - |
| NH.chart_24 H10 | A | 10th lord read "inimical" by the compound relation only (A3) | HTJAH:2930-2931 |
| NH.chart_24 H8 | D | Lincoln: the label is the manner of death, not the span | - |
| NH.chart_30 H10 | C | Career: Raman's weighting | - |
| NH.chart_31 H5 | C | Children read from Chandra Lagna | - |
| NH.chart_38 H9 | D | The label has a contested history (two reviewers graded it differently); A1 changes it either way | - |
| NH.chart_40 H5 | C | Children read from Chandra Lagna | - |
| NH.chart_46 H8 | A | Libra Lagna: degenerate lord comparison (A6); Venus's sign relation (A3) | HTJAH:11415-11416 |
| NH.chart_46 H4 | C | Education: Raman's weighting; A8 raises the house (a loss) | - |
| NH.chart_49 H3 | C | Raman's weighting; B2 lowers Venus (a loss) | - |
| NH.chart_52 H7 | A | Venus in a natural enemy's sign read neutral (A3) | HTJAH:3811-3812 |
| NH.chart_56 H10 | A | Empty 10th graded moderate (A8) | HTJAH:3669-3670 |
| NH.chart_59 H3 | A | Mars in a natural enemy's sign read neutral (A3) | HTJAH:3811-3812 |
| NH.chart_59 H5 | A | 5th lord Mars in a natural enemy's sign read neutral (A3) | HTJAH:3811-3812 |
| NH.chart_64 H10 | B | "lord of the 10th is placed in the 8th from the 10th" (B1) | NH chart 64 |
| NH.chart_64 H9 | C | Raman's weighting of the 9th | - |
| NH.chart_66 H10 | C | Career judged from yogas; B2 lowers house and lord (a loss) | - |
| NH.chart_66 H3 | B | 3rd lord Jupiter in the 8th from the 3rd (B1) | HTJAH:3826-3828 |
| NH.chart_74 H5 | C | Children: Raman's weighting | - |
| NH.chart_74 H7 | A | Empty 7th graded moderate (A8) | HTJAH:3669-3670 |
| NH.chart_74 H10 | C | Career judged from yogas | - |
| NH.chart_58 H10 | C | B2 lowers and A3 raises the lord; Raman's weighting decides | - |
| NH.chart_58 H3 | C | Raman's weighting of the 3rd | - |
| NH.chart_16 H2 | C | Wealth judged from yogas | - |
| NH.chart_17 H6 | C | Raman reads the 6th in reverse | - |
| NH.chart_17 H9 | A | The good-Sun rescue (A1) | HTJAH:13126-13127 |
| NH.chart_48 H12 | C | Raman's weighting of the 12th | - |
| NH.chart_48 H5 | C | Children: Raman's weighting | - |
| HTJAH-I.x65 H4 | B | Chart 65: the 4th lord Moon "with Mercury lord of the third and sixth and hence blemished" (B2) | HTJAH:4472-4473 |
| HTJAH-I.x75 H4 | A | The Moon read "inimical" by the compound relation only (A3) | HTJAH:2930-2931 |
| HTJAH-II.x226 H11 | A | Empty 11th graded moderate (A8) | HTJAH:3669-3670 |

**Counts: A 26, B 8 (7 addressed this round; the Special Dhana Lagna row is deferred), C 53, D 10.**

### R2.3 Planned fixes

A1, A2, A3, A6, A8, B1 and B2 as stated in R2.1. All are in `app/raman_saab/procedure/`
(`grading.py`, `conclusion.py`, `citations.py`) with the verbatim citation in the code, and each gets
a test in `tests/raman_saab/test_procedure_reader.py`. The engine, its judge, the golden ratchet and
the report sections are not touched.

### R2.4 Prediction (before the run)

The defects push in both directions across all 389 rows (A3 removes as many "inimical" readings as
it adds; A8 raises houses; B1 and B2 lower lords and houses), so currently-correct rows will also
move. Predicted: **exact 145-160 (point 152), within one 290-305 (point 298), real errors 85-97
(point 91).** Of the 34 A/B rows, I expect about half to stop being real errors and 5-10 other rows to
become real errors.

### R2.5 Results (written after the single round-2 run)

| | exact | within one | real errors (distance 2) |
|---|---|---|---|
| reader, round 1 (after bug fix 1) | 147 / 389 (37.8%) | 292 (75.1%) | 97 |
| **reader, round 2** | **151 / 389 (38.8%)** | **293 (75.3%)** | **96** |
| engine (judge), for reference | 269 / 389 (69.2%) | 354 (91.0%) | 35 |

All three figures fall inside the predicted ranges, but below every point prediction (152 / 298 /
91). The net gain is small because the fixes moved 80 of 389 verdicts and the moves nearly cancel.

- **Real errors removed (18):** HTJAH-II.chart_34 H8, HTJAH-I.chart_61 H3, HTJAH-I.chart_48 H2,
  HTJAH-I.chart_50 H2, HTJAH-II.chart_11 H7, HTJAH-I.h4_01 H4, HTJAH-I.h5_15 H5,
  HTJAH-II.h7_14 H7, HTJAH-II.h9_06 H9 (Chart 90, now exact), HTJAH-II.h9_12 H9,
  NH.chart_34 H12, NH.chart_36 H6, NH.chart_57 H7, NH.chart_18 H10, NH.chart_46 H8,
  NH.chart_59 H3 (now exact), NH.chart_59 H5, HTJAH-I.x65 H4. Seventeen of these are A/B rows
  (half of the 34, as predicted); NH.chart_36 H6 is a C row. HTJAH-I.chart_50 H2 moved although its
  own rule (the Special Dhana Lagna) was deferred, through A3 and B1.
- **Real errors created (17), against the predicted 5-10:** HTJAH-I.chart_45 H2,
  HTJAH-I.chart_51 H2, HTJAH-I.h5_11 H5, HTJAH-II.h11_08 H11, HTJAH-II.h12_04 H12,
  HTJAH-II.h12_18 H12, NH.chart_28 H9, NH.chart_37 H2, NH.chart_54 H7, NH.chart_61 H10,
  NH.chart_65 H5, NH.chart_67 H5, NH.chart_29 H7, NH.chart_38 H2, NH.chart_56 H2,
  NH.chart_56 H4, NH.chart_73 H4. Examples: in h5_11 B2 makes Jupiter, lord of the 3rd and 6th for
  Libra, afflict the 5th lord and the house; in NH.chart_73 H4 A8 makes the 4th from the Moon good,
  which tips a Moon-led mother reading to favourable. These fixes stay, because the text demands
  them; the losses are reported, not tuned away.
- **Exact gains (26):** HTJAH-I.chart_29 H1, HTJAH-II.chart_78 H8, HTJAH-I.chart_62 H3,
  HTJAH-II.h7_02/h7_05/h7_17 H7, HTJAH-II.h12_09/h12_10 H12, HTJAH-II.h9_02 H9, HTJAH-II.h9_06 H9,
  NH.chart_35 H7, NH.chart_53 H10 and H7, NH.chart_55 H1, NH.chart_18 H4, NH.chart_23 H9,
  NH.chart_27 H10, NH.chart_31 H10, NH.chart_38 H10, NH.chart_46 H12, NH.chart_49 H12,
  NH.chart_59 H3, NH.chart_58 H8, NH.chart_68 H5, NH.chart_19 H9, NH.chart_5 H1.
- **Exact losses (22):** HTJAH-I.chart_15 H1, HTJAH-I.chart_40 H2, HTJAH-II.chart_07/chart_08 H7,
  HTJAH-I.h4_05/h4_06 H4, HTJAH-I.h5_11 H5, HTJAH-II.h9_04/h9_08/h9_11 H9, HTJAH-I.h6_06 H6,
  NH.chart_25 H2, NH.chart_33 H10, NH.chart_36 H9, NH.chart_37 H7, NH.chart_47 H1,
  NH.chart_57 H9, NH.chart_67 H9, NH.chart_75 H1, NH.chart_70 H10, NH.chart_19 H10, HTJAH-I.x80 H4.

Real errors by house, round 2: H1 2, H2 12, H3 9, H4 6, H5 13, H6 8, H7 10, H8 4, H9 8, H10 14,
H11 7, H12 3.

**Timing is unchanged** (the timing rules use the engine's `timer_roles`, which no fix touches):

| Rule | events | among candidates | inside window | mean base rate | lift | strength rank |
|---|---|---|---|---|---|---|
| native's death | 6 | 1 | 1 | 0.48 | 0.35 | 0.50 |
| relative's death | 20 | 20 | 20 | 0.81 | 1.24 | 0.40 |
| good event of a house | 13 | 11 | 12 | 0.66 | 1.29 | - |
| bad event, influence set | 9 | 6 | 9 | 0.51 | 1.32 | - |
| rise and fall in rank | 2 | 0 | 2 | 0.20 | 0 | - |

**This is an in-sample figure.** The 389 rows are the same goldens the mismatch review read, and
both hold-outs (the 36-conclusion 3HC set and the 134-conclusion NH/HTJAH set) are already spent.
The 147 → 151 gain cannot be counted as out-of-sample improvement. What it does show is that
seven text-demanded corrections, taken together, barely move the literal procedure: it remains
close to indifferent to which way Raman concluded, and the engine's judge stays far ahead.

### R2.6 D rows worth the user's attention

- **NH.chart_26 H10 (Marx):** the cast Moon is in Leo; Raman's chart has it in Aries with the Sun
  and Rahu, in exchange with Mars (NH:6561-6576). A casting issue that also affects the engine.
- **HTJAH-I.chart_53 H3:** the birth year is OCR-garbled ("18*0"); the cast does not match
  Raman's Venus.
- **Off-topic labels:** NH.chart_42 H4 and NH.chart_54 H4 (scored as the mother; the prose is about
  legal brilliance and education), NH.chart_47 H9 and NH.chart_51 H9 (scored as the father; the
  prose is about Saturn as the planet of democracy and the 9th/10th raja yoga), HTJAH-II.chart_73 H8
  and NH.chart_24 H8 (Lincoln; scored as the span, the prose is the manner of death),
  NH.chart_39 H8 (maraka timing). NH.chart_38 H9 has a contested label history.

### R2.7 Guards

- `tools.raman_saab.doctrine_snapshot --check`: IDENTICAL across 346 charts.
- Golden ratchet unchanged (269 / 354 / 35); `test_goldens.py` passes.
- Every line of the reader's text output for all golden charts (715,246 lines) passes
  `_FORBIDDEN_RE`; the regex was not touched.
- Tests: 11 new in `tests/raman_saab/test_procedure_reader.py` (one class per fix, including the
  Chart 90 karaka direction). `tests/raman_saab`: 7342 passed, 18 skipped, 3 xfailed.
