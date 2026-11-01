# KP engine pre-flight, Readers 1-6 rules (2026-11-01)

Same 2,000 charts and seed as `KP_PREFLIGHT_2026-10-31.md`, re-run after:

- marriage moved to Reader 4 (R7: denial houses 4, 6, 10);
- MIXED verdicts settled by R18 (stronger ladder level, then the cusp sub-lord's own sub-lord);
- R6a (a planet in a node's star takes only the node's occupied house, from Krishnamurti's own
  significator table in Reader 5);
- children added (R19) and 17 cited events timed (R19).

No outcomes are involved.

```
python -m tools.kp.base_rates --n 2000 --seed 20261031 --out docs/kp/kp_preflight_2026-11-01.json
```

## 1. Verdicts on ordinary charts

| Matter (cusp) | PROMISED | DENIED | MIXED | NOT_SIGNIFIED |
|---|---|---|---|---|
| Marriage (7) | 48.3% | 44.0% | 4.8% | 3.1% |
| Children (5) | 47.9% | 44.8% | 3.1% | 4.3% |
| Health (1) | 35.0% | 54.4% | 4.5% | 6.2% |
| Wealth (2) | 77.3% | (no denial houses) | n/a | 22.7% |
| Service (10) | 46.6% | 43.9% | 6.8% | 2.8% |

How each verdict was reached:

| Matter | direct | settled by level | settled by sub-lord | still MIXED |
|---|---|---|---|---|
| Marriage | 37.6% | 55.7% | 2.0% | 4.8% |
| Children | 42.0% | 53.1% | 1.9% | 3.1% |
| Health | 49.9% | 43.6% | 2.1% | 4.5% |
| Service | 32.7% | 58.9% | 1.7% | 6.8% |

**Reading.** Almost every chart now gets a yes or a no. But marriage and children both split
close to even, about 48% promised and 44% denied, while most adults in India marry and have
children. As encoded, KP will say "denied" for many people who did marry or have children. That
is a property of the rules as printed, found before any real person was looked at, and the rules
are not changed to get more "yes" answers. The real-people test will show whether the denials
pick out the people without marriage or children, or fall at random.

More than half of the verdicts are settled by the level rule. That rule comes from one worked
case (KPR4 p.106) and one general statement (p.118), so it is the thinnest link; a test must
report direct and settled verdicts separately.

## 2. Birth-time stability (share of charts whose verdict changes within ± the window)

| Matter | ±2 min | ±5 min | ±15 min |
|---|---|---|---|
| Marriage | 32.6% | 60.9% | 72.6% |
| Children | 33.1% | 59.5% | 72.9% |
| Health | 33.9% | 60.1% | 72.0% |
| Wealth | 23.3% | 41.6% | 50.5% |
| Service | 34.8% | 60.1% | 72.3% |

A birth time known only to the nearest 5 minutes leaves most verdicts undetermined. Only
minute-accurate (or rectified) birth times should be scored, and unstable verdicts reported apart.

## 3. Timing coverage (chance level), ages 20-40, 500 charts

Share of the 20 years covered by candidate dasa-bhukti-antara periods, on average:

| Event | Coverage | Event | Coverage |
|---|---|---|---|
| Marriage | 52% | Transfer | 53% |
| Childbirth | 52% | Deputation | 56% |
| Getting service | 56% | Study (school/college) | 31% |
| End of service | 59% | Study abroad | 31% |
| Business | 53% | Scholarship | 28% |
| Money | 54% | Regaining position | 32% |
| Building | 53% | Overseas | 9% |
| Disposal | 50% | Imprisonment | 52% |

Most events cover about half of any 20-year stretch, so landing inside a window is close to a
coin toss by chance alone. A timing test must beat each person's own coverage, not 0%. The
narrow ones (overseas 9%, scholarship 28%) are the only ones where a hit would say much.

## What this means for testing

1. Score verdicts against facts, reporting direct, level-settled and sub-lord-settled verdicts
   separately.
2. Compare marriage and children against "always promised", which is right for most people.
3. Exclude or separate verdicts that change within the person's birth-time window.
4. Score timing against the person's own window coverage.
