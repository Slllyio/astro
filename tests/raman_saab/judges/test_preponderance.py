"""Preponderance weigh in `judges/house_template._decide` clause-2.

When BOTH a benefic and a malefic rule fire on a matter, `_decide` weighs the
``net = len(fired_malefic) - len(fired_benefic)`` surplus against two GOLDEN-TUNED
margins on ``shadbala_total`` (``CONTRA_AFFLICT_MARGIN`` / ``CONTRA_FAVOUR_MARGIN``):

* ``net >= CONTRA_AFFLICT_MARGIN``  -> 'afflicted' (malefic preponderance)
* ``(-net) >= CONTRA_FAVOUR_MARGIN`` -> 'favourable' (benefic preponderance)
* otherwise                          -> 'mixed'

The DEFAULT margin is 99 (effectively infinite): no small fired-rule net ever
reaches it, so clause-2 ALWAYS stays 'mixed' — the no-op the round-8 batch
requires (Track-B ratchet must remain 7/12). The tuner lowers the margins later.

These tests build ``FrameLedger`` instances directly and monkeypatch the live
module attributes the way the tuner's ``_ApplyThresholds`` context manager does.
"""
from __future__ import annotations

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


def _fired_many(polarity: str, count: int) -> tuple[rf.FiredRule, ...]:
    return tuple(_fired(polarity, i) for i in range(count))


def _ledger(
    *,
    fired_benefic: tuple[rf.FiredRule, ...] = (),
    fired_malefic: tuple[rf.FiredRule, ...] = (),
    navamsa_status: str = "neutral",
    lord_strong=True,
    karaka_strong=True,
) -> ht.FrameLedger:
    """A clause-2-reachable ledger: karaka intact, both pillars known (so the
    Track-B fallback at clause-3 is not taken), with the given fired rules."""
    return ht.FrameLedger(
        frame="lagna", lord="Mars", lord_strong=lord_strong, karaka="Sun",
        karaka_strong=karaka_strong, bhava_bala=None, bhava_bala_strong=None,
        navamsa_status=navamsa_status, karaka_intact=True, maraka_active=False,
        parivartana_resilient=False, lord_karaka_identical=False,
        fired_benefic=fired_benefic, fired_malefic=fired_malefic,
        fired_neutral=(), flags=())


# ---------------------------------------------------------------------------
# (a) DEFAULT margins -> the no-op proof (always 'mixed').
# ---------------------------------------------------------------------------

def test_default_margins_4v1_malefic_still_mixed():
    """With the default 99 margins a heavy 4-malefic vs 1-benefic split (net=3)
    never reaches the cut-off, so clause-2 stays 'mixed' — the no-op the round-8
    batch requires."""
    assert shadbala_total.CONTRA_AFFLICT_MARGIN == 99
    assert shadbala_total.CONTRA_FAVOUR_MARGIN == 99
    L = _ledger(fired_benefic=_fired_many("benefic", 1),
                fired_malefic=_fired_many("malefic", 4))
    v, shifted = ht._decide(L)
    assert v == "mixed" and shifted is False


def test_default_margins_4v1_benefic_still_mixed():
    """The benefic-preponderant mirror (net=-3) is also clamped to 'mixed' under
    the default infinite margins."""
    L = _ledger(fired_benefic=_fired_many("benefic", 4),
                fired_malefic=_fired_many("malefic", 1))
    v, shifted = ht._decide(L)
    assert v == "mixed" and shifted is False


# ---------------------------------------------------------------------------
# (b) CONTRA_AFFLICT_MARGIN lowered -> malefic preponderance reads 'afflicted'.
# ---------------------------------------------------------------------------

def test_afflict_margin_2_makes_4v1_afflicted(monkeypatch):
    """With CONTRA_AFFLICT_MARGIN=2, a 4-malefic vs 1-benefic split (net=3>=2)
    crosses into malefic preponderance -> 'afflicted'."""
    monkeypatch.setattr(shadbala_total, "CONTRA_AFFLICT_MARGIN", 2)
    L = _ledger(fired_benefic=_fired_many("benefic", 1),
                fired_malefic=_fired_many("malefic", 4))
    v, _ = ht._decide(L)
    assert v == "afflicted"


# ---------------------------------------------------------------------------
# (c) CONTRA_FAVOUR_MARGIN lowered -> benefic preponderance reads 'favourable'.
# ---------------------------------------------------------------------------

def test_favour_margin_2_makes_4benefic_1malefic_favourable(monkeypatch):
    """With CONTRA_FAVOUR_MARGIN=2, a 4-benefic vs 1-malefic split (-net=3>=2)
    crosses into benefic preponderance -> 'favourable'."""
    monkeypatch.setattr(shadbala_total, "CONTRA_FAVOUR_MARGIN", 2)
    L = _ledger(fired_benefic=_fired_many("benefic", 4),
                fired_malefic=_fired_many("malefic", 1))
    v, _ = ht._decide(L)
    assert v == "favourable"


# ---------------------------------------------------------------------------
# (d) balanced split stays 'mixed' even with a lowered margin.
# ---------------------------------------------------------------------------

def test_balanced_2v2_stays_mixed_with_margin_2(monkeypatch):
    """A balanced 2-malefic vs 2-benefic split (net=0) clears neither margin and
    remains 'mixed' even with both margins lowered to 2."""
    monkeypatch.setattr(shadbala_total, "CONTRA_AFFLICT_MARGIN", 2)
    monkeypatch.setattr(shadbala_total, "CONTRA_FAVOUR_MARGIN", 2)
    L = _ledger(fired_benefic=_fired_many("benefic", 2),
                fired_malefic=_fired_many("malefic", 2))
    v, shifted = ht._decide(L)
    assert v == "mixed" and shifted is False


# ---------------------------------------------------------------------------
# (e) the preponderance verdict is DECISIVE — navamsa cannot shift it.
# ---------------------------------------------------------------------------

def test_preponderance_afflicted_not_shifted_by_navamsa_confirms(monkeypatch):
    """A malefic-preponderance 'afflicted' is decisive: a D9 'confirms' (which would
    lift a borderline 'mixed' to 'favourable') must NOT touch it."""
    monkeypatch.setattr(shadbala_total, "CONTRA_AFFLICT_MARGIN", 2)
    L = _ledger(fired_benefic=_fired_many("benefic", 1),
                fired_malefic=_fired_many("malefic", 4),
                navamsa_status="confirms")
    v, shifted = ht._decide(L)
    assert v == "afflicted" and shifted is False


def test_preponderance_favourable_not_shifted_by_navamsa_weakens(monkeypatch):
    """A benefic-preponderance 'favourable' is decisive: a D9 'weakens' (which would
    drop a borderline 'mixed' to 'afflicted') must NOT touch it."""
    monkeypatch.setattr(shadbala_total, "CONTRA_FAVOUR_MARGIN", 2)
    L = _ledger(fired_benefic=_fired_many("benefic", 4),
                fired_malefic=_fired_many("malefic", 1),
                navamsa_status="weakens")
    v, shifted = ht._decide(L)
    assert v == "favourable" and shifted is False
