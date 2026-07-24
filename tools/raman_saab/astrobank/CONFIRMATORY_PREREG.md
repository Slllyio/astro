# Pre-registration — the confirmatory study + two new doctrine hypotheses (Stage 10)

> Committed BEFORE any computation on the samples below. Directions, samples, tests, and alphas are
> locked here; results will be reported regardless of outcome. Family: 3 primary tests, each
> alpha=0.05 one-sided, BH q=0.10 across the family for the headline claim.

## Study 1 — CONFIRMATORY: suicide → afflicted H8 death-manner

The one channel that survived the exploratory program (AUC 0.535, perm p=.005; specificity rank
1/56; raw-evidence 0.536 — three independent designs, all on the tier-A/B population).

- **H1:** tier-C suicide-labeled cases score LOWER (more afflicted) on the engine's H8 `death`
  signification than tier-C controls.
- **Sample (held out):** the 218 tier-C suicide cases whose verdicts sit in the feature store but
  were **never included in any analysis** (zero overlap with the 341 exploratory cases), vs the
  tier-C non-suicide cohort members in the store (~5,043), **excluding** H8_ACCIDENT-labeled people
  (same-signification contamination).
- **Test:** one-sided Mann-Whitney U on the verdict-degree score; report AUC + bootstrap 95% CI.
- **Prediction:** AUC ≈ 0.53 (the exploratory estimate). Success = AUC > 0.5 with p < .05.
- **Pipeline validity companion (not a hypothesis):** tier-C expatriate vs other tier-C controls on
  H5 children — expected null.
- **Caveat (accepted):** tier-C controls are other-cohort members, not a random sample; their
  labels (children/marriage/wealth/longevity) are judged orthogonal to the H8 death reading.
  Round-hour times blur houses mildly; the exploratory tier-A/B AUCs were near-identical
  (0.53/0.52), so attenuation should be small.

## Study 2 — NEW DOCTRINE: Kuja Dosha → marital discord (tested directly, not via the engine)

The most famous classical marriage claim. Raman's own single-chart form (HTJAH-II:2579-2632,
already encoded in the engine): **Mars in houses {2,4,7,8,12} from the Lagna** = Kuja/Mangal dosha
→ marital affliction.

- **H2:** P(divorced | Kuja dosha) > P(divorced | no Kuja dosha) within the divorced ∪
  long-marriage universe (tier A/B, the labeled-contrast design).
- **Feature:** Mars whole-sign house from the Lagna, cast fresh (raman ayanamsa); dosha =
  rasi_house ∈ {2,4,7,8,12}. **Secondary (registered):** the from-Moon reckoning variant; and the
  exemption-free vs engine-exemption forms if the primary is positive.
- **Test:** one-sided two-proportion (Fisher exact); effect as odds ratio + CI. Base rate note:
  Kuja dosha covers 5/12 houses ⇒ expected dosha prevalence ~42% in both groups under the null.

## Study 3 — NEW DOCTRINE: Saturn-afflicted Moon → suicide (tested directly)

Classical: the Moon is the mind; Saturn's affliction of the Moon yields depression/self-harm.
Raman locates suicide suppression in a well-disposed Lagna/Moon/10th (HTJAH-II:3075-3080).

- **H3:** P(suicide-labeled | Moon afflicted by Saturn — conjunct OR full-drishti-aspected,
  whole-sign) > P(suicide | Moon unafflicted by Saturn), within suicide ∪ store-control universe
  (tier A/B). **Secondary (registered):** waning Moon AND Saturn affliction (the dark-Moon
  amplification); Mars-afflicted Moon as a specificity comparator (doctrine names Saturn as the
  depressive significator — Mars should carry less of this signal).
- **Test:** one-sided Fisher exact; odds ratio + CI.

## Governance

Direct chart-feature tests (Studies 2-3) test the DOCTRINE'S OWN PRIMITIVES, bypassing the engine
verdict layer entirely — immune to the saturation/calibration issues the atlas documented. Nothing
here tunes the engine (METHODOLOGY.md sovereignty). Results will be appended to
REAL_OUTCOME_GENERALIZATION.md verbatim, positive or null.
