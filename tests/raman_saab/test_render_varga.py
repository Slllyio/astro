"""Renderer tests — deterministic, ASCII-only output containing all 16 division
headers and the vargavisesha table, in both text and markdown.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.judges.varga_judge import build_shodasavarga_report
from app.raman_saab.render_varga import to_markdown, to_text

_FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "field_case_01.json"


@pytest.fixture(scope="module")
def report():
    b = json.loads(_FIXTURE.read_text(encoding="utf-8"))["birth"]
    chart = cast_chart(BirthData(name="field", year=b["year"], month=b["month"],
                                 day=b["day"], hour=b["hour"], minute=b["minute"],
                                 tz_offset=b["tz_offset"], latitude=b["latitude"],
                                 longitude=b["longitude"]), ayanamsa="raman")
    return build_shodasavarga_report(chart)


def test_text_contains_all_divisions_and_is_ascii(report) -> None:
    txt = to_text(report)
    for n in (1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60):
        assert f"D{n} " in txt
    assert "Vargavisesha" in txt
    txt.encode("ascii")                      # raises if any non-ASCII slipped in


def test_markdown_contains_table_and_detail(report) -> None:
    md = to_markdown(report)
    assert "| D | name | domain |" in md
    assert "### D9 Navamsa" in md
    assert "## Vargavisesha" in md
    md.encode("ascii")


def test_rendering_is_deterministic(report) -> None:
    assert to_text(report) == to_text(report)
    assert to_markdown(report) == to_markdown(report)
