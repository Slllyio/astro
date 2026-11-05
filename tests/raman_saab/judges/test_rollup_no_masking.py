"""The house headline never hides an afflicted sub-matter (audit 2026-10-23)."""
from __future__ import annotations

from app.raman_saab.judges.house_template import _rollup


class TestRollupNoMasking:
    def test_afflicted_reaches_headline_over_mixed_and_favourable(self):
        """afflicted + mixed + favourable used to read 'mixed'; the afflicted sub-matter now leads."""
        assert _rollup(("favourable", "mixed", "afflicted")) == "afflicted"

    def test_mixed_and_favourable_alone_read_mixed(self):
        """A contradicted house with no afflicted sub-matter still cannot read cleanly favourable."""
        assert _rollup(("favourable", "mixed")) == "mixed"

    def test_worst_decided_verdict_otherwise(self):
        """Without the mixed+favourable pair, the worst decided verdict wins."""
        assert _rollup(("favourable", "afflicted")) == "afflicted"
        assert _rollup(("favourable", "insufficient-evidence")) == "favourable"
        assert _rollup(()) == "insufficient-evidence"
