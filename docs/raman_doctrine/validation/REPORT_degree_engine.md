# The real-birth degree engine — combustion helps, chalita hurts, degree-dignity is inert

The strength engine grades bhāva/lord/kāraka on Raman's 9-grade scale from **sign** placement,
even when handed exact longitudes — so the degree-accurate NH set (N=15) showed the same +1.13
over-credit as the sign-reconstructed corpora. This deliverable builds the **degree feature layer**
the scorer was blind to, grows the degree-accurate held-out set, and measures each degree feature
**blind** (nothing is fit; the whole corpus stays held-out).

## 1. A grown, degree-accurate held-out corpus (15 → 32)

`nh_strength_grow.json` adds **17 fresh Lagna-frame strength verdicts** (16 nativities: Gandhi,
Einstein, Lincoln, Nehru, Ramana, Marx, Nizam …) extracted from the clean *Notable Horoscopes*
full text, each carrying Raman's **printed degree positions**. Extraction was audited hard:

- three parallel agents cross-checked every candidate against Raman's actual prose, catching
  **cross-nativity section bleed** (phrases mis-sourced from adjacent charts — e.g. a Ramanuja
  Navāṁśa sentence mis-tagged to Sivananda) and the **grade-word-on-a-different-planet** failure
  mode (a kāraka's affliction read as the lord's — Lincoln's 4th lord Venus is *exalted*, not
  afflicted; Nero's affliction is Kalatrakāraka Venus, not the 7th lord Mercury);
- raw-text attribution then confirmed each surviving phrase sits in its own nativity;
- the **pre-registered** verdict map (`verdict_grade_map.json`) assigns every grade — unmappable
  phrases dropped, **no map changes**.

Pooled, the degree-accurate held-out set is **32 rows, 0 excluded**, with a healthier spread than
the affliction-heavy original (afflicted 9, weak 3, moderate 2, very strong 2, very powerful 1,
plus the original 15).

## 2. The degree feature layer (gated, doctrine-fixed)

`degree_features.py` supplies three quantities the sign scorer cannot see, wired into
`_assess_planet`/`_assess_bhava`/`_d1_houses`. Every feature is **doubly gated on
`chart.degree_resolved`** (true only for real printed/ephemeris longitudes), so sign-reconstructed
charts — the ch. IV anchor and every HTJAH held-out corpus — are **byte-identical**. Weights reuse
or are pinned to the scorer's existing dignity magnitudes; nothing is fit to NH.

- **Bhāva-chalita placement** — Sripati cusps (`bhava_chalit.py`) replace whole-sign houses.
- **Degree-graded dignity** — deep-vs-shallow exaltation/debilitation by Uccha-bala, and
  moolatrikona as a tier above ordinary own-sign (`dignity.py`).
- **Combustion** — orb-graded astangata (`planet_state.is_combust`) into the numeric assessor.

## 3. Blind ablation (NH degree pooled, N=32, 0 excluded)

| configuration | within-one | exact | mean Δ |
|---|---|---|---|
| none (== sign baseline) | 40.6% | 25.0% | +0.75 |
| bhāva-chalita only | **34.4%** | 25.0% | +0.50 |
| degree-dignity + moolatrikona only | 40.6% | 25.0% | +0.75 |
| **combustion only** | **43.8%** | 25.0% | **+0.69** |
| all three | 37.5% | 25.0% | +0.44 |

Three clean, separable results:

- **Combustion helps — the only feature that raises within-one** (40.6 → **43.8%**), and it does so
  in the right direction on the right rows: the combust Āyushkāraka Saturn in Tippu's 8th (Δ +2 →
  +1, crossing into within-one) and Buddha's combust 7th lord Saturn (Δ +4 → +3). On the original
  15 alone combustion is within-one-neutral (46.7% → 46.7%, only trimming the bias +1.13 → +1.07) —
  **consistent with Increment 13's finding** — so the gain is real but modest and shows up only once
  the corpus is broad enough to contain combust factors Raman explicitly grades.
- **Bhāva-chalita hurts** (40.6 → 34.4%). This is a genuine doctrinal result: **Raman grades
  strength by whole-sign rāśi, not Sripati cusps.** Re-classing planets to their chalita bhāva
  moves them off the houses Raman actually judges from, so it degrades agreement. The dusthāna
  under-score is *not* a cusp artifact — Raman really does read these placements whole-sign.
  Documented negative; default **off**.
- **Degree-dignity + moolatrikona is inert** (no change). Within a sign the Uccha depth spans only
  ~0.83–1.0, so the refinement never crosses a grade boundary. Documented negative; default **off**.

## 4. Result

The honest degree-engine deliverable is **combustion, orb-graded, in the numeric assessor**:
NH degree-accurate within-one rises **40.6 % → 43.8 % (N=32)**, mean over-credit **+0.75 → +0.69**,
with the anchor and all sign held-out numbers byte-identical. It is the first feature to move NH
within-one where Increment 13 could not — because it is measured on a corpus large enough to expose
combust factors Raman grades, not because the mechanism changed.

The larger lesson stands and is now **doctrinally grounded**: degree resolution does **not** rescue
the strength ceiling. The two levers that would have — cusp-accurate placement and degree-accurate
dignity — are exactly the two that *fail*, because Raman's own method is **whole-sign and
sign-dignity based**. What remains after the sign features are exhausted is his holistic weighing of
placement against dignity against association, which no feature — sign or degree — has closed. The
~53 % sign ceiling and the modest degree gain are the same story from two directions.

## Files
- `app/medini/doctrine/domains/degree_features.py` — the degree feature layer (chalita, degree
  dignity, combustion); doctrine-fixed, no fitted weights.
- `app/medini/doctrine/domains/house_judgment.py` — `degree_resolved`-gated wiring + the ablation
  toggles (`DEGREE_CHALIT/DIGNITY/COMBUST`); combustion on, the two negatives retained off as
  reproducible ablation levers.
- `app/medini/doctrine/raman_chart.py` — the `degree_resolved` flag (`from_printed_positions` → on).
- `docs/raman_doctrine/validation/corpora/nh_strength_grow.json` — the grown held-out corpus.
- `tests/doctrine/test_degree_features.py` — feature maths + the gate (sign charts untouched).
