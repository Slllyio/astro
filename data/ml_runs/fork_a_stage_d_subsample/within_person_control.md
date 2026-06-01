# Within-person concordance — confound control

Comparing the trained DeepHit model's within-person concordance against
trivial baselines that use NO chart features:

- **age**: window_start_jd - birth_jd (age in days at window start)
- **duration**: window_duration_days (longer windows have more event opportunity)
- **age+dur**: rank-sum of age and duration within each person (combined baseline)

If age, duration, or their combination achieves similar C_within to DeepHit,
the 'within-person signal' is a structural/exposure artifact, not Vedic.

## Per-class mean C_within (over 5 seeds)

| Class | DeepHit | Age | Duration | Age+Dur | DH - max(baseline) |
|---|---:|---:|---:|---:|---:|
| career | 0.5775 | 0.4033 | 0.6953 | 0.5778 | -0.1178 |
| death_cause_unspecified | 0.6091 | 0.7491 | 0.7300 | 0.8164 | -0.2073 |
| fame | 0.6028 | 0.3418 | 0.7372 | 0.5609 | -0.1344 |
| health | 0.5822 | 0.4790 | 0.6800 | 0.6216 | -0.0978 |
| personal | 0.6125 | 0.2931 | 0.7190 | 0.5133 | -0.1065 |

## Verdict heuristic

- If `DH - max(baseline)` is large positive (> +0.03), DeepHit adds chart
  structure on top of age+duration — Vedic signal is real (modest).
- If `DH - max(baseline)` is near zero or negative, the model adds nothing
  beyond trivial duration/age exposure — chart structure has no signal,
  and the original within-person concordance was a duration confound.
- Age-only is often REVERSED for life events (fame, career, personal come
  at younger windows-of-life; only death tracks age positively).