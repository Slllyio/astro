# Native-chart promise vs dasha timing (prime stage)

Does the kundli *promise* the result the dasha then *times*? Promise = domain-matched natal strength (house-lord + karaka + occupancy + aspect) of the bhava each event belongs to.

## 1. Promise → valence

| promise | n | benefit % | lift | p vs base |
|---|---:|---:|---:|---:|
| strong | 1498 | 74 | **1.00** | 0.789 |
| medium | 1958 | 75 | **1.00** | 0.876 |
| weak | 1597 | 75 | **1.00** | 1 |

## 2. Promise × timing (the doctrine test)

Benefit share split by whether the running dasha activates the promised house (MD/AD = house-lord or karaka). Doctrine predicts a *wider* strong−weak gap when timing activates.

| timing activates | promise | n | benefit % |
|---|---|---:|---:|
| True | strong | 916 | 82 |
| True | medium | 1208 | 82 |
| True | weak | 957 | 82 |
| False | strong | 582 | 62 |
| False | medium | 750 | 63 |
| False | weak | 640 | 64 |

- timing=True: strong−weak gap = **+1 pp**

- timing=False: strong−weak gap = **-2 pp**

- **activates vs not (marginal): 82% vs 63%** — looks huge, but see §3.

## 3. CONFOUND CONTROL — timing effect *within* event class

Event valence here is near-deterministic per class (career ~97% beneficial, marriage 100%, death/health 0%). Beneficial classes are also activated more often, so the marginal gap above is mostly Simpson's paradox. The honest test is within class:

| event_class | n timed | n not | benefit timed | benefit not | gap |
|---|---:|---:|---:|---:|---:|
| career | 2098 | 593 | 0.97 | 0.98 | **-0.01** |
| marriage | 381 | 469 | 1.00 | 1.00 | **+0.00** |
| death | 292 | 385 | 0.00 | 0.00 | **+0.00** |
| relationship | 116 | 163 | 0.72 | 0.73 | **-0.01** |
| divorce | 86 | 120 | 0.00 | 0.00 | **+0.00** |
| health | 64 | 170 | 0.00 | 0.00 | **+0.00** |
| education | 43 | 72 | 1.00 | 1.00 | **+0.00** |

> **Within-class gaps are ≈0** (max |gap| = 0.01). The marginal promise×timing effect is a class-composition artifact, not a real timing→outcome signal. Conditioned on event class, neither promise nor dasha-domain activation moves valence — because in this corpus valence is essentially a function of event_class.

## 4. Permutation — does the promise match beat chance?

Chart-shuffle null, K=400.

| quantity | value |
|---|---|
| real strong−weak promise gradient | **-0.0033** |
| null mean ± std | -0.0135 ± 0.0175 |
| z-score | **0.585** |
| empirical p | **0.2843** |
| K effective | 400 |
