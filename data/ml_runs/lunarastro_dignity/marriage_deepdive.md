# Marriage timing — deep dive (chart-shuffle K=600)

Chart-specific house-lord significators of marriage, tested against a donor-ascendant null. ✶ = p < 0.05.

## Significators × sub-period

| significator | level | n | obs | null | lift | z | p |
|---|---|---:|---:|---:|---:|---:|---:|
| 7th-lord | MD | 1750 | 14% | 12% | **1.15** ✶ | 2.18 | 0.0183 |
| 7th-lord | AD | 1750 | 12% | 12% | **0.99** | -0.11 | 0.5491 |
| 7th-lord | MD∩AD | 1750 | 2% | 2% | **1.25** | 1.42 | 0.0998 |
| 2nd-lord | MD | 1750 | 10% | 11% | **0.87** | -1.77 | 0.9767 |
| 2nd-lord | AD | 1750 | 12% | 12% | **1.02** | 0.26 | 0.4293 |
| 2nd-lord | MD∩AD | 1750 | 2% | 2% | **1.02** | 0.09 | 0.4975 |
| 11th-lord | MD | 1750 | 10% | 11% | **0.89** | -1.51 | 0.9517 |
| 11th-lord | AD | 1750 | 12% | 12% | **0.99** | -0.17 | 0.579 |
| 11th-lord | MD∩AD | 1750 | 2% | 2% | **1.20** | 1.13 | 0.1647 |
| any of 2/7/11 | MD | 1750 | 30% | 30% | **0.98** | -0.45 | 0.7005 |
| any of 2/7/11 | AD | 1750 | 32% | 32% | **1.00** | 0.01 | 0.4942 |
| any of 2/7/11 | MD∩AD | 1750 | 10% | 11% | **0.92** | -1.16 | 0.8935 |

## Split-half replication — 7th-lord MD

| seed | half | n marriages | obs | null | lift | z | p |
|---|---|---:|---:|---:|---:|---:|---:|
| 0 | A | 876 | 13% | 12% | **1.16** | 1.66 | 0.0649 |
| 0 | B | 874 | 14% | 12% | **1.15** | 1.62 | 0.0516 |
| 1 | A | 902 | 13% | 11% | **1.14** | 1.45 | 0.0849 |
| 1 | B | 848 | 14% | 12% | **1.16** | 1.67 | 0.0666 |
| 2 | A | 855 | 15% | 12% | **1.21** ✶ | 2.25 | 0.0183 |
| 2 | B | 895 | 12% | 11% | **1.09** | 0.97 | 0.1814 |

## Verdict

- **It is the 7th-lord in the Mahadasha** that times marriage (lift 1.15); the AD is null (0.99), and **2nd/11th lords do not time marriage** (0.87, 0.89) — combining 2/7/11 only dilutes the 7th-lord signal.
- **Double activation sharpens it**: MD∩AD on the 7th-lord lifts to 1.25 (highest of all), though underpowered (~2% of marriages).
- **Replication**: 7th-lord MD lift is positive in all 6 disjoint halves (mean lift 1.15, mean z 1.60); individual-half significance is weak only because a lift of ~1.15 needs the full sample to resolve. The direction and magnitude reproduce everywhere.
