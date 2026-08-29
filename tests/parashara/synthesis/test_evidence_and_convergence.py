"""Evidence semantics and the verdict-oriented convergence — the voting and confidence core."""
from __future__ import annotations

from app.parashara.doctrine.sources import Citation
from app.parashara.synthesis.convergence import converge
from app.parashara.synthesis.evidence import Evidence, Polarity, Tier

_C = Citation("BPHS-11", 147)


def _ev(tier: Tier, pol: Polarity, *, antidoted: bool = False) -> Evidence:
    return Evidence(topic=1, tier=tier, category="x", polarity=pol, rule="r", condition="c",
                    observed="o", source=_C, antidoted=antidoted)


class TestEvidence:
    def test_neutral_does_not_count(self):
        """A neutral testimony carries no vote."""
        assert not _ev(Tier.PROMISE, Polarity.NEUTRAL).counts

    def test_antidoted_negative_does_not_count(self):
        """A cancelled affliction is disclosed but does not vote against the promise."""
        assert not _ev(Tier.PROMISE, Polarity.CONTRADICTS, antidoted=True).counts

    def test_counting_testimony_weighs_its_tier(self):
        """A counting testimony's weight is its precedence tier."""
        assert _ev(Tier.PROMISE, Polarity.SUPPORTS).weight == int(Tier.PROMISE) == 3

    def test_audit_line_carries_the_citation_token(self):
        """The audit line renders WORK:line, so every conclusion is traceable."""
        assert "[BPHS-11:147]" in _ev(Tier.STRENGTH, Polarity.SUPPORTS).audit_line


class TestConverge:
    def test_empty_is_insufficient(self):
        """No decisive testimony -> an honest 'insufficient', not a fabricated verdict."""
        assert converge([]).tier == "insufficient"

    def test_cancelled_negative_tracked_not_counted(self):
        """An antidoted negative shows as cancelled, not as a contradiction."""
        c = converge([_ev(Tier.PROMISE, Polarity.CONTRADICTS, antidoted=True)], toward=1)
        assert c.cancelled == 1 and c.contradicting == 0

    def test_denied_orientation_makes_afflictions_concur(self):
        """toward=-1: the afflicting testimonies concur with the denial (coherent surface)."""
        c = converge([_ev(Tier.PROMISE, Polarity.CONTRADICTS),
                      _ev(Tier.STRENGTH, Polarity.SUPPORTS)], toward=-1)
        assert c.supporting == 1 and c.contradicting == 1

    def test_verdict_reached_over_the_evidence_is_weak(self):
        """A verdict whose margin is non-positive can never grade above 'weak'."""
        c = converge([_ev(Tier.PROMISE, Polarity.SUPPORTS),          # +3
                      _ev(Tier.STRENGTH, Polarity.CONTRADICTS),      # -2
                      _ev(Tier.STRENGTH, Polarity.CONTRADICTS)],     # -2  -> net -1
                     toward=1)
        assert c.net < 0 and c.tier == "weak"

    def test_full_convergence_grades_par_excellence(self):
        """All three deciding tiers agreeing gives the top tier."""
        c = converge([_ev(Tier.PROMISE, Polarity.SUPPORTS),
                      _ev(Tier.STRENGTH, Polarity.SUPPORTS),
                      _ev(Tier.CORROBORATION, Polarity.SUPPORTS)], toward=1)
        assert c.net == 6 and c.tier == "par-excellence"

    def test_activation_never_votes(self):
        """ACTIVATION-tier evidence times, it does not vote on whether (weight 0)."""
        c = converge([_ev(Tier.ACTIVATION, Polarity.SUPPORTS)], toward=1)
        assert c.net == 0
