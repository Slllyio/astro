"""Distil the analysis-prose training corpus: chart facts -> excellent grounded analysis.

Phase 2 of the own-model program (teacher -> student). For each sampled dossier chart the
deterministic engine composes its full report; the FIXED teacher (the Phase-1 grounded
explainer prompt on a Claude model) writes the analysis for one or more evidence scopes;
and ONLY outputs that pass the code-level `refusal_reason` guard AND a quality bar enter
the corpus. The result is SFT JSONL the local student (`train_llm_local.py`) learns from —
every training target is grounded, cited, prediction-free prose by construction.

Rows are ``{"system", "prompt", "completion", "_meta"}`` where ``system + "\\n\\n" + prompt``
is EXACTLY what the serving path feeds a local model (`SystemPromptWrapper`), so the
student trains on its own serve-time format.

``--seed-voice`` additionally folds in TWO sources of Raman's own authenticated diction as
high-weight VOICE anchors (style, not evidence): the "Special Features" blocks from Notable
Horoscopes, and the much larger `verdict_prose` fragment set from the golden-accuracy fixture
(`tests/fixtures/raman_goldens.jsonl`, ~389 short, terse, declarative worked-chart judgments).

The teacher needs ``ANTHROPIC_API_KEY`` in the environment (runtime only — never written
anywhere). ``--backend ollama`` swaps in the local model to smoke-test the pipeline
without spending; ``--backend stub`` runs the plumbing with a canned reply (tests).

Usage:
    py -3.12 -m app.medini.ml.build_analysis_corpus --limit 20
    py -3.12 -m app.medini.ml.build_analysis_corpus --limit 2000 --scopes digest,summary \\
        --out data/ml_runs/analysis_corpus/sft.jsonl --seed-voice
    py -3.12 -m app.medini.ml.build_analysis_corpus --limit 5 --backend ollama   # $0 smoke
"""
from __future__ import annotations

import argparse
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

logger = logging.getLogger(__name__)

DOSSIER_PATH = Path("app/medini/data/person_dossier.parquet")
NOTABLE_TEXT = Path("data/knowledge_library/sources/Notable Horoscopes BV Raman.txt")
#: the golden-accuracy fixture behind the 261/293 textbook-fidelity ratchet (CLAUDE.md) — each
#: row's `expected_verdicts.*.verdict_prose` is a short, authenticated fragment of Raman's own
#: diction (terse, declarative, e.g. "Physical features predominantly saturnine — tall, lean,
#: much hair, fair; not quite healthy."). Repurposed here (2026-07-29) as a SECOND, much larger
#: voice-anchor source — the existing Notable Horoscopes anchors alone (37 rows) were clearly
#: not enough to shift the model's voice away from "data-analyst" prose.
GOLDEN_FIXTURES = Path("tests/fixtures/raman_goldens.jsonl")
DEFAULT_OUT = Path("data/ml_runs/analysis_corpus/sft.jsonl")

#: quality bar over and above the hard guard: enough substance and enough anchoring
#: that the student learns dense grounding, not thin summaries.
MIN_CHARS = 400
MIN_ANCHORS = 3

#: the OTHER half of the quality bar (added 2026-07-29, after real feedback: "too lengthy not
#: crisp too much gibberish"). The prior corpus had a floor but NO ceiling — since the teacher,
#: unconstrained by the (also since-fixed) old prompt, always wrote well above MIN_CHARS, the
#: floor never filtered anything, and the student learned an unbounded target length. These
#: mirror EXPLAINER_SYSTEM's "BE CRISP" rule (report_explainer.py): 3 short paragraphs, ~150
#: words, never more than 200 — MAX_WORDS gives a small buffer above that stated ceiling before
#: rejecting outright, and MAX_PARAGRAPHS catches the OTHER failure mode the rule names: packing
#: the same content into fewer, denser paragraphs instead of actually cutting it.
MAX_WORDS = 220
MAX_PARAGRAPHS = 4


# ─── dossier -> BirthData ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class SampledChart:
    person_id: str
    name: str
    corpus: str
    year: int
    month: int
    day: int
    hour: int
    minute: int
    latitude: float
    longitude: float
    tz_offset: float


def parse_dossier_row(row: dict) -> Optional[SampledChart]:
    """One dossier row -> a castable chart, or None when the birth is unusable.

    Requires a TIMED birth (`birth_time_confidence == 1.0`) — lagna-dependent analysis
    from an untimed birth would teach the student confidently-wrong prose."""
    try:
        if float(row.get("birth_time_confidence") or 0.0) < 1.0:
            return None
        d = str(row["birth_date"])            # "YYYY-MM-DD"
        t = str(row["birth_time"])            # "HH:MM:SS"
        y, mo, da = (int(x) for x in d.split("-"))
        hh, mm = int(t[0:2]), int(t[3:5])
        lat, lon = float(row["birth_lat"]), float(row["birth_lon"])
        tz = float(row["tz_offset"])
        if not (-90 <= lat <= 90 and -180 <= lon <= 180 and -12 <= tz <= 14):
            return None
        if not (1800 <= y <= 2100):
            return None
        return SampledChart(person_id=str(row["person_id"]), name=str(row.get("name") or ""),
                            corpus=str(row.get("corpus") or ""), year=y, month=mo, day=da,
                            hour=hh, minute=mm, latitude=lat, longitude=lon, tz_offset=tz)
    except (KeyError, ValueError, TypeError):
        return None


def sample_charts(limit: int, offset: int = 0) -> list[SampledChart]:
    """Deterministic, corpus-stratified sample of timed births: rows are ordered by a
    stable content hash of person_id (reproducible across runs, no RNG), then interleaved
    round-robin across corpora so ADB/WD/LA all contribute."""
    import hashlib

    import pandas as pd

    cols = ["person_id", "name", "corpus", "birth_date", "birth_time",
            "birth_time_confidence", "birth_lat", "birth_lon", "tz_offset"]
    df = pd.read_parquet(DOSSIER_PATH, columns=cols)
    df = df[df["birth_time_confidence"] >= 1.0]

    def _key(pid: str) -> str:
        return hashlib.blake2b(str(pid).encode(), digest_size=8).hexdigest()

    df = df.assign(_k=df["person_id"].map(_key)).sort_values("_k")
    buckets: dict[str, list[SampledChart]] = {}
    for row in df.to_dict("records"):
        c = parse_dossier_row(row)
        if c is not None:
            buckets.setdefault(c.corpus, []).append(c)
    # round-robin interleave the corpora
    out: list[SampledChart] = []
    idx = 0
    names = sorted(buckets)
    while len(out) < offset + limit and any(idx < len(buckets[n]) for n in names):
        for n in names:
            if idx < len(buckets[n]):
                out.append(buckets[n][idx])
                if len(out) >= offset + limit:
                    break
        idx += 1
    return out[offset:offset + limit]


# ─── the teacher ────────────────────────────────────────────────────────────────

def make_teacher(backend: str):
    """The teacher client for `backend` ('anthropic' | 'ollama' | 'stub'). Anthropic reads
    ANTHROPIC_API_KEY from the environment (runtime only); raises SystemExit with a clean
    message when unavailable so a batch run never half-starts."""
    from app.llm.report_explainer import EXPLAINER_SYSTEM
    if backend == "anthropic":
        from app.llm.client import AnthropicClient, AnthropicUnavailable
        try:
            return AnthropicClient(system=EXPLAINER_SYSTEM)
        except AnthropicUnavailable as exc:
            raise SystemExit(f"Anthropic teacher unavailable: {exc}. "
                             "Set ANTHROPIC_API_KEY in the environment.") from exc
    if backend == "ollama":
        from app.core.config import settings
        from app.llm.client import OllamaClient, SystemPromptWrapper
        return SystemPromptWrapper(
            OllamaClient(settings.OLLAMA_HOST, settings.OLLAMA_MODEL,
                         settings.OLLAMA_TIMEOUT_SECONDS), EXPLAINER_SYSTEM)
    if backend == "stub":
        from app.llm.client import StubClient, SystemPromptWrapper
        from app.llm.report_explainer import EXPLAINER_SYSTEM as _sys
        return SystemPromptWrapper(StubClient("The ruler is noted [Fact 1]."), _sys)
    raise SystemExit(f"unknown backend {backend!r}")


def keep_reason(ans, min_grounding: float) -> Optional[str]:
    """Why a teacher answer is REJECTED from the corpus (None = keep). The hard guard
    (`refusal_reason`) runs first and is absolute; the quality bar then filters thin or
    weakly-anchored answers that would teach the student bad habits."""
    from app.llm.report_explainer import refusal_reason
    hard = refusal_reason(ans, min_grounding)
    if hard is not None:
        return f"guard: {hard}"
    if ans.is_deferral:
        return "deferral (no analysis content)"
    if len(ans.text) < MIN_CHARS:
        return f"too short ({len(ans.text)} < {MIN_CHARS} chars)"
    if len(ans.anchors_used) < MIN_ANCHORS:
        return f"too few anchors ({len(ans.anchors_used)} < {MIN_ANCHORS})"
    words = len(ans.text.split())
    if words > MAX_WORDS:
        return f"too long ({words} words > {MAX_WORDS})"
    paragraphs = [p for p in re.split(r"\n\s*\n", ans.text) if p.strip()]
    if len(paragraphs) > MAX_PARAGRAPHS:
        return f"too many paragraphs ({len(paragraphs)} > {MAX_PARAGRAPHS})"
    return None


#: mirrors EXPLAINER_SYSTEM's "NO EXPOSED PLUMBING" ban list (report_explainer.py) — a teacher
#: answer that leans on the engine's own internal vocabulary instead of plain astrological
#: language is exactly the "gibberish" real feedback named. Logged-only for now (not a reject):
#: the real distribution needs a look before this becomes a hard gate (see build_analysis_corpus
#: module docstring / retrain plan Phase 1).
_JARGON_TERMS: tuple[str, ...] = ("witnesses", "data structure", "honest disclosure",
                                  "headline", "common outcomes")


def jargon_term_hits(text: str) -> dict[str, int]:
    """Count of each banned engine-jargon term in `text` (case-insensitive), for visibility in
    the run stats — does NOT affect `keep_reason`'s keep/reject decision."""
    low = text.lower()
    return {term: low.count(term) for term in _JARGON_TERMS if low.count(term)}


# ─── Raman voice anchors (Notable Horoscopes "Special Features" blocks) ─────────

_VOICE_INSTRUCTION = ("Write the 'Special Features' paragraph of a nativity reading in the "
                      "measured, scholarly voice of B. V. Raman's Notable Horoscopes.")


def voice_blocks(text: str, min_chars: int = 300, max_chars: int = 2400) -> list[str]:
    """Raman's own 'Special Features. — ...' prose blocks — style anchors. A block runs
    until the next all-caps-ish heading or double blank line; size-bounded."""
    out: list[str] = []
    for m in re.finditer(r"Special Features\. ?— ?", text):
        start = m.end()
        stop = len(text)
        nxt = re.search(r"\n\s*\n\s*\n|\n[A-Z][a-z]+ [A-Z][a-z]+\. ?—", text[start:])
        if nxt:
            stop = start + nxt.start()
        block = re.sub(r"\s+", " ", text[start:stop]).strip()
        if min_chars <= len(block) <= max_chars:
            out.append(block)
    return out


# ─── the run ────────────────────────────────────────────────────────────────────

def _row_key(meta: dict) -> str:
    return f"{meta.get('person_id')}::{meta.get('scope')}"


def existing_keys(out_path: Path) -> set[str]:
    """Resume support: keys already present in the output JSONL."""
    keys: set[str] = set()
    if out_path.exists():
        for line in out_path.open(encoding="utf-8"):
            try:
                keys.add(_row_key(json.loads(line).get("_meta", {})))
            except (json.JSONDecodeError, AttributeError):
                continue
    return keys


def distil(charts: Iterable[SampledChart], scopes: list[str], teacher, out_path: Path,
           min_grounding: float, ayanamsa: str = "lahiri", *, backend: str = "anthropic") -> dict:
    """The distillation loop. Appends kept rows to `out_path`; returns run counters.

    `backend` decides how a kept row's `_meta.source` is labeled — "teacher" ONLY for
    `backend="anthropic"` (real corpus-quality data), "smoke" for anything else (`--backend
    ollama`/`stub` are pipeline smoke-tests, per the module docstring, never real training
    signal). Fixes a real bug found live 2026-07-29: every kept row used to be hardcoded
    `"source": "teacher"` regardless of which backend actually produced it, so a $0 smoke-test
    run against gemma4:12b silently became indistinguishable from real Claude-teacher rows —
    85% of one corpus turned out to be mislabeled smoke-test output."""
    from app.raman_saab.chart.model import BirthData
    from app.raman_saab.detailed_report import build_detailed_report
    from app.raman_saab.report_json import to_report_dict
    from app.llm.citation_support import repair_citations
    from app.llm.report_explainer import (EXPLAINER_SYSTEM, _answer_from_text, build_evidence,
                                          build_prompt, explain)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    done = existing_keys(out_path)
    stats = {"charts": 0, "calls": 0, "kept": 0, "rejected": 0, "skipped_done": 0,
             "cast_failures": 0, "reject_reasons": {}, "jargon_hits": {}, "jargon_rows": 0,
             "citation_repairs": 0, "rows_repaired": 0}

    with out_path.open("a", encoding="utf-8") as fh:
        for c in charts:
            try:
                birth = BirthData(name=c.name or "corpus", year=c.year, month=c.month,
                                  day=c.day, hour=c.hour, minute=c.minute,
                                  tz_offset=c.tz_offset, latitude=c.latitude,
                                  longitude=c.longitude)
                r = build_detailed_report(birth, ayanamsa=ayanamsa)
                rdict = to_report_dict(r)
            except Exception:  # noqa: BLE001 — a bad chart never stops the batch
                stats["cast_failures"] += 1
                logger.warning("cast failed for %s; skipping", c.person_id)
                continue
            stats["charts"] += 1
            for scope in scopes:
                meta_key = _row_key({"person_id": c.person_id, "scope": scope})
                if meta_key in done:
                    stats["skipped_done"] += 1
                    continue
                ev = build_evidence(rdict, scope)
                if not ev.facts:
                    continue
                try:
                    ans = explain(ev, None, teacher)
                    stats["calls"] += 1
                except Exception as exc:  # noqa: BLE001
                    logger.warning("teacher failed on %s/%s: %s", c.person_id, scope, exc)
                    continue
                # CITATION SUPPORT (2026-08-02). Measured on the previous corpus: 12.8% of the
                # teacher's own checkable sentences cited a fact that did not contain the token
                # they asserted — 78% of those by pointing at the wrong fact, 22% by asserting
                # something no fact held. The student learned that distribution, which is why
                # mis-citation survived the Phase-7 evidence decomposition. Retarget the wrong
                # pointers deterministically (never inventing a citation), then re-score: the
                # remaining fabrications fail `refusal_reason` inside keep_reason() and the row
                # is rejected rather than teaching the student to assert uncomputed claims.
                repaired, n_repairs = repair_citations(ans.text, ev)
                if n_repairs:
                    ans = _answer_from_text(repaired, ev, model=ans.model)
                    stats["citation_repairs"] += n_repairs
                    stats["rows_repaired"] += 1
                reject = keep_reason(ans, min_grounding)
                if reject is not None:
                    stats["rejected"] += 1
                    stats["reject_reasons"][reject.split(":")[0]] = \
                        stats["reject_reasons"].get(reject.split(":")[0], 0) + 1
                    continue
                row = {"system": EXPLAINER_SYSTEM,
                       "prompt": build_prompt(ev, None, ()),
                       "completion": ans.text,
                       "_meta": {"person_id": c.person_id, "corpus": c.corpus,
                                 "scope": scope, "grounding": ans.grounding_ratio,
                                 "anchors": len(ans.anchors_used), "model": ans.model,
                                 "source": "teacher" if backend == "anthropic" else "smoke",
                                 "weight": 1}}
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                done.add(meta_key)
                stats["kept"] += 1
                hits = jargon_term_hits(ans.text)
                if hits:
                    stats["jargon_rows"] += 1
                    for term, n in hits.items():
                        stats["jargon_hits"][term] = stats["jargon_hits"].get(term, 0) + n
    return stats


#: default loss weight for a Raman VOICE anchor row. Voice rows are a FIXED set (426: 37 Notable
#: Horoscopes blocks + 389 golden verdict fragments) while the teacher half varies with how many
#: charts a run distils — so this weight silently decides the style/grounding balance. At weight 3
#: over 588 teacher rows (corpus v2) voice held 23.7% of the weighted token mass and produced the
#: crisp Raman voice; over 248 teacher rows (v3) the SAME weight would hand it 41.6%, tilting most
#: of the gradient onto prose that carries no [Fact N] at all — the opposite of what a
#: citation-discipline retrain needs. Tune it to the teacher set's size, don't leave it fixed.
DEFAULT_VOICE_WEIGHT = 3


def seed_voice(out_path: Path, weight: int = DEFAULT_VOICE_WEIGHT) -> int:
    """Append the Raman voice anchors (idempotent via the voice::N keys)."""
    if not NOTABLE_TEXT.exists():
        logger.warning("Notable Horoscopes text not found at %s; skipping voice seed",
                       NOTABLE_TEXT)
        return 0
    done = existing_keys(out_path)
    blocks = voice_blocks(NOTABLE_TEXT.read_text(encoding="utf-8", errors="ignore"))
    n = 0
    with out_path.open("a", encoding="utf-8") as fh:
        for i, block in enumerate(blocks):
            meta = {"person_id": f"voice::{i}", "scope": "voice"}
            if _row_key(meta) in done:
                continue
            fh.write(json.dumps({
                "system": "", "prompt": _VOICE_INSTRUCTION,
                "completion": "Special Features. — " + block,
                "_meta": {**meta, "corpus": "notable_horoscopes", "source": "raman_voice",
                          "weight": weight}}, ensure_ascii=False) + "\n")
            n += 1
    return n


# ─── Raman voice anchors (golden-fixture verdict_prose fragments) ───────────────

_GOLDEN_VOICE_INSTRUCTION = ("Write ONE short, decisive sentence stating a single astrological "
                             "verdict, in the measured, terse, declarative voice of B. V. "
                             "Raman's own worked-chart judgments.")


def golden_verdict_prose_fragments(path: Path = GOLDEN_FIXTURES) -> list[str]:
    """Every non-null `expected_verdicts.*.verdict_prose` string in the golden-accuracy fixture
    — short, authenticated Raman diction (mean ~20 words), in stable file order. Malformed or
    non-JSON lines (the fixture carries the occasional `#`-prefixed section-marker comment) are
    skipped rather than failing the whole extraction."""
    if not path.exists():
        logger.warning("golden fixtures not found at %s; skipping golden voice extraction", path)
        return []
    out: list[str] = []
    for line in path.open(encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        for verdict in (row.get("expected_verdicts") or {}).values():
            prose = verdict.get("verdict_prose")
            if prose:
                out.append(prose.strip())
    return out


def seed_golden_voice(out_path: Path, weight: int = DEFAULT_VOICE_WEIGHT) -> int:
    """Append the golden-fixture Raman voice anchors (idempotent via the golden_voice::N keys).
    A second, much larger voice-anchor source alongside `seed_voice()` — see GOLDEN_FIXTURES."""
    done = existing_keys(out_path)
    # look up the module-level GOLDEN_FIXTURES fresh (not as a bound-at-def-time default arg)
    # so tests can monkeypatch it, matching how NOTABLE_TEXT/seed_voice already behaves.
    fragments = golden_verdict_prose_fragments(GOLDEN_FIXTURES)
    n = 0
    with out_path.open("a", encoding="utf-8") as fh:
        for i, fragment in enumerate(fragments):
            meta = {"person_id": f"golden_voice::{i}", "scope": "voice"}
            if _row_key(meta) in done:
                continue
            fh.write(json.dumps({
                "system": "", "prompt": _GOLDEN_VOICE_INSTRUCTION,
                "completion": fragment,
                "_meta": {**meta, "corpus": "raman_goldens", "source": "raman_golden_voice",
                          "weight": weight}}, ensure_ascii=False) + "\n")
            n += 1
    return n


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--limit", type=int, default=50, help="charts to sample")
    ap.add_argument("--offset", type=int, default=0, help="skip the first N sampled charts")
    ap.add_argument("--scopes", default="digest,summary",
                    help="comma list of evidence scopes per chart")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--backend", choices=("anthropic", "ollama", "stub"),
                    default="anthropic")
    ap.add_argument("--min-grounding", type=float, default=0.75,
                    help="corpus bar (stricter than the serving floor 0.6)")
    ap.add_argument("--seed-voice", action="store_true",
                    help="also fold in Raman's Special Features voice anchors")
    ap.add_argument("--voice-weight", type=int, default=DEFAULT_VOICE_WEIGHT,
                    help=f"loss weight per voice-anchor row (default {DEFAULT_VOICE_WEIGHT}). The "
                         "voice set is a fixed 426 rows while the teacher half scales with "
                         "--limit, so this decides the style/grounding balance — lower it when "
                         "the teacher set is small (see DEFAULT_VOICE_WEIGHT).")
    ap.add_argument("--allow-non-anthropic-teacher", action="store_true",
                    help="allow --backend ollama/stub to write rows into a real corpus file. "
                         "Refused by default: these backends are pipeline smoke-tests (see "
                         "module docstring) and rows they produce are labeled _meta.source="
                         "'smoke', never 'teacher' — real corpus rows need --backend anthropic.")
    args = ap.parse_args(argv)

    if args.backend != "anthropic" and not args.allow_non_anthropic_teacher:
        raise SystemExit(
            f"--backend {args.backend!r} is a $0 pipeline smoke-test only (see module "
            "docstring) — it must not write real corpus rows. Pass "
            "--allow-non-anthropic-teacher to force it anyway (rows will be labeled "
            "_meta.source='smoke', excluded from training/eval by construction).")

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    teacher = make_teacher(args.backend)
    charts = sample_charts(args.limit, args.offset)
    logger.info("sampled %d timed charts (backend=%s, scopes=%s)",
                len(charts), args.backend, args.scopes)
    stats = distil(charts, [s.strip() for s in args.scopes.split(",") if s.strip()],
                   teacher, args.out, args.min_grounding, backend=args.backend)
    if args.seed_voice:
        stats["voice_rows"] = seed_voice(args.out, args.voice_weight)
        stats["golden_voice_rows"] = seed_golden_voice(args.out, args.voice_weight)
        stats["voice_weight"] = args.voice_weight
    logger.info("run complete: %s", json.dumps(stats))
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
