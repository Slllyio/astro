"""Rule-precision ledger scoring — `tools/raman_saab/rule_precision.py`.

Pins the classification that decides which fired rules are real gaps: a misfire counts only when
the rule fired AGAINST the confirmed life AND the engine's verdict is also wrong (consequential);
a misfire the synthesis already outweighed (engine still correct) is benign. Pure logic — no
chart casting — so the discipline that separates leads from noise is guarded.
"""
from __future__ import annotations

from tools.raman_saab.rule_precision import _distance, _Firing, _RuleStat


def _stat(*firings: _Firing) -> _RuleStat:
    return _RuleStat(rule_id="H3.C.9", citation="HTJAH-I:3435", firings=list(firings))


class TestRulePrecisionScoring:
    def test_malefic_on_favourable_life_with_wrong_engine_is_consequential(self) -> None:
        """A malefic rule fires on a matter the owner confirms favourable AND the engine calls it
        afflicted (dist 2) — the over-affliction gap the ledger exists to surface."""
        s = _stat(_Firing("chart_a", 3, "siblings", "malefic", "favourable", "afflicted"))
        assert len(s.consequential) == 1
        assert s.worst_distance == 2
        assert not s.benign_misfires

    def test_malefic_on_favourable_life_with_correct_engine_is_benign(self) -> None:
        """The same errant malefic firing, but the engine still verdicts favourable — the
        synthesis outweighed the rule, so it is benign, not a gap."""
        s = _stat(_Firing("chart_a", 3, "siblings", "malefic", "favourable", "favourable"))
        assert not s.consequential
        assert len(s.benign_misfires) == 1

    def test_benefic_on_afflicted_life_with_wrong_engine_is_consequential(self) -> None:
        """The mirror: a benefic rule fires on an afflicted matter and the engine mis-lifts it."""
        s = _stat(_Firing("chart_a", 2, "speech", "benefic", "afflicted", "mixed"))
        assert len(s.consequential) == 1
        assert s.worst_distance == 1

    def test_aligned_firing_is_not_a_misfire(self) -> None:
        """A malefic rule on an afflicted life is doctrine agreeing with the outcome — no misfire."""
        s = _stat(_Firing("chart_a", 5, "children", "malefic", "afflicted", "afflicted"))
        assert not s.consequential
        assert not s.benign_misfires

    def test_consequential_charts_counts_distinct_charts_only(self) -> None:
        """The anti-overfit threshold keys on DISTINCT charts: two consequential misfires on one
        chart is still n=1, never enough to license a fix."""
        s = _stat(
            _Firing("chart_a", 3, "siblings", "malefic", "favourable", "afflicted"),
            _Firing("chart_a", 3, "courage", "malefic", "favourable", "afflicted"))
        assert len(s.consequential) == 2
        assert s.consequential_charts == {"chart_a"}

    def test_distance_is_ordinal(self) -> None:
        """afflicted<mixed<favourable ordinal gap; an unknown engine verdict scores the max."""
        assert _distance("afflicted", "favourable") == 2
        assert _distance("mixed", "favourable") == 1
        assert _distance("favourable", "favourable") == 0
        assert _distance(None, "favourable") == 2
