"""field_case_01 Shodasavarga validation — hard pins for the execution-verified robust
facts of the confirmed real nativity. The softer engine-vs-life comparison (including
the honest D24 and D3 misses) lives in docs/raman_saab/varga_validation_field_case_01.md,
reviewed by the chart's owner — not asserted here.

Owner-confirmed life facts behind the pins: two daughters with an ongoing child-worry
(D7); IFS career + cemented reputation (D10); never purchased a vehicle (D16); marriage
realized, turbulent-but-stable (D9 vargottama lagna = the rectified Scorpio rising in
both D1 and D9); wealth rising since 2020 (D2); parents alive and well (D12).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.judges.varga_judge import build_shodasavarga_report

_FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "field_case_01.json"


@pytest.fixture(scope="module")
def report():
    b = json.loads(_FIXTURE.read_text(encoding="utf-8"))["birth"]
    chart = cast_chart(BirthData(name="field", year=b["year"], month=b["month"],
                                 day=b["day"], hour=b["hour"], minute=b["minute"],
                                 tz_offset=b["tz_offset"], latitude=b["latitude"],
                                 longitude=b["longitude"]), ayanamsa="raman")
    return build_shodasavarga_report(chart)


def _d(report, n):
    return next(r for r in report.readings if r.n == n)


class TestLifeFactPins:
    def test_d9_vargottama_lagna(self, report) -> None:
        """Scorpio rises in both D1 and D9 — the rectified lagna's own confirmation."""
        assert _d(report, 9).chart.lagna_vargottama

    def test_d7_children_affliction_visible(self, report) -> None:
        """Mars and Ketu tenant the Sapthamsa lagna — the children-varga carries the
        malefic pressure the owner's real child-worry confirms."""
        assert _d(report, 7).malefics_on_lagna == ("Mars", "Ketu")

    def test_d10_career_strength_visible(self, report) -> None:
        """The Dasamsa lagna lord Jupiter stands in its OWN sign in the D10 lagna
        itself — the career/reputation strength the owner's IFS record confirms."""
        d10 = _d(report, 10)
        assert d10.lagna_lord.planet == "Jupiter"
        assert d10.lagna_lord.dignity == "own"
        assert d10.lagna_lord.varga_house == 1

    def test_d16_vehicle_weakness_visible(self, report) -> None:
        """The Shodasamsa lagna lord sits in the D16 8th — the owner never purchased
        a vehicle in his life."""
        assert _d(report, 16).lagna_lord.varga_house == 8

    def test_d2_wealth_confirms(self, report) -> None:
        """Hora: own-sign Sun + exalted Dhana-karaka Jupiter -> confirms; the owner's
        wealth has risen steadily since 2020."""
        assert _d(report, 2).status == "confirms"

    def test_d12_parents_confirm(self, report) -> None:
        """Dwadasamsa: exalted lagna lord Venus -> confirms; both parents are well."""
        assert _d(report, 12).status == "confirms"


class TestVargaviseshaPins:
    def test_mercury_holds_parvathamsa(self, report) -> None:
        """The chart's exalted Mercury is thrice in its own varga (D1/D3/D30) —
        Parvathamsa, the strongest Parijatadi standing in this nativity."""
        merc = next(v for v in report.vargavisesha if v.planet == "Mercury")
        assert merc.own_varga_count == 3 and merc.label == "Parvathamsa"

    def test_sun_holds_parijatamsa(self, report) -> None:
        sun = next(v for v in report.vargavisesha if v.planet == "Sun")
        assert sun.own_varga_count == 2 and sun.label == "Parijatamsa"
