# Phase 3Y: how to read PHASE3Y_RESULTS.md (hand-written)

Run 2026-10-21 under `PHASE3Y_YOGINI_PREREG.md` (c4c5f710), runner `f2d0a750`. Parashara engine unchanged.
The Yogini MDs come from `yogini_dasha.timeline` (BPHS-46:199), with the 36-year cycle repeated. The ADs
come from `bhukti_timeline` (BPHS-46:110). Activation is Phase 3's own instrument with the Yogini lords put
in place of the Vimshottari ones. The run used the same 13,034 risk sets as Phase 3 (2,365 day-dated → AD
level, 10,669 year-dated → MD level), and all 38,329 charts it needed were cast. All four 500-draw gates pass:
the planted +0.030 came back as +0.0312 (AD) and +0.0301 (MD).

## What was run, in plain words
Yogini dasha is a second, shorter clock: 8 periods of 1–8 years, 36 years in all, then it starts again.
The question was the same one as before. On the day something happens in a person's life, are they more
often inside a Yogini period whose lords "activate" the house for that matter than other people of the
same age? It was asked two ways: against 10 matched people (E_rs), and against the same person's own
lifetime (E_wp).

## The headline
**Yogini dasha does not time real events either.** Both primaries are BOUNDED_NULL: any effect is smaller
than the 0.03 we decided in advance would matter. The within-person check agrees.

| test | coverage | E_rs (vs matched controls) | E_wp (vs own lifetime) | verdict |
|---|---|---|---|---|
| P1: Yogini AD period activates the house (tier ≥ 3) | 0.28 | −0.010 (−0.029..+0.010) | −0.004 (−0.021..+0.013) | BOUNDED_NULL |
| P2: Yogini MD lord activates the house | 0.49 | +0.001 (−0.010..+0.011) | +0.005 (−0.004..+0.014) | BOUNDED_NULL |

- **Placebo** (Yogini seeded one nakshatra ahead, so the right chart with the wrong sequence): P1
  +0.008, P2 −0.001. The real sequence does no better than the wrong one.
- **Raman ayanamsa:** P1 −0.007, P2 −0.003. Same picture.
- **Rodden AA** (best birth times): P1 −0.021 (−0.042..+0.002). The precision prediction ("a real AD
  effect is stronger where birth times are best") goes the wrong way. Rodden A is +0.030 on only 511 events.
- **S2 specificity:** −0.013 (AD), −0.003 (MD). The target house is not favoured over the other houses.
- **S1 dose-response:** −0.037 log-odds per tier (p 0.018). Descriptive and not corrected for
  multiplicity, and it points the **opposite** way to Raman's ordering (par excellence is, if anything,
  slightly rarer at events). This is not support, and it is not a finding either. It sits beside a null primary.
- Families: none has an E_rs CI above 0 at either level.

## Why
The same reason as at every Vimshottari level. A Yogini MD lord bears on a given house about **half** of
all time (P2 coverage 0.49), so "the MD lord activates the house" is true on roughly every other date of
anyone's life. A shorter, different clock does not narrow what the significator sets mean. The event date
is never more often inside them than any other date.

## Where this leaves timing (all on the same events)
| system / level | E_rs | verdict |
|---|---|---|
| Phase 3: Vimshottari AD, Parashara inputs | −0.010 | bounded null |
| Phase 3: Vimshottari MD, Parashara inputs | −0.003 | bounded null |
| Phase 3R: Vimshottari AD, Raman engine | +0.003 | bounded null |
| Phase 3R: Vimshottari MD, Raman engine | −0.018 (within-person −0.006) | null within-person |
| Phase 3P: Vimshottari PD, Raman engine | +0.009 / −0.005 | bounded null |
| **Phase 3Y: Yogini AD, Parashara engine** | **−0.010** (wp −0.004) | **bounded null** |
| **Phase 3Y: Yogini MD, Parashara engine** | **+0.001** (wp +0.005) | **bounded null** |

The P1 numbers sit close to Phase 3's Vimshottari AD numbers (E −0.010, OR 0.951 in both). That is a
coincidence of two nulls on the same events. The coverages (0.28 vs 0.27), the CIs and the placebos all
differ, and the tests pin the store's Yogini periods to the engine's own Yogini timeline.

**C1 was not read.** Neither primary is SIGNAL, so by the prereg C1, C2, Gauquelin and Wikidata stay unread.

## Deviations from the prereg
None. One choice is stated in the prereg itself rather than made afterwards: the engine's one-cycle Yogini
timeline is repeated past age 36.
