# Raman Saab — Phase 1c-3 continuation: Bhava-bala + Adapter Wiring + Backfills (finish Phase 1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`).

**Goal:** Finish Phase 1: add **Bhava-bala** (house strength), **wire the full Shadbala into `PlanetPos`** (so real charts carry strength), and **backfill** the 1b deferrals now that Shadbala exists (maraka `strength_rank` + weakest-planet, balarishta "powerfully situated").

**Architecture:** `shadbala/bhava_bala.py` (pure, 3 components). `chart/shadbala_compute.py` orchestrates the 6 graha-bala components + ishta/kashta per planet for a real chart (it ties together the shadbala primitives + `kala_context` + `mean_longitudes`). The adapter gains a Shadbala pass that fills `PlanetPos.shadbala_rupas/ishta/kashta`, computed **before** the maraka pass so the backfill can rank by strength.

**Tech Stack:** Python 3.12, frozen dataclasses, pytest. `shadbala_compute.py` is chart-layer (orchestrates ephemeris-derived context); `bhava_bala.py` is pure. No `app/core`.

**Scope.** IN: `shadbala/bhava_bala.py`, `chart/shadbala_compute.py`, adapter wiring, maraka/balarishta backfills. After this, **Phase 1 is complete.** OUT: the Ahargana Kala year/month lords (still flagged UNKNOWN→0); the navamsa64 external pin; the Mars/Venus-Ayana & Saptavargaja-cusp xfail *decisions* (leave as documented xfails) — these are small residuals carried into Phase 2 prep.

**Authority:** `docs/raman_saab/gbb_shadbala_reference.md` §8 (Bhava-bala). All cross-cutting formulae already built + pinned (1c-1/1c-2/1c-3 capstone).

---

## Task 1: Bhava-bala

**Files:** Create `app/raman_saab/primitives/shadbala/bhava_bala.py`; Test `.../shadbala/test_bhava_bala.py`

Reference §8. Three components, summed (Shashtiamsas; /60 Rupas):
- **Bhavadhipati** = the bhava-lord's **total Shadbala** (Shashtiamsas). Lord = owner of the sign holding the bhava-madhya.
- **Bhavadig** = `|ref − bhava|` (if >6, `12−`), ×10. **`ref` = the sign-class NIL house** of the bhava-madhya's sign: Nara {Gem,Vir,Lib,Aqu,Sag-1st-half}→**7** · Jalachara {Can,Cap-2nd-half,Pis}→**10** · Chatushpada {Ari,Tau,Leo,Sag-2nd-half,Cap-1st-half}→**4** · Keeta {Sco}→**1**. (Verified: 8th-bhava-in-Leo → ref 4 → |4−8|=4 → **40**; Nara Lagna → |7−1|=6 → 60, Nara 7th → 0.)
- **BhavaDrig** = aspect on the bhava-madhya (treat as a Drushya): **full** Dristi for Jupiter & Mercury, **¼** for the others; signed (benefic +, malefic −). Reuse `drik.dristi_value` + the malefic test.

- [ ] **Step 1: failing test**
```python
from app.raman_saab.primitives.shadbala import bhava_bala as bb

def test_bhavadig_worked_example_and_extremes():
    # 8th bhava, madhya in Leo (Chatushpada, ref 4): |4-8|=4 -> 40.
    assert bb.bhavadig_bala(8, sign=5) == 40.0      # Leo = sign 5
    # Nara sign (e.g. Libra=7) at the Lagna (1st) -> max 60; at the 7th -> 0.
    assert bb.bhavadig_bala(1, sign=7) == 60.0
    assert bb.bhavadig_bala(7, sign=7) == 0.0

def test_bhava_class_ref():
    assert bb.sign_class_ref(5) == 4     # Leo -> Chatushpada -> 4
    assert bb.sign_class_ref(8) == 1     # Scorpio -> Keeta -> 1
    assert bb.sign_class_ref(7) == 7     # Libra -> Nara -> 7
    assert bb.sign_class_ref(4) == 10    # Cancer -> Jalachara -> 10
```
- [ ] **Step 2:** FAIL.
- [ ] **Step 3: implement** — `sign_class_ref(sign, deg=0.0) -> int` (handle Sag/Cap half-splits with `deg`),
  `bhavadig_bala(bhava, sign, deg=0.0)`, `bhava_drig_bala(bhava_madhya, chart)` (reuse `drik`),
  `bhava_bala(bhava, chart, lord_shadbala) -> float` summing the three. Pin Bhavadig (above) and a
  Bhavadhipati passthrough; BhavaDrig unit-tested for sign (full Drik on a benefic aspecting the madhya
  gives +). Full per-house fixture totals (I 6.70…XII 9.66) need real cusps → an **ephemeris end-to-end
  sanity test** (all 12 bhava-balas in a plausible Rupa range), not a Track-B pin.
- [ ] **Step 4:** PASS. **Step 5:** report.

---

## Task 2: `chart/shadbala_compute.py` + adapter wiring

**Files:** Create `app/raman_saab/chart/shadbala_compute.py`; Modify `app/raman_saab/chart/adapter.py`; Test `tests/raman_saab/chart/test_shadbala_compute.py` + add an adapter case.

**`compute_shadbala(chart, birth, ayanamsa_deg) -> dict[str, tuple[ShadbalaBreakdown, float, float]]`:**
build `ctx = kala_context.kala_context(birth, chart, ayanamsa=ayanamsa_deg)` and
`mns = mean_longitudes.mean_longitudes(chart.jd_ut, birth.year)`; for each of the 7 planets compute the
6 components (Shashtiamsas) →
- `sthana = sthana.sthana_bala(p, chart)`
- `dig = dig.dig_bala(p, chart)` (real cusps from `chart.bhava_madhyas`)
- `kala = kala.kala_bala(p, chart, ctx)`
- `cheshta = cheshta.cheshta_bala_for_chart(p, chart, mns["mean"], mns["seeg"])` (0 for Sun/Moon)
- `naisargika = naisargika.naisargika_bala(p)`
- `drik = drik.drik_bala(p, chart)`
then `br = total.assemble_shadbala(sthana,dig,kala,cheshta,naisargika,drik)`; **ishta/kashta** from
`ochcha = sthana.ochcha_bala(p, chart)` and the Cheshta value — for Sun/Moon use
`ishta_kashta.sun_chesta_surrogate(p_lon+ayanamsa_deg)` / `moon_chesta_surrogate(moon,sun)`.
Return `{p: (br, ishta, kashta)}`.

**Adapter:** in `cast_chart`, inside the `sidereal_mode(ayanamsa)` block capture
`ayan_deg = swe.get_ayanamsa_ut(jd)`. After the combustion pass (and before the special-points/maraka
pass — see Task 3 ordering), compute `compute_shadbala(...)` and `dataclasses.replace` each `PlanetPos`
with `shadbala_rupas=br, ishta=ishta, kashta=kashta`. `from_stated_positions` leaves them `None`.

> **Notes:** (1) The Kala Ahargana year/month lords are still `UNKNOWN`→0, so real-chart Kala slightly
> under-counts — documented; acceptable for Phase 1. (2) Computing Shadbala in every `cast_chart` adds
> a sunrise + per-planet pass; that's fine for ephemeris charts. (3) No import cycle: `shadbala_compute`
> imports primitives + `kala_context`/`mean_longitudes`; the adapter imports `shadbala_compute`; none
> import the adapter. Import guard must still pass.

- [ ] TDD: end-to-end test casts the canonical Bangalore chart, asserts every `PlanetPos.shadbala_rupas`
  is a `ShadbalaBreakdown` with `total>0` and `0 < total/60 < 12` (plausible Rupa band), and ishta/kashta
  in [0,60]. Run the full suite; import guard passes. **Do not commit.**

---

## Task 3: backfills — maraka strength_rank + weakest-planet; balarishta strength

**Files:** Modify `app/raman_saab/primitives/maraka.py`, `app/raman_saab/primitives/balarishta.py`, and the adapter ordering; Tests: extend `test_maraka.py`, `test_balarishta.py`.

- **Adapter ordering:** the maraka/balarishta pass must run **after** the Shadbala pass (Task 2) so the
  chart's `PlanetPos.shadbala_rupas` are filled. Move the `maraka.maraka_points(chart)` /
  `balarishta.balarishta(chart)` calls into a replace that happens after shadbala is attached.
- **maraka.py:** `MarakaUnit.strength_rank` = rank of the graha among all 7 by total Shadbala
  (1 = strongest), read from `chart.planets[g].shadbala_rupas.total` when present (fall back to 0 when
  absent, e.g. Track-B). Add the **weakest-planet tertiary maraka** = the planet with the lowest total
  Shadbala (GBB-8 / overview §8.2). Guard: only when shadbala is filled.
- **balarishta.py:** the antidote "lord of the lagna **powerfully situated**" (HPA-14:235) — replace the
  v1 dignity/kendra proxy with the real check `chart.planets[lagna_lord].shadbala_rupas.total/60 >=
  MIN_REQUIRED[lagna_lord]` when shadbala is present (keep the proxy as fallback for Track-B).
- Tests: an ephemeris chart's maraka units carry sane `strength_rank` (1..7, unique-ish) and a
  weakest-planet tertiary appears; a balarishta antidote fires via real Shadbala on a chart with a strong
  lagna lord. Track-B charts still work (fallbacks).

- [ ] TDD per the above; run the full suite; import guard passes. **Do not commit.**

---

## Phase 1c-3 continuation done-when (⇒ **Phase 1 COMPLETE**)
- `py -3.12 -m pytest tests/raman_saab/ -q` green (existing + new; import guard passes).
- `bhava_bala` Bhavadig pinned (8th-in-Leo=40, Nara extremes); end-to-end Bhava-bala sane.
- `cast_chart` fills `PlanetPos.shadbala_rupas/ishta/kashta` for ephemeris charts; `from_stated_positions` leaves them `None`.
- maraka units carry `strength_rank` + a weakest-planet tertiary; balarishta uses real Shadbala for the strong-lagna-lord antidote.
- **Residuals carried to Phase 2 prep** (small, documented): Ahargana Kala year/month lords; navamsa64 external pin; Mars/Venus-Ayana + Saptavargaja-cusp xfails.

**Then Phase 2** — `doctrine/conditions.py` (the predicate algebra, predicate_audit §7) + evaluable/descriptive `RuleRecord` encoding. The primitives (Phase 1) are the facts those conditions read.
