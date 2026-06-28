# Comparative-weighing — the real accuracy lever (effort kickoff, 2026-06-28)

The holdout-locked B1 tuner proved effective-strength recalibration is the WRONG mechanism for the
engine's misses (B1_ANALYSIS.md). This effort targets the RIGHT one: how bhava/lord/karaka strength
and the benefic/malefic preponderance are AGGREGATED into a verdict. Started as its own deliberate
effort, not a B1 continuation.

## Phase 1 — empirical foundation (DONE): the 13 real-errors, characterized

Pulled from `track_b_ordinal_scoreboard()` (dist>=2). Directional split: **9 under-read** (engine
favourable / Raman afflicted), **3 over-read** (engine afflicted / Raman favourable), 1
insufficient-evidence. Engine decision factors reveal TWO distinct failure types:

### Type A — comparative-weighing (~7): factors seen, weighed wrong
| case | eng | raman | lord_s | karaka_s | navamsa | #mal | #ben | diagnosis |
|---|---|---|---|---|---|---|---|---|
| h12_05 H12 expenditure | fav | aff | T | T | neutral | **13** | 3 | malefic preponderance ignored |
| h9_02 H9 father | fav | aff | T | T | neutral | 6 | 6 | malefic side should win |
| chart_44 H2 wealth | fav | aff | **F** | T | neutral | 2 | 1 | weak lord, still favourable |
| chart_60 H3 siblings | fav | aff | T | T | confirms | 3 | 3 | affliction should dominate |
| chart_17 H1 self | aff | fav | T | T | **weakens** | 2 | **5** | benefic majority ignored |
| h5_16 H5 children | aff | fav | T | T | **weakens** | 1 | 2 | navamsa over-weighed |
| h11_09 H11 gains | aff | fav | T | F | **weakens** | 1 | 3 | benefic majority ignored |

Signature: the engine treats lord/karaka strength as near-decisive; a strong lord rescues a
heavily-malefic bhava (under-reads), and `navamsa=weakens` sinks a benefic-majority bhava
(over-reads — all 3 over-reads carry navamsa=weakens). Raman weighs benefic/malefic **preponderance**
co-equally with lordship.

### Type B — rule-coverage gaps (~5): the affliction was never DETECTED
| case | eng | raman | #mal fired | gap |
|---|---|---|---|---|
| h5_10 H5 children | fav | aff | 0 | affliction not fired at all |
| h11_01 H11 elder_siblings | fav | aff | 0 | affliction not fired |
| chart_20 H1 self | fav | aff | 2 | Papakartari hemming not fired as malefic |
| chart_31 H1 self | fav | aff | 2 | Papakartari hemming not fired |

These are NOT weighing problems — the engine can't weigh what it never saw. They need detection
rules (Papakartari-on-lord; the specific afflictions of h5_10/h11_01), a separate workstream.

## Proposed plan (deliberate)
- **Phase 2 — validate against Raman:** read his reasoning for the 7 Type-A cases; confirm he
  actually reasons via benefic/malefic preponderance (the Vivekananda lesson: don't trust a tidy
  pattern without the corpus). Separate genuine preponderance cases from coverage.
- **Phase 3 — design:** a bounded preponderance-weighing step in `_decide` — when the benefic/malefic
  preponderance strongly disagrees with the lord/karaka verdict, it moves the verdict ONE step
  (favourable<->mixed<->afflicted), never inverting. Co-equal with lordship, not overriding.
- **Phase 4 — implement with holdout-lock:** the same discipline that disciplined B1 — calibrate the
  preponderance threshold on a train split, validate it holds on a holdout, ship only at zero
  regression on the 208 confirmed.

Type B (coverage) is tracked separately and not part of the weighing mechanism.
