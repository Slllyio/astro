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
| 12 | Ashtakavarga | `## Ashtakavarga` | `#sav` | v1 |
| 13 | House-by-house | `## House-by-house reading` | `#houses` | v1 |
| 14 | Longevity (band-first) | `## Longevity` | `#longevity` | v1 |
| 15 | Maraka scheme | `## The maraka scheme` | `#maraka` | v2 |
| 16 | Life-narrative (MD→AD, 4-tier) | `## Life-narrative (Vimshottari Dasha)` | `#timeline` | v1 |
| 17 | Gochara with Vedha | `## Current transits (Gochara` | `#gochara` | v2 |
| 18 | Divisional deep-reads (15 vargas) | `## Divisional deep-reads (Shodasavarga)` | `#vargas` | v1 |
| 19 | Career | `## Career (HTJAH-II` | `#career` | v1 |
| 20 | Deeptadi avasthas | `## Deeptadi avasthas` | `#deeptadi` | v1 |
| 21 | Jaimini Karakamsa (stub) | `## Jaimini Karakamsa` | `#karakamsa` | v1 |
| 22 | Soul & destiny (extended) | `## Soul & destiny` | `#soul` | v2 |
| 23 | Pitru dosha screen (bannered) | `## Pitru dosha` | `#pitru` | v2 |
| 24 | Integrated insights (cross-feature synthesis) | `## Integrated insights` | `#synthesis` | v3 |
| 25 | Glossary | `## Glossary` | `#glossary` | v1 |
| 26 | Nichod (the capstone distillation) | `## Nichod` | `#nichod` | v4 |

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
