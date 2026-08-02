"""Evaluate the local analysis student vs the Claude teacher on held-out corpus rows.

For each held-out row of the Phase-2 corpus, the candidate model (default: the Ollama-
served model, e.g. `astro-analyst` after `ollama create`) answers the SAME prompt the
teacher answered; both texts are scored with the SAME code-level machinery the serving
path uses (`provenance_check` + `refusal_reason`), PLUS a length check against `--max-words`
(2026-07-29 — the guard alone never judged length, so a maximally verbose answer could pass
perfectly), PLUS citation SUPPORT (2026-08-02 — the guard scores citation PRESENCE, so an answer
narrating one fact's numbers under another fact's citation scored a perfect 1.0; that was the
live residual complaint and nothing measured it). Reported per side: guard pass-rate, crisp
pass-rate, citation pass-rate, mean grounding ratio, mean anchors, mean length.

STANDING RULE: the student ships as the Ollama default only if it clears `guard_pass_rate`,
`crisp_pass_rate` AND `citation_pass_rate` — otherwise the stock model stays while training
iterates (the app works either way; a guard-failing answer just serves engine prose). Compare
each against the TEACHER's own numbers in the same run, never against an absolute: the teacher
scored 87.2% citation-clean on checkable sentences in the corpus that trained the last student,
so a student at parity with the teacher is at the ceiling this corpus can teach.

Hold-out selection is a stable hash of `_meta.person_id` (last hex digit in a chosen
set), so the same rows are held out across corpus growth — training must EXCLUDE them
by the same rule when this matters.

Usage:
    py -3.12 -m app.medini.ml.eval_analysis_llm --dataset data/ml_runs/analysis_corpus/sft.jsonl \\
        --backend ollama --limit 20
    py -3.12 -m app.medini.ml.eval_analysis_llm --backend stub --limit 5   # plumbing check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

#: person_ids whose blake2b hex ends in one of these digits are HELD OUT (~1/8 of rows).
HOLDOUT_SUFFIXES = ("0", "8")

#: matches build_analysis_corpus.py's MAX_WORDS ceiling (2026-07-29, after real feedback: "too
#: lengthy not crisp too much gibberish"). Added because this eval previously reported
#: `mean_chars` but had NO pass/fail on length — a maximally verbose, jargon-dense answer could
#: score guard_pass_rate=1.0 perfectly, since refusal_reason only checks grounding/citations,
#: never length. STANDING RULE: a retrained model ships only after clearing BOTH
#: `guard_pass_rate` AND `crisp_pass_rate` on held-out rows — not guard_pass_rate alone.
MAX_WORDS_DEFAULT = 220


def is_holdout(person_id: str) -> bool:
    return hashlib.blake2b(str(person_id).encode(),
                           digest_size=8).hexdigest()[-1] in HOLDOUT_SUFFIXES


def evidence_from_prompt(prompt: str):
    """Reconstruct a scoring Evidence from the fact lines the prompt itself carries —
    the same fact numbers the model may cite.

    The match is anchored to LINE START and the first definition of each N wins: the prompt's own
    instruction block also says "[Fact 1] is the honesty frame..." (report_explainer.py:535), and
    an unanchored scan let that sentence be read as Fact 1's text — which then made every correct
    citation of the real Fact 1 look unsupported."""
    from app.llm.report_explainer import Evidence, Fact
    seen: dict[int, str] = {}
    for m in re.finditer(r"^\[Fact (\d+)\] ([^\n]+)", prompt, re.M):
        seen.setdefault(int(m.group(1)), m.group(2).strip())
    return Evidence(scope="eval",
                    facts=tuple(Fact(n=n, text=t) for n, t in sorted(seen.items())))


def score(text: str, ev, min_grounding: float, max_words: int = MAX_WORDS_DEFAULT) -> dict:
    from app.llm.citation_support import audit_citations
    from app.llm.report_explainer import refusal_reason, _answer_from_text
    ans = _answer_from_text(text, ev, model="eval")
    reason = refusal_reason(ans, min_grounding)
    words = len(text.split())
    # citation SUPPORT (2026-08-02) — the metric the earlier eval could not see. guard_pass_rate
    # scores citation PRESENCE, so an answer that cites a real fact while narrating a DIFFERENT
    # fact's numbers scored a perfect 1.0. That was the live residual complaint, and without this
    # column a retrain aimed at it cannot be judged either way.
    audit = audit_citations(text, ev)
    return {"passes": reason is None, "reason": reason,
            "grounding": ans.grounding_ratio, "anchors": len(ans.anchors_used),
            "chars": len(text), "words": words, "crisp_ok": words <= max_words,
            "mis_attributed": len(audit.mis_attributed),
            "unsupported": len(audit.unsupported),
            "checked_sentences": audit.checked_sentences,
            "cite_ok": audit.is_clean}


def make_candidate(backend: str, model: str | None, num_ctx: int | None = None,
                   think: bool | None = None, timeout: float = 120.0):
    if backend == "ollama":
        from app.core.config import settings
        from app.llm.client import OllamaClient
        return OllamaClient(settings.OLLAMA_HOST, model or settings.OLLAMA_MODEL,
                            max(settings.OLLAMA_TIMEOUT_SECONDS, timeout),
                            num_ctx=num_ctx, think=think)
    if backend == "stub":
        from app.llm.client import StubClient
        return StubClient("The engine reads the Lagna with care [Fact 1]. " * 20)
    raise SystemExit(f"unknown backend {backend!r}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dataset", type=Path,
                    default=Path("data/ml_runs/analysis_corpus/sft.jsonl"))
    ap.add_argument("--backend", choices=("ollama", "stub"), default="ollama")
    ap.add_argument("--model", default=None, help="override the served model tag")
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--min-grounding", type=float, default=0.6,
                    help="the SERVING floor (config REPORT_LLM_GROUNDING_MIN)")
    ap.add_argument("--max-words", type=int, default=MAX_WORDS_DEFAULT,
                    help="crispness ceiling — matches build_analysis_corpus.py's MAX_WORDS")
    ap.add_argument("--num-ctx", type=int, default=None,
                    help="Ollama num_ctx. Evidence prompts run ~3.1k tokens, so a model left on "
                         "the 4k default has little room to answer — set 8192 for big models.")
    ap.add_argument("--no-think", dest="think", action="store_const", const=False, default=None,
                    help="disable reasoning on a thinking-capable model (see OllamaClient): "
                         "gemma4:12b otherwise spends its whole budget thinking and returns an "
                         "EMPTY response on every long prompt.")
    ap.add_argument("--timeout", type=float, default=120.0,
                    help="per-call seconds; a 12B needs well over the 120s default on this class "
                         "of hardware.")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    rows = []
    for line in args.dataset.open(encoding="utf-8"):
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        meta = r.get("_meta", {})
        if meta.get("source") == "teacher" and is_holdout(meta.get("person_id", "")):
            rows.append(r)
        if len(rows) >= args.limit:
            break
    if not rows:
        raise SystemExit("no held-out teacher rows found — grow the corpus first "
                         f"(suffixes {HOLDOUT_SUFFIXES} of the person_id hash)")
    logger.info("evaluating %d held-out rows (backend=%s)", len(rows), args.backend)

    cand = make_candidate(args.backend, args.model, args.num_ctx, args.think,
                          args.timeout)
    sides: dict[str, list[dict]] = {"student": [], "teacher": []}
    for r in rows:
        ev = evidence_from_prompt(r["prompt"])
        sides["teacher"].append(score(r["completion"], ev, args.min_grounding, args.max_words))
        try:
            text = cand.complete(f"{r.get('system', '')}\n\n{r['prompt']}".strip())
        except Exception as exc:  # noqa: BLE001
            logger.warning("candidate failed: %s", exc)
            # MUST carry every key `score()` returns — the aggregation below reads them all, and
            # a partial dict turns "the model under test failed" into a KeyError crash that
            # discards the whole run (hit 2026-08-03 when gemma4:12b returned empty every call,
            # losing 35 minutes of evaluation to a missing 'cite_ok').
            sides["student"].append({"passes": False, "reason": f"client: {exc}",
                                     "grounding": 0.0, "anchors": 0, "chars": 0,
                                     "words": 0, "crisp_ok": False, "cite_ok": False,
                                     "mis_attributed": 0, "unsupported": 0,
                                     "checked_sentences": 0})
            continue
        sides["student"].append(score(text, ev, args.min_grounding, args.max_words))

    report = {}
    for side, scores in sides.items():
        n = len(scores)
        report[side] = {
            "n": n,
            "guard_pass_rate": round(sum(s["passes"] for s in scores) / n, 3),
            "crisp_pass_rate": round(sum(s["crisp_ok"] for s in scores) / n, 3),
            "citation_pass_rate": round(sum(s["cite_ok"] for s in scores) / n, 3),
            "mean_mis_attributed": round(sum(s["mis_attributed"] for s in scores) / n, 2),
            "mean_unsupported": round(sum(s["unsupported"] for s in scores) / n, 2),
            "mean_checked_sentences": round(sum(s["checked_sentences"] for s in scores) / n, 1),
            "mean_grounding": round(sum(s["grounding"] for s in scores) / n, 3),
            "mean_anchors": round(sum(s["anchors"] for s in scores) / n, 1),
            "mean_chars": round(sum(s["chars"] for s in scores) / n),
            "mean_words": round(sum(s["words"] for s in scores) / n, 1),
            "fail_reasons": sorted({s["reason"].split(":")[0] for s in scores
                                    if s["reason"]})[:6],
        }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
