# Phase 3P results: Raman's pratyantar-level timing

Per `docs/validation/PHASE3P_PRATYANTAR_PREREG.md` (PHASE3P_PRATYANTAR_PREREG@06139d16). Raman engine, Raman ayanamsa. 2365 day-dated risk sets; 18619 charts cast. Gates passed: **True**.

E_rs = case − 10 matched controls; E_wp = case at the event − the case's own lifetime share (ages 15–75). SIGNAL needs both CIs above 0.

## Primaries

| test | n | control coverage | E_rs | 95% CI | E_wp | 95% CI | CLR OR | MDE80 | Holm p | p_TOST | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P3a: pratyantar lord activates | 2365 | 0.54 | +0.0091 | -0.0097..+0.0289 | +0.0016 | -0.0173..+0.0189 | 1.043 | 0.030 | 0.712 | 0.017 | **BOUNDED_NULL** |
| P3b: MD+AD+PD all activate | 2365 | 0.24 | -0.0048 | -0.0217..+0.0120 | -0.0109 | -0.0251..+0.0023 | 0.969 | 0.026 | 0.712 | 0.002 | **BOUNDED_NULL** |

## Control gates (500 draws, before the real comparison)

| gate | target | mean E | CI coverage | pass |
|---|---|---|---|---|
| sham_P3a | +0.000 | -0.0003 | 0.952 | True |
| planted_P3a | +0.030 | +0.0301 | 0.946 | True |
| sham_P3b | +0.000 | -0.0001 | 0.932 | True |
| planted_P3b | +0.030 | +0.0297 | 0.938 | True |

## Placebo, sensitivity, families (descriptive)

| arm | n | coverage | E_rs | 95% CI | E_wp | 95% CI |
|---|---|---|---|---|---|---|
| P3a_placebo | 2365 | 0.54 | -0.0074 | -0.0279..+0.0133 | -0.0128 | -0.0304..+0.0044 |
| P3b_placebo | 2365 | 0.25 | -0.0029 | -0.0218..+0.0153 | -0.0033 | -0.0167..+0.0104 |
| P3a_lahiri_frame | 2365 | 0.53 | +0.0086 | -0.0117..+0.0295 | +0.0005 | -0.0173..+0.0185 |
| P3b_lahiri_frame | 2365 | 0.25 | -0.0067 | -0.0238..+0.0116 | -0.0046 | -0.0186..+0.0097 |
| P3a_rodden_AA | 1854 | 0.52 | +0.0146 | -0.0085..+0.0371 | +0.0012 | -0.0191..+0.0217 |
| P3a_rodden_A | 511 | 0.59 | -0.0108 | -0.0545..+0.0309 | +0.0028 | -0.0349..+0.0429 |
| P3a family: career | 482 | 0.67 | -0.0317 | -0.0815..+0.0145 | -0.0334 | -0.0736..+0.0078 |
| P3a family: health_legal | 213 | 0.64 | +0.0296 | -0.0404..+0.1000 | +0.0290 | -0.0369..+0.0912 |
| P3a family: other | 202 | 0.78 | -0.0213 | -0.0898..+0.0410 | -0.0229 | -0.0762..+0.0300 |
| P3a family: own_death | 1006 | 0.33 | +0.0283 | -0.0010..+0.0578 | +0.0114 | -0.0178..+0.0392 |
| P3a family: relationship | 462 | 0.70 | +0.0136 | -0.0322..+0.0587 | +0.0147 | -0.0249..+0.0531 |

S1 dose-response over activating levels (0–3: MD, AD, PD), CLR log-odds per level: (0.017475500329221724, 0.47356044698823263)
