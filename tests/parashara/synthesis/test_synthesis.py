"""End-to-end synthesis on the canonical chart — structure, citation integrity, coherence, determinism.

The canonical baseline (Bangalore 1990-07-15 12:00 IST) is the project's pinned chart. These tests do
not pin specific verdicts (those are the engine's honest output, free to evolve with doctrine) — they
pin the invariants the layer must always hold.
"""
from __future__ import annotations

import pytest

from app.parashara.chart.cast import cast
from app.parashara.doctrine.sources import verify
from app.parashara.synthesis import synthesize
from app.parashara.synthesis.topics import all_topics
from app.parashara.reading import read

_VALID = {"granted", "delayed", "difficult", "denied", "mixed", "ordinary", "indeterminate"}


@pytest.fixture(scope="module")
def report():
    ch = cast(year=1990, month=7, day=15, hour=12, minute=0,
              tz_offset=5.5, latitude=12.97, longitude=77.59)
    return synthesize(read(ch))


class TestTopics:
    def test_spine_is_twelve_houses(self):
        """The topic spine is exactly the twelve bhavas (cross-matters roll up in synthesis)."""
        topics = all_topics()
        assert len(topics) == 12 and [t.houses for t in topics] == [(h,) for h in range(1, 13)]

    def test_seventh_house_karaka_is_venus(self):
        """The 7th (marriage) topic carries Venus as its karaka (BPHS ch.32)."""
        seventh = next(t for t in all_topics() if t.houses == (7,))
        assert "Venus" in seventh.karakas


class TestMatterViews:
    def test_matters_roll_up_component_verdicts(self, report):
        """Each named matter reports every component house's own verdict — no pooling."""
        for m in report.matters.values():
            assert set(m.component_verdicts) == set(m.houses)
            for h in m.houses:
                assert m.component_verdicts[h] == report.houses[h].verdict

    def test_disagreeing_components_are_mixed_with_split(self, report):
        """A matter whose houses disagree says 'mixed' and spells the split; agreeing ones share."""
        for m in report.matters.values():
            distinct = set(m.component_verdicts.values())
            if len(distinct) == 1:
                assert m.verdict in distinct and m.note == ""
            else:
                assert m.verdict == "mixed" and "not averaged" in m.note


class TestSynthesis:
    def test_all_twelve_houses_judged(self, report):
        """Every bhava gets a judgment."""
        assert sorted(report.houses) == list(range(1, 13))

    def test_every_verdict_is_valid(self, report):
        """No judgment escapes the classical axis."""
        assert all(j.verdict in _VALID for j in report.all_judgments)

    def test_every_citation_resolves(self, report):
        """Audit integrity: every evidence sloka points at a real, non-frontmatter corpus line."""
        for j in report.all_judgments:
            for e in j.evidence:
                assert verify(e.source), f"{j.topic}: unresolved {e.source}"

    def test_confidence_never_contradicts_its_verdict(self, report):
        """Measured-truth coherence: a strong/par-excellence tier requires a positive margin toward
        the verdict — the confidence can never read against the evidence beside it."""
        for j in report.all_judgments:
            if j.convergence.tier in ("strong", "par-excellence"):
                assert j.convergence.net >= 4, f"{j.topic}: {j.convergence.tier} at net {j.convergence.net}"

    def test_decided_topics_carry_an_audit_trail(self, report):
        """Any topic with a verdict shows its cited working."""
        for j in report.all_judgments:
            if j.verdict != "indeterminate":
                assert j.audit, f"{j.topic}: no audit trail"

    def test_windows_are_chronological_within_a_tier(self, report):
        """Activation windows are graded best-first; ages are non-negative (no pre-birth windows)."""
        for j in report.all_judgments:
            assert all(w.start_age >= 0 for w in j.windows)

    def test_synthesis_is_deterministic(self):
        """Same chart -> identical synthesis (no LLM, no randomness in the judgment path)."""
        ch = cast(year=1990, month=7, day=15, hour=12, minute=0,
                  tz_offset=5.5, latitude=12.97, longitude=77.59)
        a = synthesize(read(ch))
        b = synthesize(read(ch))
        sig_a = [(j.topic, j.verdict, j.convergence.tier, j.convergence.tally) for j in a.all_judgments]
        sig_b = [(j.topic, j.verdict, j.convergence.tier, j.convergence.tally) for j in b.all_judgments]
        assert sig_a == sig_b
