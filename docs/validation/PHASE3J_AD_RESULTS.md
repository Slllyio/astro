# Phase 3J-AD results: Jaimini chara antardasha timing

Per `docs/validation/PHASE3J_AD_PREREG.md` (PHASE3J_AD_PREREG@27d0516a). Parashara engine `chara_dasha.antardashas` (BPHS-51 sl.7-12), Lahiri. Day-dated non-death Phase 3 sets: 1192; kept 1192; charts cast 10866/10866. Gates passed: **True**.

Exposure: the running antardasha sign is the event house's sign from the Lagna (CONVENTION, Raman SJ art.159). SIGNAL needs both E_rs and E_wp CIs above 0. SESOI 0.03.

## Primary

| test | n | control coverage | E_rs | 95% CI | E_wp | 95% CI | CLR OR | MDE80 | p | p_TOST | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P_ad: chara AD sign = house (day-dated) | 1192 | 0.094 | -0.0042 | -0.0215..+0.0128 | +0.0038 | -0.0124..+0.0202 | 0.951 | 0.025 | 0.632 | 0.002 | **BOUNDED_NULL** |

## Control gates (500 draws, before the real comparison)

| gate | target | mean E | SD | CI coverage | pass |
|---|---|---|---|---|---|
| sham_P_ad | +0.000 | +0.0001 | 0.0089 | 0.952 | True |
| planted_P_ad | +0.030 | +0.0301 | 0.0086 | 0.966 | True |

## Placebo, secondary, sensitivity, families (descriptive)

| arm | n | coverage | E_rs | 95% CI | E_wp | 95% CI |
|---|---|---|---|---|---|---|
| P_ad_placebo | 1192 | 0.084 | -0.0117 | -0.0266..+0.0032 | -0.0141 | -0.0279..+0.0014 |
| S_conv | 1192 | 0.010 | -0.0027 | -0.0079..+0.0029 | -0.0006 | -0.0049..+0.0047 |
| P_ad_raman_ayanamsa | 1192 | 0.092 | +0.0007 | -0.0175..+0.0180 | +0.0070 | -0.0101..+0.0248 |
| P_ad_lagna_ak_karakamsa | 1192 | 0.236 | -0.0135 | -0.0362..+0.0102 | -0.0038 | -0.0264..+0.0192 |
| P_ad_rodden_AA | 889 | 0.095 | -0.0026 | -0.0238..+0.0188 | +0.0056 | -0.0124..+0.0238 |
| P_ad_rodden_A | 303 | 0.091 | -0.0089 | -0.0407..+0.0244 | -0.0018 | -0.0302..+0.0286 |
| P_ad family: career | 482 | 0.089 | -0.0124 | -0.0367..+0.0120 | -0.0072 | -0.0306..+0.0178 |
| P_ad family: health_legal | 213 | 0.093 | -0.0089 | -0.0496..+0.0315 | +0.0014 | -0.0309..+0.0382 |
| P_ad family: other | 88 | 0.122 | +0.0489 | -0.0306..+0.1326 | +0.0522 | -0.0200..+0.1266 |
| P_ad family: relationship | 409 | 0.094 | -0.0034 | -0.0319..+0.0283 | +0.0074 | -0.0204..+0.0372 |

S2 specificity: -0.0046 (-0.0223..+0.0142), p 0.625.
Shams check arithmetic only; the placebo (sequence seeded at Lagna + 1) is the informative control.
