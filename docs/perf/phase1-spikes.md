# Phase 1 Pre-Build Performance Spikes

**Date:** 2026-05-27
**Branch:** feat/app-reading (worktree e:\astro-reading)
**Purpose:** Validate spec Section 16 performance budget BEFORE writing Phase 1 code.

---

## CRITICAL secondary finding: spec inventory hallucinated modules

While running Spike A, two imports failed because the modules do not exist:
- from app.core import dignity
- from app.medini.services.knowledge_search import get_default_service

**Modules the spec/plan claim exist but do NOT exist in the codebase:**

| Module path | Audit claim | Reality |
|---|---|---|
| app/core/dignity.py | Ready - OWN_SIGNS, EXALTATION, DEBILITATION | NOT PRESENT |
| app/core/planet_state.py | Ready - is_combust(), is_vargottama() | NOT PRESENT |
| app/core/shadbala.py | Phase 0 ready - Sthana-bala | NOT PRESENT |
| app/core/yoga_strength.py | Ready - strength scoring | NOT PRESENT |
| app/core/yoga_types.py | Ready - YogaInstance dataclass | NOT PRESENT |
| app/medini/services/knowledge_search.py | Ready - RAG | DIRECTORY DOES NOT EXIST |
| app/medini/services/chart_reader.py | Ready - Reading dataclass | NOT PRESENT |
| app/llm/citations.py | Ready - citation extraction | NOT PRESENT |

**What actually exists in app/core/:** antardasha, ashtakavarga, auth, avastha, config, database, ephemeris_engine, nakshatra, panchanga, pratyantar, sade_sati, shodashavarga, yogas.

**What actually exists in app/medini/:** astrocartography.py, eclipses.py, etl/, kurma_chakra.py, ml/, mundane.py, templates/. No services/ directory.

**What actually exists in app/llm/:** __init__.py, client.py, interpreter.py, templates.py. No citations.py.

**Impact:** The spec Section 3 inventory is largely fabricated by the earlier Explore agent. Phase 1 cannot proceed under the assumption these modules exist. Surfacing to user.

---

## Spike A - Import-chain cold-start

       40ms  OK  import json
       56ms  OK  import argparse
       34ms  OK  import datetime
       41ms  OK  import logging
      105ms  OK  import pydantic
       42ms  OK  import swisseph
      102ms  OK  import numpy
      613ms  OK  import pandas
       88ms  OK  from app.core import ephemeris_engine
       44ms  OK  from app.core import shodashavarga
       38ms  FAIL  from app.core import dignity (module does not exist)
       50ms  FAIL  from app.medini.services.knowledge_search ... (path does not exist)

### Findings
- pandas at 613ms is dominant. Avoid in critical path.
- swisseph and numpy each <110ms - acceptable.
- pydantic at 105ms - acceptable, load-once.

### Decision
- Phase 1 stays under spec cold budget (<700ms) IF pandas is not in critical path.
- Defer pandas to optional I/O paths, never inside _run_core_pipeline.

---

## Spike B - RAG batch-encode latency

STATUS: COULD NOT RUN. ModuleNotFoundError: No module named 'app.medini.services'

The RAG service path assumed by spec does not exist. Either:
1. RAG functionality lives at a different path (needs discovery), or
2. RAG infrastructure must be built before Phase 6.

### Decision
- Defer Spike B until RAG reality is established. File in risk register.

---

## Spike C - Shodashavarga 16-varga marginal cost

SHODASHAVARGA_DIVISORS: (2, 3, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60) - 14 divisors
USED (per spec): (1, 2, 3, 4, 7, 9, 10, 12, 24, 60)
USED  (10 divisors):    13.6ms per 1000 charts
ALL14 (14 divisors):    16.5ms per 1000 charts
Delta: 2.9ms (21% increase). Per-chart marginal: 0.003ms

### Findings
- Computing the full divisor set adds 0.003ms per chart - essentially free.
- HOWEVER: SHODASHAVARGA_DIVISORS has only 14 divisors. Missing D4 (Chaturthamsa).
- Full Shodashavarga 16-varga support requires D4 to be added.
- D-3 doctrine lockfile commits weight 0.5 to D4 but engine cannot compute D4 today.

### Decision
- Pre-vimsopaka.py Task 1.4.4 work: add D4 Chaturthamsa to app/core/shodashavarga.py.
- ~30 LOC + paired test. Blocks vimsopaka.py.
- Marginal cost validates: yes, compute all 16 vargas in Stage 1.

---

## DECISIONS for Phase 1 build

1. STOP - Re-baseline existing-capability inventory. Spec Section 3 lists modules that do not exist. Phase 1 cannot proceed until corrected. Surfacing to user.

2. Phase 1 prerequisite (new): Add D4 Chaturthamsa support to app/core/shodashavarga.py. ~30 LOC + paired test. Blocks vimsopaka.py (Task 1.4.4).

3. pandas budget: Phase 1 modules MUST NOT import pandas in critical compute path.

4. RAG path discovery: Before Phase 6 starts, locate actual RAG implementation or confirm it needs to be built.

5. Shodashavarga full-compute validated: <0.02ms per chart once D4 added.
