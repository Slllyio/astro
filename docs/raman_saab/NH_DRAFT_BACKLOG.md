# NH corpus-expansion engine-gap backlog (2026-07-24)

The Notable Horoscopes corpus expansion (28 charts added Track-B from Raman's own printed
positions; 41 verdicts CONFIRMED where the engine already agreed with Raman) left **44 verdicts as
DRAFT** — faithful Raman readings the engine *misses*. Per project discipline these are **not
confirmed** (that would pad the accuracy floor down for zero engine benefit); they are recorded here
as the prioritized engine-gap list. Confirming any of them is gated on first building the mechanism
that closes the gap (cited fix → bphs-doctrine-reviewer → zero-regression → re-base).

## The dominant finding: H10 career is the thinnest house (11 of 44 misses)

The single biggest cluster is **H10 career** — 11 misses, split between:
- **insufficient-evidence** (the engine emits *no* verdict): chart_31 (Shaw, "literary greatness"),
  chart_52, chart_58 (Hitler's collapse), chart_59 (Nehru, "idol of India"). Multiple famous
  people's careers produce no decisive H10 verdict.
- **directional** (wrong pole): chart_30 (Tilak, afflicted vs engine-favourable), chart_41 (Gandhi,
  favourable vs engine-afflicted — Rahu-in-10th "good work"), chart_64 (afflicted vs favourable),
  chart_21/49/76 (mixed vs the engine's pole).

This **empirically confirms `DOCTRINE_ROADMAP.md`**: H10 is the thinnest house because the ~460-line
HTJAH-II:10249-10800 career-by-sign / profession-by-navamsa catalogue
(`rule_sets/house_10_karma/combinations.py`) is unencoded. **Encoding it is the single highest-value
next lever** — it would close ~11 misses at once.

## Second cluster: H4 mother / education (7 misses)

`children` (5), `education` (4), `mother` (3) dominate after career. Several read
insufficient-evidence (chart_18/23/31/49 H4). This corroborates the roadmap's **UNIMPLEMENTED H4
mother-from-Moon frame** (`significations.py:218` declares `alternate_frame_core="Moon"` but
`house_04_sukha/` has zero frame rules) and the thin H4 alternate-signification coverage.

## Full miss tally by signification

| sig | misses | | sig | misses |
|---|---|---|---|---|
| career (H10) | 11 | | wealth | 2 |
| children (H5) | 5 | | siblings | 2 |
| education (H4) | 4 | | self | 2 |
| mother (H4) | 3 | | longevity | 2 |
| marital_happiness (H7) | 3 | | father | 2 |
| fortune (H9) | 3 | | (moksha/intellect/happiness/dharma/death/courage) | 1 each |

## The two failure modes (same as the historic NH_GAP_ANALYSIS)

1. **Silent (insufficient-evidence)** — the house has no rule that fires decisively for that
   signification (career, mother, education). Fix: encode the missing catalogue / frame. Clean,
   additive, low-risk.
2. **Directional (wrong pole)** — the engine weighs the factors the opposite way to Raman
   (Gandhi's Rahu-in-10th; Tilak's afflicted-yoga career; the violent-end 8th-drekkana). Fix: the
   B1-class comparative-weighing work — HIGH-risk verdict-path (see `NH_GAP_ANALYSIS.md`).

## Priority order

1. **H10 career catalogue** (HTJAH-II:10249-10800) — closes ~11 misses; clean net-new (Tier 1).
2. **H4 mother-from-Moon frame + alternate-signification coverage** — closes ~7; Tier 2.
3. The directional/weighing misses (Gandhi, Tilak) — deferred to the B1 tuner track (Tier 3).

The 44 DRAFT rows live in `tests/fixtures/raman_goldens.jsonl` (`verdict_review="DRAFT"` on the
NH.chart_* records); each carries the verbatim Raman quote so the fix can be validated against his
text, never against engine self-output.
