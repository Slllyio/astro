# Utilizing owner-confirmed real-outcome feedback — the plan

> **Scope.** How the engine turns owner-confirmed *real life* feedback (per-signification verdicts
> + dated events, for the anchor self-chart and family members) into engine improvement — safely.
> Mechanism only; all names, birth data and health specifics live in gitignored `data/private/`
> and `tests/fixtures/field_case_01.json` (anonymized). Synthesized from a 4-agent research pass
> (2026-07-23).

## The thesis (non-negotiable)

**Owner-confirmed feedback is a held-out DIAGNOSTIC and SPECIFICITY control — never a training
target.** It reveals where the engine is wrong and whether it fires on the *right* axis. It is
never fit to. Every engine change is justified by a **Raman citation + ZERO regression on the 241
textbook goldens** (`tests/raman_saab/test_goldens.py`); the confirmed life only *reveals where to
look*. This is the discipline the two shipped real-outcome fixes already followed — and note they
deliberately **left misses unfixed** where the only available fix was doctrinally unfaithful. That
refusal is the Prime Directive in practice.

## Why the corpus forces discipline

The confirmed corpus is small and correlated: the anchor chart (~50 verdicts, 14 events) + the
elder child (~5 verdicts, 1 event) = **n≈2 charts, and effectively ~1.5 independent situations**
(one shared child-outcome is legible in three related charts and must be counted **once**). At
this size, **zero data-driven threshold tuning is legitimate.** A data-driven move on the
real-outcome track would need on the order of **30+ independent, unrelated confirmed nativities**,
diverse across lagna/dasha/affliction, held out from any fit. The family is the *seed that proves
the harness works*, not the corpus that tunes the engine.

## What already exists (don't rebuild)

- **The threshold tuner is structurally walled off** from family data — `tune_thresholds.py` only
  loads `raman_goldens.jsonl`. Keep it that way; that separation is the whole game.
- **A full rectification subsystem** — `rectification/events.py` (event→house taxonomy),
  `candidates.py` (piecewise-constant birth-time walk), `scoring.py` (event-fit), `suggest.py`
  (next-best-question by information gain), HTTP+CLI, a worked golden. Unlock = point family data
  at it.
- **Cross-chart + varga surfaces** — `two_spouse_children.py` (both-parents' 5th),
  `saptamsa_reading.py` (D-7 children); the `_MATTER_VARGA` map declares D30→disease, D12→parents.

## Guardrails (Tier 0 — must always hold)

1. Never point the tuner at the confirmed-family set.
2. Never copy a family verdict into `raman_goldens.jsonl` (that file is both the tuner's fit set
   and the CI ratchet — one copy converts a held-out test into a training target).
3. Never promote an **engine-run** reading into confirmed ground truth (verify against life, never
   engine self-output).
4. Count a cross-chart-shared outcome **once**, not once per chart it appears in.

## Program (prioritized)

### Tier 1 — highest leverage, low risk
- **[SHIPPED 2026-07-23] Rule-precision ledger** — `tools/raman_saab/rule_precision.py`. Joins each
  confirmed verdict to the per-fired-rule ledger the engine already computes, and ranks rules by
  *consequential* misfire (fired against the confirmed life AND the final verdict is also wrong),
  distance-ranked. Anti-overfit is structural: a rule is only "SAFE-TO-INVESTIGATE" once it
  misfires on **≥2 independent charts**; single-chart hits are labelled "grow the corpus first".
  It mechanically reproduces the hand-found over-affliction gap (the three H3 rules, dist=2) and
  collapses benign rule-fires to a count.
- **[SHIPPED 2026-07-23] `developmental_diagnosis` event type** — `rectification/events.py`. A
  mental-faculty diagnosis now maps to **H5 (Budhi) + aux H2 (speech), kāraka Mercury**
  (HTJAH-I:5012 intellect + 2316 speech), instead of the generic `illness_accident` H6/H8 disease
  register — so the event tests the houses the static verdicts actually concern. (Register choice
  flagged for a `bphs-doctrine-reviewer` confirmation.)
- **[OPEN] Elicit the wife's H3 + one orthogonal dated event.** Her independent H3
  (siblings/courage) is the decisive second counterexample that de-risks the Tier-3 fix from
  overfitting (n=1→n=2); an orthogonal day-precise event (career/property, not the Venus/Jupiter
  marital cluster) unlocks her rectification to ~13-min class.

### Tier 2 — engine additions (report-only, net nothing)
- **[SHIPPED 2026-07-23] D-30 Trimsāṁśa child-health surface** —
  `judges/trimsamsa_health_reading.py` (+ `render_trimsamsa.py`). The doctrinally-correct home for
  the child-health / "will she recover" question: read from the child's **own** nativity
  (1st/6th/8th + Moon/Mercury kārakas + bālāriṣṭa), with a report-only D-30 overlay. Provenance-
  honest split like the D-7 surface; reproduces the prior hand reading's core findings.
- **[OPEN] Generalize `two_spouse_children` → matter-agnostic N-chart concordance** with a
  kāraka-cluster recurrence detector. The four-chart family is its validation triangle: the
  younger child is a built-in **negative control** (same parents, without the confirmed matter), so
  a detector that fires on the affected child but not the sibling is a real specificity signal no
  single chart can give. Report-only; any "family signature" recurrence is `ABSENT_IN_RAMAN`.

### Tier 3 — the one doctrine fix the data reveals (gated)
- **[OPEN, GATED] H3 over-affliction (bhava-rescue).** The anchor chart's only dist=2 misses are
  H3 siblings/courage: three malefic rules fire on a genuinely favourable life, and the pipeline
  drops the verdict to afflicted. The doctrinal fix — port the **bhava-rescue** (HTJAH-I:503-505,
  "if the house itself has good aspects, evil should NOT be predicted") onto the contradiction
  path where it currently doesn't run. **Do NOT ship until** (a) the wife's H3 confirms it (n=2)
  and (b) it zero-regresses all 241 goldens. Cited fix, held-out-confirmed, ratchet-gated.

### Tier 4 — hardening the real-outcome track
- Populate `data/private/real_outcomes.json` per member; wire `real_outcome_validate` into a local
  pre-commit hook (CI can't see gitignored `data/`); tighten its timing check with the scorer's
  precision (`_covers`) gate; commit an **anonymized** timing fixture (like `field_case_01`) so the
  family timing track gains some CI protection without PII.

## Forbidden (overfitting / leakage traps)
Point the tuner at the family set; propose-and-validate a rule on the same chart; copy a family
verdict into the golden file; treat an engine-run reading as ground truth; count correlated
verdicts as independent; auto-re-base any ratchet floor to bank a lucky fit. Also: don't chase
dist=0 on the catastrophic-gate `mixed` floor (that conservatism is by design, not a bug).

## Elicitation protocol (grow the corpus)
Store under gitignored `data/private/`. Phrase each item as a plain life-question on the ordinal
scale (afflicted = clearly denied / mixed = present-but-troubled / favourable = clean). Prioritize
the significations where the anchor chart *misses or is borderline* (an independent second chart is
what converts a "held / overfit-risk" lead into a safe fix). For the wife: full house-by-house,
**H3 first**, plus dated orthogonal events. For a young child: a restricted, health-anchored,
gently-phrased, provisional set (~4-5 keys) — never marriage/career; the elder child's clean n=1
entry is the template.
