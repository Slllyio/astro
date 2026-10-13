"""Every re-homed clause is neutral, except the separate combinations that earned their own vote.

The twelve-house sweep moved hundreds of clauses out of strength slots into their own records.
Each refines a parent rule that ALREADY votes for the same placement, so voting again would
count one placement twice -- the evidence-redundancy blindness the ratchet cannot see.

This guard exists because the rule was violated by accident: eleven records created in the
House-6 and House-8 sweeps, before the neutral rule existed, kept the parent's malefic/benefic
sense. Harmless while they were descriptive; the moment IsStrong/IsWeak promoted two of them to
live rules, H6.L.6a voted malefic and flipped three H6/accidents verdicts.
"""
from __future__ import annotations

import re

from app.raman_saab.doctrine.rule_sets import ALL_RULES

#: Separate combinations: Raman's own paragraphs whose conditions are NOT implied by a parent
#: placement, so they cast their own vote. H8.L.5c needs the 9th lord too (HTJAH-II:2972);
#: H8.L.12b drops the conjunction because Raman re-opens the antecedent (HTJAH-II:3061).
SEPARATE_COMBINATIONS = {"H8.L.5c", "H8.L.12b"}

_REHOMED = re.compile(r"H\d+\.L\.(\d+[a-z]+|S\d+)")


class TestRehomedRecordsAreNeutral:
    def test_no_rehomed_record_casts_a_vote_by_accident(self) -> None:
        offenders = [(r.id, r.polarity) for r in ALL_RULES
                     if _REHOMED.fullmatch(r.id) and r.id not in SEPARATE_COMBINATIONS
                     and r.polarity != "neutral"]
        assert not offenders, (
            f"re-homed records must be neutral (their parent already votes for the placement): "
            f"{offenders}. If one is genuinely a separate combination, add it to "
            f"SEPARATE_COMBINATIONS with its citation.")

    def test_the_separate_combinations_still_exist_and_still_vote(self) -> None:
        by_id = {r.id: r for r in ALL_RULES}
        for rid in SEPARATE_COMBINATIONS:
            assert by_id[rid].polarity != "neutral", rid

    def test_the_sweep_produced_a_large_rehomed_population(self) -> None:
        """Guards the guard: a regex that matched nothing would pass vacuously."""
        assert sum(1 for r in ALL_RULES if _REHOMED.fullmatch(r.id)) >= 150
