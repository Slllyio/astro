"""Two-malefic-occupancy demote gate — >=2 cruel malefics (Mars/Saturn/Rahu/Ketu) tenanting a
bhava whose lord does NOT compensate (not Shadbala-strong) qualify an otherwise-FAVOURABLE house
down to MIXED (Raman's comparative weighing; NH:5890, Tagore). Demote-only.
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


def test_two_malefics_weak_lord_demotes_tagore_h4():
    """NH chart_35 (Tagore): Mars+Ketu occupy the 4th and the 4th-lord (Mercury) is not strong ->
    education reads MIXED, not favourable ('desultory ... but distinction later', NH:5890)."""
    assert ht.judge_house(_chart("NH.chart_35"), 4).rollup == "mixed"


def test_strong_lord_spares_the_twin():
    """NH chart_42 H2: two malefics occupy the 2nd, but the 2nd-lord is Shadbala-STRONG (it carries
    the house) -> the compensation exemption spares it; the 2nd stays favourable."""
    assert ht.judge_house(_chart("NH.chart_42"), 2).rollup == "favourable"


def test_gate_is_demote_only():
    """The gate never touches a mixed/afflicted verdict and never reaches afflicted; on the firing
    chart it demotes favourable -> mixed only."""
    ch = _chart("NH.chart_35")
    lead = ht.judge_house(ch, 4).significations[0].ledger
    sig = Signification(key="education", house=4, primary_karaka="Mercury")
    assert ht._malefic_occupancy_gate(ch, sig, "mixed", lead)[0] == "mixed"
    assert ht._malefic_occupancy_gate(ch, sig, "afflicted", lead)[0] == "afflicted"
    assert ht._malefic_occupancy_gate(ch, sig, "insufficient-evidence", lead)[0] == "insufficient-evidence"
    assert ht._malefic_occupancy_gate(ch, sig, "favourable", lead)[0] == "mixed"
