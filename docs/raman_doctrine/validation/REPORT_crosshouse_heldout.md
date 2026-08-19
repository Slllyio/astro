# Cross-house held-out validation — all genuinely non-tuned houses (Phase E)

The engine was tuned on houses 1/2/7/9/11 + the ch. IV anchor. This report pools **every
genuinely-held-out house** — the 4th (the original pilot) plus the six non-tuned houses
extracted in Phase E (3, 5, 6, 8, 10, 12) — into one cross-house number. No engine change;
measurement only.

## Headline
**168 held-out charts extracted → 51 scoreable rows across 7 houses; within-one 24/51
(47%), mean Δ +0.82.** Per factor: bhāva 9/18 (50%), lord 8/17 (47%), **kāraka 7/16 (44%,
mean +1.19)** — the kāraka over-credit is the dominant cross-house bias.

| house | chapter | charts | gate-pass | mappable rows | kāraka |
|---|---|--:|--:|--:|---|
| 3rd  | Vol I ch VI   | 10 | 10/11 | 4  | Mars (Bhrātṛ) |
| 4th  | Vol I ch VII  | 7  | (pilot) | 18 | Moon (Matru) |
| 5th  | Vol I ch VIII | 13 | 13/13 | 12 | Jupiter (Putra) |
| 6th  | Vol I ch IX   | 13 | 13/14 | 0  | Mars (Roga) |
| 8th  | Vol II ch XII | 42 | 42/46 | 9  | Saturn (Āyush) |
| 10th | Vol II ch XIV | 66 | 66/75 | 3  | Amātya (Sun/Merc/Jup/Sat) |
| 12th | Vol II ch XVI | 17 | 17/21 | 5  | Saturn/Venus |
| **total** | | **168** | ~91% | **51** | 5 distinct kārakas |

## The two findings
1. **The engine's biases replicate on genuinely held-out data, across 7 houses and 5
   different kārakas.** The lord/kāraka over-credit (B) recurs everywhere: ch69 kāraka
   Saturn **+6** (8th), ch59 lord **+5** (3rd), ch70 lord/kāraka +3 (4th), ch98 kāraka +3
   (5th, Jupiter). It is not a 4th-house/Moon artifact — it is structural. (One
   opposite-signed outlier: ch181 lord Moon **−5**, an atmakāraka "very strong" the engine
   under-credits — a different, rarer failure.) The bias is the same one Phase B plateaued
   on and increment 8 (B) showed is not separable on the sign-only engine's features.
2. **Raman's verdict language, not chart supply, is the binding constraint.** 168 charts
   yield only 51 scoreable rows: the crisp 9-grade "House/Lord/Kāraka is <strength>" format
   is common in Vol I houses 4/5 and Vol II 8, but the 6th (disease), 10th (profession),
   and much of 12th (loss) describe *outcomes*, which the pre-registered map correctly
   won't grade. The remaining ~117 charts are retained (gate-verified) for reuse if the map
   is extended, and their balance lines feed the daśā-timing corpus.

## Method (reusable, proven)
Per chapter: render pages (PyMuPDF) → **general-purpose vision agent** (≤15 imgs/batch after
a 32MB limit) emits per-chart JSON → normalize planet keys → **reachability + Rāhu/Ketu
gate as the automated quality filter** (~91% pass; catches mis-reads and source misprints)
→ score through `worked_chart_validate` against the pre-registered verdict map. The
`raman-chart-extractor` subagent did not engage; `general-purpose` did. Every dropped chart
and every soft/unmappable verdict is logged — no silent truncation.

## Integrity note
This supersedes the retracted "Vol 2 9th-house cross-house held-out" (that was the tuned
`h9` chapter). Every house here is confirmed absent from the tuned corpora (2/7/9/11 + ch IV
anchor).
