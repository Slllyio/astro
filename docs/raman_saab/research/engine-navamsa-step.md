---
title: "The Navamsa step: what it computes, what it cites, what it does to verdicts"
kind: analysis
topic: judge-mechanism
measured: true
updated: 2026-10-24
---
# The Navamsa step in the Raman engine

**Scope.** This audit covers how `navamsa_status` is computed, every place it changes a verdict,
whether the cited Raman text says what the code does, and what the step does to the golden pool
and the two hold-outs. It measures only. It recommends no tuning.

**Method.** Repo HEAD `0cb6058` (R2 is in it, from `57bdf66`). The working tree was clean. Each
row was scored through the harness path (`tests/raman_saab/test_goldens.py`: `build_chart`, then
`ht.judge_house`, then `_ordinal_distance`). For the pool that means CONFIRMED rows only. For the
hold-outs it means every row, as `tools/raman_saab/score_holdout.py` does. Counterfactuals swap
`house_template._decide` in memory for a wrapper. "Navamsa off" means `_decide` is run on the
ledger with `navamsa_status` forced to `"neutral"`. No file under `app/` or `tests/` was changed.
Scripts and the per-row dump are in
`/tmp/claude-0/-home-claude/0462ad3d-edef-5079-8a7a-8785976d2ea4/scratchpad/navamsa/`
(`measure.py`, `analyse.py`, `rows.json`).

The baseline matches the published figures. The pool scores **277/389 exact, 350 within one, 39
real errors**. HO1 scores 23/36, 28 within one, 8 real. HO2 at HEAD scores 58/134, 98 within one,
36 real. HO2 was 55/98/36 before R2 shipped.

---

## 1. How `navamsa_status` is computed, and where it acts

All line numbers are in `app/raman_saab/judges/house_template.py`.

### 1a. The status itself (`_navamsa_status`, :804-855; called at :1256)

```python
nav_lagna_sign = varga.navamsa_sign(chart.asc_lon)
for name in (lord, karaka, *extra):
    ...
    if p.vargottama:                                       confirms = True
    elif name in r.EXALTATION and nav == r.EXALTATION[name][0]: confirms = True
    elif SIGN_LORDS.get(nav) == name:                      confirms = True
    if name in r.DEBILITATION and nav == r.DEBILITATION[name][0]: weakens = True
    d9_house = ((nav - nav_lagna_sign) % 12) + 1
    if d9_house in _D9_WEAK_HOUSES:                        weakens = True   # {6, 8, 12}, :94
...
if confirms and not weakens: return "confirms"
if weakens and not confirms: return "weakens"
return "neutral"            # both, or neither   ("unknown" if no D9 data at all)
```

- **Which planets.** The status reads three kinds of planet:
  - The **bhava lord of the lead frame**. That is the lord counted from the Lagna, or from the
    Moon when the Moon-frame lord has the higher Shadbala (:2189-2200).
  - The signification's **natural karaka**.
  - The house's occupants in `extra` (:1236-1255). These are "hollow" occupants (exalted in
    the rasi, debilitated in the D9) and "redeemed" occupants (debilitated in the rasi, exalted
    in the D9). Both are rare.
- **Dignity tests.** "Confirms" means the planet is vargottama, or sits in its exaltation sign
  in the D9, or sits in its own sign in the D9. "Weakens" means it sits in its debilitation
  sign in the D9, or in the 6th, 8th or 12th **counted from the navamsa Lagna**.
- **What it does not read.** There is no neecha-bhanga in the D9 and no friendly or enemy
  sign. Nothing in the D9 about aspects or conjunctions is read. The house's D9 occupants are
  not read either. The status ignores **the dispositor of the lord**, and it does not ask
  whether the planet being tested is itself a dusthana lord.
- **How the pillars combine.** The status is any-confirm against any-weaken. One pillar that
  confirms while another weakens gives "neutral".
- **How often each value fires.** Across the 559 scored rows: neutral 286, confirms 141,
  weakens 132. Of the 132 "weakens", **80 come from the 6/8/12-from-navamsa-Lagna test alone**.
  The other 52 involve a D9 debilitation.

### 1b. Every place the status changes a verdict

| # | Where | What it does | Citation in code |
|---|---|---|---|
| 1 | **Clause-2 guard**, :604-608 | When both polarities fired and 2 or more pillars are strong, `favourable` is granted only if `L.navamsa_status != "weakens"` (and B1 is not set). Otherwise the row falls to `mixed`. | None to Raman. The comment (:579-591) calls the D9 "Raman's confirmation varga". The commit that added it (`1c7e0b6`, "Stage-3 calibration V2, ratchet 53/130 -> 62/130") justifies it by the golden-pool gain. `total.py:57` repeats this. |
| 2 | **`_navamsa_modulate`**, :481-519. It runs at the end of **every** `_decide` path: clause 1 (:546-547), clause 1.5 (:566), clause 2 (:611), clause 3 (:620) and clause 9 (:653). | Only a `mixed` moves. "confirms" turns it `favourable` and "weakens" turns it `afflicted`. Two exceptions: **P2**, :502-504 (no Shadbala pillars and both polarities fired, so nothing moves), and the **one-sided-rasi guard**, :513-518 (the D9 may not carry a one-sided row to the opposite pole). | HTJAH-I:979-980 and :975-978 (for P2 and the one-sided guard). |
| 3 | Clause-2 guard and modulate in sequence | A row the guard demotes (favourable to mixed) is **always** taken on to `afflicted` by `_navamsa_modulate`, because both polarities fired. So the guard is in effect a **favourable → afflicted** switch, never a favourable → mixed one. | as above |
| 4 | **B1 path**, :607 | B1 reads no navamsa. But a strong-pillar row that B1 blocks lands on `mixed`, and `_navamsa_modulate` then decides it. This happened on 5 scored rows. | HTJAH-I:3788 (for B1, not the D9) |
| 5 | `_marginal_karaka_gate`, :1830 | Re-calls `_decide`, so it inherits 1-4. | — |
| 6 | Degree, :778 and `borderline_shifted` | "confirms" is needed for a `strong` favourable degree. A navamsa shift marks the verdict `mild`. This is degree only and is not scored. | None |
| 7 | Report surfaces (`synthesis.py:234-239`, `detailed_report.py:1473/3664/6252`, `report_html.py:680`) | Display only. | — |

(`_saptamsa_gate`, :1984ff, is a parallel D7 step for H5 children with the same shape. It is
not the navamsa and is outside this audit.)

---

## 2. Do the citations say what the code does?

| Citation | Text in the book (checked in `data/knowledge_library/sources/`) | Says what the code does? |
|---|---|---|
| HTJAH-I:975-980 (`_navamsa_modulate` docstring) | "The Navamsha is also equally important… It is the pivot on which the horoscope revolves… Every combination mentioned should be applied to the Rashi, Bhava and Navamsha charts and then a conclusion drawn." The quote is verbatim and the line numbers match. | **Partly.** It supports weighing the D9 together with the rasi, which is how the code uses it for P2 and the one-sided guard (both are limits on the D9). It does **not** support the modulation itself. Raman says to apply *every combination* to the navamsa chart, which means judging the house again in the D9. The code instead uses a dignity proxy on two planets and lets it settle a contradicted `mixed` outright. |
| Clause-2 guard (:606) | No Raman citation. Its origin is golden-pool calibration (`1c7e0b6`). | **No citation exists.** |
| `_navamsa_status` docstring: "though exalted … debilitated in Navamsha", "debilitated in Rasi but exalted in Navamsa makes the native happy", "[Grahanam Amsakam Balam]" | **None of these three strings occurs in any book under `sources/`.** I grepped every `.md` file: "amsakam" has no hit, and "makes the native happy" appears only in an unrelated 11th-house sentence (HTJAH-I:16332). | **No, unverified.** These quotes back only the rare hollow/redeemed occupant arms anyway. |
| 6/8/12 from the navamsa Lagna, applied to every pillar (:840-844) | **No citation in the code.** The nearest Raman text is a set of specific combinations: HTJAH-I:8337 (7th lord in the 6/8/12 from the navamsa Lagna afflicts marriage), :14203 (10th lord there means the results are "greatly reduced"), :10156 (lord of the 10th from the navamsa Lagna, for the manner of death). HTJAH-I:1711-1755 counts the 6/8/12 **from another lord's D9 sign**, not from the navamsa Lagna, and the effect there is "a lessening of the above effects". HTJAH-I:9650 says the **opposite**: "If the 8th lord is in the 6th, 8th or 12th from Navamsha Lagna, the evil results will be greatly reduced." | **No.** Raman applies the test to a named lord inside a named combination, and the result is to temper. He never turns it into a general "weakens" for any lord and any karaka of any house, and for a dusthana lord he reads it as relief. |
| D9 exaltation / own sign / vargottama means confirms | No cited line. The general principle is HTJAH-I:485-487, factor 6 of 8: "The situation—favourable or adverse—of the house-lord **or the lord in whose house the particular house-lord is situated**, in the Navamsha", followed by "All these must be properly weighed". | **Loosely.** Raman's factor is the lord and **its dispositor**, and it is one of eight factors to be weighed. The code reads the lord and the **karaka** (no dispositor) and lets the result decide a contradiction. |

---

## 3. What the Navamsa step changes (HEAD against Navamsa off, final verdicts)

The step changes the `_decide` output on **83** rows. Later layers undo **19** of those
(saptamsa and fertility gates, the yogakaraka-in-Lagna gate). That leaves **64 final-verdict
changes**.

### By set

| Set | Changes | Agree with Raman after the change | Raman agreed with the verdict before (a loss) | Neither | Real errors created / removed |
|---|---|---|---|---|---|
| Pool | 44 | 32 | 8 | 4 | 7 / 9 |
| HO1 | 4 | 1 | 2 | 1 | 3 / 1 |
| HO2 | 16 | 10 | 2 | 4 | 6 / 1 |

In the pool the step is a net gain. On the hold-outs it adds real errors: **9 created against 2
removed**. Inside the pool, the guard (and the P2 and one-sided limits) were themselves measured
against the ratchet when they were adopted.

### By mechanism and direction (all three sets)

| Mechanism | Direction | Pool (agree/lost/neither) | HO1 | HO2 |
|---|---|---|---|---|
| Clause-2 guard, then modulate | favourable → afflicted | 16 (9/5/2) | 3 (1/2/0) | 3 (1/2/0) |
| Modulate "weakens" (4 pool rows and 1 HO1 row come through B1) | mixed → afflicted | 15 (12/2/1) | 1 (0/0/1) | 4 (1/0/3) |
| Modulate "confirms" | mixed → favourable | 13 (11/1/1) | 0 | 7 (6/0/1) |
| Modulate "weakens", then the yogakaraka-Lagna gate lifts it | mixed → favourable | 0 | 0 | 2 (counted as agree; the D9's own verdict was afflicted, Raman said favourable) |

On the hold-outs the guard changed 6 rows. It was right on 2, and **all 4 of the others are new
favourable↔afflicted inversions**. All 9 real errors the step creates out of sample come either
from the guard (4) or from "weakens"/"confirms" pushing a `mixed` past a Raman label on the other
side (5).

### Rasi evidence one-sided against contradictory

| Evidence | Pool | HO1 | HO2 |
|---|---|---|---|
| **One-sided** (only malefic, or only benefic rules fired) | 6 changes, **all 6 agree**: 5 malefic-only mixed→afflicted and 1 benefic-only mixed→favourable. 0 real errors. | 0 | 0 |
| **Contradictory** (both fired) | 38 changes: 26 agree, 8 lost, 4 neither. Real errors 7 with the step, 9 without. | 4: 1 agree, 2 lost, 1 neither. Real errors 3 against 1. | 16: 10 agree, 2 lost, 4 neither. Real errors 6 against 1. |

Every guard firing, and 58 of the 64 changes, are on contradictory rows.

### The prior "15 of 16" finding, re-measured at HEAD

Consider contradictory rows where Raman says favourable and the engine says afflicted. There are
16 at HEAD (pool 8, HO1 3, HO2 5). **15 have D9 = "weakens", and on 14 the Navamsa step is what
produced the afflicted.** With the step off, those 14 would not be afflicted. The finding holds
after R2.

### Does the status separate Raman's labels at all?

Across all 559 rows, Raman says afflicted on **44.7% of "weakens" rows, 44.0% of "confirms"
rows and 32.5% of "neutral" rows**. Raman says favourable on 47%, 53% and 57% of them. "Weakens"
and "confirms" carry the same affliction rate, so on the full population the status says almost
nothing about which direction Raman will go. The step's useful work is confined to the rows where
it fires inside a contradiction.

---

## 4. Counterfactuals (measurement only)

| Variant | Pool exact / w1 / real | HO1 | HO2 |
|---|---|---|---|
| HEAD | 277 / 350 / 39 | 23 / 28 / 8 | 58 / 98 / 36 |
| Navamsa changes only the degree, never the verdict | 253 / 348 / 41 | 24 / 30 / 6 | 50 / 103 / 31 |
| Navamsa may not turn favourable into afflicted (such rows land on mixed) | 269 / 354 / 35 | 22 / 30 / 6 | 57 / 100 / 34 |
| Navamsa off | 253 / 348 / 41 | 24 / 30 / 6 | 50 / 103 / 31 |

- **Degree-only and off give identical verdicts by construction.** The only thing the step does
  besides moving verdicts is degree (`mild` or `strong`), and degree is not scored.
- **No favourable→afflicted** means: wherever the navamsa-off verdict is favourable and HEAD is
  afflicted, report mixed. All other navamsa moves are kept. The 22 guard rows are the only ones
  it affects.
- **Read the two axes side by side.**
  - The full step buys pool exact (+24 over off) and HO2 exact (+8). It costs within-one and
    adds real errors on both hold-outs: HO1 +2 real, HO2 +5 real and −5 within-one.
  - The no-fav→aff variant gives up 8 pool exact and 1 exact on each hold-out. It removes 4
    real errors in the pool, 2 in HO1 and 2 in HO2.

---

## Summary of findings

1. `navamsa_status` is a two-planet dignity proxy (lord + karaka, plus rare occupants).
   **61% of its "weakens" verdicts come from the 6/8/12-from-navamsa-Lagna test**, which Raman
   never states as a general rule. He states it per combination, as tempering, and reverses it
   for the 8th lord (HTJAH-I:9650).
2. The **clause-2 guard has no Raman citation**. It was adopted on golden-pool gain. Because
   `_navamsa_modulate` always follows it, it works as a favourable→afflicted switch.
3. The `_navamsa_modulate` citation (HTJAH-I:975-980) is quoted accurately. It supports
   weighing the D9 together with the rasi, not a proxy that settles a contradiction alone. The
   occupant-arm quotes are not found in any book in the corpus.
4. In the pool the step agrees with Raman 32 times against 8 losses. On the two hold-outs
   combined it agrees 11 times against 4 losses, but **creates 9 real errors and removes 2**.
   All of its out-of-sample activity is on contradictory rows. On one-sided rows it was right 6
   times out of 6, all in the pool.
