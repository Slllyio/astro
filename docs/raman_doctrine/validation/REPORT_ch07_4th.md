# Held-out validation report — Vol 1 Ch. VII (Fourth House)

**Full-verdict held-out within-one: 7/18 (39%) across 7 charts — vs ~78% on the tuned
corpora.** Widening from 5→7 charts *sharpened* the diagnosis rather than just lowering
the number: the engine's misses now resolve into two systematic, opposite-signed and
mechanistically-named biases — it **under-scores benefic/clean bhāvas** (bhāva mean Δ
−1.57) and **over-rates the malefic-afflicted lord/kāraka** (kāraka mean Δ +1.83). These
are the targets the next structural increment (2.6) must hit.

## Method
Reconstruct each chart from Raman's printed Rāśi **and** Navāṁśa diagrams (read from the
PDF page scans via PyMuPDF — djvu OCR flattens the squares unusably), run
`judge_house_doctrine`, map his verbatim verdict via the **pre-registered**
`verdict_grade_map.json`, compare on the 9-grade scale. Fully held-out (tuned set =
houses 2/7/9/11 + ch. IV anchor). Each square read with the fixed South-Indian sign key
(Pisces top-left, clockwise), Rāhu/Ketu forced opposite, and **every planet cross-checked
by the (rāśi, navāṁśa) reachability gate** — charts 64/70/71/72/73/74 pass all 9; chart
69's navāṁśa Mars is unreadable so it is scored rāśi-axis. Post Phase 2.5.

**Multi-kāraka.** Each `karaka` row names its significator and the harness assesses that
planet. All seven charts here are Matrukāraka (Moon = mother) cases; the remaining Ch VII
charts (76–81) are the **Vidyā/education** sub-section, whose verdicts describe
educational outcomes rather than 9-grade strength — excluded as un-gradable (see below).

## Results (64, 70, 71, 72, 73, 74 full-verdict; 69 rāśi-axis)
| chart | factor | engine | Raman | Δ |
|-------|--------|--------|-------|---|
| 64 | bhāva | fairly good | fairly strong | −1 |
| 64 | lord (Venus) | moderate | afflicted | **+2** |
| 64 | kāraka (Moon) | weak | afflicted | +1 |
| 69 | bhāva (rāśi) | fairly good | moderately good | +1 |
| 70 | bhāva | weak | moderately good | **−2** |
| 70 | lord (Moon) | moderately good | afflicted | **+3** |
| 70 | kāraka (Moon) | moderately good | afflicted | **+3** |
| 71 | bhāva | fairly powerful | fairly strong | +1 |
| 71 | kāraka (Moon) | moderate | afflicted | **+2** |
| 72 | bhāva | weak | fairly strong | **−4** |
| 72 | lord (Saturn) | afflicted | afflicted | **0** |
| 72 | kāraka (Moon) | moderately good | afflicted | **+3** |
| 73 | bhāva | moderate | fairly powerful | **−4** |
| 73 | lord (Moon) | fairly good | moderate | **+2** |
| 73 | kāraka (Moon) | fairly good | moderate | **+2** |
| 74 | bhāva | weak | moderately good | **−2** |
| 74 | lord | moderately good | moderately good | **0** |
| 74 | kāraka (Moon) | moderately good | moderately good | **0** |

exact 3/18, within-one 7/18 (39%), mean Δ +0.389; per-factor within-one: bhāva 3/7
(mean −1.57), lord 2/5 (mean +1.4), kāraka 2/6 (mean +1.83).

## Two systematic, opposite-signed biases (the 2.6 targets)
### A. Benefic / clean bhāvas are under-scored (bhāva mean Δ −1.57)
The widening made this the dominant miss, and split it into three named mechanisms:
1. **Natural-benefic occupant penalized as a functional malefic** — ch72 (−4) and ch74
   (−2). Venus occupies the 4th; Raman calls it *unblemished* / *feebly blemished*
   ("natural benefic Venus"), but the engine's `_planet_nature` flags Venus a **functional
   malefic** (lord of 7/12 for Scorpio; 3/8 for Pisces) and drives the occupant −0.70. A
   natural benefic that is only functionally malefic blemishes far less than a natural
   malefic — a distinction Raman applies explicitly and the engine does not.
2. **Debilitated / neechabhanga-rescued aspect under-credited** — ch73 (−4). The 4th is
   aspected by a debilitated Jupiter and a Mercury that has neechabhanga; Raman reads the
   cancellation as strength ("fairly powerful"), the engine does not credit it.
3. **Clean / empty house under-scored** — ch70 (−2): a papakartari-hemmed but
   benefic-aspected empty 4th, which Raman still grades *moderately strong*.

Crucially, the tuned "weak" bhāvas that a naive floor would break (h2/42, h7/1, h7/15)
are all blemished by **natural malefics** — so a natural-benefic-scoped softening (A.1)
leaves them untouched. The widening is what raised A.1 from a 1-chart knife-edge to a
2-chart, tuned-corpus-safe signal.

### B. The malefic-afflicted lord / kāraka is over-rated (kāraka mean Δ +1.83)
~6 data points: ch70 lord/kāraka +3, ch72 kāraka +3, ch64 lord +2, ch71 kāraka +2,
ch73 lord/kāraka +2. One mechanism — a kendra placement (+1.2) plus a strong dignity
(exaltation/vargottama) offsets *stacked malefic aspects/conjunctions*, where Raman grades
the planet "afflicted". This is exactly what Phase B's optimizer independently attacked
(it lowered `pos_knee` and `kendra_trikona`). Note the engine gets *clear* afflictions
right: ch72 lord (Saturn neecha + papakartari) is graded **afflicted, exactly** — the
over-credit is specific to a positively-placed planet that is *also* heavily aspected.

## Method validation
All six full charts pass the reachability gate; Rāhu/Ketu enforced opposite; key
placements cross-checked against Raman's prose (e.g. ch72 Lagna Scorpio ⇒ 4th Aquarius,
Saturn neecha in the 6th). Chart 74's diagram was independently re-confirmed off a second
page scan. Chart 76 was **dropped**: its Navāṁśa forces Venus→Libra, unreachable from the
Rāśi read — an internal inconsistency the gate rightly rejects rather than guess.

## Caveats & next
- N=18 rows / 7 charts. Ch VII's remaining mother-charts are exhausted; charts 76–81 are
  the Vidyā/education sub-section with outcome-based (non-9-grade) verdicts, so they are
  not clean strength labels — cross-house diversity (a Vol 2 chapter) is the better path
  to reach ~30 rows.
- Engine: 2.6 now has two well-supported targets — **(A.1) natural-benefic functional-
  malefic bhāva softening** (2 clean held-out examples, tuned-corpus-safe) and **(B) the
  kāraka over-credit** (~6 examples, corroborated by Phase B). Both remain gated by the
  anchor + audit checks.
- These 18 rows are the disjoint **test set** for Phase B (ML weight-fitting).
