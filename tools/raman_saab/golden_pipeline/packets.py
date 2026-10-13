"""Reviewer packets. MUST NOT import app.raman_saab.judges (blindness by construction)."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Final

from tools.raman_saab.golden_pipeline.sources import parse_citation, passage

SCHEMA_TEXT: Final[str] = """Reply with ONLY this JSON object, nothing else:
{"decision": "CONFIRM|REVISE|REJECT",
 "kind": "conclusion|observation|splice|not_found",
 "verdict": "afflicted|mixed|favourable",
 "signification": "<matter judged, snake_case>",
 "decisive_quote": "<= 40 words copied from the passage",
 "quote_line": <the line number where the quote starts>,
 "reason": "<one sentence>"}"""

_INTROS: Final[dict[str, str]] = {
    "A": "You are checking one proposed label against B. V. Raman's printed text.",
    "B": "Read the passage from Raman's book below and judge one candidate label.",
    "C": "A third, independent reading is needed for one label drawn from Raman's text.",
}

_QUESTION: Final[str] = (
    "The single question: is the candidate Raman's CONCLUSION about the matter, or an "
    "OBSERVATION about one contributing factor he is still weighing?\n"
    "- CONFIRM: it is his conclusion and the label (verdict + signification) is right.\n"
    "- REVISE: it is his conclusion but the verdict or signification is wrong; give the "
    "correct ones.\n"
    "- REJECT: it is an observation, a splice of unrelated text, or not in the passage.\n"
    "Scale: afflicted < mixed < favourable. Quote Raman verbatim from the passage.")


def render(item: dict[str, Any], lines: list[str], reviewer: str, flags: list[str]) -> str:
    _book, start, end = parse_citation(item["citation"])
    flag_line = (f"\nExtraction flags (possible corruption): {', '.join(flags)}\n"
                 if flags else "")
    return (f"{_INTROS[reviewer]}\n\n{_QUESTION}\n\n"
            f"Candidate (house {item['house']}, cited {item['citation']}):\n"
            f"  signification: {item['signification']}\n"
            f"  proposed verdict: {item['verdict']}\n"
            f"  extracted prose: {item['verdict_prose']}\n{flag_line}\n"
            f"Passage (line| text):\n{passage(lines, start, end)}\n\n{SCHEMA_TEXT}\n")


def packet_path(run: Path, item_id: str, reviewer: str) -> Path:
    return run / "packets" / f"{item_id.replace('#', '__')}.{reviewer}.md"


def answer_path(run: Path, item_id: str, reviewer: str) -> Path:
    return run / "answers" / f"{item_id.replace('#', '__')}.{reviewer}.json"
