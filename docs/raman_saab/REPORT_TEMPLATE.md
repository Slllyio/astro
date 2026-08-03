# The detailed-report template — FROZEN (append-only)

*Locked 2026-07-25. The machine registry is `SECTION_CONTRACT` in
`app/raman_saab/detailed_report.py`; the ratchet is
`tests/raman_saab/test_report_template_contract.py`. Existing sections may never be removed,
renamed, or reordered. New sections may only be APPENDED to the registry with a new `since` tag,
updating the contract test's frozen list in the same, conscious commit.*

## The contracted sections, in order

| # | section | markdown heading | HTML anchor | since |
|---|---|---|---|---|
| 1 | Title & two-voice preamble | `# Detailed reading` | `.name` | v1 |
| 2 | **Your Reading (plain English, read first)** | `## Your Reading` | `#plain-reading` | v5 |
| 3 | Running now (HTML only) | — | `.nowbox` | v1 |
| 4 | Information content (honesty headline) | `## Information content of this reading` | `.infobox` | v1 |
| 5 | **How to read this report (interpretation guide)** | `## How to read this report` | `#interpretation-guide` | v18 |
| 6 | What stands out | `## What stands out in this chart` | `#stands-out` | v1 |
| 7 | **What matters most (ranked digest)** | `## What matters most (ranked digest)` | `#digest` | v19 |
| 8 | The twelve matters at a glance | `## The twelve matters at a glance` | `#dashboard` | v2 |
| 9 | Chart signature | `## Chart signature` | `.sig` (page header) | v1 |
| 10 | **Ruler of the nativity (first impression)** | `## Ruler of the nativity` | `#ruler` | v13 |
| 10a | **Planet biographies (dominant grahas)** | `## Planet biographies (dominant grahas)` | `#planet-bios` | v20 |
| 11 | Chart grids Rasi/Navamsa (HTML only) | — | `#charts` | v1 |
| 12 | Planetary positions | `## Planetary positions` | `#positions` | v1 |
| 13 | Shadbala | `## Shadbala` | `#shadbala` | v2 |
| 14 | Yogas | `## Yogas present in this chart` | `#yogas` | v1 |
| 15 | Yoga x Dasha timing | `## Yoga x Dasha timing` | `#yoga-timing` | v7 |
| 16 | Ashtakavarga | `## Ashtakavarga` | `#sav` | v1 |
| 17 | House-by-house | `## House-by-house reading` | `#houses` | v1 |
| 18 | House strength cross-check | `## House strength cross-check` | `#house-strength` | v8 |
| 19 | **Preponderance of testimonies** | `## Preponderance of testimonies` | `#preponderance` | v14 |
| 20 | Longevity (band-first) | `## Longevity` | `#longevity` | v1 |
| 21 | Maraka scheme | `## The maraka scheme` | `#maraka` | v2 |
| 22 | Maraka x Saturn-transit confluence | `## Maraka x Saturn-transit confluence` | `#maraka-saturn` | v11 |
| 23 | **Health & vulnerability read-out** | `## Health & vulnerability read-out` | `#health-readout` | v17 |
| 24 | Life-narrative (MD→AD, 4-tier) | `## Life-narrative (Vimshottari Dasha)` | `#timeline` | v1 |
| 25 | Ishta/Kashta outlook | `## Ishta/Kashta outlook` | `#ishta-kashta` | v9 |
| 26 | MD-lord condition outlook | `## MD-lord condition outlook` | `#md-condition` | v10 |
| 27 | AV dasha-seat outlook | `## AV dasha-seat outlook` | `#av-dasha-seat` | v12 |
| 28 | Dasha Kakshya intervals | `## Dasha Kakshya intervals` | `#dasa-kakshya` | v16 |
| 29 | **Life-chapters (one woven chapter per MD)** | `## Life-chapters` | `#life-chapters` | v15 |
| 30 | Gochara with Vedha | `## Current transits (Gochara` | `#gochara` | v2 |
| 31 | Dasha x Transit confluence | `## Dasha x Transit confluence` | `#dasha-transit` | v6 |
| 32 | Divisional deep-reads (15 vargas) | `## Divisional deep-reads (Shodasavarga)` | `#vargas` | v1 |
| 33 | Career | `## Career (HTJAH-II` | `#career` | v1 |
| 34 | Deeptadi avasthas | `## Deeptadi avasthas` | `#deeptadi` | v1 |
| 35 | Jaimini Karakamsa (stub) | `## Jaimini Karakamsa` | `#karakamsa` | v1 |
| 36 | Soul & destiny (extended) | `## Soul & destiny` | `#soul` | v2 |
| 37 | Pitru dosha screen (bannered) | `## Pitru dosha` | `#pitru` | v2 |
| 38 | Integrated insights (cross-feature synthesis) | `## Integrated insights` | `#synthesis` | v3 |
| 39 | Glossary | `## Glossary` | `#glossary` | v1 |
| 40 | Nichod (the capstone distillation) | `## Nichod` | `#nichod` | v4 |

**Table catch-up (2026-08-03).** The v16 Dasha Kakshya and v15 Life-chapters rows (now 28
and 29 after the v18/v19 renumber) had never been added to this table when their sections
shipped — repaired in the v17 commit; the whole table was renumbered again in the v18/v19
commit.

**v20 amendment (2026-08-03) — the synthesis layer (S1-S5).** The user proposed a
10-phase deterministic synthesis architecture; an inventory showed ~half already existed
(judgment objects = the frozen dataclasses; ranking = Raman's comparative weighing + the
v18 axes, numeric weights measured null and deliberately NOT built; life narrative =
plain_reading/life_chapters; master verdict = nichod; style = the guard). The genuinely
new pieces: `judgment_graph.py` (S1 — every judgment object as a node, every
already-computed relation as an edge, closed vocabulary = v18 relations + structural set;
shipped as JSON `judgment_graph`), `planet_biographies.py` (S2 — this section: dominant
grahas by graph census, Raman-tier themes cite HTJAH-II:10249-10274, the modern keyword
tier ALWAYS carries the MODERN_SYNTHESIS banner), `tension_narrator.py` (S3 — tensions
WOVEN never hidden, per the user decision: one sentence per already-detected conflict
naming BOTH poles and the governing v18 rule, on `PlainReading.reconciliations`),
`NON_RAMAN_GROUPINGS` bannered matter edges (S4), and `Nichod.turning_points` (S5 — MD
boundaries where the Ishta/Kashta lean flips). All pure re-reads (PREC-10); the
verdict-path wall test extends to all three new modules; every new prose surface passes
`_FORBIDDEN_RE` by test. Table row 10a (the one new section) sits after the ruler card it
generalizes.

**Content amendment (2026-08-03) — the pipeline wiring.** The synthesis boxes existed
after the v20 amendment; this closes the ARROWS: the judgment graph now builds from
first-pass timeline objects (decoupled from life_chapters, whose backwards dependency it
had; timer edges gained the activation GRADE), the second pass runs in the diagram's
order (objects → graph → conflict narrator → census/biographies → chapters → digest →
nichod/plain-reading), and the narrative engine CONSUMES the layers: Your Reading's
opening gains the census-dominant-planet sentence (beside the Shadbala one — two
different dominance measures, said so, HTJAH-II:10249 cited), reconciliations are
composed into `build_plain_reading` rather than attached after, and the dominant graha's
own Mahadasha chapter carries a marking sentence. `raman_style.py` names the style-writer
stage (because/weighed/governed_list/conclusion helpers, guard-tested). The order is
enforced by consumption tests: prose naming census values can only exist because the
census ran first.

**v18 amendment (2026-08-03) — the interpretation guide.** User-requested coherence work
("many sections saying the same things — how to interpret"). A coherence audit collected the
ELEVEN precedence statements the report already makes locally (each inside the section that
yields) plus the one derived rule (PREC-1, the dashboard-vs-house-by-house grain
distinction, doctrine-reviewed before shipping and explicitly tagged project governance) into
`app/raman_saab/interpretation_guide.py` — a chart-independent constant rendered as this
section and shipped machine-readable as the JSON `interpretation_guide` key (closed
`relation` vocabulary so the LLM-grounding path can branch deterministically). Placed after
the honesty headline: the reader learns how much to believe, then how to read, then reads.
Where no rule exists the guide says "parallel lenses — side by side, never averaged"; it
never invents precedence. Tests pin: every named section id exists in the contract, every
corpus citation resolves, the vocabulary is closed.

**v19 amendment (2026-08-03) — the ranked digest rendered.** The same audit found the
engine's own ranked digest (`insight_digest.py`) shipped in JSON and the interactive page
but NEVER rendered in markdown or the standalone HTML — a REPORT COMPLETENESS violation.
Repaired append-only: `## What matters most (ranked digest)` after What-stands-out (which
it generalizes), with the digest's fixed cross-category order (convergence → current
period → insights → tension → distinctive) unchanged.

**v17 amendment (2026-08-03) — Health & vulnerability read-out.** User-approved feature: the
health-adjacent verdicts the report already computes (the D-30 health core's H1/H6/H8 reads,
the H12 rollup, Moon/Mercury karaka afflictions, balarishta, the maraka tiers and the
longevity band) gathered into one section closing the longevity/maraka cluster (the v11
placement precedent). A pure second-pass re-read (`build_health_readout`), never a new
judgment; the caveat sentence ("a statement of the method, not a prognosis... never medical
statements, never a prediction") is part of the dataclass and renders in every surface, and a
contract test runs the whole rendered section through the LLM guard's `_FORBIDDEN_RE` so
decree/forecast/death-token wording can never silently enter.

**v3 amendment (2026-07-25):** the Integrated-insights section was inserted before the Glossary
(conscious amendment; `_FROZEN` updated in the same commit) so reference material stays last. It
renders the fired `SYNTHESIS_RULES` (doctrine/synthesis_rules.py) in three provenance bands —
Raman (citable), classical (CLASSICAL_NONCITABLE banner), Ashtakavarga (Raman's own caveat
banner) — plus a doctrine-on-record list and the excluded-techniques note.

**v5 amendment (2026-07-26) — Your Reading.** A user read the full 24-section report end to end
(~10,700 words on a real chart) and reported, correctly, that the content was not meaningful —
users would struggle to understand it. On inspection every section was individually faithful but
the report had no plain-English answer anywhere: the house-by-house prose repeated a dense
"activated in X(timer)/(lord)/(karaka) YYYY-YYYY" clause 12 times with zero gloss, the
population-context lines repeated the same statistical sentence template ~56 times, and even the
v4 Nichod — built specifically to be the "deep integration" answer — was itself full of unexplained
jargon (Shadbala rupas, par excellence, bindus). `detailed_report.PlainReading` /
`build_plain_reading()` is the fix: hand-written (never templated) prose, grouped into five
life-domain paragraphs from the SAME 12-matter dashboard verdicts the rest of the report already
shows, a plain description of the current dasha period via `_PLANET_THEME`, and the top distinctive
readings translated through `_plain_signification` (which glosses every one of the 56 signification
keys, e.g. "poorvapunya" -> "merit carried from the past") so no Sanskrit or house-number token
ever appears. **This is the ONE deliberate exception to "append at the end"**: `plain_reading` is
inserted as section #2, right after the title, because its entire purpose is to be read BEFORE
every technical section — including the report's own "Information content" statistics. `_FROZEN`
in the contract test was reordered to match, in the same commit, per the procedure; negative-checked
(mutating the heading fails two contract tests, reverting restores green). All existing sections
are otherwise untouched and still render exactly as before, unmoved relative to each other.

(The HTML renderer places the signature chips in the page header and adds the HTML-only
now-box/chart-grid sections; its document order is `HTML_SECTION_ORDER` in the same module.)

**Content amendment (2026-07-26) — the weakest-link contradiction.** External review of a
generated report identified a real readability defect: `house_template._rollup` grades a bhava by
its single WORST decided signification (HTJAH-I:1592-1640's own design), so one afflicted
sub-matter — e.g. Property in House 4, D-7 Children in House 5, the classical Maraka trigger in
House 8 — stamps the WHOLE house's headline afflicted even when 4-6 of its other significations
read favourable. The verdict itself is correct and un-touchable (the rollup is Raman's own rule,
protected by the golden ratchet and the verdict-authority invariant); what needed fixing was that
the report gave the reader no way to see the split. Fixed as three **presentation-only** additions
inside existing sections (no new SectionSpec row, no contract change):
- **Split-status note** (`detailed_report.signification_tenor_split` / `tenor_note`, section #12
  House-by-house): counts each house's significations by their OWN verdict and states the
  majority tenor whenever it disagrees with the weakest-link headline — e.g. *"5 of 6 sub-readings
  are actually favourable — the headline follows the single weakest decided matter, not the
  majority."* Silent when the house is genuinely afflicted throughout (majority agrees).
- **Inline inverted-channel warning** (section #12): when the specific signification driving the
  headline (`driver_entry`) is itself an atlas-proven inverted channel (H3 courage, H12
  incarceration), the house head carries an explicit WARNING, not just the small per-row tag.
- **Named inverted locations at the top level** (`InfoContent.inverted_locations`, section #3
  Information content): the honesty headline now names WHICH houses/significations are proven
  inverted (e.g. "H3 courage, H12 incarceration"), not just a bare count — so the reader meets the
  warning before reaching the house-by-house detail.

Deliberately NOT done: re-weighting or replacing the rollup verdict itself (would break the
verdict-authority invariant and the golden ratchet), and a formal "internal capacity vs external
event" signification taxonomy (the driver-naming + split-status combination already tells the
reader which specific sub-matter is the exception and how many others are sound, without inventing
a new classification scheme).

**v4 amendment (2026-07-26) — the Nichod.** The report's 24 sections were each individually
faithful but never integrated into one final read. `detailed_report.Nichod` / `build_nichod()`
distils the WHOLE document — identity, Shadbala strength profile, longevity band, fired yogas,
what stands out, the 12-matter tally, the running dasha period and the houses it lights (with
split-status caution reused from the v3-adjacent fix), live transits (Vedha/AV already applied),
and one spotlighted cross-feature synthesis insight — into a single distilled paragraph plus its
labelled "ingredients" so the essence can be checked against its parts. **Nothing here is a new
judgment**: every clause selects, counts, or quotes a value the rest of the report already
computed and displayed elsewhere; `build_nichod` takes the fully-assembled `DetailedReport` as
its only input and never calls `judge_house` or any verdict path directly. Appended as the FINAL
section (after the Glossary — an intentional exception to "reference material stays last," since
a capstone belongs at the very end). A cross-varga "does D-9/D-10 corroborate the Rasi house"
check was considered and explicitly REJECTED: `NavamsaMarriageReading.core.marital_verdict` and
`DasamsaCareerReading.core.career_verdict` are computed by calling `judge_house` on the SAME
signification already feeding the house calibration — comparing them would be tautological, not
a genuine independent cross-check, and encoding a new ad-hoc D9/D10 verdict instead would have
meant inventing an unaudited judgment outside `house_template`.

**Content amendment (2026-07-26) — the Gochara outlook over time.** A user asked, of the
point-in-time "Current transits (Gochara) with Vedha" table: "can we make a temporal graph to show
in what period of past N years and M years ahead which times are favourable." `primitives/
transits.gochara_timeline()` extends the SAME Gochara/Vedha scheme (`_GOCHARA_GOOD`, `_VEDHA`,
`_VEDHA_EXEMPT` — no new doctrine, no new citation needed) across
`[ref_jd - window_back, ref_jd + window_forward]` — the identical span the report's own
Life-narrative section already uses (`DetailedReport.window_back`/`window_forward`), so the two
stay coherent without a second window parameter. Restricted to the four slow movers (Jupiter,
Saturn, Rahu, Ketu): their Gochara good/bad status changes only at each sign ingress (~1 year for
Jupiter, ~2.5 for the others), the natural resolution for a multi-year graph — Mars and the faster
grahas would fragment into hundreds of unreadable slivers and stay covered by the existing
snapshot. Rendered as **presentation only, inside the existing Gochara section** (`gochara_outlook`
field on `DetailedReport`, no new SectionSpec row — the same enrich-in-place precedent as the
split-status fix): a "Favourable transit windows" table in Markdown, an SVG Gantt-style bar chart
in HTML (solid = clear, faded = often Vedha-cancelled — hover for exact dates/AV/Vedha).

Two honesty disclosures are stated explicitly, not silently assumed:
- **Sampling resolution.** Segment boundaries are computed at 5-day steps (not exact ephemeris
  root-finding), so a real sign-ingress date can fall anywhere within a few days of what's shown;
  windows under ~a month (a planet stationing back across a cusp near a retrograde turn) are
  dropped as sampling noise, not shown as if they were real transits.
- **Vedha at this scale is an estimate, not an exact window.** A fast mover (Moon, Mercury...) can
  start and cancel a Vedha obstruction within days — faster than a 25-year view samples. Rather
  than fabricate exact obstructed sub-dates, each favourable span reports the SHARE of sampled
  dates across its whole run where Vedha was active, in words (rare/occasional/frequent/
  sustained), directing the reader to the existing day-exact snapshot table for "is it obstructed
  right now."
- Per Raman's own doctrine (already cited in `synthesis_rules.SYN_R8_TRANSIT_CATALYST`,
  HTJAH-II:4679), transits are secondary to the Dasha — the caveat text repeats this at the point
  of use so a favourable bar is never read as sufficient on its own, only alongside the
  Life-narrative period it falls inside.

**Content amendment (2026-07-26) — the Gochara outlook, made plain and by month.** A follow-up ask
("should be more fine include months also and what does it mean clearly in simple, tell the
user") refined the outlook above rather than adding new doctrine:
- **Dates now read "Mar 2024", not "2024-03"** (`_jd_month_year` / `_outlook_window_label`), and a
  window that rounds to the same calendar month at both ends (a real but short, >=25-day window)
  collapses to that one month instead of the confusing "Apr 2019 to Apr 2019".
- **A "what it supports" column replaces raw jargon.** Each row now names the life theme the
  planet governs (`_PLANET_THEME`, the same map "Your Reading" already uses) and a plain
  "strength" word (`_outlook_strength_word`, from the same Ashtakavarga-bindus threshold, HPA-
  34:127) instead of a bare bindus count — the table leads with meaning, the citation moves to a
  short footer note (the same plain-leads/technical-follows pattern as the Integrated-insights
  fix).
- **The HTML gained a data table matching the Markdown one**, directly below the SVG graph, plus
  quarter tick-marks and an inline month-range label on wide bars — so the timing information does
  not live in hover tooltips alone (a printed page cannot hover).
No new doctrine, no new citation, no change to `gochara_timeline`'s underlying computation —
purely how the same already-computed windows are labelled and explained.

**v6 amendment (2026-07-26) — Dasha x Transit confluence.** A user asked to "interconnect the MD
and AD with Gochara to have a separate analysis" — a genuinely new cross-reference, not a
presentation tweak to an existing section, so it is registered as a new contracted section (the
same bar Nichod/synthesis met) rather than folded quietly into Gochara or Life-narrative.
`detailed_report.ConfluenceWindow` / `_dasha_transit_confluences()` walk the ALREADY-COMPUTED
windowed Vimshottari timeline (`DetailedReport.timeline`) against the ALREADY-COMPUTED Gochara
outlook (`DetailedReport.gochara_outlook`) and report every stretch where a bhukti's MD or AD
LORD is, at the same time, in one of its own favourable Gochara windows — the overlap is a plain
intersection of two existing computations, nothing new is judged. The doctrinal basis is the
same citation the outlook section already carries (`SYN_R8_TRANSIT_CATALYST`, HTJAH-II:4679:
"a good transit only delivers what the running period already permits") — a confluence is the
concrete, checkable form of that principle: the planet already ruling the period is also
well-placed by transit. Only Jupiter/Saturn/Rahu/Ketu are tracked long-range, so a bhukti led by
the Sun/Moon/Mars/Mercury/Venus simply contributes no row; the renderer states this is a coverage
gap, not a judgment that the period lacks support. Inserted right after Gochara (the natural
narrative position, matching the v2/v3 precedent of inserting new rows where they are read, not
only at the tuple's tail) — `_FROZEN` updated in the same commit.

**v7 amendment (2026-07-26) — Yoga x Dasha timing.** First of a walked-through menu of candidate
cross-reference analyses (the user asked to go through them "one by one" for feedback before
building each — see the session's discussion for the full menu and why this one was picked
first). `detailed_report.YogaTiming` / `_yoga_dasha_confluences()` answer: a fired yoga is not
always "on" — Raman says it ripens most clearly during its own constituent lord's Dasha/Bhukti
(HTJAH-I:4324), with magnitude scaling to that lord's strength and doubling at Vargottama
(HTJAH-I:5372, `SYN_R3_YOGA_LORD_PERIOD` / `SYN_R13_RAJA_VARGOTTAMA_RANK`). For each fired yoga
whose constituent lords are structurally resolved (`synthesis_rules._yoga_planets`), the section
lists every MD or AD window that lord runs in the windowed timeline, alongside
`vimshottari.lord_quality`'s existing "well / mixed / poorly
/ unknown" delivery tag — a strength read that was already computed for Life-narrative's own
MD/AD quality but had never actually been rendered anywhere until now. `_md_runs()` collapses the
windowed bhukti-level timeline into contiguous Mahadasha spans first, so an MD-role confluence is
ONE row for the whole ~7-19-year run, not nine near-duplicate bhukti-sized rows. Inserted right
after Yogas (the natural narrative position — it directly extends that section with WHEN);
`_FROZEN` updated in the same commit. A fired yoga outside the resolvable set contributes no row,
stated in the renderer as a coverage gap, not a judgment that it lacks timing.

**Content amendment (2026-07-26) — `_yoga_planets` widened from 3 families to ~30+.** The v7
build above shipped resolving only Gajakesari, Budha-Aditya, and the 9th/10th-lord Raja yoga; a
direct follow-up question ("why not all?") prompted reading every one of the ~72 encoded
`YogaRecord`s in `doctrine/yogas.py` to check which ones genuinely have a single, structurally-
certain "lord" versus which are properties of the whole chart. The answer: most do. Added,
with citations verified against the actual `Condition` class each yoga is built from (never
guessed): the five Pancha Mahapurusha (a single fixed planet each — Ruchaka=Mars, Bhadra=Mercury,
Hamsa=Jupiter, Malavya=Venus, Sasa=Saturn), Chandramangala, Vasumathi, Adhi, the arishta Sakata,
Kusuma, Kemadruma (the Moon's own isolation), every Dhana/Raja yoga whose lords are a
deterministic function of the Lagna (5th/9th, 1-2-11 chain and cyclic chain, Venus-5th/
Saturn-11th, Sun-5th/Moon-Jupiter-11th, Jaya, Daridra, Khadga, Sreenatha, Chamara, Asatyavadi),
and — the harder case — the "some planet satisfies X" flank/benefic yogas (Vesi, Vasi,
Ubhayachari, Sunapha, Anapha, Durudhara, Amala, Parvata), resolved by checking WHICH of a small,
exactly-defined candidate set (e.g. "a planet other than the Moon", 3HC:1834-1846) actually sits
in the required house on that specific chart — and two Raja/arishta yogas (kendra-trikona lords,
Vipareeta) whose condition classes search over candidate pairs for A match without keeping it;
`_kt_pair`/`_vipareeta_pair` re-run the identical search, keeping the pair instead of discarding
it as a bare boolean. `_yoga_planets` public entry point now dedupes its own result (two
different houses can share a lord — e.g. Mars rules both Aries and Scorpio — so a fixed
multi-house lookup can legitimately name the same planet twice; collapsed to one, tested
directly). What remains genuinely unresolved, and stays that way: the Nabhasa whole-chart-
distribution yogas (Asraya x3, Dala x2, Sankhya x7, Akriti x20, Chatussagara) — properties of
all seven visible planets together, with no single causing planet in Raman's own definition —
plus two rare multi-arm HPA-20 yogas (Sarada, Brihadbija) deferred because discriminating which
of their differently-worded disjuncts fired needs more care than this pass gives it.

**v8 amendment (2026-07-26) — House strength cross-check.** Second of the walked-through menu of
candidate cross-reference analyses. `detailed_report.HouseStrengthRow` / `_house_strength_rows()`
cross-tabulate two INDEPENDENT strength measures against each house's already-computed verdict —
Bhava Bala (the house-lord's Shadbala plus Bhavadig and Bhava-Drig, RANKED 1st-strongest to
12th-weakest across the chart; Raman gives no numeric cutoff, only a ranking, GBB-9:332,
`SYN_R6_BHAVA_BALA_RANK`) and Sarvashtakavarga bindus (that house's sign, against the existing
28-per-sign average already stated in the Ashtakavarga section — no new threshold invented). Both
values were already computed elsewhere (Bhava Bala feeds the one-line `SYN_R6` insight and a
per-house detail note in House-by-house; SAV bindus are the existing `#sav` table) but never
CROSS-TABULATED against the verdict as a single 12-row view answering "is this verdict standing
on strong or shaky ground." `verdict` is `HouseProforma.rollup`, read not re-derived — tested
directly that the two never disagree and that the function never calls `judge_house`. Inserted
right after House-by-house (the natural narrative position: read the verdicts, then see how
strong their ground is) as v8; `_FROZEN` updated in the same commit.

**Content amendment (2026-07-26) — what a strength/verdict divergence means.** The v8 table
surfaced a striking real case (Mainpuri chart: H1 favourable yet ranked weakest, H5 afflicted yet
ranked strongest) and the user asked for deep research into what Raman's texts say this means.
Answer, added as an explanatory paragraph in both renderers: Raman lists a house's own strength
and its aspects/qualities as SEPARATE considerations when judging a house (HTJAH-I:468-478 —
"the strength of the house itself" and "the natural qualities of the house... or the planets...
having aspects" are numbered separately); Bhava Bala is mostly a magnitude, how fully a house's
indications are enjoyed (GBB-9:32-34), THOUGH not perfectly independent of direction — one of its
three components, Bhava Drig Bala, is itself signed by benefic/malefic aspect (GBB-9:180-219;
`primitives/shadbala/bhava_bala.py`'s `bhava_drig_bala()` encodes exactly this). A first draft of
this paragraph cited `3HC:1367-1371` for the "separate axes" claim and stated strength as flatly
"not a direction" — a bphs-doctrine-reviewer pass caught both as overstatements (3HC:1367-1371 is
the closing line of a YOGA-interpretation method scoped to yogakaraka planetary dignity, not
general house Bhava Bala; and the "not a direction" claim ignored the signed Bhava Drig Bala term
this project's own code already computes) before it shipped — corrected to HTJAH-I:468-478 and
the honest "tendency, not an absolute rule" framing above.

**v9 amendment (2026-07-26) — Ishta/Kashta outlook.** Third of the walked-through menu of
candidate cross-reference analyses. `detailed_report.IshtaKashtaPeriod` /
`_ishta_kashta_periods()` paint the SAME windowed Vimshottari timeline Life-narrative already
shows with each period-lord's Ishta/Kashta lean — Raman's rule that a planet with more Ishta
Phala inclines to good results in its Dasha/Bhukti, more Kashta to harder ones (GBB-10:134),
extending `SYN_R5_ISHTA_KASHTA_PERIOD`'s current-period-only one-liner to every bhukti in the
window. Both Ishta/Kashta and Shadbala are natal-fixed values, so this is a pure lookup onto the
already-built timeline, not a new computation — one row per bhukti, matching `r.timeline.periods`
1:1 (tested directly). Where a bhukti's own lord out-strengths the Mahadasha lord, `prevails`
still only states the MD-predominates direction (GBB-10:145-152 asserts no converse, mirroring
SYN_R5's own encoding) — never claims the AD lord's character wins. Inserted right after
Life-narrative (the natural narrative position: a colour-strip companion to the section directly
above it) as v9; `_FROZEN` updated in the same commit.

**v10 amendment (2026-07-26) — MD-lord condition outlook.** Fourth of the walked-through menu.
`detailed_report.MdLordCondition` / `_md_lord_conditions()` extend `SYN_R4_MD_LORD_CONDITION`'s
current-MD-only reading to every Mahadasha RUN in the windowed timeline — Raman's rule that a
Dasha's result is modified by its lord's strength/weakness and Navamsa disposition, reaching its
stated maximum only when strong in BOTH the rasi and Navamsa charts (HPA-24:51-86). Scoped to the
MD lord only (SYN_R4 never checks the AD/bhukti lord, and neither does this). Strength,
Vargottama and Navamsa are all natal-fixed — a pure lookup onto `_md_runs` (the same MD-run
collapse `_yoga_dasha_confluences` already uses), one row per contiguous Mahadasha, not one per
bhukti (tested directly: `at_maximum` can only be true when BOTH `strong` and `vargottama` hold).
Grouped right after the Ishta/Kashta outlook (both are Life-narrative companions painting a
different natal-fixed lens across the same MD timeline) as v10; `_FROZEN` updated in the same
commit.

**v11 amendment (2026-07-26) — Maraka x Saturn-transit confluence.** Fifth of the menu, and the
one flagged from the start as needing careful framing: this is exactly the territory the
project's own real-outcome research measured as NULL (`REAL_OUTCOME_GENERALIZATION.md`).
`detailed_report.MarakaSaturnConfluence` / `_maraka_saturn_confluences()` cross-reference the
ayurdaya-anchored maraka death-window (`vimshottari.death_window()`) against transiting Saturn
sitting on the NATAL Saturn's own rasi or trine — Raman's classical "last signal" of a maraka
period (HTJAH-II:4846-4849), the RASI HALF ONLY (the Amsa/navamsa half is not computed, same
honest scope as `SYN_R9_MARAKA_SATURN_SIGNAL`'s one-liner). Saturn's transit is computed FRESH
across the death-window's own span via a dedicated `gochara_timeline()` call — NOT reused from
the report's default -10/+20-year `gochara_outlook`, since the ayurdaya-anchored death window
routinely runs decades beyond that display window (confirmed on the Mainpuri chart: confluences
land in the 2060s-2070s while the default outlook only covers 2016-2046) and silently missing
those years would be exactly the kind of silent approximation the project's conventions forbid.
Both the Markdown and HTML renderings repeat, verbatim, that this is **a statement of the method,
not a prediction** and name the null real-outcome finding explicitly — this section must never be
read as a strengthened death signal. Inserted right after The maraka scheme (the section it
directly extends) as v11; `_FROZEN` updated in the same commit.

**v12 amendment (2026-07-26) — AV dasha-seat outlook.** Sixth and last of the menu — the
candidate flagged in advance as weakest, since it is AV-tier and must never visually outweigh the
Raman-band content. `detailed_report.AvDashaSeat` / `_av_dasha_seats()` extend
`SYN_N7_AV_DASHA_SEAT`'s current-MD-only reading (a Mahadasha lord graded by his own
Ashtakavarga bindus at his natal seat — 5+ auspicious, <=3 adverse, 4 mixed, Patel ch015:996-1034)
across every Mahadasha run, the same `_md_runs` collapse `_md_lord_conditions` already uses.
Deliberately kept to the SIMPLER "dasha seat" half of N7 only — the companion `SYN_N7_AV_ANTARDASHA`
one-liner (grading the bhukti lord's houses inside the MD lord's own Ashtakavarga) has a
different, per-house shape not well suited to a flat look-ahead table, and was left as the
existing one-liner rather than force-fit. Rendered with Raman's own reliability caveat
("Ashtakavarga method is equally important. But, it does not seem to be quite reliable",
HTJAH-II:4453-4456) printed at the section head in both renderers, and placed LAST of the three
Life-narrative companions (after Ishta/Kashta and MD-lord condition, both Raman-band) as v12;
`_FROZEN` updated in the same commit. This completes the six-candidate menu discussed with the
user one by one.

**v13 amendment (2026-07-26) — Ruler of the nativity.** First of three higher-order synthesis
sections (the user asked for sections that are "the result of analysis of many sections",
thinking like Raman himself). This is Raman's own opening move, previously made nowhere in the
report: "in order to obtain a first impression we must first of all consider the ruler of the
nativity" (HTJAH-I:16001-16002). Source verification during implementation surfaced a real
doctrinal distinction the design then honoured: in Chart No. 204 the "ruler of the nativity"
Raman examines is the LAGNA LORD, while the temperament passage keys on "the strongest planet in
the horoscope" (HTJAH-I:6248-6249) — two distinct concepts his own worked chart praises when they
coincide ("he is by far the strongest planet... and since he is also the Lagnadhipati, the
foundation is quite sound", HTJAH-I:3880-3882). The card presents both, plus the nature/appearance
comparison against the Navamsa-Lagna lord (the more powerful stamps them, HTJAH-I:3892-3897), the
strongest planet's temperament line (`_RULER_TEMPERAMENT`, lightly condensed from
HTJAH-I:6248-6268 — the Moon is deliberately absent because Raman's passage names no Moon line,
an honest absence), its functional nature / Deeptadi avastha / Ishta-Kashta lean, the fired yogas
it participates in (via `_yoga_planets`), its own MD runs in the window (via `_md_runs`), and its
Gochara outlook windows when it is one of the four tracked slow movers. `build_ruler()` is a pure
re-read of already-computed report fields (the `build_nichod` pattern) — no verdict is touched,
tested by inspection. Inserted right after Chart signature (the natural narrative position — it
IS the first impression); `_FROZEN` updated in the same commit; negative-checked.

**v14 amendment (2026-07-26) — Preponderance of testimonies.** Second of the three higher-order
synthesis sections. Raman defines judgment itself as "the summing up of the influence of
planets" — house, lord, occupants, karaka weighed together (HTJAH-I:983-991), never "on the
basis of one or two combinations" (HTJAH-I:6245-6246), everything "properly weighed before any
result can be deduced" (HTJAH-I:495; HTJAH-II:654-661); his own worked-chart conclusions speak
of "a preponderance of benefic influences" (HTJAH-I:8870). `build_preponderance()` lines up, per
house, the seven ALREADY-COMPUTED witnesses (lagna-frame lord strength via `_lagna_ledger`,
karaka strength, navamsa status, Bhava-Bala rank, SAV band, the matter-varga dashboard
verdict(s) via a new `_MATTER_HOUSE` anchor map verified against each deep reader's own
documented house, and the calibration majority tenor), tallies the leaning ones, and words the
balance in Raman's own preponderance vocabulary. Printed honesty rules: the authoritative
verdict is displayed but NEVER counted among its own witnesses (circularity guard); Raman
states NO numeric N-testimonies rule and his own worked conclusion weighs witnesses unequally
(HTJAH-I:8870-8876), so the equal-weight majority is DISCLOSED as a presentation convention
borrowing his vocabulary, not his weighing; the witnesses are named as the verdict's own
inputs, not independent votes; yogas-bearing-on-a-house (e.g. HTJAH-I:4135-4139, the 4th-house
instance of the recurring Primary Considerations template) are excluded because no yoga→house
mapping primitive exists — a disclosed omission. Houses 1/8/11/12 carry an explicit "absent"
matter-varga row (no dedicated reader). Summary lines name the most-corroborated
favourable/afflicted and most-contested houses (rankings, no cutoffs).

**A bphs-doctrine-reviewer pass corrected the first draft's methodology in three real ways
before shipping** (each correction is pinned by its own regression test): (1) the navamsa
witness was first read verdict-relative ("confirms" on an afflicted house = adverse-leaning);
the reviewer showed this INVERTS the engine's own monotone semantics (`_navamsa_modulate` and
the clause-2 navamsa guard treat "confirms" as always-a-lift and "weakens" as always-adverse) —
corrected to direction-absolute. (2) The Bhava-Bala rank was first leaned by top/bottom half
(rank 1-6 favourable) — an invented numeric cutoff that also assigned direction to a measure
the report's own explainer calls a magnitude (GBB-9:32-34, GBB-9:332 ranks without a cutoff) —
corrected to a neutral, magnitude-only witness. (3) Two scoped over-generalizations in the
lord/karaka witnesses were fixed: on an AFFLICTION_MATTER house a strong lord now reads
adverse-leaning ("a strong dusthana lord strengthens, never rescues" — the engine's own
clause-1.5), and a broken karaka (`karaka_intact` False, the clause-1 veto the headline
actually obeyed) never tallies favourable whatever its raw strength. Also disclosed on review:
HTJAH-I:6245-6246 ("never on one or two combinations") is Raman's wording about mental
diagnosis specifically — the intro now says so, leading with the fully-general HTJAH-I:495.
Inserted right after the House strength cross-check it generalizes; `_FROZEN` updated same
commit; negative-checked.

**v15 amendment (2026-07-26) — Life-chapters.** Third of the higher-order synthesis sections:
one woven prose chapter per Mahadasha run, merging what Life-narrative and its three companion
tables (Ishta/Kashta, MD-lord condition, AV dasha-seat) show as separate parallel paintings.
The narration shape is Raman's own — his Chart No. 203 (Napoleon) reads each dasha period from
yoga + lord condition + house placement + directional influence in ONE paragraph
(HTJAH-I:15950-15999) — and the blending doctrine is his: "astrological predictions can be
accurate when the influences of birth chart are blended with those of Gochara and Ashtakavarga"
(HPA-34:369-381). `build_life_chapters()` is pure JOINS on `_md_runs`: `md_condition` /
`ishta_kashta` / `av_dasha_seats` rows matched per run, `yoga_timing` rows falling inside it
(deduped by yoga+role), houses lit aggregated through the ONE existing `graded_buckets` helper
(best tier per house across the run's bhuktis; `_TIER_ORDER` is ordering only, nothing
re-graded; each house carries its UNCHANGED natal verdict), and `dasha_transit` /
`maraka_saturn` overlaps by interval intersection. Within each chapter the natal factors come
FIRST and transits LAST per Raman's stated priority ("primary importance must be given to the
natal positions and Dasha and only secondary consideration to transiting planets",
HTJAH-I:8410-8411, co-cited HTJAH-II:4679-4687); any maraka overlap repeats the
method-not-prediction disclosure. Placed as the capstone of the Life-narrative companion
cluster (right after AV dasha-seat); `_FROZEN` updated same commit; negative-checked.

**A bphs-doctrine-reviewer pass corrected the first draft before shipping** (chart number,
range and style description of the Napoleon citation all verified exact): (1) the chapter lead
first said "{lord} rules X to Y" — but `_md_runs` bounds are CLIPPED to the display window, so
that asserted a false rulership span for any MD extending past the window edge (a real case:
the canonical chart shows a ~7-year slice of Venus's 20-year MD); corrected to "Mahadasha is
in view X to Y" with the clipping disclosed in the intro, pinned by a regression test. (2) The
HPA-34 blending quote was materially truncated — the sentence ends "together with Vedha or
obstructing forces"; completed, with a disclosure of WHERE Vedha is actually applied (the
Gochara and Dasha x Transit tables, not re-narrated per chapter). (3) "Houses lit... at their
best tier" risked reading a single-bhukti peak as MD-wide and used non-Raman vocabulary;
reworded to "houses whose indications fructify... peak tier reached in at least one bhukti"
with a pointer to the Life-narrative rows for which sub-period. (4) The HPA-24 "stated
maximum" clause now discloses Raman's full maximum also requires freedom from malefic aspect
(not graded by the inherited `at_maximum` flag). (5) A PRE-EXISTING defect found in passing
was fixed: `ConfluenceWindow`'s docstring presented a paraphrase in quotation marks as if
verbatim HTJAH-II:4679 — replaced with Raman's actual words ("Transits are always secondary in
importance. They are like catalytic agents...", HTJAH-II:4679-4687).

**Content amendment (2026-07-27) — per-yoga record leans for the eighth witness.** The
yoga-bearing testimony previously left every "other"- and lunar-kind yoga neutral (deliberate
under-claiming). The prior review noted that leaning the yogas whose PRINTED effect is
unambiguous — with their own citations — would be legitimate. Done: a curated
`_BENEFIC_RECORD_YOGAS` (the five Pancha Mahapurusha, Budha-Aditya, Vasumathi, Jaya, Parvata)
and `_ADVERSE_RECORD_YOGAS` (Daridra "heavy debts, very poor" 3HC:7289; Asatyavadi "loving
falsehood... fraudulent schemes" HPA-20:225) override the kind-based lean; every leaned yoga
still carries its own citation in the Yogas section. Lunar stays neutral (a conditionally-
benefic lunar yoga can be nullified in dusthana formation). The Nabhasa/Akriti shapes never
reach here (they resolve no constituents). Two tests pin the id-validity and lean discipline.
The bphs-doctrine-reviewer pass CONFIRMED the directions and forced two fixes: **Parvata** was a
missing member (resolvable, "wealthy, prosperous... head of a town" 3HC:3170, structurally like
Vasumathi/Jaya) — added; and the docstring's "unambiguously directional" claim over-reached for
the five Pancha Mahapurusha (Sasa carries a mixed-character clause, 3HC:3741-3745) — reworded to
base their lean on raja-status, with Sasa's mixed clause noted as set aside on the fortune axis,
Asatyavadi flagged as a high-base-rate contributor, and Chatussagara noted as
qualifying-on-effect-but-unresolvable. Report-only; golden ratchet unchanged; suite 4472 passed.

**Content amendment (2026-07-27) — the v13-v15 synthesis reaches the plain layers.** "Your
Reading" and the Nichod predated the higher-order synthesis sections and never mentioned them.
Presentation-only weaving, into existing fields (no dataclass change): the Nichod's identity
line now names the ruler of the nativity, its essence opens with the first-impression clause
(and "the foundation is quite sound" when ruler == strongest), and its caution flags the
most-contested house; "Your Reading" opens by naming the strongest planet that most shapes the
temperament (in plain, house-number-free terms via `_PLANET_THEME`) and its notable paragraph
flags the least-settled life-area (the most-contested house mapped through `_PLAIN_AREA`). To
feed this, `build_detailed_report` now builds ruler/preponderance/life-chapters BEFORE the two
plain builders, which read the enriched report rather than the empty sentinels. Two regression
tests pin the weave and the no-house-numbers rule of the plain layer. Golden ratchet unchanged;
suite 4471 passed.

**Content amendment (2026-07-27) — BPHS's own serpent's-curse verses recovered and encoded.**
The block between the childlessness yogas (tail of BPHS ch.82) and the father's-curse yogas
(head of ch.83) — BPHS Ch.83 verses 9-16, the SERPENT'S curse, eight numbered combinations —
was skipped by the original library scrape. Recovered from the same archive.org djvu as
`bphs/vol2_chapter_083_iii.md` and encoded per verse (`_SERPENT_CURSE_YOGAS`): 7 of the 8 (only
#5, which needs Gulika, stays on record). These are BPHS's own, more specific than the
Prasna-Marga serpent summary the engine already carried in `_serpent_curse` (e.g. #1 requires a
Mars aspect, #2 a Moon-in-5th aspected by Saturn) — both are now surfaced as distinct classical
sources. Report-only; golden ratchet unchanged; suite 4469 passed.

**Content amendment (2026-07-27) — the papakartari (hemming) primitive; four more curse-yogas
encoded.** A new pure-geometry module `doctrine/hemming.py` implements kartari (hemming) in
both forms Raman uses: the PLANET form (malefics in the signs flanking a planet, already
covered by the DSL leaf `conditions.HemmedBy`, now refactored to delegate to the shared
geometry) and the HOUSE form (malefics in the 2nd and 12th from a possibly-EMPTY bhava — the
capability nothing had, needed by "the Ascendant is hemmed" verses and the SYN_N6 bhava leg).
Geometry pinned to the 2nd/12th (HTJAH-I:1181-1184), natural malefics as flankers with the
nodes counted (HTJAH-I:1127); cancellation is deliberately left to callers as a separate
doctrine layer (HTJAH-I:2532-2533). This closes the "on record pending a hemming primitive"
gap: BPHS father's-curse #1-2, mother's-curse #1's hemming disjunct, and mother #9 (the empty
Ascendant hemmed) are now encoded — father is 11 of 11, mother 12 of 13 (only #10, OCR-garbled,
remains on record with Praśna Mārga's Gulika variant). SYN_N6's note is updated to record the
primitive now exists. Report-only; golden ratchet unchanged (261/293); suite 4466 passed.

**Content amendment (2026-07-26) — the curse-yogas re-encoded faithfully (the editorial proxy
retired).** The pitru surface's `_ancestral_curse` proxy (9th+Sun / 4th+Moon malefic-touch,
flagged with an honest-scope note when a reviewer found it tests a region BPHS-83's verses
never use) is replaced by per-verse encodings of BPHS Ch.83's OWN numbered combinations.
Father's curse: 9 of the 11 combinations from `bphs/vol2_chapter_083_i.md` (verse 20.30,
L33-93), each with a per-verse cite (BPHS-83:41...92). Mother's curse: the missing BPHS source
block was RECOVERED from the same archive.org scan the library's scrape drew from (the scrape
had cut off at the section heading — `BPHS-83:130` cited a heading, not doctrine) and saved as
`bphs/vol2_chapter_083_ii.md` with a provenance frontmatter; 11 of its 13 combinations (verses
34-50, L114-166) are encoded with per-verse cites (BPHS-83-ii:114...165). On record, unencoded,
each with its reason printed in the reading's notes: father #1-2 and mother #9 (need a
papakartari/hemming primitive — the SYN_N6 precedent), mother #1's hemming disjunct, mother
#10 (OCR-garbled), and Praśna Mārga's father's-curse variant (needs Gulika). Interpretation
conventions (association = co-occupancy; father #3's degenerate-true clause; mother #5's
strict-set reading) are documented in the module. The layering note is rewritten: the
curse-yogas now demonstrably test the 5th/Ascendant (father) and 4th/5th/Moon (mother) chains
— a genuinely different region from the House 9/4 personal significations, making the
no-contradiction separation cleaner than the proxy allowed. A per-verse cite test pins every
BPHS-83-ii cite to the exact line of the recovered file that starts its numbered combination.
NOTE ON REVIEW: the standing pre-commit bphs-doctrine-reviewer workflow first FAILED on
session usage limits; an inline line-by-line source verification of all 20 encoded checkers
was performed and documented in its place, and the commit shipped on that basis. The
independent pass was then re-run after the limit reset (2026-07-27) and COMPLETED: the
father list was CONFIRMED 9/9 clause-faithful (one documentation note — father #6's
Cancer-lagna degenerate-true case, now disclosed alongside #3's); the mother list surfaced
ONE substantive finding — #5's first encoding was placement-only and dropped the verse's
operative samyoga condition (it fired when the malefics sat together in the OTHER of the two
houses, associated with neither); tightened to require each of Saturn/Rahu/Mars to co-occupy
the 5th lord's or the Moon's house, pinned by a divergent-case regression test. The reviewer
also independently confirmed the recovered `vol2_chapter_083_ii.md` block byte-matches the
original scrape's tail (no mis-splice) and that every per-verse cite line is exact. Three
further conventions were added to the module's disclosure block on its notes (plural
"malefics" = at-least-one; mother #1's stricter shared-conjunct parse; mother #10's plausible
"or"→"are" reconstruction, still conservatively on record).

**Content amendment (2026-07-26) — yogas become the eighth witness
(`yoga_house_bearings`).** The Preponderance section's one disclosed omission is closed: yogas
(Raman's Primary Considerations, HTJAH-I:4135-4139) are now tallied per house. The mapping is
Raman's own worked-chart method, not an invention: a yoga bears on the houses its CONSTITUENT
PLANETS own, occupy or aspect ("the nature of results depends also on the nature of ownership
of the planets causing the yoga... predominantly those of the 2nd and 11th houses",
Chandramangala, HTJAH-I:2879-2890; Truman's Gajakesari "has reference to the 2nd, the 10th,
the 4th and the 7th houses", HTJAH-I:15824-15826; Dhana/Raja yogas named FOR their constituent
lords' houses, HTJAH-I:17049-17052, 15831-15832). `synthesis_rules.yoga_house_bearings()`
resolves constituents via the existing `_yoga_planets` and tests the DIRECT factors only
(ownership/occupancy/whole-sign aspect — the first three of the locked HTJAH-I:1586-1596
five-factor method): including the full `timer_set` (lord-association + karaka +
lord-from-Moon factors, the dasha-fructification extensions) saturates multi-planet yogas onto
all twelve houses, where Raman's own worked example names FOUR — a deliberate, disclosed
narrowing using only locked-doctrine factors. Each bearing yoga is one testimony row leaning
ONLY by its encoded kind (raja/dhana favourable, arishta adverse; lunar/other neutral — the
"other" bucket mixes Daridra with the Mahapurushas, so leaning it would invent a
classification). Disclosed limits, printed in the intro: whole-chart pattern yogas carry no
constituent identity and are unmapped; the forming-house strength modifier (dusthana
formation nullifies, HTJAH-I:2948-2956) is not graded. The per-house Conclusion line names
the bearing yogas, mention-only. Canonical-chart effect worth recording: H6 moved from
well-corroborated to contested (a raja-kind yoga bearing on it added a favourable witness
against the afflicted headline) — the tally is disclosure, the verdict unchanged.

**Content amendment (2026-07-26) — the per-house Conclusion line (the faithful "Net
Confluence").** A user proposed a "Net Confluence Synthesis Engine": collapse verdict +
preponderance + Bhava-Bala rank + SAV into ONE of five named archetypes per house
("Unshakeable Peak", "Latent/Mitigated Friction", ...) with rank-cutoff criteria, and asked
for a critical review. The underlying need was accepted — the report showed the full jury roll
with no per-house summation — and corpus research found the need is met by RAMAN'S OWN closing
device: essentially every worked HTJAH analysis ends with a "Conclusion.—" summation weighing
house, lord and karaka in free prose (~149 occurrences in HTJAH-I, ~107 in HTJAH-II; e.g.
HTJAH-I:4485, 8513, 8870). `detailed_report.house_conclusion()` now composes exactly that — a
free-prose closing line per house from already-computed rows, consumed by BOTH renderers.

**The proposal's mechanism was REJECTED on review, and the rejections are on record so they
are not re-proposed:** (1) the five named archetypes — the corpus shows Raman's only fixed
label taxonomy is longevity's four bands (HTJAH-I:9699-9705); every house conclusion of his is
free prose, and labels like "Unshakeable"/"Low-impact" are implicit life predictions the
Measured Truth forbids; (2) the rank cutoffs (top-6/1-5/8-12) — GBB-9:332 ranks with NO
cutoff (the v14 review had already removed exactly such a threshold); only the superlative
pair (rank 1 / rank 12, his own "most powerful... least powerful" vocabulary) triggers a
tendency clause, and those clauses are verbatim reuses of the already-reviewed v8 note; (3)
witness-majority as mitigation ("6-1 benefic ⇒ affliction is superficial") — a verdict
override of Raman's own weakest-link rule, contradicting v14's printed honesty rule and
double-counting non-independent witnesses; on contested houses the Conclusion says instead
"disclosure, not re-weighing: the headline follows the weakest-link rule and stands"; (4)
real-world severity claims ("rarely causes acute damage") — the null real-outcome finding
forbids them; a regression test bans the mitigation vocabulary outright. One genuinely new
hedged clause (rank-12 + afflicted: low strength reads as indications less fully manifest, a
tendency not a rule) was flagged to the doctrine reviewer explicitly. Presentation-only, no
new SectionSpec row (the split-status-note precedent).

**Content amendment (2026-07-26) — the confluence audit: real bugs fixed, genuine multi-axis
divergences explained.** The user asked for a full-report pass ("apply your astrological brain at
peak, find the confluence points") after noticing lingering contradictions across the ~30
sections built this session. A close-read (Explore agent) plus a root-cause investigation split
the findings into two kinds, per the project's own doctrine — errors get fixed, genuine classical
divergences get explained, never forced to agree:

*Real bugs, fixed (presentation-only — no `Verdict` value changed):*
- **Lord/Karaka strength mislabel.** The house-pillar line paired `pf.lord`'s name (always the
  LAGNA-frame lord) with `lord_strong`/`navamsa_status` from whichever frame (lagna or Moon) had
  won as the "lead" ledger — so a Moon-frame win could label the WRONG planet's strength next to
  the lagna-frame lord's name (confirmed: "Lord Mars (strong) | Karaka Mars (weak)" for the same
  planet). `HouseProforma.as_house_verdict()` already had the correct lagna-frame lookup, unused
  by the renderers. Fixed via a new `_lagna_ledger()` helper in `detailed_report.py`, applied in
  both renderers.
- **SAV band wording disagreement.** `_house_strength_rows()`'s `>28/<28/==28` cutoff disagreed
  with the older, more-depended-on `_ashtakavarga_overlay()`'s `>=30/<=25/else` cutoff for the SAME
  bindu count (26-27 read "average" in one place, "below average" in the other). Aligned the newer
  code to the established thresholds.
- **D-7 (Saptamsa children) softened.** Added a plain-language note (mirroring the Kuja-dosha
  precedent in `render_navamsa.py`) explaining the classical affliction phrases are shorthand for
  DEGREES of difficulty, not stand-alone predictions, cross-referencing the calibrated House-5
  reading as the thing that actually decides the verdict.
- **Jaimini 9th/10th disambiguated.** Soul & destiny's Karakamsa-counted 9th/10th (Jaimini) reads
  as ordinary D1 house numbers unless qualified — every bare reference now says "Xth from
  Karakāṁśa" and names, for the 9th and 10th specifically, which D1 house it is NOT.

*Genuine multi-axis divergences, explained (no verdict touched, an explainer added at the point of
visible clash):*
- **`SYN_N1_LP_MATRIX`'s `simple_meaning`** (`doctrine/synthesis_rules.py`) now states that the
  Laghu Parashari functional-role/relation scheme is a DIFFERENT, narrower classical framework
  than both Raman's own per-Lagna functional-nature table (Chart signature, HTJAH-I:523-604 +
  yogakaraka overlay, HTJAH-I:606) and his Bhukti-tier grading (Life-narrative,
  HTJAH-I:1588-1596, 1635-1640, 2588-2599) — and that per this project's own governance, Raman's
  own grading wins wherever they diverge.
- **Pitru dosha's new layering note** (`judges/pitru_dosha_reading.py`) explains that the
  ancestral-curse yogas and the House 9/4 "father"/"mother" significations test the SAME
  house/kāraka data at DIFFERENT thresholds (a narrow malefic-touch-plus-kāraka-affliction gate
  here vs. `judge_signification`'s full multi-factor aggregation there) — not unrelated layers, so
  a favourable House 9 or 4 verdict and a firing curse-yoga are not mutually exclusive.
- **Integrated insights gained a general "how to read several strength measures at once" intro
  paragraph**, generalizing the already-shipped House-strength-cross-check note (magnitude vs.
  direction) to the FULL set of independent axes a reader meets in this report: verdict
  (direction, HTJAH-I:468-478), Bhava Bala/Shadbala (magnitude, GBB-9:32-34), Avastha (state, HPA
  Ch.7), Ishta/Kashta (tendency, GBB-10:134), and AV bindus (a separate, lower-reliability
  corroborating tier, HTJAH-II:4453-4456) — stating plainly that these axes are not meant to
  always agree, so reading two of them apart is not a contradiction to resolve.

**Adversarial review.** All three explainer texts above went through a parallel
bphs-doctrine-reviewer pass (a Workflow run, not a single sequential Agent call, per the session's
"ultracode" mode) before shipping. Two real issues surfaced and were fixed: the `SYN_N1_LP_MATRIX`
text had folded yogakaraka status into the wrong citation range (HTJAH-I:523-604 covers the
per-Lagna table only; yogakaraka is HTJAH-I:606, a separate section) — split into two citations;
and the Pitru-dosha note's first draft called the two layers "independent," which the reviewer
correctly flagged as overstating a genuine data-sharing relationship — reworded to "a different
threshold on the same ground." One reviewer finding (HTJAH-II:4453-4456 supposedly not resolving
in the source) was independently re-verified and found to be a FALSE POSITIVE: the reviewer had
searched the Volume-I source directory instead of the separate Volume-II directory
(`how_to_judge_horoscope_raman2/`), where the quote resolves exactly at the cited lines — the
original citation was restored unchanged. A genuine, lower-confidence, PRE-EXISTING gap also
surfaced (out of this amendment's scope, not fixed here): `_ancestral_curse()`'s malefic-touch
test is an editorial proxy for BPHS-83's curse doctrine, not a literal encoding of its specific
numbered yogas (the on-disk BPHS-83 source is itself a partial OCR fragment) — flagged with an
honest scope note in the function's own docstring; a fuller re-encoding needs a cleaner BPHS-83
source and is left for a future session.

## Standing rules

- **Append-only.** Amendment = add a `SectionSpec` row + update this doc + update the contract
  test's `_FROZEN_IDS`, all in one commit whose message says why.
- **Two voices, always.** Raman's verdict is never altered by presentation (the verdict-authority
  invariant test); the empirical overlay is always tagged not-Raman.
- **Sensitive sections stay framed.** The maraka section carries the "method, not prediction"
  disclosure; the pitru section carries the CLASSICAL_NONCITABLE provenance banner. Removing
  either framing is a contract violation in spirit even where the test cannot see it.
- **v2 provenance.** The complementary sections (dashboard, Shadbala, maraka, Gochara/Vedha,
  soul, pitru, and the 9 vargas completing the Shodasavarga) were added 2026-07-25 from surfaces
  the engine already computed; no engine logic changed.
