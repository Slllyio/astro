# Phase 3Y results: Yogini dasha timing

Per `docs/validation/PHASE3Y_YOGINI_PREREG.md` (PHASE3Y_YOGINI_PREREG@c4c5f710). Parashara engine, Lahiri, Phase 3 instrument with Yogini lords. Risk sets 13034 (kept 13034: AD 2365, MD 10669); charts cast 38329/38329. Gates passed: **True**.

E_rs = case − 10 matched controls; E_wp = case at the event − the case's own lifetime share (ages 15–75). SIGNAL needs both CIs above 0 (Holm over P1, P2). SESOI 0.03.

## Primaries

| test | n | control coverage | E_rs | 95% CI | E_wp | 95% CI | CLR OR | MDE80 | Holm p | p_TOST | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P1: Yogini AD tier ≥ 3 (day-dated) | 2365 | 0.28 | -0.0101 | -0.0291..+0.0101 | -0.0042 | -0.0210..+0.0125 | 0.951 | 0.027 | 0.629 | 0.023 | **BOUNDED_NULL** |
| P2: Yogini MD lord activates (year-dated) | 10669 | 0.49 | +0.0008 | -0.0098..+0.0114 | +0.0049 | -0.0040..+0.0139 | 1.003 | 0.014 | 0.878 | 0.000 | **BOUNDED_NULL** |

## Control gates (500 draws, before the real comparison)

| gate | target | mean E | SD | CI coverage | pass |
|---|---|---|---|---|---|
| sham_AD | +0.000 | -0.0003 | 0.0095 | 0.938 | True |
| planted_AD | +0.030 | +0.0312 | 0.0093 | 0.932 | True |
| sham_MD | +0.000 | -0.0002 | 0.0053 | 0.932 | True |
| planted_MD | +0.030 | +0.0301 | 0.0045 | 0.958 | True |

## Placebo, sensitivity, families (descriptive)

| arm | n | coverage | E_rs | 95% CI | E_wp | 95% CI |
|---|---|---|---|---|---|---|
| P1_placebo | 2365 | 0.27 | +0.0075 | -0.0121..+0.0273 | +0.0092 | -0.0071..+0.0255 |
| P1_raman_ayanamsa | 2365 | 0.28 | -0.0071 | -0.0256..+0.0110 | -0.0045 | -0.0212..+0.0118 |
| P1_rodden_AA | 1854 | 0.28 | -0.0210 | -0.0424..+0.0018 | -0.0114 | -0.0303..+0.0071 |
| P1_rodden_A | 511 | 0.27 | +0.0295 | -0.0133..+0.0743 | +0.0222 | -0.0152..+0.0567 |
| P1 family: career | 482 | 0.30 | +0.0015 | -0.0445..+0.0504 | +0.0079 | -0.0331..+0.0482 |
| P1 family: health_legal | 213 | 0.27 | +0.0230 | -0.0440..+0.0973 | +0.0083 | -0.0538..+0.0690 |
| P1 family: other | 202 | 0.31 | -0.0540 | -0.1187..+0.0125 | -0.0358 | -0.0876..+0.0158 |
| P1 family: own_death | 1006 | 0.28 | -0.0122 | -0.0418..+0.0166 | +0.0030 | -0.0211..+0.0288 |
| P1 family: relationship | 462 | 0.25 | -0.0134 | -0.0604..+0.0353 | -0.0243 | -0.0572..+0.0108 |
| P2_placebo | 10669 | 0.49 | -0.0007 | -0.0108..+0.0098 | +0.0041 | -0.0047..+0.0131 |
| P2_raman_ayanamsa | 10669 | 0.49 | -0.0028 | -0.0131..+0.0079 | +0.0028 | -0.0064..+0.0122 |
| P2_rodden_AA | 8238 | 0.49 | -0.0003 | -0.0126..+0.0115 | +0.0024 | -0.0081..+0.0121 |
| P2_rodden_A | 2431 | 0.49 | +0.0048 | -0.0173..+0.0254 | +0.0135 | -0.0052..+0.0313 |
| P2 family: career | 3219 | 0.50 | +0.0039 | -0.0164..+0.0247 | +0.0120 | -0.0041..+0.0288 |
| P2 family: health_legal | 304 | 0.49 | +0.0026 | -0.0583..+0.0640 | -0.0177 | -0.0701..+0.0341 |
| P2 family: other | 386 | 0.52 | +0.0070 | -0.0477..+0.0590 | -0.0055 | -0.0557..+0.0436 |
| P2 family: own_death | 3332 | 0.50 | +0.0031 | -0.0144..+0.0210 | +0.0129 | -0.0023..+0.0295 |
| P2 family: relationship | 3428 | 0.48 | -0.0051 | -0.0236..+0.0130 | -0.0063 | -0.0218..+0.0088 |

| secondary | E | 95% CI | p |
|---|---|---|---|
| S2_P1 specificity | -0.0133 | -0.0325..+0.0059 | 0.173 |
| S2_P2 specificity | -0.0029 | -0.0133..+0.0068 | 0.569 |

S1 dose-response (CLR log-odds per Yogini tier 0–4, P1 sets): (-0.03727823819572444, 0.017841293830365982)
S3 (double transit) not run, per the prereg. Shams check arithmetic only; the placebo Yogini is the informative control.
