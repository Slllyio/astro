from __future__ import annotations

from pathlib import Path

from tools.raman_saab.golden_pipeline import sources as S
from tools.raman_saab.golden_pipeline import splice_check as SC

LINES = S.read_lines(Path(__file__).parent / "fixtures" / "excerpt.md")


class TestSpliceFlags:
    def test_footnote_splice_flagged(self):
        """NH.chart_5 class: a '* A ...' footnote stitched into the conclusion."""
        prose = "lost his mother very early in life * A learned scholar has observed"
        assert "footnote" in SC.flags(prose, LINES, 6)

    def test_section_heading_splice_flagged(self):
        """HTJAH-I.x75 class: the next section's heading swallowed into the prose."""
        prose = "brought up by relatives. Education and Learning The fourth lord"
        assert "section_heading" in SC.flags(prose, LINES, 6)

    def test_two_passage_splice_flagged(self):
        """NH.chart_41 class: two non-adjacent passages joined, dropping what lay between."""
        prose = "The Lagna is weak, being occupied by debilitated Mars. The fourth lord is well placed."
        assert "two_passage" in SC.flags(prose, LINES, 4)

    def test_clean_contiguous_prose_has_no_flags(self):
        """A true contiguous conclusion carries no flags."""
        prose = "The native lost his mother very early in life and was brought up by relatives."
        assert SC.flags(prose, LINES, 6) == []

    def test_ocr_image_artifact_flagged(self):
        """Converter junk inside prose (seen in the fixture) is a corruption flag."""
        prose = "no elder brother The linked image cannot be displayed. The file may"
        assert "artifact" in SC.flags(prose, LINES, 6)
