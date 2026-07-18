"""Catastrophic-key severity gate — imprisonment / blindness / grave-accident afflictions
require >= 3 fired malefic rules (Raman pronounces them only on multiply-afflicted charts);
a thinner affliction demotes afflicted -> mixed. Over-fire scanned: every confirmed Raman
jail/blind golden carries >= 3 malefic and stays afflicted.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.judges import house_template as ht

_FIELD = Path(__file__).resolve().parents[2] / "fixtures" / "field_case_01.json"


def _sig(chart, house, key):
    return next((s for s in ht.judge_house(chart, house).significations
                 if s.signification == key), None)


class TestGateUnit:
    def test_demotes_catastrophic_afflicted_below_threshold(self) -> None:
        """< 3 fired malefic on a catastrophic key demotes afflicted -> mixed."""
        from app.raman_saab.judges.house_template import FrameLedger
        from app.raman_saab.doctrine.significations import Signification

        lead = FrameLedger(
            frame="lagna", lord="Venus", lord_strong=True, karaka="Saturn",
            karaka_strong=True, bhava_bala=None, bhava_bala_strong=None,
            navamsa_status="neutral", karaka_intact=True, maraka_active=False,
            parivartana_resilient=False, lord_karaka_identical=False,
            fired_benefic=(), fired_malefic=(object(), object()), fired_neutral=())
        sig = Signification(key="incarceration", house=12, primary_karaka="Saturn")
        v, md = ht._catastrophic_severity_gate(sig, "afflicted", lead)
        assert v == "mixed" and md and md[0][0] == "catastrophic_gate"

    def test_keeps_afflicted_at_or_above_threshold(self) -> None:
        """>= 3 fired malefic (a genuinely multiply-afflicted chart) is untouched."""
        from app.raman_saab.judges.house_template import FrameLedger
        from app.raman_saab.doctrine.significations import Signification

        lead = FrameLedger(
            frame="lagna", lord="Venus", lord_strong=True, karaka="Saturn",
            karaka_strong=True, bhava_bala=None, bhava_bala_strong=None,
            navamsa_status="neutral", karaka_intact=True, maraka_active=False,
            parivartana_resilient=False, lord_karaka_identical=False,
            fired_benefic=(), fired_malefic=(object(), object(), object()),
            fired_neutral=())
        sig = Signification(key="left_eye", house=12, primary_karaka="Venus")
        v, md = ht._catastrophic_severity_gate(sig, "afflicted", lead)
        assert v == "afflicted" and md == ()

    def test_does_not_touch_non_catastrophic_keys(self) -> None:
        """Ordinary dusthana matters (disease/enemies/debts) keep the single-malefic bar."""
        from app.raman_saab.judges.house_template import FrameLedger
        from app.raman_saab.doctrine.significations import Signification

        lead = FrameLedger(
            frame="lagna", lord="Mars", lord_strong=True, karaka="Saturn",
            karaka_strong=True, bhava_bala=None, bhava_bala_strong=None,
            navamsa_status="neutral", karaka_intact=True, maraka_active=False,
            parivartana_resilient=False, lord_karaka_identical=False,
            fired_benefic=(), fired_malefic=(object(),), fired_neutral=())
        sig = Signification(key="disease_chronic", house=6, primary_karaka="Saturn")
        assert ht._catastrophic_severity_gate(sig, "afflicted", lead) == ("afflicted", ())


class TestFieldCaseEffect:
    def test_field_case_catastrophic_keys_demote_to_mixed(self) -> None:
        """The real nativity: accidents/incarceration/left_eye (< 3 malefic) read 'mixed',
        not 'afflicted' — matching a life with no jail / blindness / grave accident."""
        cs = json.loads(_FIELD.read_text(encoding="utf-8"))
        b = cs["birth"]
        ch = cast_chart(BirthData(name="f", year=b["year"], month=b["month"], day=b["day"],
                                  hour=b["hour"], minute=b["minute"], tz_offset=b["tz_offset"],
                                  latitude=b["latitude"], longitude=b["longitude"]),
                        ayanamsa="raman")
        assert _sig(ch, 12, "incarceration").verdict == "mixed"
        assert _sig(ch, 12, "left_eye").verdict == "mixed"
        assert _sig(ch, 6, "accidents").verdict == "mixed"


class TestRamanGoldensUntouched:
    @pytest.mark.parametrize("cid,house,key", [
        ("HTJAH-II.h12_13", 12, "left_eye"),
        ("HTJAH-II.h12_14", 12, "left_eye"),
        ("HTJAH-II.h12_09", 12, "incarceration"),
        ("NH.chart_34", 12, "incarceration"),
    ])
    def test_multiply_afflicted_goldens_stay_afflicted(self, cid, house, key) -> None:
        """Raman's real jailed/blind natives (>= 3 fired malefic) are NOT demoted."""
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        import test_goldens as T  # loaded by path (tests/ is not a package)
        rec = next(r for r in T._GOLDENS if T._id(r) == cid)
        chart = T.build_chart(rec)
        sv = _sig(chart, house, key)
        assert sv is not None and sv.verdict == "afflicted"
