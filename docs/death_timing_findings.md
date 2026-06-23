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

**Robustness (8-split cross-validation, mean ± 95% CI):** Mfine capture
**0.4367 ± 0.0037**, M0 (duration) 0.1997 ± 0.0017, the lord tilt
Δ(M2−M1) 0.0008 ± 0.0001 — the headline is not a single-split fluke.

**Age-bias caveat (honest):** the capture is concentrated in the typical death-age band.
Splitting Mfine capture by true death age: **≈0.57 for deaths after 70**, 0.27 for 40–70,
and **≈0.00 for deaths before 40**. The fine age model is near-useless for atypical
(young) deaths and the ~4.3× headline is carried by the elderly majority of the corpus.

**Cross-source generalization (the selection-bias test).** The corpus blends two
*person-disjoint* sources — astro_databank (30,826) and wikidata (6,049, all
day-precision). Training the age model + factors on one and testing on the *other*:

| train → test | Mfine capture | M1→M2 tilt |
|---|---|---|
| astro_databank → wikidata | **0.458** | +0.0011, **p=0.002** |
| wikidata → astro_databank | **0.430** | +0.0004, p=0.15 |

Capture holds at 0.43–0.46 across fully independent sources — **not a source/selection
artifact** — and the small astrology tilt independently replicates when trained on the
large source (it's just underpowered, not absent, when factors are fit on only 6k).

**So: the useful prediction is largely actuarial — "you'll most likely die in the
windows covering your high-mortality years."** Astrology adds a small, real tilt on top.

## Cause-specific signal — pooling hid it (new finding)
Every test above pooled ~37k mixed deaths. Classical doctrine assigns *different* killers
to *different* deaths (Mars/8th/nodes to violent ends, Saturn to chronic disease), which
pooling averages toward zero. Stratifying by the catalog's manner-of-death tags
(`manner_of_death.py`; holos: suicide ≈563, accidental ≈518, illness ≈1,959, unusual ≈182)
and contrasting **unnatural (suicide∪accidental∪unusual) vs natural (illness)**:

- Each violent-death karaka individually points the right way but is underpowered
  (dusthāna z=1.6, nodes z=1.3, Mars z=1.3 — all *unnatural > natural*).
- The **pooled violent signature** (MD-lord ∈ Mars ∪ Rahu/Ketu ∪ 8th-lord ∪ dusthāna ∪
  8th-occupants) clusters significantly more at unnatural deaths: **excess +0.048,
  z=2.82, p=0.005**, confirmed by a 5,000-shuffle permutation test (**p=0.0048**).

So the small pooled tilt is partly a **cancellation artifact**: the violent-death karakas
are real for violent deaths and washed out by natural deaths. A genuinely new, validated
result — though subgroups are modest, so it's a directional confirmation, not a large effect.

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
  **Quantified date-sharpening** (`evaluate_date_sharpening`, held-out, correct window
  given): high-precision / low-recall. Pooled it only shaves a ~145→133-day median error
  (~12 days), because just **~7% of deaths fall inside a Saturn band**. But *when a death
  does fall in a band* (n=153), the band midpoint pins the date to **~19 days vs ~162 — a
  ~9× sharpening (~144 days saved)**. Useful precisely on the minority it covers.

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
validation; doctrine-mining surfaced significators (Jaimini Karakāṁśa, Sūrya maraka)
*stronger* than the textbook one, and **manner-of-death stratification recovered a real
violent-death signature (z=2.82, p=0.005) that pooling had cancelled out**. But the
astrology-specific signal remains **small with a hard ceiling**: once the (actuarial)
age-at-death distribution is modeled finely, no classical lever nor a learned ML model
adds materially to *which* window. The product is an honest, calibrated **risk-tendency
ranker** (≈4.3× chance, age-driven — and weak for atypical ages — with a small real
astrological tilt and a high-precision Saturn-transit trigger that pins ~7% of deaths to
~3 weeks) — not a death-date oracle. It **generalizes across independent data sources**
(train astro_databank → test wikidata: capture 0.46, tilt p=0.002), so it isn't a
selection artifact. The predictor is served by `/doctrine/death-window`
(`calibrate=auto` uses the fine model; response carries a `model_card` + provenance).

## Reproduce
```
python -m app.medini.analysis.death_backtest --cross-val 8 --cross-source  # CIs, age-strata, source generalization
python -m app.medini.analysis.manner_of_death               # cause-specific (manner) signal hunt
python -m app.medini.analysis.alt_dasha_death               # significator + alt-dasha battery
python -m app.medini.analysis.transit_triggers              # transit lift + date-sharpening
python -m app.medini.ml.train_death_ranker                  # learned ranker vs the ceiling
```
See also `docs/death_timing.md` (method + API/UI).
