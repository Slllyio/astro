"""GBB B2 marginal-strength band — a marriage afflicted PURELY by a marginally-weak Venus karaka
(within ~0.2 rupa of MIN_REQUIRED) plus maraka, with a strong lord and no real malefic, re-decides
as not-decisively-weak and rises to Raman's reading (chart_08 H7: afflicted -> favourable).
"""
from __future__ import annotations

import json
from pathlib import Path

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.doctrine.significations import Signification
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


def _h7(cid: str, sig_key: str):
    return next(s.verdict for s in ht.judge_house(_chart(cid), 7).significations
               if s.signification == sig_key)


def test_marginal_venus_strong_lord_lifts_marriage_chart_08():
    """chart_08 H7: Venus at 5.37 (< the 5.5 bar by 0.13) + strong 7th lord + no malefic ->
    the cliff-artefact afflicted re-decides to favourable (Raman's confirmed reading)."""
    assert _h7("HTJAH-II.chart_08", "marital_happiness") == "favourable"


def test_gate_no_op_off_marriage_and_off_afflicted():
    """The gate is scoped to marriage significations and only acts on an afflicted input."""
    ch = _chart("HTJAH-II.chart_08")
    lead = ht.judge_house(ch, 7).significations[0].ledger
    spouse = Signification(key="spouse", house=7, primary_karaka="Venus")
    wealth = Signification(key="wealth", house=2, primary_karaka="Jupiter")
    # non-afflicted inputs are untouched
    assert ht._marginal_karaka_gate(ch, spouse, "favourable", lead)[0] == "favourable"
    assert ht._marginal_karaka_gate(ch, spouse, "mixed", lead)[0] == "mixed"
    # a non-marriage signification is out of scope even when afflicted
    assert ht._marginal_karaka_gate(ch, wealth, "afflicted", lead)[0] == "afflicted"
