# Notable Horoscopes — engine-vs-Raman gap analysis (2026-06-27)

36 NH DRAFT rows where the engine's verdict disagreed with Raman's were each analyzed against Raman's
cited reasoning (Workflow, 6 agents). Classification: **34 doctrine_gap, 1 extraction_error, 1 ambiguous.**

**Critical synthesis (the honest shape): the 34 gaps collapse into ~6 recurring principles, dominated by
ONE already-known mechanism (B1). This is NOT 34 new rules.** Each theme is a judge-mechanism change that
will move the ratchet, so each must go through the full anti-overfit pipeline (cite → bphs-doctrine-reviewer
→ over-fire scan → zero-regression → human bump), tuned not hand-fit. Direction split was symmetric
(13 fav→affl, 10 affl→fav, 6 mixed→fav, 4 mixed→affl) — confirming several distinct principles pulling
both ways, not one bug.

## Theme 1 — B1 three-factor comparative weighing (THE dominant cluster, ~17 rows) `judge-mechanism`
Raman lets the **strongest** of {bhava, lord, karaka} dominate, and a **decisively weak/afflicted dominant
factor drags the house down** even when another factor is strong. The engine's preponderance count
under-weights a strong/dignified LORD/KARAKA/benefic-OCCUPANT against malefic aspects (and vice-versa).
- **Positive leg (strong factor should LIFT; fav→affl/mixed):** chart_25 H2, chart_26 H2, chart_32 H1,
  chart_33 H1, chart_65 H1, chart_53 H7, chart_57 H1, chart_61 H10, chart_42 H10 (+ Neechabhanga).
- **Negative leg (weak factor should DRAG; the engine too lenient):** chart_26 H1 (vitality-karaka Sun
  eclipsed), chart_45 H2 (debilitated lord), chart_53 H2 (lord in dusthana), chart_65 H2, chart_67 H5,
  chart_57 H5.
**This IS the deferred backlog item B1** (HTJAH-I:3713/3788/3815/2760/2111). NH now provides ~17 charts of
corroboration — the strongest case yet to build B1. Highest yield; highest risk (must not regress chart_54).

## Theme 2 — Malefic-concentration / aspect-aggregation threshold (~5 rows) `threshold`
"≥3 malefics afflicting the lord/house → afflicted"; "house free of malefic aspect AND benefic-aspected →
not afflicted"; "two malefics OCCUPYING a house → at least mixed regardless of competing yogas."
- chart_55 H1, chart_75 H1, chart_26 H9, chart_61 H10, chart_35 H4.
Codeable + general; tune the count threshold (do not hand-set). Pairs with B1.

## Theme 3 — Functional-yogakaraka malefic does NOT afflict its house (~3 rows) `judge-mechanism`
A natural malefic that is the chart's **functional yogakaraka** should not afflict the house it occupies/
aspects. The primitives exist (`IsYogaKaraka`, `functional_nature`); the suppression rule does not.
- chart_69 H1, chart_57 H1, chart_61 H9.

## Theme 4 — Lord "blemished" (combust / node-conjunct / afflicted-dispositor) downgrades the house (~3) `new-rule`
- chart_54 H9 (lord exact-conjunct Rahu), chart_75 H9 (lord combust + afflicted constellation-lord),
  chart_54 H1 (debil malefic occupant + lord aspected by 8th-lord).

## Theme 5 — Karaka-papakartari + Navamsa(D9) cross-check (~2 rows) `new-rule` (over-fire risk)
Papakartari read on the **karaka** (not just the lord), and a **D9** condition of the bhava, temper the D1
verdict. Engine's papakartari is D1-only and lord-only.
- chart_37 H5, chart_63 H1. **Caution:** D9 overlays over-fire easily — gate hard.

## Theme 6 — Singletons (each n≈1; document, low priority)
- chart_33 H6: 6th as **upachaya** — a malefic there gives victory over enemies → mixed, not afflicted.
- chart_75 H10: a **Mahapurusha (Hamsa) yoga** occupant should floor an otherwise-afflicted house at mixed.

## REJECT — conflicts with a LOCKED decision (do NOT assimilate)
- **chart_33 H2** — relies on **Sripathi/unequal-bhava** house division (a planet late in the Lagna sign
  counts in the 2nd bhava). The engine uses **whole-sign houses (locked)**. Assimilating this would diverge
  the engine into a different house system. **Dropped; this row stays DRAFT/documented-limit.**

## VERIFY before treating as gaps (engine may already handle)
- chart_33 H10, chart_37 H7 — "doesn't co-judge from the Moon": the engine **already builds a MOON frame**
  (`house_template` LAGNA/MOON/KARAKA). Re-examine whether the real issue is lead-frame selection, not a
  missing frame.
- chart_37 H10 — Parivartana: the engine **has** `bhangas.parivartana` + Khadga yoga; the gap (if any) is
  crediting it for the 10th, a wiring question not a missing primitive.

## Not gaps
- 1 extraction_error (drop from DRAFT on review); 1 ambiguous (n=1 chart conclusion, not a general rule).

## Recommendation
Build in this order, each through the full anti-overfit pipeline with a human baseline bump:
**B1 (Theme 1)** first — it clears the largest cluster and unblocks the deferred HPA avastha + Shankha/
Kahala/Lakshmi yogas that also need effective-strength. Then **Theme 2** (threshold, tuned), then
**Themes 3–4** (additive rules). Treat **Theme 5** cautiously (D9 over-fire). The ~17 B1 + ~5 threshold +
~6 Themes 3-4 rows are the real, faithful accuracy lever — not 34 ad-hoc fixes. The rejected Sripathi row
and the verify-first rows are the guardrails that keep this from diverging.
