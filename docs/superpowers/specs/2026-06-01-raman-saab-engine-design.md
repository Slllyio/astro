# Raman Saab — Engine Design Spec

**Date:** 2026-06-01
**Status:** Design (pre-implementation)
**Topic:** A fully independent, deterministic engine that replicates B.V. Raman's
*How to Judge a Horoscope* (Vols I & II) methodology, house by house.

> Built against the audited methodology corpus in
> [`docs/raman_saab/methodology/`](../../raman_saab/methodology/README.md) — 700+ cited
> rule-records + the chart-wide method overview. That corpus is the single source of truth;
> this spec is how it becomes code.

---

## 1. Goals & non-goals

**Goal:** Given birth data, deterministically produce a structured, fully-cited
house-by-house reading in Raman's method — promise + dasha-timed timeline + longevity —
faithful enough that Raman's own published example charts reproduce his verdicts.

**Non-goals (v1):** LLM narration; Prashna (horary) and Varshaphala (annual) — separate
Raman books, out of scope; KP; any ML/DKP scoring; mutating or depending on the repo's
blended engine.

## 2. Locked decisions (from brainstorming)

| # | Decision |
|---|---|
| D1 | **Fully independent engine** `app/raman_saab/`; reuses only doctrine-neutral math (see §4.6 allowlist). Owns all judgment. |
| D2 | **Ayanamsa configurable, default Raman** (`SIDM_RAMAN`); Lahiri optional. Confined to the package; never mutates the global ayanamsa. |
| D3 | **Output = deterministic structured proforma** (JSON + Markdown), no LLM. Pure function `chart → RamanReading`. |
| D4 | **Scope = everything**: 12 houses + longevity (Ayur-nirnaya) + dasha timing + divisional annotation. Phased build (§11). |
| D5 | **Surfaces:** CLI + API + Family-Charts portal tab, all over one pure library function. |
| D6 | **Timing:** promise + full Vimshottari MD/AD activation timeline per matter. |
| D7 | **Source already on disk** — index the existing Raman corpus; no scraping. |

**Doctrine divergences from the repo (intentional, faithful to Raman):**
Bhava (Chalita) judged not Rashi · Rahu/Ketu cast only the 7th aspect (no 5/9) ·
fixed naisargika karakas (no Jaimini chara) · real Shadbala re-derived to Raman's
*Graha & Bhava Balas* · Raman ayanamsa. Each is a cited constant with a guard test.

## 3. Architecture (layer map, strict downhill imports)

```
chart/        birth data → RamanChart  (ephemeris @ chosen ayanamsa; Chalita cusps; D9; upagrahas; arudhas)
  ↓
doctrine/     Raman-as-data: significations, karakas, functional_nature, drishti(nodes=7th),
              relationships, ayus_tables, yogas/, sources(citation registry),
              rules/ (the RuleRecords), conditions (the predicate algebra)
  ↓
primitives/   FACTS (no verdict): chalita_bhava · dignity · navamsa(vargottama) ·
              shadbala(REAL, GBB) · bhava_bala · ishta_kashta · dispositor · maraka ·
              ashtakavarga · balarishta · combustion(graded) · sphutas(beeja/kshetra/…)
  ↓
judges/       chart_overview · house_template + house_01..12 · longevity · timing · divisional
  ↓
proforma.py   assemble RamanReading (per-signification sub-verdicts + ledgers)
  ↓
render/       json_render · markdown_render (book-style worksheet, prints cusp degrees)
  ↓
surfaces      cli.py · app/api/raman_routes.py · portal tab
```

## 4. Data model (`chart/`)

**Revision (self-review #4):** carries the upagrahas, Arudhas, and death-points that rules reference.

```python
@dataclass(frozen=True)
class PlanetPos:
    name: str
    lon: float                 # sidereal, chosen ayanamsa
    sign: int                  # 1..12
    rasi_house: int            # whole-sign from Lagna → lordship, sign-drishti, yogas
    bhava: int                 # CHALITA, by cusp → RESULT judgment
    bhava_sandhi: bool         # on a cusp junction → "produces no effect"
    nakshatra: int; pada: int
    retrograde: bool           # feeds Chesta-bala
    combust_fraction: float    # 0..1 graded by orb (Venus/Saturn exempt in ayus)
    navamsa_sign: int; vargottama: bool
    dispositor: str
    shadbala_rupas: ShadbalaBreakdown   # 6 components + total, Raman/GBB
    ishta: float; kashta: float

@dataclass(frozen=True)
class RamanChart:
    ayanamsa: str                       # "raman" (default) | "lahiri"
    jd_ut: float
    asc_sign: int; asc_lon: float
    bhava_madhyas: tuple[float, ...]    # 12 Sripati cusps
    bhava_sandhis: tuple[float, ...]    # 12 junctions
    planets: Mapping[str, PlanetPos]    # Sun..Ketu
    upagrahas: Mapping[str, SpecialPoint]   # Gulika, Mandi (FULL position) — H5/H6/H12 rules
    arudha_lagna: SpecialPoint              # H10/H12 rules (full position, for conjunction tests)
    karakamsa: SpecialPoint                 # Atmakaraka's navamsa as a position — H12 Ketu-from-karakamsa
    maraka_points: MarakaPoints
    balarishta: BalarishtaState
    birth: BirthData

# Supporting structures (review fix: were referenced but undefined)
@dataclass(frozen=True)
class SpecialPoint:                         # upagrahas, Arudha, Karakamsa — full positions
    name: str; lon: float; sign: int; bhava: int; navamsa_sign: int

@dataclass(frozen=True)
class MarakaUnit:
    graha: str; tier: Literal["primary","secondary","tertiary"]; strength_rank: int

@dataclass(frozen=True)
class MarakaPoints:
    units: tuple[MarakaUnit, ...]           # 2nd/7th lords + occupants + associates, tiered
    drekkana22_lord: str; navamsa64_lord: str

@dataclass(frozen=True)
class BalarishtaState:
    applies: bool; cancelled: bool; reasons: tuple[str, ...]

@dataclass(frozen=True)
class SpanClass:
    label: Literal["balarishta","alpayu","madhyayu","purnayu"]
    method: Literal["pindayu","nisargayu","amsayu","combination"]
    years: float | None
    agreement: bool                         # do the combination & mathematical tracks agree?

@dataclass(frozen=True)
class ShadbalaBreakdown:                     # the six-fold strength, in Rupas (GBB Ch.3–8)
    sthana: float; dig: float; kala: float   # position · direction · time
    cheshta: float; naisargika: float; drik: float   # motion · natural · aspect
    total: float                             # sum, vs the planet's min-required threshold
```

**4.6 `app/core` reuse allowlist (self-review #7):** the adapter MAY import only —
ephemeris position calls (with a *local* ayanamsa set, never the global), varga/Navamsa
geometry, exalt/debil/own-sign longitude tables, and Vimshottari dasha-date math.
**Shadbala is re-derived** in `primitives/shadbala.py` to Raman's *Graha & Bhava Balas*
(the on-disk `graha_bhava_balas_raman/` Ch.3–10 component definitions) — NOT imported from
`app/core/shadbala.py` — validated by a fixture of 5 hand-verified charts at **±1 rupa per
component**. A guard test (importlib-based, CI-enforced) asserts the package never imports
`app/core/{bhava_judge,reading_composer,drishti_argala,dkp_*,yogas,shadbala}` and never
mutates the global ayanamsa. **Fidelity note:** the re-derivation must follow Raman's *own*
component definitions — notably his **Dig-bala boundaries** and **Kala-bala** (paksha/hora/
ayana) defaults — which differ from modern blended Shadbala; forcing standard algorithms will
silently shift rupas and flip strength rankings. The ±1-rupa fixture pins this.

## 5. Doctrine-as-data (`doctrine/`)

### 5.1 Cited lookup tables
`sources.py` (citation registry) · `significations.py` · `karakas.py` (fixed + multi-karaka
per house) · `functional_nature.py` (per-Lagna table + generating rules) · `drishti.py`
(**nodes = 7th only**) · `relationships.py` (friendships, exalt/debil degrees, combustion
orbs) · `ayus_tables.py` (Pindayu/Amsayu terms, harana fractions+exemptions, span bands,
per-Lagna maraka table) · `yogas/` (catalogue from *Three Hundred Combinations* + bhangas).

### 5.2 The `RuleRecord` (the data form of every corpus combination)

```python
@dataclass(frozen=True)
class RuleRecord:
    id: str                       # "H7.B.23a"
    house: int; signification: str   # which matter of the house this speaks to (§6.1)
    group: str
    kind: Literal["evaluable","descriptive"]   # SELF-REVIEW #2
    condition: Condition | None   # predicate tree (evaluable); None for descriptive
    placement: Placement | None   # the placement a descriptive rule attaches to
    fortified: str; afflicted: str | None
    frame: Frame                  # LAGNA | MOON | KARAKA(p) | FROM(p) | STRONGEST_OF([...])
    varga: str                    # D1 | D9 | D7 ...
    navamsa_override: str | None
    timing: tuple[Trigger, ...]
    polarity: Polarity            # BENEFIC | MALEFIC | NEUTRAL | MARAKA
    source: Citation              # (work, line) — backlinks into the corpus
```

**Evaluable vs descriptive (self-review #2):** *evaluable* rules have a computable
`condition` that fires/doesn't; *descriptive* rules are narrative outcomes attached to a
`placement` (e.g. "Saturn in 7th → wife older/ugly, marriage to widow") — surfaced with
their citation whenever that placement holds, not boolean-scored. This makes Phase 2
tractable: only evaluable rules need precise condition encoding.

### 5.3 The condition algebra (`doctrine/conditions.py`) — enriched (self-review #3)

```
Core:        InHouse(p,n) · LordOf(h).In(n) · Occupies(p,h) · Aspects(a,b) · Conjunct(a,b)
             HemmedBy(t,[malefics]) · Dignity(p)∈{…} · Combust(p) · Retrograde(p)
             Vargottama(p) · InNavamsaOf(p,sign) · DispositorOf(p) · And/Or/Not
Added:       Strongest(among=[…]) / Weakest(among=[…])        # superlatives ("strongest in house h")
             Count(navamsas_of=…) → int · CountInHouse(h)     # sibling/child/co-born counts
             Sphuta(beeja|kshetra|special_dhana|pranapada)    # computed points
             SignParity(p)∈{odd,even} · SignModality(p)∈{movable,fixed,common}
             InSign(p, sign) · InUpagraha(gulika|mandi, h)
             DrekkanaLordOf(n, from=lagna|moon) · NavamsaLordOf(p) · DispositorChain(p)
             Vargottama(p, in=d9|d3|d60)                       # vargottama variants
Frames:      a rule's origin may be LAGNA, MOON, KARAKA(p), an arbitrary FROM(p)
             (e.g. "from Venus"), or STRONGEST_OF([Lagna,Moon,Sun]) — the engine evaluates
             from that origin and records which origin won (review fix: multi-frame rules).
All predicates evaluate relative to a (frame, varga) pair.
A **pre-Phase-1 predicate audit** (categorize all 700+ corpus rules → required predicates)
finalizes this algebra before coding, so encoding never hits an inexpressible rule.
```
*Ragged conditions* ("well disposed", "fortified", "any beneficial aspect") resolve to
**canonical cited predicates** — `is_fortified()`, `is_afflicted()`, `well_disposed()` —
defined once from dignity + Shadbala threshold + benefic aspect + placement (overview §3,
GBB thresholds). No rule stays vague.

### 5.4 Encoding workflow (self-review #2)
Parse each `house_NN_*.md` table → skeleton `RuleRecord`s (id, house, signification,
group, fortified/afflicted text, frame, varga, source) auto-populated; then hand/agent-fill
`condition` for `kind="evaluable"` rows. Descriptive rows need no condition. A test asserts
**every record's `source` cites a line that exists in the on-disk corpus.**

### 5.5 Cancellations (bhangas) & orbs (review fix #10/#11)
`doctrine/bhangas.py` holds the cancellation/inversion rules — **neecha-bhanga**,
**kemadruma-bhanga**, **balarishta-bhanga**, **subha/papa-kartari** softening, **parivartana**
(exchange), and the **Vipareeta** + **Bhavartha-Ratnakara** polarity inversions — each cited.
They run as a **pre-scoring gate**: a rule's chosen branch is re-evaluated after bhangas
(a debilitated lord with neecha-bhanga is not scored afflicted). Conjunction uses a circular
orb `min(diff, 360−diff)` with per-planet defaults in `relationships.py` (the ~12–18° gates
the corpus relies on for "free of conjunction", e.g. H1 Chart 14 Sun ~18° from Saturn).

## 6. The house judge (`judges/`)

### 6.1 Per-signification sub-verdicts (self-review #1)
Each house declares its significations and the karaka routing for each (e.g. 4th →
{mother: Moon, property: Mars, education: Jupiter+Mercury, vehicles: Venus, happiness:
Moon}). The judge produces a **sub-verdict per signification**, each judged through the
house + lord + *its own* karaka. This is Raman's karaka-reconciliation principle made
structural.

### 6.2 `house_template.judge_house(chart, n) -> HouseProforma`
```
1. PILLAR FACTS (primitives/, per frame×varga): house / lord / karaka(s) fact-sets;
   karaka judged AS A LAGNA (from-karaka frame).
2. FIRE evaluable RuleRecords; attach descriptive RuleRecords whose placement holds;
   choose fortified/afflicted branch via is_fortified()/is_afflicted(); apply navamsa_override.
3. DUAL FRAME — run from LAGNA and from MOON (overview §5 leads with the stronger).
4. ARBITRATE per signification via the StrengthLedger.
5. EMIT per-signification sub-verdicts + evidence + timing.
```

### 6.3 StrengthLedger & verdict synthesis (self-review #6)
Ledger fields: `bhava_bala, lord_shadbala, karaka_shadbala, navamsa_status,
fired_benefic[], fired_malefic[], karaka_intact, maraka_active`.
- **Pillar precedence:** Bala → Navamsa confirmation → benefic/malefic assoc & drishti → dasha.
- **Karaka veto:** `karaka_intact=False` (combust+debilitated+maraka-hit) caps the verdict.
- **Navamsa modulates, never overturns** a decisive Shadbala (strong-rasi/weak-D9 = "starts well, fades").
- **Rule-vs-rule contradiction:** when benefic and malefic rules both fire, the verdict is
  `mixed` and *both* are surfaced with citations — contradiction is shown, never hidden.
- **Verdict is an explicit ordinal**, not a score: `{favourable | mixed | afflicted |
  insufficient-evidence}`, computed by this **defined decision rule** per signification:
  1. `karaka_intact == False` → **afflicted** (karaka veto, overrides all).
  2. else, after the bhanga gate (§5.5): both fired_benefic and fired_malefic non-empty
     → **mixed** (surface both, cited).
  3. lord & karaka both ≥ their min-required Shadbala AND bhava_bala strong AND no malefic
     fired → **favourable**.
  4. lord or karaka below min-required AND (malefic fired OR bhava_bala weak) → **afflicted**.
  5. no rule fired AND pillars neutral → **insufficient-evidence**.
  Navamsa status shifts a *borderline* case one step (confirm / "starts well, fades") but
  never overturns a decisive Shadbala. Thresholds (min-required Shadbala per planet; bhava_bala
  strong/weak bands) are **GBB constants tuned only to satisfy the named-historical goldens** —
  never hand-set to force a particular reading. No false-precision number is exposed.

### 6.4 House-specific pre-passes & cross-cutting gates
Per-house: H5 Beeja/Kshetra fertility · H2 Special Dhana Lagna · H6 dusthana-inversion /
Vipareeta · **H7 Kuja-Dosha** (single-chart Mars-affliction scoring via the cited numeric
grid; couple-matching synastry is a flagged optional extra) · H8 → longevity sub-engine ·
H12 Bhavartha-Ratnakara polarity flip + Ketu-from-karakamsa + **Bandhana-yoga** (confinement).
Cross-cutting: the **bhanga gate** (§5.5) runs before scoring every house; multi-frame rules
(`STRONGEST_OF`/`FROM`) are evaluated from each candidate origin and the winning origin is recorded.

## 7. Longevity sub-engine (`judges/longevity.py` + `doctrine/ayus_tables.py` + `primitives/maraka.py`)
Runs as a **pre-pass that gates the houses** (overview §8):
1. **Balarishta gate** (<8): test infant-mortality yogas; check bhangas; uncancelled ⇒ child track, stop.
2. **Span class — two ways, reconciled:** (a) combination banks (Alpa/Madhya/Purna);
   (b) mathematical — **select** method by strongest of Sun/Moon/Lagna (Pindayu/Nisargayu/Amsayu),
   compute terms, apply the 4 ordered haranas (each to the running remainder; Venus/Saturn &
   Mars/retro exemptions), → band (Balarishta<8 · Alpa 8–32 · Madhya 33–75 · Purna 75–120).
   **Reconciliation rule:** the combination/maraka track is **primary** (Raman's stated
   preference — maraka-on-Vimshottari "proved quite satisfactory"); Pindayu/Amsayu is
   **corroborative**. On disagreement, lead with the combination/maraka span, attach the
   mathematical span, set `SpanClass.agreement=False` — never average, never silently pick.
3. **Maraka** (primary/secondary/tertiary + per-Lagna table).
4. **Death timing** — maraka dasha/bhukti ∩ ayus-band, confirmed by transit over maraka points.

## 8. Timing & divisional
**Timing (`judges/timing.py`):** Vimshottari MD/AD timeline; per window the **two-level
activation** (both period-lords relate → par-excellence; one → limited; AD-only → feeble),
over the 7 governing factors; Tara + Gochara modifiers. Emits per-matter `TimingWindow[]`.
**Divisional (`judges/divisional.py`):** primary judgment on **Rashi + Chalita + Navamsa**
(what Raman uses); conventional per-matter vargas (D7/D10/D4/D24) reported as an *optional,
flagged* enrichment — never fabricated.

## 9. Output & surfaces
`RamanReading{chart, overview: ChartOverview, longevity, houses[12], timeline, citations[], meta}`.
`ChartOverview` = whole-chart pre-pass (stronger reference lagna/moon; functional nature;
yogakarakas; raja/dhana/arishta yogas; tenor). Renderers: `json_render` + `markdown_render`
(book-style worksheet, deterministic, prints cusp degrees). One pure function
`read_chart(birth, *, ayanamsa="raman") -> RamanReading` behind: **CLI** (`python -m
app.raman_saab`), **API** (`POST /raman/reading`), **portal tab** (safe-DOM; caches per
`(person, ayanamsa)`).

## 10. Error handling
Schema-validated input (fail fast); ephemeris errors wrapped at the adapter (only failure
point); **birth-time uncertainty flags reduced confidence** on cusp-dependent verdicts;
no rule fires ⇒ `insufficient-evidence`, never fabricated; errors logged with context,
never swallowed.

## 11. Testing (self-review #5: split goldens)
| Tier | Asserts |
|---|---|
| **Judge-goldens** | given *Raman's stated chart positions* → engine reproduces his verdict. **Exact** (tests doctrine, ayanamsa-independent). |
| **Adapter-goldens** | birth-data → chart matches Raman's printed chart. **Tolerance-banded** (±a few arc-min; tests astronomy). A verdict test must never fail over a 2′ ayanamsa difference. |
| **Longevity goldens** | Chart 33 → 86y 2m 20d · 34 → 68y 10m 5d · 35 → 7-2-1966 (to the day). |
| **Named-historical** | Gandhi, Hitler, JFK, Lincoln, Napoleon, Nehru, Indira, George VI, Elizabeth II — verdict == Raman's published outcome. |
| **Unit** | primitives vs GBB numbers; condition evaluator; each judge. |
| **Doctrine-lock guards** | global ayanamsa stays Lahiri · nodes cast only 7th · fixed-karakas-only · no forbidden `app/core` import · **every RuleRecord cites a real on-disk line**. |

Raman Saab has its **own Raman-ayanamsa fixtures** (not the repo's Lahiri baseline). Target 80% coverage.

### 11.1 Three-Tier Single-Ledger Harness (the golden-chart mechanism)
The ~370 example charts are **not** scattered fixtures. One ledger + one parametrized test:

- **Single source of truth:** `tests/fixtures/raman_goldens.jsonl` — one flat JSON record per
  chart: `{id, book, case_type, name, birth{dt,tz,lat,lon}, stated_positions{planet:{lon,bhava}},
  expected_verdicts{H10:{signification,verdict}}, expected_longevity?}`. Bulk-editable, searchable,
  schema-checkable.
- **Track A — Ephemeris sanity (astronomy):** read `birth`, run the adapter at the chart's
  ayanamsa, compare to `stated_positions` within **±5 arc-min** (absorbs Raman's manual rounding).
  An ephemeris/ayanamsa drift fails *this* track only — it never breaks doctrine tests.
- **Track B — Pure doctrine (astrology):** inject `stated_positions` **directly** via
  `RamanChart.from_stated_positions(...)` (bypasses the ephemeris entirely), run the judges,
  assert the per-signification ordinal == `expected_verdicts`. Absolute determinism: refactor the
  condition algebra / ledger with full confidence you're testing logic, not planetary math.
- **Tier 3 — Evidence-ledger snapshots:** the proforma's fired-rule-IDs + citations are
  snapshot-tested (`pytest-regressions`). When the algebra changes and N charts' *reasoning*
  shifts, inspect diffs and `pytest --snapshot-update` — never hand-rewrite N tests.

This requires `RamanChart.from_stated_positions(stated, *, ayanamsa)` — an alternate constructor
that takes book-stated longitudes/bhavas and derives the rest, so Track B and Tier 3 are
ephemeris-independent. Maintenance footprint: **one data file + one test script** for all ~370 charts.

## 12. Phasing
0 skeleton+adapter → 1 primitives(+GBB Shadbala) → 2 doctrine data(+condition algebra,
evaluable/descriptive) → 3 house judge+overview(per-signification, one house fully then
replicate) → 4 longevity → 5 timing+divisional → 6 proforma+renderers+surfaces → 7
golden-chart harness (~370 charts + named-historical).

**Orchestration (resolves the gate-vs-usable tension):** the house judges emit facts +
per-signification sub-verdicts **unconditionally**; `chart_overview` and `longevity` are
pre-passes whose output is applied as a **gate at `proforma` assembly time**, not inside the
judges. So Phases 0–3 give a usable **ungated** reading; Phase 4 longevity then overlays the
gate (Balarishta suppression, span-class context for H8, maraka timing). No judge depends on
a later phase.

## 13. Open questions / risks
- **MANDATORY pre-Phase-1 predicate audit:** categorize all 700+ corpus rules → the exact
  predicate set, finalizing `doctrine/conditions.py` (§5.3) before any coding. The single
  highest-leverage de-risking step (per the architecture review): prevents encoding thrash.
  The audit must also pin **edge-case semantics** for the aggregating predicates:
  `Strongest(among=…)` tie-breaking when two planets share Shadbala rupas (deterministic
  order: higher total → higher Cheshta → lower combustion → planet-index), and `Count()`/
  `CountInHouse()` behaviour on **empty houses / no qualifying planets** (returns 0, never errors).
- **Encoding effort:** ~350 *evaluable* rules need precise conditions — the dominant labor item; mitigated by the evaluable/descriptive split and the skeleton-parse workflow.
- **Kuja-Dosha scope:** v1 ships single-chart Mars-affliction detection; two-chart synastry
  (couple matching) is a flagged, optional, post-v1 extra.
- **Adapter fidelity at cusps:** SIDM_RAMAN t0 vs Raman's hand-computations (~1–3′) — handled by the judge/adapter golden split, but a few of Raman's oldest charts may need pinned positions.
- **Verdict-synthesis tuning:** the ledger→ordinal rule is heuristic; it must stay an honest *qualified* assessment, validated against the named-historical goldens, not presented as precision.
- **Upagraha/Arudha computation** (Gulika/Mandi, Arudha, Karakamsa) must be re-derived in-package (doctrine-neutral math) consistent with the chosen ayanamsa.
