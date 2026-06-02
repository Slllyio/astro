# Raman Saab — Build Status & Resume Point

> Independent engine replicating **B.V. Raman's *How to Judge a Horoscope*** as a
> deterministic, fully-cited proforma. This file is the resume pointer between sessions.

**Branch:** `round8-unification` · **Run tests:** `py -3.12 -m pytest tests/raman_saab/ -q`
**Run CLI:** `py -3.12 -m app.raman_saab --name X --date 1990-07-15 --time 12:00 --tz 5.5 --lat 12.97 --lon 77.59 --format text`

## Done ✅

| Phase | What | Tests | Key commits |
|---|---|---|---|
| **Methodology** | `docs/raman_saab/methodology/` — overview + 12 houses; 700+ line-cited rules; audited + gap-filled; unaudited drafts quarantined in `_derived/` | — | corpus commit |
| **Predicate audit** | `docs/raman_saab/predicate_audit.md` — 12-house sweep of ~1,650 rule-atoms; finalized `conditions.py` v1 set; four-layer rule split | — | audit commit |
| **Spec** | `docs/superpowers/specs/2026-06-01-raman-saab-engine-design.md` — §1–§13, 2 arch-reviews + user review + audit-amended | — | spec commits |
| **Phase 0** | `app/raman_saab/chart/` — model, ayanamsa isolation, Sripati Chalita cusps, adapter (Raman ayanamsa, mean node), CLI, import guard | 17 | `8bb8c17…3326940` |
| **Phase 1a** | `app/raman_saab/primitives/` — relationships, compound dignity, graded combustion, sign-attrs, nakshatra+tara, dispositor chains; adapter fills `combust_fraction` | +23 (40 total) | `30692f5…c8e7658` |

Every phase gated by independent review that **verified against reality** (ran pyswisseph; ran every formula).

## Resume here ▶ — Phase 1b

Write the plan from `predicate_audit.md` §7 + spec §4–§6, build subagent-driven (same loop). Modules:
- `primitives/functional_nature.py` — per-Lagna benefic/malefic table (overview §4) + generating rules; `is_yogakaraka`, `kendradhipati_dosha`, `functional_nature(p)`.
- `primitives/bhangas.py` — `neecha_bhanga(p)`, `parivartana(h1,h2)`, kemadruma/balarishta-bhanga predicates (spec §5.5).
- `primitives/special_points.py` — Gulika/Mandi (upagrahas; need sunrise/sunset segment math), Atmakaraka (highest deg-in-sign, 7 planets), Karakamsa (AK's navamsa sign).
- `primitives/maraka.py` — 2nd/7th lords+occupants+associates tiered; 22nd-drekkana lord, 64th-navamsa lord (fills `RamanChart.maraka_points`).
- `primitives/balarishta.py` — infant-mortality yoga gate + bhangas (fills `RamanChart.balarishta`).
- Wire the special/maraka/balarishta fields into the adapter (currently `Optional=None`).

Then **Phase 1c** — GBB Shadbala (6 components in Rupas, **±1-rupa fixture** from `graha_bhava_balas_raman/` Ch.3–10), bhava-bala, ishta/kashta, sphutas (beeja/kshetra/special-dhana/sahams). Then **Phase 2** (`doctrine/conditions.py` + rule encoding), **3** (judges), **4** (longevity), **5** (timing+divisional), **6** (proforma+surfaces), **7** (golden harness via `tests/fixtures/raman_goldens.jsonl`, spec §11.1).

## Locked decisions / gotchas (do NOT relitigate)
- **Ayanamsa = Raman default**, isolated via `chart/ayanamsa.py` context manager — NEVER mutates the global (app/core stays Lahiri). `pyswisseph 2.10.x has no get_sid_mode()` — uses hasattr + Lahiri-restore fallback.
- **No `app/core` imports** — enforced by `tests/raman_saab/test_import_guard.py`. Re-derive Shadbala to GBB, don't import core's.
- **Bhava (Chalita) not Rashi** for result judgment; `rasi_house` for lordship/aspects/yogas. Both carried on `PlanetPos`.
- **Nodes cast only the 7th aspect** (no 5/9); **mean node** (not true node) — Raman's hand-calcs.
- **A rule is not always a boolean**: condition predicates → `doctrine/conditions.py`; lookup tables → `doctrine/lookups/`; numeric sub-engines → `primitives/`; timing → `judges/timing.py`; output meta-modifiers → `proforma.py`.
- **Verdict is an ordinal** (favourable/mixed/afflicted/insufficient-evidence), never a false-precision score (spec §6.3).
- Test data tables (exaltation, friendships, nakshatra lords, drekkana) verified live — Mercury moolatrikona is **Virgo 16-20** (Raman/Santhanam), not a typo.
