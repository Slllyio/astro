# Phase 3J results: Jaimini chara dasha timing

Per `docs/validation/PHASE3J_JAIMINI_PREREG.md` (PHASE3J_JAIMINI_PREREG@7d9e4402). Parashara engine `chara_dasha`, Lahiri, mahadasha level. Phase 3 risk sets 13034; death events excluded 4869; kept 8165 (year-dated 6973, day-dated 1192); charts cast 34711/34711. Gates passed: **True**.

Exposure: the running chara dasa sign is the event house's sign from the Lagna (CONVENTION, Raman SJ art.159). E_rs = case − 10 matched controls; E_wp = case at the event − own lifetime share (ages 15–75). SIGNAL needs both CIs above 0 (Holm over P_y, P_d). SESOI 0.03.

## Primaries

| test | n | control coverage | E_rs | 95% CI | E_wp | 95% CI | CLR OR | MDE80 | Holm p | p_TOST | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P_y: chara MD sign = house (year-dated) | 6973 | 0.114 | +0.0013 | -0.0068..+0.0095 | +0.0114 | +0.0036..+0.0196 | 1.014 | 0.011 | 0.759 | 0.000 | **BOUNDED_NULL** |
| P_d: chara MD sign = house (day-dated) | 1192 | 0.110 | -0.0142 | -0.0328..+0.0069 | -0.0041 | -0.0226..+0.0147 | 0.849 | 0.027 | 0.324 | 0.059 | **UNDERPOWERED** |

## Control gates (500 draws, before the real comparison)

| gate | target | mean E | SD | CI coverage | pass |
|---|---|---|---|---|---|
| sham_P_y | +0.000 | -0.0000 | 0.0037 | 0.950 | True |
| planted_P_y | +0.030 | +0.0302 | 0.0038 | 0.944 | True |
| sham_P_d | +0.000 | -0.0005 | 0.0087 | 0.952 | True |
| planted_P_d | +0.030 | +0.0299 | 0.0092 | 0.942 | True |

## Placebo, sensitivity, families (descriptive)

| arm | n | coverage | E_rs | 95% CI | E_wp | 95% CI |
|---|---|---|---|---|---|---|
| P_y_placebo | 6973 | 0.120 | +0.0010 | -0.0073..+0.0092 | +0.0132 | +0.0051..+0.0210 |
| P_y_raman_ayanamsa | 6973 | 0.113 | -0.0015 | -0.0094..+0.0062 | +0.0084 | +0.0008..+0.0161 |
| P_y_lagna_ak_karakamsa | 6973 | 0.246 | +0.0058 | -0.0058..+0.0177 | +0.0124 | +0.0018..+0.0236 |
| P_y_rodden_AA | 5277 | 0.114 | +0.0015 | -0.0076..+0.0109 | +0.0110 | +0.0024..+0.0200 |
| P_y_rodden_A | 1696 | 0.113 | +0.0005 | -0.0154..+0.0173 | +0.0127 | -0.0024..+0.0285 |
| P_y family: career | 3219 | 0.100 | -0.0022 | -0.0134..+0.0102 | -0.0011 | -0.0125..+0.0106 |
| P_y family: health_legal | 304 | 0.112 | +0.0523 | +0.0106..+0.0983 | +0.0512 | +0.0094..+0.0948 |
| P_y family: other | 142 | 0.066 | -0.0380 | -0.0629..-0.0119 | -0.0646 | -0.0899..-0.0336 |
| P_y family: relationship | 3308 | 0.130 | +0.0017 | -0.0096..+0.0130 | +0.0231 | +0.0117..+0.0348 |
| P_d_placebo | 1192 | 0.115 | -0.0018 | -0.0211..+0.0185 | +0.0109 | -0.0084..+0.0303 |
| P_d_raman_ayanamsa | 1192 | 0.111 | -0.0182 | -0.0383..+0.0022 | -0.0054 | -0.0247..+0.0141 |
| P_d_lagna_ak_karakamsa | 1192 | 0.247 | -0.0218 | -0.0506..+0.0075 | -0.0099 | -0.0340..+0.0133 |
| P_d_rodden_AA | 889 | 0.108 | -0.0020 | -0.0259..+0.0237 | +0.0057 | -0.0179..+0.0315 |
| P_d_rodden_A | 303 | 0.116 | -0.0498 | -0.0789..-0.0197 | -0.0329 | -0.0590..-0.0047 |
| P_d family: career | 482 | 0.095 | +0.0149 | -0.0182..+0.0484 | +0.0139 | -0.0178..+0.0477 |
| P_d family: health_legal | 213 | 0.123 | -0.0333 | -0.0708..+0.0071 | -0.0215 | -0.0608..+0.0222 |
| P_d family: other | 88 | 0.072 | +0.0534 | -0.0311..+0.1541 | +0.0396 | -0.0477..+0.1434 |
| P_d family: relationship | 409 | 0.129 | -0.0531 | -0.0849..-0.0187 | -0.0256 | -0.0524..+0.0061 |

| secondary | E | 95% CI | p |
|---|---|---|---|
| S2_P_y specificity | +0.0014 | -0.0068..+0.0104 | 0.751 |
| S2_P_d specificity | -0.0155 | -0.0378..+0.0070 | 0.177 |

Antardashas deferred (rulings Q4), so there is no AD-level test. Death events are excluded (rulings Q5). Shams check arithmetic only; the placebo (sequence seeded at Lagna + 1) is the informative control.
