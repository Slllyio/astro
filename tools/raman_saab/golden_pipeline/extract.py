"""Select DRAFT verdicts awaiting adjudication from a goldens-format JSONL.

New rows come from the existing deterministic extractors, e.g.
    py -3.12 -m tools.raman_saab.extract_htjah_goldens --emit > new.jsonl
and are fed here with --input new.jsonl. Default input is the committed fixture.
"""
from __future__ import annotations

from typing import Any

_PENDING = "DRAFT"
_REJECTED_PREFIX = "REJECTED"


def select_pending(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for rec in records:
        cites = rec.get("citations") or []
        if not cites:
            continue
        for tag, v in (rec.get("expected_verdicts") or {}).items():
            if v.get("verdict_review") != _PENDING:
                continue
            if str(v.get("review_note", "")).startswith(_REJECTED_PREFIX):
                continue
            items.append({
                "item_id": f"{rec['id']}#{tag}",
                "record_id": rec["id"],
                "house": int(tag.lstrip("H")),
                "book": rec["book"],
                "citation": cites[0],
                "citations": list(cites),
                "signification": v["signification"],
                "verdict": v["verdict"],
                "verdict_prose": v.get("verdict_prose", ""),
            })
    return items
