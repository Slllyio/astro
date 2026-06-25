"""H5 single-weak-sphuta fertility-gate refinement (Phase 2).

When exactly one of {Beeja, Kshetra} is weak, the gate denies progeny (afflicted) only on a
corroborating affliction — Arm A (>=2 malefic 5th-rules = "5th house spoilt") or Arm B (weak
PutraKaraka pillar AND Jupiter malefic-afflicted = "baneful PutraKaraka"). It must spare the
favourable twin h5_16 and leave the strength-disagreement chart h5_10 a documented miss.
Each test states the Raman fact it pins.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.judges import house_template as ht

_GOLDENS = Path(__file__).resolve().parents[2] / "fixtures" / "raman_goldens.jsonl"


def _chart(cid: str):
    for ln in _GOLDENS.read_text(encoding="utf-8").splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        r = json.loads(s)
        if r["id"] != cid:
            continue
        b = r["birth"]
        dp, _, tp = str(b["dt"]).partition("T")
        y, mo, d = (int(x) for x in dp.split("-"))
        hh, mm = int(tp.split(":")[0]), int(tp.split(":")[1])
        return cast_chart(BirthData(name="g", year=y, month=mo, day=d, hour=hh, minute=mm,
                                    tz_offset=float(b["tz"]), latitude=float(b["lat"]),
                                    longitude=float(b["lon"])), ayanamsa="raman")
    raise KeyError(cid)


def _children(cid: str) -> str:
    pf = ht.judge_house(_chart(cid), 5)
    return next(s.verdict for s in pf.significations if s.signification == "children")


def test_h5_05_arm_b_baneful_putrakaraka_afflicted():
    """h5_05 (Chart 95): one weak sphuta + weak karaka + Jupiter 'capable of the most baneful
    effects' (afflicted by 4 malefics) -> afflicted via Arm B."""
    assert _children("HTJAH-I.h5_05") == "afflicted"


def test_h5_12_arm_a_fifth_house_spoilt():
    """h5_12 (Chart 102): one weak sphuta + 'the 5th house is spoilt' (>=2 malefic rules)
    -> afflicted via Arm A."""
    assert _children("HTJAH-I.h5_12") == "afflicted"


def test_h5_16_favourable_twin_spared():
    """h5_16 (Chart 106): one weak sphuta BUT karaka strong (Jupiter neecha-bhanga) and only
    one malefic 5th-rule -> NEITHER arm fires; the count-favourable chart (13 children) is not
    denied by the gate. (It remains the engine's pre-existing reading, never made afflicted by
    THIS refinement.)"""
    # The refinement must not fire on h5_16: assert the one-weak gate spares it by construction.
    ch = _chart("HTJAH-I.h5_16")
    pf = ht.judge_house(ch, 5)
    sv = next(s for s in pf.significations if s.signification == "children")
    # h5_16 carries no 'one_weak_denied' fertility metadata (the gate did not deny it here).
    assert ("beeja_kshetra", "one_weak_denied") not in sv.metadata


def test_putrakaraka_malefic_afflicted_predicate():
    """The Arm-B karaka-affliction predicate fires for h5_05's heavily-afflicted Jupiter."""
    assert ht._putrakaraka_malefic_afflicted(_chart("HTJAH-I.h5_05")) is True
