# Kundli Analysis System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `app/reading/` — a 59-module deterministic kundli analysis engine that emits structured JSON given DOB + time + place. v1 is CLI-only, Parashari + Jaimini doctrine, with Tier-3 RAG enrichments but no LLM narration (deferred to v1.5).

**Architecture:** Strict downhill imports (`app/core/*` → `computations/*` → `sequences/*.py` → `domains/*` → `proforma.py` → `cli.py`). 9-stage DAG: input → natal → primitives → foundations → practitioner → sequences → domains → JSON assembly → Tier-3 afterpass → write. Public `compute(enrich=True)` and private `_run_core_pipeline` cleanly separated to eliminate recursion risk in birth-time robustness.

**Tech Stack:** Python 3.12, Pydantic 2.x (frozen+strict), Swiss Ephemeris (Lahiri), Pytest + Hypothesis, sentence-transformers (multilingual-MiniLM), existing `app/medini/services/knowledge_search.py` for RAG.

**Spec:** [docs/superpowers/specs/2026-05-27-kundli-analysis-system-design.md](../specs/2026-05-27-kundli-analysis-system-design.md) (749 lines, committed at `eaf1ffb`). Refer to spec for full module list, JSON schema details, and the 16-decision doctrine lockfile content.

**Total scope:** 59 modules, ~6300 LOC, 350+ tests, 7 phases, ~8 weeks.

---

## Pre-flight checks

Before any module is written, complete these steps. Each is a real blocker on Phase 1.

### Task P.1: Read spec end-to-end

- [ ] **Step 1: Read the spec**

Open [docs/superpowers/specs/2026-05-27-kundli-analysis-system-design.md](../specs/2026-05-27-kundli-analysis-system-design.md). Pay particular attention to:
- Section 4 (module layout) — your file structure
- Section 6 (JSON schema) — the 4 enum tuples (MD_CHECK_KEYS, AD_CHECK_KEYS, AMSHA_BALA_KRAMA_KEYS, CAREER_EXECUTIVE_KEYS) are copy-paste-ready
- Section 11 (prediction-trap guardrails) — non-negotiable discipline
- Section 13 (doctrine lockfile contents) — 16 decisions
- Section 14 (Tier 3 methodology template) — mandatory docstring contract
- Section 18 (Phase 1 sub-task ordering)

- [ ] **Step 2: Confirm understanding of the falsified-prediction-trap**

The project memory records 4 ML methodologies that returned NULL trying to predict life events. This system is **structurally orthogonal** — descriptive, not predictive. If at any point during implementation you are tempted to add scoring/calibration that compares engine output against historical-outcome data, STOP and re-read Section 11.

- [ ] **Step 3: Set up Python environment**

```powershell
cd e:\astro
.venv\Scripts\Activate.ps1
py -3.12 -m pip install -q hypothesis pytest pytest-cov
```

Verify:
```powershell
py -3.12 -m pytest --version
py -3.12 -c "import hypothesis; print(hypothesis.__version__)"
```

### Task P.2: Create worktree (if using subagent-driven execution)

- [ ] **Step 1: Create worktree on a new branch**

```powershell
git worktree add -b feat/app-reading ../astro-reading
cd ..\astro-reading
```

If staying on `round8-unification` (current branch), skip this step.

---

## Phase 1: Foundation (10 working days = 2 weeks)

The goal of Phase 1 is to land a working CLI that emits valid JSON with the natal chart + Tier-0 primitives + 2 critical Tier-1 modules (functional_nature, bhava_chalit). After Phase 1, every later phase is a layer added to an already-working pipeline.

### Task 1.0: Doctrine lockfile (Day 1 — BLOCKS EVERYTHING)

**Files:**
- Create: `docs/doctrine-decisions.md`

The doctrine lockfile is Phase 1 sub-task #1 because all 11 Tier-0 modules read from it. Locking it BEFORE code prevents contradictory implicit choices across modules.

- [ ] **Step 1: Create the lockfile skeleton**

```powershell
# Create with the 16 decision headings; fill bodies in step 2
```

The 16 decisions and their values are listed verbatim in spec Section 13. Each entry uses this template:

```markdown
## D-N: <Decision title>

**Status:** Locked 2026-05-27
**Used by:** <list of modules>
**Source citation:** <BPHS verse / Phaladeepika chapter / commentator>
**Decision:** <one-paragraph commitment>
**Alternatives considered:** <briefly>
**Rationale:** <why this choice; cross-check with external pinning source>
```

- [ ] **Step 2: Write all 16 decisions**

Copy values from spec Section 13. Examples:
- D-1: Karaka mode = 8 (PVR Narasimha Rao) — matches jagannathahora.io pin
- D-3: Vimsopaka weights = `{D1:3.5, D2:1, D3:1, D7:0.5, D9:3, D10:0.5, D12:0.5, D16:2, D20:0.5, D24:0.5, D27:0.5, D30:1, D40:0.5, D45:0.5, D60:5}`
- D-4: Ishta formula = BPHS Ch.47 v.3: `sqrt(Cheshta × Uchcha)`
- D-9: MKS table = 8-row canonical: Su-12, Mo-8, Ma-7, Me-7, Ju-3, Ve-6, Sa-1, Ra-9
- D-16: Education chart = D24 (NOT D9, NOT D4)

For each decision, the **Source citation** field MUST point to a BPHS verse, Phaladeepika chapter, or named commentator (PVR / Sanjay Rath / Iranganti). Vague citations are unacceptable.

- [ ] **Step 3: Dispatch bphs-doctrine-reviewer for audit**

```
Dispatch Agent with subagent_type="bphs-doctrine-reviewer" and prompt:
"Read e:\astro\docs\doctrine-decisions.md and audit each of the 16 decisions for doctrinal accuracy and BPHS citation correctness. Flag any decision where the cited verse does not support the chosen value, or where alternatives were not honestly considered. Return verdict per decision: APPROVED / NEEDS-CLARIFICATION / INCORRECT."
```

Address all NEEDS-CLARIFICATION and INCORRECT findings before commit.

- [ ] **Step 4: Commit**

```bash
git add docs/doctrine-decisions.md
git commit -m "docs(reading): doctrine lockfile — 16 decisions for app/reading Phase 1"
```

### Task 1.1: Performance spikes (Day 1.5)

**Files:**
- Create: `docs/perf/phase1-spikes.md`
- Create: `scratch_spike_imports.py`
- Create: `scratch_spike_rag_batch.py`
- Create: `scratch_spike_shodashavarga.py`

These spikes remove the "budget is fiction" risk identified in spec Section 16. ~1.5 hours total investment.

- [ ] **Step 1: Spike A — import-chain cold-start**

Create `scratch_spike_imports.py`:

```python
"""Measure cold-start cost of expected Phase 1 imports."""
import subprocess
import time

IMPORTS = [
    "import json",
    "import argparse",
    "import datetime",
    "import logging",
    "import pydantic",
    "import swisseph",
    "import numpy",
    "import pandas",
    "from app.core import ephemeris_engine",
    "from app.core import shodashavarga",
    "from app.core import dignity",
]

for imp in IMPORTS:
    start = time.perf_counter()
    subprocess.run(["py", "-3.12", "-c", imp], check=True, capture_output=True)
    elapsed = time.perf_counter() - start
    print(f"{elapsed*1000:7.0f}ms  {imp}")
```

Run: `py -3.12 scratch_spike_imports.py`

Capture output to `docs/perf/phase1-spikes.md`.

- [ ] **Step 2: Spike B — RAG batch-encode latency**

Create `scratch_spike_rag_batch.py`:

```python
"""Measure RAG encode latency at N={1, 50, 200}."""
import time
from app.medini.services.knowledge_search import get_default_service

svc = get_default_service()
svc.ensure_loaded()
print("RAG loaded; running batch tests...")

queries = ["Saturn in 6th house"] * 200

for n in (1, 50, 200):
    batch = queries[:n]
    start = time.perf_counter()
    _ = svc._model.encode(batch, normalize_embeddings=True)
    elapsed = time.perf_counter() - start
    print(f"N={n:3d}: {elapsed*1000:7.0f}ms  ({elapsed*1000/n:.1f}ms/query)")
```

Run and capture. **Expected outcome:** batch=200 should be roughly 5-10× faster per-query than batch=1, confirming the perf budget revision in spec Section 16.

- [ ] **Step 3: Spike C — Shodashavarga full-16 vs used-7**

Create `scratch_spike_shodashavarga.py`:

```python
"""Confirm computing all 16 D-charts is cheap vs only 7."""
import time
from app.core.shodashavarga import (
    SHODASHAVARGA_DIVISORS,
    calculate_divisional_longitude,
)

USED = (1, 2, 3, 7, 9, 10, 12, 24, 60)
ALL16 = SHODASHAVARGA_DIVISORS

# Pretend 9 planet longitudes
positions = [12.3, 45.6, 78.9, 100.0, 123.4, 156.7, 189.0, 212.3, 245.6]

def measure(divisors):
    start = time.perf_counter()
    for _ in range(1000):
        for lon in positions:
            for d in divisors:
                _ = calculate_divisional_longitude(lon, d)
    return time.perf_counter() - start

t_used = measure(USED)
t_all = measure(ALL16)
print(f"Used-9:  {t_used*1000:.1f}ms (1000 charts)")
print(f"All-16:  {t_all*1000:.1f}ms (1000 charts)")
print(f"Delta:   {(t_all-t_used)*1000:.1f}ms — {((t_all/t_used)-1)*100:.0f}% increase")
```

Run and capture. **Expected outcome:** delta is <5ms per 1000 charts. If true, computing all 16 vargas upstream is correct.

- [ ] **Step 4: Write spike report**

Create `docs/perf/phase1-spikes.md` with the 3 measurements + a "DECISIONS" section noting any budget revisions needed.

- [ ] **Step 5: Commit**

```bash
git add docs/perf/phase1-spikes.md scratch_spike_*.py
git commit -m "perf(reading): Phase 1 pre-build spikes — import chain + RAG batch + shodashavarga"
```

### Task 1.2: schema.py — base models + enum lists

**Files:**
- Create: `app/reading/__init__.py` (empty)
- Create: `app/reading/computations/__init__.py` (empty)
- Create: `app/reading/computations/divisional_readings/__init__.py` (empty)
- Create: `app/reading/sequences/__init__.py` (empty for now; SEQUENCES registry populated later)
- Create: `app/reading/domains/__init__.py` (empty)
- Create: `app/reading/schema.py`
- Create: `tests/reading/__init__.py` (empty)
- Create: `tests/reading/test_schema.py`

This is the most important Phase 1 deliverable. The schema locks the contract for every later module.

- [ ] **Step 1: Write failing test for ChartInput**

```python
# tests/reading/test_schema.py
"""Schema model validation tests."""
from __future__ import annotations
import pytest
from pydantic import ValidationError

class TestChartInput:
    def test_valid_chart_input_constructs(self):
        from app.reading.schema import ChartInput
        ci = ChartInput(
            dob="1990-07-15", time="12:00", tz="+05:30",
            lat=12.97, lon=77.59,
        )
        assert ci.dob == "1990-07-15"

    def test_invalid_latitude_rejected(self):
        from app.reading.schema import ChartInput
        with pytest.raises(ValidationError):
            ChartInput(dob="1990-07-15", time="12:00", tz="+05:30", lat=100.0, lon=77.59)

    def test_invalid_longitude_rejected(self):
        from app.reading.schema import ChartInput
        with pytest.raises(ValidationError):
            ChartInput(dob="1990-07-15", time="12:00", tz="+05:30", lat=12.97, lon=200.0)
```

- [ ] **Step 2: Run test to verify FAIL (ModuleNotFoundError)**

```powershell
py -3.12 -m pytest tests/reading/test_schema.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.reading.schema'`

- [ ] **Step 3: Implement ChartInput**

```python
# app/reading/schema.py
"""Pydantic models for app/reading JSON output.

Schema version: 1.0.0
Stability: experimental (until first downstream consumer ships)
"""
from __future__ import annotations
from typing import Final, Literal
from pydantic import BaseModel, ConfigDict, Field

class ChartInput(BaseModel):
    """User-supplied birth data."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    dob: str                  # YYYY-MM-DD
    time: str                 # HH:MM
    tz: str                   # ±HH:MM
    lat: float = Field(ge=-90.0, le=90.0)
    lon: float = Field(ge=-180.0, le=180.0)
```

- [ ] **Step 4: Run test to verify PASS**

```powershell
py -3.12 -m pytest tests/reading/test_schema.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Write tests for Finding model**

```python
# add to tests/reading/test_schema.py
class TestFinding:
    def test_finding_constructs(self):
        from app.reading.schema import Finding, ConfidenceScore
        f = Finding(
            id="primitive.karakas.atmakaraka",
            rule="Atmakaraka identification",
            source_sequence=None,
            classification="primitive",
            direction="neutral",
            verdict="Jupiter at 27.5° is Atmakaraka",
            evidence=["Jupiter degree: 27.5", "Highest among 7 planets"],
            confidence=ConfidenceScore(score=1.0, votes={"house": True, "lord": True, "karaka": True}, band="very_strong"),
        )
        assert f.enrichment_level == 0
        assert f.citations == []
        assert f.contradicts_finding_ids == []

    def test_verdict_max_length_enforced(self):
        from app.reading.schema import Finding, ConfidenceScore
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            Finding(
                id="x.y.z", rule="x", source_sequence=None,
                classification="primitive", direction="neutral",
                verdict="x" * 200,  # exceeds 140
                evidence=[],
                confidence=ConfidenceScore(score=0.5, votes={"house": False, "lord": False, "karaka": False}, band="indicative_only"),
            )
```

- [ ] **Step 6: Implement Finding + ConfidenceScore + enrichment sub-models**

Reference spec Section 6 (Universal Finding model) + Section 15 (additions). Implement:
- `ConfidenceScore`, `Citation`, `ConsensusScore`, `Dispute`, `RobustnessScore`
- `Finding` with all post-revision-1 additions (`enrichment_level`, `verdict_language`, `consensus_status`, `contradicts_finding_ids`)
- All numeric Field constraints (ge/le)

- [ ] **Step 7: Run tests, verify PASS, commit**

```powershell
py -3.12 -m pytest tests/reading/test_schema.py -v
git add app/reading/__init__.py app/reading/computations/__init__.py app/reading/sequences/__init__.py app/reading/domains/__init__.py app/reading/computations/divisional_readings/__init__.py app/reading/schema.py tests/reading/__init__.py tests/reading/test_schema.py
git commit -m "feat(reading): schema.py — ChartInput + Finding + enrichment models"
```

- [ ] **Step 8: Implement the 4 enum tuples + their validators**

Add to `app/reading/schema.py` (verbatim from spec Section 6):

```python
MD_CHECK_KEYS: Final[tuple[str, ...]] = (
    "bhaav_from_lagna",
    "commonality_significations",
    "residential_strength",
    "bhaavs_aspected_fully",
    "rashi_depositor",
    "balaadi_avastha",
    "conjunctions_within_15deg",
    "full_aspects_on_md_lord",
    "trinal_planets",
    "proximity_to_exact_trine",
    "md_lord_as_lagna_yogas",
    "nakshatra_tara_from_moon",
    "nakshatra_depositor_dignity",
    "navamsa_depositor",
    "kartari_yoga",
    "planet_in_2nd_from_md_lord",
    "ishta_phal",
    "repeat_from_arudha_lagna",
    "repeat_from_karakamsha_lagna",
)

AD_CHECK_KEYS: Final[tuple[str, ...]] = (
    "rulership_of_ad_lord",
    "house_placement_of_ad_lord",
    "strength_dignity_influence",
    "rajyoga_formed",
    "afflictions",
    "divisional_chart_assessment",
    "mutual_position_md_ad",
)

AMSHA_BALA_KRAMA_KEYS: Final[tuple[str, ...]] = (
    "analyze_d1",
    "consult_d9",
    "specific_varga_refinement",
    "dasha_transit_activation",
)

CAREER_EXECUTIVE_KEYS: Final[tuple[str, ...]] = (
    "vargottama_amatya_karaka",
    "gandanta_knots",
    "vimsopaka_strength",
    "gulika_saturn_bottlenecks",
)
```

- [ ] **Step 9: Test that judgment dicts enforce all named keys**

```python
class TestMDJudgmentSchema:
    def test_md_judgment_missing_key_rejected(self):
        from app.reading.schema import MDJudgment, MD_CHECK_KEYS, Finding, ConfidenceScore
        from pydantic import ValidationError

        # 18 keys (missing 1)
        partial = {k: _make_dummy_finding(k) for k in MD_CHECK_KEYS[:18]}
        with pytest.raises(ValidationError):
            MDJudgment(md_lord="Saturn", start_jd=2450000.0, end_jd=2456938.0, age_at_start=0, age_at_end=19, is_current=False, is_past=True, is_future=False, checks=partial, overall_verdict=_make_dummy_finding("summary"))
```

Implement `MDJudgment` with a Pydantic validator that asserts `set(checks.keys()) == set(MD_CHECK_KEYS)`. Same pattern for `ADJudgment`, `AmshaBalaKramaResult`, `CareerExecutiveResult`.

- [ ] **Step 10: Run all schema tests, verify PASS, commit**

```bash
py -3.12 -m pytest tests/reading/test_schema.py -v
git add app/reading/schema.py tests/reading/test_schema.py
git commit -m "feat(reading): schema.py — named-key enum tuples + judgment validators"
```

- [ ] **Step 11: Implement remaining top-level models**

`Meta` (with `doctrine_config`, `stability`, `schema_version`), `ChartBlock`, `PrimitivesBlock`, `FoundationsBlock`, `PractitionerBlock`, `SequencesBlock`, `DomainsBlock`, `Contradiction`, and the root `ReadingOutput`.

Tests for each. Commit per group.

### Task 1.3: cli.py + proforma.py skeleton

**Files:**
- Create: `app/reading/cli.py`
- Create: `app/reading/proforma.py`
- Create: `tests/reading/test_cli_subprocess.py`

The split between public `compute(enrich=True)` and private `_run_core_pipeline` is established now to lock the discipline before any sequence module can violate it.

- [ ] **Step 1: Write subprocess CLI test (happy path)**

```python
# tests/reading/test_cli_subprocess.py
"""End-to-end CLI test running as subprocess (spec Section 17 mandatory)."""
from __future__ import annotations
import json
import subprocess
import sys

def test_cli_happy_path_emits_valid_json():
    result = subprocess.run(
        [sys.executable, "-m", "app.reading.cli",
         "--dob", "1990-07-15", "--time", "12:00", "--tz", "+05:30",
         "--lat", "12.97", "--lon", "77.59"],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, f"CLI failed: {result.stderr}"
    output = json.loads(result.stdout)
    assert "meta" in output
    assert output["meta"]["schema_version"] == "1.0.0"

def test_cli_bad_latitude_exits_1():
    result = subprocess.run(
        [sys.executable, "-m", "app.reading.cli",
         "--dob", "1990-07-15", "--time", "12:00", "--tz", "+05:30",
         "--lat", "200", "--lon", "77.59"],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 1
```

- [ ] **Step 2: Run, verify FAIL**

Expected: `ModuleNotFoundError: No module named 'app.reading.cli'`

- [ ] **Step 3: Implement proforma.py skeleton**

```python
# app/reading/proforma.py
"""Main orchestrator for app/reading.

Two-function pattern (per spec Section 5):
- _run_core_pipeline: private, deterministic, Stages 1-7
- compute: public, optional Tier-3 wrapper

Birth-time robustness MUST import _run_core_pipeline directly to avoid recursion.
"""
from __future__ import annotations
import logging
from typing import Any

from app.reading.schema import ChartInput

logger = logging.getLogger(__name__)

def _run_core_pipeline(chart_input: ChartInput) -> dict[str, Any]:
    """Stages 1-7. Deterministic. No RAG. No recursion."""
    logger.info("Running core pipeline for chart_input=%s", chart_input)
    # Stub: minimal valid output for Phase 1 day 4
    return {
        "meta": {"schema_version": "1.0.0", "stability": "experimental"},
        "chart": {},
        "primitives": {},
        "foundations": {},
        "practitioner": {},
        "sequences": {},
        "domains": {},
        "contradictions": [],
        "warnings": [],
    }

def compute(chart_input: ChartInput, enrich: bool = True) -> dict[str, Any]:
    """Public orchestrator. Stages 1-7 + optional Tier-3 afterpass."""
    base = _run_core_pipeline(chart_input)
    if not enrich:
        return base
    return _apply_tier3_enrichments(base, chart_input)

def _apply_tier3_enrichments(base: dict[str, Any], chart_input: ChartInput) -> dict[str, Any]:
    """Tier 3 afterpass. Returns base unmodified for Phase 1 (no Tier 3 modules yet)."""
    return base
```

- [ ] **Step 4: Implement cli.py**

```python
# app/reading/cli.py
"""CLI entry point for app/reading.

Usage:
    python -m app.reading.cli --dob 1990-07-15 --time 12:00 --tz +05:30 \\
                              --lat 12.97 --lon 77.59 [--out reading.json] [--no-enrich]
"""
from __future__ import annotations
import argparse
import json
import logging
import sys

from pydantic import ValidationError

from app.reading.proforma import compute
from app.reading.schema import ChartInput

logger = logging.getLogger(__name__)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app.reading.cli")
    parser.add_argument("--dob", required=True)
    parser.add_argument("--time", required=True)
    parser.add_argument("--tz", required=True)
    parser.add_argument("--lat", type=float, required=True)
    parser.add_argument("--lon", type=float, required=True)
    parser.add_argument("--out", default=None)
    parser.add_argument("--no-enrich", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    try:
        chart_input = ChartInput(dob=args.dob, time=args.time, tz=args.tz, lat=args.lat, lon=args.lon)
    except ValidationError as e:
        sys.stderr.write(f"Invalid chart input: {e}\n")
        return 1

    try:
        output = compute(chart_input, enrich=not args.no_enrich)
    except Exception:
        logger.exception("Compute failed")
        return 2

    payload = json.dumps(output, indent=2)
    if args.out:
        with open(args.out, "w") as f:
            f.write(payload)
    else:
        print(payload)
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run test, verify PASS, commit**

```bash
py -3.12 -m pytest tests/reading/test_cli_subprocess.py -v
git add app/reading/cli.py app/reading/proforma.py tests/reading/test_cli_subprocess.py
git commit -m "feat(reading): cli.py + proforma.py skeleton — _run_core_pipeline/compute split"
```

### Task 1.4: 11 Tier-0 computation modules (Days 5-8)

Each Tier-0 module follows the same TDD pattern. The pattern is shown once below for `karakas.py`; subsequent modules use identical structure with module-specific tests.

#### Task 1.4.1: karakas.py

**Files:**
- Create: `app/reading/computations/karakas.py`
- Create: `tests/reading/computations/__init__.py`
- Create: `tests/reading/computations/test_karakas.py`
- Create: `tests/reading/pinned/karakas_bangalore.json`

**Doctrine lock: D-1** = 8-karaka (PVR Narasimha Rao).

- [ ] **Step 1: Write external-pinned test**

Pin the expected karakas for the Bangalore baseline against jagannathahora.io output (which uses 8-karaka mode per D-1). Document the URL + access date in the pin file header.

```python
# tests/reading/computations/test_karakas.py
import json
import pytest
from pathlib import Path
from app.core.ephemeris_engine import natal_chart_from_birth_data
from app.reading.computations.karakas import compute_karakas

PINNED = Path(__file__).parent.parent / "pinned" / "karakas_bangalore.json"

@pytest.fixture(autouse=True)
def reset_swe_ayanamsa():
    """Reset Swiss Ephemeris ayanamsa per spec Section 17 item 4."""
    import swisseph as swe
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    yield
    swe.set_sid_mode(swe.SIDM_LAHIRI)

def test_bangalore_karakas_match_jagannatha_hora():
    expected = json.loads(PINNED.read_text())
    chart = natal_chart_from_birth_data("1990-07-15", "12:00", 12.97, 77.59, "+05:30")
    karakas = compute_karakas(chart, karaka_mode=8)
    assert karakas.atmakaraka == expected["atmakaraka"]
    assert karakas.amatya_karaka == expected["amatya_karaka"]
    # ... all 8 karakas
```

- [ ] **Step 2: Run, verify FAIL**

- [ ] **Step 3: Implement compute_karakas (D-1 locked: 8-karaka mode default)**

Karakas are ordered by sidereal longitude within sign (degree component), highest = AK. For retrograde planets, use `30 - degree`. Rahu always uses `30 - degree`. Output: AK, AmK, BK, MK, PK, GK, DK, plus DaraK in 8-karaka mode.

- [ ] **Step 4: Run, verify PASS**

- [ ] **Step 5: Add property-based test (hypothesis)**

```python
from hypothesis import given, strategies as st

@given(st.lists(st.floats(min_value=0.0, max_value=30.0, exclude_min=False, exclude_max=True), min_size=7, max_size=7))
def test_karaka_degrees_always_in_valid_range(degrees):
    # Build a synthetic chart with these degrees; assert no karaka has degree outside [0, 30)
    ...
```

- [ ] **Step 6: Commit**

```bash
git add app/reading/computations/karakas.py tests/reading/computations/test_karakas.py tests/reading/pinned/karakas_bangalore.json tests/reading/computations/__init__.py
git commit -m "feat(reading): karakas.py — 8-karaka (PVR) per D-1"
```

#### Task 1.4.2 – 1.4.11: Remaining Tier-0 modules

**Per-module TDD discipline (mandatory for every module in this section):**
- [ ] Step A: Create pin file (with external-source URL + access date header) OR cite the BPHS verse / textbook worked example
- [ ] Step B: Write failing test that asserts engine output equals pin
- [ ] Step C: Run test, confirm RED (ModuleNotFoundError or AssertionError)
- [ ] Step D: Implement module (≤150 LOC typical)
- [ ] Step E: Run test, confirm GREEN
- [ ] Step F: Add hypothesis property-based test for module invariants
- [ ] Step G: Run all tests, confirm PASS
- [ ] Step H: Single commit covering pin file + module + tests, message `feat(reading): <module>.py — <D-N doctrine summary>`

The 10 remaining modules, each running the 8-step cycle above:

| # | Module | Doctrine lock | External pin source | Property invariants to assert |
|---|---|---|---|---|
| 1.4.2 | `arudha_upapada.py` | D-2 (1/7→10 exception) | astrosaxena.com | All pada signs ∈ Aries..Pisces |
| 1.4.3 | `karakamsha.py` | (no separate lock; uses karakas + D9) | jagannathahora.io | Karakamsha sign ∈ Aries..Pisces |
| 1.4.4 | `vimsopaka.py` | D-3 (Shodashavarga scheme weights) | Phaladeepika worked example (Ch.9) + doctrine-reviewer | Score ∈ [0, 20]; sum equals expected from weights table |
| 1.4.5 | `ishta_phal.py` | D-4 (BPHS 47.3 formula) | Saravali worked example + doctrine-reviewer | `Ishta + Kashta = 60` exactly |
| 1.4.6 | `residential_strength.py` | D-5 (linear falloff) | Phaladeepika worked example + doctrine-reviewer | `strength = 0` at sandhi, `60` at madhya |
| 1.4.7 | `gulika.py` | D-6 (Gulika ≠ Mandi) | drikpanchang.com | longitude ∈ [0, 360) |
| 1.4.8 | `gandanta.py` | (no lock; standard) | doctrinal example | Boolean; affected_planets is list |
| 1.4.9 | `planet_retrograde.py` | (no lock; extracts ephemeris flag) | jagannathahora.io | All 9 planets have boolean flags |
| 1.4.10 | `avasthas.py` | (no lock; Deeptadi 9-state per BPHS Vol.II Ch.45) | BPHS table | State ∈ {Deepta..Khala} |
| 1.4.11 | `panchanga_reader.py` | (no lock; standard panchanga) | drikpanchang.com | tithi ∈ 1..30; vara ∈ 0..6 |

Pin file convention: `tests/reading/pinned/<module>_bangalore.json` with header comment documenting external source URL + access date + (for unpinnable modules) BPHS verse citation. Each commit covers one module.

**Acceptance gate after Task 1.4:** `python -m app.reading.cli --dob ... --lat ... --lon ... --tz ...` emits valid JSON with the `primitives` block populated for the Bangalore baseline.

### Task 1.5: functional_nature.py + bhava_chalit.py (Day 9)

These two are the foundational Tier-1 modules that BLOCK every downstream interpretation. Each ~150-180 LOC.

**Doctrine locks:** D-7 (PVR/Sanjay-Rath synthesis for functional nature table) and D-8 (Sripati cusps for bhava chalit).

- [ ] **Step 1-6 (functional_nature.py):** TDD cycle, pinned test against PVR table, commit
- [ ] **Step 7-12 (bhava_chalit.py):** TDD cycle, pinned test against jagannathahora.io chalit chart, commit

### Task 1.6: Doctrine checkpoint #1 (Day 10)

- [ ] **Step 1: Dispatch bphs-doctrine-reviewer**

```
Agent(subagent_type="bphs-doctrine-reviewer", prompt:
"Read e:\astro\tests\reading\snapshots\bangalore_tier0_primitives.json (generated from the new CLI). Audit each primitive output against classical BPHS. For each finding, report APPROVED / NEEDS-CLARIFICATION / INCORRECT with verse citations.")
```

- [ ] **Step 2: Generate the snapshot**

```powershell
py -3.12 -m app.reading.cli --dob 1990-07-15 --time 12:00 --tz +05:30 --lat 12.97 --lon 77.59 --no-enrich --out tests/reading/snapshots/bangalore_tier0_primitives.json
```

- [ ] **Step 3: Address findings; commit fixes**

- [ ] **Step 4: Phase 1 complete — tag**

```bash
git tag reading-phase1-complete
```

---

## Phase 2: Tier 1 completion (1 week)

Phase 2 builds the remaining 7 Tier-1 modules in 4 parallel-eligible sub-tasks (jaimini_drishti, ashtakavarga_reader, shadbala_phase1, bhava_bala can all be built concurrently) + 3 sequential (argala depends on jaimini_drishti; karaka_triangulation depends on karakas; confidence_voting depends on everything).

**Mandatory 8-step TDD cycle for every module** (same as Phase 1.4):
- [ ] Step A: Create pin file OR cite BPHS verse / textbook worked example
- [ ] Step B: Write failing test that asserts engine output equals pin
- [ ] Step C: Run test, confirm RED
- [ ] Step D: Implement module
- [ ] Step E: Run test, confirm GREEN
- [ ] Step F: Add hypothesis property-based test for invariants
- [ ] Step G: Run all tests, confirm PASS
- [ ] Step H: Single commit covering module + tests + pin file

This template applies to EVERY module in Phases 2, 3, 4, 5, 6. No shortcuts.

**Module-specific doctrine locks:**

| Module | Doctrine lock | External pin |
|---|---|---|
| `bhava_bala.py` | (BPHS Ch.28) | None — Phaladeepika worked example |
| `shadbala_phase1.py` | (BPHS Ch.27 phases) | None — Saravali / Phaladeepika |
| `ashtakavarga_reader.py` | (Phaladeepika Ch.23-24 interpretive bands) | jagannathahora.io SAV values |
| `argala.py` | (BPHS Vol.I Ch.30) | None — doctrine-reviewer |
| `jaimini_drishti.py` | (Jaimini sutras 1.4 movable/fixed/dual) | None — doctrinal table |
| `karaka_triangulation.py` | D-10 (Sanjay-Rath reading) | None — doctrine-reviewer |
| `confidence_voting.py` | (3-vote rule from practitioner research) | None — synthetic test cases |

**Acceptance gate after Phase 2:** `foundations` block in JSON fully populated for Bangalore baseline. Snapshot `bangalore_foundations.json` created and committed.

---

## Phase 3: Tier 2 doctrine layer (2 weeks)

The biggest phase. 17 modules + 7 divisional_readings sub-modules.

### Sub-phase 3a (week 1): Doctrine atoms — 6 small modules (parallel-eligible)

Each ~80-150 LOC. All independent.

- `marana_karaka_sthana.py` (D-9: canonical 8-row table)
- `trika_doctrine.py`
- `graha_yuddha.py` (D-13: northern-latitude wins)
- `special_lagnas.py` (5 special lagnas: Hora, Ghatika, Sree, Bhava, Pranapada)
- `eclipse_natal_activation.py`
- `sade_sati_severity.py` (extends existing `app/core/sade_sati.py`)

For each: TDD cycle + commit.

### Sub-phase 3b (week 2): Synthesis + big modules

- `marriage_trigger.py` (~200 LOC; depends on multiple Tier-1 + Tier-2 outputs). TDD cycle per Phase-1.4 8-step template.

**`yogas_extended.py` — decomposed into 9 yoga-family sub-tasks** (decompose to avoid the 800-LOC ceiling; group into `computations/yogas_extended/` package with one submodule per family + `__init__.py` re-export):

| # | Sub-task | Yoga family | Doctrine lock | LOC |
|---|---|---|---|---|
| 3b.1 | `yogas_extended/adhi.py` | Adhi Yoga (benefics in 6/7/8 from Moon) | (BPHS Ch.40) | ~80 |
| 3b.2 | `yogas_extended/lakshmi.py` | Lakshmi Yoga (9L exalt + Venus strong) | (BPHS Ch.40) | ~80 |
| 3b.3 | `yogas_extended/saraswati.py` | Saraswati Yoga (Mer+Jup+Ven in kendra/2/5) | (BPHS Ch.40) | ~80 |
| 3b.4 | `yogas_extended/daridra.py` | Daridra Yoga (poverty indicator) | (BPHS Ch.40) | ~60 |
| 3b.5 | `yogas_extended/chamara.py` | Chamara Yoga (royalty pattern) | (BPHS Ch.40) | ~60 |
| 3b.6 | `yogas_extended/vipareeta.py` | Vipareeta Raja Yoga (depends on `trika_doctrine.py`) | (BPHS Vol.I) | ~100 |
| 3b.7 | `yogas_extended/parivartana.py` | Parivartana (lord exchange) | (BPHS Vol.I) | ~80 |
| 3b.8 | `yogas_extended/kala_sarpa.py` | Kala Sarpa/Kala Amrita | **D-12** (strict 180° Rahu-leading) | ~100 |
| 3b.9 | `yogas_extended/neech_bhanga.py` | Neech Bhanga (4 BPHS variants — pick D-11 primary) | **D-11** (BPHS Vol.I Ch.39 v.10) | ~120 |

Each sub-module: 8-step TDD cycle. Each commit covers one yoga family.

**`remedies.py` — decomposed into 4 category sub-tasks** (decompose by remedy type; group into `computations/remedies/` package):

| # | Sub-task | Category | LOC |
|---|---|---|---|
| 3b.10 | `remedies/mantras.py` | Beej mantras per afflicted planet (count + intonation) | ~120 |
| 3b.11 | `remedies/gemstones.py` | Gem rules with lagna-suitability gating (blue sapphire blocked for Ar/Le/Cn/Sc) | ~140 |
| 3b.12 | `remedies/daan.py` | Daan items + weekday per planet | ~100 |
| 3b.13 | `remedies/yantras.py` | Yantra recommendations per planet/yoga | ~80 |

Each sub-module: 8-step TDD cycle. `remedies/__init__.py` re-exports a unified `generate_remedies(findings) -> RemediesOutput` function.

- `rookie_guards.py` (~120 LOC; refuse-to-output invariants per spec Section 4). TDD cycle per Phase-1.4 template.
- 7 divisional_readings modules (D2, D3, D7, D9, D10 with 5-pillar voting, D12, **D24 ★ NEW**, D60):
  - **D-16 lock applies to D24** (education chart). `d24_chaturvimsamsa.py` is a freshly-added module per post-review revision — flag it for an extra `bphs-doctrine-reviewer` dispatch BEFORE commit (since it has no precedent in the original notebook proforma).

**Acceptance gate after Phase 3:**
- `practitioner` block populated
- Snapshot `bangalore_practitioner.json` created
- Doctrine checkpoint #2: dispatch `bphs-doctrine-reviewer` against full practitioner output

```bash
git tag reading-phase3-complete
```

---

## Phase 4: Sequences (1 week)

The 4 sequence orchestrators consume Tier-0/1/2 outputs and emit named-dict judgments.

**Pre-Phase-4 audit (CRITICAL):** Before writing `vimshottari_md.py`, run the KP-contamination audit:

- [ ] **Step 1: KP-contamination audit**

```
Agent(subagent_type="bphs-doctrine-reviewer", prompt:
"The 19 MD_CHECK_KEYS in app/reading/schema.py were sourced from a notebook that included KP literature. Audit each of the 19 check names against the locked Parashari+Jaimini scope. For each key, return: PURE-PARASHARI / KP-CONTAMINATED / AMBIGUOUS. If KP-contaminated, recommend a Parashari rashi-depositor equivalent.")
```

Address any contamination before implementing.

### Task 4.1: sequences/amsha_bala_krama.py (~250 LOC)

4 named checks (AMSHA_BALA_KRAMA_KEYS). BPHS layered Varga judgment: D1 → D9 → specific Varga → Dasha activation.

### Task 4.2: sequences/career_executive.py (~250 LOC)

4 named checks (CAREER_EXECUTIVE_KEYS). Notebook Sequence 2.

### Task 4.3: sequences/vimshottari_md.py (~600 LOC) — biggest file

19 named checks (MD_CHECK_KEYS). For EACH mahadasha in the natal timeline, produce an `MDJudgment` containing all 19 checks. Schema-validate every output.

Internal organization: `_check_bhaav_from_lagna`, `_check_commonality_significations`, ..., `_check_repeat_from_karakamsha_lagna` — one private function per check. Function names mirror check keys exactly for grep-ability.

If file exceeds 800 LOC, split into `vimshottari_md_natal_checks.py` (checks 1-17) + `vimshottari_md_repeat_checks.py` (checks 18-19).

### Task 4.4: sequences/vimshottari_ad.py (~350 LOC)

7 named checks (AD_CHECK_KEYS). Apply to: current AD + leftover ADs of current MD + first 3 ADs of next MD (per spec Section 2 scope lock).

### Task 4.5: sequences/__init__.py — registry

```python
from app.reading.sequences.amsha_bala_krama import run_sequence as run_amsha_bala_krama
from app.reading.sequences.career_executive import run_sequence as run_career_executive
from app.reading.sequences.vimshottari_md import run_sequence as run_vimshottari_md
from app.reading.sequences.vimshottari_ad import run_sequence as run_vimshottari_ad

SEQUENCES = {
    "amsha_bala_krama": run_amsha_bala_krama,
    "career_executive": run_career_executive,
    "vimshottari_md": run_vimshottari_md,
    "vimshottari_ad": run_vimshottari_ad,
}
```

**Acceptance gate after Phase 4:**
- `sequences` block populated
- Schema validates: every MD has all 19 keys; every AD has all 7 keys
- Snapshot `bangalore_sequences.json` created

```bash
git tag reading-phase4-complete
```

---

## Phase 5: Domains — ⭐ V1 ENGINE-ONLY MILESTONE (1 week)

6 pure synthesizers. Each ~150-250 LOC. The discipline (per spec Section 1): domains COMPOSE upstream findings by ID; they NEVER do D-chart math.

| Domain | Composes from | Key invariants |
|---|---|---|
| `career.py` | sequences/career_executive + divisional_readings/d10_dashamsha + sequences/vimshottari_md current MD | Five-pillar D10 vote referenced, not recomputed |
| `marriage.py` | divisional_readings/d9_navamsha + computations/marriage_trigger + arudha_upapada (UL) + karaka_triangulation (marriage) | UL findings present; 7L+Venus+D9 cross-checked |
| `health.py` | computations/marana_karaka_sthana + trika_doctrine + bhava_bala for 1/6/8/12 + balaadi_avastha of lagna lord | MKS findings surfaced |
| `wealth.py` | divisional_readings/d2_hora + yogas_extended (Lakshmi/Dhana/Saraswati) + computations on 2H/11H | Both 2H (retention) and 11H (inflow) findings present |
| `children.py` | divisional_readings/d7_saptamsa + yogas_extended (putra-related) + karakas (PutK) + computations on 5H | Triple-chart (D1+D9+D7) confirmation pattern |
| `education.py` | divisional_readings/d24_chaturvimsamsa + computations on 4H/5H + Mercury/Jupiter karaka | **D24 routed correctly per D-16** |

For each domain, the TDD cycle includes an **integration test that asserts the domain references upstream finding IDs** (per spec Section 7 Layer 4 — architectural-purity check):

```python
def test_marriage_domain_references_d9_finding_ids(bangalore_chart):
    output = run_stages_1_to_5(bangalore_chart)
    output_full = run_stage_6_marriage(output)
    marriage = output_full["domains"]["marriage"]
    d9_finding_ids = collect_finding_ids_from(output, source="computations.divisional_readings.d9_navamsha")
    assert any(fid in marriage["evidence_finding_refs"] for fid in d9_finding_ids), (
        "Marriage domain didn't reference any d9_navamsha finding — domain is recomputing D9 instead of consuming it"
    )
```

### Task 5.7: Famous-chart corpus expansion (parallel-eligible with Tasks 5.1-5.6)

**Files:**
- Create: `tests/reading/famous_charts/<name>.json` (10 files)
- Create: `tests/reading/test_famous_charts.py`

10 charts, **structure-only assertions** (NEVER outcome assertions per spec Section 11). Each chart file contains externally-verifiable birth data + the expected output shape (NOT verdicts).

- [ ] **Step 1: Create 6 standard reference charts**

| File | Birth data |
|---|---|
| `einstein.json` | 1879-03-14 11:30 Ulm, Germany |
| `gandhi.json` | 1869-10-02 07:33 Porbandar |
| `steve_jobs.json` | 1955-02-24 19:15 San Francisco |
| `ramana_maharshi.json` | 1879-12-30 01:00 Tiruchuli |
| `apj_kalam.json` | 1931-10-15 01:00 Rameswaram |
| `obama.json` | 1961-08-04 19:24 Honolulu |

- [ ] **Step 2: Create 4 edge-case charts (per spec Section 17 missing-edge-cases)**

| File | Edge case |
|---|---|
| `atmakaraka_tiebreaker.json` | Two karakas within 0.001° degree — tie-breaker branch test |
| `polar_latitude.json` | Reykjavík (lat 64.13°N) — house cusp computation stress |
| `equinox_zero_aries.json` | Birth at equinox with Lagna ~0° Aries (sidereal Lahiri) |
| `gandanta_moon.json` | Moon at last 1.5° Pisces / first 1.5° Aries (Gandanta junction) |

- [ ] **Step 3: Write structure-only test for all 10**

```python
@pytest.mark.parametrize("chart_file", ALL_FAMOUS_CHARTS)
def test_famous_chart_emits_valid_structure(chart_file):
    """Asserts ONLY: exit 0, schema-valid JSON, all required Finding IDs present.
    NEVER asserts verdicts or outcomes."""
    chart_data = json.loads(Path(chart_file).read_text())
    result = subprocess.run(["python", "-m", "app.reading.cli", ...args from chart_data],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0
    output = json.loads(result.stdout)
    ReadingOutput.model_validate(output)   # Pydantic raises if shape wrong
    assert_all_required_finding_ids_present(output)
```

- [ ] **Step 4: Commit**

```bash
git add tests/reading/famous_charts/ tests/reading/test_famous_charts.py
git commit -m "test(reading): famous-chart corpus (6 standard + 4 edge cases) — structure-only"
```

**Acceptance gate after Phase 5 — V1 SHIPPING MILESTONE:**
- Full deterministic JSON validates against schema
- All 6 domain readings produced for Bangalore baseline
- Snapshot `bangalore_domain_synthesis.json` created
- Doctrine checkpoint #3: dispatch `bphs-doctrine-reviewer` against full deterministic output
- Famous-chart corpus expanded to 10 charts; structure-only tests pass (Task 5.7)
- **This is shippable as-is if Phase 6 timeline slips.**

```bash
git tag reading-v1-engine-complete
```

---

## Phase 6: Tier 3 enrichments (1 week)

6 modules. Each MUST publish a `Methodology:` docstring block per spec Section 14 template BEFORE any code is written. This is the explicit anti-prediction-trap discipline.

### Task 6.0: Lazy-import refactor (Day 1 — BLOCKS Tier 3 modules)

**Files:**
- Modify: `app/reading/proforma.py` `_apply_tier3_enrichments` function
- Modify: `app/reading/cli.py` import section

Per spec Section 16 perf-win #2 (lazy import of `sentence_transformers`). This must land BEFORE the Tier-3 modules import the RAG service, otherwise cold-start eats 200-600ms even when `--no-enrich` is passed.

- [ ] **Step 1: Write a perf regression test**

```python
def test_cli_no_enrich_does_not_import_sentence_transformers():
    """When --no-enrich, sentence_transformers must NOT be imported.

    This catches accidental top-level imports of the RAG stack.
    """
    result = subprocess.run(
        [sys.executable, "-c",
         "import sys; from app.reading.cli import main; main(['--dob','1990-07-15','--time','12:00','--tz','+05:30','--lat','12.97','--lon','77.59','--no-enrich']); print('sentence_transformers' in sys.modules)"],
        capture_output=True, text=True, timeout=60,
    )
    assert result.stdout.strip().endswith("False"), "sentence_transformers leaked into --no-enrich path"
```

- [ ] **Step 2: Verify test FAILS**

- [ ] **Step 3: Refactor so RAG imports live inside `_apply_tier3_enrichments` function body**

- [ ] **Step 4: Verify test PASSES; commit**

```bash
git commit -m "perf(reading): lazy-import sentence_transformers — saves 200-600ms cold start on --no-enrich path"
```


For each Tier-3 module:

- [ ] **Step 1: Write the `Methodology:` docstring block**

Use spec Section 14 template. Specific commitments by module:
- `rag_citations.py`: query uses `rule_id + structural slots` ONLY; NEVER `Finding.verdict`. Biographical filter on famous-chart names.
- `consensus_scoring.py`: agreement over rule applicability, NOT outcome claims. Null-baseline (shuffled passages) test required.
- `contradiction_detector.py`: compares `direction` enum only.
- `dispute_surfacing.py`: report-only contract; no `is_correct` field.
- `yoga_calibration.py`: closed-form aggregation from BPHS-cited constants only.
- `birth_time_robustness.py`: ship raw `flip_rate` numerics; boolean flag is `EXPERIMENTAL`.

- [ ] **Step 2: Write the failing test (including the methodology-conformance test)**

Each module gets a test asserting its docstring contains the required `Methodology:` block.

```python
def test_module_has_methodology_block():
    from app.reading.computations import rag_citations
    assert "Methodology:" in rag_citations.__doc__
    assert "Prediction-trap declaration:" in rag_citations.__doc__
    assert "Famous-chart anti-contamination:" in rag_citations.__doc__
```

- [ ] **Step 3-5: TDD cycle, implement, run, commit**

**Performance-critical**: `rag_citations.py` MUST implement the batch-encode pattern from spec Section 16:

```python
def attach_citations(findings: list[Finding]) -> list[Finding]:
    # FILTER first: cap to high-confidence, classification ∈ {promise, yoga, trigger}
    eligible = [f for f in findings if f.confidence.band in ("very_strong", "moderate")
                and f.classification in ("promise", "yoga", "trigger")]

    # BATCH encode all queries in one call
    queries = [_build_query_from_rule_slot(f) for f in eligible]  # NEVER from f.verdict
    embeddings = svc._model.encode(queries, normalize_embeddings=True)

    # Then per-query retrieval is matrix-multiply only
    for f, emb in zip(eligible, embeddings):
        f.citations = svc.retrieve_top_k(emb, k=3)
    return findings
```

**Acceptance gate after Phase 6:**
- `enrich=True` populates citations on every eligible Finding
- Top-level `contradictions[]` present (may be empty for clean charts)
- Robustness sub-runs terminate within 4s (per perf budget)
- All 6 modules have paired tests including methodology-conformance assertion
- Snapshot `bangalore_tier3_enrichments.json` created and reviewed (per resolved Open Question #8)

```bash
git tag reading-phase6-complete
```

---

## Phase 7: Polish + spec close-out (3-5 days)

- [ ] **Step 1: Performance benchmarks formalized**

```python
# tests/reading/test_performance.py
def test_bangalore_e2e_under_budget_cold(benchmark):
    ...
    assert benchmark.stats["max"] < 12.0  # cold cache, spec Section 16

def test_bangalore_e2e_under_budget_warm(benchmark):
    ...
    assert benchmark.stats["max"] < 7.0  # warm cache, spec Section 16 revised
```

Add CI badge (informational, not blocking).

- [ ] **Step 2: Doctrine-audit cron template**

Create `.github/workflows/doctrine-audit.yml` per spec Section 7:
- Cron: `0 0 1 */3 *` (quarterly, 1st day of every 3rd month)
- Runs Bangalore baseline; dispatches doctrine-reviewer; commits markdown report to `docs/audits/doctrine-YYYY-QN.md`
- **NOT a blocking CI gate** (LLM-grader variance)

- [ ] **Step 3: User-facing CLI documentation**

Create `docs/reading/cli-reference.md`:
- All CLI flags (`--dob`, `--time`, `--tz`, `--lat`, `--lon`, `--out`, `--no-enrich`, `--config`, `--verbose`)
- Example invocations
- Exit codes (0=success, 1=bad input, 2=ephemeris failure, 3=schema validation failure, 4=RAG missing)

- [ ] **Step 4: Consumer-facing schema documentation**

Generate from Pydantic:

```python
# scripts/generate_schema_docs.py
import json
from app.reading.schema import ReadingOutput
schema = ReadingOutput.model_json_schema()
with open("docs/reading/json-schema.json", "w") as f:
    json.dump(schema, f, indent=2)
```

Create `docs/reading/json-schema.md` — human-readable companion explaining each top-level key.

- [ ] **Step 5: Final spec sign-off + tag**

Update spec status header from "post-review revision 2" to "v1.0.0 — implemented".

```bash
git tag reading-v1.0.0
```

- [ ] **Step 6: README updates**

Add a section to root `README.md`:
- "How to generate a kundli reading"
- "Where to file doctrine issues"
- Link to `docs/reading/`

---

## Phase summary table

| Phase | Duration | Deliverable | Tag |
|---|---|---|---|
| Pre-flight | 0.5d | env + spec read | — |
| 1: Foundation | 2 weeks | CLI emits primitives JSON | `reading-phase1-complete` |
| 2: Tier 1 | 1 week | Foundations populated | — |
| 3: Tier 2 | 2 weeks | Practitioner populated | `reading-phase3-complete` |
| 4: Sequences | 1 week | All 4 sequences emit valid judgments | `reading-phase4-complete` |
| 5: Domains | 1 week | **V1 ENGINE COMPLETE** | `reading-v1-engine-complete` ⭐ |
| 6: Tier 3 | 1 week | Citations + consensus + robustness | `reading-phase6-complete` |
| 7: Polish | 3-5d | Docs + audit cron | `reading-v1.0.0` |
| **Total** | **~8 weeks** | | |

---

## Cross-cutting reminders

1. **Doctrine lockfile is read-only after Phase 1 Task 1.0.** If a module needs a doctrine choice not in the lockfile, STOP — propose an amendment to the lockfile (`docs/doctrine-decisions.md`), get user approval, commit the amendment, THEN proceed. Never silently choose.

2. **Prediction-trap discipline.** Every Tier-3 module's `Methodology:` block is checked by an automated test asserting the required phrases are present in the docstring. Removing/weakening these declarations is a commit-rejecting offense.

3. **External-pinned tests are static.** If a pin needs re-generation, do it via a manual recorded session (browser screen + screenshot of URL + date). Never write a scraper. The pin file header documents the regeneration recipe.

4. **Frequent commits.** One module = one commit. One bug fix = one commit. Never bundle.

5. **CLAUDE.md compliance gates every commit:**
   - `logger = logging.getLogger(__name__)` (not `"app.reading"`)
   - Files ≤400 LOC typical; split at 800
   - Paired tests in `tests/reading/`
   - `from __future__ import annotations` at top of every new module
   - Module docstring with `Usage:` block for any CLI-invokable module
   - Co-authored-by attribution disabled globally — do NOT add it

6. **The `bphs-doctrine-reviewer` agent is your second pair of eyes.** Dispatch after every doctrinally-significant module, after the doctrine checkpoints (post-Phase 1, 3, 5), and any time a doctrine choice feels ambiguous. Cheap to invoke, expensive to skip.

7. **No premature optimization.** Spike-driven decisions are documented in `docs/perf/`. If a future module looks performance-sensitive, run a spike before optimizing.

---

## Execution handoff

**Plan complete and saved to** `docs/superpowers/plans/2026-05-27-kundli-analysis-system.md`.

**Two execution options:**

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration. Each subagent gets the spec + lockfile + relevant prior modules. Best for the ~80 atomic tasks in this plan.

**2. Inline Execution** — Execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints for review. Best if you want to watch each step happen.

**Which approach?**
