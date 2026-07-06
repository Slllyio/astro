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

## Current baseline (post Phase 2.1)

| set | n | within-one | over>1 | under>1 |
|-----|---|-----------|--------|---------|
| anchor (ch. IV 12–14) | 8 | 8 (100%) | 0 | 0 |
| full corpus (h2,7,9,11) | 104 | 79 (76%) | 12 | 13 |

`over>1` (12) is the exaltation-over-credit signal Phase 2.2 targets:
`+1.6` exaltation reaches the verdict ceiling on its own, so an exalted-but-afflicted
factor reads high where Raman grades it low.

`tests/doctrine/test_audit_anchor.py` gates the anchor (8/8) and a corpus within-one
floor so a future scheme edit cannot silently regress the calibration.
