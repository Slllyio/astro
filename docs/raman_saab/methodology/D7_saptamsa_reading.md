---
varga: 7
name: Saptāṁśa (D-7)
domain: children / progeny (santāna)
karaka: Jupiter (Putra-Kāraka)
engine: app/raman_saab/judges/saptamsa_reading.py  (REPORT-ONLY)
verdict_authority: Rāśi 5th + Navāṁśa + Beeja/Kṣetra  (NOT the D-7)
source_policy: HPA-11 (Raman-citable) · HTJAH-I Ch.VIII (Raman-citable) · KP/Rath (non-citable)
---

# How to decipher the Saptāṁśa (D-7) for children

> An exhaustive, **provenance-honest** procedure. Every step is tagged
> `[RAMAN-EXPLICIT | RAMAN-GENERAL-PRINCIPLE | CLASSICAL-NONCITABLE | ABSENT-IN-RAMAN]`.
> Nothing is invented; where Raman is silent it is said so plainly (Prime Directive:
> *no silent approximation*).

---

## 0. The one fact that governs everything below

**B. V. Raman defines the Saptāṁśa and assigns it to children, but never actually reads a
D-7 chart for progeny anywhere in his corpus.** A full-text audit of *How to Judge a
Horoscope* (Vol I & II) and *Notable Horoscopes* found **zero** Saptāṁśa occurrences, against
**358** children/Navāṁśa references — i.e. he judges progeny constantly, but always from the
**Rāśi 5th + Navāṁśa + Beeja/Kṣetra sphuṭas**.

| Question | Raman's answer | Provenance |
|---|---|---|
| D-7 defined? | Yes, "casually" | `[RAMAN-EXPLICIT]` HPA-11:187–193 |
| D-7 = children varga? | Yes, a one-line pointer | `[RAMAN-EXPLICIT]` HPA-11:197–199 |
| D-7 ever cast/read for children? | **No — never** | `[ABSENT-IN-RAMAN]` (HTJAH & NH: 0 hits) |
| Raman's real progeny engine | Rāśi 5th + Navāṁśa + Beeja/Kṣetra | `[RAMAN-EXPLICIT]` HTJAH-I:5517–5527, 5902–5904 |
| Successive-child house rule | none | `[ABSENT-IN-RAMAN]`; KP 5→7→9 & Rath Maṇḍūka non-citable |
| Gender of a child | Rāśi-5th odd/even + planet-sex rules | `[RAMAN-EXPLICIT]` HTJAH-I:5206–5220, 5940–5953 |
| Child affliction / loss | Rāśi-5th malefic / afflicted-Jupiter combos | `[RAMAN-EXPLICIT]` HTJAH-I:5192–5211, 5270–5294 |
| D-7 lagna / 5th-of-D7 / Jupiter-in-D7 rule | none | `[ABSENT-IN-RAMAN]`; only Rath (non-citable) |

Raman's own framing of the division: *"Sapthamsa.—I may also **casually** refer to
Sapthamsa…"* (HPA-11:187) and *"It is **not necessary for a beginner** to bother himself with
these technicalities."* (HPA-11:200–201). The domain pointer: *"Dwadasamsa for parents,
**Saptamsa for children**, etc."* (HPA-11:198).

**Consequence for this methodology.** The D-7 is a *corroborating* lens, not the verdict.
The verdict is decided by Raman's real method (§2). The D-7 overlay (§3) is read by the
general "judge the varga as you judge the rāśi" principle for the eldest child, and by the
classical (non-citable) house scheme for later children — both clearly flagged.

---

## 1. Cast the D-7

`cast_varga_chart(chart, 7)` (`app/raman_saab/chart/varga_chart.py`). Saptāṁśa sign of a
longitude: a sign is split into 7 parts of ~4°17′; **odd signs count from the sign itself,
even signs from the seventh from it** (HPA-11:190–193, `[RAMAN-EXPLICIT]`). The D-7 lagna is
the Saptāṁśa of the ascendant degree; houses are whole-sign from that lagna.

---

## 2. The Rāśi-anchored core — *this decides the verdict* `[RAMAN-EXPLICIT]`

Engine: `judge_house(chart, 5)` (the children signification) + `beeja_kshetra(chart)`.
These are surfaced verbatim in `saptamsa_reading.RamanCore`.

1. **The three pillars of the 5th** (HTJAH-I:5018–5022): the **house** (Pisces/… on the
   5th, its occupants, aspects), the **lord** of the 5th (placement, strength, Navāṁśa), and
   the **kāraka Jupiter** (Putra-Kāraka — own-house? Papakartari? malefic sign? trikoṇa from
   the 5th? conjoined/aspected by Mars/Saturn/Rahu?).
2. **Beeja / Kṣetra sphuṭas — the mandatory fertility pre-pass** (HTJAH-I:5517–5527): Beeja
   = (Sun+Venus+Jupiter) must fall in an **odd** sign & odd Navāṁśa; Kṣetra =
   (Mars+Moon+Jupiter) in an **even** sign & even Navāṁśa; Rahu must never join; no evil
   planet 5th-from the point. **Both barren → decisive denial** (the engine's fertility gate).
3. **Navāṁśa is the counting engine** (HTJAH-I:5902–5904): number of children ≈ Navāṁśas
   gained by the 5th house/lord; ×2 if the 5th lord is aspected by Jupiter/Venus; ×3 if
   vargottama; subtract for malefics in intervening Navāṁśas.
4. **Gender** (HTJAH-I:5206–5220): first child **male** if the 5th lord is in the 1st/2nd/3rd,
   or Mars+Venus+Moon in dual signs (Sagittarius excepted); first-born **daughter** if a
   malefic is in the 11th and Moon & Venus occupy the 5th; predominance of **even/feminine**
   elements in the 5th → female issue (HTJAH-I:5952, Chart 107). *Read from the Rāśi, never
   the D-7.*
5. **Affliction / loss of a child** (HTJAH-I:5192–5211, 5270–5294): 5th lord in 3/6/12 with
   no benefic aspect, or hemmed between malefics → children die early; **Mars** afflicting →
   *"children die after some time"* (5270); **Ketu** → *"lacks the human touch in his
   approach towards one or two of the issues"* (5293); **Saturn** → sorrows through children
   (5258); **Rahu** → loses a number of children (5262).

The engine already nets all of this into one verdict (`children`), plus the D-7 *borderline*
nudge shipped earlier this session (`_saptamsa_status`/`_saptamsa_gate` — a general-principle
confirm/weaken, never a decisive move).

---

## 3. The D-7 overlay — *report-only corroboration*

Engine: `saptamsa_reading.D7Overlay`. Read the child-varga **as you would read a rāśi** — but
label the provenance, because Raman never demonstrates it.

> **Two distinct D-7 roles — do not conflate them.** *This reading surface*
> (`saptamsa_reading.py`) is **strictly report-only**; it never touches the verdict.
> *Separately*, the engine carries a `_saptamsa_gate` (`house_template.py`) that may nudge a
> **borderline `mixed`** children verdict **one step, never decisively**, and is suppressed when
> both Beeja and Kṣetra are strong (see §5). Everything in *this* section is the report surface.

1. **The eldest child = the D-7 lagna** `[RAMAN-GENERAL-PRINCIPLE]`. The domain-varga's own
   ascendant is the seat of the (first) child matter. Read its sign, its lord, its
   **occupants**, and the planets **aspecting** it (whole-sign drishti, the locked table:
   Mars 4/8, Jupiter 5/9, Saturn 3/10, nodes 7th-only). Malefics on/aspecting the seat carry
   Raman's Rāśi-5th planet-effects **applied by analogy** (the effect text is Raman-explicit;
   its D-7 application is the general principle — see the `_MALEFIC_5TH_EFFECT` map).
2. **Putra-Kāraka Jupiter in the D-7** — its sign, house, and dignity, as a strength read on
   the progeny significator inside the child-varga `[RAMAN-GENERAL-PRINCIPLE]`.
3. **The 5th-from-the-D-7-lagna** — the child-of-the-child / continuity seat, read the same
   way `[RAMAN-GENERAL-PRINCIPLE]`.
4. **Successive children (2nd, 3rd …)** `[CLASSICAL-NONCITABLE]`. Raman gives **no** rule.
   The engine uses the KP/Rath house scheme (2nd child ≈ the 7th, 3rd ≈ the 9th from the D-7
   lagna) **flagged non-citable** — suggestive, never authoritative. (KP:
   *kp_reader2_fundamentals:11950*; Rath Maṇḍūka-gati: *crux_of_vedic_astrology_rath:1865*.)

---

## 4. The decipher checklist (each step → its engine primitive)

| Step | Read | Engine primitive | Provenance |
|---|---|---|---|
| 1 | Cast the D-7 | `cast_varga_chart(chart, 7)` | RAMAN-EXPLICIT (definition) |
| 2 | Rāśi 5th house/lord/occupants/aspects | `RamanCore.rasi_fifth_*` | RAMAN-EXPLICIT |
| 3 | Putra-Kāraka Jupiter (Rāśi + Navāṁśa) | `RamanCore.putrakaraka_*` | RAMAN-EXPLICIT |
| 4 | Beeja / Kṣetra fertility | `beeja_kshetra(chart)` | RAMAN-EXPLICIT |
| 5 | **The verdict** | `judge_house(chart, 5)` → `children` | RAMAN (real method) |
| 6 | D-7 lagna = eldest-child seat | `D7Overlay.child_loci[0]` | RAMAN-GENERAL-PRINCIPLE |
| 7 | Per-seat affliction → Raman effect | `ChildLocus.afflictions` | RAMAN-GENERAL-PRINCIPLE |
| 8 | Gender | `D7Overlay.gender_indicators` | RAMAN-EXPLICIT (Rāśi) |
| 9 | Successive children | `child_loci[1:]` | CLASSICAL-NONCITABLE |

Run it: `py -3.12 -m tools.raman_saab.saptamsa_reading --fixture <chart>.json`.

---

## 5. Honest limits & confidence framing

- The **D-7 lagna reading and the successive-child scheme are not Raman's** — they are a
  general-principle / classical extension. Never present a D-7 conclusion as a verbatim Raman
  verdict; the verdict is §2's.
- The engine's D-7 verdict influence is **only** the borderline `_saptamsa_gate` nudge (a
  `mixed` children verdict, one step, guarded against strong sphuṭas) — validated
  verdict-invariant on the golden ratchet and passed by the `bphs-doctrine-reviewer`.
- A reading of a specific living child is an **astrological reading in Raman's system**, to be
  stated with explicit confidence and **never as medical prognosis**.
