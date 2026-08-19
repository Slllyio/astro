# Phase D.0 — kāraka-ceiling separability diagnostic

**Question.** The kāraka/lord over-credit (increment 8 / "B") is not separable on the
engine's sign-only features. Phase D asks whether the sub-degree resolution we *already
carry* — `reconstruct.longitude_for` parks every planet at its **pada midpoint** (3°20′),
preserved on `chart.bundle.chart.planet_lons` — could break it via a **conjunction-orb**
feature. A conjunction-orb only bites on **same-sign conjunctions**; Raman's aspects are
whole-sign rāśi-drishti (degree-free by doctrine), so aspect-based affliction is orb-immune.
So: **where does the over-credit actually live — in tight-orb conjunctions (orb can help), or
in whole-sign aspects + the positive offset (orb cannot)?**

Measurement only, **no engine change**
(`app/medini/doctrine/validation/ceiling_diagnostic.py`). For every held-out lord/kāraka row
with **engine − Raman ≥ +2**, it decomposes the subject planet's malefic testimony — from the
LIVE engine's own `Finding`s — into same-sign conjunctions (with the pada-orb) vs whole-sign
aspects, and sums the positive offset (placement/dignity/vargottama) propping the planet up.

## Headline

**14 over-credit rows. Only 6 carry any same-sign malefic conjunction; 8 do not — 6 are
purely whole-sign-aspect afflictions (orb-immune) and 2 have no malefic testimony at all
(pure positive-offset over-credit). The two flagship cases (ch70 lord & kāraka, +3) are
aspect-only. The one factor common to nearly every row is the positive offset (kendra +1.2
recurs throughout).**

| classification | rows | orb-attackable? |
|---|--:|---|
| ≥1 same-sign malefic **conjunction** | 6 | maybe (see below) |
|  — of which **tight** (min orb ≤ 1 pada) | 4 | only via a *tighten* penalty |
|  — of which **wide** (4–5 padas) | 2 | no — a falloff moves them the WRONG way |
| **whole-sign aspect only** (no conjunction) | 6 | **no** (Raman's aspects are degree-free) |
| **offset only** (no malefic testimony) | 2 | **no** |

## The table

```
  ch src                    fac    subj     raman          engine          Δ #cj   orb°  orbP #asp   off
  69 heldout_ch12_8th       karaka Saturn   afflicted      fairly powerful +6   0    -     -      2  +1.2
  59 heldout_ch06_3rd       lord   Venus    weak           fairly powerful +5   1   3.33  1.00    0  +2.0
  70 heldout_ch07_4th       lord   Moon     afflicted      moderately good +3   0    -     -      2  +1.2
  70 heldout_ch07_4th       karaka Moon     afflicted      moderately good +3   0    -     -      2  +1.2
  72 heldout_ch07_4th       karaka Moon     afflicted      moderately good +3   2   3.33  1.00    0  +0.0
  98 heldout_ch08_5th       karaka Jupiter  weak           fairly good     +3   1   3.33  1.00    0  +2.4
 100 heldout_ch08_5th       lord   Mercury  afflicted      moderately good +3   1  16.67  5.00    1  +2.0
 103 heldout_ch08_5th       lord   Saturn   afflicted      moderately good +3   0    -     -      0  +1.2
  64 heldout_ch07_4th       lord   Venus    afflicted      moderate        +2   1  13.33  4.00    0  +1.2
  71 heldout_ch07_4th       karaka Moon     afflicted      moderate        +2   1   3.33  1.00    2  +3.2
  73 heldout_ch07_4th       lord   Moon     moderate       fairly good     +2   0    -     -      1  +1.2
  73 heldout_ch07_4th       karaka Moon     moderate       fairly good     +2   0    -     -      1  +1.2
  99 heldout_ch08_5th       lord   Mars     afflicted      moderate        +2   0    -     -      1  +2.0
 234 heldout_ch16_12th      karaka Venus    afflicted      moderate        +2   0    -     -      0  +0.8
```
`#cj` = same-sign malefic conjunctions · `orb°/orbP` = min conjunction gap in degrees/padas ·
`#asp` = whole-sign malefic aspects · `off` = positive offset (kendra/dignity/vargottama).

## Falsification check (passed)
The plan's own falsifier: **ch70's Moon must show 0 same-sign conjunctions** (it sits alone in
Capricorn, besieged only by Saturn's 3rd and Mars's 8th whole-sign aspects). The diagnostic
reports `#cj = 0, #asp = 2` for both ch70 rows — confirming the chart read and that the
decomposition is faithful. Four orbs were hand-verified against the raw longitudes (ch72
Mercury+Saturn at 1 pada; ch59 Sun at 1 pada with the benefic Mercury correctly excluded;
ch100 Sun at 5 padas; ch70 alone).

## Interpretation — a conjunction-orb feature has weak, ambiguous purchase

1. **It cannot touch 8 of 14 rows.** Six are whole-sign-aspect afflictions (orb-immune by
   Raman's own doctrine) and two have no malefic testimony at all. This includes the **two
   largest and most-cited cases** (ch70 lord & kāraka, +3), whose over-credit is Saturn/Mars
   *aspects* offset by a kendra Moon exalted in navāṁśa — a weight problem, not a resolution
   problem.

2. **For an over-credit, the fixable direction is a *tighten*, not a *falloff*.** To lower an
   engine verdict that is too high, an orb feature must *increase* the malefic penalty. A
   conjunction-orb *falloff* (discount wide same-sign pairs — the intuitive "orb" feature)
   would move the two **wide** cases (ch64 at 4 padas, ch100 at 5 padas) the **wrong way**,
   deepening their over-credit. So only a *tighten-when-close* rule is viable, and it reaches
   at most the **4 tight-orb rows** (ch59, ch72, ch98, ch71).

3. **That tighten rule directly threatens the anchor.** The anchor's ceiling analogue (ch14,
   Sun kāraka → "moderate") is itself conjunction-based (2 malefic conjunctions), but is held
   **findings-only** in the repo, so its orb is unknown. If ch14's conjunctions are also tight
   (1 pada), a tight-orb penalty pushes the anchor below "moderate" and breaks the hard
   constraint. We cannot even test this without first extracting ch14's grid.

4. **The real common denominator is the positive offset, not the malefic side.** The kendra
   `+1.2` recurs in ~10 of 14 rows; ch71 (+3.2), ch98 (+2.4), ch59/ch100/ch99 (+2.0) are
   propped up by placement+dignity that the additive model lets fully offset the malefic
   testimony. This is exactly the `pos_knee` / `kendra_trikona` over-credit that **Phase B's
   optimizer independently attacked** and that increment 8 showed is not threshold-separable —
   a re-weighting question, not a degree question.

5. **Even the "tight" signal is coarse and partly artificial.** Because the reconstruction
   pins each planet to its **pada midpoint**, a "1-pada orb" means only "adjacent padas," and a
   true same-pada pair (real orb anywhere 0–3°20′) collapses to 0. The orb axis has ≥3°20′ of
   built-in quantization noise — thin ground on which to justify an engine change that risks
   the anchor.

## Conclusion & recommended checkpoint decision

**Do not build the conjunction-orb feature (D.1) as the ceiling fix.** The diagnostic upgrades
increment 8's negative result: *the kāraka/lord over-credit is not orb-separable at pada
resolution — it is dominated by whole-sign-aspect affliction and the positive kendra/dignity
offset, both degree-free. Its common driver is a weight question (Phase-B territory), not the
missing intra-sign resolution.* Pada-orb could, at best, nudge 4 of 14 cases, and only via a
tighten rule that endangers the anchor and rests on a ≥3°20′-quantized signal.

This is a **decision checkpoint** (per the approved plan, "decide together"). The honest
options, in the author's recommended order:

- **(a) Pivot off the ceiling.** Take the two cheap, high-certainty fronts instead: scale the
  daśā-timing corpus (Phase C at larger N) and/or build the outcome-classification track that
  reclaims the ~117 soft-verdict charts. The ceiling is now a well-characterised, documented
  limit.
- **(b) Attack the positive offset directly**, not via degrees: a *ceiling-specific*
  re-weighting study of `kendra_trikona` / `pos_knee` under the anchor + audit + held-out
  gates (a bounded extension of Phase B focused on these 14 rows). Higher risk of the same
  Phase-B plateau, but it targets the actual driver.
- **(c) Escalate to true ephemeris (deferred Phase D-full).** Only worthwhile if we later
  decide the 4 tight-conjunction cases are worth chasing with real (non-quantized) orbs — but
  it still cannot make the 8 aspect/offset rows orb-sensitive, so its ceiling upside is ≤4/14.

Measurement only; no engine change. Guarded by
`tests/doctrine/test_ceiling_diagnostic.py`. CI red remains the pre-existing
`forecast_routes`/`[5E-1]` baseline.
