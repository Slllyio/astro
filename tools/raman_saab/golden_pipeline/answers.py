"""Parse and validate one reviewer answer."""
from __future__ import annotations

import json
import re
from typing import Any, Final

DECISIONS: Final = {"CONFIRM", "REVISE", "REJECT"}
KINDS: Final = {"conclusion", "observation", "splice", "not_found"}
VERDICTS: Final = {"afflicted", "mixed", "favourable"}
MAX_QUOTE_WORDS: Final = 40


class InvalidAnswer(ValueError):
    """The reply does not meet the reviewer schema."""


def parse(text: str) -> dict[str, Any]:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise InvalidAnswer("no JSON object in reply")
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError as exc:
        raise InvalidAnswer(f"bad JSON: {exc}") from exc


def validate(a: dict[str, Any]) -> dict[str, Any]:
    if a.get("decision") not in DECISIONS:
        raise InvalidAnswer(f"decision={a.get('decision')!r}")
    if a.get("kind") not in KINDS:
        raise InvalidAnswer(f"kind={a.get('kind')!r}")
    if a["decision"] != "REJECT":
        if a["kind"] != "conclusion":
            raise InvalidAnswer(f"{a['decision']} requires kind='conclusion', got {a['kind']!r}")
        if a.get("verdict") not in VERDICTS:
            raise InvalidAnswer(f"verdict={a.get('verdict')!r}")
    if not isinstance(a.get("signification"), str) or not a["signification"].strip():
        raise InvalidAnswer("signification missing")
    q = a.get("decisive_quote")
    if not isinstance(q, str) or not q.strip() or len(q.split()) > MAX_QUOTE_WORDS:
        raise InvalidAnswer("decisive_quote missing, empty or over 40 words")
    ql = a.get("quote_line")
    if not isinstance(ql, int) or isinstance(ql, bool):
        raise InvalidAnswer("quote_line must be an int")
    if not isinstance(a.get("reason"), str):
        raise InvalidAnswer("reason must be a string")
    return a
