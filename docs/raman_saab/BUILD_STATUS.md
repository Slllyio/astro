# Raman Saab — Build Status & Resume Point

> Independent engine replicating **B.V. Raman's *How to Judge a Horoscope*** as a
> deterministic, fully-cited proforma. This file is the resume pointer between sessions.

**Branch:** `round8-unification` · **Run tests:** `py -3.12 -m pytest tests/raman_saab/ -q` (67 passing)
**Run CLI:** `py -3.12 -m app.raman_saab --name X --date 1990-07-15 --time 12:00 --tz 5.5 --lat 12.97 --lon 77.59 --format text`

## Done ✅

| Phase | What | Tests | Key commits |
|---|---|---|---|
| **Methodology** | `docs/raman_saab/methodology/` — overview + 12 houses; 700+ line-cited rules; audited + gap-filled; unaudited drafts quarantined in `_derived/` | — | corpus commit |
| **Predicate audit** | `docs/raman_saab/predicate_audit.md` — 12-house sweep of ~1,650 rule-atoms; finalized `conditions.py` v1 set; four-layer rule split | — | audit commit |
| **Spec** | `docs/superpowers/specs/2026-06-01-raman-saab-engine-design.md` — §1–§13, 2 arch-reviews + user review + audit-amended | — | spec commits |
| **Phase 0** | `app/raman_saab/chart/` — model, ayanamsa isolation, Sripati Chalita cusps, adapter (Raman ayanamsa, mean node), CLI, import guard | 17 | `8bb8c17…3326940` |
| **Phase 1a** | `app/raman_saab/primitives/` — relationships, compound dignity, graded combustion, sign-attrs, nakshatra+tara, dispositor chains; adapter fills `combust_fraction` | +23 (40 total) | `30692f5…c8e7658` |
| **Phase 1b** | `primitives/` — functional_nature (per-Lagna table + yogakaraka + kendradhipati), bhangas (neecha-bhanga/parivartana/kemadruma), special_points (Atmakaraka 7-karaka / Karakamsa / Arudha), maraka (tiered + 22nd-drekkana + 64th-navamsa), balarishta (HPA-14 gate); `chart/upagrahas.py` (Gulika/Mandi); adapter fills all 5 `Optional` fields | +27 (67 total) | `56b7c61…7d3825e` |

Every phase gated by independent review that **verified against reality** (ran pyswisseph; ran every formula). Phase 1b: plan-doc review (approved) + bphs-doctrine review caught 3 doctrine errors → fixed against Raman's printed text (64th-navamsa from the **Moon** HTJAH-II:4544; 22nd-drekkana offset **+22** pinned to 27°-Aquarius→Libra→Venus HTJAH-II:3692-3695; balarishta houses **7/8/12** + real HPA-14 antidotes); final code-quality + doctrine re-audit on the shipped source = sound.

## Phase 1c — GBB Shadbala (in progress)

The last Phase-1 primitive: re-derive Raman's six-fold strength to his *Graha & Bhava Balas*
(NOT `app/core/shadbala`). **Research done** — `docs/raman_saab/gbb_shadbala_reference.md` is the
authoritative, line-cited formula spec (4-agent corpus extraction + my Ch.4 read), with the two
key fidelity traps pinned (Sun/Moon get **no** Cheshta in the Shadbala total; Dig from the
bhava-**madhya** cusp; Ayana 24°/48° Sun-doubled; Paksha Moon-doubled; Kendra by sign;
Saptavargaja 45-only-in-D1) and a **validated worked fixture** (GBB "Standard Horoscope", 16 Oct
1918, Libra Lagna — full 6-component table in Rupas). The Drik 30-60 branch bug (`(K−30)/2`, not
`K−30`) was caught live. **Decomposed into 3 sub-plans, each pinned to the fixture:**

| Sub-plan | Components | Status |
|---|---|---|
| **1c-1** | varga_lords + `shadbala/{naisargika,sthana,dig,drik}` (pure/cusp, Track-B) | **plan written + reviewed** (`docs/superpowers/plans/2026-06-03-raman-saab-phase1c1-shadbala-pure.md`) — **▶ RESUME: execute subagent-driven** |
| **1c-2** | `shadbala/{cheshta,kala}` — mean longitudes, declination, sunrise/ghatis, Ahargana (ephemeris) | not started |
| **1c-3** | total Shadbala assembly + min-required verdict; `bhava_bala`; `ishta_kashta`; wire `PlanetPos.shadbala_rupas/ishta/kashta`; **backfill** maraka `strength_rank`+weakest-planet, balarishta strength, navamsa64 external pin | not started |

**Resume ▶** Execute the **1c-1** plan (subagent-driven, same loop as 1b). Known carry-over inside
1c-1: Mars/Venus/Saturn/Moon **Saptavargaja** cells don't yet reconcile (gap is in the per-varga
compound-relation, NOT Kendra which is verified) — localize via the per-sub-component fixture in
Task 6, `xfail` + carry any residual to 1c-3.

Then **Phase 2** (`doctrine/conditions.py` + evaluable/descriptive rule encoding — predicate_audit §7 is the finalized algebra), **3** (judges + overview), **4** (longevity), **5** (timing+divisional), **6** (proforma+surfaces), **7** (golden harness via `tests/fixtures/raman_goldens.jsonl`, spec §11.1).

## Locked decisions / gotchas (do NOT relitigate)
- **Ayanamsa = Raman default**, isolated via `chart/ayanamsa.py` context manager — NEVER mutates the global (app/core stays Lahiri). `pyswisseph 2.10.x has no get_sid_mode()` — uses hasattr + Lahiri-restore fallback.
- **No `app/core` imports** — enforced by `tests/raman_saab/test_import_guard.py`. Re-derive Shadbala to GBB, don't import core's.
- **Bhava (Chalita) not Rashi** for result judgment; `rasi_house` for lordship/aspects/yogas. Both carried on `PlanetPos`.
- **Nodes cast only the 7th aspect** (no 5/9); **mean node** (not true node) — Raman's hand-calcs.
- **A rule is not always a boolean**: condition predicates → `doctrine/conditions.py`; lookup tables → `doctrine/lookups/`; numeric sub-engines → `primitives/`; timing → `judges/timing.py`; output meta-modifiers → `proforma.py`.
- **Verdict is an ordinal** (favourable/mixed/afflicted/insufficient-evidence), never a false-precision score (spec §6.3).
- Test data tables (exaltation, friendships, nakshatra lords, drekkana) verified live — Mercury moolatrikona is **Virgo 16-20** (Raman/Santhanam), not a typo.
- **Phase 1b doctrine locks (pinned to Raman's printed text, do NOT "correct" to textbook):**
  - **22nd drekkana = lagna decanate + 22** (mod 36), pinned to Raman's worked example 27° Aquarius → 1st-of-Libra → Venus (HTJAH-II:3692-3695). The textbook "8th-house +21" is the alternative; Raman's printed example is the authority.
  - **64th navamsa is reckoned from the MOON** (HTJAH-II:4544), not the Lagna. Offset +63 is the textbook default but **unpinned** (no Raman worked example) → external-pin (JH/drikpanchang) is a Phase-1c backfill.
  - **Atmakaraka = 7 visible planets only** (`special_points._SEVEN`), never Rahu/Ketu — load-bearing because the adapter DOES inject nodes into `chart.planets` (CLAUDE.md lock).
  - **Functional nature = Raman's printed per-Lagna table is the authority** (it embeds his hand-tuned calls, e.g. Libra-Mars "feeble benefic" = neutral); 3 unprinted holes (Aries-Moon, Gemini-Saturn = neutral; Aquarius-Saturn = benefic) are generating-rule derivations.
  - **Balarishta Moon-affliction houses = 7/8/12** (HPA-14:96-98), NOT 6/8/12; antidotes are the real HPA-14 list (no "malefics in upachaya").
  - Aspect-based conditions (neecha-bhanga aspect-by-dispositor, kemadruma/balarishta benefic-aspect, maraka aspect-association) use a **conjunction proxy** in 1b → refined in Phase 2 (drishti engine). `strength_rank`/weakest-planet maraka → Phase 1c.
