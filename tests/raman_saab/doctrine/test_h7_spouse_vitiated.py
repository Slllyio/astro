"""H7.C.86 — afflicted 7th lord vitiates the spouse (the 3 HIGH-confidence reversals).

A heavily-afflicted 7th lord (conjunct a node + malefic-aspected, OR papakartari) renders the
spouse/marriage character vitiated (afflicted), carried decisively past the engine's favourable
preponderance. Guarded to exclude a debilitated lord (the milder unconventional-marriage =
mixed reading) and a blemishless-benefic-relieved lord.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData, RamanChart
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


def _spouse(cid: str) -> str:
    return next(s.verdict for s in ht.judge_house(_chart(cid), 7).significations
               if s.signification == "spouse")


def test_h7_02_node_afflicted_lord_immoral_spouse():
    """h7_02 (Chart 14): 7th lords afflicted by Rahu -> immoral spouse -> afflicted."""
    assert _spouse("HTJAH-II.h7_02") == "afflicted"


def test_h7_05_papakartari_lord_wife_left():
    """h7_05 (Chart 17): papakartari on the 7th lord Mars -> disharmony, wife left -> afflicted."""
    assert _spouse("HTJAH-II.h7_05") == "afflicted"


def test_h7_15_lord_and_venus_much_afflicted_profligate():
    """h7_15 (Chart 27): 7th lord (node + 2 malefic aspects) much afflicted -> profligate ->
    afflicted (the touching Venus is node-conjunct, so the blemishless-relief guard is safe)."""
    assert _spouse("HTJAH-II.h7_15") == "afflicted"


def test_h7_19_debilitated_lord_excluded():
    """h7_19 (Chart 32): the 7th lord is DEBILITATED -> the unconventional-marriage (mixed)
    family; the debil guard suppresses the rule so it is NOT pushed to afflicted."""
    assert _spouse("HTJAH-II.h7_19") != "afflicted"


def test_h7_06_clean_lord_spared():
    """h7_06 (Chart 18, mixed): a clean 7th lord -> the rule does not fire (stays mixed)."""
    assert _spouse("HTJAH-II.h7_06") == "mixed"
