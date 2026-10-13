"""Load answers for one item, validate, verify quotes against the source, reconcile."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.raman_saab.golden_pipeline import answers as A
from tools.raman_saab.golden_pipeline.packets import answer_path
from tools.raman_saab.golden_pipeline.reconcile import reconcile
from tools.raman_saab.golden_pipeline.sources import quote_in_windows, spans


def ingest_item(run: Path, item: dict[str, Any], lines: list[str]) -> dict[str, Any]:
    got: dict[str, dict[str, Any]] = {}
    invalid: list[str] = []
    for r in "ABC":
        p = answer_path(run, item["item_id"], r)
        if not p.is_file():
            continue
        try:
            a = A.validate(A.parse(p.read_text(encoding="utf-8")))
        except A.InvalidAnswer:
            invalid.append(r)
            continue
        got[r] = {**a, "quote_ok": quote_in_windows(lines, a["decisive_quote"], spans(item))}
    decision = reconcile(item, got)
    return {"item_id": item["item_id"], "record_id": item["record_id"],
            "house": item["house"], "proposed_verdict": item["verdict"],
            "proposed_signification": item["signification"], "invalid": invalid,
            "reasons": {r: a["reason"] for r, a in got.items()}, **decision}
