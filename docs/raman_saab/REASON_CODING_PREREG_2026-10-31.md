# Reason coding: what Raman uses that the engine's rules miss (pre-registration, 2026-10-31)

User decision 2026-10-31 ("Find what Raman uses that rules miss"). Follows the weighted-judge
finding (WEIGHTED_JUDGE_PREREG Addendum 1): the engine's fired rules barely inform Raman's
verdict (log-loss 0.786 vs 0.838 for class frequencies), so the deciding information must be
somewhere the rules do not reach. Descriptive study on the pool only (389 conclusions, 237
charts). No engine change. Hold-outs 4 and 5 are not read.

## Step 1. Code Raman's reasons, blind to the engine and to the gold label

For each chart, coders read Raman's passage and, for each listed matter, record every factor
Raman states as bearing on it:
`{type, detail, direction (+ or -), decisive (true if Raman says or clearly shows that it
settles the matter)}`. Coders do not see the gold verdict, the engine, or each other.

Factor types (fixed codebook):
1. lord_house: the matter's house lord by house placement (incl. dusthana / kendra / trikona)
2. lord_dignity: the lord's sign dignity (exalted, debilitated, own, friendly, inimical)
3. lord_association: the lord joined or aspected by benefics or malefics; combustion
4. occupants: planets in the house
5. house_aspects: aspects on the house
6. karaka: the karaka's placement, dignity or affliction
7. navamsa: any Navamsa or other divisional-chart factor
8. other_frame: reading from the Moon, from the karaka, or from another house as Lagna
9. hemming: papakartari / subhakartari / hemming between malefics or benefics
10. dusthana_lords: involvement of the 6th, 8th or 12th lords
11. named_yoga: a named yoga (Raja, Dhana, Kemadruma, Arishta, Parivartana, etc.)
12. nodes: Rahu or Ketu specifically
13. strength_number: Shadbala, Bhava Bala or Ashtakavarga figures
14. dasa_timing: running or coming dasa / bhukti, or transits
15. maraka_longevity: maraka or longevity reasoning
16. life_fact: a known event of the native cited as evidence ("he did lose his father")
17. general_maxim: a general principle not tied to a chart feature
18. other: anything else (free text)

## Step 2. Line up Raman's factors against the engine

For each conclusion, a separate matcher (who sees Raman's coded factors and the engine's
fired rules and ledger flags for that matter, but not the gold verdict or the engine's verdict)
marks each Raman factor **covered** (the engine fired a rule on, or its ledger records, that
same factor with the same direction), **opposed** (it records it with the opposite direction),
or **absent**.

## Step 3. Analysis (fixed now)

Per factor type: how often Raman cites it, how often as decisive, and its covered / opposed /
absent shares. Engine exact rate on conclusions whose decisive factor is covered vs absent vs
opposed. **Ranking of missing factors:** factor types ordered by the number of conclusions
where a decisive Raman factor is absent or opposed AND the engine's verdict is not exact.
The top of that list is what to encode next; each candidate then needs its own
pre-registration, and any test must be on data not used here (hold-outs 4 and 5, with the
user's say-so).

## Reliability

A random 20% of charts (`random.Random(20261031)`) is coded twice by an independent coder.
Reported: per-conclusion overlap of factor types (Jaccard), and agreement on which factor type
is decisive. If mean Jaccard is under 0.5, the ranking is reported as unreliable.

## Honesty notes

- Everything here is in-sample to the pool. It finds candidates; it does not measure gains.
- Raman's prose names reasons selectively; a factor he omits may still have weighed with him.
