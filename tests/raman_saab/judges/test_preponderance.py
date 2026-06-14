"""Pillar-preponderance weigh in `judges/house_template._decide` clause-2.

When BOTH a benefic and a malefic rule fire on a matter, `_decide` no longer
counts fired-rule surplus. It weighs the THREE RAMAN PILLARS — lord strength,
karaka strength, Bhava-Bala strength (``L.lord_strong`` / ``L.karaka_strong`` /
``L.bhava_bala_strong``) — against two GOLDEN-TUNED pillar-count knobs on
``shadbala_total`` (``CONTRA_PILLAR_AFFLICT`` / ``CONTRA_PILLAR_FAVOUR``):

* count the KNOWN pillars (Shadbala present -> not None);
* ``weak`` = how many known pillars are False, ``strong`` = how many are True;
* ``weak  >= CONTRA_PILLAR_AFFLICT`` -> 'afflicted' (Raman "factors afflicted");
* ``strong >= CONTRA_PILLAR_FAVOUR`` AND D9 does not weaken -> 'favourable';
* otherwise                          -> 'mixed'.

The DEFAULTS are 3/2 (Stage-3 calibration, user-signed-off "V2"): AFFLICT=3 (all three
pillars must be weak to condemn a contradicted matter) and FAVOUR=2 (a two-pillar strong
majority lifts to favourable) — but the FAVOUR lift is GUARDED by the navamsa: it does NOT
fire when ``L.navamsa_status == "weakens"`` (a weakening confirmation-varga is never painted
over). See ``app/raman_saab/primitives/shadbala/total.py`` for the calibration note.

On Track-B sparse charts all three pillars are None -> the known set is empty ->
clause-2 is 'mixed' regardless of the knob (safe). Our fresh-cast goldens HAVE
Shadbala, so their pillars ARE populated — that is the point of the refinement.

These tests build ``FrameLedger`` instances directly and monkeypatch the live
module attributes the way the tuner's ``_ApplyThresholds`` context manager does.
"""
from __future__ import annotations

from typing import Optional

from app.raman_saab.judges import house_template as ht
from app.raman_saab.judges import rule_firing as rf
from app.raman_saab.doctrine.rules import RuleRecord
from app.raman_saab.doctrine.sources import Citation
from app.raman_saab.primitives.shadbala import total as shadbala_total


def _fired(polarity: str, n: int = 0) -> rf.FiredRule:
    """A synthetic FiredRule carrying only the polarity `_decide` reads. `n` makes
    the rule id unique so a tuple of several fired rules holds distinct records."""
    rule = RuleRecord(
        id=f"TEST.{polarity}.{n}",
        house=1,
        signification="self",
        group="combination",
        kind="evaluable",
        condition=None,
        fortified="ok",
        afflicted="bad",
        frame="LAGNA",
        varga="D1",
        polarity=polarity,
        source=Citation("HTJAH-I", 1),
    )
    return rf.FiredRule(rule=rule, branch="fortified", text="ok")


def _both_fired() -> tuple[tuple[rf.FiredRule, ...], tuple[rf.FiredRule, ...]]:
    """One benefic + one malefic fired — the clause-2 trigger (both polarities)."""
    return (_fired("benefic"),), (_fired("malefic"),)


def _ledger(
    *,
    lord_strong: Optional[bool],
    karaka_strong: Optional[bool],
    bhava_bala_strong: Optional[bool],
    navamsa_status: str = "neutral",
    fired_benefic: tuple[rf.FiredRule, ...] = (),
    fired_malefic: tuple[rf.FiredRule, ...] = (),
) -> ht.FrameLedger:
    """A clause-2-reachable ledger: karaka intact, both polarities fire when both
    fired tuples are non-empty. Pillars (lord/karaka/bhava-bala strong) are set
    explicitly so the pillar-preponderance weigh can be exercised directly.

    NOTE: when lord_strong/karaka_strong are both None the clause-3 Track-B fallback
    would intercept — but clause-2 fires first whenever BOTH polarities are present,
    so an all-None / both-fired ledger still reaches the pillar weigh (and resolves
    to 'mixed' on an empty known set)."""
    return ht.FrameLedger(
        frame="lagna", lord="Mars", lord_strong=lord_strong, karaka="Sun",
        karaka_strong=karaka_strong, bhava_bala=None,
        bhava_bala_strong=bhava_bala_strong,
        navamsa_status=navamsa_status, karaka_intact=True, maraka_active=False,
        parivartana_resilient=False, lord_karaka_identical=False,
        fired_benefic=fired_benefic, fired_malefic=fired_malefic,
        fired_neutral=(), flags=())


# ---------------------------------------------------------------------------
# (a) DEFAULT knobs 3/2 (Stage-3 'V2') -> calibrated preponderance behaviour.
# ---------------------------------------------------------------------------

def test_default_knob_two_weak_pillars_still_mixed():
    """With the calibrated default AFFLICT=3, a ledger with only 2 weak pillars
    (weak=2 < 3) and BOTH polarities fired stays 'mixed' — the afflicted
    preponderance needs ALL three pillars weak. (Stage-3 'V2' default: AFFLICT=3,
    FAVOUR=2.)"""
    assert shadbala_total.CONTRA_PILLAR_AFFLICT == 3
    assert shadbala_total.CONTRA_PILLAR_FAVOUR == 2
    b, m = _both_fired()
    L = _ledger(lord_strong=False, karaka_strong=False, bhava_bala_strong=True,
                fired_benefic=b, fired_malefic=m)
    v, shifted = ht._decide(L)
    assert v == "mixed" and shifted is False


def test_default_two_strong_pillars_favourable():
    """Under the calibrated default FAVOUR=2, a both-fired ledger with 2 strong
    pillars (strong=2 >= 2) and a NON-weakening navamsa lifts to 'favourable'
    (Stage-3 'V2'). This is the favour-preponderance the old no-op 99 default
    suppressed."""
    b, m = _both_fired()
    L = _ledger(lord_strong=True, karaka_strong=True, bhava_bala_strong=False,
                navamsa_status="neutral", fired_benefic=b, fired_malefic=m)
    v, shifted = ht._decide(L)
    assert v == "favourable" and shifted is False


# ---------------------------------------------------------------------------
# (b) CONTRA_PILLAR_AFFLICT lowered -> weak-pillar preponderance reads 'afflicted'.
# ---------------------------------------------------------------------------

def test_afflict_pillar_2_with_two_weak_pillars_afflicted(monkeypatch):
    """With CONTRA_PILLAR_AFFLICT=2, a both-fired ledger carrying 2 weak pillars
    (weak=2>=2) crosses into 'factors afflicted' -> 'afflicted'."""
    monkeypatch.setattr(shadbala_total, "CONTRA_PILLAR_AFFLICT", 2)
    b, m = _both_fired()
    L = _ledger(lord_strong=False, karaka_strong=False, bhava_bala_strong=True,
                fired_benefic=b, fired_malefic=m)
    v, _ = ht._decide(L)
    assert v == "afflicted"


# ---------------------------------------------------------------------------
# (c) CONTRA_PILLAR_FAVOUR lowered -> strong-pillar preponderance reads 'favourable'.
# ---------------------------------------------------------------------------

def test_favour_pillar_2_with_two_strong_pillars_favourable(monkeypatch):
    """With CONTRA_PILLAR_FAVOUR=2, a both-fired ledger carrying 2 strong pillars
    (strong=2>=2) crosses into benefic preponderance -> 'favourable'."""
    monkeypatch.setattr(shadbala_total, "CONTRA_PILLAR_FAVOUR", 2)
    b, m = _both_fired()
    L = _ledger(lord_strong=True, karaka_strong=True, bhava_bala_strong=False,
                fired_benefic=b, fired_malefic=m)
    v, _ = ht._decide(L)
    assert v == "favourable"


# ---------------------------------------------------------------------------
# (d) mixed pillar signal (1 weak / 1 strong / 1 None) stays 'mixed'.
# ---------------------------------------------------------------------------

def test_mixed_pillar_signal_stays_mixed(monkeypatch):
    """A ledger with one weak, one strong, and one unknown (None) pillar carries
    weak=1 and strong=1 — neither reaches a lowered threshold of 2, so it remains
    'mixed' even with both knobs lowered."""
    monkeypatch.setattr(shadbala_total, "CONTRA_PILLAR_AFFLICT", 2)
    monkeypatch.setattr(shadbala_total, "CONTRA_PILLAR_FAVOUR", 2)
    b, m = _both_fired()
    L = _ledger(lord_strong=False, karaka_strong=True, bhava_bala_strong=None,
                fired_benefic=b, fired_malefic=m)
    v, shifted = ht._decide(L)
    assert v == "mixed" and shifted is False


# ---------------------------------------------------------------------------
# (e) all-None pillars (Track-B) + both fired -> 'mixed' regardless of margin.
# ---------------------------------------------------------------------------

def test_all_none_pillars_track_b_stays_mixed_regardless_of_margin(monkeypatch):
    """On a Track-B sparse chart all three pillars are None, so the known set is
    empty and the pillar weigh can never trigger — clause-2 stays 'mixed' even with
    both knobs lowered to the most aggressive setting (2)."""
    monkeypatch.setattr(shadbala_total, "CONTRA_PILLAR_AFFLICT", 2)
    monkeypatch.setattr(shadbala_total, "CONTRA_PILLAR_FAVOUR", 2)
    b, m = _both_fired()
    L = _ledger(lord_strong=None, karaka_strong=None, bhava_bala_strong=None,
                fired_benefic=b, fired_malefic=m)
    v, shifted = ht._decide(L)
    assert v == "mixed" and shifted is False


# ---------------------------------------------------------------------------
# (f) the pillar-preponderance verdict is DECISIVE — navamsa cannot shift it.
# ---------------------------------------------------------------------------

def test_pillar_afflicted_not_shifted_by_navamsa_confirms(monkeypatch):
    """A weak-pillar 'afflicted' is decisive: a D9 'confirms' (which would lift a
    borderline 'mixed' to 'favourable') must NOT touch it."""
    monkeypatch.setattr(shadbala_total, "CONTRA_PILLAR_AFFLICT", 2)
    b, m = _both_fired()
    L = _ledger(lord_strong=False, karaka_strong=False, bhava_bala_strong=True,
                navamsa_status="confirms", fired_benefic=b, fired_malefic=m)
    v, shifted = ht._decide(L)
    assert v == "afflicted" and shifted is False


def test_pillar_favourable_guarded_by_navamsa_weakens(monkeypatch):
    """NAVAMSA GUARD (Stage-3 'V2' — a doctrinal reversal of the round-8 "favourable
    is decisive" rule): a strong-pillar majority does NOT lift to 'favourable' when
    the D9 weakens. The favour branch is skipped, the matter falls to 'mixed', and
    _navamsa_modulate then drops that borderline to 'afflicted' — a weakening
    confirmation-varga is never painted over by Rasi pillar strength. This guard is
    what protected the H9 father-death charts + the H2 afflictions from inversion."""
    monkeypatch.setattr(shadbala_total, "CONTRA_PILLAR_FAVOUR", 2)
    b, m = _both_fired()
    L = _ledger(lord_strong=True, karaka_strong=True, bhava_bala_strong=False,
                navamsa_status="weakens", fired_benefic=b, fired_malefic=m)
    v, shifted = ht._decide(L)
    assert v == "afflicted" and shifted is True
