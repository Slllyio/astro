# फलादेशः — The Whole Process & Methodology

*The reading app end-to-end: how a birth becomes a manuscript, where every word comes from,
what the AI is allowed to do, and how the system keeps itself honest. (2026-07-28)*

---

## 1. What this system is

A **deterministic Vedic-astrology engine** encoding B. V. Raman's system (89.1% exact against
his own printed verdicts), wrapped in a page-turning Pothi-manuscript web report, with a
carefully-walled AI layer on top. The engine is the sole authority; every AI surface either
translates it, or is explicitly labeled as *not* it.

```
birth details ──► Swiss Ephemeris cast (Lahiri) ──► build_detailed_report (pure function)
                                                        │
                                    21 contracted sections, every verdict cited to Raman
                                                        │
              ┌─────────────────────────────────────────┼──────────────────────────┐
              ▼                                         ▼                          ▼
      the manuscript report                    feedback questions           evidence facts
      (13 leaves, all data)                    (from the digest)            (for the LLM layer)
```

## 2. The report structure — what a reader turns through

The report is a **13-leaf palm-manuscript book** (swipe on phones, keys/clicks on desktop):

| Leaf | Folio | What it holds |
|---|---|---|
| 0 | **Cover** | फलादेशः — tap to enter |
| 1 | **Birth details** | Name, date/time, **city picker** (258 cities auto-fill lat/lon/tz), ayanamsa, presets |
| 2 | **What matters most** | The engine's ranked *Insight Digest*: convergences, the running life-chapter, top insights, the sharpest tension, what statistically distinguishes this chart — each with citations and click-to-source |
| 3 | **Signature & ruler** | Chart signature chips (lagna, karakas, panchanga…), ruler of the nativity, temperament |
| 4 | **The charts** | Rasi/Navamsa grids and companions — every placement |
| 5 | **Yogas & Ashtakavarga** | Every fired yoga with its Raman citation; bindu tables and strips |
| 6 | **Houses** | House-by-house proformas: lord, occupants, aspects, per-signification verdicts, conclusions |
| 7 | **Matters & longevity** | The twelve life-matters tiled by their divisional readers (D-2 wealth … D-30 health), longevity band |
| 8 | **Life-narrative** | Vimshottari timeline with the four-tier bhukti grading (Raman's "When do indications fructify?"), life-chapters woven as prose |
| 9 | **Transits** | Gochara with Vedha and Ashtakavarga applied, outlook panel |
| 10 | **Divisional & soul** | Shodasavarga deep-reads, soul & destiny (Jaimini), pitru dosha |
| 11 | **Insights** | Integrated cross-feature insights, "what stands out" vs the population, **information content** (the honesty disclosure), and the **walled AI panel** |
| 12 | **Nichod (colophon)** | The essence, spotlight, caution — then the **feedback card** |

**Completeness is locked doctrine:** every value the engine computes appears in the reading;
sections only ever gain content, never lose it. Every citation is clickable to Raman's verbatim
text.

## 3. The four-voice contract (who wrote each word)

| Surface | Voice | Cost | Guard |
|---|---|---|---|
| The whole report + "read as one story" + section explains | **Engine only** — deterministic, cited | $0 | is the ground truth |
| **Ask panel** (❋) | Local LLM *translating* engine facts | $0 (your GPU) | `refusal_reason`: every paragraph anchored to a [Fact N]; decree language refused → engine prose served instead |
| **AI-interpretation panel** | Local LLM *speculating* — labeled "NOT the engine, not validated" | $0 | Code-enforced wall: death, lifespan, serious illness, self-harm never discussed, in any register |
| Feedback questions | Engine (re-read of the digest) | $0 | deterministic |

**The guard line** (doctrine-reviewed): descriptive idiom — "points to", "tends to", undated
"indicates" — is Raman's own language and is *served*; asserting a future life event ("you will
marry", "indicated in 2027", "at age 30") is *refused*. The engine is never presented as a
validated predictor — because measured against 22,177 real lives, it is not one.

## 4. The feedback methodology (why the questions exist)

After the reading, up to five questions generated **from that chart's own strongest claims**
("the engine marks home & mother favourable — does that match your experience?") + one overall.
Answers land anonymously in `chart_feedback`, keyed by the birth data. This grows exactly the
dataset the project lacks: **per-claim, per-chart human calibration** — the honest measurement
of where readings meet real lives, continuing the Measured Truth program with fresh data.

## 5. The own-model pipeline (teacher → curated corpus → student)

```
person_dossier.parquet (75k charts, timed births only)
        │  deterministic stratified sample
        ▼
engine report ──► evidence facts ──► TEACHER writes the analysis
                                     (Claude API, or gemma4:12b locally for $0)
        ▼
CURATION GATE — only answers that pass refusal_reason (grounded, cited,
prediction-free) AND a quality bar (length, ≥3 anchors) enter the corpus.
The gate, not the teacher, guarantees corpus safety.
        +  B. V. Raman's own "Special Features" prose as high-weight voice anchors
        ▼
sft.jsonl ──► train_llm_local.py (LoRA on your AMD GPU, DirectML, no cloud)
        ▼
adapter → GGUF → `ollama create astro-analyst` → OLLAMA_MODEL=astro-analyst
        ▼
eval_analysis_llm.py — student vs teacher on guard pass-rate, on held-out charts
```

Measured so far: Claude teacher keep-rate **87.5%**, gemma4:12b keep-rate **100%** (of
completed calls; ~half time out and are retried by simply re-running — the run is resumable
and every pass grows the corpus at $0).

## 6. The pros — what this architecture buys you

1. **Honesty by construction.** The engine's information-content disclosure, the Ask guard,
   and the AI panel's labeling make it *structurally impossible* for the system to quietly
   pass off speculation as Raman or prediction as fact. Most astrology apps do the opposite.
2. **$0 per reading, forever.** After the cost cut, a full reading costs no API money at all;
   Ask and the AI panel run on your own GPU. Sharing with 100 people costs the same as 1.
3. **Total privacy.** Birth data — the most personal data an astrology app touches — never
   leaves your machine. No third-party API sees a chart.
4. **Fidelity with receipts.** Every verdict traces to a cited Raman passage you can open in
   one click; the 261/293 golden ratchet stops any regression permanently.
5. **Safety that survives a bad model.** The guards are *code*, not prompts. A weak or
   jailbroken model can only ever degrade to the engine's own prose — verified live when the
   1.5B model's decree slipped and the guard served engine text instead.
6. **A learning loop.** Chart-specific feedback accumulates real calibration data; the corpus
   + fine-tune loop turns every improvement of the teacher into a better owned model.
7. **Ownership.** The end state is your model, your data, your hardware — no vendor,
   no per-call bill, no policy change can take the capability away.
8. **Mobile + one-command sharing.** The manuscript works one-handed on a phone; a
   `cloudflared` tunnel shares it in a minute (see `SHARE_QUICKSTART.md`).

## 7. The honest limits (so the pros stay true)

- Textbook fidelity ≠ real-world prediction: the validation program measured **null**
  real-outcome generalization. The report says so about itself, and must keep saying so.
- The local 1.5B student won't out-write Claude; its wins are cost, privacy, and ownership.
  The corpus quality gate keeps its floor high; the fine-tune raises its ceiling.
- The quick-share tunnel exposes your machine — trusted circles, short-lived links.

## 8. Operations quick reference

```powershell
$env:REPORT_LLM_ENABLED = "true"
py -3.12 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
cloudflared tunnel --url http://localhost:8000        # share <url>/report/page

# grow the corpus (each pass retries failures, $0):
$env:OLLAMA_MODEL="gemma4:12b"; $env:OLLAMA_TIMEOUT_SECONDS="420"
py -3.12 -m app.medini.ml.build_analysis_corpus --limit 350 --backend ollama

# train + serve the owned model (GPU free):
py -3.12 -m app.medini.ml.train_llm_local --epochs 2 --device dml
# convert adapter → GGUF (llama.cpp), then:
ollama create astro-analyst -f data/ml_runs/astro_analyst_lora/Modelfile
$env:OLLAMA_MODEL = "astro-analyst"

# read the feedback people left:
py -3.12 -c "import sqlite3; [print(r) for r in sqlite3.connect('astro.db').execute('select * from chart_feedback')]"
```



A report of this scope is too large to produce in a single response. It would be approximately 30–40 pages with diagrams, figures, tables, and publication-quality layout.
The most useful deliverable is a professionally structured whitepaper that can be exported directly to PDF.

फलादेशः
The Whole Process & Methodology
From Birth to Manuscript
A deterministic B. V. Raman Vedic Astrology Engine with Explainable AI
Version 2026-07-28

Cover
(Full-page illustration)
• Palm-leaf manuscript background
• Zodiac wheel watermark
• Sanskrit title in gold
• Minimal geometric border
• Subtitle:
From Birth Data to Evidence-Based Astrological Reading

Table of Contents
1. Executive Summary
2. System Overview
3. End-to-End Architecture
4. Birth Data Processing
5. Deterministic Astrology Engine
6. The Thirteen-Leaf Manuscript
7. Evidence Generation
8. The Four-Voice Contract
9. AI Safety Architecture
10. Feedback System
11. Teacher → Student Pipeline
12. Validation
13. Advantages
14. Limitations
15. Operations
16. Future Work

1 Executive Summary
Purpose
फलादेशः is an explainable Vedic astrology platform built around a deterministic implementation of B. V. Raman's astrological methodology.
Unlike conventional AI astrology applications, the engine—not the language model—is the primary authority.
Every astrological conclusion originates from deterministic calculations, documented rules, and cited passages.
Artificial intelligence is used exclusively for explanation, summarization, and optional speculative discussion that is explicitly separated from the engine's conclusions.

Key Principles
PrincipleDescriptionDeterministicSame birth → identical readingExplainableEvery verdict has evidencePrivacyRuns locallySafeAI cannot bypass engineHonestValidation limitations disclosed
Architecture Overview
Birth Details
      │
      ▼
Swiss Ephemeris
      │
      ▼
Deterministic Engine
      │
 ┌────┼────┐
 ▼    ▼    ▼
Report AI Feedback
      │
      ▼
Training Dataset
      │
      ▼
Local Fine-tuned Model

2 System Overview
Philosophy
The platform follows a strict separation of responsibilities.
Astronomy

↓

Astrological Rules

↓

Evidence

↓

Report

↓

AI Explanation
The AI never creates astrological facts.
It only explains existing facts.

Why this architecture?
Traditional astrology applications usually work like
Birth

↓

GPT

↓

Prediction
This introduces hallucinations and unverifiable claims.
फलादेशः instead follows
Birth

↓

Swiss Ephemeris

↓

Rule Engine

↓

Evidence

↓

Report

↓

Optional AI
The engine always remains the source of truth.

3 End-to-End Workflow
Stage 1 — Birth Information
Input includes
• Name
• Birth date
• Birth time
• Birth city
• Coordinates
• Time zone
The system automatically selects latitude and longitude from the internal city database.

Stage 2 — Astronomical Computation
Swiss Ephemeris computes
• planetary positions
• ascendant
• ayanamsa
• houses
• divisional charts
All computations use Lahiri ayanamsa.

Stage 3 — Rule Engine
The deterministic engine evaluates hundreds of rules including
• Yogas
• House strength
• Functional benefics
• Vargas
• Dasha
• Transits
• Ashtakavarga
• Jaimini
• Longevity
Each rule is independently evaluated.

Stage 4 — Integration
Individual observations are merged into
• Insight Digest
• House summaries
• Life chapters
• Narrative
No information is discarded.

4 The Thirteen-Leaf Report
Each report resembles a traditional Indian palm manuscript.
LeafPurposeCoverIntroductionBirthBirth detailsDigestRanked insightsSignatureChart identityChartsHoroscope diagramsYogasClassical combinationsHousesHouse analysisMattersWealth, career, healthTimelineVimshottariTransitCurrent influencesDivisionalVargasInsightsAI & statisticsNichodSummary
5 Evidence Generation
Every statement is accompanied by
• source rule
• supporting observations
• Raman citation
• confidence
Example
Conclusion

↓

Supporting Rules

↓

Planetary Positions

↓

Astronomical Data

6 Four-Voice Contract
LayerSourceReportEngineAsk PanelLocal LLMAI InterpretationLocal LLMFeedbackEngineEach layer has clearly defined responsibilities.

7 AI Safety
User Question

↓

Fact Extraction

↓

Grounding Check

↓

Prediction Filter

↓

Medical Filter

↓

Safety Rules

↓

Final Response
If grounding fails, the system falls back to deterministic engine text.

8 Feedback Loop
Every report ends with chart-specific questions.
Reading

↓

User Feedback

↓

Database

↓

Training Corpus

↓

Improved Model

↓

Future Reading
This gradually builds a real-world calibration dataset.

9 Local Model Training
75,000 Birth Charts

↓

Deterministic Reports

↓

Evidence Facts

↓

Teacher Model

↓

Quality Gate

↓

Training Dataset

↓

LoRA Fine-tuning

↓

GGUF

↓

astro-analyst
Only grounded responses enter the corpus.

10 Validation
Engine
Golden Tests
261 / 293
Accuracy against published B. V. Raman interpretations
89.1%

Analysis Model
MetricResultClaude Keep Rate87.5%Gemma Keep Rate100%Cost$0PrivacyLocal
11 Advantages
• Explainable reasoning
• Deterministic outputs
• Complete privacy
• No cloud dependency
• Evidence-backed interpretations
• Continuous learning
• Zero recurring cost
• Safe AI integration

12 Honest Limitations
The system openly acknowledges several constraints.
• Fidelity to classical texts does not imply predictive validity.
• AI-generated explanations remain secondary to the deterministic engine.
• Local deployment requires user-managed hardware.
• Temporary sharing through local tunnels should be restricted to trusted users.
This transparency is an intentional design feature that distinguishes the platform from systems that present speculative interpretations as established fact.

13 Operational Workflow
Run Server

↓

Generate Report

↓

Collect Feedback

↓

Grow Corpus

↓

Train Model

↓

Deploy New Adapter

14 Future Directions
Planned enhancements include:
• Interactive report visualizations
• Multi-language manuscript generation
• Rich PDF export with embedded citations
• Comparative chart analysis
• Longitudinal feedback analytics
• Expanded deterministic rule coverage
• Enhanced local language model fine-tuning

Appendix
Include:
• Complete architecture diagrams
• Database schema
• Engine flowcharts
• Validation methodology
• Command reference
• Configuration variables
• Citation index
• Example report pages
• Safety policy
• Glossary of astrological terms
This structure is suitable for a professionally typeset PDF of approximately 30–40 pages, with diagrams, screenshots, and manuscript-inspired graphics replacing many of the text-only sections.


