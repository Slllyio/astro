---
layer: soul-destiny (Jaimini + Parashari mokṣa)
engine: app/raman_saab/judges/soul_reading.py + family_soul_group.py  (REPORT-ONLY)
verdict_authority: Rāśi 5th/9th/12th (Parashari) — the Jaimini/nakshatra layers corroborate
branch: soul-destiny-experiment (EXPERIMENT — Jaimini firewall lifted; do not merge to main)
---

# Reading a nativity as a scripted soul (D-1 Parashari + Jaimini)

> A **report-only, provenance-honest** procedure. Every line is tagged
> `RAMAN_EXPLICIT | RAMAN_GENERAL_PRINCIPLE | JAIMINI_EXPLICIT | CLASSICAL_NONCITABLE |
> EDITORIAL_SYNTHESIS | ABSENT_IN_RAMAN`. Nothing is invented; where a text is silent it is said so.
> **This is an astrological reading, not a fixed fate** — a scripted destiny is a promise and a
> tendency, held alongside the person's own free life.

## 0. The two provenance regimes (the fact that governs everything)

The soul divides across two schools, and the engine keeps them apart:

- **Parashari core (authoritative, citable).** Raman's *own* natal doctrine on the soul: past-birth
  merit (5th, poorvapunya, HTJAH-I:5019), dharma (9th, HTJAH-II:7285), and the mokṣa / after-death
  state of the soul (12th, HTJAH-II:16669, with the `house_12_vyaya.md` Groups F/G apparatus). This
  **decides.**
- **Jaimini soul-script (report-only).** The Ātmakāraka, Karakāṁśa, the 7 chara karakas, the Chara
  Dasha, the Arudha Lagna. On the main engine the Jaimini corpus is **firewalled** (non-citable, a
  different system). On the **`soul-destiny-experiment`** branch that firewall is deliberately
  lifted (`book_registry.py`, sentinel `EXPERIMENT-BRANCH-ONLY (soul-destiny)`), so these lines
  carry `JAIMINI_EXPLICIT` citations (`JAIMINI-49`, `JS-1`). **⚠ Never merge this branch to `main`
  without re-review** — `git grep "EXPERIMENT-BRANCH-ONLY (soul-destiny)"` shows the full blast
  radius; `PRASNA/MUHURTHA/VARSHA` stay firewalled so the mechanism is proven intact.

The Ātmakāraka is strict 7-karaka (Rahu/Ketu can never be the soul — CLAUDE.md lock); AK here is
identical by construction to `special_points.atmakaraka`.

## 1. The Parashari soul core — *this decides*

`judges/soul_reading.py` → `raman_core`, delegating to `judge_house`:
1. **Poorvapunya** (5th) — the merit the soul carries in. `judge_house(chart, 5)` → `poorvapunya`.
2. **Dharma** (9th) — the soul's law/path. `judge_house(chart, 9)` → `dharma`.
3. **Mokṣa / after-death state** (12th) — `judge_house(chart, 12)` → `moksha`.
4. **The Kaivalya combination** — *Ketu in the 12th from the Karakāṁśa → Final Emancipation*
   (HTJAH-II:16527). This ports the standing stub `house_12_vyaya/combinations.py` H12.C.G2 into an
   evaluable **report-only** predicate (Ketu's navāṁśa sign == the 12th sign from the Karakāṁśa); it
   does not alter the D1 rule engine.

## 2. The Jaimini soul-script — *report-only corroboration*

`judges/soul_reading.py` → `jaimini_overlay` (every field provenance-`Tagged`):
- **The 7 chara karakas** (`primitives/chara_karakas.py`): AK (soul), AmK (mind), BK, MK, PK, GK,
  DK (spouse) — ranked by degree-within-sign descending.
- **The Karakāṁśa soul-cartography** — each of the 12 bhavas *from the Karakāṁśa* read as the soul's
  scripted purpose (5th = purpose-mantra / what it came to teach; 9th = guru-lineage; 10th = worldly
  mission; 12th = mokṣa-vehicle / iṣṭa-devatā), with the planets seating each bhava. Ported from the
  classical soul-cartography; cited `JAIMINI-49`.
- **Karakāṁśa occupant professions** — planets navāṁśa-conjunct the AK (Jaimini Sūtras 1.2, `JS-1`).
- **The Chara Dasha** — the 12-sign "script" unfolding from birth (`primitives/chara_dasha.py`).
- **The Arudha Lagna** — the soul's worldly mask (`primitives/arudha.py`).

**Node drishti:** in this engine Rahu/Ketu cast the **7th aspect only** (`doctrine/drishti.py:31`),
not the 5/9 of other traditions — the soul layer inherits this.

## 3. The nakshatra soul-signature — *split provenance*

`primitives/nakshatra_signature.py` gives each of the AK / Moon / Lagna birth-stars its deepest
archetype. **Provenance is per column:** `devata` / `symbol` / `gana` are classical-Vedic but
outside Raman's corpus → `CLASSICAL_NONCITABLE`; the `soul_archetype` / `soul_keyword` phrasings are
this layer's authored synthesis → `EDITORIAL_SYNTHESIS`. Neither ever enters `raman_core` or a D1
verdict.

## 4. The family soul-group — *how souls interlock, report-only, nets nothing*

`judges/family_soul_group.py` cross-references several members' soul-signatures and surfaces:
- **Shared soul-frames** — members sharing an AK / Karakāṁśa / Ketu sign (or, more strongly,
  nakshatra): souls seated in one frame.
- **Karmic role-swaps** — one member's soul-planet (AK) being another's AmK or DK (counsel- or
  spouse-significator); AK↔DK reciprocity.
- **Ketu-axis resonance** — a shared Ketu sign/axis, or one member's Ketu (mokṣa-vehicle) seating
  another's Karakāṁśa (soul).
- **Recurring soul-motif** — the AK sign recurring across ≥ half the group.

Like `two_spouse_children.py`, it **nets nothing** — no text gives a formula for combining souls, so
there is no group verdict (`ABSENT_IN_RAMAN`); the synthesis is the reader's.

## 5. Honest limits

- The Jaimini layer is a **parallel school**, not Raman's Parashari-natal method; on `main` it is not
  even citable. Its authority here rests on the experiment carve-out, not on the Prime Directive.
- Shared soul-frames across same-era births partly reflect shared slow-point placements — read the
  concordance as *resonance*, not proof of a metaphysical claim.
- The nakshatra archetypes are editorial; the "scripted-together" interpretations are
  `EDITORIAL_SYNTHESIS`, never Raman.
- **Everything here is report-only and imported by nothing in the D1 verdict path** — the golden
  ratchet is untouched by construction. A soul reading is a contemplative lens, never a fixed fate,
  and never medical or life advice.
