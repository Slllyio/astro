# Fresh, engine-unseen corpus — extraction, de-dup integrity, and the honest strength re-baseline

The strength engine's held-out number (52.8% within-one, 51 rows) is no longer pristine:
the Phase-1 verdict-map fixes were verified against it and the Phase-2 recalibration was
fit to it. This deliverable builds a **genuinely engine-unseen** corpus — worked charts
neither the engine nor this project has touched — and measures the engine on it **blind**.

## 1. Tier-1 text catalog + a de-dup integrity fix

`catalog_unseen.py` enumerates every "Chart No. N … Born …" across both HTJAH volumes and
de-dupes against every existing corpus. The first cut de-duped on **birth-date only**, and
that silently leaked **48 already-seen charts into the "fresh" set** — including the
calibration **anchor (Charts 12–14)** and every tuned chapter (**h2/h7/h9/h11**). Those
corpora store a chart number but **no birth line**, so nothing keyed them out; OCR-garbled
years (`18*0`) slipped the date net too.

The fix keys de-dup on **(vol, chart_no)**. HTJAH restarts "Chart No." numbering at the top
of Vol II (the 7th-house chapter is Chart No. 1), so chart numbers are unique only *within*
a volume; volume is derived from the house judged (≤6 → Vol I, ≥7 → Vol II). Result:

| | charts | strength candidates |
|---|---|---|
| before (birth-date de-dup) | 164 "fresh" | 60 |
| after (vol, chart_no) de-dup | **115 fresh (0 leaks)** | **38** |

`test_unseen_corpus.py` now pins the (vol, chart_no) disjointness against every extracted
corpus. The reading-type histogram of the 115 fresh charts: strength 38, yoga 28,
death_timing 12, longevity 4 — confirming up front that the fresh **9-grade strength** count
is small; the bulk of unseen material is timing/longevity/yoga (the house-strength vein is
largely spent, exactly as forecast).

## 2. Tier-2 — sign-grid extraction for the fresh strength charts (vision)

For each fresh strength candidate: render its diagram page (PyMuPDF 3×) → a vision agent
reads the two South-Indian squares against the **fixed sign key** and emits Rāśi + Navāṁśa
signs (Rāhu/Ketu-opposite enforced) → **cross-check every placement against Raman's own prose**
(the relative positions he states) → **reachability gate** → score through
`worked_chart_validate` against the pre-registered map. Grids/verdicts are attached separately:
agents do the vision, the verbatim verdicts come from Raman's text (which factor/chart each
phrase judges).

### Honest yield: 38 candidates → 7 clean scoreable charts (14 rows)
Most fresh strength candidates were **not** cleanly scoreable, and every drop is recorded:

- **Offset analysis.** In HTJAH the chart *diagram* floats to the top of a page while the
  *analysis prose* on that page discusses the **next** chart number ("after the Chart No. 91
  diagram comes … 'The 5th house in Chart No. 92 is Gemini'"). Verdicts must be paired via the
  in-prose chart reference, not the birth line above them — several candidates were narrative
  or soft ("good", "ordinary") with no gradeable house verdict.
- **Dropped, not guessed:** ch65 (agent grid irreconcilable with the prose — "the 4th is
  Cancer" forces Lagna Aries, contradicting the read); ch91 (its Conclusion could not be
  unambiguously attributed to it vs the adjacent sterility chart 90 under the floated-diagram
  flow); ch83 (a duplicate nativity of ch52); ch36/113/242/252 (Balāriṣṭa death-narrative /
  no gradeable strength verdict).
- **ch35** passed prose-verification on the Rāśi but its Navāṁśa **failed the reachability
  gate** (Saturn Gemini unreachable from Scorpio) → scored **Rāśi-axis-only**, not discarded.
- **ch80** was extracted and fully prose-verified by hand (Rāśi-only).

Each retained grid was checked against Raman's explicit statements, e.g. ch52: Lagna
Capricorn → 8th Leo occupied by Rahu ✓, 8th-lord Sun in a kendra with the 4/11, 6/9 and
5/10 lords all in Libra ✓, Āyushkāraka Saturn 11th in Scorpio ✓, and from the Moon the 8th
lord Jupiter with Ketu in the 10th ✓ — a full independent reconstruction.

## 3. Results (blind — the engine was never tuned on these)

| set | n rows | exact | within-one | mean Δ |
|---|---|---|---|---|
| **fresh Tier-2 (blind)** | **14** | 35.7% | **71.4%** | **−0.50** |
| existing held-out (pooled) | 53 | 26.4% | 52.8% | +0.49 |
| **pooled held-out + fresh** | **67** | 28.4% | **56.7%** | +0.28 |

The fresh set's within-one (71.4%, N=14) is higher than the standing held-out number but on a
small sample, and its bias is **opposite** (mean Δ −0.50: the engine *under*-scores here,
vs +0.49 *over*-scoring on the older set) because the fresh set is 8th-house-heavy. Both big
misses are **already-documented engine gaps**, not new ones:

- **ch35** — 8th-lord Moon in its own sign Cancer with exalted Jupiter: Raman "full and very
  powerful", engine "weak" (Δ−7). The **dusthāna-lord under-score** the project has flagged
  repeatedly (the engine reads any 8th-house placement as weakening).
- **ch52** — the 8th lord Sun is debilitated in Libra but sits in a kendra with four lords:
  Raman grades it "fairly strong" *by placement/association*, engine "afflicted" (Δ−5) —
  the **debilitation-vs-placement** trade the sign-only engine can't weigh.

The pooled **56.7% within-one (N=67)** is the honest, refreshed strength number, consistent
with the established ~53% held-out ceiling. Adding 14 blind rows moved it within noise — it
did **not** reveal the engine as better or worse than the tuned-corpus-informed estimate,
which is exactly what a clean held-out test should show.

## 4. Integrity guardrails
- `unseen_scoreable.json` charts are disjoint by (vol, chart_no) from every extracted corpus
  (pinned in `test_unseen_corpus.py`); the corpus scores with **0 excluded** (every row
  prose-verified + gate-passed).
- Measurement only — **no engine change**; the anchor (ch IV 8/8) and tuned floor are
  untouched. The fresh corpus is kept blind for any future structural fix.
- Every candidate is accounted for: catalogued, scored, or logged as an explicit drop with a
  reason. No cherry-picking.

## Files
- `app/medini/doctrine/validation/catalog_unseen.py` — Tier-1 catalog + (vol, chart_no) de-dup.
- `app/medini/doctrine/validation/build_unseen_scoreable.py` — self-contained Tier-2 corpus
  builder (embedded verified grids + verbatim verdicts).
- `docs/raman_doctrine/validation/corpora/{unseen_catalog,unseen_scoreable}.json`.
- `tests/doctrine/test_unseen_corpus.py` — de-dup + fresh-corpus integrity guards.

## Maximum expansion — the clean full text sets the ceiling (2026-07-10)

With the clean full text supplying garble-free, offset-corrected verdicts for ~200 charts,
the **maximum addressable** fresh strength set is now exactly quantifiable: filter the clean
charts to those that (a) are house-judgments, (b) carry a map-gradeable verdict, (c) have a
birth date, and (d) are unseen by **(vol, chart_no)** against every extracted corpus. That
yields **8 charts** — decisive proof the HTJAH house-strength vein is spent (the 12 house
chapters are otherwise fully mined).

Of the 8: **7 survived** vision extraction + the reachability gate + a per-chart cross-check
against Raman's own prose placements (ch79 failed the Navāṁśa gate). Corpus `unseen_grow.json`
(builder embeds the verified grids). **ch65 is recovered** — the chart Tier-2 dropped for an
irreconcilable grid; with the clean prose as the cross-check ("the 4th is Cancer" → Lagna
Aries; Moon+Mercury in Libra; Rahu in Aquarius; Jupiter debilitated in Capricorn) the agent
produced a fully prose-consistent grid.

### Result — the remaining charts are the *hard tail*
| set | rows | within-one | mean Δ |
|---|---|---|---|
| grow (all 7 charts) | 9 | **33.3%** | +1.11 |
| grow, non-tuned-house only | 5 | **0.0%** | +0.80 |
| **ALL POOLED** (held-out + Tier-2 + grow) | **76** | **53.9%** | +0.43 |

Growing to the maximum **lowered** the pooled held-out (56.7% → **53.9%**), because the
charts that were *left* are the ones the engine gets wrong: ch76 (RFK) — the 8th house Raman
calls "heavily afflicted" the engine grades "fairly good" (Δ+4, benefic-aspect over-credit);
ch65 — the afflicted 4th lord/kāraka the engine grades "moderate" and the clean 4th house it
grades "weak" (the holistic-weighing inversion). The earlier **71% Tier-2 figure was an
easy-subset artifact**; the honest broad held-out on the full mined HTJAH set is **~54%**,
right at the established structural ceiling. Houses 4/8/11 are non-tuned held-out; house 7 is
tuned-*house* (flagged `tuned_house`) so the pooled number separates them.

### Honest takeaways
- **The vein is empty.** 8 addressable → 7 scored is the end of the HTJAH strength corpus;
  further growth needs a different source (*Notable Horoscopes*, still figure-less) or the
  degree path.
- **The blind number fell, and that is the point.** A clean maximal held-out set removed the
  small-sample optimism; ~54% is the number to beat, and the misses it exposes are the same
  documented structural ceilings (benefic-aspect over-credit, holistic negative-weighing),
  not new phenomena.
- Guarded by `test_unseen_corpus.py::test_grow_corpus_is_unseen_and_scores`.
