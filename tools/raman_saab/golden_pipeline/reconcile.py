"""Two-or-three blind answers -> one outcome. Pure; no I/O."""
from __future__ import annotations

from collections import Counter
from typing import Any


def _key(a: dict[str, Any]) -> tuple:
    if a["decision"] == "REJECT":
        return ("REJECT",)
    return ("ACCEPT", a["verdict"], a["signification"].strip().casefold())


def _outcome(item: dict[str, Any], key: tuple, answers: dict[str, Any]) -> dict[str, Any]:
    quotes = {r: (a["decisive_quote"], a["quote_line"]) for r, a in answers.items()
              if _key(a) == key}
    if key[0] == "REJECT":
        # "the passage holds no conclusion" says the WINDOW failed, not the label: re-queueable
        agreeing = [a for a in answers.values() if _key(a) == key]
        if all(a.get("kind") == "not_found" for a in agreeing):
            return {"outcome": "NOT_FOUND", "quotes": quotes}
        return {"outcome": "REJECTED", "quotes": quotes}
    first = next(a for a in answers.values() if _key(a) == key)  # keep reviewer's own string
    verdict, sig = first["verdict"], first["signification"]
    return {"outcome": "CONFIRMED", "verdict": verdict, "signification": sig,
            "revised": _key({"decision": "CONFIRM", "verdict": verdict, "signification": sig})
            != _key({"decision": "CONFIRM", "verdict": item["verdict"],
                     "signification": item["signification"]}),
            "quotes": quotes}


def reconcile(item: dict[str, Any], answers: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Decide one outcome from blind answers A, B (and optional tiebreak C)."""
    if "A" not in answers or "B" not in answers:
        return {"outcome": "INCOMPLETE"}
    if not all(a.get("quote_ok") for a in answers.values()):
        return {"outcome": "UNVERIFIED"}
    if _key(answers["A"]) == _key(answers["B"]):
        return _outcome(item, _key(answers["A"]), answers)
    if "C" not in answers:
        return {"outcome": "TIEBREAK"}
    key, n = Counter(_key(a) for a in answers.values()).most_common(1)[0]
    return _outcome(item, key, answers) if n >= 2 else {"outcome": "CONTESTED"}
