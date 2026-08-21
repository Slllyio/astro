"""Every citation in the engine must land on actual text, not merely on a line that exists.

`sources.verify` asks one question — is this line number within the file? — and a citation
that survives it can still be pointing at nothing. That is not hypothetical: e773041 replaced
the Notable Horoscopes derivation with one 2,790 lines longer, and three anchors in
`yoga_deep_read.NH_EXAMPLES` came to rest on BLANK lines. Click-to-source on Hamsa, Malavya,
Sasa and Ruchaka returned an empty passage to the reader, and every existing check stayed
green, because the line numbers were still in range.

A fourth anchor moved onto the wrong text entirely: `SYN_R14_BR_LIBRA_SATURN_DASA` cited
NH:9580 for Bhavartha Ratnakara's Libra dictum and landed on a 1876 birth-details block. No
mechanical test can catch that one — a wrong line is still a non-blank line — so this file
checks what it can, and the rest is re-validation by reading.

Scoped to the corpus being present; skips where it is not, CI included.
"""
from __future__ import annotations

import pathlib
import re
import subprocess

import pytest

from corpus_presence import needs_corpus

from app.raman_saab.doctrine import sources

_APP = pathlib.Path(__file__).resolve().parents[3] / "app"
#: WORK:line or WORK:start-end, as the tokens appear in code and report prose.
_TOKEN = re.compile(r"\b([A-Z][A-Za-z]*(?:-[A-Za-z0-9]+)*):(\d+)(?:-(\d+))?\b")


def _tokens() -> set[str]:
    """Every citation token written anywhere in the engine's Python."""
    out = subprocess.run(
        ["grep", "-rhoE", r"\b[A-Z][A-Za-z]*(-[A-Za-z0-9]+)*:[0-9]+(-[0-9]+)?\b",
         str(_APP), "--include=*.py"], capture_output=True, text=True).stdout
    return {t for t in out.split() if _TOKEN.match(t)}


@pytest.fixture(scope="module")
def resolvable() -> list[tuple[str, str]]:
    """(token, text) for every token the corpus can resolve at all.

    Tokens that do not resolve are NOT failures here: the classical non-citable works are
    refused on purpose (the divergence firewall), and a book may simply not be vendored on
    this machine. This file is about anchors that resolve to nothing, which is different.
    """
    out = []
    for tok in sorted(_tokens()):
        p = sources.passage(tok, context=0)
        if p is not None:
            out.append((tok, str(p.get("text", ""))))
    return out


@needs_corpus
class TestAnchorsLandOnText:
    def test_the_corpus_resolves_a_useful_number_of_anchors(self, resolvable):
        """Guard the guard: if resolution broke wholesale, the blank check below would pass
        vacuously by having nothing left to check."""
        assert len(resolvable) > 100, f"only {len(resolvable)} anchors resolved at all"

    def test_no_anchor_resolves_to_blank(self, resolvable):
        """The exact defect: a line number still in range after the file grew, now pointing
        at whitespace. The reader sees an empty source panel and the suite sees nothing."""
        blank = [tok for tok, text in resolvable if not text.strip()]
        assert not blank, (
            f"{len(blank)} citation(s) land on a blank line — the file they point into has "
            f"almost certainly changed under them: {sorted(blank)}")

    def test_the_re_mined_yoga_anchors_name_their_own_yoga(self):
        """`NH_EXAMPLES` promises the passage around each line names the nativity in which
        that yoga appears. After a re-mine that is checkable directly: the cited line must
        contain the yoga's own name."""
        from app.raman_saab.yoga_deep_read import NH_EXAMPLES
        wrong = []
        for yoga, toks in NH_EXAMPLES.items():
            for tok in toks:
                p = sources.passage(tok, context=0)
                # Skipping an unresolved token made this test pass when an anchor was
                # malformed or out of range — the two failures a re-mine is most likely to
                # introduce. The whole test is corpus-gated, so absence is already handled.
                assert p is not None, f"{yoga} @ {tok} resolves to nothing"
                if yoga.lower() not in str(p.get("text", "")).lower():
                    wrong.append(f"{yoga} @ {tok}")
        assert not wrong, f"anchors that do not name their yoga: {wrong}"
