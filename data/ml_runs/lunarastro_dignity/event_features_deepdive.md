# Native-kundli event features — deep dive (prime stage)

Benefit share by each native-chart feature of the running lords, net of the stage base rate. `lift` > 1 ⇒ more beneficial than average; ✶ marks raw p < 0.05 vs base.

## Headlines

- **57 feature-levels tested** → Bonferroni family-wise bar p < 0.0009.
- **None** survive the family-wise bar.
- **Natural benefic/malefic is flat**: a running natural benefic and a running natural malefic carry essentially the same benefit rate — the naisargika dichotomy does *not*, by itself, separate good from bad events here. `pair_both_benefic` is likewise null.
- The composite *dignity* gradient (separate module, +0.2 pair) is stronger than any single feature below, because it pools dignity across both lords and contrasts the tails.

## md_natural

| level | n | benefit % | lift | p |
|---|---:|---:|---:|---:|
| benefic | 2683 | 75 | **1.00** | 1 |
| malefic | 2370 | 75 | **1.00** | 0.981 |

## ad_natural

| level | n | benefit % | lift | p |
|---|---:|---:|---:|---:|
| benefic | 2649 | 75 | **1.01** | 0.607 |
| malefic | 2404 | 74 | **0.99** | 0.573 |

## md_functional

| level | n | benefit % | lift | p |
|---|---:|---:|---:|---:|
| benefic | 596 | 78 | **1.04** | 0.0894 |
| unknown | 1144 | 77 | **1.03** | 0.0659 |
| malefic | 1149 | 75 | **1.01** | 0.684 |
| neutral | 2164 | 72 | **0.97** ✶ | 0.01 |

## ad_functional

| level | n | benefit % | lift | p |
|---|---:|---:|---:|---:|
| malefic | 1282 | 76 | **1.02** | 0.222 |
| unknown | 981 | 75 | **1.00** | 0.971 |
| benefic | 658 | 75 | **1.00** | 0.928 |
| neutral | 2132 | 74 | **0.99** | 0.383 |

## md_dignity

| level | n | benefit % | lift | p |
|---|---:|---:|---:|---:|
| exalted | 268 | 78 | **1.05** | 0.205 |
| own | 515 | 76 | **1.02** | 0.389 |
| neutral | 1261 | 75 | **1.00** | 0.871 |
| friendly | 1638 | 75 | **1.00** | 0.977 |
| inimical | 1076 | 74 | **0.99** | 0.505 |
| debilitated | 295 | 70 | **0.94** | 0.0938 |

## md_house_kind

| level | n | benefit % | lift | p |
|---|---:|---:|---:|---:|
| lagna | 455 | 76 | **1.02** | 0.589 |
| maraka | 401 | 76 | **1.01** | 0.687 |
| dusthana | 1295 | 76 | **1.01** | 0.522 |
| kendra | 1209 | 75 | **1.00** | 0.974 |
| upachaya | 814 | 74 | **0.99** | 0.545 |
| trikona | 879 | 73 | **0.98** | 0.295 |

## ad_house_kind

| level | n | benefit % | lift | p |
|---|---:|---:|---:|---:|
| lagna | 416 | 81 | **1.08** ✶ | 0.00326 |
| upachaya | 902 | 75 | **1.01** | 0.759 |
| dusthana | 1186 | 75 | **1.01** | 0.763 |
| maraka | 453 | 74 | **0.99** | 0.829 |
| trikona | 812 | 74 | **0.99** | 0.657 |
| kendra | 1284 | 73 | **0.97** | 0.0719 |

## md_is_yogakaraka

| level | n | benefit % | lift | p |
|---|---:|---:|---:|---:|
| True | 260 | 76 | **1.02** | 0.568 |
| False | 4793 | 75 | **1.00** | 0.881 |

## md_is_dusthana

| level | n | benefit % | lift | p |
|---|---:|---:|---:|---:|
| True | 1295 | 76 | **1.01** | 0.522 |
| False | 3758 | 74 | **1.00** | 0.693 |

## md_is_trikona

| level | n | benefit % | lift | p |
|---|---:|---:|---:|---:|
| False | 3719 | 75 | **1.00** | 0.792 |
| True | 1334 | 74 | **0.99** | 0.636 |

## md_is_kendra

| level | n | benefit % | lift | p |
|---|---:|---:|---:|---:|
| True | 1664 | 75 | **1.00** | 0.735 |
| False | 3389 | 75 | **1.00** | 0.797 |

## pair_naisargika

| level | n | benefit % | lift | p |
|---|---:|---:|---:|---:|
| friend | 1481 | 76 | **1.02** | 0.169 |
| neutral | 1081 | 75 | **1.00** | 0.916 |
| unknown | 898 | 75 | **1.00** | 0.908 |
| own | 619 | 74 | **0.99** | 0.644 |
| enemy | 974 | 73 | **0.98** | 0.253 |

## pair_both_benefic

| level | n | benefit % | lift | p |
|---|---:|---:|---:|---:|
| False | 3642 | 75 | **1.00** | 0.985 |
| True | 1411 | 75 | **1.00** | 0.976 |

## pair_both_malefic

| level | n | benefit % | lift | p |
|---|---:|---:|---:|---:|
| False | 3921 | 75 | **1.00** | 0.686 |
| True | 1132 | 74 | **0.99** | 0.431 |

## pair_same_sign

| level | n | benefit % | lift | p |
|---|---:|---:|---:|---:|
| False | 3918 | 75 | **1.00** | 0.927 |
| True | 1135 | 74 | **1.00** | 0.838 |

## chart_kendra_net

| level | n | benefit % | lift | p |
|---|---:|---:|---:|---:|
| 2 | 455 | 81 | **1.08** ✶ | 0.00351 |
| 1 | 1046 | 75 | **1.00** | 1 |
| -1 | 1108 | 75 | **1.00** | 1 |
| 0 | 1292 | 74 | **1.00** | 0.798 |
| -3 | 310 | 73 | **0.98** | 0.514 |
| 3 | 104 | 73 | **0.98** | 0.653 |
| -2 | 640 | 73 | **0.98** | 0.295 |
| -4 | 88 | 68 | **0.91** | 0.176 |
