"""Layer-A `degree` (strong/moderate/mild) — the deterministic verdict intensity.

`_compute_degree` surfaces the gradation the engine already computes (pillar count,
decisive/veto flags, marginal-shift) as strong/moderate/mild, giving verdict x degree =
7 graded output states WITHOUT changing the verdict bucket. Each test states the rule.
"""
from __future__ import annotations

from app.raman_saab.judges import house_template as ht


def _ledger(*, lord_strong=None, karaka_strong=None, bhava_strong=None,
            navamsa="neutral", karaka_intact=True, fired_malefic=()):
    """A minimal FrameLedger with the fields _compute_degree reads."""
    return ht.FrameLedger(
        frame="lagna", lord="Sun", lord_strong=lord_strong, karaka="Mars",
        karaka_strong=karaka_strong, bhava_bala=None, bhava_bala_strong=bhava_strong,
        navamsa_status=navamsa, karaka_intact=karaka_intact, maraka_active=False,
        parivartana_resilient=False, lord_karaka_identical=False,
        fired_benefic=(), fired_malefic=fired_malefic, fired_neutral=())


def test_insufficient_evidence_is_mild():
    """No evidence to grade -> mild."""
    assert ht._compute_degree("insufficient-evidence", _ledger(), False) == "mild"


def test_marginal_shift_is_mild():
    """A verdict nudged at the margin (navamsa / relief floor) -> mild, regardless of pillars."""
    led = _ledger(lord_strong=True, karaka_strong=True, bhava_strong=True)
    assert ht._compute_degree("favourable", led, True) == "mild"


def test_favourable_all_pillars_confirmed_is_strong():
    """Favourable with all known pillars strong + navamsa confirms -> strong."""
    led = _ledger(lord_strong=True, karaka_strong=True, bhava_strong=True, navamsa="confirms")
    assert ht._compute_degree("favourable", led, False) == "strong"


def test_favourable_two_strong_is_strong():
    """Favourable with a 2+ strong-pillar majority -> strong."""
    led = _ledger(lord_strong=True, karaka_strong=True, bhava_strong=False)
    assert ht._compute_degree("favourable", led, False) == "strong"


def test_favourable_one_strong_is_moderate():
    """Favourable resting on a single strong pillar (no majority) -> moderate."""
    led = _ledger(lord_strong=True, karaka_strong=None, bhava_strong=None)
    assert ht._compute_degree("favourable", led, False) == "moderate"


def test_afflicted_all_pillars_weak_is_strong():
    """Afflicted with all known pillars weak -> strong."""
    led = _ledger(lord_strong=False, karaka_strong=False, bhava_strong=False)
    assert ht._compute_degree("afflicted", led, False) == "strong"


def test_afflicted_broken_karaka_is_strong():
    """Afflicted via a broken karaka (veto) -> strong, even without weak pillars."""
    led = _ledger(lord_strong=True, karaka_intact=False)
    assert ht._compute_degree("afflicted", led, False) == "strong"


def test_afflicted_one_weak_amid_strong_is_moderate():
    """Afflicted on a single weak pillar amid a strong one (not all-weak, no >=2 weak,
    no decisive flag) -> moderate."""
    led = _ledger(lord_strong=False, karaka_strong=True, bhava_strong=None)
    assert ht._compute_degree("afflicted", led, False) == "moderate"


def test_mixed_is_moderate():
    """Mixed is the genuine middle -> moderate (mild only when shifted)."""
    led = _ledger(lord_strong=True, karaka_strong=False)
    assert ht._compute_degree("mixed", led, False) == "moderate"
