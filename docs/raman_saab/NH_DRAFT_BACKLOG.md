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

This **empirically confirms `DOCTRINE_ROADMAP.md`**: H10 is the thinnest house.

### UPDATE (2026-07-24): H10.C.61 shipped; the career gap is confirmed B1 (not a clean catalogue)

A diagnostic scan showed the Track-B career misses are largely a **no-Shadbala artifact** (strength
pillars None -> the career verdict abstains), and that **no placement signature separates favourable
from afflicted careers** — a blanket "raja yoga -> favourable" over-fires (Hitler/Tilak/Gandhi have
raja yogas but afflicted careers). So the career gap is confirmed **B1 comparative-weighing**, NOT a
clean sign-by-sign catalogue. The ONE clean, over-fire-free discriminator — the 10th influenced by an
**undebilitated benefic AND free of any malefic occupation/aspect** (holds 7/0/0 on the golden career
charts) — was encoded as **H10.C.61** (HTJAH-II:10181/11064/3232; fires without Shadbala, reaches
Track-B; bphs-doctrine-reviewer VALIDATED/KEEP). It closed **3 career misses** (chart_19/52/61) with
zero regression. The **remaining ~8 career misses are B1** (raja lifts *unless* the 10th is afflicted;
the benefic-predominance weighing Raman uses for Nehru's malefic-touched-but-favourable 10th) — the
tuner-gated verdict-path track, not clause work.

## Second cluster: H4 mother / education (7 misses)

`children` (5), `education` (4), `mother` (3) dominate after career. Several read
insufficient-evidence (chart_18/23/31/49 H4). This corroborates the roadmap's **UNIMPLEMENTED H4
mother-from-Moon frame** (`significations.py:218` declares `alternate_frame_core="Moon"` but
`house_04_sukha/` has zero frame rules) and the thin H4 alternate-signification coverage.

### UPDATE (2026-07-24): H4 has NO clean placement discriminator — it is a karaka-frame cluster

Unlike H10 career (one clean B+/M- win -> H10.C.61), a full diagnostic found **no** clean,
non-over-firing, n>=2 placement rule for H4 mother or education. Every candidate over-fires on a
CONFIRMED-favourable chart:
- **B+/M- 4th** (the H10.C.61 pattern): does not separate — chart_74 (mixed) is B+/M+; favourable
  mothers span B+/M+, B-/M+.
- **Papakartari on the 4th**: over-fires — a confirmed favourable education (h4_03) has it, and a
  favourable mother (chart_31) has it (mother is judged from the Moon, not the 4th house).
- **4th-lord in a dusthana**: over-fires — chart_67 (favourable happiness) has the 4th lord in the 8th.
- **Mercury (Vidyakaraka) affliction** for education: the only clean signal is a *debilitated*
  Mercury (chart_18 afflicted), but that is n=1 — below the anti-overfit threshold; malefic
  conjunction/aspect counts do NOT separate (favourable h4_04/chart_70 carry 2 malefic aspects).

**Conclusion:** the H4 misses need the KARAKA FRAME — the **Moon-as-Matrukaraka** reading for the
mother (the roadmap's unimplemented mother-from-Moon frame: chart_31 favourable via a well-disposed
Matrukaraka, chart_23/73 afflicted via Moon affliction) and the **Mercury-Vidyakaraka + 4th-lord**
reading for education — not a single placement clause. That is a Tier-2 frame-encoding effort, not a
clean one-rule win; it is deferred rather than forced (no over-firing/n=1 rule shipped).

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
