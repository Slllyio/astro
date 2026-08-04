---
title: "D-7 (Sapthāṁśa) children layer — engine-enhancement scope"
kind: spec
topic: doctrine
measured: false
updated: 2026-07-23
words: 1422
tags: [raman-saab, spec, doctrine]
---
# D-7 (Sapthāṁśa) children layer — engine-enhancement scope (2026-07-22)

## Motivation

The engine casts all sixteen shodasavarga and reads each through the four-principle per-varga
judge (`judges/varga_judge.py`), but **only the navamsa (D9) feeds the verdict path** — via
`_navamsa_status` → `_navamsa_modulate`, which nudges a borderline `mixed` one step. Every
other division, including the Sapthāṁśa, is a **report-only** surface. Yet Raman reads the
Sapthāṁśa *specifically for progeny* — *"Saptamsa for children"* (HPA-11:198) — on the
principle that the rasi is the promise and the varga the fruit: *"Every combination should be
applied to the Rashi, Bhava and Navamsha charts and then a conclusion drawn"* (HtJaH:979). So a
chart's children verdict should be confirmed/tempered by its **own D-7 testimony**, not only by
the general navamsa.

This layer promotes the Sapthāṁśa to a real judging layer **for the H5 children/progeny matter
only**, the exact parallel of the D9 layer, with the same ratchet-preserving guardrail.

## What was already there

`judges/varga_judge.py` already computes a children-scoped confirms/weakens/neutral for the D-7
via the reviewer-validated four principles — but as a **report** (its docstring: *"VERDICT-
AUTHORITY INVARIANT: imported by NOTHING in the D1 verdict path"*, and *"re-review is MANDATORY
if any non-D9 varga_status ever feeds the verdict path"*). The children matter also already
carries a decisive verdict-path gate: `_fertility_gate` (Beeja/Kshetra sphuta test,
HTJAH-I:5517-5527). This layer slots the D-7 testimony **between** the yoga step and that
decisive sphuta gate.

## Design (mirrors the D9 mechanism)

- **`_saptamsa_status(lord, karaka, chart)`** (house_template.py) — a significators-in-the-varga
  read (mirroring `_navamsa_status`, distinct from the varga_judge report row which reads the
  D-7 *lagna* lord). Casts the D-7 (`cast_varga_chart(chart, 7)`, Track-B-safe) and reads the
  two children significators, the **5th lord** and Putrakāraka **Jupiter**:
  - *confirms*: a pillar is D-7-exalted, or in its own D-7 sign;
  - *weakens*: a pillar is D-7-debilitated, or in a 6/8/12 from the D-7 lagna;
  - *unknown*: neither pillar resolvable (sparse / Track-B) → safe no-op.
  - **The D1==D9 `vargottama` credit is deliberately EXCLUDED** (P-review fix): vargottama is a
    *navamsa* fact already weighed by `_navamsa_status`, so counting it here would double-use one
    datum across two varga layers and let a "D-7 confirm" rest on non-Sapthāṁśa evidence. The
    status is therefore purely D-7-native.
- **`_saptamsa_gate(chart, sig, verdict, lead, ctx)`** (house_template.py) — scoped to the H5
  children/progeny signification (the fertility-gate scope). Nudges **only a borderline
  `mixed`** one step (confirms→favourable, weakens→afflicted); a decisive verdict never shifts
  (the `_navamsa_modulate` discipline). Runs **after** yoga/floors, **before** `_fertility_gate`.
  The Putra-sphuta test outranks the casual D-7 in **both** directions: a both-barren denial
  overrides a confirming D-7 (enforced by `_fertility_gate` running last), and a **both-strong**
  affirmation is protected from a weakening D-7 (enforced **here** — the `weakens→afflicted` push
  is suppressed when both Beeja and Kshetra are strong, since the fertility gate only denies,
  never lifts; P-review fix for the authority-asymmetry flag). Always emits `("saptamsa", status)`
  report metadata.

## Doctrine basis

- D-7 *is* the children varga: HPA-11:195-201 (Raman's pointer *"Saptamsa for children"*);
  definition HPA-11:187-193 — already cited in `doctrine/varga_domains.py`.
- confirm/weaken model: the **same reviewer-validated four principles** documented in
  `varga_judge.py` (GBB-3:447-543 Saptavargaja dignity; HTJAH-I:1090-1096 / 9913-9914 /
  9849-9850 benefic/malefic occupancy; HPA-20:247-248 vargottama; the confirms/weakens model
  generalized from the proven D9 `_navamsa_status`).
- rasi = promise, varga = fruit: HtJaH:979.

## Guardrails (verdict-invariant by construction)

- H5 children/progeny scope only — no other house or matter can move;
- only a borderline `mixed` moves, one step; decisive verdicts architecturally frozen;
- runs before the decisive Beeja/Kshetra gate, so barren-sphuta denials are never overturned;
- the Tier-3 evidence snapshot pins no H5 house and excludes metadata, so it cannot drift.

## Validation (2026-07-22, post P-review)

- **Unit**: `tests/raman_saab/judges/test_saptamsa_status.py` (7) + `test_saptamsa_gate.py` (7)
  — green.
- **Over-fire / impact scan** (gate ON vs OFF across all 190 birth goldens, `judge_house(.,5)`,
  after the review fixes): D-7 status distribution neutral 84 / weakens 61 / confirms 45 (a
  *read*, not an over-firing rule; confirms fell / weakens rose vs the pre-fix run because the
  vargottama credit was removed). **Exactly 2 verdict moves**, both on a borderline `mixed`:
  - `h5_15` `mixed → favourable` (D-7 confirms) — **improves** toward Raman's recorded verdict,
    but that verdict is `verdict_review=DRAFT` → not asserted;
  - `h7_07` `mixed → afflicted` on the *children* matter of a chart that pins H7 (not H5) — no
    recorded-verdict conflict.
  - (`h6_03`, which moved before the fix, is now spared: it has both fertility sphutas strong, so
    the new both-strong guard correctly blocks the D-7 weakening — the fix doing real work.)
- **Ratchet UNCHANGED**: no CONFIRMED H5 verdict moves; no Tier-3 record pins H5; metadata is
  not snapshotted. Full run: **209/241 exact, 229/241 within-1** — `test_goldens.py` green
  (557 passed / 21 skipped). Fertility gate still authoritative
  (`test_h5_fertility_one_weak.py` green). `field_case_01` children now surfaces
  `saptamsa='neutral'`, verdict `afflicted` unchanged (the D-7 reports where doctrine says to
  look — Mars+Ketu on the Sapthāṁśa lagna — while the Beeja/Kshetra denial stays decisive).
- **bphs-doctrine-reviewer** (MANDATORY, per the varga_judge non-D9 clause): verdict **PARTIAL —
  KEEP with FLAG** (0 BUG, 0 REVERSAL). Claims A/D FAITHFUL, B FAITHFUL (label caveat), C/E
  PARTIAL (defensible-but-simplified). All three flags were addressed, not deferred:
  1. *(MEDIUM) sphuta authority asymmetry* — the fertility gate denies but never affirms, so a
     weakening D-7 could beat two strong sphutas → **fixed** (both-strong guard in the gate).
  2. *(LOW-MED) vargottama double-count* across D9/D-7 → **fixed** (vargottama excluded from the
     D-7 read).
  3. *(LOW) docstring over-claim* ("four-principle" / pillar-parity with varga_judge) → **fixed**
     (docstrings corrected).
  The reviewer noted the D-7 is a Raman *casual* pointer whose demonstrated children technique is
  navamsa-lagna + Beeja/Kshetra; the borderline-only, sphuta-outranked posture matches that
  casual weight (proportional, not overbroad).

## D7-4 Item 1 — occupant D-7 dignity — SHIPPED (2026-07-23)

The D-7 mirror of the D9-4/D9-6 "hollow/redeemed occupant" is now live, but only in its
**surgical** slice (narrower than the deferred bullet below):
- `_saptamsa_status(lord, karaka, chart, extra=())` now takes `extra` occupants, exactly like
  `_navamsa_status`; `_d7_hollow_redeemed_occupants(chart, lord, karaka)` selects **only** the
  5th-house occupants whose rashi↔D-7 dignity FLIPS (exalt-rashi/debil-D7 = hollow → weakens;
  debil-rashi/exalt-D7 = redeemed → confirms). The broad "all strong occupants" form is NOT
  used (it regressed borderline verdicts in D9-4). `_saptamsa_gate` wires it in.
- **Guardrail unchanged**: still borderline-only (moves a `mixed` H5 one step, never decisive;
  the both-strong-sphuta suppression stands). The borderline-gate discipline substitutes for the
  holdout tuner because the shipped slice is the de-risked flip-only subset.
- **Validation**: 19/19 D-7 unit tests green (5 new occupant tests in `test_saptamsa_status.py`);
  **golden ratchet UNCHANGED — 209/241 exact, 229/241 within-1** (`test_goldens.py`, 539 passed);
  `bphs-doctrine-reviewer` **PARTIAL / KEEP-WITH-FLAG** (0 BUG, 0 REVERSAL; Q2/Q3/Q4 FAITHFUL,
  Q1 PARTIAL = a principled analogical extension of a navamsa rule to the children varga, so it
  **inherits** the base D-7 layer's PARTIAL rather than upgrading it — Raman never casts a D-7).

## D7-4 Item 2 — child-seat malefic occupancy — SHIPPED (2026-07-23)

Judges the two D-7 child-seats — the D-7 lagna (house 1 = eldest-child seat) and the
5th-from-D-7-lagna (house 5 = continuity seat) — for **malefic occupancy**, the FIRST place
benefic/malefic occupancy feeds a varga *status* (it is report-only in `varga_judge` and absent
from `_navamsa_status`). `_d7_seat_occupancy(vc)` + `_saptamsa_status(..., include_seats=True)`.
- **WEAKEN-ONLY** (bphs-doctrine-reviewer decisive ruling): a malefic-afflicted child-seat
  tempers a borderline `mixed` H5 down; a benefic seat can NEVER lift it. Raman's progeny
  apparatus denies but never affirms — the malefic-in-5th map is malefic-only, and a benefic-lift
  would break the same asymmetry the fertility gate + Item-1 sphuta guard enforce. (This does NOT
  touch Item-1's redeemed-occupant confirm, which has a cited uplift rule — Grahaṇam Aṁśakam Balam.)
- **PER-SEAT** (reviewer Q3): each seat judged on its own occupants, so a benefic on the
  continuity seat (house 5) cannot cancel a malefic on the primary eldest seat (house 1).
- **ALL natural malefics** (reviewer Q4: Sun + nodes included — cruel-only does not transfer to
  children; Raman names the Sun and both nodes as 5th-house progeny afflictors).
- **Fires, correctly**: field_case_01 (father) D-7 lagna Leo carries Mars+Ketu → seat weakens,
  flipping the status neutral→weakens (matching the elder-daughter reading). His verdict stays
  decisively `afflicted`, so the borderline gate leaves it untouched.
- **Validation**: 26/26 D-7 unit tests green (6 new seat tests); **golden ratchet UNCHANGED —
  209/241 exact, 229/241 within-1** (`test_goldens.py`, 539 passed); `bphs-doctrine-reviewer`
  **PARTIAL / KEEP-WITH-FLAG** (0 BUG, 0 REVERSAL; the weaken-only + per-seat ruling was applied,
  not deferred).

## Deferred — D7-4 item 3 (HIGH risk, note only)

Still behind the holdout/threshold-tuner discipline:
- **netting a decisive verdict** — letting the D-7 temper/redeem a *decisive* children verdict
  (not merely a borderline `mixed`) — the biggest behavioural change; deferred until it can go
  through `tools/raman_saab/tune_thresholds.py` with a holdout lock, exactly as D9-6 / B1 require.
