# Held-out validation report — Vol 1 Ch. VII (Fourth House)

**Full-verdict held-out within-one: 4/9 (44%) across 4 charts — vs ~78% on the tuned
corpora. The engine overfits and over-rates the lord/kāraka systematically (mean Δ
+1.2).** This is the honest feedback the tuned corpora could not give.

## Method
Reconstruct each chart from Raman's printed Rāśi **and** Navāṁśa diagrams (read from the
PDF page scans via PyMuPDF — the djvu OCR flattens the squares unusably), run
`judge_house_doctrine`, map his verbatim verdict via the **pre-registered**
`verdict_grade_map.json`, compare on the 9-grade scale. Fully held-out (tuned set =
houses 2/7/9/11 + ch. IV anchor). Each square read with the fixed South-Indian sign key
(Pisces top-left, clockwise) and **every planet cross-checked by the (rāśi, navāṁśa)
reachability gate** — charts 64/70/71 passed all 9; chart 69's navāṁśa Mars was
unreadable so it is scored rāśi-axis. Post Phase 2.4.

## Results (charts 64, 70, 71 full-verdict; 69 rāśi-axis)
| chart | factor | engine | Raman | Δ |
|-------|--------|--------|-------|---|
| 64 | bhāva | fairly good | fairly strong | −1 |
| 64 | lord (Venus) | moderate | afflicted | **+2** |
| 64 | kāraka (Moon) | weak | afflicted | +1 |
| 69 | bhāva (rāśi) | (within-one) | moderately good | ≤1 |
| 70 | bhāva | weak | moderately good | **−2** |
| 70 | lord (Moon) | moderately good | afflicted | **+3** |
| 70 | kāraka (Moon) | moderately good | afflicted | **+3** |
| 71 | bhāva | fairly strong | fairly strong | (≤1) |
| 71 | kāraka (Moon) | moderately good | afflicted | **+3** |

exact 0/9, within-one 4/9 (44%); per-factor within-one: bhāva 3/4, lord 0/2, kāraka 1/3.

## The dominant finding — the kāraka/lord is over-rated
Raman repeatedly grades the Matrukāraka Moon **afflicted**; the engine says **moderately
good** (ch70 +3, ch71 +3), and the lord similarly (ch64 +2, ch70 +3). Two mechanisms:
1. **Dusthāna lordship** (ch64 kāraka, Moon owns the 6th) — addressed by **Phase 2.4**,
   which moved it to within-one (+1) once the real Navāṁśa is included.
2. **Non-dusthāna affliction the engine under-weighs** (ch70/ch71): the Moon conjoins
   Rahu / sits with malefics, which Raman treats as heavy affliction of the kāraka, but
   the engine's kendra-placement credit and optimistic cross-varga blend keep it
   "moderately good". This is the **positive-saturation / kendra-over-credit frontier**
   (v2) meeting the kāraka — the next candidate after 2.4.

Secondary: **clean/empty house under-scored** (ch70 bhāva −2), already ledger-flagged.

## Method validation
The Navāṁśa reads are trustworthy: all three full charts passed the reachability gate
(a mis-read almost always yields an impossible rāśi→navāṁśa pair). Full-verdict differs
from rāśi-axis (ch64 kāraka +3 rāśi → +1 full), confirming the Navāṁśa carries real
signal — so full-verdict is the honest test.

## Caveats & next
- N=9 verdict rows / 4 charts — a seed. Direction is consistent across the pilot, the
  rāśi-axis pass, and the tuned-corpus audit.
- Scale: the extraction is mechanical now (crop each square, fixed-sign key, gate-check);
  chart 69's Mars needs a cleaner re-crop.
- Engine: after 2.4, the standing gap is the **kāraka over-credit** (kendra placement +
  optimistic blend vs Raman's affliction) — a Phase-2.5 candidate, but it is the v2
  positive-saturation frontier and should be approached as a structural change.
- These rows are the disjoint **test set** for Phase B (ML weight-fitting).
