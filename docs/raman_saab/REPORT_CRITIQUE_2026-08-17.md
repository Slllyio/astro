---
title: "Report critique 2026-08-17 — six-specialist chapter audit"
kind: record
topic: report
measured: false
updated: 2026-08-17
tags: [raman-saab, record, report, critique]
---
# The Manuscript Audit — six-specialist critique of every report chapter (2026-08-17)

Six parallel specialist reviews (opening/synthesis, foundation, yogas & strength,
house judgments, matter monographs, timing/divisional/soul), each generating the
canonical Bangalore chart's full render and reading every composer at source, twice —
once as a senior Raman scholar, once as a first-time client. The doctrine corpus was
ABSENT on the review machine (which itself exposed a family of real failure modes);
every Raman citation herein is repeated from the codebase's own records and MUST be
corpus-verified before encoding. Every recommendation is add-only or a located fix:
no computed data hidden, Measured-Truth framing and the golden ratchet untouched.

The consolidated blueprint is sequenced in four waves; the six full critiques follow
as appendices A-F (preserved verbatim so this session's derived knowledge is not lost).

## Wave 0 — wrong on the page today (fix before anything)

1. **Longevity repr leak**: `y, mo, d = r.longevity_ymd` (detailed_report.py:2656) is
   clobbered by `for y in r.yoga_deep:` (:3140); :3401 renders a YogaDeepRead repr
   inside the "about 88 years" sentence. Rename the loop variable.
2. **Empty verbatim quotes** rendered as `""` with citations when corpus absent:
   marriage x3 (:3878/:3895/:3906), children (:3929), arishta antidotes (:3501),
   every yoga deep-read definition; the houses' classical-text level silently
   vanishes. Render an honest corpus-absence line instead.
3. **Yoga deep-read participant pipeline is wrong** (syntactic scan): Sunapha averages
   5 candidates ("7.00 rupas"), Gajakesari drops the Moon ("MOON"!="Moon"),
   Vesi/Pasa/Amala/Raja resolve zero -> false "no Shadbala on this chart", comparison
   ranking is a -1-sentinel artifact. Fix: call `synthesis_rules._yoga_planets`.
4. **Raw `LordQuality(...)` repr** in every yoga's Operating-periods (markdown + JSON).
5. **Maraka-flooded activation lines** on H4/H7/H9: five "(maraka)" windows, zero
   ordinary fructification windows (house_template.py:1365 sort + cap-5). Cap maraka
   at 1-2, keep lord/karaka windows.
6. **H3 navamsa self-contradiction**: pillar line reads the lagna ledger, reading line
   the lead/Moon ledger; frame never named.
7. **Two chapters silently vanish without corpus**: psych profile
   (monographs.py:243-245 returns None) and karmic evolution. Degrade gracefully.
8. **ASCII-fold garbling**: `render.py:22 _REPL` lacks `·` (badges print `?`); `±`
   prints `?60` in rect confidence (:3042/:3051).
9. **What-stands-out sort/header contradiction** (detailed_report.py:683-684): "Rare
   readings first" but the only rare row lands last; favourable-at-32% rows unglossed;
   `_plain_intensity` (:2325) latent inversion (keys on percentile only).
10. **Small blemishes**: Rahu chapter dangling "neutral for this Lagna: ."
    (:2082-2084); "2th/3th/4th" ordinals; decade chips duplicated at two tiers
    (life_arc.py:100-105); Nichod ".;" join + unwoven spotlight; Rules badge counts
    firings while Sources dedupes; `_MATTER_HOUSE` (tension_narrator.py:21) missing
    7 dashboard keys; D-9 Kuja-dosha note contradicts the full H7 `_KujaDosha` rule.

## Wave 1 — computed but never shown (REPORT COMPLETENESS debts)

- BAV 7x12 matrix + HPA-26 Trikona/Ekadhipathya reductions + Sodya Pinda: computed,
  regression-pinned, consumed by NO surface.
- Baladi/Jagradadi avasthas (house_template.py:540-575): actively demote verdicts,
  never rendered.
- `lord_quality` md/antar delivery tags: dropped by the markdown timeline renderer
  (:3544) — the licensed antidote to par-excellence flooding.
- Bhava Bala rupas column: in JSON/page, dropped from the markdown cross-check.
- Pratyantars (vimshottari.py:120-154, HTJAH-II:668-702): never rendered anywhere.
- Sade-Sati dates + adverse gochara segments: only favourable windows rendered; the
  canonical native is in peak Sade-Sati and cannot learn when it ends.
- Distinctive readings: 17 computed, 7 shown (cap n=7).
- Chara dasha: undated, no current-sign marker.
- Positions table: subtitle promises "Exact degrees", table has none, no Asc row.
- Per-planet maraka qualifying clauses: known at `add()`, discarded.
- The Muhurtha surface is unmentioned in markdown/standalone.

## Wave 2 — Raman-licensed additions (per group; citations to corpus-verify)

**Synthesis layer**: period-pairing everywhere (HTJAH-I:1586-1596) — with the
2026-08-17 prediction unblock these clauses may carry dates; digest rank-0 governing
factor (HTJAH-I:16001) + longevity-foundation item; stronger-frame sentence in Your
Reading (HTJAH-I:645-646); rebuild Full life synthesis as content re-reads + a
Present-chapter theme; info-content breakdown strip + name all 17 distinctive.

**Foundation**: Ruler chapter gets the ruler's full condition block + sound/unsound
verdict (HTJAH-I:3880-3882) + Chandra-lagna candidate; signature gains balance-of-dasha
at birth, degrees, paksha read, Sun/Moon strength flags, lagna-lord clause, stronger-
frame variant named in-render; planet bios gain functional nature (Jupiter bio vs
signature currently clash), itemized aspects, Shadbala header, avastha consequences,
named karakatvas, node-lordship wording fix; Deeptadi promoted to testimony (HPA
Ch.7:46-83 RESULTS + houses ruled + secondary states + node-Sakta note); Shadbala
ratio column + weakest-component diagnosis; psych profile (once un-silenced) gains
Moon-in-sign (HTJAH-I:1452) + Mercury-buddhi.

**Yogas & strength**: coverage honesty (72 of ~300 + family breakdown + cancelled-
Kemadruma + notable absences); deep-read per-yoga SYN_R1 line (3HC:1359), placement +
functional-nature tags, "none of the ENCODED cancellations" narrowing; timing MD-
context on AD rows + NOW marker + next-ripening summaries + vargottama-combust
reconciliation (HTJAH-I:5372); preponderance witness-class tags (core HTJAH-I:983-991
vs overlay) + direct-vs-aspect yoga bearings.

**Houses**: chief combinations per house (FiredRule.text prose + citations); frame
disclosure line (HTJAH-I:645-646); moderating-factor clause; current-period tier line;
missing significations (H1 appearance/character, H3 writing/neighbours, H2 food,
H5 speculation, H6 servants, H12 bed-comforts).

**Matters**: marriage happiness/coverture split + Kuja cancellation narration
(HTJAH-II:2579-2622) + spouse description + computed timing lean + Jupiter-transit
trigger; health anatomical mapping (HPA sign->body Kalapurusha + planet->disease —
the biggest content gap in the report); children D-7 corroboration row + shorthand-
reframe note BEFORE fired rules + Jupiter condition; profession 10th-from-Moon/Sun
derivations (genuine doctrine gap) + D-10 row + H10 timing + same-graha convergence
annotation; wealth dhana/Daridra row + lord conditions + non-differential disclosure;
longevity/arishta balarishta screen disclosure + label harmonisation + two-case
no-bhanga distinction.

**Timing/divisional/soul**: role-preserving timer_set -> influence-basis tags; this-
year lens + pratyantar drill-down for the current bhukti; the adverse half of the sky
(Sade-Sati strip, adverse windows table, adverse dasha x transit confluences — drop
the gochara_good-only filter, HPA-34:369-381 — plus per-row synthesis sentences);
divisional verdict-first summaries + D-27/40/45/60 domain sentences + karmic re-reads
instead of embedded blocks; chara dasha dated + karakamsa pairing (Studies in Jaimini,
verify passage) + nodal-MD dispositor sentence (HTJAH-I:2764/8566); Muhurtha
scan-the-day mode + a pointer line in markdown.

## Wave 3 — structure & reading experience

Verdict-first 12-row house strip + Conclusion promoted; calibration rollups above
retained rows; cross-references at the point of confusion (H10->PREC-1, H8->Longevity,
WARNING->Information content); Judgment graph out of position 2 + navamsa +
aspects-the-lord/conjoins-the-lord edges; Yoga x Dasha rows grouped by yoga; Pitru
leads with the finding; maintainer notes out of client prose.

## Decisions for the USER (not taken unilaterally)

1. Shadbala Sun minimum: 5.0 tuned vs GBB-8:303's printed 6.5 — retune or relabel
   (render currently claims "RAMAN'S OWN minimum", inaccurately for the Sun).
2. Preponderance raja/dhana yoga-lean house-conditional (favourable on non-dusthanas
   only)? — bphs-doctrine-reviewer pass required.
3. Jaimini overlay aspect scheme: rasi drishti (`primitives/rasi_drishti.py`, unused
   there) vs graha drishti — doctrine review.
4. Decade timeline whole-life mode default.
5. (Carried from Stage-9 scorecard) holdout gate + the 90% bar vs proven ceiling.

---


# Appendix — full critique: opening_synthesis (verbatim agent report)

I built the canonical report from the Bangalore baseline, sliced out the opening/synthesis chapters, read them as a client would, then read every composer (`build_plain_reading`/`build_nichod` in `detailed_report.py`, `insight_digest.py`, `judgment_graph.py`, `interpretation_guide.py`, `life_arc.build_life_synthesis`, plus the `information_content`/`distinctive_entries`/`tenor_split` machinery). Critique below, per chapter, then the top-5 moves.

---

## 1. Your Reading (`build_plain_reading`, /home/user/astro/app/raman_saab/detailed_report.py:2337)

**What it does today:** hand-written plain-English prose over the 12-matter dashboard verdicts, grouped into five life-themes, plus strongest-planet opening, census-dominant planet, running MD/AD, top-3 distinctive entries, and the S3 reconciliation sentences.

**Verdict: strong (astrologically adequate, UX strong).** As reader experience this is the best chapter in the report — warm, honest, jargon-free, deterministic-variant phrasing so charts don't all read identically. Astrologically it honors Raman's "first impression from the ruler" habit (HTJAH-I:6248) but drops two of his most characteristic disciplines: the Lagna/Moon dual frame and pairing indication with period.

**ADD:**
- **The stronger-frame sentence.** The engine already computes `stronger_frame` (MOON here, HTJAH-I:645-646, cited in Chart signature) but Your Reading never says the reading was weighed from the Moon. Raman states the judging frame before judging — one plain sentence: "This chart is read chiefly from the Moon's position, which is stronger than the rising sign here — a choice Raman himself prescribes." Pure re-read. *(Source: HTJAH-I ch. on Judgment, "ascendant or the Moon, whichever is stronger" — corpus-verify line 645-646.)*
- **Period-pairing per life-theme.** Raman never states an indication without its fructification window (HTJAH-I ch.1, "When Do Indications Fructify?" — the locked timer_set doctrine). The judgment graph already computes "periods that light it (at best)" per house. Each of the five theme paragraphs should close with one undated clause: "these matters ripen most fully in the chapters ruled by Venus, Sun and Moon." Planet-period naming, no dates, no events — guard-safe, and it is the single most Raman-like thing this chapter could gain. *(Source: HTJAH-I:1586-1596, already locked in CLAUDE.md.)*
- **The vitality/longevity foundation line.** The classical order Raman follows (HTJAH-II longevity chapter; the dictum that ayurdaya is ascertained before predictions — corpus-verify) makes longevity the gate to everything else. A single guarded plain line ("the chart's vitality reads at the full classical band — a foundation, not a forecast") would mirror his sequence; keep all death-token discipline (band word only, no number here — the number stays in the Longevity section).

**MODIFY:**
- The reconciliation bullets leak method jargon into the one enforced jargon-free zone: "(PREC-3)", "never re-voted", "its dedicated reader". Keep both sentences (they're valuable) but gloss the tokens plainly and let the PREC id be the parenthetical for the curious, e.g. "…the report keeps both and explains which to trust in 'How to read this report' (rule PREC-3)". The current phrasing assumes the reader has already read a section that comes later.
- Latent wording bug in `_plain_intensity` (line 2325): it keys only on `favourability_percentile`, so a **favourable-verdict** entry at the 32nd percentile (exactly this chart's H4 education) would render "notably challenging" while its verdict says favourable. It doesn't surface here only because just the top 3 distinctive entries are shown. Guard the intensity word on verdict direction + percentile jointly.

**UX:** ordering (first) is right; length right; the five-theme grouping is exactly how a client thinks. P1 for the period-pairing add; the rest P2.

---

## 2. What matters most — ranked digest (/home/user/astro/app/raman_saab/insight_digest.py)

**What it does today:** a fixed editorial sequence (convergence → afflicted convergence → current MD → top-3 synthesis insights → tension → top-3 distinctive), each item a pure re-read with citations and section bridges.

**Verdict: adequate-to-strong.** The deterministic, non-LLM ranking is the correct architectural call, and the convergence/tension pair is genuinely how Raman weighs ("preponderance of testimonies", HTJAH-I:8870). But the *sequence* is not Raman's: he opens a judgment by naming the governing factor (the ruler of the nativity / strongest planet), then longevity, then bhavas. The digest opens with a house.

**ADD:**
- **A rank-0 "governing factor" item** from the already-built Ruler card: Lagna lord Mercury vs Shadbala-strongest Sun, coincide or not, one line. Raman's "in order to obtain a first impression we must first of all consider the ruler of the nativity" (HTJAH-I:16001-16002, already cited in the Ruler section) licenses making this literally item #1. Pure re-read of `r.ruler`.
- **A "foundation" item: longevity band + Balarishta/bhanga status.** The digest currently ranks children and moksha but never mentions that longevity is purna with a cancelled/absent arishta — the classical precondition for everything else it ranks. Re-read of `r.longevity_class` + `r.balarishta` + the "Strength lifts the longevity band" insight (HTJAH-I:11703). *(Corpus-verify the longevity-first dictum's exact HTJAH-II line.)*
- **Shadbala weighing on the convergence/tension items.** When Raman says a house is strong he says *by how much relative to the rest* (Bhava Bala ranking, GBB-9:332 — an insight the report already fires: "strongest bhava H12, weakest H6"). The convergence item for H4 should carry its Bhava Bala rank in one clause. Re-read of `house_strength` rows.

**MODIFY:**
- The timing item's `lean` reads "favourable" (from the Ishta lean) while the bhukti-tier insight two rows down says the same period is graded **ordinary** (lords not associated, HTJAH-I:1635). Both are true on different axes, but side-by-side in one table with no axis label it reads as self-contradiction. Add the tier to the timing item's own detail ("…an *ordinary*-grade sub-period by Raman's four-tier scheme") so the table is internally coherent.
- Table numbering starts at 0 ("| 0 |") — render 1-based for humans.

**UX:** the three `distinctive` rows duplicate the What-stands-out table that sits 20 lines above; they earn their place only because the digest is the "read only this" surface — fine, but the two chapters should cross-reference explicitly ("full table above"). P1 (governing-factor + foundation items), P2 (rest).

---

## 3. Judgment graph (/home/user/astro/app/raman_saab/judgment_graph.py)

**What it does today:** nodes/edges over houses, grahas, yogas, MD runs, insights and section relations; rendered as a per-house table (who touches it, natural karakas, periods that light it at best) plus edge statistics.

**Verdict: adequate astrologically, weak as a chapter-2 reader experience.** The per-house `house_facts` table is a genuinely good invention — it is Raman's five/six-factor influence doctrine (HTJAH-I:1586-1589) made visible, and the "at best" honesty on peak grades is exemplary. But the graph is missing the two factors Raman never omits, and its placement is wrong.

**ADD:**
- **Navamsa disposition on planet nodes / house rows.** Raman's dasha grading and dignity judgment always pass through the navamsa (HPA-24:51-86 — "at its maximum only when strong in both charts", already fired as an insight). The graph has no navamsa data at all; the engine computes vargottama and navamsa status elsewhere (Ruler card shows it). Add it as node `data` and a table column. Pure re-read.
- **The two missing timer-set factors as edges.** The locked doctrine says a planet influences a house via the house *or its lord* — aspects-the-lord and conjoins-the-lord edges (plus lord-from-the-Moon) are part of the locked five/six factors but the graph only encodes lord_of/occupies/aspects on the *house*. If the timer_set already computes them (it does, per CLAUDE.md), surface them as `aspects_lord_of` / `conjoins_lord_of` relations so the table's "what touches it" sentence matches the doctrine the timers actually used. Currently the "Periods that light it" column can list a planet whose connection the "What touches it" sentence never explains — a reader can't reconcile the two columns. *(Source: HTJAH-I:1586-1589, locked.)*
- **Yoga→participant edges.** The module's own docstring records this honest gap (FiredYoga carries no participant list). The digest's `yoga_house_bearings` already resolves constituents; closing the gap is licensed by 3HC:1359 (stronger constituent delivers the yoga).

**MODIFY:** nothing in the mechanics; the tier-peak fix and grade-regex are sound.

**UX:** this is a mechanics appendix sitting at position 2, between the plain reading and the honesty gate — a lay reader hits a 12-row × 5-column table with "254 edges — karaka_of 56, timer_of 59" before they've seen a single verdict card. The interpretation guide's own reading order (step 2 = twelve matters) disagrees with the physical order. Move the chapter after the dashboard/houses (reordering removes nothing), or at minimum move the edge-statistics paragraph below the table. P2.

---

## 4. How to read this report (/home/user/astro/app/raman_saab/interpretation_guide.py)

**What it does today:** chart-independent precedence rules (PREC-1..12), parallel lenses (PAR-1..4), the five independent axes, and a five-step reading order — machine-readable and rendered.

**Verdict: strong.** This chapter is the report's intellectual spine and has no real equivalent in commercial astrology software; the closed relation vocabulary and repo-line authority pointers are exactly right. Raman himself works with implicit precedence (dasha over transit, HTJAH-II:4679; verdict over AV, HTJAH-II:4453) and this makes it explicit and citable.

**ADD:**
- **A worked micro-example under PREC-1 using this chart's own data.** The abstract grain rule is the single hardest idea in the report, and this very chart is its perfect teaching case (career favourable / H10 afflicted — already narrated in Your Reading). One chart-specific illustration line under the rule ("in this chart: …") would convert the rule from doctrine to demonstration. Re-read of existing fields.
- **A PREC or PAR entry for the karmic-evolution / Jaimini-lifted layer** (`karmic`): PAR-3 covers karakamsa/soul but the 2026-08-04 Jaimini lift added a karmic layer whose relation to houses/timeline is presently unstated. If it is a parallel lens, say so in the structure rather than leaving it the one unlisted section.

**MODIFY:** the reading-order list says "step 2: The twelve matters" but the rendered document interleaves judgment graph and info content before the dashboard; either reorder the document (preferred, see chapter 3) or add the physical positions to the steps so the reader can actually follow them.

**UX:** the PREC table is long but scannable; the axes table is excellent. P3 (it already works).

---

## 5. Information content (`information_content`, detailed_report.py:659)

**What it does today:** one honesty sentence — total readings, modal-verdict count, near-universal count, inverted channels (named), distinctive count.

**Verdict: strong in principle, thin in rendering.** This is the Measured-Truth crown jewel — no other astrology product tells you 12 of your 56 readings are shared by half of humanity. But it is one dense sentence carrying five statistics, and it appears verbatim twice (here and as the digest headline) — repetition without added grain.

**ADD:**
- **The breakdown as a small table/strip under the sentence** (counts by class: modal / near-universal / inverted / distinctive), so the sentence's arithmetic is checkable at a glance. Append-only.
- **Name the distinctive 17, not just count them.** The section says "17 are genuinely distinctive" but shows 7 in What-stands-out (`distinctive_entries` caps at n=7). The other 10 exist and are computed; listing them (even in a `<details>` open-by-default per the completeness rule's own standard) honors "we show everything we compute". This is arguably a REPORT COMPLETENESS gap already.
- **One sentence of population framing from the mechanism finding** (median chart carries 19 afflicted and 31 favourable significations simultaneously — the canonical measured-truth record): it converts "near-universal" from a statistic into an understanding. Re-read of docs-recorded constants; corpus-verify against `REAL_OUTCOME_GENERALIZATION.md`.

**MODIFY:** nothing doctrinal.

**UX:** its placement before the guide is correct (honesty gate before belief). P2.

---

## 6. What stands out (`distinctive_entries`, detailed_report.py:678)

**What it does today:** top-7 calibrated readings furthest from the population midpoint, rare-first (claimed), as a house/matter/verdict/percentile/share table.

**Verdict: weak-to-adequate — one real defect and one real confusion.**

- **Defect: the sort contradicts the header.** The italic says "Rare readings first", but the sort key at detailed_report.py:683-684 only splits common vs non-common, then orders by |percentile − 0.5|. Result in this very chart: H4 education, the *only* "rare" row (3% share), is listed **last**, below six "notable" rows. Either the header claim or the sort must change; sorting by rarity band then distance would honor both.
- **Confusion: the H4 education row reads "verdict favourable (mild), percentile 32%"** — a favourable verdict below the favourability midpoint. Correct data, but no lay reader can parse a favourable-yet-32nd-percentile row without a gloss.

**ADD:**
- **A plain gloss column or per-row sentence**: "more favourable than 88% of charts" / "less favourable than 68% of charts despite the favourable verdict". Raman's comparative habit — he always situates a chart against the ordinary run of nativities ("in ordinary horoscopes…", passim in HTJAH worked charts — corpus-verify the idiom) — is precisely what this column would speak.
- **The inverted-channel rows if any distinctive entry sits on one** — the flag exists (`inverted_warning`) and the digest shows it; the table should carry the same warning inline.

**MODIFY:** fix the sort/header mismatch (above).

**UX:** good compact table; belongs exactly where it is. P1 (the sort defect), P2 (glosses).

---

## 7. Integrated insights (/home/user/astro/app/raman_saab/synthesis.py + doctrine/synthesis_rules.py)

**What it does today:** fired cross-feature combination rules in four provenance bands (Raman's own → classical-noncitable → Ashtakavarga → on-record-uncomputed), each with plain meaning, this-chart instantiation, verbatim text, and section links.

**Verdict: strong — the most Raman-faithful chapter in the whole layer.** The band discipline (Raman wins; AV's own caveat governs its band; "absence findings honoured — none were invented") is doctrine-first engineering of a high order. The "further doctrine on record (not yet computed)" band is honest scholarship.

**ADD:**
- **A this-chart consequence line joining the three period-grading verdicts that all fire on the same running period.** Right now Bhukti-tier (ordinary, HTJAH-I:1635), Laghu Parashari (mixed), BPHS seat-from-MD-lord (neutral), and AV-bhukti (distress-leaning) each appear as separate bullets; Raman's comparative-weighing habit would state the confluence once: "three independent gradings of the running Sun/Mercury sub-period agree it is middling; the AV tier alone leans lower and yields by PREC-4." That is a count of already-shown verdicts, not a new judgment — PREC-10-safe and enormously clarifying.
- **Karaka-tripod note when the Uttara Kalamrita tripod becomes computable** — the chapter itself records the hemming primitive now exists; when built, it belongs in the classical band with its firewall banner.

**MODIFY:** the band-2 provenance notice is good but the transition from band 1 to band 2 deserves one sentence of *why* the reader should care at all about noncitable corroboration (it strengthens or thins confidence; it never moves a verdict).

**UX:** long, but each bullet is self-contained; the plain-meaning-first format works. Sitting just before Full life synthesis is right. P2.

---

## 8. Full life synthesis (/home/user/astro/app/raman_saab/life_arc.py:129)

**What it does today:** eleven themed one-to-two-line paragraphs (Temperament … Dominant themes), each a re-read of a named chapter, closing with the re-read disclaimer.

**Verdict: weak — the chapter least earning its separate existence as rendered.** The concept (a biography-shaped closing pass) is exactly Raman's narrative form — his worked judgments close by walking temperament → profession → domestic life → health in prose. But the execution is a list of pointers, not a weave:

- **The "Destiny" paragraph pastes the entire Nichod essence verbatim** (life_arc.py:146). The reader meets the same 150-word block twice within a page. The essence stays fully displayed in Nichod (completeness intact); Destiny should carry its own distinct clause — e.g. the identity line + longevity band + the one governing factor — instead of the whole paste.
- Paragraphs like "Marriage: …the monograph carries Raman's own words for the placement" and "Children: …the chapter quotes the classical combination block whole" describe *the report*, not *the life*. A synthesis should re-read the content ("the seventh reads favourable, Moon in the 7th from a strong Jupiter lordship…"), not cite that content exists.

**ADD:**
- **Period-pairing per theme** (again the HTJAH-I ch.1 discipline): each theme paragraph should name the MD lords whose chapters most light its houses — data already in the graph's timers. "Wealth: leading channel gains-through-profession; ripens most under Venus, Sun and Moon chapters."
- **A dual-frame clause in Temperament**: the Moon-frame is the stronger here and the psychological paragraphs are Moon-driven — say so (HTJAH-I:645).
- **A "Present chapter" theme** between Turning points and Dominant themes: the running MD/AD, its tier, and its lit houses — the one thing a biography-shaped closing pass should never omit. Re-read of the Nichod's `current_period`.

**MODIFY:** rewrite the pointer-style paragraphs into content re-reads (all source data already computed and shown; the paragraphs merely select more of it).

**UX:** position (after all deep-reads, before glossary/Nichod) is correct. P1.

---

## 9. Nichod (`build_nichod`, detailed_report.py:2171)

**What it does today:** one distilled essence paragraph + a checkable "Ingredients" list (identity, strength, longevity, yogas, stands-out, tally, running period, transits, spotlight, caution, turning points).

**Verdict: adequate-to-strong.** The Ingredients-so-the-essence-can-be-checked device is excellent and very much in the spirit of Raman's summing-up ("the summing up of the influence of planets", HTJAH-I:8870). Two problems: the essence paragraph's second half is a chain of caution clauses that reads like a compliance appendix ("…never re-voted… atlas-proven inverted channels… read that house's section with extra care" — three cautions back-to-back with a stray ".;" join at the tenor-note boundary, visible in the output: *"not the majority.; this chart carries…"*), and the *spotlight* ingredient is computed but **never woven into the essence paragraph** — it appears only in the Ingredients list.

**ADD:**
- **The governing-factor opening clause already half-exists** (`ruler_bit`) — extend it with the stronger-frame consequence ("read from the Moon…") so the Nichod opens the way Raman opens: frame, ruler, strongest, then matters. (HTJAH-I:645-646, 16001-16002.)
- **A one-clause forward horizon**: the next MD boundary with its lean (the turning-points scan already computes exactly this; the essence mentions only the *past* flip, Mar 2022). Naming "the Moon chapter that follows from 2028 carries a hard lean" is period-grading, not event prediction — guard-safe; corpus-verify GBB-10:134 framing.
- **Weave the spotlight into the essence** (it is the single best cross-feature finding and currently silent in the paragraph).

**MODIFY:**
- Fix the ".;" punctuation join in the caution chain (cosmetic but on the capstone paragraph).
- Collapse the three cautions into one sentence with three named flags — same content, one breath.

**UX:** the section subtitle says "the final paragraph" but "Aptitude, intelligence & work style" renders *after* it in the markdown — either move aptitude above Nichod or drop the "final" claim; a capstone should be last. P2.

---

## Cross-chapter redundancy verdict (do they earn separate existence?)

Yes, with two exceptions. The layered design — plain prose (feel) → digest (ranked) → stands-out (full table) → guide (rules) → insights (doctrine connections) → synthesis (biography) → Nichod (capstone) — maps onto genuinely different reader questions, and the PREC-10 re-read discipline keeps them coherent. The two that currently don't earn their keep: **Full life synthesis** (pointer-paragraphs + verbatim Nichod paste) and the **verbatim duplication of the info sentence** as the digest headline (give the digest a one-line summary of its own items instead, keeping the info sentence in its own chapter). The stands-out top-3 appearing on five surfaces is acceptable *because* each surface frames it differently — but only once the stands-out table itself is sorted and glossed correctly.

---

## Top-5 highest-value moves

1. **P1 — Period-pairing across the whole layer** (Your Reading theme paragraphs, life-synthesis themes, digest items): Raman's always-pair-indication-with-period discipline (HTJAH-I ch.1, the locked timer doctrine). The data already sits in the judgment graph's timers; every synthesis surface should speak it. Biggest single fidelity gain available, zero new computation.
2. **P1 — Fix the What-stands-out sort/header contradiction** (detailed_report.py:683): "Rare readings first" is claimed but the only rare row lands last; add the plain favourability gloss so a favourable-verdict/32nd-percentile row is intelligible.
3. **P1 — Rebuild Full life synthesis paragraphs as content re-reads**: stop pasting the Nichod essence into Destiny, stop describing the report ("the monograph carries Raman's own words"), and add the missing Present-chapter theme. This is the chapter furthest from Raman's own closing-narrative form.
4. **P1 — Governing-factor + longevity-foundation items at the top of the digest** (ruler card re-read, HTJAH-I:16001; longevity-first order, HTJAH-II — corpus-verify): makes the digest open the way Raman opens and ground the way he grounds.
5. **P2 — Move the Judgment graph out of position 2** and enrich it with navamsa status + the aspects-the-lord/conjoins-the-lord timer-set edges (HTJAH-I:1586-1589; HPA-24:51-86): mechanics after verdicts for the reader, and the influence table finally matching the full locked five/six-factor doctrine it grades by.

All recommendations are add/reorder/reword only — no computed data hidden, Measured-Truth framing and the forecast guard untouched; every Raman concept cited above by book+chapter should be corpus-verified before encoding since the corpus was not available in this session.

# Appendix — full critique: foundation (verbatim agent report)

I generated the canonical report (Bangalore 1990-07-15 12:00 IST) via `build_detailed_report` → `to_markdown` (211,801 chars; saved at `/tmp/claude-0/-home-user-astro/f5b04b2d-8abf-53b0-bb89-84bcfac4280d/scratchpad/foundation_report.md`), read all nine foundation chapters as a client, and read the composing code: `/home/user/astro/app/raman_saab/detailed_report.py` (signature ~L2831, ruler L1625-1731 + L2855, positions L3013, rect L3032, shadbala L3055, deeptadi L3931), `/home/user/astro/app/raman_saab/planet_biographies.py`, `/home/user/astro/app/raman_saab/monographs.py` (psych/aptitude), `/home/user/astro/app/raman_saab/rect_confidence.py`, `/home/user/astro/app/raman_saab/primitives/deeptadi.py`, `/home/user/astro/app/raman_saab/primitives/shadbala/total.py`, `/home/user/astro/app/raman_saab/judges/chart_overview.py`, `/home/user/astro/app/raman_saab/report_html.py` (`_chart_grid` L1038, `_psych_section` L1657), `/home/user/astro/app/medini/templates/report.html` (`chartGrid` L1015).

Note on this machine: the doctrine corpus is absent, so every verbatim-quote field (HPA-18/21/22/24/34 pulls) came back empty. That itself exposed real behavior differences per chapter, noted below. All Raman citations below are by book+concept and flagged FOR CORPUS VERIFICATION where line-precision matters.

---

## 1. Chart signature

**What it does.** Identity card: Lagna/Navamsa Lagna/AK/Arudha, Moon nakshatra+devata+gana, stronger frame (lagna vs Moon), Jaimini trio, running MD/AD + Chara + Sade-Sati, panchanga string, functional natures for the Lagna. Composed inline at `to_markdown` L2831-2853 from `synthesis.py` + `judges/chart_overview.py`.

**VERDICT.** Astrological: **adequate** — a good coordinate card, but it is not yet what Raman reads at first glance. Reader: **strong** (compact, scannable).

**ADD** (each with Raman source concept):
- **Balance of dasha at birth** ("Balance of Mercury dasha at birth: X y-m-d"). Raman opens every worked nativity with this (HPA, casting-the-horoscope chapters; the Mainpuri chart's proforma). The signature shows only the *running* period; the birth balance is the classical first line and is already computable from the timeline. FOR CORPUS VERIFICATION.
- **Lagna degree and Moon degree** — the signature never states the ascendant longitude (~173.99° = Virgo 23°59′). Late/early-degree lagna is exactly why Rectification confidence later shows a +25-min Libra flip; the two chapters should visibly connect. (Raman: sandhi/degree awareness throughout HTJAH-I judgment of the lagna.)
- **Moon's condition at a glance**: waxing/waning (Krishna Ashtami is shown but never *read* — Raman weighs bright-half/dark-half Moon as benefic/malefic strength, HPA ch. on benefics/malefics; paksha bala in GBB). One clause: "Moon waning (Krishna paksha) yet Shadbala-strong (6.7 rupas)".
- **Sun's and Moon's strength flags** (strong/weak by the report's own Shadbala) — Raman's first glance always registers lagna, Sun, Moon strength (HTJAH-I, "Judgment of a Horoscope" opening considerations).
- **Lagna lord's disposition in one clause** ("Mercury in H11, enemy sign, Deena") — currently the signature names functional natures of all nine planets but not the disposition of the one planet Raman looks at first.
- **Day/night birth + weekday lord** (vara is shown; "born on Sunday, the Sun's day — the Sun is also this chart's strongest planet" is a Raman-style observation, HPA panchanga chapter).

**MODIFY.** The "Stronger frame — MOON" line cites HTJAH-I:645-646 but silently operationalizes it as *Shadbala of the two sign-lords* (`chart_overview._stronger_frame`). Raman's test is the relative strength of the lagna vs the Moon-sign themselves (occupancy/aspect counts too). Per the No-silent-approximation rule, name the variant in-render: "(measured here by the lords' Shadbala)". FOR CORPUS VERIFICATION.

**UX.** Jargon (Arudha, Upapada, Karakamsa) appears 1,900 lines before the glossary — inline one-word glosses. In the interactive page the chart grids render far below; the signature deserves the Rasi grid beside it (see §6).

**Priority: HIGH** (cheap adds, first thing every client reads).

## 2. Ruler of the nativity

**What it does.** `build_ruler` (L1625): Lagna lord named with house; strongest-by-Shadbala planet with rupas; nature-stamp comparison vs Navamsa-Lagna lord (HTJAH-I:3892-3897); temperament of the strongest (HTJAH-I:6248-6268); condition (functional nature, avastha, Ishta/Kashta, vargottama); yogas; own MD; transit outlook. Honest-absence branches throughout are excellent.

**VERDICT.** Astrological: **weak-to-adequate** — the chapter is titled "Ruler of the nativity" but describes the *strongest planet* in seven bullets and the actual ruler in one. Reader: **adequate** (card + knitted paragraph works, but the paragraph repeats the bullets verbatim).

**ADD:**
- **The ruler's own condition block** — Mercury's sign, dignity (enemy), avastha (Deena), Shadbala (6.15 rupas, *below* its required minimum — the only planet failing), aspects received, dispositor (Moon, in H7). Raman's doctrine: the Lagna lord's strength decides whether "the foundation is quite sound" (HTJAH-I:3880-3882 — the quote is already in the code but only fires on the *coincide* branch). Right now this chart's foundation-planet weakness is invisible in the very chapter about it.
- **The third classical candidate**: this chart's own signature says the MOON is the stronger frame, yet the ruler comparison never examines the Chandra-lagna lord (Jupiter, for Pisces Moon). Raman reads from the stronger frame (HTJAH-I:645-646); the ruler card should at least disclose the tension. FOR CORPUS VERIFICATION against HPA's ruler-of-nativity treatment.
- **"Foundation" verdict line** even when ruler ≠ strongest: strong-ruler / weak-ruler in Raman's sound/unsound idiom (descriptive, guard-safe).

**MODIFY.** "Its transit outlook — Sun is not one of the four slow movers..." is honest but reads as an apology; also give the ruler's (Mercury's) transit/gochara note where available.

**UX.** One-line takeaway missing; lead with e.g. "Mercury rules this nativity from the 11th, but runs dejected and under-strength; the Sun, strongest planet, carries the chart." Priority: **HIGH**.

## 3. Planet biographies

**What it does.** `planet_biographies.py`: judgment-graph census ranks all 9 grahas; per graha: roles, dignity+avastha, helps/obstructs houses, karaka duties, disease indications (HTJAH-I:6439), vocation words (HTJAH-II:10249-10274), bannered modern keywords, plus verbatim HPA-21/22/24/34 fields.

**VERDICT.** Astrological: **adequate** — genuinely novel structure (census + helps/obstructs receipts), but thin against Raman's own planet readings. Reader: **weak-to-adequate** — every biography opens with "25 graph appearances (aspects 3, karaka_of 18...)": engineering-speak where the client expects a portrait.

**ADD:**
- **Functional nature per lagna inside each bio** (Raman/HTJAH functional benefic-malefic doctrine). Jupiter's bio here reads warmly while the signature calls Jupiter a functional *malefic* for Virgo — the bio must carry that line or the two chapters contradict in tone.
- **Aspect give-and-receive, itemized.** The census counts `aspects` edges but never names them. Raman never reads a planet without "aspected by / aspecting" (HTJAH-I house-judgment factors). Two bullets: "Casts drishti on: H4 (Saturn 10th aspect)...", "Receives: aspect of Mars...".
- **Shadbala rupas + powerful? in the bio header line** — delivery capacity is the bio's missing spine (GBB-8 required minimums).
- **Avastha consequence, not just the label**: "Vikala — indications arrive weakened or obscured (HPA Ch.7)" — the phrase already exists in `deeptadi.RESULTS`; wire it in.
- **Combustion facts for Jupiter** (separation in degrees; Raman treats combustion as a first-rank affliction, HPA ch. on planetary states).
- **Named karakatvas**: "karaka for house 2 (wealth), 4 (mother/home)..." — numbers alone force a lookup.
- **Honest-absence note when HPA-21/22 verbatims are unavailable** (see MODIFY).

**MODIFY:**
- **Corpus-absent silence**: on this machine the HPA-22 sign / HPA-21 house paragraphs simply vanish for the seven visible planets (bullets are conditional, `to_markdown` L2956-2964) while Rahu/Ketu get an explicit honest-absence line. Same standard for all: "In its sign (HPA-22) — corpus not present on this machine".
- **Nodes' prose template bug**: Rahu/Ketu prose says "Because its **lordship** and aspects reach house 5..." — nodes rule nothing (locked doctrine). Wording branch needed in `_compose_prose`.
- **Conclusion line is always vocational.** Raman's summary judgment of a planet is house-topic-centric; the vocation words belong to the career analysis. Give each planet a role-based one-liner (lagna-lord under strain / yoga-giver / maraka-bearer), keeping the trade line as a bullet.

**UX.** Demote the census to a trailing receipt ("receipts: 25 graph edges — ..."); open with the one-line takeaway. Priority: **HIGH**.

## 4. Psychological profile

**What it does.** `monographs.build_psych_profile`: HPA-18 lagna portrait verbatim + Moon (manas) state + strongest-planet temperament + nature stamp + AK, woven line. Rendered at `to_markdown` L2991 and `report_html._psych_section`.

**VERDICT.** Astrological: **cannot be judged as shipped — the chapter silently does not exist on a corpus-less machine.** `build_psych_profile` returns `None` when the HPA-18 pull is empty (L243-245), and every renderer skips `None`. Reader: **weak** by absence.

**MODIFY (the critical one).** Degrade gracefully: when the lagna quote is unavailable, still emit the computed rows (Moon state, temperament, stamp, AK) with an honest-absence line for the portrait. Silent chapter-drop is against the spirit of REPORT COMPLETENESS even though it is an "honest absence" — the *computed* parts are being hidden by a missing *quote*.

**ADD:**
- **Moon-in-sign mental disposition** (HTJAH-I:1452 per-sign Moon results — already fired for the Aptitude chapter; the psych chapter is its natural home).
- **Mercury (buddhi) condition** — Raman's mind is Moon (manas) *and* Mercury (buddhi); the profile has no Mercury line.
- **Affliction-to-the-mind screen**: Moon/Mercury under malefic aspect, 5th-house affliction — Raman's mental-affliction combinations (HTJAH-I 5th-house / Moon judgment; descriptive idiom keeps it guard-safe). FOR CORPUS VERIFICATION.
- Cross-reference to Deeptadi ("Moon Muditha — inclines to happiness in its topics").

**Priority: CRITICAL** (chapter currently vanishes).

## 5. Planetary positions

**What it does.** Table: sign, house, nakshatra(pada), navamsa sign, notes (retro/vargottama/combust). `to_markdown` L3013-3030.

**VERDICT.** Astrological: **weak** — the subtitle promises "Exact degrees" and the table contains **no degrees at all**. Not checkable against Jagannatha Hora/drikpanchang, which the project's own test-pinning policy demands. Reader: **adequate** (clean).

**ADD:** longitude column (sign + D°M′S″); an **Ascendant row** (and ideally Arudha/Upapada as points); **nakshatra lord** column (makes Vimshottari auditable — Revati→Mercury explains the birth MD); dispositor column; combustion separation for Jupiter; speed/stationary flag (Raman's cheshta context, GBB). All add-only columns.

**UX.** Move this table (with grids) toward the top of the document order — a reading must be checkable *before* it is believed. Priority: **HIGH** (degrees), rest MEDIUM.

## 6. Chart grids (Rasi/Navamsa/Gochara)

**What they do.** Interactive page: one South-Indian builder (`report.html` `chartGrid` L1015) for rasi/navamsa/**gochara**/verdict-wheel, with verdict tinting and Moon marker. Standalone HTML (`report_html._chart_grid` L1038): rasi + navamsa only. Markdown: **no grids at all**.

**VERDICT.** Astrological: **adequate** (correct fixed-sign South-Indian form, Asc marked). Reader: **adequate**, with parity gaps.

**ADD:** Gochara grid in the standalone HTML (parity with the interactive page, add-only); planet degree + retrograde "(R)" marks inside cells (a bare "Sa" in Sagittarius hides retrogression the positions table knows); an ASCII/mermaid-free text grid in markdown (Raman's readers always see the chart before the reading — every HTJAH worked example prints the chart first). Chara-karaka tag (AK etc.) in cells would serve the Jaimini chapters.

**UX.** In `_HTML_ORDER` (detailed_report.py L608-612) `chart_grids` sits far below signature/ruler/bios; the client should *see* the chart in the first screenful. Priority: **MEDIUM**.

## 7. Shadbala

**What it does.** Six components + total (rupas), `is_powerful` vs `MIN_REQUIRED`, Ishta/Kashta raw, plain band (`plain_terms.band_rupas`). L3055-3084.

**VERDICT.** Astrological: **adequate, with one fidelity flag**. Reader: **strong** (best table in the foundation layer; horsepower metaphor lands).

**Fidelity flag (report it, do not silently "fix"):** `MIN_REQUIRED["Sun"] = 5.0` in `primitives/shadbala/total.py` L75-83, while GBB-8's printed minimum for the Sun is 6.5 rupas (390 shashtiamsas; Moon 6.0, Mars 5.0, Mercury 7.0, Jupiter 6.5, Venus 5.5, Saturn 5.0 — the other six match). The dict is a documented golden-tuned knob, but the *render text* claims "RAMAN'S OWN required minimum (GBB-8:303)". Either restore 6.5 with a golden that earns it, or amend the claim to "Raman's minima, one golden-tuned deviation (Sun) disclosed". At 6.5 the Sun here (9.69) is still comfortably "powerful", so on this chart nothing flips — but the label is currently inaccurate. FOR CORPUS VERIFICATION (GBB-8:303).

**ADD** (GBB's own interpretive use):
- **Ratio column** (total/required) — Raman ranks planets by relative strength, not raw rupas (GBB ch. on application of balas).
- **Component-level diagnosis** — Raman diagnoses *which* bala fails (GBB-8 gives per-component requirements). Mercury fails its total here; the table never says the deficit is mostly kala/cheshta. One "weakest component" cell or a footnote per failing planet. FOR CORPUS VERIFICATION of the component minima table.
- **Definitional note for cheshta = 0.00 on Sun/Moon** (no retrogression; how the engine treats their cheshta/ayana) — currently looks like a data hole.
- **Ishta/Kashta scale note** ("out of 60") + one-word lean, matching the lean words used elsewhere.
- Cross-link: "Bhava Bala lives in the House-strength cross-check" pointer.

**Priority: HIGH** (the Sun-minimum label), rest MEDIUM.

## 8. Deeptadi avasthas

**What it does.** One line of states + a gloss list of the states present (TERM_GLOSS). `primitives/deeptadi.py` computes nine of Raman's ten states (Bhita omitted, disclosed in code).

**VERDICT.** Astrological: **weak — this is the dangling-trivia case the brief asked about.** Reader: **weak** (a comma-list plus dictionary entries).

**ADD:**
- **Raman's own result-phrases per planet** — `RESULTS` (HPA Ch.7:46-83) already holds them ("Vikala → disease, loss of..., disgrace") and `chart_states()` already returns them; the section renders only the label + a modern gloss. Per-planet table: planet | state | Raman's stated result | houses it rules/occupies. That last column is the integration step: "Mercury Deena — the *lagna lord* dejected" is a judgment-relevant sentence; "Mercury Deena" alone is trivia.
- **Secondary states disclosed.** `state()` is priority-ordered and returns one state: Saturn here is retrograde (Sakta) *and* in an enemy sign (Deena); only Deena shows, while the positions table shows retrograde — a reader sees an apparent contradiction. One parenthetical: "Deena (also retrograde → Sakta; the dignity state is read as dominant)". Priority rule itself: FOR CORPUS VERIFICATION (HPA Ch.7 gives no explicit precedence).
- **Baladi + Jagradadi avasthas — computed and used, never shown.** `judges/house_template.py` L540-575 scores Baladi/Jagradadi per planet and *demotes verdict degrees* with them; no renderer surfaces them. Under REPORT COMPLETENESS this is exactly the "computed value must appear" case — the canonical baseline even pins "Saturn Avastha = Mrita/Swapna". Add them to this chapter (with the source naming: BPHS-family avastha schemes, CLASSICAL_NONCITABLE banner if outside Raman's citable canon).
- **Definitional note for nodes**: Rahu/Ketu are always retrograde, hence perpetually "Sakta (empowered)" — say so, or the label over-promises.

**Priority: HIGH.**

## 9. Rectification confidence

**What it does.** `rect_confidence.py`: minute-by-minute recast ±60 min, 10 pillars, stable ranges, flip targets, overall window, firm/soft label. Conceptually excellent and honestly framed.

**VERDICT.** Astrological: **strong** (a genuinely Raman-spirited honesty instrument; correctly separated from event-rectification). Reader: **adequate**, marred by a mojibake bug.

**MODIFY (bug):** the rendered markdown shows "the full **?60**-minute scan" and "stable beyond **?60** min" — the `±` at `to_markdown` L3042/L3051 is blanked to `?` by the ASCII fold (`_fold_ascii` → `render._ascii`), while `_FRAME` deliberately writes "+-60". Use "+-" at both call sites (or teach `_ascii` to fold `±`).

**ADD:**
- **Name the binding pillar**: the overall −2/+10 window is bound by the Navamsa Lagna pillar; the reader must deduce this from the table. One line: "binding pillar: Navamsa Lagna (flips at −3/+11)".
- **Consequence-of-flip note** for the big one: "+25 min → Libra lagna: every house verdict re-derives" — connects to the late-degree Virgo lagna (see §1).
- **Disclose the 'firm' threshold** (±10 min, `_FIRM_THRESHOLD`) in the render — the label currently arrives unexplained.
- Navamsa-Lagna sensitivity cross-reference into the Ruler chapter (the nature-stamp comparison rests on a pillar stable only −2/+10).

**Priority: MEDIUM** (the `?60` fix itself is trivial and should ride along with anything).

---

## Top-5 moves for the foundation group

1. **Un-silence the Psychological profile** — degrade `build_psych_profile` to render computed rows with an honest-absence line when the HPA-18 quote is unavailable, and add Moon-in-sign (HTJAH-I:1452) + Mercury-buddhi rows. A whole chapter currently vanishes on corpus-less machines.
2. **Give the Ruler chapter its ruler** — full condition block for the Lagna lord (dignity, avastha, Shadbala vs minimum, aspects, dispositor) plus the sound/unsound-foundation verdict line (HTJAH-I:3880-3882), and disclose the Chandra-lagna-lord candidate when the Moon is the stronger frame.
3. **Make the report checkable: degrees everywhere** — longitude + Ascendant row + nakshatra-lord column in Planetary positions; degree/(R) marks in the grids; Gochara grid parity in standalone HTML; markdown grid. The positions subtitle already promises "exact degrees".
4. **Resolve the Shadbala Sun-minimum label** (5.0 tuned vs GBB-8's 6.5 printed) and add ratio + weakest-component diagnosis — GBB's own interpretive use is component-level, and the current "RAMAN'S OWN minimum" claim is not accurate for the Sun as tuned. Needs a user decision (golden retune vs relabel), per Measured-Truth rules.
5. **Promote Deeptadi from trivia to testimony** — per-planet table with Raman's HPA Ch.7 result-phrases (already in `RESULTS`), secondary-state disclosure, node-Sakta definitional note, and surface the Baladi/Jagradadi states that `house_template` already uses to demote verdict degrees (a live REPORT COMPLETENESS gap).

All recommendations are add-only or disclosure-level modifications; none touches verdict logic, the golden ratchet, or Measured-Truth framing; nothing introduces dated predictions (descriptive idiom throughout). Items marked FOR CORPUS VERIFICATION need line-precise checks against HPA Ch.7/18, HTJAH-I:645/1452/3880/6248, and GBB-8:303 once a corpus machine is available.

# Appendix — full critique: yoga_strength (verbatim agent report)

All evidence gathered — report generated from the canonical BirthData, all six chapter composers read (yogas.py 72 records, yoga_deep_read.py, synthesis_rules._yoga_planets/yoga_house_bearings, detailed_report composers/renderers, primitives/ashtakavarga*, kakshya*, shadbala/bhava_bala). Findings below.

# YOGAS & STRENGTH — chapter-by-chapter critique

Canonical chart facts used throughout: 7 yogas fire (Vesi, Pasa, Gajakesari, Sunapha, Amala, 2 Raja); SAV total 337, H8=38/H12=21; Sun MD–Mercury AD running at ref date.

---

## 1. Yogas present in this chart

**What it does** (`detailed_report.py` ~3087-3098; `doctrine/yogas.py`): flat bullet list of fired yogas — name, kind tag, paraphrased effect, citation — under one generic epigraph ("A yoga's effect depends on the strength of the planets causing it, HTJAH-I:611").

**VERDICT — Raman lens: B-.** The encodings themselves are exemplary fidelity work (Vipareeta exactly Raman's form with no Phaladeepika isolation clauses; Kemadruma folds its 3HC:2182-2185 bhanga in; the Chamara over-firing arm consciously omitted and documented; deferred yogas deferred for *measured* reasons). But the *presentation* violates 3HC's own per-combination protocol (definition → results → remarks-with-strength-and-cancellation): this section gives results only; definition and remarks are deferred to the deep-read, and the strength qualification is one epigraph, not per-yoga. **The absence of the ~228 un-encoded 3HC combinations is disclosed nowhere** — the deep-read count says "72 of Raman's ~300" in no surface; a reader cannot distinguish "chart lacks Lakshmi Yoga" from "engine never checks Lakshmi Yoga." The timing section discloses its own coverage gap in exemplary style; this section discloses nothing. **Reader lens: C+** — seven bullets with no ordering, no sense of which matters, "other" as a kind tag is meaningless to a lay reader.

**ADD (Raman-licensed):**
- A coverage-honesty paragraph, mirroring the timing section's existing gap prose: "72 combinations encoded (families: Mahapurusha 5, lunar 7, solar 3, Nabhasa 32, raja 7, dhana 6, arishta 2, HPA-20 named 8, other 2); the remaining ~228 of *Three Hundred Important Combinations* are not yet encoded — a yoga absent from this list is *unchecked*, not absent." Pure disclosure; no doctrine invented.
- **Cancelled-Kemadruma line.** Because Kemadruma's record fires only while uncancelled, a chart with Kemadruma-geometry-plus-bhanga shows *nothing* — yet 3HC's remarks on Kemadruma bhanga treat the cancelled state as itself significant (flag exact line for verification against 3HC:2182ff once corpus present). The bhanga primitives already compute both halves; surface "Kemadruma geometry present but cancelled by (branch)" as an additive line.
- Notable *absences* Raman himself checks in worked charts (no arishta fired, no Mahapurusha fired) — one sentence, computed trivially from the same detect pass.

**MODIFY:** none of the records; the kind tag could render as "solar-flank / Nabhasa-Sankhya / …" (family names, all Raman's own taxonomy) instead of "other".

**UX:** order the bullets by the deep-read's comparison rank (once fixed — see ch.3) so list order = importance; link each bullet to its deep-read anchor. **Priority: HIGH (the coverage disclosure), MEDIUM (rest).**

---

## 2. Yoga × Dasha timing

**What it does** (`_yoga_dasha_confluences`, ~1061-1088): for each fired yoga whose constituents `_yoga_planets` resolves, one row per constituent-lord MD run and AD window across the 30-year timeline, with `lord_quality` (well/mixed/poorly) as "Delivery". Doctrine anchor HTJAH-I:4324 + magnitude scaling HTJAH-I:5372.

**VERDICT — Raman lens: A-.** This is genuinely Raman's rule made concrete, the semantic lord-resolution (`_yoga_planets_impl`) is careful and per-branch discriminating (e.g. Y.DHANA.CHAIN resolves only the disjunct that actually fired), and the whole-chart-pattern gap disclosure is model honesty prose. Two doctrinal soft spots: (a) **the vargottama-combust tension is silently collapsed** — Jupiter AD rows read "poorly" (combust drives the tag) while the same engine's deep-read shows `vargottama=True`, and HTJAH-I:5372 is quoted in this very section's intro saying vargottama doubles magnitude; a lay reader sees the section promise vargottama-doubling and then a vargottama lord tagged "poorly" with no reconciliation. (b) AD rows omit their MD context — "Mercury AD Mar 2018–Jan 2021" doesn't say *under Venus MD*, yet Raman's whole bhukti doctrine (the locked four-tier scheme) is MD-lord-relative. **Reader lens: C.** 39 rows for 7 yogas; the three Venus-MD rows are triplicated verbatim across three yogas; nothing marks the *running* window (Vesi's Mercury AD Jan–Nov 2026 is live at the ref date — only the ranked digest says so, 250 lines earlier).

**ADD:** MD-context column on AD rows (`p.maha` is already in the timeline period — computed, unshown); a "NOW" marker on the row containing the reference date; a one-line-per-yoga "next ripening" summary above the full table (the full table stays, per REPORT COMPLETENESS). **MODIFY:** delivery cell for combust-but-vargottama lords should carry both facts — "poorly (combust) — but vargottama, HTJAH-I:5372" — the LordQuality struct already holds both booleans; this is rendering, not re-judging. **UX:** group rows by yoga (or add rowspan-style repetition suppression in HTML surface); the interactive page's timeline yoga-tick overlay is excellent — mirror a hint of it in markdown ("see timeline chart"). **Priority: MEDIUM-HIGH.**

---

## 3. Yoga deep-read — the best-designed chapter, and the buggiest

**What it does** (`yoga_deep_read.py`): per fired yoga — verbatim definition via `sources.passage`, condition tree rendered, participant facts (house/sign/dignity/rupas), Shadbala-mean strength, cancellation note, aspect modifiers, operating periods, Notable Horoscopes mentions, comparison rank. Structurally this **is** 3HC's definition → results → remarks protocol — the right skeleton.

**VERDICT — Raman lens: D+ execution on an A- design.** Four concrete defects, all verified in the canonical output:

1. **Participant resolution is syntactic and wrong.** `participants()` scans condition-tree string attrs for graha names. Consequences in this chart: **Sunapha lists all five flank *candidates*** (Mars, Mercury, Jupiter, Venus, Saturn) as participants and averages their Shadbala to "7.00 rupas" — but 3HC's Sunapha is caused by *the planet actually in the 2nd from the Moon* (Mars here, 6.73). Four of the five rows in "Why it qualifies" describe planets that do not form the yoga. **Gajakesari omits the Moon** (origin token `"MOON"` ≠ `"Moon"`), so its "strength" is Jupiter alone — while 3HC's own remark protocol grades Gajakesari by *both* Jupiter and the Moon (and the report's own SYN_R1 insight, 3HC:1359, weighs exactly that pair correctly elsewhere in the same document). **Vesi, Pasa, Amala and both Raja yogas resolve zero participants**, producing the false line "Shadbala mean unavailable (no Shadbala on this chart)" — directly above a full Shadbala table for this chart. The correct semantic resolver **already exists** (`synthesis_rules._yoga_planets` — it pins Vesi→Mercury, Amala→Jupiter+Venus, kendra-trikona→the actual conjoined pair, and the timing section uses it); the deep-read simply doesn't call it.
2. **The comparison ranking is therefore an artifact**: unresolvable yogas get sentinel -1.0 and sink to the bottom regardless of actual participant strength; two Raja yogas whose participants (Venus 7.42, Jupiter 8.72, Mercury 6.15) are computable rank below Pasa.
3. **Corpus-absent failure mode**: `passage()` returns None → `- **Definition (verbatim)** — "" (3HC:1589)` — an empty string presented as a verbatim quotation, for every yoga. Needs an explicit fallback ("source corpus not mounted; definition at 3HC:1589 — paraphrase: …effect string…").
4. **Cancellation overclaim + raw repr leak.** "no cancellation Raman states applies to this chart's instance" is asserted, but only neecha-bhanga (and Kemadruma's folded bhanga) are *checked*; Gajakesari's dusthana nullification (HTJAH-I:2948-2956) and Raja-Yoga Bhanga (HTJAH-I:15903, 16139) are known to the codebase (cited in the preponderance disclosure and in `yoga_house_bearings`' docstring) yet not evaluated here. Honest wording: "none of the *encoded* Raman-stated cancellations applies; not graded: dusthana-formation nullification (HTJAH-I:2948-2956), Raja-Yoga Bhanga (HTJAH-I:15903)." And the Operating-periods lines print `LordQuality(lord='Moon', strong=True, dignity='friend', combust=False, vargottama=False, tag='well')` — a Python dataclass repr in reader-facing prose, in every yoga block (markdown AND the JSON the interactive cards render).

**Reader lens: D.** Computation lines leak private class names (`_SunFlank(n=2)`, `_KendraTrikonaLordsConjoined()`) with no gloss; a lay reader cannot learn from `ClassInHouseFrom(klass=benefic, origin=MOON, houses={10})` *which* benefic made their Amala. The NH cross-references are a genuinely lovely touch (add-only historical texture).

**ADD:** per-yoga SYN_R1 line ("of the pair, X at N rupas delivers the larger part, in its own periods — 3HC:1359") — the rule engine already computes it; per-participant kendra/trikona/dusthana placement tag (3HC remarks' standard strength qualifiers; placement is already in ParticipantFacts.house — just label it); functional nature (benefic/malefic *for this Lagna*) per participant — computed in `functional_nature.py`, unshown here. **MODIFY:** points 1-4 above. **Priority: HIGHEST in the whole group — this section presents wrong facts under a "measured" banner.**

---

## 4. Ashtakavarga (Sarvashtakavarga bindus by sign)

**What it does** (renderer ~3166-3175): a single 12-column row of SAV bindus + the average/total line + Raman's reliability caveat (HTJAH-II:4453-4456).

**VERDICT — Raman lens: C+ for the section, A- for the codebase.** The caveat-first framing and the PREC-4 precedence rule (AV never outranks a Raman-band reading) are exactly right. But Raman's AV toolkit inventory, computed-vs-shown:

| Raman AV instrument | Computed? | Shown in report? |
|---|---|---|
| SAV by sign | yes | yes (bare grid) |
| SAV per bhava banding | yes | yes (cross-check + house prose) |
| **BAV per planet (7×12 + totals)** | yes (`primitives/ashtakavarga.py`) | **only as single derived cells** (gochara AV-bindus column, AV dasha-seat, kakshya donation); the matrix itself is invisible in the natal report (only the Muhurtha electional widget touches it) |
| Kakshya transit grading | yes | yes (gochara Kakshya column; Dasha Kakshya intervals, ASP-12) — genuinely good |
| **Trikona + Ekadhipathya reductions (HPA-26, Raman's own subtract-reading with his footnote honored)** | yes, regression-pinned to HPA-26's worked Sun table | **consumed by NO surface** — grep confirms zero importers outside its own tests |
| **Sodya Pinda (Rasi+Graha Gunakara, ASP-14 naming)** | yes, with the honest recorded delta vs Raman's misprinted 1962 tables | **consumed by NO surface** |
| HPA-26 pinda→longevity application | not wired (Longevity uses Graha-pindayu/amsayu, a different method) | missing |
| ASP transit-multiplier via pinda | deliberately deferred until ASP fully in corpus (docstring) | correctly absent |

So the answer to the brief's question: **the reductions and the pinda are the flagship computed-but-unshown items** — doctrine-verified, test-pinned, invisible. Under REPORT COMPLETENESS ("if the engine computed a value, it appears") the BAV matrix, reduced tables and per-planet Sodya Pinda are not merely licensed additions, they are arguably *owed*.

**ADD:** (1) BAV 7×12 matrix with per-planet totals and the natal seat of each planet marked — this also makes the gochara "AV bindus" and Kakshya columns legible (a reader can finally see *where* Jupiter's 7-bindu Cancer sits in Jupiter's own row); (2) reduced-BAV tables + Sodya Pinda per planet, labeled "HPA-26 reductions — used classically for special calculations; shown for completeness, ASP transit application deferred pending corpus"; (3) mark the Moon-sign and Lagna columns on the SAV grid (transits are graded from the Moon; the reader currently maps signs→houses mentally). **MODIFY:** the 30/25 band thresholds carry no citation in report prose (`ashtakavarga_predictive.py` calls them "empirical thresholds widely used" per BPHS/Manual) — flag for verification against Raman's *Manual*/ASP once corpus is mounted, and say in-report whose thresholds they are. Also worth a doctrine review: uniform "more bindus = favourable-leaning" is applied even to dusthanas (H8's 38 counts as a favourable longevity witness — defensible via 8th=ayushthana, but H12's band-lean should be checked against ASP's per-house bindu readings; flag, don't change). **UX:** in markdown the grid is a bare number row; the interactive page's above/below-average column chart is the right idea — add a plain-text deviation row (`+10 / -4 …`) to markdown too. **Priority: HIGH (BAV/reductions/pinda surfacing), LOW (cosmetics).**

---

## 5. House strength cross-check

**What it does** (~1095-1135, renderer ~3270-3307): 12-row table — verdict (unchanged) × Bhava-Bala rank (GBB-9, rank-only per Raman's no-cutoff) × SAV band; magnitude-vs-direction explainer with the Bhava-Drig-Bala caveat.

**VERDICT — Raman lens: A-.** This is the group's best doctrine writing: GBB-9:332 rank-not-cutoff honored, the strong-yet-afflicted reading ("delivers its difficulty with unusual force") is a defensible synthesis of GBB-9:32-34, stated as tendency; the band-threshold alignment note shows real care. One completeness defect: **`HouseStrengthRow.bhava_bala` (the measured rupas value) is rendered in JSON and the interactive page but dropped from the markdown table** — only the rank appears. Under the locked REPORT COMPLETENESS directive ("no dropping columns... every field of every section... in ALL renderers") this is a live violation, and it is exactly the measured-rupas kind of number the Measured-Truth constraint welcomes. **Reader lens: B+** — clean; this chart's two teaching anomalies (H12 afflicted on the chart's *highest* Bhava Bala; H6 afflicted on its lowest) are well-handled in the house conclusions.

**ADD:** the Bhava-Bala rupas column to the markdown table (value exists in the dataclass); optionally the three GBB components (Bhavadhipati/Bhavadig/Bhava-Drig) as a drill-down since Bhava-Drig is the one signed component the explainer discusses — computed in `shadbala/bhava_bala.py`, unshown. **MODIFY:** nothing doctrinal. **Priority: MEDIUM (the dropped column is a directive violation — cheap fix).**

---

## 6. Preponderance of testimonies

**What it does** (`build_preponderance`, ~1830-1990): per house, a ledger of already-computed witnesses (lord, karaka, navamsa, Bhava-Bala rank [neutral], SAV band, matter-vargas, majority tenor, bearing yogas) with leans; equal-weight majority → benefic/adverse/evenly-balanced; status vs the untouched headline; per-house bullet ledgers; most-corroborated/most-contested close.

**VERDICT — Raman lens: A- for honesty, B for method.** Is it "weigh the testimonies" or raw counts? **Both, and it says so** — the three honesty rules paragraph is the most self-aware disclosure in the report (equal-weight majority named as "a presentation convention borrowing his vocabulary, not his weighing"; non-independence of witnesses admitted; the strong-dusthana-lord and broken-karaka special cases encode real Raman semantics; the navamsa direction-absolute correction records its own doctrine-review history). Remaining doctrinal weaknesses: (1) **yoga-witness saturation** — the own/occupy/aspect bearing map spreads each two-planet yoga over 5-8 houses (disclosed as coarser than Raman's demonstrated Truman set), so Gajakesari testifies on seven houses and a Raja yoga counts as a *favourable* witness on H6 disease — noise wearing a citation; the counts these rows inflate then drive the "well-corroborated" status (H4's headline "10 witnesses" includes 4 yoga rows). (2) Raman's own summation weighs unequally (HTJAH-I:8870-8876, quoted) — the table's For/Against columns are still flat counts, and the status word derives from them. **Reader lens: B+** — the table + bullets + the two closing callouts are genuinely readable; "contested" rows correctly alarm without re-judging.

**ADD (both licensed by already-cited text):** (a) a *witness-class* tag per row — "core testimony" (house/lord/occupants/karaka — HTJAH-I:983-991's own list, plus navamsa) vs "overlay" (SAV, tenor, yoga-bearings) — and a second count pair "core: N for / N against" beside the flat one; this is Raman's unequal weighing made visible without inventing weights. (b) Split yoga bearings into "direct (own/occupy — Raman-demonstrated)" vs "aspect-derived (admitted extension)" — the bearing function already knows which factor matched; showing it converts the saturation problem into disclosed structure. **MODIFY:** consider making raja/dhana yoga-lean house-conditional (favourable on 1/2/4/5/7/9/10/11, neutral on dusthanas) — but that is a doctrine decision; flag for a bphs-doctrine-reviewer pass rather than change. **Priority: MEDIUM.**

---

# Top-5 moves for the YOGAS & STRENGTH group

1. **Fix the deep-read's participant pipeline** (`yoga_deep_read.py`): call `synthesis_rules._yoga_planets` instead of the syntactic `participants()` scan. One change repairs five defects at once — Sunapha's false 5-candidate strength mean, Gajakesari's missing Moon (3HC grades the pair), Vesi/Amala/Raja's "no Shadbala on this chart" falsehood, the -1-sentinel comparison ranking, and the empty "Why it qualifies" blocks. This is the group's only *wrong-facts* issue and it sits under a "Strength (measured)" banner.
2. **Kill the two presentation-integrity leaks in the deep-read**: empty `""` verbatim quotes when the corpus is unmounted (explicit fallback naming the citation), and the raw `LordQuality(...)` dataclass repr in Operating-periods (format as `well — friend, strong` / `poorly — combust, though vargottama (HTJAH-I:5372)`); narrow the cancellation claim to "none of the *encoded* cancellations", naming the ungraded ones with their existing citations.
3. **Surface the orphaned Ashtakavarga layer**: BAV 7×12 matrix + totals (makes gochara/kakshya/AV-seat columns legible), the HPA-26 reduced tables, and per-planet Sodya Pinda — all computed, regression-pinned to Raman's own worked examples, and currently invisible to every reader. Pure ADD; also restores the dropped `bhava_bala` rupas column to the markdown cross-check (a live REPORT COMPLETENESS violation).
4. **Coverage honesty in "Yogas present"**: 72-of-~300 disclosure with family breakdown, cancelled-Kemadruma surfacing, and notable-absence lines — matching the honesty standard the timing and preponderance sections already set.
5. **Yoga × Dasha timing readability**: MD-context on AD rows, a NOW marker, per-yoga next-ripening summary above the (retained) full table, and the vargottama-combust reconciliation in the Delivery cell.

Key files: `/home/user/astro/app/raman_saab/yoga_deep_read.py` (defects 1-2), `/home/user/astro/app/raman_saab/doctrine/synthesis_rules.py` (`_yoga_planets`, `yoga_house_bearings`), `/home/user/astro/app/raman_saab/doctrine/yogas.py`, `/home/user/astro/app/raman_saab/detailed_report.py` (renderers ~3087-3310, composers ~1030-1135, ~1830-1990), `/home/user/astro/app/raman_saab/primitives/ashtakavarga_reduction.py` + `ashtakavarga_pinda.py` (computed-but-unshown), `/home/user/astro/app/raman_saab/doctrine/sources.py` (`passage` None path). All 3HC/HPA/ASP line-number citations above are repeated from the codebase's own records; the corpus is absent in this environment, so they are flagged for verification once mounted, per the brief.

# Appendix — full critique: house_judgment (verbatim agent report)

I have everything I need. Here is the full critique of THE HOUSE JUDGMENTS chapters.

---

# THE HOUSE JUDGMENTS — critique

Report generated from `BirthData('C',1990,7,15,12,0,5.5,12.97,77.59)` via `build_detailed_report` → `to_markdown` (211,801 chars; house chapter = lines 526–740; dashboard = lines 155–176 of the generated markdown). Composing code read: `/home/user/astro/app/raman_saab/judges/house_template.py`, `/home/user/astro/app/raman_saab/doctrine/significations.py`, `/home/user/astro/app/raman_saab/detailed_report.py` (house renderer ~3178–3270, dashboard ~2807–2830, helpers 600–830), `/home/user/astro/app/raman_saab/judges/matter_varga_dashboard.py`, `/home/user/astro/app/raman_saab/synthesis.py`, `/home/user/astro/app/raman_saab/report_html.py` (`_house_section`), `/home/user/astro/app/raman_saab/render.py` (`_ascii`).

## Per-house observations (where houses differ from the general pattern)

- **H1 Self/Body** — the weakest chapter opener. Its three significations (`self`/`body`/`health`) all share the single `"self"` rule bucket (`significations.py` _H1), so the reader's very first house shows **three verbatim-identical calibration lines** ("favourable (moderate) — more favourable than 56%… [NEAR-UNIVERSAL]" ×3). Raman's own Lagna chapter judges appearance, character, and constitution as distinct karyas; the engine's H1 is the thinnest of the twelve, and the redundancy teaches the reader early that the per-signification lines may be copy-paste — which poisons trust in the houses where they genuinely differ (H4, H10, H12).
- **H3 Siblings/Courage** — carries a **visible self-contradiction**: the pillar line prints "**Navamsa** neutral" while the reading line one paragraph below says "and the navamsa confirms it (delivered)." Mechanism (verified live): the lead frame for every H3 signification is the **Moon frame** (lord Venus, navamsa `confirms`); `synthesis._compose_v2` reads the *lead* ledger, while the markdown/HTML pillar line reads the *lagna* ledger (`_lagna_ledger`, lord Mars, navamsa `neutral`). Same clash in the HTML "Why" vs "Calculation" panes. The reader is also told "**Lord** Mars in H8" when the verdict was actually decided in a frame whose 3rd-lord is Venus — the frame is never named.
- **H4 Mother/Home, H7 Spouse, H9 Father** — the timing hook is **hijacked by the maraka set**. Because `mother`/`spouse`/`coverture`/`father` are in `_TIMING_MARAKA_KEYS` (`house_template.py:1365`), the maraka windows sort first (`{"maraka": 0, …}` at :1410) and the display caps at 5, so the entire activation line reads "activated in Mercury(maraka) 1990-1995 / Venus(maraka) 2002-2022 / Sun(maraka)… / Mars(maraka)… / Jupiter(maraka)…" — five death-dealing labels covering the native's whole life, **zero** ordinary lord/karaka/timer fructification windows, and the word "maraka" is glossed only 300 lines later in the maraka chapter. To a client, "Mother/Home… activated in (maraka)" for 70 straight years is alarming, doctrinally mis-emphasized (these are the *native's* 2nd/7th lords repurposed toward a relative's longevity), and information-free. H4 is otherwise the best-covered house (6 karyas matching HTJAH-I's 4th-house table exactly, per-karaka routing Moon/Jupiter/Venus/Mars with citations).
- **H6 Health/Enemies** — the best Conclusion of the twelve: "the lord is strong — on this affliction matter it feeds the affliction, never rescues" plus the rank-12 magnitude clause. This is genuinely Raman's dusthana logic voiced correctly, and shows the composer *can* speak doctrine when the flags are wired.
- **H10 Career** — the flagship *split-status* case (5 of 6 favourable, headline afflicted via `profession_trade`) and the flagship dashboard conflict (dashboard: career **favourable** from the D-10 reader). PREC-1 and the tension-narrator line in "Your Reading" do reconcile it — but only for a reader who has already internalized the interpretation guide 400 lines earlier; nothing *in the H10 block itself* points at the dashboard disagreement.
- **H12 Loss/Moksha** — the honesty machinery at full stretch: split-status note + INVERTED-channel WARNING + "highest Bhava Bala → difficulty delivered with unusual force" — immediately followed by calibration lines showing 4 of 6 significations *favourable*, two of them top-quintile (`loss_moksha` 84%, `foreign_residence` 79%). The house that most needs a reconciling sentence gets three separate disclaimers instead of one synthesis. Also note the layered irony the block never voices: the headline is driven by a *catastrophic-gated, inversion-flagged* channel while the two genuinely distinctive favourable readings sit unremarked below it.
- **H8 Longevity** — clean, and the one house whose `death_window`/`decanate_cause` metadata is computed but never shown in the block (deliberate deferral to the Longevity chapter — correct call, but an explicit "see Longevity below" pointer is absent).

## The general pattern — measured against Raman's own house-chapter anatomy

Raman's per-house analyses pair the verdict with four things. Scorecard:

1. **The specific combination that fired, in his words** — **computed, buried**. Every fired rule carries Raman's own condition→effect prose and citation (verified: `H3.C.9` "the 3rd lord an evil planet, or evil planets occupying the 3rd → very few brothers… (HTJAH-I:3435)"), yet the house block renders only **counts** (`Rules 38`, `Sources 7`). The matter monographs (marriage/wealth/children) *do* print rule prose verbatim — so the report's longest chapter is the only judgment surface that withholds its own evidence text. The "Raman writes" verbatim level (item 14) exists in both renderers but is corpus-gated: `passage_quote()` returns `''` here, so the level **silently vanishes** from all 12 houses with no placeholder (flag: citations render as book:line only; verify verbatim quotes when the corpus is present).
2. **The timing hook** — **present and good** (activation windows + ACTIVE badge; the four-tier par-excellence/ordinary/limited/feeble grading lives correctly in the Life-narrative). Defect: the maraka hijack above, and the badge only fires on par-excellence, so a "limited/feeble now" house shows nothing about the current period.
3. **The frame comparison (Lagna vs Moon)** — **computed, invisible**. `FrameLedger`s for lagna/moon/karaka exist per signification with `lead_frame` chosen by lord Shadbala (house_template docstring), and "Stronger frame — LAGNA (HTJAH-I:645-646)" appears once in Chart signature — but no house block ever says *which frame judged this house*, producing the H3 contradiction. Raman names his frame in nearly every worked chart; this is the largest doctrinal presentation gap.
4. **Remedial/moderating remarks on partial affliction** — **absent**. Zero occurrences of moderation language in the chapter. The ledger holds the material (`parivartana_resilient`, `karaka_intact`, neecha-bhanga, benefic-relief clauses inside rules, `catastrophic_gate: demote(malefic<3)` metadata on H12), so Raman-style "the affliction is considerably reduced by…" sentences are compose-from-computed, not new doctrine. (Constraint respected: moderating *description*, never remedy prescriptions or dated relief.)

**Signification coverage vs HTJAH's chapter tables**: strong where it counts — H4 (6), H7 (6, incl. coverture and virility), H10 (Sun/Mercury/Jupiter/Saturn quad-karaka dispatch), H12 (6, incl. left_eye paired with H2 vision — a fine doctrinal touch). Thin: **H1** (3 keys, 1 rule bucket); **H3** missing writing/neighbours (HTJAH-I 3rd-house karyas — flag for verification against the chapter TOC); **H2** missing food/sustenance; **H5** missing speculation and upasana (flag for verification); **H6** missing servants/subordinates; **H12** missing bed-comforts. All are add-only rows in `significations.py` + rule buckets.

**Correctness bugs found while reading as a client:**
- **The `·` → `?` mangle**: `_REPL` in `render.py:22` lacks `"·"`, so `_fold_ascii` turns every computation badge into `` `Evidence 10` ? `Rules 24` ? `Sources 4` `` — 12 garbled lines in the chapter's most metric-looking element.
- **The badge inflates**: `Rules` counts every fired-rule *instance* across all significations × all frames (`for _led in (_sv.ledger, *_sv.alt_ledgers)`, detailed_report ~3233), so H3 shows "Rules 38" where distinct rules number ~9; `Sources` is deduped but `Rules` is not — the two badges use different arithmetic under one visual grammar.
- **Dashboard support column half-dead**: `_MATTER_HOUSE` (tension_narrator.py:21) maps only 12 legacy keys; 7 of the 12 dashboard matters (siblings, mother, property, father, comforts, spiritual, education) miss and print "-" — a pure key-mismatch, since every matter has an obvious house.

**Reader experience of the chapter as a whole**: the markdown flattens what the HTML gets right. `report_html._house_section` has real traversal design — verdict chip + split badge + driver in one scannable head, then Why (open) / Evidence / Calculation / Classical-text disclosures. The markdown prints everything at one level, so the 12-house stretch reads as: header → blockquote → pillars → garbled badges → a semicolon run-on (`mr.reading` is machine-composed: "the rashi reads **favourable**; and the navamsa confirms it (delivered); Ashtakavarga average…") → Conclusion → calibration list. The **Conclusion lines are the chapter's best prose** and its natural scanning spine, but they sit *below* the run-on instead of directly under the header. The calibration lines land well when they differ (H4, H12) and badly when they repeat (H1, H6 — five near-identical NEAR-UNIVERSAL rows); a house-level rollup line ("all five sub-readings near-universal") would say the same in one line and let the distinct rows stand out. The split-status notes are excellent — the single best honesty device in the chapter.

## VERDICT

**Sound skeleton, buried evidence.** The chapter is doctrinally *safe* — nothing it says misrepresents Raman, the weakest-link rule is disclosed, the calibration/Measured-Truth lines are a genuine feature and correctly framed as disclosure. But judged against Raman's own house chapters it reads as a *scorecard about* a judgment rather than the judgment itself: the fired combinations (his words, computed and citated in `FiredRule.text`), the frame that decided, and the moderating factors are all in the proforma and all withheld. Plus one visible self-contradiction (H3 navamsa), one alarming mis-emphasis (maraka-flooded activation on H4/H7/H9), and three mechanical defects (`?` badges, inflated Rules count, half-dead dashboard column).

## ADD (all Raman-licensed, all add-only)

1. **Per-house "Chief combinations" sub-list**: top 2–3 fired rules per decided signification, rendered as `fr.rule.id` + effect prose (`fr.text`/`.afflicted`/`.fortified`) + `(work:line)` — exactly how HTJAH chapters argue. Skip `branch="fortified"` rows whose text is the "no favourable variant given" placeholder (H3.L.8 would otherwise print nonsense). Corpus-absent citations stay book:line (flagged for verification).
2. **Frame disclosure line**: "Judged from the **Moon** (Chandra-Lagna 3rd, lord Venus); from the Lagna (lord Mars) the reading is neutral — the stronger lord's frame decides (HTJAH-I:645-646 concept; flag exact line for verification)." One sentence, composed entirely from `lead_frame` + the two ledgers; also *fixes* the H3 contradiction by explaining it.
3. **Moderating-factor clause** in the Conclusion when the ledger carries `parivartana_resilient` / intact-karaka-under-affliction / catastrophic-gate demotions: "the affliction is qualified — …" (Raman's own partial-affliction device). Descriptive only, no remedies, no dates.
4. **Missing significations** (rows in `significations.py` + rule buckets, per HTJAH chapter TOCs, each flagged for citation verification): H1 appearance/character; H3 writing, neighbours; H2 food; H5 speculation; H6 servants; H12 bed-comforts.
5. **Current-period tier line per house**: "in the running Sun/Mercury period this house grades *ordinary*" — the four-tier vocabulary already computed for the Life-narrative, surfaced where the reader is asking about the house.

## MODIFY (renderer fixes; nothing removed)

1. `render.py::_REPL` — add `"·": " - "` (or similar) so badges stop printing `?`.
2. Badge arithmetic — dedupe `Rules` by `rule.id` (match `Sources`), or relabel as "rule-firings".
3. `_MATTER_HOUSE` — add the 7 missing dashboard keys (siblings→3, mother→4, property→4, father→9, comforts→4, spiritual→9 or 12, education→4) so the support column fills.
4. `synthesis` reading line vs pillar line — read navamsa from the same ledger (or, better, implement ADD-2, which makes both true statements about named frames).
5. `_event_timing` — for `_TIMING_MARAKA_KEYS`, cap maraka windows at 1–2 and keep lord/karaka windows visible (or split into a separately-labeled, glossed "relative-longevity windows" note); never let "(maraka)" be the entire activation line for the mother/spouse/father houses.

## UX

- **Verdict-first traversal**: open the chapter with a 12-row strip (H# — name — verdict chip — driver — split badge — active?) so a client scans in 10 seconds, then reads deep; markdown table equivalent of the HTML house-head row. Per-house, promote the **Conclusion** directly under the header; demote the semicolon run-on into a labeled "Working" line.
- **Calibration rollup**: when ≥3 of a house's lines share verdict+band, prefix one summary line and keep the full rows (add-only, satisfies the completeness directive) — H1's three clones and H6's five NEAR-UNIVERSALs currently dilute the genuinely notable rows (H4 education 3% rare, H12 84th percentile).
- **In-block cross-references**: H10 → "the dashboard's career verdict differs; PREC-1 governs"; H8 → "death-window detail in Longevity below"; every WARNING → link to Information-content. The interpretation guide is excellent but 400 lines away at the moment of confusion.
- **Corpus-absent placeholder** for the Classical-text level ("verbatim passage unavailable in this build — citation HTJAH-I:3428") instead of silent disappearance.

## Top-5 moves (priority order)

1. **Surface the fired combinations with Raman's effect prose + citations per house** (ADD-1) — converts the chapter from scorecard to judgment; the data is already in every `FiredRule`.
2. **Fix the maraka-flooded activation lines on H4/H7/H9** (MODIFY-5) — the chapter's one genuinely alarming/misleading element for a real client.
3. **Name the deciding frame and reconcile the H3 navamsa contradiction** (ADD-2 + MODIFY-4) — restores Raman's Lagna-vs-Moon device and removes the only visible self-contradiction.
4. **Mechanical trust repairs in one pass**: `·`→`?` badges, deduped Rules count, the 7 dead dashboard-support cells (MODIFY-1/2/3).
5. **Verdict-first strip + Conclusion-promoted block layout with in-block PREC-1 cross-refs** (UX) — makes the report's longest stretch traversable and lets the split-status/calibration honesty devices land where the reader actually stumbles.

# Appendix — full critique: matter (verbatim agent report)

I have everything I need. Here is the full critique.

---

# THE MATTER MONOGRAPHS — senior-astrologer + reader-experience review

**Basis:** canonical chart (BirthData C, 1990-07-15 12:00 +5.5, Bangalore) rendered via `build_detailed_report` → `to_markdown` (211,801 chars); composers read: `/home/user/astro/app/raman_saab/monographs.py`, `/home/user/astro/app/raman_saab/arishta_wealth_profession.py`, `/home/user/astro/app/raman_saab/detailed_report.py` (longevity/maraka/health/arishta render blocks, lines 3383–3515 and 3871–3930), `/home/user/astro/app/raman_saab/primitives/maraka.py`, `primitives/career.py`, `judges/trimsamsa_health_reading.py`, `doctrine/rule_sets/house_07_kalatra/combinations.py`.

**Two hard bugs found first (both in `/home/user/astro/app/raman_saab/detailed_report.py`):**

1. **Repr leak into the Longevity chapter.** `to_markdown` unpacks `y, mo, d = r.longevity_ymd` at line 2656, but line 3140's `for y in r.yoga_deep:` re-binds `y` to a `YogaDeepRead` object; line 3401 then renders `({y}y {mo}m {d}d)` — the client-facing Longevity section prints a full multi-hundred-character dataclass repr inside the "about 88 years" sentence. One-character fix (rename the loop variable); it corrupts the single most sensitive chapter in the report.
2. **Empty "Raman verbatim" quotes rendered as `""` with a citation.** On a corpus-absent machine, `_pull()`/`passage()` return empty, and the renderers print the empty string unconditionally: the marriage monograph's *three* headline quotes ("The 7th house's scope", "Timing doctrine", the separation block, lines 3878/3895/3906), the children chapter's combination block (line 3929), and Arishta's "Raman's antidotes (verbatim) — \"\" (HPA-14:232)" (line 3501). Five empty quotation marks each solemnly cited look broken and corrode the authority the verbatim device exists to project. Render an honest absence instead: "[passage HPA-14:232–266 — corpus not present on this machine; flagged for verification]". (Contrast: `lord_period_text` and `spouse_sign_text` are correctly gated behind `if`.)

---

## 1. Marriage monograph (`monographs.py: build_marriage_monograph`, render 3871–3907)

**What it does:** verbatim 7th-house scope (HTJAH-II:198–231), the 7th-lord-in-house dasha extract (710–852), 7th-lord-in-sign paragraph (HPA-22), all fired kalatra rules of the 50-rule set with cites, upapada, verbatim navamsa timing doctrine (853–886), H7 dasha activations, H5 pointer, verbatim separation passage (887–940) under the method-not-prediction frame, unchanged H7 verdict.

**VERDICT — astrological:** the strongest chapter architecturally: right inspection order, chart-specific fired rules with cites, and the separation material handled exactly as doctrine demands (quoted, never composed). But of Raman's full protocol it is missing spouse *description* as an assembled read (the D-9 section computes "spouse significator: Saturn" and the 7th-lord's navamsa but never describes the partner), spouse *direction*, computed early/late timing indicators (the 853–886 passage is quoted, not operationalised — no "Saturn on the 7th/Venus → delay" vs "benefic 7th → early" line, though the primitives to derive both exist), Kuja dosha *cancellation narration*, and the marital-happiness vs spouse-longevity (coverture) split the engine just shipped — the H7 proforma computes `marital_happiness` and `coverture` separately (visible in the House 7 population context) but the monograph shows only the rolled-up "favourable".
**VERDICT — UX:** with the corpus present this would read like a consult; on this render it opens and closes with empty quotes, and the fired-rule bullets dump raw rule text ("Bhava-frame + per-sign exceptions (7th exempt in Cn/Cp...) kept in text; two-chart matching grid is v1-OOS") — engineering provenance leaking into client prose.

**ADD (all Raman-licensed, add-only):**
- **Happiness/coverture split line:** "Marital happiness: favourable (mild); the partner's own longevity (coverture): favourable (mild)" — pure re-read of H7 significations (HTJAH-II 7th-house chapter separates the two; this is B3's exact distinction surfaced where the client looks for it).
- **Kuja dosha narration:** the `_KujaDosha` condition (combinations.py:223) already evaluates Lagna/Moon/Venus frames, Leo/Aquarius universal exemption, per-house sign exemptions, and Mars+Jupiter/Mars+Moon neutralisation — but emits only fired/not-fired. Emit *which reference point(s) place Mars in a dosha house, and each cancellation checked with its result* ("from the Moon, Mars falls in the 8th; Mars in Sagittarius — not an exempt sign for the 8th; Mars conjunct neither Jupiter nor the Moon — dosha stands"). HTJAH-II:2579–2622; the data is in the evaluation path already.
- **Spouse-description block:** the 7th sign's nature, the navamsa sign occupied by the 7th lord and by Venus, and the D-9 spouse-significator's temperament — cite HTJAH-II 7th-house descriptive passages, *flag ranges for verification against the vendored file* (per the v33 precedent of refusing to guess line ranges).
- **Computed timing indicators:** an early/delayed lean from encoded primitives (benefics vs Saturn/malefics influencing the 7th and Venus), presented beside the verbatim timing doctrine as "the method's own lean", undated. Flag the exact passage for verification.
- **Transit trigger line:** Raman uses Jupiter's transit of the 7th/7th-lord/Venus in marriage timing — re-read the already-computed favourable-transit windows for Jupiter-on-H7 rows and surface them here. Flag for verification.

**MODIFY (within add-only):** route fired-rule text through a client register that drops maintainer notes ("v1-OOS", "owned by H7.C.60") into a footnote rather than the bullet; fix empty-quote rendering (bug 2).

**UX:** the eight fired rules mix fortified and afflicted in arbitrary order — group fortified/afflicted with a one-line tally so the reader sees the balance before the detail.
**Priority: HIGH** (bug 2 + the happiness/coverture split are cheap and high-value).

## 2. Children chapter (`build_children_chapter`, render 3909–3930)

**What it does:** H5 verdict + all H5 significations, fired putra rules with cites, H5 dasha activations, verbatim HTJAH-I:5179–5297 combination block.

**VERDICT — astrological:** thin relative to its own preamble. The preamble promises "3. the Saptamsa D-7" — the chapter contains *no D-7 row at all*, while the D-7 section 500 lines earlier carries beeja/kshetra, per-child seat afflictions, and a gender lean. Jupiter (putrakaraka) gets no condition line here (the aptitude chapter has one; children doesn't). No count indication. Classical shorthand ("loses a number of children", "with Venus → homosexual tendencies") appears raw in the fired-rule bullets *without* the excellent degrees-of-difficulty reframe that the D-7 section's `[RAMAN_GENERAL_PRINCIPLE]` note provides — the one chapter clients read most anxiously is the one without the softening frame.
**VERDICT — UX:** a bullet list, not a chapter; ends on an empty quote (bug 2).

**ADD:** (a) a D-7 corroboration row re-reading the Saptamsa core (beeja/kshetra, D-7 verdict, gender lean) with its provenance tags; (b) Jupiter's condition line (karaka, HTJAH-I:5012 neighbourhood); (c) the classical-shorthand reframe note copied verbatim from the D-7 section's preamble — it exists, it is doctrine-reviewed, it just isn't here; (d) count indications from the 5th lord's navamsa/occupants *only if* a pinnable Raman passage is found — flag for verification, do not guess.
**MODIFY:** fix bug 2 on `combos_quote`.
**UX:** put the H5 headline and the reframe note *before* the fired rules so "loses a number of children" is never the first thing a parent reads.
**Priority: HIGH** (the missing reframe is a real reader-harm risk; the D-7 row is a pure re-read).

## 3. Profession synthesis + Career (`build_profession_synthesis`, career one-liner at 1637)

**What it does:** five derivations (10th sign, navamsa-dispositor — Raman's primary method, correctly encoded in `primitives/career.py` per HTJAH-II:10249 — strongest planet, AK with an honest Jaimini-scope note, running MD), H10 mode split, deterministic token-overlap convergence.

**VERDICT — astrological:** the navamsa-dispositor technique is present and correct. Missing from Raman's fuller protocol: (a) **10th-from-the-Moon** (and Sun) — grep confirms no career derivation from the Moon exists anywhere (`career.py` is Lagna-only); Raman explicitly judges the 10th from Lagna, Moon and Sun and takes the strongest; (b) **a D-10 row** — the preamble lists "the Dasamsa D-10" as step 4, but the table has no Dasamsa row even though the D-10 reading (career FAVOURABLE, 10th-lord-in-D-10 enemy) sits computed in the same report; (c) **profession timing** — marriage and children both get "H-activations in the window"; the work chapter has no H10 activation line and no "rise in the 10th-lord's dasha" statement (HTJAH-II ties professional rise to the periods of the 10th lord and the navamsa-dispositor — flag passage for verification).
**VERDICT — UX:** the convergence count is quietly misleading: "gold (4)" — but strongest planet, AK and running MD *all resolved to the Sun*, so three of the four votes are one planet wearing three hats. Deterministic, yes; informative, no. The standalone "Career" section is a one-line duplicate of table rows 1–2 with no cross-reference.

**ADD:** 10th-from-Moon (+Sun) derivation rows with the same CAREER_BY_SIGN table (cite HTJAH-II/HPA, flag for verification); a D-10 re-read row; an H10-activations timing line (same infrastructure as marriage); a note on the convergence line when ≥2 derivations resolve to the same graha ("3 of 4 'gold' votes are the Sun under three hats").
**MODIFY:** none required doctrinally.
**UX:** append "expanded in the Profession synthesis below" to the Career one-liner.
**Priority: MEDIUM-HIGH** (10th-from-Moon is a genuine doctrine gap; the rest is re-reads).

## 4. Wealth chapter (`build_wealth_chapter`)

**What it does:** channel table — earning style via 2nd-lord's house (SECOND_LORD_HOUSE_GAINS, HTJAH-I:2511), planets-in-11th gains, H2/H11/H8/H5/H10/H4/H12 signification verdicts, and expansion periods (MDs with H2/H11 at ordinary+).

**VERDICT — astrological:** channels-not-verdict is the right instinct and the earning-style/gains-channel rows are genuinely Raman. Missing: **dhana yogas and Daridra** — `doctrine/yogas.py` encodes Y.DHANA.EXCH, Y.DHANA.59, Y.DHANA.CHAIN, Y.DHANA.122, Y.DHANA.125 and Y.DARIDRA, yet the wealth chapter never states which fired or that none did. Presence *and absence* of dhana yogas is the classical first question about wealth; an explicit "Dhana yogas: none of the encoded set fires; Daridra: absent" line is a pure re-read.
**VERDICT — UX:** the expansion-period line is the chapter's biggest credibility problem: *every one of the five MDs* shows "H2 (par excellence), H11 (par excellence)". A timing lens under which all periods qualify at the top grade discriminates nothing — and this report already knows how to say so (the population-context rows flag near-universal readings as "carries little information"). The chapter should apply its own standard to itself.

**ADD:** dhana/daridra fired-or-absent row (cites already on the YogaRecords); 2nd-lord and 11th-lord condition lines (dignity/avastha — same `_condition` helper as aptitude); a self-disclosure note when all MDs in the window qualify ("in this chart every period activates H2/H11 at the top grade — the lens is non-differential here"), which is Measured-Truth framing applied consistently.
**MODIFY:** none.
**UX:** eleven of fourteen rows read "favourable (moderate/mild)" — add the population-calibration percentile per row (it exists for house significations) so the table stops being a wall of "favourable".
**Priority: MEDIUM** (dhana-yoga row HIGH within it).

## 5. Aptitude, intelligence & work style (`build_aptitude_profile`)

**What it does:** H5 intellect + fired combos, Mercury/Jupiter condition lines, fired H1.M.* Moon-mind rules (per-sign, cited), H3 courage, the three vocational angles, H10 mode split, 10th-lord/Saturn/Mars conditions, bannered modern keywords, deference-to-synthesis conclusion.

**VERDICT — astrological:** the best-behaved composer in the group: every Optional is an honest absence, modern glosses are bannered, the deliberate refusal to guess the Moon-mind master-passage range (module docstring, lines 33–36) is exactly the project's doctrine standard. The Moon-mind fired rule surfaces bluntly though: "stubborn, psychically receptive, highly religious, stoical, bigoted and God-fearing" — Raman's own words, but presented as a naked bullet.
**VERDICT — UX:** it is a well-labeled parts list, not a profile. The `woven` paragraph is meta-commentary about method; no sentence actually *weaves* ("a Mercury-ruled 10th resolving to Venus, over a stubborn Revati Moon…"). Duplicates the profession rows verbatim (acceptable per report-completeness, but a "governed by the Profession synthesis" tag per-row would prevent clients reading them as independent confirmations — currently only the closing note says so).

**ADD:** the pinned HPA Moon-mind master passage once the corpus machine verifies the range (already planned); a 2–3 sentence guard-safe composed synthesis in Raman's descriptive idiom drawing only on the listed rows.
**MODIFY:** none.
**Priority: LOW-MEDIUM.**

## 6. Longevity (render 3383–3404)

**What it does:** states Raman's order (band by combination first, marakas second, numeric Ayurdaya as cross-check only — HTJAH-II:4465–4472), shows Balarishta result, the fired band combination *with its basis* ("Purnayu (75-120y): the Lagna and 8th lords in the 8th or the 11th"), then the numeric span with band-not-date framing.

**VERDICT — astrological:** the honest gating is exemplary — the classification basis is shown with its reason, which is what the brief asked. Gaps: Balarishta "does not apply" gives no account of *what was screened* (the applies-case shows reasons; the clear-case shows nothing — a client can't see the method worked); the band label is inconsistent ("Purnayu" in the combo, "class **purna**" in the cross-check).
**VERDICT — UX:** currently destroyed by bug 1 (the repr leak sits exactly in this sentence). "the engine's own health layer defers lifespan" is developer-speak in a client chapter.

**ADD:** a one-line Balarishta screen disclosure on the clear case ("screened: Moon-in-malefic-frames, malefic lagna afflictions per HPA-14 — none present"), pulled from the primitive's checked-conditions; harmonise purna/Purnayu labels.
**MODIFY:** fix bug 1; replace "engine's own health layer defers lifespan" with reader language ("this report never converts the band into a date").
**Priority: CRITICAL** (bug 1) then LOW.

## 7. The maraka scheme + Maraka×Saturn confluence (render 3406–3455; `primitives/maraka.py`)

**What it does:** tiered maraka set (correct HTJAH-I:776–814 construction: 2/7 lords, malefic occupants/associates, 3/8 lords secondary, Saturn-touching + 6th lord + Shadbala-weakest tertiary), 22nd drekkana / 64th navamsa lords, running-period flag with "broad, low-discrimination by design"; then the Saturn-return-to-natal-sign/trines confluence table (HTJAH-II:4846–4849) with the rasi-half-only admission and double Measured-Truth framing.

**VERDICT — astrological:** the scheme is doctrinally sound and the tier-score explanation is honest. The one real doctrinal gap: **no per-planet reason.** `maraka_points` knows *why* each graha entered its tier (which clause fired) but `seen.setdefault` discards it; the report says "primary: Venus, Jupiter, Sun, Saturn" as bare assertion. For a section whose whole licence is "disclosure of the method", the derivation is the content. The Navamsa half of the Saturn signature is honestly declared uncomputed — encode it eventually or keep the declaration.
**VERDICT — UX:** the framing is clear and not yet deadening (two disclaimers is the right number here). But the confluence table prints *dated calendar windows* (2067–2089) beside death vocabulary — it survives the decree guard only by its framing. Keep the framing physically adjacent to the table on every surface (in the HTML, the disclaimer must not be collapsible away from the table). Tier column: a reader must retro-fit the primary=3/secondary=2 arithmetic from the preamble; add the addends ("6 = Saturn 3 + Venus 3").

**ADD:** per-unit reason strings in `MarakaUnit` ("Venus — lord of the 2nd"; "Sun — malefic aspecting the 7th lord Jupiter") — small change in `maraka.py` (record the clause at `add()`), pure disclosure; tier addends in the table.
**MODIFY:** none.
**Priority: MEDIUM-HIGH** (reasons are cheap and go to the heart of the method-disclosure claim).

## 8. Health & vulnerability read-out (render 3457–3485; `trimsamsa_health_reading.py`)

**What it does:** one-page re-read: H1/H6/H8/H12 verdicts, Moon/Mercury karakas with afflictors, balarishta, maraka tiers, band — every row naming its source section; the D-30 module's core/overlay split is provenance-exemplary.

**VERDICT — astrological:** faithful to Raman's real method (1st+6th+8th+Moon+Mercury+balarishta, with D-30 as corroboration only — correctly argued in the module docstring). The major absence the brief predicted is confirmed: **no anatomical mapping at all** — no sign→body (Kalapurusha) table, no planet→disease table exists anywhere in the package (grep across `app/raman_saab` finds nothing). Raman's HPA carries both; "which body areas does the chart mark" is literally this section's subtitle question, and it answers with house numbers, not bodies.
**VERDICT — UX:** the best-framed section in the group ("nothing here is new" + per-row provenance is exactly right). Minor: Moon/Mercury rows are provenance-labeled "D-30 health core (Raman's single-chart method)" — confusing, since the docstring itself insists the core is *not* the D-30; label it "single-chart health core (H1/H6/H8 + karakas)".

**ADD:** the HPA sign→body-region and planet→disease tables (cite by chapter, flag line ranges for verification), applied as a re-read: the 6th's sign, the lagna sign, and signs holding the afflicting malefics → "areas the method marks for care", tendency-framed. This is the single biggest Raman-licensed content gap in my group.
**MODIFY:** the provenance label above.
**Priority: HIGH.**

## 9. Arishta & Bhanga (`build_arishta_chapter`, render 3487–3515)

**What it does:** balarishta with cancellation state, verbatim HPA-14:232–266 antidotes, per-planet bhanga (dignity vs effective dignity), Kemadruma with its own bhanga honoured ("geometry present but CANCELLED — the yoga does not fire" is exactly the right narration), fired longevity protections, band, maraka context.

**VERDICT — astrological:** the affliction-*and*-antidote symmetry is doctrinally correct and the Kemadruma three-state narration is the best bhanga prose in the report. Two gaps: (a) "no debilitation-cancellation operates" is ambiguous between "no planet is debilitated" (this chart — Mars is moolatrikona) and "a planet is debilitated and stays uncancelled" — doctrinally opposite situations collapsed into one sentence; (b) the balarishta clear-case again shows no screened-conditions disclosure.
**VERDICT — UX:** seven bullets, clear frames; but the marquee item — Raman's antidote passage — is the empty-quote bug, so the chapter's crown jewel renders as `""`.

**ADD:** distinguish the two no-bhanga cases ("no planet is debilitated in this chart, so no bhanga question arises" vs per-planet uncancelled-debility lines); balarishta screen disclosure (shared with Longevity).
**MODIFY:** bug 2 on the antidote quote.
**Priority: MEDIUM** (bug 2 fix is CRITICAL-adjacent).

---

## Cross-chapter finding

The D-9 marriage reading (its own section) states Kuja dosha is "reckoned from the Lagna only" and that Moon/Venus frames, per-sign exceptions and cancellations are "not yet encoded here" — while the H7 kalatra rule `_KujaDosha` (combinations.py:223–246) encodes all of it. Two surfaces, contradictory scope claims, and this chart's D-9 says "dosha: present" under the narrow check while the full-check fired-rule also fires — they agree here by luck, and the stale note misinforms the reader either way. Update the D-9 note to point at the full H7 rule (add-only: the note is prose, correcting a false provenance claim is fidelity, not removal).

## Top-5 moves for the group

1. **Fix the two renderer bugs** — the `y` shadowing repr-leak in the Longevity sentence (`detailed_report.py:3140` vs `:2656`/`:3401`) and the empty-verbatim-quote rendering (five sites: 3501, 3878, 3895, 3906, 3929) → render a flagged corpus-absence line instead of `""`. Nothing else matters to a reader until these are gone.
2. **Surface the marital-happiness vs spouse-longevity (coverture) split in the Marriage monograph, plus Kuja dosha cancellation narration** — both are pure re-reads of already-evaluated state (H7 significations; `_KujaDosha`'s own evaluation path), and they are exactly the B3 distinction and the HTJAH-II:2579–2622 protocol the engine just committed to.
3. **Anatomical mapping for Health** — encode Raman's HPA sign→body and planet→disease tables (chapter-cited, line ranges flagged for verification) and re-read the afflicted signs through them. Largest genuine doctrine gap in the group.
4. **Per-planet maraka reasons** — record the qualifying clause in `maraka.py`'s `add()` and print it. Converts the scheme from assertion to the method-disclosure it claims to be, at trivial cost.
5. **Profession: add the 10th-from-Moon derivation, a D-10 row, and an H10-timing line; annotate same-graha convergence** — closes the preamble-vs-content mismatch (the chapter promises the Dasamsa and never shows it), adds Raman's Moon-reference check (currently absent from the codebase), and stops "gold (4)" from over-selling one planet counted thrice. Apply the same non-differential disclosure to Wealth's all-par-excellence expansion periods.

All recommendations are add-only, keep Measured-Truth framing intact, keep the decree guard (everything timing-flavoured stays undated-lean or method-window with framing), and every new doctrinal claim above is marked for corpus verification rather than asserted from memory.

# Appendix — full critique: timing_divisional (verbatim agent report)

I generated the canonical report (BirthData('C',1990,7,15,12,0,5.5,12.97,77.59) via `build_detailed_report` → `to_markdown`, saved at /tmp/claude-0/-home-user-astro/f5b04b2d-8abf-53b0-bb89-84bcfac4280d/scratchpad/timing_report.md) and read every composer in my chapter group. Two environment notes before the critique: **Karmic evolution rendered as absent** in this run because `passage("JAIMINI-9:799-847")` returns None with the corpus absent (`build_karmic_evolution` → None, section silently skipped), and **Today for you (Muhurtha)** exists only as an on-demand panel on the interactive page (`/electional/today`), not in the markdown/standalone HTML at all.

---

# TIMING, DIVISIONAL & SOUL — chapter critiques

## 1. Life-narrative (Vimshottari) + four outlook companions

**What it does.** `app/raman_saab/primitives/vimshottari.py` encodes the locked HTJAH-I method exactly: `timer_set` (six-factor influence), `lords_associated` (conjunction/mutual aspect), `bhukti_tier` (par excellence / ordinary / limited / feeble, uniform across houses). `detailed_report.py:3517-3557` renders MD→AD bullets with tier buckets and a plain-terms line; the four companions (Ishta/Kashta GBB-10, MD-lord condition HPA-24, AV dasha-seat, ASP-12 Kakshya) paint the same windowed timeline.

**VERDICT.** *Doctrine:* the strongest chapter in the report — the four-tier grading is faithfully encoded AND its association clause is narrated per bhukti ("AD associated with MD" / "own bhukti"). But the narration stops one level short of Raman: the tier is **asserted, never derived**. Raman always names the factor — "Saturn, as lord of the 2nd, aspecting its lord…" — whereas here the reader learns H2 is par excellence without learning *by which of the six factors* Venus and Saturn influence H2. The engine knows this inside `timer_set` but throws the roles away (it returns a flat `frozenset`; roles are lost at vimshottari.py:205-238). Second doctrinal gap: **par-excellence flooding** — in own/associated bhuktis 10-11 houses grade par excellence (the primitive's own docstring admits broad-recall/low-precision), and the one Raman-licensed discriminator the engine already computes — `lord_quality` (delivers well/poorly/mixed, HTJAH-II:10004-10008, carried on every `ActivatedHouseReading`) — is **dropped by the markdown renderer** (only `a.house` and `a.natal_verdict` survive at detailed_report.py:3544). That is a Report-Completeness violation by the project's own locked rule. Third: **Pratyantar is computed and never shown** — `pratyantars()`/`pratyantar_on()` exist (vimshottari.py:120-154, citing HTJAH-II:668-702 naming all three levels as result-carriers) and are used by rectification, but no report surface renders them. *Reader:* the MD-header + AD-bullet structure does carry Raman's "dasha of X, bhukti of Y" frame; the plain-terms lines are excellent; but a reader asking "what about 2027?" must scan date ranges in five separate structures.

**ADD (Raman-licensed).** (a) Per-house influence-basis tags in the tier buckets — "H2 par excellence (MD: aspects lord; AD: owns)" — via a role-preserving `timer_set` variant; HTJAH-I:1586-1596 lists the factors individually. (b) Render the already-computed `md_quality`/`antar_quality` delivery tags per row. (c) A Pratyantar drill-down for the current bhukti only (9 rows, same uniform grading; HTJAH-II:668-702 — flag exact lines for corpus verification). (d) One clause explaining nodal "no data" rows in Ishta/Kashta (nodes carry no Ishta/Kashta by construction) and the silent absence of nodal MDs from the Kakshya table (kakshya_timing.py returns no rows for nodes; the table never says so).
**MODIFY.** Open each plain-terms line "In the Sun dasha, Mercury bhukti…" — restores Raman's sentence form at row level.
**UX.** The four companions fragment; the interactive `lifePanel` (report.html:1100-1180) is genuinely the integrating answer — the markdown needs at least a per-year index (see Top-5 #2). **Priority: HIGH.**

## 2. Life-chapters

**What it does.** `build_life_chapters` (detailed_report.py:2016-2168) knits one paragraph per MD run — functional nature, condition, lean, yogas ripening (HTJAH-I:4324), houses lit at best tier, AV seat under Raman's own caveat, transits last per HTJAH-I:8410-8411 — explicitly modeled on Chart No. 203 (HTJAH-I:15950-15999).

**VERDICT.** *Doctrine:* the correct Raman narration shape, correctly ordered (natal first, transits secondary). Weakness: because houses_lit floods, chapters read nearly identically — differentiation comes only from lean/condition/yogas. *Reader:* good; current chapter auto-opens on the interactive page. Real blemish: the Rahu chapter renders "**Rahu is a neutral for this Lagna: .**" — `cond_words` is empty for a node (no Shadbala, no lean), leaving a dangling colon-period (detailed_report.py:2082-2084).

**ADD.** For nodal MDs, the sentence Raman actually licenses: a node gives the results of its dispositor/occupied house (HTJAH-I:2764/8566 — already cited in `timer_set`); name the dispositor and its condition. This fixes the empty clause *and* adds doctrine. Also: Sade-Sati phases overlapping the chapter's years (see chapter 4) belong in the transits-last sentence.
**MODIFY.** Compress the houses-lit list when >8 houses share a tier ("all houses save H3…" — a join, not a re-grade).
**UX.** Fine. **Priority: MEDIUM** (the nodal sentence is cheap and visible).

## 3. Decade indication timeline

**What it does.** `life_arc.py:build_decade_timeline` slices the windowed timeline into birth-decades; honest frame; decades outside the window labeled, not guessed.

**VERDICT.** *Doctrine:* clean pure-re-read; the "never a probability" frame is exactly right. *Reader:* two problems. (a) Duplicate contradictory chips — 2020-2030 lists "self & health (H1, limited)" AND "(H1, par excellence)" because the dedup key is the full label string including tier (life_arc.py:100-105); the reader sees the same area twice with two grades and no explanation that they come from different MDs. (b) Ages 0-30 and 50+ are "outside the displayed timeline window — not read": a decade timeline that cannot read childhood defeats its own premise, even though `mahadasha_timeline` covers 140 years.

**ADD.** A whole-life mode: MD lords + leans per decade are derivable from the full timeline without the windowed expansion (bhukti-level detail can stay windowed).
**MODIFY.** Aggregate to best tier per area per decade, or suffix the MD ("H1 par excellence in Sun MD; limited in Venus MD").
**UX.** Chips work well on the interactive page. **Priority: MEDIUM.**

## 4. Current transits (Gochara) with Vedha

**What it does.** `primitives/transits.py` — station-from-Moon table, per-planet Vedha with exempt pairs, BAV bindus + Raman's proportion (ASP-13:280-282), Kakshya micro-transit (ASP-13:459-474), NET column; `gochara_timeline` computes ALL slow-mover segments; `sade_sati()` computes the phase.

**VERDICT.** *Doctrine:* the three-layer pairing (station + vedha + bindus) is all present — but only as **columns**. Raman's transit paragraphs are synthesis sentences ("Jupiter in the 5th from the Moon, favourable, well supported at 7 bindus, yet Mars obstructs by vedha — the good is withheld"); here the reader must join five columns to reach what the `net` column silently concluded. Bigger gap: **the markdown renders only the FAVOURABLE windows** ("Favourable transit windows 2016-2046") while `gochara_timeline` computes every segment — the adverse spans, including the entirety of **Sade-Sati**, are computed and invisible in text. Sade-Sati itself appears exactly once in the whole report, as an undated chip in Chart signature ("Sade-Sati: peak (over the Moon)") — no start, no end, no phases. The CLAUDE.md absence-note ("no Sade-Sati × Moon doctrine — none invented") bars invented intensity doctrine, but Saturn-in-12/1/2-from-Moon *dates* are plain Gochara arithmetic already in `_GOCHARA_GOOD`/`sade_sati()` — showing them adds no doctrine. *Reader:* someone in peak Sade-Sati (this native!) deserves to find when it ends.

**ADD.** (a) One deterministic synthesis sentence per snapshot row. (b) A Sade-Sati window strip: the three phase spans with dates, labeled method-only; likewise name Ashtama Shani when Saturn's segment sits 8th from Moon (flag the naming's HPA cite for corpus verification). (c) An "adverse windows" table (or full segment table) mirroring the favourable one — arguably owed under Report Completeness since the data is computed.
**MODIFY.** Nothing.
**UX.** The interactive from-Moon grid and outlook lanes are excellent; markdown lags them. **Priority: HIGH.**

## 5. Dasha × Transit confluence

**What it does.** `_dasha_transit_confluences` (detailed_report.py:999-1030) intersects bhukti bounds with the period-lord's own favourable Gochara segments; HTJAH-II:4679-4687 framing ("transit only delivers what the period permits"); honest note that fast-lord periods have no rows.

**VERDICT.** *Doctrine:* the framing is Raman's, and the honesty note is exemplary. But the check is **one-sided by construction**: `if not seg.gochara_good: continue` — the equally Raman-readable inverse (the running period's own lord transiting adversely, e.g. the current Sun MD while Saturn sits on the Moon) is never surfaced. Raman's blending doctrine (HPA-34:369-381, quoted by Life-chapters itself) blends obstruction too, not only reinforcement. *Reader:* a table of only good news teaches readers to skip it.

**ADD.** Adverse-confluence rows (period lord in an adverse station during its own period), same coarse sampling honesty, method-only framing. **MODIFY.** Nothing. **UX.** Fine. **Priority: MEDIUM-HIGH** (small code delta, real doctrinal balance).

## 6. Today for you (Muhurtha)

**What it does.** Walled electional subsystem (`app/raman_saab/electional/`): Tarabala/Chandrabala from the native's own janma star/rasi, five limbs, Panchaka with per-act exception (MUHURTHA-3:157-168), ASP ch.XV transit-band elections against the native's BAV, Rahu Kalam/Durmuhurtha as local ISO times; hard-fail ordering per MUHURTHA-10:226-228. Interactive-only, on demand.

**VERDICT.** *Doctrine:* a faithful essentials implementation of Raman's *Muhurtha*, correctly walled. *Reader:* actionable within method-only framing — "the day scores 5 of 8; Rahu Kalam 13:30-15:00" tells a reader when *not* to schedule without predicting anything. But it answers "how is noon today?" when the electional question is "**when today** is clean?" — `evaluate_moment` is single-moment and the reader must re-query hour by hour.

**ADD.** (a) A scan-the-day mode: evaluate the day at interval samples, return the clean spans ranked by essentials score with each span's failing/passing factors — pure iteration over the existing scorer, no new doctrine. (b) A one-line pointer in the markdown/standalone report that this surface exists (currently a markdown reader never learns of it). (c) Optional: a Tarabala month-calendar ("your favourable stars ahead") — same `tarabala()` looped over dates.
**MODIFY.** Nothing. **UX.** The act-selector panel is good. **Priority: MEDIUM.**

## 7. Divisional deep-reads (Shodasavarga)

**What it does.** Fifteen labeled blocks: matter vargas (D-9/10/7/12/2/3/4/30/16/20/24) each read "Raman core authoritative + varga overlay corroborating" with an explicit verdict; D-27/40/45/60 as generic strength/character reads. Renderers: `render_navamsa/dasamsa/saptamsa/...`, `render_general_varga.py`, plus `render_varga.py` for the separate varga-judge report.

**VERDICT.** *Doctrine:* the matter vargas genuinely ARE read for their own domain with a verdict, and the authoritative/corroborating split is doctrinally exemplary (D-7's note on classical shorthand for degrees of difficulty is model honesty). Two gaps: (a) **D-27/D-40/D-45/D-60 name a domain in the header and never speak to it** — the body is lagna + strong/weak lists with no domain sentence, exactly the "described generically" failure mode; (b) no varga×dasha linkage anywhere (acceptable — MD-condition already reads the lord's navamsa; low priority). Cosmetic but visible: "the **2th** house", "3th", "4th" ordinals throughout the matter-varga blocks. *Reader:* ~330 lines of preformatted ASCII in markdown; on the interactive page the collapsed `<details>` summaries show the first 110 chars — which is always the citation preamble, never the verdict, so the collapsed view is unscannable.

**ADD.** One domain-verdict sentence for D-27/40/45/60 tying the lagna-lord condition to the domain word, with the existing HPA-11 cites.
**MODIFY.** Put the verdict in the details summary ("D-10 Career (Dasamsa) — FAVOURABLE"); fix "2th/3th/4th".
**UX.** Verdict-first summaries convert this from a wall into an index. **Priority: MEDIUM-HIGH** (the summary fix is nearly free).

## 8. Jaimini Karakamsa + Soul & destiny + Karmic evolution

**What it does.** `jaimini_reading.py` (karakamsa occupants → JS 1.2 Su.14-22), the soul reading (Parashari core authoritative; Jaimini overlay with all 12 houses-from-Karakamsa, chara karakas per the locked 7-karaka scheme, Arudha, Upapada, Ishta-Devata; nakshatra signature provenance-tagged), `karmic_evolution.py` (AK + Karakamssa + Upapada + JAIMINI-9:799-847 verbatim + D-20/D-60 cores).

**VERDICT.** *Doctrine:* the 7-karaka lock is honored; provenance tagging is meticulous. Three gaps. (a) **Chara dasha is orphaned**: the sequence prints undated — "Virgo(2y) -> Leo(10y) -> …" — with no calendar dates, no current-sign marker (the Chart-signature chip separately says "Chara dasha Aries"), and no pairing with the karakamsa reading, whereas *Studies in Jaimini* reads karakamsa indications **through** the running chara period. Dating it is JD arithmetic on data already computed; the pairing sentence is one join (flag the exact Studies-in-Jaimini pairing passage for corpus verification — the JAIMINI lift makes it citable in this walled layer). (b) The soul overlay's note "Nodes cast the 7th aspect only in this engine (not 5/9)" sits inside a **Jaimini** overlay where the school's own aspect scheme is rasi drishti (`primitives/rasi_drishti.py` exists and is unused here) — flag for doctrine review rather than assert. (c) **Karmic evolution embeds the entire D-20 and D-60 ASCII blocks verbatim as its "cores"** — duplicative, unsynthesized; and when the corpus passage is unavailable the whole section silently vanishes (this run) rather than stating so, which sits badly with Report Completeness. *Reader:* the standalone "Jaimini Karakamsa" chapter is three bullets with no header context (AK, Karakamsa sign) — the reader meets sutra fragments before learning whose navamsa seat this is.

**ADD.** Dated chara-dasha table with current-sign highlight, paired one-liner to the karakamsa reading; AK/Karakamsa header line on the short chapter; a "corpus unavailable" placeholder when `passage()` fails.
**MODIFY.** Karmic evolution should re-read the D-20/D-60 domain line (one sentence each), not embed the blocks.
**UX.** The 12-houses-from-Karakamsa list is good material trapped in an ASCII block; the interactive page renders it as tagged lines — fine. **Priority: MEDIUM.**

## 9. Pitru dosha screen

**What it does.** `render_pitru.py` + the BPHS ch.83 per-verse screens: Raman's children verdict authoritative (HTJAH-I:5018), curse-yogas CLASSICAL_NONCITABLE, encoding coverage stated verse by verse (including what remains unencoded and why), sraddha remedy cited, and the superb "different layer, not a contradiction" note.

**VERDICT.** *Doctrine:* the most provenance-honest section in the whole report; nothing to fault against Raman because it never claims him beyond the one verdict. *Reader:* when nothing fires (this chart), the reader wades through five long caveat bullets to reach "(no classical ancestral-curse yoga fires)".

**ADD.** Nothing doctrinal. **MODIFY.** Lead with the finding; keep the caveat bullets after it (interactive already collapses them). **UX.** Minor reorder. **Priority: LOW.**

---

# Top-5 moves for this group

1. **Narrate the tier's mechanism, and render the delivery quality you already compute** (Life-narrative). Role-preserving `timer_set` → per-house influence-basis tags (HTJAH-I:1586-1596); surface `lord_quality` md/antar tags in markdown (currently computed and dropped — a Report-Completeness repair, and the only licensed antidote to par-excellence flooding).
2. **A "this year" lens + Pratyantar drill-down.** Per-year digest joining MD/AD(/PD), lean, Kakshya interval, and transit windows touching that year — all pure joins of existing rows; render `pratyantars()` for the current bhukti (HTJAH-II:668-702). Timing is where readers return; today they must join five tables by eye.
3. **Show the adverse half of the sky.** Sade-Sati phase windows with dates (data already inside `gochara_timeline` + `sade_sati()`), adverse transit-window table, adverse dasha×transit confluences (drop the `gochara_good`-only filter's one-sidedness), and a per-row Gochara synthesis sentence. All method-only, no invented doctrine, consistent with the recorded Sade-Sati absence-finding.
4. **Divisional verdict-first.** Verdicts in the collapsed summaries, a domain sentence for D-27/40/45/60, ordinal typo fix; karmic evolution re-reads the D-20/D-60 domain lines instead of embedding blocks.
5. **Marry Chara dasha to the Karakamsa** (Studies-in-Jaimini pairing; corpus-verify the passage): dated sequence, current-sign highlight, one pairing sentence — plus the nodal-MD dispositor sentence in Life-chapters (HTJAH-I:2764/8566), which also fixes the dangling "Rahu is a neutral for this Lagna: ." blemish.

Small defects noticed en route (all in rendered output): empty antidote quote line `— "" (HPA-14:232)` when the corpus is absent (arishta section); decade chips duplicating an area at two tiers; "2th/3th/4th"; Rahu chapter's dangling clause; Karmic-evolution section silently absent without corpus.

Key files: /home/user/astro/app/raman_saab/primitives/vimshottari.py, /home/user/astro/app/raman_saab/detailed_report.py (renderers ~3517-3640, life-chapters 2016-2168, confluences 999-1030), /home/user/astro/app/raman_saab/life_arc.py, /home/user/astro/app/raman_saab/reading_timeline.py, /home/user/astro/app/raman_saab/primitives/transits.py, /home/user/astro/app/raman_saab/electional/window_scorer.py + /home/user/astro/app/api/electional_routes.py, /home/user/astro/app/raman_saab/karmic_evolution.py, /home/user/astro/app/raman_saab/primitives/jaimini_reading.py, /home/user/astro/app/raman_saab/primitives/chara_dasha.py, /home/user/astro/app/medini/templates/report.html (lifePanel 1100-1180, muhurtha 1753-1820, timing folio 2470-2560).
