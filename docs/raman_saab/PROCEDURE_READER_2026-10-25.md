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
