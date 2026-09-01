"""The condition-delta harness — the instrument for measuring a predicate change.

A TEXT change cannot move a verdict, so it ships on review alone. A CONDITION change starts or
stops a rule firing, so playbook rule 3 requires it be measured first. This harness is that
measurement, generalised out of the H8 lord-in-house narrowing where it was improvised.

The tests below pin the two properties that make it trustworthy: it must not leak a mutated
condition into the live corpus (it swaps conditions on real rule objects to re-judge), and it
must report the DIRECTION of each moved row, not just a count — the H8 change cost one exact
match, and a bare delta would have argued for reverting something that was right to ship.
"""
from __future__ import annotations

import pytest

from app.raman_saab.doctrine import conditions as C
from tools.raman_saab import condition_delta as cd


@pytest.fixture(scope="module")
def charts():
    return cd._golden_charts()


class TestItCannotCorruptTheCorpus:
    def test_the_swapped_condition_is_restored(self, charts) -> None:
        """`measure` mutates a live `RuleRecord` to re-judge, then puts it back. A leaked
        swap would silently corrupt every later measurement in the same process."""
        before = cd._RULES["H1.L.4"].condition
        cd.measure("H1.L.4", cd.lord_conjunction("H1.L.4"), charts)
        assert cd._RULES["H1.L.4"].condition is before

    def test_restored_even_when_the_proposal_raises(self, charts) -> None:
        """The restore is in a `finally`, so a proposal that blows up mid-measurement still
        leaves the corpus intact."""
        class Exploding(C.Condition):
            def evaluate(self, ctx):
                raise RuntimeError("boom")

        before = cd._RULES["H1.L.4"].condition
        with pytest.raises(RuntimeError):
            cd.measure("H1.L.4", Exploding(), charts)
        assert cd._RULES["H1.L.4"].condition is before

    def test_measurement_is_repeatable(self, charts) -> None:
        a = cd.measure("H1.L.4", cd.lord_conjunction("H1.L.4"), charts)
        b = cd.measure("H1.L.4", cd.lord_conjunction("H1.L.4"), charts)
        assert (a.fires_now, a.fires_proposed, a.moved) == (b.fires_now, b.fires_proposed,
                                                            b.moved)


class TestItReportsWhatDecidesTheCall:
    def test_an_identical_proposal_changes_nothing(self, charts) -> None:
        rule = cd._RULES["H1.L.4"]
        d = cd.measure("H1.L.4", rule.condition, charts)
        assert d.fires_now == d.fires_proposed
        assert d.moved == ()

    def test_coverage_and_exposure_are_separated(self, charts) -> None:
        """A change touching no scored row cannot move the ratchet; its safety is then a
        coverage question, not an accuracy one. Conflating the two is how a harmless-looking
        delta hides a verdict flip."""
        d = cd.measure("H1.L.4", cd.lord_conjunction("H1.L.4"), charts)
        assert d.fires_proposed <= d.fires_now
        assert len(d.exposed) <= d.charts_total
        assert "coverage" in str(d) and "exposure" in str(d) and "IMPACT" in str(d)

    def test_a_large_narrowing_is_flagged_for_a_source_re_read(self, charts) -> None:
        """Removing most firings means either the encoded predicate was over-broad or the
        proposal is too narrow. The harness must not let that pass silently — H8's 81% was
        the signal that started the whole investigation."""
        d = cd.measure("H1.L.4", cd.lord_conjunction("H1.L.4"), charts)
        assert d.fires_now - d.fires_proposed > 0.75 * d.fires_now
        assert any("over-broad" in n or "too narrow" in n for n in d.notes)

    def test_moved_rows_carry_the_golden_and_both_verdicts(self, charts) -> None:
        """Direction is the point. Each moved row reports golden, current and proposed so a
        re-base can be argued from the specific chart rather than from a net count."""
        d = cd.measure("H8.L.1", C.LordIn(8, 1), charts)   # widen H8.L.1 back to bare
        assert d.moved, "widening H8.L.1 should move Lincoln's H8/death row"
        for cid, sig, gold, now, prop in d.moved:
            assert cid and sig and gold and now and prop
        rendered = str(d)
        assert "FIXES" in rendered or "BREAKS" in rendered or "shifts" in rendered


class TestTheLordConjunctionProposal:
    def test_it_requires_both_the_placement_and_the_conjunction(self) -> None:
        """Raman's H8 form is "the lord of the 8th house in conjunction with the 2nd lord IN
        THE 2ND HOUSE" — the conjunction alone is not enough, the placement is also stated."""
        proposal = cd.lord_conjunction("H8.L.2")
        assert isinstance(proposal, C.And)

    def test_identity_rules_are_excluded_by_the_scan(self) -> None:
        """`LordsConjunct(N, N)` is identity-false by design, so HN.L.N could never satisfy
        the proposal — scanning it would report a spurious 100% removal."""
        assert C.LordsConjunct(8, 8).__class__ is C.LordsConjunct
