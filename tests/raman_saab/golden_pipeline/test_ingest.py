from __future__ import annotations

import json
from pathlib import Path

from tools.raman_saab.golden_pipeline import ingest as I
from tools.raman_saab.golden_pipeline import packets as P
from tools.raman_saab.golden_pipeline import sources as S

LINES = S.read_lines(Path(__file__).parent / "fixtures" / "excerpt.md")
ITEM = {"item_id": "NH.chart_1#H4", "record_id": "NH.chart_1", "house": 4, "book": "NH",
        "citation": "NH:6", "signification": "mother", "verdict": "afflicted",
        "verdict_prose": "x"}


def _write(run, reviewer, quote="lost his mother very early in life", extra=None):
    a = {"decision": "CONFIRM", "kind": "conclusion", "verdict": "afflicted",
         "signification": "mother", "decisive_quote": quote, "quote_line": 6, "reason": "r"}
    a.update(extra or {})
    p = P.answer_path(run, ITEM["item_id"], reviewer)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(a), encoding="utf-8")


class TestIngest:
    def test_agreeing_verified_answers_confirm(self, tmp_path):
        """Two valid, source-verified, agreeing answers confirm."""
        _write(tmp_path, "A"); _write(tmp_path, "B")
        d = I.ingest_item(tmp_path, ITEM, LINES)
        assert d["outcome"] == "CONFIRMED" and d["item_id"] == ITEM["item_id"]

    def test_quote_not_in_source_stays_draft(self, tmp_path):
        """A fabricated quote makes the item UNVERIFIED, never CONFIRMED."""
        _write(tmp_path, "A", quote="the native gained a great fortune abroad")
        _write(tmp_path, "B")
        assert I.ingest_item(tmp_path, ITEM, LINES)["outcome"] == "UNVERIFIED"

    def test_invalid_answer_counts_as_missing(self, tmp_path):
        """A schema-invalid reply is re-dispatched, not scored."""
        _write(tmp_path, "A", extra={"decision": "MAYBE"}); _write(tmp_path, "B")
        d = I.ingest_item(tmp_path, ITEM, LINES)
        assert d["outcome"] == "INCOMPLETE" and d["invalid"] == ["A"]

    def test_rerun_is_idempotent(self, tmp_path):
        """Ingesting twice yields identical decisions."""
        _write(tmp_path, "A"); _write(tmp_path, "B")
        assert I.ingest_item(tmp_path, ITEM, LINES) == I.ingest_item(tmp_path, ITEM, LINES)


    def test_quote_under_second_citation_verifies(self, tmp_path):
        """The verdict often sits under a later citation; a quote there is verified."""
        lines = ["filler"] * 400
        lines[299] = "The native lost his mother very early in life"
        item = {**ITEM, "citation": "NH:6", "citations": ["NH:6", "NH:300"]}
        _write(tmp_path, "A"); _write(tmp_path, "B")
        assert I.ingest_item(tmp_path, item, lines)["outcome"] == "CONFIRMED"
