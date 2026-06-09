# Robustness battery & split-half replication (K=300)

## A. Robustness — permutation under confound/label-noise filters

Each row re-runs the full chart-shuffle permutation on the restricted slice. Signal is robust if `z` stays ≳2 and `p` ≲0.05 throughout. `one_per_person` keeps one RANDOM event per native (seed 0 shown; see stability table below).

| filter | events | prime | real grad | null mean | z | p |
|---|---:|---:|---:|---:|---:|---:|
| none (baseline) | 12832 | 5053 | +0.2149 | +0.0060 | 4.09 | 0.0033 |
| one_per_person | 2733 | 1087 | +0.2115 | -0.0188 | 2.13 | 0.0233 |
| concordant | 11984 | 4693 | +0.2078 | +0.0057 | 3.91 | 0.0033 |
| hard_only | 12277 | 4773 | +0.2139 | +0.0051 | 4.00 | 0.0033 |
| strict (all 3) | 2604 | 1039 | +0.2464 | -0.0195 | 2.38 | 0.0100 |

### A′. Independence check — one random event per person, 6 seeds

The strictest confound test: with only one event per native, within-person clustering cannot inflate the evidence.

| seed | events | prime | real grad | z | p |
|---|---:|---:|---:|---:|---:|
| 0.0 | 2733.0 | 1087.0 | +0.2115 | 2.13 | 0.0233 |
| 1.0 | 2731.0 | 1045.0 | +0.2649 | 2.63 | 0.0100 |
| 2.0 | 2759.0 | 1074.0 | +0.2169 | 2.19 | 0.0266 |
| 3.0 | 2760.0 | 1046.0 | +0.2889 | 2.89 | 0.0066 |
| 4.0 | 2743.0 | 1067.0 | +0.3390 | 3.35 | 0.0033 |
| 5.0 | 2721.0 | 1011.0 | +0.1321 | 1.11 | 0.1429 |

_Median z = 2.41; significant (p≤0.05) in 5/6 draws. Gradient magnitude (~+0.2) is preserved at ¼ the sample, so the full-sample significance is **not** an artifact of repeated events per person._

## B. Split-half replication (disjoint person halves)

Internal replication: each half has its own events and its own donor chart pool. A real effect reproduces in *both* halves, same sign.

| seed | half | people | prime | real grad | z | p |
|---|---|---:|---:|---:|---:|---:|
| 0 | A | 1889 | 2492 | +0.2605 | 3.93 | 0.0033 |
| 0 | B | 1890 | 2561 | +0.1782 | 2.65 | 0.0100 |
| 1 | A | 1889 | 2634 | +0.2392 | 3.69 | 0.0033 |
| 1 | B | 1890 | 2419 | +0.1862 | 2.71 | 0.0066 |
| 2 | A | 1889 | 2446 | +0.2113 | 2.92 | 0.0033 |
| 2 | B | 1890 | 2607 | +0.2161 | 3.42 | 0.0033 |

## Verdict

- **Confound filters** (label noise, soft classes): ✅ hold — z stays ≥2 (effect is not a label-coding artifact).
- **Independence** (one random event/native): ✅ holds — median z = 2.41, significant in 5/6 draws at ¼ sample; the evidence is not inflated by within-person event clustering.
- **Replication** (disjoint halves): ✅ holds — gradient positive in every half, z≥2 in most halves.

**Bottom line**: the prime-stage chart→event dignity signal is real, modest (~+0.2 strong−weak), robust to label noise and event clustering, and reproduces across disjoint subsamples. The one caveat that remains is the headline one: this is **internal** replication on a single corpus. A truly independent second dataset is the gold standard and is not yet available in this repo.
