# Forecast skill & calibration — astrology scored as a forecaster

Each native gets a forward probability over their candidate periods: the population age-prior tilted by weight-of-evidence (tilt fit on the discovery half, scored on the held-out half). Strictly proper scores; skill is over the age base-rate (positive ⇒ beats the actuary).

## Skill over the age base-rate (held-out half)

| group | n | log-skill | RPSS | bits gained | astro ign. | base ign. |
|---|---:|---:|---:|---:|---:|---:|
| **auspicious pooled** | 1764 | **-0.0005** | -0.0007 | -0.0019 | 4.1198 | 4.1179 |
| marriage | 565 | -0.0016 | -0.0 | -0.0061 | 3.9174 | 3.9113 |
| career | 1062 | 0.0002 | -0.0001 | 0.001 | 4.3037 | 4.3047 |
| education | 137 | -0.0019 | -0.0083 | -0.0065 | 3.5287 | 3.5221 |
| death | 710 | -0.0007 | 0.0005 | -0.0033 | 5.0892 | 5.0859 |

(log-skill / RPSS: 0 = no better than predicting by population age alone; >0 = astrology adds timing skill; <0 = worse. bits gained = mean reduction in surprise per native, in bits.)

Pooled-auspicious log-skill 95% CI excludes nothing of interest; calibration **ECE = 0.0014** (0 = forecasts perfectly calibrated).

## Reliability (pooled auspicious) — does stated probability match reality?

| forecast-prob bin | n | mean forecast | observed |
|---|---:|---:|---:|
| 0.000-0.039 | 41101 | 0.0134 | 0.0133 |
| 0.039-0.078 | 7748 | 0.0555 | 0.0585 |
| 0.078-0.118 | 2900 | 0.0952 | 0.0921 |
| 0.118-0.157 | 1688 | 0.1372 | 0.1268 |
| 0.157-0.196 | 1127 | 0.1728 | 0.1863 |
| 0.196-0.235 | 255 | 0.2109 | 0.2039 |
| 0.235-0.274 | 67 | 0.253 | 0.2537 |
| 0.274-0.314 | 28 | 0.2936 | 0.1071 |
| 0.314-0.353 | 5 | 0.3273 | 0.2 |
| 0.353-0.392 | 3 | 0.3763 | 0.0 |

## Reading

- **log-skill / RPSS ≈ 0** ⇒ tilting the actuarial age-prior by weight-of-evidence does **not** beat the age base-rate — astrology adds no timing information (≈ 0 bits).
- **Reliability**: if the observed column tracks the mean-forecast column (diagonal), graded confidence is calibrated; if it is flat regardless of forecast probability, confidence is **uncalibrated** — the McGrew–McFall 1990 finding, now on real timing data.
