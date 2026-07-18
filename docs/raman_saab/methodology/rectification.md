# Birth-Time Rectification & Time Discovery — methodology

Module: `app/raman_saab/rectification/` · CLI: `py -3.12 -m tools.raman_saab.rectify` ·
Tests: `tests/raman_saab/rectification/` · Golden: `tests/fixtures/rect_case_01.json`

## Doctrine basis (every layer cited)

Raman's own stated method is the module's PRIMARY channel: **"birth times can be
rectified only by men of experience by a consideration of pronounced life incidents"**
(HPA ch.12, *On Birth Verification and Rectification*). He demonstrates it on his own
rectified nativities — Goethe (NH:4051-4080: three biographical facts fix the lagna),
H. G. Wells (NH:6683: "the application of rectification rules" + life incidents), Ford,
Pius XII, Eisenhower. The event→period machinery is his **Time-of-Fructification**
doctrine, systematic for all 12 houses (significator set = lord / aspecters / occupants
/ aspecters-and-associates-of-lord / lord-from-Moon / karaka; HTJAH-I:1583-1596 et al.),
with the **par-excellence** grade when Dasha AND Bhukti lords both time the house
(HTJAH-II:680-694). Event-type karaka lists: AFB ch.9-10 (marriage AFB-9:98, children
AFB-9:142, the per-lord Dasa menu AFB-10:449-476). The HPA ch.12 arithmetic rules
(R1-R3) are encoded as a SECONDARY capped channel — Raman himself subordinates them.
Relative-death events rotate the maraka apparatus to the relative's frame per Raman's
worked usage (HTJAH-I:4479-4483). Deferred to v2 (cited): the pre-natal epoch
(HPA ch.12:38-60; BPHS vol1 ch.4 Gulika/Adhana as corroboration) and the Prasna
fallback for wholly-unknown times (HPA ch.28).

## Method

1. **Candidate space** = ayanamsa {raman, lahiri} × birth-time **equivalence classes**.
   Chart judgment is piecewise-constant in time; an adaptive probe walks the window and
   bisects every boundary (lagna, navamsa-lagna, Moon pada, planet cusps, bhava sandhi,
   per-event dasha-chain flips) to ±5 s. Dual-ayanamsa search is mandatory — the
   raman↔lahiri Moon shift moves every dasha boundary ~2 years.
2. **Two chart tiers**: a light positions-only cast (~10 swisseph calls) scores all
   events; the expensive full cast (Shadbala) runs only for the natal-fact channel on
   the top-K. A tier guard makes a light chart reaching `judge_house` a hard error.
3. **Scoring channels** (subtotals always visible): A — period-lord fit at MD/AD/PD
   (W_AD 1.5 > W_MD 1.0 > W_PD 0.75) against the fructification timer union; B —
   **house activation** (`active_houses` grade: par_excellence +1.0 / limited +0.5 /
   absent penalized), with the full lit-house panel displayed per event; natal facts —
   `judge_house` verdict agreement (+1/0/−1); arithmetic — HPA ch.12 R1-R3, capped 0.65.
4. **Resolution honesty, enforced**: a dasha level is *scorable* only if one period of
   that level covers the event's whole stated-precision interval (a year-grade event
   can never claim pratyantar evidence); the winner is always reported as a **class
   interval**, never a point time; the resolution statement is computed from the
   evidence actually present.
5. **Orthogonality + the next question**: per-event score spread across candidates
   separates discriminators from flat evidence; identical candidate-orderings flag
   correlated pairs ("one witness"). The suggester ranks unsupplied event types by the
   Jaccard distance of their Bhukti-level match timelines across leading candidates,
   and surfaces natal-fact questions on which the two ayanamsas' verdicts sharply
   disagree — the module autonomously reproduces the worked session's "mother" move.

## Validation

`rect_case_01` (anonymized real nativity, five dated events + one natal fact): the
module autonomously reproduces the interactive session's conclusion — the raman class
containing the stated time ranks #1 (+2.0 over lahiri's best), driven by the 2024
childbirth (Jupiter putrakaraka Bhukti) and the 2026 career_change (Mercury MD opening,
Me/Me/Me par-excellence); the Venus-natured pair is flagged correlated; persistence
round-trips reproduce the ranking. Pratyantar arithmetic is pinned to hand-computed
session values. The doctrine gate (bphs-doctrine-reviewer) reviewed the event taxonomy
(10/17 VERIFIED, 7 amended per review, 0 refuted) and the AFB registry admission
(in-scope; out-of-scope-chapter firewall pinned by test).

## Limits (v1, by design)

Event types outside the taxonomy are hard errors (no free-text mapping); minute-level
claims require day-grade events; correlated evidence discounts confidence rather than
inflating it; the winning ayanamsa is an output with a stated margin, never a default.
