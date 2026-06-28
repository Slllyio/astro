# D9 (Navamsa) Layer — engine-enhancement scope (2026-06-28)

## Motivation
The engine uses the navamsa only as a thin lord/karaka confirm-nudge (`_navamsa_status`
house_template.py:538-576) that can shift only a borderline `mixed` (`_navamsa_modulate`
:288-296). It never casts a D9 chart, never judges D9 houses, never reads a house's *occupant*
D9 dignity, and runs no neecha-bhanga in D9. BV Raman, by contrast, judged **every** house in the
navamsa and treated it as decisive — *"Every combination should be applied to the Rashi, Bhava and
Navamsha charts and then a conclusion drawn"* (HtJaH:979); rasi = promise, navamsa = fruit. The
Mainpuri test exposed the gap concretely: the engine reads H11 as "navamsa confirms" (via lord
Jupiter) while blind to its exalted occupant **Mercury being debilitated in D9** — the single most
important navamsa fact in that chart.

## Key finding: ~40% of the D9 layer is ALREADY scaffolded, switched off
House 1 alone carries **~14 cited navamsa-qualifier rules** (`H1.N.38–67`,
`house_01_lagna/navamsa_qualifiers.py`) written as `kind="descriptive"`, `condition=None` — they
never fire. The audit found **~37 of 50 D9 rule-records are descriptive** for the same reason: a
single predicate gap, **G13**. `InVargaHouseFrom`/`VargaDignity` (conditions.py:367-424) already
resolve `LORD_OF:n` for the **origin** (`_origin_varga_sign`) but not for the **subject** planet —
`evaluate` does a direct `chart.planets.get(self.planet)`, so the subject must be a static name, not
the chart-dependent "lord of house n". Closing G13 turns those ~10 House-1 D9 reversal rules
(`H1.N.39/41/43/45/47/49/50/53/64`) from dead stubs into live, cited rules.

## Phased plan (each phase gated: over-fire scan → bphs-doctrine-reviewer → zero-regression → human bump)

**D9-1 — Close the G13 subject-resolution gap. (foundation, LOW risk, HIGH value)**
Add `_resolve_subject(name, chart)` (symmetric to `_origin_varga_sign`): `"LORD_OF:n"` → the D1
lord of house n; else the name. Use it in `InVargaHouseFrom.evaluate`, `VargaDignity.evaluate`,
and `Vargottama`/`HasDignity` where a LORD_OF subject is needed. Re-point the ~10 House-1 stubs to
`evaluable` with their already-documented TODO conditions
(`InVargaHouseFrom("LORD_OF:1","LORD_OF:N",{6,8,12},"D9")`, `VargaDignity("LORD_OF:1","D9",{...})`).
Pure capability unlock — the doctrine + citations already exist. These are *qualifiers* (adverse-D9
demotes / favourable-D9 lifts of the existing self-verdict), so the risk is bounded; validate they
fire only where Raman intends.

**D9-2 — The remaining auxiliary predicate gaps (G13a–d).** A `lord-strength` predicate on dynamic
lords (#38/55/58), a comparative `StrongerThan/WeakerThan` (#52), `AspectsBetweenLords` (#66),
`NavamshaDispositorExaltInChara` (#65), and disambiguation of "adverse Navamsha" (#57/60/62). Each
unlocks more already-cited rules. Incremental.

**D9-3 — Replicate the lord-based D9 scaffold to houses 2–12.** Raman's uniform spoiler test —
"the Nth-house lord in the 6/8/12 from the navamsa lagna (or from the Nth lord) cancels the
promise" — applied per house, cited (HtJaH:8337 7th, :9650 5th, :10156 10th, :14203 8th). This is
his most-used D9 technique; the House-1 block is the template.

**D9-4 — Occupant D9 dignity (the Mercury gap). (MEDIUM risk)** Extend `_navamsa_status` (or add an
overlay) to also weigh the D9 dignity of a house's *strong occupants*, not only lord+karaka — via a
new `OccupantVargaDignity` condition. This is what catches "exalted-D1 Mercury debilitated-in-D9 in
the 11th." Changes the D9 signal → gate hard.

**D9-5 — Neecha-bhanga in D9. (MEDIUM)** Extend `bhangas.neecha_bhanga(planet, chart)` to accept a
`varga` so a D9-debilitated planet with cancellation (Mercury: dispositor Jupiter own + conjoined)
reads as **redeemed / rise-after-struggle**, not merely weak. Pairs with D9-4.

**D9-6 — The netting. (HIGH risk — B1-class, DEFER)** Today `_navamsa_modulate` only nudges a
borderline `mixed`. Raman *nets* rasi-promise × navamsa-fruit: a strong-D1/weak-D9 house is
tempered and a weak-D1/strong-D9 house redeemed **even when the rasi verdict is decisive**. Letting
D9 move a decisive favourable/afflicted is the biggest behavioural change and threatens the whole
208/241 ratchet — it must go through `tools/raman_saab/tune_thresholds.py` with a holdout-lock, the
same discipline B1 needs. Build only after D9-1..5 land.

**D9-7 — D9-lagna + karakamsa reading. (additive metadata, LOW risk)** A D9-lagna body/temperament
overlay + karakamsa profession/spirituality, emitted as metadata like the current overlays (the
engine already has `special_points.karakamsa` and the D9-lagna counting origin) — does not change
verdicts.

## Risk & sequencing
- **Safe foundation (do first):** D9-1 then D9-3 — activate + replicate the *cited* lord-based
  scaffold. Each gated zero-regression. Likely to **net-improve** alignment, because the goldens
  were judged by Raman *using* D9, so some current engine misses are D9-driven.
- **Medium:** D9-2, D9-4, D9-5 (auxiliary predicates, occupant dignity, D9 bhanga).
- **High-risk / deferred:** D9-6 (the netting — B1-class; the tuner, not a clause).
- **Additive:** D9-7.

## Honest assessment
Raman's most-used D9 technique (the lord-based dusthana-from-navamsa spoiler/booster) is **~40%
scaffolded and unlockable at low risk** (D9-1..3) — this is genuinely the best-value, lowest-risk
engine work currently on the table. The occupant-level + neecha-bhanga capabilities (D9-4/5) are
real new work but bounded. The Raman-grade *"navamsa vetoes the rasi"* netting (D9-6) is the hard,
high-risk piece and shares B1's calibration profile. So a faithful D9 layer is buildable
incrementally; only its final step is genuinely difficult.

## Validation
The 130/241 goldens are the test set: every phase must hold the ratchet at ≥ its current value with
zero real-error regression, pass `bphs-doctrine-reviewer`, and earn a human baseline bump — exactly
the pipeline that delivered the two-malefic, B2, and Theme-3 gates.
