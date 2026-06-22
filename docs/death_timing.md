# Death-Timing Predictor

A per-chart predictor that ranks a living person's future Vimśottarī dāśā periods by
death risk, with **calibrated probabilities** — built on findings validated at
population scale over a 36,959-death corpus.

## What it does

Given birth data it casts the natal chart, enumerates the future MD×AD (or MD×AD×PD)
dāśā windows, and ranks them by death risk. With calibration on, each window carries a
real probability `P(death falls here | alive now)` plus a longevity summary
(`median_remaining_years`, `prob_within_5y`, `prob_within_10y`).

- **UI:** `GET /medini/doctrine/death-window/page` (linked from the landing page as
  "Life-Stage Timing").
- **API:** `GET /medini/doctrine/death-window?year=&month=&day=&latitude=&longitude=&tz_offset=&depth=ad|pd&top_n=&calibrate=true`

## The validated method

Two empirically-significant levers, each tested vs a dāśā-length-weighted baseline:

1. **Composite death-significator confluence** — how many of {maraka_full, 3rd-lord,
   64th-navāṁśa} the running MD lord plays. Monotonic dose-response:
   lift **1.025 / 1.093 / 1.187** at ≥1/2/3 roles.
2. **Longevity bracket (āyurdāya)** — the marakas fire in *madhya* (age 32–70, lift
   **1.09**, p≈0), are under-represented in *alpa* (<32, 0.89), marginal in *pūrṇa* (>70).

The transit (gochara) **house** lever is **null** (slow planets over natal 6/8/12 at
death all lift ≈ 1.00). But the **degree-orb transit-conjunction** lever is real
(see "Narrowing" below).

## Narrowing: transit-Saturn conjunction trigger

Validated on the 8,578 exact-date deaths against a per-person uniform baseline (a
transiting planet's longitude on a random day is ~uniform over 360°, so each person's
expected hit-rate is the fraction of the circle within orb of their natal trigger
points). Only **transit Saturn** carries signal (Jupiter/Mars/Rāhu/Ketu null):

| Trigger (orb ±3°) | lift | p |
|---|---|---|
| transit Saturn → natal Sun | 1.20 | 0.019 |
| transit Saturn → natal Saturn (Saturn return) | 1.18 | 0.029 |
| transit Saturn → maraka set | 1.13 | 0.017 |
| **combined: transit Saturn → (maraka ∪ Sun)** | **1.131** | **0.001** |

Lift rises as the orb tightens (±8°→1.09, ±5°→1.10, ±3°→1.13) — the signature of a
genuine conjunction, not an artifact. Transit Saturn over the 2nd/7th lords *alone*
is null; the effect concentrates on natal Saturn and Sun.

`death_window_predictor.predict_death_windows(..., transit_refine=True)` (or
`/death-window?transit_refine=true`) uses this to **narrow** each flagged multi-year
dāśā window to the multi-week bands when transit Saturn is within ±3° of a natal
maraka/Sun point — e.g. a 3.3-year window collapses to three ~45–171-day bands (the
splits are Saturn's retrograde loops over the point). Module:
`app/medini/analysis/transit_triggers.py` (validate with `python -m app.medini.analysis.transit_triggers`).

## Calibration (real probability)

The empirical age-at-death distribution from the corpus is used as a conditional
survival model. A window's probability is its age-mass (conditioned on survival to the
current age — this already encodes duration + the longevity bracket) tilted by the
composite confluence, renormalized over the person's future windows. No double-counting
of age.

## Honest effect size (held-out backtest)

Validated on a 25% held-out person split (factors calibrated on the disjoint 75%),
scoring nested models of `P(death in window w)`:

| Model | per-death log-likelihood |
|---|---|
| M0 — duration only | −4.223 |
| M1 — + longevity bracket | −4.201 |
| M2 — + composite confluence | −4.200 |

- **Top-decile capture: 19.3% → 21.9%** vs a 10% null — the predictor lands the real
  death window in its riskiest 10% about **2× chance**.
- The bulk of that is time-at-risk + age (M0→M1). The **lord-specific signal (M1→M2)
  is real and significant (z≈2.7, p≈0.006) but small** (realized lift ≈1.001).

**Bottom line:** this ranks life-stage mortality *exposure* — a genuine ~2× edge over
chance — not an individual death date. It is a risk-tendency ranker, not a prophecy.

## Other event classes

The same machinery (`GET /medini/doctrine/event-significators?event_class=`) was run on
marriage and career. Unlike death's multi-significator confluence, both reduce to a
**single kāraka — Jupiter MD** (relationships lift 1.34 p=1e-6; career 1.36 p=1e-4);
the classical 7th-lord/Venus/10th-lord/Saturn significators are weak or null here, so
no confluence predictor is offered for them.

## Data provenance

36,959 dated deaths: holos "NNNN deaths" tags (year-precision) + Astro-Databank dated
events + **Wikidata P570 day-precision enrichment** (+6,052 across two passes, matched
by exact label + birth-year ±1; accented and mononym names recovered in a second pass).
Lahiri (Chitra Paksha) ayanāṁśa throughout.

## Code map

- `app/medini/analysis/doctrine_validator.py` — significators, composite, bracket, maraka tests
- `app/medini/analysis/death_window_predictor.py` — predictor + `MortalityModel` calibration + PD windows
- `app/medini/analysis/death_backtest.py` — held-out nested-model backtest
- `app/medini/etl/enrich_deaths_wikidata.py` — day-precision death enrichment
- `app/api/doctrine_routes.py` — HTTP surface; `app/templates/death_window.html` — UI
