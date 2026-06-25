"""H7 marital-bond gate — a heavily-afflicted 8th-from-Moon softens an otherwise-favourable
marriage to mixed (troubled/unconventional but realized). Demote-only; cruel-four malefics.
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


def _h7(cid: str, sig: str) -> str:
    return next(s.verdict for s in ht.judge_house(_chart(cid), 7).significations
               if s.signification == sig)


def test_h7_16_afflicted_marital_bond_divorcee():
    """h7_16 (Chart 28): clean 7th lord but 8th-from-Moon afflicted (Saturn+Ketu) -> divorcee,
    mixed (not favourable)."""
    assert _h7("HTJAH-II.h7_16", "spouse") == "mixed"


def test_h7_19_afflicted_marital_bond_interfaith():
    """h7_19 (Chart 32): 8th-from-Moon afflicted (Mars+Ketu, Sun excluded) -> inter-faith, mixed."""
    assert _h7("HTJAH-II.h7_19", "spouse") == "mixed"


def test_h7_01_clean_marital_bond_spared():
    """h7_01 (favourable marriage): 8th-from-Moon clean -> not demoted, stays favourable."""
    assert _h7("HTJAH-II.h7_01", "marital_happiness") == "favourable"


def test_marital_bond_gate_demote_only():
    """The gate only demotes favourable; mixed/afflicted are untouched, and it never reaches
    afflicted."""
    from app.raman_saab.doctrine.significations import Signification
    ch = _chart("HTJAH-II.h7_16")
    sig = Signification(key="spouse", house=7, primary_karaka="Venus")
    assert ht._marital_bond_gate(ch, sig, "mixed")[0] == "mixed"        # no-op on mixed
    assert ht._marital_bond_gate(ch, sig, "afflicted")[0] == "afflicted"  # no-op on afflicted
    assert ht._marital_bond_gate(ch, sig, "favourable")[0] == "mixed"   # demotes favourable
