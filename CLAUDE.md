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

- **Textbook fidelity: ACHIEVED and at its proven ceiling — 259/293 = 88.4% exact and
  283/293 = 96.6% within one ordinal step** against Raman's own printed verdicts, externally
  verified casting (96.7% ascendant agreement with AstroDatabank's published placements). Five
  independent methods proved the ceiling cannot be faithfully exceeded (placement harvest
  exhausted, karaka frames over-fire, tuner null on 5x data, no clean cited-fix patterns, ML on
  the same features loses to the hand-tuned judge). **Do not chase accuracy further; it is not
  there without overfitting.**
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
| **Lahiri sidereal ayanamsa** for all Vedic calculations | Not tropical, not Raman, not KP. |
| `DAYS_PER_VEDIC_YEAR = 365.2425` for Vimshottari math | Gregorian mean year; 365.25 (Julian) drifts ~5 days over a 19-yr Saturn MD. |
| **Whole-sign Vedic aspects (drishti)** | Conjunction/opposition fire by sign membership; orb only sets `is_exact=True`. |
| **Circular orb distance**: `min(diff, 360 - diff)` where `diff = abs(lon1 - lon2) % 360` | Naive `abs()` silently fails at the 359°/2° Pisces/Aries cusp. |
| **Floor division for nakshatra cusps**: `int(moon_lon // nak_span)` | Differs from `/` cast-to-int at exact boundaries (e.g. `40.0`). |
| **JD arithmetic for calendar dates** — never `datetime.timedelta` | Use `birth_jd ± years * 365.2425` then `swe.revjul(jd, swe.GREG_CAL)`. |
| **Rahu/Ketu drishti = Jupiter-style 5/9** (modern Sukra Nadi) | Not BV Raman (no nodal drishti), not KP. |
| **Avastha benefics**: Jupiter, Venus, Mercury, Moon. **Malefics**: Sun, Mars, Saturn, Rahu, Ketu. | |
| **Astrocartography in EQUATORIAL** (`FLG_EQUATORIAL`) | Ayanamsa doesn't enter line geometry. |
| **Chara Karakas: strict 7-karaka Jaimini, NO Rahu/Ketu** | Rahu/Ketu are chayagrahas and cannot signify the soul or any karaka role. AK can NEVER be Rahu or Ketu. Use only the 7 visible planets (Sun..Saturn) ranked by degree-within-sign descending. The 8-karaka extension (Rahu degree-inverted as PK2_PutraKaraka2) is a Narasimha-Rao modern-minority interpretation that the project doctrinally rejects per BV Raman / Sanjay Rath / Jaimini Sutras strict reading. **Locked 2026-06-01 after a real reading error.** |
| **Dasha/bhukti house-activation = Raman's "When Do Indications Fructify?" method (HTJAH-I ch.1)** | A planet INFLUENCES a house if it owns, occupies, or aspects **the house OR its lord** — i.e. the five/six factors: house-lord, occupants, aspecters, planets aspecting the lord, planets conjoining the lord, and the lord-from-the-Moon (HTJAH-I:1586-1589). This is exactly the broad `timer_set` — do NOT narrow it to own/occupy/aspect only. **Grading is a four-tier scheme, UNIFORM for all 12 houses** (Raman states this repeatedly: HTJAH-I:1588-1589, 2617, 3522, 4333, 8294, 16435 — "the general principles… hold equally good"): both MD & AD lord influence the house **and AD lord is _associated_ (conjunct / mutual aspect) with the MD lord → par excellence**; both influence but AD **not** associated → **ordinary**; **only the bhukti (AD) lord influences → limited**; **only the MD lord influences → feeble** (HTJAH-I:1592-1596, 1635-1640; 2588-2599 incl. "feeble"; recurs 16404 / 17746). The method is house-agnostic; only the *inputs* (each house's own lord/karaka/occupants) differ. NOT a Shadbala "supersession" (that was a wrong guess, reverted). Encoded in `vimshottari.bhukti_tier` + `lords_associated`; surfaced in `detailed_report`. **Locked 2026-07-25 after re-deriving it from the source (this had been done before and lost).** |

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
- **The guard line (narrowed 2026-07-28, doctrine-reviewed PASS-WITH-NOTES + hardened):** undated
  descriptive-indication idiom ("points to", "tends to", "indicates", "signifies") is ALLOWED —
  it is Raman's own descriptive usage; asserting a future LIFE EVENT is refused (you-will/decree
  verbs, third-person `he/she/they will|shall <verb>`, dated/age-attached indications like
  "indicated in 2027"/"at age 30", `promises/brings/foretells/bound to/sure to`).
  Do not re-widen OR re-narrow without a doctrine review.
  **Corrected 2026-08-07 — this entry used to end "…, all death tokens", and that is wrong.**
  Read `_FORBIDDEN_RE` itself: what it refuses is the subject attached to a CLOCK —
  `end of life`, `death (around|at|by|near)`, `die (around|at|by|before|after)`,
  `will/shall die`. Naming longevity, maraka or arishta is ALLOWED; timing them is not. The
  mistaken summary cost real work: it read as "never mention it", which would have made the
  `longevity`/`arishta`/`maraka` plain leads impossible to write and left three sections
  permanently mute. **When this file summarises a regex, go read the regex.**
- **`/report/ai-interpret` is the ONE walled speculation surface** (user-approved exception):
  always labeled ("AI, not the engine, not validated" — `DISCLAIMER` on every response), gentle/bold
  registers, and death/lifespan/serious-illness/self-harm excluded IN CODE (`excluded_topic` on
  output + input scrub) — no register or request lifts that. It has NO deterministic fallback: the
  engine must never author speculation.
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

- **Pre-1906 charts crash the report.** `build_detailed_report` raises
  `AttributeError: 'NoneType' object has no attribute 'maha'` for any nativity whose 120-year
  Vimshottari span ended before today — there is no "currently running" period, and
  `synthesize()` dereferences it. Verified on Queen Victoria (1819). **This bites the Prime
  Directive directly: most of Raman's own worked nativities are 19th century, so the engine
  cannot produce a report for the charts it is validated against.** The measurement tools work
  around it with `on=(birth.year + 35, …)`; the report has no such escape. Fixing it needs a
  product decision first — what "now" means for a chart whose life ended in 1939 (cast at a date
  inside the life / cycle the sequence / state that the reference date is outside the span).
- **`app/raman_saab/plainspoken.py` has no test file** (910 lines, 41 lead functions, the layer
  with the most reader contact). Twelve defects were found in it on 2026-08-06/07 — all by
  printing output by hand, none by CI. Every class is mechanically checkable: guard-clean,
  subject-verb agreement at n=1, no truncated list in a sentence claiming completeness, no lead
  that addresses nobody, no lead contradicting its own section's label.

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
