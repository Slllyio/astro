"""Varga-judge tests — 16 readings build on the field-case nativity, the D2 hora
peculiarity, sparse-chart degradation, the generalized status model, and the
verdict-authority invariant (varga_judge must never enter the D1 verdict path).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData, RamanChart
from app.raman_saab.judges.varga_judge import build_shodasavarga_report

_FIXTURE = Path(__file__).resolve().parents[2] / "fixtures" / "field_case_01.json"


@pytest.fixture(scope="module")
def report():
    b = json.loads(_FIXTURE.read_text(encoding="utf-8"))["birth"]
    chart = cast_chart(BirthData(name="field", year=b["year"], month=b["month"],
                                 day=b["day"], hour=b["hour"], minute=b["minute"],
                                 tz_offset=b["tz_offset"], latitude=b["latitude"],
                                 longitude=b["longitude"]), ayanamsa="raman")
    return build_shodasavarga_report(chart)


class TestReportShape:
    def test_sixteen_readings_ascending(self, report) -> None:
        assert [r.n for r in report.readings] == [1, 2, 3, 4, 7, 9, 10, 12, 16, 20,
                                                  24, 27, 30, 40, 45, 60]

    def test_every_reading_has_a_resolvable_citation(self, report) -> None:
        from app.raman_saab.doctrine.sources import verify
        for r in report.readings:
            assert verify(r.source), f"D{r.n}"

    def test_statuses_are_valid(self, report) -> None:
        assert all(r.status in ("confirms", "weakens", "neutral", "unknown")
                   for r in report.readings)

    def test_vargavisesha_included(self, report) -> None:
        assert len(report.vargavisesha) == 7


class TestHoraPeculiarity:
    def test_d2_is_sign_placement_only(self, report) -> None:
        """The hora reading carries no house-frame artifacts: empty occupancy tuples
        and the hora-distribution note instead."""
        d2 = next(r for r in report.readings if r.n == 2)
        assert d2.benefics_in_kendra == () and d2.malefics_in_kendra == ()
        assert d2.benefics_on_lagna == () and d2.malefics_on_lagna == ()
        assert any(k == "hora_distribution" for k, _ in d2.notes)


class TestSparseChart:
    def test_track_b_sparse_degrades_to_unknown_not_crash(self) -> None:
        """A chart with no resolvable pillar reads 'unknown', never crashes."""
        sparse = RamanChart.from_stated_positions(
            {"Rahu": {"lon": 100.0, "bhava": 4}},          # nodes are never pillars
            asc_lon=15.0, ayanamsa="raman")
        report = build_shodasavarga_report(sparse)
        assert all(r.status == "unknown" for r in report.readings)


class TestVerdictAuthorityInvariant:
    def test_house_template_does_not_import_varga_judge(self) -> None:
        """D9 keeps its exclusive D1-verdict role: the verdict path never imports the
        varga judge (report-only surface in v1)."""
        import app.raman_saab.judges.house_template as ht
        src = Path(ht.__file__).read_text(encoding="utf-8")
        assert "varga_judge" not in src

    def test_d1_judgment_unchanged_by_import(self) -> None:
        """Importing/building the varga report leaves judge_house output identical."""
        from app.raman_saab.judges.house_template import judge_house
        b = json.loads(_FIXTURE.read_text(encoding="utf-8"))["birth"]
        chart = cast_chart(BirthData(name="x", year=b["year"], month=b["month"],
                                     day=b["day"], hour=b["hour"], minute=b["minute"],
                                     tz_offset=b["tz_offset"], latitude=b["latitude"],
                                     longitude=b["longitude"]), ayanamsa="raman")
        before = [(sv.signification, sv.verdict)
                  for sv in judge_house(chart, 10).significations]
        build_shodasavarga_report(chart)
        after = [(sv.signification, sv.verdict)
                 for sv in judge_house(chart, 10).significations]
        assert before == after
