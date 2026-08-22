"""The markdown render — completeness and citation discipline.

The platform contract: show EVERYTHING the reading computed, cite every claim, and never overstate.
These tests assert exactly that against a real cast chart, so a future edit that drops a section or
a citation fails here.
"""
from __future__ import annotations

import pytest

from app.parashara.chart.cast import cast
from app.parashara.reading import read
from app.parashara.render import to_markdown


@pytest.fixture(scope="module")
def md():
    chart = cast(year=1990, month=7, day=15, hour=12, minute=0,
                 tz_offset=5.5, latitude=12.97, longitude=77.59)
    return to_markdown(read(chart))


class TestCompleteness:
    def test_every_section_is_present(self, md):
        for heading in ("# Parashara reading",
                        "## House judgments", "## Vimsopaka bala", "## Shadbala",
                        "## Planetary avasthas", "## Conditional dashas", "## Sthira dasha",
                        "## Nisargayu"):
            assert heading in md, heading

    def test_all_twelve_houses_rendered(self, md):
        """No house collapsed away — every one of the 12 appears in the judgments table."""
        rows = [ln for ln in md.splitlines() if ln.startswith("| ") and " | " in ln]
        # the house table rows begin "| <n> | <sign> |"
        house_cells = [ln.split("|")[1].strip() for ln in rows]
        for h in range(1, 13):
            assert str(h) in house_cells, h

    def test_all_seven_grahas_in_vimsopaka_and_nisargayu(self, md):
        vim = md.split("## Vimsopaka")[1].split("## Conditional")[0]
        ayu = md.split("## Nisargayu")[1]
        for g in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
            assert g in vim, f"{g} missing from Vimsopaka"
            assert g in ayu, f"{g} missing from Nisargayu"

    def test_nisargayu_total_row_present(self, md):
        assert "**Total**" in md.split("## Nisargayu")[1]


class TestCitationDiscipline:
    def test_bphs_is_named_as_root(self, md):
        assert "Brihat Parashara Hora Shastra" in md
        assert "Root authority" in md

    def test_vimsopaka_rows_carry_a_resolvable_looking_citation(self, md):
        vim = md.split("## Vimsopaka")[1].split("## Conditional")[0]
        assert "BPHS-7:" in vim

    def test_chapter_citations_appear_for_each_technique(self, md):
        assert "ch.11" in md and "ch.7" in md and "ch.46" in md and "ch.43" in md


class TestHonesty:
    def test_dasha_balance_caveat_shown(self, md):
        assert "not adjusted for" in md and "Bhayat" in md

    def test_nisargayu_pre_reduction_caveat_shown(self, md):
        assert "Pre-reduction" in md.split("## Nisargayu")[1]


def test_render_is_deterministic():
    chart = cast(year=1990, month=7, day=15, hour=12, minute=0,
                 tz_offset=5.5, latitude=12.97, longitude=77.59)
    r = read(chart)
    assert to_markdown(r) == to_markdown(r)
