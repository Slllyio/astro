# Held-out validation — Vol 2 Ch. XIII (Ninth House), cross-house extension

**Purpose:** widen the held-out set beyond the 4th house (Ch VII pilot) into a different
house, lord, and kāraka — the 9th house (father), 9th-lord Venus/Mercury, Pitrukāraka
**Sun** — to test whether the engine's two diagnosed biases are 4th-house-specific or
structural. **They are structural: both reappear in the 9th house.**

## Two headline findings
### 1. The two biases generalize across houses (the point of this extension)
Only 2 of the 9th-house rows carry a crisply-mappable verdict, but both land on the same
two biases the 4th house showed:
- **ch94 bhāva −4** — the 9th (Libra) holds a debilitated-but-neechabhanga Sun under a
  subhakartari yoga; Raman grades it *quite strong* (fairly strong), the engine *weak*.
  Identical to the Ch VII bhāva under-score (A): a rescued/benefic-hemmed occupant that
  Raman credits and the engine penalizes.
- **ch93 lord +2** — the 9th-lord Venus sits in a kendra (7th) but inimical, hemmed
  between malefics, afflicted by Mars; Raman *afflicted*, engine *moderate*. Identical to
  the Ch VII lord/kāraka over-credit (B): a kendra placement offsetting stacked malefic
  testimony.

So the bhāva-under-score and lord/kāraka-over-credit are **not artifacts of the 4th house
or the Moon kāraka** — the same engine mechanisms misfire on the 9th house, a Venus/Mercury
lord, and a Sun kāraka. This is the cross-house generalization evidence a single-chapter
set could not give.

### 2. Vol 2's strength verdicts are largely un-gradable (a scope finding)
**6 of 8 verdict rows were excluded as unmappable** by the pre-registered map. Vol 2's
9th-house verdicts are narrative, hedged, or collective rather than crisp 9-grade
strength words:
- ch92 — one collective verdict for all three factors: *"the 9th house, the 9th lord and
  kāraka Sun are well placed with slight afflictions"* (no per-factor strength grade).
- ch94 lord — *"strongly fortified"* (bare "strong", intentionally un-mapped).
- ch93/ch94 kāraka Sun — explicitly hedged (*"Saturn does not afflict in the strict
  sense"*, *"not very welcome but protected by subhakartari"*).

The map correctly refuses to guess these. The implication: **the crisp-verdict held-out
material is largely exhausted after Vol 1 Ch VII** — further growth of the *strength*-label
test set has diminishing returns, and closing the two biases should lean on the current
evidence (now cross-house-confirmed) rather than on more extraction.

## Method
Same pipeline as Ch VII (reconstruct from Raman's Rāśi+Navāṁśa sign diagrams via PyMuPDF,
reachability gate, pre-registered verdict map). Vol 2 PDF from archive.org item
`raman-how-to-judge-horoscope-2`. Chart 93 is the 8-8-1912 nativity (= Vol 1 ch64):
positions reused and prose-confirmed (Venus/Mars/Mercury in 7th Leo, Sun in 6th Cancer,
Jupiter Scorpio vargottama). Charts 92/94 extracted and gate-checked (9/9); ch92's Rāśi
house-shift resolved against Raman's prose (Lagna Libra ⇒ Sun cluster in the 4th=Capricorn,
9th=Gemini lord Mercury in the 3rd=Sagittarius).

## Pooled held-out (Ch VII 4th + Vol 2 9th)
`worked_chart_validate` now pools multiple corpora. Combined: **20 scored rows / 9 charts /
2 houses, within-one 7/20 (35%), mean Δ +0.25.** Per-factor: bhāva 3/8 (mean −1.88, three
−4 misses across both houses), lord 2/6 (+1.5), kāraka 2/6 (+1.83). The two biases dominate
the pooled divergence list unchanged.

## Next
- Engine 2.6 targets are now cross-house-confirmed: **(A) benefic/rescued-occupant bhāva
  under-score** and **(B) kendra-offsets-affliction lord/kāraka over-credit**. Both remain
  gated by the anchor + audit checks.
- Held-out *strength* labels are near-exhausted in crisp-verdict form; the 20-row,
  2-house set is the disjoint test bed for Phase B and for gating 2.6.
