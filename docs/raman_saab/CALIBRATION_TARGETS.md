# Raman Saab — Stage-3/4 calibration target matrix

Generated from `track_b_scoreboard()`. Ratchet **53/130 (40.8%)**, 77 mismatches across 11 houses (H8=Phase-E).

Each row is a CONFIRMED golden the engine currently misreads. `engine` = current output, `golden` = Raman's verdict (ground truth).

## Per-house accuracy
| House | correct/total | mismatches |
|---|---|---|
| H1 | 7/12 | 5 |
| H2 | 7/13 | 6 |
| H3 | 4/12 | 8 |
| H4 | 3/6 | 3 |
| H5 | 1/12 | 11 |
| H6 | 2/10 | 8 |
| H7 | 6/12 | 6 |
| H9 | 7/16 | 9 |
| H10 | 5/6 | 1 |
| H11 | 7/17 | 10 |
| H12 | 4/14 | 10 |

## Dominant pattern
~50/77 are `engine=mixed` where golden is a committed afflicted/favourable — the clause-2 mixed-bias / missing preponderance (see CONTRA_PILLAR in judges/house_template.py, currently no-op=99).

## Target rows by house
| id | house/sig | engine | golden |
|---|---|---|---|
| HTJAH-I.chart_09 | H1/self | mixed | insufficient-evidence |
| HTJAH-I.chart_15 | H1/self | mixed | favourable |
| HTJAH-I.chart_17 | H1/self | afflicted | favourable |
| HTJAH-I.chart_20 | H1/self | mixed | afflicted |
| HTJAH-I.chart_31 | H1/self | mixed | afflicted |
| HTJAH-I.chart_43 | H2/wealth | mixed | favourable |
| HTJAH-I.chart_44 | H2/wealth | mixed | afflicted |
| HTJAH-I.chart_45 | H2/wealth | mixed | favourable |
| HTJAH-I.chart_46 | H2/wealth | mixed | favourable |
| HTJAH-I.chart_48 | H2/wealth | favourable | mixed |
| HTJAH-I.chart_49 | H2/wealth | mixed | favourable |
| HTJAH-I.chart_53 | H3/siblings | mixed | favourable |
| HTJAH-I.chart_54 | H3/siblings | mixed | favourable |
| HTJAH-I.chart_56 | H3/ear_throat | mixed | afflicted |
| HTJAH-I.chart_58 | H3/siblings | favourable | afflicted |
| HTJAH-I.chart_59 | H3/siblings | mixed | afflicted |
| HTJAH-I.chart_60 | H3/siblings | favourable | afflicted |
| HTJAH-I.chart_61 | H3/siblings | mixed | afflicted |
| HTJAH-I.chart_62 | H3/siblings | favourable | afflicted |
| HTJAH-I.h4_01 | H4/mother | mixed | afflicted |
| HTJAH-I.h4_05 | H4/vehicles | mixed | favourable |
| HTJAH-I.h4_06 | H4/property | mixed | favourable |
| HTJAH-I.h5_01 | H5/children | favourable | afflicted |
| HTJAH-I.h5_02 | H5/children | mixed | afflicted |
| HTJAH-I.h5_04 | H5/children | mixed | afflicted |
| HTJAH-I.h5_05 | H5/children | mixed | afflicted |
| HTJAH-I.h5_07 | H5/children | mixed | afflicted |
| HTJAH-I.h5_08 | H5/children | mixed | afflicted |
| HTJAH-I.h5_09 | H5/children | mixed | afflicted |
| HTJAH-I.h5_10 | H5/children | favourable | afflicted |
| HTJAH-I.h5_11 | H5/children | mixed | afflicted |
| HTJAH-I.h5_12 | H5/children | favourable | afflicted |
| HTJAH-I.h5_16 | H5/children | afflicted | favourable |
| HTJAH-I.h6_03 | H6/enemies_disease | mixed | afflicted |
| HTJAH-I.h6_04 | H6/disease_chronic | favourable | afflicted |
| HTJAH-I.h6_07 | H6/enemies_disease | mixed | afflicted |
| HTJAH-I.h6_08 | H6/enemies_disease | mixed | afflicted |
| HTJAH-I.h6_09 | H6/disease_chronic | mixed | afflicted |
| HTJAH-I.h6_11 | H6/debts | favourable | afflicted |
| HTJAH-I.h6_12 | H6/enemies | mixed | afflicted |
| HTJAH-I.h6_13 | H6/enemies | favourable | afflicted |
| HTJAH-II.chart_03 | H7/marital_happiness | afflicted | favourable |
| HTJAH-II.chart_04 | H7/marital_happiness | mixed | afflicted |
| HTJAH-II.chart_05 | H7/marital_happiness | favourable | afflicted |
| HTJAH-II.chart_06 | H7/marital_happiness | favourable | afflicted |
| HTJAH-II.chart_08 | H7/marital_happiness | afflicted | favourable |
| HTJAH-II.chart_09 | H7/marital_happiness | mixed | afflicted |
| HTJAH-II.h9_02 | H9/father | mixed | afflicted |
| HTJAH-II.h9_07 | H9/father | afflicted | mixed |
| HTJAH-II.h9_08 | H9/father | mixed | favourable |
| HTJAH-II.h9_09 | H9/father | afflicted | mixed |
| HTJAH-II.h9_10 | H9/father | mixed | favourable |
| HTJAH-II.h9_11 | H9/father | mixed | favourable |
| HTJAH-II.h9_13 | H9/father | mixed | afflicted |
| HTJAH-II.h9_14 | H9/fortune | mixed | favourable |
| HTJAH-II.h9_15 | H9/long_journeys | mixed | favourable |
| HTJAH-II.h10_04 | H10/profession_authority | afflicted | mixed |
| HTJAH-II.h11_01 | H11/elder_siblings | favourable | afflicted |
| HTJAH-II.h11_02 | H11/elder_siblings | afflicted | mixed |
| HTJAH-II.h11_05 | H11/elder_siblings | mixed | favourable |
| HTJAH-II.h11_06 | H11/elder_siblings | mixed | favourable |
| HTJAH-II.h11_09 | H11/gains | afflicted | favourable |
| HTJAH-II.h11_12 | H11/gains | afflicted | favourable |
| HTJAH-II.h11_13 | H11/acquisitions | mixed | favourable |
| HTJAH-II.h11_14 | H11/acquisitions | mixed | favourable |
| HTJAH-II.h11_17 | H11/gains | afflicted | mixed |
| HTJAH-II.h11_18 | H11/gains | afflicted | mixed |
| HTJAH-II.h12_01 | H12/moksha | afflicted | mixed |
| HTJAH-II.h12_04 | H12/expenditure | afflicted | mixed |
| HTJAH-II.h12_05 | H12/expenditure | mixed | afflicted |
| HTJAH-II.h12_06 | H12/incarceration | favourable | afflicted |
| HTJAH-II.h12_08 | H12/expenditure | afflicted | mixed |
| HTJAH-II.h12_09 | H12/incarceration | mixed | afflicted |
| HTJAH-II.h12_10 | H12/incarceration | mixed | afflicted |
| HTJAH-II.h12_16 | H12/left_eye | favourable | afflicted |
| HTJAH-II.h12_17 | H12/moksha | mixed | favourable |
| HTJAH-II.h12_18 | H12/moksha | mixed | favourable |
