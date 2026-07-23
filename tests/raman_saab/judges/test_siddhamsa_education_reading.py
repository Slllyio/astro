"""Siddhāṁśa (D-24) education reading — `judges/siddhamsa_education_reading.py`.

Public-baseline structure/smoke (never private data) + the report-only invariant.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.raman_saab.chart.adapter import cast_chart
from app.raman_saab.chart.model import BirthData
from app.raman_saab.judges import siddhamsa_education_reading as se

_BASELINE = BirthData(name="baseline", year=1990, month=7, day=15, hour=12, minute=0,
                      tz_offset=5.5, latitude=12.97, longitude=77.59)


class TestSiddhamsaEducationSmoke:
    @pytest.fixture(scope="class")
    def reading(self) -> se.SiddhamsaEducationReading:
        return se.build_siddhamsa_education_reading(cast_chart(_BASELINE, ayanamsa="raman"))

    def test_core_and_overlay_assemble(self, reading: se.SiddhamsaEducationReading) -> None:
        """Raman core (4th + Jupiter/Mercury) + the D-24 overlay both build."""
        c = reading.core
        assert 1 <= c.fourth_sign <= 12 and c.fourth_lord
        assert 1 <= reading.overlay.lagna_sign <= 12

    def test_education_karakas_are_jupiter_and_mercury(self, reading) -> None:
        """The education kārakas are Jupiter and Mercury, each with rasi + navāṁśa dignity."""
        names = {k for k, _h, _r, _n in reading.core.karakas}
        assert names == {"Jupiter", "Mercury"}

    def test_verdicts_present(self, reading: se.SiddhamsaEducationReading) -> None:
        """Education and intellect verdicts come from Raman's real method."""
        allowed = {"favourable", "mixed", "afflicted", "insufficient-evidence"}
        assert reading.core.education_verdict in allowed
        assert reading.core.intellect_verdict in allowed


class TestReportOnlyInvariant:
    def test_house_template_never_imports_the_siddhamsa_surface(self) -> None:
        import app.raman_saab.judges.house_template as ht
        assert "siddhamsa_education" not in Path(ht.__file__).read_text(encoding="utf-8")
