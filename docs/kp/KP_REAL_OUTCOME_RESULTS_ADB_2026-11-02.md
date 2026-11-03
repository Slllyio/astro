# KP real-outcome test on Astro-Databank: results (2026-11-02)

Registered in `KP_REAL_OUTCOME_PREREG_ADDENDUM_ADB_2026-11-02.md` (commit 6f73687, pushed before
any number below existed). Engine commit 6f73687. Numbers: `kp_adb_timing_2026-11-02.json`,
`kp_adb_traits_2026-11-02.json`. Lock digests: timing `a5eaaa39...`, traits `426f3561...`.

## Answer

**Every registered test is a null.** The KP timing windows did not catch real marriage dates more
often than another person's windows at the same age, and none of Reader 2's sign rules was more
common among the people they describe. One speech test had too few cases to judge.

## Data

Astro-Databank tiers A and B (Rodden AA or A), 39,708 records. 35,455 passed the Ascendant gate
(Astro-Databank's own published Ascendant within 1.5 degrees of the cast one); 2,482 failed it and
1,766 had no published Ascendant. Tier C (the C1/C2 holdouts) was not read.

## Part A: timing

| Test | Sample | Events | Hits in own windows | Shuffled mean | Lift (shuffled 95th pct) | p | Verdict |
|---|---|---|---|---|---|---|---|
| **marriage, R25 (primary)** | tier A | 92 | 33 | 34.4 | 0.96 (1.16) | 0.72 | **BOUNDED_NULL** |
| marriage, R17 | tier A | 92 | 49 | 48.8 | 1.00 (1.13) | 0.53 | BOUNDED_NULL |
| service, R25 | tier A | 12 | 5 | 5.7 | 0.87 | 0.77 | UNDERPOWERED |
| marriage, R25 | A + B | 206 | 71 | 77.2 | 0.92 (1.12) | 0.89 | BOUNDED_NULL |
| marriage, R17 | A + B | 206 | 108 | 110.5 | 0.98 (1.09) | 0.69 | BOUNDED_NULL |

Children could not be run: the copy has no day-dated births of children. With 92 events, a lift
above about 1.16 would have shown as a SIGNAL; the observed 0.96 rules that out on this sample.

## Part B: Reader 2's sign rules against Astro-Databank's tags (primary sample A + B)

| Test | Rule | Cases firing | Controls firing | Risk ratio (95% CI) | p | Verdict |
|---|---|---|---|---|---|---|
| T1 no children | barren signs lessen children | 18/337 (5.3%) | 282/4,758 (5.9%) | 0.90 (0.57-1.43) | 0.71 | BOUNDED_NULL |
| T1 (secondary) | fruitful 5th or 11th promises children (predicted lower) | 51.6% | 50.3% | 1.03 (0.92-1.14) | 0.70 | BOUNDED_NULL |
| T2 married late/never | barren 1st and 5th: not married in time | 14/251 (5.6%) | 249/3,424 (7.3%) | 0.77 (0.46-1.29) | 0.87 | BOUNDED_NULL |
| T3 voice / public speaker | voice sign on the 2nd cusp | 110/416 (26.4%) | 8,941/35,039 (25.5%) | 1.04 (0.88-1.22) | 0.35 | BOUNDED_NULL |
| T3 (secondary) | voice sign on the 2nd with Venus or Mercury there | 3.1% | 3.5% | 0.88 (0.52-1.51) | 0.71 | BOUNDED_NULL |
| T4 stutter | any of the three speech rules | 1/20 | 4.5% | 1.12 (0.17-7.6) | 0.60 | UNDERPOWERED |

Tier A alone (secondary) gives the same picture: every p above 0.39. In T1 and T2 the rule fired
slightly *less* often among the people it describes. Diagnostics: the "no children" and "married
late" cases were born earlier (median 1922-25 vs 1934-42) and slightly further north (mean
latitude 44 vs 40-41 degrees); neither difference is large enough to hide an effect of the size
the rules imply.

## What it means

- On the most accurate public birth data there is, KP's marriage timing (R25 and R17) did no better
  than chance, and Reader 2's general sign rules did not match the traits they name.
- This is one sample, and Astro-Databank's tags are incomplete (a person without a "Kids none" tag
  may still have had no children), which weakens T1-T3 but cannot create the reversed directions
  seen.
- It agrees with the earlier results on the Raman and Parashara engines on the same data. The KP
  engine stays described as a faithful rendering of Krishnamurti's books, not a validated
  predictor. The user's own relatives' test (main registration) is still open and would be a
  separate, independent sample.
