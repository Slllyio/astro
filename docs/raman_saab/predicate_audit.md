---
title: "Raman Saab — Predicate Audit (mandatory pre-Phase-1 gate, spec §13)"
kind: spec
topic: doctrine
measured: false
updated: 2026-07-24
words: 1529
tags: [raman-saab, spec, doctrine]
---
# Raman Saab — Predicate Audit (mandatory pre-Phase-1 gate, spec §13)

> Finalizes the condition algebra (`doctrine/conditions.py`) **before** any rule encoding.
> Synthesized from 12 independent per-house audits of the methodology corpus against the
> spec §5.3 algebra. Each house file's rules were classified evaluable / descriptive /
> lookup / numeric, every required predicate extracted, and gaps vs §5.3 flagged.

## 1. Headline numbers

| House | Rule-atoms | Evaluable | Descriptive | Lookup/numeric |
|---|---|---|---|---|
| 1 Lagna | 163 | 98 | 65 | — |
| 2 Dhana | 148 | 122 | 26 | + Drekkana table, Special-Dhana arithmetic |
| 3 Sahaja | 117 | 74 | 43 | — |
| 4 Sukha | 127 | 107 | 20 | — |
| 5 Putra | 134 | 81 | 53 | + Beeja/Kshetra arithmetic |
| 6 Ari | 170 | 103 | 14 | + 45 disease lookup rows |
| 7 Kalatra | 170 | 134 | 36 | + Kuja-Dosha grid |
| 8 Ayur | 170 | 118 | 35 | + 36 decanate-cause rows, 17 ayus-arithmetic |
| 9 Bhagya | 132 | 89 | 43 | + Sahams |
| 10 Karma | 130 | 82 | 48 | + vocation lookup tables |
| 11 Labha | 85 | 59 | 26 | + source-of-gains lookup |
| 12 Vyaya | 102 | 61 | 41 | — |
| **Total** | **~1,648** | **~1,128** | **~450** | + 5 lookup/numeric sub-systems |

**Key finding:** §5.3 already covers ~80% of evaluable rules. The remaining ~20% is **not
scattered** — it is a convergent set of ~20 predicate families, ~6 of which recur in nearly
every house and are therefore CRITICAL. Plus four *non-predicate* layers the algebra must
NOT try to absorb (lookup tables, numeric sub-engines, the timing layer, output meta-modifiers).

## 2. The four layers (a rule is NOT always a boolean predicate)

The single most important architectural takeaway: rules fall into **four kinds**, and only
the first belongs in `doctrine/conditions.py`.

1. **Condition predicates** (boolean over a static chart) → the algebra. ~1,128 rules.
2. **Lookup tables** (planet/sign → category string): disease organ/tridosha/season (H6, 45 rows),
   decanate cause (H8, 36), vocation kind (H10, 14+), source-of-gains (H11, 7), confinement-mode
   (H12), drekkana financial (H2, 36). → `doctrine/lookups/*.py` **data**, returned as result
   metadata, never boolean-evaluated.
3. **Numeric sub-engines** (compute a number/point, then feed predicates): Pindayu/Amsayu ayus
   (H8), Beeja/Kshetra fertility sphuta (H5), Special Dhana Lagna (H2), Kuja-Dosha units (H7),
   Sahams (H9), co-born count (H3/H11), child count (H5). → `primitives/sphutas.py` etc.;
   their *outputs* become predicate arguments.
4. **Timing layer** (evaluated at a date, not natal): two-level MD×AD activation, tara,
   gochara, dasha-phala. → `judges/timing.py` with its own mini-vocabulary (§5). Present in
   **every** house; the spec already scopes this separately.
5. **Output meta-modifiers** (transform another rule's polarity): Bhavartha-Ratnakara inversion
   (H12), benefic-aspect-confers-capacity-not-profession (H10). → `proforma.py` post-pass, not
   a condition.

## 3. CRITICAL predicate gaps (recur in ≥5 houses — add before Phase 2)

| # | Predicate family | Houses | Signature |
|---|---|---|---|
| C1 | **Generalized origin frame** — `FROM` any of {planet, house, special-point, navamsa-lagna, karakamsa} + house arithmetic | 1,4,5,7,9,11,12 | `HouseFrom(origin, n) -> house` · `InHouseFrom(p, origin, n)` where origin ∈ Planet\|House\|SpecialPoint. (Generalizes §5.3 `FROM(p)` beyond karaka.) |
| C2 | **Relative position within a varga** — "X is 6/8/12 from Y in D9" | 1,3,4,5,7,9,10,11 | `InVargaHouseFrom(p, ref, houses, varga=D9) -> bool` · `VargaHouseDist(p, ref, varga) -> int`. The single **most-recurrent** gap (the "6/8/12-from-Navamsa-Lagna / from-co-lord" overlay). |
| C3 | **Nakshatra layer** — star-lord, tara distance | 1,2,4,8,9,11,12 | `NakshatraOf(p) -> int(1..27)` · `NakshatraLordOf(p) -> Planet` · `InStarOf(p, lord)` · `TaraOf(p, from=Moon) -> {janma..param_mitra}` · `TaraPosition(p, from) -> int`. Decisive for father/longevity timing; entirely absent from §5.3. |
| C4 | **Functional nature (chart-relative)** — "evil/good planet" is per-Lagna | 1,2,10,11 (implicit all) | `FunctionalNature(p) -> {benefic,malefic,neutral,yogakaraka,maraka}` · `IsYogaKaraka(p)` · `KendradhipatiDosha(p)` · `IsFunctionalMalefic(p)`. Reads `doctrine/functional_nature.py`. Without it, "aspected by evil planets" stays ragged. |
| C5 | **Neecha-bhanga as a first-class predicate** (not just a §5.5 gate) | 1,3,5,7,9,10,11 | `NeechaBhanga(p) -> bool` · `EffectiveDignity(p)`. Some rules' *condition* IS the bhanga (debil lord + cancellation → favourable); also gates `Strongest()`/scoring. |
| C6 | **Parivartana / Exchange** (mutual sign exchange) — named | 2,4,6,7,8,10,12 | `Parivartana(h1, h2) -> bool` · `Exchange(a, b) -> bool`. Composable from `LordOf`+`InSign` but treated as a first-class yoga (Vipareeta trigger). |
| C7 | **Timing vocabulary** (the whole timing layer) | ALL | `DashaLordIs(p)` · `BhuktiLordIs(p)` · `Influences(p, house)` (the 6–7 governing factors) · `DashaQuality(md, ad) -> {par_excellence,limited,feeble}`. Lives in `judges/timing.py`; (chart,date) context. |

## 4. HIGH gaps (recur in 2–4 houses)

| # | Predicate | Houses | Signature |
|---|---|---|---|
| H1 | **Subhakartari** — generalize `HemmedBy` to a planet-class | 1,7,9,10 | `HemmedBy(target, klass=malefic\|benefic)`. Papakartari is the malefic case; subhakartari (benefic) is the protective mirror. |
| H2 | **SignElement** (fire/earth/air/water) | 6,8,9,10,12 | `SignElement(s) -> {fire,earth,air,water}` · `IsWaterySign(s)`. §5.3 has modality+parity, not element; "watery sign" is pervasive. |
| H3 | **Planet gender** | 3,5 | `Gender(p) -> {masculine,feminine,neuter}` (+ gendered-navamsa counting). Required for sex-of-sibling/child. |
| H4 | **MoonPhase** | 3,4,6,8,12 | `MoonPhase() -> {waxing,waning}`. Distinct from `Combust`. |
| H5 | **Sub-varga dignity / grades** | 4,7,8,10,11,12 | `VargaDignity(p, varga)` · `ShashtiamsaClass(p) -> {benefic,malefic,cruel,…}` · `VaiseshikamsaGrade(p) -> int`/`bool` (cross-varga count) · Gopura/Simhasana grades. |
| H6 | **House-class shorthand** | 2,3,4,9,10 | `InHouseClass(p, {kendra,trikona,dusthana,upachaya,maraka})`. Pure sugar over `InHouse` but very high-frequency; reduces encoding error. |
| H7 | **Mutual-relationship predicates** | 1,2,6,7,8 | `MutualAspect(a,b)` · `MutualKendra(a,b)` · `Dwirdwadasa(a,b)` (2/12) · `Shashtashtaka(a,b)` (6/8). |
| H8 | **Node-as-dispositor substitution** | 6,8,9 | `SanivadRahu()` / `KujavadKetu()` / `NodeSubstitute(p) -> Planet`. Rahu→Saturn, Ketu→Mars for maraka/cause. |
| H9 | **Vipareeta / dusthana-inversion** | 6,10,11,12 | `Vipareeta(lords, in_house)` · a `dusthana_inverts(signification)` flag (H6 enemy-axis spine: malefic-in-6 protects). |
| H10 | **Filtered/aggregate counts** | 1,2,10,11 | `CountInHouse(h, filter=malefic\|benefic)` · `CountAspecting(target, exclude=[])` · `AtLeastN(conds, n)`. |
| H11 | **Atmakaraka + Karakamsa** | 10,12 | `Atmakaraka() -> Planet` (highest deg-in-sign, 7-karaka per CLAUDE.md) · `Karakamsa() -> sign` · `FROM(karakamsa)` frame. |
| H12 | **Lordship identity** | 3,4 | `LordIs(h, p) -> bool` (i.e. `LordOf(h)==p`), for karaka-collapse rules. |

## 5. MEDIUM / LOW gaps (localized)

`Eclipsed(p)` (node conjunction; H8,H11) · `PlanetaryWarLoser(p)` (H8,H11) · `BhavaSandhi(p)`
(H10 — disables results; note Phase-0 already computes `bhava_sandhi`) · `MovingTowardDebility(p)`
(H7) · `InRasiSandhi(p)` (H7) · `ExactDegree(p, [..])` (H6 imprisonment gate) · `InDrekkana(p, n)`
+ `DrekkanaType(n)` + `DrekkanaCell(sign, dec)` (H8 — the 22nd-drekkana/decanate machinery) ·
`Saham(name)` (H9) · `Seershodaya/Prushtodaya(sign)` (H8) · `IsKeetaRasi(s)` (H12) ·
`EqualStrength(p, q, tol)` (H12) · `CommonSignPreponderance()` (H7,H12) · `EyeLaterality` tag (H12) ·
`Sushka/Watery planet` sets (H1) · `IsSushkaSign` (H1).

## 6. DEFERRED (out of single-chart v1 scope)

**Cross-chart / synastry** predicates: H4 joint-fertility, H5 both-spouses, H7 synastry S1–S7,
H9 native↔father-chart. Consistent with spec §13 (Kuja-Dosha synastry deferred). v1 is
single-chart; a `chart_b` parameter + cross-chart relations are a post-v1 module.

## 7. Finalized `doctrine/conditions.py` v1 predicate set

The algebra to implement (= §5.3 core + the CRITICAL/HIGH additions above; LOW added on demand):

```
Boolean:     And · Or · Not · AtLeastN(conds, n)
Position:    InHouse(p,n)[=Chalita bhava] · InRashiHouse(p,n) · Occupies(p,h) · InSign(p,s)
             InHouseFrom(p, origin, n) · HouseFrom(origin, n)          # C1
             InVargaHouseFrom(p, ref, houses, varga) · VargaHouseDist(p, ref, varga)  # C2
             InHouseClass(p, {kendra,trikona,dusthana,upachaya,maraka})  # H6
Lordship:    LordOf(h).In(n) · LordIs(h,p) · DispositorOf(p) · DispositorChain(p)
             NavamsaLordOf(p) · DrekkanaLordOf(n,from) · NakshatraLordOf(p)   # C3
Relations:   Aspects(a,b) · Conjunct(a,b, orb=None) · MutualAspect(a,b) · MutualKendra(a,b)
             HemmedBy(target, klass=malefic|benefic)   # H1 (papakartari + subhakartari)
             Parivartana(h1,h2) · Exchange(a,b) · Dwirdwadasa(a,b) · Shashtashtaka(a,b)   # C6,H7
Dignity:     Dignity(p, varga=D1) ∈ {exalt,debil,own,moolatrikona,friend,enemy,neutral}
             Combust(p) · Retrograde(p) · Vargottama(p, in=d9|d3|d60) · Eclipsed(p)
             NeechaBhanga(p) · EffectiveDignity(p)        # C5
             ShashtiamsaClass(p) · VaiseshikamsaGrade(p)  # H5
Functional:  FunctionalNature(p) · IsYogaKaraka(p) · KendradhipatiDosha(p)   # C4
Nakshatra:   NakshatraOf(p) · InStarOf(p,lord) · TaraOf(p, from) · TaraPosition(p, from)   # C3
Sign attrs:  SignModality(s) · SignParity(s) · SignElement(s) · Gender(p) · Gender(s)   # H2,H3
Aggregates:  Strongest(among=[…]) · Weakest(among=[…]) · CountInHouse(h, filter=any|malefic|benefic)
             CountAspecting(target, exclude=[]) · Count(navamsas_of=…)
Luminary:    MoonPhase() ∈ {waxing,waning}                # H4
Points:      Sphuta(beeja|kshetra|special_dhana|pranapada) · Saham(name)
             Atmakaraka() · Karakamsa()                   # H11
Frames:      LAGNA · MOON · SUN · KARAKA(p) · FROM(origin) · STRONGEST_OF([...]) · KARAKAMSA
Ragged:      is_fortified(p) · is_afflicted(p) · well_disposed(lord)   # canonical, GBB-backed
```

**Companion data (NOT predicates):** `doctrine/lookups/` (disease, vocation, source-of-gains,
decanate-cause, confinement-mode, drekkana-financial); `primitives/sphutas.py` (ayus, beeja/
kshetra, special-dhana, kuja-units, sahams, co-born/child counts); `judges/timing.py` (the
timing vocabulary C7); `proforma.py` meta-modifiers (Bhavartha-Ratnakara, capacity-not-profession).

## 8. Spec amendments (fold into §5.3 / §6)

1. **§5.3 frames**: generalize `FROM(p)` → `FROM(origin)` (planet/house/point/karakamsa); add `KARAKAMSA`, `SUN`.
2. **§5.3**: add the C1–C6 + H1–H12 predicate families above.
3. **§5.3 semantic lock**: every position predicate evaluates **Chalita bhava** by default; `InRashiHouse` is the explicit whole-sign variant (the "Bhava not Rashi" rule, surfaced in H1).
4. **§5.2 RuleRecord**: add `kind="lookup"` and `kind="numeric"` alongside evaluable/descriptive; add an optional `polarity_inverts` flag for meta-modifier rules.
5. **§6/§8**: confirm the timing vocabulary (C7) lives in `judges/timing.py` (chart,date) — not in the natal condition algebra.
6. **Effort note**: ~1,128 evaluable rules need conditions (more than the §13 estimate of ~350 — that figure counted rule-*records*, not the atomic fortified/afflicted/placement expansion). The evaluable/descriptive/lookup split keeps this tractable: ~450 descriptive + ~80 lookup/numeric need NO condition encoding.
