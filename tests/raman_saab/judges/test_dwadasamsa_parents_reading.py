"""Dvādaśāṁśa (D-12) parents reading — `judges/dwadasamsa_parents_reading.py`.

Public-baseline structure/smoke (never private data) + the report-only invariant.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.judges import dwadasamsa_parents_reading as dp

_BASELINE = BirthData(name="baseline", year=1990, month=7, day=15, hour=12, minute=0,
                      tz_offset=5.5, latitude=12.97, longitude=77.59)
_ALLOWED = {"favourable", "mixed", "afflicted", "insufficient-evidence"}


class TestDwadasamsaParentsSmoke:
    @pytest.fixture(scope="class")
    def reading(self) -> dp.DwadasamsaParentsReading:
        return dp.build_dwadasamsa_parents_reading(cast_chart(_BASELINE, ayanamsa="raman"))

    def test_mother_is_4th_moon_father_is_9th_sun(self, reading) -> None:
        """The mother is read from the 4th/Moon, the father from the 9th/Sun."""
        assert reading.mother.house == 4 and reading.mother.karaka == "Moon"
        assert reading.father.house == 9 and reading.father.karaka == "Sun"

    def test_both_verdicts_present(self, reading: dp.DwadasamsaParentsReading) -> None:
        """Both parents carry a Raman-method verdict."""
        assert reading.mother.verdict in _ALLOWED and reading.father.verdict in _ALLOWED

    def test_overlay_casts_the_d12(self, reading: dp.DwadasamsaParentsReading) -> None:
        """The D-12 overlay cast succeeds (valid lagna + parent-house signs)."""
        ov = reading.overlay
        assert 1 <= ov.lagna_sign <= 12 and 1 <= ov.fourth_sign <= 12 and 1 <= ov.ninth_sign <= 12


class TestReportOnlyInvariant:
    def test_house_template_never_imports_the_dwadasamsa_surface(self) -> None:
        import app.raman_saab.judges.house_template as ht
        assert "dwadasamsa_parents" not in Path(ht.__file__).read_text(encoding="utf-8")
