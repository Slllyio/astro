"""Powerful-Dhana-in-a-kendra floor (frontier increment, HTJAH-II:15273-15289).

Raman, Chart 218 (Libra Lagna): "The Eleventh Lord: The Sun occupies a kendra in exaltation
joining the 2nd lord Mars and 9th lord Mercury ... The powerful combination of the 2nd, 7th,
9th and 11th lords in the 7th house, a kendra, has generated a very strong yoga for gains" ->
the native a newspaper magnate. The engine read gains 'afflicted' (a benefic/malefic
contradiction + weak Jupiter karaka + weakening navamsa tripped the clause-2 V2 guard);
_powerful_dhana_kendra_floor lifts it decisively to favourable when the 11th lord is itself the
strong, exalted/own, kendra-placed anchor of the multi-lord yoga. The >= 2-conjunct-artha-lords
clause is the discriminator that keeps it off every other H11 golden (over-fire scanned to
Chart 218 alone).
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


def _sig_verdict(pf, key: str):
    for sv in pf.significations:
        if sv.signification == key:
            return sv
    return None


def test_chart_218_gains_lifted_to_favourable():
    """Chart 218: exalted 11th-lord Sun in the 7th (kendra) joined by 2nd/7th-lord Mars and
    9th-lord Mercury -> the powerful Dhana yoga makes gains favourable (was afflicted)."""
    sv = _sig_verdict(ht.judge_house(_chart("HTJAH-II.h11_09"), 11), "gains")
    assert sv is not None and sv.verdict == "favourable"
    assert ("dhana_kendra_floor", "Y.DHANA.KENDRA:favourable") in sv.metadata


def test_gate_no_op_off_house_and_when_already_favourable():
    """The gate touches only an afflicted/mixed H11 gains/acquisitions matter."""
    ch = _chart("HTJAH-II.h11_09")
    gains = Signification(key="gains", house=11, primary_karaka="Jupiter")
    off_house = Signification(key="self", house=1, primary_karaka="Sun")
    lead = ht._build_frame_ledger(ch, gains, "lagna")
    off_lead = ht._build_frame_ledger(ch, off_house, "lagna")
    assert ht._powerful_dhana_kendra_floor(ch, gains, "favourable", lead)[0] == "favourable"
    assert ht._powerful_dhana_kendra_floor(ch, off_house, "afflicted", off_lead)[0] == "afflicted"
    # the target lift itself, exercised directly on the gains ledger:
    assert ht._powerful_dhana_kendra_floor(ch, gains, "afflicted", lead)[0] == "favourable"


def test_discriminator_requires_two_conjunct_artha_lords_chart_37():
    """NH chart_37: the 11th lord is strong, exalted/own AND in a kendra — but only ONE other
    {2,7,9,11} lord joins it (< 2), so the powerful-yoga floor does NOT fire (no over-lift)."""
    ch = _chart("NH.chart_37")
    gains = Signification(key="gains", house=11, primary_karaka="Jupiter")
    lead = ht._build_frame_ledger(ch, gains, "lagna")
    assert ht._powerful_dhana_kendra_floor(ch, gains, "afflicted", lead)[0] == "afflicted"
