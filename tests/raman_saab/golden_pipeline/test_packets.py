from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from tools.raman_saab.golden_pipeline import packets as P
from tools.raman_saab.golden_pipeline import sources as S

LINES = S.read_lines(Path(__file__).parent / "fixtures" / "excerpt.md")
ITEM = {"item_id": "NH.chart_1#H4", "record_id": "NH.chart_1", "house": 4, "book": "NH",
        "citation": "NH:6", "signification": "mother", "verdict": "afflicted",
        "verdict_prose": "The native lost his mother very early in life"}


class TestPacket:
    def test_packet_contains_question_schema_and_numbered_passage(self):
        """A packet is self-contained: question, schema, real line numbers."""
        text = P.render(ITEM, LINES, reviewer="A", flags=[])
        assert "CONCLUSION" in text and "OBSERVATION" in text
        assert '"decision"' in text
        assert "6| Conclusion" in text

    def test_reviewers_get_different_wording_same_schema(self):
        """A, B, C are worded differently so they don't share a phrasing failure."""
        a, b, c = (P.render(ITEM, LINES, reviewer=r, flags=[]) for r in "ABC")
        assert len({a, b, c}) == 3
        assert all(P.SCHEMA_TEXT in t for t in (a, b, c))

    def test_splice_flags_are_disclosed(self):
        """A flagged row goes to review WITH its flag, never silently dropped."""
        text = P.render(ITEM, LINES, reviewer="A", flags=["footnote"])
        assert "footnote" in text

    def test_packet_contains_no_engine_output(self):
        """Blindness by construction: building packets never imports the judge."""
        code = ("import sys; import tools.raman_saab.golden_pipeline.packets; "
                "bad=[m for m in sys.modules if m.startswith('app.raman_saab.judges')]; "
                "print(bad); sys.exit(1 if bad else 0)")
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr

    def test_packet_text_has_no_engine_words(self):
        """No engine verdict field can leak into the text."""
        text = P.render(ITEM, LINES, reviewer="B", flags=[]).lower()
        assert "engine" not in text and "fidelity" not in text and "ratchet" not in text


class TestMultiCitation:
    def test_passage_contains_both_blocks(self):
        """Every cited span appears, with line numbers, separated by an ellipsis line."""
        lines = [f"text{n}" for n in range(1, 401)]
        item = {**ITEM, "citation": "NH:50", "citations": ["NH:50", "NH:300-301"]}
        text = P.render(item, lines, reviewer="A", flags=[])
        assert "50| text50" in text and "300| text300" in text and "301| text301" in text
        assert "\n...\n" in text and "150| text150" not in text

    def test_overlapping_windows_merge(self):
        """Close citations yield one contiguous block, no ellipsis."""
        lines = [f"text{n}" for n in range(1, 201)]
        item = {**ITEM, "citation": "NH:50", "citations": ["NH:50", "NH:70"]}
        assert "\n...\n" not in P.render(item, lines, reviewer="A", flags=[])
