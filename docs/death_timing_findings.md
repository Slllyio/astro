# Death-Timing: Consolidated Findings

A research report on whether classical Vedic doctrine can time death, validated at
population scale and held-out backtested. Every claim below is gated: it survived a
25%-held-out person split (factors calibrated only on the disjoint 75%) and/or a
per-death test against a dāśā-length / per-person-uniform baseline.

## Corpus & method
- **36,959 dated deaths** (holos year-precision + Astro-Databank dated + Wikidata P570
  day-precision enrichment, matched by exact label + birth-year ±1). Lahiri ayanāṁśa.
- **Backtest** (`death_backtest.py`): each person died in exactly one of their 81
  Vimśottarī MD×AD windows; we score nested models of P(death in window) and measure
  **capture@10%** (true window in the model's riskiest 10%; null ≈ 0.10) on held-out
  persons.
- **Doctrine battery** (`alt_dasha_death.py`): per-death lift + p of each significator
  / dasha vs its baseline share.

## Headline (corrected)
The calibrated predictor lands the true death window in its **top 10% about 43% of the
time — ≈4.3× chance.** That power is **overwhelmingly the age-at-death distribution**,
not astrology:

| Ranking model | capture@10% |
|---|---|
| duration only (time-at-risk) | 0.193 |
| + coarse 3-bucket longevity bracket (old "M2") | 0.219 |
| **+ fine age-at-death model (MortalityModel) × composite** | **0.435** |
| XGBoost learning-to-rank (all features) | 0.436 |

The learned ML ranker (0.436) ≈ the fine age model (0.435): the ML found **no signal
beyond the empirical age-at-death curve** — its top features are age/time (md_seq,
duration, mid_age); the astrology features barely register. The earlier "≈2× / 0.22"
figure was an artifact of the *coarse* 3-bucket age factor; the fine `MortalityModel`
(already shipped for calibrated probabilities) roughly doubles it.

**So: the useful prediction is largely actuarial — "you'll most likely die in the
windows covering your high-mortality years."** Astrology adds a small, real tilt on top.

## What's astrologically real (the tilt, beyond age)
- **Composite confluence** — MD lord playing more of {maraka, 3rd-lord, 64th-navāṁśa}:
  dose-response 1.025 / 1.093 / 1.187 at ≥1/2/3 roles. Held-out M1→M2 Δ logLik z=2.7,
  p=0.006 — real but tiny (realized lift ≈1.001).
- **Doctrine-mined stronger marakas (new finding):** the maraka counted from the
  **Karakāṁśa** (Jaimini, lift 1.067) and from the **Sun** (1.058) individually beat the
  textbook **Lagna** maraka (1.035), all p<1e-8. The tradition's Jaimini/Sūrya marakas
  really are sharper — but being correlated, they don't raise the composite ceiling.
- **Transit-Saturn conjunction (narrowing, not ranking):** transit Saturn within ±3° of
  a natal maraka/Sun is over-represented on death days (lift 1.131, p=0.001; ±2°→1.167).
  It pinpoints *weeks within* a flagged window — but adds nothing to *which* window
  (M2→M3 p=0.97), because it's a within-window timing signal.

## What's null (tested and rejected — kept honest)
| Hypothesis | Result |
|---|---|
| Transit over natal dusthāna *houses* (6/8/12) | null (lift ≈1.00) |
| Double transit (Saturn AND Jupiter on a death point) | null (1.06, p=0.52) |
| Strength-gating: maraka must be strong (shadbala) | null (p=0.69) |
| Strength-gating: avastha / Mrita-state | contradicted (death lords don't avoid Mrita) |
| Ashtottari dasha (classically a *death* dasha) | *anti*-correlated (0.97, p=1e-6) |
| Yogini dasha | weak (1.02), below Vimśottarī |
| Maraka from the Moon; 8th-from-Karakāṁśa | *anti*-correlated (0.96 / 0.93) |
| Atmakaraka as death lord | null |
| Transit factor for window *ranking* | null (M2→M3 p=0.97) |
| Learned ML ranker beyond age | no gain (≈ fine age model) |

## Verdict
Classical Vedic death-timing **is not noise** — multiple effects survive held-out
validation, and doctrine-mining even surfaced significators (Jaimini Karakāṁśa, Sūrya
maraka) *stronger* than the standard textbook one. But the **astrology-specific signal
is small and has a hard ceiling**: once the (actuarial) age-at-death distribution is
modeled finely, no classical lever — composite, transit, strength, alt-dasha, Jaimini —
nor a learned ML model adds materially to *which* window. The product is an honest,
calibrated **risk-tendency ranker** (≈4.3× chance, age-driven, with a small real
astrological tilt and a validated Saturn-transit trigger that narrows to weeks) — not a
death-date oracle.

## Reproduce
```
python -m app.medini.analysis.death_backtest        # nested models + Mfine capture
python -m app.medini.analysis.alt_dasha_death        # significator + alt-dasha battery
python -m app.medini.analysis.transit_triggers       # transit-conjunction lift
python -m app.medini.ml.train_death_ranker           # learned ranker vs the ceiling
```
See also `docs/death_timing.md` (method + API/UI).
