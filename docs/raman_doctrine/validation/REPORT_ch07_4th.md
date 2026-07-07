# Held-out validation report — Vol 1 Ch. VII (Fourth House)

**Held-out within-one: 3/8 (37.5%) across 4 charts, rāśi-axis — vs ~78% on the tuned
corpora. The engine overfits its calibration data, and over-rates systematically
(mean Δ +1.1).** This is the honest feedback the tuned corpora could not give.

## Method
Strength-from-signs: reconstruct each chart from Raman's printed Rāśi diagram (read
from the PDF page scans via PyMuPDF; the djvu OCR flattens the squares unusably), run
`judge_house_doctrine`, map his verbatim verdict via the **pre-registered**
`verdict_grade_map.json`, compare on the 9-grade scale. Fully held-out (tuned set =
houses 2/7/9/11 + ch. IV anchor). **Rāśi-axis only** for now — the printed Navāṁśa is
extractable (South-Indian fixed-sign squares, cross-checked against Raman's prose) but
meticulous; deferred to keep this pass reliable. Charts 64, 69, 70, 71 (Rāśi
cross-verified against Raman's aspect/lordship prose; Rāhu/Ketu axis checked).

## Results
| chart | factor | engine (rāśi) | Raman | Δ |
|-------|--------|---------------|-------|---|
| 64 | bhāva | fairly strong | fairly strong | **0** |
| 64 | lord (Venus) | weak | afflicted | +1 |
| 64 | kāraka (Moon) | moderately good | afflicted | **+3** |
| 69 | bhāva | (within-one) | moderately good | ≤1 |
| 70 | bhāva | weak | moderately good | **−2** |
| 70 | lord (Moon) | moderate | afflicted | **+2** |
| 70 | kāraka (Moon) | moderate | afflicted | **+2** |
| 71 | bhāva | very strong | fairly strong | **+2** |

exact 1/8, within-one 3/8; per-factor within-one: bhāva 2/4, lord 1/2, kāraka 0/2.

## Findings — three concrete, recurring gaps
1. **Dusthāna-lordship affliction of the lord/kāraka is under-weighed (the dominant
   error).** ch64 kāraka (+3), ch70 lord (+2), ch70 kāraka (+2): Raman grades a
   lord/kāraka *afflicted* explicitly because it owns a dusthāna (the Moon owns the 6th),
   a functional-malefic status the engine's planet assessment does not carry. **3 of 8
   rows.** Strongest candidate for a future engine increment (Phase 2.4).
2. **Clean/empty house under-scored.** ch70 bhāva −2: an empty 4th (Cancer) that Raman
   calls "moderately strong" the engine rates "weak" — the clean-house gap the ledger
   already flagged, now confirmed held-out.
3. **Own-sign occupant over-credited.** ch71 bhāva +2: Venus in its own sign occupying
   the 4th drives the engine to "very strong" where Raman says "fairly strong" — the
   Phase-2.1 occupant-dignity credit **over-shoots** on a strong occupant. A held-out
   counter-signal to 2.1 worth weighing before adopting more dignity credit.

## Caveats
- N=8 verdict rows / 4 charts — a seed, not a population. Rāśi-axis only (Raman's
  verdict is holistic; the lord/kāraka gaps may narrow or widen with Navāṁśa).
- Direction is consistent with the Chart-64 pilot and the tuned-corpus audit, which is
  why the dusthāna-lordship finding is already actionable.

## Next
- Scale: extract more charts (Navāṁśa included) via the `raman-chart-extractor` on the
  scans — the method is mechanical now (crop RASI/NAVAMSA squares, read with the
  fixed-sign key, consistency-gate).
- Phase 2.4 candidate: a lord/kāraka **dusthāna-lordship** functional-malefic penalty,
  re-audited against the tuned corpora (anchor-preserved) before adoption.
- These held-out rows are also the disjoint **test set** for Phase B (ML weight-fitting).
