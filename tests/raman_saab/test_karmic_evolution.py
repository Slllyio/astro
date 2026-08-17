"""Paired test for app/raman_saab/karmic_evolution.py (v30, the walled Jaimini layer).

P0 fix (docs/raman_saab/REPORT_CRITIQUE_2026-08-17.md): the section must NEVER vanish
just because the JAIMINI-9 verbatim pull is empty — the AK, Karakamsa, Upapada and the
D-20/D-60 cores are all computed. The quote field carries an honest-absence line, so no
renderer needs a change. The corpus-present path (real quote, resolving cite, the wall)
stays pinned by test_report_template_contract.py::TestKarmicEvolution.
"""
from __future__ import annotations

import pytest

from app.raman_saab.chart.model import BirthData
from app.raman_saab.detailed_report import build_detailed_report
from app.raman_saab.karmic_evolution import (KARAKAMSA_DOCTRINE, KarmicEvolution,
                                             build_karmic_evolution)

_CANONICAL = BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59)


@pytest.fixture(scope="module")
def report():
    return build_detailed_report(_CANONICAL)


class TestKarmicEvolutionWithoutCorpus:
    def test_empty_pull_still_builds_a_renderable_section(self, report, monkeypatch):
        """passage() returning None (corpus absent) yields a full KarmicEvolution, not None."""
        import app.raman_saab.karmic_evolution as ke
        monkeypatch.setattr(ke, "passage", lambda *a, **k: None)
        kv = build_karmic_evolution(report)
        assert isinstance(kv, KarmicEvolution)
        # all COMPUTED parts still present
        assert kv.atmakaraka in ("Sun", "Moon", "Mars", "Mercury", "Jupiter",
                                 "Venus", "Saturn")   # the 7-karaka lock holds
        assert kv.frame
        # the D-20/D-60 deep-read cores the report already builds flow through
        assert kv.d20_core is not None
        assert kv.d60_core is not None

    def test_absence_line_reuses_the_existing_citation(self, report, monkeypatch):
        """The absence line names the frozen JAIMINI-9 range already in the code —
        never an invented line number — and the cite field is unchanged."""
        import app.raman_saab.karmic_evolution as ke
        monkeypatch.setattr(ke, "passage", lambda *a, **k: None)
        kv = build_karmic_evolution(report)
        lo, hi = KARAKAMSA_DOCTRINE
        assert kv.doctrine_quote == (
            f"Raman's Jaimini doctrine at JAIMINI-9:{lo}-{hi}"
            " - corpus not mounted on this machine")
        assert kv.doctrine_cite == f"JAIMINI-9:{lo}"

    def test_real_quote_still_wins_when_the_corpus_is_present(self, report, monkeypatch):
        """A non-empty pull renders verbatim — the absence line is the fallback only."""
        import app.raman_saab.karmic_evolution as ke
        monkeypatch.setattr(
            ke, "passage",
            lambda cite, **k: {"work": "JAIMINI-9", "start": 799, "end": 847,
                               "text": "From the Karakamsa the\ncharacter is judged."})
        kv = build_karmic_evolution(report)
        assert kv.doctrine_quote == "From the Karakamsa the character is judged."
        assert "corpus not mounted" not in kv.doctrine_quote

    def test_no_atmakaraka_still_returns_none(self, monkeypatch):
        """A sparse/Track-B chart without an AK stays an honest None — that guard is
        about missing COMPUTED input, not the corpus, and is unchanged."""
        import app.raman_saab.karmic_evolution as ke

        class _NoAK:
            class chart:
                planets: dict = {}
        monkeypatch.setattr(ke, "passage", lambda *a, **k: None)
        assert build_karmic_evolution(_NoAK()) is None
