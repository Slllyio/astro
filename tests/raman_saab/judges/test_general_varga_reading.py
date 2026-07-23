"""General-varga reading — `judges/general_varga_reading.py`.

Public-baseline structure/smoke over the four matterless vargas + the unknown-varga guard + the
report-only invariant.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.judges import general_varga_reading as gv

_BASELINE = BirthData(name="baseline", year=1990, month=7, day=15, hour=12, minute=0,
                      tz_offset=5.5, latitude=12.97, longitude=77.59)


class TestGeneralVargaReading:
    @pytest.fixture(scope="class")
    def chart(self):
        return cast_chart(_BASELINE, ayanamsa="raman")

    def test_all_four_general_vargas_build(self, chart) -> None:
        """D-27/40/45/60 each read their own strength/character (valid lagna, disjoint strong/weak)."""
        for v in (27, 40, 45, 60):
            r = gv.build_general_varga_reading(chart, v)
            assert r.varga == v and 1 <= r.lagna_sign <= 12
            assert not (set(r.strong_planets) & set(r.weak_planets))   # a planet isn't both

    def test_general_vargas_constant(self) -> None:
        """GENERAL_VARGAS enumerates exactly the matterless vargas."""
        assert set(gv.GENERAL_VARGAS) == {27, 40, 45, 60}

    def test_d60_theme_and_provenance(self, chart) -> None:
        """The Ṣaṣṭyāṁśa carries the accumulated-karma theme, tagged CLASSICAL (Rath)."""
        r = gv.build_general_varga_reading(chart, 60)
        assert "accumulated karma" in r.theme
        assert any(n.provenance == "CLASSICAL_NONCITABLE" for n in r.notes)

    def test_unknown_varga_raises(self, chart) -> None:
        """A varga that IS a matter-varga (e.g. D-9) is rejected here — wrong reader."""
        with pytest.raises(ValueError):
            gv.build_general_varga_reading(chart, 9)


class TestReportOnlyInvariant:
    def test_house_template_never_imports_the_general_varga_surface(self) -> None:
        import app.raman_saab.judges.house_template as ht
        assert "general_varga_reading" not in Path(ht.__file__).read_text(encoding="utf-8")
