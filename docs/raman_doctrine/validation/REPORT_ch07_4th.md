# Held-out validation report — Vol 1 Ch. VII (Fourth House)

**Full-verdict held-out within-one: 6/12 (50%) across 5 charts — vs ~78% on the tuned
corpora. The engine overfits, with two systematic, opposite-signed biases: it
over-rates the lord/kāraka (mean Δ +1.5/+1.67) and under-rates clean houses (bhāva
mean Δ −0.6).** This is the honest feedback the tuned corpora could not give, and it is
the target Phase B (ML weight-fitting) exists to correct.

## Method
Reconstruct each chart from Raman's printed Rāśi **and** Navāṁśa diagrams (read from the
PDF page scans via PyMuPDF — the djvu OCR flattens the squares unusably), run
`judge_house_doctrine`, map his verbatim verdict via the **pre-registered**
`verdict_grade_map.json`, compare on the 9-grade scale. Fully held-out (tuned set =
houses 2/7/9/11 + ch. IV anchor). Each square read with the fixed South-Indian sign key
(Pisces top-left, clockwise) and **every planet cross-checked by the (rāśi, navāṁśa)
reachability gate** — charts 64/70/71/74 passed all 9; chart 69's navāṁśa Mars was
unreadable so it is scored rāśi-axis. Post Phase 2.5.

**Multi-kāraka.** Raman judges the 4th by several significators (Moon = Matrukāraka /
mother, Mars = Bhūmikāraka / property, Mercury = Vidyākāraka / education). Each `karaka`
row now names its planet and the harness assesses **that** planet, so a Moon verdict is
never scored against a Mars significator. (Here every kāraka row is the Matrukāraka Moon.)

## Results (charts 64, 70, 71, 74 full-verdict; 69 rāśi-axis)
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
| 74 | bhāva | weak | moderately good | **−2** |
| 74 | lord | moderately good | moderately good | **0** |
| 74 | kāraka (Moon) | moderately good | moderately good | **0** |

exact 2/12, within-one 6/12 (50%), mean Δ +0.667; per-factor within-one: bhāva 3/5
(mean −0.6), lord 1/3 (mean +1.67), kāraka 2/4 (mean +1.5).

## Two systematic biases, opposite-signed
### 1. The kāraka / lord is over-rated (mean Δ +1.5 / +1.67)
Raman repeatedly grades the Matrukāraka Moon **afflicted**; the engine says **moderately
good** (ch70 +3, ch71 +2) and the lord similarly (ch64 +2, ch70 +3). Two mechanisms:
1. **Dusthāna lordship** (ch64 kāraka, Moon owns the 6th) — addressed by **Phase 2.4**;
   it is now within-one (+1) once the real Navāṁśa is included.
2. **Non-dusthāna affliction the engine under-weighs** (ch70/ch71): the Moon conjoins
   Rahu / sits with malefics, which Raman treats as heavy affliction of the kāraka, but
   the engine's kendra-placement credit and optimistic cross-varga blend keep it
   "moderately good". This is the **positive-saturation / kendra-over-credit frontier**
   — a single strong Rāśi vector saturates the total before real Navāṁśa blemishes can
   pull it down. The remaining structural knob (Phase 2.6 candidate).

### 2. Clean / empty houses are under-scored (bhāva mean Δ −0.6)
`ch70 bhāva −2` and `ch74 bhāva −2`: Raman rates a 4th house free of malefic
intervention **moderately good**, but the engine treats a clean house as a zero-baseline
neutral rather than crediting structural purity. This recurs at larger N (both −2 charts
are bhāva rows) and is now the clearest second target — a **structural-purity lift** the
engine does not yet encode.

## What the widening changed
- **Multi-kāraka scoring** removed the significator-collision risk and, with the
  `verdict_grade_map.json` "blemish" extension (feebly/moderately/considerably blemished →
  moderately good / moderate / weak; unblemished → fairly strong), landed **ch74 lord and
  kāraka exactly (Δ 0)** — the first exact factor rows in the held-out set.
- Confirmed both biases persist at N=12 rather than being 4-chart noise: the report now
  gives Phase B two clean, opposite-signed targets instead of one.

## Method validation
The Navāṁśa reads are trustworthy: all four full charts passed the reachability gate (a
mis-read almost always yields an impossible rāśi→navāṁśa pair). Full-verdict differs from
rāśi-axis (ch64 kāraka +3 rāśi → +1 full), confirming the Navāṁśa carries real signal —
so full-verdict is the honest test.

## Caveats & next
- N=12 verdict rows / 5 charts — a seed, but direction is now consistent across the
  pilot, the rāśi-axis pass, the tuned-corpus audit, and this widening.
- Extraction is mechanical now (crop each square, fixed-sign key, gate-check);
  chart 69's Mars still needs a cleaner re-crop to promote it to full-verdict.
- Engine: the two standing structural gaps are (a) the **kāraka over-credit**
  (kendra + optimistic blend vs Raman's affliction) and (b) the **clean-house
  under-score** (no structural-purity lift) — both are v2 saturation/baseline frontiers,
  approached as structural changes, not weight tweaks.
- These 12 rows are the disjoint **test set** for Phase B (ML weight-fitting); the tuned
  corpora are the train set (the wall is fit-on-tuned / validate-on-held-out).
