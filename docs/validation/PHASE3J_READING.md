# Phase 3J: how to read PHASE3J_RESULTS.md (hand-written)

Run 2026-10-24 under `PHASE3J_JAIMINI_PREREG.md` (7d9e4402), runner `5dff2454`. Engine: the Parashara engine's new
`chara_dasha` (13087d3f). It was encoded from BPHS-46 sl.155-167 after the rulings in `docs/parashara/CHARA_DASHA_RULINGS.md`
("find answers in ancient texts") and a doctrine review. It reproduces Raman's worked Example 20 table 12/12 and
the BPHS ledger rows.

The run used Phase 3's 13,034 risk sets, minus the 4,869 death events (excluded by the prereg), leaving 8,165.
All 34,711 charts were cast, and all four 500-draw gates pass (planted +0.030 recovered as +0.0302 and +0.0299).

## What was run, in plain words
Chara dasha is a clock of signs, not planets: each of the twelve signs rules a stretch of 1–12 years in turn. Raman
says a sign's period brings the events of the house that sign is, counted from the Lagna. So the question was this.
On the date of a marriage, a job change or an illness, is the running chara sign more often that matter's house
than it is for 10 matched people of the same age (E_rs)? And than it is across the person's own life (E_wp)?

## The headline
**Jaimini chara dasha does not time real events either.** There is no SIGNAL.

| test | coverage | E_rs (vs matched controls) | E_wp (vs own lifetime) | verdict |
|---|---|---|---|---|
| P_y: year-dated events | 0.114 | +0.001 (−0.007..+0.010) | +0.011 (+0.004..+0.020) | BOUNDED_NULL |
| P_d: day-dated events | 0.110 | −0.014 (−0.033..+0.007) | −0.004 (−0.023..+0.015) | UNDERPOWERED (TOST p 0.059) |

- **P_y**: the event date is no more often in the house's sign than it is for matched people. Any such effect is
  smaller than the 0.03 that would matter.
- **P_d** leans the wrong way (−0.014). Its interval just reaches −0.033, so it misses the bound by a hair. It is
  "underpowered", not support.
- **The P_y within-person +0.011 is not a dasha effect.** The placebo (the right chart, but the sequence started one
  sign ahead) gives the same within-person number, **+0.013 (+0.005..+0.021)**.
  - A shifted, wrong sequence cannot carry Raman's doctrine. So whatever lifts E_wp here is structural: event ages
    vs the 15–75 window, combined with 1–12-year periods. It is not timing.
  - On E_rs, real and placebo are also identical (+0.001 vs +0.001).
  - SIGNAL needs both E_rs and E_wp above 0 and the placebo beaten. None of the three holds.
- **Raman ayanamsa:** P_y −0.002, P_d −0.018. Same picture.
- **Wider activation** (the full art.159 reading: from the Lagna, the Atmakaraka or the Karakamsa; coverage 0.25):
  P_y +0.006 (−0.006..+0.018), P_d −0.022. Null.
- **Rodden AA:** P_y +0.002, P_d −0.002. Null.
- **S2 specificity:** +0.001 (P_y), −0.016 (P_d). The target house is not favoured over the others.
- **Families** (descriptive, 8 cells, not corrected for multiplicity):
  - P_y health/legal +0.052 (+0.011..+0.098);
  - P_y "other" −0.038;
  - P_d relationship −0.053.
  - Two point against the doctrine and one for it, about what chance gives across eight cells. This is not a finding.

## Why
One sign is the running sign for about a ninth of a life, so the base rate is low (~0.11) and a +0.03 excess would
be a large, easy effect to see. The design could see it (MDE80 0.011 for P_y), and it isn't there. The sign that
"is" the house is no more often running on the day the house's matter happens than on any other day.

## Where this leaves timing (all on the same events)
| system / level | E_rs | verdict |
|---|---|---|
| Vimshottari AD / MD (Phase 3, Parashara) | −0.010 / −0.003 | bounded null |
| Vimshottari AD / MD (Phase 3R, Raman engine) | +0.003 / −0.018 (wp −0.006) | null |
| Vimshottari PD (Phase 3P, Raman engine) | +0.009 / −0.005 | bounded null |
| Yogini AD / MD (Phase 3Y) | −0.010 / +0.001 | bounded null |
| **Jaimini chara MD (Phase 3J), year / day-dated** | **+0.001 / −0.014** | **bounded null / underpowered** |

**C1 was not read.** No primary is SIGNAL, so C1, C2, Gauquelin and Wikidata stay unread.

## Deviations from the prereg
None. Every CONVENTION and deferral (antardashas, death events, the activation rule from Raman art.159) was listed
in the prereg before any exposure was computed.
