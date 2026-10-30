# Parashara synthesis on real outcomes — results (run 2026-10-13, per PARASHARA_PREREG.md)

**Verdict: NULL on every pre-registered test — static and timing.** The prior (null, from the Raman
engine's run on the same data) is confirmed. The engine remains what CLAUDE.md says it is: a faithful
scholarly instrument answering "what would Parashara say", NOT a validated predictor of lives.

Store: 22,315 people (Raman store population) recast with the Parashara engine (Lahiri);
22,173 cast, 142 failures (0.64%; Raman 138). Primary tier A+B; tier C held out, untouched.
Pre-registration commit precedes every number below.

## Static — house verdict vs life outcome
Sham gate (expatriate -> H5): AUC 0.507, CI (0.475, 0.540), n=293 — NULL, gate passes.

| test | strength | AUC | 95% CI | perm p | BH | spec rank | n | status |
|---|---|---|---|---|---|---|---|---|
| H5 children | core | 0.471 | (0.438, 0.501) | 0.966 | – | 1 | 391 | null (wrong direction) |
| H8 longevity (Nisargayu) | core | 0.515 | (0.493, 0.539) | 0.916 | – | – | 685 | null |
| H12 prison | core | 0.497 | (0.469, 0.524) | 0.745 | – | 9 | 430 | null |
| H7 marriage | supporting | 0.500 | (0.477, 0.523) | 0.374 | – | – | 793 | null |
| H7 widowed | supporting | 0.512 | (0.486, 0.537) | 0.088 | – | – | 477 | null |
| H2 wealth | supporting | 0.430 | (0.347, 0.510) | 0.840 | – | – | 37 | null (under-powered) |
| H8 suicide | exploratory | 0.489 | (0.461, 0.520) | 0.712 | – | – | 341 | null |
| H8 accident | exploratory | 0.506 | (0.480, 0.536) | 0.306 | – | – | 394 | null |
| H9 father | supporting | 0.516 | (0.478, 0.555) | 0.225 | – | – | 496 | null |
| H4 mother | supporting | 0.497 | (0.458, 0.533) | 0.529 | – | – | 496 | null |

Pass bar AUC >= 0.55: none. No test survives BH q=0.10. (Raman's engine, same tests: also all null.)

## Timing — dasha windows vs dated events
| instrument | events / people | coverage | within-person lift (CI) | cross-chart excess (CI) | status |
|---|---|---|---|---|---|
| marriage -> auspicious H7 | 2,034 / 1,307 | 0.43 | −0.012 (−0.036, +0.009) | −0.012 (−0.037, +0.013) | null |
| divorce -> adverse H7 | 665 / 436 | 0.39 | −0.011 (−0.052, +0.030) | −0.055 (−0.103, −0.008) | null (excess in the WRONG direction) |
| death -> maraka, both lords | 2,377 / 1,990 | 0.34 | −0.002 (−0.023, +0.020) | −0.000 (−0.020, +0.019) | null |
| death -> maraka, either lord | 2,377 / 1,990 | 0.38 | −0.005 (−0.028, +0.018) | +0.001 (−0.019, +0.022) | null |

No instrument was withheld for saturation (Raman's run had to withhold 3 of 5). The cross-chart
control is now committed code (it was ad hoc in the Raman program).

**Caveat added 2026-10-13 (validation audit; numbers unchanged).** Each row mixes two levels:
day-dated events are scored against AD windows, year-only events (~83%) against MD windows. At MD
level the instruments are NOT distinct: `h7_auspicious` and `h7_adverse` share one MD window set,
and so do `maraka_both` and `maraka_either` (every MD maraka row is `both=True`). So the "both" row
is not an independent confirmation of the "either" row, and most of each row's n is MD-level.
The validation program (Phase 3, risk-set timing) reports AD and MD separately and supersedes
these rows; they stay as published.

## Reading it honestly
- This is the same measured truth as the Raman engine: classical indications are abundant enough
  to fit any life and cannot discriminate one — BPHS doctrine faithfully encoded inherits that.
- The report card's Raman/BPHS fidelity scores and this null are DIFFERENT axes; report them side by
  side, never averaged. A fidelity gain is not, and is not claimed to be, a predictive gain.
- Do not tune the engine toward these labels (METHODOLOGY.md): that would be overfitting.

Reproduce:
    py -3.12 -m tools.parashara.astrobank.build_store --raman-root <raman store> --out <parashara store>
    py -3.12 -m tools.parashara.astrobank.static_tests --raman-root <raman store> --store <parashara store>
    py -3.12 -m tools.parashara.astrobank.timing_tests --raman-root <raman store> --store <parashara store>

---

# Dasha + double transit (run 2026-10-13, per DOUBLE_TRANSIT_PREREG.md, committed first)

**Verdict: NULL on every instrument — but UNDERPOWERED.** Day-precision events only (transits cannot
be localised to a year-only date), tier A+B: just 199 marriages, 34 divorces, 230 deaths.

| instrument | events / people | coverage | within-person lift (CI) | cross-chart excess (CI) | status |
|---|---|---|---|---|---|
| marriage: dasha H7 AND double transit H7 | 199 / 169 | 0.21 | +0.038 (−0.022, +0.101) | +0.036 (−0.027, +0.099) | null |
| divorce: dasha H7 AND double transit H7 | 34 / 26 | 0.22 | −0.027 (−0.134, +0.104) | −0.062 (−0.171, +0.062) | null |
| death: maraka AD AND double transit H8 | 230 / 230 | 0.18 | +0.012 (−0.041, +0.065) | +0.018 (−0.035, +0.070) | null |
| marriage, transit only | 199 / 169 | 0.32 | +0.041 (−0.022, +0.109) | +0.017 (−0.051, +0.085) | null |
| divorce, transit only | 34 / 26 | 0.34 | −0.034 (−0.191, +0.160) | −0.043 (−0.177, +0.127) | null |
| death, transit only | 230 / 230 | 0.31 | +0.021 (−0.040, +0.083) | +0.029 (−0.033, +0.092) | null |

- The double transit SOLVED saturation (coverage 0.66 -> ~0.20): the instrument is narrow enough to
  test. It did not pass.
- Point estimates for marriage (+3.8%) and death (+1.2%) lean the predicted way, but the CIs are
  ~4x too wide to separate them from zero. Honest reading: the hypothesis is NOT confirmed, and a
  small true effect is NOT ruled out. Divorce (n=34) is uninformative.
- What would settle it: ~4x more day-precision events. The pre-registered rule stands unchanged for a
  confirmatory run (tier C held out; new day-dated events) — no redesign after seeing these numbers.

Reproduce:
    py -3.12 -m tools.parashara.astrobank.build_store --raman-root <raman store> --out <parashara store> --natal-only
    py -3.12 -m tools.parashara.astrobank.transit_tests --raman-root <raman store> --store <parashara store>

---

# Amendment 1: A+B extension (run 2026-10-13, per AMENDMENT_1, tier C withdrawn by AMENDMENT_2)

Extension store: 1,204 people outside the original store (0 cast failures), engine sha 19dc1dc4.
Rule, instruments, controls and pass bar are identical to the primary run.

| instrument | extension n | extension lift (CI) | **pooled A+B n** | **pooled lift (CI)** | pooled cross-chart (CI) | status |
|---|---|---|---|---|---|---|
| marriage: dasha H7 AND DT H7 | 115 | +0.026 (−0.050, +0.111) | **314** | **+0.034 (−0.014, +0.084)** | +0.029 (−0.019, +0.080) | null |
| divorce: dasha H7 AND DT H7 | 11 | +0.027 (−0.200, +0.266) | 45 | −0.040 (−0.139, +0.069) | −0.020 (−0.132, +0.094) | null (uninformative) |
| death: maraka AD AND DT H8 | 287 | −0.008 (−0.052, +0.038) | **517** | **+0.006 (−0.027, +0.043)** | +0.006 (−0.027, +0.040) | null |
| marriage, transit only | 115 | −0.027 | 314 | +0.004 (−0.051, +0.059) | +0.004 | null |
| divorce, transit only | 11 | −0.146 | 45 | −0.064 | −0.038 | null |
| death, transit only | 287 | −0.010 | 517 | +0.009 (−0.032, +0.050) | +0.010 | null |

- **Pooled verdict: null on every instrument.** No CI excludes 0 in the predicted direction.
- Marriage leaned the predicted way in both samples (+0.038 primary, +0.026 extension, +0.034 pooled),
  and the pooled CI is narrower, but still crosses 0. Reading: a small marriage effect (≲ +8%)
  is not ruled out. Nothing is confirmed.
- With the dasha leg removed, the marriage transit-only lean vanishes in the pool (+0.041 → +0.004).
  Whatever lean there is sits in the dasha + transit conjunction, not in the transits alone. This is
  an observation, not a test: no post-hoc claim is made on it.
- Death shows no lean (+0.006). Divorce (n=45) stays uninformative.
- Per AMENDMENT_1, this design is now CLOSED. The dasha + double-transit question moves into the
  validation program's pooled risk-set timing test (Phase 3), with held-out confirmation on tier-C half C1.

Reproduce:
    py -3.12 -m tools.parashara.astrobank.build_store --raman-root <raman> --out <parashara_ext> --extension
    py -3.12 -m tools.parashara.astrobank.build_store --raman-root <raman> --out <parashara_ext> --extension --natal-only
    py -3.12 -m tools.parashara.astrobank.transit_tests --raman-root <raman> --store <parashara_ext> --population extension
    py -3.12 -m tools.parashara.astrobank.transit_tests --raman-root <raman> --store <parashara_ext> --store <parashara> --population pooled
