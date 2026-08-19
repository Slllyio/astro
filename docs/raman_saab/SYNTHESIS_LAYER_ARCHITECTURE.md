---
title: "Integrated Interpretation Layer — architecture spec (A–M)"
kind: design
topic: report
measured: false
updated: 2026-08-18
tags: [raman-saab, design, synthesis, themes]
---
# Integrated Interpretation Layer — architecture spec

The engine answers *"what does each section say?"* well. It answers *"what does the
whole horoscope say when the sections are considered together?"* only in scattered,
partial ways. This spec designs the missing layer as **structured reasoning first,
prose second**, built entirely as a **read-only overlay** on the already-computed
`DetailedReport` — it consumes finished verdicts, never re-judges, and is byte-transparent
to the golden ratchet by construction.

Grounded in the 2026-08-18 subsystem map (`docs/raman_saab/` workflow record); every
anchor below is `file:line` from that verified pass. **One correction to the brief:** the
locked non-regression benchmark is **259/293 = 88.4% exact, 283/293 = 96.6% within-one,
10 real errors** (`tests/fixtures/golden_accuracy_baseline.json`), not 89.1%; the
Measured-Truth record proves that figure is a *ceiling*. The synthesis layer keeps it
byte-identical because it imports nothing into the verdict path.

---

## A. Current architecture diagnosis

The engine already has **six partial integrators**, each of which the new layer must
consume rather than duplicate:

| Integrator | What it unifies | The gap it leaves |
|---|---|---|
| `judgment_graph.build_judgment_graph` (`judgment_graph.py:94`) | all sections' *structural* relations (lord_of/occupies/aspects/karaka_of/timer_of) into one nodes/edges graph; `house_facts`, `planet_census` | not stored on the report; only a MODERN-bannered `NON_RAMAN_GROUPINGS` theme kind — **no first-class Raman-cited thematic cluster** |
| `synthesis.synthesize` (`synthesis.py:187`) | D1 + navamsa + matter-varga + AV + activation + transit into one line **per bhava** | per-matter, flat, one line each — **no cross-matter convergence** |
| `insight_digest.build_insight_digest` (`insight_digest.py:356`) | the fullest whole-chart re-read: governing/foundation/convergence/timing/insight/tension/distinctive | order is a **fixed chart-agnostic template**; not sequenced by *this* chart's dominant themes |
| `life_arc.build_life_synthesis` (`life_arc.py:142`) | ~12 biography themes | a flat re-read **list** — no convergence/tension across themes, no ranking, "introduces no judgment" |
| `detailed_report.build_plain_reading` (`:3690`) | 12 matters → five life-domain paragraphs | **thin** — weaves only dashboard verdicts + `period_pairing`; no yogas-on-house, no divisional testimony, no preponderance |
| `build_nichod` (`:3412`) + `tension_narrator` (`:40`, `house_dashboard_conflicts:1186`) | one distillation paragraph + a conflict layer | conflict grain is **house-vs-dashboard only** |

**Diagnosis:** all the *inputs* for genuine integration exist; the *wiring across
matters* does not. Nothing detects that the same planet or period drives two life areas,
reconciles a favourable monograph against an afflicted house rollup at theme grain, ranks
themes by this chart's own evidence, or exposes a traceable mechanism chain
(house→planet→yoga→varga→dasha→transit) with per-link provenance.

## B. Exact location of the missing layer

A new **overlay module** `app/raman_saab/theme_synthesis.py`, on the same side of the wall
as `synthesis_rules.py` (imports nothing in the D1 verdict path; imported only by report
composers — mirrors the `synthesis_rules.py:32-35` discipline). It is built **last** in
`build_detailed_report` (after digest / nichod / life_synthesis, ~`detailed_report.py:3811`)
so it can only re-read finished state. Single new field `DetailedReport.themes:
ThemeSynthesis|None` (since-v34, append-only). It sits **above** the technical sections in
the report and explains them; it removes nothing.

## C. Proposed data model

> **As-built note.** The roster shipped as a fixed twelve-bhava `_THEME_ROSTER` (one theme per
> bhava), not as a projection of the sixteen `varga_domains.DOMAINS`. A varga domain supplies a
> theme's `karakas`/`domain`/`source` where one is assigned; H8, H11 and H12 have no classical
> division and carry a plain description with no karakas and no citation.

Three frozen dataclasses, every field a passthrough or a re-read with an accessor string
for traceability:

```text
ThemeEvidenceLink (frozen)
  axis:        Literal['verdict','magnitude','state','dasha','varga','transit','yoga','citation']
  label:       str            # human label ("H10 rollup", "D9 navamsa", "Saturn MD lights H2/H11")
  value:       str            # the finding, verbatim ("afflicted", "confirms", "par excellence 2079-2098")
  lean:        str            # 'favourable'/'adverse'/'neutral' via insight_digest._lean_of — CORROBORATION only
  accessor:    str            # "r.proformas[9].rollup @ house_template.py:236" — the audit trail
  provenance:  str            # RAMAN_EXPLICIT / RAMAN_GENERAL_PRINCIPLE / CLASSICAL_NONCITABLE / STATISTICAL / MODERN_SYNTHESIS
  cite:        Citation|None  # only when the source object already carried one; the layer authors NO WORK:line

ThemeReading (frozen)
  theme_id:          str
  name:              str            # from _THEME_ROSTER (the varga domain supplies only
                                    # karakas/domain/source, and may be absent entirely)
  domain:            str
  houses:            tuple[int,...] # roster primary_house + the support houses that
                                    # survive _discover_support (evidence-gated)
  karakas:           tuple[str,...] # domain.karakas
  headline_verdict:  str            # PASSTHROUGH of pf.rollup / dashboard — never recomputed
  driver:            str            # rollup_driver(...)
  dominant_planets:  tuple[str,...] # from planet_census breadth ∩ this theme's houses
  links:             tuple[ThemeEvidenceLink,...]   # the mechanism chain, one per axis-signal
  convergence:       str            # VERY_HIGH / HIGH / MODERATE / MIXED / WEAK  (evidentiary, not probability)
  convergence_why:   str            # "5 of 6 axes agree favourable; D9 confirms; Saturn MD activates"
  contradictions:    tuple[Contradiction,...]
  activation_span:   str            # period_pairing_clause(r, houses)  — timed indication idiom, never decree
  varga_relation:    str            # confirms / strengthens / qualifies / modifies / contradicts / D9-only
  final_interpretation: str         # the synthesized sentence, traceable to links

Contradiction (frozen)
  kind:        str    # one of the taxonomy classes below
  poles:       tuple[str,str]       # the two findings, each with its accessor
  governing:   str    # the PREC-id that resolves it (INTERPRETATION_GUIDE['precedence'])
  resolution:  str    # the resolving sentence

ThemeSynthesis (frozen)
  themes:      tuple[ThemeReading,...]   # ranked by evidence strength
  spine:       tuple[str,...]            # theme_ids of the 3–5 dominant themes
  frame:       str                       # stronger frame (lagna/moon), from chart_overview
  portrait:    ExecutivePortrait         # the two-page opening
```

`ExecutivePortrait` gathers: temperament (from `psych`/deeptadi), the spine theme names,
the census-dominant actors (`planet_bios[0..2]`), strongest/weakest domains (from theme
convergence + `house_strength` rank), principal tension (highest-severity contradiction),
protective factors (bhanga / neecha-bhanga / benefic-relief flags already on ledgers),
current chapter and next chapter (`life_chapters` + the running-period boundary). No event
predictions.

## D. Proposed algorithms

`build_theme_synthesis(r)` runs six deterministic passes:

1. **Theme roster** — start from `varga_domains.DOMAINS` (16 canonical domains, each with
   `related_houses` + `karakas` + `domain`, `varga_domains.py:46`). Keep the domains the
   engine actually judges (intersect with the 12-matter dashboard + the specialist
   monographs present on `r`). No hardcoded per-chart themes.
2. **Evidence gather** — per theme, collect `ThemeEvidenceLink`s by reading (never
   recomputing): the house rollups for `houses` (`r.proformas[h-1].rollup` via
   `_lagna_ledger`), the matching dashboard/monograph verdict, yogas bearing on `houses`
   (`yoga_house_bearings`/`_detail` + `_yoga_record_lean`), D9 confirmation
   (`r.synthesis.matters[i].navamsa`), activation (`period_pairing`), subordinated transit
   (`r.dasha_transit` filtered to `houses`), strength/state (`shadbala_rupas`, `deeptadi`),
   and the fired cross-feature insights whose `links` touch `houses` (`r.insights`).
3. **Dominant actors** — `build_judgment_graph(r)` once; `planet_census` breadth ∩ theme
   houses gives `dominant_planets` — the *why* is the census breakdown itself, no invented
   score.
4. **Convergence** (§E) and **contradiction** (§F) classification per theme.
5. **Ranking** — themes ordered by evidence weight (convergence tier + centrality among the
   chart's top census grahas + network breadth + `digest` priority of any digest item whose
   houses overlap); the spine is cut at the largest drop in the ranking, 3–5 themes.
   *(As-built: the original design multiplied by axis count. Measured, every theme carries
   the same 5–6 axes, so that term was a constant and was replaced.)*
6. **Portrait + spine assembly**, then prose (§ built via the Evidence pipeline, not here).

## E. Scoring / convergence methodology (evidentiary, never probability)

Convergence is a **count of agreeing vs opposing evidence axes**, not a number and not a
likelihood. For a theme, tally the `lean` of its links across the independent axes
{house rollup, lord/frame verdict, dashboard/monograph verdict, D9 navamsa, yoga lean,
preponderance status}:

- **VERY_HIGH** — ≥5 axes present and all agree with `headline_verdict`, D9 confirms, and
  an activation window exists.
- **HIGH** — ≥4 agree, ≤1 opposes.
- **MODERATE** — majority agree, one substantive opposing axis.
- **MIXED** — roughly even split (this is the *honest* default for most charts — the median
  chart carries 19 afflicted AND 31 favourable significations simultaneously, CLAUDE.md ★★).
- **WEAK / INSUFFICIENT** — <3 axes present.

`convergence_why` states the tally in words. **Both poles are always reported** — a theme
never suppresses its opposing axis; `r.info.sentence` (the population-honesty frame) is
attached so convergence is read as evidentiary agreement, not destiny. Magnitude/state
links carry `lean` as corroboration only and can never flip `headline_verdict`.

## F. Contradiction-resolution methodology

The brief's classes A–H map onto **concrete codebase signals**, each resolved by citing an
existing precedence rule (`INTERPRETATION_GUIDE['precedence']`, `interpretation_guide.py:23`):

| Class | Detected from | Governing |
|---|---|---|
| B. Different levels (house vs sub-matter) | `house_dashboard_conflicts` (`:1186`): dashboard verdict ≠ bhava rollup | PREC-1 (matter judged by its dedicated reader) |
| D. House condition vs sub-matter | `signification_tenor_split`/`TenorSplit` (`:752`) — split-status within a house | PREC-3 (the house's weakest decided matter drives the headline) |
| E. Strength vs beneficence | `is_powerful`==True AND rollup=='afflicted' | GBB-9 note (strong house delivers its difficulty with force) |
| F. General vs divisional | rollup ≠ `navamsa_status` (D9) | PREC-11 (the D1 core decides, the divisional corroborates). *Corrected from PREC-5, which governs Laghu Parashari timing bands, not divisionals.* |
| G. Primary vs corroboration | a RAMAN-band link opposed by a CLASSICAL/AV-band `FiredInsight` | PREC-4 (Raman > classical > AV, the `detect_synthesis` sort order) |
| H. Population vs doctrine | `CalibratedEntry.inverted_warning` / a percentile opposing the verdict | PREC-9 (the overlay may invert *confidence*, never a verdict) |
| C. Natal promise vs timing | favourable rollup but the theme's houses `not lit` in the running period | timer doctrine (promise ≠ current activation) |

Every contradiction stores both poles *with their accessors*, the governing PREC-id, and a
resolving sentence. Unresolvable ones are marked, not hidden. The archetypal case
("H4 afflicted" ≠ "mother afflicted") is exactly class B → PREC-1.

### F.1 Cross-checks are laid on a cited ladder — and deliberately not graded

Each theme also carries a `DissentSummary`: the *inventory* of every independent cross-check on
that bhava, each placed at its own **cited** reliability tier with the PREC-id that governs it.

| Cross-check | Tier | Independent? | Governing |
|---|---|---|---|
| the bhava's own testimony ledger | D1 core (lord / karaka / navamsa), HTJAH-I:983-991 | **No** — these are the verdict's own inputs restated by name | PREC-3 |
| the assigned division | corroborating (the D1 core decides) | Yes | PREC-11 |
| Ashtakavarga | lower-reliability tier, on Raman's own caveat ("equally important. But, it does not seem to be quite reliable", HTJAH-II:4453-4456) | Yes | PREC-4 |
| the Jaimini/karmic lens | **outside the cross-checks entirely** — walled, recorded in `walled_note` | n/a | wall |

**No aggregate confidence grade is produced, by design.** An earlier version scored a bhava
*settled / qualified / seriously contested* by counting how many cross-checks dissented. That was
invented arithmetic, and three findings already in this repo kill it:

1. `docs/raman_saab/COMPARATIVE_WEIGHING.md:52-56` — head-counting influences was measured
   against Raman's own reasoning on all seven Type-A cases and **held 0 of 7**: *"Raman does NOT
   head-count influences."*
2. `detailed_report.py` (HouseTestimonies) already records, with citation, that *Raman states no
   numeric N-testimonies rule (HTJAH-I:495 says only "all these must be properly weighed")* — so
   any 0/1/2 cutoff is exactly the class of invented threshold a doctrine review strikes out.
3. `report_html.py` states the witnesses *are NOT independent votes: lord, karaka and navamsa are
   the verdict's own inputs restated by name* — so the testimony ledger cannot be tallied as an
   independent dissenter at all without double-counting the verdict.

The tiers are Raman's; the arithmetic would have been ours. `contested_themes` is therefore the
plain inventory of themes carrying **any** cross-check that reads against the verdict — no `>= 2`
threshold — and every surface names the dissent at its tier rather than scoring it.

## G. Theme-discovery methodology

Themes are **derived from the engine's own domain map**, not invented: `varga_domains.DOMAINS`
already encodes which houses + karakas + varga belong to each life domain (wealth, career,
marriage, children, home, learning, health, longevity, spirituality, …). A theme is kept if
the engine judges it (dashboard entry or monograph present). Networks emerge naturally:
because a domain's `related_houses` can overlap another's, and `planet_census`/`yoga_house_bearings`
attach the same planet or yoga to both, the layer *discovers* (does not assert) that e.g.
a wealth theme (H2/H11) and a career theme (H10/H2/H11) share H2 and possibly a dominant
planet. Nabhasa/Akriti whole-chart yogas (which resolve no house — `_yoga_planets`→None) are
rendered as **disclosed coverage-gap nodes**, never dropped or force-attached.

### G.1 The span frames the reading (PREC-8)

`LongevityFrame` is built FIRST and rendered first, because that is Raman's own order:
*"first establish the band by combination, THEN fix the period by the marakas. The numeric span
is a cross-check, never a prediction of death"* (HTJAH-II:4465-4472, PREC-8). Before this the
synthesis named forward windows out to the 2040s without once asking whether they sat inside the
span the engine had already computed — the band was a chapter beside the reading rather than the
frame around it.

What it does: states the band (`r.longevity_class`, harmonised label) with the ayurdaya number as
a **cross-check**, tests every window the reading names against the span, dates each theme's own
window at its ordinal year of life (`activation_in_span`), and names Raman's step two — the
maraka-tier bhuktis carrying the classical Saturn signal (`r.maraka_saturn`, HTJAH-II:4846-4849)
— **after** the band, deduplicated per bhukti and each marked inside or beyond the span. Where
the two methods disagree (the maraka scheme runs the whole Vimshottari timeline while the
ayurdaya stops), the disagreement is disclosed and Raman's order settles which leads.

Guard: every string is held to `_FORBIDDEN_RE` by test. The 2026-08-17 decision permits timed
indications in the classical idiom and still refuses the decree voice; longevity is the
highest-stakes surface for that line. Rendering rounds to whole years — a two-decimal lifespan is
false precision the report has banned since v2.

### G.2 Connections name a mechanism, not a join

A tie needs the same CHIEF driving graha or one theme's primary house inside the other's network.
What changed is the note. It used to be a template ("A and B overlap at H6, tying the two areas
together"), which restates the join and says nothing about the chart. Now a shared bhava is
reported as one bhava in two roles (whose primary, what the other draws through), a shared graha
carries that graha's own measured condition from `driver_concordance` (Ishta/Kashta, avastha,
the named pattern), and every note sets the two verdicts against each other — an inversion
(favourable one end, afflicted the other) reads as strength-and-strain, a difference of degree
does not. Ties rank graha-before-house and no theme may hold more than `_CONN_PER_THEME` of them:
the busiest theme has the widest network by construction, and uncapped it took four of six slots.

### G.3 The weather calendar — subordinate by citation

`AfflictionCalendar` joins three schemes the engine ran in full and the synthesis never consulted:
Sade Sati phases, the MD/AD lord meeting its own **adverse** transit (`r.dasha_transit_adverse`,
the mirror of the favourable confluence already read), and the eightfold Dasha Kakshya split.
Forward-only; contiguous passes inside one Mahadasha merge into one stretch. Each theme's own
window is then read against it (`weather_on_window`) — the join that was missing, since a bhukti
grading *par excellence* while Sade Sati sits over the Moon is not the same window as one running
clear.

Subordination travels with the data, not just the section header: every window carries its
governing rule — PREC-6 (*"transits are always secondary in importance… like catalytic agents"*,
HTJAH-II:4679) or PREC-7 (Dasha Kakshya is *"a timing lens, never a verdict"*, ASP-12:174). A
window can say a stretch runs rough; it can never say a bhava is afflicted.

The **pitru** screen rides beside this as `pitru_screen` on the 5th and the 9th only, governed by
PREC-12 (*non-Raman screens are a different layer, not a contradiction*). It is CLASSICAL_NONCITABLE
(BPHS provenance), so it wears that on its face and is walled out of the cross-checks, the
evidence links and the contradictions — tested in all three directions.

## H. Dasha synthesis methodology (the time axis)

Reuse `r.life_chapters` (per-MD chapters, already a time-axis synthesis) and overlay
**which themes each chapter activates**: for each MD/AD, `graded_buckets` gives the lit
houses + tier + activating lord + delivery quality; map those houses back to themes. The
**Dasha Evolution** section then reads as: *this chapter lights themes X and Y at par-excellence
(carried by planet P, delivering well), continues theme Z from the prior chapter, and
introduces theme W* — all from `life_chapters` + `period_pairing`, no new dasha math (JD
arithmetic, 365.2425, is never re-derived). Transits enter only as a subordinate modifier
under an already-active theme (`r.dasha_transit`), preserving natal→dasha→transit.

## I. Varga integration methodology (confirmation / modification)

A per-theme **varga relation**, typed `confirms / strengthens / qualifies / modifies /
contradicts / D9-only`:
- **D9 (the only verdict-bearing varga signal)** — `r.synthesis.matters[i].navamsa`
  (`synthesis.py:39`): `confirms`/`weakens`/`neutral` vs the natal rollup. Available for all
  12 houses.
- **D7 for children** — the `_saptamsa_gate` borderline signal (`house_template.py:726`).
- **Matter deep-reader CORE verdicts** — `r.dashboard.entries[*].verdict`
  (`matter_varga_dashboard.py:38`): each is a full `judge_house` on the relevant varga
  (D10 career, D9 marriage, D7 children, D30 health…), the authoritative divisional read.
- **Report-only dignity** — `r.synthesis.matters[i].matter_varga` (`'varga_D*=lord:dig|karaka:dig'`)
  as texture, never a verdict.

Where a theme has no dedicated varga reader, the relation is honestly `D9-only` rather than
a fabricated confirmation. This produces the **Varga Confirmation Matrix** section as a
re-read table, not new essays.

## J. Proposed report architecture

Add a high-level interpretive layer **above** the technical sections; remove nothing:

```text
1. Executive Portrait            (new — ThemeSynthesis.portrait)
2. What Dominates This Horoscope (new — spine names + dominant actors)
3. Interpretive Spine            (new — the 3–7 spine themes, each a mechanism chain)
4. Major Life-Themes             (new — every ThemeReading, ranked)
5. Dominant Planetary Actors     (re-read of planet_bios, theme-linked)
6. House Networks                (new — theme-clustered judgment_graph view)
7. Major Contradictions          (new — the Contradiction objects, PREC-cited)
8. Dasha Evolution               (life_chapters + theme overlay)
9. Varga Confirmation Matrix     (new — the §I table)
10. Current Transit Overlay      (r.dasha_transit, subordinated)
... then the EXISTING technical sections unchanged (auditability) ...
N-2. Full Life Synthesis         (rebuilt integrative — theme cross-links)
N-1. Nichod                      (upgraded — traceable engines + tension + evolution)
```

The `plain_reading` and flat `life_synthesis` remain for back-compat (append-only). All new
sections ship through `to_report_dict` → the four surfaces (markdown / standalone HTML /
`report_html` / interactive page, safe-DOM only).

## K. Test strategy

The QC harness (`tests/raman_saab/test_theme_synthesis.py`) enforces the brief's item-22
checks as assertions on the Mainpuri + canonical + several golden charts:

1. Every `final_interpretation` / link has a non-empty `accessor` (evidence traceability).
2. `headline_verdict` byte-equals the source `pf.rollup` / dashboard verdict (no re-judgment).
3. No link with `axis!='verdict'` asserts a direction; only passthrough verdicts carry polarity.
4. No `provenance=='STATISTICAL'` link appears in a doctrine claim; population material stays
   labelled and framed by `r.info`.
5. Every theme has ≥1 supporting evidence link.
6. Every `Contradiction` has a governing PREC-id or is explicitly `unresolved`.
7. Dasha spans in links equal `dasha_on`/`life_chapters` (no independent dasha math).
8. Varga relations equal `synthesis.matters[].navamsa` / dashboard CORE.
9. Transit links equal `r.dasha_transit` rows (subordinated; none independent).
10. `_FORBIDDEN_RE` decree-guard sweep over all theme prose (timed idiom allowed, decree refused).
11. The layer authors no `WORK:line` (`provenance_check` would treat it as fabricated).
12. **Golden ratchet byte-identical** — 259/293, the hard gate, proving zero verdict drift.
13. Contract + completeness: the new section renders on all four surfaces, no new `##` heading in a
    frozen prefix.

## L. Risks of false synthesis (codebase-specific, with guardrails)

1. **Frame-lord pairing trap** — reading strength off `sv.ledger` (the LEAD, possibly Moon,
   frame) pairs the displayed lord NAME with a different planet's strength. *Guard:* always
   `_lagna_ledger(sv)` (`:172`).
2. **Support metric → direction call** — turning SAV band / Ishta-Kashta / Sodya Pinda /
   Baladi / a percentile into favourable/afflicted re-implements `_decide` uncalibrated.
   *Guard:* typed `axis`; only `axis=='verdict'` carries polarity; `headline_verdict` is a
   passthrough.
3. **Fabricated convergence from bilateral abundance** — cherry-picking one pole from the
   19-afflicted/31-favourable field. *Guard:* report convergence AND contradiction together;
   never suppress the opposing axis; attach the honesty frame.
4. **Promoting classical/AV/modern to Raman doctrine.** *Guard:* preserve band/provenance on
   every link; cite `INTERPRETATION_GUIDE` precedence rather than inventing it.
5. **Statistics-as-destiny in prose.** *Guard:* quote `POPULATION_NOTE`/`distinctive_gloss`
   verbatim; route prose through `build_evidence`→`refusal_reason`.
6. **Death/longevity idiom breach.** *Guard:* longevity as a band never a date; decree voice
   code-refused; the walled `ai_interpret` illness/self-harm exclusion untouched.
7. **Yoga edge fabrication** — `FiredYoga` carries no participants; parsing rendered banners
   is fragile. *Guard:* participants from `r.yoga_deep`/`_yoga_planets` only; whole-chart
   shapes disclosed as coverage-gap nodes.
8. **Recompute drift** — re-running any judge with a monkeypatched knob disagrees with the
   printed report. *Guard:* strictly read-only over built `DetailedReport`; the one allowed
   rebuild is `build_judgment_graph(r)`, once.

## M. Implementation plan (staged, each stage ratchet-safe)

- **Stage 1 — engine core (no surface change).** `theme_synthesis.py`: dataclasses +
  `build_theme_synthesis(r)` (all six passes) + the QC harness (K1–K12). Pure new module,
  imported by nothing yet; ratchet untouched. *This is where the reasoning architecture is
  proven before a single line of prose ships.*
- **Stage 2 — transport + surfaces.** The five coordinated append-only edits (SECTION_CONTRACT
  since-v34, `_FROZEN`, `HTML_SECTION_ORDER`, `to_report_dict` key, the four renderers).
  Contract + completeness tests. The new sections render as structured tables/chains.
- **Stage 3 — the framing sections.** Executive Portrait, What Dominates, Interpretive Spine,
  House Networks, Contradictions, Dasha Evolution, Varga Matrix — all re-reads of Stage-1
  objects.
- **Stage 4 — rebuilt Full Life Synthesis + upgraded Nichod**, integrative and theme-linked,
  append-only beside the existing ones.
- **Stage 5 — prose pipeline.** `build_evidence` scope `section:themes`, one-Fact-per-claim;
  the section becomes explainable via `/report/explain` with no new endpoint. `_FORBIDDEN_RE`
  + `provenance_check` gate the output.
- **Stage 6 — integration proof.** Mainpuri as the primary integration test (does the layer
  *discover* the Jupiter/Mercury/Saturn actors, the H2/H8/H11 wealth network, the career/
  children/home themes, the Saturn/Mercury MD activations — without forcing them?), plus
  generic-behaviour tests across the golden charts, plus the full ratchet.

Every stage keeps the golden baseline byte-identical and the source firewall intact; the
layer synthesizes the astrology already computed, and judges nothing anew.
