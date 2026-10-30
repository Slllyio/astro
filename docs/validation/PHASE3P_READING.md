# Phase 3P: how to read PHASE3P_RESULTS.md (hand-written)

Run 2026-10-14 under `PHASE3P_PRATYANTAR_PREREG.md` (06139d16). Raman engine unchanged (engine
`pratyantars`, `timer_set` + aux houses, `maraka_set().primary`, Raman ayanamsa). The same 2,365
day-dated risk sets as Phases 3 / 3R; 18,619 charts cast. All four 500-draw gates pass (planted +0.030
recovered as +0.0301 / +0.0297).

## The headline
**Raman's pratyantar level does not time real events either.** Both primaries are BOUNDED_NULL, and the
within-person check (the event date vs the person's own lifetime, immune to the 3R chart-level artefact)
agrees.

| test | coverage | E_rs (vs matched controls) | E_wp (vs own lifetime) | verdict |
|---|---|---|---|---|
| P3a: the pratyantar lord activates the event's house | 0.54 | +0.009 (−0.010..+0.029) | +0.002 (−0.017..+0.019) | BOUNDED_NULL |
| P3b: MD + AD + PD lords all activate it | 0.24 | −0.005 (−0.022..+0.012) | −0.011 (−0.025..+0.002) | BOUNDED_NULL |

- **Placebo** (dasha seeded one nakshatra ahead): P3a −0.007, P3b −0.003. Real and placebo are
  indistinguishable.
- **S1 dose-response** over the number of activating levels (0–3): +0.017 log-odds per level (p 0.47).
  Having all three lords on the house is not more common at events than having none.
- **Lahiri frame:** P3a +0.009, P3b −0.007. Same picture.
- **Rodden AA** (best birth times, where a 2-month period is still resolvable): +0.015 (−0.009..+0.037),
  with within-person +0.001. Null.
- Families: own death P3a +0.028 (−0.001..+0.058) is the largest lean, but its within-person effect is
  +0.011 (−0.018..+0.039). It is one of 5 descriptive families, not multiplicity-corrected, and not a
  finding.

## Why the finest level cannot rescue timing
A pratyantar lord is one of the ~5–6 timer lords out of 9, so "PD lord activates" covers **54%** of all
time. Requiring all three lords to converge narrows that to 24%, and that is still null. Going finer in
time does not make the doctrine narrower in meaning: at every level the significator sets are broad,
and the event date is never more often inside them than any other date.

## Where this leaves timing (all on the same events)
| level / version | E | verdict |
|---|---|---|
| Phase 3: AD, Parashara inputs | −0.010 | bounded null |
| Phase 3: MD, Parashara inputs | −0.003 | bounded null |
| Phase 3R: AD, Raman engine | +0.003 | bounded null |
| Phase 3R: MD, Raman engine | −0.018 (chart selection; within-person −0.006) | null within-person |
| **Phase 3P: PD, Raman engine** | **+0.009 / −0.005** | **bounded null** |

C1 remains unread.
