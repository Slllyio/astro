# Does chart strength predict the AGE of an event?

Continuous, non-circular target. Chart index = summed `bhava_promise` of the relevant houses. Spearman ρ vs age with a chart-shuffle permutation (K=2000); strong/weak split at the index median.

| target | class | n | ρ(index,age) | z | p | mean age strong | mean age weak | gap | expectation |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| longevity | death | 2030 | **-0.011** | -0.48 | 0.6342 | 43.91 | 44.46 | -0.55 | higher strength → later death (ρ>0) |
| marriage_age | marriage | 1200 | **-0.060** ✶ | -2.08 | 0.0405 | 29.06 | 30.41 | -1.35 | higher 7th strength → earlier marriage (ρ<0) |

## Reading

- ρ significantly ≠ 0 ⇒ the chart's domain strength tracks *when* the event happens — a real, non-circular astrological signal.
- ρ ≈ 0 (within a tight permutation band) ⇒ a real null: this chart index does not time the event's age on this corpus.
- Longevity uses a died-already, notable-person sample — interpret within that selection.
