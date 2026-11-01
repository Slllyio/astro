# KP engine pre-flight, Reader 4 rules (2026-11-01)

Same 2,000 charts and seed as `KP_PREFLIGHT_2026-10-31.md`, re-run after marriage moved to
Reader 4 (R7: denial houses 4, 6, 10) and MIXED verdicts are settled by R18 (stronger ladder
level, then the cusp sub-lord's own sub-lord). No outcomes involved.

```
python -m tools.kp.base_rates --n 2000 --seed 20261031 --out docs/kp/kp_preflight_2026-11-01.json
```

## 1. Verdicts on ordinary charts

| Matter (cusp) | PROMISED | DENIED | MIXED | NOT_SIGNIFIED |
|---|---|---|---|---|
| Marriage (7) | 47.9% | 44.3% | 5.8% | 2.1% |
| Health (1) | 35.1% | 55.0% | 5.5% | 4.5% |
| Wealth (2) | 81.7% | (no denial houses) | n/a | 18.4% |
| Service (10) | 46.5% | 43.5% | 8.2% | 1.9% |

Before R18 (raw verdict, R12) marriage was MIXED for 68.7% (74.6% under the old 1, 6, 10, 12
houses). How each verdict was reached:

| Matter | direct | settled by level | settled by sub-lord | still MIXED |
|---|---|---|---|---|
| Marriage | 31.4% | 60.7% | 2.2% | 5.8% |
| Health | 43.2% | 49.2% | 2.2% | 5.5% |
| Service | 25.7% | 64.7% | 1.5% | 8.2% |

**Reading.** R18 does what it was chosen for: almost every chart now gets a yes or no. But the
marriage split is close to even, 48% promised and 44% denied, while most adults in India marry.
If the rules are applied as encoded, KP will say "denied" for many people who did marry. That is
a property of the rules as printed, found before any real person was looked at. It is not a
reason to change them now. Changing them to get more "yes" answers would be people-pleasing, not
fidelity. The real-people test will show whether the denials pick out the people who did not
marry or late marriages, or whether they fall at random.

Note also that 61% of marriage verdicts are settled by the level rule, which comes from one
worked case (KPR4 p.106) and one general statement (p.118). That is the thinnest link in the
chain, and the test should report direct and settled verdicts separately.

## 2. Birth-time stability (share of charts whose verdict changes within ± the window)

| Matter | ±2 min | ±5 min | ±15 min |
|---|---|---|---|
| Marriage | 32.4% | 61.0% | 72.2% |
| Health | 33.2% | 59.0% | 71.1% |
| Wealth | 19.8% | 35.5% | 42.9% |
| Service | 35.3% | 60.5% | 72.2% |

Settling ties makes verdicts **more** time-sensitive than before (marriage ±5 min: 50.1% → 61.0%),
because a yes/no now flips where MIXED used to absorb small shifts. A birth time known only to
the nearest 5 minutes leaves most verdicts undetermined. Only minute-accurate (or rectified)
birth times should be scored, and unstable verdicts reported apart.

## 3. Timing coverage

Unchanged: candidate periods for marriage cover on average 59.8% of ages 20-40 (promise houses
2, 7, 11 did not change). Timing must beat each person's own coverage, not 0%.

## What this means for testing

1. Score the verdict against facts, and report direct, level-settled and sub-lord-settled
   verdicts separately.
2. The chance baseline for marriage is not 50/50: compare against "always promised", which is
   right for everyone who married.
3. Exclude or separate verdicts that change within the person's birth-time window.
