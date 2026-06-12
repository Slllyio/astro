"""Pillar-preponderance weigh in `judges/house_template._decide` clause-2.

When BOTH a benefic and a malefic rule fire on a matter, `_decide` no longer
counts fired-rule surplus. It weighs the THREE RAMAN PILLARS — lord strength,
karaka strength, Bhava-Bala strength (``L.lord_strong`` / ``L.karaka_strong`` /
``L.bhava_bala_strong``) — against two GOLDEN-TUNED pillar-count knobs on
``shadbala_total`` (``CONTRA_PILLAR_AFFLICT`` / ``CONTRA_PILLAR_FAVOUR``):

* count the KNOWN pillars (Shadbala present -> not None);
* ``weak`` = how many known pillars are False, ``strong`` = how many are True;
* ``weak  >= CONTRA_PILLAR_AFFLICT`` -> 'afflicted' (Raman "factors afflicted");
* ``strong >= CONTRA_PILLAR_FAVOUR`` -> 'favourable';
* otherwise                          -> 'mixed'.

The DEFAULT knob is 99 (effectively infinite): at most 3 pillars exist, so the
weak/strong count never reaches it and clause-2 ALWAYS stays 'mixed' — the no-op
the round-8 batch requires (Track-B ratchet must remain 9/24). The tuner lowers
the knobs to a discrete pillar count later.

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
# (a) DEFAULT knob 99 -> the no-op proof (always 'mixed').
# ---------------------------------------------------------------------------

def test_default_knob_two_weak_pillars_still_mixed():
    """With the default 99 knobs, a ledger with 2 weak pillars and BOTH polarities
    fired still reads 'mixed' — weak (max 3) never reaches 99, the no-op the
    round-8 batch requires."""
    assert shadbala_total.CONTRA_PILLAR_AFFLICT == 99
    assert shadbala_total.CONTRA_PILLAR_FAVOUR == 99
    b, m = _both_fired()
    L = _ledger(lord_strong=False, karaka_strong=False, bhava_bala_strong=True,
                fired_benefic=b, fired_malefic=m)
    v, shifted = ht._decide(L)
    assert v == "mixed" and shifted is False


def test_default_knob_two_strong_pillars_still_mixed():
    """The strong-pillar mirror is also clamped to 'mixed' under the default
    infinite knobs (strong never reaches 99)."""
    b, m = _both_fired()
    L = _ledger(lord_strong=True, karaka_strong=True, bhava_bala_strong=False,
                fired_benefic=b, fired_malefic=m)
    v, shifted = ht._decide(L)
    assert v == "mixed" and shifted is False


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


def test_pillar_favourable_not_shifted_by_navamsa_weakens(monkeypatch):
    """A strong-pillar 'favourable' is decisive: a D9 'weakens' (which would drop a
    borderline 'mixed' to 'afflicted') must NOT touch it."""
    monkeypatch.setattr(shadbala_total, "CONTRA_PILLAR_FAVOUR", 2)
    b, m = _both_fired()
    L = _ledger(lord_strong=True, karaka_strong=True, bhava_bala_strong=False,
                navamsa_status="weakens", fired_benefic=b, fired_malefic=m)
    v, shifted = ht._decide(L)
    assert v == "favourable" and shifted is False
