"""Theme 3 — functional-yogakaraka non-affliction. A natural malefic (Mars/Saturn) that is the
chart's yogakaraka, occupying the Lagna, is a Raja-yoga that fortifies the self -> an over-harsh
afflicted self rises to favourable (NH chart_69, Cancer Lagna with Mars-yogakaraka). The
comparative-weighing guard holds the gate back when >=2 non-yogakaraka malefics also tenant the
Lagna (NH chart_57), mirroring _malefic_occupancy_gate.
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


def test_yogakaraka_in_lagna_lifts_self_chart_69():
    """NH chart_69 (Cancer Lagna): Mars the 5th+10th yogakaraka in the Lagna (with one co-malefic
    Ketu) fortifies the self -> favourable, not afflicted."""
    assert ht.judge_house(_chart("NH.chart_69"), 1).rollup == "favourable"


def test_guard_excludes_multi_malefic_lagna_chart_57():
    """NH chart_57: Mars-yogakaraka but TWO non-yogakaraka malefics (Saturn + Rahu) also tenant the
    Lagna -> the comparative-weighing guard holds the lift back; the self stays afflicted."""
    assert ht.judge_house(_chart("NH.chart_57"), 1).rollup == "afflicted"


def test_gate_no_op_off_lagna_and_off_afflicted():
    """The gate only acts on an afflicted LAGNA self-matter."""
    ch = _chart("NH.chart_69")
    self_sig = Signification(key="self", house=1, primary_karaka="Sun")
    career = Signification(key="career", house=10, primary_karaka="Sun")
    assert ht._yogakaraka_lagna_gate(ch, self_sig, "favourable")[0] == "favourable"
    assert ht._yogakaraka_lagna_gate(ch, self_sig, "mixed")[0] == "mixed"
    assert ht._yogakaraka_lagna_gate(ch, career, "afflicted")[0] == "afflicted"
    assert ht._yogakaraka_lagna_gate(ch, self_sig, "afflicted")[0] == "favourable"
