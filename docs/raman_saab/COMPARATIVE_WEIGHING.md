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

## Phase 2 — validation REFUTED the preponderance hypothesis (2026-06-28)

Two agents read Raman's reasoning for all 7 Type-A cases. The benefic/malefic-preponderance
hypothesis held **0 of 7**. Raman does NOT head-count influences. The real mechanism:

- **Under-reads:** the engine's "lord/karaka strong" premise is WRONG in Raman's reading — the
  lord/karaka are afflicted by **Papakartari hemming** (h9_02: house+lord+karaka each hemmed; this is
  also chart_20/chart_31), by rasi affliction (h12_05: Saturn afflicted by Rahu), or the affliction
  is a Chandra-lagna + dasha matter the natal house doesn't carry (chart_44, read "ordinarily
  disposed"). The engine's per-leg affliction DETECTION is incomplete.
- **Over-reads:** Raman reads favourable via (1) **functional reclassification** — a malefic that is
  the lagna-lord / yogakaraka is GOOD, not afflicting (chart_17 Ketu disqualified as 12th-bhava;
  h5_16 Mars good as lagna-lord); (2) **named yogas** (h11_09 four-lord kendra dhana + Vipareeta Raja
  Yoga); (3) the navamsa is actually **corroborating/Vargottama**, so the engine's `navamsa=weakens`
  flag is simply WRONG in all 3 over-reads.

### Reframe: it's DETECTION, not aggregation
Raman's three-factor triangulation (bhava+lord+karaka, each checked, negative if ANY leg afflicted)
is the model the engine ALREADY has. The misses are per-leg DETECTION errors, not a missing weighing
scale. This is good news: the fix is the project's PROVEN safe pattern — specific cited gates that
fire only on the named structure, zero regression — NOT a risky aggregation change (which is the
calibration wall B1/B2/preponderance all hit).

### Revised plan — cited detection gates (safe pattern)
1. **Papakartari-on-lord/karaka demote gate** (covers chart_20, chart_31, h9_02; also B1's one real
   win chart_45) — when a leg is hemmed between two malefics and uncancelled, that leg is afflicted.
2. **Functional reclassification** — a natural malefic that is the bhava's functional benefic
   (lagna-lord / yogakaraka) must not count as a malefic affliction on it (chart_17, h5_16).
3. **Navamsa `weakens` false-positive fixes** — investigate the navamsa_status mis-reads in the 3
   over-reads (Vargottama/benefic-aspected navamsa wrongly flagged weakens).
4. (separate) yoga detection (Vipareeta/dhana) for h11_09; dasha/Chandra-lagna for chart_44.

Each gate: cite Raman -> bphs-doctrine-reviewer -> over-fire scan -> zero-regression ratchet ->
human baseline bump. Start with #1 (clearest, highest coverage, already validated by the B1 probe).
