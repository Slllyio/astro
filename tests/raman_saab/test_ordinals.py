"""Paired test for app/raman_saab/ordinals.py — the shared English-ordinal helper.

Pins the fix for the "the 2th house" / "3th" typos the matter-varga report blocks
printed (docs/raman_saab/REPORT_CRITIQUE_2026-08-17.md), and regression-guards the
render modules that now use it.
"""
from __future__ import annotations

import re

import pytest

from app.raman_saab.ordinals import ordinal


class TestOrdinal:
    def test_first_three_take_st_nd_rd(self):
        """1/2/3 take the irregular suffixes — the exact bug was '2th'/'3th'."""
        assert ordinal(1) == "1st"
        assert ordinal(2) == "2nd"
        assert ordinal(3) == "3rd"

    def test_four_through_ten_take_th(self):
        """4..10 are all regular 'th'."""
        assert [ordinal(n) for n in range(4, 11)] == [
            "4th", "5th", "6th", "7th", "8th", "9th", "10th"]

    def test_teens_take_th(self):
        """11/12/13 are 'th' despite ending in 1/2/3."""
        assert ordinal(11) == "11th"
        assert ordinal(12) == "12th"
        assert ordinal(13) == "13th"

    def test_twenties_revert_to_st_nd_rd(self):
        """21/22/23 take the irregular suffixes again."""
        assert ordinal(21) == "21st"
        assert ordinal(22) == "22nd"
        assert ordinal(23) == "23rd"

    def test_hundreds_follow_the_same_rule(self):
        """101st but 111th — the mod-100 teen rule, not mod-10 alone."""
        assert ordinal(101) == "101st"
        assert ordinal(111) == "111th"
        assert ordinal(112) == "112th"
        assert ordinal(113) == "113th"
        assert ordinal(122) == "122nd"


#: A wrong ordinal: final digit 1/2/3 followed by 'th', not preceded by a '1'
#: (so 11th/12th/13th/112th stay legal). Houses only reach 12, so this suffices.
_BAD_ORDINAL = re.compile(r"(?<!1)[123]th\b")


def _renderer_lines(txt: str) -> str:
    """Only the lines the render module itself formats. Tagged doctrine notes
    ('* ...' / '- ...') are authored in the judges/ files, owned by another
    cluster — their remaining ordinal typos are reported, not fixed here."""
    return "\n".join(ln for ln in txt.splitlines()
                     if not ln.lstrip().startswith(("*", "-")))


@pytest.fixture(scope="module")
def chart():
    from app.raman_saab.chart.adapter import cast_chart
    from app.raman_saab.chart.model import BirthData
    return cast_chart(BirthData("Canonical Test", 1990, 7, 15, 12, 0, 5.5, 12.97, 77.59))


class TestRenderModulesUseCorrectOrdinals:
    def test_matter_varga_blocks_print_2nd_and_3rd(self, chart):
        """D-2 wealth reads 'the 2nd house', D-3 siblings 'the 3rd' — never '2th'/'3th'."""
        from app.raman_saab.judges.matter_varga_reading import build_matter_varga_reading
        from app.raman_saab.render_matter_varga import to_text
        wealth = _renderer_lines(to_text(build_matter_varga_reading(chart, "wealth")))
        siblings = _renderer_lines(to_text(build_matter_varga_reading(chart, "siblings")))
        assert "2nd house" in wealth and "2th" not in wealth
        assert "3rd house" in siblings and "3th" not in siblings
        for txt in (wealth, siblings):
            assert _BAD_ORDINAL.search(txt) is None

    def test_dwadasamsa_parent_lines_use_correct_ordinals(self, chart):
        """The D-12 mother (4th) / father (9th) header lines carry proper suffixes."""
        from app.raman_saab.judges.dwadasamsa_parents_reading import (
            build_dwadasamsa_parents_reading)
        from app.raman_saab.render_dwadasamsa import to_text
        txt = to_text(build_dwadasamsa_parents_reading(chart))
        assert _BAD_ORDINAL.search(txt) is None

    def test_relative_blocks_use_correct_ordinals(self, chart):
        """Derivative-house offsets (2nd/3rd from a relative's lagna) are suffixed right."""
        from app.raman_saab.judges.relative_reading import build_family_derivative_reading
        from app.raman_saab.render_relative import to_text
        txt = _renderer_lines(to_text(build_family_derivative_reading(chart)))
        assert _BAD_ORDINAL.search(txt) is None
        assert "2nd" in txt or "3rd" in txt      # the fixed offsets actually exercised

    def test_synastry_kuja_line_uses_correct_ordinal(self):
        """'Mars in the 2nd from Lagna' — the KujaProfile line, rendered directly."""
        from app.raman_saab.judges.two_chart_synastry import KujaProfile
        from app.raman_saab.render_synastry import _kuja_line
        line = _kuja_line(KujaProfile("husband", ("Lagna",), 2, 1, False))
        assert "2nd from Lagna" in line
        assert "2th" not in line
