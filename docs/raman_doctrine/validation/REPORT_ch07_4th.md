# Held-out validation report — Vol 1 Ch. VII (Fourth House)

**Status: pipeline proven end-to-end on a verified held-out chart. Scaling gated on
careful vision extraction (see Extraction below).**

## Method
Strength-from-signs (no ephemeris, no daśā): reconstruct the chart from Raman's printed
signs, run `judge_house_doctrine`, map his verbatim verdict via the **pre-registered**
`verdict_grade_map.json`, compare on the 9-grade scale. This chapter is fully held-out
(the tuned set is houses 2/7/9/11 + the ch. IV anchor).

## Extraction — the gold-set gate did its job
The archive.org **djvu OCR text is inadequate** for full-chart extraction: the
Rāśi/Navāṁśa square diagrams are flattened into unusable token soup (e.g. Chart 64's
diagram OCR'd as `Rabu erin Satum | Venus … Jee RASI SAn NAVAMSA`). The **page scans,
however, are perfectly legible** when rendered from the PDF (`PyMuPDF` at 3×). So the
extraction method is **vision-from-PDF**, not text. Even then, reading the South-Indian
fixed-sign square is meticulous — placing a planet in the wrong cell flips its sign — so
each chart must be cross-checked against Raman's prose (his aspect/hemming statements
pin placements independently). This is why the plan front-loaded a hand-verified gold set.

## Result — Chart 64 (born 8-8-1912, Aquarius Lagna), rāśi-axis
Rāśi cross-verified from the scan **and** Raman's prose (every placement internally
consistent: Venus hemmed between Sun-6th and Ketu-8th; Jupiter-10th 7th-aspects the
4th; Rahu/Ketu axis). Navāṁśa not yet extracted → **rāśi-axis verdict only**.

| factor | engine (rāśi-axis) | Raman | Δ |
|--------|--------------------|-------|---|
| bhāva (4th house) | fairly strong | fairly strong | **0 (exact)** |
| lord (Venus) | weak | afflicted | +1 (within-one) |
| kāraka (Moon) | moderately good | afflicted | **+3 (divergence)** |

- **Exact on the bhāva.** The engine independently reproduced Raman's "fairly strong"
  for the 4th house on a chart it has never seen.
- **The kāraka divergence is the finding.** Raman grades the Moon *afflicted* explicitly
  "because it owns the 6th" — a **dusthāna-lordship** affliction of the kāraka. The
  engine's kāraka assessment weighs the planet's dignity/aspects/conjunctions (Moon +
  Saturn) but not its functional-malefic status as a dusthāna lord, so it lands three
  grades high. This is a concrete, held-out doctrinal gap — the kind Phase-2's tuned
  corpora could not reveal — and a candidate feature for a future engine increment
  (kāraka/lord dusthāna-lordship penalty).

## Caveats
- N=1 (a seed, not a sample). Rāśi-axis only (Raman's verdict is holistic; the
  divergence may narrow or widen once the Navāṁśa is included).
- The kāraka phrase used is "definitely afflicted"; Raman's softer "considerable
  affliction" would be unmappable under the pre-registered map (excluded, not guessed).

## Next
Extract a hand-verified gold set (~10–15 charts) from this chapter via the
`raman-chart-extractor` on the PDF scans, including Navāṁśa (back-solved and
consistency-gated), then report full-verdict exact/within-one/per-factor. The
divergence catalog to date already flags the kāraka dusthāna-lordship gap for Phase 2.4.
