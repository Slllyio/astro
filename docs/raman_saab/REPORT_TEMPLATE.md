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
| 5 | What stands out | `## What stands out in this chart` | `#stands-out` | v1 |
| 6 | The twelve matters at a glance | `## The twelve matters at a glance` | `#dashboard` | v2 |
| 7 | Chart signature | `## Chart signature` | `.sig` (page header) | v1 |
| 8 | Chart grids Rasi/Navamsa (HTML only) | — | `#charts` | v1 |
| 9 | Planetary positions | `## Planetary positions` | `#positions` | v1 |
| 10 | Shadbala | `## Shadbala` | `#shadbala` | v2 |
| 11 | Yogas | `## Yogas present in this chart` | `#yogas` | v1 |
| 12 | Yoga x Dasha timing | `## Yoga x Dasha timing` | `#yoga-timing` | v7 |
| 13 | Ashtakavarga | `## Ashtakavarga` | `#sav` | v1 |
| 14 | House-by-house | `## House-by-house reading` | `#houses` | v1 |
| 15 | Longevity (band-first) | `## Longevity` | `#longevity` | v1 |
| 16 | Maraka scheme | `## The maraka scheme` | `#maraka` | v2 |
| 17 | Life-narrative (MD→AD, 4-tier) | `## Life-narrative (Vimshottari Dasha)` | `#timeline` | v1 |
| 18 | Gochara with Vedha | `## Current transits (Gochara` | `#gochara` | v2 |
| 19 | Dasha x Transit confluence | `## Dasha x Transit confluence` | `#dasha-transit` | v6 |
| 20 | Divisional deep-reads (15 vargas) | `## Divisional deep-reads (Shodasavarga)` | `#vargas` | v1 |
| 21 | Career | `## Career (HTJAH-II` | `#career` | v1 |
| 22 | Deeptadi avasthas | `## Deeptadi avasthas` | `#deeptadi` | v1 |
| 23 | Jaimini Karakamsa (stub) | `## Jaimini Karakamsa` | `#karakamsa` | v1 |
| 24 | Soul & destiny (extended) | `## Soul & destiny` | `#soul` | v2 |
| 25 | Pitru dosha screen (bannered) | `## Pitru dosha` | `#pitru` | v2 |
| 26 | Integrated insights (cross-feature synthesis) | `## Integrated insights` | `#synthesis` | v3 |
| 27 | Glossary | `## Glossary` | `#glossary` | v1 |
| 28 | Nichod (the capstone distillation) | `## Nichod` | `#nichod` | v4 |

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
