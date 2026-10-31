# KP engine pre-flight: base rates and birth-time stability (2026-10-31)

Run before any real-people test, on ordinary charts with **no outcomes involved**:

```
python -m tools.kp.base_rates --n 2000 --seed 20261031 --out docs/kp/kp_preflight_2026-10-31.json
```

2,000 charts: uniform random dates 1940-2005, uniform random local time, 12 Indian cities.
Engine as frozen in `docs/kp/KP_RULINGS.md`. Raw numbers: `kp_preflight_2026-10-31.json`.

## 1. What the engine says for ordinary charts

| Matter (cusp) | PROMISED | DENIED | MIXED | NOT_SIGNIFIED |
|---|---|---|---|---|
| Marriage (7) | 8.0% | 16.3% | **74.6%** | 1.2% |
| Health (1) | 11.5% | 27.2% | 56.9% | 4.5% |
| Wealth (2) | **81.7%** | (no denial houses, R14) | n/a | 18.4% |
| Service (10) | 12.5% | 11.4% | **74.3%** | 1.9% |

The marriage 7th-cusp sub-lord signifies on average 5.0 of the 12 houses, so it usually hits
both the favourable group (2, 7, 11) and the denial group (1, 6, 10, 12).

**Reading.** As Reader 3 states the rules, the 7th-cusp test does not give a yes/no for three
charts in four. It gives MIXED, and Reader 3 has no tie-break: Krishnamurti weighs these by
judgment. Most adults in India marry, so if MIXED counted as "no", KP would be wrong for most
people. If it counted as "yes", KP would say yes for 83% of charts, close to "always yes". Either
way, **the bare 7th-cusp rule cannot separate people who marry from people who don't** unless a
tie-break is added. Any tie-break is our addition (for example "the stronger significator wins"
or the later 4-step theory), so it must be chosen, named and frozen before seeing outcomes.

Wealth is the opposite case. With no denial houses in Reader 3, 82% of charts come out PROMISED,
so it is close to "always yes" by construction.

## 2. Birth-time stability

Share of charts whose verdict changes somewhere within ± the window:

| Matter | ±2 min | ±5 min | ±15 min |
|---|---|---|---|
| Marriage | 27.0% | 50.1% | 59.7% |
| Health | 38.2% | 66.1% | 77.7% |
| Wealth | 19.8% | 35.5% | 42.9% |
| Service | 28.5% | 49.2% | 58.9% |

A birth time rounded to the nearest 5 minutes (±2.5) already leaves about a third of marriage
verdicts undetermined. Every verdict the engine prints carries its own stability count for the
person's stated window, and a blind test must score unstable verdicts separately.

## 3. Timing coverage

For the marriage question, candidate dasa-bhukti-antara periods (all three lords signify 2, 7
or 11) cover on average **59.8%** of ages 20 to 40 (range 0% to 100% across 500 charts). A
marriage date falls in a candidate period about 60% of the time by chance alone, so a timing test
must beat that per-person coverage, not 0%.

## What this means for testing

1. The engine is ready to make sealed, blind records (`Verdict.to_dict()`), with fired rules,
   citations and stability. It takes no outcome as input.
2. As encoded strictly from Reader 3, the yes/no marriage and service verdicts are mostly MIXED.
   A real-people test of the strict rules would mostly measure how MIXED is scored. Before
   testing, one tie-break has to be chosen and frozen, or MIXED is scored as "no prediction"
   and the test runs on the rest (about a quarter of charts), which needs many more people.
3. Timing must be scored against each person's own coverage (chance level), not against zero.
4. Only minute-accurate birth times should enter a test; unstable verdicts are reported apart.

Nothing here touches real people or their outcomes. These are properties of the rules.
