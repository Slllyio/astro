# astro — project conventions for Claude

This file is loaded into every Claude Code session in this repo. It captures
**locked-in decisions** that should not be relitigated and **conventions that
shape the right way to add code here.** Update sparingly; this is the
team-shared brain.

## ★ PRIME DIRECTIVE — the North Star (never forget this)

**The one aim: build the truest, most accurate Vedic-astrology engine ever encoded
to Sri B. V. Raman's system.** Everything else — architecture, speed, product
polish — is subordinate to *fidelity to Raman's siddhanta*.

We are building this as a **fresh unified engine** (see `unified_engine/`, kept
local). Because it is fresh, we take **every step and process required** for maximal
truth and accuracy to Raman — no shortcuts that trade doctrinal correctness for
convenience:

- **Doctrine first.** Every rule, verdict, dignity, aspect, dasha, and longevity
  judgment must trace to Raman's own texts (*How to Judge a Horoscope* Vol I & II,
  *Hindu Predictive Astrology*, *Three Hundred Combinations*, *Studies in Jaimini*)
  with a verbatim citation. If Raman and another authority disagree, **Raman wins.**
- **Verify against Raman, never against engine self-output.** Pin accuracy on his
  own published worked nativities (e.g. the Mainpuri chart) and printed verdicts.
- **No silent approximation.** Where a technique has variants, encode the one Raman
  taught, name it, and cite it; document any deliberate omission.
- **Measure honestly.** Distinguish textbook fidelity from real-outcome
  generalization; report both; overfitting to worked examples is not accuracy.
- **Take all the steps.** Full ephemeris precision, full doctrine coverage, adversarial
  validation, regression guardrails — completeness over expedience, always.

This directive overrides expedience. When in doubt, choose the path that makes the
engine *more faithful to B. V. Raman*.

### ★★ MEASURED TRUTH (2026-07-24) — the directive's own verdict, binding on all future sessions

The directive was carried out in full, and then honored to its last clause ("measure honestly;
report both"). The results are settled and MUST NOT be re-litigated by re-running what is closed:

- **Textbook fidelity — the "88.4% ceiling" was a CEILING ON A SELECTED POOL. Corrected
  2026-08-23, user-signed; read this before quoting any fidelity figure.** The 259/293 = 88.4%
  below was measured honestly *within its pool*, and the five ceiling proofs still stand *for
  that pool* — but the pool itself could only ever admit verdicts the engine already agreed
  with, because old playbook rule 7 confirmed engine-MATCHES from the DRAFT queue and left
  mismatches parked. The gate was removed and the ENTIRE adjudicable DRAFT queue (94 rows) was
  then reviewed by four parallel engine-blind `bphs-doctrine-reviewer` agents against Raman's
  printed text — 59 CONFIRM, 17 REVISE, 18 REJECT.
- **★ CURRENT FIGURE (2026-10-24, after the NAVAMSA ONE-STEP RULE — quote this one): 269/389 = 69.2%
  exact, 354/389 = 91.0% within one step, 35 real errors. User decisions the same day: R2 re-scoped ten rules to their citations (277/350/39, prereg Addendum 8), then the Navamsa was limited to moving a Rasi verdict one step, as Raman does (`house_template.NAVAMSA_ONE_STEP`, `NAVAMSA_STEP_FINDINGS_2026-10-24.md`; the old clause-2 flip had no citation). FIRST OUT-OF-SAMPLE FIGURE: a sealed
  hold-out of 36 unseen Raman conclusions (3HC charts) scores 23/36 = 63.9% exact, 28/36 = 77.8%
  within one, 8 inversions (22%). SECOND HOLD-OUT (2026-10-24, 134 unseen conclusions from NH Nos. 1-15 and HTJAH I/II): 55/134 = 41.0% exact, 98/134 = 73.1% within one, 36 real errors (27%); the engine over-calls affliction (`HOLDOUT2_RESULTS_2026-10-24.md`). Quote the in-pool and hold-out figures together.** Two engine-blind reviewers corrected 23 labels
  (15 "mixed" rows were one-sided, 7 had no conclusion and left the pool). Five pre-registered
  engine fixes (R1-R5) were measured; none passed in-pool; R2 and R5 passed hold-out 2 and the user shipped R2 only (R4 dropped, R5 held). Record:
  `docs/raman_saab/FIDELITY_FIXES_PREREG.md` (addenda 1-4) and `WHY_273_OF_396.md`.
- Previous figure (2026-10-24, after the chart-fidelity fix): 273/396 = 68.9%
  exact, 363/396 = 91.7% within one ordinal step, 33 real errors (distance ≥ 2). It fell from
  276/366/30 because 8 HTJAH-I charts had been cast with a Lagna Raman never judged; re-timed to his
  Lagna, three former matches became inversions (REAL_ERRORS_2026-10-23.md addendum). No judge code changed. Lineage and the
  per-step measurements: `golden_accuracy_baseline.json` `_comment`; the 30 rows, pinned by key:
  its `real_errors` + `docs/raman_saab/REAL_ERRORS_2026-10-23.md`. Two of the 2026-10-23 steps were user
  decisions: the Bhava Bala pillar no longer votes (`house_template.BHAVA_BALA_PILLAR_VOTES`) and
  the Raman engine defaults to Raman's ayanamsa. The figures below are the history.
- **★ THE HONEST FIGURE (2026-08-23 adjudication): 269/381 = 70.6% exact, 329/381 = 86.4%
  within one ordinal step, 52 real errors (distance ≥ 2).** Nothing regressed in the engine
  between 88.8% and 70.6% — not one line of judge or doctrine code changed. The old number
  measured a pool that could only admit verdicts the engine already agreed with; this measures
  every conclusion Raman actually reached, hit or miss. Full record: DOCTRINE_BACKLOG
  "AUDIT + CONFIRMATION-RULE AMENDMENT" and "FULL ADJUDICATION".
  - Rejected rows (18) stay DRAFT and unscored: they are observations about a single factor, or
    prose corrupted by a footnote/section-heading splice — they were never Raman verdicts.
  - One row is HELD unscored (NH.chart_38 H9) because two independent reviewers graded it
    differently. **A contested label never enters the scored pool**; reviewer disagreement is
    evidence the label is genuinely contestable, not something to average away.
  - Historic (selected-pool) figure, retained because the ceiling analysis references it:
    259/293 = 88.4% exact, 283/293 = 96.6% within-1, externally verified casting (96.7%
    ascendant agreement with AstroDatabank). Five independent methods proved that pool's ceiling
    could not be faithfully exceeded (placement harvest exhausted, karaka frames over-fire,
    tuner null on 5x data, no clean cited-fix patterns, ML on the same features loses to the
    hand-tuned judge). **Those findings are about the JUDGE and remain binding: do not chase
    accuracy by tuning; it is not there without overfitting.** What changed is the DENOMINATOR,
    not the judge.
  - **STALE, do not act on it: "the 10 remaining dist-2 errors are ONE mechanism at a proven
    local optimum".** That described the selected pool. The real error surface is **52 rows**:
    26 favourable-where-Raman-says-afflicted, 16 the reverse, 9 engine ABSTENTIONS
    (insufficient-evidence, scored distance 2 by the deliberate `_ordinal_distance` convention),
    1 mixed. Concentrated in H5 (9), H4 (7), H1/H2/H10 (6 each). The one-mechanism diagnosis has
    NOT been re-derived against these 52 and must not be assumed to generalise — the nine
    abstentions in particular are a different failure from a wrong grade, and were invisible
    before. Re-derive before designing any fix.
  - **Read the two fidelity axes side by side, never just the strict one.** The strict figure
    moved DOWN 261→259 on 2026-08-03 — deliberately, user-signed-off — when the B1 dominant-factor
    guard was enabled (`house_template.B1_DOMINANT_FACTOR_GUARD`). It bought within-1 281→283 and
    cut REAL errors (distance ≥ 2, i.e. favourable↔afflicted inversions) **12 → 10**. A strict
    miss that is one ordinal step out is a contestable boundary call; an inversion is the engine
    saying the opposite of Raman. Trading 2 of the second for 2 of the first is a fidelity GAIN,
    and the ceiling claim is untouched — it was never beaten, only re-traded. Full measurement
    and the per-chart diff: `DOCTRINE_BACKLOG` B1 + `tests/fixtures/golden_accuracy_baseline.json`.
- **Real-outcome generalization: NULL — measured, not assumed.** 22,177 verified charts, 47k dated
  events, pre-registered, sham-gated, controls valid in both directions: engine verdicts, raw rule
  evidence, the 91 classical conditionals, dasha/maraka timing, and the doctrine's own primitives
  tested directly (Kuja dosha OR 1.09; Moon-Saturn OR 1.13) — all null. One thread remains
  suggestive-unconfirmed (suicide → afflicted 8th: 0.535 exploratory, 0.528 held-out, p=.062,
  underpowered; `confirmatory_study.py` is pre-registered and waiting if ~500 new cases arrive).
- **The mechanism is measured**: the median chart carries 19 afflicted AND 31 favourable
  significations simultaneously (97.1% of charts offer both poles at all times) — indications
  abundant enough to explain any life are non-differential and cannot predict one. Raman's books
  validate at 89% because they are a curated gallery of agreement (his charts are astronomically
  ordinary — rule fire-rates identical to the population).
- **What the engine IS**: a faithful scholarly instrument answering "what would Raman say"
  (legitimate, preserved, ratcheted) + the population-calibration overlay that makes every reading
  disclose its own information content — NOT a validated predictor of lives, and it must never be
  presented as one.
- Canonical records: `docs/raman_saab/REAL_OUTCOME_GENERALIZATION.md` (that it fails),
  `WHY_THE_ENGINE_FAILS_ON_REAL_CHARTS.md` (why — two levels), `FAILURE_ATLAS.md` (where, per
  case). Guards: the golden ratchet (fidelity) + `test_astrobank_ratchet.py` (generalization
  floors). The two axes are reported side by side, never averaged.

### ★★★ NORTH STAR PLAYBOOK (2026-08-23) — how fidelity actually moves; binding on all future sessions

Distilled from the all-houses dead-rule sweep (12 house passes, 19 rules shipped, 6 held by
proof, the first strict-ratchet gain since the measured ceiling: 259→260 via H2.C.40). Every
rule below was EARNED by a caught mistake, with the receipts in `DOCTRINE_BACKLOG.md`:

1. **"Best in the world" = most faithful to Raman + most honest about what a reading can
   claim.** Those are the only two axes. Real-outcome "accuracy" is measured NULL and is not
   a target — chasing it is overfitting, forbidden by `astrobank/METHODOLOGY.md`.
2. **Citation first, always.** Real-people data may only PRIORITIZE where to look or satisfy
   a pre-registered gate — never justify a change. And a pre-registered fix can still be
   refuted by its own citation's conditions (the Tier-3 bhava-rescue was: gate met, fix
   refuted twice — that outcome is a SUCCESS of the process, record it and stop).
3. **Measure BEFORE doctrine review, review BEFORE ship.** Per rule: (a) firing rate over the
   Track-B goldens; (b) whether any firing chart carries a scored expectation for that house;
   (c) co-fire against live rules sharing a conjunct; (d) SATISFIABILITY BY ENUMERATION for
   any predicate built from lagna-fixed lordship + fixed pair-tables (H11.C.6/7) or a derived
   point's reachable set (H2.C.46's parity proof — Arudha offsets are always even).
4. **A green ratchet proves NO REGRESSION, never correctness.** Three documented blindness
   modes: corroboration-only firing, evidence-redundancy on AFFLICTION_MATTER keys,
   coverage gaps (no scored chart fires the rule). A ratchet GAIN is banked only after
   adversarial review of the responsible rule (H2.C.40's 52% rate got an enumeration before
   the baseline bump).
5. **An honest hold beats a forced ship.** Every hold gets a backlog entry with its re-open
   path. A faithful predicate can still be wrong to FIRE given the verdict machinery around
   it (H1.N.38 reproduced the exact chart_33 contradiction its sibling's deferral note
   predicted). Deferral notes are design decisions — read WHY a rule is descriptive before
   assuming the TODO is stale.
6. **Stale-TODO audits are the cheapest fidelity lever.** Primitives ship after rules are
   deferred and nobody revisits (maraka/arudha/dispositor/effective_strength all unlocked
   rules years-of-sessions later). When sweeping: reuse the B1/B2 measures ONLY in the
   statistical context they were tuned for (H12.C.D6 died on exactly this).
7. **The accuracy lever now is the GOLDEN CORPUS, not the judge.** Extract remaining worked
   charts and let the denominator grow. The judge's remaining dist-2 errors are ONE mechanism
   (the pillar-preponderance clause) at a PROVEN local optimum — a new mechanism is design
   work, not tuning (sweep table in DOCTRINE_BACKLOG).
   - **★ CONFIRMATION RULE — AMENDED 2026-08-23, user-signed. The old wording said "confirm
     engine-matches from DRAFTs (never confirm mismatches to pad)". The parenthesis was right;
     the main clause was a ONE-WAY GATE and it was quietly corrupting the measurement.** Under
     it a DRAFT could enter the scored pool only by agreeing with the engine, so the ratchet
     could climb and never fall, and genuine Raman conclusions the engine gets WRONG stayed
     parked in DRAFT forever, invisible to the number. Audit evidence: an engine-blind reviewer
     read 16 sampled drafts against Raman's printed text and found 14 salvageable, among them
     six REAL engine misses (Roosevelt's career, the Gaekwar's children, Bose's speech) — all
     of which the old rule would have excluded by construction.
   - **The rule is now: confirm whatever Raman actually CONCLUDED, regardless of whether the
     engine agrees.** A confirmed miss is worth exactly as much as a confirmed hit; both are
     measurement. Never confirm to pad, and never withhold to protect the number.
   - **The confirmable unit is Raman's CONCLUSION about a matter, never an OBSERVATION about
     one contributing factor.** "The native lost his mother very early" is a conclusion;
     "the Lagna is weak, being occupied by debilitated Mars" is a factor Raman is still
     weighing, and confirming it as a house verdict blames the engine for disagreeing with
     something that was never a verdict. This distinction is the whole of the review job.
   - Expect the honest figure to FALL when the DRAFT queue is adjudicated (projection at
     amendment time: ~70-75% exact vs the then-current 88.8%). That is the measurement becoming
     truthful, not the engine regressing — the same standard already applied when real-outcome
     generalization was reported NULL. Re-base the baseline deliberately, with lineage.
8. **Grow the private real-outcome set** (`data/private/real_outcomes.json`, guarded by
   `.githooks/pre-commit`): owner-confirmed facts only, floors measured-then-locked, misses
   recorded honestly (never fudged). It is the only ground-truth instrument the project
   fully controls.

## Project shape

- Python **3.12** primary interpreter (`py -3.12` on Windows, `.venv/Scripts/python.exe` for the local venv).
- **FastAPI** application at `app/main.py` with three router groups (auth, chart+profile, medini) + a vendored **Flask** portal mounted at `/portal/*` (NumeroAstro).
- **SQLAlchemy 2.0 async** ORM, `aiosqlite` for dev (WAL mode), `asyncpg` for prod via `DATABASE_URL`.
- In-process **asyncio daemon** started in FastAPI lifespan (NOT Celery).
- **Pytest** for tests (`pythonpath = ["."]`, `asyncio_mode = "auto"`) — 48+ test files, coverage gate 80% in CI.
- ETL/ML pipeline lives under `app/medini/etl/` (31 scripts) and `app/medini/ml/` (44 scripts), all CLI-invoked via `python -m app.medini.<...>`.
- Data outputs flow to `data/` (gitignored) and `app/medini/data/*.parquet` (kept).

## Locked astrology-domain conventions — do NOT change

| Rule | Why |
|---|---|
| **Lahiri sidereal ayanamsa** for Vedic calculations — EXCEPT the Raman engine (`app/raman_saab`), whose reports, CLI and API default to **Raman's ayanamsa** (Lahiri still selectable) | Not tropical, not KP. Raman-engine exception = USER DECISION 2026-10-23 (engine audit): fidelity is measured with Raman's ayanamsa (the golden harness pins it), and Raman vs Lahiri changed ~24% of sub-matter verdicts, so a Lahiri default meant users got readings whose fidelity was never measured. Canonical-chart tests pinned to Lahiri-based external sources pass `ayanamsa="lahiri"` explicitly. |
| `DAYS_PER_VEDIC_YEAR = 365.2425` for Vimshottari math | Gregorian mean year; 365.25 (Julian) drifts ~5 days over a 19-yr Saturn MD. |
| **Whole-sign Vedic aspects (drishti)** | Conjunction/opposition fire by sign membership; orb only sets `is_exact=True`. |
| **Circular orb distance**: `min(diff, 360 - diff)` where `diff = abs(lon1 - lon2) % 360` | Naive `abs()` silently fails at the 359°/2° Pisces/Aries cusp. |
| **Floor division for nakshatra cusps**: `int(moon_lon // nak_span)` | Differs from `/` cast-to-int at exact boundaries (e.g. `40.0`). |
| **JD arithmetic for calendar dates** — never `datetime.timedelta` | Use `birth_jd ± years * 365.2425` then `swe.revjul(jd, swe.GREG_CAL)`. |
| **Rahu/Ketu drishti: Raman engine (`app/raman_saab`) = 7th ONLY**; legacy `app/core` = Jupiter-style 5/9 (modern Sukra Nadi) | User decision 2026-10-13: "follow Raman only, even for Rahu/Ketu aspects." Raman's aspect chapter (HPA-8) is silent on the nodes, but his own judgments count their 7th aspect (HTJAH-I:2062 "Lagna is occupied by Ketu and aspected by Rahu") and never a 5th/9th. The old wording "Raman = no nodal drishti" was wrong. |
| **Avastha benefics**: Jupiter, Venus, Mercury, Moon. **Malefics**: Sun, Mars, Saturn, Rahu, Ketu. | |
| **Astrocartography in EQUATORIAL** (`FLG_EQUATORIAL`) | Ayanamsa doesn't enter line geometry. |
| **Chara Karakas: strict 7-karaka Jaimini, NO Rahu/Ketu** | Rahu/Ketu are chayagrahas and cannot signify the soul or any karaka role. AK can NEVER be Rahu or Ketu. Use only the 7 visible planets (Sun..Saturn) ranked by degree-within-sign descending. The 8-karaka extension (Rahu degree-inverted as PK2_PutraKaraka2) is a Narasimha-Rao modern-minority interpretation that the project doctrinally rejects per BV Raman / Sanjay Rath / Jaimini Sutras strict reading. **Locked 2026-06-01 after a real reading error.** |
| **Dasha/bhukti house-activation = Raman's "When Do Indications Fructify?" method (HTJAH-I ch.1)** | **USER DECISION 2026-10-24 (timing gap check, all 16 fixes) — the timer set follows Raman's PRINTED per-house lists.** A planet INFLUENCES a house if it owns, occupies, or aspects **the house OR its lord**: house-lord, occupants, aspecters, planets aspecting the lord, planets conjoining the lord (HTJAH-I:1586-1589), plus **the lord counted from the Moon from the 2nd house on only** (H1's list prints none; H3 by Raman's "general principles", HTJAH-I:3521-3522), plus **a karaka ONLY where he prints one** (`vimshottari.TIMER_KARAKA`): H3 Mars + its associates/aspecters (HTJAH-I:3526), H4 Moon, H5 Jupiter, H6 Mars, H7 Venus, **H9 the Sun, not Jupiter** (HTJAH-I:12737-12738), H12 Saturn; **none for H1, H2, H10, H11** (and H8 prints no list, HTJAH-I:10316). **Nodes join through all four channels**: dispositor, a conjoined planet, nakshatra lord, and Sanivad Rahu / Kujavad Ketu (HTJAH-I:8566-8567, 4513-4520, 11194-11203). Do NOT narrow it to own/occupy/aspect only, and do not re-add an unprinted karaka. **Grading is a four-tier scheme, UNIFORM for all 12 houses** (HTJAH-I:1588-1589, 2617, 3522, 4333, 8294, 16435 — "the general principles… hold equally good"): both MD & AD lord influence the house **and AD lord is _associated_ (conjunct / mutual aspect) with the MD lord → par excellence**; both influence but AD **not** associated → **ordinary**; **only the bhukti (AD) lord influences → limited**; **only the MD lord influences → feeble** (HTJAH-I:1592-1596, 1635-1640; 2588-2599; recurs 16404 / 17746). **Graded on the house's OWN set** (fix 3): the 2/11 and 9/12 allied houses are a separately labelled `allied_via` note, never part of the grade; the MD lord's own bhukti is **"same lord"** (Raman's association test is for "the sub-period of another", HTJAH-I:1635). NOT a Shadbala "supersession" (a wrong guess, reverted). Encoded in `vimshottari.timer_set`/`timer_roles`, `period_tier`, `bhukti_tier` + `lords_associated`; surfaced in `detailed_report`. Locked 2026-07-25 after re-deriving it from the source; revised 2026-10-24 by the user decision above (record: `DOCTRINE_BACKLOG.md` "TIMING GAP CHECK"). |

## Locked architecture decisions — do NOT change

- `extra="forbid"` on Settings — kwargs typos fail loudly.
- `asyncio.to_thread` for CPU-bound ephemeris calls in async route handlers.
- `yield_per` streaming in `process_natal_charts` to bound memory.
- `Account` keyed on `google_sub` (NOT email — email can change).
- Per-account rate limiting via `slowapi` with JWT-aware key function.
- **Tab 3 (Medini)**: Leaflet + OSM (NOT Mapbox), axis-aligned bbox tiling (NOT PostGIS), safe DOM construction (`createElement` + `textContent`, never innerHTML).
- Single source of truth for Kurma GeoJSON: `/medini/regions` is consumed by both the educational widget and the personalized cartography page.
- **PRASNA + MUHURTHA + VARSHA firewalls LIFTED (user decisions 2026-08-03)**: horary (`app/raman_saab/horary/`) and electional (`app/raman_saab/electional/`) are walled subsystems — they may import natal primitives, natal verdict code NEVER imports them (tested both directions); their sources (PRASNA/MUHURTHA/VARSHA tags, + HPA-27/AFB-11/ASP-15:21-183 content) are citable by those subsystems only; outputs carry Measured-Truth framing; death/lifespan queries excluded in code. **JAIMINI lifted 2026-08-04** (karmic-evolution layer) — **NO book remains firewalled; the content-scope rule is now the ONLY wall**: each lifted book is citable by its own walled subsystem, natal verdict code imports none of them, and the golden ratchet is untouchable by construction. Full record: `DOCTRINE_BACKLOG.md` "PRASNA + MUHURTHA firewall LIFT" + the Jaimini addendum.
- **THREE 3HC-COMPLETION DECISIONS (user-approved 2026-08-11, "do all three")**, each with
  its record in the code: (1) **D60 cruel/benign class** = Phaladeepika ch.3's Krura table
  (classical corroboration; `primitives/shashtiamsa.py` — CONSISTENCY-GATED, test-pinned, on
  Raman's three applied rulings, which always win over the table); (2) **the two-ladder
  finding**: Raman's GBB amsa ladder (Parvathamsa-3/Gopuramsam-8, shodasavarga) and 3HC's
  ladder (Uttama-3/Gopura-4, SAPTAVARGA — the unique set reproducing both of Raman's worked
  counts, incl. Chart 125 cast from its printed birth data) are DIFFERENT LADDERS; each is
  citable only for its own book's yogas (`varga_attainment.THREE_HUNDRED_LADDER`; the
  Sumukha-167 arm was fixed for borrowing GBB's rung); (3) **Gulika/Mandi natal scope**: the
  engine's own HPA-cited upagraha layer (`chart/upagrahas.py`) serves natal yoga conditions
  via `chart.upagrahas` — the Prasna Marga wall was never about these mechanics. With these,
  **the 3HC far half (163-300) is FULLY encoded or consciously deferred**; the registry's
  skip notes are the per-arm authority.
- **SALIENCE: every modulation weight is ZERO, and that is a MEASURED RESULT, not a stub**
  (`app/raman_saab/salience.py`, locked 2026-08-07). Eight chart-specific signals — surprisal,
  extremity, graph centrality, occupancy, dignity, house-lord shadbala, lord-strength deviation,
  yoga-by-kind — were ablated across two independent benchmarks at n=14 and n=95, and **none
  beat the doctrinal prior alone**. Raman's attention follows doctrine and nothing else the
  engine computes (`docs/raman_saab/SALIENCE_BASELINE.md`). The consequence to know before
  editing: with the weights at zero, `house_salience` returns the SAME ranking for every chart
  — `(1, 10, 7, 9, 4, 5, 2, 11, 8, 12, 6, 3)` — and that order drives the digest, the most-read
  section of the report. `tests/raman_saab/test_salience.py` pins the weights, the constancy,
  the hand-copied order AND the exact scores (an order-only test passes while a term fires too
  weakly to reorder). **Raising a weight requires clearing the prior on the HOLDOUT split,
  paired, with an interval excluding zero, recorded in SALIENCE_BASELINE.md — then update the
  test deliberately.** Ranking behaviour is otherwise frozen; `why` may only ever cite a term
  whose weight is live, `notable` carries the rest.

## ★ REPORT COMPLETENESS — do NOT omit anything (locked 2026-07-27, after a real error)

**Every report surface shows EVERYTHING the report computes. We only ADD, never remove or hide.**
This is a standing user directive, confirmed twice and once violated — treat it as inviolable:

- The interactive page (`app/medini/templates/report.html`), the standalone HTML
  (`report_html.py`), and the markdown (`to_markdown`) must each render **every field of every
  section** the report produces. If the engine computed a value, it appears in the reading.
- **No collapsing a section to a bare count** (e.g. "Ishta/Kashta outlook (18)" with the rows
  hidden). A `<details>` drill-down is fine ONLY if its summary already shows the substantive
  content or it is `open` by default; never hide data behind a click that shows only a number.
- **No dropping columns.** A generic table renderer must render nested-object / list values
  (format them), never silently skip a column because its value is not a scalar. This was the
  exact bug: `gochara.vedha_by`, `yoga_timing.quality`, the dashboard `reader`, and the
  preponderance `testimonies`/`absent` all vanished this way.
- When adding a section or field, add it to ALL renderers (append-only per the template contract).
- If a value is genuinely not meaningful to show, that is a product decision for the USER to make
  — surface it and ask; do not drop it unilaterally.
- **ADDING is always welcome; REMOVING is not.** Data-visualizations, charts (rasi/navamsa/gochara
  grids, dasha-period timelines, goodness strips, strength bars, heatmaps), derived summaries, and
  new interactive views are encouraged — but they SUPPLEMENT the full data tables/prose, they never
  replace them. A chart is an *additional* lens on data that must still be present in full below it.
- Self-contained only: the interactive page builds every visual with inline SVG/Canvas/CSS via safe
  DOM (`createElement`, namespaced SVG, `textContent` — never `innerHTML`, never an external chart
  library/CDN). Theme-aware through the page's CSS custom properties (light + dark).

## ★ REPORT READING ARC — v33 movements, and the split contract (locked 2026-08-05)

**The report's section SET is frozen and append-only; its ORDER is a design decision.** These
were one invariant until v33 and conflating them is what made the document read as a pile of
sections: `test_registry_is_append_only` asserted the whole registry *prefix* as an exact
ordered tuple, so for 32 versions the only legal move was "append at the end" and each section
landed where the contract allowed rather than where it reads best.

- **`app/raman_saab/report_movements.py` is the single source of truth for the sequence.** Seven
  movements — Who this is / How to read it honestly / The instrument / The twelve fields / The
  matters of life / In time / The summing up. `SECTION_CONTRACT` and `HTML_SECTION_ORDER` are
  both DERIVED from `flattened_order()`; never restate an order anywhere else.
- **Two separate guards, both required.** `test_section_set_is_append_only` asserts SET equality
  on the 53 `(id, md_marker, html_marker)` triples (completeness — REPORT COMPLETENESS still
  stands, nothing is ever removed or hidden). `test_reading_order_is_the_reviewed_arc` asserts
  the sequence against `_ORDER_V33`, **copied BY HAND into the test file** for exactly the
  reason `_FROZEN` is: the registry derives its order from `MOVEMENTS`, so a test comparing only
  those two passes silently when both are edited together. Re-sequencing means editing that
  tuple, consciously, in the same commit.
- **Two structural constraints, test-pinned.** `nichod` stays last. `title`/`plain_reading`/
  `chart_signature` stay adjacent in that order — they are one `<header>` element in the HTML
  and are emitted as a single chunk.
- **Connective passages are deterministic**, composed from `raman_style` (`because`/`weighed`/
  `conclusion` — Raman's own compositional habits) over facts the adjacent sections have already
  judged. No model call, PREC-10 pure re-read, identical every run, and every passage is checked
  against `_FORBIDDEN_RE`. The guard is a blunt denylist and has already caught an innocent
  "brings to" here — **write around it, never widen it.**
- **Both renderers are order-driven, not position-driven.** `to_markdown` routes its appends
  through `_SectionedLines`; `to_html` assembles from a section-keyed `chunk` dict. Neither
  hard-codes sequence any more. The interactive page keeps its own manuscript folios (a
  different but coherent shape the page-turn depends on) and LAYERS the passages onto them via
  the `movements` key in the report JSON.
- **Tests must not slice content to a hardcoded neighbouring section** — that encodes order into
  assertions about content, and a neighbour moving ahead yields an empty slice that fails
  against `""`. Use the `section_text` fixture in `tests/raman_saab/conftest.py`; order
  assertions belong only in `test_report_template_contract.py`.

## ★ PLAINSPOKEN — the report speaks to the reader (v35, locked 2026-08-07)

`app/raman_saab/plainspoken.py` gives each section a **person-facing lead**: one short paragraph,
above the section's own tables, that says what the section means *for the reader*. Measured
before and after — **12 of 54 sections addressed the reader at the start, 50 of 54 now.**

- **It ADDS, never replaces.** REPORT COMPLETENESS is untouched: the lead sits above the full
  data, never in place of it. PREC-10 holds — every lead re-voices a value already decided.
- **Every lead is computed from its OWN section's data**, so it cannot drift from the table it
  introduces. A lead that reads a different object than its section renders is the defect that
  shipped once: `section_id="synthesis"` renders *Integrated insights*, while `r.synthesis` is a
  different dataclass rendered under `houses`.
- **Three surfaces, always in step**: markdown (`_plain_section`), standalone HTML
  (`_plain_lead`), interactive page (`plainLead(sid)`). A lead added to one and not the others
  is a bug.
- **Every lead must pass `_FORBIDDEN_RE`.** Write around the guard, never widen it.
- **`_join` vs `_join_all` is a correctness choice, not style.** `_join` caps at three so a lead
  never becomes an inventory; use it ONLY where the phrasing signals a selection ("among them",
  "most strongly"). Where the sentence reads as the complete set, use `_join_all`. The cap
  silently dropped Mars from a four-planet maraka list, arishta from a four-kind yoga breakdown,
  and 4 of 7 wealth channels — each in a sentence that read as exhaustive.
- **A lead must agree with what sits beside it.** `rect_confidence` led with the count surviving
  the full ±60 scan ("1 of 10") directly above its own label reading *"firm"*. Same class as a
  plain line saying "reads strongly" under a heading saying AFFLICTED.
- **Failures are swallowed but LOGGED.** A phrasing bug must never cost the reader a section, so
  `plain_for_section` catches — but silently swallowing made a crash (`_SIGN_NAME` is a tuple,
  not a dict) indistinguishable from "nothing to say" and blanked a whole lead unnoticed.
- **Four sections stay in the engine's voice deliberately**: `positions`, `glossary`,
  `info_content`, `career`. Reference apparatus; a lead there is padding.
- **Three checks, none redundant** — the guard regex, a reader-address count
  (`\byou\b|\byour\b` per section slice), and *reading the leads in document order*. The count
  caught leads that existed and addressed nobody; only reading caught the truncations, the
  contradiction, and untranslated jargon (`poorvapunya`). Run all three.
- **THE SITTING (v35, user-requested "instinct and flow", 2026-08-07)** — `sitting.py` composes
  the reading as ONE continuous piece in Raman's NH arc: the Grip (thesis, echoed by the
  closing — pinned on `grip_key`), the Cast (2-3 census-ranked grahas with EARNED epithets,
  clauses kept separately so a callback can drop the one that would be circular in its own
  house), the life told forward (matters whose house is `unsettled` are HELD APART, never
  counted either way — verdict and firmness are different axes and one continuous reading must
  honour both), and event-first timing. The weave in `plain_for_house` calls back to cast
  members ("the same Jupiter, the strongest planet…") — never circularly.
- **HEDGE CONSOLIDATION (user decision 2026-08-07, sign-off recorded):** the
  "not a prediction/never a forecast" family appears at most 8 times per reading (was 26) —
  the header frame, the nichod/life-synthesis distillation line, and the longevity/maraka
  family, where the subject demands it. Per-lead and per-row restatements were REMOVED as
  framing repetition, not data. `test_sitting.py::TestTheHedgeCensus` pins both the cap and
  that the guard trio still carries it. Do not re-add hedges to individual leads; do not
  strip the trio.

## ★ REPORT LLM SURFACES — the four-voice contract (locked 2026-07-28, share-the-app arc)

- **`/report/insights` ("read as one story") and `/report/explain` DO call the local model**
  (changed 2026-07-29, corrected here 2026-08-03 — this entry still described the older
  deterministic-only rule and cited `test_insights_and_explain_make_no_model_call`, a test that no
  longer exists; it was replaced by `test_insights_and_explain_attempt_a_model_call`, asserting the
  opposite). The deterministic-only rule was an *Anthropic cost* cut and lapsed once local serving
  became $0. Both still fall back to the engine's own ranked digest / plain prose whenever the LLM
  is disabled or unavailable, so the engine's output remains the product floor. **Latency note:**
  on the 12B these are ~15s (`/explain`) and ~25s (`/insights`) per call, up from ~7s on the 1.5B.
- **`/report/ask` is the grounded LLM voice**, served by the LOCAL backend by default
  (`REPORT_LLM_BACKEND="ollama"`, `REPORT_LLM_MODEL` — SystemPromptWrapper prepends the system
  prompt). `refusal_reason` is model-agnostic and stays the final gate; guard-fail → deterministic
  fallback, never a 500. The Anthropic backend is opt-in and must never be the default on a shared
  instance.
- **The narrative model is a STOCK 12B, not the fine-tuned 1.5B (measured 2026-08-03, locked).**
  `REPORT_LLM_MODEL` is deliberately separate from `OLLAMA_MODEL` (which stays the fast model for
  high-frequency paths). Head-to-head on 34 genuinely held-out rows: citation-clean **85.3%
  (gemma4:12b, no fine-tune) vs 44.1% (astro-analyst LoRA) vs 91.2% (Claude teacher)**; guard
  88.2/73.5, crisp 70.6/47.1. The 12B wins on every axis — including the voice and crispness the
  LoRA existed to teach — for ~4s more per answer at the same $0 local cost. **The 1.5B is
  capacity-limited for citation precision across ~20 facts; corpus quality was not the constraint**
  (the same corpus's teacher rows score 91.2%). `train_llm_local.py` is PARKED, not deleted — the
  corpus builder and eval harness remain live and are what produced these numbers.
- **A reasoning model needs `REPORT_LLM_THINK=false` + `REPORT_LLM_NUM_CTX=8192`.** gemma4:12b
  advertises `thinking`; without these it spends its whole budget in the thinking channel on a
  ~3.1k-token evidence prompt and returns an EMPTY response, which surfaces as `OllamaUnavailable`
  and silently degrades EVERY answer to deterministic prose while the app still looks healthy.
- **The guard line (re-narrowed 2026-08-17, "unblock prediction part" — USER DECISION):** the
  boundary is now **idiom, not timing**. TIMED INDICATIONS in the classical voice are ALLOWED on
  every surface ("marriage is indicated during the Venus bhukti, 2027–2028", "the maraka periods
  2031–2034 are classically sensitive", "the span reads at the purna band, around the 83rd year");
  the DECREE voice stays refused (you-will/`he/she/they will|shall <verb>`, `is going to`,
  `destined/certain/guaranteed/bound to/sure to`, `i predict`, and decree-dated death:
  "death around/at/by <year>", "will die"). The 2026-07-28 dated-indication arms
  ("indicated in 2027", "at age 30", promises/brings/foretells) were REMOVED by this decision.
  History: narrowed 2026-07-28 (doctrine-reviewed); death/lifespan wall lifted 2026-08-17 over
  the assistant's recorded recommendation to keep it — record in DOCTRINE_BACKLOG "prediction
  unblock". Do not re-widen OR re-narrow without a doctrine review + user sign-off.
  **Lesson carried from main (2026-08-07 correction):** a summary of this guard once said it
  refused "all death tokens" -- wrong, and it nearly muted the longevity/arishta/maraka leads.
  Naming longevity, maraka or arishta is ALLOWED; only the decree voice and decree-dated death
  are refused. **When this file summarises a regex, go read the regex.**
- **`/report/ai-interpret` is the ONE walled speculation surface** (user-approved exception):
  always labeled ("AI, not the engine, not validated" — `DISCLAIMER` on every response), gentle/bold
  registers, and serious-illness/self-harm excluded IN CODE (`excluded_topic` on output + input
  scrub) — no register or request lifts that. Death/lifespan tokens were LIFTED from the exclusion
  2026-08-17 (user decision, "unblock prediction part"): the panel may reflect on longevity in the
  classical indication idiom; decree-dated death phrasing remains code-refused. It has NO
  deterministic fallback: the engine must never author speculation.
- **Chart feedback** (`/report/feedback*`): questions are a deterministic re-read of the digest
  (`feedback_questions.py`), answers land in `chart_feedback` keyed by the server-built chart_key;
  anonymous-first. Wording keeps the Measured-Truth frame (calibration, not validation).
- **The own-model program**: `build_analysis_corpus.py` (teacher → curated SFT; ONLY guard-passing
  rows enter the corpus) → `train_llm_local.py` (DirectML LoRA; NO bitsandbytes; Ollama serves the
  adapter via Modelfile `ADAPTER`) → `eval_analysis_llm.py` (student vs teacher on guard pass-rate).
  Teacher backend may be Claude (paid) or a big local model via `--backend ollama` ($0) — the
  curation gate, not the teacher, guarantees corpus safety.

## Test-pinning policy

- **Canonical baseline**: Bangalore 1990-07-15 12:00 IST, lat 12.97, lon 77.59, tz +5.5.
  Produces Mercury MD, Virgo Lagna ~173.99°, Moon at Revati pada 3, Saturn Avastha = Mrita/Swapna.
- **Pin against externally-verifiable sources**, never engine self-output: Wikipedia, Prokerala, Jagannatha Hora, drikpanchang.com.
- The PDF `Geo-Astrological Planetary Intelligence Engine.pdf` is the source of truth for the Kurma Chakra 27-nakshatra → region table.

## Known-broken — do NOT rediscover these the hard way

- **Both earlier entries here are FIXED (re-checked 2026-10-23).** Pre-1906 charts now produce a
  full report (b5d21a0: the running period reads `synthesis.BEYOND_SEQUENCE` instead of
  dereferencing None; Queen Victoria 1819 renders). `plainspoken.py` has its test file
  (`tests/raman_saab/test_plainspoken.py`, 3ffca1d, the twelve defect classes pinned).
- **Book OCR corrections travel as data.** The corpus is git-ignored, so word-level OCR repairs
  live in `tools/raman_saab/ocr_corrections.json` (line-preserving, digits never touched, valid
  Sanskrit never "corrected"). On a machine with the corpus: `python -m
  tools.raman_saab.apply_ocr_corrections --apply`, then re-lock with `UPDATE_SOURCE_LOCK=1`. Until
  applied, the source lock still matches the uncorrected books. Fuzzy auto-correction was tried
  and rejected: it rewrote maraka→karaka, chidra→chandra, lagnam→lagna.

## Style conventions

- `from __future__ import annotations` at the top of every new module.
- Every CLI-invokable module has a module docstring with a `Usage:` block showing the exact `python -m` command and arg names.
- Logging via `logger = logging.getLogger(__name__)`. Avoid `print()` outside scripts.
- Type annotations on all public function signatures. Prefer `from typing import ...` over postponed-string forms beyond annotations.
- Test classes named `Test<Subject>`, methods `test_<scenario>_<expected>`, each with a one-line docstring stating the astronomical fact being verified.

## Operational

- Repo branch policy: **commit directly to `main`**. No PRs, no branch protection in v1.
- **Co-authored-by attribution is disabled globally.** Do not add `Co-Authored-By` trailers to commits.
- Commit message style: conventional (`feat(medini): …`, `fix(core): …`, `docs(medini): …`).
- CI: GitHub Actions runs `pytest --cov=app` with 80% coverage gate.

## Running the project

```powershell
# tests
py -3.12 -m pytest -q
py -3.12 -m pytest --cov=app --cov-report=term-missing -q

# live app
py -3.12 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# then visit /docs, /medini/kurma-widget, /medini/cartography/page, /portal/
```

## Where to put things

| Adding... | Goes in... | Paired test in... |
|---|---|---|
| New core engine code | `app/core/<name>.py` | `tests/test_<name>.py` |
| New API endpoint | `app/api/<group>_routes.py` | `tests/test_<name>.py` |
| New ETL stage | `app/medini/etl/<name>.py` | `tests/test_<name>.py` |
| New ML experiment | `app/medini/ml/<name>.py` | `tests/test_<name>.py` (when stateless logic is testable) |
| Throwaway exploration | `scratch_<topic>.py` at repo root — **but promote or delete before merge.** |
| New Medini doctrine source | `data/knowledge_library/` (manifest in `topics.yaml`) | — |

## Files NOT to edit blindly

- `.env`, `.env.example` — secrets.
- `data/ml_runs/**/*.parquet` — generated artifacts.
- `app/medini/data/*.parquet` — generated artifacts (rebuild via ETL).
- `Geo-Astrological Planetary Intelligence Engine.pdf` — source-of-truth reference.

The `.claude/settings.json` PreToolUse hook enforces some of this automatically.

## Custom skills, subagents, and hooks in this repo

- `.claude/skills/bphs-rule-validator/` — validate ML-discovered rules against BPHS classical doctrine.
- `.claude/skills/medini-etl-scaffold/` — scaffold a new `app/medini/etl/` module + paired test from the canonical pattern.
- `.claude/agents/bphs-doctrine-reviewer.md` — read-only reviewer for doctrine compliance.
- `.claude/agents/ml-experiment-auditor.md` — read-only reviewer for ML pitfalls (data leakage, CV, target alignment).
- `.claude/settings.json` hooks: auto-run paired tests on edit; block edits to `.env`/`data/**/*.parquet`.

Invoke a skill with `/<skill-name>`. Dispatch a subagent via the `Agent` tool with `subagent_type="bphs-doctrine-reviewer"` or `"ml-experiment-auditor"`.

## gstack (recommended)

This project uses [gstack](https://github.com/garrytan/gstack) for AI-assisted workflows.
Install it for the best experience:

```bash
git clone --depth 1 https://github.com/garrytan/gstack.git ~/.claude/skills/gstack
cd ~/.claude/skills/gstack && ./setup --team
```

Skills like /qa, /ship, /review, /investigate, and /browse become available after install.
Use /browse for all web browsing. Use ~/.claude/skills/gstack/... for gstack file paths.
