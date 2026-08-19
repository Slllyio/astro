# Held-out audit corpora for the HTJAH strength point-scheme

These corpora calibrate the house-strength point-scheme in
`app/medini/doctrine/domains/house_judgment.py` against B. V. Raman's own worked
verdicts in *How to Judge a Horoscope*. They were scratchpad-only through the
twelve-house walk and the v1/v2 consolidation; they are committed here so they
survive container resets and gate future verdict changes (Phase 2).

## Layout

- `corpora/htjah_anchor_calibration.json` — the **ch. IV Charts 12–14 anchor**
  (house-1 vargottama calibration). A fixed invariant: must stay **8/8 within-one**.
- `corpora/htjah_h{2,7,9,11}_calibration.json` — per-house calibration corpora
  (2 wealth, 7 marriage, 9 fortune, 11 gains). 104 rows total.
- `builders/build_h{2,7,9,11}_corpus.py` — the row provenance: each row hand-encodes
  a Raman worked-chart factor as the assessor sees it (feature tokens), his verdict on
  the 9-grade scale, and a verbatim citation. Re-run to regenerate a corpus JSON.
- `validate_house.py` — the harness. Imports the **live** scheme (`_combine`,
  `_DIGNITY_W`, `_W`, `_verdict_label`), maps each row's tokens to live deltas, and
  reports how far each prediction lands from Raman.

## Running

```
PYTHONPATH=. python3 docs/raman_doctrine/audit/validate_house.py \
    docs/raman_doctrine/audit/corpora/htjah_h2_calibration.json \
    docs/raman_doctrine/audit/corpora/htjah_h7_calibration.json \
    docs/raman_doctrine/audit/corpora/htjah_h9_calibration.json \
    docs/raman_doctrine/audit/corpora/htjah_h11_calibration.json -v
```

`-v` prints every row that misses by more than one grade (the tuning signal). Holdout
rows are `chart_no % 3 == 0`; TRAIN/HOLDOUT/OVERALL are reported separately.

## Current baseline (post Phase 2.3)

| set | n | within-one | exact | over>1 | under>1 | mean |
|-----|---|-----------|-------|--------|---------|------|
| anchor (ch. IV 12–14) | 8 | 8 (100%) | 3 | 0 | 0 | −0.38 |
| full corpus (h2,7,9,11) | 104 | 81 (78%) | 52 (50%) | 10 | 13 | −0.02 |

Phase 2.2 (no-phantom-frame blend) raised within-one 79→81 and exact 44→52 while
leaving under>1 flat at 13 — an un-assessed varga no longer rescues an afflicted Rasi.

Phase 2.3 synced the **harness** to the engine's occupant dignity (2.1) and added
**bhāva-aspect dignity** (an exalted planet aspecting a house is credited like an
exalted companion). Within-one is unchanged (81), but the worst outlier collapses:
chart 40's 2nd bhāva (own Mars + neechabhaṅga Moon + exalted-Jupiter aspect) moves
from **d=−6 (weak) to d=−2 (fairly strong)**. It stops two grades short of Raman's
"very strong" only because the positive soft-cap holds the score near 1.0 — the
dignity *features* now fire correctly, and the residual is purely positive-cap
saturation.

That frontier now bounds the corpus on both sides: the `over>1` (10, stacked
positives just under the ceiling) and the tail of `under>1` (multi-positive bhāvas
Raman calls "very strong"). The cap cannot be both looser (to reach "very strong")
and tighter (to stop over-crediting "moderate"), so further movement needs a
structural change to how positives saturate — not more features.

`tests/doctrine/test_audit_anchor.py` gates the anchor (8/8) and the corpus
within-one floor (81) so a future scheme edit cannot silently regress the calibration.
